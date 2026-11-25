"""Dividend checks D1–D6 (SPEC §7, slice S7). Owner: C (Flo).

Where the expected values come from (SPEC rule 14.5, AGENTS.md rule 5):
- Edge cases: small test companies built below, with the expected results worked out by hand by Flo; his
  working is written in docs/acceptance.md ("S7 edge cases").
- Appendix A (synthetic company): `synthetic.expected_check("D1")` etc., signed off by Flo on PR #5 (at the
  end of this file); Coca-Cola: tests/integration/test_dividend_demo.py.
Never from running `src/checks/dividend.py`.

Flo's decisions for this slice are listed in the docstring of `src/checks/dividend.py`.
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


# --- SPEC Appendix A: the synthetic company (CALC-D, AC3), signed off by Flo and Simon on PR #5 ------------------

from tests.fixtures import synthetic  # noqa: E402  (kept next to the tests that use it)


def as_shown(value: float, unit: str) -> float:
    """A result in the unit Appendix A shows: USD millions, or percent."""
    return {"USD m": value / MILLION, "%": value * 100}[unit]


@pytest.mark.parametrize("check_id", ["D1", "D3", "D4", "D5", "D6"])
def test_appendix_a_synthetic_company(check_id):
    expected = synthetic.expected_check(check_id)
    result = results(synthetic.company_data())[check_id]
    assert result.status == expected["result"]
    assert as_shown(result.value, expected["unit"]) == pytest.approx(expected["value"],
                                                                      abs=synthetic.tolerance(expected))
    if "compared_with" in expected:
        assert as_shown(result.threshold, expected["unit"]) == pytest.approx(expected["compared_with"],
                                                                              abs=synthetic.tolerance(expected))


def test_appendix_a_d2_is_not_assessed_without_share_price_and_benchmark():
    # CALC-D2 (1.867% > 1.5%) needs the share price and the market yield: slice S9. In S7 it is not assessed.
    d2 = results(synthetic.company_data())["D2"]
    assert d2.status == "insufficient_data" and d2.value is None


def test_appendix_a_d2_with_share_price_and_market_yield():
    # CALC-D2 (S9): 56 ÷ (30.00 × 100) = 1.867% > 1.5% → pass, signed off by Flo on PR #5.
    expected = synthetic.expected_check("D2")
    yield_fact = Fact("dividend_yield", synthetic.inputs()["benchmarks"]["market_dividend_yield"], "pure", None,
                      date(2025, 12, 31), "assumption", None, None, None, None, None,
                      "market dividend yield of the synthetic company (SYNTHETIC DATA: SPEC Appendix A)")
    d2 = {r.check_id: r for r in dividend_checks(synthetic.company_data(), SETTINGS,
                                                 share_price=synthetic.inputs()["share_price"],
                                                 market_dividend_yield=yield_fact)}["D2"]
    assert d2.status == expected["result"]
    assert as_shown(d2.value, expected["unit"]) == pytest.approx(expected["value"], abs=synthetic.tolerance(expected))
    assert as_shown(d2.threshold, expected["unit"]) == pytest.approx(expected["compared_with"],
                                                                      abs=synthetic.tolerance(expected))


def test_ac3_tier_1_dividend_score_of_the_synthetic_company():
    expected = synthetic.expected_tier1()
    checks = dividend_checks(synthetic.company_data(), SETTINGS)
    assessed = [r for r in checks if r.status in ("pass", "fail")]
    assert len(assessed) == expected["scores"]["dividend"]["assessed"]
    assert sum(r.status == "pass" for r in assessed) == expected["scores"]["dividend"]["passed"]
    assert [r.check_id for r in checks if r.status == "insufficient_data"] == \
        [c for c in expected["not_assessed"] if c.startswith("D")]


# --- review round 1 (22 November): Flo's hand results for T1–T11; written in docs/acceptance.md ------------------
# Decision of 22 November: capital expenditure is a payment too, so a negative capex is a sign error and every check
# that uses it (D6) is insufficient data, like a negative dividend.


def test_t1_a_negative_capex_is_a_sign_error_and_d6_is_insufficient_data():
    data = company([120, 122, 124, 126, 130], operating_cash_flow=[600, 600, 600, 600, 100],
                   capital_expenditure=[100, 100, 100, 100, -50])
    r = results(data)
    assert statuses(r, ["D1", "D3", "D4", "D5", "D6"]) == ["pass", "pass", "pass", "pass", "insufficient_data"]
    assert "sign" in r["D6"].explanation.lower()


@pytest.mark.parametrize("dividends, status, lowest_change", [
    ([50, 40, 45, 50, 55], "fail", -0.2000),         # T2: a cut in the first step, then recovery
    ([30, 0, 30, 32, 34], "fail", -1.0000),          # T3: suspended for a year, then resumed
    ([100, 92, 84.64, 90, 95], "pass", -0.0800),     # T4: two falls of 8% in a row, measured year on year
])
def test_t2_to_t4_d3_looks_at_every_step_year_on_year(dividends, status, lowest_change):
    d3 = results(company(dividends))["D3"]
    assert d3.status == status
    assert d3.value == pytest.approx(lowest_change, abs=PCT)


def test_t5_a_negative_fy_minus_4_dividend_blocks_only_d3_and_d4():
    r = results(company([-30, 32, 34, 36, 38]))
    assert statuses(r, ["D1", "D3", "D4", "D5", "D6"]) == [
        "pass", "insufficient_data", "insufficient_data", "pass", "pass"]
    assert "sign" in r["D3"].explanation.lower() and "sign" in r["D4"].explanation.lower()


def test_t6_a_missing_fy_minus_4_dividend_blocks_d3_and_d4():
    r = results(company([None, 32, 34, 36, 38]))
    assert statuses(r, ["D3", "D4"]) == ["insufficient_data", "insufficient_data"]


def test_t7_missing_net_income_blocks_d5_only():
    r = results(company([30, 32, 34, 36, 38], net_income=[500, 500, 500, 500, None]))
    assert statuses(r, ["D5", "D6"]) == ["insufficient_data", "pass"]


def test_t8_a_changed_cut_limit_changes_d3():
    changed = {**SETTINGS, "dividend": {"max_dividend_cut": 0.25, "max_payout_ratio": 0.90}}
    d3 = results(company([50, 50, 50, 50, 40]), changed)["D3"]
    assert d3.status == "pass"
    assert d3.value == pytest.approx(-0.2000, abs=PCT)
    assert d3.threshold == pytest.approx(-0.25)


def test_t9_a_positive_dividend_typed_in_by_a_user_passes_d1():
    typed = Fact("dividends_paid", 40 * MILLION, "USD", date(2025, 1, 1), date(2025, 12, 31), "assumption", None,
                 None, None, None, None, "typed in by the user")
    d1 = results(company([30, 32, 34, 36, 36]).with_fact(typed))["D1"]
    assert d1.status == "pass"
    # Review round 2: the 40 replaces the reported 36, so check it is the figure used.
    assert d1.value == pytest.approx(40 * MILLION) and d1.inputs[0].kind == "assumption"


def test_t10_a_missing_middle_year_leaves_d1_d4_d5_d6_assessed():
    r = results(company([30, 32, None, 36, 38]))
    assert statuses(r, ["D1", "D4", "D5", "D6"]) == ["pass"] * 4


def test_t11_with_four_fiscal_years_d1_d5_d6_are_still_assessed():
    r = results(company([32, 34, 36, 38], years=(2022, 2023, 2024, 2025)))
    assert statuses(r, ["D1", "D5", "D6"]) == ["pass"] * 3


# --- review round 1: wording (findings 7, 9 and 10, approved by Flo) ---------------------------------------------


def test_the_nil_explanation_is_one_plain_sentence_and_the_full_note_stays_with_the_figure():
    d1 = results(company([0, 0, 0, 0, 0], nil=True))["D1"]
    assert "treated as nil" in d1.explanation
    assert "SPEC" not in d1.explanation and "plan Q1" not in d1.explanation
    assert d1.inputs[0].kind == "assumption" and d1.inputs[0].note == NIL_NOTE  # for the sources page


def test_explanations_do_not_round_in_a_misleading_way():
    changed = {**SETTINGS, "dividend": {"max_dividend_cut": 0.125, "max_payout_ratio": 0.875}}
    r = results(company([100, 100, 100, 100, 90]), changed)
    assert "12.5%" in r["D3"].explanation
    assert "87.5%" in r["D5"].explanation
    tiny = results(company([0.04, 0.04, 0.04, 0.04, 0.04]))["D1"]    # USD 40,000
    assert "USD 40,000" in tiny.explanation and "USD 0 million" not in tiny.explanation
    d3 = results(company([50, 50, 50, 50, 44.9]))["D3"]
    assert "−10.20%" in d3.explanation and "-" not in d3.explanation  # one minus sign everywhere


# --- review round 2 (22 November): findings 1 and 3, approved by Flo -------------------------------------------


def test_a_zero_assumption_that_is_not_the_nil_is_shown_as_a_plain_zero():
    # Only the data layer's nil (plan Q1) gets the "treated as nil" sentence; any other zero is just "USD 0".
    other = Fact("dividends_paid", 0.0, "USD", date(2025, 1, 1), date(2025, 12, 31), "assumption", None, None,
                 None, None, None, "set to zero for a test")
    r = results(company([30, 32, 34, 36, 36]).with_fact(other))
    assert r["D1"].status == "fail"
    assert "treated as nil" not in r["D1"].explanation and "set to zero" not in r["D1"].explanation
    assert "USD 0" in r["D1"].explanation
    assert statuses(r, LATER) == ["not_applicable"] * 5


def test_the_sign_warning_is_named_only_for_a_figure_read_from_a_filing():
    # The data layer raises its SIGN warning only for reported figures (resolver.py).
    negative = Fact("capital_expenditure", -50 * MILLION, "USD", date(2025, 1, 1), date(2025, 12, 31),
                    "assumption", None, None, None, None, None, "set for a test")
    d6 = results(company([120, 122, 124, 126, 130]).with_fact(negative))["D6"]
    assert d6.status == "insufficient_data"
    assert "positive amount" in d6.explanation and "sign warning" not in d6.explanation



# --- S9: D2 switched on (yield above the market). Flo's hand working, docs/acceptance.md "S9 edge cases" --------------


def with_shares(data: CompanyData, millions: float | None) -> CompanyData:
    """The test company with a share count at FY0 (None: no share count in the data)."""
    items = {metric: dict(by_year) for metric, by_year in data.items.items()}
    if millions is not None:
        items["shares"] = {date(2025, 12, 31): Fact("shares", millions * MILLION, "shares", None, date(2025, 12, 31),
                                                     "reported", "test:shares", "TEST", "test-company", None, None,
                                                     "test company")}
    return CompanyData(ticker="TST", cik="0000000001", name="Test Co. (test data)", sic=None, sic_description=None,
                       fiscal_year_end="1231", latest_10k_filed=None, retrieved=None, items=items)


MARKET_YIELD = Fact("dividend_yield", 0.015, "pure", None, date(2025, 12, 31), "assumption", None, None, None, None,
                    None, "US market dividend yield of a test (test data)")


def d2(dividends_fy0: float, *, price=20.0, shares=100, market_yield=MARKET_YIELD):
    data = with_shares(company([dividends_fy0] * 5), shares)
    return {r.check_id: r for r in dividend_checks(data, SETTINGS, share_price=price,
                                                   market_dividend_yield=market_yield)}["D2"]


def test_e9_yield_equal_to_the_market_yield_fails():
    result = d2(30)  # 30 ÷ (20.00 × 100) = 1.50%, against 1.50%
    assert (result.status, result.value, result.threshold) == ("fail", pytest.approx(0.015), 0.015)


def test_e10_yield_below_the_market_yield_fails():
    result = d2(20)  # 20 ÷ (20.00 × 100) = 1.00%, against 1.50%
    assert (result.status, result.value, result.threshold) == ("fail", pytest.approx(0.010), 0.015)


@pytest.mark.parametrize("missing, words", [
    ({"price": None}, "share price"), ({"market_yield": None}, "dividend yield"), ({"shares": None}, "share count")])
def test_d2_without_price_market_yield_or_shares_is_insufficient_data(missing, words):
    result = d2(30, **missing)
    assert (result.status, result.value) == ("insufficient_data", None)
    assert words in result.explanation


def test_d2_is_not_applicable_when_no_dividend_is_paid():
    data = with_shares(company([10, 10, 10, 10, 0]), 100)
    result = {r.check_id: r for r in dividend_checks(data, SETTINGS, share_price=20.0,
                                                     market_dividend_yield=MARKET_YIELD)}["D2"]
    assert result.status == "not_applicable"


def test_d2_yield_halves_when_the_share_count_doubles():
    # The rule itself (dividends ÷ (price × shares)): every other test company has 100 million shares, so a formula
    # that ignored the share count would pass them all (planted-bug check, 25 November).
    assert d2(30, shares=200).value == pytest.approx(d2(30, shares=100).value / 2)


# --- Review of 25 November (Flo: "yes, as recommended"): D2's guards, from the rules themselves --------------------

def missing_yield() -> Fact:
    return Fact("dividend_yield", None, "pure", None, date(2025, 12, 31), "missing", None, None, None, None, None,
                "the source cell is blank (test)")


@pytest.mark.parametrize("bad, words", [
    ({"price": 0.0}, "a share price above zero"), ({"price": -1.0}, "a share price above zero"),
    ({"price": float("nan")}, "a share price above zero"), ({"price": float("inf")}, "a share price above zero"),
    ({"shares": 0}, "share count"), ({"shares": -100}, "share count"),
    ({"market_yield": missing_yield()}, "the source cell is blank (test)"),
    ({"market_yield": Fact("dividend_yield", 0.0, "pure", None, date(2025, 12, 31), "assumption", None, None, None,
                           None, None, "test")}, "zero or negative"),
    ({"market_yield": Fact("dividend_yield", -0.01, "pure", None, date(2025, 12, 31), "assumption", None, None, None,
                           None, None, "test")}, "zero or negative"),
])
def test_r_d2_bad_inputs_give_insufficient_data_naming_them(bad, words):
    result = d2(30, **bad)
    assert (result.status, result.value) == ("insufficient_data", None)
    assert words in result.explanation


def test_r_d2_with_dividends_fy0_missing_is_insufficient_data_naming_them():
    data = with_shares(company([10, 10, 10, 10, None]), 100)
    r = {x.check_id: x for x in dividend_checks(data, SETTINGS, share_price=20.0, market_dividend_yield=MARKET_YIELD)}
    assert (r["D1"].status, r["D2"].status, r["D2"].value) == ("insufficient_data", "insufficient_data", None)
    assert "dividends paid" in r["D2"].explanation


def test_r_d2_yields_that_round_to_the_same_number_are_shown_with_more_decimals():
    # 29.998 ÷ 2,000 = 1.4999%, against 1.50%: with two decimals both would read "1.50%" next to a fail.
    result = d2(29.998)
    assert result.status == "fail"
    assert "1.4999%" in result.explanation and "1.5000%" in result.explanation
    e9 = d2(30).explanation  # exactly equal (E9): two decimals
    assert "Dividend yield 1.50% " in e9 and "against 1.50% for the US market" in e9


def test_appendix_a_dividend_area_score_with_d2():
    # CALC-S, signed off by Emma (E): dividend 6 of 6 once D2 is assessed (share price 30.00, market yield 1.5%).
    from src.scores import area_score

    yield_fact = Fact("dividend_yield", synthetic.inputs()["benchmarks"]["market_dividend_yield"], "pure", None,
                      date(2025, 12, 31), "assumption", None, None, None, None, None,
                      "market dividend yield of the synthetic company (SYNTHETIC DATA: SPEC Appendix A)")
    found = dividend_checks(synthetic.company_data(), SETTINGS, share_price=synthetic.inputs()["share_price"],
                            market_dividend_yield=yield_fact)
    score = area_score(found)
    assert (score.passed, score.assessed) == (synthetic.expected_scores()["dividend"], 6)


# --- Review round 2 (Flo: option A, 25 November): a yield equal to the market's by hand fails (as E9) ---------------
# Flo's hand working: 30,150 ÷ (2.01 × 1,000,000) = 30,150 ÷ 2,010,000 = 0.015, exactly 1.5% (row T2).

def test_t2_a_yield_equal_to_the_market_yield_by_hand_fails():
    result = d2(0.03015, price=2.01, shares=1)
    assert result.status == "fail"
    assert "Dividend yield 1.50% " in result.explanation and "against 1.50% for the US market" in result.explanation


def test_t_d2_differences_of_one_part_in_a_trillion_are_ties_and_one_in_a_million_counts():
    assert d2(30 * (1 + 1e-12)).status == "fail"
    assert d2(30 * (1 + 1e-6)).status == "pass"
