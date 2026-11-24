"""The sources page: one row per figure (SPEC §3 item 7, §5.1; acceptance AC5). Owner: D.

A missing figure shows its reason and the checks it blocks (the checks that list it as an input, SPEC §5.2).
Every warning other than the two customer warnings of the header is listed here (SPEC §10).
"""

from __future__ import annotations

from typing import Mapping, Sequence

import pandas as pd
import streamlit as st

from src.contracts import KINDS, CheckResult, CompanyData, Fact
from ui.format import fact_value

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


def source_rows(data: CompanyData, results: Mapping[str, Sequence[CheckResult] | None]) -> pd.DataFrame:
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
    return pd.DataFrame(rows, columns=list(COLUMNS))


def render_sources(data: CompanyData, results: Mapping[str, Sequence[CheckResult] | None]) -> None:
    st.subheader("Sources: every figure and where it comes from")
    kinds = st.multiselect("Kind of figure", KINDS, default=list(KINDS), key="sources_kinds")
    table = source_rows(data, results)
    st.dataframe(table[table["Kind"].isin(kinds)], hide_index=True, width="stretch")
    if data.warnings:
        st.markdown("**Notes from reading the filings**")
        for warning in data.warnings:
            st.markdown(f"- {warning}")
