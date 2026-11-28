"""Valuation engine, equity method (SPEC §8.1–8.3, §8.6; slices S8 and S8b). Owner: C (Flo).

The free cash flow that belongs to the shareholders, forecast for ten years and discounted at the cost of equity.
A pure function: `CompanyData`, the settings and three market inputs in, one `Valuation` out. No network, no files,
no interface (SPEC §11).

    from src.settings import load_settings
    v = value_company(data, load_settings(), share_price=30.0, risk_free_rate=rf, unlevered_beta=beta)
    v.status          # "ok", "insufficient_data" or "not_applicable" (SPEC §8.6)
    v.fair_value      # Fact in USD per share, or None with the reason in v.reason

The steps, in order (method of issue #71, agreed 27 November 2026):
1. §8.6, first test: every input is there and usable: revenue FY-4 to FY0 (all above zero), from `data.recent` the
   operating cash flow and capital expenditure of the last twelve months, the latest financial debt, minority
   interest and share count, then the share price, the risk-free rate and the industry beta. Otherwise "insufficient
   data", naming every input that is missing. A missing latest figure is never replaced by an annual one.
2. §8.1: levered beta = unlevered beta × (1 + (1 − tax rate) × latest financial debt ÷ (share price × latest
   shares)), limited to `beta_min`–`beta_max`; cost of equity = risk-free rate + beta × equity risk premium
   (Damodaran's implied premium, with its date in the settings).
3. §8.2: FCF0 = operating cash flow − capital expenditure of the last twelve months. g1 = (revenue FY0 ÷ revenue
   FY-4)^(1/4) − 1, limited to `growth_floor`–`growth_cap`; g(t) = gT + (g1 − gT) × 0.5^((t − 1) ÷
   `growth_half_life_years`); FCF(t) = FCF(t − 1) × (1 + g(t)) for t = 1 to `forecast_years`.
4. §8.6, second test: FCF0 ≤ 0 → "not applicable" (the model does not fit).
5. §8.3: gT = the risk-free rate; terminal value = FCF(N) × (1 + gT) ÷ (cost of equity − gT); end-of-year
   discounting, the terminal value at t = N; the valuation date is the end of the twelve months; equity value =
   present value − latest minority interest; fair value = equity value ÷ latest shares.
6. §8.6, second test: equity value ≤ 0 → "not applicable".
The same valuation with g1 set to `growth_cap` gives the fair value V6 uses (SPEC §7).

The comparison with the three fiscal years (Flo's decisions, 27 November 2026), only when there is an estimate: one
line in `notes` when FCF0 is more than `fcf_difference_warning` above or below the plain average of the free cash flow
of the last `fcf_base_years` fiscal years (or when that average is zero or less). When a figure of those years is
missing or has a sign error, the estimate stays and the line says that no comparison is possible. The average never
enters the estimate.

Decisions (Flo, 24 November 2026):
- The risk-free rate and the industry beta come in as `Fact`s, so their source and period stay with them. A's data
  layer (S2b) supplies the rate (FRED, or the dated fallback in settings.yaml); B's benchmark loader (S4) the beta.
  This module never reads a fallback itself, so a missing rate is "insufficient data", never a guess.
- The share price is the number the user typed in (SPEC §3). It is not among `Valuation.inputs` (it has no filing
  source). The checks V1, V2 and V6 (S9) use it as their value and name it in their texts, never as a `Fact`
  (Flo's decision d, 25 November).
- A negative capital expenditure or a negative financial debt is a sign error that the data layer keeps as filed
  and flags (SPEC §5.4): it is never flipped, so the valuation is "insufficient data" (as in the dividend checks).
- The growth note names the terminal growth actually used (since S8b: the risk-free rate).
Decisions after the review of 24 November (Flo):
- Revenue ≤ 0 in any of the five years is "insufficient data" (SPEC §8.6 names FY0 and FY-4; a middle year ≤ 0 is
  a sign error).
- Past growth within 1e-10 of a limit counts as at the limit: not labelled as limited, no growth note (otherwise
  rounding makes exactly 30% "limited" but exactly −10% not).
- A limited beta or starting growth is a record for the sources page (`records`, prefixes BETA_LIMIT and
  GROWTH_LIMIT), never a header warning (SPEC §10).
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from datetime import date
from typing import Literal, Mapping

from src.contracts import CompanyData, Fact

YEARS = 5  # FY-4 to FY0: four intervals of revenue growth
AT_LIMIT = 1e-10  # past growth this close to a growth limit counts as at the limit, not beyond it
# The latest figures the estimate needs (`CompanyData.recent`), and how a gap names the date it stands for
LATEST = {
    "operating_cash_flow": "over the last twelve months",
    "capital_expenditure": "over the last twelve months",
    "financial_debt": "on the latest balance sheet",
    "shares": "from the latest report",
    "minority_interest": "on the latest balance sheet",
}
LABELS = {
    "revenue": "revenue",
    "operating_cash_flow": "operating cash flow",
    "capital_expenditure": "capital expenditure",
    "financial_debt": "financial debt",
    "minority_interest": "minority interest",
    "shares": "shares",
}
WORDS = {1: "one", 2: "two", 3: "three", 4: "four", 5: "five"}


@dataclass(frozen=True)
class ForecastYear:
    year: int  # 1 to N, counted from the end of FY0
    growth: float  # g(t), a decimal
    free_cash_flow: float  # USD
    discounted: float  # USD, at the end of FY0


@dataclass(frozen=True)
class Forecast:
    years: tuple[ForecastYear, ...]
    sum_of_discounted: float  # USD
    terminal_value: float  # USD, at the end of year N
    discounted_terminal_value: float  # USD

    @property
    def present_value(self) -> float:
        return self.sum_of_discounted + self.discounted_terminal_value

    @property
    def terminal_value_share(self) -> float:
        return self.discounted_terminal_value / self.present_value


@dataclass(frozen=True)
class Valuation:
    """Everything the valuation detail shows (S10b) and the checks V1, V2 and V6 use (S9).

    Which fields are filled:
    - "insufficient_data": only `status`, `reason` and `inputs` (the figures that exist, so the checks and the sources
      page can link them: the revenue years found, and the risk-free rate and industry beta when given).
    - "not_applicable": `reason` and `inputs`, plus the steps that ran: `levered_beta`, `cost_of_equity`,
      `terminal_growth`, `equity_risk_premium`, `base_free_cash_flows`, `average_free_cash_flow`,
      `starting_free_cash_flow`, `starting_growth`, `past_revenue_growth`, `minority_interest` and `records`.
      `forecast` only when the minority interests were larger than the value;
      `notes` is empty; `equity_value`, `fair_value` and `fair_value_at_growth_cap` are None.
    - "ok": everything, `reason` is "".
    """

    status: Literal["ok", "insufficient_data", "not_applicable"]
    reason: str  # "" when ok; otherwise the plain-words reason for V1, V2 and V6
    inputs: tuple[Fact, ...]  # every figure the valuation used or needed
    levered_beta: Fact | None = None
    cost_of_equity: Fact | None = None
    terminal_growth: Fact | None = None
    base_free_cash_flows: tuple[Fact, ...] = ()
    free_cash_flow_margin: Fact | None = None  # always None since S8b; the screen (D) still reads the name
    starting_free_cash_flow: Fact | None = None
    starting_growth: Fact | None = None
    equity_risk_premium: Fact | None = None  # an assumption, with its source in plain words
    past_revenue_growth: Fact | None = None  # the company's actual growth a year, never limited (SPEC §3, item 6)
    forecast: Forecast | None = None
    minority_interest: Fact | None = None
    equity_value: Fact | None = None
    fair_value: Fact | None = None  # USD per share
    fair_value_at_growth_cap: Fact | None = None  # USD per share, for V6
    notes: tuple[str, ...] = ()  # extra lines for the valuation detail (growth note, comparison with three years)
    records: tuple[str, ...] = ()  # lines for the sources page, never the header (SPEC §10), e.g. "BETA_LIMIT: ..."
    average_free_cash_flow: Fact | None = None  # of the last fiscal years; for the comparison only


# --- the formulas (pure arithmetic, used by the property tests) ------------------------------------------------------


def levered_beta(unlevered: float, debt: float, market_value_of_equity: float, tax_rate: float, beta_min: float,
                 beta_max: float) -> tuple[float, float]:
    """(beta within the limits, beta before the limits), SPEC §8.1."""
    before = unlevered * (1 + (1 - tax_rate) * debt / market_value_of_equity)
    return min(max(before, beta_min), beta_max), before


def growth_path(g1: float, terminal_growth: float, half_life_years: float, forecast_years: int) -> tuple[float, ...]:
    """g(t) = gT + (g1 − gT) × 0.5^((t − 1) ÷ H) for t = 1 to N (SPEC §8.2)."""
    gap = g1 - terminal_growth
    return tuple(terminal_growth + gap * 0.5 ** ((t - 1) / half_life_years) for t in range(1, forecast_years + 1))


def forecast(fcf0: float, growth: tuple[float, ...], cost_of_equity: float, terminal_growth: float) -> Forecast:
    """The free cash flows, discounted at the end of each year, and the terminal value at year N (SPEC §8.2–8.3)."""
    if cost_of_equity <= terminal_growth:
        # Cannot happen with valid settings (beta_min × premium > 0, SPEC §8.3): a settings error, not a company case.
        raise ValueError(f"cost of equity {cost_of_equity} is not above terminal growth {terminal_growth}")
    rows, cash_flow = [], fcf0
    for t, g in enumerate(growth, start=1):
        cash_flow *= 1 + g
        rows.append(ForecastYear(t, g, cash_flow, cash_flow / (1 + cost_of_equity) ** t))
    n = len(rows)
    terminal = cash_flow * (1 + terminal_growth) / (cost_of_equity - terminal_growth)
    return Forecast(tuple(rows), sum(r.discounted for r in rows), terminal, terminal / (1 + cost_of_equity) ** n)


# --- the valuation of one company ------------------------------------------------------------------------------------


def value_company(data: CompanyData, settings: Mapping[str, Mapping], *, share_price: float | None,
                  risk_free_rate: Fact | None, unlevered_beta: Fact | None) -> Valuation:
    """The fair value per share of one company, or the reason there is none (SPEC §8.6)."""
    s = settings["valuation"]
    base_years = int(s["fcf_base_years"])
    years = data.fiscal_years("revenue")[-YEARS:]
    market = [f for f in (risk_free_rate, unlevered_beta) if f is not None]
    if len(years) < YEARS:
        gaps = [f"the valuation needs revenue for five fiscal years (four years earlier to the latest); the data has "
                f"{len(years)}"] + _market_gaps(share_price, risk_free_rate, unlevered_beta)
        found = tuple(_figure(data, "revenue", end) for end in years) + tuple(market)  # what exists, for the links
        return Valuation("insufficient_data", f"Insufficient data: {'; '.join(gaps)}.", found)
    fy0 = years[-1]

    # 1. §8.6, first test: every input there and usable.
    revenue = [_figure(data, "revenue", end) for end in years]
    latest = {metric: _latest(data, metric, fy0) for metric in LATEST}
    cash_flow, capex, debt = latest["operating_cash_flow"], latest["capital_expenditure"], latest["financial_debt"]
    shares, minority = latest["shares"], latest["minority_interest"]
    base, average, no_average = _three_years(data, years[-base_years:])
    listed = {(f.metric, f.period_end) for f in latest.values()}  # no figure of the same period twice
    # the annual figures behind the average, only when all of them are usable
    compared = [f for row in base for f in row[1:] if (f.metric, f.period_end) not in listed]
    inputs = tuple(revenue + compared + list(latest.values()) + market)

    gaps = []
    for fact in revenue:
        why = _unusable(fact)
        if why:
            gaps.append(f"{_label(fact)}: {why}")
    for metric, fact in latest.items():
        # the sources page lists the warnings about annual figures only: point to it only for a fiscal year's figure
        why = _unusable(fact, on_sources_page=data.fact(metric, fact.period_end) is not None)
        if why:
            gaps.append(f"{LABELS[metric]} {LATEST[metric]}: {why}")
    gaps += _market_gaps(share_price, risk_free_rate, unlevered_beta)
    if gaps:
        return Valuation("insufficient_data", f"Insufficient data: {'; '.join(gaps)}.", inputs)
    as_of = cash_flow.period_end  # the end of the twelve months: the valuation date (SPEC §8.3)
    records = []  # for the sources page (SPEC §10)

    # 2. §8.1: beta and cost of equity.
    rf = risk_free_rate.value
    beta, before = _beta(unlevered_beta.value, debt, share_price, shares, s, as_of)
    if beta.kind == "assumption":
        records.append(f"BETA_LIMIT: the company's beta, adjusted for its debt, is {_beta_text(before, beta.value)}, "
                       f"outside the range "
                       f"{s['beta_min']} to {s['beta_max']}, so {beta.value} is used.")
    ke = rf + beta.value * s["equity_risk_premium"]
    cost_of_equity = _derived("cost_of_equity", ke, "pure", as_of,
                              f"risk-free rate {_pct(rf)} + beta {beta.value:.5f} × equity risk premium "
                              f"{_pct(s['equity_risk_premium'])}")
    premium = s["equity_risk_premium"]
    premium_fact = Fact("equity_risk_premium", premium, "pure", None, as_of, "assumption", None, None, None, None, None,
                        f"equity risk premium of {_limit(premium)}: Damodaran's implied premium for the US share "
                        f"market on {_day(s['equity_risk_premium_date'])}, the same for every company; not read from a filing")
    gt = rf
    terminal_growth = _derived("terminal_growth", gt, "pure", as_of, f"set equal to the risk-free rate ({_pct(rf)})")

    # 3. §8.2: starting free cash flow and starting growth.
    fcf0 = _derived("starting_free_cash_flow", cash_flow.value - capex.value, "USD", as_of,
                    f"operating cash flow {_usd(cash_flow.value)} − capital expenditure {_usd(capex.value)}, over "
                    f"the twelve months to {_day(as_of)}", start=cash_flow.period_start)
    fcfs = tuple(_derived("free_cash_flow", c.value - x.value, "USD", end,
                          f"operating cash flow {_usd(c.value)} − capital expenditure {_usd(x.value)}",
                          start=c.period_start) for end, c, x in base)
    average_fact = None if average is None else _derived(
        "average_free_cash_flow", average, "USD", fy0,
        f"plain average of the free cash flow of the last {_count(base_years)} fiscal years; compared with the last "
        "twelve months, not used in the estimate")
    g1, past = _starting_growth(revenue[0], revenue[-1], s)
    past_growth = _derived("past_revenue_growth", past, "pure", fy0, _growth_formula(revenue[0], revenue[-1]),
                           start=revenue[0].period_end)
    notes = []
    if g1.kind == "assumption":
        notes.append(_growth_note(past, g1.value, gt, s))
        first, last = revenue[0], revenue[-1]
        records.append(f"GROWTH_LIMIT: revenue changed by {_growth(past)} a year, from {_usd(first.value)} in the "
                       f"fiscal year ended {_day(first.period_end)} to {_usd(last.value)} in the fiscal year ended "
                       f"{_day(last.period_end)}; this is beyond the {_limit(g1.value)} limit, so the model starts at "
                       f"{_limit(g1.value)}.")
    if minority.value < 0:
        records.append(f"The minority interest on {_day(minority.period_end)} is negative ({_usd(minority.value)}); it is "
                       "used as "
                       "reported, so it adds to the equity value.")
    detail = dict(levered_beta=beta, cost_of_equity=cost_of_equity, terminal_growth=terminal_growth,
                  equity_risk_premium=premium_fact, past_revenue_growth=past_growth,
                  base_free_cash_flows=fcfs, average_free_cash_flow=average_fact, starting_free_cash_flow=fcf0,
                  starting_growth=g1, minority_interest=minority, notes=tuple(notes), records=tuple(records))

    # 4. §8.6, second test: no free cash flow over the last twelve months.
    if fcf0.value <= 0:
        return Valuation("not_applicable", (
            f"Not applicable: the model does not fit. Over the last twelve months (to {_day(as_of)}) the company "
            f"produced no free cash flow ({_usd(fcf0.value)}), so a cash flow model says nothing useful about its "
            "value."), inputs, **{**detail, "notes": ()})

    # 5. §8.3: forecast, terminal value, equity value.
    shape = (gt, s["growth_half_life_years"], int(s["forecast_years"]))
    own = forecast(fcf0.value, growth_path(g1.value, *shape), ke, gt)
    equity = own.present_value - minority.value

    # 6. §8.6, second test: minority interests larger than the value.
    if equity <= 0:
        return Valuation("not_applicable", (
            f"Not applicable: the model does not fit. The minority interests of {_usd(minority.value)} are larger than "
            f"the estimated value of the company's cash flows ({_usd(own.present_value)}), so the value left for "
            "the shareholders is zero or negative."), inputs, forecast=own, **{**detail, "notes": ()})

    # The comparison with the three fiscal years (issue #71, item 2): only when there is an estimate, so that no line
    # describes a valuation that never ran (review of 24 November, Igor).
    line = _comparison(fcf0.value, average, no_average, s["fcf_difference_warning"], base_years)
    if line:
        detail.update(notes=detail["notes"] + (line,))

    at_cap = forecast(fcf0.value, growth_path(s["growth_cap"], *shape), ke, gt).present_value - minority.value
    return Valuation(
        "ok", "", inputs, forecast=own,
        equity_value=_derived("equity_value", equity, "USD", as_of,
                              f"present value {_usd(own.present_value)} − minority interest {_usd(minority.value)}"),
        fair_value=_derived("fair_value", equity / shares.value, "USD/shares", as_of,
                            f"equity value {_usd(equity)} ÷ {shares.value:,.0f} shares"),
        fair_value_at_growth_cap=_derived("fair_value_at_growth_cap", at_cap / shares.value, "USD/shares", as_of,
                                          f"the same valuation with starting growth at the upper limit "
                                          f"({_limit(s['growth_cap'])}): equity value {_usd(at_cap)} ÷ "
                                          f"{shares.value:,.0f} shares"),
        **detail,
    )


def starting_growth(data: CompanyData, settings: Mapping[str, Mapping]) -> Fact:
    """g1 of one company: past revenue growth FY-4 to FY0, limited (SPEC §8.2). Raises ValueError if it cannot be
    calculated; `value_company` names the reason instead."""
    years = data.fiscal_years("revenue")[-YEARS:]
    if len(years) < YEARS:
        raise ValueError(f"needs revenue for five fiscal years; the data has {len(years)}")
    first, last = _figure(data, "revenue", years[0]), _figure(data, "revenue", years[-1])
    for fact in (first, last):
        why = _unusable(fact)
        if why:
            raise ValueError(f"{_label(fact)}: {why}")
    return _starting_growth(first, last, settings["valuation"])[0]


# --- the steps -------------------------------------------------------------------------------------------------------


def _beta(unlevered: float, debt: Fact, price: float, shares: Fact, s: Mapping, as_of: date) -> tuple[Fact, float]:
    """(the levered beta as a Fact, the beta before the limits)."""
    market_value = price * shares.value
    beta, before = levered_beta(unlevered, debt.value, market_value, s["tax_rate"], s["beta_min"], s["beta_max"])
    formula = (f"industry unlevered beta {unlevered} × (1 + (1 − tax rate {_limit(s['tax_rate'])}) × financial debt "
               f"{_usd(debt.value)} ÷ market value of equity {_usd(market_value)})")
    if beta == before:
        return _derived("levered_beta", beta, "pure", as_of, f"{formula}; inside the limits {s['beta_min']} to "
                        f"{s['beta_max']}"), before
    limit = "upper" if before > s["beta_max"] else "lower"
    return Fact("levered_beta", beta, "pure", None, as_of, "assumption", None, None, None, None, None,
                f"{formula} = {before:.5f} before the limit; set to the {limit} limit ({beta})"), before


def _three_years(data: CompanyData, ends: tuple[date, ...] | list[date]):
    """((fiscal year end, operating cash flow, capital expenditure) per year, their plain average free cash flow, "")
    or ((), None, why) when a figure is missing or has a sign error."""
    rows = tuple((end, _figure(data, "operating_cash_flow", end), _figure(data, "capital_expenditure", end))
                 for end in ends)
    gaps = [f"{_label(f)}: {_unusable(f)}" for row in rows for f in row[1:] if _unusable(f)]
    if gaps:
        return (), None, "; ".join(gaps)
    return rows, sum(c.value - x.value for _, c, x in rows) / len(rows), ""


def _comparison(fcf0: float, average: float | None, why: str, threshold: float, years: int) -> str:
    """The one line on screen comparing the last twelve months with the fiscal years, or "" if they are close."""
    span = f"the last {_count(years)} fiscal years"
    if average is None:
        return (f"The free cash flow of the last twelve months cannot be compared with the average of {span}: {why}.")
    start = "the estimate starts from the last twelve months."
    if average <= 0:
        return (f"Free cash flow over the last twelve months ({_usd(fcf0)}) is far from {span}, which on average "
                f"produced no free cash flow ({_usd(average)}); {start}")
    change = fcf0 / average - 1
    if abs(change) <= threshold or math.isclose(abs(change), threshold, rel_tol=1e-9):
        return ""
    side = "above" if change > 0 else "below"
    return (f"Free cash flow over the last twelve months ({_usd(fcf0)}) is {abs(change):.1%} {side} the average of "
            f"{span} ({_usd(average)}); {start}")


def _growth_formula(first: Fact, last: Fact) -> str:
    intervals = YEARS - 1
    return (f"(revenue {_usd(last.value)}, fiscal year ended {_day(last.period_end)} ÷ revenue "
            f"{_usd(first.value)}, fiscal year ended {_day(first.period_end)})^(1/{intervals}) − 1")


def _starting_growth(first: Fact, last: Fact, s: Mapping) -> tuple[Fact, float]:
    """(g1 as a Fact, the past growth before any limit)."""
    past = (last.value / first.value) ** (1 / (YEARS - 1)) - 1
    formula = _growth_formula(first, last)
    cap, floor = s["growth_cap"], s["growth_floor"]
    for limit in (cap, floor):
        if abs(past - limit) <= AT_LIMIT:  # exactly at a limit (up to rounding): the limit itself, not "limited"
            return _derived("starting_growth", limit, "pure", last.period_end, formula,
                            start=first.period_end), past
    if floor <= past <= cap:
        return _derived("starting_growth", past, "pure", last.period_end, formula,
                        start=first.period_end), past
    name, limited = ("upper", cap) if past > cap else ("lower", floor)
    return Fact("starting_growth", limited, "pure", first.period_end, last.period_end, "assumption", None, None,
                None, None, None, f"past revenue growth {_growth(past)} a year before the limit ({formula}); "
                f"set to the {name} limit ({_limit(limited)})"), past


def _beta_text(before: float, limit: float) -> str:
    """The beta before the limit: two decimals, or more when two would print it as the limit itself (2.003 → "2.003")."""
    for decimals in range(2, 7):
        if round(before, decimals) != limit:
            return f"{before:.{decimals}f}"
    return f"{before:.6f}"


def _growth_note(past: float, g1: float, gt: float, s: Mapping) -> str:
    """The one factual line of SPEC §8.3 when the growth limit applies."""
    if past > s["growth_cap"]:
        return (f"Revenue grew {_growth(past)} a year over the last four years; the model starts at "
                f"{_limit(g1)} and lets growth slow towards {_limit(gt)}.")
    return (f"Revenue fell {_growth(-past)} a year over the last four years; the model starts at {_limit(g1)} "
            f"and lets growth recover towards {_limit(gt)}.")


# --- helpers ---------------------------------------------------------------------------------------------------------


def _figure(data: CompanyData, metric: str, fy_end: date) -> Fact:
    """The figure for one fiscal year; a year with no entry becomes a `missing` figure with its reason (SPEC §5.2)."""
    fact = data.fact(metric, fy_end)
    return fact if fact is not None else _missing(metric, fy_end, f"no figure for the fiscal year ended {_day(fy_end)}")


def _latest(data: CompanyData, metric: str, fy_end: date) -> Fact:
    """The latest figure (`CompanyData.recent`); none becomes a `missing` figure, never the annual one."""
    fact = data.recent.get(metric)
    if fact is not None:
        return fact
    return _missing(metric, fy_end, "no latest figure in the data", unit="shares" if metric == "shares" else "USD")


def _count(number: int) -> str:
    return WORDS.get(number, str(number))


def _missing(metric: str, end: date, why: str, unit: str = "USD") -> Fact:
    return Fact(metric, None, unit, None, end, "missing", None, None, None, None, None, why)


def _unusable(fact: Fact, on_sources_page: bool = True) -> str:
    """Why a company figure cannot be used, or "" if it can (SPEC §5.2, §5.4, §8.6)."""
    if fact.kind == "missing":
        return fact.note
    if fact.metric in ("capital_expenditure", "financial_debt") and fact.value < 0:
        what = "a payment is filed" if fact.metric == "capital_expenditure" else "debt is filed"
        why = f"negative ({_usd(fact.value)}), but {what} as a positive amount"
        # only a figure read from a filing has the data layer's SIGN warning (as in S7)
        if fact.kind == "reported" and on_sources_page:
            why += "; see the sign warning on the sources page"
        return why
    if fact.metric in ("revenue", "shares") and fact.value <= 0:
        amount = _usd(fact.value) if fact.unit == "USD" else f"{fact.value:,.0f}"
        return f"zero or negative ({amount})"
    return ""


def _market_gaps(price: float | None, risk_free: Fact | None, beta: Fact | None) -> list[str]:
    gaps = []
    if price is None:
        gaps.append("share price: not given")
    elif not math.isfinite(price):
        gaps.append("share price: not a usable number")
    elif price <= 0:
        gaps.append(f"share price: zero or negative ({price})")
    for fact, label, absent in ((risk_free, "risk-free rate", "not available at the moment"),
                                (beta, "industry beta", "not given (no industry benchmark)")):
        if fact is None:
            gaps.append(f"{label}: {absent}")
        elif fact.kind == "missing":
            gaps.append(f"{label}: {fact.note}")
        elif label == "industry beta" and fact.value <= 0:
            gaps.append(f"{label}: zero or negative ({fact.value})")
    return gaps


def _label(fact: Fact) -> str:
    return f"{LABELS.get(fact.metric, fact.metric)} for the fiscal year ended {_day(fact.period_end)}"


def _derived(metric: str, value: float, unit: str, end: date, formula: str, start: date | None = None) -> Fact:
    return Fact(metric, value, unit, start, end, "derived", None, None, None, None, None, formula)


def _usd(value: float) -> str:
    """An amount in USD as text: "USD 8,779 million", "USD 44.9 million", or in dollars below one million."""
    if abs(value) < 1_000_000:
        text = f"USD {value:,.0f}"
    else:
        text = f"USD {value / 1_000_000:,.1f}".removesuffix(".0") + " million"
    return text.replace("-", "−")


def _pct(ratio: float) -> str:
    """A rate in percent with three decimals, e.g. "9.033%"."""
    return f"{ratio:.3%}".replace("-", "−")


def _growth(ratio: float) -> str:
    """A past growth rate with one decimal, as in SPEC §8.2: "68.3%"."""
    return f"{ratio:.1%}".replace("-", "−")


def _limit(ratio: float) -> str:
    """A setting in percent without misleading rounding: "30%", "2.5%", "−10%"."""
    return (f"{ratio * 100:.2f}".rstrip("0").rstrip(".") + "%").replace("-", "−")


def _day(day: date) -> str:
    return f"{day.day} {day:%B %Y}"
