"""The scorecard page: header, score chart, checks (SPEC 2.4.1 §3; issue #32 points 3, 5, 7, 11). Owner: D.

Shows what it receives: `CompanyData`, the check results per area (`ui.results`) and the typed price. Scores come
from `src.scores`; numbers are written by `ui.format`. Nothing here computes, rounds or fills in a financial number.
Colours come from the theme file `app/.streamlit/config.toml`, never from this file.
"""

from __future__ import annotations

import calendar
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


def _fiscal_year_end(mmdd: str | None) -> str:
    if not mmdd or len(mmdd) != 4 or not mmdd.isdigit():
        return "n/a"
    return f"{int(mmdd[2:])} {calendar.month_name[int(mmdd[:2])]}"


def is_synthetic(data: CompanyData) -> bool:
    return SYNTHETIC in data.name or any(w.startswith(SYNTHETIC) for w in data.warnings)


def render_header(data: CompanyData) -> None:
    if is_synthetic(data):
        st.warning(f"{SYNTHETIC}: an invented company for tests (SPEC Appendix A), not a real company.")
    st.header(data.name)  # as the SEC lists it (SPEC 2.4.1 §3)
    industry = f"{data.sic_description}, SEC code {data.sic}" if data.sic else "n/a"
    st.caption(
        f"Industry: {industry} · Fiscal year ends: {_fiscal_year_end(data.fiscal_year_end)} · "
        f"Latest annual report (10-K): {_day(data.latest_10k_filed)} · Data retrieved: {_day(data.retrieved)}"
    )
    st.container()  # place of the two customer warnings ("not fully checked", "latest annual report is old"): S11


# --- score chart ------------------------------------------------------------------------------------------------


def _colours() -> dict[str, str]:
    """Theme colours from config.toml; without a theme (tests) the browser's own colours."""
    def option(name: str, fallback: str) -> str:
        try:
            return st.get_option(f"theme.{name}") or fallback
        except Exception:  # an unknown option name in another Streamlit version
            return fallback
    return {"accent": option("primaryColor", "currentColor"), "text": option("textColor", "currentColor"),
            "page": option("backgroundColor", "Canvas"), "soft": option("secondaryBackgroundColor", "transparent")}


def _style() -> str:
    c = _colours()
    return f"""<style>
.fs-row {{display:flex; align-items:center; gap:.75rem; margin:.35rem 0; flex-wrap:wrap}}
.fs-area {{width:9.5rem; font-weight:600}}
.fs-blocks {{display:flex; gap:.25rem}}
.fs-block {{min-width:6.2rem; min-height:2.8rem; padding:.3rem .5rem; border-radius:.3rem; font-size:.75rem;
  line-height:1.2; white-space:nowrap; text-align:center; display:flex; flex-direction:column;
  align-items:center; justify-content:center; box-sizing:border-box}}
.fs-pass {{background:{c['accent']}; color:{c['page']}}}
.fs-fail {{background:{c['text']}; color:{c['page']}}}
.fs-insufficient_data, .fs-empty {{border:2px dashed {c['text']}; color:{c['text']}}}
.fs-not_applicable {{border:1px solid {c['soft']}; background:{c['page']}; color:{c['text']}}}
.fs-label {{font-size:.9rem}}
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
        if result.status in ("insufficient_data", "not_applicable"):
            st.markdown(f"**{word}:** {result.explanation}")
        if rule:
            st.markdown(f"**Rule:** {rule}")
        st.markdown(f"**How it is calculated:** {result.explanation}")
        if result.value is not None or result.threshold is not None:
            shown, against = check_value(result.check_id, result.value, result.threshold)
            st.markdown(f"**Value:** {shown}" + (f" · **compared with:** {against}" if against else ""))
        if result.inputs:
            st.table(pd.DataFrame([{"Figure": f.metric, "Period": _period(f), "Value": fact_value(f), "Kind": f.kind}
                                   for f in result.inputs]))
            links = sorted({link for f in result.inputs if (link := filing_link(data, f))})
            if links:
                st.markdown("**Filing:** " + " · ".join(f"[{link.rsplit('/', 2)[-2]}]({link})" for link in links))
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
                     price: float | None) -> None:
    render_header(data)
    render_score_chart(results, price)
    render_checks(data, results)
