"""S6: H1–H6, SPEC §7. Pure functions; source facts in, six CheckResults out.

    results = health_checks(company, settings=settings['financial_health'])

Amounts are USD; ratios are decimals and interest cover is a multiple. A missing
amount is never zero. No-debt/zero-interest rules do not manufacture an infinite ratio.
Appendix A values: tests/unit/test_b_appendix_a.py (signed off by Greg on PR #5, 24 November 2026).
"""
from __future__ import annotations

import math
from collections.abc import Mapping

from src.contracts import CheckResult, CompanyData
from src.checks._b_inputs import Inputs, compared, day, missing, money, rational, result, unavailable


def health_checks(data: CompanyData, *, settings: Mapping[str, float]) -> tuple[CheckResult, ...]:
    """Return H1–H6 in order. Pass the financial_health settings section."""
    limits = {}
    for name in ("max_net_debt_to_equity", "min_operating_cash_flow_to_debt", "min_interest_cover"):
        value = settings[name]
        if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value) or value <= 0:
            raise ValueError(f"{name} must be a positive finite number, with rates stored as decimals.")
        limits[name] = value
    inputs = Inputs(data)
    checks = []
    assets, current, liabilities = (inputs.fact(m) for m in ("current_assets", "current_liabilities", "total_liabilities"))

    cover = assets, current
    if missing(cover):
        checks.append(unavailable("H1", cover, "Short-term cover cannot be assessed because a short-term asset or liability figure is missing."))
    else:
        checks.append(result("H1", assets.value > current.value, assets.value, current.value, cover,
                             f"On {day(assets.period_end)}, short-term assets were {money(assets.value)}, {compared(assets.value > current.value)} short-term liabilities of {money(current.value)}. Assets must be higher to pass."))

    long_cover = assets, liabilities, current
    if missing(long_cover):
        checks.append(unavailable("H2", long_cover, "Long-term cover cannot be assessed because short-term assets, total liabilities or short-term liabilities are missing."))
    else:
        long_term = rational(liabilities.value) - rational(current.value)
        covered = rational(assets.value) > long_term
        checks.append(result("H2", covered, assets.value, float(long_term), long_cover,
                             f"On {day(assets.period_end)}, short-term assets were {money(assets.value)}, {compared(covered)} long-term liabilities of {money(float(long_term))} (total liabilities of {money(liabilities.value)} less short-term liabilities of {money(current.value)}). Assets must be higher to pass."))

    debt, cash, equity = (inputs.fact(m) for m in ("financial_debt", "cash", "equity"))
    leverage = debt, cash, equity
    if equity.kind != "missing" and equity.value <= 0:
        checks.append(result("H3", False, None, None, (equity,),
                             f"Negative equity: shareholder equity was {money(equity.value)} on {day(equity.period_end)}. Zero or negative equity fails this check; no debt-to-equity ratio is calculated."))
    elif missing(leverage):
        checks.append(unavailable("H3", leverage, "Debt cover cannot be assessed because a debt, cash or shareholder equity figure is missing."))
    elif debt.value < 0:
        checks.append(unavailable("H3", leverage,
                                  f"Financial debt was {money(debt.value)} on {day(debt.period_end)}. This negative debt figure needs checking before debt cover can be assessed."))
    else:
        ratio = (rational(debt.value) - rational(cash.value)) / rational(equity.value)
        limit = limits["max_net_debt_to_equity"]
        moderate = ratio < rational(limit)
        checks.append(result("H3", moderate, float(ratio), limit, leverage,
                             f"On {day(equity.period_end)}, financial debt of {money(debt.value)} less cash of {money(cash.value)} was about {float(ratio):.2%} of shareholder equity of {money(equity.value)}, {compared(moderate, 'below', 'not below')} the limit of {limit:.2%}. It must be below to pass."))

    old_debt, old_equity = inputs.fact("financial_debt", 4), inputs.fact("equity", 4)
    debt_pair = debt, old_debt
    debt_trend = debt, equity, old_debt, old_equity
    known_equity = tuple(f for f in (equity, old_equity) if f.kind != "missing")
    if any(f.value <= 0 for f in known_equity):
        checks.append(result("H4", False, None, None, known_equity,
                             "Negative equity: " + "; ".join(
                                 f"shareholder equity was {money(f.value)} on {day(f.period_end)}"
                                 for f in known_equity if f.value <= 0)
                             + ". Zero or negative equity at either comparison date fails this check; no debt-to-equity ratio is calculated."))
    elif not missing(debt_pair) and debt.value == 0 and old_debt.value == 0:
        checks.append(result("H4", True, None, None, debt_pair,
                             f"No debt: financial debt was {money(old_debt.value)} on {day(old_debt.period_end)} and {money(debt.value)} on {day(debt.period_end)}. This passes the debt-trend check without dividing by shareholder equity."))
    elif missing(debt_trend):
        checks.append(unavailable("H4", debt_trend, "The debt trend cannot be assessed because debt or shareholder equity is missing at the latest annual-report date or four years earlier."))
    elif debt.value < 0 or old_debt.value < 0:
        checks.append(unavailable("H4", debt_trend,
                                  "Financial debt needs checking: " + "; ".join(
                                      f"the figure was {money(f.value)} on {day(f.period_end)}"
                                      for f in debt_pair if f.value < 0)
                                  + ". A negative debt figure cannot establish a meaningful debt trend."))
    else:
        now = rational(debt.value) / rational(equity.value)
        old = rational(old_debt.value) / rational(old_equity.value)
        falling = now < old
        checks.append(result("H4", falling, float(now), float(old), debt_trend,
                             f"Financial debt of {money(debt.value)} was about {float(now):.2%} of shareholder equity of {money(equity.value)} on {day(equity.period_end)}, {compared(falling, 'down from', 'not below')} about {float(old):.2%} on {day(old_equity.period_end)} (debt of {money(old_debt.value)}, equity of {money(old_equity.value)}). The later share must be lower to pass; cash is not deducted from debt."))

    cash_flow = inputs.fact("operating_cash_flow")
    cash_cover = cash_flow, debt
    if debt.kind != "missing" and debt.value == 0:
        checks.append(result("H5", True, None, limits["min_operating_cash_flow_to_debt"], (debt,),
                             f"No debt: financial debt was {money(debt.value)} on {day(debt.period_end)}. This passes the cash-flow cover check without dividing by zero."))
    elif missing(cash_cover):
        checks.append(unavailable("H5", cash_cover, "Cash-flow cover cannot be assessed because operating cash flow or financial debt is missing."))
    elif debt.value < 0:
        checks.append(unavailable("H5", cash_cover,
                                  f"Financial debt was {money(debt.value)} on {day(debt.period_end)}. A negative debt figure does not give meaningful cash-flow cover."))
    else:
        ratio = rational(cash_flow.value) / rational(debt.value)
        limit = limits["min_operating_cash_flow_to_debt"]
        covered = ratio >= rational(limit)
        checks.append(result("H5", covered, float(ratio), limit, cash_cover,
                             f"Operating cash flow of {money(cash_flow.value)} for the year ended {day(cash_flow.period_end)} covered about {float(ratio):.2%} of financial debt of {money(debt.value)}, {compared(covered, 'at or above', 'below')} the required {limit:.2%}."))

    operating, interest = inputs.fact("operating_income"), inputs.fact("interest_expense")
    interest_cover = operating, interest
    if interest.kind != "missing" and interest.value == 0:
        checks.append(result("H6", True, None, limits["min_interest_cover"], (interest,),
                             f"Interest expense was zero ({money(interest.value)}) for the year ended {day(interest.period_end)}. This passes the interest-cover check without dividing by zero."))
    elif interest.kind == "missing" and debt.kind == "reported" and debt.value == 0:
        checks.append(result("H6", True, None, limits["min_interest_cover"], (debt,),
                             f"No debt: financial debt was reported as zero ({money(debt.value)}) on {day(debt.period_end)}. This passes the no-debt exception. Interest expense remains missing and no interest-cover ratio is calculated."))
    elif missing(interest_cover):
        checks.append(unavailable("H6", interest_cover, "Interest cover cannot be assessed because operating profit or interest expense is missing. Missing interest is not zero."))
    elif interest.value < 0:
        checks.append(unavailable("H6", interest_cover,
                                  f"Interest expense was {money(interest.value)} for the year ended {day(interest.period_end)}. A negative interest expense does not give meaningful interest cover."))
    else:
        ratio = rational(operating.value) / rational(interest.value)
        limit = limits["min_interest_cover"]
        covered = ratio >= rational(limit)
        checks.append(result("H6", covered, float(ratio), limit, interest_cover,
                             f"Operating profit of {money(operating.value)} covered interest expense of {money(interest.value)} about {float(ratio):.2f} times for the year ended {day(operating.period_end)}, {compared(covered, 'at or above', 'below')} the required {limit:g} times."))
    return tuple(checks)
