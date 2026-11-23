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


def test_valuation_is_not_assessed_in_v0_1():
    assert check_results(synthetic.company_data())["valuation"] is None


def test_a_module_not_on_main_yet_gives_none(monkeypatch):
    def not_merged(data, settings):
        raise ModuleNotFoundError("No module named 'src.checks.past'", name="src.checks.past")

    monkeypatch.setitem(results.PROVIDERS, "past_performance", not_merged)
    assert check_results(synthetic.company_data())["past_performance"] is None


def test_a_missing_library_inside_a_check_module_is_not_hidden(monkeypatch):
    def broken(data, settings):
        raise ModuleNotFoundError("No module named 'numpy'", name="numpy")

    monkeypatch.setitem(results.PROVIDERS, "past_performance", broken)
    with pytest.raises(ModuleNotFoundError):
        check_results(synthetic.company_data())


def test_results_from_a_module_are_passed_on_unchanged(monkeypatch):
    given = six("dividend", "not_applicable")
    monkeypatch.setitem(results.PROVIDERS, "dividend", lambda data, settings: given)
    assert check_results(synthetic.company_data())["dividend"] is given


def test_wrong_check_ids_from_a_module_are_refused(monkeypatch):
    monkeypatch.setitem(results.PROVIDERS, "financial_health", lambda data, settings: six("past_performance"))
    with pytest.raises(ValueError, match="financial_health"):
        check_results(synthetic.company_data())
