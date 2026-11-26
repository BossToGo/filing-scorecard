"""The latest figures (slice S2c, issue #71 item 1): twelve months to the latest quarterly report, and the latest
balance sheet, in `CompanyData.recent`. Owner: A.

Rule: twelve months ending at the latest quarter = the last fiscal year (10-K) + this year's year to date (10-Q,
starting the day after that fiscal year end) − last year's year to date (the comparison column of the same 10-Q).
When the 10-K is the latest report, the twelve months are that fiscal year. Balances (debt, minority interest) follow
the annual rules at the latest balance-sheet date; shares come from the cover page of the latest report.

Inputs are a small hand-made company in the SEC's layout: fiscal year = calendar year, the 10-K for 2025, and a 10-Q
for the nine months to 30 September 2026 (filed 28 October 2026) with its 2025 comparison column. Amounts in USD
million (M), the arithmetic written out in each test.
"""

from datetime import date, datetime, timezone

import pytest

from src.data.resolver import resolve

M = 1_000_000
Q3 = "0000000000-26-000090"  # the 10-Q for the nine months to 2026-09-30
Q2 = "0000000000-26-000060"  # the 10-Q for the six months to 2026-06-30
K25 = "0000000000-26-000001"  # the 10-K for 2025
RETRIEVED = datetime(2026, 11, 18, 15, 0, tzinfo=timezone.utc)
SUBMISSIONS = {"cik": "0000000001", "name": "TEST CO", "sic": "2080", "sicDescription": "Beverages",
               "fiscalYearEnd": "1231", "filings": {"recent": {"form": ["10-K"], "filingDate": ["2026-02-20"],
                                                               "accessionNumber": ["a"]}}}


def e(val, end, start=None, form="10-K", accn=None, filed=None):
    """One company-facts entry, `val` in USD million; 10-K entries default to the 2025 annual report."""
    entry = {"end": end, "val": val * M, "fy": int(end[:4]), "fp": "FY",
             "form": form, "accn": accn or (K25 if form == "10-K" else Q3),
             "filed": filed or ("2026-02-20" if form == "10-K" else "2026-10-28")}
    if start:
        entry["start"] = start
    return entry


def count(shares, end, form="10-K", accn=K25):
    """A cover-page share count (dei), in shares."""
    return {**e(0, end, form=form, accn=accn), "val": shares}


def years(first_value, step=10):
    """Annual flows 2021 to 2025, each in the 10-K of the following year."""
    return [e(first_value + step * (y - 2021), f"{y}-12-31", f"{y}-01-01", accn=f"0000000000-{y - 1999}-000001",
              filed=f"{y + 1}-02-20") for y in range(2021, 2026)]


def ytd(val, prior, accn=Q3, end="2026-09-30", prior_end="2025-09-30", form="10-Q", filed=None):
    """A 10-Q's year to date and its comparison column (same filing)."""
    return [e(val, end, "2026-01-01", form, accn, filed), e(prior, prior_end, "2025-01-01", form, accn, filed)]


# FY2025 / nine months 2026 / nine months 2025 (USD m):
#   revenue              1,040 / 820 / 760  ->  1,040 + 820 − 760 = 1,100
#   net income             190 / 130 / 110  ->    190 + 130 − 110 =   210
#   operating cash flow    340 / 260 / 210  ->    340 + 260 − 210 =   390
#   capital expenditure    130 /  70 /  60  ->    130 +  70 −  60 =   140
FLOWS = {
    "Revenues": years(1000) + ytd(820, 760),
    "NetIncomeLoss": years(150) + ytd(130, 110),
    "NetCashProvidedByUsedInOperatingActivities": years(300) + ytd(260, 210),
    "PaymentsToAcquirePropertyPlantAndEquipment": years(90) + ytd(70, 60),
}
# Balance sheet at 2026-09-30 (10-Q): long-term debt 500 including current maturities (450 + 50), short-term
# borrowings 20 -> financial debt 500 + 20 = 520; minority interest 30. At 2025-12-31 (10-K): 480 and 25.
BALANCES = {
    "LongTermDebt": [e(480, "2025-12-31"), e(500, "2026-09-30", form="10-Q")],
    "LongTermDebtNoncurrent": [e(440, "2025-12-31"), e(450, "2026-09-30", form="10-Q")],
    "LongTermDebtCurrent": [e(40, "2025-12-31"), e(50, "2026-09-30", form="10-Q")],
    "ShortTermBorrowings": [e(10, "2025-12-31"), e(20, "2026-09-30", form="10-Q")],
    "MinorityInterest": [e(25, "2025-12-31"), e(30, "2026-09-30", form="10-Q")],
}
# Cover pages: 1,010,000,000 shares on 2026-02-10 (10-K), 1,000,000,000 on 2026-10-20 (the Q3 10-Q).
COVER = [count(1_010_000_000, "2026-02-10"), count(1_000_000_000, "2026-10-20", "10-Q", Q3)]


def company(us_gaap=None, cover=None, drop=()):
    tags = {**FLOWS, **BALANCES, **(us_gaap or {})}
    return {"cik": 1, "entityName": "TEST CO", "facts": {
        "us-gaap": {tag: {"label": tag, "units": {"USD": entries}} for tag, entries in tags.items() if tag not in drop},
        "dei": {"EntityCommonStockSharesOutstanding": {"units": {"shares": COVER if cover is None else cover}}},
    }}


def run(**kw):
    return resolve("TST", company(**kw), SUBMISSIONS, RETRIEVED)


def annual_only(entries):
    return [x for x in entries if x["form"] == "10-K"]


ANNUAL_ONLY = {tag: annual_only(entries) for tag, entries in {**FLOWS, **BALANCES}.items()}


# --- twelve months to the latest quarter ------------------------------------------------------------------------


@pytest.mark.parametrize("metric, expected", [
    ("revenue", 1_100), ("net_income", 210), ("operating_cash_flow", 390), ("capital_expenditure", 140),
])
def test_the_twelve_months_are_the_fiscal_year_plus_this_year_to_date_minus_last_year_to_date(metric, expected):
    fact = run().recent[metric]
    assert fact.value == expected * M
    assert fact.kind == "derived"
    assert (fact.period_start, fact.period_end) == (date(2025, 10, 1), date(2026, 9, 30))
    assert fact.unit == "USD" and fact.metric == metric


def test_the_note_names_the_three_figures_and_their_filings():
    note = run().recent["revenue"].note
    for text in ("1,040,000,000", "820,000,000", "760,000,000", K25, Q3, "2025-12-31", "2026-09-30", "2025-09-30"):
        assert text in note


def test_the_latest_10q_is_used_when_there_are_several():
    # Six months to 2026-06-30 (10-Q Q2): 520 against 500. The nine-month 10-Q filed later wins: still 1,100.
    revenue = FLOWS["Revenues"] + ytd(520, 500, accn=Q2, end="2026-06-30", prior_end="2025-06-30",
                                      filed="2026-07-28")
    assert run(us_gaap={"Revenues": revenue}).recent["revenue"].value == 1_100 * M


def test_an_amended_10q_replaces_the_original():
    # 10-Q/A filed 2026-11-15 restates the year to date to 830 (prior 760): 1,040 + 830 − 760 = 1,110.
    revenue = FLOWS["Revenues"] + ytd(830, 760, accn="0000000000-26-000099", form="10-Q/A", filed="2026-11-15")
    assert run(us_gaap={"Revenues": revenue}).recent["revenue"].value == 1_110 * M


def test_twelve_month_totals_in_a_10q_are_never_read_as_a_fiscal_year():
    # Amazon's 10-Qs also file "twelve months ended" totals (365 days). Neither the fiscal years nor the twelve
    # months may use them: the annual figures stay those of the 10-K, the twelve months stay 1,100.
    twelve = e(9_999, "2026-09-30", "2025-10-01", "10-Q")
    data = run(us_gaap={"Revenues": FLOWS["Revenues"] + [twelve]})
    assert data.fiscal_years("revenue")[-1] == date(2025, 12, 31)
    assert data.fact("revenue", date(2025, 12, 31)).value == 1_040 * M
    assert data.recent["revenue"].value == 1_100 * M


def test_the_annual_figures_and_warnings_do_not_change_when_quarterly_reports_are_added():
    with_quarters, without = run(), run(us_gaap=ANNUAL_ONLY, cover=annual_only(COVER))
    assert with_quarters.items == without.items
    assert with_quarters.warnings == without.warnings


# --- the 10-K is the latest report --------------------------------------------------------------------------------


def test_when_the_10k_is_the_latest_report_the_twelve_months_are_that_fiscal_year():
    data = run(us_gaap=ANNUAL_ONLY, cover=annual_only(COVER))
    fact = data.recent["revenue"]
    assert fact.value == 1_040 * M and fact.kind == "reported" and fact.form == "10-K"
    assert (fact.period_start, fact.period_end) == (date(2025, 1, 1), date(2025, 12, 31))
    assert "latest report" in fact.note


def test_when_the_10k_is_the_latest_report_the_balances_are_those_of_the_fiscal_year_end():
    data = run(us_gaap=ANNUAL_ONLY, cover=annual_only(COVER))
    fy0 = date(2025, 12, 31)
    assert data.recent["financial_debt"].value == data.fact("financial_debt", fy0).value == 490 * M  # 480 + 10
    assert data.recent["minority_interest"].value == 25 * M
    assert data.recent["shares"] == data.latest("shares")


def test_a_10q_of_last_year_does_not_count_as_a_later_report():
    # Only the nine months to 2025-09-30 were filed on a 10-Q (before the 2025 10-K): the 10-K is the latest report.
    old = [e(760, "2025-09-30", "2025-01-01", "10-Q", "0000000000-25-000090", "2025-10-28")]
    data = run(us_gaap={**ANNUAL_ONLY, "Revenues": years(1000) + old}, cover=annual_only(COVER))
    assert data.recent["revenue"].value == 1_040 * M and data.recent["revenue"].period_end == date(2025, 12, 31)


# --- missing is never zero ------------------------------------------------------------------------------------------


def test_a_figure_with_no_year_to_date_in_the_latest_10q_is_missing():
    # Capital expenditure is in the 10-K only, while revenue has a 10-Q: never the fiscal year alone, never zero.
    fact = run(us_gaap={"PaymentsToAcquirePropertyPlantAndEquipment": years(90)}).recent["capital_expenditure"]
    assert fact.kind == "missing" and fact.value is None
    assert "year to date" in fact.note and fact.period_end == date(2026, 9, 30)


def test_a_year_to_date_without_its_comparison_column_is_missing():
    # Last year's nine months are only in last year's own 10-Q, not in the comparison column of this one.
    revenue = years(1000) + [e(820, "2026-09-30", "2026-01-01", "10-Q"),
                             e(760, "2025-09-30", "2025-01-01", "10-Q", "0000000000-25-000090", "2025-10-28")]
    fact = run(us_gaap={"Revenues": revenue}).recent["revenue"]
    assert fact.kind == "missing" and fact.value is None and "comparison" in fact.note


def test_a_comparison_period_of_another_length_is_not_used():
    # Nine months this year against six months last year (272 days against 180): not the same quarters.
    revenue = years(1000) + [e(820, "2026-09-30", "2026-01-01", "10-Q"), e(500, "2025-06-30", "2025-01-01", "10-Q")]
    fact = run(us_gaap={"Revenues": revenue}).recent["revenue"]
    assert fact.kind == "missing" and fact.value is None and "days" in fact.note


def test_a_missing_fiscal_year_figure_makes_the_twelve_months_missing():
    net_income = [x for x in FLOWS["NetIncomeLoss"] if x["end"] != "2025-12-31"]  # no FY2025 net income
    fact = run(us_gaap={"NetIncomeLoss": net_income}).recent["net_income"]
    assert fact.kind == "missing" and fact.value is None


def test_the_year_to_date_must_use_the_tag_of_the_fiscal_year_figure():
    # FY2025 under Revenues, the 10-Q only under another revenue tag: the definitions may differ, so not mixed.
    other = {"RevenueFromContractWithCustomerExcludingAssessedTax": ytd(820, 760)}
    fact = run(us_gaap={"Revenues": years(1000), **other}).recent["revenue"]
    assert fact.kind == "missing" and "no year to date to 2026-09-30 under Revenues" in fact.note


# --- the latest balance sheet ---------------------------------------------------------------------------------------


def test_debt_and_minority_interest_come_from_the_latest_10q_balance_sheet():
    recent = run().recent
    debt, minority = recent["financial_debt"], recent["minority_interest"]
    assert debt.value == 520 * M and debt.kind == "derived" and debt.period_end == date(2026, 9, 30)
    assert minority.value == 30 * M and minority.kind == "reported" and minority.accession == Q3
    assert minority.period_end == date(2026, 9, 30)


def test_shares_come_from_the_cover_page_of_the_latest_report():
    shares = run().recent["shares"]
    assert shares.value == 1_000_000_000 and shares.kind == "reported" and shares.accession == Q3
    assert shares.unit == "shares" and shares.period_end == date(2026, 10, 20)


def test_a_cover_page_dated_on_the_quarter_end_itself_counts():
    # McDonald's dates its 10-Q cover-page count on the quarter end (2026-09-30).
    cover = [COVER[0], count(1_000_000_000, "2026-09-30", "10-Q", Q3)]
    assert run(cover=cover).recent["shares"].value == 1_000_000_000


def test_without_a_cover_page_count_in_the_latest_10q_the_annual_count_is_used_and_said():
    shares = run(cover=annual_only(COVER)).recent["shares"]
    assert shares.value == 1_010_000_000 and shares.period_end == date(2026, 2, 10)
    assert "latest quarterly report" in shares.note


def test_an_older_10q_cover_page_does_not_stand_in_for_the_latest_report():
    # The latest 10-Q (Q3) has no count; the Q2 10-Q has one (dated 2026-07-20). The rule is "the cover page of the
    # latest report, else the latest annual report's": the Q2 count belongs to another report, so it is not used.
    cover = [COVER[0], count(1_005_000_000, "2026-07-20", "10-Q", Q2)]
    shares = run(cover=cover).recent["shares"]
    assert shares.value == 1_010_000_000 and shares.accession == K25


def test_minority_interest_reported_in_the_10k_but_not_in_the_10q_is_missing_not_nil():
    fact = run(us_gaap={"MinorityInterest": [e(25, "2025-12-31")]}).recent["minority_interest"]
    assert fact.kind == "missing" and fact.value is None


def test_no_minority_interest_anywhere_is_nil_as_for_the_annual_figures():
    fact = run(drop=("MinorityInterest",)).recent["minority_interest"]
    assert fact.kind == "assumption" and fact.value == 0 and "nil" in fact.note


def test_no_debt_in_the_10q_makes_the_latest_debt_missing():
    debt_tags = ("LongTermDebt", "LongTermDebtNoncurrent", "LongTermDebtCurrent", "ShortTermBorrowings")
    us_gaap = {tag: annual_only(BALANCES[tag]) for tag in debt_tags}
    fact = run(us_gaap=us_gaap).recent["financial_debt"]
    assert fact.kind == "missing" and fact.value is None and fact.period_end == date(2026, 9, 30)


def test_a_debt_warning_at_the_quarter_end_goes_into_the_note_not_into_the_company_warnings():
    # At 2026-09-30 the total 500 differs from non-current + current 450 + 30 = 480 by 4% (> 1%): DEBT_CHECK.
    # The gates read `warnings`, and nothing that exists today may change, so the warning stays in the figure.
    us_gaap = {"LongTermDebtCurrent": [e(40, "2025-12-31"), e(30, "2026-09-30", form="10-Q")]}
    data = run(us_gaap=us_gaap)
    assert "DEBT_CHECK" in data.recent["financial_debt"].note
    assert not any("2026-09-30" in w for w in data.warnings)


def test_a_warning_about_another_balance_does_not_land_in_the_minority_interest_note():
    # Preferred stock at 2026-09-30 restated by a 10-Q/A (5 -> 6, more than 1%): a RESTATED warning about preferred
    # stock, which is no latest figure. It must not be written into the minority interest's note.
    preferred = {"PreferredStockValue": [e(5, "2026-09-30", form="10-Q"),
                                         e(6, "2026-09-30", form="10-Q/A", accn="0000000000-26-000099",
                                           filed="2026-11-15")]}
    note = run(us_gaap=preferred).recent["minority_interest"].note
    assert "preferred" not in note.lower() and "RESTATED" not in note


def test_the_recent_figures_hold_exactly_the_seven_line_items():
    assert set(run().recent) == {"revenue", "net_income", "operating_cash_flow", "capital_expenditure",
                                 "financial_debt", "minority_interest", "shares"}
