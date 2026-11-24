"""Customer messages for stops, header warnings and SEC errors (`app/ui/messages.py`; SPEC §3, §10; issue #32
point 9; slice S11). Owner: D.

The texts were proposed by review assistants and accepted by Simon (D) on 23 November 2026 (S11 prompt), including
the next step added to every stop message. No threshold is written in a text: it comes from the settings.
"""

from datetime import date

import pytest

from src.data.company import (InvalidCik, MissingUserAgent, NotFound, SecRefused, SourceUnreachable,
                              UnknownTicker)
from src.gates import GateResult, Stop
from src.settings import load_settings
from ui.messages import header_warnings, sec_error_message, stop_message

GATES = load_settings()["gates"]
NEXT = " Pick one of the five demo companies, or type another ticker."


def test_industry_stop():
    assert stop_message(Stop("industry", sic=6021), "JPMORGAN CHASE & CO") == (
        "Not supported: JPMORGAN CHASE & CO is in an industry these checks do not cover (banks, insurers, real "
        "estate trusts; SEC industry code 6021)." + NEXT)


def test_no_annual_data_stop():
    assert stop_message(Stop("no_annual_data"), "SOME CO") == (
        "Not supported: no annual report (10-K) figures were found for SOME CO." + NEXT)


def test_non_usd_stop():
    assert stop_message(Stop("non_usd"), "SOME CO") == "Not supported: SOME CO does not report in US dollars." + NEXT


def test_too_few_years_stop_takes_the_minimum_from_the_result():
    assert stop_message(Stop("too_few_years", years=2, minimum=3), "SOME CO") == (
        "Not supported: SOME CO has fewer than 3 fiscal years of figures." + NEXT)
    assert "fewer than 4 fiscal" in stop_message(Stop("too_few_years", years=2, minimum=4), "SOME CO")


def test_header_warnings():
    result = GateResult(stop=None, not_fully_checked=True, old_report_filed=date(2024, 8, 20))
    assert header_warnings(result, GATES) == (
        "Not fully checked: read automatically, not compared by hand for this company.",
        "Latest annual report is old: filed on 20 August 2024, more than 15 months before the data was read.",
    )


def test_the_old_report_months_come_from_the_settings():
    result = GateResult(stop=None, not_fully_checked=False, old_report_filed=date(2024, 8, 20))
    assert "more than 18 months" in header_warnings(result, {**GATES, "stale_report_months": 18})[0]


def test_no_header_warning():
    assert header_warnings(GateResult(stop=None, not_fully_checked=False, old_report_filed=None), GATES) == ()


def test_a_ticker_outside_the_demo_data_in_demo_mode():
    assert sec_error_message(UnknownTicker("raw"), "MSFT", demo=True) == (
        "MSFT is not one of the five saved companies. Switch demo mode off to look it up on the SEC website, or "
        "pick one of the five.")


@pytest.mark.parametrize("error", [UnknownTicker("raw"), NotFound("raw"), InvalidCik("raw")])
def test_a_ticker_not_found_live(error):
    assert sec_error_message(error, "ZZZZ", demo=False) == (
        "We could not find this ticker. Check the spelling, or pick one of the five demo companies.")


def test_sec_unreachable_suggests_demo_mode_e4():
    assert sec_error_message(SourceUnreachable("raw"), "MSFT", demo=False) == (
        "The SEC website cannot be reached right now. Try again later, or switch on demo mode to see the five "
        "saved companies.")


@pytest.mark.parametrize("error", [MissingUserAgent("raw"), SecRefused("raw")])
def test_sec_cannot_be_read(error):
    assert sec_error_message(error, "MSFT", demo=False) == (
        "The app cannot read SEC data at the moment. Switch on demo mode, or try again later.")
