"""`app/settings.yaml`: one section per owner, every setting with a value and a one-line reason (SPEC §7, R10).

Owner: A. The values themselves belong to each section's owner; this test only checks the shape.
"""

from pathlib import Path

import yaml

SETTINGS = Path(__file__).resolve().parents[2] / "settings.yaml"
SECTIONS = {"data", "benchmarks", "past_performance", "financial_health", "dividend", "valuation", "gates", "forces"}


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
    "data": ["restatement_warning", "tag_conflict_warning", "debt_inside_tolerance"],
    "financial_health": ["max_net_debt_to_equity", "min_operating_cash_flow_to_debt"],
    "dividend": ["max_dividend_cut", "max_payout_ratio"],
    "valuation": [
        "equity_risk_premium",
        "tax_rate",
        "cost_of_debt_max_spread",
        "cost_of_debt_default_spread",
        "terminal_growth_cap",
        "sensitivity_range",
        "sensitivity_step",
        "well_below_fair_value",
    ],
    "gates": ["balance_sheet_tolerance", "terminal_value_share_warning"],
}


def test_rates_are_decimals_not_percentages():
    # SPEC §5.4: percent against decimal is a planted mistake. 40% is written 0.40.
    settings = load()
    for section, names in RATES.items():
        for name in names:
            assert 0 < settings[section][name]["value"] < 1, f"{section}.{name} must be a decimal, e.g. 0.40 for 40%"
    valuation = settings["valuation"]
    assert -1 < valuation["reverse_dcf_min_growth"]["value"] < 0 < valuation["reverse_dcf_max_growth"]["value"] < 1
    risk_free = valuation["risk_free_rate"]["value"]
    assert risk_free is None or 0 <= risk_free < 0.2, "risk_free_rate is a decimal, e.g. 0.042 for 4.2%"
