"""Valuation checks V1–V6 (SPEC §7, §8.6; slice S9). Owner: C (Flo).

A pure function: `CompanyData`, the settings, the engine's `Valuation`, the share price and three benchmarks in, six
`CheckResult`s out. No network, no files, no interface (SPEC §11). The engine is run by the caller, once, at the
same share price: the screen shows the estimate from that same `Valuation`, so the checks and the screen never
disagree.

    from src.valuation.equity_method import value_company
    v = value_company(data, settings, share_price=price, risk_free_rate=rf, unlevered_beta=beta)
    results = valuation_checks(data, settings, v, share_price=price, industry_pe=pe, market_pe=market_pe,
                               industry_pb=pb)                       # V1, V2, V3, V4, V5, V6
    estimate_gap(price, v.fair_value.value)                          # for G7 and W8: 0.49 = "49.0% above"

The checks (SPEC §7). On screen the engine's result is "the estimate", never "fair value" (SPEC §3):
- V1 "Price below the cash-flow estimate": share price < estimate.
- V2 "Price at or below 80% of the estimate": share price ≤ `well_below_fair_value` × estimate.
- V3 "Price to earnings below industry", V4 "... below the US market": (price × shares) ÷ net income FY0 <
  benchmark. Net income ≤ 0: fail, with no ratio.
- V5 "Price to book below industry": (price × shares) ÷ equity FY0 < benchmark. Equity ≤ 0: fail, with no ratio.
- V6 "Price does not demand heroic growth": share price ≤ the estimate with starting growth at `growth_cap`.

Rules, in order (Flo's decisions, 25 November 2026):
1. No usable share price or no usable share count: the whole area is "insufficient data" (SPEC §7, §8.6). One
   exception (slice S8b): the estimate uses the latest share count (`CompanyData.recent`), V3 to V5 the annual one.
   When only the annual count is unusable and there is an estimate, V1, V2 and V6 are assessed, so that the checks and
   the estimate on screen never disagree.
2. V1, V2 and V6: when the engine has no estimate ("insufficient_data" or "not_applicable", SPEC §8.6), they take
   its status and its reason, word for word. V3 to V5 are still assessed.
3. V3 to V5: a missing net income or equity is "insufficient data"; net income ≤ 0 (V3, V4) or equity ≤ 0 (V5) is a
   fail even when the benchmark is missing; only then does a missing benchmark give "insufficient data". Such a
   fail shows no ratio and no benchmark, and does not list the benchmark among its inputs (it was not used).
Other decisions:
- (a) A price equal to the estimate fails V1 and reads "at the estimate". Otherwise the gap is (price − estimate) ÷
  estimate, shown with one decimal: "49.0% above the estimate" or "25.0% below the estimate". The unrounded values
  are compared first.
- (b) V6 keeps its own ≤ rule also when the starting growth is already at the cap (Nvidia, or past growth of exactly
  30%), and says that it then uses the same estimate as V1. With a price equal to that estimate, V1 fails and V6
  passes.
- Review of 25 November (Flo: "yes, as recommended"): a benchmark of zero or below is "insufficient data", like
  an industry beta ≤ 0 in the engine; a ratio that would round to its benchmark is shown with more decimals; V2 and
  V6 say "above", "below" or "equal to"; an unusable share price reads "the share price must be a number above
  zero".
- Review round 2 (Flo: option A): two values that differ by less than one billionth (relative, `TIE`) are equal,
  in every comparison: V1, V3, V4 and V5 (strictly below) fail, V2 and V6 (at or below) pass, and the texts show
  "at the estimate", "equal to" and two decimals. Without it, 2.01 × 1,000,000 ÷ 100,000, exactly 20.1 by hand, is
  20.099999999999998 in the computer and would pass "below 20.1".
- (d) The share price is the user's input, not a `Fact`: it has no filing and no date. It is the value of V1, V2
  and V6 and is named in their texts; the screen shows it as "the price you typed".
"""

from __future__ import annotations

import math
from datetime import date
from typing import Mapping

from src.contracts import CheckResult, CompanyData, Fact
from src.valuation.equity_method import Valuation, _day, _limit, _usd

PRICE_CHECKS = ("V1", "V2", "V6")  # the checks that need the estimate (SPEC §8.6)
TIE = 1e-9  # two values this close (relative) are equal: computer rounding, not a real difference (review round 2)
MAX_DECIMALS = 15  # enough for two values that are not a tie (more than TIE apart) to print differently


def estimate_gap(share_price: float, estimate: float) -> float:
    """(price − estimate) ÷ estimate: above zero means the price is above the estimate (G7, W8; SPEC §9).

    Call it only when V1 was assessed (the engine returned an estimate, `Valuation.status == "ok"`). A tie (equal up
    to computer rounding, option A) is plain 0, never −0.0% (Igor's review of #52)."""
    if _equal(share_price, estimate):
        return 0.0
    return (share_price - estimate) / estimate


def valuation_checks(data: CompanyData, settings: Mapping[str, Mapping], valuation: Valuation, *,
                     share_price: float | None, industry_pe: Fact | None, market_pe: Fact | None,
                     industry_pb: Fact | None) -> tuple[CheckResult, ...]:
    """V1 to V6 for one company, in that order."""
    s = settings["valuation"]
    years = data.fiscal_years("revenue")
    shares = data.latest("shares")

    # 1. The whole area needs a share price and a share count.
    gaps = []
    if share_price is None:
        gaps.append("the valuation checks need the share price; type it in to assess them")
    elif not math.isfinite(share_price) or share_price <= 0:
        gaps.append("the share price must be a number above zero")
    if shares is None or shares.kind == "missing":
        gaps.append("the share count is missing" + (f" ({shares.note})" if shares is not None else ""))
    elif shares.value <= 0:
        gaps.append(f"the share count is zero or negative ({shares.value:,.0f})")
    if not years:
        gaps.append("the company has no fiscal year with figures")
    if gaps:
        reason = f"Insufficient data: {'; '.join(gaps)}."
        inputs = (shares,) if shares is not None else ()
        blocked = tuple(CheckResult(f"V{n}", "insufficient_data", None, None, inputs, reason) for n in range(1, 7))
        only_the_count = len(gaps) == 1 and gaps[0].startswith("the share count")
        if only_the_count and valuation.status == "ok":  # the estimate has its own, latest, share count
            v1, v2, v6 = _price_checks(valuation, share_price, s)
            return (v1, v2, *blocked[2:5], v6)
        return blocked

    fy0 = years[-1]
    market_value = share_price * shares.value
    earnings = _figure(data, "net_income", fy0)
    equity = _figure(data, "equity", fy0)
    v1, v2, v6 = _price_checks(valuation, share_price, s)
    v3 = _price_to_earnings("V3", share_price, market_value, earnings, shares, industry_pe, "the industry")
    v4 = _price_to_earnings("V4", share_price, market_value, earnings, shares, market_pe, "the US market")
    v5 = _price_to_book(share_price, market_value, equity, shares, industry_pb)
    return v1, v2, v3, v4, v5, v6


# --- V1, V2, V6: the price against the estimate ----------------------------------------------------------------------


def _price_checks(v: Valuation, price: float, s: Mapping) -> tuple[CheckResult, CheckResult, CheckResult]:
    if v.status != "ok":
        # SPEC §8.6: no estimate; the engine's reason is shown as it is (it never says "fair value").
        return tuple(CheckResult(c, v.status, None, None, v.inputs, v.reason) for c in PRICE_CHECKS)

    estimate = v.fair_value.value
    inputs = v.inputs + (v.fair_value,)
    # Each text prints the price and what it is compared with by `_two_prices`: two different amounts never read the
    # same (Igor's review of #52: "USD 14.85, is above USD 14.85").
    shown, other = _two_prices(price, estimate)
    v1 = CheckResult("V1", "pass" if _below(price, estimate) else "fail", price, estimate, inputs,
                     f"The share price you typed, {shown}, is {_gap_text(price, estimate)} of {other} per share.")

    limit = s["well_below_fair_value"] * estimate
    shown, other = _two_prices(price, limit)
    v2 = CheckResult("V2", "pass" if not _above(price, limit) else "fail", price, limit, inputs,
                     f"The share price you typed, {shown}, is {_versus(price, limit)} {other}, which is "
                     f"{_limit(s['well_below_fair_value'])} of the estimate ({_price(estimate)}).")

    at_cap = v.fair_value_at_growth_cap
    shown, other = _two_prices(price, at_cap.value)
    text = (f"The share price you typed, {shown}, is {_versus(price, at_cap.value)} the estimate with starting growth "
            f"at the {_limit(s['growth_cap'])} cap ({other}).")
    if v.starting_growth is not None and v.starting_growth.value == s["growth_cap"]:
        text += (f" The company's starting growth is already at the {_limit(s['growth_cap'])} cap, so V6 uses the "
                 "same estimate as V1.")
    v6 = CheckResult("V6", "pass" if not _above(price, at_cap.value) else "fail", price, at_cap.value,
                     v.inputs + (at_cap,), text)
    return v1, v2, v6


def _equal(a: float, b: float) -> bool:
    """Equal up to computer rounding (`TIE`)."""
    return math.isclose(a, b, rel_tol=TIE, abs_tol=0.0)


def _below(a: float, b: float) -> bool:
    """Strictly below, and not merely by computer rounding."""
    return a < b and not _equal(a, b)


def _above(a: float, b: float) -> bool:
    """Strictly above, and not merely by computer rounding."""
    return a > b and not _equal(a, b)


def _versus(price: float, other: float) -> str:
    """"above", "below" or "equal to", from the unrounded values (equal up to computer rounding)."""
    return "equal to" if _equal(price, other) else "above" if price > other else "below"


def _gap_text(price: float, estimate: float) -> str:
    """"at the estimate", or "49.0% above the estimate" / "25.0% below the estimate" (decision a)."""
    if _equal(price, estimate):  # the unrounded values, before any rounding (up to computer rounding)
        return "at the estimate"
    gap = estimate_gap(price, estimate)
    return f"{abs(gap):.1%} {'above' if gap > 0 else 'below'} the estimate"


# --- V3, V4, V5: price to earnings and price to book -----------------------------------------------------------------


def _price_to_earnings(check_id: str, price: float, market_value: float, earnings: Fact, shares: Fact,
                       benchmark: Fact | None, against: str) -> CheckResult:
    inputs = _inputs(earnings, shares, benchmark)
    if earnings.kind == "missing":
        return _insufficient(check_id, inputs, f"net income for the fiscal year ended {_day(earnings.period_end)}: "
                                               f"{earnings.note}")
    year = f"fiscal year ended {_day(earnings.period_end)}"
    if earnings.value == 0:
        return CheckResult(check_id, "fail", None, None, inputs[:2],
                           f"Net income is zero ({year}): with no earnings, the price is not covered by any profit.")
    if earnings.value < 0:
        return CheckResult(check_id, "fail", None, None, inputs[:2],
                           f"The company made a loss (net income {_usd(earnings.value)}, {year}), so a price to "
                           "earnings ratio is not meaningful.")
    gap = _benchmark_gap(benchmark, f"the price to earnings ratio of {against}")
    if gap:
        return _insufficient(check_id, inputs, gap)
    ratio = market_value / earnings.value
    shown, bench = _two_numbers(ratio, benchmark.value)
    return CheckResult(check_id, "pass" if _below(ratio, benchmark.value) else "fail", ratio, benchmark.value, inputs,
                       f"Price to earnings {shown} (share price {_price(price)} × {shares.value:,.0f} shares = "
                       f"{_usd(market_value)}, ÷ net income {_usd(earnings.value)}, {year}) against "
                       f"{bench} for {against}.")


def _price_to_book(price: float, market_value: float, equity: Fact, shares: Fact,
                   benchmark: Fact | None) -> CheckResult:
    inputs = _inputs(equity, shares, benchmark)
    if equity.kind == "missing":
        return _insufficient("V5", inputs, f"equity on {_day(equity.period_end)}: {equity.note}")
    on = _day(equity.period_end)
    if equity.value == 0:
        return CheckResult("V5", "fail", None, None, inputs[:2],
                           f"The equity is zero on {on}, so a price to book ratio is not meaningful.")
    if equity.value < 0:
        return CheckResult("V5", "fail", None, None, inputs[:2],
                           f"The company has negative equity ({_usd(equity.value)} on {on}), so a price to book "
                           "ratio is not meaningful.")
    gap = _benchmark_gap(benchmark, "the price to book ratio of the industry")
    if gap:
        return _insufficient("V5", inputs, gap)
    ratio = market_value / equity.value
    shown, bench = _two_numbers(ratio, benchmark.value)
    return CheckResult("V5", "pass" if _below(ratio, benchmark.value) else "fail", ratio, benchmark.value, inputs,
                       f"Price to book {shown} (share price {_price(price)} × {shares.value:,.0f} shares = "
                       f"{_usd(market_value)}, ÷ equity {_usd(equity.value)} on {on}) against "
                       f"{bench} for the industry.")


# --- helpers ---------------------------------------------------------------------------------------------------------


def _figure(data: CompanyData, metric: str, fy_end: date) -> Fact:
    """The FY0 figure; a year with no entry becomes a `missing` figure with its reason (SPEC §5.2)."""
    fact = data.fact(metric, fy_end)
    if fact is not None:
        return fact
    return Fact(metric, None, "USD", None, fy_end, "missing", None, None, None, None, None,
                f"no figure for the fiscal year ended {_day(fy_end)}")


def _inputs(figure: Fact, shares: Fact, benchmark: Fact | None) -> tuple[Fact, ...]:
    return (figure, shares) + ((benchmark,) if benchmark is not None else ())


def _benchmark_gap(benchmark: Fact | None, what: str) -> str:
    """Why the benchmark cannot be used, or "" if it can."""
    if benchmark is None:
        return f"{what}: not available (no benchmark for this company)"
    if benchmark.kind == "missing":
        return f"{what}: {benchmark.note}"
    if benchmark.value <= 0:  # review decision 1 (Flo): not usable, like an industry beta ≤ 0 in the engine
        return f"{what}: zero or negative ({benchmark.value:g}), so it cannot be compared".replace("-", "−")
    return ""


def _insufficient(check_id: str, inputs: tuple[Fact, ...], why: str) -> CheckResult:
    return CheckResult(check_id, "insufficient_data", None, None, inputs, f"Insufficient data: {why}.")


def _two_numbers(value: float, benchmark: float) -> tuple[str, str]:
    """Both numbers with two decimals, or with more when two would show different numbers as the same (19.999
    against 20 reads "19.999 against 20.000", never "20.00 against 20.00" next to a pass). Equal numbers keep two."""
    for decimals in range(2, MAX_DECIMALS + 1):
        a, b = (f"{x:.{decimals}f}" for x in (value, benchmark))
        if a != b or _equal(value, benchmark):
            return a, b
    return a, b


def _two_prices(price: float, other: float) -> tuple[str, str]:
    """Two amounts in USD with cents, or with more decimals when cents would show different amounts as the same
    ("USD 14.8500 against USD 14.8504"); equal amounts (up to computer rounding) keep cents."""
    for decimals in range(2, MAX_DECIMALS + 1):
        a, b = (f"USD {x:,.{decimals}f}".replace("-", "−") for x in (price, other))
        if a != b or _equal(price, other):
            return a, b
    return a, b


def _price(value: float) -> str:
    """A price per share in USD with cents: "USD 30.00"."""
    return f"USD {value:,.2f}".replace("-", "−")
