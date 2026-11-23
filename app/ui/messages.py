"""Customer messages: stops, header warnings, SEC errors (SPEC 2.4.1 §3, §10; issue #32 point 9). Owner: D.

All in one place until E's `texts.yaml` has keys for them. Proposed by review assistants and accepted by Simon (D)
on 23 November 2026. Each message says what happened and what to do next; numbers such as the minimum number of
fiscal years or the age limit of the annual report come from the settings, never from this file.
"""

from __future__ import annotations

from datetime import date
from typing import Mapping

from src.data.company import (InvalidCik, MissingUserAgent, NotFound, SecError, SecRefused, SourceUnreachable,
                              UnknownTicker)
from src.gates import GateResult, Stop

NEXT_AFTER_STOP = "Pick one of the five demo companies, or type another ticker."
NOT_FULLY_CHECKED = "Not fully checked: read automatically, not compared by hand for this company."
OLD_REPORT = "Latest annual report is old: filed on {filed}, more than {months} months before the data was read."
TECHNICAL_DETAILS = "Technical details"

_STOPS = {
    "industry": "Not supported: {name} is in an industry these checks do not cover (banks, insurers, real estate "
                "trusts; SEC industry code {sic}).",
    "no_annual_data": "Not supported: no annual report (10-K) figures were found for {name}.",
    "non_usd": "Not supported: {name} does not report in US dollars.",
    "too_few_years": "Not supported: {name} has fewer than {minimum} fiscal years of figures.",
}
_NOT_IN_DEMO = ("{ticker} is not one of the five saved companies. Switch demo mode off to look it up on the SEC "
                "website, or pick one of the five.")
_NOT_FOUND = "We could not find this ticker. Check the spelling, or pick one of the five demo companies."
_UNREACHABLE = ("The SEC website cannot be reached right now. Try again later, or switch on demo mode to see the five "
                "saved companies.")
_CANNOT_READ = "The app cannot read SEC data at the moment. Switch on demo mode, or try again later."


def _day(value: date) -> str:
    return f"{value.day} {value:%B %Y}"


def stop_message(stop: Stop, name: str) -> str:
    """Why the report is refused, then what to do next."""
    reason = _STOPS[stop.case].format(name=name, sic=stop.sic, minimum=stop.minimum)
    return f"{reason} {NEXT_AFTER_STOP}"


def header_warnings(result: GateResult, gates: Mapping) -> tuple[str, ...]:
    """The only two warnings shown in the header (SPEC §10); every other one is on the sources page."""
    shown = []
    if result.not_fully_checked:
        shown.append(NOT_FULLY_CHECKED)
    if result.old_report_filed is not None:
        shown.append(OLD_REPORT.format(filed=_day(result.old_report_filed), months=gates["stale_report_months"]))
    return tuple(shown)


def sec_error_message(error: SecError, ticker: str, demo: bool) -> str:
    """One sentence and a next step for the customer; the raw message goes under "Technical details"."""
    if isinstance(error, UnknownTicker) and demo:
        return _NOT_IN_DEMO.format(ticker=ticker)
    if isinstance(error, (UnknownTicker, NotFound, InvalidCik)):
        return _NOT_FOUND
    if isinstance(error, SourceUnreachable):
        return _UNREACHABLE
    if isinstance(error, (MissingUserAgent, SecRefused)):
        return _CANNOT_READ
    return _CANNOT_READ  # any other SEC error: same advice
