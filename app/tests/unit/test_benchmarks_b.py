"""S4: source-based known answers, not the app's output or locked Appendix A.

Damodaran January 2026, Industry Averages: betas.xls F20; margin.xls F30;
divfund.xls F103. indname.xls, By company name, C2034/C2722/C26031/C29696/C42201.
Flo's second-member source reread is recorded in PR #27 (23 November 2026).
"""

import csv
from pathlib import Path

import pytest

from src.benchmarks.loader import BenchmarkDataError, load_benchmarks


DATA = Path(__file__).resolve().parents[2] / "data" / "benchmarks_us_2026.csv"


@pytest.mark.parametrize("ticker,industry,firms", [
    ("KO", "Beverage (Soft)", 27),
    ("AAPL", "Computers/Peripherals", 36),
    ("MCD", "Restaurant/Dining", 64),
    ("NVDA", "Semiconductor", 66),
    ("AMZN", "Retail (General)", 23),
])
def test_demo_industries_match_the_original_lookup(ticker, industry, firms):
    result = load_benchmarks(ticker)
    assert result.industry == industry
    assert result.route == "Damodaran lookup"
    assert result.num_firms == firms
    assert "indname.xls" in result.lookup_source
    assert "By company name" in result.lookup_source


def test_three_original_source_cells_keep_their_values_and_provenance():
    beta = load_benchmarks("KO").fact("unlevered_beta")
    margin = load_benchmarks("AAPL").fact("operating_margin")
    dividend = load_benchmarks("KO").market_fact("dividend_yield")
    for fact, value, filename, row in [
        (beta, 0.5556711918551647, "betas.xls", 20),
        (margin, 0.22484874696685003, "margin.xls", 30),
        (dividend, 0.011040267773068387, "divfund.xls", 103),
    ]:
        assert fact.value == pytest.approx(value)
        assert fact.unit == "pure"
        assert fact.kind == "reported"
        assert fact.form == filename
        assert fact.period_end.isoformat() == "2026-01-05"
        assert "Industry Averages" in fact.note
        assert f"row {row}" in fact.note
        assert "https://pages.stern.nyu.edu/" in fact.note
        assert fact.retrieved is not None and fact.retrieved.tzinfo is not None


def test_v4_market_pe_excludes_financials_but_d2_yield_uses_the_whole_market():
    # SPEC §7 V4 explicitly selects the non-financial market row, Current PE.
    # Original pedata.xls, Industry Averages, D104; independently read from that workbook.
    market_pe = load_benchmarks("KO").market_fact("pe")
    assert market_pe.value == pytest.approx(60.258294591721196)
    assert market_pe.tag == "Current PE"
    assert "Total Market (without financials)" in market_pe.note
    assert "row 104" in market_pe.note
    dividend = load_benchmarks("KO").market_fact("dividend_yield")
    assert "Total Market, " in dividend.note
    assert "row 103" in dividend.note


def test_settings_record_the_selected_columns_and_market_source_rows():
    from src.settings import load_settings
    choices = load_settings()["benchmarks"]
    b = load_benchmarks("KO")
    for metric in ("roe", "operating_margin", "pe", "pb", "unlevered_beta", "dividend_yield"):
        assert choices[f"{metric}_column"] == b.fact(metric).tag
    for metric in ("pe", "dividend_yield"):
        fact = b.market_fact(metric)
        assert choices[f"market_{metric}_group"] in fact.note
        assert f"row {choices[f'market_{metric}_source_row']}" in fact.note


def test_company_symbol_normalization_and_unknown_industry_keep_market_values():
    assert load_benchmarks(" ko ").industry == "Beverage (Soft)"
    unknown = load_benchmarks("NOT_A_DEMO_COMPANY")
    assert unknown.industry is None and unknown.route == "missing"
    assert unknown.fact("roe").kind == "missing"
    assert unknown.fact("roe").value is None
    assert unknown.fact("roe").note
    assert unknown.market_fact("pe").kind == "reported"
    assert unknown.market_fact("dividend_yield").kind == "reported"


def edited_csv(tmp_path, *, field=None, value=None, duplicate=False):
    with DATA.open(newline="", encoding="utf-8") as source:
        reader = csv.DictReader(source)
        fields, rows = reader.fieldnames, list(reader)
    target = next(row for row in rows if row["ticker"] == "KO" and row["metric"] == "roe")
    if field is not None:
        target[field] = value
    if duplicate:
        rows.append(dict(target))
    path = tmp_path / "benchmarks.csv"
    with path.open("w", newline="", encoding="utf-8") as dest:
        writer = csv.DictWriter(dest, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)
    return path


def test_blank_benchmark_is_missing_and_a_real_zero_is_preserved(tmp_path):
    path = edited_csv(tmp_path, field="value", value="")
    missing = load_benchmarks("KO", path=path).fact("roe")
    assert missing.kind == "missing" and missing.value is None
    assert "blank" in missing.note.lower()
    path = edited_csv(tmp_path, field="value", value="0")
    zero = load_benchmarks("KO", path=path).fact("roe")
    assert zero.kind == "reported" and zero.value == 0


def test_blank_source_cell_preserves_its_structured_provenance(tmp_path):
    # A known blank source cell is different from having no source file at all.
    original = load_benchmarks("KO").fact("roe")
    blank = load_benchmarks("KO", path=edited_csv(tmp_path, field="value", value="")).fact("roe")
    assert blank.kind == "missing" and blank.value is None
    assert blank.tag == original.tag
    assert blank.form == original.form
    assert blank.accession == original.accession
    assert blank.retrieved == original.retrieved
    assert blank.period_end == original.period_end


@pytest.mark.parametrize("field,value", [
    ("value", "nan"), ("value", "inf"), ("value", "not a number"),
    ("unit", "percent"), ("as_of", "2025-01-05"),
    ("source_row", "0"), ("num_firms", "2.5"),
    ("source_column", ""), ("source_sha256", ""),
    ("lookup_row", ""), ("lookup_country", "Canada"),
    ("lookup_exchange_ticker", "NYSE:WRONG"),
    ("source_file", "unverified.xls"),
    ("source_column", "ROE (adjusted for R&D)"),
])
def test_invalid_data_is_rejected_with_an_actionable_error(tmp_path, field, value):
    path = edited_csv(tmp_path, field=field, value=value)
    with pytest.raises(BenchmarkDataError, match="benchmark"):
        load_benchmarks("KO", path=path)


def test_duplicate_benchmark_rows_are_rejected(tmp_path):
    with pytest.raises(BenchmarkDataError, match="duplicate"):
        load_benchmarks("KO", path=edited_csv(tmp_path, duplicate=True))


def test_absent_csv_makes_both_industry_and_market_missing(tmp_path):
    result = load_benchmarks("KO", path=tmp_path / "absent.csv")
    assert result.fact("roe").kind == "missing"
    assert result.market_fact("pe").kind == "missing"
    assert result.warnings


def test_malformed_header_is_rejected(tmp_path):
    path = tmp_path / "wrong.csv"
    path.write_text("industry,value\nUnknown,0\n", encoding="utf-8")
    with pytest.raises(BenchmarkDataError, match="columns"):
        load_benchmarks("KO", path=path)


def test_corrupt_text_is_reported_as_a_benchmark_error(tmp_path):
    path = tmp_path / "corrupt.csv"
    path.write_bytes(b"\xff\xfe\x80")
    with pytest.raises(BenchmarkDataError, match="benchmark"):
        load_benchmarks("KO", path=path)


def test_every_demo_has_all_six_metrics_and_no_analyst_forecast_column():
    for ticker in ("KO", "AAPL", "NVDA", "MCD", "AMZN"):
        result = load_benchmarks(ticker)
        for metric in ("unlevered_beta", "roe", "operating_margin", "pe", "pb", "dividend_yield"):
            assert result.fact(metric).kind == "reported"
            assert result.market_fact(metric).kind == "reported"
    with DATA.open(newline="", encoding="utf-8") as source:
        columns = {row["source_column"].lower() for row in csv.DictReader(source)}
    assert not any("forward" in column or "expected" in column or "peg" in column for column in columns)


# --- Igor's review of #27 (24 November 2026) ----------------------------------------------------------------------

def test_ratios_are_decimals_not_percent_numbers():
    # A margin typed as 22.48 instead of 0.2248 would show as 2,248%. Ratios must lie between -1 and 1.
    with DATA.open(encoding="utf-8", newline="") as f:
        rows = [r for r in csv.DictReader(f) if r["metric"] in ("roe", "operating_margin", "dividend_yield")]
    assert len(rows) == 3 * 5 + 3  # five industries and the market row, for each of the three ratios
    for row in rows:
        assert -1 <= float(row["value"]) <= 1, row


def test_a_missing_industry_figure_is_explained_in_plain_words():
    # The note reaches customers through the valuation engine ("industry beta: ...").
    note = load_benchmarks("MSFT").fact("unlevered_beta").note
    assert note == "No industry figure: industry benchmarks cover only the five demo companies."


# --- Flo's S18 read-only review (#64), points 3 and 7: the values themselves -----------------------------------------
# Expected values come from Damodaran's own web tables of the same January 2026 edition ("Updated in January 2026"),
# https://pages.stern.nyu.edu/~adamodar/New_Home_Page/datafile/<page>, accessed 26 November 2026, as shown there
# (percent with two decimals, multiples and betas with two decimals). The six dividend yields are not on those pages
# (divfund.html shows cash returned, not the yield), so they stay checked against divfund.xls only.
WEB_TABLES = [
    ('AAPL', 'unlevered_beta', '1.31', 36),  # Computers/Peripherals, Betas.html
    ('AAPL', 'roe', '-0.17%', 36),  # Computers/Peripherals, roe.html
    ('AAPL', 'operating_margin', '22.48%', 36),  # Computers/Peripherals, margin.html
    ('AAPL', 'pe', '80.95', 36),  # Computers/Peripherals, pedata.html
    ('AAPL', 'pb', '34.08', 36),  # Computers/Peripherals, pbvdata.html
    ('AMZN', 'unlevered_beta', '0.76', 23),  # Retail (General), Betas.html
    ('AMZN', 'roe', '26.05%', 23),  # Retail (General), roe.html
    ('AMZN', 'operating_margin', '6.80%', 23),  # Retail (General), margin.html
    ('AMZN', 'pe', '46.68', 23),  # Retail (General), pedata.html
    ('AMZN', 'pb', '7.19', 23),  # Retail (General), pbvdata.html
    ('KO', 'unlevered_beta', '0.56', 27),  # Beverage (Soft), Betas.html
    ('KO', 'roe', '30.92%', 27),  # Beverage (Soft), roe.html
    ('KO', 'operating_margin', '20.53%', 27),  # Beverage (Soft), margin.html
    ('KO', 'pe', '37.11', 27),  # Beverage (Soft), pedata.html
    ('KO', 'pb', '6.87', 27),  # Beverage (Soft), pbvdata.html
    ('MCD', 'unlevered_beta', '0.77', 64),  # Restaurant/Dining, Betas.html
    ('MCD', 'roe', '0.10%', 64),  # Restaurant/Dining, roe.html
    ('MCD', 'operating_margin', '15.79%', 64),  # Restaurant/Dining, margin.html
    ('MCD', 'pe', '67.67', 64),  # Restaurant/Dining, pedata.html
    ('MCD', 'pb', '74.74', 64),  # Restaurant/Dining, pbvdata.html
    ('NVDA', 'unlevered_beta', '1.49', 66),  # Semiconductor, Betas.html
    ('NVDA', 'roe', '31.36%', 66),  # Semiconductor, roe.html
    ('NVDA', 'operating_margin', '35.33%', 66),  # Semiconductor, margin.html
    ('NVDA', 'pe', '70.13', 66),  # Semiconductor, pedata.html
    ('NVDA', 'pb', '13.31', 66),  # Semiconductor, pbvdata.html
    (None, 'unlevered_beta', '0.72', 5994),  # Total Market, Betas.html
    (None, 'roe', '17.21%', 5994),  # Total Market, roe.html
    (None, 'operating_margin', '12.82%', 5994),  # Total Market, margin.html
    (None, 'pe', '60.26', 4822),  # Total Market (without financials), pedata.html
    (None, 'pb', '4.61', 5994),  # Total Market, pbvdata.html
]


def _shown(cell: str) -> tuple[float, int]:
    return (float(cell[:-1]) / 100, 4) if cell.endswith("%") else (float(cell), 2)


@pytest.mark.parametrize("ticker,metric,cell,firms", WEB_TABLES)
def test_benchmark_value_matches_damodarans_published_table(ticker, metric, cell, firms):
    data = load_benchmarks(ticker or "KO")
    fact = data.fact(metric) if ticker else data.market_fact(metric)
    expected, decimals = _shown(cell)
    assert round(fact.value, decimals) == round(expected, decimals), (ticker, metric, fact.value, cell)
    if ticker:
        assert data.num_firms == firms
