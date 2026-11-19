"""Streamlit entry point: `streamlit run main.py` from the `app/` folder.

Walking skeleton written by A in slice S0. Owner from slice S10 on: D (interface). The interface only shows values
it receives from `src/`; it never computes financial numbers (SPEC §11, layering rule).
"""

import streamlit as st

st.set_page_config(page_title="Filing Scorecard", layout="wide")

st.title("Filing Scorecard")
st.caption(
    "Working title. A one-page, fully sourced scorecard of a US company, built only from SEC filings and free data."
)
st.info("Walking skeleton: the scorecard arrives with release v0.1 (see docs/plan.md).")
