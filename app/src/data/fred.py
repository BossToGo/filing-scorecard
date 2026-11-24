"""The risk-free rate: FRED's 10-year US Treasury yield, averaged over the last five years (SPEC §4, §8.1).
Owner: A. Slice S2b.

    from src.data.company import risk_free_rate    # the interface imports it from there (layering test)
    rate = risk_free_rate(demo=True)               # a Fact: value 0.0412 means 4.12%, unit "pure"
    rate.value, rate.kind, rate.period_start, rate.period_end, rate.note

Nothing that goes wrong with FRED or the key stops the app: the saved value is used instead. (A broken
settings.yaml still raises; `tests/unit/test_fred.py` checks the real file.)

Live (`demo=False`, with FRED_API_KEY in the environment or app/.env): the daily values of series DGS10 from the
same day `risk_free_average_years` years ago (settings.yaml, 5) up to the latest day FRED has are downloaded. Days
without a value (".") are skipped, and the average of the rest, divided by 100, comes back as a `derived` Fact with
its period. It is kept in memory for the day, not saved on disk (decided by Igor, 24 November): one download per
day while the app runs. After a failed download the saved value is used for `FAILURE_PAUSE_SECONDS` without
asking FRED again, because Streamlit reruns the page on every click.

Otherwise (demo mode, no key, a key in the wrong format, FRED unreachable, an unusable answer, or an average outside
`PLAUSIBLE`) the dated value saved in settings.yaml (`valuation.risk_free_rate`, its period in
`data.risk_free_fallback_period`) comes back as an `assumption` Fact whose note says why in plain words: the note
is shown to customers on the sources page. Without a saved value the rate is `missing`, never zero.

The key travels in the request's address (`?api_key=`), as FRED requires. Our code never stores, quotes or logs it:
it is kept out of every Fact, message and the memory, only an error's type is kept (the web library's own error
messages contain the full address), redirects are not followed, and a problem outside the expected ones is caught
without keeping its details. The web library would print the address only if someone switched on its debug logging.

FRED's terms of use (read on 24 November 2026) ask every product using the API to show `NOTICE`. DGS10 comes from
the Board of Governors of the Federal Reserve System (release H.15).
"""

from __future__ import annotations

import json
import math
import os
import re
import time
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
FAILURE_PAUSE_SECONDS = 600  # after a failed download, use the saved value for 10 minutes without asking FRED again
PLAUSIBLE = (0.0, 0.2)  # a live average outside 0% to 20% is not used (the same range as the settings test)
_KEY_FORMAT = re.compile(r"[a-z0-9]{32}")

_MEMORY: dict[tuple[date, int], Fact] = {}  # (day, years) -> the rate; never the key
_FAILED: dict[tuple[date, int], tuple[float, str]] = {}  # (day, years) -> (pause until, reason); never the key


class FredError(Exception):
    """FRED could not give the rate. The message is plain words for customers: it never contains the key."""


def forget() -> None:
    """Clear the rates and failures kept in memory, so the next call downloads again."""
    _MEMORY.clear()
    _FAILED.clear()


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
    clock: Callable[[], float] = time.monotonic,
) -> Fact:
    """The risk-free rate as a decimal Fact: FRED's five-year average live, otherwise the saved value."""
    settings = load_settings() if settings is None else settings
    today = today or date.today()
    if demo:
        return _saved(settings, today, "demo mode is on")
    years = settings["data"]["risk_free_average_years"]
    day = (today, years)
    if day in _MEMORY:
        return _MEMORY[day]
    try:
        key = _key(env_file or ENV_FILE)
    except FredError as problem:
        return _saved(settings, today, str(problem))
    paused = _FAILED.get(day)
    if paused is not None and clock() < paused[0]:
        return _saved(settings, today, paused[1])

    result = _try_download(key, window_start(today, years), session, now)
    if isinstance(result, Fact):
        _MEMORY[day] = result
        _FAILED.pop(day, None)
        return result
    _FAILED[day] = (clock() + FAILURE_PAUSE_SECONDS, result)
    return _saved(settings, today, result)


def _try_download(key: str, start: date, session, now) -> Fact | str:
    """The rate, or the reason it could not be had. Nothing about an error is kept but its type."""
    reason = None
    try:
        if session is not None:
            return _download_average(key, start, session, now)
        with requests.Session() as own:
            return _download_average(key, start, own, now)
    except FredError as problem:
        reason = str(problem)
    except Exception as error:  # anything else must not stop the app; its details could hold the key
        reason = f"the live rate could not be used ({type(error).__name__})"
    return reason


def _key(env_file: Path) -> str:
    key = os.environ.get("FRED_API_KEY")
    if not key and env_file.exists():
        unreadable = False
        try:
            key = dotenv_values(env_file, encoding="utf-8-sig").get("FRED_API_KEY")
        except (OSError, UnicodeDecodeError):
            unreadable = True
        if unreadable:
            raise FredError("the settings file with the FRED key could not be read")
    key = (key or "").strip().strip("\"'").strip()
    if not key:
        raise FredError("no FRED key is set up")
    if not _KEY_FORMAT.fullmatch(key):
        raise FredError("the FRED key set up is not in FRED's format")
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
        raise FredError(f"FRED did not answer as expected (HTTP {response.status_code})")

    days = _days_with_a_value(response.content)
    first, last = days[0][0], days[-1][0]
    rate = sum(value for _, value in days) / len(days) / 100
    if not PLAUSIBLE[0] < rate < PLAUSIBLE[1]:
        raise FredError("FRED's average was outside the plausible range of 0% to 20%")
    retrieved = now() if now else datetime.now(timezone.utc).replace(microsecond=0)
    return Fact(
        metric="risk_free_rate",
        value=rate,
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
    if len({day for day, _ in days}) != len(days):
        raise FredError("FRED's answer could not be read (a day appears twice)")
    if not days:
        raise FredError("FRED's answer had no values")
    return sorted(days)


def _saved(settings: dict, today: date, reason: str) -> Fact:
    value = settings["valuation"]["risk_free_rate"]
    if value is None:
        return Fact(
            metric="risk_free_rate", value=None, unit="pure", period_start=None, period_end=today, kind="missing",
            tag=SERIES, form="FRED", accession=None, filed=None, retrieved=None,
            note=f"No risk-free rate: {reason}, and no saved value is available.",
        )
    start, end = settings["data"]["risk_free_fallback_period"]
    return Fact(
        metric="risk_free_rate", value=value, unit="pure", period_start=start, period_end=end, kind="assumption",
        tag=SERIES, form="FRED", accession=None, filed=None, retrieved=None,
        note=(
            f"Saved five-year average of the 10-year US Treasury yield (FRED series DGS10) from {start} to {end}, "
            f"refreshed before each release; used because {reason}."
        ),
    )
