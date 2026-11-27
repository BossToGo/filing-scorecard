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
from src.overview import (NA, RADAR_ORDER, Charts, Comparison, Coverage, Figure, KeyFigure, MoneyFlow, Overview,
                          Payout, PriceCheck, Scorecard, Series, Split, charts, overview, radar_shape, scorecard)

KIND_WORDS = {"reported": "Reported", "derived": "Derived", "assumption": "Assumption", "missing": "Not available"}
ARROWS = {1: "▲", -1: "▼", 0: ""}
DASHES = {"Revenue": "solid", "Net income": "solid", "Free cash flow": "dash", "Cash and equivalents": "dot"}


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
table.fs-ov-rows td.fs-ov-num {{text-align:right; font-weight:600; white-space:nowrap}}
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
[class*="st-key-ov_card"] .js-plotly-plot .main-svg {{background:transparent !important}}
[class*="st-key-ov_card"] .js-plotly-plot .bg {{fill:transparent !important}}
.fs-ov-section {{display:flex; align-items:baseline; gap:18px; flex-wrap:wrap; border-top:1px solid var(--ov-line);
  margin:34px 0 4px; padding-top:22px; scroll-margin-top:72px}}
.fs-ov-section b {{font-family:Georgia, 'Times New Roman', serif; font-weight:400; font-size:36px; letter-spacing:-0.01em}}
.fs-ov-section span {{font-size:15px; color:var(--ov-muted)}}
.fs-ov-says {{font-size:16px; line-height:1.5; margin:4px 0 6px}}
.fs-ov-zones {{display:flex; gap:6px 22px; flex-wrap:wrap; font-size:14px; color:var(--ov-muted); margin:2px 0 8px}}
.fs-ov-zones span {{display:inline-flex; align-items:center; gap:8px}}
.fs-ov-zones i {{display:inline-block; width:14px; height:14px; border-radius:3px; background:var(--ov-accent)}}
details.fs-ov-more {{margin-top:6px; font-size:15px}}  details.fs-ov-more summary {{cursor:pointer; color:var(--ov-muted)}}
details.fs-ov-more table.fs-ov-rows {{font-size:15px; margin-top:8px}}
.fs-ov-legend-line i.fs-ov-square {{width:14px; height:14px; border:0; border-radius:3px; background:var(--ov-accent)}}
.fs-ov-zones b {{font-weight:600; color:inherit}}
.fs-ov-ring {{text-align:center; font-size:15px; color:var(--ov-muted); margin-top:-8px}}
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
    shifts = _label_shifts(series)
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
                               xshift=14, yshift=shifts.get(line.label, 0), font={"color": colour, "size": 15})
    grid = _option("borderColor")
    fig.add_vline(x=years[-1], line={"dash": "dot", "width": 1, "color": grid}) if years else None
    fig.update_layout(height=330, margin={"l": 0, "r": 64, "t": 10, "b": 0}, hovermode="x unified", font={"size": 14},
                      yaxis={"rangemode": "tozero", "gridcolor": grid, "griddash": "dot", "zeroline": False},
                      xaxis={"tickmode": "array", "tickvals": years, "showgrid": False})
    return fig


def _unit_words(series: Series) -> str:
    """The unit of one five-year chart in words, for its own card (each chart picks its own unit)."""
    return "USD billions" if series.unit == "USD bn" else "USD millions"


def _label_shifts(series: Series, height: int = 330, gap: int = 18) -> dict[str, int]:
    """Pixels to move each end label up or down so two lines ending close together do not write over each other
    (Nvidia's cash and debt). Layout only: the values themselves are not touched."""
    ends = sorted((line.values[-1], line.label) for line in series.lines if line.values and line.values[-1] is not None)
    known = [v for line in series.lines for v in line.values if v is not None]
    if len(ends) < 2 or not known:
        return {}
    top, bottom = max(known + [0.0]), min(known + [0.0])
    per_pixel = (top - bottom) / (height - 60) if top > bottom else 1.0
    placed, shifts = [], {}
    for value, label in ends:  # from the lowest up: each label at least `gap` pixels above the one below it
        y = value / per_pixel
        if placed and y - placed[-1] < gap:
            y = placed[-1] + gap
        placed.append(y)
        shifts[label] = round(y - value / per_pixel)
    return shifts


def _table(series: Series) -> str:
    head = "".join(f"<td class='fs-ov-num'>{year}</td>" for year in series.years)
    body = "".join(
        f"<tr><td>{_e(line.label)}</td>" + "".join(f"<td class='fs-ov-num'>{_e(t)}</td>" for t in line.texts) + "</tr>"
        for line in series.lines)
    return f'<div class="fs-ov"><table class="fs-ov-rows"><tr><td></td>{head}</tr>{body}</table></div>'


# --- the charts of S10d (Igor, 26 November): drawn from `src.overview.charts`, nothing computed here -------------
# Colours: the theme's accent and text colour, and tints of them mixed with the panel colour (never a colour of
# our own, tests/app/test_theme.py). The company's own bar or part is the accent; benchmarks and costs are grey.

PROFIT_NODES = ("Revenue", "Gross profit", "Operating income", "Net income", "Other income, net")
ZONE_WEIGHT = {"80% of the estimate or less": ("accent", 0.34), "80% to 100% of the estimate": ("accent", 0.16),
               "Below the estimate": ("accent", 0.24), "Above the estimate": ("text", 0.07)}
PART_WEIGHT = (1.0, 0.72, 0.5, 0.34, 0.22)  # tints of the accent for the balance sheet blocks, largest first
CHART_CONFIG = {"displayModeBar": False}


def _mix(colour: str | None, weight: float) -> str | None:
    """`weight` of a theme colour on the theme's panel colour (1 is the colour itself), for lighter tints that
    still follow the theme file."""
    base = _option("secondaryBackgroundColor") or _option("backgroundColor")
    try:
        a = [int(colour[i:i + 2], 16) for i in (1, 3, 5)]
        b = [int(base[i:i + 2], 16) for i in (1, 3, 5)]
    except (TypeError, ValueError, IndexError):
        return colour
    return "#" + "".join(f"{round(x * weight + y * (1 - weight)):02x}" for x, y in zip(a, b))


def _ink() -> tuple[str | None, str | None]:
    return _pass_colour(), _option("textColor")


def _plain(fig: go.Figure, height: int, **layout) -> go.Figure:
    fig.update_layout(height=height, showlegend=False, font={"size": 13}, **layout)
    return fig


def _says(text: str, note: str = "") -> str:
    extra = f'<div class="fs-ov-note">{_e(note)}</div>' if note else ""
    return f'<div class="fs-ov"><p class="fs-ov-says">{_e(text)}</p>{extra}</div>'


def _figures(rows) -> str:
    """The chart's figures as a table, folded under it (the text alternative of every chart)."""
    body = "".join(f"<tr><td>{_e(label)}</td><td class='fs-ov-num'>{_e(text)}</td></tr>" for label, text in rows)
    return (f'<div class="fs-ov"><details class="fs-ov-more"><summary>Figures</summary>'
            f'<table class="fs-ov-rows">{body}</table></details></div>')


def _price_chart(price: PriceCheck) -> go.Figure:
    accent, text = _ink()
    fig = go.Figure()
    for label, start, end in price.zones:
        fig.add_shape(type="rect", x0=start, x1=end, y0=0, y1=1, yref="paper", layer="below", line={"width": 0},
                      fillcolor=_zone_colour(label))
    bars = list(reversed(price.bars))  # the share price on top
    fig.add_trace(go.Bar(orientation="h", y=[b.label for b in bars], x=[b.value for b in bars], width=0.44,
                         text=[b.text for b in bars], textposition="auto", cliponaxis=False,  # inside if no room
                         textfont={"size": 15}, marker={"color": [accent if b.label == "Estimate" else text
                                                                   for b in bars]},
                         hovertemplate="%{y}: %{text}<extra></extra>"))
    for mark in price.marks:
        fig.add_vline(x=mark.value, line={"dash": "dot", "width": 2, "color": text},
                      annotation_text=f"{mark.label}: {mark.text}", annotation_position="top",
                      annotation_font_size=12)
    return _plain(fig, 240, margin={"l": 0, "r": 16, "t": 30, "b": 0}, bargap=0.3,
                  xaxis={"range": [0, price.axis_max], "tickprefix": "USD ", "showgrid": False, "zeroline": False},
                  yaxis={"showgrid": False, "ticksuffix": "  "})


def _zone_colour(label: str) -> str | None:
    accent, text = _ink()
    role, weight = ZONE_WEIGHT.get(label, ("text", 0.07))
    return _mix(accent if role == "accent" else text, weight)


def _zones(price: PriceCheck) -> str:
    items = "".join(f'<span><i style="background:{_zone_colour(label)}"></i>{_e(label)}</span>'
                    for label, _, _ in price.zones)
    return f'<div class="fs-ov fs-ov-zones">{items}</div>'


def _compare_chart(comparison: Comparison) -> go.Figure:
    accent, text = _ink()
    bars = [b for b in comparison.bars if b.value is not None]
    first = bars[0].label if bars else ""
    bars.reverse()  # the company (or short-term assets) on top
    top = max([abs(b.value) for b in bars] or [1.0])
    fig = go.Figure(go.Bar(orientation="h", y=[b.label for b in bars], x=[b.value for b in bars], width=0.56,
                           text=[b.text for b in bars], textposition="outside", cliponaxis=False,
                           textfont={"size": 14},
                           marker={"color": [accent if b.label == first else _mix(text, 0.32) for b in bars]},
                           hovertemplate="%{y}: %{text}<extra></extra>"))
    return _plain(fig, 70 + 48 * len(bars), margin={"l": 0, "r": 16, "t": 6, "b": 0}, bargap=0.25,
                  xaxis={"range": [min(0, min(b.value for b in bars)) * 1.7, top * 1.7], "visible": False},
                  yaxis={"showgrid": False, "ticksuffix": "  "})


def _flow_chart(flow: MoneyFlow) -> go.Figure:
    accent, text = _ink()
    labels = [label for label, _ in flow.nodes]
    index = {label: i for i, label in enumerate(labels)}
    grey = _mix(text, 0.42)
    depth = {"Revenue": 0}
    for _ in flow.flows:  # a step's column is one more than the column of the step it comes from
        for f in flow.flows:
            if f.source in depth:
                depth[f.target] = max(depth.get(f.target, 0), depth[f.source] + 1)
    for f in flow.flows:  # "Other income, net" comes from outside: one column before net income
        depth.setdefault(f.source, depth.get(f.target, 1) - 1)
    last = max(depth.values()) or 1
    x = [min(max(depth[label] / last, 0.001), 0.999) for label in labels]
    main = [label for label in PROFIT_NODES if label != "Other income, net"]
    y = [0.45 if label == "Revenue" else 0.3 if label in main else 0.88 for label in labels]  # costs branch off below
    fig = go.Figure(go.Sankey(
        arrangement="snap",
        node={"label": [f"{label}<br>{amount}" for label, amount in flow.nodes], "pad": 26, "thickness": 14,
              "x": x, "y": y,
              "color": [accent if label in PROFIT_NODES else grey for label in labels], "line": {"width": 0},
              "hovertemplate": "%{label}<extra></extra>"},
        link={"source": [index[f.source] for f in flow.flows], "target": [index[f.target] for f in flow.flows],
              "value": [f.value for f in flow.flows], "customdata": [f.text for f in flow.flows],
              "color": [_mix(accent, 0.22) if f.target in PROFIT_NODES else _mix(text, 0.12) for f in flow.flows],
              "hovertemplate": "%{customdata}<extra></extra>"},
        textfont={"size": 13}))
    return _plain(fig, 360, margin={"l": 4, "r": 4, "t": 8, "b": 8})


def _split_chart(split: Split) -> go.Figure:
    """The balance sheet as two block charts side by side: what the company owns (assets) and what it owes plus the
    shareholders' part (liabilities and equity). Each block's area is its amount, largest first, labelled with its
    name, amount and share of total assets. Owned parts in tints of the accent, owed parts in greys (never red or
    green); negative equity is not a block, the sentence under the chart says it."""
    fig = go.Figure()
    panel = _mix(_option("textColor"), 0)
    sides = (("assets", "Assets", split.total, split.assets, [0.0, 0.485]),
             ("claims", split.claims_title, split.claims_total, split.claims, [0.515, 1.0]))
    for side, title, total, parts, x in sides:
        if not parts:
            continue
        colours = _block_colours(parts, owed=side == "claims")
        fig.add_trace(go.Treemap(
            ids=[side] + [f"{side}/{p.label}" for p in parts], parents=[""] + [side] * len(parts),
            labels=[f"{title} · {total}"] + [p.label for p in parts],  # the header shows the column's total
            values=[sum(p.value for p in parts)] + [p.value for p in parts],
            branchvalues="total", sort=True, domain={"x": x, "y": [0, 1]},
            text=[f"<b>{_e(title)}</b>  {_e(total)}"] + [f"<b>{_wrap(p.label)}</b><br>{_e(p.text)} · {_e(p.share)}"
                                                           for p in parts],
            texttemplate="%{text}", textposition="top left", textfont={"size": 13},
            customdata=[f"{title}: {total}"] + [f"{p.label}: {p.text} ({p.share} of total assets)" for p in parts],
            hovertemplate="%{customdata}<extra></extra>",
            marker={"colors": [panel] + colours, "line": {"width": 3, "color": panel},
                    "pad": {"t": 30, "l": 0, "r": 0, "b": 0}},
            tiling={"pad": 3}, pathbar={"visible": False}))
    return _plain(fig, 380, margin={"l": 0, "r": 0, "t": 4, "b": 0}, uniformtext={"minsize": 10, "mode": "hide"})


def _wrap(label: str, width: int = 16) -> str:
    """A block's name on short lines ("Property, plant<br>and equipment"), so it fits a narrow block."""
    lines, line = [], ""
    for word in label.split():
        if line and len(line) + 1 + len(word) > width:
            lines.append(line)
            line = word
        else:
            line = f"{line} {word}".strip()
    return "<br>".join(_e(part) for part in lines + [line])


def _split_legend(split: Split) -> str:
    """Every block's colour, name, amount and share under the chart, for the blocks too small to carry them."""
    rows = []
    for title, parts, owed in (("Assets", split.assets, False), (split.claims_title, split.claims, True)):
        items = "".join(f'<span><i style="background:{colour}"></i>{_e(part.label)} {_e(part.text)} · '
                        f"{_e(part.share)}</span>" for part, colour in zip(parts, _block_colours(parts, owed)))
        rows.append(f'<div class="fs-ov-zones"><b>{_e(title)}</b>{items}</div>')
    return '<div class="fs-ov">' + "".join(rows) + "</div>"


def _block_colours(parts, owed: bool) -> list[str | None]:
    """Largest first: owned parts (assets, equity) in tints of the accent, owed parts (liabilities) in greys."""
    accent, text = _ink()
    order = {p.label: rank for rank, p in enumerate(sorted(parts, key=lambda p: -p.value))}
    colours = []
    for part in parts:
        rank = min(order[part.label], len(PART_WEIGHT) - 1)
        if owed and not part.label.startswith("Equity"):
            colours.append(_mix(text, (0.55, 0.4, 0.28, 0.2, 0.14)[rank]))
        else:
            colours.append(_mix(accent, 0.62 if owed else PART_WEIGHT[rank]))
    return colours


def _dividend_chart(series: Series) -> go.Figure:
    accent, text = _ink()
    lines = {line.label: line for line in series.lines}
    years = list(series.years)
    fig = go.Figure()
    paid, fcf = lines.get("Dividends paid"), lines.get("Free cash flow")
    if paid is not None:
        fig.add_trace(go.Bar(x=years, y=list(paid.values), name=paid.label, marker={"color": accent}, width=0.5,
                             customdata=list(paid.texts), hovertemplate="%{x}: %{customdata}<extra>Dividends paid</extra>"))
    if fcf is not None:
        fig.add_trace(go.Scatter(x=years, y=list(fcf.values), name=fcf.label, mode="lines+markers",
                                 line={"color": text, "width": 3, "dash": "dash"}, marker={"size": 9},
                                 customdata=list(fcf.texts), connectgaps=False,
                                 hovertemplate="%{x}: %{customdata}<extra>Free cash flow</extra>"))
    grid = _option("borderColor")
    return _plain(fig, 300, margin={"l": 0, "r": 10, "t": 10, "b": 0}, hovermode="x unified",
                  yaxis={"rangemode": "tozero", "gridcolor": grid, "griddash": "dot", "zeroline": False},
                  xaxis={"tickmode": "array", "tickvals": years, "showgrid": False})


def _ring(payout: Payout) -> go.Figure:
    accent, text = _ink()
    share = payout.share or 0.0
    fig = go.Figure(go.Pie(values=[share, 1 - share], hole=0.74, sort=False, direction="clockwise", rotation=0,
                           marker={"colors": [accent, _mix(text, 0.12)]}, textinfo="none", hoverinfo="skip"))
    fig.add_annotation(text=f"<b>{payout.percent}</b>", showarrow=False, font={"size": 30, "color": text})
    return _plain(fig, 230, margin={"l": 0, "r": 0, "t": 6, "b": 6})


LINE_STYLES = {"dash": "border-top-style:dashed;", "dot": "border-top-style:dotted;"}


def _legend(series: Series) -> str:
    """The line legend above a five-year chart: each line's colour and dash, as `_chart` draws it."""
    colours = _series_colours()
    items = "".join(f'<span><i style="border-color:{colours[i % len(colours)] or "currentColor"};'
                    f'{LINE_STYLES.get(DASHES.get(line.label, ""), "")}"></i>{_e(line.label)}</span>'
                    for i, line in enumerate(series.lines))
    return f'<div class="fs-ov fs-ov-legend-line">{items}</div>'


def _section(title: str, anchor: str, sub: str = "") -> None:
    st.markdown(f'<div class="fs-ov fs-ov-section" id="{anchor}"><b>{_e(title)}</b><span>{_e(sub)}</span></div>',
                unsafe_allow_html=True)


def _card(key: str, title: str, sub: str = "", stretch: bool = True):
    """A bordered card with its heading; `stretch` makes it as tall as its neighbour in a row."""
    box = st.container(border=True, height="stretch" if stretch else "content", key=f"ov_card_{key}")
    box.markdown(_heading(title, sub, sans=True), unsafe_allow_html=True)
    return box


def _comparison_card(key: str, comparison: Comparison | None, sub: str, stretch: bool = True) -> None:
    if comparison is None:
        return
    with _card(key, comparison.title, sub, stretch):
        if comparison.status == "ok":
            st.plotly_chart(_compare_chart(comparison), theme="streamlit", config=CHART_CONFIG, key=f"chart_{key}")
        st.markdown(_says(comparison.text), unsafe_allow_html=True)
        if comparison.bars:
            st.markdown(_figures((b.label, b.text if not b.note else f"{b.text} ({b.note})") for b in comparison.bars),
                        unsafe_allow_html=True)


def render_valuation(ch: Charts) -> None:
    """The share price against the estimate and the price ratios, at the top of the page (Igor, 26 November: "this
    is what our whole pitch is to the bank"). The numbers are V1 to V6's own, so the chart and the checks agree."""
    if ch.price is None:
        return
    _section("Valuation", "ov-valuation", "The estimate per share from the company's cash flows, and its price ratios")
    with _card("price", "Share price against the estimate", "USD per share"):
        if ch.price.status == "ok":
            st.markdown(_zones(ch.price), unsafe_allow_html=True)
            st.plotly_chart(_price_chart(ch.price), theme="streamlit", config=CHART_CONFIG, key="chart_price")
        st.markdown(_says(ch.price.text), unsafe_allow_html=True)
        if ch.price.bars:
            rows = [(b.label, b.text) for b in ch.price.bars + ch.price.marks]
            st.markdown(_figures(rows), unsafe_allow_html=True)
    for column, key, comparison in zip(st.columns(2, gap="medium"), ("ratio_pe", "ratio_pb"), ch.ratios):
        with column:
            _comparison_card(key, comparison, "Against the industry and the US market" if key == "ratio_pe"
                             else "Against the industry")


def _folded_table(series: Series) -> str:
    """A five-year chart's figures as a table, folded under it."""
    return f'<div class="fs-ov"><details class="fs-ov-more"><summary>Figures</summary>{_table(series)}</details></div>'


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
                  f"<br><span style='font-size:11px'>{areas[k].short_text}</span>"  # "2 passed of 6 assessed"
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
    fig.update_layout(
        height=430, margin={"l": 118, "r": 118, "t": 74, "b": 74}, showlegend=False, font={"size": 13},
        polar={"gridshape": "linear",
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
       ("Valuation", "ov-valuation", '<path d="M3 10l7-7h7v7l-7 7z"/><circle cx="13.5" cy="6.5" r="1.2"/>'),
       ("Past performance", "ov-performance", '<path d="M3 16h14M4 13l4-4 3 3 5-6"/>'),
       ("Financial health", "ov-health", '<path d="M3 8h14M4 8v8M8 8v8M12 8v8M16 8v8M3 16h14M10 3l7 4H3z"/>'),
       ("Dividend", "ov-dividend", '<circle cx="10" cy="10" r="7"/><path d="M12.5 7.5c-.5-.8-1.4-1.2-2.5-1.2-1.4 0-2.4.8'
        '-2.4 1.8 0 2.4 5 1.2 5 3.7 0 1-1 1.8-2.6 1.8-1.2 0-2.2-.5-2.7-1.3M10 5v1.3M10 13.7V15"/>'),
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
    `ui.results.check_results` returns them), the valuation comes first, then the radar of the four areas; then one
    section per area of the main screen, each with its charts (S10d, Igor, 26 November)."""
    ov = overview(data)
    ch = charts(data, results)
    st.markdown(_style(), unsafe_allow_html=True)
    if results is not None:
        render_valuation(ch)
        render_scorecard_panel(scorecard(results), ov.fiscal_year)
    if ov.key_figures:
        strip = "".join(_key_figure(f) for f in ov.key_figures)
        st.markdown(f'<div class="fs-ov"><div class="fs-ov-kpis">{strip}</div></div>', unsafe_allow_html=True)
    unit = _unit_words(ov.series)
    year = f"FY{ov.fiscal_year}" if ov.fiscal_year else ""

    _section("Past performance", "ov-performance", "Five years of results, and where the latest revenue went")
    with st.container(border=True, key="ov_card_performance"):
        top, switch = st.columns([5, 1], vertical_alignment="top")
        top.markdown(_heading("Financial performance", f"Annual results / {unit}", sans=True), unsafe_allow_html=True)
        view = switch.segmented_control("View", ["Chart", "Table"], default="Chart", key="overview_view",
                                        label_visibility="collapsed")
        if view == "Table":
            st.markdown(_table(ov.series), unsafe_allow_html=True)
        else:
            st.markdown(_legend(ov.series), unsafe_allow_html=True)
            st.plotly_chart(_chart(ov.series), theme="streamlit", config=CHART_CONFIG, key="overview_chart")
    with _card("flow", "Where the revenue goes", f"{year} / from revenue to net income", stretch=False):
        flow = ch.money_flow
        if flow.status == "ok":
            st.plotly_chart(_flow_chart(flow), theme="streamlit", config=CHART_CONFIG, key="chart_flow")
        st.markdown(_says(flow.text, flow.note), unsafe_allow_html=True)
        if flow.flows:
            st.markdown(_figures(flow.nodes), unsafe_allow_html=True)

    _section("Financial health", "ov-health", "What the company owns and owes")
    left, right = st.columns([1.62, 1], gap="medium")
    with left:
        with _card("split", "Balance sheet", f"On {ov.fiscal_year_end} / what it owns against what it owes",
                   stretch=False):
            split = ch.split
            if split.status == "ok":
                st.plotly_chart(_split_chart(split), theme="streamlit", config=CHART_CONFIG, key="chart_split")
                st.markdown(_split_legend(split), unsafe_allow_html=True)
            st.markdown(_says(split.text, split.note), unsafe_allow_html=True)
            if split.assets or split.claims:
                st.markdown(_figures([("Total assets", split.total)] +
                                     [(p.label, f"{p.text} · {p.share}") for p in split.assets + split.claims]),
                            unsafe_allow_html=True)
        with _card("debt", "Debt, equity and cash", f"Five years / {_unit_words(ch.debt_history)}", stretch=False):
            st.markdown(_legend(ch.debt_history), unsafe_allow_html=True)
            st.plotly_chart(_chart(ch.debt_history), theme="streamlit", config=CHART_CONFIG, key="chart_debt")
            st.markdown(_says(ch.debt_text), unsafe_allow_html=True)
            st.markdown(_folded_table(ch.debt_history), unsafe_allow_html=True)
    with right:
        _comparison_card("position", ch.position, "Short-term assets against liabilities", stretch=False)
        with st.container(border=True, key="ov_card_balance"):
            st.markdown(_heading("Key balance sheet figures", sans=True), unsafe_allow_html=True)
            st.markdown(f'<div class="fs-ov">{_rows(ov.balance)}</div>', unsafe_allow_html=True)

    _section("Dividend", "ov-dividend", "What the company paid out, and whether its cash covered it")
    left, right = st.columns([1.62, 1], gap="medium")
    with left:
        with _card("dividends", "Dividends and free cash flow", f"Five years / {_unit_words(ch.dividend_history)}",
                   stretch=False):
            st.markdown('<div class="fs-ov fs-ov-legend-line"><span><i class="fs-ov-square"></i>Dividends paid</span>'
                        '<span><i style="border-top-style:dashed"></i>Free cash flow</span></div>',
                        unsafe_allow_html=True)
            st.plotly_chart(_dividend_chart(ch.dividend_history), theme="streamlit", config=CHART_CONFIG,
                            key="chart_dividends")
            st.markdown(_says(ch.dividend_text), unsafe_allow_html=True)
            st.markdown(_folded_table(ch.dividend_history), unsafe_allow_html=True)
        _comparison_card("yield", ch.dividend_yield, "Against the US market", stretch=False)
    with right:
        with st.container(border=True, key="ov_card_coverage"):
            st.markdown(_heading("Dividend coverage", "Free cash flow as a share of dividends paid", sans=True),
                        unsafe_allow_html=True)
            st.markdown(_coverage(ov.coverage), unsafe_allow_html=True)
        with _card("payout", "Earnings payout", "Dividends paid as a share of net income", stretch=False):
            if ch.payout.status == "ok":
                st.plotly_chart(_ring(ch.payout), theme="streamlit", config=CHART_CONFIG, key="chart_payout")
            st.markdown(_says(ch.payout.text), unsafe_allow_html=True)

    with st.container(border=True, key="ov_card_filing"):
        f = ov.filing
        st.markdown('<span id="ov-source"></span>' + _heading("Filing details", sans=True), unsafe_allow_html=True)
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
