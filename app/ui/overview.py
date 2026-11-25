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
from src.overview import NA, Coverage, Figure, KeyFigure, Overview, Scorecard, Series, overview, scorecard

KIND_WORDS = {"reported": "Reported", "derived": "Derived", "assumption": "Assumption", "missing": "Not available"}
ARROWS = {1: "▲", -1: "▼", 0: ""}
DASHES = {"Revenue": "solid", "Net income": "solid", "Free cash flow": "dash"}


def _option(key: str):
    """A theme value for Plotly, which cannot follow CSS: the dark theme's value when the viewer sees the dark theme
    and the theme file has one (#54), else the light one; None without a theme file."""
    dark = getattr(getattr(st.context, "theme", None), "type", None) == "dark"
    return (dark and st.get_option(f"theme.dark.{key}")) or st.get_option(f"theme.{key}")


def _series_colours() -> tuple[str | None, ...]:
    """Line colours from the theme file, never written here (D's rule, tests/app/test_theme.py). The theme's
    `chartCategoricalColors` when set (design spec §9: blue, teal, magenta); until then the accent for revenue and
    the text colour for the other two, told apart by the dashed free cash flow line and the legend. Never red or
    green, so a colour never reads as good or bad. None lets the chart use the page's own colour."""
    themed = _option("chartCategoricalColors")
    if themed:
        return tuple(themed)
    accent, text = _option("primaryColor"), _option("textColor")
    return (accent, text, text)


def _pass_colour() -> str | None:
    """Passed checks and the radar: the theme's green when set, else its accent."""
    return _option("greenColor") or _option("primaryColor")


def _theme(key: str) -> str:
    """A theme colour as CSS that follows the active theme; the browser's text colour without a theme file."""
    light = st.get_option(f"theme.{key}") or "currentColor"
    dark = st.get_option(f"theme.dark.{key}") or light
    return f"light-dark({light}, {dark})"


def _theme_or(key: str, fallback: str) -> str:
    """Like `_theme`, falling back to another theme colour when this one is not set."""
    light = st.get_option(f"theme.{key}") or st.get_option(f"theme.{fallback}") or "currentColor"
    dark = st.get_option(f"theme.dark.{key}") or st.get_option(f"theme.dark.{fallback}") or light
    return f"light-dark({light}, {dark})"


def _style() -> str:
    return f"""<style>
.fs-ov {{--ov-pass:{_theme_or('greenColor', 'primaryColor')}; --ov-fail:{_theme_or('redColor', 'textColor')};
  --ov-page:{_theme('backgroundColor')}; --ov-accent:{_theme('primaryColor')}; --ov-muted:color-mix(in srgb, currentColor 66%, transparent);
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
.fs-ov-total {{font-size:64px; font-weight:600; line-height:1; margin:14px 0 6px}}
.fs-ov-total small {{font-size:32px; font-weight:400; color:var(--ov-muted)}}
.fs-ov-strong {{font-size:17px; font-weight:600; margin-bottom:4px}}
.fs-ov-focus {{border-top:1px solid var(--ov-line); margin-top:16px; padding-top:14px}}
.fs-ov-focus b {{display:block; font-size:22px; font-weight:600; color:var(--ov-pass); margin-top:4px}}
.fs-ov-area {{padding:10px 0; border-bottom:1px solid var(--ov-line)}}
.fs-ov-area-top {{display:flex; justify-content:space-between; gap:12px; font-weight:600}}
.fs-ov-area-top span {{font-weight:400; font-size:14px; color:var(--ov-muted); text-align:right}}
.fs-ov-marks {{display:flex; gap:6px; margin-top:8px}}
.fs-ov-mk {{width:20px; height:20px; border-radius:50%; box-sizing:border-box; display:inline-grid; place-items:center;
  font-size:12px; font-weight:700; line-height:1; flex:none; color:var(--ov-page)}}
.fs-ov-mk.fs-ov-pass {{background:var(--ov-pass)}}  .fs-ov-mk.fs-ov-fail {{background:var(--ov-fail)}}
.fs-ov-mk.fs-ov-wait {{color:inherit; border:1.5px dashed color-mix(in srgb, currentColor 60%, transparent)}}
.fs-ov-mk.fs-ov-none {{color:inherit; border:1px solid color-mix(in srgb, currentColor 35%, transparent)}}
.fs-ov-legend {{display:flex; flex-wrap:wrap; gap:8px 16px; margin-top:12px; font-size:13px; color:var(--ov-muted)}}
.fs-ov-legend > span {{display:inline-flex; align-items:center; gap:6px}}
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


MARK_LOOKS = {"pass": ("fs-ov-pass", "✓", "Passed"), "fail": ("fs-ov-fail", "✕", "Failed"),
              "not_assessed": ("fs-ov-wait", "", "Not assessed"), "not_applicable": ("fs-ov-none", "–", "Does not apply")}
RADAR_ORDER = ("financial_health", "past_performance", "valuation", "dividend")  # top, right, bottom, left


def _mark(look: str) -> str:
    css, glyph, word = MARK_LOOKS[look]
    return f'<span class="fs-ov-mk {css}" title="{word}" aria-hidden="true">{glyph}</span>'


def _radar(card: Scorecard) -> go.Figure:
    """Four axes, the share of assessed checks passed per area (centre 0%, edge 100%). An area with nothing assessed
    keeps its axis and label but is left off the shape, so it never reads as 0%."""
    areas = {a.area: a for a in card.areas}
    labels = [f"{areas[k].label}<br>{areas[k].share_text}" for k in RADAR_ORDER]
    scored = [(label, areas[k].share * 100) for k, label in zip(RADAR_ORDER, labels) if areas[k].share is not None]
    colour = _pass_colour()
    fig = go.Figure()
    fig.add_trace(go.Scatterpolar(r=[0] * len(labels), theta=labels, mode="markers", marker={"opacity": 0},
                                  hoverinfo="skip", showlegend=False))  # keeps every axis, even unscored ones
    if scored:
        r = [v for _, v in scored] + [scored[0][1]]
        theta = [label for label, _ in scored] + [scored[0][0]]
        fig.add_trace(go.Scatterpolar(r=r, theta=theta, mode="lines+markers", fill="toself", showlegend=False,
                                      line={"color": colour, "width": 2.5}, marker={"size": 8, "color": colour},
                                      hovertemplate="%{theta}<extra></extra>"))
    grid = _option("borderColor")  # None: Plotly's own grey
    page = _option("backgroundColor")
    fig.update_layout(
        height=360, margin={"l": 100, "r": 100, "t": 56, "b": 56}, showlegend=False, font={"size": 13},
        paper_bgcolor=page, plot_bgcolor=page,
        polar={"bgcolor": page, "gridshape": "linear",
               "angularaxis": {"rotation": 90, "direction": "clockwise", "categoryorder": "array",
                               "categoryarray": labels, "gridcolor": grid, "linecolor": grid},
               "radialaxis": {"range": [0, 100], "tickvals": [25, 50, 75, 100], "showticklabels": False,
                              "showline": False, "gridcolor": grid}})
    return fig


def render_scorecard_panel(card: Scorecard, fiscal_year: int | None) -> None:
    """The panel at the top of the overview: the total, the radar of the four areas, and the checks by area."""
    with st.container(border=True):
        left, middle, right = st.columns([1, 1.25, 1.05], gap="medium")
        with left:
            year = f"FY{fiscal_year} filing checks" if fiscal_year else "Filing checks"
            st.markdown(f"#### Company scorecard\n<span class='fs-ov-note'>{_e(year)}</span>", unsafe_allow_html=True)
            if card.headline:
                passed, assessed = card.headline
                total = (f'<div class="fs-ov-total">{_e(passed)}<small> / {_e(assessed)}</small></div>'
                         f'<div class="fs-ov-strong">assessed checks passed</div>'
                         f'<div class="fs-ov-note">{card.failed} failed · {card.not_assessed} not assessed</div>')
            else:
                total = '<div class="fs-ov-big">No check assessed yet</div>'
            focus = (f'<div class="fs-ov-focus"><span class="fs-ov-note">{_e(card.focus.label)}</span>'
                     f'<b>{_e(card.focus.count_text)}</b></div>') if card.focus else ""
            st.markdown(f'<div class="fs-ov">{total}{focus}</div>', unsafe_allow_html=True)
        with middle:
            st.plotly_chart(_radar(card), theme="streamlit", config={"displayModeBar": False}, key="scorecard_radar")
            st.caption("Share of assessed checks passed in each area: centre 0%, edge 100%. An area not assessed "
                       "is left off the shape.")
        with right:
            rows = "".join(
                f'<div class="fs-ov-area" role="group" aria-label="{_e(a.label)}: {_e(a.count_text)}">'
                f'<div class="fs-ov-area-top">{_e(a.label)}<span>{_e(a.count_text)}</span></div>'
                f'<div class="fs-ov-marks">{"".join(_mark(m) for m in a.marks)}</div></div>'
                for a in card.areas)
            legend = "".join(f"<span>{_mark(look)}{word}</span>" for look, (_, _, word) in MARK_LOOKS.items())
            st.markdown(f'#### Checks by area\n<div class="fs-ov">{rows}<div class="fs-ov-legend">{legend}</div>'
                        f'</div>', unsafe_allow_html=True)


def render_overview(data: CompanyData, results=None) -> Overview:
    """Draw the overview for one company and return what was drawn (for tests). With the check results (as
    `ui.results.check_results` returns them), the scorecard panel comes first."""
    ov = overview(data)
    st.markdown(_style(), unsafe_allow_html=True)
    if results is not None:
        render_scorecard_panel(scorecard(results), ov.fiscal_year)
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
