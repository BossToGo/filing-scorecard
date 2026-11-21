"""Shared data shapes (SPEC §11). Every area of the app passes these between each other.

Owner: A. A change here needs the approval of every owner whose code uses it (SPEC §11).

Conventions:
- Amounts are stored as filed, in US dollars (unit "USD"), never in millions; the interface converts for display.
  Share counts in "shares", per-share amounts in "USD/shares", ratios and multiples in "pure", days in "days".
- Outflows such as capital expenditure and dividends paid are stored as the positive amounts filed under the
  `PaymentsTo...` / `PaymentsOf...` tags.
- Line items use the names in `LINE_ITEMS` (SPEC §6), e.g. `data.fact("net_income", date(2025, 12, 31))`.
- A check that cannot be assessed (an input missing, or "not assessed" until tier 2, SPEC §2) has the status
  `insufficient_data` and says why in its explanation. The area score counts passes out of the checks that were
  assessed ("4 of 5 assessed, 1 with insufficient data", SPEC §3).
- The checks a missing figure blocks (SPEC §5.2) are found from the `CheckResult`s that list it as an input.

Rules built in (each one has a test in `tests/unit/test_contracts.py`):
- `missing` has no value (not even 0) and a reason. NaN and infinity are rejected, so missing data cannot hide
  inside a float.
- `reported` names its tag, form and accession number (SPEC §5.1); sources that are not SEC filings put their name
  in `form` (e.g. "SYNTHETIC"). `derived` records its formula; `assumption` says which setting or override.
- In `CompanyData`, a fact is stored under its own line item and its own period end date. (That the period end,
  not the filing's `fy` label, decides the fiscal year, SPEC §5.3.2, is the resolver's job, tested in slice S2.)
- A check with a missing input cannot pass or fail; a check that was not assessed has no value.
"""

from __future__ import annotations

import dataclasses
import math
import numbers
import re
from dataclasses import dataclass, field
from datetime import date, datetime
from typing import Literal, Mapping

Kind = Literal["reported", "derived", "assumption", "missing"]
Status = Literal["pass", "fail", "insufficient_data", "not_applicable"]

KINDS: tuple[str, ...] = ("reported", "derived", "assumption", "missing")
STATUSES: tuple[str, ...] = ("pass", "fail", "insufficient_data", "not_applicable")
CHECK_IDS: tuple[str, ...] = tuple(f"{area}{n}" for area in "PHDV" for n in range(1, 7))
UNITS: tuple[str, ...] = ("USD", "USD/shares", "shares", "pure", "days")

# Line items of SPEC §6, in its order. Add a name here (with the owners' approval) before using a new one.
LINE_ITEMS: tuple[str, ...] = (
    "revenue",
    "cost_of_revenue",
    "gross_profit",
    "operating_income",
    "net_income",
    "interest_expense",
    "depreciation_amortization",
    "total_assets",
    "current_assets",
    "current_liabilities",
    "total_liabilities",
    "equity",  # StockholdersEquity
    "total_equity",  # including non-controlling interests
    "cash",
    "financial_debt",
    "current_financial_debt",  # needed for net working capital, SPEC §8.2
    "receivables",
    "inventory",
    "payables",
    "ppe_net",
    "operating_cash_flow",
    "capital_expenditure",
    "dividends_paid",
    "shares",
    "minority_interest",
    "preferred_stock",
    "equity_method_investments",
)


def _number(value: object, what: str) -> float:
    if isinstance(value, bool) or not isinstance(value, numbers.Real):
        raise TypeError(f"{what} must be a number, got {type(value).__name__}")
    if not math.isfinite(value):
        raise ValueError(f"{what} must be finite; use kind='missing' (or no value) for an unknown figure")
    return float(value)


def _plain_date(value: object, what: str, optional: bool) -> None:
    if value is None and optional:
        return
    if not isinstance(value, date) or isinstance(value, datetime):
        raise TypeError(f"{what} must be a date (datetime.date), got {type(value).__name__}")


@dataclass(frozen=True)
class Fact:
    """One number with its source (SPEC §5.1)."""

    metric: str
    value: float | None
    unit: str
    period_start: date | None  # None for balance sheet figures (a single date)
    period_end: date
    kind: Kind
    tag: str | None
    form: str | None
    accession: str | None
    filed: date | None
    retrieved: datetime | None
    note: str = ""  # formula, reason for missing, or what was changed

    def __post_init__(self) -> None:
        if self.kind not in KINDS:
            raise ValueError(f"unknown kind {self.kind!r}; use one of {KINDS}")
        if self.unit not in UNITS:
            raise ValueError(f"unit {self.unit!r} is not allowed; amounts stay as filed, in one of {UNITS}")
        _plain_date(self.period_end, "period_end", optional=False)
        _plain_date(self.period_start, "period_start", optional=True)
        _plain_date(self.filed, "filed", optional=True)
        if self.retrieved is not None and not isinstance(self.retrieved, datetime):
            raise TypeError(f"retrieved must be a datetime, got {type(self.retrieved).__name__}")
        if self.period_start is not None and self.period_start > self.period_end:
            raise ValueError(f"the period starts ({self.period_start}) after it ends ({self.period_end})")

        if self.kind == "missing":
            if self.value is not None:
                raise ValueError("a missing figure has no value: never zero, never guessed (SPEC §5.2)")
            if not self.note.strip():
                raise ValueError("a missing figure needs a reason in `note` (SPEC §5.2)")
            return
        if self.value is None:
            raise ValueError(f"a {self.kind} figure needs a value; use kind='missing' with a reason")
        object.__setattr__(self, "value", _number(self.value, "value"))
        if self.kind == "reported":
            for name in ("tag", "form", "accession"):
                if not getattr(self, name):
                    raise ValueError(f"a reported figure names its {name} (SPEC §5.1)")
        if self.kind == "derived" and not self.note.strip():
            raise ValueError("a derived figure records its formula in `note` (SPEC §5.2)")
        if self.kind == "assumption" and not self.note.strip():
            raise ValueError("an assumption says in `note` which setting or override it comes from (SPEC §5.2)")


@dataclass(frozen=True)
class CheckResult:
    """The result of one of the 24 checks (SPEC §7)."""

    check_id: str  # "P1" ... "V6"
    status: Status
    value: float | None
    threshold: float | None
    inputs: tuple[Fact, ...]
    explanation: str

    def __post_init__(self) -> None:
        if self.check_id not in CHECK_IDS:
            raise ValueError(f"unknown check id {self.check_id!r}; use one of P1–P6, H1–H6, D1–D6, V1–V6")
        if self.status not in STATUSES:
            raise ValueError(f"unknown status {self.status!r}; use one of {STATUSES}")
        inputs = tuple(self.inputs)
        if not all(isinstance(item, Fact) for item in inputs):
            raise TypeError("inputs must be Fact objects, so every input keeps its source")
        object.__setattr__(self, "inputs", inputs)
        for name in ("value", "threshold"):
            if getattr(self, name) is not None:
                object.__setattr__(self, name, _number(getattr(self, name), name))
        if self.status in ("pass", "fail") and any(item.kind == "missing" for item in inputs):
            raise ValueError("an input is missing, so the status is insufficient_data, not pass or fail (SPEC §7)")
        if self.status in ("insufficient_data", "not_applicable") and self.value is not None:
            raise ValueError(f"a check with status {self.status} was not assessed, so it has no value")
        if not self.explanation.strip():
            raise ValueError("a check result needs an explanation in plain words")


class _ReadOnlyDict(dict):
    """A dict that cannot be changed after it is made. Unlike MappingProxyType it can be pickled (Streamlit's
    cache), deep-copied and turned into a plain dict by dataclasses.asdict (export, sources page)."""

    def _read_only(self, *args, **kwargs):
        raise TypeError("CompanyData is read-only; use with_fact() for an override")

    __setitem__ = __delitem__ = __ior__ = _read_only
    clear = pop = popitem = setdefault = update = _read_only

    def __reduce__(self):
        return (type(self), (dict(self),))


def _freeze(items: Mapping[str, Mapping[date, Fact]]) -> _ReadOnlyDict:
    frozen = {}
    for metric, by_year in items.items():
        if metric not in LINE_ITEMS:
            raise ValueError(f"unknown line item {metric!r}; use one of LINE_ITEMS in src/contracts.py")
        for fy_end, fact in by_year.items():
            if fact.metric != metric:
                raise ValueError(f"a {fact.metric!r} fact is stored under the line item {metric!r}")
            if fact.period_end != fy_end:
                raise ValueError(
                    f"{metric}: a fact ending {fact.period_end} is stored under fiscal year end {fy_end}; "
                    "the key must be the fact's own period end date"
                )
        frozen[metric] = _ReadOnlyDict(by_year)
    return _ReadOnlyDict(frozen)


@dataclass(frozen=True)
class CompanyData:
    """Header fields plus, per line item, a mapping from fiscal-year end date to `Fact` (SPEC §11)."""

    ticker: str
    cik: str  # SEC company number, 10 digits with leading zeros
    name: str
    sic: str | None  # SEC industry code
    sic_description: str | None
    fiscal_year_end: str | None  # "MMDD", as in the SEC submissions file
    latest_10k_filed: date | None
    retrieved: datetime | None
    items: Mapping[str, Mapping[date, Fact]] = field(default_factory=dict)
    warnings: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if not re.fullmatch(r"\d{10}", self.cik):
            raise ValueError(f"the SEC company number must be 10 digits with leading zeros, got {self.cik!r}")
        object.__setattr__(self, "items", _freeze(self.items))
        object.__setattr__(self, "warnings", tuple(self.warnings))

    def fact(self, metric: str, fy_end: date) -> Fact | None:
        """The fact for one line item and fiscal-year end date, or None if the year is not there at all."""
        return self.items.get(metric, {}).get(fy_end)

    def fiscal_years(self, metric: str) -> list[date]:
        """Fiscal-year end dates available for a line item, oldest first."""
        return sorted(self.items.get(metric, {}))

    def latest(self, metric: str) -> Fact | None:
        """The fact at the latest date of a line item, or None. Use it for `shares`, which are stored at the date
        of the cover page of the latest annual report, a few weeks after the fiscal year end."""
        years = self.fiscal_years(metric)
        return self.items[metric][years[-1]] if years else None

    def with_fact(self, fact: Fact) -> CompanyData:
        """A copy with one fact added or replaced (for user overrides); the original is unchanged."""
        items = {metric: dict(by_year) for metric, by_year in self.items.items()}
        items.setdefault(fact.metric, {})[fact.period_end] = fact
        return dataclasses.replace(self, items=items)
