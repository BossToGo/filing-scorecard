"""The valuation method of issue #71, items 2 to 4 (slice S8b). Owner: C (Flo).

Every expected result is the rule itself, a relation between two figures of the same run, or a figure recorded in a
published source. No worked valuation number is here: those are Flo's (Appendix A, docs/acceptance.md).
The rules (Flo's decisions of 27 November 2026, issue #71):
- starting free cash flow = operating cash flow − capital expenditure of the last twelve months;
- financial debt, minority interest and shares from the latest balance sheet; a missing one is "insufficient data";
- long-run growth = the risk-free rate;
- equity risk premium: Damodaran's implied premium, 4.41% on 1 November 2026;
- one sentence when the twelve months are more than 25% above or below the plain average of the free cash flow of the
  last three fiscal years; when that average cannot be worked out, the estimate stays and a sentence says so.
"""

from __future__ import annotations

import dataclasses
from datetime import date

import pytest
import yaml

from src.checks.valuation import valuation_checks
from src.contracts import Fact
from src.settings import SETTINGS_FILE, load_settings
from src.valuation.equity_method import levered_beta, value_company
from tests.fixtures import synthetic
from tests.unit.valuation_data import FY0, MILLION, latest, synthetic_company, without_latest

SETTINGS = load_settings()
V = SETTINGS["valuation"]
PRICE = synthetic.inputs()["share_price"]


def rate(value: float, metric: str = "risk_free_rate") -> Fact:
    return Fact(metric, value, "pure", None, FY0, "assumption", None, None, None, None, None,
                f"{metric} of the synthetic company (SYNTHETIC DATA)")


def value(data=None, *, price=PRICE, risk_free=0.04, settings=SETTINGS):
    return value_company(synthetic_company() if data is None else data, settings, share_price=price,
                         risk_free_rate=rate(risk_free), unlevered_beta=rate(0.90, "unlevered_beta"))


def annual(metric: str, year: int, millions: float | None, data):
    old = data.fact(metric, date(year, 12, 31))
    if millions is None:
        return data.with_fact(dataclasses.replace(old, value=None, kind="missing", tag=None, form=None,
                                                  accession=None, note=f"no annual figure for {metric} (test)"))
    return data.with_fact(dataclasses.replace(old, value=millions * MILLION))


# --- item 2: the starting free cash flow is the last twelve months ----------------------------------------------------


def test_the_starting_free_cash_flow_is_the_last_twelve_months():
    v = value(latest("capital_expenditure", 100, latest("operating_cash_flow", 300)))
    assert v.starting_free_cash_flow.value == 200 * MILLION  # 300 − 100
    assert (v.starting_free_cash_flow.kind, v.starting_free_cash_flow.unit) == ("derived", "USD")
    assert v.forecast.years[0].free_cash_flow == pytest.approx(200 * MILLION * (1 + v.forecast.years[0].growth))


def test_the_annual_figures_do_not_change_the_starting_free_cash_flow():
    changed = annual("operating_cash_flow", 2025, 500, synthetic_company())
    assert value(changed).starting_free_cash_flow.value == value().starting_free_cash_flow.value
    assert value(changed).fair_value.value == value().fair_value.value


def test_the_note_and_dates_of_the_starting_free_cash_flow_are_those_of_the_twelve_months():
    end, start = date(2026, 10, 2), date(2025, 9, 27)
    data = synthetic_company()
    flows = {m: dataclasses.replace(data.recent[m], period_start=start, period_end=end)
             for m in ("operating_cash_flow", "capital_expenditure")}
    v = value(dataclasses.replace(data, recent={**data.recent, **flows}))
    fcf = v.starting_free_cash_flow
    assert (fcf.period_start, fcf.period_end) == (start, end)
    assert "twelve months to 2 October 2026" in fcf.note
    assert v.fair_value.period_end == end
    assert v.average_free_cash_flow.period_end == FY0  # the comparison stays dated by its fiscal years
    # 3 (review): the inputs hold the twelve-month figures themselves, not only the annual ones of the comparison
    assert flows["operating_cash_flow"] in v.inputs and flows["capital_expenditure"] in v.inputs


@pytest.mark.parametrize("metric, words", [
    ("operating_cash_flow", ["operating cash flow", "last twelve months"]),
    ("capital_expenditure", ["capital expenditure", "last twelve months"]),
    ("financial_debt", ["financial debt", "latest balance sheet"]),
    ("minority_interest", ["minority interest", "latest balance sheet"]),
    ("shares", ["shares", "latest report"]),
])
@pytest.mark.parametrize("how", ["missing", "no entry"])
def test_a_missing_latest_figure_is_insufficient_data_with_no_fallback_to_the_annual_one(metric, words, how):
    data = latest(metric, None) if how == "missing" else without_latest(metric)
    v = value(data)
    assert v.status == "insufficient_data" and v.fair_value is None and v.starting_free_cash_flow is None
    for word in words:
        assert word in v.reason, v.reason


def test_a_company_with_no_latest_figures_names_all_five():
    v = value(dataclasses.replace(synthetic.company_data(), recent={}))
    assert v.status == "insufficient_data"
    for word in ("operating cash flow", "capital expenditure", "financial debt", "minority interest", "shares"):
        assert word in v.reason


@pytest.mark.parametrize("metric, millions, words", [
    ("capital_expenditure", -85, ["capital expenditure", "negative"]),
    ("financial_debt", -450, ["financial debt", "negative"]),
    ("shares", 0, ["shares", "zero or negative"]),
])
def test_an_unusable_latest_figure_is_insufficient_data(metric, millions, words):
    v = value(latest(metric, millions))
    assert v.status == "insufficient_data"
    for word in words:
        assert word in v.reason


@pytest.mark.parametrize("operating", [85, 50], ids=["exactly zero", "negative"])
def test_no_free_cash_flow_in_the_last_twelve_months_means_not_applicable(operating):
    # Capital expenditure is 85; the three fiscal years before are positive and do not rescue the model.
    v = value(latest("operating_cash_flow", operating))
    assert v.status == "not_applicable" and v.fair_value is None and v.fair_value_at_growth_cap is None
    assert v.starting_free_cash_flow.value <= 0  # shown, so the reader sees why
    assert "last twelve months" in v.reason and "free cash flow" in v.reason
    assert v.notes == ()


def test_a_positive_twelve_months_gives_an_estimate_even_after_three_years_without_free_cash_flow():
    data = synthetic_company()
    for year in (2023, 2024, 2025):
        data = annual("operating_cash_flow", year, 10, data)
    assert value(data).status == "ok"


# --- item 1: the latest balance sheet ---------------------------------------------------------------------------------


def test_the_beta_uses_the_latest_debt_and_shares():
    v = value(latest("shares", 200, latest("financial_debt", 600)))
    expected, _ = levered_beta(0.90, 600 * MILLION, PRICE * 200 * MILLION, V["tax_rate"], V["beta_min"], V["beta_max"])
    assert v.levered_beta.value == pytest.approx(expected)


def test_the_latest_minority_interest_is_subtracted_and_the_latest_shares_divide():
    v = value(latest("shares", 200, latest("minority_interest", 100)))
    assert v.equity_value.value == pytest.approx(v.forecast.present_value - 100 * MILLION)
    assert v.fair_value.value == pytest.approx(v.equity_value.value / (200 * MILLION))
    assert v.fair_value_at_growth_cap.value > v.fair_value.value


@pytest.mark.parametrize("metric", ["financial_debt", "minority_interest"])
def test_the_annual_balance_sheet_does_not_change_the_estimate(metric):
    assert value(annual(metric, 2025, 999, synthetic_company())).fair_value.value == value().fair_value.value


# --- item 3: long-run growth is the risk-free rate --------------------------------------------------------------------


@pytest.mark.parametrize("risk_free", [0.02, 0.0393, 0.06])
def test_long_run_growth_is_the_risk_free_rate(risk_free):
    v = value(risk_free=risk_free)
    assert v.terminal_growth.value == risk_free
    assert "risk-free rate" in v.terminal_growth.note
    f = v.forecast
    assert f.terminal_value == pytest.approx(
        f.years[-1].free_cash_flow * (1 + risk_free) / (v.cost_of_equity.value - risk_free))


def test_there_is_no_fixed_limit_on_long_run_growth_any_more():
    assert "terminal_growth_cap" not in V


# --- item 4: the equity risk premium ----------------------------------------------------------------------------------


def test_the_premium_is_damodarans_of_1_november_2026_with_its_source_recorded():
    # Source: Damodaran's home page, "Implied ERP on November 1, 2026" = 4.41% (issue #71, item 4).
    assert V["equity_risk_premium"] == 0.0441
    assert V["equity_risk_premium_date"] == date(2026, 11, 1)
    entry = yaml.safe_load(SETTINGS_FILE.read_text(encoding="utf-8"))["valuation"]["equity_risk_premium"]
    assert "https://pages.stern.nyu.edu/~adamodar/" in entry["reason"]
    assert "1 November 2026" in entry["reason"] and "4.41%" in entry["reason"]


def test_the_screen_note_of_the_premium_names_damodaran_and_the_date():
    note = value().equity_risk_premium.note
    assert "4.41%" in note and "Damodaran" in note and "1 November 2026" in note
    assert "not read from a filing" in note


def test_the_premium_date_comes_from_the_settings():
    settings = {**SETTINGS, "valuation": {**V, "equity_risk_premium_date": date(2027, 1, 1)}}
    assert "1 January 2027" in value(settings=settings).equity_risk_premium.note


# --- the sentence when the twelve months differ a lot from the three years --------------------------------------------


def comparison(operating: float, *, capex: float = 100, settings=SETTINGS, data=None):
    """The three fiscal years have a free cash flow of 40, 80 and 180: an average of exactly 100, which is neither
    the latest year nor the middle one (operating cash flow = capex + free cash flow)."""
    data = synthetic_company() if data is None else data
    for year, spent, free in zip((2023, 2024, 2025), (75, 80, 85), (40, 80, 180)):
        data = annual("operating_cash_flow", year, spent + free, data)
    data = latest("capital_expenditure", capex, latest("operating_cash_flow", operating, data))
    return value(data, settings=settings)


def sentences(v) -> list[str]:
    return [line for line in v.notes if "last three fiscal years" in line]


def test_the_threshold_is_25_percent():
    assert V["fcf_difference_warning"] == 0.25


@pytest.mark.parametrize("operating", [200, 225, 175], ids=["the same", "exactly 25% above", "exactly 25% below"])
def test_no_sentence_up_to_the_threshold(operating):
    v = comparison(operating)  # twelve months: operating − 100, against an average of 100
    assert v.status == "ok" and sentences(v) == []


@pytest.mark.parametrize("operating, word, shown", [(226, "above", "USD 126 million"), (174, "below", "USD 74 million")])
def test_one_sentence_beyond_the_threshold(operating, word, shown):
    v = comparison(operating)
    assert v.status == "ok"
    (line,) = sentences(v)
    assert word in line and shown in line and "USD 100 million" in line and "26.0%" in line
    assert v.average_free_cash_flow.value == pytest.approx(100 * MILLION)


def test_the_threshold_comes_from_the_settings():
    settings = {**SETTINGS, "valuation": {**V, "fcf_difference_warning": 0.50}}
    assert sentences(comparison(226, settings=settings)) == []


def test_the_average_is_the_plain_average_of_the_three_years():
    v = value()
    flows = [f.value for f in v.base_free_cash_flows]
    assert [f.period_end.year for f in v.base_free_cash_flows] == [2023, 2024, 2025]
    assert v.average_free_cash_flow.value == pytest.approx(sum(flows) / 3)
    assert v.free_cash_flow_margin is None  # the margin is no longer part of the method


@pytest.mark.parametrize("operating", [0, -50], ids=["average zero", "average negative"])
def test_an_average_of_zero_or_less_also_gets_the_sentence_without_a_percentage(operating):
    data = synthetic_company()
    for year, spent in zip((2023, 2024, 2025), (75, 80, 85)):
        data = annual("operating_cash_flow", year, spent + operating, data)
    v = value(data)
    assert v.status == "ok"
    (line,) = sentences(v)
    assert "no free cash flow" in line and "%" not in line


@pytest.mark.parametrize("make", [
    lambda: annual("operating_cash_flow", 2023, None, synthetic_company()),
    lambda: annual("capital_expenditure", 2023, -75, synthetic_company()),
], ids=["a year missing", "a sign error in a year"])
def test_without_the_three_years_the_estimate_stays_and_a_sentence_says_so(make):
    v = value(make())
    assert v.status == "ok" and v.fair_value.value == value().fair_value.value
    (line,) = sentences(v)
    assert "cannot be compared" in line and "31 December 2023" in line
    assert v.average_free_cash_flow is None


def test_the_checks_still_work_when_a_comparison_year_is_missing():
    # A missing annual figure is not an input of the estimate, so V1, V2 and V6 are still pass or fail.
    data = annual("operating_cash_flow", 2023, None, synthetic_company())
    v = value(data)
    found = valuation_checks(data, SETTINGS, v, share_price=PRICE, industry_pe=None, market_pe=None, industry_pb=None)
    assert [r.status in ("pass", "fail") for r in (found[0], found[1], found[5])] == [True, True, True]


# --- review of 27 November -------------------------------------------------------------------------------------------


def test_the_checks_follow_the_estimate_when_only_the_annual_share_count_is_missing():
    # The estimate uses the latest share count, V3 to V5 the annual one: the screen and V1, V2, V6 never disagree.
    data = synthetic_company()
    data = dataclasses.replace(data, items={m: v for m, v in data.items.items() if m != "shares"})
    v = value(data)
    assert v.status == "ok"
    found = valuation_checks(data, SETTINGS, v, share_price=PRICE, industry_pe=None, market_pe=None, industry_pb=None)
    assert [r.check_id for r in found] == ["V1", "V2", "V3", "V4", "V5", "V6"]
    assert [r.status in ("pass", "fail") for r in (found[0], found[1], found[5])] == [True, True, True]
    for result in found[2:5]:
        assert result.status == "insufficient_data" and "share count" in result.explanation


def test_a_comparison_year_is_not_listed_twice_among_the_inputs():
    keys = [(f.metric, f.period_end) for f in value().inputs]
    assert len(keys) == len(set(keys))


def test_the_sign_warning_is_mentioned_only_when_the_sources_page_has_it():
    # The sources page lists the warnings about annual figures, not those about the latest figures.
    data = synthetic_company()
    quarter = dataclasses.replace(data.recent["capital_expenditure"], value=-80 * MILLION, period_end=date(2026, 9, 30))
    v = value(dataclasses.replace(data, recent={**data.recent, "capital_expenditure": quarter}))
    assert v.status == "insufficient_data" and "negative" in v.reason and "sign warning" not in v.reason


def test_the_growth_note_and_the_comparison_sentence_are_both_shown():
    data = synthetic_company()
    old = data.fact("revenue", date(2021, 12, 31))
    data = data.with_fact(dataclasses.replace(old, value=300 * MILLION))  # past growth above the cap
    v = value(latest("operating_cash_flow", 400, data))
    assert len(v.notes) == 2
    assert "Revenue grew" in v.notes[0] and "last three fiscal years" in v.notes[1]


def test_the_estimate_at_the_cap_subtracts_the_latest_minority_interest():
    # USD 100 million ÷ 100 million shares = USD 1.00 per share, whatever the estimate itself is.
    without, with_it = value(), value(latest("minority_interest", 100))
    assert with_it.fair_value_at_growth_cap.value == pytest.approx(without.fair_value_at_growth_cap.value - 1.0)


def test_the_estimate_at_the_cap_divides_by_the_latest_shares():
    # With no debt the beta does not depend on the share count, so twice the shares is half the value per share.
    one = value(latest("financial_debt", 0))
    two = value(latest("shares", 200, latest("financial_debt", 0)))
    assert two.fair_value_at_growth_cap.value == pytest.approx(one.fair_value_at_growth_cap.value / 2)


def test_a_record_about_the_latest_minority_interest_carries_its_own_date():
    data = latest("minority_interest", -50)
    dated = dataclasses.replace(data.recent["minority_interest"], period_end=date(2026, 9, 30))
    v = value(dataclasses.replace(data, recent={**data.recent, "minority_interest": dated}))
    assert any("minority interest on 30 September 2026 is negative" in record for record in v.records)
