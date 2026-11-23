"""Dividend checks on the saved demo data (slice S7). Owner: C (Flo). Network blocked.

Known answer, from a cited source (not from the code): Coca-Cola's dividends paid in fiscal year 2025 are
USD 8,779 million, read by hand by Igor from the 10-K (accession 0001628280-26-010047, page 64, line "Dividends";
tests/reconciliation/KO.yaml). Tolerance USD 0.5 million, as in the reconciliation rule (figures read to the
nearest million).

Also D5 (66.98%) and D6 (fail, against 7,408 − 2,112 = 5,296, both read by hand), and Amazon (no dividend at all,
SPEC v2.4 §7, plan Q1, A's #21): "no dividend paid".
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


def test_coca_cola_dividend_not_covered_by_cash_in_fiscal_year_2025():
    # Known answer from Igor's hand reading (KO.yaml, page 64): operating cash flow 7,408 and capital expenditure
    # 2,112 (USD m, capex added in PR #24); Flo's hand working: 8,779 ≤ 7,408 − 2,112 = 5,296 is false → fail.
    results = {r.check_id: r for r in dividend_checks(load_company("KO", demo=True), load_settings())}
    d6 = results["D6"]
    assert d6.status == "fail"
    assert d6.value == pytest.approx(8_779 * MILLION, abs=0.5 * MILLION)
    assert d6.threshold == pytest.approx(5_296 * MILLION, abs=1.0 * MILLION)  # two figures, each within 0.5


def test_amazon_shows_no_dividend_paid():
    # Plan Q1 (SPEC v2.4 §7, A's #21): no dividend under any dividend tag in Amazon's fiscal years, so dividends paid
    # are nil, labelled. Flo's rule (row S7-1): D1 fails with "no dividend paid", D2–D6 not applicable. The plain
    # sentence is checked here on A's real note (review findings: wording coupling; Igor's review of #23).
    results = {r.check_id: r for r in dividend_checks(load_company("AMZN", demo=True), load_settings())}
    d1 = results["D1"]
    assert d1.status == "fail"
    assert d1.inputs[0].kind == "assumption"
    assert "no dividend paid" in d1.explanation.lower()
    assert "not reported in any fiscal year in the data, so they are treated as nil" in d1.explanation
    assert "SPEC" not in d1.explanation and "plan Q1" not in d1.explanation
    assert [results[c].status for c in ("D2", "D3", "D4", "D5", "D6")] == ["not_applicable"] * 5
