"""The sources page: one row per figure (SPEC §3 item 7, §5.1; acceptance AC5). Owner: D.

A missing figure shows its reason and the checks it blocks (the checks that list it as an input, SPEC §5.2).
Every warning other than the two customer warnings of the header is listed here (SPEC §10). The share price the
user typed is one "assumption" row (SPEC §5.2; S10b), and C's valuation records (BETA_LIMIT, GROWTH_LIMIT, ...) are
listed with the notes (SPEC §8.6, §10).
"""

from __future__ import annotations

from typing import Mapping, Sequence

import pandas as pd
import streamlit as st

from src.contracts import KINDS, CheckResult, CompanyData, Fact
from ui.format import fact_value, share_price

COLUMNS = ("Metric", "Value", "Unit", "Period", "Kind", "Tag", "Form", "Accession", "Filed", "Retrieved", "Note",
           "Blocks checks")


def _blocks(fact: Fact, results: Mapping[str, Sequence[CheckResult] | None]) -> str:
    if fact.kind != "missing":
        return ""
    ids = [r.check_id for area in results.values() for r in (area or ())
           if any(i.metric == fact.metric and i.period_end == fact.period_end for i in r.inputs)]
    return ", ".join(ids)


def _period(fact: Fact) -> str:
    end = fact.period_end.isoformat()
    return f"{fact.period_start.isoformat()} to {end}" if fact.period_start else f"at {end}"


PRICE_NOTE = "The share price you typed, in US dollars: an assumption, not from a filing (SPEC §5.2)."


def _price_row(price: float) -> dict:
    return {"Metric": "share_price", "Value": share_price(price), "Unit": "USD/shares", "Period": "typed on screen",
            "Kind": "assumption", "Tag": "", "Form": "", "Accession": "", "Filed": "", "Retrieved": "",
            "Note": PRICE_NOTE, "Blocks checks": ""}


def source_rows(data: CompanyData, results: Mapping[str, Sequence[CheckResult] | None],
                price: float | None = None) -> pd.DataFrame:
    rows = [
        {
            "Metric": fact.metric, "Value": fact_value(fact), "Unit": fact.unit, "Period": _period(fact),
            "Kind": fact.kind, "Tag": fact.tag or "", "Form": fact.form or "", "Accession": fact.accession or "",
            "Filed": fact.filed.isoformat() if fact.filed else "",
            "Retrieved": fact.retrieved.isoformat(timespec="minutes") if fact.retrieved else "",
            "Note": fact.note, "Blocks checks": _blocks(fact, results),
        }
        for metric in sorted(data.items) for _, fact in sorted(data.items[metric].items())
    ]
    if price is not None:
        rows.append(_price_row(price))
    return pd.DataFrame(rows, columns=list(COLUMNS))


def render_sources(data: CompanyData, results: Mapping[str, Sequence[CheckResult] | None],
                   price: float | None = None, records: Sequence[str] = ()) -> None:
    st.subheader("Sources: every figure and where it comes from")
    kinds = st.multiselect("Kind of figure", KINDS, default=list(KINDS), key="sources_kinds")
    table = source_rows(data, results, price)
    st.dataframe(table[table["Kind"].isin(kinds)], hide_index=True, width="stretch")
    if data.warnings:
        st.markdown("**Notes from reading the filings**")
        for warning in data.warnings:
            st.markdown(f"- {warning}")
    if records:  # C's valuation records, never in the header (SPEC §10)
        st.markdown("**Notes from the valuation**")
        for record in records:
            st.markdown(f"- {record}")
