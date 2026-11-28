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

Slice S8b (27 November 2026, issue #71, agreed by the group; the written reason for every test changed, rule 14.6):
the method changed. The starting free cash flow is the last twelve months, debt, minority interest and shares come
from the latest balance sheet (`CompanyData.recent`), long-run growth is the risk-free rate and the premium is 4.41%.
So tests that planted an annual FY0 balance or cash flow now plant the latest figure, the three-year margin and the
"negative FY0" line are gone, and "towards 2.5%" reads the risk-free rate. The new rules: test_valuation_latest.py.
"""

from __future__ import annotations

import dataclasses
from datetime import date

import pytest

from src.contracts import CompanyData, Fact
from src.settings import load_settings
from src.valuation.equity_method import forecast, growth_path, starting_growth, value_company
from tests.fixtures import synthetic
from tests.unit.valuation_data import latest, synthetic_company, without_latest

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
    return value_company(synthetic_company() if data is None else data, settings,
                         share_price=price, risk_free_rate=risk_free, unlevered_beta=beta)


def changed(metric: str, year: int, millions: float | None, data: CompanyData | None = None) -> CompanyData:
    """The synthetic company with one annual figure replaced; None makes it `missing` with a reason (never zero)."""
    data = synthetic_company() if data is None else data
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


def test_f1_base_free_cash_flows_and_starting_free_cash_flow():
    v = value()
    e = synthetic.expected_valuation("base_free_cash_flows")
    assert [f.period_end.year for f in v.base_free_cash_flows] == [2023, 2024, 2025]
    assert [f.value for f in v.base_free_cash_flows] == pytest.approx([x * MILLION for x in e["values"]],
                                                                       abs=tol(e, MILLION))
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
    assert v.notes == ()  # no growth limit, the twelve months are close to the three years


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
    ("operating cash flow, twelve months", lambda: latest("operating_cash_flow", None), {},
     ["operating cash flow", "last twelve months"]),
    ("capital expenditure, no entry", lambda: without_latest("capital_expenditure"), {},
     ["capital expenditure", "last twelve months"]),
    ("latest financial debt", lambda: latest("financial_debt", None), {}, ["financial debt"]),
    ("shares", lambda: without_latest("shares"), {}, ["shares"]),
    ("latest minority interest", lambda: latest("minority_interest", None), {}, ["minority interest"]),
    ("industry beta", lambda: None, {"beta": None}, ["industry beta"]),
    ("risk-free rate", lambda: None, {"risk_free": None}, ["risk-free rate"]),
    ("share price", lambda: None, {"price": None}, ["share price"]),
    ("revenue FY0 zero", lambda: changed("revenue", 2025, 0), {}, ["revenue", "31 December 2025", "zero or negative"]),
    ("revenue FY-4 negative", lambda: changed("revenue", 2021, -5), {},
     ["revenue", "31 December 2021", "zero or negative"]),
    ("only four fiscal years", lambda: without(synthetic_company(), "revenue", 2021), {}, ["five fiscal years"]),
    ("negative capital expenditure (sign error)", lambda: latest("capital_expenditure", -80), {},
     ["capital expenditure", "negative", "sign warning"]),
    # Added after the review of 24 November (Flo's decisions: any revenue year ≤ 0 and a negative debt are refused).
    ("revenue FY-1 zero", lambda: changed("revenue", 2024, 0), {},
     ["revenue", "31 December 2024", "zero or negative"]),
    ("revenue FY-3 negative", lambda: changed("revenue", 2022, -500), {},
     ["revenue", "31 December 2022", "zero or negative"]),
    ("negative financial debt (sign error)", lambda: latest("financial_debt", -400), {},
     ["financial debt", "negative"]),
    ("shares zero", lambda: latest("shares", 0), {}, ["shares", "zero or negative"]),
    ("share price zero", lambda: None, {"price": 0.0}, ["share price", "zero or negative"]),
    ("industry beta zero", lambda: None, {"beta": rate(0.0, "unlevered_beta")}, ["industry beta", "zero or negative"]),
    # S18 (breaks GE-negative-share-count, GE-price-negative, GE-beta-negative): only zero was tested,
    # not a negative number.
    ("shares negative", lambda: latest("shares", -100), {}, ["shares", "zero or negative"]),
    ("share price negative", lambda: None, {"price": -5.0}, ["share price", "zero or negative"]),
    ("industry beta negative", lambda: None, {"beta": rate(-0.5, "unlevered_beta")},
     ["industry beta", "zero or negative"]),
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
    data = latest("financial_debt", None, latest("operating_cash_flow", None))
    v = value(data, beta=None)
    for word in ("financial debt", "operating cash flow", "industry beta"):
        assert word in v.reason


def test_e22_with_four_fiscal_years_the_missing_market_inputs_are_named_too():
    v = value(without(synthetic_company(), "revenue", 2021), price=None, beta=None)
    assert v.status == "insufficient_data"
    for word in ("five fiscal years", "share price", "industry beta"):
        assert word in v.reason


@pytest.mark.parametrize("price", [float("inf"), float("-inf"), float("nan")], ids=["inf", "-inf", "nan"])
def test_e22_a_share_price_that_is_not_a_finite_number_means_no_fair_value(price):
    # Review of 24 November (Igor, point 2): the screen blocks these, the engine must be safe on its own.
    v = value(price=price)
    assert v.status == "insufficient_data"
    assert "share price" in v.reason and "not a usable number" in v.reason
    assert v.fair_value is None and v.equity_value is None


def test_e22_with_four_fiscal_years_the_result_still_lists_the_figures_that_exist():
    # Review of 24 November (Igor, point 3): V1, V2 and V6 and the sources page link to these. The four revenue years
    # that exist are 2022 to 2025 (2021 removed); the two market inputs come with them.
    v = value(without(synthetic_company(), "revenue", 2021))
    assert v.status == "insufficient_data"
    used = {(f.metric, f.period_end.year) for f in v.inputs}
    assert used == {("revenue", y) for y in range(2022, 2026)} | {("risk_free_rate", 2025), ("unlevered_beta", 2025)}


def test_a_negative_capex_not_read_from_a_filing_does_not_point_to_a_sign_warning():
    # As in the dividend checks (S7-R2): only a figure read from a filing has the data layer's SIGN warning.
    data = synthetic_company()
    old = data.recent["capital_expenditure"]
    typed = dataclasses.replace(old, value=-80 * MILLION, kind="assumption", tag=None, form=None, accession=None,
                                note="test override")
    v = value(dataclasses.replace(data, recent={**data.recent, "capital_expenditure": typed}))
    assert v.status == "insufficient_data"
    assert "negative" in v.reason and "sign warning" not in v.reason


# --- §8.6 second test: the model does not fit, so "not applicable" (E19) ---------------------------------------------


def test_e19_equity_value_zero_or_below_after_minority_interests_means_not_applicable():
    v = value(latest("minority_interest", 5000))  # far above the synthetic company's value
    assert v.status == "not_applicable"
    assert "minority interests" in v.reason
    assert v.fair_value is None and v.fair_value_at_growth_cap is None


def test_e19_minority_case_carries_no_line_about_a_valuation_that_never_ran():
    # Review of 24 November (Igor, point 1): a result that is "not applicable" carries no line about a valuation that
    # never ran. Here the twelve months (300 − 85) differ a lot from the three years, and minority interests are 50,000.
    data = latest("operating_cash_flow", 300, latest("minority_interest", 50_000))
    v = value(data)
    assert v.status == "not_applicable" and "minority interests" in v.reason
    assert v.fair_value is None
    assert v.notes == ()


def test_e22_before_e19_a_missing_input_wins_over_no_free_cash_flow():
    data = latest("financial_debt", None, latest("operating_cash_flow", 50))
    v = value(data)
    assert v.status == "insufficient_data" and "financial debt" in v.reason


# --- the beta (E12, E20) ---------------------------------------------------------------------------------------------


def test_e12_with_zero_debt_the_levered_beta_is_the_unlevered_beta():
    beta = value(latest("financial_debt", 0)).levered_beta
    assert beta.value == pytest.approx(0.90)
    assert beta.kind == "derived"


# Flo's hand working (S8 cases a and b in docs/acceptance.md): unlevered beta × (1 + 0.79 × 450 ÷ 3,000).
@pytest.mark.parametrize("unlevered, before, limit_name", [(1.9, "2.12515", "beta_max"), (0.5, "0.55925", "beta_min")])
def test_e20_a_beta_outside_the_limits_is_set_to_the_limit_labelled_and_recorded(unlevered, before, limit_name):
    v = value(beta=rate(unlevered, "unlevered_beta"))
    limit = SETTINGS["valuation"][limit_name]
    assert v.levered_beta.value == limit
    assert v.levered_beta.kind == "assumption"
    assert f"= {before} before the limit" in v.levered_beta.note
    assert f"set to the {'upper' if limit_name == 'beta_max' else 'lower'} limit ({limit})" in v.levered_beta.note
    # SPEC §10: a limited beta is a record on the sources page, not a warning in the header.
    assert any(r.startswith("BETA_LIMIT:") for r in v.records)
    assert v.status == "ok"
    if limit_name == "beta_max":  # plain words (Flo, 24 November); 2.12515 shown with two decimals
        assert ("BETA_LIMIT: the company's beta, adjusted for its debt, is 2.13, outside the range 0.8 to 2.0, so 2.0 "
                "is used.") in v.records
    # Review of 24 November, M2: the cost of equity uses the beta after the limit, not before it (SPEC §8.1).
    assert v.cost_of_equity.value == pytest.approx(RISK_FREE.value + limit * SETTINGS["valuation"]["equity_risk_premium"])


@pytest.mark.parametrize("unlevered, shown", [(1.7908, "2.003"), (1.7883, "2.0002")])
def test_e20_a_beta_just_past_the_limit_is_not_printed_as_the_limit(unlevered, shown):
    # Review of 24 November (Igor, point 1): with two decimals 2.003 would read "is 2.00, outside the range 0.8 to 2.0".
    # Hand working: 1.7908 × (1 + 0.79 × 450 ÷ 3,000) = 1.7908 × 1.1185 = 2.00301, and 1.7883 × 1.1185 = 2.00021.
    v = value(beta=rate(unlevered, "unlevered_beta"))
    assert v.levered_beta.value == SETTINGS["valuation"]["beta_max"]
    assert (f"BETA_LIMIT: the company's beta, adjusted for its debt, is {shown}, outside the range 0.8 to 2.0, "
            "so 2.0 is used.") in v.records


def test_e12_with_zero_debt_a_low_unlevered_beta_is_still_limited():
    v = value(latest("financial_debt", 0), beta=rate(0.5, "unlevered_beta"))
    assert v.levered_beta.value == SETTINGS["valuation"]["beta_min"]
    assert v.levered_beta.kind == "assumption"


# --- the starting growth and the growth note (E18) -------------------------------------------------------------------


def test_e18_past_growth_above_the_cap_starts_at_the_cap_with_the_growth_note():
    v = value(changed("revenue", 2021, 300))  # Flo, case c: (1,300 ÷ 300)^(1/4) − 1 = 44.2798%
    assert v.starting_growth.value == SETTINGS["valuation"]["growth_cap"]
    assert v.starting_growth.kind == "assumption"
    assert "past revenue growth 44.3% a year before the limit" in v.starting_growth.note
    assert "set to the upper limit (30%)" in v.starting_growth.note
    assert v.notes == ("Revenue grew 44.3% a year over the last four years; the model starts at 30% and lets growth "
                       "slow towards 4%.",)
    # SPEC §10: a record on the sources page, in plain words (Flo, 24 November).
    assert ("GROWTH_LIMIT: revenue changed by 44.3% a year, from USD 300 million in the fiscal year ended 31 December "
            "2021 to USD 1,300 million in the fiscal year ended 31 December 2025; this is beyond the 30% limit, so the "
            "model starts at 30%.") in v.records
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
    assert v.starting_growth.kind == "assumption" and ("upper limit" if limit_name == "growth_cap" else "lower limit") in v.starting_growth.note
    assert len(v.notes) == 1 and any(r.startswith("GROWTH_LIMIT:") for r in v.records)


def test_e18_past_growth_below_the_floor_starts_at_the_floor_with_the_growth_note():
    v = value(changed("revenue", 2021, 3000))  # Flo, case d: (1,300 ÷ 3,000)^(1/4) − 1 = −18.8655%
    assert v.starting_growth.value == SETTINGS["valuation"]["growth_floor"]
    assert v.starting_growth.kind == "assumption"
    assert "past revenue growth −18.9% a year before the limit" in v.starting_growth.note
    assert "set to the lower limit (−10%)" in v.starting_growth.note
    assert v.notes == ("Revenue fell 18.9% a year over the last four years; the model starts at −10% and lets growth "
                       "recover towards 4%.",)


# --- the two figures Simon's screen shows (SPEC §3 item 6; his review of #43, 24 November) ----------------------------


def test_the_actual_revenue_growth_is_a_figure_of_its_own_inside_the_limits():
    # Inside the limits it equals the starting growth of Appendix A (Flo's sign-off).
    e = synthetic.expected_valuation("starting_growth")
    past = value().past_revenue_growth
    assert past.value == pytest.approx(pct(e), abs=tol(e, 0.01))
    assert (past.metric, past.unit, past.kind) == ("past_revenue_growth", "pure", "derived")
    assert (past.period_start, past.period_end) == (date(2021, 12, 31), FY0)
    assert "SPEC" not in past.note  # a plain-words note: the screen shows it as it is


@pytest.mark.parametrize("revenue_2021, expected", [(300, 0.442798), (3000, -0.188655)],
                         ids=["above the cap", "below the floor"])
def test_the_actual_revenue_growth_is_not_limited_when_the_starting_growth_is(revenue_2021, expected):
    # Flo's hand working, cases c and d: (1,300 ÷ 300)^(1/4) − 1 = 44.2798%; (1,300 ÷ 3,000)^(1/4) − 1 = −18.8655%.
    v = value(changed("revenue", 2021, revenue_2021))
    assert v.starting_growth.kind == "assumption"
    assert v.past_revenue_growth.value == pytest.approx(expected, abs=1e-6)
    assert v.past_revenue_growth.kind == "derived"


def test_the_actual_revenue_growth_is_there_when_the_model_does_not_fit_and_absent_without_five_years():
    not_fitting = value(latest("operating_cash_flow", 50))
    assert not_fitting.status == "not_applicable" and not_fitting.past_revenue_growth is not None
    too_short = value(without(synthetic_company(), "revenue", 2021))
    assert too_short.status == "insufficient_data" and too_short.past_revenue_growth is None


def test_the_equity_risk_premium_is_an_assumption_with_its_source_in_plain_words():
    premium = value().equity_risk_premium
    assert premium.value == synthetic.inputs()["settings"]["equity_risk_premium"]  # 4.41%, Appendix A
    assert (premium.metric, premium.unit, premium.kind, premium.period_end) == ("equity_risk_premium", "pure",
                                                                                 "assumption", FY0)
    assert "4.41%" in premium.note and "not read from a filing" in premium.note
    assert not any(word in premium.note for word in ("SPEC", "setting", "yaml"))
    v = value()  # the relation between two figures of the same run: cost of equity = risk-free + beta × premium
    assert v.cost_of_equity.value == pytest.approx(RISK_FREE.value + v.levered_beta.value * premium.value)


def test_the_equity_risk_premium_follows_the_settings_and_is_absent_without_a_result():
    settings = {**SETTINGS, "valuation": {**SETTINGS["valuation"], "equity_risk_premium": 0.06}}
    assert value(settings=settings).equity_risk_premium.value == 0.06
    assert "6%" in value(settings=settings).equity_risk_premium.note
    assert value(price=None).equity_risk_premium is None  # insufficient data: no build-up to show


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
    # Revenue FY-4 set so that the past growth is exactly 4% a year (the terminal growth: the risk-free rate).
    v = value(changed("revenue", 2021, 1300 / 1.04 ** 4))
    assert [r.growth for r in v.forecast.years] == pytest.approx([0.04] * 10, abs=1e-12)


# --- terminal growth, minority interests, a negative FY0 free cash flow ----------------------------------------------


def test_s8_f_a_risk_free_rate_of_2_percent():
    # Flo's Excel model, case f (risk-free rate 2.0%), USD millions to 8 decimals; recalculated by Flo for the
    # method of issue #71 (28 November 2026, docs/acceptance.md S8-f).
    v = value(risk_free=rate(0.02))
    assert v.terminal_growth.value == pytest.approx(0.02)
    assert v.cost_of_equity.value == pytest.approx(0.064393265, abs=1e-12)
    assert v.starting_free_cash_flow.value == pytest.approx(130 * MILLION, abs=0.01)
    assert v.forecast.sum_of_discounted == pytest.approx(1165.18457915 * MILLION, abs=0.01)
    assert v.forecast.terminal_value == pytest.approx(4242.28029927 * MILLION, abs=0.01)
    assert v.forecast.discounted_terminal_value == pytest.approx(2272.88876280 * MILLION, abs=0.01)
    assert v.equity_value.value == pytest.approx(3438.07334195 * MILLION, abs=0.01)
    assert v.fair_value.value == pytest.approx(34.38073342, abs=1e-8)
    assert value().terminal_growth.value == pytest.approx(0.04)  # long-run growth = the risk-free rate


def test_a_minority_interest_is_subtracted_from_the_present_value():
    # Flo, case e (28 November 2026, his Excel model with minority interest 100): equity value USD 3,201.65417623
    # million; ÷ 100 million shares = USD 32.01654176.
    v = value(latest("minority_interest", 100))
    assert v.status == "ok"
    assert v.equity_value.value == pytest.approx(3201.65417623 * MILLION, abs=0.01)
    assert v.fair_value.value == pytest.approx(32.01654176, abs=1e-8)
    assert v.equity_value.value == pytest.approx(v.forecast.present_value - 100 * MILLION)
    # Review of 24 November, M3: the V6 value subtracts the minority interest too: USD 100 million ÷ 100 million
    # shares = USD 1.00 per share below the Appendix A value at the cap (62.32, Flo's recalculation of 28 November).
    e = synthetic.expected_valuation("fair_value_at_growth_cap")
    assert v.fair_value_at_growth_cap.value == pytest.approx(value().fair_value_at_growth_cap.value - 1.0)
    assert v.fair_value_at_growth_cap.value == pytest.approx(e["value"] - 1.0, abs=tol(e))


def test_a_negative_minority_interest_is_used_as_reported_and_recorded():
    v = value(latest("minority_interest", -50))
    assert v.equity_value.value == pytest.approx(v.forecast.present_value + 50 * MILLION)
    assert any("negative" in r and "minority interest" in r for r in v.records)


def test_a_minority_interest_treated_as_nil_subtracts_nothing():
    nil = Fact("minority_interest", 0, "USD", None, FY0, "assumption", None, None, None, None, None,
               "not reported under MinorityInterest, treated as nil (SPEC §8.3)")
    data = synthetic_company()
    v = value(dataclasses.replace(data, recent={**data.recent, "minority_interest": nil}))
    e = synthetic.expected_valuation("fair_value_per_share")
    assert v.fair_value.value == pytest.approx(e["value"], abs=tol(e))
    assert nil in v.inputs


def test_customer_texts_name_no_spec_section_setting_or_tool():
    # Flo, 24 November: what a bank customer reads (reasons, detail lines, sources-page records) is in plain words.
    cases = [value(changed("operating_cash_flow", 2023, None)),  # no comparison possible
             value(changed("operating_cash_flow", 2023, -500)),  # an average below zero
             value(changed("revenue", 2021, 300)), value(changed("revenue", 2021, 3000)),
             value(beta=rate(1.9, "unlevered_beta")), value(latest("minority_interest", -50)),
             value(latest("operating_cash_flow", 300)), value(price=None, risk_free=None, beta=None),
             value(latest("operating_cash_flow", 50)), value(latest("minority_interest", 5000))]
    for v in cases:
        for text in (v.reason,) + v.notes + v.records:
            for jargon in ("SPEC", "§", "settings.yaml", "FRED", "growth_cap", "growth_floor", "beta_min", "beta_max",
                           "re-levered"):
                assert jargon not in text, f"{jargon!r} in {text!r}"
    assert "risk-free rate: not available at the moment" in cases[7].reason


def test_every_figure_note_the_screen_shows_is_in_plain_words():
    # Flo, 24 November (Igor's point 1a, after Simon's answer on #43: the screen shows each Fact with its note). The
    # figures the engine builds, not the inputs: those come from the data layer (A) and the benchmarks (B).
    cases = [value(), value(changed("revenue", 2021, 300)), value(changed("revenue", 2021, 3000)),
             value(beta=rate(1.9, "unlevered_beta")), value(beta=rate(0.5, "unlevered_beta")),
             value(changed("revenue", 2021, 1300 / 1.3 ** 4)), value(latest("minority_interest", -50)),
             value(latest("operating_cash_flow", 50)), value(latest("minority_interest", 5000))]
    own = ("levered_beta", "cost_of_equity", "terminal_growth", "equity_risk_premium", "average_free_cash_flow",
           "starting_free_cash_flow", "starting_growth", "past_revenue_growth", "equity_value", "fair_value",
           "fair_value_at_growth_cap")
    seen = 0
    for v in cases:
        facts = [getattr(v, name) for name in own] + list(v.base_free_cash_flows)
        for fact in (f for f in facts if f is not None):
            seen += 1
            for jargon in ("SPEC", "§", "settings", "yaml", "FRED", "terminal_growth_cap", "growth_cap", "growth_floor",
                           "beta_min", "beta_max", "_cap", "_floor"):
                assert jargon not in fact.note, f"{jargon!r} in the note of {fact.metric}: {fact.note!r}"
    assert seen > 40  # the loop did look at the figures


# --- S18, break-it round (26 November): breaks that no test caught ---------------------------------------------------
# Every expected result is the rule itself (SPEC §7, §8.3, §8.6) or a relation between two runs: no worked numbers.


def test_with_six_fiscal_years_the_valuation_uses_the_latest_five():
    # Break E-FY0. SPEC §7: FY0 is the latest fiscal year, FY-4 four years earlier, so a revenue of 2020 changes nothing.
    data = synthetic_company()
    old = data.fact("revenue", date(2021, 12, 31))
    older = dataclasses.replace(old, value=500 * MILLION, period_start=date(2020, 1, 1), period_end=date(2020, 12, 31))
    v = value(data.with_fact(older))
    assert [f.period_end.year for f in v.inputs if f.metric == "revenue"] == [2021, 2022, 2023, 2024, 2025]
    assert v.fair_value.value == value().fair_value.value


def test_e19_an_equity_value_of_exactly_zero_means_not_applicable():
    # Break FIT-c. SPEC §8.6: equity value ≤ 0. Minority interests set to the present value of the same company.
    v = value(latest("minority_interest", value().forecast.present_value / MILLION))
    assert v.status == "not_applicable" and "minority interests" in v.reason
    assert v.fair_value is None


@pytest.mark.parametrize("cost_of_equity", [0.025, 0.02], ids=["equal to terminal growth", "below it"])
def test_a_cost_of_equity_not_above_terminal_growth_is_refused(cost_of_equity):
    # Breaks GE-forecast-rate, GE-forecast-rate-eq. SPEC §8.3: the terminal value divides by (cost of equity − gT),
    # which must stay above zero.
    with pytest.raises(ValueError):
        forecast(100 * MILLION, growth_path(0.05, 0.025, 2, 10), cost_of_equity, 0.025)


def test_starting_growth_refuses_a_company_with_only_four_fiscal_years():
    # Break GE-g1-years. SPEC §8.6: fewer than five fiscal years.
    with pytest.raises(ValueError, match="five fiscal years"):
        starting_growth(without(synthetic_company(), "revenue", 2021), SETTINGS)


@pytest.mark.parametrize("year, millions", [(2021, None), (2021, 0), (2025, 0)],
                         ids=["FY-4 missing", "FY-4 zero", "FY0 zero"])
def test_starting_growth_refuses_unusable_revenue(year, millions):
    # Break GE-g1-unusable. SPEC §8.6: revenue missing, or FY0 or FY-4 ≤ 0.
    with pytest.raises(ValueError, match="revenue"):
        starting_growth(changed("revenue", year, millions), SETTINGS)
