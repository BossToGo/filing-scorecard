"""The overview above the tabs, drawn without a browser (Streamlit AppTest; slice S10c). Owner: A.

Expected texts are the hand-worked values of docs/acceptance.md, "Overview (S10c)" (AC12 to AC14); the screen only
shows what `src.overview` prepared, so these tests check that it shows all of it, and shows "n/a" with a reason.
"""

from streamlit.testing.v1 import AppTest


def page(ticker: str, missing: str | None = None) -> None:
    from dataclasses import replace
    from datetime import date

    from src.data.company import load_company
    from tests.fixtures import synthetic
    from ui.overview import render_overview

    data = synthetic.company_data() if ticker == "SYN" else load_company(ticker, demo=True)
    if missing:
        items = {m: dict(by_year) for m, by_year in data.items.items()}
        fact = items[missing][date(2025, 12, 31)]
        items[missing][date(2025, 12, 31)] = replace(fact, value=None, kind="missing", tag=None,
                                                     note="not in the filing")
        data = replace(data, items=items)
    render_overview(data)


def run(*args) -> AppTest:
    at = AppTest.from_function(page, args=args, default_timeout=30)
    at.run()
    assert not at.exception, at.exception
    return at


def shown(at: AppTest) -> str:
    return "\n".join(m.value for m in at.markdown) + "\n".join(c.value for c in at.caption)


def test_ac12_coca_cola_key_figures_coverage_and_balance_sheet_are_shown():
    text = shown(run("KO"))
    for expected in ("47.94", "+1.9%", "28.7", "+7.5 pp", "13.11", "+23.3%", "5.30", "+11.7%", "vs FY2024",
                     "60.3%", "USD 3.48 bn", "Dividends above free cash flow", "1.46×", "0001628280-26-010047",
                     "20 February 2026", "27 metrics, 119 records"):
        assert expected in text, expected


def test_each_key_figure_says_reported_or_derived():
    text = shown(run("KO"))
    assert text.count("Reported") >= 2 and text.count("Derived") >= 2


def test_the_chart_has_a_table_view_with_the_same_figures():
    at = run("SYN")
    assert at.get("plotly_chart")
    at.segmented_control(key="overview_view").set_value("Table").run()
    text = shown(at)
    for expected in ("2021", "2025", "USD 100 m", "USD 75 m", "USD 130 m", "USD 1.30 bn"):
        assert expected in text, expected


def test_ac13_amazon_shows_no_dividend_paid():
    text = shown(run("AMZN"))
    assert "No dividend paid" in text
    assert "0.0%" not in text


def test_ac14_a_missing_figure_shows_na_with_its_reason_never_zero():
    at = run("SYN", "operating_cash_flow")
    text = shown(at)
    assert "n/a" in text and "operating cash flow for FY2025: not in the filing" in text
    assert "Dividend coverage is not available" in text
    at.segmented_control(key="overview_view").set_value("Table").run()
    assert "n/a" in shown(at)


def test_no_advice_words_on_the_overview():
    text = shown(run("KO")).lower()
    for word in ("buy", "sell", "undervalued", "fair value", "cheap", "expensive"):
        assert f" {word} " not in f" {text} ", word


# --- the scorecard panel (Igor's design of 25 November) ---------------------------------------------------------


def page_with_checks(ticker: str) -> None:
    from src.data.company import load_company
    from ui.overview import render_overview
    from ui.results import check_results

    data = load_company(ticker, demo=True)
    render_overview(data, check_results(data))


def run_with_checks(ticker: str) -> AppTest:
    at = AppTest.from_function(page_with_checks, args=(ticker,), default_timeout=30)
    at.run()
    assert not at.exception, at.exception
    return at


def test_the_scorecard_panel_shows_the_total_the_radar_and_the_checks_by_area():
    from src.data.company import load_company
    from src.overview import scorecard
    from ui.results import check_results

    card = scorecard(check_results(load_company("KO", demo=True)))
    at = run_with_checks("KO")
    text = shown(at)
    passed, assessed = card.headline
    assert f">{passed}<small> / {assessed}</small>" in text and "assessed checks passed" in text
    assert f"{card.failed} failed · {card.not_assessed} not assessed" in text
    for area in card.areas:
        assert area.label in text and area.count_text in text
    assert text.count('class="fs-ov-mk') >= 24 + 4  # six marks per area, plus the legend
    charts = at.get("plotly_chart")
    assert len(charts) == 2  # the radar and the five-year chart


def test_without_check_results_there_is_no_scorecard_panel():
    assert "Company scorecard" not in shown(run("KO"))


def test_amazon_panel_says_no_dividend_paid():
    assert "No dividend paid · 0 passed of 1 assessed" in shown(run_with_checks("AMZN"))
