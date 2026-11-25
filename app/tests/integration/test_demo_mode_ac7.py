"""Demo mode opens the five demo companies in the app with the network off (slice S14, AC7). Owner: A.

Runs the real `main.py` through Streamlit's AppTest, with the network blocked as in every test
(`tests/network_guard.py`). The five tickers are written here by hand, not read from the code under test.
Expected names: the "name" field of each company's saved SEC submissions file in `app/evidence/demo/<ticker>/`
(read on 23 November 2026), which SPEC 2.4.1 §3 says the header shows as the SEC lists it.
"""

from pathlib import Path

import pytest
from streamlit.testing.v1 import AppTest

from tests import network_guard

MAIN = str(Path(__file__).resolve().parents[2] / "main.py")

SEC_NAMES = {
    "KO": "COCA COLA CO",
    "AAPL": "Apple Inc.",
    "NVDA": "NVIDIA CORP",
    "MCD": "MCDONALDS CORP",
    "AMZN": "AMAZON COM INC",
}

TEXT_ELEMENTS = ("title", "header", "subheader", "markdown", "caption")


def open_in_demo_mode(ticker: str) -> AppTest:
    app = AppTest.from_file(MAIN).run(timeout=30)
    app.toggle(key="demo").set_value(True)
    app.selectbox(key="company").set_value(ticker)
    app.button(key="show").click()
    return app.run(timeout=60)


@pytest.mark.parametrize("ticker", list(SEC_NAMES))
def test_each_demo_company_opens_with_the_network_off_ac7(ticker):
    attempts_before = len(network_guard.ATTEMPTS)

    app = open_in_demo_mode(ticker)

    assert not app.exception, f"{ticker}: the app crashed"
    assert [e.value for e in app.error] == [], f"{ticker}: an error message is shown"
    assert network_guard.ATTEMPTS[attempts_before:] == [], f"{ticker}: demo mode tried the network"
    shown = [str(e.value) for kind in TEXT_ELEMENTS for e in getattr(app, kind)]
    assert any(SEC_NAMES[ticker] in text for text in shown), f"{ticker}: the SEC name is not on the page"
    warnings = " ".join(str(w.value) for w in app.warning).lower()
    assert "not fully checked" not in warnings, f"{ticker}: a demo company is marked not fully checked"
    assert app.expander, f"{ticker}: no checks are shown"
