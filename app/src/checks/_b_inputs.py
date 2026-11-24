"""Input and result helpers for B's P/H checks. Pure: no files or network.

Fiscal-year offsets are distances in annual periods, not positions in a shortened list.
A missing year is never replaced by the next available year. The 350–380-day annual
window is the resolver's SPEC §5.3 convention; its multiples allow 52/53-week calendars.
"""
from __future__ import annotations

import math
from datetime import date
from fractions import Fraction

from src.contracts import CheckResult, CompanyData, Fact

FLOWS = {"revenue", "net_income", "operating_income", "operating_cash_flow", "interest_expense"}


def rational(value: float) -> Fraction:
    """Compare a stored decimal number exactly, without its binary floating-point residue."""
    return Fraction(str(value))


def money(value: float) -> str:
    """Readable USD millions; keep extremely small nonzero values visible."""
    millions = value / 1_000_000
    return f"USD {millions:,.6g} million" if millions or value == 0 else f"USD {value:g}"


def day(value: date) -> str:
    return value.strftime("%d %B %Y")


class Inputs:
    def __init__(self, data: CompanyData):
        self.data = data
        self.ends = sorted({end for metric, rows in data.items.items() if metric != "shares" for end in rows})
        self.latest = self.ends[-1] if self.ends else None

    def end(self, offset: int) -> date | None:
        if self.latest is None:
            return None
        if offset == 0:
            return self.latest
        candidates = [d for d in self.ends if 350 * offset <= (self.latest - d).days <= 380 * offset]
        return candidates[0] if len(candidates) == 1 else None

    def fact(self, metric: str, offset: int = 0) -> Fact:
        end = self.end(offset)
        fact = self.data.fact(metric, end) if end is not None else None
        if fact is None:
            return Fact(metric, None, "USD", None, end or self.latest or date.min, "missing", None,
                        None, None, None, None, f"Missing {metric.replace('_', ' ')} for the required fiscal year.")
        if fact.kind == "missing":
            return fact
        invalid = None
        if fact.unit != "USD":
            invalid = f"{metric} must be in USD as filed, not {fact.unit}."
        elif metric in FLOWS and (fact.period_start is None or
                                 not 350 <= (fact.period_end - fact.period_start).days <= 380):
            invalid = f"{metric} must cover one annual period (350–380 days)."
        if invalid:
            from dataclasses import replace
            return replace(fact, value=None, kind="missing", note=f"{invalid} {fact.note}")
        return fact


def unavailable(check: str, facts: tuple[Fact, ...], reason: str) -> CheckResult:
    gaps = ", ".join(dict.fromkeys(f.metric.replace("_", " ") for f in facts if f.kind == "missing"))
    if gaps:
        gaps = f"Unavailable figures: {gaps}. See their source notes for details."
    return CheckResult(check, "insufficient_data", None, None, facts, f"{reason} {gaps}".strip())


def missing(facts: tuple[Fact, ...]) -> bool:
    return any(f.kind == "missing" for f in facts)


def result(check: str, passed: bool, value: float | None, threshold: float | None,
           facts: tuple[Fact, ...], explanation: str) -> CheckResult:
    if any(v is not None and not math.isfinite(v) for v in (value, threshold)):
        return unavailable(check, facts, "The calculation exceeds the supported finite numeric range.")
    return CheckResult(check, "pass" if passed else "fail", value, threshold, facts, explanation)
