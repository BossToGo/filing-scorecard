"""Dividend checks D1–D6 (SPEC §7, slice S7). Owner: C (Flo).

Where the expected values come from (SPEC rule 14.5, AGENTS.md rule 5):
- Edge cases: small test companies built below, with the expected results worked out by hand by Flo.
- Appendix A (synthetic company): `synthetic.expected_check("D1")` etc., signed off by Flo on PR #5. Those tests
  are added once PR #5 (the fixture) is on main.
Never from running `src/checks/dividend.py`.

Decisions for this slice (Flo, 22 November 2026):
- D2 is "not assessed" (status insufficient_data, plan Q9) until slice S9 switches it on.
- D3 counts a cut as "this year < (1 − max_dividend_cut) × last year": no division, so a rise from a year of zero
  is never a cut. The value shown is the lowest year-on-year change among years whose previous year is positive.
"""

from __future__ import annotations

from datetime import date

import pytest

from src.checks.dividend import dividend_checks
from src.contracts import CompanyData, Fact
from src.settings import load_settings

MILLION = 1_000_000.0
YEARS = (2021, 2022, 2023, 2024, 2025)  # FY-4 ... FY0
SETTINGS = load_settings()

# The labelled nil of plan Q1 (SPEC v2.4 §7), in the shape A's resolver produces it (PR #21): Amazon's case.
NIL_NOTE = ("no dividend under any dividend tag in the five fiscal years: not reported, treated as nil, so no "
            "dividend paid (SPEC §7, plan Q1)")


# --- a small test company ---------------------------------------------------------------------------------------


def fact(metric: str, millions: float | None, year: int, *, nil: bool = False) -> Fact:
    """One figure of the test company, in USD millions. None means missing (with a reason), never zero."""
    end = date(year, 12, 31)
    if millions is None:
        return Fact(metric, None, "USD", date(year, 1, 1), end, "missing", None, None, None, None, None,
                    "no annual 10-K figure for this year (test company)")
    if nil:
        return Fact(metric, millions * MILLION, "USD", None, end, "assumption", None, None, None, None, None, NIL_NOTE)
    return Fact(metric, millions * MILLION, "USD", date(year, 1, 1), end, "reported", f"test:{metric}", "TEST",
                "test-company", None, None, "test company")


def company(dividends, *, net_income=None, operating_cash_flow=None, capital_expenditure=None, years=YEARS,
            nil=False) -> CompanyData:
    """A test company. Each list holds USD millions, oldest year first (FY-4 ... FY0); None = missing that year.

    Unless a test gives them, the other figures are the same every year: revenue 1,000, net income 500, operating
    cash flow 600, capital expenditure 100.
    """
    n = len(years)
    columns = {
        "revenue": [1000] * n,
        "dividends_paid": dividends,
        "net_income": [500] * n if net_income is None else net_income,
        "operating_cash_flow": [600] * n if operating_cash_flow is None else operating_cash_flow,
        "capital_expenditure": [100] * n if capital_expenditure is None else capital_expenditure,
    }
    items = {}
    for metric, values in columns.items():
        assert len(values) == n, f"{metric}: give one value per fiscal year ({n})"
        is_nil = nil and metric == "dividends_paid"
        items[metric] = {date(y, 12, 31): fact(metric, v, y, nil=is_nil) for y, v in zip(years, values)}
    return CompanyData(ticker="TST", cik="0000000001", name="Test Co. (test data)", sic=None, sic_description=None,
                       fiscal_year_end="1231", latest_10k_filed=None, retrieved=None, items=items)


def results(data: CompanyData, settings=SETTINGS) -> dict:
    return {r.check_id: r for r in dividend_checks(data, settings)}


def figures(result) -> list[tuple[str, int]]:
    """The input figures of a result as (line item, fiscal year)."""
    return [(f.metric, f.period_end.year) for f in result.inputs]


PAYER = [20, 22, 24, 26, 28]  # a company that pays a dividend every year


# --- structure: no money values needed -----------------------------------------------------------------------------


def test_the_six_results_come_in_order_d1_to_d6():
    assert [r.check_id for r in dividend_checks(company(PAYER), SETTINGS)] == ["D1", "D2", "D3", "D4", "D5", "D6"]


def test_each_check_lists_the_figures_its_rule_uses():
    # SPEC §5.2: the checks a missing figure blocks are found from the results that list it as an input.
    r = results(company(PAYER))
    assert figures(r["D1"]) == [("dividends_paid", 2025)]
    assert figures(r["D3"]) == [("dividends_paid", y) for y in YEARS]
    assert figures(r["D4"]) == [("dividends_paid", 2025), ("dividends_paid", 2021)]
    assert figures(r["D5"]) == [("dividends_paid", 2025), ("net_income", 2025)]
    assert figures(r["D6"]) == [("dividends_paid", 2025), ("operating_cash_flow", 2025),
                                ("capital_expenditure", 2025)]


def test_d2_is_not_assessed_until_s9_and_says_what_it_needs():
    # Plan Q9: "not assessed" is insufficient_data with the reason; it has no value (SPEC §7, §13.2 slice S9).
    d2 = results(company(PAYER))["D2"]
    assert d2.status == "insufficient_data"
    assert d2.value is None
    assert "not assessed" in d2.explanation
    assert "share price" in d2.explanation and "dividend yield" in d2.explanation


def test_the_thresholds_come_from_the_settings_not_the_code():
    r = results(company(PAYER))
    assert r["D3"].threshold == pytest.approx(-SETTINGS["dividend"]["max_dividend_cut"])
    assert r["D5"].threshold == pytest.approx(SETTINGS["dividend"]["max_payout_ratio"])

    changed = {**SETTINGS, "dividend": {"max_dividend_cut": 0.25, "max_payout_ratio": 0.50}}
    r = results(company(PAYER), changed)
    assert r["D3"].threshold == pytest.approx(-0.25)
    assert r["D5"].threshold == pytest.approx(0.50)
