"""The one place where the interface gets the results of the checks (SPEC §7, §11; slice S10). Owner: D.

Each area's module belongs to its owner (`src/checks/past.py` and `health.py`: B; `dividend.py`: C). Until a
module is on `main`, its area is `None` and the screen shows it as "not assessed": the interface never invents
a result. Valuation (V1-V6) arrives with C's S9 in v0.2, so it is `None` in v0.1.
"""

from __future__ import annotations

from typing import Callable, Mapping

from src.contracts import CheckResult, CompanyData
from src.settings import load_settings

AREAS = ("past_performance", "financial_health", "dividend", "valuation")
AREA_CHECKS = {area: tuple(f"{letter}{n}" for n in range(1, 7)) for area, letter in zip(AREAS, "PHDV")}
_MODULES = {
    "past_performance": "src.checks.past",
    "financial_health": "src.checks.health",
    "dividend": "src.checks.dividend",
}


# The modules do not take their settings in the same shape: B's take their own section, C's the whole file.
# Reported to B and C in the S10 pull request; adapted here only, without touching any value.
def _past(data: CompanyData, settings: Mapping) -> tuple[CheckResult, ...]:
    from src.checks.past import past_checks

    return past_checks(data, settings=settings["past_performance"])


def _health(data: CompanyData, settings: Mapping) -> tuple[CheckResult, ...]:
    from src.checks.health import health_checks

    return health_checks(data, settings=settings["financial_health"])


def _dividend(data: CompanyData, settings: Mapping) -> tuple[CheckResult, ...]:
    from src.checks.dividend import dividend_checks

    return dividend_checks(data, settings)


PROVIDERS: dict[str, Callable[[CompanyData, Mapping], tuple[CheckResult, ...]]] = {
    "past_performance": _past,
    "financial_health": _health,
    "dividend": _dividend,
}


def check_results(data: CompanyData, settings: Mapping | None = None) -> dict[str, tuple[CheckResult, ...] | None]:
    """Results per area, in P1-P6, H1-H6, D1-D6, V1-V6 order; `None` for an area whose module is not merged yet."""
    settings = load_settings() if settings is None else settings
    found: dict[str, tuple[CheckResult, ...] | None] = {}
    for area in AREAS:
        provider = PROVIDERS.get(area)
        if provider is None:
            found[area] = None
            continue
        try:
            area_results = tuple(provider(data, settings))
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
