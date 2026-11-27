"""Small helpers shared by the resolver and the latest figures (src/data/resolver.py, src/data/twelve_months.py).
Owner: A. Kept in one place so the two never order filings differently (review of PR #72).
"""

from __future__ import annotations

# The line items whose 12-month periods define the fiscal years; the latest 10-Q is found under the same ones.
FISCAL_YEAR_ITEMS = ("revenue", "net_income", "operating_cash_flow")


def filing_order(e: dict) -> tuple:
    """Order of company-facts entries for the same period: later filing date first; on the same day an amendment
    (10-K/A, 10-Q/A) after the original; then the accession number."""
    return e["filed"], e.get("form", "").endswith("/A"), e["accn"]


def money(value: float) -> str:
    """An amount as filed, with thousands separators: 47941000000 -> "47,941,000,000"."""
    return f"{value:,.0f}"


def relative_difference(a: float, b: float) -> float:
    """|a − b| as a share of the larger amount (0 when equal): the measure behind the 1% warning settings."""
    if a == b:
        return 0.0
    return abs(a - b) / max(abs(a), abs(b))
