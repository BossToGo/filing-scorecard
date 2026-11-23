"""The scorecard screen without a browser (Streamlit AppTest; slice S10). Owner: D.

Synthetic company (AC3, V3, AC4, AC5): the check results are built by hand with the statuses of Simon's AC3
sign-off, https://github.com/BossToGo/filing-scorecard/pull/5#pullrequestreview-5977120036 , and no value, so no
locked expected value of another owner is used. **Switch this test to the real check modules (`ui.results`) once
B's #28 and #29 and C's #23 are merged** (S17 then checks the whole chain).

Demo companies (AC1, V4) go through `main.py` itself, on the saved SEC data (no network).
"""

from pathlib import Path

from streamlit.testing.v1 import AppTest

MAIN = str(Path(__file__).resolve().parents[2] / "main.py")
AC3 = {
    "P1": "pass", "P2": "pass", "P3": "pass", "P4": "insufficient_data", "P5": "insufficient_data", "P6": "pass",
    "H1": "pass", "H2": "fail", "H3": "fail", "H4": "pass", "H5": "pass", "H6": "pass",
    "D1": "pass", "D2": "insufficient_data", "D3": "pass", "D4": "pass", "D5": "pass", "D6": "pass",
}


def synthetic_page(statuses):
    from datetime import date

    from src.contracts import CheckResult
    from tests.fixtures import synthetic
    from ui.results import AREA_CHECKS, AREAS
    from ui.scorecard import render_scorecard
    from ui.sources import render_sources

    data = synthetic.company_data()
    fy0 = date(2025, 12, 31)
    h3_inputs = tuple(data.fact(metric, fy0) for metric in ("financial_debt", "cash", "equity"))
    results = {
        area: None if area == "valuation" else tuple(
            CheckResult(cid, statuses[cid], None, None, h3_inputs if cid == "H3" else (), f"{cid}: built by hand (AC3)")
            for cid in AREA_CHECKS[area])
        for area in AREAS
    }
    render_scorecard(data, results, None)
    render_sources(data, results)


def run_synthetic() -> AppTest:
    return AppTest.from_function(synthetic_page, kwargs={"statuses": AC3}).run(timeout=30)


def texts(app: AppTest) -> str:
    return "\n".join(str(e.value) for kind in ("markdown", "caption", "warning", "header", "info") for e in getattr(app, kind))


def show(ticker: str, price: str = "") -> AppTest:
    app = AppTest.from_file(MAIN).run(timeout=30)
    app.selectbox(key="company").set_value(ticker)
    app.text_input(key="price").set_value(price)
    app.button(key="show").click()
    return app.run(timeout=60)


# --- synthetic company --------------------------------------------------------------------------------------------


def test_ac3_scores_on_screen():
    app = run_synthetic()
    assert not app.exception
    shown = texts(app)
    assert "4 passed of 4 assessed" in shown  # past performance
    assert "4 passed of 6 assessed" in shown  # financial health
    assert "5 passed of 5 assessed" in shown  # dividend
    assert "Not assessed until v0.2" in shown  # valuation, v0.1


def test_synthetic_data_mark_v3():
    assert "SYNTHETIC DATA" in "\n".join(w.value for w in run_synthetic().warning)


def test_a_closed_check_row_shows_mark_result_and_check_ac4():
    labels = [e.label for e in run_synthetic().expander]
    assert len(labels) == 18
    assert any(label.startswith("✕ Failed") and "H2" in label for label in labels)
    assert any(label.startswith("⋯ Not assessed") and "P4" in label for label in labels)


def test_an_open_check_shows_its_figures_with_units_and_fiscal_year_ac4():
    app = run_synthetic()
    h3 = next(e for e in app.expander if "H3" in e.label)
    table = h3.table[0].value if h3.table else h3.dataframe[0].value
    shown = table.astype(str).to_string()
    # Simon's sign-off: financial debt 450, cash 120, equity 820 (USD m, 2025)
    for figure in ("USD 450 m", "USD 120 m", "USD 820 m"):
        assert figure in shown
    assert "2025" in shown
    assert "SYNTHETIC DATA" in "\n".join(m.value for m in h3.markdown)  # no filing to link to


def test_sources_page_one_row_per_figure_ac5():
    from tests.fixtures import synthetic

    data = synthetic.company_data()
    table = run_synthetic().dataframe[-1].value
    assert len(table) == sum(len(by_year) for by_year in data.items.values())
    for column in ("Metric", "Value", "Unit", "Period", "Kind", "Tag", "Form", "Accession", "Filed", "Retrieved",
                   "Note", "Blocks checks"):
        assert column in table.columns


# --- demo companies through main.py ------------------------------------------------------------------------------


def test_start_screen_lists_the_five_demo_companies():
    shown = texts(AppTest.from_file(MAIN).run(timeout=30))
    for ticker in ("KO", "AAPL", "NVDA", "MCD", "AMZN"):
        assert ticker in shown


def test_coca_cola_header_shows_the_sec_name_ac1():
    app = show("KO")
    assert not app.exception
    assert "COCA COLA CO" in [h.value for h in app.header]
    assert "Beverages, SEC code 2080" in texts(app)


def test_apple_missing_interest_expense_is_n_a_with_its_reason_never_zero_v4():
    table = show("AAPL").dataframe[-1].value
    rows = table[table["Metric"] == "interest_expense"]
    missing = rows[rows["Kind"] == "missing"]
    assert len(missing) == 3  # fiscal 2024, 2025 and 2026
    for shown in missing["Value"]:
        assert shown.startswith("n/a: no annual 10-K value")


def test_a_typed_price_is_repeated_next_to_valuation():
    assert "At the price you typed: USD 182.50" in texts(show("KO", "182,50"))


def test_an_invalid_price_says_how_to_type_it():
    app = show("KO", "1,234")
    assert [e.value for e in app.error] == ["Type the price in US dollars, e.g. 1234 or 182.50"]
