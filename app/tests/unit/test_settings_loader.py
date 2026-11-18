"""Loading app/settings.yaml into plain values (slice S1). Owner: A."""

import pytest

from src.settings import load_settings


def test_settings_are_loaded_as_plain_values_per_section():
    settings = load_settings()
    assert settings["data"]["max_requests_per_second"] == 5
    assert settings["financial_health"]["max_net_debt_to_equity"] == 0.40
    assert settings["valuation"]["risk_free_rate"] is None


def test_empty_sections_are_empty_dicts():
    assert load_settings()["forces"] == {}


def test_a_missing_setting_names_the_section_and_the_file():
    with pytest.raises(KeyError, match="settings.yaml"):
        load_settings()["data"]["no_such_setting"]
