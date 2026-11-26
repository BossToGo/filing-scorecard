"""The overview above the tabs (slice S10c). Owner: A.

Expected values come from the hand working in docs/acceptance.md, "Overview (S10c)" (rule 14.5), never from running
`src.overview`. The edge rules are Igor's of 25 November (same section).
"""

from dataclasses import replace
from datetime import date

import pytest

from src.contracts import CompanyData, Fact
from src.data.company import load_company
from src.overview import overview
from tests.fixtures import synthetic

FY0, FY1 = date(2025, 12, 31), date(2024, 12, 31)
MILLION = 1_000_000


def changed(data: CompanyData, metric: str, fy_end: date, millions: float | None) -> CompanyData:
    """The same company with one figure changed; None makes it missing (kind "missing", no value)."""
    items = {m: dict(by_year) for m, by_year in data.items.items()}
    old = items[metric][fy_end]
    if millions is None:
        items[metric][fy_end] = replace(old, value=None, kind="missing", tag=None, note="not in the filing")
    else:
        items[metric][fy_end] = replace(old, value=millions * MILLION)
    return replace(data, items=items)


def figures(data: CompanyData) -> dict:
    return {f.label: f for f in overview(data).key_figures}


# --- synthetic company (hand working: docs/acceptance.md, "Overview (S10c)") ------------------------------------


def test_synthetic_key_figures_with_their_change_on_the_year_before():
    got = figures(synthetic.company_data())
    assert list(got) == ["Revenue", "Operating margin", "Net income", "Free cash flow"]
    assert (got["Revenue"].text, got["Revenue"].change) == ("USD 1.30 bn", "+7.4%")
    assert (got["Operating margin"].text, got["Operating margin"].change) == ("16.0%", "+0.3 pp")
    assert (got["Net income"].text, got["Net income"].change) == ("USD 140 m", "+9.4%")
    assert (got["Free cash flow"].text, got["Free cash flow"].change) == ("USD 130 m", "+13.0%")
    assert {f.versus for f in got.values()} == {"vs FY2024"}


def test_each_key_figure_says_whether_it_is_reported_or_derived():
    got = figures(synthetic.company_data())
    assert [got[label].kind for label in got] == ["reported", "derived", "reported", "derived"]


def test_the_big_number_and_its_unit_are_separate_for_the_screen():
    revenue = figures(synthetic.company_data())["Revenue"]
    assert (revenue.before, revenue.number, revenue.after) == ("USD", "1.30", "bn")


def test_synthetic_five_years_of_free_cash_flow():
    series = overview(synthetic.company_data()).series
    assert series.years == (2021, 2022, 2023, 2024, 2025)
    assert series.unit == "USD bn"
    lines = {line.label: line for line in series.lines}
    assert list(lines) == ["Revenue", "Net income", "Free cash flow"]
    assert lines["Free cash flow"].values == pytest.approx((0.100, 0.105, 0.075, 0.115, 0.130))
    assert lines["Free cash flow"].texts == ("USD 100 m", "USD 105 m", "USD 75 m", "USD 115 m", "USD 130 m")
    assert lines["Revenue"].texts[-1] == "USD 1.30 bn"


def test_synthetic_dividend_coverage():
    cover = overview(synthetic.company_data()).coverage
    assert (cover.status, cover.percent) == ("covered", "232.1%")
    assert (cover.free_cash_flow, cover.dividends) == ("USD 130 m", "USD 56 m")
    assert (cover.gap, cover.gap_label) == ("USD 74 m", "Free cash flow above dividends")
    assert cover.share == 1.0  # the free cash flow bar is full when it covers the dividends
    assert cover.bar_width == "100.0"  # the bar's width in percent, prepared here so the screen computes nothing


def test_synthetic_balance_sheet_figures():
    rows = {f.label: f for f in overview(synthetic.company_data()).balance}
    assert list(rows) == ["Cash and equivalents", "Financial debt", "Total assets", "Current ratio"]
    assert (rows["Cash and equivalents"].text, rows["Total assets"].text) == ("USD 120 m", "USD 1.75 bn")
    assert (rows["Current ratio"].text, rows["Current ratio"].kind) == ("1.50×", "derived")


# --- the demo companies (AC16, AC17) -------------------------------------------------------------------------


def test_ac16_coca_cola_overview():
    data = load_company("KO", demo=True)
    got = figures(data)
    assert (got["Revenue"].text, got["Revenue"].change) == ("USD 47.94 bn", "+1.9%")
    assert (got["Operating margin"].text, got["Operating margin"].change) == ("28.7%", "+7.5 pp")
    assert (got["Net income"].text, got["Net income"].change) == ("USD 13.11 bn", "+23.3%")
    assert (got["Free cash flow"].text, got["Free cash flow"].change) == ("USD 5.30 bn", "+11.7%")
    ov = overview(data)
    assert (ov.coverage.status, ov.coverage.percent) == ("not_covered", "60.3%")
    assert (ov.coverage.gap, ov.coverage.gap_label) == ("USD 3.48 bn", "Dividends above free cash flow")
    assert ov.coverage.share == pytest.approx(5296 / 8779)
    assert {f.label: f.text for f in ov.balance}["Current ratio"] == "1.46×"


def test_ac16_coca_cola_filing_details():
    filing = overview(load_company("KO", demo=True)).filing
    assert (filing.form, filing.accession) == ("10-K", "0001628280-26-010047")
    assert filing.filed == "20 February 2026"
    assert filing.retrieved == "18 November 2026, 14:17 UTC"
    assert (filing.metrics, filing.records) == (27, 119)


def test_ac17_amazon_shows_no_dividend_paid_never_zero_percent():
    cover = overview(load_company("AMZN", demo=True)).coverage
    assert cover.status == "no_dividend"
    assert cover.percent is None
    assert cover.text == "No dividend paid"
    # in plain words, not the list of SEC tags the data layer searched (those stay on the Sources tab)
    assert cover.note == "No dividends paid in FY2025. The Sources tab shows how this was read."


# --- edge rules (AC18; Igor, 25 November) --------------------------------------------------------------------


def test_ac18_a_missing_year_gives_no_change_never_zero():
    data = changed(synthetic.company_data(), "net_income", FY1, None)
    net = figures(data)["Net income"]
    assert (net.text, net.change, net.direction) == ("USD 140 m", "n/a", None)
    assert "2024" in net.note


def test_ac18_missing_operating_cash_flow_leaves_free_cash_flow_and_coverage_open():
    data = changed(synthetic.company_data(), "operating_cash_flow", FY0, None)
    ov = overview(data)
    fcf = {f.label: f for f in ov.key_figures}["Free cash flow"]
    assert (fcf.text, fcf.kind) == ("n/a", "missing")
    assert "operating cash flow" in fcf.note
    assert (ov.coverage.status, ov.coverage.percent, ov.coverage.share) == ("missing", None, None)
    line = {line.label: line for line in ov.series.lines}["Free cash flow"]
    assert (line.values[-1], line.texts[-1]) == (None, "n/a")


def test_a_change_from_a_loss_is_not_meaningful():
    data = changed(synthetic.company_data(), "net_income", FY1, -20)
    net = figures(data)["Net income"]
    assert (net.change, net.direction) == ("not meaningful", None)
    assert "loss" in net.note


def test_negative_free_cash_flow_shows_both_amounts_and_no_percentage():
    data = changed(synthetic.company_data(), "operating_cash_flow", FY0, 50)  # 50 − 85 = −35
    ov = overview(data)
    assert {f.label: f.text for f in ov.key_figures}["Free cash flow"] == "USD −35 m"
    cover = ov.coverage
    assert (cover.status, cover.percent, cover.share) == ("negative", None, 0.0)
    assert (cover.free_cash_flow, cover.dividends) == ("USD −35 m", "USD 56 m")
    assert cover.text == "Free cash flow was negative"
    assert (cover.gap, cover.gap_label) == ("USD 91 m", "Dividends above free cash flow")  # 56 − (−35) = 91
    assert cover.bar_width == "0.0"


def test_revenue_at_zero_gives_no_margin():
    data = changed(synthetic.company_data(), "revenue", FY0, 0)
    margin = figures(data)["Operating margin"]
    assert (margin.text, margin.kind, margin.change) == ("n/a", "missing", "n/a")
    assert "revenue" in margin.note


def test_current_liabilities_at_zero_give_no_current_ratio():
    data = changed(synthetic.company_data(), "current_liabilities", FY0, 0)
    ratio = {f.label: f for f in overview(data).balance}["Current ratio"]
    assert (ratio.text, ratio.kind) == ("n/a", "missing")


def test_negative_capital_expenditure_is_a_sign_error_not_a_bigger_cash_flow():
    data = changed(synthetic.company_data(), "capital_expenditure", FY0, -85)
    fcf = figures(data)["Free cash flow"]
    assert (fcf.text, fcf.kind) == ("n/a", "missing")
    assert "capital expenditure" in fcf.note


@pytest.mark.parametrize("millions, text", [(999, "USD 999 m"), (1000, "USD 1.00 bn"), (-1500, "USD −1.50 bn"),
                                            (1234.5, "USD 1.23 bn")])
def test_amounts_switch_to_billions_from_one_billion(millions, text):
    data = changed(synthetic.company_data(), "cash", FY0, millions)
    assert {f.label: f.text for f in overview(data).balance}["Cash and equivalents"] == text


def test_each_line_carries_its_last_value_for_the_end_of_the_chart():
    lines = {line.label: line for line in overview(synthetic.company_data()).series.lines}
    assert (lines["Revenue"].end_label, lines["Free cash flow"].end_label) == ("1.30", "0.13")  # USD bn


def test_a_missing_last_value_has_no_end_label():
    data = changed(synthetic.company_data(), "operating_cash_flow", FY0, None)
    assert {line.label: line for line in overview(data).series.lines}["Free cash flow"].end_label == ""


def test_the_fiscal_year_end_and_the_years_covered_are_written_for_the_header():
    ov = overview(load_company("KO", demo=True))
    assert (ov.fiscal_year_end, ov.years_text) == ("31 December 2025", "FY2021 – FY2025")



# --- edge rules the audit of 26 November found untested; hand working in each comment -----------------------------


def test_a_prior_year_of_exactly_zero_gives_not_meaningful():
    data = changed(synthetic.company_data(), "net_income", FY1, 0)  # a change from 0 cannot be a percentage
    net = figures(data)["Net income"]
    assert (net.change, net.direction) == ("not meaningful", None)


def test_a_figure_with_no_entry_at_all_is_missing_never_zero():
    data = synthetic.company_data()
    items = {m: dict(by_year) for m, by_year in data.items.items()}
    del items["cash"][FY0]  # no entry at all, not an entry marked missing
    rows = {f.label: f for f in overview(replace(data, items=items)).balance}
    assert (rows["Cash and equivalents"].text, rows["Cash and equivalents"].kind) == ("n/a", "missing")


def test_free_cash_flow_of_exactly_zero_covers_none_of_the_dividends():
    data = changed(synthetic.company_data(), "operating_cash_flow", FY0, 85)  # 85 − 85 = 0
    cover = overview(data).coverage
    assert (cover.status, cover.percent, cover.share, cover.bar_width) == ("not_covered", "0.0%", 0.0, "0.0")
    assert (cover.gap, cover.gap_label) == ("USD 56 m", "Dividends above free cash flow")


def test_free_cash_flow_equal_to_the_dividends_covers_them_exactly():
    data = changed(synthetic.company_data(), "operating_cash_flow", FY0, 141)  # 141 − 85 = 56, the dividends
    cover = overview(data).coverage
    assert (cover.status, cover.percent, cover.share) == ("covered", "100.0%", 1.0)
    assert (cover.gap, cover.gap_label) == ("USD 0 m", "Free cash flow equals the dividends")


def test_coverage_above_1000_percent_is_written_with_a_thousands_separator():
    data = changed(synthetic.company_data(), "dividends_paid", FY0, 10)  # 130 ÷ 10 = 13 → 1,300.0%
    assert overview(data).coverage.percent == "1,300.0%"  # Nvidia read "9925.7%" (audit of 26 November)


def test_negative_dividends_are_a_sign_error_never_no_dividend_paid():
    # a payment is filed as a positive amount; a negative one is a sign error, as D1 says (code review, 26 November)
    data = changed(synthetic.company_data(), "dividends_paid", FY0, -56)
    cover = overview(data).coverage
    assert (cover.status, cover.text, cover.percent) == ("missing", "Dividend coverage is not available", None)
    assert "negative" in cover.note
