"""Loading app/settings.yaml into plain values (slice S1). Owner: A."""

import pytest

from src.settings import load_settings


def test_settings_are_loaded_as_plain_values_per_section():
    settings = load_settings()
    assert settings["data"]["max_requests_per_second"] == 5
    assert settings["financial_health"]["max_net_debt_to_equity"] == 0.40
    # Until slice S2b this line read `risk_free_rate is None`: it used the one empty setting of the time to show
    # that an empty value loads as None. S2b filled that setting in as planned (known problem test #9), so the empty
    # case now has its own test below, and this line checks only that the saved rate loads as a plain number (its
    # value is refreshed before each release and checked in test_fred.py). Agreed by Igor (A), 24 November 2026,
    # rule 14.6.
    assert isinstance(settings["valuation"]["risk_free_rate"], float)


def test_an_empty_value_loads_as_none(tmp_path):
    path = tmp_path / "settings.yaml"
    path.write_text('example:\n  not_set_yet:\n    value: null\n    reason: "an empty setting"\n', encoding="utf-8")

    assert load_settings(path)["example"]["not_set_yet"] is None


def test_empty_sections_are_empty_dicts():
    assert load_settings()["highlights"] == {}


def test_a_missing_setting_names_the_section_and_the_file():
    with pytest.raises(KeyError, match="settings.yaml"):
        load_settings()["data"]["no_such_setting"]
