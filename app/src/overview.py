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

from src.contracts import CompanyData, Fact

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


# --- writing numbers --------------------------------------------------------------------------------------------


def _signed(number: str) -> str:
    return number.replace("-", MINUS)


def amount_parts(value: float) -> tuple[str, str, str]:
    """USD 1 bn or more in USD bn with two decimals, smaller amounts in USD m with none."""
    if abs(value) >= BILLION:
        return "USD", _signed(f"{value / BILLION:,.2f}"), "bn"
    return "USD", _signed(f"{value / MILLION:,.0f}"), "m"


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
    columns = {
        "Revenue": [_value(data, "revenue", end)[0] for end in years],
        "Net income": [_value(data, "net_income", end)[0] for end in years],
        "Free cash flow": [_free_cash_flow(data, end)[0] for end in years],
    }
    known = [abs(v) for values in columns.values() for v in values if v is not None]
    scale, unit = (BILLION, "USD bn") if known and max(known) >= BILLION else (MILLION, "USD m")
    lines = tuple(
        Line(label, tuple(None if v is None else v / scale for v in values),
             tuple(NA if v is None else amount_text(v) for v in values))
        for label, values in columns.items()
    )
    return Series(tuple(end.year for end in years), unit, lines)


def _coverage(data: CompanyData, fy0: date) -> Coverage:
    fcf, fcf_why = _free_cash_flow(data, fy0)
    dividends_fact = data.fact("dividends_paid", fy0)
    dividends, div_why = _value(data, "dividends_paid", fy0)
    fcf_text = NA if fcf is None else amount_text(fcf)
    if dividends is not None and dividends <= 0:  # treated as nil (SPEC §7, plan Q1) or reported as zero
        note = dividends_fact.note if dividends_fact is not None else ""
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
    return Coverage(
        "covered" if covered else "not_covered",
        "Free cash flow covers the dividends" if covered else "Free cash flow does not cover the dividends",
        percent=f"{ratio * 100:.1f}%",
        share=min(ratio, 1.0),
        free_cash_flow=fcf_text,
        dividends=div_text,
        gap=amount_text(abs(fcf - dividends)),
        gap_label="Free cash flow above dividends" if covered else "Dividends above free cash flow",
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
    )
