"""The charts of the overview (slice S10d, Igor, 26 November 2026). Owner: A.

Each chart answers one question with the usual chart type for it: the share price against the estimate, the price
ratios against the industry and the market, where the revenue goes, the financial position, the balance sheet split,
debt, equity and cash over five years, dividends against free cash flow, the earnings payout and the dividend yield
against the market. `src.overview.charts` prepares every value and text, so the screen only draws them.

Expected values are worked by hand below (docs/acceptance.md, "Overview charts (S10d)"): the synthetic company's
Appendix A line items and the Coca-Cola and McDonald's FY2025 10-K figures (accessions in docs/acceptance.md),
never from running `src.overview`. The valuation and ratio charts take their numbers from the check results, so
their tests build the results by hand (as tests/unit/test_scorecard_summary.py does).
"""

from dataclasses import replace
from datetime import date

import pytest

from src.contracts import CheckResult, Fact
from src.data.company import load_company
from src.overview import _percent, _times, charts
from tests.fixtures import synthetic

FY0 = date(2025, 12, 31)


def by_label(parts) -> dict:
    return {p.label: p for p in parts}


def without(data, metric: str, fy_end: date = FY0):
    """The company with one figure missing (as the data layer marks it), never zero."""
    items = {m: dict(by_year) for m, by_year in data.items.items()}
    fact = items[metric][fy_end]
    items[metric][fy_end] = replace(fact, value=None, kind="missing", tag=None, note="not in the filing")
    return replace(data, items=items)


def changed(data, metric: str, value: float, fy_end: date = FY0):
    items = {m: dict(by_year) for m, by_year in data.items.items()}
    items[metric][fy_end] = replace(items[metric][fy_end], value=value)
    return replace(data, items=items)


def result(check_id: str, status: str, value=None, threshold=None, why: str = "") -> CheckResult:
    return CheckResult(check_id, status, value, threshold, (), why or f"{status} (built by hand)")


def results(**by_id) -> dict:
    """Check results built by hand; every check not given is not assessed."""
    out = {}
    for area, letter in (("past_performance", "P"), ("financial_health", "H"), ("dividend", "D"), ("valuation", "V")):
        out[area] = tuple(by_id.get(f"{letter}{n}", result(f"{letter}{n}", "insufficient_data"))
                          for n in range(1, 7))
    return out


# --- where the revenue goes (revenue → costs → operating income → net income) ------------------------------------
# Synthetic company FY2025 (USD m): revenue 1,300; no gross profit in Appendix A, so one cost step; operating income
# 208; net income 140. Operating costs = 1,300 − 208 = 1,092; interest, tax and other = 208 − 140 = 68; net income
# as a share of revenue = 140 ÷ 1,300 = 0.10769 → 10.8%.


def test_the_synthetic_company_revenue_flows_to_net_income_in_one_cost_step():
    flow = charts(synthetic.company_data()).money_flow
    assert flow.status == "ok"
    assert [(f.source, f.target, f.text) for f in flow.flows] == [
        ("Revenue", "Operating costs", "USD 1.09 bn"),
        ("Revenue", "Operating income", "USD 208 m"),
        ("Operating income", "Interest, tax and other", "USD 68 m"),
        ("Operating income", "Net income", "USD 140 m"),
    ]
    assert [f.value for f in flow.flows] == [1_092e6, 208e6, 68e6, 140e6]
    assert flow.text == ("Of revenue of USD 1.30 bn, USD 1.09 bn went to operating costs, leaving operating income of "
                         "USD 208 m; after interest, tax and other items of USD 68 m, net income was USD 140 m, "
                         "10.8% of revenue.")


# Coca-Cola FY2025 (USD m, 10-K 0001628280-26-010047): revenue 47,941; gross profit 29,544 (cost of revenue
# 47,941 − 29,544 = 18,397, as filed); operating income 13,762, so operating expenses 29,544 − 13,762 = 15,782;
# net income 13,107, so interest, tax and other 13,762 − 13,107 = 655; 13,107 ÷ 47,941 = 0.27340 → 27.3%.


def test_coca_cola_revenue_flows_through_gross_profit():
    flow = charts(load_company("KO", demo=True)).money_flow
    assert [(f.source, f.target, f.text) for f in flow.flows] == [
        ("Revenue", "Cost of revenue", "USD 18.40 bn"),
        ("Revenue", "Gross profit", "USD 29.54 bn"),
        ("Gross profit", "Operating expenses", "USD 15.78 bn"),
        ("Gross profit", "Operating income", "USD 13.76 bn"),
        ("Operating income", "Interest, tax and other", "USD 655 m"),
        ("Operating income", "Net income", "USD 13.11 bn"),
    ]
    assert dict(flow.nodes)["Revenue"] == "USD 47.94 bn"
    assert flow.text.endswith("net income was USD 13.11 bn, 27.3% of revenue.")


def test_net_income_above_operating_income_comes_in_as_other_income():
    # 208 operating income, net income set to 250: other income, net of interest and tax = 250 − 208 = 42
    flow = charts(changed(synthetic.company_data(), "net_income", 250e6)).money_flow
    assert ("Operating income", "Net income", "USD 208 m") in [(f.source, f.target, f.text) for f in flow.flows]
    assert ("Other income, net", "Net income", "USD 42 m") in [(f.source, f.target, f.text) for f in flow.flows]
    assert "Interest, tax and other" not in [f.target for f in flow.flows]
    assert "other income, net of interest and tax, of USD 42 m" in flow.text


def test_a_loss_or_a_missing_figure_gives_no_flow_chart_and_says_why():
    loss = charts(changed(synthetic.company_data(), "net_income", -20e6)).money_flow
    assert (loss.status, loss.flows) == ("none", ())
    assert loss.text == "The flow chart needs a profit: FY2025 had a net loss of USD −20 m."
    gone = charts(without(synthetic.company_data(), "operating_income")).money_flow
    assert gone.status == "none" and "operating income for FY2025: not in the filing" in gone.text


# --- financial position: short-term assets against short- and long-term liabilities -------------------------------
# Synthetic FY2025: current assets 540, current liabilities 360, total liabilities 930 → long-term 930 − 360 = 570.
# Coca-Cola FY2025: 31,044; 21,281; 70,541 − 21,281 = 49,260 (USD m).


def test_financial_position_of_the_synthetic_company():
    position = charts(synthetic.company_data()).position
    assert position.unit == "USD m"
    assert [(b.label, b.value, b.text) for b in position.bars] == [
        ("Short-term assets", 540.0, "USD 540 m"), ("Short-term liabilities", 360.0, "USD 360 m"),
        ("Long-term liabilities", 570.0, "USD 570 m")]
    assert position.text == ("Short-term assets of USD 540 m are above short-term liabilities of USD 360 m and below "
                             "long-term liabilities of USD 570 m.")


def test_financial_position_of_coca_cola_in_billions():
    position = charts(load_company("KO", demo=True)).position
    assert position.unit == "USD bn"
    assert [b.text for b in position.bars] == ["USD 31.04 bn", "USD 21.28 bn", "USD 49.26 bn"]
    assert [b.value for b in position.bars] == pytest.approx([31.044, 21.281, 49.26])


def test_a_missing_liability_figure_is_na_with_its_reason_never_zero():
    position = charts(without(synthetic.company_data(), "total_liabilities")).position
    bars = by_label(position.bars)
    assert bars["Long-term liabilities"].value is None and bars["Long-term liabilities"].text == "n/a"
    assert "total liabilities for FY2025: not in the filing" in bars["Long-term liabilities"].note
    assert bars["Short-term assets"].text == "USD 540 m"


# --- the balance sheet split -------------------------------------------------------------------------------------
# Synthetic FY2025: total assets 1,750; cash 120 → 120 ÷ 1,750 = 6.857% → 6.9%; receivables, inventory and property
# are not in Appendix A, so they stay in other assets: 1,750 − 120 = 1,630 → 93.1%. Financial debt 450 → 25.7%;
# payables not in Appendix A, so other liabilities = 930 − 450 = 480 → 27.4%; equity = 1,750 − 930 = 820 → 46.9%.


def test_the_synthetic_balance_sheet_split():
    split = charts(synthetic.company_data()).split
    assert [(p.label, p.text, p.share) for p in split.assets] == [
        ("Cash and equivalents", "USD 120 m", "6.9%"), ("Other assets", "USD 1.63 bn", "93.1%")]
    assert [(p.label, p.text, p.share) for p in split.claims] == [
        ("Financial debt", "USD 450 m", "25.7%"), ("Other liabilities", "USD 480 m", "27.4%"),
        ("Equity", "USD 820 m", "46.9%")]
    # wording corrected while the slice was being built (the list reads as five items without "and"; Igor, S10d)
    # "not reported separately" was not true for McDonald's, which files receivables under a tag we do not read
    # (independent check of 26 November): the note now says the figure is not in the data
    assert split.note == ("Not in the data as a separate figure, so counted in other assets: receivables, inventory and "
                          "property, plant and equipment. In other liabilities: payables.")
    assert split.text == ("Of total assets of USD 1.75 bn, cash and equivalents are 6.9%; financial debt is 25.7% and "
                          "equity 46.9% of the same total.")


# Coca-Cola FY2025 (USD m): total assets 104,816; cash 10,270 (9.8%); receivables 3,038 (2.9%); inventory 4,425
# (4.2%); property, plant and equipment 9,613 (9.2%); equity-method investments 20,235 (19.3%); other assets
# 104,816 − 47,581 = 57,235 (54.6%). Financial debt 45,492 (43.4%); payables not in the data, so other liabilities
# 70,541 − 45,492 = 25,049 (23.9%); equity including minority interests 104,816 − 70,541 = 34,275 (32.7%).


def test_coca_cola_balance_sheet_split():
    split = charts(load_company("KO", demo=True)).split
    assert [(p.label, p.share) for p in split.assets] == [
        ("Cash and equivalents", "9.8%"), ("Receivables", "2.9%"), ("Inventory", "4.2%"),
        ("Property, plant and equipment", "9.2%"), ("Investments in associates", "19.3%"),
        ("Other assets", "54.6%")]
    assert by_label(split.assets)["Other assets"].text == "USD 57.24 bn"
    # the right-hand column: 45,492 + 25,049 + 34,275 = 104,816, the same total as the assets
    assert (split.claims_title, split.claims_total, split.total) == ("Liabilities and equity", "USD 104.82 bn",
                                                                      "USD 104.82 bn")
    assert [(p.label, p.text, p.share) for p in split.claims] == [
        ("Financial debt", "USD 45.49 bn", "43.4%"), ("Other liabilities", "USD 25.05 bn", "23.9%"),
        ("Equity, including minority interests", "USD 34.28 bn", "32.7%")]


# McDonald's FY2025 (USD m, 10-K of 24 February 2026): total assets 59,515; total liabilities 61,306, so equity is
# 59,515 − 61,306 = −1,791; financial debt 39,973 → 39,973 ÷ 59,515 = 67.2%; cash 774 → 1.3%.


def test_negative_equity_is_said_in_words_and_never_drawn_as_a_part():
    split = charts(load_company("MCD", demo=True)).split
    assert "Equity" not in [p.label for p in split.claims]
    # what is drawn on the right: debt 39,973 + payables 1,149 + other liabilities 61,306 − 39,973 − 1,149 = 20,184,
    # so 61,306 in all (the total liabilities), above the assets of 59,515
    assert (split.claims_title, split.claims_total) == ("Liabilities (equity is negative)", "USD 61.31 bn")
    assert split.text == ("Of total assets of USD 59.52 bn, cash and equivalents are 1.3%; financial debt is 67.2% of "
                          "the same total; liabilities are larger than assets, so equity is negative (USD −1.79 bn).")


def test_parts_larger_than_the_total_leave_no_negative_other_part():
    data = changed(synthetic.company_data(), "cash", 1_800e6)  # cash above total assets of 1,750
    split = charts(data).split
    assert "Other assets" not in [p.label for p in split.assets]
    assert "add up to more than the total of USD 1.75 bn" in split.note


# --- debt, equity and cash over five years ------------------------------------------------------------------------
# Synthetic: debt 450 ÷ equity 820 = 0.54878 → 54.9% (FY2025); 400 ÷ 600 = 0.66667 → 66.7% (FY2021).
# Coca-Cola: 45,492 ÷ 32,169 = 1.41416 → 141.4%; 42,761 ÷ 22,999 = 1.85926 → 185.9% (USD m).


def test_debt_equity_and_cash_over_five_years():
    c = charts(synthetic.company_data())
    assert c.debt_history.years == (2021, 2022, 2023, 2024, 2025) and c.debt_history.unit == "USD m"
    lines = {line.label: line for line in c.debt_history.lines}
    assert list(lines) == ["Financial debt", "Shareholder equity", "Cash and equivalents"]
    assert lines["Financial debt"].values == (400.0, 410.0, 430.0, 440.0, 450.0)
    assert lines["Cash and equivalents"].texts[-1] == "USD 120 m"
    assert c.debt_text == "Financial debt was 54.9% of shareholder equity in FY2025, against 66.7% in FY2021."


def test_coca_cola_debt_to_equity_in_words():
    assert charts(load_company("KO", demo=True)).debt_text == (
        "Financial debt was 141.4% of shareholder equity in FY2025, against 185.9% in FY2021.")


def test_negative_equity_makes_debt_to_equity_not_meaningful():
    assert charts(load_company("MCD", demo=True)).debt_text == (
        "Shareholder equity was negative in FY2025 (USD −1.79 bn), so debt to equity is not meaningful.")


# --- dividends against free cash flow, the earnings payout ---------------------------------------------------------
# Synthetic: free cash flow 100, 105, 75, 115, 130 against dividends 40, 44, 48, 45, 56: covered in all five years.
# Earnings payout 56 ÷ 140 = 0.40 → 40.0%. Coca-Cola: free cash flow 11,258, 9,534, 9,747, 4,741, 5,296 against
# dividends 7,252, 7,616, 7,952, 8,359, 8,779: covered in FY2021 to FY2023, not in FY2024 and FY2025; payout
# 8,779 ÷ 13,107 = 0.66979 → 67.0%.


def test_dividends_against_free_cash_flow_over_five_years():
    c = charts(synthetic.company_data())
    lines = {line.label: line for line in c.dividend_history.lines}
    assert lines["Dividends paid"].values == (40.0, 44.0, 48.0, 45.0, 56.0)
    assert lines["Free cash flow"].values == (100.0, 105.0, 75.0, 115.0, 130.0)
    assert c.dividend_text == "Free cash flow covered the dividends paid in all 5 years."
    assert (c.payout.percent, c.payout.share) == ("40.0%", pytest.approx(0.4))
    assert c.payout.text == "Dividends paid were 40.0% of net income in FY2025."


def test_coca_cola_dividends_and_payout():
    c = charts(load_company("KO", demo=True))
    assert c.dividend_text == "Free cash flow covered the dividends paid in 3 of 5 years; not in FY2024 and FY2025."
    assert c.payout.percent == "67.0%"


def test_a_payout_above_net_income_fills_the_ring_and_says_so():
    payout = charts(changed(synthetic.company_data(), "net_income", 50e6)).payout  # 56 ÷ 50 = 1.12 → 112.0%
    assert (payout.percent, payout.share) == ("112.0%", 1.0)
    assert payout.text == "Dividends paid were 112.0% of net income in FY2025: more than the year's profit."


def test_no_dividend_gives_no_payout_and_no_coverage_count():
    c = charts(load_company("AMZN", demo=True))
    assert (c.payout.status, c.payout.percent, c.payout.text) == ("none", "n/a", "No dividend paid in FY2025.")
    assert c.dividend_text == "No dividend paid in the five years."


def test_a_loss_makes_the_payout_not_meaningful():
    payout = charts(changed(synthetic.company_data(), "net_income", -10e6)).payout
    assert payout.status == "none"
    assert payout.text == "Net income was a loss in FY2025, so a payout ratio is not meaningful."


# --- the share price against the estimate (from V1, V2 and V6) -----------------------------------------------------
# Built by hand: price USD 30.00, estimate 20.13, 80% mark 0.8 × 20.13 = 16.104, estimate at the growth cap 37.37.
# 30 ÷ 20.13 − 1 = 0.49031 → 49.0% above; axis to 37.37 × 1.15 = 42.9755.


def valuation(price: float, estimate: float = 20.13, at_cap: float = 37.37) -> dict:
    status = "pass" if price < estimate else "fail"
    return results(V1=result("V1", status, price, estimate), V2=result("V2", status, price, 0.8 * estimate),
                   V6=result("V6", "pass" if price < at_cap else "fail", price, at_cap))


def test_the_share_price_against_the_estimate_with_its_zones():
    price = charts(synthetic.company_data(), valuation(30.0)).price
    assert price.status == "ok"
    assert [(b.label, b.value, b.text) for b in price.bars] == [("Share price", 30.0, "USD 30.00"),
                                                              ("Estimate", 20.13, "USD 20.13")]
    assert [(label, start, end) for label, start, end in price.zones] == [
        ("80% of the estimate or less", 0.0, pytest.approx(16.104)),
        ("80% to 100% of the estimate", pytest.approx(16.104), 20.13),
        ("Above the estimate", 20.13, pytest.approx(42.9755))]
    assert [(m.label, m.text) for m in price.marks] == [("Estimate at the growth cap", "USD 37.37")]
    assert price.text == "The share price you typed, USD 30.00, is 49.0% above the estimate of USD 20.13."


def test_a_price_below_the_estimate_reads_below():
    # 15 ÷ 20.13 − 1 = −0.25484 → 25.5% below
    text = charts(synthetic.company_data(), valuation(15.0)).price.text
    assert text == "The share price you typed, USD 15.00, is 25.5% below the estimate of USD 20.13."


def test_without_an_estimate_the_chart_gives_the_checks_reason():
    why = "Insufficient data: the valuation checks need the share price; type it in to assess them."
    price = charts(synthetic.company_data(), results(V1=result("V1", "insufficient_data", why=why))).price
    assert (price.status, price.text, price.bars) == ("none", why, ())


# --- the price ratios and the dividend yield against the industry and the market (V3, V4, V5, D2) ----------------


def test_price_ratios_against_the_industry_and_the_market():
    found = results(V3=result("V3", "pass", 15.0, 18.0), V4=result("V4", "pass", 15.0, 20.0),
                    V5=result("V5", "pass", 2.5, 3.0))
    earnings, book = charts(synthetic.company_data(), found).ratios
    assert [(b.label, b.value, b.text) for b in earnings.bars] == [
        ("SYN", 15.0, "15.00×"), ("Industry", 18.0, "18.00×"), ("US market", 20.0, "20.00×")]
    assert earnings.text == "Price to earnings 15.00× against 18.00× for the industry and 20.00× for the US market."
    assert book.text == "Price to book 2.50× against 3.00× for the industry."


def test_dividend_yield_against_the_market_in_percent():
    # 56 ÷ (30.00 × 100) = 0.018667 → 1.87%; market 1.50%
    found = results(D2=result("D2", "pass", 56 / 3000, 0.015))
    dividend_yield = charts(synthetic.company_data(), found).dividend_yield
    assert [(b.label, b.text) for b in dividend_yield.bars] == [("SYN", "1.87%"), ("US market", "1.50%")]
    assert dividend_yield.text == "Dividend yield 1.87% against 1.50% for the US market."


def test_a_ratio_not_assessed_gives_the_checks_reason():
    why = "Insufficient data: the valuation checks need the share price; type it in to assess them."
    earnings, book = charts(synthetic.company_data(), results(V3=result("V3", "insufficient_data", why=why),
                                                              V4=result("V4", "insufficient_data", why=why))).ratios
    assert (earnings.status, earnings.text, earnings.bars) == ("none", why, ())


def test_without_check_results_only_the_charts_from_the_filings():
    c = charts(synthetic.company_data())
    assert c.price is None and c.ratios == () and c.dividend_yield is None
    assert c.money_flow.status == "ok"


def test_a_line_end_label_rounds_a_half_as_the_texts_do():
    # Amazon's equity on 31 December 2025: USD 411,065 m = 411.065 bn, a half, so 411.07 by hand; the line's end
    # label read 411.06 (Python's own format) while the balance sheet said USD 411.07 bn (review of 26 November)
    c = charts(load_company("AMZN", demo=True))
    equity = {line.label: line for line in c.debt_history.lines}["Shareholder equity"]
    assert equity.end_label == "411.07" and equity.texts[-1] == "USD 411.07 bn"


def test_a_worked_out_gross_profit_says_so_under_the_flow():
    # Amazon files no gross profit; the data layer derives it as revenue 716,924 − cost of sales 356,414 = 360,510
    amazon = charts(load_company("AMZN", demo=True)).money_flow
    assert ("Revenue", "Gross profit", "USD 360.51 bn") in [(f.source, f.target, f.text) for f in amazon.flows]
    assert amazon.note.startswith("Gross profit is worked out as revenue − cost of revenue")
    assert charts(load_company("KO", demo=True)).money_flow.note == ""  # Coca-Cola files its gross profit


# --- S18 break-it round (27 November 2026): breaks of the chart code no earlier test caught -------------------------
# Each test failed against its deliberate break (named in the comment) in a throwaway copy of PR #70's head, and
# passes on the unchanged code. Hand working in each comment; synthetic FY2025 figures as in the sections above.

OLD = date(2020, 12, 31)


def test_amounts_per_share_of_a_thousand_or_more_have_a_thousands_comma():
    # CH-fixed-comma. Numbers are written with thousands commas ("1,300.0%", S10c). Price 1,250.00 against an estimate
    # of 1,000.00: 1,250 ÷ 1,000 − 1 = 25.0% above.
    price = charts(synthetic.company_data(), valuation(1250.0, estimate=1000.0, at_cap=1500.0)).price
    assert [b.text for b in price.bars] == ["USD 1,250.00", "USD 1,000.00"]
    assert price.text == "The share price you typed, USD 1,250.00, is 25.0% above the estimate of USD 1,000.00."


def test_negative_percentages_and_ratios_use_the_minus_sign():
    # CH-percent-minus. Every negative is written with "−", not a hyphen (Flo's finding 10, S18 part B).
    assert (_percent(-0.123), _times(-1.5)) == ("−12.3%", "−1.50×")


def test_short_term_assets_equal_to_short_term_liabilities_read_equal_to():
    # CH-versus-equal. Current assets set to 360, the current liabilities: neither above nor below.
    position = charts(changed(synthetic.company_data(), "current_assets", 360e6)).position
    assert position.text == ("Short-term assets of USD 360 m are equal to short-term liabilities of USD 360 m and below "
                             "long-term liabilities of USD 570 m.")


def test_a_chart_reaching_exactly_one_billion_is_drawn_in_billions():
    # CH-scaled. USD 1 bn or more in USD bn (S10c). Total liabilities 1,360 − current 360 = long-term 1,000.
    position = charts(changed(synthetic.company_data(), "total_liabilities", 1_360e6)).position
    assert position.unit == "USD bn"


def test_revenue_of_zero_gives_no_flow_chart():
    # CH-flow-zero-revenue. The flow chart needs revenue above zero.
    flow = charts(changed(synthetic.company_data(), "revenue", 0.0)).money_flow
    assert flow.status == "none" and "needs revenue above zero" in flow.text


def test_an_operating_profit_of_zero_gives_no_flow_chart():
    # CH-flow-zero-profit. The flow chart needs a profit; zero is none.
    flow = charts(changed(synthetic.company_data(), "operating_income", 0.0)).money_flow
    assert flow.status == "none" and "needs a profit" in flow.text


def test_operating_income_above_revenue_gives_no_flow_chart():
    # CH-flow-income-above. Operating income 1,400 above revenue 1,300 cannot flow out of revenue.
    flow = charts(changed(synthetic.company_data(), "operating_income", 1_400e6)).money_flow
    assert flow.status == "none"
    assert flow.text == ("The flow chart is not available: operating income (USD 1.40 bn) is above revenue "
                         "(USD 1.30 bn) in FY2025.")


def test_a_gross_profit_above_revenue_is_not_drawn_as_a_step():
    # CH-flow-gross-range. A gross profit is drawn only between operating income and revenue; 1,400 above revenue
    # 1,300 is not, so the chart keeps one cost step: 1,300 − 208 = 1,092 operating costs.
    data = synthetic.company_data().with_fact(Fact("gross_profit", 1_400e6, "USD", date(2025, 1, 1), FY0, "derived",
                                                   None, None, None, None, None, "revenue − cost_of_revenue"))
    flow = charts(data).money_flow
    assert ("Revenue", "Operating costs", "USD 1.09 bn") in [(f.source, f.target, f.text) for f in flow.flows]
    assert "Gross profit" not in [f.target for f in flow.flows]


def test_net_income_equal_to_operating_income_has_no_other_step():
    # CH-flow-net-equal, CH-flow-zero-flows. Net income set to 208, the operating income: nothing for interest, tax
    # and other (208 − 208 = 0, not drawn) and no other income; 208 ÷ 1,300 = 0.16 → 16.0% of revenue.
    flow = charts(changed(synthetic.company_data(), "net_income", 208e6)).money_flow
    assert [(f.source, f.target) for f in flow.flows] == [("Revenue", "Operating costs"),
                                                          ("Revenue", "Operating income"),
                                                          ("Operating income", "Net income")]
    assert flow.text.endswith("leaving operating income of USD 208 m; net income was USD 208 m, 16.0% of revenue.")


def test_total_liabilities_below_current_liabilities_leave_long_term_open():
    # CH-position-guard. Total liabilities 300 below current liabilities 360: no long-term figure (never −60).
    bars = by_label(charts(changed(synthetic.company_data(), "total_liabilities", 300e6)).position.bars)
    assert bars["Long-term liabilities"].value is None
    assert "below current liabilities" in bars["Long-term liabilities"].note


def test_a_negative_part_is_named_as_not_in_the_data():
    # CH-parts-negative. Cash of −10 (a sign error) is not drawn and is named among the figures counted in other assets.
    split = charts(changed(synthetic.company_data(), "cash", -10e6)).split
    assert "Cash and equivalents" not in [p.label for p in split.assets]
    assert "cash and equivalents" in split.note


def test_total_assets_of_zero_give_no_split():
    # CH-split-zero-assets. Shares of a total of zero cannot be worked out.
    split = charts(changed(synthetic.company_data(), "total_assets", 0.0)).split
    assert split.status == "none" and "at or below zero" in split.text


def test_equity_of_exactly_zero_is_said_and_not_drawn():
    # CH-split-equity-zero. Total liabilities set to the total assets, 1,750: equity 1,750 − 1,750 = 0.
    split = charts(changed(synthetic.company_data(), "total_liabilities", 1_750e6)).split
    assert "Equity" not in [p.label for p in split.claims]
    assert split.claims_title == "Liabilities (equity is zero)"


def test_equity_of_zero_makes_debt_to_equity_not_meaningful():
    # CH-debt-zero-equity. A ratio to zero equity does not exist.
    text = charts(changed(synthetic.company_data(), "equity", 0.0)).debt_text
    assert text == "Shareholder equity was zero in FY2025 (USD 0 m), so debt to equity is not meaningful."


def test_an_earlier_year_with_negative_equity_gives_no_earlier_ratio():
    # CH-debt-then-guard. FY2021 equity −100: no ratio for that year; FY2025 450 ÷ 820 = 0.54878 → 54.9%.
    text = charts(changed(synthetic.company_data(), "equity", -100e6, date(2021, 12, 31))).debt_text
    assert text == "Financial debt was 54.9% of shareholder equity in FY2025."


def test_the_equity_line_is_the_shareholders_equity_without_minority_interests():
    # CH-debt-equity-series. Coca-Cola FY2025 (10-K 0001628280-26-010047): shareholders' equity 32,169, total equity
    # with minority interests 34,275 (USD m). The line is the first, as in the debt-to-equity sentence above it.
    lines = {line.label: line for line in charts(load_company("KO", demo=True)).debt_history.lines}
    assert lines["Shareholder equity"].texts[-1] == "USD 32.17 bn"


def test_no_dividend_in_four_years_and_one_year_missing_is_not_no_dividend():
    # CH-div-all-known. Missing is never zero: with FY2025 missing, "no dividend paid in the five years" is not known.
    data = synthetic.company_data()
    for year in (2021, 2022, 2023, 2024):
        data = changed(data, "dividends_paid", 0.0, date(year, 12, 31))
    data = without(data, "dividends_paid")
    assert charts(data).dividend_text == "Dividends against free cash flow are not available for these years."


def test_free_cash_flow_equal_to_the_dividends_covers_them():
    # CH-div-covered-equal. As the S10c coverage: 141 − 85 = 56, the dividends, covers them.
    data = changed(synthetic.company_data(), "operating_cash_flow", 141e6)
    assert charts(data).dividend_text == "Free cash flow covered the dividends paid in all 5 years."


def test_negative_dividends_give_no_payout():
    # CH-payout-negative. A payment filed as a negative amount is a sign error, never a negative payout.
    payout = charts(changed(synthetic.company_data(), "dividends_paid", -56e6)).payout
    assert payout.status == "none" and "sign error" in payout.text


def test_net_income_of_zero_gives_no_payout():
    # CH-payout-zero-net. A payout ratio of a zero profit is not meaningful.
    payout = charts(changed(synthetic.company_data(), "net_income", 0.0)).payout
    assert payout.status == "none" and "not meaningful" in payout.text


def test_a_payout_of_exactly_100_percent_is_not_more_than_the_profit():
    # CH-payout-more-equal. Net income set to 56, the dividends: 56 ÷ 56 = 100.0%, not more.
    payout = charts(changed(synthetic.company_data(), "net_income", 56e6)).payout
    assert payout.text == "Dividends paid were 100.0% of net income in FY2025."


def test_an_estimate_of_zero_gives_no_price_chart():
    # CH-price-zero-estimate. A price cannot be placed against an estimate of zero.
    found = results(V1=result("V1", "fail", 30.0, 0.0, why="Fail: the estimate is zero (built by hand)"))
    price = charts(synthetic.company_data(), found).price
    assert (price.status, price.text) == ("none", "Fail: the estimate is zero (built by hand)")


def test_with_six_fiscal_years_the_charts_use_the_latest_five():
    # CH-years. The charts cover FY-4 to FY0 (SPEC §7); a sixth, older year (2020, a copy of 2021) is left out.
    data = synthetic.company_data()
    items = {m: {**by_year, OLD: replace(by_year[min(by_year)], period_end=OLD,
                                         period_start=date(2020, 1, 1) if by_year[min(by_year)].period_start else None)}
             for m, by_year in data.items.items()}
    assert charts(replace(data, items=items)).debt_history.years == (2021, 2022, 2023, 2024, 2025)
