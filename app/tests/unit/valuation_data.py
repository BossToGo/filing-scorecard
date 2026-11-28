"""Test data of the valuation tests (slice S8b). Owner: C (Flo).

The synthetic company has annual figures only, so its last twelve months and its latest balance sheet are FY2025
(issue #71, item 6; SPEC Appendix A). They are put into `CompanyData.recent` here, explicitly: the engine itself
never falls back to the annual figures.
"""

from __future__ import annotations

import dataclasses
from datetime import date

from src.contracts import CompanyData
from tests.fixtures import synthetic

FY0 = date(2025, 12, 31)
MILLION = 1_000_000.0
FLOWS = ("revenue", "net_income", "operating_cash_flow", "capital_expenditure")
BALANCES = ("financial_debt", "minority_interest")


def synthetic_company() -> CompanyData:
    data = synthetic.company_data()
    recent = {metric: data.fact(metric, FY0) for metric in FLOWS + BALANCES}
    recent["shares"] = data.latest("shares")
    return dataclasses.replace(data, recent=recent)


def latest(metric: str, millions: float | None, data: CompanyData | None = None) -> CompanyData:
    """The company with one latest figure replaced; None makes it `missing` with a reason (never zero)."""
    data = synthetic_company() if data is None else data
    old = data.recent[metric]
    if millions is None:
        new = dataclasses.replace(old, value=None, kind="missing", tag=None, form=None, accession=None,
                                  note=f"no latest figure for {metric} (test)")
    else:
        new = dataclasses.replace(old, value=millions * MILLION)
    return dataclasses.replace(data, recent={**data.recent, metric: new})


def without_latest(metric: str, data: CompanyData | None = None) -> CompanyData:
    """The company with no entry at all for one latest figure."""
    data = synthetic_company() if data is None else data
    return dataclasses.replace(data, recent={m: f for m, f in data.recent.items() if m != metric})
