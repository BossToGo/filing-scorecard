"""The scorecard screen without a browser (Streamlit AppTest; slice S10). Owner: D.

Synthetic company (AC3, V3, AC4, AC5): the check results are built by hand with the statuses of Simon's AC3
sign-off, https://github.com/BossToGo/filing-scorecard/pull/5#pullrequestreview-5977120036 , and no value, so no
locked expected value of another owner is used. **Switch this test to the real check modules (`ui.results`) once
B's #28 and #29 and C's #23 are merged** (S17 then checks the whole chain).

Demo companies (AC1, V4) go through `main.py` itself, on the saved SEC data (no network).
"""

from pathlib import Path

import pytest
from streamlit.testing.v1 import AppTest

MAIN = str(Path(__file__).resolve().parents[2] / "main.py")
CROSS = '<path d="M3.2 3.2l5.6 5.6M8.8 3.2 3.2 8.8"/>'  # the failed mark's cross (docs/design/mockup.html)
AC3 = {
    "P1": "pass", "P2": "pass", "P3": "pass", "P4": "insufficient_data", "P5": "insufficient_data", "P6": "pass",
    "H1": "pass", "H2": "fail", "H3": "fail", "H4": "pass", "H5": "pass", "H6": "pass",
    "D1": "pass", "D2": "insufficient_data", "D3": "pass", "D4": "pass", "D5": "pass", "D6": "pass",
}


def name_of(check_id: str) -> str:
    """E's name of a check, read from texts.yaml, so a test finds the row whatever the name is (her #55 renames some)."""
    from ui.scorecard import load_texts

    return load_texts()[check_id]["name"]


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
    with render_scorecard(data, results, None):  # the Sources tab, filled as main.py does
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
    """Label change (rule 14.6, Simon's written agreement of 25 November 2026): valuation in v0.1 reads "Not part of
    this version" (SPEC 2.4.2 §3, design spec §6), no longer "Not assessed until v0.2". The scores are unchanged."""
    app = run_synthetic()
    assert not app.exception
    shown = texts(app)
    assert "4 passed of 4 assessed" in shown  # past performance
    assert "4 passed of 6 assessed" in shown  # financial health
    assert "5 passed of 5 assessed" in shown  # dividend
    assert "Not part of this version" in shown  # valuation, v0.1


def chart(app: AppTest) -> str:
    return next(m.value for m in app.markdown if "fs-row" in m.value)


def row(app: AppTest, area: str) -> str:
    """One area row of the score chart, as HTML."""
    import re

    return re.search(rf'<div class="fs-row"><span class="fs-area">{area}</span>.*?</div>', chart(app)).group(0)


def test_ac3_rows_name_what_is_not_assessed_and_the_failed_checks():
    """Simon's hand count of 25 November 2026: past 2 not assessed (P4, P5), health 0, dividend 1 (D2); the AC3
    statuses fail H2 and H3. The hand-built explanations do not say "yet", so no "yet" is shown.

    Test change (rule 14.6, Simon's written agreement of 25 November 2026): the rows show E's names since #17, so the
    check is found by its name, looked up in texts.yaml (`name_of`), no longer by its id; no score, count or figure
    changed."""
    import re

    app = run_synthetic()
    assert "2 not assessed<" in row(app, "Past performance")
    assert "not assessed" not in row(app, "Financial health")
    assert "1 not assessed<" in row(app, "Dividend")
    assert 'aria-label="Financial health: 4 passed of 6 assessed"' in chart(app)
    assert 'aria-label="Past performance: 4 passed of 4 assessed, 2 not assessed"' in chart(app)
    assert len(re.findall(r'class="fs-mk fs-wait"', row(app, "Valuation"))) == 6
    failed = next(m.value for m in app.markdown if "Failed checks" in m.value)
    assert re.findall(r"</span>([^<]+)<span class=\"fs-sub\">([\w ]+)</span>", failed) == [
        (name_of("H2"), "Financial health"), (name_of("H3"), "Financial health")]


def test_the_legend_names_the_four_marks_and_says_it_is_not_advice():
    shown = chart(run_synthetic())
    for word in ("Passed", "Failed", "Not assessed", "Does not apply", "not a rating of the share and not advice"):
        assert word in shown


def test_no_failed_check_says_so():
    app = AppTest.from_function(synthetic_page, kwargs={"statuses": {cid: "pass" for cid in AC3}}).run(timeout=30)
    assert "No check failed." in texts(app)


def test_coca_cola_dividend_is_one_not_assessed_yet():
    """C's D2 explanation says "not assessed yet" (Simon, 25 November 2026). The check that past performance and
    financial health show "Not assessed" without a module was removed with Simon's agreement of 25 November 2026:
    B's modules are on main since #28 and #29, so it could no longer fail."""
    pytest.importorskip("src.checks.dividend", reason="needs C's dividend module (merged in #23)")
    app = show("KO")
    assert "4 passed of 5 assessed" in row(app, "Dividend") and "1 not assessed yet" in row(app, "Dividend")


def test_a_mark_s_hover_text_does_not_repeat_the_word():
    """Simon, 25 November 2026: same rule as the row. Not "Not assessed. This check is not assessed yet: ..." on D2's
    mark; the word stays when the explanation does not say it (P4)."""
    pytest.importorskip("src.checks.dividend", reason="needs C's dividend module (merged in #23)")
    shown = chart(show("KO"))
    assert "Not assessed. This check is not assessed yet" not in shown
    assert f'title="{name_of("D2")}: This check is not assessed yet: ' in shown
    assert f'title="{name_of("P4")}: Not assessed. ' in shown


def test_amazon_dividend_row_reads_no_dividend_paid_0_passed_of_1_assessed():
    """Simon's hand check of 25 November 2026 (SPEC §3): D1 failed, five does-not-apply marks."""
    import re

    pytest.importorskip("src.checks.dividend", reason="needs C's dividend module (merged in #23)")
    dividend = row(show("AMZN"), "Dividend")
    assert "No dividend paid" in dividend and "0 passed of 1 assessed" in dividend
    assert len(re.findall(r'class="fs-mk fs-none"', dividend)) == 5


def test_one_tab_per_area_and_the_sources_last():
    """SPEC 2.4.2 §3 item 5: one tab per area, the sources page last; the summary stays above the tabs.

    Test change (rule 14.6, Simon's written agreement of 25 November 2026): the rows show E's names since #17, so the
    check is found by its name, looked up in texts.yaml (`name_of`), no longer by its id; no score, count or figure
    changed."""
    app = run_synthetic()
    assert [t.label for t in app.tabs] == ["Past performance", "Financial health", "Dividend", "Valuation", "Sources"]
    past, health, dividend, valuation, sources = app.tabs
    assert [e.label for e in health.expander][2].count(f"**{name_of('H3')}.**") == 1 and len(health.expander) == 6
    assert len(past.expander) == len(dividend.expander) == 6 and not valuation.expander
    assert "Not part of this version" in "\n".join(str(m.value) for m in valuation.markdown)
    assert sources.dataframe and not any("fs-row" in m.value for t in app.tabs for m in t.markdown)


def test_synthetic_data_mark_v3():
    assert "SYNTHETIC DATA" in "\n".join(w.value for w in run_synthetic().warning)


FAILED_ICON = ":material/disabled_by_default:"
WAIT_ICON = ":gray[:material/check_box_outline_blank:]"


def test_a_closed_check_row_shows_mark_result_and_check_ac4():
    """Label change (rule 14.6, Simon's written agreement of 25 November 2026): the row starts with the design's
    Material icon, no longer the "✕" or "⋯" character (design spec §4); the result word and the check stay.

    Test change (rule 14.6, Simon's written agreement of 25 November 2026): the rows show E's names since #17, so the
    check is found by its name, looked up in texts.yaml (`name_of`), no longer by its id; no score, count or figure
    changed."""
    labels = [e.label for e in run_synthetic().expander]
    assert len(labels) == 18
    assert any(label.startswith(f"{FAILED_ICON} **{name_of('H2')}.** Failed") for label in labels)
    assert any(label.startswith(f"{WAIT_ICON} **{name_of('P4')}.** :gray[Not assessed.") for label in labels)


def one_check(result):
    from tests.fixtures import synthetic
    from ui.scorecard import load_texts, render_check

    render_check(synthetic.company_data(), result, load_texts())


def closed_row(*args) -> str:
    from src.contracts import CheckResult

    return AppTest.from_function(one_check, args=(CheckResult(*args),)).run(timeout=30).expander[0].label


def test_until_e_s_texts_a_closed_check_says_its_result_and_figures():
    """Simon's sentence of 25 November 2026, kept with E's texts (#17): "Passed. USD 31,044 m against USD 21,281 m."

    Test change (rule 14.6, Simon's written agreement of 25 November 2026): the rows show E's names since #17, so the
    check is found by its name, looked up in texts.yaml (`name_of`), no longer by its id; no score, count or figure
    changed."""
    assert closed_row("H1", "pass", 31_044e6, 21_281e6, (), "x").endswith(
        f"**{name_of('H1')}.** Passed. USD 31,044 m against USD 21,281 m.")
    assert closed_row("H1", "fail", 31_044e6, 49_260e6, (), "x") == (
        f"{FAILED_ICON} **{name_of('H1')}.** Failed. USD 31,044 m against USD 49,260 m.")
    assert closed_row("D3", "pass", None, None, (), "x").endswith(f"**{name_of('D3')}.** Passed.")


def test_amazon_d1_says_no_dividend_paid_never_usd_0_m():
    """Simon's look of 25 November 2026, Flo's rule: a dividend treated as nil is "no dividend paid", never "USD 0 m".
    When a figure of the check is an assumption, the row shows the check's own explanation instead of the figures.

    Test change (rule 14.6, Simon's written agreement of 25 November 2026): the rows show E's names since #17, so the
    check is found by its name, looked up in texts.yaml (`name_of`), no longer by its id; no score, count or figure
    changed."""
    pytest.importorskip("src.checks.dividend", reason="needs C's dividend module (merged in #23)")
    d1 = next(e.label for e in show("AMZN").expander if f"**{name_of('D1')}.**" in e.label)
    assert "USD 0 m" not in d1
    assert d1.startswith(f"{FAILED_ICON} **{name_of('D1')}.** Failed. No dividend paid in the fiscal year ended 31 December 2025")


def test_amazon_d1_shows_its_explanation_once_in_the_row():
    """Simon, 25 November 2026: a passed or failed check whose row already shows its explanation (an assumed figure)
    does not repeat it under "How it is calculated" in the open detail (Igor's review of #35: once).

    Test change (rule 14.6, Simon's written agreement of 25 November 2026): the rows show E's names since #17, so the
    check is found by its name, looked up in texts.yaml (`name_of`), no longer by its id; no score, count or figure
    changed."""
    pytest.importorskip("src.checks.dividend", reason="needs C's dividend module (merged in #23)")
    d1 = next(e for e in show("AMZN").expander if f"**{name_of('D1')}.**" in e.label)
    shown = [d1.label, *(m.value for m in d1.markdown)]
    assert sum("No dividend paid in the fiscal year ended 31 December 2025" in line for line in shown) == 1
    assert not any(m.value.startswith("**How it is calculated:**") for m in d1.markdown)


def test_amazon_d1_detail_has_no_value_against_threshold_line():
    """Simon's look of 25 November 2026, same rule as the row: with an assumed figure, no "Value: USD 0 m · compared
    with: USD 0 m"; the figure table already says "no dividend paid".

    Test change (rule 14.6, Simon's written agreement of 25 November 2026): the rows show E's names since #17, so the
    check is found by its name, looked up in texts.yaml (`name_of`), no longer by its id; no score, count or figure
    changed."""
    pytest.importorskip("src.checks.dividend", reason="needs C's dividend module (merged in #23)")
    d1 = next(e for e in show("AMZN").expander if f"**{name_of('D1')}.**" in e.label)
    assert not any(m.value.startswith("**Value:**") for m in d1.markdown)
    assert "USD 0 m" not in "\n".join(m.value for m in d1.markdown)
    table = d1.table[0].value if d1.table else d1.dataframe[0].value
    assert "no dividend paid" in table.astype(str).to_string()


def test_the_company_heading_has_no_link_icon():
    """Simon's look of 25 November 2026: Streamlit 1.67 adds a link icon to headings (`stHeaderActionElements`);
    hidden on the company heading only."""
    from ui.scorecard import _style

    assert 'h1:has(.fs-ticker) [data-testid="stHeaderActionElements"] {display:none}' in _style()


def test_the_word_is_not_repeated_when_the_explanation_already_says_it():
    """Simon's look of 25 November 2026: not "Not assessed. This check is not assessed yet: ...". The word is left out
    when the explanation's first clause already contains it.

    Test change (rule 14.6, Simon's written agreement of 25 November 2026): the rows show E's names since #17, so the
    check is found by its name, looked up in texts.yaml (`name_of`), no longer by its id; no score, count or figure
    changed."""
    d2 = "This check is not assessed yet: it needs the share price and the US market dividend yield."
    assert closed_row("D2", "insufficient_data", None, None, (), d2) == f"{WAIT_ICON} **{name_of('D2')}.** :gray[{d2}]"
    p4 = "Not assessed: needs a sourced industry return on equity benchmark."
    assert closed_row("P4", "insufficient_data", None, None, (), p4) == f"{WAIT_ICON} **{name_of('P4')}.** :gray[{p4}]"
    assert closed_row("P4", "insufficient_data", None, None, (), "P4: built by hand (AC3)") == (
        f"{WAIT_ICON} **{name_of('P4')}.** :gray[Not assessed. P4: built by hand (AC3)]")


def test_does_not_apply_shows_the_check_s_own_explanation_unchanged():
    """Simon, 25 November 2026: Flo's explanation as it is, under the "Does not apply" label.

    Test change (rule 14.6, Simon's written agreement of 25 November 2026): the rows show E's names since #17, so the
    check is found by its name, looked up in texts.yaml (`name_of`), no longer by its id; no score, count or figure
    changed."""
    assert closed_row("D2", "not_applicable", None, None, (), "Not applicable: no dividend paid (D1).") == (
        f":gray[:material/indeterminate_check_box:] **{name_of('D2')}.** :gray[Does not apply. Not applicable: no dividend paid "
        "(D1).]")


def test_an_open_check_shows_its_figures_with_units_and_fiscal_year_ac4():
    """Simon's AC3 sign-off figures in the open H3 check.

    Test change (rule 14.6, Simon's written agreement of 25 November 2026): the rows show E's names since #17, so the
    check is found by its name, looked up in texts.yaml (`name_of`), no longer by its id; no score, count or figure
    changed."""
    app = run_synthetic()
    h3 = next(e for e in app.expander if f"**{name_of('H3')}.**" in e.label)
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


def test_the_title_and_start_sentence_show_only_on_the_start_screen():
    """Design spec §3 and §6: "Filing Scorecard" and one sentence under the inputs, gone once a company is shown."""
    app = show("KO")
    assert not app.title
    assert "press Show scorecard" not in texts(app)


def test_the_ticker_field_takes_space_only_for_another_ticker():
    """Simon's look at the app, 23 November: no empty gap in the input bar.

    Label change (rule 14.6, Simon's written agreement of 25 November 2026): 4 and 5 columns, not 3 and 4, because
    the design puts the Show scorecard button in the same row (design spec §3, item 3)."""
    app = AppTest.from_file(MAIN).run(timeout=30)
    assert [t.label for t in app.text_input] == ["Share price (USD)"] and len(app.columns) == 4
    app.selectbox(key="company").set_value("Other ticker").run(timeout=30)
    assert [t.label for t in app.text_input] == ["Ticker", "Share price (USD)"] and len(app.columns) == 5


def heading(app: AppTest) -> str:
    """The page heading: the company name as a 28 px h1 in markdown (design spec §3, §4)."""
    return next(m.value for m in app.markdown if m.value.startswith("<h1"))


def test_coca_cola_header_shows_the_sec_name_ac1():
    """Label change (rule 14.6, Simon's written agreement of 25 November 2026): the name is looked for in the page
    heading, no longer in `st.header`, because the design shows it as the 28 px h1 with the ticker beside it
    (`st.header` is 18 px). The expected name and industry are unchanged; the SEC code stays until #27 (Igor, #39)."""
    app = show("KO")
    assert not app.exception
    assert ">COCA COLA CO<" in heading(app)
    assert "Beverages, SEC code 2080" in texts(app)


def test_the_header_shows_the_ticker_muted_and_the_typed_price():
    """Design spec §3: muted ticker beside the SEC name; the typed price on the right."""
    app = show("KO", "65.40")
    assert '<span class="fs-ticker">KO</span>' in heading(app)
    shown = texts(app)
    assert "Share price you typed" in shown and "USD 65.40" in shown
    assert "Share price you typed" not in texts(show("KO"))  # no price typed: nothing on the right


def test_header_shows_the_latest_fiscal_year_end_from_the_data():
    """Igor's review of #35: the date the checks use (Apple's fiscal 2026 ended on 26 September 2026), not the SEC's
    nominal year end (25 September)."""
    shown = texts(show("AAPL"))
    assert "Latest fiscal year ended 26 September 2026" in shown
    assert "25 September" not in shown


def test_a_check_not_assessed_shows_its_explanation_once():
    """Igor's review of #35: not "Not assessed: ..." and again "How it is calculated: ...".

    Test change (rule 14.6, Simon's written agreement of 25 November 2026): Igor's intent is kept, the explanation is
    shown once; only its place moves, from the open detail to the closed row, as in the design (SPEC 2.4.2 §3 item 5).
    So it is counted across the row and the open detail together, and must be in the row.

    Test change (rule 14.6, Simon's written agreement of 25 November 2026): the rows show E's names since #17, so the
    check is found by its name, looked up in texts.yaml (`name_of`), no longer by its id; no score, count or figure
    changed."""
    p4 = next(e for e in run_synthetic().expander if f"**{name_of('P4')}.**" in e.label)
    shown = [p4.label, *(m.value for m in p4.markdown)]
    assert sum("P4: built by hand (AC3)" in line for line in shown) == 1
    assert "P4: built by hand (AC3)" in p4.label


def test_apple_missing_interest_expense_is_n_a_with_its_reason_never_zero_v4():
    table = show("AAPL").dataframe[-1].value
    rows = table[table["Metric"] == "interest_expense"]
    missing = rows[rows["Kind"] == "missing"]
    assert len(missing) == 3  # fiscal 2024, 2025 and 2026
    for shown in missing["Value"]:
        assert shown.startswith("n/a: no annual 10-K value")


def test_a_check_names_its_filing_number_with_dashes_as_on_the_sources_page():
    """Simon's request, 23 November: e.g. 0000021344-26-000010, not 000002134426000010.

    Test change (rule 14.6, Simon's written agreement of 25 November 2026): the rows show E's names since #17, so the
    check is found by its name, looked up in texts.yaml (`name_of`), no longer by its id; no score, count or figure
    changed."""
    import re

    pytest.importorskip("src.checks.dividend", reason="needs C's dividend module (merged in #23)")
    app = show("KO")
    d1 = next(e for e in app.expander if f"**{name_of('D1')}.**" in e.label)
    filing = next(m.value for m in d1.markdown if m.value.startswith("**Filing:**"))
    accessions = set(app.dataframe[-1].value["Accession"]) - {""}
    shown = re.findall(r"\[([^\]]+)\]", filing)
    assert shown and all(re.fullmatch(r"\d{10}-\d{2}-\d{6}", a) and a in accessions for a in shown)


def test_a_failed_block_is_filled_in_the_text_colour_of_both_themes():
    """SPEC §3: a failed block is filled in a second colour, with a cross. Simon's look of 25 November: the fill was
    `currentColor`, which is the page colour inside a block whose text has the page colour, so D6 disappeared.

    Test change (rule 14.6, Simon's written agreement of 25 November 2026): the rows show E's names since #17, so the
    check is found by its name, looked up in texts.yaml (`name_of`), no longer by its id; no score, count or figure
    changed."""
    import re
    import tomllib

    from ui.scorecard import _style

    theme = tomllib.loads((Path(MAIN).parent / ".streamlit" / "config.toml").read_text(encoding="utf-8"))["theme"]
    css = _style()
    fills = re.findall(r"\.fs-fail \{\{?background:([^;}]+)", css)
    assert fills == ["var(--fs-text)"]  # one fill, named, never currentColor
    assert f"--fs-text:light-dark({theme['textColor']}, {theme['dark']['textColor']})" in css

    # Since item 5 the cross is the design's drawn cross (two paths), no longer the "✕" character.
    d6 = re.search(rf'<span class="([^"]*)" title="{re.escape(name_of('D6'))}[^"]*">(.*?)</span>', chart(show("KO")))
    assert "fs-fail" in d6.group(1).split() and CROSS in d6.group(2)


def test_the_check_row_icon_rule_targets_the_icon_streamlit_draws():
    """Simon's look of 25 November 2026: the icon sat higher than the text. Streamlit 1.67 draws a Material icon as
    `<span data-testid="stIconMaterial" aria-hidden="true">` (static/js/DynamicIcon), so the design spec's selector
    `span[role="img"]` matched nothing and the icon kept its default size and position."""
    from ui.scorecard import _style

    css = _style()
    assert '[data-testid="stExpander"] summary [data-testid="stIconMaterial"]' in css
    assert 'role="img"]' not in css


def test_a_typed_price_is_repeated_in_the_header():
    """Label change (rule 14.6, Simon's written agreement of 25 November 2026): the typed price is repeated in the
    header as "Share price you typed", no longer next to valuation (design spec §3). The price shown is unchanged."""
    shown = texts(show("KO", "182,50"))
    assert "Share price you typed" in shown and "USD 182.50" in shown
    assert "At the price you typed" not in shown


def test_an_invalid_price_says_how_to_type_it():
    app = show("KO", "1,234")
    assert [e.value for e in app.error] == ["Type the price in US dollars, e.g. 1234 or 182.50"]
