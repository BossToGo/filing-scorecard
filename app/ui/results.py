"""The one place where the interface gets the results of the checks (SPEC §7, §8, §11; slices S10, S10b). Owner: D.

Each area's module belongs to its owner (`src/checks/past.py` and `health.py`: B; `dividend.py`, `valuation.py` and
the engine `src/valuation/equity_method.py`: C; the benchmarks `src/benchmarks/loader.py`: B; the risk-free rate
`src/data/fred.py`: A, reached through `src.data.company`). Until a module is on `main`, its area is `None` and the
screen shows it as "not assessed": the interface never invents a result.

`run_checks` does everything once (S10b): the benchmarks for the ticker, the risk-free rate, one valuation at the
typed price, then the four areas. The valuation detail and V1-V6 use the same `Valuation`, so the screen and the
checks show the same estimate.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Mapping

from src.benchmarks.loader import BenchmarkData, load_benchmarks
from src.contracts import CheckResult, CompanyData, Fact
from src.data.company import risk_free_rate
from src.settings import load_settings
from src.valuation.equity_method import Valuation, value_company

AREAS = ("past_performance", "financial_health", "dividend", "valuation")
AREA_CHECKS = {area: tuple(f"{letter}{n}" for n in range(1, 7)) for area, letter in zip(AREAS, "PHDV")}
_MODULES = {
    "past_performance": "src.checks.past",
    "financial_health": "src.checks.health",
    "dividend": "src.checks.dividend",
    "valuation": "src.checks.valuation",
}


@dataclass(frozen=True)
class Market:
    """What the checks need besides the company's filings: the typed price, B's benchmarks, A's risk-free rate and
    C's valuation at that price (`None` only when no valuation was run)."""

    price: float | None
    benchmarks: BenchmarkData
    risk_free: Fact
    valuation: Valuation | None = None


@dataclass(frozen=True)
class Run:
    results: dict[str, tuple[CheckResult, ...] | None]
    market: Market


# The modules do not take their inputs in the same shape (B's take their own settings section and the benchmarks as a
# dict, #28; C's the whole settings, #23 and #52; B's loader returns `BenchmarkData`, #27). Adapted here only.
def _past(data: CompanyData, settings: Mapping, market: Market) -> tuple[CheckResult, ...]:
    from src.checks.past import past_checks

    b = market.benchmarks
    return past_checks(data, settings=settings["past_performance"],
                       benchmarks={"roe": b.fact("roe"), "operating_margin": b.fact("operating_margin")})


def _health(data: CompanyData, settings: Mapping, market: Market) -> tuple[CheckResult, ...]:
    from src.checks.health import health_checks

    return health_checks(data, settings=settings["financial_health"])


def _dividend(data: CompanyData, settings: Mapping, market: Market) -> tuple[CheckResult, ...]:
    from src.checks.dividend import dividend_checks

    return dividend_checks(data, settings, share_price=market.price,
                           market_dividend_yield=market.benchmarks.market_fact("dividend_yield"))


def _valuation(data: CompanyData, settings: Mapping, market: Market) -> tuple[CheckResult, ...]:
    from src.checks.valuation import valuation_checks

    b = market.benchmarks
    return valuation_checks(data, settings, market.valuation, share_price=market.price, industry_pe=b.fact("pe"),
                            market_pe=b.market_fact("pe"), industry_pb=b.fact("pb"))


PROVIDERS: dict[str, Callable[[CompanyData, Mapping, Market], tuple[CheckResult, ...]]] = {
    "past_performance": _past,
    "financial_health": _health,
    "dividend": _dividend,
    "valuation": _valuation,
}


def market_inputs(data: CompanyData, price: float | None, *, demo: bool, settings: Mapping,
                  benchmarks: BenchmarkData | None = None, risk_free: Fact | None = None) -> Market:
    """The benchmarks (loaded once), the risk-free rate and one valuation at the typed price. Tests pass their own
    benchmarks and rate (the synthetic company of Appendix A); the app uses B's file and A's rate."""
    benchmarks = load_benchmarks(data.ticker) if benchmarks is None else benchmarks
    risk_free = risk_free_rate(demo) if risk_free is None else risk_free
    valuation = value_company(data, settings, share_price=price, risk_free_rate=risk_free,
                              unlevered_beta=benchmarks.fact("unlevered_beta"))
    return Market(price, benchmarks, risk_free, valuation)


def check_results(data: CompanyData, settings: Mapping | None = None,
                  market: Market | None = None) -> dict[str, tuple[CheckResult, ...] | None]:
    """Results per area, in P1-P6, H1-H6, D1-D6, V1-V6 order; `None` for an area whose module is not merged yet.
    Without `market`: no share price, B's benchmarks and the saved risk-free rate (no network)."""
    settings = load_settings() if settings is None else settings
    market = market_inputs(data, None, demo=True, settings=settings) if market is None else market
    found: dict[str, tuple[CheckResult, ...] | None] = {}
    for area in AREAS:
        provider = PROVIDERS.get(area)
        if provider is None:
            found[area] = None
            continue
        try:
            area_results = tuple(provider(data, settings, market))
        except ModuleNotFoundError as error:
            # Only the check module itself being absent means "not merged yet"; any other missing import is a bug.
            if error.name != _MODULES[area]:
                raise
            found[area] = None
            continue
        ids = tuple(r.check_id for r in area_results)
        if ids != AREA_CHECKS[area]:
            raise ValueError(f"{area}: expected the checks {AREA_CHECKS[area]} in order, got {ids}")
        found[area] = area_results
    return found


def run_checks(data: CompanyData, price: float | None, *, demo: bool, settings: Mapping | None = None,
               benchmarks: BenchmarkData | None = None, risk_free: Fact | None = None) -> Run:
    """Everything the scorecard shows for one company at one typed price (or none)."""
    settings = load_settings() if settings is None else settings
    market = market_inputs(data, price, demo=demo, settings=settings, benchmarks=benchmarks, risk_free=risk_free)
    return Run(check_results(data, settings, market), market)
