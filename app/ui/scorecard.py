"""The scorecard page: header, score chart, checks (SPEC 2.4.1 §3; issue #32 points 3, 5, 7, 11). Owner: D.

Shows what it receives: `CompanyData`, the check results per area (`ui.results`) and the typed price. Scores come
from `src.scores`; numbers are written by `ui.format`. Nothing here computes, rounds or fills in a financial number.
Colours come from the theme file `app/.streamlit/config.toml`, never from this file.
"""

from __future__ import annotations

import html
import re
from datetime import date, datetime
from pathlib import Path
from typing import Mapping, Sequence

import pandas as pd
import streamlit as st
import yaml

from src.contracts import CheckResult, CompanyData, Fact
from src.scores import area_score, dividend_note, not_assessed
from ui.format import check_value, fact_value, share_price
from ui.results import AREA_CHECKS, AREAS, Market
from ui.valuation import LABELS, NOT_FROM_A_FILING, benchmark_value, render_detail, render_estimate

TEXTS_FILE = Path(__file__).with_name("texts.yaml")  # E's plain-language texts (PR #17)
AREA_TITLES = {"past_performance": "Past performance", "financial_health": "Financial health",
               "dividend": "Dividend", "valuation": "Valuation"}
# The score label, written here only (issue #32 point 3; SPEC §3 wording to follow A's next SPEC pull request).
SCORE_LABEL = "{passed} passed of {assessed} assessed"
NOT_IN_THIS_VERSION = "Not part of this version"  # valuation in v0.1 (design spec §6)
NOT_ASSESSED = "Not assessed"  # an area whose module is not merged yet, or with nothing assessed (Simon, 25 Nov)
NOTHING_ASSESSED = "open each check for its reason"
CHART_NOTE = ("Each mark is one check of the company's annual reports. It is not a rating of the share and not "
              "advice.")  # one name per thing (design spec §5 rule 5; Emma's review of #54)
FAILED_TITLE = "Failed checks"
SOURCES_TAB = "Sources"
NO_FAILED = "No check failed."
SYNTHETIC = "SYNTHETIC DATA"
# The four looks of a mark (SPEC 2.4.2 §3): CSS class, word, and the glyph drawn on it (docs/design/mockup.html).
MARK_CLASSES = {"pass": "pass", "fail": "fail", "insufficient_data": "wait", "not_applicable": "none"}
MARK_WORDS = {"pass": "Passed", "fail": "Failed", "insufficient_data": "Not assessed",
              "not_applicable": "Does not apply"}
# Words in a check's explanation that already say the result word (Igor's review of #54, point 3: C's "Not applicable")
SAME_AS = {"Does not apply": ("not applicable",)}
_SVG = '<svg viewBox="0 0 12 12" aria-hidden="true"><path d="{}"/></svg>'
GLYPHS = {"pass": _SVG.format("M2.5 6.3 5 8.6 9.5 3.6"), "fail": _SVG.format("M3.2 3.2l5.6 5.6M8.8 3.2 3.2 8.8"),
          "not_applicable": _SVG.format("M3.5 6h5")}
# Icon of each result in a check row (design spec §4): shape and word, never colour alone (issue #32 point 11). No
# box, so a row does not look like a form checkbox (Igor's review of #54, point 4; icons chosen by Simon).
ICONS = {"pass": ":primary[:material/check:]", "fail": ":material/close:",
         "insufficient_data": ":gray[:material/more_horiz:]", "not_applicable": ":gray[:material/remove:]"}
_MARKDOWN = str.maketrans({c: "\\" + c for c in "\\*_[]$`~"})  # a check's text shown as written, not as markdown


# --- texts ------------------------------------------------------------------------------------------------------


def load_texts(path: Path = TEXTS_FILE) -> dict:
    """E's texts per check id ({"P1": {"name": ..., "rule": ...}}), or {} until her file is merged."""
    if not path.exists():
        return {}
    return yaml.safe_load(path.read_text(encoding="utf-8")) or {}


def _plain_name(check_id: str, texts: Mapping) -> str:
    """E's name of a check, or its id until her texts (#17) are merged."""
    return texts.get(check_id, {}).get("name") or check_id


# --- header -----------------------------------------------------------------------------------------------------


def _day(value: date | datetime | None) -> str:
    if value is None:
        return "n/a"
    shown = f"{value.day} {value:%B %Y}"
    return f"{shown}, {value:%H:%M} UTC" if isinstance(value, datetime) else shown


def _latest_fiscal_year_end(data: CompanyData) -> str:
    """The latest fiscal year end in the data, the date the checks use (Igor's review of #35); not the SEC's
    nominal year end, which is a week off for 52/53-week years (Apple, Nvidia)."""
    years = data.fiscal_years("revenue")
    return _day(years[-1]) if years else "n/a"


def is_synthetic(data: CompanyData) -> bool:
    return SYNTHETIC in data.name or any(w.startswith(SYNTHETIC) for w in data.warnings)


def render_header(data: CompanyData, warnings: Sequence[str] = (), price: float | None = None) -> None:
    """SEC name with the muted ticker, one meta line, the typed price on the right (design spec §3)."""
    if is_synthetic(data):
        st.warning(f"{SYNTHETIC}: an invented company for tests (SPEC Appendix A), not a real company.")
    company, typed = st.columns([4, 1], vertical_alignment="bottom")
    # The name as the SEC lists it (SPEC 2.4.1 §3); the SEC code stays in the meta line until #27 (Igor, #39), named
    # "SEC industry" so it is not confused with the industry group under the valuation detail (Emma's review of #54).
    company.markdown(f'<h1>{html.escape(data.name)}<span class="fs-ticker">{html.escape(data.ticker)}</span></h1>',
                     unsafe_allow_html=True)
    industry = f"SEC industry: {data.sic_description} (code {data.sic})" if data.sic else "SEC industry: n/a"
    company.caption(
        f"{industry} · Latest fiscal year ended {_latest_fiscal_year_end(data)} · "
        f"Latest annual report filed {_day(data.latest_10k_filed)} · Data retrieved {_day(data.retrieved)}"
    )
    if price is not None:
        typed.markdown(f'<div class="fs-price"><span class="fs-muted">Share price you typed</span><br>'
                       f'<strong>{share_price(price)}</strong></div>', unsafe_allow_html=True)
    for warning in warnings:  # only "not fully checked" and "latest annual report is old" (SPEC §10, src/gates.py)
        st.warning(warning)


# --- score chart ------------------------------------------------------------------------------------------------


def _theme(key: str) -> str:
    """A theme colour as CSS: light-dark(light, dark), so it follows the active theme (design spec §4). Without a
    theme file (tests) the browser's own text colour."""
    light = st.get_option(f"theme.{key}") or "currentColor"
    dark = st.get_option(f"theme.dark.{key}") or light
    return f"light-dark({light}, {dark})"


def _style() -> str:
    """The one CSS block of the page (design spec §4). Colours come from the theme file, never from here."""
    return f"""<style>
.stApp {{--fs-accent:{_theme('primaryColor')}; --fs-page:{_theme('backgroundColor')}; --fs-text:{_theme('textColor')};
  --fs-muted:color-mix(in srgb, currentColor 68%, transparent); --fs-line:color-mix(in srgb, currentColor 20%, transparent);
  font-variant-numeric:tabular-nums}}
[data-testid="stMainBlockContainer"] {{max-width:1200px; padding-left:32px; padding-right:32px}}
[data-testid="stExpander"] details {{border:0; border-bottom:1px solid var(--fs-line); border-radius:0}}
[data-testid="stExpander"] summary [data-testid="stIconMaterial"] {{font-size:20px; line-height:24px; vertical-align:-5px}}
[data-testid="stTab"][aria-selected="true"], [data-testid="stTab"][aria-selected="true"] p {{color:var(--fs-text)}}
.fs-price {{text-align:right; font-size:14px}}  .fs-price strong {{font-size:16px}}
h1:has(.fs-ticker) [data-testid="stHeaderActionElements"] {{display:none}}
.fs-muted {{color:var(--fs-muted)}}  .fs-ticker {{font-size:16px; font-weight:400; color:var(--fs-muted); margin-left:8px}}
.fs-row {{display:flex; align-items:center; gap:16px; min-height:40px; box-sizing:border-box; padding:6px 0;
  border-bottom:1px solid var(--fs-line)}}
.fs-label {{display:flex; flex-wrap:wrap; align-items:baseline; column-gap:16px; flex:1; min-width:0; line-height:20px}}
.fs-bar {{display:inline-flex; gap:4px}}
.fs-mk {{width:20px; height:20px; border-radius:4px; box-sizing:border-box; display:inline-grid; place-items:center}}
.fs-mk svg {{width:12px; height:12px; fill:none; stroke:var(--fs-page); stroke-width:2.5; stroke-linecap:round}}
.fs-pass {{background:var(--fs-accent)}}  .fs-fail {{background:var(--fs-text)}}
.fs-wait {{border:1.5px dashed var(--fs-muted)}}  .fs-none {{border:1px solid var(--fs-line)}}  .fs-none svg {{stroke:var(--fs-muted)}}
.stMarkdown table.fs-kv {{width:100%; border-collapse:collapse}}
.stMarkdown table.fs-kv td {{padding:8px 0; border:0; border-bottom:1px solid var(--fs-line)}}
.stMarkdown table.fs-kv td:last-child {{text-align:right}}
.fs-row:first-of-type {{border-top:1px solid var(--fs-line)}}
.fs-area {{width:160px; flex:none; font-weight:600}}  .fs-score {{font-weight:600}}
.fs-sub {{color:var(--fs-muted); font-size:14px}}  .fs-mk {{flex:none}}
.fs-legend {{display:flex; align-items:center; flex-wrap:wrap; gap:8px 16px; margin-top:12px; font-size:14px;
  line-height:20px; color:var(--fs-muted)}}
.fs-key {{display:inline-flex; align-items:center; gap:8px}}
ul.fs-failed {{list-style:none; margin:0; padding:0; max-width:100%}}
ul.fs-failed li {{display:grid; grid-template-columns:20px minmax(0, 1fr) auto; align-items:center; column-gap:12px;
  min-height:40px; box-sizing:border-box; padding:6px 0; margin:0; line-height:20px; overflow-wrap:anywhere;  /* as .fs-row */
  border-bottom:1px solid var(--fs-line)}}
ul.fs-failed li:not(:has(.fs-mk)) {{display:block; padding-top:10px}}
ul.fs-failed li.fs-hd {{border-top:1px solid var(--fs-line); font-weight:600}}
ul.fs-failed li .fs-sub {{white-space:nowrap; text-align:right}}
</style>"""


def _word_before(word: str, explanation: str) -> str:
    """"Not assessed. " before the explanation, or "" when its first clause already says the word (Simon, 25 November
    2026: not "Not assessed. This check is not assessed yet: ..."); used by the row and the mark alike."""
    first_clause = re.split(r"[:.]", explanation, maxsplit=1)[0].lower()
    said = (word.lower(), *SAME_AS.get(word, ()))
    return "" if any(words in first_clause for words in said) else f"{word}. "


def _block(status: str | None, title: str = "") -> str:
    """One 20 px mark: shape and fill differ per look, so colour is never alone (design spec §4). `None`: dashed."""
    look = MARK_CLASSES[status or "insufficient_data"]
    glyph = GLYPHS.get(status or "", "")
    tip = f' title="{html.escape(title, quote=True)}"' if title else ""
    return f'<span class="fs-mk fs-{look}"{tip}>{glyph}</span>'


def _label(area: str, results: Sequence[CheckResult] | None) -> tuple[str, str]:
    """The row's score and its muted note: ("4 passed of 5 assessed", "1 not assessed yet")."""
    if results is None:
        return "", NOT_IN_THIS_VERSION if area == "valuation" else NOT_ASSESSED
    score = area_score(results)
    if score.assessed == 0:
        return NOT_ASSESSED, NOTHING_ASSESSED
    label = SCORE_LABEL.format(passed=score.passed, assessed=score.assessed)
    note = dividend_note(results) if area == "dividend" else None
    if note:  # "No dividend paid", then the score muted (SPEC §3)
        return f"{note[0].upper()}{note[1:]}", label
    waiting = not_assessed(results)
    if not waiting.count:
        return label, ""
    return label, f"{waiting.count} not assessed" + (" yet" if waiting.yet else "")


def _legend() -> str:
    keys = "".join(f'<span class="fs-key">{_block(status)}{word}</span>' for status, word in MARK_WORDS.items())
    return f'<div class="fs-legend">{keys}<span>{CHART_NOTE}</span></div>'


def _failed_list(results: Mapping[str, Sequence[CheckResult] | None], texts: Mapping) -> str:
    """The failed checks with their area, next to the chart until tier 3 (SPEC §3 item 4)."""
    rows = [f'<li>{_block("fail")}{html.escape(_plain_name(r.check_id, texts))}'
            f'<span class="fs-sub">{AREA_TITLES[area]}</span></li>'
            for area in AREAS for r in (results.get(area) or ()) if r.status == "fail"]
    return f'<ul class="fs-failed"><li class="fs-hd">{FAILED_TITLE}</li>{"".join(rows) or f"<li>{NO_FAILED}</li>"}</ul>'


def render_score_chart(results: Mapping[str, Sequence[CheckResult] | None]) -> None:
    """One row of six marks per area, the legend, and the failed checks on the right (design spec §3)."""
    texts = load_texts()
    rows = []
    for area in AREAS:
        area_results = results.get(area)
        if area_results is None:
            marks = "".join(_block(None) for _ in AREA_CHECKS[area])
        else:
            marks = "".join(_block(r.status, f"{_plain_name(r.check_id, texts)}: "
                                   + (f"{_word_before(MARK_WORDS[r.status], r.explanation)}{r.explanation}"
                                      if r.status in ("insufficient_data", "not_applicable")
                                      else MARK_WORDS[r.status]))
                            for r in area_results)
        score, sub = _label(area, area_results)
        said = ", ".join(part for part in (score, sub) if part)  # "Dividend: no dividend paid, 0 passed of 1 assessed"
        aria = html.escape(f"{AREA_TITLES[area]}: {said[:1].lower()}{said[1:]}", quote=True)
        rows.append(f'<div class="fs-row"><span class="fs-area">{AREA_TITLES[area]}</span>'
                    f'<span class="fs-bar" role="img" aria-label="{aria}">{marks}</span>'
                    f'<span class="fs-label"><span class="fs-score">{html.escape(score)}</span>'
                    f'<span class="fs-sub">{html.escape(sub)}</span></span></div>')
    chart, failed = st.columns([2, 1], gap="large")
    chart.markdown(_style() + "".join(rows) + _legend(), unsafe_allow_html=True)
    failed.markdown(_failed_list(results, texts), unsafe_allow_html=True)


# --- checks -----------------------------------------------------------------------------------------------------


SEC_ACCESSION = re.compile(r"\d{10}-\d{2}-\d{6}")


def filing_link(data: CompanyData, fact: Fact) -> str | None:
    """Address of the SEC filing a reported figure comes from, or None (synthetic, derived, missing)."""
    # Only a real SEC accession number (0000021344-26-000010): never a benchmark's "Damodaran:..." source or the
    # risk-free rate (Igor's review of #63, point 1)
    if fact.form in (None, "SYNTHETIC") or not SEC_ACCESSION.fullmatch(fact.accession or "") or not data.cik.strip("0"):
        return None
    return f"https://www.sec.gov/Archives/edgar/data/{int(data.cik)}/{fact.accession.replace('-', '')}/"


def _period(fact: Fact) -> str:
    """A company figure's fiscal year; a benchmark or the risk-free rate is dated, not a fiscal year (Igor, #63)."""
    if fact.metric in NOT_FROM_A_FILING:
        return f"as of {_day(fact.period_end)}"
    return f"fiscal year ended {_day(fact.period_end)}"


def _input_value(fact: Fact) -> str:
    return benchmark_value(fact) if fact.metric in NOT_FROM_A_FILING else fact_value(fact)


def render_check(data: CompanyData, result: CheckResult, texts: Mapping) -> None:
    """A closed check shows its icon, its name and one sentence (SPEC 2.4.2 §3 item 5). Until E's texts (#17): the
    result and the figures, "Passed. USD 31,044 m against USD 21,281 m."; not assessed or does not apply: the word
    and the check's own explanation, unchanged."""
    word = MARK_WORDS[result.status]
    # The row shows the explanation when the check is not assessed, does not apply, uses an assumed figure or has no
    # value; the open detail then does not repeat it (Igor's review of #35: once; Simon, 25 November 2026)
    assumed = any(f.kind == "assumption" for f in result.inputs)  # e.g. dividends treated as nil: never "USD 0 m"
    no_value = result.value is None  # e.g. McDonald's negative equity: "Failed." alone says nothing (Igor, #54)
    in_row = result.status not in ("pass", "fail") or assumed or no_value
    if result.status in ("pass", "fail") and in_row:
        # A figure is an assumption (e.g. dividends treated as nil) or there is no value: the check's own words,
        # never "USD 0 m" (Flo's rule, plan Q1; Simon's look of 25 November 2026; Igor's review of #54, point 2)
        sentence = f"{word}. {result.explanation.translate(_MARKDOWN)}"
    elif result.status in ("pass", "fail"):
        shown, against = check_value(result.check_id, result.value, result.threshold)
        sentence = f"{word}. {shown}" + (f" against {against}" if against else "") + "."
    else:  # the word only when the explanation's first clause does not already say it (Simon, 25 November 2026)
        sentence = f":gray[{_word_before(word, result.explanation)}{result.explanation.translate(_MARKDOWN)}]"
    with st.expander(f"{ICONS[result.status]} **{_plain_name(result.check_id, texts)}.** {sentence}"):
        rule = texts.get(result.check_id, {}).get("rule")
        if rule:
            st.markdown(f"**Rule:** {rule}")
        if not in_row:
            st.markdown(f"**How it is calculated:** {result.explanation}")
        if (result.value is not None or result.threshold is not None) and not assumed:  # the table says it
            shown, against = check_value(result.check_id, result.value, result.threshold)
            st.markdown(f"**Value:** {shown}" + (f" · **compared with:** {against}" if against else ""))
        if result.inputs:
            st.table(pd.DataFrame([{"Figure": LABELS.get(f.metric, f.metric), "Period": _period(f), "Value": _input_value(f), "Kind": f.kind}
                                   for f in result.inputs]))
            # Filing number with its dashes, as on the sources page (e.g. 0000063908-26-000035)
            links = sorted({(f.accession, link) for f in result.inputs if (link := filing_link(data, f))})
            if links:
                st.markdown("**Filing:** " + " · ".join(f"[{accession}]({link})" for accession, link in links))
            elif is_synthetic(data):
                st.markdown(f"**Filing:** none ({SYNTHETIC})")


def render_checks(data: CompanyData, results: Mapping[str, Sequence[CheckResult] | None],
                  market: Market | None = None):
    """One tab per area, the Sources tab last (SPEC 2.4.2 §3 item 5); returns the Sources tab for `main.py`. With
    `market` (S10b) the Valuation tab starts with the estimate and ends with the valuation detail (SPEC §3 item 6)."""
    texts = load_texts()
    *area_tabs, sources_tab = st.tabs([*(AREA_TITLES[area] for area in AREAS), SOURCES_TAB])
    for area, tab in zip(AREAS, area_tabs):
        area_results = results.get(area)
        with tab:
            detail = area == "valuation" and market is not None
            if detail:
                render_estimate(market)
            if not area_results:  # no module yet: the same words as its row in the chart
                st.markdown(f'<span class="fs-sub">{_label(area, area_results)[1]}</span>', unsafe_allow_html=True)
                continue
            for result in area_results:
                render_check(data, result, texts)
            if detail:
                render_detail(market, texts)
    return sources_tab


def render_scorecard(data: CompanyData, results: Mapping[str, Sequence[CheckResult] | None],
                     price: float | None, warnings: Sequence[str] = (), market: Market | None = None,
                     overview=None):
    """Header, the overview (`overview(data, results)`, A's `ui.overview.render_overview`, S10c), score chart, then
    the tabs; returns the Sources tab, which `main.py` fills with `render_sources`."""
    render_header(data, warnings, price)
    if overview is not None:
        overview(data, results)
    render_score_chart(results)
    return render_checks(data, results, market)
