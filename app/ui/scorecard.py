"""The scorecard page: header, score chart, checks (SPEC 2.4.1 §3; issue #32 points 3, 5, 7, 11). Owner: D.

Shows what it receives: `CompanyData`, the check results per area (`ui.results`) and the typed price. Scores come
from `src.scores`; numbers are written by `ui.format`. Nothing here computes, rounds or fills in a financial number.
Colours come from the theme file `app/.streamlit/config.toml`, never from this file.
"""

from __future__ import annotations

import html
from datetime import date, datetime
from pathlib import Path
from typing import Mapping, Sequence

import pandas as pd
import streamlit as st
import yaml

from src.contracts import CheckResult, CompanyData, Fact
from src.scores import area_score, dividend_note
from ui.format import check_value, fact_value
from ui.results import AREA_CHECKS, AREAS

TEXTS_FILE = Path(__file__).with_name("texts.yaml")  # E's plain-language texts (PR #17)
AREA_TITLES = {"past_performance": "Past performance", "financial_health": "Financial health",
               "dividend": "Dividend", "valuation": "Valuation"}
# The score label, written here only (issue #32 point 3; SPEC §3 wording to follow A's next SPEC pull request).
SCORE_LABEL = "{passed} passed of {assessed} assessed"
NOT_IN_THIS_VERSION = "Not assessed in this version"
VALUATION_V01 = "Not assessed until v0.2"
NOTHING_ASSESSED = "Insufficient data: none of these checks could be assessed (open each check for its reason)"
CHART_NOTE = "Each block is one yes/no test on the filings; not a rating of the share, not advice."
SYNTHETIC = "SYNTHETIC DATA"
# Look of each result: (mark, result word). Text and mark, never colour alone (issue #32 point 11).
LOOKS = {"pass": ("✓", "Passed"), "fail": ("✕", "Failed"), "insufficient_data": ("⋯", "Not assessed"),
         "not_applicable": ("–", "n/a")}


# --- texts ------------------------------------------------------------------------------------------------------


def load_texts(path: Path = TEXTS_FILE) -> dict:
    """E's texts per check id ({"P1": {"name": ..., "rule": ...}}), or {} until her file is merged."""
    if not path.exists():
        return {}
    return yaml.safe_load(path.read_text(encoding="utf-8")) or {}


def _name(check_id: str, texts: Mapping) -> str:
    name = texts.get(check_id, {}).get("name")
    return f"{check_id} {name}" if name else check_id


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
    # The name as the SEC lists it (SPEC 2.4.1 §3); the SEC code stays in the meta line until #27 (Igor, #39).
    company.markdown(f'<h1>{html.escape(data.name)}<span class="fs-ticker">{html.escape(data.ticker)}</span></h1>',
                     unsafe_allow_html=True)
    industry = f"{data.sic_description}, SEC code {data.sic}" if data.sic else "Industry n/a"
    company.caption(
        f"{industry} · Latest fiscal year ended {_latest_fiscal_year_end(data)} · "
        f"Latest annual report filed {_day(data.latest_10k_filed)} · Data retrieved {_day(data.retrieved)}"
    )
    if price is not None:
        typed.markdown(f'<div class="fs-price"><span class="fs-muted">Share price you typed</span><br>'
                       f'<strong>USD {price:,.2f}</strong></div>', unsafe_allow_html=True)
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
[data-testid="stExpander"] summary span[role="img"] {{font-size:20px; vertical-align:-4px}}
[data-testid="stTab"][aria-selected="true"], [data-testid="stTab"][aria-selected="true"] p {{color:var(--fs-text)}}
.fs-price {{text-align:right; font-size:14px}}  .fs-price strong {{font-size:16px}}
.fs-muted {{color:var(--fs-muted)}}  .fs-ticker {{font-size:16px; font-weight:400; color:var(--fs-muted); margin-left:8px}}
.fs-row {{display:flex; align-items:center; gap:16px; height:40px; border-bottom:1px solid var(--fs-line)}}
.fs-bar {{display:inline-flex; gap:4px}}
.fs-mk {{width:20px; height:20px; border-radius:4px; box-sizing:border-box; display:inline-grid; place-items:center}}
.fs-mk svg {{width:12px; height:12px; fill:none; stroke:var(--fs-page); stroke-width:2.5; stroke-linecap:round}}
.fs-pass {{background:var(--fs-accent)}}  .fs-fail {{background:var(--fs-text)}}
.fs-wait {{border:1.5px dashed var(--fs-muted)}}  .fs-none {{border:1px solid var(--fs-line)}}  .fs-none svg {{stroke:var(--fs-muted)}}
.stMarkdown table.fs-kv {{width:100%; border-collapse:collapse}}
.stMarkdown table.fs-kv td {{padding:8px 0; border:0; border-bottom:1px solid var(--fs-line)}}
.stMarkdown table.fs-kv td:last-child {{text-align:right}}
/* Until item 5: the old six-block bar, in the new colours */
.fs-area {{width:9.5rem; font-weight:600}}  .fs-blocks {{display:flex; gap:4px}}
.fs-block {{min-width:6.2rem; min-height:40px; padding:4px 8px; border-radius:4px; font-size:12px; line-height:16px;
  white-space:nowrap; text-align:center; flex-direction:column;
  display:flex; align-items:center; justify-content:center; box-sizing:border-box}}
.fs-block.fs-pass {{color:var(--fs-page)}}  .fs-block.fs-fail {{color:var(--fs-page)}}
.fs-insufficient_data, .fs-empty {{border:1.5px dashed var(--fs-muted)}}  .fs-not_applicable {{border:1px solid var(--fs-line)}}
</style>"""


def _block(check_id: str, status: str | None, reason: str = "") -> str:
    if status is None:  # area not assessed in this version
        return f'<div class="fs-block fs-empty" title="{check_id}: not assessed">{check_id}<br>not assessed</div>'
    mark, word = LOOKS[status]
    title = html.escape(f"{check_id}: {word}" + (f": {reason}" if status in ("insufficient_data", "not_applicable")
                                                 else ""), quote=True)
    return f'<div class="fs-block fs-{status}" title="{title}">{mark} {check_id}<br>{word.lower()}</div>'


def _label(area: str, results: Sequence[CheckResult] | None) -> str:
    if results is None:
        return VALUATION_V01 if area == "valuation" else NOT_IN_THIS_VERSION
    score = area_score(results)
    if score.assessed == 0:
        return NOTHING_ASSESSED
    label = SCORE_LABEL.format(passed=score.passed, assessed=score.assessed)
    note = dividend_note(results) if area == "dividend" else None
    return f"{note[0].upper()}{note[1:]} · {label}" if note else label


def render_score_chart(results: Mapping[str, Sequence[CheckResult] | None], price: float | None) -> None:
    rows = [_style()]
    for area in AREAS:
        area_results = results.get(area)
        if area_results is None:
            blocks = "".join(_block(cid, None) for cid in AREA_CHECKS[area])
        else:
            blocks = "".join(_block(r.check_id, r.status, r.explanation) for r in area_results)
        label = html.escape(_label(area, area_results))
        if area == "valuation" and price is not None:
            label += f" · At the price you typed: USD {price:,.2f}"
        rows.append(f'<div class="fs-row"><div class="fs-area">{AREA_TITLES[area]}</div>'
                    f'<div class="fs-blocks">{blocks}</div><div class="fs-label">{label}</div></div>')
    st.markdown("\n".join(rows), unsafe_allow_html=True)
    st.caption(CHART_NOTE)


# --- checks -----------------------------------------------------------------------------------------------------


def filing_link(data: CompanyData, fact: Fact) -> str | None:
    """Address of the SEC filing a reported figure comes from, or None (synthetic, derived, missing)."""
    if fact.form in (None, "SYNTHETIC") or not fact.accession or not data.cik.strip("0"):
        return None
    return f"https://www.sec.gov/Archives/edgar/data/{int(data.cik)}/{fact.accession.replace('-', '')}/"


def _period(fact: Fact) -> str:
    return f"fiscal year ended {_day(fact.period_end)}"


def render_check(data: CompanyData, result: CheckResult, texts: Mapping) -> None:
    mark, word = LOOKS[result.status]
    with st.expander(f"{mark} {word} · {_name(result.check_id, texts)}"):
        rule = texts.get(result.check_id, {}).get("rule")
        not_assessed = result.status in ("insufficient_data", "not_applicable")
        if not_assessed:  # its explanation is the reason, shown once (Igor's review of #35)
            st.markdown(f"**{word}:** {result.explanation}")
        if rule:
            st.markdown(f"**Rule:** {rule}")
        if not not_assessed:
            st.markdown(f"**How it is calculated:** {result.explanation}")
        if result.value is not None or result.threshold is not None:
            shown, against = check_value(result.check_id, result.value, result.threshold)
            st.markdown(f"**Value:** {shown}" + (f" · **compared with:** {against}" if against else ""))
        if result.inputs:
            st.table(pd.DataFrame([{"Figure": f.metric, "Period": _period(f), "Value": fact_value(f), "Kind": f.kind}
                                   for f in result.inputs]))
            # Filing number with its dashes, as on the sources page (e.g. 0000063908-26-000035)
            links = sorted({(f.accession, link) for f in result.inputs if (link := filing_link(data, f))})
            if links:
                st.markdown("**Filing:** " + " · ".join(f"[{accession}]({link})" for accession, link in links))
            elif is_synthetic(data):
                st.markdown(f"**Filing:** none ({SYNTHETIC})")


def render_checks(data: CompanyData, results: Mapping[str, Sequence[CheckResult] | None]) -> None:
    texts = load_texts()
    for area in AREAS:
        area_results = results.get(area)
        if not area_results:
            continue
        st.subheader(AREA_TITLES[area])
        for result in area_results:
            render_check(data, result, texts)


def render_scorecard(data: CompanyData, results: Mapping[str, Sequence[CheckResult] | None],
                     price: float | None, warnings: Sequence[str] = ()) -> None:
    render_header(data, warnings, price)
    render_score_chart(results, price)
    render_checks(data, results)
