"""Load `app/settings.yaml` as plain values (owner A).

    from src.settings import load_settings
    settings = load_settings()
    settings["financial_health"]["max_net_debt_to_equity"]   # 0.40

Each setting in the file has a `value` and a `reason`; this returns the values only, per section. Asking for a
setting that does not exist raises a KeyError naming the section and the file, instead of a silent default.
"""

from __future__ import annotations

from pathlib import Path

import yaml

SETTINGS_FILE = Path(__file__).resolve().parents[1] / "settings.yaml"


class _Section(dict):
    def __init__(self, name: str, values: dict):
        super().__init__(values)
        self.name = name

    def __missing__(self, key):
        raise KeyError(f"{key!r} is not a setting in section {self.name!r} of app/settings.yaml")


def load_settings(path: Path = SETTINGS_FILE) -> dict[str, dict]:
    raw = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    settings = {
        section: _Section(section, {name: entry["value"] for name, entry in (entries or {}).items()})
        for section, entries in raw.items()
    }
    _check_cost_of_equity_floor(settings.get("valuation", {}), path)
    return settings


def _check_cost_of_equity_floor(valuation: dict, path: Path) -> None:
    """SPEC §8.3: beta_min × equity_risk_premium > 0, so the cost of equity stays above terminal growth."""
    beta_min, premium = valuation.get("beta_min"), valuation.get("equity_risk_premium")
    if beta_min is None or premium is None:
        return
    if not beta_min * premium > 0:
        raise ValueError(
            f"beta_min × equity_risk_premium must be above 0 (SPEC §8.3), got {beta_min} × {premium} in {path.name}: "
            "otherwise the cost of equity can fall to terminal growth and the terminal value does not exist"
        )
