"""B's saved-demo health regressions; no network or personal-reading sign-off.

Sources: evidence/demo/README.md records McDonald's negative FY2025 equity
(USD -1,791m); SPEC v2.4 and member-B.md record Apple's missing interest
after FY2023. Expected decisions follow those source traits and Greg's
23 November Q3 approval, not previously observed health_checks outputs.
"""
from datetime import date

import pytest

from src.checks.health import health_checks
from src.data.company import load_company
from src.settings import load_settings


@pytest.mark.parametrize("check_id", ["H3", "H4"])
def test_mcdonalds_known_negative_equity_fails_leverage_checks(check_id):
    data = load_company("MCD", demo=True)
    equity = data.fact("equity", date(2025, 12, 31))
    assert equity.kind == "reported" and equity.value == -1_791_000_000
    checks = {r.check_id: r for r in health_checks(data, settings=load_settings()["financial_health"])}
    assert checks[check_id].status == "fail"
    assert "negative equity" in checks[check_id].explanation.lower()
    assert equity in checks[check_id].inputs


def test_apple_missing_interest_with_nonzero_debt_keeps_interest_cover_unassessed():
    data = load_company("AAPL", demo=True)
    fy0 = date(2026, 9, 26)
    interest = data.fact("interest_expense", fy0)
    debt = data.fact("financial_debt", fy0)
    assert interest.kind == "missing" and interest.value is None
    assert debt.kind != "missing" and debt.value > 0
    check = {r.check_id: r for r in health_checks(data, settings=load_settings()["financial_health"])}["H6"]
    assert check.status == "insufficient_data"
    assert interest in check.inputs
    assert data.fact("interest_expense", fy0) is interest
