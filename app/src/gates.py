"""Data-quality gates: stop, or warn the customer in the header (SPEC 2.4.1 §10). Owner: D.

    from src.gates import check_gates
    result = check_gates(data, load_settings()["gates"], DEMO_TICKERS)
    result.stop                 # None, or Stop("industry", sic=6021)
    result.not_fully_checked    # True for any ticker other than the five demo companies
    result.old_report_filed     # None, or the filing date of a latest 10-K that is too old

Logic only: it reads `CompanyData`, the `gates` settings and the demo tickers passed in by `main.py`; it imports
neither the data layer nor the interface, and holds no text for the customer (`app/ui/messages.py` does). Every
other warning of `data.warnings` is recorded on the sources page, not here.
"""

from __future__ import annotations

import calendar
from dataclasses import dataclass
from datetime import date, timezone
from typing import Collection, Literal, Mapping

from src.contracts import CompanyData

StopCase = Literal["industry", "no_annual_data", "non_usd", "too_few_years"]
NO_ANNUAL_DATA = "NO_ANNUAL_DATA:"
# The resolver's company-wide currency warning; a NON_USD warning about one figure does not stop the report.
# A separate warning code from the data layer would be safer than reading this text (asked to A in the S11 PR).
COMPANY_WIDE_NON_USD = "NON_USD: the company files its annual figures in "


@dataclass(frozen=True)
class Stop:
    case: StopCase
    sic: int | None = None  # the SEC industry code, for "industry"
    years: int | None = None  # fiscal years found, for "too_few_years"
    minimum: int | None = None  # the setting min_fiscal_years, for "too_few_years"


@dataclass(frozen=True)
class GateResult:
    stop: Stop | None
    not_fully_checked: bool
    old_report_filed: date | None


def add_months(day: date, months: int) -> date:
    """The same day `months` later, or the last day of that month when the day does not exist."""
    index = day.month - 1 + months
    year, month = day.year + index // 12, index % 12 + 1
    return date(year, month, min(day.day, calendar.monthrange(year, month)[1]))


def _sic(data: CompanyData) -> int | None:
    code = (data.sic or "").strip()
    return int(code) if code.isdigit() else None  # empty or not a number: treated as no code


def _stop(data: CompanyData, gates: Mapping) -> Stop | None:
    sic = _sic(data)
    if sic is not None and gates["unsupported_sic_min"] <= sic <= gates["unsupported_sic_max"]:
        return Stop("industry", sic=sic)
    if any(w.startswith(NO_ANNUAL_DATA) for w in data.warnings):
        return Stop("no_annual_data")
    if any(w.startswith(COMPANY_WIDE_NON_USD) for w in data.warnings):
        return Stop("non_usd")
    years = len(data.fiscal_years("revenue"))
    if years < gates["min_fiscal_years"]:
        return Stop("too_few_years", years=years, minimum=gates["min_fiscal_years"])
    return None


def _old_report(data: CompanyData, gates: Mapping) -> date | None:
    filed, read = data.latest_10k_filed, data.retrieved
    if filed is None or read is None:
        return None
    read_day = read.date() if read.tzinfo is None else read.astimezone(timezone.utc).date()
    return filed if read_day > add_months(filed, gates["stale_report_months"]) else None


def check_gates(data: CompanyData, gates: Mapping, demo_tickers: Collection[str]) -> GateResult:
    """Stop, header warnings, in the order of SPEC §10 and Simon's decisions of 23 November 2026."""
    return GateResult(
        stop=_stop(data, gates),
        not_fully_checked=data.ticker not in demo_tickers,
        old_report_filed=_old_report(data, gates),
    )

