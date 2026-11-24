"""Area scores: passes out of the checks assessed (SPEC 2.4.1 §3, §7). Owner: D.

    from src.scores import area_score, dividend_note
    score = area_score(results)        # AreaScore(passed=4, assessed=6)
    note = dividend_note(results)      # "no dividend paid" or None

Logic only: it reads `CheckResult`s and imports neither the data layer nor the interface. `not_applicable` and
`insufficient_data` are not assessed, so a company without a dividend scores 0 passed of 1 assessed (SPEC §3).
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Sequence

from src.contracts import CheckResult

ASSESSED = ("pass", "fail")
_NO_DIVIDEND = {"D1": "fail", **{f"D{n}": "not_applicable" for n in range(2, 7)}}


@dataclass(frozen=True)
class AreaScore:
    passed: int
    assessed: int


def area_score(results: Sequence[CheckResult]) -> AreaScore:
    """Number of passes and number assessed (pass or fail) in one area."""
    return AreaScore(
        passed=sum(r.status == "pass" for r in results),
        assessed=sum(r.status in ASSESSED for r in results),
    )


def dividend_note(results: Sequence[CheckResult]) -> str | None:
    """The dividend module's own "no dividend paid" text when it returned D1 failed and D2 to D6 not applicable.

    The text is C's (`src.checks.dividend.NO_DIVIDEND`), never written here; it is imported only when the pattern
    is found, which cannot happen before C's module returns results (SPEC §7)."""
    if {r.check_id: r.status for r in results} != _NO_DIVIDEND:
        return None
    from src.checks.dividend import NO_DIVIDEND

    return NO_DIVIDEND
