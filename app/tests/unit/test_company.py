"""`src.data.company`: the one module the interface imports from the data layer (SPEC §11). Owner: A.

Simon's review of PR #7: the interface must recognise the SEC errors (e.g. `SourceUnreachable` for acceptance E4)
without importing `src.data.sec_client`, so `src.data.company` makes them available next to `load_company`.
"""

import pytest

from src.data import company, sec_client

ERRORS = ("SecError", "SourceUnreachable", "SecRefused", "MissingUserAgent", "UnknownTicker", "NotFound", "InvalidCik")


@pytest.mark.parametrize("name", ERRORS)
def test_every_sec_error_is_available_from_the_interface_entry_point(name):
    assert getattr(company, name) is getattr(sec_client, name)
    assert name in company.__all__


def test_the_entry_point_lists_what_the_interface_may_use():
    assert {"load_company", "DEMO_TICKERS"} <= set(company.__all__)


@pytest.mark.parametrize("typed", ["KO/../AAPL", "MCD/", "../demo/KO", "/etc", "KO\\..\\AAPL", ""])
def test_demo_mode_only_opens_the_listed_demo_companies(typed):
    # Security review of 21 November 2026: "KO/../AAPL" loaded Apple under the name typed, and "MCD/" loaded
    # McDonald's without its company-specific rule. The typed text never reaches the file system.
    with pytest.raises(company.UnknownTicker):
        company.load_company(typed, demo=True)


def test_demo_mode_still_opens_the_demo_companies_however_they_are_typed():
    assert company.load_company(" ko ", demo=True).ticker == "KO"
    assert company.load_company("JPM", demo=True).ticker == "JPM"  # kept so that the app can refuse a bank
