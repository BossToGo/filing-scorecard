"""Valuation engine, equity method (SPEC v2.3 §8.1–8.3, §8.6; slice S8). Owner: C (Flo).

Where the expected values come from (SPEC rule 14.5, AGENTS.md rule 5):
- Appendix A (synthetic company): `synthetic.expected_valuation(...)`, the values Flo recalculated in his own Excel
  model (`docs/crosscheck/valuation-crosscheck.xlsx`, PR #14) and signed off on PR #5 (CALC-W1–W2, CALC-F1–F4,
  CALC-V6).
- Edge cases: the rule itself (a limited beta equals the limit, a capped growth equals the cap, a missing input
  gives "insufficient data") or the relation between two results of the same run (equity value = present value −
  minority interests). Numbers that need working (the value before a limit, a fair value with a minority interest)
  come from Flo's hand working, recorded in docs/acceptance.md.
- Nvidia's past revenue growth of 68.3% a year: SPEC §8.2, from the 10-Ks it cites.
Never from running `src/valuation/equity_method.py`.
"""

from __future__ import annotations

import dataclasses
from datetime import date

import pytest

from src.contracts import CompanyData, Fact
from src.settings import load_settings
from src.valuation.equity_method import starting_growth, value_company
from tests.fixtures import synthetic

MILLION = 1_000_000.0
FY0 = date(2025, 12, 31)
SETTINGS = load_settings()
PRICE = synthetic.inputs()["share_price"]  # USD 30.00


# --- inputs ----------------------------------------------------------------------------------------------------------


def rate(value: float | None, metric: str = "risk_free_rate") -> Fact | None:
    """A market input as the data layer (S2b) or the benchmark loader (S4) hands it over: a Fact with its source."""
    if value is None:
        return None
    return Fact(metric, value, "pure", None, FY0, "assumption", None, None, None, None, None,
                f"{metric} of the synthetic company (SYNTHETIC DATA: SPEC Appendix A)")


RISK_FREE = rate(synthetic.inputs()["settings"]["risk_free_rate"])  # 4.0%
BETA = rate(synthetic.inputs()["benchmarks"]["unlevered_beta"], "unlevered_beta")  # 0.90


def value(data: CompanyData | None = None, *, price=PRICE, risk_free=RISK_FREE, beta=BETA, settings=SETTINGS):
    return value_company(synthetic.company_data() if data is None else data, settings,
                         share_price=price, risk_free_rate=risk_free, unlevered_beta=beta)


def changed(metric: str, year: int, millions: float | None, data: CompanyData | None = None) -> CompanyData:
    """The synthetic company with one figure replaced; None makes it `missing` with a reason (never zero)."""
    data = synthetic.company_data() if data is None else data
    old = data.fact(metric, date(year, 12, 31))
    if millions is None:
        new = dataclasses.replace(old, value=None, kind="missing", tag=None, form=None, accession=None,
                                  note=f"no annual 10-K figure for {metric} (test)")
    else:
        new = dataclasses.replace(old, value=millions * MILLION)
    return data.with_fact(new)


def without(data: CompanyData, metric: str, year: int | None = None) -> CompanyData:
    """The company with one fiscal year of a line item removed (None: the whole line item)."""
    items = {m: dict(by_year) for m, by_year in data.items.items()}
    if year is None:
        del items[metric]
    else:
        del items[metric][date(year, 12, 31)]
    return dataclasses.replace(data, items=items)


def usd_m(entry: dict) -> float:
    return entry["value"] * MILLION


def pct(entry: dict) -> float:
    return entry["value"] / 100


def tol(entry: dict, scale: float = 1.0) -> float:
    return synthetic.tolerance(entry) * scale


# --- Appendix A, synthetic company (CALC-W1–W2, CALC-F1–F4, V6) -------------------------------------------------------


def test_the_fixture_settings_are_the_settings_of_the_app():
    # Appendix A is worked with these settings; if a setting changes, the expected values no longer apply.
    fixture = synthetic.inputs()["settings"]
    valuation = SETTINGS["valuation"]
    for name in ("equity_risk_premium", "tax_rate", "fcf_base_years", "growth_floor", "growth_cap",
                 "growth_half_life_years", "forecast_years", "beta_min", "beta_max"):
        assert valuation[name] == fixture[name], name
    assert valuation["terminal_growth_cap"] == fixture["terminal_growth"]


def test_the_settings_keep_the_cost_of_equity_above_terminal_growth():
    # SPEC §8.3: with beta_min × premium > 0 the cost of equity is always above gT, so the terminal value exists.
    # src/settings.py (owner A) does not check this yet (review of 24 November), so this test guards C's settings.
    valuation = SETTINGS["valuation"]
    assert valuation["beta_min"] * valuation["equity_risk_premium"] > 0


def test_w1_levered_beta():
    e = synthetic.expected_valuation("levered_beta")
    beta = value().levered_beta
    assert beta.value == pytest.approx(e["value"], abs=tol(e))
    assert (beta.kind, beta.unit) == ("derived", "pure")  # inside 0.8–2.0, so not an assumption


def test_w2_cost_of_equity():
    e = synthetic.expected_valuation("cost_of_equity")
    assert value().cost_of_equity.value == pytest.approx(pct(e), abs=tol(e, 0.01))


def test_f1_base_free_cash_flows_margin_and_starting_free_cash_flow():
    v = value()
    e = synthetic.expected_valuation("base_free_cash_flows")
    assert [f.period_end.year for f in v.base_free_cash_flows] == [2023, 2024, 2025]
    assert [f.value for f in v.base_free_cash_flows] == pytest.approx([x * MILLION for x in e["values"]],
                                                                       abs=tol(e, MILLION))
    e = synthetic.expected_valuation("free_cash_flow_margin")
    assert v.free_cash_flow_margin.value == pytest.approx(pct(e), abs=tol(e, 0.01))
    e = synthetic.expected_valuation("starting_free_cash_flow")
    assert v.starting_free_cash_flow.value == pytest.approx(usd_m(e), abs=tol(e, MILLION))
    assert v.starting_free_cash_flow.unit == "USD"


def test_starting_growth_inside_the_limits_is_derived_not_an_assumption():
    e = synthetic.expected_valuation("starting_growth")
    g1 = value().starting_growth
    assert g1.value == pytest.approx(pct(e), abs=tol(e, 0.01))
    assert g1.kind == "derived"


def test_f2_the_ten_forecast_years():
    e = synthetic.expected_valuation("forecast")
    rows = value().forecast.years
    assert [r.year for r in rows] == list(range(1, 11))
    growth_tol = 0.5 * 10 ** -e["growth_decimals"] / 100
    assert [r.growth for r in rows] == pytest.approx([g / 100 for g in e["growth"]], abs=growth_tol)
    assert [r.free_cash_flow for r in rows] == pytest.approx([x * MILLION for x in e["free_cash_flow"]],
                                                             abs=tol(e, MILLION))
    assert [r.discounted for r in rows] == pytest.approx([x * MILLION for x in e["discounted"]], abs=tol(e, MILLION))


def test_f2_sum_of_discounted_free_cash_flows():
    e = synthetic.expected_valuation("sum_of_discounted_cash_flows")
    assert value().forecast.sum_of_discounted == pytest.approx(usd_m(e), abs=tol(e, MILLION))


def test_f3_terminal_value_discounted_and_its_share():
    f = value().forecast
    e = synthetic.expected_valuation("terminal_value")
    assert f.terminal_value == pytest.approx(usd_m(e), abs=tol(e, MILLION))
    e = synthetic.expected_valuation("discounted_terminal_value")
    assert f.discounted_terminal_value == pytest.approx(usd_m(e), abs=tol(e, MILLION))
    e = synthetic.expected_valuation("terminal_value_share")
    assert f.terminal_value_share == pytest.approx(pct(e), abs=tol(e, 0.01))


def test_f4_equity_value_and_fair_value_per_share():
    v = value()
    assert v.status == "ok" and v.reason == ""
    e = synthetic.expected_valuation("equity_value")
    assert v.equity_value.value == pytest.approx(usd_m(e), abs=tol(e, MILLION))
    e = synthetic.expected_valuation("fair_value_per_share")
    assert v.fair_value.value == pytest.approx(e["value"], abs=tol(e))
    assert (v.fair_value.unit, v.fair_value.kind, v.fair_value.period_end) == ("USD/shares", "derived", FY0)


def test_v6_input_fair_value_with_starting_growth_at_the_cap():
    e = synthetic.expected_valuation("fair_value_at_growth_cap")
    assert value().fair_value_at_growth_cap.value == pytest.approx(e["value"], abs=tol(e))


def test_the_model_fits_the_synthetic_company():
    assert synthetic.expected_valuation("model_fits")["value"] is True
    v = value()
    assert v.status == "ok"
    assert v.notes == ()  # no growth limit, FY0's own free cash flow is positive


def test_the_result_lists_every_figure_it_used():
    used = {(f.metric, f.period_end.year) for f in value().inputs}
    for year in range(2021, 2026):
        assert ("revenue", year) in used
    for year in (2023, 2024, 2025):
        assert ("operating_cash_flow", year) in used and ("capital_expenditure", year) in used
    for metric in ("financial_debt", "shares", "minority_interest", "risk_free_rate", "unlevered_beta"):
        assert (metric, 2025) in used, metric


# --- §8.6 first test: a missing input gives "insufficient data", naming it (E22) -------------------------------------


MISSING_INPUTS = [
    ("revenue FY-2", lambda: changed("revenue", 2023, None), {}, ["revenue", "31 December 2023"]),
    ("revenue FY-4", lambda: changed("revenue", 2021, None), {}, ["revenue", "31 December 2021"]),
    ("operating cash flow FY-1", lambda: changed("operating_cash_flow", 2024, None), {},
     ["operating cash flow", "31 December 2024"]),
    ("capital expenditure FY0, year absent", lambda: without(synthetic.company_data(), "capital_expenditure", 2025),
     {}, ["capital expenditure", "31 December 2025"]),
    ("financial debt FY0", lambda: changed("financial_debt", 2025, None), {}, ["financial debt"]),
    ("shares", lambda: without(synthetic.company_data(), "shares"), {}, ["shares"]),
    ("minority interest reported for FY-1 but not FY0", lambda: changed("minority_interest", 2025, None), {},
     ["minority interest"]),
    ("industry beta", lambda: None, {"beta": None}, ["industry beta"]),
    ("risk-free rate", lambda: None, {"risk_free": None}, ["risk-free rate"]),
    ("share price", lambda: None, {"price": None}, ["share price"]),
    ("revenue FY0 zero", lambda: changed("revenue", 2025, 0), {}, ["revenue", "31 December 2025", "zero or negative"]),
    ("revenue FY-4 negative", lambda: changed("revenue", 2021, -5), {},
     ["revenue", "31 December 2021", "zero or negative"]),
    ("only four fiscal years", lambda: without(synthetic.company_data(), "revenue", 2021), {}, ["five fiscal years"]),
    ("negative capital expenditure (sign error)", lambda: changed("capital_expenditure", 2024, -80), {},
     ["capital expenditure", "negative", "sign warning"]),
    # Added after the review of 24 November (Flo's decisions: any revenue year ≤ 0 and a negative debt are refused).
    ("revenue FY-1 zero (base years would divide by it)", lambda: changed("revenue", 2024, 0), {},
     ["revenue", "31 December 2024", "zero or negative"]),
    ("revenue FY-3 negative", lambda: changed("revenue", 2022, -500), {},
     ["revenue", "31 December 2022", "zero or negative"]),
    ("negative financial debt (sign error)", lambda: changed("financial_debt", 2025, -400), {},
     ["financial debt", "negative"]),
    ("shares zero", lambda: changed("shares", 2025, 0), {}, ["shares", "zero or negative"]),
    ("share price zero", lambda: None, {"price": 0.0}, ["share price", "zero or negative"]),
    ("industry beta zero", lambda: None, {"beta": rate(0.0, "unlevered_beta")}, ["industry beta", "zero or negative"]),
]


@pytest.mark.parametrize("case, make, overrides, words", MISSING_INPUTS, ids=[c[0] for c in MISSING_INPUTS])
def test_e22_a_missing_input_means_no_fair_value_and_names_it(case, make, overrides, words):
    v = value(make(), **overrides)
    assert v.status == "insufficient_data"
    assert v.reason.startswith("Insufficient data")
    for word in words:
        assert word in v.reason, f"{case}: {word!r} not in {v.reason!r}"
    assert v.fair_value is None and v.fair_value_at_growth_cap is None and v.equity_value is None


def test_e22_a_missing_risk_free_fact_counts_like_no_risk_free_rate():
    gap = Fact("risk_free_rate", None, "pure", None, FY0, "missing", None, None, None, None, None,
               "no FRED key and no fallback in settings.yaml")
    v = value(risk_free=gap)
    assert v.status == "insufficient_data" and "risk-free rate" in v.reason
    assert "no FRED key" in v.reason


def test_e22_every_missing_input_is_named_not_only_the_first():
    data = changed("financial_debt", 2025, None, changed("operating_cash_flow", 2023, None))
    v = value(data, beta=None)
    for word in ("financial debt", "operating cash flow", "industry beta"):
        assert word in v.reason


def test_e22_with_four_fiscal_years_the_missing_market_inputs_are_named_too():
    v = value(without(synthetic.company_data(), "revenue", 2021), price=None, beta=None)
    assert v.status == "insufficient_data"
    for word in ("five fiscal years", "share price", "industry beta"):
        assert word in v.reason


def test_a_negative_capex_not_read_from_a_filing_does_not_point_to_a_sign_warning():
    # As in the dividend checks (S7-R2): only a figure read from a filing has the data layer's SIGN warning.
    old = synthetic.company_data().fact("capital_expenditure", date(2024, 12, 31))
    typed = dataclasses.replace(old, value=-80 * MILLION, kind="assumption", tag=None, form=None, accession=None,
                                note="test override")
    v = value(synthetic.company_data().with_fact(typed))
    assert v.status == "insufficient_data"
    assert "negative" in v.reason and "sign warning" not in v.reason


# --- §8.6 second test: the model does not fit, so "not applicable" (E19) ---------------------------------------------


def with_operating_cash_flow(values_2023_to_2025, data=None) -> CompanyData:
    for year, millions in zip((2023, 2024, 2025), values_2023_to_2025):
        data = changed("operating_cash_flow", year, millions, data)
    return data


@pytest.mark.parametrize("cash_flows", [(75, 80, 85), (50, 50, 50)], ids=["three-year FCF exactly zero", "negative"])
def test_e19_no_free_cash_flow_over_three_years_means_not_applicable(cash_flows):
    # Capital expenditure FY2023–FY2025 is 75, 80, 85: equal cash flows give a total of exactly zero.
    v = value(with_operating_cash_flow(cash_flows))
    assert v.status == "not_applicable"
    assert "free cash flow" in v.reason
    assert v.fair_value is None and v.fair_value_at_growth_cap is None
    assert v.starting_free_cash_flow.value <= 0  # shown, so the reader sees why
    # Review of 24 November, M1: no line may claim the three-year margin is positive when the model does not fit.
    assert not any("positive" in line for line in v.notes + v.records)


def test_e19_equity_value_zero_or_below_after_minority_interests_means_not_applicable():
    v = value(changed("minority_interest", 2025, 5000))  # far above the synthetic company's value
    assert v.status == "not_applicable"
    assert "minority interests" in v.reason
    assert v.fair_value is None and v.fair_value_at_growth_cap is None


def test_e22_before_e19_a_missing_input_wins_over_no_free_cash_flow():
    data = changed("financial_debt", 2025, None, with_operating_cash_flow((50, 50, 50)))
    v = value(data)
    assert v.status == "insufficient_data" and "financial debt" in v.reason


# --- the beta (E12, E20) ---------------------------------------------------------------------------------------------


def test_e12_with_zero_debt_the_levered_beta_is_the_unlevered_beta():
    beta = value(changed("financial_debt", 2025, 0)).levered_beta
    assert beta.value == pytest.approx(0.90)
    assert beta.kind == "derived"


# Flo's hand working (S8 cases a and b in docs/acceptance.md): unlevered beta × (1 + 0.79 × 450 ÷ 3,000).
@pytest.mark.parametrize("unlevered, before, limit_name", [(1.9, "2.12515", "beta_max"), (0.5, "0.55925", "beta_min")])
def test_e20_a_beta_outside_the_limits_is_set_to_the_limit_labelled_and_recorded(unlevered, before, limit_name):
    v = value(beta=rate(unlevered, "unlevered_beta"))
    limit = SETTINGS["valuation"][limit_name]
    assert v.levered_beta.value == limit
    assert v.levered_beta.kind == "assumption"
    assert f"= {before} before the limit" in v.levered_beta.note and limit_name in v.levered_beta.note
    # SPEC §10: a limited beta is a record on the sources page, not a warning in the header.
    assert any(r.startswith("BETA_LIMIT:") for r in v.records)
    assert v.status == "ok"
    # Review of 24 November, M2: the cost of equity uses the beta after the limit, not before it (SPEC §8.1).
    assert v.cost_of_equity.value == pytest.approx(RISK_FREE.value + limit * SETTINGS["valuation"]["equity_risk_premium"])


def test_e12_with_zero_debt_a_low_unlevered_beta_is_still_limited():
    v = value(changed("financial_debt", 2025, 0), beta=rate(0.5, "unlevered_beta"))
    assert v.levered_beta.value == SETTINGS["valuation"]["beta_min"]
    assert v.levered_beta.kind == "assumption"


# --- the starting growth and the growth note (E18) -------------------------------------------------------------------


def test_e18_past_growth_above_the_cap_starts_at_the_cap_with_the_growth_note():
    v = value(changed("revenue", 2021, 300))  # Flo, case c: (1,300 ÷ 300)^(1/4) − 1 = 44.2798%
    assert v.starting_growth.value == SETTINGS["valuation"]["growth_cap"]
    assert v.starting_growth.kind == "assumption"
    assert "past revenue growth 44.3% a year before the limit" in v.starting_growth.note
    assert "growth_cap" in v.starting_growth.note
    assert v.notes == ("Revenue grew 44.3% a year over the last four years; the model starts at 30% and lets growth "
                       "slow towards 2.5%.",)
    assert any(r.startswith("GROWTH_LIMIT:") for r in v.records)  # SPEC §10: a record on the sources page
    # At the cap, the V6 valuation is the same valuation (SPEC §7, V6 repeats V1).
    assert v.fair_value_at_growth_cap.value == pytest.approx(v.fair_value.value)


@pytest.mark.parametrize("past, limit_name", [(1.3, "growth_cap"), (0.9, "growth_floor")])
def test_past_growth_exactly_at_a_limit_is_not_labelled_as_limited(past, limit_name):
    # Flo's decision (review of 24 November): within 1e-10 of a limit counts as at the limit, so both ends behave
    # the same. Revenue FY-4 = 1,300 ÷ 1.3^4 (or ÷ 0.9^4): past growth exactly +30% (or −10%), up to rounding.
    v = value(changed("revenue", 2021, 1300 / past ** 4))
    assert v.starting_growth.value == SETTINGS["valuation"][limit_name]
    assert v.starting_growth.kind == "derived"
    assert v.notes == () and not any(r.startswith("GROWTH_LIMIT") for r in v.records)
    if limit_name == "growth_cap":  # SPEC §15: starting growth exactly at the cap, so V6 repeats V1
        assert v.fair_value_at_growth_cap.value == pytest.approx(v.fair_value.value)


@pytest.mark.parametrize("past, limit_name", [(1.3 + 1e-6, "growth_cap"), (0.9 - 1e-6, "growth_floor")])
def test_past_growth_just_beyond_a_limit_is_still_labelled_as_limited(past, limit_name):
    # Round 2 of the review: the "at the limit" allowance is tiny (1e-10), so 0.0001 percentage points beyond a
    # limit is limited, labelled and noted as usual.
    v = value(changed("revenue", 2021, 1300 / past ** 4))
    assert v.starting_growth.value == SETTINGS["valuation"][limit_name]
    assert v.starting_growth.kind == "assumption" and limit_name in v.starting_growth.note
    assert len(v.notes) == 1 and any(r.startswith("GROWTH_LIMIT:") for r in v.records)


def test_e18_past_growth_below_the_floor_starts_at_the_floor_with_the_growth_note():
    v = value(changed("revenue", 2021, 3000))  # Flo, case d: (1,300 ÷ 3,000)^(1/4) − 1 = −18.8655%
    assert v.starting_growth.value == SETTINGS["valuation"]["growth_floor"]
    assert v.starting_growth.kind == "assumption"
    assert "past revenue growth −18.9% a year before the limit" in v.starting_growth.note
    assert "growth_floor" in v.starting_growth.note
    assert v.notes == ("Revenue fell 18.9% a year over the last four years; the model starts at −10% and lets growth "
                       "recover towards 2.5%.",)


def test_the_limits_come_from_the_settings_not_the_code():
    settings = {**SETTINGS, "valuation": {**SETTINGS["valuation"], "growth_cap": 0.05}}
    v = value(settings=settings)  # the synthetic company's own growth is above 5%
    assert v.starting_growth.value == 0.05
    assert "the model starts at 5%" in v.notes[0]


def test_e18_nvidia_past_growth_is_capped_and_the_note_gives_68_3_percent():
    from src.data.company import load_company

    g1 = starting_growth(load_company("NVDA", demo=True), SETTINGS)
    assert g1.value == SETTINGS["valuation"]["growth_cap"]
    assert g1.kind == "assumption"
    # SPEC §8.2; Flo, case g: (215,938 ÷ 26,914)^(1/4) − 1 = 68.3014% (USD million, FY2022 to FY2026)
    assert "past revenue growth 68.3% a year before the limit" in g1.note


def test_starting_growth_equal_to_terminal_growth_stays_flat():
    # Revenue FY-4 set so that the past growth is exactly 2.5% a year (the terminal growth).
    v = value(changed("revenue", 2021, 1300 / 1.025 ** 4))
    assert [r.growth for r in v.forecast.years] == pytest.approx([0.025] * 10, abs=1e-12)


# --- terminal growth, minority interests, a negative FY0 free cash flow ----------------------------------------------


def test_terminal_growth_is_the_risk_free_rate_when_that_is_below_2_5_percent():
    # Flo's Excel model, case f (risk-free rate 2.0%), USD millions to 8 decimals.
    v = value(risk_free=rate(0.02))
    assert v.terminal_growth.value == pytest.approx(0.02)
    assert v.cost_of_equity.value == pytest.approx(0.0703325, abs=1e-12)
    assert v.starting_free_cash_flow.value == pytest.approx(113.66120219 * MILLION, abs=0.01)
    assert v.forecast.sum_of_discounted == pytest.approx(989.58369563 * MILLION, abs=0.01)
    assert v.forecast.terminal_value == pytest.approx(3271.42402094 * MILLION, abs=0.01)
    assert v.forecast.discounted_terminal_value == pytest.approx(1657.86709202 * MILLION, abs=0.01)
    assert v.equity_value.value == pytest.approx(2647.45078766 * MILLION, abs=0.01)
    assert v.fair_value.value == pytest.approx(26.47450788, abs=1e-8)
    assert value().terminal_growth.value == pytest.approx(0.025)  # 4.0% risk-free: the 2.5% limit


def test_a_minority_interest_is_subtracted_from_the_present_value():
    # Flo, case e: 2,012.95283165 − 100 = 1,912.95283165 (USD millions); ÷ 100 million shares = USD 19.12952832.
    v = value(changed("minority_interest", 2025, 100))
    assert v.status == "ok"
    assert v.equity_value.value == pytest.approx(1912.95283165 * MILLION, abs=0.01)
    assert v.fair_value.value == pytest.approx(19.12952832, abs=1e-8)
    assert v.equity_value.value == pytest.approx(v.forecast.present_value - 100 * MILLION)
    # Review of 24 November, M3: the V6 value subtracts the minority interest too: USD 100 million ÷ 100 million
    # shares = USD 1.00 per share below the Appendix A value at the cap (37.37, Flo's sign-off).
    e = synthetic.expected_valuation("fair_value_at_growth_cap")
    assert v.fair_value_at_growth_cap.value == pytest.approx(value().fair_value_at_growth_cap.value - 1.0)
    assert v.fair_value_at_growth_cap.value == pytest.approx(e["value"] - 1.0, abs=tol(e))


def test_a_negative_minority_interest_is_used_as_reported_and_recorded():
    v = value(changed("minority_interest", 2025, -50))
    assert v.equity_value.value == pytest.approx(v.forecast.present_value + 50 * MILLION)
    assert any("negative" in r and "minority interest" in r for r in v.records)


def test_a_minority_interest_treated_as_nil_subtracts_nothing():
    nil = Fact("minority_interest", 0, "USD", None, FY0, "assumption", None, None, None, None, None,
               "not reported under MinorityInterest, treated as nil (SPEC §8.3)")
    v = value(synthetic.company_data().with_fact(nil))
    e = synthetic.expected_valuation("fair_value_per_share")
    assert v.fair_value.value == pytest.approx(e["value"], abs=tol(e))
    assert nil in v.inputs


def test_a_negative_free_cash_flow_in_fy0_is_shown_with_a_line_and_a_record():
    v = value(changed("operating_cash_flow", 2025, 80))  # 80 − 85 = −5 in FY0; 75 + 115 − 5 > 0 over three years
    assert v.status == "ok"
    assert any("negative" in n and "31 December 2025" in n for n in v.notes)
    assert any("negative" in r and "31 December 2025" in r for r in v.records)
