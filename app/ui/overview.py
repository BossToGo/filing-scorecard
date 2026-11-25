"""The overview above the tabs (slice S10c): key figures, five years, dividend coverage, balance sheet, filing.

Built by A in D's folder, with D's agreement on #47 (25 November 2026); D calls `render_overview(data)` above the
tabs. Display only: every number and text comes from `src.overview` (SPEC §11). Colours come from the theme file, as
in the rest of the screen (design spec §4); the chart uses Streamlit's theme.
"""

from __future__ import annotations

import html

import plotly.graph_objects as go
import streamlit as st

from src.contracts import CompanyData
from src.overview import NA, Coverage, Figure, KeyFigure, Overview, Series, overview

KIND_WORDS = {"reported": "Reported", "derived": "Derived", "assumption": "Assumption", "missing": "Not available"}
ARROWS = {1: "▲", -1: "▼", 0: ""}
DASHES = {"Revenue": "solid", "Net income": "solid", "Free cash flow": "dash"}
# Chart lines: blue, teal and magenta, a colour per series that never means good or bad (no red, no green; design
# spec §9). Each has at least 3:1 contrast on a white page and on a dark navy one, so one set works in both themes.
# Used until the theme file sets `chartCategoricalColors`; then the theme's colours win (D's config.toml).
SERIES_COLOURS = ("#3A86CC", "#1FA08B", "#BD5A97")


def _series_colours() -> tuple[str, ...]:
    themed = st.get_option("theme.chartCategoricalColors")
    return tuple(themed) if themed else SERIES_COLOURS


def _theme(key: str) -> str:
    """A theme colour as CSS that follows the active theme; the browser's text colour without a theme file."""
    light = st.get_option(f"theme.{key}") or "currentColor"
    dark = st.get_option(f"theme.dark.{key}") or light
    return f"light-dark({light}, {dark})"


def _style() -> str:
    return f"""<style>
.fs-ov {{--ov-accent:{_theme('primaryColor')}; --ov-muted:color-mix(in srgb, currentColor 66%, transparent);
  --ov-line:color-mix(in srgb, currentColor 18%, transparent); font-variant-numeric:tabular-nums}}
.fs-ov-kpis {{display:grid; grid-template-columns:repeat(4, minmax(0, 1fr)); border-top:1px solid var(--ov-line);
  border-bottom:1px solid var(--ov-line); padding:16px 0; margin:4px 0 8px}}
.fs-ov-kpi {{padding:0 20px; border-left:1px solid var(--ov-line)}}  .fs-ov-kpi:first-child {{padding-left:0; border-left:0}}
.fs-ov-label {{font-size:14px; color:var(--ov-muted)}}
.fs-ov-big {{font-size:32px; font-weight:600; line-height:1.2; margin:4px 0}}
.fs-ov-big small {{font-size:16px; font-weight:400; color:var(--ov-muted); margin:0 4px}}
.fs-ov-meta {{font-size:13px; color:var(--ov-muted); display:flex; gap:12px; flex-wrap:wrap}}
.fs-ov-meta b {{font-weight:600; color:var(--ov-accent)}}
.fs-ov-note {{font-size:13px; color:var(--ov-muted)}}
.fs-ov-pct {{font-size:44px; font-weight:600; line-height:1.1; color:var(--ov-accent); margin:4px 0 12px}}
.fs-ov-bar {{display:flex; justify-content:space-between; font-size:15px; margin-bottom:6px}}
.fs-ov-track {{height:8px; border-radius:4px; background:var(--ov-line); margin-bottom:14px}}
.fs-ov-fill {{height:8px; border-radius:4px; background:var(--ov-accent)}}
.fs-ov-fill.fs-ov-text {{background:currentColor}}
.fs-ov-gap {{border-top:1px solid var(--ov-line); padding-top:10px; display:flex; gap:12px; align-items:baseline}}
.fs-ov-gap b {{font-size:22px; color:var(--ov-accent)}}
table.fs-ov-rows {{width:100%; border-collapse:collapse}}
table.fs-ov-rows td {{padding:9px 0; border:0; border-bottom:1px solid var(--ov-line)}}
table.fs-ov-rows td.fs-ov-kind {{font-size:12px; color:var(--ov-muted); text-align:right; padding-right:16px}}
table.fs-ov-rows td.fs-ov-num {{text-align:right; font-weight:600}}
@media (max-width: 760px) {{.fs-ov-kpis {{grid-template-columns:repeat(2, minmax(0, 1fr)); row-gap:16px}}
  .fs-ov-kpi:nth-child(3) {{padding-left:0; border-left:0}}}}
</style>"""


def _e(text: str) -> str:
    return html.escape(text, quote=True)


def _number(figure: Figure) -> str:
    if figure.number == NA:
        return "n/a"
    before = f"<small>{_e(figure.before)}</small>" if figure.before else ""
    after = f"<small>{_e(figure.after)}</small>" if figure.after else ""
    return f"{before}{_e(figure.number)}{after}"


def _key_figure(figure: KeyFigure) -> str:
    arrow = ARROWS.get(figure.direction, "") if figure.direction is not None else ""
    change = f"<b>{arrow} {_e(figure.change)}</b>" if figure.change not in (NA, "") else f"<span>{_e(figure.change)}</span>"
    note = f'<div class="fs-ov-note">{_e(figure.note)}</div>' if figure.note else ""
    return (f'<div class="fs-ov-kpi"><div class="fs-ov-label">{_e(figure.label)}</div>'
            f'<div class="fs-ov-big">{_number(figure)}</div>'
            f'<div class="fs-ov-meta">{change}<span>{_e(figure.versus)}</span>'
            f'<span>{_e(KIND_WORDS.get(figure.kind, figure.kind))}</span></div>{note}</div>')


def _rows(figures: tuple[Figure, ...]) -> str:
    rows = "".join(
        f'<tr><td>{_e(f.label)}' + (f'<div class="fs-ov-note">{_e(f.note)}</div>' if f.note else "") + "</td>"
        f'<td class="fs-ov-kind">{_e(KIND_WORDS.get(f.kind, f.kind))}</td><td class="fs-ov-num">{_e(f.text)}</td></tr>'
        for f in figures)
    return f'<table class="fs-ov-rows">{rows}</table>'


def _coverage(cover: Coverage) -> str:
    head = (f'<div class="fs-ov-pct">{_e(cover.percent)}</div>' if cover.percent
            else f'<div class="fs-ov-big">{_e(cover.text)}</div>')
    if cover.status in ("no_dividend", "missing"):
        note = f'<div class="fs-ov-note">{_e(cover.note)}</div>' if cover.note else ""
        return f'<div class="fs-ov">{head}{note}</div>'
    share = f"{(cover.share or 0) * 100:.1f}"  # bar width only, from the prepared share
    bars = (f'<div class="fs-ov-bar"><span>Free cash flow</span><b>{_e(cover.free_cash_flow)}</b></div>'
            f'<div class="fs-ov-track"><div class="fs-ov-fill fs-ov-text" style="width:{share}%"></div></div>'
            f'<div class="fs-ov-bar"><span>Dividends paid</span><b>{_e(cover.dividends)}</b></div>'
            f'<div class="fs-ov-track"><div class="fs-ov-fill" style="width:100%"></div></div>')
    gap = f'<div class="fs-ov-gap"><b>{_e(cover.gap)}</b><span>{_e(cover.gap_label)}</span></div>' if cover.gap else ""
    text = f'<div class="fs-ov-note">{_e(cover.text)}</div>' if cover.percent else ""
    return f'<div class="fs-ov">{head}{text}{bars}{gap}</div>'


def _chart(series: Series) -> go.Figure:
    fig = go.Figure()
    colours = _series_colours()
    for index, line in enumerate(series.lines):
        colour = colours[index % len(colours)]
        fig.add_trace(go.Scatter(
            x=list(series.years), y=list(line.values), name=line.label, mode="lines+markers",
            line={"width": 2.5, "dash": DASHES.get(line.label, "solid"), "color": colour},
            marker={"size": 7, "color": colour},
            customdata=list(line.texts), hovertemplate="%{x}: %{customdata}<extra>" + line.label + "</extra>",
            connectgaps=False))
    fig.update_layout(height=300, margin={"l": 0, "r": 0, "t": 8, "b": 0}, hovermode="x unified",
                      legend={"orientation": "h", "y": 1.12, "x": 0}, yaxis={"title": series.unit, "rangemode": "tozero"},
                      xaxis={"tickmode": "array", "tickvals": list(series.years)})
    return fig


def _table(series: Series) -> str:
    head = "".join(f"<td class='fs-ov-num'>{year}</td>" for year in series.years)
    body = "".join(
        f"<tr><td>{_e(line.label)}</td>" + "".join(f"<td class='fs-ov-num'>{_e(t)}</td>" for t in line.texts) + "</tr>"
        for line in series.lines)
    return f'<div class="fs-ov"><table class="fs-ov-rows"><tr><td></td>{head}</tr>{body}</table></div>'


def render_overview(data: CompanyData) -> Overview:
    """Draw the overview for one company and return what was drawn (for tests)."""
    ov = overview(data)
    st.markdown(_style(), unsafe_allow_html=True)
    if ov.key_figures:
        strip = "".join(_key_figure(f) for f in ov.key_figures)
        st.markdown(f'<div class="fs-ov"><div class="fs-ov-kpis">{strip}</div></div>', unsafe_allow_html=True)

    left, right = st.columns([1.62, 1], gap="medium")
    with left, st.container(border=True, height="stretch"):
        top, switch = st.columns([3, 1], vertical_alignment="bottom")
        top.markdown(f"#### Financial performance\n<span class='fs-ov-note'>Annual results, {_e(ov.series.unit)}</span>",
                     unsafe_allow_html=True)
        view = switch.segmented_control("View", ["Chart", "Table"], default="Chart", key="overview_view",
                                        label_visibility="collapsed")
        if view == "Table":
            st.markdown(_table(ov.series), unsafe_allow_html=True)
        else:
            st.plotly_chart(_chart(ov.series), theme="streamlit", config={"displayModeBar": False},
                            key="overview_chart")
            st.caption("Revenue, net income and free cash flow (operating cash flow minus capital expenditure) for "
                       "each fiscal year. Choose Table for the exact figures.")
    with right, st.container(border=True, height="stretch"):
        st.markdown("#### Dividend coverage\n<span class='fs-ov-note'>Free cash flow as a share of dividends paid</span>",
                    unsafe_allow_html=True)
        st.markdown(_coverage(ov.coverage), unsafe_allow_html=True)

    left, right = st.columns([1.62, 1], gap="medium")
    with left, st.container(border=True, height="stretch"):
        st.markdown("#### Balance sheet", unsafe_allow_html=True)
        st.markdown(f'<div class="fs-ov">{_rows(ov.balance)}</div>', unsafe_allow_html=True)
    with right, st.container(border=True, height="stretch"):
        f = ov.filing
        st.markdown("#### Filing details", unsafe_allow_html=True)
        rows = (("Source", f"SEC Form {f.form}" if f.form != NA else NA), ("Filed", f.filed),
                ("Accession", f.accession), ("Data retrieved", f.retrieved))
        table = "".join(f"<tr><td>{_e(k)}</td><td class='fs-ov-num'>{_e(v)}</td></tr>" for k, v in rows)
        st.markdown(f'<div class="fs-ov"><table class="fs-ov-rows">{table}</table>'
                    f'<div class="fs-ov-note" style="margin-top:8px">{f.metrics} metrics, {f.records} records on the '
                    f"Sources tab</div></div>", unsafe_allow_html=True)
    return ov
