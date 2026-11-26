"""Display fixes from Igor's review on #47 (slice S10d). Owner: D.

Coca-Cola in demo mode with a typed price of USD 65.40, through main.py. Expected texts written by hand from the
figures on screen (Simon, 26 November 2026): the check sentences as the checks write them, the share count date
from the cover of Coca-Cola's 10-K (18 February 2026), and the names A's overview already shows.
"""

from __future__ import annotations

from pathlib import Path

from streamlit.testing.v1 import AppTest

MAIN = str(Path(__file__).resolve().parents[2] / "main.py")
_APP = {}


def ko() -> AppTest:
    if "KO" not in _APP:
        app = AppTest.from_file(MAIN).run(timeout=30)
        app.selectbox(key="company").set_value("KO")
        app.text_input(key="price").set_value("65.40")
        app.button(key="show").click()
        _APP["KO"] = app.run(timeout=60)
    return _APP["KO"]


def row(check_id: str) -> str:
    from ui.scorecard import _plain_name, load_texts

    name = _plain_name(check_id, load_texts())
    return next(e.label for e in ko().expander if f"**{name}.**" in e.label)


def open_table(check_id: str):
    from ui.scorecard import _plain_name, load_texts

    name = _plain_name(check_id, load_texts())
    return next(e for e in ko().expander if f"**{name}.**" in e.label).table[0].value


# --- 1. the check's own sentence in the closed row -----------------------------------------------------------------

def test_closed_rows_show_the_check_s_own_sentence_not_two_numbers():
    expected = {
        "P1": "Passed. Net income was positive in 5 of the last 5 fiscal years (2021 to 2025); at least 4 are required.",
        "H1": "Passed. On 31 December 2025, short-term assets were USD 31,044 million, above short-term liabilities of "
              "USD 21,281 million. Assets must be higher to pass.",
        "D1": "Passed. Dividends paid in the fiscal year ended 31 December 2025: USD 8,779 million.",
        "V3": "Passed. Price to earnings 21.46 (share price USD 65.40 × 4,300,723,069 shares = USD 281,267.3 million, "
              "÷ net income USD 13,107 million, fiscal year ended 31 December 2025) against 37.11 for the industry.",
    }
    for check_id, sentence in expected.items():
        assert row(check_id).endswith(sentence), check_id
        assert " against USD " not in row("H1")


# --- 2. plain names in the open checks' tables ---------------------------------------------------------------------

def test_figures_have_the_overview_s_names():
    figures = set(open_table("P3")["Figure"]) | set(open_table("H1")["Figure"]) | set(open_table("D6")["Figure"])
    figures |= set(open_table("V3")["Figure"]) | set(open_table("H4")["Figure"]) | set(open_table("P5")["Figure"])
    for code in ("net_income", "revenue", "cash", "financial_debt", "total_assets"):
        assert code not in figures, code
    assert {"Net income", "Revenue"} <= figures


# --- 3. a share count is a date, not a fiscal year -------------------------------------------------------------------

def test_the_share_count_reads_as_of_its_date():
    table = open_table("V3")
    shares = table[table["Figure"] == "shares"]
    assert list(shares["Period"]) == ["as of 18 February 2026"]
    net_income = table[table["Figure"] == "Net income"]
    assert list(net_income["Period"]) == ["fiscal year ended 31 December 2025"]
