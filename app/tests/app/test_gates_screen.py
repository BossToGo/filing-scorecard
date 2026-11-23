"""Stops, header warnings and error messages on screen (Streamlit AppTest; slice S11). Owner: D.

SEC errors in live mode are simulated with a stand-in for `load_company` (no network). Expected texts: see
`test_messages.py` (proposed by review assistants, accepted by Simon on 23 November 2026).
"""

from pathlib import Path

import pytest
from streamlit.testing.v1 import AppTest

import src.data.company as company_module
from src.data.company import SourceUnreachable, UnknownTicker

MAIN = str(Path(__file__).resolve().parents[2] / "main.py")


def show(ticker: str, *, demo: bool = True, price: str = "") -> AppTest:
    app = AppTest.from_file(MAIN).run(timeout=30)
    if ticker in ("KO", "AAPL", "NVDA", "MCD", "AMZN"):
        app.selectbox(key="company").set_value(ticker)
    else:
        app.selectbox(key="company").set_value("Other ticker").run(timeout=30)
        app.text_input(key="ticker").set_value(ticker)
    app.toggle(key="demo").set_value(demo)
    app.text_input(key="price").set_value(price)
    app.button(key="show").click()
    return app.run(timeout=60)


def raising(error):
    def fake_load_company(ticker, *, demo=False, **kwargs):
        raise error
    return fake_load_company


def details(app: AppTest):
    return next(e for e in app.expander if e.label == "Technical details")


def test_jpmorgan_is_not_supported_and_shows_no_score_ac2():
    app = show("JPM")
    assert not app.exception
    assert [e.value for e in app.error] == [
        "Not supported: JPMORGAN CHASE & CO is in an industry these checks do not cover (banks, insurers, real "
        "estate trusts; SEC industry code 6021). Pick one of the five demo companies, or type another ticker."]
    shown = "\n".join(m.value for m in app.markdown)
    assert "passed of" not in shown and "fs-block" not in shown  # no score chart
    assert not app.dataframe and not app.expander  # no checks, no sources


def test_a_ticker_outside_the_demo_data_in_demo_mode():
    app = show("MSFT")
    assert app.error[0].value.startswith("MSFT is not one of the five saved companies.")
    assert not details(app).proto.expanded


def test_unknown_ticker_live_e1(monkeypatch):
    monkeypatch.setattr(company_module, "load_company", raising(UnknownTicker("ZZZZ: no such ticker (raw)")))
    app = show("ZZZZ", demo=False)
    assert app.error[0].value == "We could not find this ticker. Check the spelling, or pick one of the five demo companies."
    assert not details(app).proto.expanded
    assert "ZZZZ: no such ticker (raw)" in [c.value for c in details(app).code]


def test_sec_unreachable_suggests_demo_mode_e4(monkeypatch):
    monkeypatch.setattr(company_module, "load_company", raising(SourceUnreachable("timed out (raw)")))
    app = show("MSFT", demo=False)
    assert "switch on demo mode" in app.error[0].value
    assert not details(app).proto.expanded


def test_an_invalid_price_still_says_how_to_type_it_v2():
    assert [e.value for e in show("KO", price="abc").error] == ["Type the price in US dollars, e.g. 1234 or 182.50"]


def test_coca_cola_has_no_header_warning_and_its_reading_note_is_on_the_sources_page_e15():
    from src.data.company import load_company

    app = show("KO")
    assert not app.warning  # neither "not fully checked" nor "old", and no other warning in the header
    notes = "\n".join(m.value for m in app.markdown)
    for warning in load_company("KO", demo=True).warnings:
        assert warning in notes


def synthetic_page():
    from src.data.company import DEMO_TICKERS
    from src.gates import check_gates
    from src.settings import load_settings
    from tests.fixtures import synthetic
    from ui.messages import header_warnings
    from ui.scorecard import render_scorecard

    data = synthetic.company_data()
    gates = load_settings()["gates"]
    result = check_gates(data, gates, DEMO_TICKERS)
    render_scorecard(data, {}, None, warnings=header_warnings(result, gates))


def test_a_company_outside_the_five_shows_not_fully_checked_in_the_header_e16():
    app = AppTest.from_function(synthetic_page).run(timeout=30)
    assert "Not fully checked: read automatically, not compared by hand for this company." in [
        w.value for w in app.warning]
