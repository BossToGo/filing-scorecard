"""S5: P1–P6, SPEC §7. Pure CompanyData + settings + sourced benchmark Facts.

    results = past_checks(company, settings=settings['past_performance'],
                          benchmarks={'roe': roe_fact, 'operating_margin': margin_fact})

All ratios stay decimals; money stays USD. No rounding is used to decide a result.
This implementation remains a draft until Greg's Appendix A calculation sign-off.
"""
from __future__ import annotations

import math
from collections.abc import Mapping
from datetime import date

from src.contracts import CheckResult, CompanyData, Fact
from src.checks._b_inputs import Inputs, missing, rational, result, unavailable


def _benchmark(metric: str, benchmarks: Mapping[str, Fact] | None, inputs: Inputs) -> Fact:
    fact = benchmarks.get(metric) if benchmarks is not None else None
    if fact is None:
        return Fact(metric, None, "pure", None, inputs.latest or date.min,
                    "missing", None, None, None, None, None,
                    f"Not assessed: needs a sourced industry {metric} benchmark (S4).")
    if not isinstance(fact, Fact):
        raise TypeError("Industry benchmarks must be Fact objects with their sources, not bare numbers.")
    if fact.metric != metric:
        raise ValueError(f"Expected benchmark metric {metric!r}, received {fact.metric!r}.")
    if fact.unit != "pure":
        from dataclasses import replace
        return replace(fact, value=None, kind="missing", note="Industry benchmark must be a decimal ratio.")
    return fact


def past_checks(data: CompanyData, *, settings: Mapping[str, float],
                benchmarks: Mapping[str, Fact] | None = None) -> tuple[CheckResult, ...]:
    """Return all six checks in P1–P6 order. Pass the past_performance settings section."""
    minimum = settings["p1_min_profitable_years"]
    if isinstance(minimum, bool) or not isinstance(minimum, int) or not 1 <= minimum <= 5:
        raise ValueError("p1_min_profitable_years must be an integer from 1 to 5.")
    inputs = Inputs(data)
    net = tuple(inputs.fact("net_income", offset) for offset in range(5))
    checks = []

    if missing(net):
        checks.append(unavailable("P1", net, "All five fiscal-year net income figures are required."))
    else:
        count = sum(f.value > 0 for f in net)
        checks.append(result("P1", count >= minimum, count, minimum, net,
                             "Net income is strictly positive in at least the configured number of the last five fiscal years."))

    pair = net[0], net[4]
    if missing(pair):
        checks.append(unavailable("P2", pair, "Latest and four-years-earlier net income are required."))
    else:
        checks.append(result("P2", net[0].value > net[4].value and net[0].value > 0,
                             net[0].value, net[4].value, pair, "Latest net income > FY-4 net income, and latest net income > 0 (USD)."))

    growth_inputs = net[0], net[1], net[4]
    if missing(growth_inputs):
        checks.append(unavailable("P3", growth_inputs, "FY0, FY-1 and FY-4 net income are required."))
    elif net[4].value <= 0 or net[1].value <= 0:
        checks.append(result("P3", False, None, None, growth_inputs, "Growth from a loss is not meaningful (FY-4 or FY-1 net income is zero or negative)."))
    elif net[0].value < 0:
        checks.append(unavailable("P3", growth_inputs, "The latest fiscal year is a loss, so its four-year compound growth is undefined."))
    else:
        recent = net[0].value / net[1].value - 1
        # Log differences avoid overflowing the ratio before taking its fourth root.
        compound = math.expm1((math.log(net[0].value) - math.log(net[4].value)) / 4) if net[0].value else -1.0
        # With positive NI, recent > CAGR iff NI0^3 * NI-4 > NI-1^4.
        # Compare decimal source amounts exactly: equal growth must never pass due to root rounding.
        accelerating = (rational(net[0].value) ** 3 * rational(net[4].value)
                        > rational(net[1].value) ** 4) if net[0].value else False
        checks.append(result("P3", accelerating, recent, compound, growth_inputs,
                             "Latest annual net income growth > compound annual growth over four intervals: (FY0/FY-4)^(1/4) - 1."))

    equity = inputs.fact("equity"), inputs.fact("equity", 1)
    roe = _benchmark("roe", benchmarks, inputs)
    roe_inputs = (net[0], *equity, roe)
    if roe.kind == "missing":
        checks.append(unavailable("P4", roe_inputs, "Not assessed: industry return-on-equity benchmark required."))
    elif any(f.kind != "missing" and f.value <= 0 for f in equity):
        known_equity = tuple(f for f in equity if f.kind != "missing")
        checks.append(result("P4", False, None, None, known_equity, "Negative equity: equity is zero or negative in FY0 or FY-1."))
    elif missing(roe_inputs):
        checks.append(unavailable("P4", roe_inputs, "Net income and both opening/closing equity figures are required."))
    else:
        average = equity[0].value + (equity[1].value - equity[0].value) / 2
        value = net[0].value / average
        # Compare source amounts and the published decimal cell before any ratio rounding.
        above = (2 * rational(net[0].value) > rational(roe.value)
                 * (rational(equity[0].value) + rational(equity[1].value)))
        checks.append(result("P4", above, value, roe.value, roe_inputs,
                             "Net income FY0 / average equity (FY-1, FY0) > industry ROE (decimal)."))

    operating = inputs.fact("operating_income")
    revenue = inputs.fact("revenue")
    margin = _benchmark("operating_margin", benchmarks, inputs)
    margin_inputs = operating, revenue, margin
    if missing(margin_inputs):
        checks.append(unavailable("P5", margin_inputs, "Operating income, revenue and an industry operating-margin benchmark are required."))
    elif revenue.value <= 0:
        checks.append(unavailable("P5", margin_inputs, "Revenue is zero or negative; operating margin is not meaningful."))
    else:
        value = operating.value / revenue.value
        above = rational(operating.value) > rational(margin.value) * rational(revenue.value)
        checks.append(result("P5", above, value, margin.value, margin_inputs,
                             "Operating income / revenue (FY0) > industry pre-tax unadjusted operating margin (decimal)."))

    capital_inputs = (operating, inputs.fact("total_assets"), inputs.fact("current_liabilities"),
                      inputs.fact("operating_income", 3), inputs.fact("total_assets", 3),
                      inputs.fact("current_liabilities", 3))
    if missing(capital_inputs):
        checks.append(unavailable("P6", capital_inputs, "Operating income, assets and current liabilities in FY0 and FY-3 are required."))
    else:
        now_capital = capital_inputs[1].value - capital_inputs[2].value
        old_capital = capital_inputs[4].value - capital_inputs[5].value
        if not math.isfinite(now_capital) or not math.isfinite(old_capital):
            checks.append(unavailable("P6", capital_inputs, "Assets minus current liabilities exceeds the supported finite numeric range."))
        elif now_capital <= 0 or old_capital <= 0:
            checks.append(unavailable("P6", capital_inputs, "Assets minus current liabilities is zero or negative in a comparison year."))
        else:
            now, old = operating.value / now_capital, capital_inputs[3].value / old_capital
            improved = (rational(operating.value)
                        * (rational(capital_inputs[4].value) - rational(capital_inputs[5].value))
                        > rational(capital_inputs[3].value)
                        * (rational(capital_inputs[1].value) - rational(capital_inputs[2].value)))
            checks.append(result("P6", improved, now, old, capital_inputs,
                                 "Operating income / (assets - current liabilities), FY0 > FY-3 (decimal)."))
    return tuple(checks)
