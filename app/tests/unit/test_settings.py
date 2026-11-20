"""`app/settings.yaml`: one section per owner, every setting with a value and a one-line reason (SPEC §7, R10).

Owner: A. The values themselves belong to each section's owner; this test only checks the shape.
"""

from pathlib import Path

import yaml

SETTINGS = Path(__file__).resolve().parents[2] / "settings.yaml"
SECTIONS = {"data", "benchmarks", "past_performance", "financial_health", "dividend", "valuation", "gates",
            "highlights"}


def load():
    return yaml.safe_load(SETTINGS.read_text(encoding="utf-8"))


def test_every_owner_has_a_section():
    assert set(load()) == SECTIONS


def test_every_setting_has_a_value_and_a_reason():
    problems = []
    for section, settings in load().items():
        for name, entry in (settings or {}).items():
            if not isinstance(entry, dict) or set(entry) != {"value", "reason"}:
                problems.append(f"{section}.{name}: needs exactly 'value' and 'reason'")
            elif not isinstance(entry["reason"], str) or not entry["reason"].strip():
                problems.append(f"{section}.{name}: the reason is empty")
    assert not problems, "\n".join(problems)


RATES = {  # every setting that is a rate or a share: a decimal strictly between 0 and 1
    "data": ["restatement_warning", "tag_conflict_warning", "debt_check_warning"],
    "financial_health": ["max_net_debt_to_equity", "min_operating_cash_flow_to_debt"],
    "dividend": ["max_dividend_cut", "max_payout_ratio"],
    "valuation": [
        "equity_risk_premium",
        "tax_rate",
        "terminal_growth_cap",
        "well_below_fair_value",
        "growth_cap",
    ],
    "gates": ["balance_sheet_tolerance"],
}


def test_the_valuation_settings_follow_the_equity_method():
    # SPEC v2.3 (lean, 20 November): no cost of debt, no sensitivity table, no user inputs, no terminal-value warning;
    # free cash flow starts from the margin of the last few fiscal years.
    settings = load()
    removed = {"cost_of_debt_max_spread", "cost_of_debt_default_spread", "sensitivity_range", "sensitivity_step",
               "user_tax_rate_max", "reverse_dcf_min_growth", "reverse_dcf_max_growth"}
    assert not removed & set(settings["valuation"])
    assert "terminal_value_share_warning" not in settings["gates"]
    years = settings["valuation"]["fcf_base_years"]["value"]
    assert isinstance(years, int) and 1 <= years <= 5
    # Round 2: ten forecast years, growth halving its gap to terminal growth every two years, cap 30%.
    assert settings["valuation"]["forecast_years"]["value"] == 10
    assert settings["valuation"]["growth_half_life_years"]["value"] == 2
    assert settings["valuation"]["growth_cap"]["value"] == 0.30
    # Risk-free rate: the five-year average of FRED DGS10 (decided 20 November); A's data layer downloads it.
    average_years = settings["data"]["risk_free_average_years"]["value"]
    assert isinstance(average_years, int) and 1 <= average_years <= 10


def test_rates_are_decimals_not_percentages():
    # SPEC §5.4: percent against decimal is a planted mistake. 40% is written 0.40.
    settings = load()
    for section, names in RATES.items():
        for name in names:
            assert 0 < settings[section][name]["value"] < 1, f"{section}.{name} must be a decimal, e.g. 0.40 for 40%"
    valuation = settings["valuation"]
    # SPEC v2.3 §8.2 (round 2): the automatic starting growth is limited, then decays towards terminal growth.
    assert -1 < valuation["growth_floor"]["value"] < 0 < valuation["growth_cap"]["value"] < 1
    # SPEC v2.3 §8.1: the re-levered beta is limited (0.8 to 2.0), written as plain numbers, not percentages.
    assert 0 < valuation["beta_min"]["value"] < 1 < valuation["beta_max"]["value"] < 5
    risk_free = valuation["risk_free_rate"]["value"]
    assert risk_free is None or 0 <= risk_free < 0.2, "risk_free_rate is a decimal, e.g. 0.042 for 4.2%"
