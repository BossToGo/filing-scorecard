"""The risk-free rate: FRED's 10-year US Treasury yield, averaged over the last five years (SPEC §4, §8.1).
Owner: A. Slice S2b.

    from src.data.company import risk_free_rate    # the interface imports it from there (layering test)
    rate = risk_free_rate(demo=True)               # a Fact: value 0.0412 means 4.12%, unit "pure"
    rate.value, rate.kind, rate.period_start, rate.period_end, rate.note

Live (`demo=False`, with FRED_API_KEY in app/.env): the daily values of series DGS10 from the last
`risk_free_average_years` years (settings.yaml, 5) up to the latest day are downloaded. Days without a value (".")
are skipped, and the average of the rest, divided by 100, comes back as a `derived` Fact with its period. It is
kept in memory for the day, not saved on disk (decided by Igor, 24 November): one download per day while the app
runs. A failed download is not remembered, so the next call tries again.

Otherwise (demo mode, no key, FRED unreachable or an unusable answer) the dated value saved in settings.yaml
(`valuation.risk_free_rate`, its period in `data.risk_free_fallback_period`) comes back as an `assumption` Fact
whose note says why. Without a saved value the rate is `missing`, never zero.

The key goes only into the request's parameters. It is never put in a Fact, a message, a log, a file or the
memory: the web library's own error messages contain the full address with the key, so only the error's type is
kept, and redirects are not followed.

FRED's terms of use (read on 24 November 2026) ask every product using the API to show `NOTICE`. DGS10 comes from
the Board of Governors of the Federal Reserve System (release H.15).
"""

from __future__ import annotations

import json
import math
import os
import re
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Callable

import requests
from dotenv import dotenv_values

from src.contracts import Fact
from src.settings import load_settings

APP = Path(__file__).resolve().parents[2]
ENV_FILE = APP / ".env"
OBSERVATIONS_URL = "https://api.stlouisfed.org/fred/series/observations"
SERIES = "DGS10"
SERIES_PAGE = "https://fred.stlouisfed.org/series/DGS10"
NOTICE = "This product uses the FRED® API but is not endorsed or certified by the Federal Reserve Bank of St. Louis."
TIMEOUT_SECONDS = 15
_KEY_FORMAT = re.compile(r"[a-z0-9]{32}")

_MEMORY: dict[tuple[date, int], Fact] = {}  # (day, years) -> the rate; never the key


class FredError(Exception):
    """FRED could not give the rate. The message is safe to show: it never contains the key."""


def forget() -> None:
    """Clear the rates kept in memory, so the next call downloads again."""
    _MEMORY.clear()


def window_start(today: date, years: int) -> date:
    """The same day `years` years earlier; 29 February becomes 28 February."""
    try:
        return today.replace(year=today.year - years)
    except ValueError:
        return today.replace(year=today.year - years, day=28)


def risk_free_rate(
    demo: bool = False,
    *,
    env_file: Path | None = None,
    session=None,
    today: date | None = None,
    settings: dict | None = None,
    now: Callable[[], datetime] | None = None,
) -> Fact:
    """The risk-free rate as a decimal Fact: FRED's five-year average live, otherwise the saved value."""
    settings = load_settings() if settings is None else settings
    today = today or date.today()
    if demo:
        return _saved(settings, today, "demo mode is on")
    years = settings["data"]["risk_free_average_years"]
    remembered = _MEMORY.get((today, years))
    if remembered is not None:
        return remembered
    try:
        key = _key(env_file or ENV_FILE)
        rate = _download_average(key, window_start(today, years), session or requests.Session(), now)
    except FredError as problem:
        return _saved(settings, today, str(problem))
    _MEMORY[(today, years)] = rate
    return rate


def _key(env_file: Path) -> str:
    key = os.environ.get("FRED_API_KEY")
    if not key and env_file.exists():
        try:
            key = dotenv_values(env_file, encoding="utf-8-sig").get("FRED_API_KEY")
        except (OSError, UnicodeDecodeError):
            key, unreadable = None, True
        else:
            unreadable = False
        if unreadable:
            raise FredError("app/.env could not be read (save it as UTF-8)")
    key = (key or "").strip().strip("\"'").strip()
    if not key:
        raise FredError("there is no FRED_API_KEY in app/.env (a free key gives today's five-year average)")
    if not _KEY_FORMAT.fullmatch(key):
        raise FredError("FRED_API_KEY in app/.env is not a FRED key, which has 32 lower-case letters and digits")
    return key


def _download_average(key: str, start: date, session, now: Callable[[], datetime] | None) -> Fact:
    params = {"series_id": SERIES, "api_key": key, "file_type": "json", "observation_start": start.isoformat()}
    failure = None
    try:
        response = session.get(OBSERVATIONS_URL, params=params, timeout=TIMEOUT_SECONDS, allow_redirects=False)
    except requests.RequestException as error:
        failure = type(error).__name__  # never str(error): it contains the address with the key
    if failure is not None:
        raise FredError(f"FRED could not be reached ({failure})")
    if response.status_code != 200:
        raise FredError(f"FRED answered with HTTP {response.status_code}")

    days = _days_with_a_value(response.content)
    first, last = days[0][0], days[-1][0]
    average = sum(value for _, value in days) / len(days)
    retrieved = now() if now else datetime.now(timezone.utc).replace(microsecond=0)
    return Fact(
        metric="risk_free_rate",
        value=average / 100,
        unit="pure",
        period_start=first,
        period_end=last,
        kind="derived",
        tag=SERIES,
        form="FRED",
        accession=None,
        filed=None,
        retrieved=retrieved,
        note=(
            f"Average of the {len(days):,} daily values of FRED series DGS10 (10-year US Treasury yield, in percent) "
            f"from {first} to {last}, divided by 100; days without a value skipped. Source: Board of Governors of "
            f"the Federal Reserve System, release H.15, via {SERIES_PAGE}."
        ),
    )


def _days_with_a_value(content: bytes) -> list[tuple[date, float]]:
    """(day, percent) for every day with a value, oldest first; FredError if the answer cannot be read."""
    days = []
    try:
        for row in json.loads(content)["observations"]:
            if row["value"] == ".":
                continue
            value = float(row["value"])
            if not math.isfinite(value):
                raise ValueError("not a finite number")
            days.append((date.fromisoformat(row["date"]), value))
    except (ValueError, KeyError, TypeError):
        days = None
    if days is None:
        raise FredError("FRED's answer could not be read")
    if not days:
        raise FredError("FRED's answer has no values for DGS10")
    return sorted(days)


def _saved(settings: dict, today: date, reason: str) -> Fact:
    value = settings["valuation"]["risk_free_rate"]
    if value is None:
        return Fact(
            metric="risk_free_rate", value=None, unit="pure", period_start=None, period_end=today, kind="missing",
            tag=SERIES, form="FRED", accession=None, filed=None, retrieved=None,
            note=f"No risk-free rate: {reason}, and settings.yaml has no saved value (valuation.risk_free_rate).",
        )
    start, end = settings["data"]["risk_free_fallback_period"]
    return Fact(
        metric="risk_free_rate", value=value, unit="pure", period_start=start, period_end=end, kind="assumption",
        tag=SERIES, form="FRED", accession=None, filed=None, retrieved=None,
        note=(
            f"Saved value: the average of FRED series DGS10 from {start} to {end} (settings.yaml, "
            f"valuation.risk_free_rate), refreshed by member A before each release. Used because {reason}."
        ),
    )
