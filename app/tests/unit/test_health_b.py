"""S6 rule/edge/property tests, SPEC §7. Appendix A acceptance awaits Greg.

The constructed threshold examples come from the published rules (40%, 20%, 5x),
not the app's output. No locked Appendix A expected values are used.
"""
from dataclasses import replace
from datetime import date, timedelta

import pytest
from hypothesis import given, strategies as st

from src.contracts import CompanyData, Fact
from src.checks.health import health_checks


SETTINGS = {"max_net_debt_to_equity": 0.40, "min_operating_cash_flow_to_debt": 0.20,
            "min_interest_cover": 5.0}


def company():
    items = {}
    for metric, value in {"revenue": 100, "current_assets": 100, "current_liabilities": 100,
                          "total_liabilities": 200, "equity": 100, "cash": 0, "financial_debt": 40,
                          "operating_cash_flow": 20, "operating_income": 5, "interest_expense": 1}.items():
        flow = metric in {"revenue", "operating_cash_flow", "operating_income", "interest_expense"}
        items[metric] = {date(y, 12, 31): Fact(metric, value, "USD", date(y, 1, 1) if flow else None,
                                             date(y, 12, 31), "assumption", None, None, None, None, None,
                                             "SYNTHETIC DATA: SPEC §7 threshold example, not Appendix A.")
                         for y in range(2021, 2026)}
    return CompanyData("TEST", "0000000000", "SYNTHETIC DATA", None, None, "1231", None, None, items)


def change(data, metric, value, year=2025):
    fact = data.fact(metric, date(year, 12, 31))
    return data.with_fact(replace(fact, value=value, kind="missing" if value is None else "assumption",
                                  note="SYNTHETIC DATA: missing" if value is None else "SYNTHETIC DATA: boundary change"))


def run(data, settings=SETTINGS):
    return {r.check_id: r for r in health_checks(data, settings=settings)}


def test_six_checks_and_strict_cover_and_debt_boundaries():
    checks = run(company())
    assert tuple(checks) == ("H1", "H2", "H3", "H4", "H5", "H6")
    assert checks["H1"].status == "fail"   # current assets equal current liabilities
    assert checks["H2"].status == "fail"   # current assets equal long-term liabilities
    assert checks["H3"].status == "fail"   # net debt is exactly 40% of equity
    assert checks["H4"].status == "fail"   # unchanged debt/equity is not falling
    assert checks["H6"].status == "pass"   # exactly 5x passes


def test_h5_includes_exactly_twenty_percent():
    data = change(company(), "financial_debt", 100)
    assert run(data)["H5"].status == "pass"
    assert run(change(data, "operating_cash_flow", 19))["H5"].status == "fail"


def test_h2_subtracts_the_current_portion_from_total_liabilities():
    # Holding total liabilities fixed, more current liabilities means less long-term cover needed.
    assert run(change(company(), "current_liabilities", 101))["H2"].status == "pass"


@given(st.integers(min_value=2, max_value=100))
def test_h4_scales_each_year_with_its_own_equity(factor):
    data = company()
    scaled_old = change(change(data, "financial_debt", 40 * factor, 2021), "equity", 100 * factor, 2021)
    first, second = run(data)["H4"], run(scaled_old)["H4"]
    assert first.threshold == pytest.approx(second.threshold)
    assert first.status == second.status


def test_h3_uses_cash_and_is_not_gross_debt_to_equity():
    assert run(company())["H3"].status == "fail"
    assert run(change(company(), "cash", 1))["H3"].status == "pass"
    assert run(change(company(), "cash", 100))["H3"].status == "pass"


@pytest.mark.parametrize("equity", [0, -1])
def test_h3_nonpositive_equity_fails_without_dividing(equity):
    data = change(change(company(), "equity", equity), "cash", None)
    check = run(data)["H3"]
    assert check.status == "fail" and check.value is None
    assert "negative equity" in check.explanation.lower()
    assert all(f.kind != "missing" for f in check.inputs)


def test_h4_no_debt_in_both_years_passes_even_without_equity():
    data = change(change(company(), "financial_debt", 0), "financial_debt", 0, 2021)
    data = change(change(data, "equity", None), "equity", None, 2021)
    assert run(data)["H4"].status == "pass"


@pytest.mark.parametrize("year", [2021, 2025])
@pytest.mark.parametrize("equity", [0, -1])
def test_h4_nonpositive_equity_is_unassessed_under_general_denominator_rule(year, equity):
    check = run(change(company(), "equity", equity, year))["H4"]
    assert check.status == "insufficient_data" and check.value is None
    assert "equity" in check.explanation.lower()


def test_h4_compares_four_years_earlier_and_uses_gross_debt():
    data = change(company(), "financial_debt", 100, 2021)
    before = run(data)["H4"]
    assert before.status == "pass"
    assert run(change(data, "cash", 100000))["H4"] == before
    assert {f.period_end.year for f in before.inputs} == {2021, 2025}


def test_h5_zero_debt_passes_without_cash_flow():
    data = change(change(company(), "financial_debt", 0), "operating_cash_flow", None)
    check = run(data)["H5"]
    assert check.status == "pass" and check.value is None
    assert "no debt" in check.explanation.lower()


def test_h6_reported_zero_interest_passes_without_division_or_operating_income():
    data = change(change(company(), "interest_expense", 0), "operating_income", None)
    check = run(data)["H6"]
    assert check.status == "pass" and check.value is None
    assert all(f.kind != "missing" for f in check.inputs)


def test_h6_missing_interest_never_becomes_zero_even_with_no_debt():
    data = change(change(company(), "interest_expense", None), "financial_debt", 0)
    assert run(data)["H6"].status == "insufficient_data"


def test_h6_does_not_require_debt_when_operating_profit_and_interest_are_known():
    assert run(change(company(), "financial_debt", None))["H6"].status == "pass"


def test_h6_operating_loss_fails_and_negative_interest_is_unassessed():
    assert run(change(company(), "operating_income", -1))["H6"].status == "fail"
    assert run(change(company(), "interest_expense", -1))["H6"].status == "insufficient_data"


@pytest.mark.parametrize("metric,check", [
    ("current_assets", "H1"), ("total_liabilities", "H2"), ("cash", "H3"),
    ("financial_debt", "H4"), ("operating_cash_flow", "H5"), ("interest_expense", "H6"),
])
def test_required_missing_inputs_remain_unassessed(metric, check):
    result = run(change(company(), metric, None))[check]
    assert result.status == "insufficient_data" and result.value is None
    assert any(f.kind == "missing" for f in result.inputs)
    assert result.explanation


def test_h4_does_not_compress_a_missing_oldest_year():
    data = company()
    items = {m: {d: f for d, f in values.items() if d.year != 2021} for m, values in data.items.items()}
    assert run(replace(data, items=items))["H4"].status == "insufficient_data"


def test_wrong_money_units_and_partial_cash_flow_are_unassessed():
    data = company()
    cash = data.fact("cash", date(2025, 12, 31))
    flow = data.fact("operating_cash_flow", date(2025, 12, 31))
    assert run(data.with_fact(replace(cash, unit="pure")))["H3"].status == "insufficient_data"
    assert run(data.with_fact(replace(flow, period_start=date(2025, 4, 1))))["H5"].status == "insufficient_data"


@given(st.integers(min_value=1, max_value=10**8))
def test_common_currency_scaling_keeps_health_results(scale):
    data = company()
    scaled = replace(data, items={m: {d: replace(f, value=f.value * scale) for d, f in values.items()}
                                 for m, values in data.items.items()})
    original, changed = run(data), run(scaled)
    assert [r.status for r in changed.values()] == [r.status for r in original.values()]
    for check in ("H3", "H4", "H5", "H6"):
        assert changed[check].value == pytest.approx(original[check].value)


def test_empty_company_has_no_assessed_health_checks():
    assert all(r.status == "insufficient_data" for r in run(replace(company(), items={})).values())


@pytest.mark.parametrize("latest,old,expected", [
    ((99_999_998, 99_999_999), (99_999_999, 100_000_000), "pass"),
    ((99_999_999, 100_000_000), (99_999_998, 99_999_999), "fail"),
])
def test_h4_preserves_exact_order_when_displayed_ratios_tie(latest, old, expected):
    # The cross-products differ by 1; a displayed float tie must not hide falling debt.
    data = company()
    for year, (debt, equity) in ((2025, latest), (2021, old)):
        data = change(change(data, "financial_debt", debt, year), "equity", equity, year)
    assert run(data)["H4"].status == expected


def test_h2_does_not_round_away_the_current_liability_before_comparing_cover():
    # 10^16 > 10^16 - 1 exactly. The difference rounds back to 10^16 as a float.
    data = change(change(change(company(), "current_assets", 10**16),
                         "total_liabilities", 10**16), "current_liabilities", 1)
    assert run(data)["H2"].status == "pass"


def test_h3_does_not_round_away_cash_before_comparing_with_forty_percent():
    # (10^16 - 1)/(25*10^15) < 2/5: multiply by 5 to get 5*10^16 - 5 < 5*10^16.
    data = change(change(change(company(), "financial_debt", 10**16),
                         "cash", 1), "equity", 25 * 10**15)
    assert run(data)["H3"].status == "pass"


def test_h6_below_five_times_does_not_pass_when_the_displayed_ratio_rounds_up():
    # 15,000,000,000,000,004 < 5 * 3,000,000,000,000,001 by 1; both inputs are exact floats.
    data = change(change(company(), "operating_income", 15_000_000_000_000_004),
                  "interest_expense", 3_000_000_000_000_001)
    assert run(data)["H6"].status == "fail"


def test_h5_preserves_a_configured_minimum_when_the_ratio_rounds_up():
    # At a configurable 75% minimum: 4*9,007,199,254,740,994 is 2 below
    # 3*12,009,599,006,321,326. The exact ratio is below 3/4, despite displaying 0.75.
    data = change(change(company(), "operating_cash_flow", 9_007_199_254_740_994),
                  "financial_debt", 12_009_599_006_321_326)
    settings = dict(SETTINGS, min_operating_cash_flow_to_debt=.75)
    assert run(data, settings)["H5"].status == "fail"


@pytest.mark.parametrize("days,expected", [
    (349, "insufficient_data"), (350, "pass"), (379, "pass"),
    (380, "pass"), (381, "insufficient_data"),
])
def test_cash_flow_boundaries_use_the_resolvers_elapsed_days(days, expected):
    data = company()
    original = data.fact("operating_cash_flow", date(2025, 12, 31))
    data = data.with_fact(replace(original, period_start=original.period_end - timedelta(days=days)))
    assert run(data)["H5"].status == expected


def test_decimal_long_term_cover_equality_fails_the_strict_rule():
    data = change(change(change(company(), "current_assets", .1),
                         "total_liabilities", .3), "current_liabilities", .2)
    assert run(data)["H2"].status == "fail"  # 0.1 == 0.3 - 0.2


def test_decimal_net_debt_equal_to_forty_percent_fails_the_strict_rule():
    data = change(change(change(company(), "financial_debt", .3), "cash", .2), "equity", .25)
    assert run(data)["H3"].status == "fail"  # (0.3 - 0.2) / 0.25 == 0.4


def test_equal_decimal_debt_ratios_are_not_falling():
    data = change(change(company(), "financial_debt", .3), "equity", .1)
    data = change(change(data, "financial_debt", .9, 2021), "equity", .3, 2021)
    assert run(data)["H4"].status == "fail"  # 0.3/0.1 == 0.9/0.3 == 3


def test_decimal_cash_flow_equal_to_twenty_percent_passes_the_inclusive_rule():
    data = change(change(company(), "operating_cash_flow", .3), "financial_debt", 1.5)
    assert run(data)["H5"].status == "pass"  # 0.3/1.5 == 0.2


def test_decimal_interest_cover_equal_to_five_passes_the_inclusive_rule():
    data = change(change(company(), "operating_income", .25), "interest_expense", .05)
    assert run(data)["H6"].status == "pass"  # 0.25/0.05 == 5
