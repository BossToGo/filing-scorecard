"""The scorecard panel of the overview: the radar of the four areas and the checks by area (slice S10c). Owner: A.

Expected values: the synthetic company's tier 1 scores and not-assessed checks of SPEC Appendix A
(`expected_tier1`, signed off by Simon and Emma on PR #5) and the AC3 statuses. Never from running `src.overview`.

The total and the area to read first are out (the group's answers on #60, 26 November), so their tests went with them
(rule 14.6, agreed by Igor). The radar is back at Igor's request of 26 November, with Flo's two cases fixed: an area
with a check that does not apply stays off the shape.
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


def test_the_four_areas_in_order_and_valuation_not_part_of_this_version():
    areas = by_area(scorecard(results(AC3)))
    assert [a.label for a in areas.values()] == ["Past performance", "Financial health", "Dividend", "Valuation"]
    assert areas["financial_health"].short_text == "4 passed of 6 assessed"
    assert areas["valuation"].short_text == "Not part of this version"


def test_the_share_of_assessed_checks_passed_per_area_for_the_radar():
    areas = by_area(scorecard(results(AC3)))
    assert (areas["past_performance"].share, areas["past_performance"].share_text) == (1.0, "100%")  # 4 ÷ 4
    assert areas["financial_health"].share_text == "67%"  # 4 ÷ 6 = 0.667
    assert (areas["dividend"].share, areas["dividend"].share_text) == (1.0, "100%")  # 5 ÷ 5
    assert (areas["valuation"].share, areas["valuation"].share_text) == (None, "Not part of this version")


def test_an_area_with_a_check_that_does_not_apply_stays_off_the_radar():
    # Flo's two cases on #60: no dividend, and a valuation without an estimate (V1, V2, V6 do not apply), are the only
    # checks that return "does not apply"; a share there would read as 0% or 100% and mislead
    statuses = dict(AC3, dividend=["fail"] + ["not_applicable"] * 5,
                    valuation=["not_applicable", "not_applicable", "pass", "pass", "pass", "not_applicable"])
    areas = by_area(scorecard(results(statuses)))
    assert (areas["dividend"].share, areas["dividend"].share_text) == (None, "No dividend paid")
    assert (areas["valuation"].share, areas["valuation"].share_text) == (None, "3 passed of 3 assessed")


def test_there_is_no_total_and_no_area_to_read_first():
    # was `test_totals_add_the_areas` and `test_the_area_to_read_first_is_the_weakest_assessed_one`: both taken out by
    # the group's decision on #60 (26 November; rule 14.6, agreed by Igor)
    card = scorecard(results(AC3))
    for gone in ("headline", "focus", "passed", "assessed", "failed", "not_assessed"):
        assert not hasattr(card, gone), gone


def test_each_area_lists_its_six_marks_in_order():
    areas = by_area(scorecard(results(AC3)))
    assert areas["financial_health"].marks == ("pass", "fail", "fail", "pass", "pass", "pass")
    assert areas["dividend"].marks[1] == "not_assessed"
    assert areas["valuation"].marks == ("not_assessed",) * 6
    assert areas["valuation"].count_text == "Not part of this version"


def test_no_dividend_counts_one_assessed_check_and_five_that_do_not_apply():
    statuses = dict(AC3, dividend=["fail"] + ["not_applicable"] * 5)
    dividend = by_area(scorecard(results(statuses)))["dividend"]
    assert (dividend.passed, dividend.assessed) == (0, 1)  # was also share_text "0%": the radar is gone (see above)
    assert dividend.marks == ("fail",) + ("not_applicable",) * 5
    assert dividend.count_text == "No dividend paid · 0 passed of 1 assessed"
    assert (dividend.short_text, dividend.note) == ("0 passed of 1 assessed", "No dividend paid")  # both on screen


def test_an_area_with_nothing_assessed_reads_not_assessed_and_stays_off_the_radar():
    statuses = dict(AC3, financial_health=["insufficient_data"] * 6)
    health = by_area(scorecard(results(statuses)))["financial_health"]
    # was also "left off the focus": the area to read first is gone (see above)
    assert (health.short_text, health.count_text) == ("Not assessed", "Not assessed")
    assert (health.share, health.share_text) == (None, "Not assessed")  # off the radar's shape, never 0%


def test_nothing_assessed_at_all_reads_not_assessed_in_every_area():
    # was "no headline number": there is no total any more (see above)
    areas = by_area(scorecard(results({area: ["insufficient_data"] * 6 for area in AC3})))
    assert [areas[area].short_text for area in AC3] == ["Not assessed"] * 3
    assert areas["valuation"].short_text == "Not part of this version"


def test_coca_cola_counts_per_area_equal_a_count_of_its_check_results():
    # was the four totals; now the same count per area (see above)
    from ui.results import check_results

    checks = check_results(load_company("KO", demo=True))
    areas = by_area(scorecard(checks))
    for area, found in checks.items():
        if found:
            statuses = [r.status for r in found]
            assert areas[area].passed == statuses.count("pass"), area
            assert areas[area].assessed == statuses.count("pass") + statuses.count("fail"), area


def test_one_count_format_everywhere():
    # was "4 of 6 passed" and "4 of 6 checks passed" (Igor's design): one format, "N passed of M assessed", as SPEC
    # §3 writes it (Emma's review of #60, 26 November; rule 14.6, agreed by Igor)
    areas = by_area(scorecard(results(AC3)))
    assert areas["financial_health"].short_text == "4 passed of 6 assessed"
    assert areas["valuation"].short_text == "Not part of this version"
    assert areas["dividend"].note == ""
