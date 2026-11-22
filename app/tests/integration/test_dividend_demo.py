"""Dividend checks on the saved demo data (slice S7). Owner: C (Flo). Network blocked.

Known answer, from a cited source (not from the code): Coca-Cola's dividends paid in fiscal year 2025 are
USD 8,779 million, read by hand by Igor from the 10-K (accession 0001628280-26-010047, page 64, line "Dividends";
tests/reconciliation/KO.yaml). Tolerance USD 0.5 million, as in the reconciliation rule (figures read to the
nearest million).

Amazon (no dividend at all, SPEC v2.4 §7, plan Q1) is added once PR #21 is on main.
"""

from datetime import date

import pytest

from src.checks.dividend import dividend_checks
from src.data.company import load_company
from src.settings import load_settings

MILLION = 1_000_000.0


def test_coca_cola_pays_a_dividend_in_fiscal_year_2025():
    results = {r.check_id: r for r in dividend_checks(load_company("KO", demo=True), load_settings())}
    d1 = results["D1"]
    assert d1.status == "pass"
    assert d1.value == pytest.approx(8_779 * MILLION, abs=0.5 * MILLION)
    (dividends,) = d1.inputs
    assert dividends.period_end == date(2025, 12, 31)
    assert dividends.accession == "0001628280-26-010047"


def test_coca_cola_dividend_covered_by_earnings_in_fiscal_year_2025():
    # Known answer from Igor's hand reading (KO.yaml, page 64 and the income statement): net income USD 13,107
    # million; Flo's hand working: 8,779 ÷ 13,107 = 66.98% < 90% → pass.
    results = {r.check_id: r for r in dividend_checks(load_company("KO", demo=True), load_settings())}
    d5 = results["D5"]
    assert d5.status == "pass"
    assert d5.value == pytest.approx(0.6698, abs=0.00005)
