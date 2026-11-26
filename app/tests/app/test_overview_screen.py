"""The overview above the tabs, drawn without a browser (Streamlit AppTest; slice S10c). Owner: A.

Expected texts are the hand-worked values of docs/acceptance.md, "Overview (S10c)" (AC16 to AC18; numbered AC12 to AC14 until 26 November); the screen only
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


def test_ac16_coca_cola_key_figures_coverage_and_balance_sheet_are_shown():
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


def test_ac17_amazon_shows_no_dividend_paid():
    text = shown(run("AMZN"))
    assert "No dividend paid" in text
    assert "0.0%" not in text


def test_ac18_a_missing_figure_shows_na_with_its_reason_never_zero():
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


def test_the_panel_shows_the_radar_and_explains_it_without_repeating_the_marks():
    # was "the radar and the checks by area": the panel's own rows of marks and legend repeated the score chart below
    # it, which shows the same marks with each check's name and reason (Simon's open point on #63; Igor's decision,
    # 26 November; rule 14.6, agreed by Igor). The total and the area to read first stay out (#60).
    at = run_with_checks("KO")
    text, seen = shown(at), visible(at)
    assert "Checks by area" in seen and "Centre 0% · edge 100%" in seen
    assert "score chart below" in seen  # where each area's six checks are listed, with their reasons
    assert len(at.get("plotly_chart")) == 2  # the radar and the five-year chart
    for gone in ("fs-ov-mk", "fs-ov-area", "fs-ov-total", "fs-ov-strong", "fs-ov-focus"):  # marks, rows, total, focus
        assert gone not in text, gone


def test_the_radar_labels_each_area_with_its_share_or_why_it_is_off_the_shape():
    from src.data.company import load_company
    from src.overview import scorecard
    from ui import overview as ui_overview
    from ui.results import check_results

    card = scorecard(check_results(load_company("AMZN", demo=True)))
    labels = " ".join(str(t) for trace in ui_overview._radar(card).data for t in (trace.theta or ()))
    for area in card.areas:
        assert area.label.split()[0] in labels and area.share_text in labels, area.label
    assert "No dividend paid" in labels  # Amazon's dividend: off the shape, said in words


def test_the_radar_fills_only_a_complete_shape_and_never_draws_through_the_centre():
    from src.contracts import CheckResult
    from src.overview import radar_shape, scorecard
    from ui import overview as ui_overview

    def card(valuation):
        found = {"past_performance": ("pass",) * 4 + ("insufficient_data",) * 2, "financial_health": ("pass",) * 6,
                 "dividend": ("pass",) * 6, "valuation": valuation}
        letters = {"past_performance": "P", "financial_health": "H", "dividend": "D", "valuation": "V"}
        return scorecard({a: None if st is None else tuple(CheckResult(f"{letters[a]}{n}", s, None, None, (), s)
                                                             for n, s in enumerate(st, 1)) for a, st in found.items()})

    open_card, full_card = card(None), card(("pass",) * 3 + ("fail",) * 3)
    open_fig, full_fig = ui_overview._radar(open_card), ui_overview._radar(full_card)
    assert not any(t.fill == "toself" for t in open_fig.data)  # valuation off: no filled shape
    lines = [t for t in open_fig.data if t.mode and "lines" in t.mode]
    assert len(lines) == len(radar_shape(open_card).edges) == 2  # top–right and left–top, never right–left
    assert sum(t.fill == "toself" for t in full_fig.data) == 1  # all four scored: one closed, filled shape


def test_the_radar_says_it_is_not_a_rating():
    # was "the radar and the legend" (twice): the panel's legend went with its rows; the score chart's legend below
    # says it too on the page (rule 14.6, agreed by Igor)
    assert visible(run_with_checks("KO")).count("Not a rating of the share and not advice") >= 1


def test_the_overview_leaves_the_page_width_to_the_score_chart():
    # replaces "the marks are square as on the main chart": the panel has no marks any more. Once D placed the
    # overview above the score chart (#63), its page-wide width rule overrode D's (audit of 26 November).
    from ui import overview as ui_overview

    css = ui_overview._style()
    assert "stMainBlockContainer" not in css and "stSidebar" not in css


def test_without_check_results_there_is_no_scorecard_panel():
    # was "Company scorecard", the panel's old heading; the panel is now headed "Checks by area"
    assert "Checks by area" not in shown(run("KO"))


def test_amazon_panel_says_no_dividend_paid():
    # was also "0 passed of 1 assessed" in the panel's rows; the rows went to the score chart (see above). The words
    # stay visible in the coverage card and under the radar's dividend axis (rule 14.6, agreed by Igor)
    assert "No dividend paid" in visible(run_with_checks("AMZN"))


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

