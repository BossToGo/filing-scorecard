"""Walking skeleton: the app starts and shows its first page, without a browser (Streamlit AppTest, SPEC §11).

Written by A in slice S0; owned by D from slice S10 on.
"""

from pathlib import Path

from streamlit.testing.v1 import AppTest

MAIN = Path(__file__).resolve().parents[2] / "main.py"


def test_the_first_page_loads_without_an_error():
    app = AppTest.from_file(str(MAIN)).run(timeout=30)
    assert not app.exception
    assert app.title[0].value == "Filing Scorecard"
