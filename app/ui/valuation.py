"""The valuation tab's estimate and detail (SPEC §3 item 6, §8, §9.1; slice S10b). Owner: D.

Shows what `ui.results.run_checks` returns: C's `Valuation` (one run at the typed price, the same one V1-V6 use),
B's benchmarks and A's risk-free rate. Nothing here computes a financial number; `ui.format` only writes them.
On screen the model's result is "the estimate", never "fair value" (SPEC §3). No sensitivity table, no implied growth
and no user inputs (SPEC §8.4, §8.5, §8.7).
"""

from __future__ import annotations

from typing import Mapping

import pandas as pd
import streamlit as st

from src.contracts import Fact
from src.data.company import FRED_NOTICE
from ui.format import beta, fact_value, rate, share_price, usd_m
from ui.results import Market

NEEDS_PRICE = ("Needs a share price. Type it in US dollars in the Share price box above, then show the scorecard "
               "again: the estimate and the valuation checks use it.")
ESTIMATE_TITLE = "The estimate"
ESTIMATE_NOTE = "The cash-flow estimate per share under the assumptions below. It is information, not advice."
NO_ESTIMATE = "No estimate."
# Plain labels for the engine's metric names (SPEC §3: never "fair value" or the internal names on screen)
LABELS = {
    "risk_free_rate": "Risk-free rate",
    "equity_risk_premium": "Equity risk premium",
    "unlevered_beta": "Industry unlevered beta",
    "levered_beta": "Levered beta (with the company's own debt)",
    "cost_of_equity": "Cost of equity",
    "terminal_growth": "Long-run growth after year 10",
    "free_cash_flow_margin": "Free cash flow margin (last three years)",
    "starting_free_cash_flow": "Starting free cash flow",
    "past_revenue_growth": "The company's actual revenue growth a year",
    "starting_growth": "Starting growth used by the model",
    "minority_interest": "Minority interests",
    "equity_value": "Equity value",
    "fair_value": "The estimate",
    "fair_value_at_growth_cap": "The estimate with starting growth at the cap",
    "roe": "Return on equity",
    "operating_margin": "Operating margin",
    "pe": "Price to earnings",
    "pb": "Price to book",
    "dividend_yield": "Dividend yield",
}
RATES = {"risk_free_rate", "equity_risk_premium", "cost_of_equity", "terminal_growth", "free_cash_flow_margin",
         "past_revenue_growth", "starting_growth", "roe", "operating_margin", "dividend_yield"}
BETAS = {"unlevered_beta", "levered_beta"}


def label(metric: str) -> str:
    return LABELS.get(metric, metric.replace("_", " "))


def shown(fact: Fact | None) -> str:
    """A figure of the valuation as written on screen; a missing one is "n/a" with its reason."""
    if fact is None:
        return "n/a"
    if fact.value is None or fact.kind == "missing":
        return fact_value(fact)
    if fact.metric in RATES:
        return rate(fact.value)
    if fact.metric in BETAS:
        return beta(fact.value)
    return fact_value(fact)


def _rows(facts) -> pd.DataFrame:
    return pd.DataFrame([{"Step": label(f.metric), "Value": shown(f), "Kind": f.kind, "Source": f.note}
                         for f in facts if f is not None], columns=["Step", "Value", "Kind", "Source"])


def render_estimate(market: Market) -> None:
    """The key result at the top of the tab: the estimate per share against the typed price, or why there is none."""
    st.subheader(ESTIMATE_TITLE)
    v = market.valuation
    if market.price is None:  # AC10
        st.info(NEEDS_PRICE)
        return
    if v is None or v.status != "ok":
        st.markdown(f"**{NO_ESTIMATE}** {v.reason if v is not None else ''}")
        return
    estimate, typed = st.columns(2)
    estimate.markdown(f"**{ESTIMATE_TITLE}:** {shown(v.fair_value)}")
    typed.markdown(f"**Share price you typed:** {share_price(market.price)}")
    st.caption(ESTIMATE_NOTE)


def render_detail(market: Market, texts: Mapping) -> None:
    """Cost of equity build-up, starting point, ten-year table, notes, then the industry and its benchmarks."""
    v = market.valuation
    st.markdown("**Cost of equity, step by step**")
    steps = (market.risk_free, v.equity_risk_premium if v else None, market.benchmarks.fact("unlevered_beta"),
             v.levered_beta if v else None, v.cost_of_equity if v else None, v.terminal_growth if v else None)
    st.table(_rows(steps))
    st.caption(FRED_NOTICE)  # FRED's terms: wherever the risk-free rate is shown

    if v is not None and v.starting_free_cash_flow is not None:
        st.markdown("**Starting point**")
        st.table(_rows((v.free_cash_flow_margin, v.starting_free_cash_flow, v.past_revenue_growth,
                        v.starting_growth)))
    if v is not None and v.forecast is not None:
        st.markdown("**Free cash flow, the next ten years**")
        st.table(pd.DataFrame([{"Year": y.year, "Growth": rate(y.growth), "Free cash flow": usd_m(y.free_cash_flow),
                                "Discounted to the end of the latest year": usd_m(y.discounted)}
                               for y in v.forecast.years]))
        f = v.forecast
        lines = [("Ten years, discounted", usd_m(f.sum_of_discounted)), ("Value after year 10", usd_m(f.terminal_value)),
                 ("Value after year 10, discounted", usd_m(f.discounted_terminal_value))]
        lines += [(label(x.metric), shown(x)) for x in (v.minority_interest, v.equity_value, v.fair_value,
                                                         v.fair_value_at_growth_cap) if x is not None]
        st.table(pd.DataFrame(lines, columns=["Item", "Value"]).set_index("Item"))
    if v is not None and v.status != "ok" and v.reason:
        st.markdown(f"**Why there is no estimate:** {v.reason}")
    for note in (v.notes if v is not None else ()):
        st.markdown(f"- {note}")
    render_industry(market, texts)


def render_industry(market: Market, texts: Mapping) -> None:
    """The industry group, how it was found and its number of firms, and each benchmark with its source (AC8)."""
    b = market.benchmarks
    st.markdown("**Industry and benchmarks**")
    if b.industry is None:
        st.markdown(f"Industry: none found. {b.fact('roe').note}")
    else:
        firms = f", {b.num_firms} firms" if b.num_firms is not None else ""
        st.markdown(f"Industry: {b.industry} ({b.route}{firms}).")
        if b.lookup_source:
            st.caption(f"How it was found: {b.lookup_source}")
    note = texts.get("industry_note")  # Emma's text (#56), shown once it is merged
    if isinstance(note, str) and note:
        st.caption(note)
    rows = [{"Benchmark": label(f.metric), "Group": group, "Value": shown(f), "Source file": f.form or "",
             "Column": f.tag or "", "Note": f.note}
            for group, facts in ((b.industry or "none", (b.fact(m) for m in ("unlevered_beta", "roe",
                                                                             "operating_margin", "pe", "pb"))),
                                 ("Whole US market", (b.market_fact(m) for m in ("pe", "dividend_yield"))))
            for f in facts]
    st.table(pd.DataFrame(rows))
