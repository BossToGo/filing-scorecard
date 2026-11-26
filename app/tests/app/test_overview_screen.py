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


def visible(at: AppTest) -> str:
    """What a reader sees: the page text without tags and attributes (so not an aria-label or a title)."""
    import html
    import re

    text = re.sub(r"<style>.*?</style>", " ", shown(at), flags=re.S)
    text = re.sub(r"<[^>]+>", " ", text)
    return " ".join(html.unescape(text).split())


def test_ac12_coca_cola_key_figures_coverage_and_balance_sheet_are_shown():
    text = shown(run("KO"))
    for expected in ("47.94", "+1.9%", "28.7", "+7.5 pp", "13.11", "+23.3%", "5.30", "+11.7%", "vs FY2024",
                     "60.3%", "USD 3.48 bn", "Dividends above free cash flow", "1.46×", "0001628280-26-010047",
                     "20 February 2026", "27 metrics · 119 records"):  # was "27 metrics, 119 records": label only, "·" as in Igor's design of 25 November (rule 14.6, agreed by Igor)
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


def test_the_scorecard_panel_shows_the_radar_and_the_checks_by_area_without_a_total():
    # was "the total, the radar and the checks by area": the total is out (the group's answers on #60, 26 November;
    # rule 14.6, agreed by Igor); the radar is back at Igor's request
    from src.data.company import load_company
    from src.overview import scorecard
    from ui.results import check_results

    card = scorecard(check_results(load_company("KO", demo=True)))
    at = run_with_checks("KO")
    text = shown(at)
    seen = visible(at)
    assert "Checks by area" in seen
    for area in card.areas:  # was `area.count_text in text`, which also matched the hidden aria-label; the visible
        # count is `short_text` since Emma's review of #60 (26 November; rule 14.6, agreed by Igor)
        assert area.label in seen and area.short_text in seen, area.label
    assert text.count('class="fs-ov-mk') >= 24 + 4  # six marks per area, plus the legend
    assert len(at.get("plotly_chart")) == 2  # the radar and the five-year chart
    assert "Centre 0% · edge 100%" in seen
    for gone in ("fs-ov-total", "fs-ov-strong", "fs-ov-focus"):  # the total, its label and the area to read first
        assert gone not in text, gone


def test_the_radar_and_the_legend_say_they_are_not_a_rating():
    # was "the total and the radar" (twice): the total is out, so the sentence is under the radar and in the legend, as
    # SPEC §3 asks of every score chart's legend (rule 14.6, agreed by Igor)
    assert visible(run_with_checks("KO")).count("Not a rating of the share and not advice") >= 2


def test_the_marks_are_square_as_on_the_main_chart():
    # Simon's condition on #60 for keeping the checks by area (26 November): the same square marks as the score chart
    from ui import overview as ui_overview

    css = ui_overview._style()
    rule = css[css.index(".fs-ov-mk {"):].split("}", 1)[0]
    assert "border-radius:4px" in rule and "50%" not in rule


def test_without_check_results_there_is_no_scorecard_panel():
    # was "Company scorecard", the panel's old heading; the panel is now headed "Checks by area"
    assert "Checks by area" not in shown(run("KO"))


def test_amazon_panel_says_no_dividend_paid():
    # was a search of the HTML source, where the text sat only in the aria-label; now the visible text (Emma's
    # review of #60, SPEC §3 and AC15; rule 14.6, agreed by Igor)
    seen = visible(run_with_checks("AMZN"))
    assert "No dividend paid" in seen and "0 passed of 1 assessed" in seen


def test_an_area_not_in_this_version_reads_as_on_the_main_screen():
    from src.data.company import load_company
    from ui.results import check_results

    missing = [area for area, found in check_results(load_company("KO", demo=True)).items() if found is None]
    seen = visible(run_with_checks("KO"))
    for area in missing:
        assert "Not part of this version" in seen, area


def page_with_frame(ticker: str) -> None:
    from src.data.company import load_company
    from src.overview import overview
    from ui.overview import render_overview, render_page_shell
    from ui.results import check_results

    data = load_company(ticker, demo=True)
    render_page_shell(data, overview(data))
    render_overview(data, check_results(data))


def test_each_menu_link_goes_to_its_own_section_with_the_main_screens_names():
    from ui.overview import NAV

    at = AppTest.from_function(page_with_frame, args=("KO",), default_timeout=30)
    at.run()
    assert not at.exception, at.exception
    page = shown(at) + "\n".join(m.value for m in at.sidebar.markdown)
    anchors = [anchor for _, anchor, _ in NAV]
    assert len(set(anchors)) == len(anchors)  # "Cash flow" and "Dividends" both went to the coverage card
    for anchor in anchors:
        assert f'href="#{anchor}"' in page and f'id="{anchor}"' in page, anchor
    labels = [label for label, _, _ in NAV]
    assert "Sources" in labels and "Dividend" in labels  # the Sources tab and the Dividend area of the main screen
    for word in ("Company research", "Company report"):  # one name for the page (Emma's review of #60)
        assert word not in page, word


def test_passed_is_the_accent_and_failed_the_text_colour_never_green_or_red(monkeypatch):
    import streamlit as st

    from ui import overview as ui_overview

    theme = {"theme.primaryColor": "#111111", "theme.textColor": "#222222", "theme.greenColor": "#00ff00",
             "theme.redColor": "#ff0000"}
    monkeypatch.setattr(st, "get_option", lambda key: theme.get(key))
    assert ui_overview._pass_colour() == "#111111"
    css = ui_overview._style()
    assert "--ov-pass:light-dark(#111111, #111111)" in css and "--ov-fail:light-dark(#222222, #222222)" in css
    assert "#00ff00" not in css and "#ff0000" not in css  # SPEC §3; decision log "never red or green"


def test_chart_colours_given_as_text_on_the_command_line_are_read_as_a_list(monkeypatch):
    import streamlit as st

    from ui import overview as ui_overview

    real = st.get_option
    monkeypatch.setattr(st, "get_option", lambda key: '["#111111", "#222222", "#333333"]'
                        if key == "theme.chartCategoricalColors" else real(key))
    assert ui_overview._series_colours() == ("#111111", "#222222", "#333333")

