"""Area scores (`app/src/scores.py`, SPEC 2.4.1 §7; slice S10). Owner: D.

The area score is the number of passes, always with the number assessed; `not_applicable` and `insufficient_data`
are not assessed (SPEC §3, §7).

Expected values are Simon's (D), from his AC3 sign-off on the synthetic company (SPEC Appendix A, no share price,
no benchmarks): https://github.com/BossToGo/filing-scorecard/pull/5#pullrequestreview-5977120036
and from SPEC §3 for a company without a dividend ("0 of 1 assessed"). The check results below are built by hand
with those statuses and no value, so no expected value of another owner is used.
"""

import pytest

from src.contracts import CheckResult
from src.scores import AreaScore, NotAssessed, area_score, dividend_note, not_assessed


def results(statuses: dict[str, str]) -> tuple[CheckResult, ...]:
    return tuple(CheckResult(cid, status, None, None, (), f"{cid}: hand-built for the test")
                 for cid, status in statuses.items())


# AC3 statuses, from Simon's sign-off
PAST = results({"P1": "pass", "P2": "pass", "P3": "pass", "P4": "insufficient_data", "P5": "insufficient_data",
                "P6": "pass"})
HEALTH = results({"H1": "pass", "H2": "fail", "H3": "fail", "H4": "pass", "H5": "pass", "H6": "pass"})
DIVIDEND = results({"D1": "pass", "D2": "insufficient_data", "D3": "pass", "D4": "pass", "D5": "pass",
                    "D6": "pass"})
# SPEC §3: no dividend -> D1 failed, D2 to D6 not applicable
NO_DIVIDEND_PAID = results({"D1": "fail", **{f"D{n}": "not_applicable" for n in range(2, 7)}})


def test_synthetic_company_past_performance_4_passed_of_4_assessed():
    assert area_score(PAST) == AreaScore(passed=4, assessed=4)


def test_synthetic_company_financial_health_4_passed_of_6_assessed():
    assert area_score(HEALTH) == AreaScore(passed=4, assessed=6)


def test_synthetic_company_dividend_5_passed_of_5_assessed():
    assert area_score(DIVIDEND) == AreaScore(passed=5, assessed=5)


def test_no_dividend_paid_is_0_passed_of_1_assessed():
    assert area_score(NO_DIVIDEND_PAID) == AreaScore(passed=0, assessed=1)


@pytest.mark.parametrize("status", ["insufficient_data", "not_applicable"])
def test_an_area_with_nothing_assessed_is_0_passed_of_0_assessed(status):
    assert area_score(results({f"V{n}": status for n in range(1, 7)})) == AreaScore(passed=0, assessed=0)


def test_a_paying_company_has_no_dividend_note():
    assert dividend_note(DIVIDEND) is None


def test_other_areas_have_no_dividend_note():
    assert dividend_note(HEALTH) is None


def test_no_dividend_note_comes_from_the_dividend_module():
    dividend = pytest.importorskip("src.checks.dividend", reason="C's dividend module (PR #23) is not on main yet")
    assert dividend_note(NO_DIVIDEND_PAID) == dividend.NO_DIVIDEND


def test_amazon_through_the_real_dividend_module_reads_no_dividend_paid():
    """The note's pattern must stay the one C's module returns for a non-payer (plan Q1, SPEC §7)."""
    dividend = pytest.importorskip("src.checks.dividend", reason="C's dividend module (PR #23) is not on main yet")
    from src.data.company import load_company
    from src.settings import load_settings

    amazon = dividend.dividend_checks(load_company("AMZN", demo=True), load_settings())
    assert area_score(amazon) == AreaScore(passed=0, assessed=1)
    assert dividend_note(amazon) == "no dividend paid"


# --- "not assessed" and "not assessed yet" (SPEC 2.4.2 §3; design spec §3) ---------------------------------------
# Counts: Simon's hand count of 25 November 2026 from the AC3 statuses (past 2: P4, P5; health 0; dividend 1: D2)
# and for Amazon (0). "yet" only when the check's own explanation says so (agreed with Igor on #39).


def test_synthetic_company_not_assessed_counts():
    assert not_assessed(PAST) == NotAssessed(count=2, yet=False)
    assert not_assessed(HEALTH) == NotAssessed(count=0, yet=False)
    assert not_assessed(DIVIDEND) == NotAssessed(count=1, yet=False)


def test_does_not_apply_is_not_counted_as_not_assessed():
    assert not_assessed(NO_DIVIDEND_PAID) == NotAssessed(count=0, yet=False)


def explained(cid: str, explanation: str) -> CheckResult:
    return CheckResult(cid, "insufficient_data", None, None, (), explanation)


def test_yet_when_every_not_assessed_check_says_a_later_version_brings_its_input():
    """C's D2 wording (`src/checks/dividend.py`)."""
    d2 = explained("D2", "This check is not assessed yet: it needs the share price and the US market dividend yield.")
    assert not_assessed((*DIVIDEND[:1], d2, *DIVIDEND[2:])) == NotAssessed(count=1, yet=True)


def test_no_yet_when_the_explanation_does_not_say_it():
    """Greg's current P4 wording: no "yet" until his module says so (Simon, 25 November 2026)."""
    p4 = explained("P4", "Not assessed: needs a sourced industry return on equity benchmark.")
    p5 = explained("P5", "Not assessed yet: needs a sourced industry operating margin benchmark.")
    assert not_assessed((p4, p5)) == NotAssessed(count=2, yet=False)


def test_amazon_through_the_real_dividend_module_has_nothing_not_assessed():
    dividend = pytest.importorskip("src.checks.dividend", reason="C's dividend module (PR #23) is not on main yet")
    from src.data.company import load_company
    from src.settings import load_settings

    amazon = dividend.dividend_checks(load_company("AMZN", demo=True), load_settings())
    assert not_assessed(amazon) == NotAssessed(count=0, yet=False)
