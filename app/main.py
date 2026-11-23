"""Streamlit entry point: `streamlit run main.py` from the `app/` folder. Owner: D (slice S10).

Input bar, start screen, then the scorecard and sources pages. The interface only shows values it receives from
`src/`; it never computes financial numbers (SPEC §11). The data-quality gates (`src/gates.py`, S11) decide
whether a report is shown; every message for the customer comes from `ui/messages.py`.
"""

import streamlit as st

from src.data.company import DEMO_TICKERS, SecError, load_company
from src.gates import check_gates
from src.settings import load_settings
from ui.inputs import PriceError, parse_price
from ui.messages import TECHNICAL_DETAILS, header_warnings, sec_error_message, stop_message
from ui.results import check_results
from ui.scorecard import render_scorecard
from ui.sources import render_sources

OTHER = "Other ticker"

st.set_page_config(page_title="Filing Scorecard", layout="wide")
st.title("Filing Scorecard")


@st.cache_data(show_spinner=False)
def company(ticker: str, demo: bool):
    return load_company(ticker, demo=demo)


# --- input bar (SPEC 2.4.1 §3 item 1) ---------------------------------------------------------------------------
# The Ticker field takes a column only when "Other ticker" is chosen (no empty gap otherwise).
other = st.session_state.get("company") == OTHER
pick, *typed, price_box, demo_box = st.columns(4 if other else 3)
choice = pick.selectbox("Company", [*DEMO_TICKERS, OTHER], key="company")
ticker = typed[0].text_input("Ticker", key="ticker", placeholder="e.g. MSFT") if typed else choice
if choice == OTHER and not typed:  # first run after switching: the column appears on the next rerun
    st.rerun()
price_text = price_box.text_input("Share price (USD)", key="price", placeholder="e.g. 182.50")
demo = demo_box.toggle("Demo mode (saved data, no network)", value=True, key="demo")
if st.button("Show scorecard", type="primary", key="show"):
    st.session_state["request"] = (ticker.strip().upper(), price_text, demo)

request = st.session_state.get("request")
if request is None:
    st.info(
        f"Pick one of the five demo companies ({', '.join(DEMO_TICKERS)}) or choose \"{OTHER}\" and type a US "
        "ticker. Type the share price in US dollars if you have it, then click **Show scorecard**."
    )
    st.stop()

ticker, price_text, demo = request
try:
    price = parse_price(price_text)
except PriceError as error:
    st.error(str(error))
    st.stop()

try:
    with st.spinner("Reading the saved SEC data…" if demo else "Fetching SEC filings…"):
        data = company(ticker, demo)
except SecError as error:
    st.error(sec_error_message(error, ticker, demo))
    with st.expander(TECHNICAL_DETAILS, expanded=False):
        st.code(str(error), language=None)
    st.stop()

# --- data-quality gates (SPEC 2.4.1 §10) -------------------------------------------------------------------------
gates = load_settings()["gates"]
gate = check_gates(data, gates, DEMO_TICKERS)
if gate.stop is not None:  # "Not supported": the reason, no scores (AC2, E2, E3)
    st.error(stop_message(gate.stop, data.name))
    st.stop()

results = check_results(data)
scorecard_tab, sources_tab = st.tabs(["Scorecard", "Sources"])
with scorecard_tab:
    render_scorecard(data, results, price, warnings=header_warnings(gate, gates))
with sources_tab:
    render_sources(data, results)
