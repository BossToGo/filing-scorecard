"""The one place where the interface gets check results (`app/ui/results.py`, slice S10). Owner: D.

Until Greg's and Flo's check modules are merged, their area is `None` ("not assessed" on screen); the interface
never invents a `CheckResult`. A bug inside a check module is never hidden as "not merged yet".
"""

import pytest

from src.contracts import CheckResult
from tests.fixtures import synthetic
from ui import results
from ui.results import AREA_CHECKS, AREAS, check_results


def six(area, status="pass"):
    return tuple(CheckResult(cid, status, None, None, (), "test result") for cid in AREA_CHECKS[area])


def test_four_areas_with_six_checks_each_in_spec_order():
    assert AREAS == ("past_performance", "financial_health", "dividend", "valuation")
    assert AREA_CHECKS["past_performance"] == ("P1", "P2", "P3", "P4", "P5", "P6")
    assert AREA_CHECKS["valuation"] == ("V1", "V2", "V3", "V4", "V5", "V6")


def test_today_each_area_is_either_not_merged_or_six_results_in_order():
    found = check_results(synthetic.company_data())
    assert set(found) == set(AREAS)
    for area, area_results in found.items():
        assert area_results is None or tuple(r.check_id for r in area_results) == AREA_CHECKS[area]


def test_valuation_gives_v1_to_v6_in_order():
    """Test change (rule 14.6, Simon's written agreement of 26 November 2026): this test asserted that valuation is
    `None` in v0.1 ("test_valuation_is_not_assessed_in_v0_1"). S10b switches on C's V1-V6 (merged in #52), so the
    area now gives its six results in order; no score, count or figure changed."""
    found = check_results(synthetic.company_data())["valuation"]
    assert tuple(r.check_id for r in found) == AREA_CHECKS["valuation"]


def test_a_module_not_on_main_yet_gives_none(monkeypatch):
    # Test change (rule 14.6, Simon's written agreement of 26 November 2026): the area functions take a third
    # argument, the market inputs (share price, benchmarks, risk-free rate, valuation; S10b); nothing else changed.
    def not_merged(data, settings, market):
        raise ModuleNotFoundError("No module named 'src.checks.past'", name="src.checks.past")

    monkeypatch.setitem(results.PROVIDERS, "past_performance", not_merged)
    assert check_results(synthetic.company_data())["past_performance"] is None


def test_a_missing_library_inside_a_check_module_is_not_hidden(monkeypatch):
    # Test change (rule 14.6, Simon's written agreement of 26 November 2026): the area functions take a third
    # argument, the market inputs (share price, benchmarks, risk-free rate, valuation; S10b); nothing else changed.
    def broken(data, settings, market):
        raise ModuleNotFoundError("No module named 'numpy'", name="numpy")

    monkeypatch.setitem(results.PROVIDERS, "past_performance", broken)
    with pytest.raises(ModuleNotFoundError):
        check_results(synthetic.company_data())


def test_results_from_a_module_are_passed_on_unchanged(monkeypatch):
    given = six("dividend", "not_applicable")
    # Test change (rule 14.6, Simon's written agreement of 26 November 2026): the area functions take a third
    # argument, the market inputs (share price, benchmarks, risk-free rate, valuation; S10b); nothing else changed.
    monkeypatch.setitem(results.PROVIDERS, "dividend", lambda data, settings, market: given)
    assert check_results(synthetic.company_data())["dividend"] is given


def test_wrong_check_ids_from_a_module_are_refused(monkeypatch):
    # Test change (rule 14.6, Simon's written agreement of 26 November 2026): the area functions take a third
    # argument, the market inputs (share price, benchmarks, risk-free rate, valuation; S10b); nothing else changed.
    monkeypatch.setitem(results.PROVIDERS, "financial_health", lambda data, settings, market: six("past_performance"))
    with pytest.raises(ValueError, match="financial_health"):
        check_results(synthetic.company_data())


# --- S10b: one run with the share price, the benchmarks and the risk-free rate (tier 2) ------------------------------
# Expected values only from the signed-off synthetic company: synthetic.expected_check (B for P, C for D and V),
# expected_valuation (C) and expected_scores (E). The inputs are in tests/app/synthetic_market.py.

from tests.app import synthetic_market  # noqa: E402
from ui.results import run_checks  # noqa: E402


def tier2(price=synthetic_market.PRICE):
    return run_checks(synthetic.company_data(), price, demo=True, benchmarks=synthetic_market.benchmarks(),
                      risk_free=synthetic_market.risk_free())


def by_id(run):
    return {r.check_id: r for area in run.results.values() for r in (area or ())}


def test_ac8_p4_p5_and_d2_get_the_benchmarks_and_the_price():
    found = by_id(tier2())
    for check_id in ("P4", "P5", "D2"):
        expected = synthetic.expected_check(check_id)
        assert found[check_id].status == expected["result"], check_id


def test_ac9_the_estimate_and_the_four_scores():
    from src.scores import area_score

    run = tier2()
    expected = synthetic.expected_valuation("fair_value_per_share")
    assert run.market.valuation.status == "ok"
    assert abs(run.market.valuation.fair_value.value - expected["value"]) <= synthetic.tolerance(expected)
    for area, passed in synthetic.expected_scores().items():
        assert area_score(run.results[area]).passed == passed, area


def test_the_checks_use_the_same_valuation_as_the_detail():
    run = tier2()
    v1 = by_id(run)["V1"]
    assert run.market.valuation.fair_value in v1.inputs or v1.threshold == run.market.valuation.fair_value.value


def test_ac10_without_a_share_price_the_whole_valuation_area_is_insufficient_data():
    run = tier2(price=None)
    assert [r.status for r in run.results["valuation"]] == ["insufficient_data"] * 6
    assert run.market.price is None
