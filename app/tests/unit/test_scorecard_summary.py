"""The scorecard panel of the overview: totals, the share per area for the radar, checks by area (slice S10c).
Owner: A.

Expected values: the synthetic company's tier 1 scores and not-assessed checks of SPEC Appendix A
(`expected_tier1`, signed off by Simon and Emma on PR #5) and the AC3 statuses; the totals are those counts added
by hand (4 + 4 + 5 = 13 passed of 4 + 6 + 5 = 15 assessed). Never from running `src.overview`.
"""

from src.contracts import CheckResult
from src.data.company import load_company
from src.overview import scorecard
from tests.fixtures import synthetic

AC3 = {  # SPEC Appendix A tier 1 statuses (Simon's AC3 sign-off), valuation not part of tier 1
    "past_performance": ["pass", "pass", "pass", "insufficient_data", "insufficient_data", "pass"],
    "financial_health": ["pass", "fail", "fail", "pass", "pass", "pass"],
    "dividend": ["pass", "insufficient_data", "pass", "pass", "pass", "pass"],
}
LETTERS = {"past_performance": "P", "financial_health": "H", "dividend": "D", "valuation": "V"}


def results(statuses: dict) -> dict:
    out = {area: None for area in LETTERS}
    for area, area_statuses in statuses.items():
        out[area] = tuple(CheckResult(f"{LETTERS[area]}{n}", s, None, None, (), f"{s} (built by hand)")
                          for n, s in enumerate(area_statuses, start=1))
    return out


def by_area(card) -> dict:
    return {a.area: a for a in card.areas}


def test_the_synthetic_company_matches_the_signed_off_tier_1_scores():
    card = scorecard(results(AC3))
    expected = synthetic.expected_tier1()["scores"]
    for area, score in expected.items():
        assert (by_area(card)[area].passed, by_area(card)[area].assessed) == (score["passed"], score["assessed"])


def test_totals_add_the_areas():
    card = scorecard(results(AC3))
    assert (card.passed, card.assessed, card.failed, card.not_assessed) == (13, 15, 2, 9)  # 3 waiting + valuation's 6
    assert card.headline == ("13", "15")


def test_the_share_of_assessed_checks_passed_per_area_for_the_radar():
    areas = by_area(scorecard(results(AC3)))
    assert [a.label for a in areas.values()] == ["Past performance", "Financial health", "Dividend", "Valuation"]
    assert areas["past_performance"].share == 1.0 and areas["past_performance"].share_text == "100%"
    assert areas["financial_health"].share_text == "67%"  # 4 ÷ 6
    assert (areas["valuation"].share, areas["valuation"].share_text) == (None, "Not assessed")


def test_the_area_to_read_first_is_the_weakest_assessed_one():
    card = scorecard(results(AC3))
    assert card.focus.area == "financial_health"
    assert card.focus.count_text == "4 passed of 6 assessed"


def test_each_area_lists_its_six_marks_in_order():
    areas = by_area(scorecard(results(AC3)))
    assert areas["financial_health"].marks == ("pass", "fail", "fail", "pass", "pass", "pass")
    assert areas["dividend"].marks[1] == "not_assessed"
    assert areas["valuation"].marks == ("not_assessed",) * 6
    assert areas["valuation"].count_text == "Not assessed"


def test_no_dividend_counts_one_assessed_check_and_five_that_do_not_apply():
    statuses = dict(AC3, dividend=["fail"] + ["not_applicable"] * 5)
    dividend = by_area(scorecard(results(statuses)))["dividend"]
    assert (dividend.passed, dividend.assessed, dividend.share_text) == (0, 1, "0%")
    assert dividend.marks == ("fail",) + ("not_applicable",) * 5
    assert dividend.count_text == "No dividend paid · 0 passed of 1 assessed"


def test_an_area_with_nothing_assessed_is_left_off_the_radar_and_the_focus():
    statuses = dict(AC3, financial_health=["insufficient_data"] * 6)
    card = scorecard(results(statuses))
    health = by_area(card)["financial_health"]
    assert (health.share, health.share_text, health.count_text) == (None, "Not assessed", "Not assessed")
    assert card.focus.area != "financial_health"


def test_nothing_assessed_at_all_has_no_headline_number():
    card = scorecard(results({area: ["insufficient_data"] * 6 for area in AC3}))
    assert card.assessed == 0 and card.headline is None and card.focus is None


def test_coca_cola_totals_equal_a_count_of_its_check_results():
    from ui.results import check_results

    checks = check_results(load_company("KO", demo=True))
    statuses = [r.status for area in checks.values() if area for r in area]
    card = scorecard(checks)
    assert card.passed == statuses.count("pass")
    assert card.failed == statuses.count("fail")
    assert card.assessed == statuses.count("pass") + statuses.count("fail")
    assert card.not_assessed == statuses.count("insufficient_data") + 6 * sum(1 for a in checks.values() if a is None)


def test_the_short_counts_of_igors_design():
    areas = by_area(scorecard(results(AC3)))
    assert areas["financial_health"].short_text == "4 of 6 passed"
    assert areas["financial_health"].focus_text == "4 of 6 checks passed"
    assert areas["valuation"].short_text == "Not assessed"

