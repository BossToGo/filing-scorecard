"""Property tests of the valuation engine (SPEC §15; slice S8). Owner: C (Flo).

Hypothesis tries many random inputs and checks that a rule of SPEC §8 always holds. The expected result is the rule
itself, so no number is needed:
1. With no debt the levered beta equals the unlevered beta (within the limits).
2. The beta always stays within its limits.
3. The fair value rises with the starting growth and falls with the cost of equity whenever FCF0 > 0.
4. g(t) moves towards terminal growth every year and never crosses it.
"""

from __future__ import annotations

import pytest
from hypothesis import given
from hypothesis import strategies as st

from src.settings import load_settings
from src.valuation.equity_method import forecast, growth_path, levered_beta

V = load_settings()["valuation"]
LIMITS = dict(tax_rate=V["tax_rate"], beta_min=V["beta_min"], beta_max=V["beta_max"])
SHAPE = dict(half_life_years=V["growth_half_life_years"], forecast_years=V["forecast_years"])

betas = st.floats(min_value=0.01, max_value=5.0)
amounts = st.floats(min_value=1e3, max_value=1e13)  # USD
growths = st.floats(min_value=V["growth_floor"], max_value=V["growth_cap"])
terminal = st.floats(min_value=-0.02, max_value=V["terminal_growth_cap"])


@given(unlevered=betas, market_value=amounts)
def test_with_no_debt_the_levered_beta_is_the_unlevered_beta_within_the_limits(unlevered, market_value):
    beta, before = levered_beta(unlevered, 0.0, market_value, **LIMITS)
    assert before == unlevered
    assert beta == min(max(unlevered, V["beta_min"]), V["beta_max"])


@given(unlevered=betas, debt=st.floats(min_value=0, max_value=1e13), market_value=amounts)
def test_the_beta_always_stays_within_its_limits(unlevered, debt, market_value):
    beta, before = levered_beta(unlevered, debt, market_value, **LIMITS)
    assert V["beta_min"] <= beta <= V["beta_max"]
    assert before >= unlevered  # debt only ever adds risk
    if V["beta_min"] <= before <= V["beta_max"]:
        assert beta == before


@given(g1=growths, gt=terminal)
def test_growth_moves_towards_terminal_growth_and_never_crosses_it(g1, gt):
    path = growth_path(g1, gt, **SHAPE)
    assert len(path) == V["forecast_years"]
    assert path[0] == pytest.approx(g1)
    for this, following in zip(path, path[1:]):
        assert abs(following - gt) <= abs(this - gt)
        assert (following - gt) * (g1 - gt) >= 0  # same side of gT as the start, or on it


@given(g1=growths, gt=terminal, half_life=st.integers(min_value=1, max_value=4), t=st.integers(min_value=0, max_value=5))
def test_the_gap_to_terminal_growth_halves_every_half_life(g1, gt, half_life, t):
    # SPEC §8.2: the gap between g(t) and gT halves every H years, whatever H is (review of 24 November: a formula
    # that misuses H can still be right at H = 2).
    path = growth_path(g1, gt, half_life_years=half_life, forecast_years=10)
    assert path[t + half_life] - gt == pytest.approx(0.5 * (path[t] - gt), rel=1e-12, abs=1e-15)


@given(fcf0=amounts, g_low=growths, g_high=growths, gt=terminal, premium=st.floats(min_value=0.04, max_value=0.20))
def test_the_value_rises_with_the_starting_growth_when_fcf0_is_positive(fcf0, g_low, g_high, gt, premium):
    g_low, g_high = sorted((g_low, g_high))
    cost_of_equity = max(gt, 0) + premium
    low = forecast(fcf0, growth_path(g_low, gt, **SHAPE), cost_of_equity, gt).present_value
    high = forecast(fcf0, growth_path(g_high, gt, **SHAPE), cost_of_equity, gt).present_value
    assert high >= low * (1 - 1e-12)
    if g_high - g_low > 1e-6:
        assert high > low


@given(fcf0=amounts, g1=growths, gt=terminal, low=st.floats(min_value=0.04, max_value=0.20),
       step=st.floats(min_value=1e-4, max_value=0.10))
def test_the_value_falls_with_the_cost_of_equity_when_fcf0_is_positive(fcf0, g1, gt, low, step):
    path = growth_path(g1, gt, **SHAPE)
    cheap = forecast(fcf0, path, max(gt, 0) + low, gt).present_value
    dear = forecast(fcf0, path, max(gt, 0) + low + step, gt).present_value
    assert dear < cheap
