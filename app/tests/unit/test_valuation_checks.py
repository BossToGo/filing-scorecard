"""Valuation checks V1–V6 (SPEC §7, §8.6; slice S9). Owner: C (Flo).

Where the expected values come from (SPEC rule 14.5, AGENTS.md rule 5):
- Appendix A (synthetic company): `synthetic.expected_check("V1")` etc., the values Flo recalculated in his own
  Excel model (`docs/crosscheck/valuation-crosscheck.xlsx`, PR #14) and signed off on PR #5 (CALC-V1–V6); the
  valuation area score from Emma's sign-off (CALC-S, `synthetic.expected_scores()`).
- Edge cases: small test cases with the expected results worked out by hand by Flo, written in docs/acceptance.md
  ("S9 edge cases").
Never from running `src/checks/valuation.py` or `src/valuation/equity_method.py`.
"""

from __future__ import annotations

import dataclasses
import math
import re
from datetime import date

import pytest

from src.checks.valuation import estimate_gap, valuation_checks
from src.contracts import CompanyData, Fact
from src.scores import area_score
from src.settings import load_settings
from src.valuation.equity_method import Valuation, value_company
from tests.fixtures import synthetic

FY0 = date(2025, 12, 31)
SETTINGS = load_settings()
PRICE = synthetic.inputs()["share_price"]  # USD 30.00
BENCHMARKS = synthetic.inputs()["benchmarks"]


# --- inputs ----------------------------------------------------------------------------------------------------------


def market(value: float | None, metric: str) -> Fact | None:
    """A market input as the data layer (S2b) or the benchmark loader (S4) hands it over: a Fact with its source."""
    if value is None:
        return None
    return Fact(metric, value, "pure", None, FY0, "assumption", None, None, None, None, None,
                f"{metric} of the synthetic company (SYNTHETIC DATA: SPEC Appendix A)")


RISK_FREE = market(synthetic.inputs()["settings"]["risk_free_rate"], "risk_free_rate")  # 4.0%
BETA = market(BENCHMARKS["unlevered_beta"], "unlevered_beta")  # 0.90
INDUSTRY_PE = market(BENCHMARKS["price_to_earnings"], "pe")  # 20.0
MARKET_PE = market(BENCHMARKS["market_price_to_earnings"], "pe")  # 24.0
INDUSTRY_PB = market(BENCHMARKS["price_to_book"], "pb")  # 4.0


def results(data: CompanyData | None = None, *, price=PRICE, industry_pe=INDUSTRY_PE, market_pe=MARKET_PE,
            industry_pb=INDUSTRY_PB) -> dict:
    """V1–V6 of a company, on the valuation the engine gives at the same share price."""
    data = synthetic.company_data() if data is None else data
    valuation = value_company(data, SETTINGS, share_price=price, risk_free_rate=RISK_FREE, unlevered_beta=BETA)
    checks = valuation_checks(data, SETTINGS, valuation, share_price=price, industry_pe=industry_pe,
                              market_pe=market_pe, industry_pb=industry_pb)
    return {r.check_id: r for r in checks}


# --- Appendix A (CALC-V1 to CALC-V6, CALC-S) -------------------------------------------------------------------------


def test_the_six_checks_come_in_order():
    assert list(results()) == ["V1", "V2", "V3", "V4", "V5", "V6"]


@pytest.mark.parametrize("check_id", ["V1", "V2", "V3", "V4", "V5", "V6"])
def test_appendix_a_synthetic_company(check_id):
    # Units as Appendix A shows them: V1, V2, V6 in USD per share; V3–V5 as multiples (x). Both are the units the
    # results carry, so no conversion.
    expected = synthetic.expected_check(check_id)
    result = results()[check_id]
    assert result.status == expected["result"]
    assert result.value == pytest.approx(expected["value"], abs=synthetic.tolerance(expected))
    assert result.threshold == pytest.approx(expected["compared_with"], abs=synthetic.tolerance(expected))


def test_appendix_a_valuation_area_score():
    # CALC-S, signed off by Emma (E): valuation 3 of 6.
    score = area_score(list(results().values()))
    assert score.passed == synthetic.expected_scores()["valuation"]
    assert score.assessed == 6


def test_appendix_a_gap_to_the_estimate_for_g7_and_w8():
    # Flo's value (25 November 2026), his hand working in docs/acceptance.md row S9-W8 (the unrounded estimate from his
    # Excel model, Valuation!G17): (30.00 − unrounded estimate) ÷ unrounded estimate = 49.0% above (one
    # decimal, as SPEC Appendix A shows it for W8). docs/acceptance.md, S9 edge cases, row S9-W8.
    data = synthetic.company_data()
    v = value_company(data, SETTINGS, share_price=PRICE, risk_free_rate=RISK_FREE, unlevered_beta=BETA)
    assert estimate_gap(PRICE, v.fair_value.value) * 100 == pytest.approx(49.0, abs=0.05)
    assert "49.0% above the estimate" in results()["V1"].explanation


# --- S9 edge cases: Flo's hand working (docs/acceptance.md, "S9 edge cases") ----------------------------------------

MILLION = 1_000_000.0
YEAR_END = date(2025, 12, 31)
BANNED = ("fair value", "cheap", "expensive", "undervalued", "overvalued")  # SPEC §3, §7: "the estimate" on screen
CAP = SETTINGS["valuation"]["growth_cap"]


def per_share(value: float, metric: str = "fair_value") -> Fact:
    return Fact(metric, value, "USD/shares", None, YEAR_END, "derived", None, None, None, None, None,
                f"{metric} of a test valuation")


def estimate(fair: float = 20.0, at_cap: float = 25.0, g1: float = 0.05) -> Valuation:
    """A valuation the engine could return (status ok): the estimate, the estimate at the growth cap, g1."""
    g = Fact("starting_growth", g1, "pure", None, YEAR_END, "derived", None, None, None, None, None,
             "starting growth of a test valuation")
    return Valuation("ok", "", (), starting_growth=g, fair_value=per_share(fair),
                     fair_value_at_growth_cap=per_share(at_cap, "fair_value_at_growth_cap"))


def figure(metric: str, millions: float | None, unit: str = "USD") -> Fact:
    """One FY0 figure of the test company. None means missing (with a reason), never zero."""
    if millions is None:
        return Fact(metric, None, unit, None, YEAR_END, "missing", None, None, None, None, None,
                    f"no annual 10-K figure for {metric} (test company)")
    start = None if metric in ("equity", "shares") else date(2025, 1, 1)
    return Fact(metric, millions * MILLION, unit, start, YEAR_END, "reported", f"test:{metric}", "TEST",
                "test-company", None, None, "test company")


def company(*, net_income: float | None = 100, equity: float | None = 500, shares: float | None = 100) -> CompanyData:
    """A test company for V3–V5 (S9-E5, S9-E7): FY0 net income and equity in USD millions, shares in millions."""
    items = {"revenue": {YEAR_END: figure("revenue", 1000)},
             "net_income": {YEAR_END: figure("net_income", net_income)},
             "equity": {YEAR_END: figure("equity", equity)}}
    if shares is not None:
        items["shares"] = {YEAR_END: figure("shares", shares, unit="shares")}
    return CompanyData(ticker="TST", cik="0000000001", name="Test Co. (test data)", sic=None, sic_description=None,
                       fiscal_year_end="1231", latest_10k_filed=None, retrieved=None, items=items)


def checks(valuation: Valuation | None = None, data: CompanyData | None = None, *, price=20.0, industry_pe=20.0,
           market_pe=20.0, industry_pb=4.0, settings=SETTINGS) -> dict:
    """V1–V6 for a test valuation and a test company; benchmarks given as numbers become Facts (a Fact is kept)."""
    def bench(value, metric):
        return value if isinstance(value, Fact) else market(value, metric)

    found = valuation_checks(company() if data is None else data, settings,
                             estimate() if valuation is None else valuation, share_price=price,
                             industry_pe=bench(industry_pe, "pe"), market_pe=bench(market_pe, "pe"),
                             industry_pb=bench(industry_pb, "pb"))
    return {r.check_id: r for r in found}


def outcome(result) -> tuple:
    return result.status, result.value, result.threshold


# S9-E1 to S9-E4: the price against the estimate (V1, V2, V6) and the gap for G7 and W8

def test_s9_e1_gap_below_the_estimate():
    assert estimate_gap(15.0, 20.0) == pytest.approx(-0.25)
    assert "25.0% below the estimate" in checks(estimate(20.0), price=15.0)["V1"].explanation


def test_s9_e2_price_equal_to_the_estimate_and_to_the_estimate_at_the_cap():
    r = checks(estimate(20.0, 20.0, g1=CAP), price=20.0)
    assert outcome(r["V1"]) == ("fail", 20.0, 20.0)
    assert (r["V2"].status, r["V2"].value) == ("fail", 20.0) and r["V2"].threshold == pytest.approx(16.0)
    assert outcome(r["V6"]) == ("pass", 20.0, 20.0)
    assert "at the estimate" in r["V1"].explanation  # decision a: not "0.0% above"
    assert "% above" not in r["V1"].explanation and "% below" not in r["V1"].explanation


def test_s9_e3_price_exactly_at_80_percent_of_the_estimate():
    r = checks(estimate(20.0), price=16.0)
    assert outcome(r["V1"]) == ("pass", 16.0, 20.0)
    assert (r["V2"].status, r["V2"].value) == ("pass", 16.0) and r["V2"].threshold == pytest.approx(16.0)


def test_s9_e4_price_equal_to_the_estimate_at_the_cap():
    assert outcome(checks(estimate(20.0, 25.0), price=25.0)["V6"]) == ("pass", 25.0, 25.0)


def test_v6_says_when_starting_growth_is_already_at_the_cap():
    # Decision b (Flo): V6 keeps its own ≤ rule and says why it uses the same estimate as V1.
    line = "The company's starting growth is already at the 30% cap, so V6 uses the same estimate as V1."
    assert line in checks(estimate(20.0, 20.0, g1=CAP), price=15.0)["V6"].explanation
    assert line not in checks(estimate(20.0, 25.0, g1=0.05), price=15.0)["V6"].explanation


# S9-E5 to S9-E8: price to earnings and price to book (V3, V4, V5)

def test_s9_e5_price_to_earnings_equal_to_both_benchmarks_fails():
    r = checks(price=20.0)
    assert outcome(r["V3"]) == ("fail", pytest.approx(20.0), 20.0)
    assert outcome(r["V4"]) == ("fail", pytest.approx(20.0), 20.0)


@pytest.mark.parametrize("earnings, words", [(0, "zero"), (-50, "loss")])
def test_s9_e6_no_earnings_fails_v3_and_v4_without_a_ratio(earnings, words):
    r = checks(data=company(net_income=earnings))
    for check_id in ("V3", "V4"):
        assert (r[check_id].status, r[check_id].value, r[check_id].threshold) == ("fail", None, None)
        assert words in r[check_id].explanation
        assert "pe" not in [f.metric for f in r[check_id].inputs]  # decision c: the benchmark was not used


def test_s9_e6_no_earnings_fails_even_without_benchmarks():
    # Decision c (Flo): net income ≤ 0 fails before a missing benchmark is looked at.
    r = checks(data=company(net_income=-50), industry_pe=None, market_pe=None)
    assert (r["V3"].status, r["V4"].status) == ("fail", "fail")


def test_s9_e7_price_to_book_equal_to_the_benchmark_fails():
    assert outcome(checks()["V5"]) == ("fail", pytest.approx(4.0), 4.0)


@pytest.mark.parametrize("book, words", [(0, "equity is zero"), (-1791, "negative equity")])
def test_s9_e8_zero_or_negative_equity_fails_v5_without_a_ratio(book, words):
    for pb in (4.0, None):  # also without the benchmark (decision c)
        v5 = checks(data=company(equity=book), industry_pb=pb)["V5"]
        assert (v5.status, v5.value, v5.threshold) == ("fail", None, None)
        assert words in v5.explanation
        assert "pb" not in [f.metric for f in v5.inputs]  # decision c: the benchmark was not used


# The whole area without a share price or a share count (SPEC §7, §8.6; decision c)

def test_without_a_share_price_the_whole_area_is_insufficient_data():
    v = Valuation("insufficient_data", "Insufficient data: share price: not given.", ())
    r = checks(v, price=None)
    assert [x.status for x in r.values()] == ["insufficient_data"] * 6
    assert all("share price" in x.explanation for x in r.values())


def test_without_a_share_count_the_whole_area_is_insufficient_data():
    v = Valuation("insufficient_data", "Insufficient data: shares: no share count in the data.", ())
    r = checks(v, company(shares=None))
    assert [x.status for x in r.values()] == ["insufficient_data"] * 6
    assert all("share count" in x.explanation for x in r.values())


# SPEC §8.6: V1, V2 and V6 take the engine's status and reason; V3 to V5 are still assessed

@pytest.mark.parametrize("status", ["insufficient_data", "not_applicable"])
def test_v1_v2_v6_take_the_engines_status_and_reason(status):
    reason = f"The engine's own reason for {status} (test)."
    r = checks(Valuation(status, reason, ()))
    for check_id in ("V1", "V2", "V6"):
        assert (r[check_id].status, r[check_id].value, r[check_id].explanation) == (status, None, reason)
    assert [r[c].status for c in ("V3", "V4", "V5")] == ["fail", "fail", "fail"]  # S9-E5 and S9-E7, still assessed


# Missing figures and benchmarks: "insufficient data", naming them

@pytest.mark.parametrize("missing, blocked", [("net_income", ("V3", "V4")), ("equity", ("V5",))])
def test_a_missing_figure_gives_insufficient_data(missing, blocked):
    r = checks(data=company(**{missing: None}))
    for check_id in blocked:
        assert (r[check_id].status, r[check_id].value) == ("insufficient_data", None)
        assert missing.replace("_", " ") in r[check_id].explanation


@pytest.mark.parametrize("check_id, benchmark, words", [
    ("V3", "industry_pe", "industry"), ("V4", "market_pe", "market"), ("V5", "industry_pb", "industry")])
def test_a_missing_benchmark_gives_insufficient_data(check_id, benchmark, words):
    result = checks(**{benchmark: None})[check_id]
    assert (result.status, result.value) == ("insufficient_data", None)
    assert words in result.explanation


def test_the_texts_say_the_estimate_never_fair_value_cheap_or_expensive():
    cases = (checks(), checks(estimate(20.0, 20.0, g1=CAP), price=15.0), checks(estimate(20.0), price=16.0),
             checks(data=company(net_income=-50, equity=-1791)), results())
    for case in cases:
        for r in case.values():
            assert not any(word in r.explanation.lower() for word in BANNED), r.explanation


def test_price_to_earnings_and_to_book_double_when_the_share_count_doubles():
    # The rule itself ((price × shares) ÷ net income or equity): the other test companies all have 100 million
    # shares, so a formula that ignored the share count would pass them (planted-bug check, 25 November).
    one, two = checks(data=company(shares=100)), checks(data=company(shares=200))
    for check_id in ("V3", "V4", "V5"):
        assert two[check_id].value == pytest.approx(2 * one[check_id].value)


# --- Review of 25 November (code and test reviewers; Flo: "yes, as recommended") -------------------------------------
# Expected results are the rules themselves (a bad input gives "insufficient data" naming it), except S9-R9, Flo's
# confirmed hand working: 0.5 × 20.00 = 10.00; 12.00 > 10.00, so V2 fails.

@pytest.mark.parametrize("price", [0.0, -5.0, float("nan"), float("inf")])
def test_r1_a_price_that_is_not_above_zero_makes_the_whole_area_insufficient_data(price):
    r = checks(Valuation("insufficient_data", "Insufficient data: share price: not usable.", ()), price=price)
    assert [(x.status, x.value) for x in r.values()] == [("insufficient_data", None)] * 6
    assert all("the share price must be a number above zero" in x.explanation for x in r.values())


@pytest.mark.parametrize("count", [0, -100])
def test_r2_a_share_count_not_above_zero_makes_the_whole_area_insufficient_data(count):
    r = checks(Valuation("insufficient_data", "Insufficient data: shares: zero or negative.", ()),
               company(shares=count))
    assert [(x.status, x.value) for x in r.values()] == [("insufficient_data", None)] * 6
    assert all("share count" in x.explanation for x in r.values())
    assert all("shares" in [f.metric for f in x.inputs] for x in r.values())  # traceable on the sources page


@pytest.mark.parametrize("check_id, benchmark", [("V3", "industry_pe"), ("V4", "market_pe"), ("V5", "industry_pb")])
def test_r3_a_benchmark_marked_missing_gives_insufficient_data_with_its_reason(check_id, benchmark):
    gap = Fact("pe" if benchmark != "industry_pb" else "pb", None, "pure", None, FY0, "missing", None, None, None,
               None, None, "the source cell is blank (test)")
    result = checks(**{benchmark: gap})[check_id]
    assert (result.status, result.value) == ("insufficient_data", None)
    assert "the source cell is blank (test)" in result.explanation


@pytest.mark.parametrize("value", [0.0, -5.0])
@pytest.mark.parametrize("check_id, benchmark", [("V3", "industry_pe"), ("V4", "market_pe"), ("V5", "industry_pb")])
def test_r4_a_benchmark_of_zero_or_below_gives_insufficient_data(check_id, benchmark, value):
    # Decision 1 of the review (Flo): like the industry beta in the engine, a benchmark ≤ 0 is not usable.
    result = checks(**{benchmark: value})[check_id]
    assert (result.status, result.value) == ("insufficient_data", None)
    assert "zero or negative" in result.explanation


def test_r5_the_cap_line_does_not_appear_just_below_the_cap():
    line = "already at the 30% cap"
    assert line not in checks(estimate(20.0, 25.0, g1=0.2999), price=15.0)["V6"].explanation


def test_r6_ratios_that_round_to_the_same_number_are_shown_with_more_decimals():
    # P/E 19.999 against 20: with two decimals both would read "20.00" next to a pass.
    v3 = checks(price=19.999)["V3"]
    assert v3.status == "pass"
    assert "Price to earnings 19.999 " in v3.explanation and "against 20.000 for the industry" in v3.explanation
    v4 = checks(price=19.999)["V4"].explanation
    assert "Price to earnings 19.999 " in v4 and "against 20.000 for the US market" in v4
    assert "Price to earnings 20.00 " in checks(price=20.0)["V3"].explanation  # exactly equal: two decimals (S9-E5)


def test_r7_v2_and_v6_say_above_below_or_equal():
    synthetic_case = results()
    assert ("The share price you typed, USD 30.00, is above USD 16.10, which is 80% of the estimate (USD 20.13)."
            in synthetic_case["V2"].explanation)
    assert ("The share price you typed, USD 30.00, is below the estimate with starting growth at the 30% cap "
            "(USD 37.37)." in synthetic_case["V6"].explanation)
    e3 = checks(estimate(20.0), price=16.0)["V2"]
    assert "is equal to USD 16.00, which is 80% of the estimate (USD 20.00)." in e3.explanation
    e4 = checks(estimate(20.0, 25.0), price=25.0)["V6"]
    assert "is equal to the estimate with starting growth at the 30% cap (USD 25.00)." in e4.explanation


def test_s9_r9_v2_reads_its_share_of_the_estimate_from_the_settings():
    half = {**SETTINGS, "valuation": {**SETTINGS["valuation"], "well_below_fair_value": 0.5}}
    v2 = checks(estimate(20.0), price=12.0, settings=half)["V2"]
    assert (v2.status, v2.value) == ("fail", 12.0) and v2.threshold == pytest.approx(10.0)


# --- Review round 2 (Flo: option A, 25 November): values that differ only by computer rounding are equal ------------
# A relative difference below one billionth counts as equal (as growth within 1e-10 of a limit is "at the limit" in
# the engine): the strict checks (V1, V3, V4, V5) fail, the "at or below" checks (V2, V6) pass, both numbers are shown
# with two decimals. Flo's hand working: 2.01 × 1,000,000 = 2,010,000; ÷ 100,000 = 20.1 exactly (row S9-T1).

def test_s9_t1_a_price_to_earnings_equal_to_the_benchmark_by_hand_fails():
    v3 = checks(data=company(net_income=0.1, shares=1), price=2.01, industry_pe=20.1)["V3"]
    assert v3.status == "fail"
    assert "Price to earnings 20.10 " in v3.explanation and "against 20.10 for the industry" in v3.explanation


@pytest.mark.parametrize("noise", [1e-12, -1e-12])
def test_t_differences_of_one_part_in_a_trillion_are_ties(noise):
    tie = 1 + noise
    r = checks(estimate(20.0, 25.0), price=20.0 * tie)
    assert (r["V1"].status, r["V2"].status) == ("fail", "fail")
    assert "at the estimate" in r["V1"].explanation
    assert checks(estimate(20.0), price=16.0 * tie)["V2"].status == "pass"
    v6 = checks(estimate(20.0, 25.0), price=25.0 * tie)["V6"]
    assert v6.status == "pass" and "is equal to the estimate" in v6.explanation
    r = checks(price=20.0 * tie)  # P/E 20 and P/B 4 against 20 and 4 (S9-E5, S9-E7), up to the noise
    assert [r[c].status for c in ("V3", "V4", "V5")] == ["fail", "fail", "fail"]
    assert "Price to book 4.00 " in r["V5"].explanation


def test_t_differences_of_one_part_in_a_million_still_count():
    near = 1 - 1e-6
    r = checks(estimate(20.0, 25.0), price=20.0 * near)
    assert r["V1"].status == "pass" and "below the estimate" in r["V1"].explanation
    assert checks(estimate(20.0), price=16.0 / near)["V2"].status == "fail"
    assert checks(estimate(20.0, 25.0), price=25.0 / near)["V6"].status == "fail"
    assert checks(price=20.0 * near)["V3"].status == "pass"


# --- Igor's review of #52 (25 November; Flo: "yes, (a) and plan") ---------------------------------------------------
# Expected results are the rules themselves: two different values never print as the same number, the estimate is
# among the inputs, the engine's own status and reason reach V1, V2 and V6 unchanged, a tie has no "−0.0%".

def prices(text: str) -> list[str]:
    """The amounts "USD …" in a text, in order."""
    return re.findall(r"USD ([0-9][0-9,]*\.[0-9]+)", text)


@pytest.mark.parametrize("check_id, valuation, price", [
    ("V1", estimate(20.1295), 20.13),                      # the estimate itself
    ("V2", estimate(18.563), 14.85),                       # 80% of 18.563 is 14.8504
    ("V6", estimate(20.0, 38.0801), 38.08),                # the estimate at the cap
    ("V1", estimate(20.0), 20.0 * (1 + 5e-9)),             # not a tie (option A), but equal to 6 decimals
])
def test_igor_1_a_price_and_a_different_estimate_never_print_the_same(check_id, valuation, price):
    shown = prices(checks(valuation, price=price)[check_id].explanation)
    assert len(shown) >= 2 and shown[0] != shown[1], shown


def test_igor_1_equal_prices_keep_two_decimals():
    assert prices(checks(estimate(20.0), price=16.0)["V2"].explanation)[:2] == ["16.00", "16.00"]
    assert prices(checks(estimate(20.0, 25.0), price=25.0)["V6"].explanation)[:2] == ["25.00", "25.00"]


def test_igor_1_a_ratio_that_is_not_a_tie_never_prints_like_its_benchmark():
    # P/E 20.0000001 against 20: not a tie under option A (5 billionths apart), but equal to six decimals.
    text = checks(price=20.0 * (1 + 5e-9))["V3"].explanation
    ratio, benchmark = re.search(r"Price to earnings (\S+) .* against (\S+) for", text).groups()
    assert ratio != benchmark, text


def test_igor_4_zero_earnings_fail_even_without_benchmarks():
    # Decision c with net income exactly 0 (the −50 case is test_s9_e6_no_earnings_fails_even_without_benchmarks).
    r = checks(data=company(net_income=0), industry_pe=None, market_pe=None)
    assert (r["V3"].status, r["V4"].status) == ("fail", "fail")


def test_igor_5_v1_v2_and_v6_carry_the_estimate_in_their_inputs():
    v = estimate(20.0, 25.0)
    r = checks(v, price=15.0)
    assert v.fair_value in r["V1"].inputs and v.fair_value in r["V2"].inputs
    assert v.fair_value_at_growth_cap in r["V6"].inputs


def synthetic_with(metric: str, years: tuple[int, ...], millions: float | None) -> CompanyData:
    """The synthetic company with one line item replaced in some years; None makes it `missing`, never zero."""
    data = synthetic.company_data()
    items = {m: dict(by_year) for m, by_year in data.items.items()}
    for year in years:
        old = items[metric][date(year, 12, 31)]
        items[metric][old.period_end] = (
            dataclasses.replace(old, value=None, kind="missing", tag=None, form=None, accession=None,
                                note=f"no annual 10-K figure for {metric} (test)")
            if millions is None else dataclasses.replace(old, value=millions * MILLION))
    return dataclasses.replace(data, items=items)


@pytest.mark.parametrize("data, status", [
    (lambda: synthetic_with("capital_expenditure", (2023, 2024, 2025), 10_000), "not_applicable"),  # no free cash flow
    (lambda: synthetic_with("revenue", (2021,), None), "insufficient_data"),                        # revenue FY-4 missing
])
def test_igor_6_the_real_engines_status_and_reason_reach_v1_v2_and_v6(data, status):
    company_data = data()
    v = value_company(company_data, SETTINGS, share_price=PRICE, risk_free_rate=RISK_FREE, unlevered_beta=BETA)
    assert v.status == status and v.reason
    r = valuation_checks(company_data, SETTINGS, v, share_price=PRICE, industry_pe=INDUSTRY_PE, market_pe=MARKET_PE,
                         industry_pb=INDUSTRY_PB)
    for result in (r[0], r[1], r[5]):  # V1, V2, V6
        assert (result.status, result.value, result.explanation) == (status, None, v.reason)


def test_estimate_gap_is_plain_zero_on_a_tie():
    gap = estimate_gap(20.0 * (1 - 1e-12), 20.0)  # a tie under option A
    assert gap == 0.0 and math.copysign(1.0, gap) == 1.0 and f"{gap:.1%}" == "0.0%"
