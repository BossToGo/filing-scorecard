"""Dividend checks D1–D6 (SPEC §7, slice S7). Owner: C (Flo).

A pure function: `CompanyData` and the settings in, six `CheckResult`s out. No network, no files, no interface
(SPEC §11). The thresholds come from the `dividend` section of `app/settings.yaml`.

    from src.settings import load_settings
    results = dividend_checks(data, load_settings())     # D1, D2, D3, D4, D5, D6

The rules, in order:
1. D1: dividends paid in FY0 > 0. A missing or negative figure gives "insufficient data"; a labelled nil (plan Q1,
   Amazon) or a reported zero is a fail: "no dividend paid".
2. If D1 fails, D2 to D6 are "not applicable" and the area shows "no dividend paid", score 0 (SPEC §7). This
   applies only when D1 fails, never when its figure is missing: a payer is never shown as paying none.
3. Otherwise each of D2 to D6 is assessed on its own; any input it needs that is missing, not in the data, or a
   negative dividends paid figure gives "insufficient data".

Decisions (Flo, 22 November 2026):
- D2 is "not assessed" (status insufficient_data, plan Q9) until slice S9 adds the share price and the market yield.
- D3: a cut is "this year < (1 − max_dividend_cut) × last year", so no division and a rise from a year of zero is
  never a cut. Its value is the lowest year-on-year change among the years whose previous year is above zero.
- A fiscal year that is not in the data is a missing input (D3 and D4 need five fiscal years, FY-4 to FY0).
- D5 with net income zero or negative fails with the reason in plain words and shows no payout ratio.
- A negative payment (dividends paid or capital expenditure) is a sign error (SPEC §5.4) that the data layer keeps
  as filed and flags; it is never flipped (§5.2: never guessed). Every check that uses that figure is "insufficient
  data", naming the sign. (Capital expenditure added after the review of 22 November.)
- D3 passes with no value when no step starts from a year above zero (e.g. 0, 0, 0, 0, 5): no cut happened.

FY0 is the latest fiscal year of revenue and FY-4 the fifth latest, as for every other check.
"""

from __future__ import annotations

from datetime import date
from typing import Mapping

from src.contracts import CheckResult, CompanyData, Fact

NO_DIVIDEND = "no dividend paid"  # what the dividend area shows when D1 fails (SPEC §7)
PAYMENTS = ("dividends_paid", "capital_expenditure")  # filed as positive amounts; negative means a sign error
YEARS = 5  # FY-4 to FY0
LABELS = {
    "dividends_paid": "dividends paid",
    "net_income": "net income",
    "operating_cash_flow": "operating cash flow",
    "capital_expenditure": "capital expenditure",
}


def dividend_checks(data: CompanyData, settings: Mapping[str, Mapping]) -> tuple[CheckResult, ...]:
    """D1 to D6 for one company, in that order."""
    max_cut = float(settings["dividend"]["max_dividend_cut"])
    max_payout = float(settings["dividend"]["max_payout_ratio"])
    years = data.fiscal_years("revenue")[-YEARS:]
    if not years:
        reason = "Insufficient data: the company has no fiscal year with figures."
        return tuple(CheckResult(f"D{n}", "insufficient_data", None, None, (), reason) for n in range(1, 7))

    dividends_fy0 = _figure(data, "dividends_paid", years[-1])
    d1 = _d1(dividends_fy0)
    if d1.status == "fail":
        reason = f"Not applicable: {NO_DIVIDEND} in the fiscal year ended {_day(years[-1])} (D1)."
        return (d1,) + tuple(CheckResult(f"D{n}", "not_applicable", None, None, (dividends_fy0,), reason)
                             for n in range(2, 7))
    return (
        d1,
        _d2(dividends_fy0),
        _d3(data, years, max_cut),
        _d4(data, years),
        _d5(data, years[-1], max_payout),
        _d6(data, years[-1]),
    )


# --- the six checks ------------------------------------------------------------------------------------------------


def _d1(dividends: Fact) -> CheckResult:
    blocked = _blocked("D1", (dividends,))
    if blocked:
        return blocked
    year = _day(dividends.period_end)
    if dividends.value > 0:
        return CheckResult("D1", "pass", dividends.value, 0.0, (dividends,),
                           f"Dividends paid in the fiscal year ended {year}: {_usd(dividends.value)}.")
    if dividends.kind == "assumption" and "treated as nil" in dividends.note:
        # Plan Q1: the data layer's nil. Its full note (tags searched) stays with the figure for the sources page.
        why = "dividends paid are not reported in any of the five fiscal years, so they are treated as nil"
    else:
        typed = f" ({dividends.note})" if dividends.kind == "assumption" else ""
        why = f"dividends paid {_usd(dividends.value)}{typed}"
    return CheckResult("D1", "fail", dividends.value, 0.0, (dividends,),
                       f"No dividend paid in the fiscal year ended {year}: {why}.")


def _d2(dividends: Fact) -> CheckResult:
    return CheckResult("D2", "insufficient_data", None, None, (dividends,),
                       "This check is not assessed yet: it needs the share price and the US market dividend yield.")


def _d3(data: CompanyData, years: list[date], max_cut: float) -> CheckResult:
    facts = [_figure(data, "dividends_paid", end) for end in years]
    if len(years) < YEARS:
        return _too_few_years("D3", facts, len(years))
    blocked = _blocked("D3", facts)
    if blocked:
        return blocked

    changes = []  # (change, last year, this year), only where last year is above zero
    for last, this in zip(facts, facts[1:]):
        if last.value > 0:
            changes.append((this.value / last.value - 1, last, this))
    cuts = [(last, this) for _, last, this in changes if this.value < (1 - max_cut) * last.value]
    if not changes:
        return CheckResult("D3", "pass", None, -max_cut, facts,
                           "No cut: there is no earlier year with a dividend to compare with.")
    lowest, last, this = min(changes, key=lambda c: c[0])
    fall = (f"from {_usd(last.value)} (fiscal year ended {_day(last.period_end)}) to {_usd(this.value)} "
            f"({_day(this.period_end)}), a change of {_pct(lowest)}")
    if cuts:
        return CheckResult("D3", "fail", lowest, -max_cut, facts,
                           f"Dividends paid fell by more than {_limit(max_cut)} in a year: {fall}.")
    return CheckResult("D3", "pass", lowest, -max_cut, facts,
                       f"No year-on-year fall of more than {_limit(max_cut)} in five years. The lowest change was "
                       f"{fall}.")


def _d4(data: CompanyData, years: list[date]) -> CheckResult:
    now = _figure(data, "dividends_paid", years[-1])
    if len(years) < YEARS:
        return _too_few_years("D4", [now], len(years))
    then = _figure(data, "dividends_paid", years[0])
    inputs = (now, then)
    blocked = _blocked("D4", inputs)
    if blocked:
        return blocked
    status = "pass" if now.value > then.value else "fail"
    return CheckResult("D4", status, now.value, then.value, inputs,
                       f"Dividends paid {_usd(now.value)} in the fiscal year ended {_day(now.period_end)}, against "
                       f"{_usd(then.value)} four years earlier ({_day(then.period_end)}).")


def _d5(data: CompanyData, fy0: date, max_payout: float) -> CheckResult:
    dividends = _figure(data, "dividends_paid", fy0)
    earnings = _figure(data, "net_income", fy0)
    inputs = (dividends, earnings)
    blocked = _blocked("D5", inputs)
    if blocked:
        return blocked
    if earnings.value <= 0:
        return CheckResult("D5", "fail", None, max_payout, inputs,
                           f"Net income is zero or negative ({_usd(earnings.value)} in the fiscal year ended "
                           f"{_day(fy0)}), so earnings do not cover the dividend.")
    payout = dividends.value / earnings.value
    status = "pass" if payout < max_payout else "fail"
    return CheckResult("D5", status, payout, max_payout, inputs,
                       f"Dividends paid are {_pct(payout)} of net income ({_usd(dividends.value)} of "
                       f"{_usd(earnings.value)}, fiscal year ended {_day(fy0)}); the limit is below "
                       f"{_limit(max_payout)}.")


def _d6(data: CompanyData, fy0: date) -> CheckResult:
    dividends = _figure(data, "dividends_paid", fy0)
    cash_flow = _figure(data, "operating_cash_flow", fy0)
    capex = _figure(data, "capital_expenditure", fy0)
    inputs = (dividends, cash_flow, capex)
    blocked = _blocked("D6", inputs)
    if blocked:
        return blocked
    free_cash_flow = cash_flow.value - capex.value
    status = "pass" if dividends.value <= free_cash_flow else "fail"
    return CheckResult("D6", status, dividends.value, free_cash_flow, inputs,
                       f"Dividends paid {_usd(dividends.value)} against operating cash flow minus capital "
                       f"expenditure of {_usd(free_cash_flow)} ({_usd(cash_flow.value)} − {_usd(capex.value)}, "
                       f"fiscal year ended {_day(fy0)}).")


# --- helpers -------------------------------------------------------------------------------------------------------


def _figure(data: CompanyData, metric: str, fy_end: date) -> Fact:
    """The figure for one fiscal year; a year with no entry at all becomes a `missing` figure with its reason, so
    the result still lists what it needed (SPEC §5.2)."""
    fact = data.fact(metric, fy_end)
    if fact is not None:
        return fact
    return Fact(metric, None, "USD", None, fy_end, "missing", None, None, None, None, None,
                f"no {LABELS[metric]} figure for the fiscal year ended {_day(fy_end)}")


def _unusable(fact: Fact) -> str:
    """Why a figure cannot be used, or "" if it can: it is missing (SPEC §5.2), or it is a negative payment, a sign
    error the data layer keeps as filed and flags (SPEC §5.4)."""
    if fact.kind == "missing":
        return fact.note
    if fact.metric in PAYMENTS and fact.value < 0:
        return (f"negative ({_usd(fact.value)}), but a payment is filed as a positive amount; see the sign warning "
                "on the sources page")
    return ""


def _blocked(check_id: str, inputs) -> CheckResult | None:
    """"Insufficient data" naming each input that cannot be used, or None when all of them can."""
    gaps = [f"{LABELS.get(f.metric, f.metric)} for the fiscal year ended {_day(f.period_end)}: {why}"
            for f in inputs if (why := _unusable(f))]
    if not gaps:
        return None
    return CheckResult(check_id, "insufficient_data", None, None, tuple(inputs),
                       f"Insufficient data: {'; '.join(gaps)}.")


def _too_few_years(check_id: str, inputs, found: int) -> CheckResult:
    return CheckResult(check_id, "insufficient_data", None, None, tuple(inputs),
                       f"Insufficient data: needs dividends paid for five fiscal years (four years earlier to the "
                       f"latest); the data has {found}.")


def _usd(value: float) -> str:
    """An amount in USD as text: "USD 8,779 million", "USD 44.9 million", or in dollars below one million
    ("USD 40,000"), so that a small amount never reads as zero."""
    if abs(value) < 1_000_000:
        text = f"USD {value:,.0f}"
    else:
        text = f"USD {value / 1_000_000:,.1f}".removesuffix(".0") + " million"
    return text.replace("-", "−")


def _pct(ratio: float) -> str:
    """A change or a ratio in percent with two decimals, e.g. "−10.20%"."""
    return f"{ratio:.2%}".replace("-", "−")


def _limit(ratio: float) -> str:
    """A threshold from the settings in percent, without misleading rounding: "10%", "12.5%"."""
    return (f"{ratio * 100:.2f}".rstrip("0").rstrip(".") or "0") + "%"


def _day(day: date) -> str:
    return f"{day.day} {day:%B %Y}"
