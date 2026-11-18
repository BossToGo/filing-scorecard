"""Shared data shapes (SPEC §11). Every area of the app passes these between each other.

Owner: A. A change here needs the approval of every owner whose code uses it (SPEC §11).

The rules built in (each one has a test in `tests/unit/test_contracts.py`):
- A `Fact` is one number with its source (SPEC §5.1) and one of four kinds (SPEC §5.2).
- `missing` has no value and a reason: never zero, never guessed. NaN and infinity are rejected, so missing data
  cannot hide inside a float.
- `derived` records its formula, `assumption` says which setting or override it comes from, `reported` names
  its XBRL tag.
- In `CompanyData`, a fact is stored under its own line item and its own period end date, so a figure with the
  wrong fiscal-year label cannot be filed under another year (SPEC §5.3.2).
"""

from __future__ import annotations

import dataclasses
import math
import re
from dataclasses import dataclass, field
from datetime import date, datetime
from types import MappingProxyType
from typing import Literal, Mapping

Kind = Literal["reported", "derived", "assumption", "missing"]
Status = Literal["pass", "fail", "insufficient_data", "not_applicable"]

KINDS: tuple[str, ...] = ("reported", "derived", "assumption", "missing")
STATUSES: tuple[str, ...] = ("pass", "fail", "insufficient_data", "not_applicable")
CHECK_IDS: tuple[str, ...] = tuple(f"{area}{n}" for area in "PHDV" for n in range(1, 7))


@dataclass(frozen=True)
class Fact:
    """One number with its source (SPEC §5.1). Amounts in `unit` exactly as filed (e.g. "USD", not USD m)."""

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
        if self.kind == "missing":
            if self.value is not None:
                raise ValueError("a missing figure has no value: never zero, never guessed (SPEC §5.2)")
            if not self.note.strip():
                raise ValueError("a missing figure needs a reason in `note` (SPEC §5.2)")
        else:
            if self.value is None:
                raise ValueError(f"a {self.kind} figure needs a value; use kind='missing' with a reason")
            if isinstance(self.value, bool) or not isinstance(self.value, (int, float)):
                raise TypeError(f"value must be a number, got {type(self.value).__name__}")
            if not math.isfinite(self.value):
                raise ValueError("value must be finite; use kind='missing' for an unknown figure")
            object.__setattr__(self, "value", float(self.value))
        if self.kind == "reported" and not self.tag:
            raise ValueError("a reported figure names the tag it was copied from (SPEC §5.2)")
        if self.kind == "derived" and not self.note.strip():
            raise ValueError("a derived figure records its formula in `note` (SPEC §5.2)")
        if self.kind == "assumption" and not self.note.strip():
            raise ValueError("an assumption says in `note` which setting or override it comes from (SPEC §5.2)")
        if self.period_start is not None and self.period_start > self.period_end:
            raise ValueError(f"the period starts ({self.period_start}) after it ends ({self.period_end})")


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
        if not self.explanation.strip():
            raise ValueError("a check result needs an explanation in plain words")


def _freeze(items: Mapping[str, Mapping[date, Fact]]) -> Mapping[str, Mapping[date, Fact]]:
    frozen = {}
    for metric, by_year in items.items():
        for fy_end, fact in by_year.items():
            if fact.metric != metric:
                raise ValueError(f"a {fact.metric!r} fact is stored under the line item {metric!r}")
            if fact.period_end != fy_end:
                raise ValueError(
                    f"{metric}: a fact ending {fact.period_end} is stored under fiscal year end {fy_end}; "
                    "the fiscal year comes from the period end date (SPEC §5.3.2)"
                )
        frozen[metric] = MappingProxyType(dict(by_year))
    return MappingProxyType(frozen)


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

    def with_fact(self, fact: Fact) -> CompanyData:
        """A copy with one fact added or replaced (for user overrides); the original is unchanged."""
        items = {metric: dict(by_year) for metric, by_year in self.items.items()}
        items.setdefault(fact.metric, {})[fact.period_end] = fact
        return dataclasses.replace(self, items=items)
