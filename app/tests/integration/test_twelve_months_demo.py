"""The latest figures of the five demo companies (slice S2c, issue #71 item 1), from the saved demo data, network
blocked. Owner: A.

Expected values: the hand working "S2c" in docs/acceptance.md (each figure read from the SEC company facts of
18 November 2026 with its accession number, the arithmetic written out; re-read independently by the code and test
reviewer agents on 27 November; checked by Igor with a calculator on 27 November, rule 14.5). Coca-Cola is
also in the issue (#71). Amazon files its own twelve-month totals in its 10-Q (accession 0001018724-26-000040):
capital expenditure 215,192, operating cash flow 168,300 and net income 134,779 (USD m), a source independent of
this code. Amounts in USD million unless said otherwise.
"""

import json
from datetime import date

import pytest

from src.data.company import DEMO_DIR, load_company
from src.data.evidence import ANNUAL_FORMS, trim_companyfacts
from src.data.resolver import resolve

M = 1_000_000

# ticker: (start, end of the twelve months, {line item: USD m})
TWELVE_MONTHS = {
    # FY2025 + nine months 2026 (to 2 October) − nine months 2025 (to 26 September)
    "KO": (date(2025, 9, 27), date(2026, 10, 2), {
        "revenue": 51_054,  # 47,941 + 39,232 − 36,119
        "net_income": 14_629,  # 13,107 + 12,358 − 10,836
        "operating_cash_flow": 16_227,  # 7,408 + 12,471 − 3,652
        "capital_expenditure": 1_945,  # 2,112 + 1,063 − 1,230
    }),
    # FY2025 + nine months 2026 − nine months 2025 (to 30 September)
    "AMZN": (date(2025, 10, 1), date(2026, 9, 30), {
        "revenue": 797_455,  # 716,924 + 584,069 − 503,538
        "net_income": 134_779,  # 77,670 + 113,587 − 56,478; Amazon's own total: 134,779
        "operating_cash_flow": 168_300,  # 139,514 + 113,841 − 85,055; Amazon's own total: 168,300
        "capital_expenditure": 215_192,  # 131,819 + 175,670 − 92,297; Amazon's own total: 215,192
    }),
    # FY2025 + nine months 2026 − nine months 2025 (to 30 September)
    "MCD": (date(2025, 10, 1), date(2026, 9, 30), {
        "revenue": 27_782,  # 26,885 + 20,773 − 19,876
        "net_income": 8_995,  # 8,563 + 6,831 − 6,399
        "operating_cash_flow": 10_951,  # 10,551 + 8,254 − 7,854
        "capital_expenditure": 3_460,  # 3,365 + 2,401 − 2,306
    }),
    # FY ending 2026-01-25 + six months to 2026-07-26 − six months to 2025-07-27
    "NVDA": (date(2025, 7, 28), date(2026, 7, 26), {
        "revenue": 302_970,  # 215,938 + 177,837 − 90,805
        "net_income": 192_880,  # 120,067 + 118,010 − 45,197
        "operating_cash_flow": 134_360,  # 102,718 + 74,421 − 42,779
        "capital_expenditure": 7_354,  # 6,042 + 4,434 − 3,122
    }),
}

# Apple's latest report is its 10-K for the fiscal year ending 2026-09-26 (filed 2026-11-03): no 10-Q after it.
APPLE_FY = {"revenue": 478_834, "net_income": 132_175, "operating_cash_flow": 145_097, "capital_expenditure": 9_041}

# ticker: (balance-sheet date, financial debt, minority interest in USD m; shares; cover-page date)
BALANCES = {
    "KO": (date(2026, 10, 2), 41_546, 2_161, 4_301_902_335, date(2026, 10, 26)),  # 36,623 + 4,923 = 41,546
    "AMZN": (date(2026, 9, 30), 181_267, 0, 10_813_138_306, date(2026, 10, 21)),  # 180,887 + 380
    "MCD": (date(2026, 9, 30), 39_820, 0, 705_784_744, date(2026, 9, 30)),  # long-term debt, all inside it
    "NVDA": (date(2026, 7, 26), 33_366, 0, 24_100_000_000, date(2026, 8, 21)),  # 32,366 + 1,000
    "AAPL": (date(2026, 9, 26), 80_111, 0, 14_532_182_000, date(2026, 10, 23)),  # 78,114 + commercial paper 1,997
}


@pytest.fixture(scope="module")
def demo():
    return {ticker: load_company(ticker, demo=True) for ticker in ("KO", "AAPL", "NVDA", "MCD", "AMZN")}


@pytest.mark.parametrize("ticker, metric", [(t, m) for t, (_, _, values) in TWELVE_MONTHS.items() for m in values])
def test_the_twelve_months_to_the_latest_quarter_match_the_hand_working(demo, ticker, metric):
    start, end, values = TWELVE_MONTHS[ticker]
    fact = demo[ticker].recent[metric]
    assert fact.value == values[metric] * M
    assert (fact.kind, fact.period_start, fact.period_end) == ("derived", start, end)


@pytest.mark.parametrize("metric", APPLE_FY)
def test_apples_twelve_months_are_its_latest_fiscal_year(demo, metric):
    fact = demo["AAPL"].recent[metric]
    assert fact.value == APPLE_FY[metric] * M
    assert (fact.kind, fact.form, fact.accession) == ("reported", "10-K", "0000320193-26-000026")
    assert (fact.period_start, fact.period_end) == (date(2025, 9, 28), date(2026, 9, 26))


def test_coca_colas_free_cash_flow_over_the_last_twelve_months_is_the_one_in_issue_71(demo):
    recent = demo["KO"].recent
    assert recent["operating_cash_flow"].value - recent["capital_expenditure"].value == 14_282 * M  # 16,227 − 1,945


def test_amazons_twelve_months_equal_the_totals_amazon_files_itself(demo):
    # Independent of our formula: Amazon's 10-Q states these twelve-month totals (10-Q 0001018724-26-000040).
    facts = json.loads((DEMO_DIR / "AMZN" / "companyfacts.json").read_text(encoding="utf-8"))["facts"]["us-gaap"]
    tags = {"capital_expenditure": "PaymentsToAcquireProductiveAssets", "net_income": "NetIncomeLoss",
            "operating_cash_flow": "NetCashProvidedByUsedInOperatingActivities"}
    for metric, tag in tags.items():
        own = [x["val"] for x in facts[tag]["units"]["USD"] if x["accn"] == "0001018724-26-000040"
               and x.get("start") == "2025-10-01" and x["end"] == "2026-09-30"]
        assert own == [demo["AMZN"].recent[metric].value], metric


@pytest.mark.parametrize("ticker", BALANCES)
def test_the_latest_balance_sheet_and_share_count_match_the_hand_working(demo, ticker):
    when, debt, minority, shares, cover = BALANCES[ticker]
    recent = demo[ticker].recent
    assert (recent["financial_debt"].value, recent["financial_debt"].period_end) == (debt * M, when)
    assert recent["minority_interest"].value == minority * M
    assert recent["minority_interest"].period_end == when
    assert (recent["shares"].value, recent["shares"].period_end) == (shares, cover)


@pytest.mark.parametrize("ticker", ["AMZN", "MCD", "NVDA", "AAPL"])
def test_no_minority_interest_reported_is_nil_with_its_reason(demo, ticker):
    fact = demo[ticker].recent["minority_interest"]
    assert fact.kind == "assumption" and "nil" in fact.note


@pytest.mark.parametrize("ticker", ["KO", "AAPL", "NVDA", "MCD", "AMZN"])
def test_every_demo_company_has_all_seven_latest_figures(demo, ticker):
    recent = demo[ticker].recent
    assert set(recent) == {"revenue", "net_income", "operating_cash_flow", "capital_expenditure",
                           "financial_debt", "minority_interest", "shares"}
    assert all(fact.kind != "missing" for fact in recent.values())


@pytest.mark.parametrize("ticker", ["KO", "AAPL", "NVDA", "MCD", "AMZN"])
def test_the_annual_figures_and_warnings_are_the_same_as_without_the_quarterly_reports(demo, ticker):
    # The demo files now hold the 10-Q entries too (slice S2c). Everything the app read before must be unchanged:
    # the same data resolved from the annual-report entries only gives the same items and warnings.
    folder = DEMO_DIR / ticker
    facts = json.loads((folder / "companyfacts.json").read_text(encoding="utf-8"))
    submissions = json.loads((folder / "submissions.json").read_text(encoding="utf-8"))
    annual = resolve(ticker, trim_companyfacts(facts, ANNUAL_FORMS), submissions, demo[ticker].retrieved)
    assert demo[ticker].items == annual.items
    assert demo[ticker].warnings == annual.warnings
