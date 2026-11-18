"""Line-item resolver (slice S2): one test per rule of SPEC §5.3 and per planted mistake of SPEC §5.4. Owner: A.

Inputs are small hand-made company facts in the SEC's layout; the expected results follow from the rules, with
the arithmetic written out. Amounts are in USD as filed.
"""

from datetime import date, datetime, timezone

import pytest

from src.data.resolver import load_tag_map, resolve

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
    return [flow((1000 + 10 * (y - first)) * M, y) for y in range(first, last + 1)]  # 1,000 ... 1,040


def facts(us_gaap=None, dei=None, units=None, with_revenue=True):
    units = units or {}
    base = {"Revenues": revenue_years()} if with_revenue else {}
    return {
        "cik": 1,
        "entityName": "TEST CO",
        "facts": {
            "us-gaap": {tag: {"label": tag, "units": {units.get(tag, "USD"): entries}}
                        for tag, entries in {**base, **(us_gaap or {})}.items()},
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


def run(us_gaap=None, dei=None, units=None, with_revenue=True, **kw):
    return resolve("TST", facts(us_gaap, dei, units, with_revenue), SUBMISSIONS, RETRIEVED, **kw)


def with_override(metric, override):
    tag_map = load_tag_map()
    return {**tag_map, "overrides": {"TST": {metric: override}}}


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


def test_a_change_of_fiscal_year_end_does_not_create_overlapping_years():
    # June year ends until 2023-06-30, then December. 2023-06-30 is only 184 days before 2023-12-31: dropped.
    revenue = [entry(v * M, end, start=start) for v, start, end in [
        (900, "2021-07-01", "2022-06-30"), (950, "2022-07-01", "2023-06-30"), (980, "2023-01-01", "2023-12-31"),
        (1000, "2024-01-01", "2024-12-31"), (1040, "2025-01-01", "2025-12-31")]]
    data = run({"Revenues": revenue})
    assert data.fiscal_years("revenue") == [date(2022, 6, 30), fy(2023), fy(2024), fy(2025)]
    assert "FY_CHANGE" in codes(data)


# --- §5.3.1 only 10-K / 10-K/A; flows cover 350 to 380 days ------------------------------------------------------


def test_figures_from_quarterly_reports_are_ignored():
    data = run({"NetIncomeLoss": [flow(100 * M, 2025),
                                  flow(90 * M, 2025, form="10-Q", filed="2026-05-01", accn="q-acc")]})
    fact = data.fact("net_income", fy(2025))
    assert fact.value == 100 * M and fact.form == "10-K"


def test_an_amended_annual_report_counts():
    data = run({"NetIncomeLoss": [flow(100 * M, 2025), flow(101 * M, 2025, form="10-K/A", filed="2026-05-01")]})
    assert data.fact("net_income", fy(2025)).value == 101 * M


def test_an_amendment_filed_the_same_day_wins_whatever_its_accession_number():
    data = run({"NetIncomeLoss": [flow(101 * M, 2025, form="10-K/A", accn="0000000000-26-000001"),
                                  flow(100 * M, 2025, form="10-K", accn="0000000000-26-000009")]})
    assert data.fact("net_income", fy(2025)).value == 101 * M


@pytest.mark.parametrize("start, kept", [("2025-01-16", False), ("2025-01-15", True),
                                         ("2024-12-16", True), ("2024-12-15", False)])
def test_a_flow_must_cover_350_to_380_days(start, kept):
    # 2025-01-16 → 2025-12-31 is 349 days; 2025-01-15 is 350; 2024-12-16 is 380; 2024-12-15 is 381.
    fact = run({"NetIncomeLoss": [entry(100 * M, "2025-12-31", start=start)]}).fact("net_income", fy(2025))
    assert (fact.kind == "reported") is kept


def test_planted_a_nine_month_figure_is_never_read_as_a_year():
    # SPEC §5.4: nine months ending on the fiscal year end (1 April to 31 December, 274 days) is not a year.
    fact = run({"NetIncomeLoss": [entry(75 * M, "2025-12-31", start="2025-04-01")]}).fact("net_income", fy(2025))
    assert fact.kind == "missing" and fact.value is None


def test_two_annual_periods_ending_the_same_day_are_not_a_restatement():
    data = run({"NetIncomeLoss": [entry(100 * M, "2025-12-31", start="2025-01-01", filed="2026-02-20"),
                                  entry(104 * M, "2025-12-31", start="2024-12-27", filed="2026-02-21")]})
    assert "RESTATED" not in codes(data)


# --- §5.3.2 the fiscal year comes from the period end date, never from `fy` -------------------------------------


def test_planted_a_wrong_fiscal_year_label_is_ignored():
    data = run({"NetCashProvidedByUsedInOperatingActivities": [flow(160 * M, 2022, fy=2024, filed="2025-02-21")]})
    assert data.fact("operating_cash_flow", fy(2022)).value == 160 * M
    assert data.fact("operating_cash_flow", fy(2024)).kind == "missing"


# --- §5.3.3 balance sheet figures at the fiscal year end date ------------------------------------------------------


def test_a_balance_at_another_date_is_not_used():
    data = run({"Assets": [entry(1750 * M, "2025-06-30"), instant(1640 * M, 2024)]})
    assert data.fact("total_assets", fy(2025)).kind == "missing"
    assert data.fact("total_assets", fy(2024)).value == 1640 * M


def test_a_balance_filed_with_a_start_date_is_not_used():
    data = run({"Assets": [entry(1750 * M, "2025-12-31", start="2025-01-01")]})
    assert data.fact("total_assets", fy(2025)).kind == "missing"


# --- §5.3.4 restatements --------------------------------------------------------------------------------------------


def test_planted_a_restated_figure_uses_the_latest_filing_and_keeps_the_original():
    # Listed newest first on purpose. 100 filed in 2022, restated to 103 in 2024: 3% > 1% → warning.
    data = run({"NetIncomeLoss": [flow(103 * M, 2021, filed="2024-02-20", accn="acc-new"),
                                  flow(100 * M, 2021, filed="2022-02-20", accn="acc-orig")]})
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


def test_a_company_filing_only_in_another_currency_is_flagged_as_such():
    eur = {"Revenues": revenue_years(), "NetIncomeLoss": [flow(100 * M, 2025)]}
    data = run(eur, units={"Revenues": "EUR", "NetIncomeLoss": "EUR"}, with_revenue=False)
    assert "NON_USD" in codes(data) and "NO_ANNUAL_DATA" not in codes(data)


def test_planted_amounts_are_kept_in_dollars_exactly_as_filed():
    # SPEC §5.4: dollars read as millions. Nothing is scaled; the unit stays "USD".
    fact = run({"Revenues": [flow(47_941_000_000, 2025)]}).fact("revenue", fy(2025))
    assert fact.value == 47_941_000_000 and fact.unit == "USD"


# --- §5.3.6 never add up segments; §5.2 missing is never zero; a real zero stays zero ---------------------------------


def test_a_line_item_without_a_company_wide_figure_is_missing_with_a_reason():
    fact = run().fact("operating_income", fy(2025))
    assert fact.kind == "missing" and fact.value is None
    assert "OperatingIncomeLoss" in fact.note and "2025-12-31" in fact.note


def test_a_reported_zero_is_kept_as_zero():
    data = run({"CostOfRevenue": [flow(0, 2025)]})
    assert data.fact("cost_of_revenue", fy(2025)).value == 0
    assert data.fact("gross_profit", fy(2025)).value == 1040 * M  # 1,040 − 0


# --- §5.3.7 fallback tags, per fiscal year; differences recorded and flagged -------------------------------------------


def test_fallback_tags_are_tried_for_each_fiscal_year():
    data = run({"Revenues": [flow(1000 * M, 2021), flow(1080 * M, 2022)],
                "RevenueFromContractWithCustomerExcludingAssessedTax": [flow(v * M, y) for y, v in
                                                                         [(2023, 1150), (2024, 1210), (2025, 1300)]]})
    tags = [data.fact("revenue", fy(y)).tag for y in range(2021, 2026)]
    assert tags == ["Revenues"] * 2 + ["RevenueFromContractWithCustomerExcludingAssessedTax"] * 3


def test_two_tags_with_different_values_are_flagged_and_the_first_in_the_list_is_used():
    # The smaller value sits under the first tag: the order decides, not the size.
    # Changed in S3 (rule 14.6, reason written in the S3 pull request): this used revenue tags, which S3 showed to
    # differ legitimately (they are now noted, not warned); depreciation tags should agree, so the rule is tested there.
    data = run({"DepreciationDepletionAndAmortization": [flow(60 * M, 2025)],
                "DepreciationAndAmortization": [flow(65 * M, 2025)]})
    fact = data.fact("depreciation_amortization", fy(2025))
    assert fact.value == 60 * M and fact.tag == "DepreciationDepletionAndAmortization"
    assert "65,000,000" in fact.note
    assert "TAG_CONFLICT" in codes(data)


def test_a_small_difference_between_tags_is_recorded_without_a_warning():
    data = run({"NetIncomeLoss": [flow(13_107 * M, 2025)], "ProfitLoss": [flow(13_137 * M, 2025)]})  # 0.2%
    assert "13,137,000,000" in data.fact("net_income", fy(2025)).note
    assert "TAG_CONFLICT" not in codes(data)


def test_two_tags_with_the_same_value_are_not_flagged():
    data = run({"RevenueFromContractWithCustomerExcludingAssessedTax": [flow(1040 * M, 2025)]})
    assert "TAG_CONFLICT" not in codes(data)


def test_a_company_override_changes_the_tag_order_and_explains_why():
    override = {"tags": ["RevenueFromContractWithCustomerExcludingAssessedTax", "Revenues"],
                "reason": "the 10-K's income statement total is filed under the second tag"}
    data = run({"Revenues": revenue_years()[:-1] + [flow(457 * M, 2025)],
                "RevenueFromContractWithCustomerExcludingAssessedTax": [flow(2199 * M, 2025)]},
               tag_map=with_override("revenue", override))
    fact = data.fact("revenue", fy(2025))
    assert fact.value == 2199 * M and fact.tag == "RevenueFromContractWithCustomerExcludingAssessedTax"
    assert "income statement total" in fact.note and "457,000,000" in fact.note
    assert "TAG_CONFLICT" not in codes(data)  # a known, explained difference is recorded, not raised again


def test_fallback_tags_with_a_different_definition_are_noted_but_not_warned():
    # ProfitLoss includes the non-controlling interests' share of profit: a different figure, not an error (S3).
    data = run({"NetIncomeLoss": [flow(140 * M, 2025)], "ProfitLoss": [flow(150 * M, 2025)]})
    fact = data.fact("net_income", fy(2025))
    assert fact.value == 140 * M and "150,000,000" in fact.note
    assert "TAG_CONFLICT" not in codes(data)


def test_tags_that_should_agree_still_raise_a_conflict():
    # Depreciation: both tags mean the cash flow total; a gap points to an error (the McDonald's case).
    data = run({"DepreciationDepletionAndAmortization": [flow(457 * M, 2025)],
                "DepreciationAndAmortization": [flow(2199 * M, 2025)]})
    assert "TAG_CONFLICT" in codes(data)


def test_interest_net_of_interest_income_is_caught_by_a_much_larger_later_tag():
    # The Linde case (S3 review): InterestExpenseNonoperating holds net interest 255; InterestExpenseDebt gross 575.
    data = run({"InterestExpenseNonoperating": [flow(255 * M, 2025)], "InterestExpenseDebt": [flow(575 * M, 2025)]})
    assert data.fact("interest_expense", fy(2025)).value == 255 * M
    assert any(w.startswith("TAG_CONFLICT: interest_expense") for w in data.warnings)


def test_interest_on_debt_only_below_total_interest_is_not_a_conflict():
    data = run({"InterestExpense": [flow(26 * M, 2025)], "InterestExpenseDebt": [flow(24 * M, 2025)]})
    assert "TAG_CONFLICT" not in codes(data)


def test_interest_and_debt_expense_only_fills_gaps_after_the_debt_interest_tag():
    tags = load_tag_map()["line_items"]["interest_expense"]["tags"]
    assert tags[-1] == "InterestAndDebtExpense"


def test_a_tag_that_changes_between_years_is_noted_as_a_switch():
    # The Chevron case: cash without restricted cash until 2024, with it in 2025.
    data = run({"CashAndCashEquivalentsAtCarryingValue": [instant(100 * M, y) for y in range(2021, 2025)],
                "CashCashEquivalentsRestrictedCashAndRestrictedCashEquivalents": [instant(116 * M, 2025)]})
    assert any(w.startswith("TAG_SWITCH: cash") for w in data.warnings)


def test_equity_is_derived_from_total_equity_minus_minority_interest_when_not_reported():
    # S3: nine large companies report only total equity including non-controlling interests.
    data = run({"StockholdersEquityIncludingPortionAttributableToNoncontrollingInterest": [instant(850 * M, 2025)],
                "MinorityInterest": [instant(30 * M, 2025)]})
    fact = data.fact("equity", fy(2025))
    assert fact.kind == "derived" and fact.value == (850 - 30) * M


def test_equity_from_total_equity_without_any_sign_of_minority_interest_says_so():
    data = run({"StockholdersEquityIncludingPortionAttributableToNoncontrollingInterest": [instant(850 * M, 2025)]})
    fact = data.fact("equity", fy(2025))
    assert fact.value == 850 * M and "non-controlling" in fact.note


def test_equity_stays_missing_when_minority_interest_exists_but_is_not_reported_that_year():
    # The GE Vernova case (S3 review): minority interest reported for 2024 only, so 2025's total includes some.
    data = run({"StockholdersEquityIncludingPortionAttributableToNoncontrollingInterest": [instant(850 * M, 2025)],
                "MinorityInterest": [instant(40 * M, 2024)]})
    assert data.fact("equity", fy(2025)).kind == "missing"


def test_equity_stays_missing_when_profit_shows_a_minority_share():
    # ProfitLoss (all owners) differs from NetIncomeLoss (shareholders): non-controlling interests exist.
    data = run({"StockholdersEquityIncludingPortionAttributableToNoncontrollingInterest": [instant(850 * M, 2025)],
                "NetIncomeLoss": [flow(140 * M, 2025)], "ProfitLoss": [flow(150 * M, 2025)]})
    assert data.fact("equity", fy(2025)).kind == "missing"


def test_cash_including_restricted_cash_is_a_noted_fallback():
    data = run({"CashCashEquivalentsRestrictedCashAndRestrictedCashEquivalents": [instant(125 * M, 2025)]})
    fact = data.fact("cash", fy(2025))
    assert fact.value == 125 * M and fact.tag == "CashCashEquivalentsRestrictedCashAndRestrictedCashEquivalents"


def test_interest_and_debt_expense_is_a_fallback():
    fact = run({"InterestAndDebtExpense": [flow(26 * M, 2025)]}).fact("interest_expense", fy(2025))
    assert fact.value == 26 * M


def test_the_tag_map_has_no_per_share_line_items():
    # SPEC §5.3.8: growth is measured on totals; per-share history breaks at share splits.
    tags = [t for spec in load_tag_map()["line_items"].values() for t in spec["tags"]]
    assert not [t for t in tags if "PerShare" in t]


# --- derived figures (SPEC §6) -----------------------------------------------------------------------------------------


def test_gross_profit_is_derived_when_not_reported():
    data = run({"CostOfRevenue": [flow(600 * M, 2025)]})
    fact = data.fact("gross_profit", fy(2025))
    assert fact.kind == "derived" and fact.value == (1040 - 600) * M
    assert "revenue" in fact.note and "cost_of_revenue" in fact.note
    assert "DERIVED" in codes(data)


def test_a_derived_figure_with_a_missing_input_stays_missing_and_says_why():
    fact = run().fact("gross_profit", fy(2025))  # revenue present, cost of revenue missing
    assert fact.kind == "missing" and fact.value is None
    assert "cost_of_revenue" in fact.note


def test_total_liabilities_without_total_assets_stay_missing():
    fact = run({"StockholdersEquity": [instant(820 * M, 2025)]}).fact("total_liabilities", fy(2025))
    assert fact.kind == "missing" and fact.value is None


def test_total_liabilities_are_derived_from_assets_minus_total_equity():
    data = run({"Assets": [instant(1750 * M, 2025)], "StockholdersEquity": [instant(800 * M, 2025)],
                "MinorityInterest": [instant(20 * M, 2025)]})
    assert data.fact("total_equity", fy(2025)).value == (800 + 20) * M
    assert data.fact("total_liabilities", fy(2025)).value == (1750 - 820) * M
    assert data.fact("total_liabilities", fy(2025)).kind == "derived"


def test_negative_equity_is_subtracted_with_its_sign():
    # The McDonald's case: 1,750 − (−200) = 1,950.
    data = run({"Assets": [instant(1750 * M, 2025)], "StockholdersEquity": [instant(-200 * M, 2025)]})
    assert data.fact("total_liabilities", fy(2025)).value == 1950 * M


def test_without_minority_interest_total_equity_is_equity_with_a_note():
    data = run({"Assets": [instant(1750 * M, 2025)], "StockholdersEquity": [instant(820 * M, 2025)]})
    total_equity = data.fact("total_equity", fy(2025))
    assert total_equity.value == 820 * M and "non-controlling" in total_equity.note


# --- financial debt (SPEC §6; plan Q5) ---------------------------------------------------------------------------------


def debt(us_gaap, **kw):
    data = run(us_gaap, **kw)
    return data.fact("financial_debt", fy(2025)), data.fact("current_financial_debt", fy(2025)), data


def test_the_reported_total_long_term_debt_is_used_with_short_term_borrowings():
    d, c, data = debt({"LongTermDebt": [instant(450 * M, 2025)], "LongTermDebtNoncurrent": [instant(400 * M, 2025)],
                       "LongTermDebtCurrent": [instant(50 * M, 2025)], "ShortTermBorrowings": [instant(30 * M, 2025)]})
    assert d.value == (450 + 30) * M and d.kind == "derived"
    assert c.value == (50 + 30) * M
    assert "0000000000-26-000001" in d.note  # every part names its filing (SPEC §5.1)


def test_without_a_total_the_non_current_and_current_parts_are_added():
    d, c, _ = debt({"LongTermDebtNoncurrent": [instant(400 * M, 2025)], "LongTermDebtCurrent": [instant(50 * M, 2025)],
                    "ShortTermBorrowings": [instant(30 * M, 2025)]})
    assert d.value == (400 + 50 + 30) * M and c.value == (50 + 30) * M


def test_commercial_paper_is_added_when_there_is_no_short_term_borrowings_total():
    d, c, _ = debt({"LongTermDebtNoncurrent": [instant(400 * M, 2025)], "LongTermDebtCurrent": [instant(50 * M, 2025)],
                    "CommercialPaper": [instant(20 * M, 2025)], "OtherShortTermBorrowings": [instant(5 * M, 2025)]})
    assert d.value == (400 + 50 + 20 + 5) * M and c.value == (50 + 20 + 5) * M


def test_commercial_paper_is_not_added_twice_when_short_term_borrowings_include_it():
    d, _, _ = debt({"LongTermDebt": [instant(400 * M, 2025)], "ShortTermBorrowings": [instant(30 * M, 2025)],
                    "CommercialPaper": [instant(20 * M, 2025)]})
    assert d.value == (400 + 30) * M


def test_a_company_without_current_maturities_keeps_its_commercial_paper():
    # Total = non-current only shows there are no current maturities, not that commercial paper is inside.
    d, c, _ = debt({"LongTermDebt": [instant(900 * M, 2025)], "LongTermDebtNoncurrent": [instant(900 * M, 2025)],
                    "CommercialPaper": [instant(300 * M, 2025)]})
    assert d.value == (900 + 300) * M
    assert c.value == 300 * M  # current maturities 900 − 900 = 0, plus commercial paper 300


INSIDE = {"short_term_inside_long_term_debt": True, "reason": "the 10-K classifies them inside long-term debt"}


def test_a_cited_override_says_short_term_items_are_inside_long_term_debt():
    # The McDonald's case (2025): current maturities are tagged, yet classified inside long-term debt.
    d, c, data = debt({"LongTermDebt": [instant(400 * M, 2025)], "LongTermDebtNoncurrent": [instant(400 * M, 2025)],
                       "LongTermDebtCurrent": [instant(7 * M, 2025)], "CommercialPaper": [instant(8 * M, 2025)]},
                      tag_map=with_override("debt", INSIDE))
    assert d.value == 400 * M
    assert c.value == 0  # 400 − 400 on the balance sheet
    assert "classifies them inside" in d.note and "DEBT_CHECK" not in codes(data)


def test_with_the_override_current_debt_on_the_balance_sheet_still_counts():
    # The McDonald's case (2023): total 393 = non-current 371 + current 22.
    d, c, _ = debt({"LongTermDebt": [instant(393 * M, 2025)], "LongTermDebtNoncurrent": [instant(371 * M, 2025)]},
                   tag_map=with_override("debt", INSIDE))
    assert d.value == 393 * M and c.value == 22 * M


def test_the_newer_capital_lease_tags_are_used_as_fallbacks():
    # The Coca-Cola case from 2024 on.
    d, _, _ = debt({"LongTermDebtAndCapitalLeaseObligations": [instant(420 * M, 2025)],
                    "LongTermDebtAndCapitalLeaseObligationsCurrent": [instant(18 * M, 2025)],
                    "CommercialPaper": [instant(15 * M, 2025)]})
    assert d.value == (420 + 18 + 15) * M


def test_a_total_that_disagrees_with_its_parts_is_flagged():
    _, _, data = debt({"LongTermDebt": [instant(450 * M, 2025)], "LongTermDebtNoncurrent": [instant(400 * M, 2025)],
                       "LongTermDebtCurrent": [instant(80 * M, 2025)]})  # 450 against 400 + 80 = 480
    assert "DEBT_CHECK" in codes(data)


def test_a_small_face_value_difference_is_not_flagged():
    # The Amazon case: total 68,836 against 65,648 + 2,748 = 68,396 (0.6%).
    _, _, data = debt({"LongTermDebt": [instant(68_836 * M, 2025)], "LongTermDebtNoncurrent": [instant(65_648 * M, 2025)],
                       "LongTermDebtCurrent": [instant(2_748 * M, 2025)]})
    assert "DEBT_CHECK" not in codes(data)


def test_a_missing_current_portion_is_not_counted_as_zero():
    d, c, data = debt({"LongTermDebtNoncurrent": [instant(400 * M, 2025)]})
    assert d.value == 400 * M and "DEBT_INCOMPLETE" in codes(data)
    assert c.kind == "missing"


def test_short_term_borrowings_alone_are_not_passed_off_as_total_debt():
    d, c, _ = debt({"CommercialPaper": [instant(5 * M, 2025)]})  # long-term debt may sit under another tag
    assert d.kind == "missing" and "long-term" in d.note
    assert c.kind == "missing"


def test_debt_without_any_debt_tag_is_missing():
    d, c, _ = debt({})
    assert d.kind == "missing" and c.kind == "missing"


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
    fact = run(dei=dei).latest("shares")
    assert fact.value == 4_300_000_000 and fact.unit == "shares" and fact.kind == "reported"
    assert fact.period_end == date(2026, 2, 18)


def test_without_a_cover_page_count_the_diluted_average_is_used_with_a_warning():
    tag = "WeightedAverageNumberOfDilutedSharesOutstanding"
    data = run({tag: [flow(100_000_000, 2025)]}, units={tag: "shares"})
    fact = data.latest("shares")
    assert fact.value == 100_000_000 and fact.kind == "derived" and "average" in fact.note
    assert "AVERAGE_SHARES" in codes(data)


# --- planted sign error (SPEC §5.4) ---------------------------------------------------------------------------------------


def test_planted_a_negative_capital_expenditure_is_kept_as_filed_and_flagged():
    data = run({"PaymentsToAcquirePropertyPlantAndEquipment": [flow(-85 * M, 2025)]})
    assert data.fact("capital_expenditure", fy(2025)).value == -85 * M
    assert "SIGN" in codes(data)


def test_a_negative_dividend_payment_is_flagged_too():
    assert "SIGN" in codes(run({"PaymentsOfDividends": [flow(-56 * M, 2025)]}))


def test_a_positive_payment_raises_no_sign_warning():
    data = run({"PaymentsToAcquirePropertyPlantAndEquipment": [flow(85 * M, 2025)],
                "PaymentsOfDividends": [flow(56 * M, 2025)]})
    assert "SIGN" not in codes(data)


def test_a_company_without_company_facts_still_has_its_header():
    # JPMorgan in the demo data: only the submissions file, so the gates can refuse it by its industry code.
    data = resolve("TST", None, SUBMISSIONS, RETRIEVED)
    assert data.sic == "2080" and data.items == {} and "NO_ANNUAL_DATA" in codes(data)
