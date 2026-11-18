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


def test_rates_are_decimals_not_percentages():
    # SPEC §5.4: percent against decimal is a planted mistake. 40% is written 0.40.
    for name in ("max_net_debt_to_equity", "min_operating_cash_flow_to_debt"):
        assert 0 < load()["financial_health"][name]["value"] < 1
    for name in ("equity_risk_premium", "tax_rate", "terminal_growth_cap"):
        assert 0 < load()["valuation"][name]["value"] < 1
