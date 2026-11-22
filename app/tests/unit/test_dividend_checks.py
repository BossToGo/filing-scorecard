"""Dividend checks D1–D6 (SPEC §7, slice S7). Owner: C (Flo).

Where the expected values come from (SPEC rule 14.5, AGENTS.md rule 5):
- Edge cases: small test companies built below, with the expected results worked out by hand by Flo.
- Appendix A (synthetic company): `synthetic.expected_check("D1")` etc., signed off by Flo on PR #5. Those tests
  are added once PR #5 (the fixture) is on main.
Never from running `src/checks/dividend.py`.

Decisions for this slice (Flo, 22 November 2026):
- D2 is "not assessed" (status insufficient_data, plan Q9) until slice S9 switches it on.
- D3 counts a cut as "this year < (1 − max_dividend_cut) × last year": no division, so a rise from a year of zero
  is never a cut. The value shown is the lowest year-on-year change among years whose previous year is positive.
"""

from __future__ import annotations

from datetime import date

import pytest

from src.checks.dividend import dividend_checks
from src.contracts import CompanyData, Fact
from src.settings import load_settings

MILLION = 1_000_000.0
YEARS = (2021, 2022, 2023, 2024, 2025)  # FY-4 ... FY0
SETTINGS = load_settings()

# The labelled nil of plan Q1 (SPEC v2.4 §7), in the shape A's resolver produces it (PR #21): Amazon's case.
NIL_NOTE = ("no dividend under any dividend tag in the five fiscal years: not reported, treated as nil, so no "
            "dividend paid (SPEC §7, plan Q1)")


# --- a small test company ---------------------------------------------------------------------------------------


def fact(metric: str, millions: float | None, year: int, *, nil: bool = False) -> Fact:
    """One figure of the test company, in USD millions. None means missing (with a reason), never zero."""
    end = date(year, 12, 31)
    if millions is None:
        return Fact(metric, None, "USD", date(year, 1, 1), end, "missing", None, None, None, None, None,
                    "no annual 10-K figure for this year (test company)")
    if nil:
        return Fact(metric, millions * MILLION, "USD", None, end, "assumption", None, None, None, None, None, NIL_NOTE)
    return Fact(metric, millions * MILLION, "USD", date(year, 1, 1), end, "reported", f"test:{metric}", "TEST",
                "test-company", None, None, "test company")


def company(dividends, *, net_income=None, operating_cash_flow=None, capital_expenditure=None, years=YEARS,
            nil=False) -> CompanyData:
    """A test company. Each list holds USD millions, oldest year first (FY-4 ... FY0); None = missing that year.

    Unless a test gives them, the other figures are the same every year: revenue 1,000, net income 500, operating
    cash flow 600, capital expenditure 100.
    """
    n = len(years)
    columns = {
        "revenue": [1000] * n,
        "dividends_paid": dividends,
        "net_income": [500] * n if net_income is None else net_income,
        "operating_cash_flow": [600] * n if operating_cash_flow is None else operating_cash_flow,
        "capital_expenditure": [100] * n if capital_expenditure is None else capital_expenditure,
    }
    items = {}
    for metric, values in columns.items():
        assert len(values) == n, f"{metric}: give one value per fiscal year ({n})"
        is_nil = nil and metric == "dividends_paid"
        items[metric] = {date(y, 12, 31): fact(metric, v, y, nil=is_nil) for y, v in zip(years, values)}
    return CompanyData(ticker="TST", cik="0000000001", name="Test Co. (test data)", sic=None, sic_description=None,
                       fiscal_year_end="1231", latest_10k_filed=None, retrieved=None, items=items)


def results(data: CompanyData, settings=SETTINGS) -> dict:
    return {r.check_id: r for r in dividend_checks(data, settings)}


def figures(result) -> list[tuple[str, int]]:
    """The input figures of a result as (line item, fiscal year)."""
    return [(f.metric, f.period_end.year) for f in result.inputs]


PAYER = [20, 22, 24, 26, 28]  # a company that pays a dividend every year


# --- structure: no money values needed -----------------------------------------------------------------------------


def test_the_six_results_come_in_order_d1_to_d6():
    assert [r.check_id for r in dividend_checks(company(PAYER), SETTINGS)] == ["D1", "D2", "D3", "D4", "D5", "D6"]


def test_each_check_lists_the_figures_its_rule_uses():
    # SPEC §5.2: the checks a missing figure blocks are found from the results that list it as an input.
    r = results(company(PAYER))
    assert figures(r["D1"]) == [("dividends_paid", 2025)]
    assert figures(r["D3"]) == [("dividends_paid", y) for y in YEARS]
    assert figures(r["D4"]) == [("dividends_paid", 2025), ("dividends_paid", 2021)]
    assert figures(r["D5"]) == [("dividends_paid", 2025), ("net_income", 2025)]
    assert figures(r["D6"]) == [("dividends_paid", 2025), ("operating_cash_flow", 2025),
                                ("capital_expenditure", 2025)]


def test_d2_is_not_assessed_until_s9_and_says_what_it_needs():
    # Plan Q9: "not assessed" is insufficient_data with the reason; it has no value (SPEC §7, §13.2 slice S9).
    d2 = results(company(PAYER))["D2"]
    assert d2.status == "insufficient_data"
    assert d2.value is None
    assert "not assessed" in d2.explanation
    assert "share price" in d2.explanation and "dividend yield" in d2.explanation


def test_the_thresholds_come_from_the_settings_not_the_code():
    r = results(company(PAYER))
    assert r["D3"].threshold == pytest.approx(-SETTINGS["dividend"]["max_dividend_cut"])
    assert r["D5"].threshold == pytest.approx(SETTINGS["dividend"]["max_payout_ratio"])

    changed = {**SETTINGS, "dividend": {"max_dividend_cut": 0.25, "max_payout_ratio": 0.50}}
    r = results(company(PAYER), changed)
    assert r["D3"].threshold == pytest.approx(-0.25)
    assert r["D5"].threshold == pytest.approx(0.50)


# --- edge cases: expected results worked out by hand by Flo (22 November 2026) ----------------------------------
# Decisions of 22 November: a fiscal year that is not in the data counts as a missing input; when net income is
# zero or negative, D5 fails with the reason in plain words and shows no payout ratio.

LATER = ["D2", "D3", "D4", "D5", "D6"]
PCT = 0.00005  # half a unit of a percentage shown to two decimals (0.005%), as a decimal


def statuses(r: dict, ids: list[str]) -> list[str]:
    return [r[i].status for i in ids]


def test_1_a_labelled_nil_means_no_dividend_paid():
    # Amazon's case (SPEC v2.4 §7, plan Q1): no dividend in any of the five years, labelled nil.
    r = results(company([0, 0, 0, 0, 0], nil=True))
    assert r["D1"].status == "fail"
    assert "no dividend paid" in r["D1"].explanation.lower()
    assert statuses(r, LATER) == ["not_applicable"] * 5
    assert all("no dividend paid" in r[c].explanation.lower() for c in LATER)


def test_2_a_reported_zero_in_fy0_means_no_dividend_paid():
    r = results(company([30, 32, 34, 36, 0]))
    assert r["D1"].status == "fail"
    assert "no dividend paid" in r["D1"].explanation.lower()
    assert statuses(r, LATER) == ["not_applicable"] * 5


def test_3_missing_fy0_dividends_are_insufficient_data_never_no_dividend():
    # SPEC v2.4 §7: a payer must never be shown as paying none.
    r = results(company([30, 32, 34, 36, None]))
    assert statuses(r, ["D1"] + LATER) == ["insufficient_data"] * 6
    assert not any("no dividend paid" in r[c].explanation.lower() for c in r)


@pytest.mark.parametrize("fy0, status, lowest_change", [
    (45, "pass", -0.1000),    # 4a: a fall of exactly 10% is not "more than 10%"
    (44.9, "fail", -0.1020),  # 4b
])
def test_4_d3_a_fall_of_exactly_10_percent_is_not_a_cut(fy0, status, lowest_change):
    d3 = results(company([50, 50, 50, 50, fy0]))["D3"]
    assert d3.status == status
    assert d3.value == pytest.approx(lowest_change, abs=PCT)
    assert d3.threshold == pytest.approx(-0.10)


def test_5_d3_with_a_year_missing_is_insufficient_data():
    assert results(company([30, 32, None, 36, 38]))["D3"].status == "insufficient_data"


def test_6_d3_a_rise_from_a_year_of_zero_is_never_a_cut():
    # The step 0 → 30 is left out of the lowest change; the lowest is 38 → 40.
    d3 = results(company([0, 30, 35, 38, 40]))["D3"]
    assert d3.status == "pass"
    assert d3.value == pytest.approx(0.0526, abs=PCT)


def test_7_with_only_four_fiscal_years_d3_and_d4_are_insufficient_data():
    # FY-3 to FY0 only, so FY-4 is not in the data: a missing input.
    r = results(company([32, 34, 36, 38], years=(2022, 2023, 2024, 2025)))
    assert r["D3"].status == "insufficient_data"
    assert r["D4"].status == "insufficient_data"


def test_8_d4_a_dividend_equal_to_four_years_earlier_did_not_grow():
    d4 = results(company([40, 42, 41, 40, 40]))["D4"]
    assert d4.status == "fail"
    assert d4.value == pytest.approx(40 * MILLION)
    assert d4.threshold == pytest.approx(40 * MILLION)


@pytest.mark.parametrize("net_income_fy0, payout", [(100, 0.9000), (0, None), (-50, None)])
def test_9_d5_fails_at_exactly_90_percent_and_when_net_income_is_zero_or_negative(net_income_fy0, payout):
    d5 = results(company([80, 82, 84, 86, 90], net_income=[500, 500, 500, 500, net_income_fy0]))["D5"]
    assert d5.status == "fail"
    if payout is None:
        assert d5.value is None
        assert "zero or negative" in d5.explanation
    else:
        assert d5.value == pytest.approx(payout, abs=PCT)


@pytest.mark.parametrize("ocf_fy0, capex_fy0, status, compared_with", [
    (215, 85, "pass", 130),                     # 10a: equal is enough (≤)
    (215, None, "insufficient_data", None),     # 10b: capex missing
    (100, 150, "fail", -50),                    # 10c: negative free cash flow
])
def test_10_d6_dividends_against_operating_cash_flow_minus_capex(ocf_fy0, capex_fy0, status, compared_with):
    data = company([120, 122, 124, 126, 130], operating_cash_flow=[600, 600, 600, 600, ocf_fy0],
                   capital_expenditure=[100, 100, 100, 100, capex_fy0])
    d6 = results(data)["D6"]
    assert d6.status == status
    if compared_with is None:
        assert d6.value is None and d6.threshold is None
    else:
        assert d6.value == pytest.approx(130 * MILLION)
        assert d6.threshold == pytest.approx(compared_with * MILLION)


def test_11_a_changed_payout_limit_changes_d5():
    changed = {**SETTINGS, "dividend": {"max_dividend_cut": 0.10, "max_payout_ratio": 0.30}}
    d5 = results(company([30, 32, 34, 36, 40], net_income=[500, 500, 500, 500, 100]), changed)["D5"]
    assert d5.status == "fail"
    assert d5.value == pytest.approx(0.40, abs=PCT)
    assert d5.threshold == pytest.approx(0.30)


def test_a_company_without_any_fiscal_year_is_insufficient_data_everywhere():
    # Follows from Flo's decision that a fiscal year not in the data is a missing input. No crash.
    empty = CompanyData(ticker="NIL", cik="0000000002", name="No figures", sic=None, sic_description=None,
                        fiscal_year_end=None, latest_10k_filed=None, retrieved=None, items={})
    assert statuses(results(empty), ["D1"] + LATER) == ["insufficient_data"] * 6


# --- negative dividends and D3 without an earlier dividend: Flo's decisions and hand results (22 November) ------
# A negative dividends paid figure is a sign error (SPEC §5.4): the data layer keeps it as filed with a SIGN warning
# and never flips it (§5.2: never guessed). Every check that uses that year is insufficient data, with the reason.


def test_a_negative_fy0_dividend_is_insufficient_data_everywhere():
    r = results(company([30, 32, 34, 36, -10]))
    assert statuses(r, ["D1"] + LATER) == ["insufficient_data"] * 6
    assert "sign" in r["D1"].explanation.lower()
    assert not any("no dividend paid" in r[c].explanation.lower() for c in r)


def test_b_a_negative_dividend_in_fy_minus_2_blocks_only_d3():
    r = results(company([30, 32, -34, 36, 38]))
    assert statuses(r, ["D1"] + LATER) == ["pass", "insufficient_data", "insufficient_data", "pass", "pass", "pass"]
    assert "sign" in r["D3"].explanation.lower()
    assert r["D4"].value == pytest.approx(38 * MILLION) and r["D4"].threshold == pytest.approx(30 * MILLION)
    assert r["D5"].value == pytest.approx(0.0760, abs=PCT)
    assert r["D6"].value == pytest.approx(38 * MILLION) and r["D6"].threshold == pytest.approx(500 * MILLION)


def test_c_d3_passes_with_no_value_when_every_step_starts_from_zero():
    d3 = results(company([0, 0, 0, 0, 5]))["D3"]
    assert d3.status == "pass"
    assert d3.value is None
