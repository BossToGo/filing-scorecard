"""The overview above the tabs (slice S10c): key figures, five years, dividend coverage, balance sheet, filing.

Built by A in D's folder, with D's agreement on #47 (25 November 2026); D calls `render_overview(data)` above the
tabs. Display only: every number and text comes from `src.overview` (SPEC §11). Colours come from the theme file, as
in the rest of the screen (design spec §4); the chart uses Streamlit's theme.
"""

from __future__ import annotations

import html
import json

import plotly.graph_objects as go
import streamlit as st

from src.contracts import CompanyData
from src.overview import (NA, RADAR_ORDER, Coverage, Figure, KeyFigure, Overview, Scorecard, Series, overview,
                          radar_shape, scorecard)

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
    if isinstance(themed, str):  # given on the command line it arrives as text: '["…", "…"]'
        try:
            themed = json.loads(themed)
        except ValueError:
            themed = [part.strip(" '\"[]") for part in themed.split(",")]
    if themed:
        return tuple(themed)
    accent, text = _option("primaryColor"), _option("textColor")
    return (accent, text, text)


def _pass_colour() -> str | None:
    """Passed checks and the radar: the theme's accent (SPEC §3). Never green or red, so a colour never reads as
    good or bad on its own; the tick, the cross and the words carry the meaning (Igor's choice, 26 November)."""
    return _option("primaryColor")


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
    """One CSS block for the overview (Igor's design of 25 November). Colours come from the theme file only."""
    return f"""<style>
.fs-ov, [class*="st-key-ov_card"], .fs-ov-shell {{--ov-pass:{_theme('primaryColor')};
  --ov-fail:{_theme('textColor')}; --ov-page:{_theme('backgroundColor')};
  --ov-panel:{_theme_or('secondaryBackgroundColor', 'backgroundColor')}; --ov-accent:{_theme('primaryColor')};
  --ov-muted:color-mix(in srgb, currentColor 62%, transparent); --ov-line:color-mix(in srgb, currentColor 14%, transparent);
  font-variant-numeric:tabular-nums}}
[class*="st-key-ov_card"] {{background:var(--ov-panel); border-radius:12px !important; padding:22px 26px !important}}
.fs-ov-h {{font-family:Georgia, 'Times New Roman', serif; font-weight:400; font-size:30px; line-height:1.15; white-space:nowrap;
  letter-spacing:-0.01em}}
.fs-ov-h.fs-ov-sans {{font-family:inherit; font-weight:600; font-size:20px}}
.fs-ov-sub {{font-size:15px; color:var(--ov-muted); margin-top:6px}}
.fs-ov-kpis {{display:grid; grid-template-columns:repeat(4, minmax(0, 1fr)); border-top:1px solid var(--ov-line);
  border-bottom:1px solid var(--ov-line); padding:22px 0; margin:18px 0 22px}}
.fs-ov-kpi {{padding:0 28px; border-left:1px solid var(--ov-line)}}  .fs-ov-kpi:first-child {{padding-left:0; border-left:0}}
.fs-ov-label {{font-size:16px; color:var(--ov-muted)}}
.fs-ov-big {{font-size:42px; font-weight:700; line-height:1.15; margin:6px 0 8px; letter-spacing:-0.01em; white-space:nowrap}}
.fs-ov-big small {{font-size:22px; font-weight:400; color:var(--ov-muted); margin:0 6px}}
.fs-ov-meta {{font-size:14px; color:var(--ov-muted); display:flex; gap:22px; flex-wrap:wrap}}
.fs-ov-up {{color:var(--ov-pass); font-weight:600}}  .fs-ov-down {{color:var(--ov-fail); font-weight:600}}
.fs-ov-note {{font-size:13px; color:var(--ov-muted)}}
.fs-ov-legend-line {{display:flex; gap:28px; font-size:15px; margin:18px 0 0}}
.fs-ov-legend-line span {{display:inline-flex; align-items:center; gap:10px}}
.fs-ov-legend-line i {{display:inline-block; width:20px; border-top:3px solid}}
.fs-ov-pct {{font-family:Georgia, 'Times New Roman', serif; font-size:76px; line-height:1; color:var(--ov-accent);
  margin:22px 0 26px}}
.fs-ov-bar {{display:flex; justify-content:space-between; font-size:17px; margin-bottom:10px}}
.fs-ov-bar b {{font-weight:600}}
.fs-ov-track {{height:9px; border-radius:5px; background:var(--ov-line); margin-bottom:24px}}
.fs-ov-fill {{height:9px; border-radius:5px; background:var(--ov-accent)}}
.fs-ov-gap {{border-top:1px solid var(--ov-line); padding-top:18px; display:flex; gap:22px; align-items:baseline;
  font-size:17px; color:var(--ov-muted)}}
.fs-ov-gap b {{font-size:28px; font-weight:700; color:var(--ov-accent); white-space:nowrap}}
table.fs-ov-rows {{width:100%; border-collapse:collapse; margin-top:16px; font-size:17px}}
table.fs-ov-rows td {{padding:10px 0; border:0; border-top:1px solid var(--ov-line)}}
table.fs-ov-rows td.fs-ov-kind {{font-size:14px; color:var(--ov-muted); text-align:right; padding-right:28px}}
table.fs-ov-rows td.fs-ov-kind.fs-ov-derived {{color:var(--ov-accent)}}
table.fs-ov-rows td.fs-ov-num {{text-align:right; font-weight:600}}
table.fs-ov-rows td.fs-ov-plain {{color:var(--ov-muted)}}
.st-key-ov_card_scorecard [data-testid="stColumn"]:not(:first-child) {{border-left:1px solid var(--ov-line); padding-left:24px}}
.fs-ov-caption {{text-align:center; font-size:14px; color:var(--ov-muted); margin-top:-6px}}
.fs-ov-read {{font-size:16px; line-height:1.55; margin-top:6px}}  .fs-ov-read p {{margin:0 0 12px}}
.fs-ov-read b {{font-weight:600}}
.fs-ov-foot {{display:flex; justify-content:space-between; gap:16px; font-size:14px; color:var(--ov-muted); margin:22px 0 8px}}
.fs-ov-shell-bar {{display:flex; align-items:center; gap:20px; height:64px}}
.fs-ov-brand {{display:flex; align-items:center; gap:14px; font-family:Georgia, 'Times New Roman', serif; font-size:30px}}
.fs-ov-brand svg {{color:var(--ov-accent)}}
.fs-ov-sep {{width:1px; height:30px; background:var(--ov-line)}}
.fs-ov-crumbs {{font-size:16px; color:var(--ov-muted); display:flex; gap:16px; margin-top:8px}}
.fs-ov-crumbs b {{color:var(--ov-accent); font-weight:400}}
.fs-ov-title-row {{display:flex; justify-content:space-between; align-items:flex-start; gap:24px}}
.fs-ov-title {{font-family:Georgia, 'Times New Roman', serif; font-size:72px; line-height:1.05; margin:18px 0 10px;
  letter-spacing:-0.01em}}
.fs-ov-title-meta {{font-size:18px; color:var(--ov-muted)}}  .fs-ov-title-meta b {{color:inherit; font-weight:600}}
.fs-ov-pill {{margin-top:30px; border:1px solid var(--ov-line); border-radius:8px; padding:12px 18px; font-size:17px;
  font-weight:600; white-space:nowrap}}
.fs-ov-nav-eyebrow {{font-size:13px; letter-spacing:0.16em; text-transform:uppercase; color:var(--ov-muted);
  margin:22px 0 18px 4px}}
a.fs-ov-nav {{display:flex; align-items:center; gap:14px; padding:12px 16px; border-radius:8px; font-size:18px;
  color:inherit !important; text-decoration:none !important; border-left:3px solid transparent; margin-bottom:6px}}
a.fs-ov-nav.fs-ov-on {{color:var(--ov-accent) !important; background:color-mix(in srgb, var(--ov-accent) 12%, transparent);
  border-left-color:var(--ov-accent)}}
a.fs-ov-nav svg {{width:20px; height:20px; flex:none}}
.fs-ov-coverage {{border-top:1px solid var(--ov-line); margin-top:48px; padding-top:22px}}
.fs-ov-coverage b {{display:block; font-size:18px; font-weight:400; margin-top:8px}}
@media (max-width: 760px) {{.fs-ov-kpis {{grid-template-columns:repeat(2, minmax(0, 1fr)); row-gap:16px}}
  .fs-ov-kpi:nth-child(3) {{padding-left:0; border-left:0}}  .fs-ov-title {{font-size:44px}}}}
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
    css = {1: "fs-ov-up", -1: "fs-ov-down"}.get(figure.direction, "")
    change = f'<span class="{css}">{_e(figure.change)}</span>' if css else f"<span>{_e(figure.change)}</span>"
    note = f'<div class="fs-ov-note">{_e(figure.note)}</div>' if figure.note else ""
    return (f'<div class="fs-ov-kpi"><div class="fs-ov-label">{_e(figure.label)}</div>'
            f'<div class="fs-ov-big">{_number(figure)}</div>'
            f'<div class="fs-ov-meta">{change}<span>{_e(figure.versus)}</span>'
            f'<span>{_e(KIND_WORDS.get(figure.kind, figure.kind))}</span></div>{note}</div>')


def _heading(title: str, sub: str = "", sans: bool = False) -> str:
    sub_html = f'<div class="fs-ov-sub">{_e(sub)}</div>' if sub else ""
    return f'<div class="fs-ov"><div class="fs-ov-h{" fs-ov-sans" if sans else ""}">{_e(title)}</div>{sub_html}</div>'


def _rows(figures: tuple[Figure, ...]) -> str:
    rows = "".join(
        f'<tr><td>{_e(f.label)}' + (f'<div class="fs-ov-note">{_e(f.note)}</div>' if f.note else "") + "</td>"
        f'<td class="fs-ov-kind{" fs-ov-derived" if f.kind == "derived" else ""}">{_e(KIND_WORDS.get(f.kind, f.kind))}</td>'
        f'<td class="fs-ov-num">{_e(f.text)}</td></tr>'
        for f in figures)
    return f'<table class="fs-ov-rows">{rows}</table>'


def _coverage(cover: Coverage) -> str:
    head = (f'<div class="fs-ov-pct">{_e(cover.percent)}</div>' if cover.percent
            else f'<div class="fs-ov-big" style="margin-top:22px">{_e(cover.text)}</div>')
    if cover.status in ("no_dividend", "missing"):
        note = f'<div class="fs-ov-note">{_e(cover.note)}</div>' if cover.note else ""
        return f'<div class="fs-ov">{head}{note}</div>'
    fcf = _series_colours()[2 % len(_series_colours())]  # the free cash flow line's colour in the chart
    fill = f"width:{cover.bar_width}%" + (f"; background:{fcf}" if fcf else "")
    bars = (f'<div class="fs-ov-bar"><span>Free cash flow</span><b>{_e(cover.free_cash_flow)}</b></div>'
            f'<div class="fs-ov-track"><div class="fs-ov-fill" style="{fill}"></div></div>'
            f'<div class="fs-ov-bar"><span>Dividends paid</span><b>{_e(cover.dividends)}</b></div>'
            f'<div class="fs-ov-track"><div class="fs-ov-fill" style="width:100%"></div></div>')
    gap = f'<div class="fs-ov-gap"><b>{_e(cover.gap)}</b><span>{_e(cover.gap_label)}</span></div>' if cover.gap else ""
    return f'<div class="fs-ov">{head}{bars}{gap}</div>'


def _chart(series: Series) -> go.Figure:
    """Lines with hollow markers, each line's last value written at its end, a dotted grid and a dashed line at the
    latest year. Every number comes from `src.overview`."""
    fig = go.Figure()
    colours = _series_colours()
    years = list(series.years)
    for index, line in enumerate(series.lines):
        colour = colours[index % len(colours)]
        fig.add_trace(go.Scatter(
            x=years, y=list(line.values), name=line.label, mode="lines+markers",
            line={"width": 3, "dash": DASHES.get(line.label, "solid"), "color": colour},
            marker={"size": 10, "color": _option("secondaryBackgroundColor") or _option("backgroundColor"),
                    "line": {"width": 2.5, "color": colour}},
            customdata=list(line.texts), hovertemplate="%{x}: %{customdata}<extra>" + line.label + "</extra>",
            connectgaps=False, showlegend=False))
        if line.end_label and line.values[-1] is not None:
            fig.add_annotation(x=years[-1], y=line.values[-1], text=line.end_label, showarrow=False, xanchor="left",
                               xshift=14, font={"color": colour, "size": 15})
    grid = _option("borderColor")
    fig.add_vline(x=years[-1], line={"dash": "dot", "width": 1, "color": grid}) if years else None
    panel = _option("secondaryBackgroundColor") or _option("backgroundColor")
    fig.update_layout(height=330, margin={"l": 0, "r": 64, "t": 10, "b": 0}, hovermode="x unified",
                      paper_bgcolor=panel, plot_bgcolor=panel, font={"size": 14},
                      yaxis={"rangemode": "tozero", "gridcolor": grid, "griddash": "dot", "zeroline": False},
                      xaxis={"tickmode": "array", "tickvals": years, "showgrid": False})
    return fig


def _table(series: Series) -> str:
    head = "".join(f"<td class='fs-ov-num'>{year}</td>" for year in series.years)
    body = "".join(
        f"<tr><td>{_e(line.label)}</td>" + "".join(f"<td class='fs-ov-num'>{_e(t)}</td>" for t in line.texts) + "</tr>"
        for line in series.lines)
    return f'<div class="fs-ov"><table class="fs-ov-rows"><tr><td></td>{head}</tr>{body}</table></div>'


NOT_A_RATING = "Not a rating of the share and not advice."  # SPEC §3, under the radar
HOW_TO_READ = (  # static words of the panel; every figure comes from src.overview
    "<p><b>How to read it.</b> Each corner is one area of the scorecard. The further out the point, the larger the "
    "share of that area's assessed checks that passed: the centre is 0% and the edge 100%.</p>"
    "<p>An area with nothing to score (not assessed, or a check that does not apply) keeps its label but stays off "
    "the shape, and the line breaks at its corner, so it never reads as 0%.</p>"
    "<p>Each area's six checks, with their reasons, are listed in the score chart below.</p>")


def _radar(card: Scorecard) -> go.Figure:
    """Four axes, the share of assessed checks passed per area (centre 0%, edge 100%). What to draw comes from
    `src.overview.radar_shape`: lines only between neighbouring scored areas, a filled shape only when all four are
    scored, so an area off the shape is never crossed through the centre."""
    areas = {a.area: a for a in card.areas}
    shape = radar_shape(card)
    colour = _pass_colour()
    def name(k: str, side: bool) -> str:  # a side label on two lines ("Past / performance"), so it is not cut off
        return areas[k].label.replace(" ", "<br>", 1) if side else areas[k].label

    labels = {k: (f"<b>{name(k, i % 2)}</b><br><span style='color:{colour}'>{areas[k].share_text}</span>"
                  if areas[k].share is not None else f"<b>{name(k, i % 2)}</b><br>{areas[k].share_text}")
              for i, k in enumerate(RADAR_ORDER)}
    r = dict(shape.points)
    line = {"color": colour, "width": 3}
    fig = go.Figure()
    fig.add_trace(go.Scatterpolar(r=[0] * len(RADAR_ORDER), theta=[labels[k] for k in RADAR_ORDER], mode="markers",
                                  marker={"opacity": 0}, hoverinfo="skip", showlegend=False))  # every axis, always
    if shape.filled:
        order = list(RADAR_ORDER) + [RADAR_ORDER[0]]
        fig.add_trace(go.Scatterpolar(r=[r[k] for k in order], theta=[labels[k] for k in order], mode="lines+markers",
                                      fill="toself", line=line, marker={"size": 9, "color": colour},
                                      hoverinfo="skip", showlegend=False))
    else:
        for a, b in shape.edges:
            fig.add_trace(go.Scatterpolar(r=[r[a], r[b]], theta=[labels[a], labels[b]], mode="lines", line=line,
                                          hoverinfo="skip", showlegend=False))
        if shape.points:
            fig.add_trace(go.Scatterpolar(r=[r[k] for k, _ in shape.points], theta=[labels[k] for k, _ in shape.points],
                                          mode="markers", marker={"size": 9, "color": colour}, hoverinfo="skip",
                                          showlegend=False))
    grid = _option("borderColor")  # None: Plotly's own grey
    panel = _option("secondaryBackgroundColor") or _option("backgroundColor")
    fig.update_layout(
        height=390, margin={"l": 114, "r": 114, "t": 50, "b": 50}, showlegend=False, font={"size": 13},
        paper_bgcolor=panel, plot_bgcolor=panel,
        polar={"bgcolor": panel, "gridshape": "linear",
               "angularaxis": {"rotation": 90, "direction": "clockwise", "categoryorder": "array",
                               "categoryarray": [labels[k] for k in RADAR_ORDER], "gridcolor": grid, "linecolor": grid},
               "radialaxis": {"range": [0, 100], "tickvals": [25, 50, 75, 100], "showticklabels": False,
                              "showline": False, "gridcolor": grid}})
    return fig


def render_scorecard_panel(card: Scorecard, fiscal_year: int | None) -> None:
    """The panel at the top of the overview: the radar of the four areas and how to read it. The six marks of each
    area are in D's score chart below, with each check's name and reason, so the panel does not repeat them (Igor,
    26 November). No total and no area to read first (the group's answers on #60)."""
    with st.container(border=True, key="ov_card_scorecard"):
        st.markdown(_heading("Checks by area", f"FY{fiscal_year} filing checks" if fiscal_year else "Filing checks"),
                    unsafe_allow_html=True)
        left, right = st.columns([1.25, 1], gap="large")
        with left:
            st.plotly_chart(_radar(card), theme="streamlit", config={"displayModeBar": False}, key="scorecard_radar")
            st.markdown('<div class="fs-ov fs-ov-caption">Share of assessed checks passed per area<br>'
                        f"Centre 0% · edge 100%<br>{NOT_A_RATING}</div>", unsafe_allow_html=True)
        with right:
            st.markdown(f'<div class="fs-ov fs-ov-read">{HOW_TO_READ}</div>', unsafe_allow_html=True)


NAV = (("Overview", "ov-overview", '<rect x="3" y="3" width="6" height="6" rx="1"/><rect x="11" y="3" width="6" '
        'height="6" rx="1"/><rect x="3" y="11" width="6" height="6" rx="1"/><rect x="11" y="11" width="6" height="6" rx="1"/>'),
       ("Performance", "ov-performance", '<path d="M3 16h14M4 13l4-4 3 3 5-6"/>'),
       ("Dividend", "ov-dividend", '<circle cx="10" cy="10" r="7"/><path d="M12.5 7.5c-.5-.8-1.4-1.2-2.5-1.2-1.4 0-2.4.8'
        '-2.4 1.8 0 2.4 5 1.2 5 3.7 0 1-1 1.8-2.6 1.8-1.2 0-2.2-.5-2.7-1.3M10 5v1.3M10 13.7V15"/>'),
       ("Balance sheet", "ov-balance", '<path d="M3 8h14M4 8v8M8 8v8M12 8v8M16 8v8M3 16h14M10 3l7 4H3z"/>'),
       ("Sources", "ov-source", '<path d="M6 3h6l3 3v11H6z"/><path d="M12 3v3h3M8 10h5M8 13h5"/>'))


def _icon(paths: str) -> str:
    return (f'<svg viewBox="0 0 20 20" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" '
            f'stroke-linejoin="round" aria-hidden="true">{paths}</svg>')


def render_page_shell(data: CompanyData, ov: Overview, active: str = "Overview"):
    """The page frame of Igor's design: a top bar with the product name, the left menu (links to the overview's
    sections) with the years covered, the breadcrumb, and the company's name as the title. Returns the top bar's
    right-hand column, where the caller puts the company picker. The menu goes in Streamlit's sidebar."""
    st.markdown(_style(), unsafe_allow_html=True)
    brand, inputs = st.columns([2, 1.2], vertical_alignment="center")
    brand.markdown('<div class="fs-ov-shell fs-ov-shell-bar"><span class="fs-ov-brand">'
                   '<svg width="28" height="24" viewBox="0 0 26 22" aria-hidden="true"><rect x="1" y="12" width="5" '
                   'height="10" rx="1" fill="currentColor"/><rect x="10" y="6" width="5" height="16" rx="1" '
                   'fill="currentColor"/><rect x="19" y="0" width="5" height="22" rx="1" fill="currentColor"/></svg>'
                   'Filing Scorecard</span><span class="fs-ov-sep"></span>'
                   '<span class="fs-ov-note" style="font-size:17px">Annual filing checks</span></div>',
                   unsafe_allow_html=True)
    nav = "".join(f'<a class="fs-ov-nav{" fs-ov-on" if label == active else ""}" href="#{anchor}">{_icon(paths)}'
                  f"<span>{_e(label)}</span></a>" for label, anchor, paths in NAV)
    st.sidebar.markdown(f'<div class="fs-ov-shell"><div class="fs-ov-nav-eyebrow">Company scorecard</div>{nav}'
                        f'<div class="fs-ov-coverage"><span class="fs-ov-nav-eyebrow" style="margin:0">Data coverage'
                        f'</span><b>{_e(ov.years_text)}</b></div></div>', unsafe_allow_html=True)
    year = f"FY{ov.fiscal_year}" if ov.fiscal_year else ""
    pill = f'<span class="fs-ov-pill">{_e(year)}</span>' if year else ""
    st.markdown(f'<div class="fs-ov-shell" id="ov-overview"><div class="fs-ov-crumbs"><span>Company scorecard</span>'
                f'<span>/</span><b>{_e(active)}</b></div><div class="fs-ov-title-row"><div>'
                f'<div class="fs-ov-title">{_e(data.name)}</div><div class="fs-ov-title-meta"><b>{_e(data.ticker)}</b>'
                f"&nbsp;&nbsp;/ Fiscal year ended {_e(ov.fiscal_year_end)} / USD</div></div>{pill}</div></div>",
                unsafe_allow_html=True)
    return inputs


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
    with left, st.container(border=True, height="stretch", key="ov_card_performance"):
        top, switch = st.columns([3, 1], vertical_alignment="top")
        unit = "USD billions" if ov.series.unit == "USD bn" else "USD millions"
        top.markdown('<span id="ov-performance"></span>' + _heading("Financial performance", f"Annual results / {unit}"),
                     unsafe_allow_html=True)
        view = switch.segmented_control("View", ["Chart", "Table"], default="Chart", key="overview_view",
                                        label_visibility="collapsed")
        colours = _series_colours()
        legend = "".join(f'<span><i style="border-color:{colours[i % len(colours)] or "currentColor"};'
                         f'{"border-top-style:dashed;" if DASHES.get(line.label) == "dash" else ""}"></i>'
                         f"{_e(line.label)}</span>" for i, line in enumerate(ov.series.lines))
        if view == "Table":
            st.markdown(_table(ov.series), unsafe_allow_html=True)
        else:
            st.markdown(f'<div class="fs-ov fs-ov-legend-line">{legend}</div>', unsafe_allow_html=True)
            st.plotly_chart(_chart(ov.series), theme="streamlit", config={"displayModeBar": False},
                            key="overview_chart")
    with right, st.container(border=True, height="stretch", key="ov_card_coverage"):
        st.markdown('<span id="ov-dividend"></span>' + _heading("Dividend coverage",
                    "Free cash flow as a share of dividends paid"), unsafe_allow_html=True)
        st.markdown(_coverage(ov.coverage), unsafe_allow_html=True)

    left, right = st.columns([1.62, 1], gap="medium")
    with left, st.container(border=True, height="stretch", key="ov_card_balance"):
        st.markdown('<span id="ov-balance"></span>' + _heading("Balance sheet"), unsafe_allow_html=True)
        st.markdown(f'<div class="fs-ov">{_rows(ov.balance)}</div>', unsafe_allow_html=True)
    with right, st.container(border=True, height="stretch", key="ov_card_filing"):
        f = ov.filing
        st.markdown('<span id="ov-source"></span>' + _heading("Filing details"), unsafe_allow_html=True)
        rows = (("Source", f"SEC Form {f.form}" if f.form != NA else NA), ("Filed", f.filed),
                ("Accession", f.accession), ("Data retrieved", f.retrieved))
        table = "".join(f"<tr><td class='fs-ov-plain'>{_e(k)}</td><td class='fs-ov-num' style='font-weight:400'>"
                        f"{_e(v)}</td></tr>" for k, v in rows)
        st.markdown(f'<div class="fs-ov"><table class="fs-ov-rows">{table}</table>'
                    f'<div class="fs-ov-note" style="margin-top:12px; font-size:15px">{f.metrics} metrics · '
                    f"{f.records} records on the Sources tab</div></div>", unsafe_allow_html=True)
    st.markdown('<div class="fs-ov fs-ov-foot"><span>Free cash flow = operating cash flow − capital expenditure.</span>'
                "<span>Figures rounded for display.</span></div>", unsafe_allow_html=True)
    return ov
