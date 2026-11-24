"""B's checks on the synthetic company of SPEC Appendix A (Igor's review of #28, 24 November 2026).

- P1-P6 and H1-H6 against Appendix A: value, compared-with figure and result. Skipped until B's sign-off is recorded in
  tests/fixtures/synthetic_co.yaml (rule 14.5), then they switch on by themselves.
- AC3 (tier 1: no benchmarks) and the tier 2 area score use expected_tier1() and expected_scores(), already
  signed off by Simon (D) and Emma (E) on PR #5, so they run now.
Expected values come only from the fixture, never from running the code under test.
"""
from datetime import date

import pytest

from src.checks.health import health_checks
from src.checks.past import past_checks
from src.contracts import Fact
from tests.fixtures import synthetic

MILLION = 1_000_000
P_CHECKS = ["P1", "P2", "P3", "P4", "P5", "P6"]
H_CHECKS = ["H1", "H2", "H3", "H4", "H5", "H6"]
# The fixture names the ROE benchmark return_on_equity; the benchmark CSV and the checks call it roe.
BENCHMARK_NAMES = {"roe": ("roe", "return_on_equity"), "operating_margin": ("operating_margin",)}


def benchmarks() -> dict:
    given = synthetic.inputs()["benchmarks"]
    facts = {}
    for metric, names in BENCHMARK_NAMES.items():
        value = next(given[n] for n in names if n in given)
        facts[metric] = Fact(metric, value, "pure", None, date(2026, 1, 5), "assumption", None, None, None, None,
                             None, "SYNTHETIC DATA: SPEC Appendix A benchmark")
    return facts


def settings() -> dict:
    return {"p1_min_profitable_years": 4}


def health_settings() -> dict:
    return {"max_net_debt_to_equity": 0.40, "min_operating_cash_flow_to_debt": 0.20, "min_interest_cover": 5.0}


def results(with_benchmarks: bool) -> dict:
    checks = past_checks(synthetic.company_data(), settings=settings(),
                         benchmarks=benchmarks() if with_benchmarks else None)
    checks += health_checks(synthetic.company_data(), settings=health_settings())
    return {r.check_id: r for r in checks}


def as_shown(value: float, unit: str) -> float:
    """A result in the unit Appendix A shows: USD millions, percent, or as is (years, times)."""
    return {"USD m": value / MILLION, "%": value * 100}.get(unit, value)


@pytest.mark.parametrize("check_id", P_CHECKS + H_CHECKS)
def test_appendix_a_past_performance_and_health(check_id):
    try:
        expected = synthetic.expected_check(check_id)
    except synthetic.NotSignedOff as locked:
        pytest.skip(str(locked))
    result = results(with_benchmarks=True)[check_id]
    assert result.status == expected["result"]
    tolerance = synthetic.tolerance(expected)
    assert as_shown(result.value, expected["unit"]) == pytest.approx(expected["value"], abs=tolerance)
    if "compared_with" in expected:
        assert as_shown(result.threshold, expected["unit"]) == pytest.approx(expected["compared_with"], abs=tolerance)


def test_ac3_tier_1_past_performance_score_of_the_synthetic_company():
    expected = synthetic.expected_tier1()
    checks = {c: r for c, r in results(with_benchmarks=False).items() if c.startswith("P")}
    assessed = [r for r in checks.values() if r.status in ("pass", "fail")]
    assert len(assessed) == expected["scores"]["past_performance"]["assessed"]
    assert sum(r.status == "pass" for r in assessed) == expected["scores"]["past_performance"]["passed"]
    assert [c for c, r in checks.items() if r.status == "insufficient_data"] == \
        [c for c in expected["not_assessed"] if c.startswith("P")]


def test_tier_2_past_performance_score_with_benchmarks():
    expected = synthetic.expected_scores()
    passed = sum(r.status == "pass" for c, r in results(with_benchmarks=True).items() if c.startswith("P"))
    assert passed == expected["past_performance"]


def test_ac3_tier_1_financial_health_score_of_the_synthetic_company():
    expected = synthetic.expected_tier1()["scores"]["financial_health"]
    health = [r for c, r in results(with_benchmarks=False).items() if c.startswith("H")]
    assessed = [r for r in health if r.status in ("pass", "fail")]
    assert len(assessed) == expected["assessed"]
    assert sum(r.status == "pass" for r in assessed) == expected["passed"]


def test_tier_2_financial_health_score():
    passed = sum(r.status == "pass" for c, r in results(with_benchmarks=True).items() if c.startswith("H"))
    assert passed == synthetic.expected_scores()["financial_health"]
