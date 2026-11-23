"""S4: source-based known answers, not the app's output or locked Appendix A.

Damodaran January 2026, Industry Averages: betas.xls F20; margin.xls F30;
divfund.xls F103. indname.xls, By company name, C2034/C2722/C26031/C29696/C42201.
A second teammate's visual re-reading is still required before S4 is accepted.
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
