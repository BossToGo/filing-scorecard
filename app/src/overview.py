"""The overview above the tabs (slice S10c). Owner: A.

    from src.overview import overview
    ov = overview(data)        # key figures, five-year series, dividend coverage, balance sheet, filing details

Every number the overview shows is worked out and written here, so the screen (`ui/overview.py`) only lays it out
(SPEC §11: the interface computes and rounds nothing). Rules and expected values: docs/acceptance.md, "Overview
(S10c)". A missing figure is never zero: it gives "n/a" with the reason in `note`.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from decimal import ROUND_HALF_UP, Decimal

from src.contracts import CheckResult, CompanyData, Fact
from src.scores import area_score, dividend_note

BILLION, MILLION = 1e9, 1e6
MINUS = "−"
NA = "n/a"
NOT_MEANINGFUL = "not meaningful"


@dataclass(frozen=True)
class Figure:
    """One figure as shown: `before` `number` `after` ("USD", "47.94", "bn"), with its kind and any reason."""

    label: str
    number: str
    before: str = ""
    after: str = ""
    kind: str = "reported"  # reported, derived, assumption or missing (as in src.contracts)
    note: str = ""

    @property
    def text(self) -> str:
        if self.number == NA:
            return NA
        return f"{self.before} {self.number}".strip() + (self.after if self.after in ("%", "×") else f" {self.after}")


@dataclass(frozen=True)
class KeyFigure(Figure):
    change: str = NA  # "+1.9%", "+7.5 pp", "not meaningful" or "n/a"
    direction: int | None = None  # 1 up, -1 down, 0 unchanged, None when there is no change to show
    versus: str = ""  # "vs FY2024"


@dataclass(frozen=True)
class Line:
    label: str
    values: tuple[float | None, ...]  # in the series' unit, for the chart; None is a gap, never zero
    texts: tuple[str, ...]  # the same values written for the table view
    end_label: str = ""  # the last value in the series' unit, two decimals, written at the end of the line


@dataclass(frozen=True)
class Series:
    years: tuple[int, ...]
    unit: str  # "USD bn" or "USD m"
    lines: tuple[Line, ...]


@dataclass(frozen=True)
class Coverage:
    status: str  # covered, not_covered, negative, no_dividend or missing
    text: str  # the sentence shown when there is no percentage
    percent: str | None = None  # "60.3%"
    share: float | None = None  # free cash flow ÷ dividends for the bar, between 0 and 1
    bar_width: str = "0.0"  # the same share in percent for the bar's width, so the screen computes nothing
    free_cash_flow: str = NA
    dividends: str = NA
    gap: str = ""  # "USD 3.48 bn"
    gap_label: str = ""  # "Dividends above free cash flow" or "Free cash flow above dividends"
    note: str = ""


@dataclass(frozen=True)
class Filing:
    form: str
    filed: str
    accession: str
    retrieved: str
    metrics: int
    records: int


@dataclass(frozen=True)
class Overview:
    fiscal_year: int | None
    key_figures: tuple[KeyFigure, ...]
    series: Series
    coverage: Coverage
    balance: tuple[Figure, ...]
    filing: Filing
    fiscal_year_end: str = NA  # "31 December 2025"
    years_text: str = NA  # "FY2021 – FY2025", the years the overview covers


# --- writing numbers --------------------------------------------------------------------------------------------


def _signed(number: str) -> str:
    return number.replace("-", MINUS)


def _fixed(number: float, places: int) -> str:
    """`number` with `places` decimals and thousands commas, a half rounded away from zero as by hand: 34.275 gives
    "34.28" (Python's own format gives "34.27", because 34.275 is stored as 34.27499…; S10d hand working)."""
    exact = Decimal(repr(number)).quantize(Decimal(1).scaleb(-places), rounding=ROUND_HALF_UP)
    return f"{exact:,.{places}f}"


def amount_parts(value: float) -> tuple[str, str, str]:
    """USD 1 bn or more in USD bn with two decimals, smaller amounts in USD m with none."""
    if abs(value) >= BILLION:
        return "USD", _signed(_fixed(value / BILLION, 2)), "bn"
    return "USD", _signed(_fixed(value / MILLION, 0)), "m"


def amount_text(value: float) -> str:
    before, number, after = amount_parts(value)
    return f"{before} {number} {after}"


def _year(day: date) -> str:
    return f"FY{day.year}"


def _day(day: date) -> str:
    return f"{day.day} {day:%B %Y}"


# --- reading figures --------------------------------------------------------------------------------------------


def _value(data: CompanyData, metric: str, fy_end: date) -> tuple[float | None, str]:
    """The figure's value, or None with the reason it can't be used."""
    fact: Fact | None = data.fact(metric, fy_end)
    name = metric.replace("_", " ")
    if fact is None:
        return None, f"no {name} for {_year(fy_end)} in the data"
    if fact.kind == "missing" or fact.value is None:
        return None, f"{name} for {_year(fy_end)}: {fact.note or 'not in the filing'}"
    return fact.value, ""


def _kind(data: CompanyData, metric: str, fy_end: date) -> str:
    fact = data.fact(metric, fy_end)
    return fact.kind if fact is not None else "missing"


def _free_cash_flow(data: CompanyData, fy_end: date) -> tuple[float | None, str]:
    """Operating cash flow − capital expenditure (SPEC §8, D6). Capital expenditure is filed as a positive amount."""
    ocf, why = _value(data, "operating_cash_flow", fy_end)
    if ocf is None:
        return None, why
    capex, why = _value(data, "capital_expenditure", fy_end)
    if capex is None:
        return None, why
    if capex < 0:
        return None, f"capital expenditure for {_year(fy_end)} is filed as a negative amount (a sign error)"
    return ocf - capex, ""


def _margin(data: CompanyData, fy_end: date) -> tuple[float | None, str]:
    income, why = _value(data, "operating_income", fy_end)
    if income is None:
        return None, why
    revenue, why = _value(data, "revenue", fy_end)
    if revenue is None:
        return None, why
    if revenue <= 0:
        return None, f"revenue for {_year(fy_end)} is at or below zero"
    return income / revenue, ""


# --- the parts of the overview ----------------------------------------------------------------------------------


def _change(now: float | None, before: float | None, before_why: str, fy_prior: date | None, *,
            margin: bool = False, loss: str = "a loss") -> tuple[str, int | None, str]:
    if now is None:
        return NA, None, ""
    if fy_prior is None:
        return NA, None, "no earlier fiscal year in the data"
    if before is None:
        return NA, None, before_why
    if margin:
        points = round((now - before) * 100, 1)
        return _signed(f"{points:+.1f} pp"), (points > 0) - (points < 0), ""
    if before <= 0:
        return NOT_MEANINGFUL, None, f"{_year(fy_prior)} was {loss}, so a change in percent is not meaningful"
    percent = round((now / before - 1) * 100, 1)
    return _signed(f"{percent:+.1f}%"), (percent > 0) - (percent < 0), ""


def _key_figure(label: str, now: float | None, now_why: str, kind: str, before: float | None, before_why: str,
                fy_prior: date | None, *, margin: bool = False, loss: str = "a loss") -> KeyFigure:
    versus = f"vs {_year(fy_prior)}" if fy_prior else ""
    change, direction, change_why = _change(now, before, before_why, fy_prior, margin=margin, loss=loss)
    if now is None:
        return KeyFigure(label, NA, kind="missing", note=now_why, versus=versus)
    if margin:
        before_text, number, after = "", f"{now * 100:.1f}", "%"
    else:
        before_text, number, after = amount_parts(now)
    return KeyFigure(label, number, before_text, after, kind, change_why, change, direction, versus)


def _key_figures(data: CompanyData, fy0: date, fy1: date | None) -> tuple[KeyFigure, ...]:
    def reported(metric: str, label: str, loss: str) -> KeyFigure:
        now, why = _value(data, metric, fy0)
        before, before_why = _value(data, metric, fy1) if fy1 else (None, "")
        return _key_figure(label, now, why, _kind(data, metric, fy0), before, before_why, fy1, loss=loss)

    margin, margin_why = _margin(data, fy0)
    margin_before, margin_before_why = _margin(data, fy1) if fy1 else (None, "")
    fcf, fcf_why = _free_cash_flow(data, fy0)
    fcf_before, fcf_before_why = _free_cash_flow(data, fy1) if fy1 else (None, "")
    return (
        reported("revenue", "Revenue", "at or below zero"),
        _key_figure("Operating margin", margin, margin_why, "derived", margin_before, margin_before_why, fy1,
                    margin=True),
        reported("net_income", "Net income", "a loss"),
        _key_figure("Free cash flow", fcf, fcf_why, "derived", fcf_before, fcf_before_why, fy1,
                    loss="negative free cash flow"),
    )


def _series(data: CompanyData, years: list[date]) -> Series:
    return _lines({
        "Revenue": [_value(data, "revenue", end)[0] for end in years],
        "Net income": [_value(data, "net_income", end)[0] for end in years],
        "Free cash flow": [_free_cash_flow(data, end)[0] for end in years],
    }, years)


def _lines(columns: dict[str, list[float | None]], years: list[date]) -> Series:
    """Five-year lines in one unit (USD bn when any amount reaches 1 bn), each value also written for the table."""
    known = [abs(v) for values in columns.values() for v in values if v is not None]
    scale, unit = (BILLION, "USD bn") if known and max(known) >= BILLION else (MILLION, "USD m")
    lines = tuple(
        Line(label, tuple(None if v is None else v / scale for v in values),
             tuple(NA if v is None else amount_text(v) for v in values),
             "" if values[-1] is None else _signed(_fixed(values[-1] / scale, 2)))
        for label, values in columns.items()
    )
    return Series(tuple(end.year for end in years), unit, lines)


def _coverage(data: CompanyData, fy0: date) -> Coverage:
    fcf, fcf_why = _free_cash_flow(data, fy0)
    dividends, div_why = _value(data, "dividends_paid", fy0)
    fcf_text = NA if fcf is None else amount_text(fcf)
    if dividends is not None and dividends < 0:  # a payment is filed as a positive amount: a sign error, as in D1
        return Coverage("missing", "Dividend coverage is not available", free_cash_flow=fcf_text,
                        dividends=amount_text(dividends),
                        note=f"dividends paid for {_year(fy0)} are filed as a negative amount, which is read as a "
                             "sign error, never as no dividend")
    if dividends is not None and dividends == 0:  # treated as nil (SPEC §7, plan Q1) or reported as zero
        # plain words for the reader; the tags searched stay in the fact's note, on the Sources tab
        note = f"No dividends paid in {_year(fy0)}. The Sources tab shows how this was read."
        return Coverage("no_dividend", "No dividend paid", free_cash_flow=fcf_text, note=note)
    if dividends is None or fcf is None:
        return Coverage("missing", "Dividend coverage is not available", free_cash_flow=fcf_text,
                        dividends=NA if dividends is None else amount_text(dividends), note=div_why or fcf_why)
    div_text = amount_text(dividends)
    if fcf < 0:
        return Coverage("negative", "Free cash flow was negative", share=0.0, free_cash_flow=fcf_text,
                        dividends=div_text, gap=amount_text(dividends - fcf), gap_label="Dividends above free cash flow")
    ratio = fcf / dividends
    covered = fcf >= dividends
    if fcf == dividends:
        gap_label = "Free cash flow equals the dividends"
    else:
        gap_label = "Free cash flow above dividends" if covered else "Dividends above free cash flow"
    return Coverage(
        "covered" if covered else "not_covered",
        "Free cash flow covers the dividends" if covered else "Free cash flow does not cover the dividends",
        percent=f"{ratio * 100:,.1f}%",  # "9,925.7%", not "9925.7%" (Nvidia)
        share=min(ratio, 1.0),
        bar_width=f"{min(ratio, 1.0) * 100:.1f}",
        free_cash_flow=fcf_text,
        dividends=div_text,
        gap=amount_text(abs(fcf - dividends)),
        gap_label=gap_label,
    )


def _balance(data: CompanyData, fy0: date) -> tuple[Figure, ...]:
    rows = []
    for metric, label in (("cash", "Cash and equivalents"), ("financial_debt", "Financial debt"),
                          ("total_assets", "Total assets")):
        value, why = _value(data, metric, fy0)
        if value is None:
            rows.append(Figure(label, NA, kind="missing", note=why))
        else:
            before, number, after = amount_parts(value)
            rows.append(Figure(label, number, before, after, kind=_kind(data, metric, fy0)))
    assets, why_a = _value(data, "current_assets", fy0)
    liabilities, why_l = _value(data, "current_liabilities", fy0)
    if assets is None or liabilities is None:
        rows.append(Figure("Current ratio", NA, kind="missing", note=why_a or why_l))
    elif liabilities <= 0:
        rows.append(Figure("Current ratio", NA, kind="missing",
                           note=f"current liabilities for {_year(fy0)} are at or below zero"))
    else:
        rows.append(Figure("Current ratio", f"{assets / liabilities:.2f}", after="×", kind="derived"))
    return tuple(rows)


def _filing(data: CompanyData, fy0: date) -> Filing:
    revenue = data.fact("revenue", fy0)
    retrieved = data.retrieved
    return Filing(
        form=(revenue.form if revenue is not None and revenue.form else NA),
        filed=_day(data.latest_10k_filed) if data.latest_10k_filed else NA,
        accession=(revenue.accession if revenue is not None and revenue.accession else NA),
        retrieved=f"{_day(retrieved)}, {retrieved:%H:%M} UTC" if retrieved else NA,
        metrics=len(data.items),
        records=sum(len(by_year) for by_year in data.items.values()),
    )


def overview(data: CompanyData) -> Overview:
    years = data.fiscal_years("revenue") or data.fiscal_years("net_income")
    if not years:
        empty = Series((), "USD m", ())
        return Overview(None, (), empty, Coverage("missing", "Dividend coverage is not available"), (),
                        _filing(data, date.min))
    last_five = years[-5:]
    fy0 = last_five[-1]
    fy1 = last_five[-2] if len(last_five) > 1 else None
    return Overview(
        fiscal_year=fy0.year,
        key_figures=_key_figures(data, fy0, fy1),
        series=_series(data, last_five),
        coverage=_coverage(data, fy0),
        balance=_balance(data, fy0),
        filing=_filing(data, fy0),
        fiscal_year_end=_day(fy0),
        years_text=f"FY{last_five[0].year} – FY{fy0.year}",
    )


# --- the scorecard panel: the radar of the four areas and the checks by area ----------------------------------
# No total and no area to read first (the group's answers on #60, 26 November).

AREA_LABELS = {"past_performance": "Past performance", "financial_health": "Financial health",
               "dividend": "Dividend", "valuation": "Valuation"}
CHECKS_PER_AREA = 6
MARKS = {"pass": "pass", "fail": "fail", "insufficient_data": "not_assessed", "not_applicable": "not_applicable"}
NOT_IN_THIS_VERSION = "Not part of this version"  # as the main screen says (ui/scorecard.py, design spec §6)


@dataclass(frozen=True)
class AreaSummary:
    area: str
    label: str
    marks: tuple[str, ...]  # per check, in order: pass, fail, not_assessed or not_applicable
    passed: int
    assessed: int
    count_text: str  # for screen readers: "4 passed of 4 assessed", "No dividend paid · 0 passed of 1 assessed"
    short_text: str  # the count on screen, one format (SPEC §3): "4 passed of 4 assessed", "Not assessed"
    note: str = ""  # shown under the marks: "No dividend paid", else empty
    share: float | None = None  # passed ÷ assessed on the radar; None keeps the area off the shape (see below)
    share_text: str = ""  # under the radar's label: "67%", or why the area is off the shape


@dataclass(frozen=True)
class Scorecard:
    areas: tuple[AreaSummary, ...]


def _area_summary(area: str, results) -> AreaSummary:
    """Counts come from `src.scores` (D's), the no-dividend words from the dividend module (C's), as on the main
    screen, so the panel and the score chart cannot disagree (Simon's point on #60)."""
    label = AREA_LABELS.get(area, area.replace("_", " ").capitalize())
    if results is None:  # no check module in this version
        return AreaSummary(area, label, ("not_assessed",) * CHECKS_PER_AREA, 0, 0, NOT_IN_THIS_VERSION,
                           NOT_IN_THIS_VERSION, share_text=NOT_IN_THIS_VERSION)
    score = area_score(results)
    short = f"{score.passed} passed of {score.assessed} assessed" if score.assessed else "Not assessed"
    note = dividend_note(results) if area == "dividend" else None
    note = note[:1].upper() + note[1:] if note else ""
    marks = tuple(MARKS.get(r.status, "not_assessed") for r in results) or ("not_assessed",) * CHECKS_PER_AREA
    # Off the radar's shape: nothing assessed, or a check that does not apply (no dividend; a valuation without an
    # estimate), where a share would read as 0% or 100% and mislead (Flo's two cases on #60).
    on_shape = score.assessed and "not_applicable" not in marks
    share = score.passed / score.assessed if on_shape else None
    return AreaSummary(area, label, marks, score.passed, score.assessed, f"{note} · {short}" if note else short,
                       short, note, share, f"{share * 100:.0f}%" if share is not None else (note or short))


RADAR_ORDER = ("financial_health", "past_performance", "valuation", "dividend")  # axes: top, right, bottom, left


@dataclass(frozen=True)
class RadarShape:
    points: tuple[tuple[str, float], ...]  # (area, share in percent) for each scored area, in RADAR_ORDER
    edges: tuple[tuple[str, str], ...]  # neighbouring scored areas joined by a line, in RADAR_ORDER
    filled: bool  # only when all four areas are scored


def radar_shape(card: "Scorecard") -> RadarShape:
    """What the radar draws. Two areas are joined only when both are scored and next to each other, and the shape is
    filled only when all four are scored: an area off the shape breaks the line at its own axis instead of being
    crossed through the centre, where it would read as 0% (SPEC §3; Igor, 26 November)."""
    shares = {a.area: a.share for a in card.areas}
    scored = [area for area in RADAR_ORDER if shares.get(area) is not None]
    neighbours = [(RADAR_ORDER[i], RADAR_ORDER[(i + 1) % len(RADAR_ORDER)]) for i in range(len(RADAR_ORDER))]
    return RadarShape(
        points=tuple((area, shares[area] * 100) for area in scored),
        edges=tuple((a, b) for a, b in neighbours if a in scored and b in scored and len(scored) > 1),
        filled=len(scored) == len(RADAR_ORDER),
    )


def scorecard(results) -> Scorecard:
    """`results` maps each area to its check results in order, or None for an area not part of this version (as
    `ui.results.check_results` returns). Counts only: which check passes is decided by the checks themselves."""
    return Scorecard(tuple(_area_summary(area, results.get(area)) for area in AREA_LABELS))


# --- the charts (slice S10d, Igor, 26 November) -------------------------------------------------------------------
# One chart per question, with the chart type a reader expects for it: the share price against the estimate, the
# price ratios against the industry and the market, where the revenue goes, the financial position, the balance sheet
# split, debt, equity and cash over five years, dividends against free cash flow, the earnings payout and the dividend
# yield against the market. Every value and sentence is prepared here; a missing figure is a gap with its reason,
# never zero. Hand working: docs/acceptance.md, "Overview charts (S10d)".

ASSET_PARTS = (("cash", "Cash and equivalents"), ("receivables", "Receivables"), ("inventory", "Inventory"),
               ("ppe_net", "Property, plant and equipment"), ("equity_method_investments", "Investments in associates"))
CLAIM_PARTS = (("financial_debt", "Financial debt"), ("payables", "Payables"))
ASSESSED = ("pass", "fail")
NUMBER_WORDS = {2: "two", 3: "three", 4: "four", 5: "five"}


@dataclass(frozen=True)
class Bar:
    label: str
    value: float | None  # in the chart's unit; None is a gap, never zero
    text: str  # as written on the bar and in the figures table
    note: str = ""  # why a value is missing


@dataclass(frozen=True)
class Comparison:
    """Bars side by side: the company against the industry and the market, or its short-term assets against its
    short- and long-term liabilities."""

    title: str
    status: str  # ok, or none (then `text` says why)
    text: str  # the sentence under the chart
    bars: tuple[Bar, ...] = ()
    unit: str = ""  # "USD m", "USD bn", "×" or "%"


@dataclass(frozen=True)
class PriceCheck:
    """The share price against the estimate, on one scale with the estimate's zones (from V1, V2 and V6)."""

    status: str
    text: str
    bars: tuple[Bar, ...] = ()  # share price, estimate (USD per share)
    zones: tuple[tuple[str, float, float], ...] = ()  # (label, from, to) in USD per share
    marks: tuple[Bar, ...] = ()  # the estimate at the growth cap
    axis_max: float = 0.0


@dataclass(frozen=True)
class Flow:
    source: str
    target: str
    value: float  # USD
    text: str


@dataclass(frozen=True)
class MoneyFlow:
    """Where the revenue goes: revenue → costs → operating income → interest, tax and other → net income."""

    status: str
    text: str
    nodes: tuple[tuple[str, str], ...] = ()  # (label, amount) in the order of the flows
    flows: tuple[Flow, ...] = ()
    note: str = ""  # a figure in the flow that is worked out, not filed


@dataclass(frozen=True)
class Part:
    label: str
    value: float  # USD
    text: str
    share: str  # of total assets, "9.8%"
    fraction: float  # the same share for the bar's length


@dataclass(frozen=True)
class Split:
    """What the company owns (assets) against what it owes and the shareholders' part (liabilities and equity)."""

    status: str
    text: str
    assets: tuple[Part, ...] = ()
    claims: tuple[Part, ...] = ()
    note: str = ""  # which parts are not reported separately, or why a part is left out
    total: str = NA  # total assets
    claims_title: str = "Liabilities and equity"  # "Liabilities (equity is negative)" when equity is at or below zero
    claims_total: str = NA  # the parts drawn on that side: total assets, or total liabilities when equity is negative


@dataclass(frozen=True)
class Payout:
    status: str
    text: str
    percent: str = NA  # dividends paid ÷ net income, "67.0%"
    share: float | None = None  # the filled part of the ring, between 0 and 1


@dataclass(frozen=True)
class Charts:
    money_flow: MoneyFlow
    position: Comparison
    split: Split
    debt_history: Series
    debt_text: str
    dividend_history: Series
    dividend_text: str
    payout: Payout
    price: PriceCheck | None = None  # these three need the check results (no results: not drawn)
    ratios: tuple[Comparison, ...] = ()
    dividend_yield: Comparison | None = None


def _percent(ratio: float) -> str:
    return _signed(_fixed(ratio * 100, 1)) + "%"


def _per_share(value: float) -> str:
    return f"USD {_fixed(value, 2)}"


def _times(value: float) -> str:
    return _signed(_fixed(value, 2)) + "×"


def _versus(a: float, b: float) -> str:
    return "above" if a > b else "below" if a < b else "equal to"


def _and(words: list[str]) -> str:
    return words[0] if len(words) == 1 else ", ".join(words[:-1]) + " and " + words[-1]


def _scaled(values: list[float | None]) -> tuple[float, str]:
    known = [abs(v) for v in values if v is not None]
    return (BILLION, "USD bn") if known and max(known) >= BILLION else (MILLION, "USD m")


def _money_flow(data: CompanyData, fy0: date) -> MoneyFlow:
    figures = {}
    for metric in ("revenue", "operating_income", "net_income"):
        figures[metric], why = _value(data, metric, fy0)
        if figures[metric] is None:
            return MoneyFlow("none", f"The flow chart is not available: {why}.")
    revenue, income, net = figures["revenue"], figures["operating_income"], figures["net_income"]
    if revenue <= 0:
        return MoneyFlow("none", f"The flow chart needs revenue above zero: {_year(fy0)} revenue was "
                                 f"{amount_text(revenue)}.")
    for value, what in ((income, "an operating loss"), (net, "a net loss")):
        if value <= 0:
            return MoneyFlow("none", f"The flow chart needs a profit: {_year(fy0)} had {what} of "
                                     f"{amount_text(value)}.")
    if income > revenue:
        return MoneyFlow("none", f"The flow chart is not available: operating income ({amount_text(income)}) is "
                                 f"above revenue ({amount_text(revenue)}) in {_year(fy0)}.")
    gross, _ = _value(data, "gross_profit", fy0)
    if gross is not None and income <= gross <= revenue:  # else one cost step (Appendix A has no gross profit)
        steps = [("Revenue", "Cost of revenue", revenue - gross), ("Revenue", "Gross profit", gross),
                 ("Gross profit", "Operating expenses", gross - income), ("Gross profit", "Operating income", income)]
        costs = (f"{amount_text(revenue - gross)} went to cost of revenue and {amount_text(gross - income)} to "
                 "operating expenses")
    else:
        steps = [("Revenue", "Operating costs", revenue - income), ("Revenue", "Operating income", income)]
        costs = f"{amount_text(revenue - income)} went to operating costs"
    share = _percent(net / revenue)
    if net <= income:
        steps += [("Operating income", "Interest, tax and other", income - net), ("Operating income", "Net income", net)]
        after = (f"after interest, tax and other items of {amount_text(income - net)}, net income was "
                 if net < income else "net income was ")
        end = f"{after}{amount_text(net)}, {share} of revenue."
    else:
        steps += [("Operating income", "Net income", income), ("Other income, net", "Net income", net - income)]
        end = (f"other income, net of interest and tax, of {amount_text(net - income)} raised net income to "
               f"{amount_text(net)}, {share} of revenue.")
    flows = tuple(Flow(a, b, value, amount_text(value)) for a, b, value in steps if value > 0)
    totals = {"Revenue": revenue, "Net income": net}
    for flow in flows:
        totals.setdefault(flow.target, flow.value)
        totals.setdefault(flow.source, flow.value)
    order = list(dict.fromkeys(label for flow in flows for label in (flow.source, flow.target)))
    text = (f"Of revenue of {amount_text(revenue)}, {costs}, leaving operating income of {amount_text(income)}; "
            f"{end}")
    note = ""
    if gross is not None and "Gross profit" in totals and _kind(data, "gross_profit", fy0) == "derived":
        note = ("Gross profit is worked out as revenue − cost of revenue: the filing gives no gross profit, and what "
                "the company counts as cost of revenue varies.")
    return MoneyFlow("ok", text, tuple((label, amount_text(totals[label])) for label in order), flows, note)


def _position(data: CompanyData, fy0: date) -> Comparison:
    assets, why_a = _value(data, "current_assets", fy0)
    short, why_s = _value(data, "current_liabilities", fy0)
    total, why_t = _value(data, "total_liabilities", fy0)
    if short is None or total is None:
        long, why_l = None, why_s or why_t
    elif total < short:
        long, why_l = None, f"total liabilities for {_year(fy0)} are below current liabilities"
    else:
        long, why_l = total - short, ""
    values = [assets, short, long]
    scale, unit = _scaled(values)
    bars = tuple(Bar(label, None if v is None else v / scale, NA if v is None else amount_text(v), why)
                 for label, v, why in (("Short-term assets", assets, why_a), ("Short-term liabilities", short, why_s),
                                       ("Long-term liabilities", long, why_l)))
    if assets is None:
        return Comparison("Financial position", "none", f"The financial position is not available: {why_a}.", bars,
                          unit)
    parts = [f"{_versus(assets, v)} {label.lower()} of {amount_text(v)}"
             for label, v in (("Short-term liabilities", short), ("Long-term liabilities", long)) if v is not None]
    if not parts:
        return Comparison("Financial position", "none", f"The financial position is not available: {why_l}.", bars,
                          unit)
    return Comparison("Financial position", "ok", f"Short-term assets of {amount_text(assets)} are {_and(parts)}.",
                      bars, unit)


def _parts(data: CompanyData, fy0: date, spec, total: float, rest_label: str, whole: float, whole_name: str):
    """The named parts that are reported, the rest as one part, and the parts not reported separately."""
    found, missing = [], []
    for metric, label in spec:
        value, _ = _value(data, metric, fy0)
        if value is None or value < 0:
            missing.append(label[:1].lower() + label[1:])
        elif value > 0:  # zero: nothing to draw (an equity-method investment of nil)
            found.append((label, value))
    rest = whole - sum(v for _, v in found)
    overlap = ""
    if rest > 0:
        found.append((rest_label, rest))
    elif rest < 0:
        overlap = (f"The {whole_name} parts add up to more than the total of {amount_text(whole)}; the figures may "
                   "overlap (check the 10-K).")
    parts = tuple(Part(label, v, amount_text(v), _percent(v / total), v / total) for label, v in found)
    return parts, missing, overlap


def _split(data: CompanyData, fy0: date) -> Split:
    total, why_t = _value(data, "total_assets", fy0)
    liabilities, why_l = _value(data, "total_liabilities", fy0)
    if total is None or liabilities is None:
        return Split("none", f"The balance sheet split is not available: {why_t or why_l}.")
    if total <= 0:
        return Split("none", f"The balance sheet split is not available: total assets for {_year(fy0)} are at or "
                             "below zero.")
    assets, missing_a, overlap_a = _parts(data, fy0, ASSET_PARTS, total, "Other assets", total, "asset")
    claims, missing_c, overlap_c = _parts(data, fy0, CLAIM_PARTS, total, "Other liabilities", liabilities,
                                          "liability")
    equity = total - liabilities
    minority, _ = _value(data, "minority_interest", fy0)
    if equity > 0:
        label = "Equity, including minority interests" if minority else "Equity"
        claims += (Part(label, equity, amount_text(equity), _percent(equity / total), equity / total),)
    named = {p.label: p for p in assets + claims}
    first = [f"cash and equivalents are {named['Cash and equivalents'].share}"] if "Cash and equivalents" in named else []
    debt = f"financial debt is {named['Financial debt'].share}" if "Financial debt" in named else ""
    if equity > 0:
        equity_text = f"equity {claims[-1].share}" if debt else f"equity is {claims[-1].share}"
        tail = (f"{debt} and {equity_text}" if debt else equity_text) + " of the same total"
    else:
        state = "negative" if equity < 0 else "zero"
        larger = "larger than" if equity < 0 else "equal to"
        tail = ((f"{debt} of the same total; " if debt else "") +
                f"liabilities are {larger} assets, so equity is {state} ({amount_text(equity)})")
    notes = []
    if missing_a:
        notes.append(f"Not in the data as a separate figure, so counted in other assets: {_and(missing_a)}.")
    if missing_c:
        lead = ("In other liabilities: " if missing_a else
                "Not in the data as a separate figure, so counted in other liabilities: ")
        notes.append(f"{lead}{_and(missing_c)}.")
    notes += [n for n in (overlap_a, overlap_c) if n]
    title = "Liabilities and equity" if equity > 0 else f"Liabilities (equity is {state})"
    return Split("ok", f"Of total assets of {amount_text(total)}, " + "; ".join(first + [tail]) + ".", assets,
                 claims, " ".join(notes), amount_text(total), title, amount_text(sum(p.value for p in claims)))


def _debt_text(data: CompanyData, years: list[date]) -> str:
    fy0, first = years[-1], years[0]
    debt, why_d = _value(data, "financial_debt", fy0)
    equity, why_e = _value(data, "equity", fy0)
    if debt is None or equity is None:
        return f"Debt to equity is not available: {why_d or why_e}."
    if equity <= 0:
        state = "negative" if equity < 0 else "zero"
        return (f"Shareholder equity was {state} in {_year(fy0)} ({amount_text(equity)}), so debt to equity is not "
                "meaningful.")
    text = f"Financial debt was {_percent(debt / equity)} of shareholder equity in {_year(fy0)}"
    if first != fy0:
        debt_then, _ = _value(data, "financial_debt", first)
        equity_then, _ = _value(data, "equity", first)
        if debt_then is not None and equity_then is not None and equity_then > 0:
            text += f", against {_percent(debt_then / equity_then)} in {_year(first)}"
    return text + "."


def _dividend_text(data: CompanyData, years: list[date]) -> str:
    dividends = [_value(data, "dividends_paid", end)[0] for end in years]
    known = [d for d in dividends if d is not None]
    if known and all(d == 0 for d in known) and len(known) == len(years):
        span = f"the {NUMBER_WORDS[len(years)]} years" if len(years) in NUMBER_WORDS else "the year"
        return f"No dividend paid in {span}."
    paying = [(end, d, fcf) for end, d in zip(years, dividends)
              if d is not None and d > 0 and (fcf := _free_cash_flow(data, end)[0]) is not None]
    if not paying:
        return "Dividends against free cash flow are not available for these years."
    short = [_year(end) for end, d, fcf in paying if fcf < d]
    if not short:
        return f"Free cash flow covered the dividends paid in all {len(paying)} years."
    if len(short) == len(paying):
        return f"Free cash flow did not cover the dividends paid in any of the {len(paying)} years."
    return (f"Free cash flow covered the dividends paid in {len(paying) - len(short)} of {len(paying)} years; not in "
            f"{_and(short)}.")


def _payout(data: CompanyData, fy0: date) -> Payout:
    dividends, why_d = _value(data, "dividends_paid", fy0)
    if dividends is None:
        return Payout("none", f"The payout ratio is not available: {why_d}.")
    if dividends < 0:
        return Payout("none", f"The payout ratio is not available: dividends paid for {_year(fy0)} are filed as a "
                              "negative amount (a sign error).")
    if dividends == 0:
        return Payout("none", f"No dividend paid in {_year(fy0)}.")
    net, why_n = _value(data, "net_income", fy0)
    if net is None:
        return Payout("none", f"The payout ratio is not available: {why_n}.")
    if net <= 0:
        return Payout("none", f"Net income was a loss in {_year(fy0)}, so a payout ratio is not meaningful.")
    ratio = dividends / net
    more = ": more than the year's profit." if ratio > 1 else "."
    return Payout("ok", f"Dividends paid were {_percent(ratio)} of net income in {_year(fy0)}{more}", _percent(ratio),
                  min(ratio, 1.0))


def _assessed(check: CheckResult | None) -> bool:
    return check is not None and check.status in ASSESSED and check.value is not None


def _price(checks: dict[str, CheckResult]) -> PriceCheck:
    v1, v2, v6 = checks.get("V1"), checks.get("V2"), checks.get("V6")
    if v1 is None:
        return PriceCheck("none", NOT_IN_THIS_VERSION)
    if not _assessed(v1) or v1.threshold is None or v1.threshold <= 0:
        return PriceCheck("none", v1.explanation)
    price, estimate = v1.value, v1.threshold
    marks = (Bar("Estimate at the growth cap", v6.threshold, _per_share(v6.threshold)),) \
        if _assessed(v6) and v6.threshold is not None else ()
    top = max([price, estimate] + [m.value for m in marks]) * 1.15
    if _assessed(v2) and v2.threshold is not None:
        zones = (("80% of the estimate or less", 0.0, v2.threshold),
                 ("80% to 100% of the estimate", v2.threshold, estimate), ("Above the estimate", estimate, top))
    else:
        zones = (("Below the estimate", 0.0, estimate), ("Above the estimate", estimate, top))
    gap = price / estimate - 1
    where = f"is {_percent(abs(gap))} {'above' if gap > 0 else 'below'}" if gap else "is equal to"
    return PriceCheck("ok", f"The share price you typed, {_per_share(price)}, {where} the estimate of "
                            f"{_per_share(estimate)}.",
                      (Bar("Share price", price, _per_share(price)), Bar("Estimate", estimate, _per_share(estimate))),
                      zones, marks, top)


def _against(title: str, ticker: str, checks: dict[str, CheckResult], pairs, write, scale: float = 1.0) -> Comparison:
    """The company's ratio against the benchmarks the checks compared it with (each check's threshold)."""
    found = [(checks.get(check_id), label) for check_id, label in pairs]
    company = next((c for c, _ in found if _assessed(c)), None)
    if company is None:
        first = found[0][0]
        return Comparison(title, "none", first.explanation if first is not None else NOT_IN_THIS_VERSION)
    bars = [Bar(ticker, company.value * scale, write(company.value))]
    words = []
    for check, label in found:
        if _assessed(check) and check.threshold is not None:
            bars.append(Bar(label, check.threshold * scale, write(check.threshold)))
            words.append(f"{write(check.threshold)} for the {label.lower().replace('us ', 'US ')}")
    return Comparison(title, "ok", f"{title} {write(company.value)} against {_and(words)}." if words else
                      f"{title} {write(company.value)}; no benchmark to compare it with.", tuple(bars),
                      "%" if scale == 100 else "×")


def charts(data: CompanyData, results=None) -> Charts:
    """Everything the overview's charts draw. With the check results (as `ui.results.check_results` returns them),
    also the share price against the estimate, the price ratios and the dividend yield, from the checks' own
    figures, so the charts and the checks cannot disagree."""
    years = (data.fiscal_years("revenue") or data.fiscal_years("net_income"))[-5:]
    if not years:
        empty, why = Series((), "USD m", ()), "no fiscal year in the data"
        return Charts(MoneyFlow("none", f"The flow chart is not available: {why}."),
                      Comparison("Financial position", "none", f"The financial position is not available: {why}."),
                      Split("none", f"The balance sheet split is not available: {why}."), empty,
                      f"Debt to equity is not available: {why}.", empty, "", Payout("none", ""))
    fy0 = years[-1]
    found = dict(
        money_flow=_money_flow(data, fy0),
        position=_position(data, fy0),
        split=_split(data, fy0),
        debt_history=_lines({"Financial debt": [_value(data, "financial_debt", end)[0] for end in years],
                             "Shareholder equity": [_value(data, "equity", end)[0] for end in years],
                             "Cash and equivalents": [_value(data, "cash", end)[0] for end in years]}, years),
        debt_text=_debt_text(data, years),
        dividend_history=_lines({"Dividends paid": [_value(data, "dividends_paid", end)[0] for end in years],
                                 "Free cash flow": [_free_cash_flow(data, end)[0] for end in years]}, years),
        dividend_text=_dividend_text(data, years),
        payout=_payout(data, fy0),
    )
    if results is not None:
        checks = {r.check_id: r for area in results.values() if area for r in area}
        found.update(
            price=_price(checks),
            ratios=(_against("Price to earnings", data.ticker, checks, (("V3", "Industry"), ("V4", "US market")),
                             _times),
                    _against("Price to book", data.ticker, checks, (("V5", "Industry"),), _times)),
            dividend_yield=_against("Dividend yield", data.ticker, checks, (("D2", "US market"),),
                                    lambda v: _fixed(v * 100, 2) + "%", scale=100),
        )
    return Charts(**found)
