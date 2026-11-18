"""SEC EDGAR client with a cache (SPEC §4). Owner: A. Slice S1.

    from src.data.sec_client import SecClient
    sec = SecClient.from_settings()          # User-Agent from app/.env, limits from app/settings.yaml
    cik = sec.cik_for("KO")                  # "0000021344"
    facts = sec.companyfacts(cik).data       # the SEC's companyfacts JSON, as a dict

The SEC rules of SPEC §4, built in:
- every request carries the declared User-Agent (name and e-mail, from SEC_USER_AGENT). It is never printed,
  logged, put in an error message or written to the cache;
- at most `max_requests_per_second` requests (5, settings.yaml; the SEC allows 10);
- three retries with a growing pause (1, 2, 4 seconds) for temporary failures, then `SourceUnreachable`, which
  the caller turns into a `missing` figure and a message suggesting demo mode;
- every raw response is saved in the cache with its retrieval time and reused, so nothing is downloaded twice;
  `refresh=True` downloads again.

This is the only module of the app that talks to the SEC. Logic modules never import it (layering test).
"""

from __future__ import annotations

import json
import os
import re
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable

import requests
from dotenv import dotenv_values

from src.data.evidence import provenance
from src.settings import load_settings

APP = Path(__file__).resolve().parents[2]
DEFAULT_CACHE = APP / ".cache" / "sec"
ENV_FILE = APP / ".env"
TICKERS_URL = "https://www.sec.gov/files/company_tickers.json"
SUBMISSIONS_URL = "https://data.sec.gov/submissions/CIK{cik}.json"
FACTS_URL = "https://data.sec.gov/api/xbrl/companyfacts/CIK{cik}.json"
RETRYABLE = {429, 500, 502, 503, 504}
TIMEOUT_SECONDS = 30


class SecError(Exception):
    """Something went wrong with SEC data; the message says how to fix it."""


class MissingUserAgent(SecError):
    pass


class UnknownTicker(SecError):
    pass


class NotFound(SecError):
    pass


class SourceUnreachable(SecError):
    pass


@dataclass(frozen=True)
class Download:
    """One SEC file: its parsed JSON and where and when it was retrieved."""

    data: dict
    source: str
    retrieved: datetime
    from_cache: bool
    provenance: dict


def check_user_agent(agent: str | None) -> str:
    """The declared User-Agent, or MissingUserAgent. The value itself is never put in the message."""
    agent = (agent or "").strip().strip('"')
    if not agent.isascii():
        raise MissingUserAgent(
            "SEC_USER_AGENT contains a character that is not plain ASCII, often a curly quote typed by the Mac. "
            'Retype it in app/.env with straight quotes: SEC_USER_AGENT="Your Name your@email".'
        )
    if "@" not in agent or "example.com" in agent:
        raise MissingUserAgent(
            "SEC_USER_AGENT is missing or still the example. The SEC requires your name and e-mail: create "
            'app/.env from app/.env.example and set SEC_USER_AGENT="Your Name your@email". Demo mode needs none.'
        )
    return agent


def user_agent_from_env(env_file: Path = ENV_FILE) -> str:
    """SEC_USER_AGENT from the environment if set (inline runs), otherwise from app/.env. Changes no variable."""
    agent = os.environ.get("SEC_USER_AGENT")
    if not agent and env_file.exists():
        agent = dotenv_values(env_file).get("SEC_USER_AGENT")
    return check_user_agent(agent)


def _cik(cik: str | int) -> str:
    text = str(cik).strip()
    if not re.fullmatch(r"\d{1,10}", text):
        raise ValueError(f"an SEC company number has 1 to 10 digits, got {cik!r}")
    return text.zfill(10)


def _normalise_ticker(ticker: str) -> str:
    return ticker.strip().upper().replace(".", "-")


class SecClient:
    def __init__(
        self,
        user_agent: str | None,
        cache_dir: Path = DEFAULT_CACHE,
        *,
        session=None,
        max_per_second: float = 5,
        retries: int = 3,
        clock: Callable[[], float] = time.monotonic,
        sleep: Callable[[float], None] = time.sleep,
        now: Callable[[], datetime] = lambda: datetime.now(timezone.utc).replace(microsecond=0),
    ):
        self._agent = check_user_agent(user_agent)
        self._cache = Path(cache_dir)
        self._session = session if session is not None else requests.Session()
        self.max_per_second = max_per_second
        self.retries = retries
        self._clock, self._sleep, self._now = clock, sleep, now
        self._last_request: float | None = None
        self._tickers: dict[str, dict] | None = None

    @classmethod
    def from_settings(cls, cache_dir: Path = DEFAULT_CACHE, env_file: Path = ENV_FILE, **options) -> SecClient:
        data = load_settings()["data"]
        return cls(
            user_agent_from_env(env_file),
            cache_dir,
            max_per_second=data["max_requests_per_second"],
            retries=data["retries"],
            **options,
        )

    # --- public ------------------------------------------------------------------------------------------------

    def ticker_list(self, refresh: bool = False) -> Download:
        return self._cached(TICKERS_URL, "company_tickers", refresh)

    def submissions(self, cik: str | int, refresh: bool = False) -> Download:
        cik = _cik(cik)
        return self._cached(SUBMISSIONS_URL.format(cik=cik), f"submissions_{cik}", refresh)

    def companyfacts(self, cik: str | int, refresh: bool = False) -> Download:
        cik = _cik(cik)
        return self._cached(FACTS_URL.format(cik=cik), f"companyfacts_{cik}", refresh)

    def cik_for(self, ticker: str) -> str:
        """The 10-digit SEC company number of a ticker ("BRK.B" and "brk-b" both work)."""
        return self._ticker_entry(ticker)["cik"]

    def company_name(self, ticker: str) -> str:
        return self._ticker_entry(ticker)["title"]

    # --- internals -----------------------------------------------------------------------------------------------

    def _ticker_entry(self, ticker: str) -> dict:
        if self._tickers is None:
            self._tickers = {
                _normalise_ticker(entry["ticker"]): {"cik": _cik(entry["cik_str"]), "title": entry["title"]}
                for entry in self.ticker_list().data.values()
            }
        key = _normalise_ticker(ticker)
        if key not in self._tickers:
            raise UnknownTicker(
                f"Ticker {ticker.strip()!r} is not in the SEC's list of companies. Check the spelling (US tickers "
                "only, e.g. KO for Coca-Cola)."
            )
        return self._tickers[key]

    def _cached(self, url: str, name: str, refresh: bool) -> Download:
        raw_path = self._cache / f"{name}.json"
        meta_path = self._cache / f"{name}.provenance.json"
        if raw_path.exists() and meta_path.exists() and not refresh:
            record = json.loads(meta_path.read_text(encoding="utf-8"))
            return Download(self._parse(raw_path.read_bytes(), url), url,
                            datetime.fromisoformat(record["retrieved"]), True, record)
        raw = self._get(url)
        data = self._parse(raw, url)  # refuse to cache an answer that is not JSON
        retrieved = self._now()
        record = provenance(url, retrieved, raw, trimmed="none (raw download)")
        self._cache.mkdir(parents=True, exist_ok=True)
        raw_path.write_bytes(raw)
        meta_path.write_text(json.dumps(record, indent=1) + "\n", encoding="utf-8")
        return Download(data, url, retrieved, False, record)

    @staticmethod
    def _parse(raw: bytes, url: str) -> dict:
        try:
            return json.loads(raw)
        except ValueError:
            raise SecError(f"{url} did not return JSON (the SEC may be limiting requests). Try again later.") from None

    def _get(self, url: str) -> bytes:
        problem = ""
        for attempt in range(self.retries + 1):
            self._respect_rate_limit()
            try:
                response = self._session.get(
                    url,
                    headers={"User-Agent": self._agent, "Accept-Encoding": "gzip, deflate"},
                    timeout=TIMEOUT_SECONDS,
                )
            except requests.RequestException as error:
                problem = type(error).__name__
            else:
                if response.status_code == 200:
                    return response.content
                if response.status_code == 404:
                    raise NotFound(f"{url} does not exist (HTTP 404): check the ticker or SEC company number.")
                problem = f"HTTP {response.status_code}"
                if response.status_code not in RETRYABLE:
                    break
            if attempt < self.retries:
                self._sleep(2**attempt)
        raise SourceUnreachable(
            f"The SEC could not be reached for {url} ({problem}, after {self.retries} retries). Check the internet "
            "connection and try again, or switch on demo mode."
        )

    def _respect_rate_limit(self) -> None:
        if self._last_request is not None:
            wait = 1 / self.max_per_second - (self._clock() - self._last_request)
            if wait > 0:
                self._sleep(wait)
        self._last_request = self._clock()
