"""Line-item resolver (slice S2): one test per rule of SPEC §5.3 and per planted mistake of SPEC §5.4. Owner: A.

Inputs are small hand-made company facts in the SEC's layout; the expected results follow from the rules, with
the arithmetic written out. Amounts are in USD as filed.
"""

from datetime import date, datetime, timezone

import pytest

from src.data.resolver import resolve

M = 1_000_000  # one million USD, so the inputs read like a 10-K


def entry(val, end, start=None, form="10-K", filed=None, fy=None, accn=None):
    year = int(end[:4])
    e = {"end": end, "val": val, "accn": accn or f"0000000000-{(year + 1) % 100:02d}-000001",
         "fy": fy if fy is not None else year, "fp": "FY", "form": form, "filed": filed or f"{year + 1}-02-20"}
    if start:
        e["start"] = start
    return e


def flow(val, year, **kw):
    return entry(val, f"{year}-12-31", start=f"{year}-01-01", **kw)


def instant(val, year, **kw):
    return entry(val, f"{year}-12-31", **kw)


def revenue_years(first=2021, last=2025):
    return [flow((1000 + 10 * (y - first)) * M, y) for y in range(first, last + 1)]


def facts(us_gaap=None, dei=None, units=None):
    units = units or {}
    return {
        "cik": 1,
        "entityName": "TEST CO",
        "facts": {
            "us-gaap": {tag: {"label": tag, "units": {units.get(tag, "USD"): entries}}
                        for tag, entries in {"Revenues": revenue_years(), **(us_gaap or {})}.items()},
            "dei": dei or {},
        },
    }


SUBMISSIONS = {
    "cik": "0000000001",
    "name": "TEST CO",
    "sic": "2080",
    "sicDescription": "Beverages",
    "fiscalYearEnd": "1231",
    "filings": {"recent": {"form": ["10-K", "10-K"], "filingDate": ["2026-02-20", "2025-02-21"],
                           "accessionNumber": ["a", "b"]}},
}
RETRIEVED = datetime(2026, 11, 18, 15, 0, tzinfo=timezone.utc)


def run(us_gaap=None, dei=None, units=None, **kw):
    return resolve("TST", facts(us_gaap, dei, units), SUBMISSIONS, RETRIEVED, **kw)


def fy(year):
    return date(year, 12, 31)


def codes(data):
    return {w.split(":")[0] for w in data.warnings}


# --- header and fiscal years ------------------------------------------------------------------------------------


def test_the_header_comes_from_the_submissions_file():
    data = run()
    assert (data.ticker, data.cik, data.name, data.sic, data.fiscal_year_end) == ("TST", "0000000001", "TEST CO",
                                                                                   "2080", "1231")
    assert data.latest_10k_filed == date(2026, 2, 20)
    assert data.retrieved == RETRIEVED


def test_the_five_latest_fiscal_years_are_kept_oldest_first():
    data = run({"Revenues": revenue_years(2019, 2025)})
    assert data.fiscal_years("revenue") == [fy(y) for y in range(2021, 2026)]


def test_the_number_of_years_is_a_setting():
    assert run(years=3).fiscal_years("revenue") == [fy(2023), fy(2024), fy(2025)]


# --- §5.3.1 only 10-K / 10-K/A; flows cover 350 to 380 days ------------------------------------------------------


def test_figures_from_quarterly_reports_are_ignored():
    data = run({"NetIncomeLoss": [flow(90 * M, 2025, form="10-Q"), flow(100 * M, 2025)]})
    assert data.fact("net_income", fy(2025)).value == 100 * M


def test_an_amended_annual_report_counts():
    data = run({"NetIncomeLoss": [flow(100 * M, 2025), flow(101 * M, 2025, form="10-K/A", filed="2026-05-01")]})
    assert data.fact("net_income", fy(2025)).value == 101 * M


def test_a_53_week_year_is_kept():
    data = run({"NetIncomeLoss": [entry(100 * M, "2025-12-31", start="2024-12-26")]})  # 370 days
    assert data.fact("net_income", fy(2025)).value == 100 * M


def test_planted_a_nine_month_figure_is_never_read_as_a_year():
    # SPEC §5.4: nine months ending on the fiscal year end (1 April to 31 December, 274 days) is not a year.
    data = run({"NetIncomeLoss": [entry(75 * M, "2025-12-31", start="2025-04-01")]})
    fact = data.fact("net_income", fy(2025))
    assert fact.kind == "missing" and fact.value is None


# --- §5.3.2 the fiscal year comes from the period end date, never from `fy` -------------------------------------


def test_planted_a_wrong_fiscal_year_label_is_ignored():
    # A comparative for 2022 inside the 10-K for 2024 carries fy=2024 (session 5: Coca-Cola).
    data = run({"NetCashProvidedByUsedInOperatingActivities": [flow(160 * M, 2022, fy=2024, filed="2025-02-21")]})
    assert data.fact("operating_cash_flow", fy(2022)).value == 160 * M
    assert data.fact("operating_cash_flow", fy(2024)).kind == "missing"


# --- §5.3.3 balance sheet figures at the fiscal year end date ------------------------------------------------------


def test_a_balance_at_another_date_is_not_used():
    data = run({"Assets": [entry(1750 * M, "2025-06-30"), instant(1640 * M, 2024)]})
    assert data.fact("total_assets", fy(2025)).kind == "missing"
    assert data.fact("total_assets", fy(2024)).value == 1640 * M


# --- §5.3.4 restatements --------------------------------------------------------------------------------------------


def test_planted_a_restated_figure_uses_the_latest_filing_and_keeps_the_original():
    # 100 filed in 2022, restated to 103 in the 10-K filed in 2024: 3% > 1% → warning.
    data = run({"NetIncomeLoss": [flow(100 * M, 2021, filed="2022-02-20", accn="acc-orig"),
                                  flow(103 * M, 2021, filed="2024-02-20", accn="acc-new")]})
    fact = data.fact("net_income", fy(2021))
    assert fact.value == 103 * M and fact.accession == "acc-new" and fact.filed == date(2024, 2, 20)
    assert "100,000,000" in fact.note and "acc-orig" in fact.note
    assert "RESTATED" in codes(data)


def test_a_restatement_within_one_percent_is_recorded_without_a_warning():
    data = run({"NetIncomeLoss": [flow(100 * M, 2021, filed="2022-02-20"), flow(100.5 * M, 2021, filed="2024-02-20")]})
    assert data.fact("net_income", fy(2021)).value == 100.5 * M
    assert "RESTATED" not in codes(data)


# --- §5.3.5 only US dollars ----------------------------------------------------------------------------------------


def test_a_figure_in_another_currency_is_missing_and_flagged():
    data = run({"NetIncomeLoss": [flow(100 * M, 2025)]}, units={"NetIncomeLoss": "EUR"})
    fact = data.fact("net_income", fy(2025))
    assert fact.kind == "missing" and "EUR" in fact.note
    assert "NON_USD" in codes(data)


def test_planted_amounts_are_kept_in_dollars_exactly_as_filed():
    # SPEC §5.4: dollars read as millions. Nothing is scaled; the unit stays "USD".
    data = run({"Revenues": [flow(47_941_000_000, 2025)]})
    fact = data.fact("revenue", fy(2025))
    assert fact.value == 47_941_000_000 and fact.unit == "USD"


# --- §5.3.6 never add up segments; §5.2 missing is never zero --------------------------------------------------------


def test_a_line_item_without_a_company_wide_figure_is_missing_with_a_reason():
    fact = run().fact("operating_income", fy(2025))
    assert fact.kind == "missing" and fact.value is None
    assert "OperatingIncomeLoss" in fact.note and "2025-12-31" in fact.note


# --- §5.3.7 fallback tags, per fiscal year; conflicts flagged ----------------------------------------------------------


def test_fallback_tags_are_tried_for_each_fiscal_year():
    data = run({"Revenues": [flow(1000 * M, 2021), flow(1080 * M, 2022)],
                "RevenueFromContractWithCustomerExcludingAssessedTax": [flow(v * M, y) for y, v in
                                                                         [(2023, 1150), (2024, 1210), (2025, 1300)]]})
    tags = [data.fact("revenue", fy(y)).tag for y in range(2021, 2026)]
    assert tags == ["Revenues"] * 2 + ["RevenueFromContractWithCustomerExcludingAssessedTax"] * 3


def test_two_tags_with_different_values_are_flagged_and_the_first_is_used():
    data = run({"Revenues": revenue_years()[:-1] + [flow(1300 * M, 2025)],
                "RevenueFromContractWithCustomerExcludingAssessedTax": [flow(1250 * M, 2025)]})
    fact = data.fact("revenue", fy(2025))
    assert fact.value == 1300 * M and fact.tag == "Revenues"
    assert "1,250,000,000" in fact.note
    assert "TAG_CONFLICT" in codes(data)


def test_a_company_override_changes_the_tag_order_and_explains_why():
    from src.data.resolver import load_tag_map

    tag_map = load_tag_map()
    tag_map = {**tag_map, "overrides": {"TST": {"revenue": {
        "tags": ["RevenueFromContractWithCustomerExcludingAssessedTax", "Revenues"],
        "reason": "the 10-K's income statement total is filed under the second tag"}}}}
    data = run({"Revenues": revenue_years()[:-1] + [flow(457 * M, 2025)],
                "RevenueFromContractWithCustomerExcludingAssessedTax": [flow(2199 * M, 2025)]}, tag_map=tag_map)
    fact = data.fact("revenue", fy(2025))
    assert fact.value == 2199 * M and fact.tag == "RevenueFromContractWithCustomerExcludingAssessedTax"
    assert "income statement total" in fact.note and "457,000,000" in fact.note
    assert "TAG_CONFLICT" not in codes(data)  # a known, explained difference is recorded, not raised again


def test_two_tags_with_the_same_value_are_not_flagged():
    data = run({"RevenueFromContractWithCustomerExcludingAssessedTax": [flow(1040 * M, 2025)]})
    assert "TAG_CONFLICT" not in codes(data)


# --- derived figures (SPEC §6) -----------------------------------------------------------------------------------------


def test_gross_profit_is_derived_when_not_reported():
    data = run({"CostOfRevenue": [flow(600 * M, 2025)]})
    fact = data.fact("gross_profit", fy(2025))
    assert fact.kind == "derived" and fact.value == (1040 - 600) * M  # revenue 2025 = 1,040
    assert "revenue" in fact.note and "cost_of_revenue" in fact.note
    assert "DERIVED" in codes(data)


def test_total_liabilities_are_derived_from_assets_minus_total_equity():
    data = run({"Assets": [instant(1750 * M, 2025)], "StockholdersEquity": [instant(800 * M, 2025)],
                "MinorityInterest": [instant(20 * M, 2025)]})
    assert data.fact("total_equity", fy(2025)).value == (800 + 20) * M
    assert data.fact("total_liabilities", fy(2025)).value == (1750 - 820) * M
    assert data.fact("total_liabilities", fy(2025)).kind == "derived"


def test_without_minority_interest_total_equity_is_equity_with_a_note():
    data = run({"Assets": [instant(1750 * M, 2025)], "StockholdersEquity": [instant(820 * M, 2025)]})
    total_equity = data.fact("total_equity", fy(2025))
    assert total_equity.value == 820 * M and "non-controlling" in total_equity.note
    assert data.fact("total_liabilities", fy(2025)).value == (1750 - 820) * M


# --- financial debt (SPEC §6; plan Q5) ---------------------------------------------------------------------------------


def debt_fact(us_gaap):
    data = run(us_gaap)
    return data.fact("financial_debt", fy(2025)), data.fact("current_financial_debt", fy(2025))


def test_debt_is_non_current_plus_current_plus_short_term_borrowings():
    debt, current = debt_fact({"LongTermDebtNoncurrent": [instant(400 * M, 2025)],
                               "LongTermDebtCurrent": [instant(50 * M, 2025)],
                               "ShortTermBorrowings": [instant(30 * M, 2025)]})
    assert debt.value == (400 + 50 + 30) * M and debt.kind == "derived"
    assert current.value == (50 + 30) * M


def test_commercial_paper_is_added_when_there_is_no_short_term_borrowings_total():
    debt, current = debt_fact({"LongTermDebtNoncurrent": [instant(400 * M, 2025)],
                               "LongTermDebtCurrent": [instant(50 * M, 2025)],
                               "CommercialPaper": [instant(20 * M, 2025)],
                               "OtherShortTermBorrowings": [instant(5 * M, 2025)]})
    assert debt.value == (400 + 50 + 20 + 5) * M
    assert current.value == (50 + 20 + 5) * M


def test_commercial_paper_is_not_added_twice_when_short_term_borrowings_include_it():
    debt, _ = debt_fact({"LongTermDebtNoncurrent": [instant(400 * M, 2025)],
                         "ShortTermBorrowings": [instant(30 * M, 2025)],
                         "CommercialPaper": [instant(20 * M, 2025)]})
    assert debt.value == (400 + 30) * M


def test_nothing_is_added_when_short_term_items_are_classified_inside_long_term_debt():
    # The McDonald's case: total long-term debt equals the non-current part.
    debt, current = debt_fact({"LongTermDebt": [instant(400 * M, 2025)],
                               "LongTermDebtNoncurrent": [instant(400 * M, 2025)],
                               "LongTermDebtCurrent": [instant(7 * M, 2025)],
                               "CommercialPaper": [instant(8 * M, 2025)]})
    assert debt.value == 400 * M
    assert current.value == 0 and "inside" in current.note


def test_the_newer_capital_lease_tags_are_used_as_fallbacks():
    # The Coca-Cola case from 2024 on.
    debt, _ = debt_fact({"LongTermDebtAndCapitalLeaseObligations": [instant(420 * M, 2025)],
                         "LongTermDebtAndCapitalLeaseObligationsCurrent": [instant(18 * M, 2025)],
                         "CommercialPaper": [instant(15 * M, 2025)]})
    assert debt.value == (420 + 18 + 15) * M


def test_a_total_long_term_debt_is_used_when_there_is_no_split():
    debt, _ = debt_fact({"LongTermDebt": [instant(450 * M, 2025)], "ShortTermBorrowings": [instant(10 * M, 2025)]})
    assert debt.value == (450 + 10) * M


def test_debt_without_any_debt_tag_is_missing():
    debt, current = debt_fact({})
    assert debt.kind == "missing" and current.kind == "missing"


# --- bridge items (SPEC §8.3) and shares (SPEC §6) -----------------------------------------------------------------------


def test_an_absent_bridge_item_is_treated_as_nil_and_labelled():
    fact = run().fact("preferred_stock", fy(2025))
    assert fact.kind == "assumption" and fact.value == 0 and "treated as nil" in fact.note


def test_a_reported_bridge_item_is_used():
    assert run({"MinorityInterest": [instant(20 * M, 2025)]}).fact("minority_interest", fy(2025)).value == 20 * M


def test_shares_come_from_the_cover_page_of_the_latest_annual_report():
    dei = {"EntityCommonStockSharesOutstanding": {"units": {"shares": [
        entry(4_310_000_000, "2025-02-18", form="10-K", filed="2025-02-21"),
        entry(4_300_000_000, "2026-02-18", form="10-K", filed="2026-02-20"),
        entry(4_290_000_000, "2026-04-20", form="10-Q", filed="2026-04-28")]}}}
    data = run(dei=dei)
    assert data.fiscal_years("shares") == [date(2026, 2, 18)]
    fact = data.fact("shares", date(2026, 2, 18))
    assert fact.value == 4_300_000_000 and fact.unit == "shares" and fact.kind == "reported"


def test_without_a_cover_page_count_the_diluted_average_is_used_with_a_warning():
    tag = "WeightedAverageNumberOfDilutedSharesOutstanding"
    data = run({tag: [flow(100_000_000, 2025)]}, units={tag: "shares"})
    fact = data.fact("shares", fy(2025))
    assert fact.value == 100_000_000 and fact.kind == "derived" and "average" in fact.note
    assert "AVERAGE_SHARES" in codes(data)


# --- planted sign error (SPEC §5.4) ---------------------------------------------------------------------------------------


def test_planted_a_negative_capital_expenditure_is_kept_as_filed_and_flagged():
    data = run({"PaymentsToAcquirePropertyPlantAndEquipment": [flow(-85 * M, 2025)]})
    assert data.fact("capital_expenditure", fy(2025)).value == -85 * M
    assert "SIGN" in codes(data)


def test_a_company_without_company_facts_still_has_its_header():
    # JPMorgan in the demo data: only the submissions file, so the gates can refuse it by its industry code.
    data = resolve("TST", None, SUBMISSIONS, RETRIEVED)
    assert data.sic == "2080" and data.items == {} and "NO_ANNUAL_DATA" in codes(data)
