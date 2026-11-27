"""End-to-end app test (slice S17, SPEC §13 "End to end" row). Owner: D.

Runs the real `main.py` through Streamlit's AppTest with demo mode on and the network blocked (as in every test,
`tests/network_guard.py`), doing only what a user does: pick the company, leave the share price empty, press Show
scorecard. Expected values come from people, never from running the code (rule 14.5):

- Known figure: McDonald's revenue for fiscal year 2025 is USD 26,885 million, read by hand by Simon (D) from the
  10-K filed 24 February 2026, page 40, "Total revenues" (S15 reconciliation, `tests/reconciliation/MCD.yaml`).
  P5 is assessed for McDonald's (Greg's check on #63: "MCD P4 fail / P5 pass").
- Known score: Amazon's dividend row reads "No dividend paid" and "0 passed of 1 assessed" (Simon's hand check of
  25 November 2026: D1 failed, the five other dividend checks do not apply).
- Known estimate: added in a second commit, once the group has decided #71 and C has signed an estimate for KO.

The helpers below are copied from `show()` in `test_valuation_screen.py` and A's `open_in_demo_mode()` in
`tests/integration/test_demo_mode_ac7.py`, not imported, so this file depends on no other member's test file.
"""

from pathlib import Path

from streamlit.testing.v1 import AppTest

from tests import network_guard

MAIN = str(Path(__file__).resolve().parents[2] / "main.py")
TEXT_ELEMENTS = ("title", "header", "subheader", "markdown", "caption")


def open_as_a_user(ticker: str) -> AppTest:
    """Pick the company, leave the price empty, press Show scorecard: demo mode on, the network blocked."""
    app = AppTest.from_file(MAIN).run(timeout=30)
    app.toggle(key="demo").set_value(True)
    app.selectbox(key="company").set_value(ticker)
    app.text_input(key="price").set_value("")
    app.button(key="show").click()
    return app.run(timeout=60)


def page_text(app: AppTest) -> str:
    texts = [str(e.value) for kind in TEXT_ELEMENTS for e in getattr(app, kind)]
    texts += [e.label for e in app.expander] + [t.label for t in app.tabs]
    texts += [table.value.to_string() for table in app.table]
    return "\n".join(texts)


def assert_a_clean_page(app: AppTest, attempts_before: int):
    assert not app.exception, "the app crashed"
    assert [e.value for e in app.error] == [], "an error box is shown"
    assert network_guard.ATTEMPTS[attempts_before:] == [], "demo mode tried the network"
    assert "fair value" not in page_text(app).lower(), 'the page says "fair value"'


def test_mcdonalds_revenue_fy2025_shows_in_p5_row_and_figures_table():
    attempts_before = len(network_guard.ATTEMPTS)
    app = open_as_a_user("MCD")
    assert_a_clean_page(app, attempts_before)

    p5 = [e for e in app.expander if "**Margin above its industry.**" in e.label]
    assert len(p5) == 1, "P5 is not on the page once; stop and tell Simon (no fallback to another check)"
    assert "on USD 26,885 million revenue" in p5[0].label, p5[0].label
    values = list(p5[0].table[0].value["Value"])
    assert "USD 26,885 m" in values, values


def test_amazon_dividend_row_reads_no_dividend_paid_0_passed_of_1_assessed():
    attempts_before = len(network_guard.ATTEMPTS)
    app = open_as_a_user("AMZN")
    assert_a_clean_page(app, attempts_before)

    import re

    chart = next(m.value for m in app.markdown if "fs-row" in m.value)
    dividend = re.search(r'<div class="fs-row"><span class="fs-area">Dividend</span>.*?</div>', chart).group(0)
    assert "No dividend paid" in dividend and "0 passed of 1 assessed" in dividend, dividend
