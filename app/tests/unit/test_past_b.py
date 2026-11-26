"""S5 draft: rule/edge/property tests from SPEC §7; no locked Appendix A answers.

These cases establish comparisons and safety behavior, not Greg's personal numerical sign-off.
The Appendix A known answers are in test_b_appendix_a.py (Greg's sign-off on PR #5, 24 November 2026).
"""
import re
from dataclasses import replace
from datetime import date, timedelta

import pytest
from hypothesis import given, strategies as st

from src.contracts import CompanyData, Fact
from src.checks.past import past_checks


def company():
    items = {}
    for metric, value in {"net_income": 1, "operating_income": 1, "revenue": 2,
                          "equity": 2, "total_assets": 3, "current_liabilities": 1}.items():
        items[metric] = {}
        for year in range(2021, 2026):
            flow = metric in {"net_income", "operating_income", "revenue"}
            end = date(year, 12, 31)
            items[metric][end] = Fact(metric, value, "USD", date(year, 1, 1) if flow else None,
                                      end, "assumption", None, None, None, None, None,
                                      "SYNTHETIC DATA: rule-based boundary example, not Appendix A.")
    return CompanyData("TEST", "0000000000", "SYNTHETIC DATA", None, None, "1231", None, None, items)


def change(data, metric, year, value):
    fact = data.fact(metric, date(year, 12, 31))
    return data.with_fact(replace(fact, value=value, kind="missing" if value is None else "assumption",
                                  note="SYNTHETIC DATA: missing input" if value is None else "SYNTHETIC DATA: changed input"))


def benchmark(metric, value):
    return Fact(metric, value, "pure", None, date(2026, 1, 5), "assumption", None, None,
                None, None, None, "SYNTHETIC DATA: rule boundary benchmark")


def run(data, benchmarks=None, minimum=4):
    return {r.check_id: r for r in past_checks(data, settings={"p1_min_profitable_years": minimum},
                                            benchmarks=benchmarks)}


def test_six_ordered_checks_and_benchmarks_start_unassessed():
    results = run(company())
    assert tuple(results) == ("P1", "P2", "P3", "P4", "P5", "P6")
    for check in ("P4", "P5"):
        assert results[check].status == "insufficient_data"
        assert results[check].value is None
        assert "benchmark" in results[check].explanation.lower()


def test_profitability_requires_four_strictly_positive_years_and_all_inputs():
    data = change(company(), "net_income", 2021, 0)
    assert run(data)["P1"].status == "pass"
    assert run(change(data, "net_income", 2022, 0))["P1"].status == "fail"
    assert run(change(data, "net_income", 2022, None))["P1"].status == "insufficient_data"
    assert run(data, minimum=5)["P1"].status == "fail"


def test_equal_profits_are_not_growth_or_acceleration():
    results = run(company())
    assert results["P2"].status == "fail"
    assert results["P3"].status == "fail"


def test_positive_profit_above_four_years_earlier_passes_p2():
    # Independent rule working: latest 2 USD > old 1 USD, and 2 > 0.
    result = run(change(company(), "net_income", 2025, 2))["P2"]
    assert result.status == "pass"
    assert result.value == 2 and result.threshold == 1


def test_p2_compares_with_four_years_earlier_not_the_year_before():
    # Break-it round (S18): comparing with FY-1 instead of FY-4 was caught by only one test, so two direct cases.
    # FY0 = 5, FY-1 = 9, FY-4 = 3: 5 > 3 and 5 > 0 -> pass (against FY-1 it would fail, 5 < 9).
    data = change(change(change(company(), "net_income", 2025, 5), "net_income", 2024, 9), "net_income", 2021, 3)
    assert run(data)["P2"].status == "pass"
    # FY0 = 5, FY-1 = 3, FY-4 = 9: 5 < 9 -> fail (against FY-1 it would pass, 5 > 3).
    data = change(change(change(company(), "net_income", 2025, 5), "net_income", 2024, 3), "net_income", 2021, 9)
    assert run(data)["P2"].status == "fail"


def test_latest_zero_profit_fails_p3_because_both_growth_rates_are_minus_one():
    # 0/1 - 1 = -1; (0/1) ** (1/4) - 1 = -1. Strict -1 > -1 is false.
    result = run(change(company(), "net_income", 2025, 0))["P3"]
    assert result.status == "fail"
    assert result.value == -1 and result.threshold == -1


@pytest.mark.parametrize("check,metric", [("P4", "roe"), ("P5", "operating_margin")])
def test_missing_benchmark_message_does_not_label_available_company_figures_missing(check, metric):
    result = run(company())[check]
    assert result.status == "insufficient_data"
    assert [f.metric for f in result.inputs if f.kind == "missing"] == [metric]
    assert "benchmark" in result.explanation.lower()
    assert "unavailable figures" not in result.explanation.lower()
    if check == "P5":
        assert "operating income" not in result.explanation.lower()
        assert "revenue" not in result.explanation.lower()


def test_nonzero_equal_compound_growth_does_not_pass_acceleration():
    # Geometric identity: fivefold each year gives the same final growth as its four-year CAGR.
    # NI FY0/FY-1 = 625/125 = 5; (NI FY0/FY-4)^(1/4) = 625^(1/4) = 5.
    data = company()
    for year, value in zip(range(2021, 2026), (1, 5, 25, 125, 625)):
        data = change(data, "net_income", year, value)
    assert run(data)["P3"].status == "fail"


@given(st.integers(min_value=2, max_value=10))
def test_geometric_growth_uses_four_intervals_and_distinguishes_acceleration(factor):
    data = company()
    for offset, year in enumerate(range(2021, 2026)):
        data = change(data, "net_income", year, factor ** offset)
    equal = run(data)["P3"]
    assert equal.status == "fail"
    assert equal.value == pytest.approx(equal.threshold)
    assert run(change(data, "net_income", 2025, factor ** 4 * 2))["P3"].status == "pass"
    assert run(change(data, "net_income", 2025, factor ** 4 / 2))["P3"].status == "fail"


@given(st.integers(min_value=1, max_value=100))
def test_roe_is_invariant_to_redistributing_opening_and_closing_equity(amount):
    data = change(change(company(), "equity", 2024, amount), "equity", 2025, amount + 2)
    balanced = change(change(data, "equity", 2024, amount + 1), "equity", 2025, amount + 1)
    b = {"roe": benchmark("roe", 0)}
    first, second = run(data, b)["P4"], run(balanced, b)["P4"]
    assert first.value == pytest.approx(second.value)
    assert first.status == second.status


def test_overflowing_capital_is_unassessed_instead_of_turning_into_zero_return():
    data = change(change(company(), "total_assets", 2025, 1e308), "current_liabilities", 2025, -1e308)
    assert run(data)["P6"].status == "insufficient_data"


@pytest.mark.parametrize("year", [2021, 2024])
@pytest.mark.parametrize("value", [0, -1])
def test_growth_from_zero_or_a_loss_fails_with_the_required_reason(year, value):
    result = run(change(company(), "net_income", year, value))["P3"]
    assert result.status == "fail"
    assert "growth from a loss is not meaningful" in result.explanation.lower()


def test_a_recent_loss_never_passes_earnings_growth():
    data = change(change(company(), "net_income", 2021, -2), "net_income", 2025, -1)
    assert run(data)["P2"].status == "fail"


def test_latest_year_loss_fails_with_a_loss_reason_without_computing_compound_growth():
    # Greg adopted Flo's policy on 23 November 2026, replacing the earlier unassessed rule.
    result = run(change(company(), "net_income", 2025, -1))["P3"]
    assert result.status == "fail" and result.value is None and result.threshold is None
    assert "the latest year is a loss" in result.explanation.lower()


@pytest.mark.parametrize("year", [2024, 2025])
@pytest.mark.parametrize("value", [0, -1])
@pytest.mark.parametrize("missing_benchmark", [False, True])
def test_roe_nonpositive_equity_fails_even_when_benchmark_is_absent_or_missing(year, value, missing_benchmark):
    data = change(company(), "equity", year, value)
    b = ({"roe": replace(benchmark("roe", 0), value=None, kind="missing", note="Source cell absent.")}
         if missing_benchmark else None)
    check = run(data, b)["P4"]
    assert check.status == "fail"
    assert "negative equity" in check.explanation.lower()
    assert all(f.kind != "missing" for f in check.inputs)


def test_known_nonpositive_equity_is_decisive_despite_other_missing_roe_inputs():
    data = change(change(change(company(), "equity", 2025, -1), "equity", 2024, None),
                  "net_income", 2025, None)
    check = run(data)["P4"]
    assert check.status == "fail"
    assert tuple(f.metric for f in check.inputs) == ("equity",)
    assert check.inputs[0].value == -1


@pytest.mark.parametrize("year", [2024, 2025])
@pytest.mark.parametrize("value", [0, -1])
def test_roe_rejects_nonpositive_equity(year, value):
    result = run(change(company(), "equity", year, value), {"roe": benchmark("roe", 0)})["P4"]
    assert result.status == "fail"
    assert "negative equity" in result.explanation.lower()


def test_matching_benchmarks_fail_because_industry_rules_are_strict():
    # This boundary is constructed from identical source amounts, not a copied Appendix A answer.
    b = {"roe": benchmark("roe", 1), "operating_margin": benchmark("operating_margin", 1)}
    data = company()
    for year in (2024, 2025):
        data = change(data, "equity", year, 1)
    data = change(data, "revenue", 2025, 1)
    assert run(data, b)["P4"].status == "fail"
    assert run(data, b)["P5"].status == "fail"


def test_p6_compares_three_years_earlier_and_not_four():
    data = change(company(), "operating_income", 2022, 0)
    before = run(data)["P6"]
    after = run(change(data, "operating_income", 2021, 1_000_000))["P6"]
    assert before.status == "pass" and after == before
    assert {f.period_end.year for f in before.inputs} == {2022, 2025}


@pytest.mark.parametrize("metric,year,check", [
    ("revenue", 2025, "P5"), ("total_assets", 2025, "P6"), ("total_assets", 2022, "P6"),
])
def test_nonpositive_denominators_do_not_become_ratios(metric, year, check):
    value = 0 if metric == "revenue" else 1  # assets equal current liabilities
    result = run(change(company(), metric, year, value),
                 {"operating_margin": benchmark("operating_margin", 0)})[check]
    assert result.status == "insufficient_data" and result.value is None


def test_missing_year_is_not_silently_replaced_by_an_older_year():
    data = company()
    items = {m: {d: f for d, f in values.items() if d.year != 2024} for m, values in data.items.items()}
    result = run(replace(data, items=items))["P3"]
    assert result.status == "insufficient_data"


def test_cover_page_shares_do_not_move_the_fiscal_year():
    data = company()
    shares = Fact("shares", 100, "shares", None, date(2026, 2, 1), "assumption", None,
                  None, None, None, None, "SYNTHETIC DATA: later cover-page shares")
    assert run(data.with_fact(shares)) == run(data)


def test_annual_flows_and_dollar_units_are_required():
    data = company()
    latest = data.fact("net_income", date(2025, 12, 31))
    short = data.with_fact(replace(latest, period_start=date(2025, 4, 1)))
    wrong_unit = data.with_fact(replace(latest, unit="pure"))
    assert run(short)["P2"].status == "insufficient_data"
    assert run(wrong_unit)["P2"].status == "insufficient_data"


def test_53_week_financial_year_is_accepted():
    data = company()
    latest = data.fact("net_income", date(2025, 12, 31))
    long_year = data.with_fact(replace(latest, period_start=latest.period_end - timedelta(days=370)))
    assert run(long_year)["P2"].status == run(data)["P2"].status


@given(st.integers(min_value=1, max_value=10**8))
def test_common_currency_scaling_does_not_change_ratio_checks(scale):
    data = company()
    b = {"roe": benchmark("roe", 0), "operating_margin": benchmark("operating_margin", 0)}
    scaled = replace(data, items={m: {d: replace(f, value=f.value * scale) for d, f in values.items()}
                                 for m, values in data.items.items()})
    original, changed = run(data, b), run(scaled, b)
    for check in ("P3", "P4", "P5", "P6"):
        assert changed[check].value == pytest.approx(original[check].value)
        assert changed[check].status == original[check].status


def test_an_empty_company_has_no_assessed_checks():
    data = replace(company(), items={})
    assert all(r.status == "insufficient_data" for r in run(data).values())


def test_benchmark_mapping_cannot_silently_use_a_different_metric():
    with pytest.raises(ValueError, match="metric"):
        run(company(), {"roe": benchmark("operating_margin", 0)})


@pytest.mark.parametrize("latest,old,expected", [
    ((99_999_999, 100_000_000), (99_999_998, 99_999_999), "pass"),
    ((99_999_998, 99_999_999), (99_999_999, 100_000_000), "fail"),
])
def test_p6_preserves_exact_order_when_displayed_ratios_tie(latest, old, expected):
    # Cross-products differ by exactly 1: 99,999,999^2 - 99,999,998*100,000,000 = 1.
    data = company()
    for year, (profit, capital) in ((2025, latest), (2022, old)):
        data = change(change(data, "operating_income", year, profit), "total_assets", year, capital + 1)
    assert run(data)["P6"].status == expected


@pytest.mark.parametrize("check,metric,denominator", [
    ("P4", "equity", 3), ("P5", "revenue", 3),
])
def test_industry_comparison_does_not_round_a_higher_ratio_to_its_decimal_benchmark(check, metric, denominator):
    # 1/3 > 0.3333333333333333: 10^16 > 3*3,333,333,333,333,333, by exactly 1.
    # The benchmark is the supplied decimal cell, not an assertion that it equals mathematical 1/3.
    data = change(change(company(), metric, 2025, denominator), metric, 2024, denominator)
    b = {"roe": benchmark("roe", .3333333333333333),
         "operating_margin": benchmark("operating_margin", .3333333333333333)}
    assert run(data, b)[check].status == "pass"


@pytest.mark.parametrize("days,expected", [
    (349, "insufficient_data"), (350, "fail"), (379, "fail"),
    (380, "fail"), (381, "insufficient_data"),
])
def test_annual_flow_boundaries_use_the_resolvers_elapsed_days(days, expected):
    data = company()
    original = data.fact("net_income", date(2025, 12, 31))
    data = data.with_fact(replace(original, period_start=original.period_end - timedelta(days=days)))
    # P2's equal profits fail when annual data is accepted; unavailable periods stay unassessed.
    assert run(data)["P2"].status == expected


@pytest.mark.parametrize("check,metric", [("P4", "net_income"), ("P5", "operating_income")])
def test_decimal_amount_equal_to_decimal_industry_ratio_does_not_pass(check, metric):
    data = change(company(), metric, 2025, .1)
    for year in (2024, 2025):
        data = change(change(data, "equity", year, 1), "revenue", year, 1)
    b = {"roe": benchmark("roe", .1), "operating_margin": benchmark("operating_margin", .1)}
    # 0.10 USD / 1 USD equals the 10% benchmark, so the strict rule fails.
    assert run(data, b)[check].status == "fail"


def test_decimal_geometric_growth_is_not_acceleration():
    data = company()
    for year, value in zip(range(2021, 2026), (.1, .5, 2.5, 12.5, 62.5)):
        data = change(data, "net_income", year, value)
    # Fivefold each year: 62.5/12.5 = 5 and (62.5/0.1)^(1/4) = 5.
    assert run(data)["P3"].status == "fail"


def test_equal_decimal_capital_returns_do_not_improve():
    data = company()
    for year, profit, assets, current in ((2025, .9, .6, .3), (2022, .3, .2, .1)):
        data = change(change(change(data, "operating_income", year, profit),
                             "total_assets", year, assets), "current_liabilities", year, current)
    # 0.9/(0.6-0.3) = 0.3/(0.2-0.1) = 3 exactly in decimal USD.
    assert run(data)["P6"].status == "fail"


# --- Igor's review of #28 (24 November 2026); expected values are hand working written next to each test ---------

def test_p3_known_loss_fails_even_when_the_latest_year_is_missing():
    # SPEC §7 P3: FY-4 or FY-1 <= 0 fails whatever FY0 is, so a missing FY0 cannot change the result
    # (same reasoning as P4's known negative equity). Flo's open point on #28.
    data = change(change(company(), "net_income", 2021, -1), "net_income", 2025, None)
    result = run(data)["P3"]
    assert result.status == "fail"
    assert "loss" in result.explanation.lower()


def test_p3_says_fell_not_grew_by_a_negative_amount():
    # NI 2024 = 1, NI 2025 = 0.9: change -10%. Hand working: 0.9 / 1 - 1 = -0.10.
    result = run(change(company(), "net_income", 2025, 0.9))["P3"]
    assert result.value == pytest.approx(-0.10)
    assert "fell by about 10.00%" in result.explanation
    assert "grew by about -" not in result.explanation and "grew by about −" not in result.explanation


def test_p4_value_is_the_exact_ratio_of_profit_to_average_equity():
    # NI 1, equity 2 and 2: 1 / ((2 + 2) / 2) = 0.5 exactly; benchmark 0.4 -> pass.
    result = run(company(), benchmarks={"roe": benchmark("roe", 0.4)})["P4"]
    assert result.status == "pass" and result.value == 0.5 and result.threshold == 0.4


def test_p5_just_below_the_benchmark_does_not_read_like_a_pass():
    # Operating income 0.99999 on revenue 2: 0.499995 against 0.5 -> fail; rounds to 50.00% on screen.
    data = change(company(), "operating_income", 2025, 0.99999)
    result = run(data, benchmarks={"operating_margin": benchmark("operating_margin", 0.5)})["P5"]
    assert result.status == "fail"
    assert result.value == pytest.approx(0.499995)
    assert "below the industry's 50.00%" in result.explanation


def test_p6_value_and_threshold_are_the_returns_on_capital_employed():
    # 2025: operating income 1 / (assets 3 - current liabilities 1) = 0.5; 2022: the same 0.5 -> not improved.
    result = run(company())["P6"]
    assert result.status == "fail" and result.value == 0.5 and result.threshold == 0.5


def test_amounts_above_one_trillion_are_written_in_full():
    from src.checks._b_inputs import money
    assert money(1.2e15) == "USD 1,200,000,000 million"
    assert "e+" not in money(3.5e12)


# --- Flo's S18 read-only review of B's checks (#64, 26 November): cases no test covered -------------------------

def test_p6_a_worse_return_fails_even_when_both_years_are_losses():
    # Capital employed 3 - 1 = 2 in both years. Now -0.4 / 2 = -20%; three years earlier -0.2 / 2 = -10%.
    # -20% is not above -10% -> fail (comparing sizes without the sign would wrongly pass it: 20% > 10%).
    data = change(change(company(), "operating_income", 2025, -0.4), "operating_income", 2022, -0.2)
    assert run(data)["P6"].status == "fail"


@pytest.mark.parametrize("year", [2025, 2022])
def test_p6_negative_capital_employed_is_not_a_ratio(year):
    # Total assets 0.5 - current liabilities 1 = -0.5: capital employed below zero gives no meaningful return.
    result = run(change(company(), "total_assets", year, 0.5))["P6"]
    assert result.status == "insufficient_data" and result.value is None


def test_p5_negative_revenue_is_not_a_margin():
    # Revenue -2: 1 / -2 = -50% is not an operating margin; the check is not assessed.
    result = run(change(company(), "revenue", 2025, -2), {"operating_margin": benchmark("operating_margin", 0.1)})["P5"]
    assert result.status == "insufficient_data" and result.value is None


@pytest.mark.parametrize("check,metric", [("P4", "roe"), ("P5", "operating_margin")])
def test_a_benchmark_in_a_non_ratio_unit_is_refused_not_compared(check, metric):
    # The contract already refuses a "percent" unit; a benchmark in an allowed but wrong unit (USD) must still never
    # be compared with a decimal ratio.
    wrong = replace(benchmark(metric, 0.15), unit="USD")
    result = run(company(), {metric: wrong})[check]
    assert result.status == "insufficient_data"


@pytest.mark.parametrize("metric,check", [("revenue", "P5"), ("operating_income", "P5")])
def test_a_half_year_figure_is_not_used_as_a_full_year(metric, check):
    # A six-month revenue or operating income would halve or double the margin: not a fiscal-year figure.
    latest = company().fact(metric, date(2025, 12, 31))
    data = company().with_fact(replace(latest, period_start=date(2025, 7, 1)))
    result = run(data, {"operating_margin": benchmark("operating_margin", 0.1)})[check]
    assert result.status == "insufficient_data"
