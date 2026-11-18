"""The resolver on the saved demo data (slice S2), checked against cited figures. Owner: A. Network blocked.

Known answers, each from a cited source:
- Coca-Cola FY2025 revenue USD 47,941 million, accession 0001628280-26-010047 (session 5, slide 30);
- Coca-Cola operating cash flow USD 11,599 million in FY2023 and 6,805 million in FY2024 (session 5, slide 33);
- Coca-Cola FY2018 revenue first reported as 31,856, later 34,300 (USD million, session 5, slide 29);
- McDonald's: commercial paper and current maturities are classified inside long-term debt (10-K filed
  2026-02-24, accession 0000063908-26-000035, Debt Financing note), so its financial debt is the long-term debt
  on the balance sheet.
"""

from datetime import date

import pytest

from src.data.company import DEMO_TICKERS, load_company

KO = load_company("KO", demo=True)


def millions(fact):
    return round(fact.value / 1_000_000)


def test_coca_cola_fy2025_revenue_is_the_figure_shown_in_session_5():
    fact = KO.fact("revenue", date(2025, 12, 31))
    assert fact.value == 47_941_000_000
    assert fact.accession == "0001628280-26-010047" and fact.form == "10-K" and fact.tag == "Revenues"


def test_coca_cola_operating_cash_flow_fell_as_shown_in_session_5():
    assert millions(KO.fact("operating_cash_flow", date(2023, 12, 31))) == 11_599
    assert millions(KO.fact("operating_cash_flow", date(2024, 12, 31))) == 6_805


def test_coca_cola_2018_revenue_restatement_as_shown_in_session_5():
    data = load_company("KO", demo=True, years=8)
    fact = data.fact("revenue", date(2018, 12, 31))
    assert millions(fact) == 34_300
    assert "31,856" in fact.note
    assert any(w.startswith("RESTATED: revenue") and "2018" in w for w in data.warnings)


def test_a_comparative_labelled_with_a_later_fiscal_year_lands_in_its_own_year():
    # SPEC §5.3.2: Coca-Cola's FY2022 cash flow also appears in later 10-Ks, labelled with their fiscal year.
    fact = KO.fact("operating_cash_flow", date(2022, 12, 31))
    assert fact.kind == "reported" and fact.period_end == date(2022, 12, 31)


def test_mcdonalds_debt_does_not_count_commercial_paper_twice():
    mcd = load_company("MCD", demo=True)
    debt = mcd.fact("financial_debt", date(2025, 12, 31))
    assert millions(debt) == 39_973  # LongTermDebtNoncurrent = LongTermDebt on the balance sheet
    assert "inside" in mcd.fact("current_financial_debt", date(2025, 12, 31)).note


def test_mcdonalds_depreciation_is_the_cash_flow_statement_total():
    # McDonald's 10-K filed 2026-02-24 (0000063908-26-000035), cash flow statement: depreciation and amortization
    # 2,199 / 2,097 / 1,978 (2025 / 2024 / 2023, USD million). The 457 under the first tag is only the part in SG&A.
    mcd = load_company("MCD", demo=True)
    assert [millions(mcd.fact("depreciation_amortization", date(y, 12, 31))) for y in (2025, 2024, 2023)] == \
        [2_199, 2_097, 1_978]
    assert not any(w.startswith("TAG_CONFLICT: depreciation_amortization") for w in mcd.warnings)


def test_mcdonalds_negative_equity_comes_through():
    assert load_company("MCD", demo=True).fact("equity", date(2025, 12, 31)).value < 0


def test_coca_cola_debt_is_found_after_its_tags_changed_in_2024():
    debt = KO.fact("financial_debt", date(2025, 12, 31))
    assert debt.kind == "derived" and "LongTermDebtAndCapitalLeaseObligations" in debt.note


def test_amazon_dividends_are_missing_with_a_reason_not_zero():
    fact = load_company("AMZN", demo=True).fact("dividends_paid", date(2025, 12, 31))
    assert fact.kind == "missing" and fact.value is None and "PaymentsOfDividends" in fact.note


def test_nvidia_and_amazon_capital_expenditure_is_found():
    for ticker, fy_end in (("NVDA", date(2026, 1, 25)), ("AMZN", date(2025, 12, 31))):
        fact = load_company(ticker, demo=True).fact("capital_expenditure", fy_end)
        assert fact.kind == "reported" and fact.tag == "PaymentsToAcquireProductiveAssets"


def test_apple_interest_expense_is_missing_after_fy2023_not_guessed():
    fact = load_company("AAPL", demo=True).fact("interest_expense", date(2026, 9, 26))
    assert fact.kind == "missing"


@pytest.mark.parametrize("ticker", DEMO_TICKERS)
def test_every_demo_company_resolves_five_fiscal_years(ticker):
    data = load_company(ticker, demo=True)
    years = data.fiscal_years("revenue")
    assert len(years) == 5
    for metric in ("revenue", "net_income", "total_assets", "operating_cash_flow"):
        assert data.fact(metric, years[-1]).kind == "reported", metric
    assert data.fiscal_years("shares"), "a share count"


def test_jpmorgan_loads_with_its_industry_code_so_it_can_be_refused():
    jpm = load_company("JPM", demo=True)
    assert 6000 <= int(jpm.sic) <= 6799


def test_a_ticker_outside_the_demo_data_is_refused_in_demo_mode():
    from src.data.sec_client import UnknownTicker

    with pytest.raises(UnknownTicker, match="demo"):
        load_company("MSFT", demo=True)
