"""SEC EDGAR client with a cache (SPEC §4). Owner: A. Slice S1.

    from src.data.sec_client import SecClient
    sec = SecClient.from_settings()          # User-Agent from app/.env, limits from app/settings.yaml
    cik = sec.cik_for("KO")                  # "0000021344"
    facts = sec.companyfacts(cik).data       # the SEC's companyfacts JSON, as a dict

In Streamlit, make one client per session (e.g. with `st.cache_resource`); all clients share one rate limiter.

The SEC rules of SPEC §4, built in:
- every request carries the declared User-Agent (a name and an e-mail, from SEC_USER_AGENT). It is never printed,
  logged, put in an error message, shown in the client's attributes or written to the cache;
- at most `max_requests_per_second` requests (5, settings.yaml; the SEC allows 10) for the whole app;
- three retries with a growing pause (1, 2, 4 seconds) for temporary failures;
- every raw response is saved in the cache with its retrieval time and reused, so nothing is downloaded twice;
  `refresh=True` downloads again. Cache files are written atomically and checked (SHA-256) when read; a damaged
  entry is downloaded again.

What the errors mean for the caller (all are `SecError`, and every message says how to fix the problem):
- `SourceUnreachable`: temporary (no connection, SEC busy, an answer that is not JSON) after the retries. The
  input becomes `missing` with this message as the reason; the app suggests demo mode (SPEC §4, E4).
- `MissingUserAgent`, `SecRefused` (HTTP 403): the person running the app must fix app/.env or wait.
- `UnknownTicker`, `NotFound`, `InvalidCik`: the ticker or company number does not exist.

This is the only module of the app that talks to the SEC. Logic modules never import it (layering test).
"""

from __future__ import annotations

import hashlib
import io
import json
import numbers
import os
import re
import threading
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
SEC_MAX_PER_SECOND = 10


class SecError(Exception):
    """Something went wrong with SEC data; the message says how to fix it."""


class MissingUserAgent(SecError):
    pass


class SecRefused(SecError):
    pass


class UnknownTicker(SecError):
    pass


class NotFound(SecError):
    pass


class InvalidCik(SecError, ValueError):
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


class _Hidden:
    """Holds the User-Agent so that it never shows in a repr, a debugger or a traceback."""

    __slots__ = ("value",)

    def __init__(self, value: str):
        self.value = value

    def __repr__(self) -> str:
        return "<hidden>"


class RateLimiter:
    """Keeps requests apart; one limiter is shared by every client of the app, so the limit holds overall."""

    def __init__(self, clock: Callable[[], float] = time.monotonic, sleep: Callable[[float], None] = time.sleep):
        self._clock, self._sleep = clock, sleep
        self._lock = threading.Lock()
        self._last: float | None = None

    def wait(self, interval: float) -> None:
        with self._lock:
            if self._last is not None:
                pause = interval - (self._clock() - self._last)
                if pause > 0:
                    self._sleep(pause)
            self._last = self._clock()


_SHARED_LIMITER = RateLimiter()

_AGENT = re.compile(r"(?P<name>\S.*?)\s+(?P<email>[^\s@]+@[^\s@]+\.[^\s@]+)")


def check_user_agent(agent: str | None) -> str:
    """The declared User-Agent (a name and an e-mail), or MissingUserAgent. The value is never put in a message."""
    agent = (agent or "").strip().strip("\"'").strip()
    if any(ord(ch) < 32 or ord(ch) == 127 for ch in agent):
        raise MissingUserAgent("SEC_USER_AGENT contains a line break or another control character; keep it on one line.")
    if not agent.isascii():
        raise MissingUserAgent(
            "SEC_USER_AGENT contains a character that is not plain ASCII: a curly quote typed by the Mac, or an "
            'accented letter (write ü as ue). Retype it in app/.env as SEC_USER_AGENT="Your Name your@email".'
        )
    if not _AGENT.fullmatch(agent) or "example.com" in agent:
        raise MissingUserAgent(
            "SEC_USER_AGENT is missing, incomplete or still the example. The SEC requires your name and e-mail: "
            'create app/.env from app/.env.example and set SEC_USER_AGENT="Your Name your@email". Demo mode '
            "needs none of this."
        )
    return agent


def user_agent_from_env(env_file: Path = ENV_FILE) -> str:
    """SEC_USER_AGENT from the environment if set (inline runs), otherwise from app/.env. Changes no variable."""
    agent = os.environ.get("SEC_USER_AGENT")
    if not agent and env_file.exists():
        raw = env_file.read_bytes()
        try:
            if raw[:2] in (b"\xff\xfe", b"\xfe\xff"):
                raise UnicodeDecodeError("utf-16", raw[:2], 0, 2, "byte-order mark of UTF-16")
            text = raw.decode("utf-8-sig")
        except UnicodeDecodeError:
            raise MissingUserAgent(
                "app/.env could not be read: save it as UTF-8 (Windows PowerShell 5 writes UTF-16 with `>`; create "
                "it with `copy .env.example .env` and edit it in VS Code instead)."
            ) from None
        agent = dotenv_values(stream=io.StringIO(text)).get("SEC_USER_AGENT")
    return check_user_agent(agent)


def _cik(cik: str | int) -> str:
    text = str(cik).strip()
    if not re.fullmatch(r"[0-9]{1,10}", text):
        raise InvalidCik(f"An SEC company number has 1 to 10 digits, got {cik!r}.")
    return text.zfill(10)


def _normalise_ticker(ticker: str) -> str:
    return ticker.strip().upper().replace(".", "-")


def _json_object(raw: bytes) -> dict | None:
    try:
        data = json.loads(raw)
    except ValueError:
        return None
    return data if isinstance(data, dict) else None


def _write_atomic(path: Path, content: bytes) -> None:
    temporary = path.with_name(path.name + ".tmp")
    temporary.write_bytes(content)
    os.replace(temporary, path)


class SecClient:
    def __init__(
        self,
        user_agent: str | None,
        cache_dir: Path = DEFAULT_CACHE,
        *,
        session=None,
        max_per_second: float = 5,
        retries: int = 3,
        limiter: RateLimiter | None = None,
        clock: Callable[[], float] | None = None,
        sleep: Callable[[float], None] | None = None,
        now: Callable[[], datetime] = lambda: datetime.now(timezone.utc).replace(microsecond=0),
    ):
        if isinstance(max_per_second, bool) or not isinstance(max_per_second, numbers.Real) or not (
            0 < max_per_second <= SEC_MAX_PER_SECOND
        ):
            raise ValueError(f"max_per_second must be above 0 and at most {SEC_MAX_PER_SECOND} (the SEC's limit)")
        if isinstance(retries, bool) or not isinstance(retries, int) or retries < 0:
            raise ValueError("retries must be a whole number, 0 or more")
        self._agent = _Hidden(check_user_agent(user_agent))
        self._cache = Path(cache_dir)
        self._session = session if session is not None else requests.Session()
        self.max_per_second = max_per_second
        self.retries = retries
        self._sleep = sleep or time.sleep
        if limiter is not None:
            self._limiter = limiter
        elif clock is not None or sleep is not None:
            self._limiter = RateLimiter(clock or time.monotonic, self._sleep)  # tests: a limiter of their own
        else:
            self._limiter = _SHARED_LIMITER
        self._now = now
        self._tickers: dict[str, list[dict]] | None = None

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
        download = self._cached(TICKERS_URL, "company_tickers", refresh)
        lookup: dict[str, list[dict]] = {}
        for entry in download.data.values():
            lookup.setdefault(_normalise_ticker(entry["ticker"]), []).append(
                {"cik": _cik(entry["cik_str"]), "title": entry["title"]}
            )
        self._tickers = lookup
        return download

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
            self.ticker_list()
        entries = self._tickers.get(_normalise_ticker(ticker), [])
        if not entries:
            raise UnknownTicker(
                f"Ticker {ticker.strip()!r} is not in the SEC's list of companies. Check the spelling (US tickers "
                "only, e.g. KO for Coca-Cola)."
            )
        if len({entry["cik"] for entry in entries}) > 1:
            raise SecError(
                f"Ticker {ticker.strip()!r} matches more than one company in the SEC's list; use the SEC company "
                "number instead."
            )
        return entries[0]

    def _cached(self, url: str, name: str, refresh: bool) -> Download:
        raw_path = self._cache / f"{name}.json"
        meta_path = self._cache / f"{name}.provenance.json"
        if not refresh:
            cached = self._read_cache(raw_path, meta_path, url)
            if cached is not None:
                return cached
        raw, data = self._get(url)
        retrieved = self._now()
        record = provenance(url, retrieved, raw, trimmed="none (raw download)")
        self._cache.mkdir(parents=True, exist_ok=True)
        _write_atomic(raw_path, raw)  # raw first, provenance last: a stop in between leaves a checksum mismatch
        _write_atomic(meta_path, (json.dumps(record, indent=1) + "\n").encode("utf-8"))
        return Download(data, url, retrieved, False, record)

    @staticmethod
    def _read_cache(raw_path: Path, meta_path: Path, url: str) -> Download | None:
        """A cached download, or None if the entry is missing, damaged or does not match its checksum."""
        try:
            record = json.loads(meta_path.read_text(encoding="utf-8"))
            raw = raw_path.read_bytes()
            if record["source"] != url or hashlib.sha256(raw).hexdigest() != record["raw_sha256"]:
                return None
            data = _json_object(raw)
            if data is None:
                return None
            return Download(data, url, datetime.fromisoformat(record["retrieved"]), True, record)
        except (OSError, ValueError, KeyError, TypeError):
            return None

    def _get(self, url: str) -> tuple[bytes, dict]:
        attempts = self.retries + 1
        problem = ""
        for attempt in range(attempts):
            self._limiter.wait(1 / self.max_per_second)
            try:
                response = self._session.get(
                    url,
                    headers={"User-Agent": self._agent.value, "Accept-Encoding": "gzip, deflate"},
                    timeout=TIMEOUT_SECONDS,
                )
            except requests.RequestException as error:
                problem = f"connection problem ({type(error).__name__})"
            else:
                code = response.status_code
                if code == 200:
                    data = _json_object(response.content)
                    if data is not None:
                        return response.content, data
                    problem = "an answer that is not JSON (the SEC may be limiting requests)"
                elif code == 404:
                    raise NotFound(f"{url} does not exist (HTTP 404): check the ticker or SEC company number.")
                elif code == 403:
                    raise SecRefused(
                        "The SEC refused the request (HTTP 403). It does this when SEC_USER_AGENT is not a real name "
                        "and e-mail, or after too many requests: check app/.env, wait ten minutes, then try again."
                    )
                elif code in RETRYABLE:
                    problem = f"HTTP {code}"
                else:
                    raise SecError(f"The SEC answered {url} with HTTP {code}, which is not retried.")
            if attempt < attempts - 1:
                self._sleep(2**attempt)
        count = "1 attempt" if attempts == 1 else f"{attempts} attempts"
        raise SourceUnreachable(
            f"The SEC could not be reached for {url}: {problem}, {count}. Check the internet connection and try "
            "again, or switch on demo mode."
        )
