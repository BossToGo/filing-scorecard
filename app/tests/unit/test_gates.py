"""Data-quality gates (`app/src/gates.py`, SPEC 2.4.1 §10; slice S11). Owner: D.

Expected results are Simon's (D), 23 November 2026: the stop order (industry code, no 10-K figures, company-wide
non-USD, too few fiscal years), the inclusive bounds 6000-6799, "15 months" as the same day 15 months later (or the
last day of that month), compared with the UTC day the data was read. Edge cases are built from the synthetic
company or from the saved demo data, never downloaded.
"""

import dataclasses
from datetime import date, datetime, timezone

import pytest

from src.data.company import DEMO_TICKERS, load_company
from src.gates import Stop, check_gates
from src.settings import load_settings
from tests.fixtures import synthetic

GATES = load_settings()["gates"]
COMPANY_WIDE_NON_USD = ("NON_USD: the company files its annual figures in EUR, not US dollars, so it is not "
                        "supported (SPEC §5.3.5)")


def company(**changes):
    """The synthetic company (no SEC code, five fiscal years) with some header fields changed."""
    return dataclasses.replace(synthetic.company_data(), **changes)


def gates(data, demo_tickers=DEMO_TICKERS):
    return check_gates(data, GATES, demo_tickers)


def with_years(data, count):
    """Keep only the latest `count` fiscal years of revenue."""
    items = {metric: dict(by_year) for metric, by_year in data.items.items()}
    items["revenue"] = dict(sorted(items["revenue"].items())[-count:])
    return dataclasses.replace(data, items=items)


def read_on(day: date, hour: int = 12) -> datetime:
    return datetime(day.year, day.month, day.day, hour, tzinfo=timezone.utc)


# --- stop ---------------------------------------------------------------------------------------------------------


def test_jpmorgan_is_stopped_by_its_industry_code():
    result = gates(load_company("JPM", demo=True))
    assert result.stop == Stop("industry", sic=6021)


@pytest.mark.parametrize("ticker", DEMO_TICKERS)
def test_the_five_demo_companies_pass_without_a_header_warning(ticker):
    result = gates(load_company(ticker, demo=True))
    assert result.stop is None
    assert result.not_fully_checked is False
    assert result.old_report_filed is None


@pytest.mark.parametrize("sic", ["6000", "6799"])
def test_industry_codes_at_the_bounds_are_stopped(sic):
    assert gates(company(sic=sic)).stop == Stop("industry", sic=int(sic))


@pytest.mark.parametrize("sic", ["5999", "6800", None, "", "n/a"])
def test_industry_codes_outside_the_bounds_empty_or_not_a_number_pass(sic):
    assert gates(company(sic=sic)).stop is None


def test_no_annual_figures_stop_a_company_outside_the_industry_range():
    data = company(sic="2080", items={}, warnings=("NO_ANNUAL_DATA: no annual 10-K figures found",))
    assert gates(data).stop == Stop("no_annual_data")


def test_a_company_filing_in_another_currency_is_stopped():
    assert gates(company(items={}, warnings=(COMPANY_WIDE_NON_USD,))).stop == Stop("non_usd")


def test_one_figure_in_another_currency_does_not_stop_the_report():
    warning = "NON_USD: dividends_paid 2025-12-31 is filed in EUR, not US dollars"
    assert gates(company(warnings=(warning,))).stop is None


def test_the_industry_code_is_checked_first():
    data = company(sic="6021", items={}, warnings=("NO_ANNUAL_DATA: no annual 10-K figures found",))
    assert gates(data).stop == Stop("industry", sic=6021)


def test_two_fiscal_years_are_too_few():
    assert gates(with_years(synthetic.company_data(), 2)).stop == Stop("too_few_years", years=2, minimum=3)


def test_three_fiscal_years_are_enough():
    assert gates(with_years(synthetic.company_data(), 3)).stop is None


# --- header warnings --------------------------------------------------------------------------------------------


def test_a_ticker_that_is_not_a_demo_company_is_not_fully_checked():
    assert gates(company(ticker="MSFT")).not_fully_checked is True
    assert gates(company()).not_fully_checked is True  # the synthetic company SYN too: the rule stays simple


@pytest.mark.parametrize("filed, read, old", [
    (date(2024, 8, 20), date(2025, 11, 20), False),
    (date(2024, 8, 20), date(2025, 11, 21), True),
    (date(2024, 11, 30), date(2026, 2, 28), False),  # 30 February does not exist: last day of February
    (date(2024, 11, 30), date(2026, 3, 1), True),
])
def test_latest_annual_report_is_old_after_fifteen_months(filed, read, old):
    result = gates(company(latest_10k_filed=filed, retrieved=read_on(read)))
    assert result.old_report_filed == (filed if old else None)


def test_the_time_of_day_of_the_reading_does_not_matter():
    data = company(latest_10k_filed=date(2024, 8, 20), retrieved=read_on(date(2025, 11, 20), hour=23))
    assert gates(data).old_report_filed is None


@pytest.mark.parametrize("filed, read", [(None, read_on(date(2026, 11, 18))), (date(2020, 1, 1), None)])
def test_without_both_dates_there_is_no_old_warning(filed, read):
    assert gates(company(latest_10k_filed=filed, retrieved=read)).old_report_filed is None
