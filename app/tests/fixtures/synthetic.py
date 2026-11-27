"""Synthetic Co. (SYNTHETIC DATA, SPEC Appendix A, version 2.3) for tests. Collected by A (slice S0c).

Use in a test:

    from tests.fixtures import synthetic

    data = synthetic.company_data()          # CompanyData, amounts in USD (not millions)
    e = synthetic.expected_check("P3")        # refuses until owner B has signed off (rule 14.5)
    assert result.value * 100 == pytest.approx(e["value"], abs=synthetic.tolerance(e))

Expected values are shown as in Appendix A: "%" values are percent (9.375 means 0.09375), "USD m" values are
millions. Inputs (`inputs()`) are decimals and plain numbers.

Assert the value and what it is compared with, not only pass or fail: on this company several wrong formulas give
the same result (net against gross debt in H3, FY0 against average equity in P4, any earlier year for "four years
earlier"). Add one case at each threshold (exactly 40%, 20%, 5 times, −10%, 90%; price equal to the fair value).
"""

from __future__ import annotations

import dataclasses
from datetime import date
from functools import lru_cache
from pathlib import Path

import yaml

from src.contracts import CompanyData, Fact

FIXTURE = Path(__file__).with_name("synthetic_co.yaml")
MILLION = 1_000_000.0
FLOWS = {
    "revenue",
    "operating_income",
    "interest_expense",
    "net_income",
    "depreciation_amortization",
    "capital_expenditure",
    "operating_cash_flow",
    "dividends_paid",
}
NOTE = "SYNTHETIC DATA: SPEC Appendix A"
# The latest figures (`CompanyData.recent`, slice S2c): the company has annual data only, so they are its FY2025
# figures, written out so that the valuation never falls back to annual figures by itself (issue #71 item 6; Flo on
# PR #72, 27 November).
RECENT = ("revenue", "net_income", "operating_cash_flow", "capital_expenditure", "financial_debt", "minority_interest",
          "shares")
RECENT_NOTE = "annual data only, so the last twelve months are FY2025 and the latest balances those of 31 December 2025"


class NotSignedOff(LookupError):
    """An expected value was used before its owner recalculated it and signed off (SPEC rule 14.5)."""


@lru_cache(maxsize=1)
def _read() -> dict:
    return yaml.safe_load(FIXTURE.read_text(encoding="utf-8"))


def _load() -> dict:
    return _read()


def _fact(metric: str, millions: float, year: int, *, flow: bool, unit: str = "USD", scale: float = MILLION) -> Fact:
    return Fact(
        metric=metric,
        value=millions * scale,
        unit=unit,
        period_start=date(year, 1, 1) if flow else None,
        period_end=date(year, 12, 31),
        kind="reported",
        tag=f"synthetic:{metric}",
        form="SYNTHETIC",
        accession="synthetic-appendix-a",
        filed=None,
        retrieved=None,
        note=NOTE,
    )


def company_data() -> CompanyData:
    """The synthetic company as CompanyData: five fiscal years ending 31 December, amounts in USD."""
    raw = _load()
    years = raw["fiscal_years"]
    items: dict = {}
    for metric, values in raw["line_items"].items():
        items[metric] = {
            date(year, 12, 31): _fact(metric, value, year, flow=metric in FLOWS) for year, value in zip(years, values)
        }
    other, latest = raw["other_inputs"], years[-1]
    items["current_financial_debt"] = {
        date(latest, 12, 31): _fact("current_financial_debt", other["current_financial_debt_fy2025"], latest, flow=False)
    }
    items["shares"] = {date(latest, 12, 31): _fact("shares", other["shares_millions"], latest, flow=False, unit="shares")}
    for metric in ("minority_interest", "preferred_stock", "equity_method_investments"):
        items[metric] = {date(latest, 12, 31): _fact(metric, other[metric], latest, flow=False)}
    recent = {metric: dataclasses.replace(items[metric][date(latest, 12, 31)], note=f"{NOTE}; {RECENT_NOTE}")
              for metric in RECENT}
    return CompanyData(
        ticker="SYN",
        cik="0000000000",
        name="Synthetic Co. (SYNTHETIC DATA)",
        sic=None,
        sic_description=None,
        fiscal_year_end="1231",
        latest_10k_filed=None,
        retrieved=None,
        items=items,
        warnings=("SYNTHETIC DATA: invented company from SPEC Appendix A",),
        recent=recent,
    )


def inputs() -> dict:
    """Share price (USD), settings and benchmarks of Appendix A, as decimals and plain numbers."""
    raw = _load()
    return {
        "share_price": raw["other_inputs"]["share_price_usd"],
        "settings": dict(raw["settings"]),
        "benchmarks": dict(raw["benchmarks"]),
    }


def _require_sign_off(owner: str, what: str) -> None:
    if not _load()["sign_off"].get(owner):
        raise NotSignedOff(
            f"{what} belongs to member {owner}, who has not yet recalculated it and signed off (SPEC rule 14.5): "
            "post your hand recalculation as a review comment on the S0c pull request; A records it under "
            "`sign_off` in tests/fixtures/synthetic_co.yaml."
        )


def expected_check(check_id: str) -> dict:
    """Expected result of one check (Appendix A), once its owner has signed off."""
    entry = _load()["expected_checks"][check_id]
    _require_sign_off(entry["owner"], f"Expected value {check_id}")
    return dict(entry)


def expected_valuation(name: str) -> dict:
    """Expected valuation working (Appendix A), once owner C has signed off."""
    _require_sign_off("C", f"Expected valuation value {name!r}")
    return dict(_load()["expected_valuation"][name])


def expected_scores() -> dict:
    """Expected area scores, tier 2 (Appendix A), once owner E has signed off."""
    _require_sign_off("E", "The expected area scores")
    return dict(_load()["expected_scores"])


def expected_statements() -> dict:
    """Which strengths and points to watch are shown (SPEC §9, Appendix A), once owner B has signed off these too.

    B's sign-off of the P and H rows does not cover them: they have their own record, `B_statements`.
    """
    _require_sign_off("B", "The expected strengths and points to watch")
    if not _load()["sign_off"].get("B_statements"):
        raise NotSignedOff(
            "The expected strengths and points to watch (CALC-G) belong to member B, whose sign-off so far covers "
            "the P and H rows only: B posts a recalculation of CALC-G as a review on the S0c pull request; A records "
            "it under `sign_off: B_statements` in tests/fixtures/synthetic_co.yaml."
        )
    return {key: dict(entry) for key, entry in _load()["expected_statements"].items()}


def expected_tier1() -> dict:
    """Expected tier 1 scores without benchmarks or share price (docs/acceptance.md AC3), once D has signed off."""
    _require_sign_off("D", "The expected tier 1 scores (AC3)")
    return dict(_load()["expected_tier1"])


def tolerance(entry: dict) -> float:
    """Half a unit of the last decimal shown in Appendix A, in the unit shown there."""
    return 0.5 * 10 ** -entry["decimals"]
