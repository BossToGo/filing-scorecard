"""Coverage report logic (slice S3). Owner: A.

Expected behaviour from SPEC §13.4 (go/no-go thresholds; the verified universe: every tier 1 figure resolves and
passes the accounting checks), §10 (stale report, balance check) and §13.2 S3 (about 100 non-financial companies,
at least 8 industries, 30 verified). Companies are built by hand.
"""

from datetime import date, datetime, timezone

import pytest

from src.contracts import CompanyData, Fact
from src.data.coverage import (
    CORE,
    SECONDARY,
    TIER1,
    choose_universe,
    coverage,
    decision,
    depends_on_q1,
    industry,
    longest_year,
    pretax_at,
    problem_type,
    selection_problem,
    verification_problems,
)

YEARS = [date(y, 12, 31) for y in range(2021, 2026)]
TODAY = date(2026, 11, 18)
M = 1_000_000

GOOD = {  # USD millions, the same every year: assets 1,750 = liabilities 930 + equity 820
    "revenue": 1300, "operating_income": 208, "net_income": 140, "interest_expense": 26,
    "depreciation_amortization": 65, "total_assets": 1750, "current_assets": 540, "current_liabilities": 360,
    "total_liabilities": 930, "equity": 820, "total_equity": 820, "cash": 120, "financial_debt": 450,
    "operating_cash_flow": 215, "capital_expenditure": 85, "dividends_paid": 56,
}


def fact(metric, value, year_end, kind="reported"):
    if value is None:
        return Fact(metric, None, "USD", None, year_end, "missing", None, None, None, None, None, "not reported")
    if kind == "derived":
        return Fact(metric, value * M, "USD", None, year_end, "derived", None, None, None, None, None, "formula")
    return Fact(metric, value * M, "USD", None, year_end, "reported", f"Tag{metric}", "10-K", "acc", None, None)


def company(ticker="TST", sic="2080", values=None, missing=(), derived=(), warnings=(), filed=date(2026, 2, 20),
            years=YEARS, drop=()):
    values = {**GOOD, **(values or {})}
    items = {}
    for metric, value in values.items():
        if metric in drop:
            continue
        items[metric] = {y: fact(metric, None if (metric, y) in missing or metric in missing else value, y,
                                 "derived" if metric in derived else "reported") for y in years}
    return CompanyData(ticker, "0000000001", f"{ticker} INC", sic, "Beverages", "1231", filed,
                       datetime(2026, 11, 18, tzinfo=timezone.utc), items, tuple(warnings))


# --- the line items of SPEC §13.4 ------------------------------------------------------------------------------


def test_the_go_no_go_groups_are_those_of_spec_13_4():
    assert CORE == ("revenue", "operating_income", "net_income", "total_assets", "current_assets",
                    "current_liabilities", "equity", "operating_cash_flow", "capital_expenditure")
    assert SECONDARY == ("financial_debt", "interest_expense", "depreciation_amortization")
    assert set(CORE) | set(SECONDARY) <= set(TIER1) | {"depreciation_amortization"}


# --- coverage rates ---------------------------------------------------------------------------------------------


def test_coverage_is_the_share_of_companies_with_the_latest_year_resolved():
    companies = [company("A"), company("B"), company("C", missing=[("interest_expense", YEARS[-1])]),
                 company("D", missing=["interest_expense"])]
    rates = coverage(companies, ["revenue", "interest_expense"])
    assert rates == {"revenue": 1.0, "interest_expense": 0.5}  # 2 of 4


def test_coverage_over_all_five_years_counts_a_gap_in_any_year():
    companies = [company("A"), company("B", missing=[("interest_expense", YEARS[0])])]
    assert coverage(companies, ["interest_expense"], all_years=True) == {"interest_expense": 0.5}
    assert coverage(companies, ["interest_expense"]) == {"interest_expense": 1.0}


def test_the_five_year_column_needs_five_years():
    assert coverage([company(years=YEARS[2:])], ["revenue"], all_years=True, years=5) == {"revenue": 0.0}


def test_a_derived_figure_counts_as_resolved():
    assert coverage([company(derived=["total_liabilities"])], ["total_liabilities"]) == {"total_liabilities": 1.0}


# --- the decision of SPEC §13.4 ---------------------------------------------------------------------------------


@pytest.mark.parametrize(
    "core, secondary, expected",
    [
        (0.90, 0.70, "go as planned"),  # exactly at both thresholds
        (0.95, 0.69, "go with manual fields"),
        (0.89, 0.99, "change scope"),
    ],
)
def test_the_decision_follows_the_thresholds(core, secondary, expected):
    core_rates = {m: 1.0 for m in CORE} | {"capital_expenditure": core}
    secondary_rates = {m: 1.0 for m in SECONDARY} | {"interest_expense": secondary}
    assert decision(core_rates, secondary_rates, core_threshold=0.90, secondary_threshold=0.70) == expected


# --- verification: every tier 1 figure, the accounting checks ---------------------------------------------------


def check(data, **kw):
    return verification_problems(data, today=TODAY, balance_tolerance=0.01, stale_months=15, **kw)


def test_a_complete_consistent_company_is_verified():
    assert check(company()) == []


def test_a_tier1_figure_missing_in_any_year_is_a_problem():
    problems = check(company(missing=[("net_income", YEARS[1])]))
    assert any("net_income" in p for p in problems)


def test_fewer_than_five_fiscal_years_is_a_problem():
    assert any("fiscal years" in p for p in check(company(years=YEARS[2:])))


def test_a_company_that_pays_no_dividend_at_all_is_not_held_back_by_it():
    # Plan Q1: no dividend tag in any year means "no dividend paid", not a broken figure.
    assert check(company(missing=["dividends_paid"])) == []


def test_a_dividend_missing_in_some_years_only_is_a_problem():
    assert any("dividends_paid" in p for p in check(company(missing=[("dividends_paid", YEARS[0])])))


def test_reported_liabilities_that_do_not_balance_are_a_problem():
    # 1,750 against 1,000 + 820 = 1,820: 4% apart.
    problems = check(company(values={"total_liabilities": 1000}))
    assert any("balance" in p for p in problems)


def test_derived_liabilities_are_not_used_for_the_balance_check():
    # Derived as assets − equity, they balance by construction; the check would prove nothing.
    assert check(company(values={"total_liabilities": 1000}, derived=["total_liabilities"])) == []


@pytest.mark.parametrize("values, word", [({"current_assets": 1800}, "current assets"),
                                          ({"cash": 600}, "cash"),
                                          ({"current_liabilities": 1000}, "current liabilities"),
                                          ({"revenue": 0}, "revenue")])
def test_impossible_relations_between_figures_are_problems(values, word):
    assert any(word in p for p in check(company(values=values)))


@pytest.mark.parametrize("code", ["NON_USD", "FY_CHANGE", "DEBT_CHECK", "DEBT_INCOMPLETE", "SIGN"])
def test_a_resolver_warning_that_questions_a_figure_is_a_problem(code):
    assert any(code in p for p in check(company(warnings=[f"{code}: something"])))


def test_a_tag_conflict_outside_the_tier1_figures_is_not_a_problem():
    # Depreciation is used only in tier 2 (valuation); the conflict stays visible as a resolver warning.
    assert check(company(warnings=["TAG_CONFLICT: depreciation_amortization 2025-12-31: a used, b gives c"])) == []


def test_a_tag_conflict_on_a_tier1_figure_is_a_problem():
    assert check(company(warnings=["TAG_CONFLICT: net_income 2025-12-31: a used, b gives c"]))


def test_an_average_share_count_does_not_hold_back_tier1():
    # Shares are used from tier 2 on (D2, valuation); the gates warn about the average.
    assert check(company(warnings=["AVERAGE_SHARES: the share count is the diluted average"])) == []


def test_a_restatement_alone_is_not_a_problem():
    assert check(company(warnings=["RESTATED: revenue 2021-12-31: first filed 1, now 2"])) == []


def test_an_annual_report_older_than_15_months_is_a_problem():
    assert any("older than 15 months" in p for p in check(company(filed=date(2025, 8, 1))))


def test_a_company_verified_only_by_the_no_dividend_rule_is_marked():
    # Plan Q1 is still open: the report must show which companies depend on it.
    assert depends_on_q1(company(missing=["dividends_paid"])) is True
    assert depends_on_q1(company()) is False


@pytest.mark.parametrize("problem, kind", [
    ("revenue missing for 2025-12-31", "revenue missing"),
    ("revenue 2025-12-31 is not positive", "revenue not positive"),
    ("resolver warning TAG_CONFLICT: net_income 2025-12-31: x", "resolver warning TAG_CONFLICT"),
    ("only 3 fiscal years, 5 needed", "fewer than five fiscal years"),
    ("latest annual report older than 15 months", "latest annual report older than 15 months"),
    ("balance sheet does not balance in 2025-12-31: assets 1", "balance sheet does not balance"),
])
def test_problems_are_grouped_by_kind(problem, kind):
    assert problem_type(problem) == kind
    assert problem_type(problem_type(problem)) == kind  # grouping twice changes nothing


@pytest.mark.parametrize("submissions, reason", [
    ({"sic": "6021", "filings": {"recent": {"form": ["10-K"]}}}, "financial"),
    ({"sic": "2834", "filings": {"recent": {"form": ["20-F", "6-K"]}}}, "20-F"),
    ({"sic": "2911", "filings": {"recent": {"form": ["8-K"]}}}, "no Form 10-K"),
    ({"sic": "2080", "filings": {"recent": {"form": ["10-Q", "10-K"]}}}, None),
])
def test_candidates_are_classified_by_the_selection_rule(submissions, reason):
    found = selection_problem(submissions)
    assert (found is None) if reason is None else (reason in found)


def test_pre_tax_income_is_found_only_for_an_annual_10k_period():
    tag = "IncomeLossFromContinuingOperationsBeforeIncomeTaxesExtraordinaryItemsNoncontrollingInterest"
    facts = {"facts": {"us-gaap": {tag: {"units": {"USD": [
        {"start": "2025-01-01", "end": "2025-12-31", "val": 1, "form": "10-K"},
        {"start": "2024-04-01", "end": "2024-12-31", "val": 1, "form": "10-K"}]}}}}}
    assert pretax_at(facts, date(2025, 12, 31)) is True
    assert pretax_at(facts, date(2024, 12, 31)) is False  # nine months only


def test_the_longest_year_tells_a_53_week_year():
    def year(start, end):
        return Fact("revenue", 1.0, "USD", date.fromisoformat(start), date.fromisoformat(end), "reported", "Revenues",
                    "10-K", "a", None, None)
    data = CompanyData("T", "0000000001", "T", "2080", None, None, None, None, {"revenue": {
        date(2023, 9, 30): year("2022-09-25", "2023-09-30"), date(2024, 9, 28): year("2023-10-01", "2024-09-28")}})
    assert longest_year(data) == 370  # 2022-09-25 → 2023-09-30


# --- industries and the choice of 30 ----------------------------------------------------------------------------


def test_the_industry_is_the_two_digit_sec_major_group():
    assert industry(company(sic="2080")) == "20"
    assert industry(company(sic="3571")) == "35"
    assert industry(company(sic=None)) == "unknown"


def test_the_universe_takes_verified_companies_in_list_order():
    candidates = [company(f"C{i}", sic=f"{20 + i % 10}00") for i in range(40)]
    chosen = choose_universe(candidates, size=30, min_industries=8)
    assert [c.ticker for c in chosen] == [f"C{i}" for i in range(30)]


def test_the_universe_swaps_in_new_industries_when_too_few_are_covered():
    # 30 companies of one industry first, then one company each of 7 other industries.
    candidates = [company(f"S{i}", sic="3500") for i in range(30)] + \
                 [company(f"N{i}", sic=f"{20 + i}00") for i in range(7)]
    chosen = choose_universe(candidates, size=30, min_industries=8)
    assert len(chosen) == 30
    assert len({industry(c) for c in chosen}) == 8
    assert {c.ticker for c in chosen} >= {f"N{i}" for i in range(7)}
    assert [c.ticker for c in chosen[:23]] == [f"S{i}" for i in range(23)]  # the largest same-industry ones stay


def test_with_too_few_candidates_the_universe_is_smaller_and_says_so():
    chosen = choose_universe([company("A"), company("B")], size=30, min_industries=8)
    assert [c.ticker for c in chosen] == ["A", "B"]
