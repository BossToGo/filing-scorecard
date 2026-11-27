"""S5: P1–P6, SPEC §7. Pure CompanyData + settings + sourced benchmark Facts.

    results = past_checks(company, settings=settings['past_performance'],
                          benchmarks={'roe': roe_fact, 'operating_margin': margin_fact})

All ratios stay decimals; money stays USD. No rounding is used to decide a result.
Appendix A values: tests/unit/test_b_appendix_a.py (signed off by Greg on PR #5, 24 November 2026).
"""
from __future__ import annotations

import math
from collections.abc import Mapping
from datetime import date

from src.contracts import CheckResult, CompanyData, Fact
from src.checks._b_inputs import Inputs, change, compared, day, missing, money, rational, result, unavailable


def _benchmark(metric: str, benchmarks: Mapping[str, Fact] | None, inputs: Inputs) -> Fact:
    fact = benchmarks.get(metric) if benchmarks is not None else None
    if fact is None:
        return Fact(metric, None, "pure", None, inputs.latest or date.min,
                    "missing", None, None, None, None, None,
                    f"Not assessed: needs a sourced industry {metric.replace('_', ' ')} benchmark.")
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
                             f"Net income was positive in {count} of the last 5 fiscal years ({net[4].period_end.year} to {net[0].period_end.year}); at least {minimum} are required."))

    pair = net[0], net[4]
    if missing(pair):
        checks.append(unavailable("P2", pair, "Net income for the latest year and four years earlier is required."))
    else:
        checks.append(result("P2", net[0].value > net[4].value and net[0].value > 0,
                             net[0].value, net[4].value, pair,
                             f"Net income was {money(net[0].value)} for the year ended {day(net[0].period_end)}, against {money(net[4].value)} four years earlier ({day(net[4].period_end)}). The latest profit must be positive and higher."))

    growth_inputs = net[0], net[1], net[4]
    known_losses = tuple(f for f in (net[4], net[1]) if f.kind != "missing" and f.value <= 0)
    if known_losses:
        # A known loss in a comparison year fails P3 whatever the other years are (SPEC §7), even when one is missing.
        amounts = " and ".join(f"{money(f.value)} for the year ended {day(f.period_end)}" for f in known_losses)
        known = tuple(f for f in growth_inputs if f.kind != "missing")
        checks.append(result("P3", False, None, None, known,
                             f"Growth from a loss is not meaningful: net income was {amounts}. Both comparison years must be profitable."))
    elif missing(growth_inputs):
        checks.append(unavailable("P3", growth_inputs, "Net income for the latest year, the preceding year and four years earlier is required."))
    elif net[0].value < 0:
        checks.append(result("P3", False, None, None, growth_inputs,
                             f"The latest year is a loss: net income was {money(net[0].value)} for the year ended {day(net[0].period_end)}."))
    else:
        recent = float(rational(net[0].value) / rational(net[1].value) - 1)
        # Log differences avoid overflowing the ratio before taking its fourth root.
        compound = math.expm1((math.log(net[0].value) - math.log(net[4].value)) / 4) if net[0].value else -1.0
        # With positive NI, recent > CAGR iff NI0^3 * NI-4 > NI-1^4.
        # Compare decimal source amounts exactly: equal growth must never pass due to root rounding.
        accelerating = (rational(net[0].value) ** 3 * rational(net[4].value)
                        > rational(net[1].value) ** 4) if net[0].value else False
        checks.append(result("P3", accelerating, recent, compound, growth_inputs,
                             f"Net income {change(recent)} in the year ended {day(net[0].period_end)}, against an average change of about {compound:.2%} a year since {day(net[4].period_end)}. The latest change is {compared(accelerating, 'higher', 'not higher')} than the average; it must be higher to pass."))

    equity = inputs.fact("equity"), inputs.fact("equity", 1)
    if any(f.kind != "missing" and f.value <= 0 for f in equity):
        known_equity = tuple(f for f in equity if f.kind != "missing")
        amounts = "; ".join(f"{money(f.value)} at {day(f.period_end)}" for f in known_equity)
        checks.append(result("P4", False, None, None, known_equity,
                             f"Negative equity: shareholder equity was {amounts}. Zero or negative equity prevents a meaningful return-on-equity comparison."))
    else:
        roe = _benchmark("roe", benchmarks, inputs)
        roe_inputs = (net[0], *equity, roe)
        if roe.kind == "missing" and not missing((net[0], *equity)):
            checks.append(CheckResult("P4", "insufficient_data", None, None, roe_inputs,
                                      "The industry return-on-equity benchmark is unavailable."))
        elif missing(roe_inputs):
            checks.append(unavailable("P4", roe_inputs, "Return on equity cannot be assessed from the available figures."))
        else:
            average = (rational(equity[0].value) + rational(equity[1].value)) / 2
            ratio = rational(net[0].value) / average  # one exact ratio for both the result and the figure shown
            above = ratio > rational(roe.value)
            checks.append(result("P4", above, float(ratio), roe.value, roe_inputs,
                                 f"Return on equity was about {float(ratio):.2%} for the year ended {day(net[0].period_end)} ({money(net[0].value)} profit on average equity of {money(float(average))}), {compared(above)} the industry's {roe.value:.2%}. It must be higher to pass."))

    operating = inputs.fact("operating_income")
    revenue = inputs.fact("revenue")
    margin = _benchmark("operating_margin", benchmarks, inputs)
    margin_inputs = operating, revenue, margin
    if margin.kind == "missing" and not missing((operating, revenue)) and revenue.value > 0:
        checks.append(CheckResult("P5", "insufficient_data", None, None, margin_inputs,
                                  "The industry operating-margin benchmark is unavailable."))
    elif missing(margin_inputs):
        checks.append(unavailable("P5", margin_inputs, "Operating margin cannot be assessed from the available figures."))
    elif revenue.value <= 0:
        checks.append(unavailable("P5", margin_inputs, "Revenue is zero or negative; operating margin is not meaningful."))
    else:
        ratio = rational(operating.value) / rational(revenue.value)
        above = ratio > rational(margin.value)
        checks.append(result("P5", above, float(ratio), margin.value, margin_inputs,
                             f"Operating margin was about {float(ratio):.2%} for the year ended {day(operating.period_end)} ({money(operating.value)} operating profit on {money(revenue.value)} revenue), {compared(above)} the industry's {margin.value:.2%}. It must be higher to pass."))

    capital_inputs = (operating, inputs.fact("total_assets"), inputs.fact("current_liabilities"),
                      inputs.fact("operating_income", 3), inputs.fact("total_assets", 3),
                      inputs.fact("current_liabilities", 3))
    if missing(capital_inputs):
        checks.append(unavailable("P6", capital_inputs, "Operating profit, assets and short-term liabilities for the latest year and three years earlier are required."))
    else:
        now_capital = capital_inputs[1].value - capital_inputs[2].value
        old_capital = capital_inputs[4].value - capital_inputs[5].value
        if not math.isfinite(now_capital) or not math.isfinite(old_capital):
            checks.append(unavailable("P6", capital_inputs, "Assets minus current liabilities exceeds the supported finite numeric range."))
        elif now_capital <= 0 or old_capital <= 0:
            checks.append(unavailable("P6", capital_inputs, "Assets minus current liabilities is zero or negative in a comparison year."))
        else:
            now = rational(operating.value) / (rational(capital_inputs[1].value) - rational(capital_inputs[2].value))
            old = rational(capital_inputs[3].value) / (rational(capital_inputs[4].value) - rational(capital_inputs[5].value))
            improved = now > old
            checks.append(result("P6", improved, float(now), float(old), capital_inputs,
                                 f"Return on capital employed was about {float(now):.2%} for the year ended {day(operating.period_end)}, {compared(improved, 'up from', 'not above')} {float(old):.2%} three years earlier ({day(capital_inputs[3].period_end)}). Capital employed was {money(now_capital)} and {money(old_capital)}, respectively; the latest return must be higher to pass."))
    return tuple(checks)
