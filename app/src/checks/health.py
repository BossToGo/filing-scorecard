"""S6: H1–H6, SPEC §7. Pure functions; source facts in, six CheckResults out.

    results = health_checks(company, settings=settings['financial_health'])

Amounts are USD; ratios are decimals and interest cover is a multiple. A missing
amount is never zero. No-debt/zero-interest rules do not manufacture an infinite ratio.
Known-answer acceptance remains pending Greg's own Appendix A calculation sign-off.
"""
from __future__ import annotations

import math
from collections.abc import Mapping

from src.contracts import CheckResult, CompanyData
from src.checks._b_inputs import Inputs, missing, rational, result, unavailable


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
        checks.append(unavailable("H1", cover, "Current assets and current liabilities are required."))
    else:
        checks.append(result("H1", assets.value > current.value, assets.value, current.value, cover,
                             "Current assets > current liabilities at FY0 (USD)."))

    long_cover = assets, liabilities, current
    if missing(long_cover):
        checks.append(unavailable("H2", long_cover, "Current assets, total liabilities and current liabilities are required."))
    else:
        long_term = liabilities.value - current.value
        covered = rational(assets.value) > rational(liabilities.value) - rational(current.value)
        checks.append(result("H2", covered, assets.value, long_term, long_cover,
                             "Current assets > total liabilities - current liabilities at FY0 (USD)."))

    debt, cash, equity = (inputs.fact(m) for m in ("financial_debt", "cash", "equity"))
    leverage = debt, cash, equity
    if equity.kind != "missing" and equity.value <= 0:
        checks.append(result("H3", False, None, None, (equity,), "Negative equity: equity is zero or negative; no debt/equity ratio is calculated."))
    elif missing(leverage):
        checks.append(unavailable("H3", leverage, "Debt, cash and positive equity are required."))
    elif debt.value < 0:
        checks.append(unavailable("H3", leverage, "Reported financial debt is negative; the debt sign needs checking."))
    else:
        value = (debt.value - cash.value) / equity.value
        limit = limits["max_net_debt_to_equity"]
        moderate = (rational(debt.value) - rational(cash.value)
                    < rational(limit) * rational(equity.value))
        checks.append(result("H3", moderate, value, limit, leverage,
                             "(Financial debt - cash) / equity < configured limit at FY0 (decimal)."))

    old_debt, old_equity = inputs.fact("financial_debt", 4), inputs.fact("equity", 4)
    debt_pair = debt, old_debt
    debt_trend = debt, equity, old_debt, old_equity
    if not missing(debt_pair) and debt.value == 0 and old_debt.value == 0:
        checks.append(result("H4", True, None, None, debt_pair, "No debt in both FY0 and FY-4: pass; no ratio is required."))
    elif missing(debt_trend):
        checks.append(unavailable("H4", debt_trend, "Debt and equity for FY0 and FY-4 are required."))
    elif equity.value <= 0 or old_equity.value <= 0:
        checks.append(unavailable("H4", debt_trend, "Equity is zero or negative in a comparison year; the general nonpositive-denominator rule applies."))
    elif debt.value < 0 or old_debt.value < 0:
        checks.append(unavailable("H4", debt_trend, "Financial debt is negative in a comparison year; the debt sign needs checking."))
    else:
        now, old = debt.value / equity.value, old_debt.value / old_equity.value
        falling = (rational(debt.value) * rational(old_equity.value)
                   < rational(old_debt.value) * rational(equity.value))
        checks.append(result("H4", falling, now, old, debt_trend,
                             "Gross financial debt / equity FY0 < FY-4 (decimal); cash is not subtracted."))

    cash_flow = inputs.fact("operating_cash_flow")
    cash_cover = cash_flow, debt
    if debt.kind != "missing" and debt.value == 0:
        checks.append(result("H5", True, None, limits["min_operating_cash_flow_to_debt"], (debt,),
                             "No debt: pass; operating cash flow / zero debt is not calculated."))
    elif missing(cash_cover):
        checks.append(unavailable("H5", cash_cover, "Operating cash flow and financial debt are required."))
    elif debt.value < 0:
        checks.append(unavailable("H5", cash_cover, "Financial debt is negative; operating cash flow / debt is not meaningful."))
    else:
        value = cash_flow.value / debt.value
        limit = limits["min_operating_cash_flow_to_debt"]
        covered = rational(cash_flow.value) >= rational(limit) * rational(debt.value)
        checks.append(result("H5", covered, value, limit, cash_cover,
                             "Operating cash flow / financial debt >= configured limit at FY0 (decimal)."))

    operating, interest = inputs.fact("operating_income"), inputs.fact("interest_expense")
    interest_cover = operating, interest
    if interest.kind != "missing" and interest.value == 0:
        checks.append(result("H6", True, None, limits["min_interest_cover"], (interest,),
                             "Interest expense is reported as zero: pass; no infinite coverage ratio is shown."))
    elif missing(interest_cover):
        checks.append(unavailable("H6", interest_cover, "Operating income and a reported interest-expense figure are required; missing interest is not zero."))
    elif interest.value < 0:
        checks.append(unavailable("H6", interest_cover, "Interest expense is negative; coverage is not meaningful."))
    else:
        value = operating.value / interest.value
        limit = limits["min_interest_cover"]
        covered = rational(operating.value) >= rational(limit) * rational(interest.value)
        checks.append(result("H6", covered, value, limit, interest_cover,
                             "Operating income / interest expense >= configured interest-cover multiple at FY0."))
    return tuple(checks)
