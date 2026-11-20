"""Trimming SEC files for the saved demo data (slice S0b). Owner: A.

Expected behaviour from SPEC §5.3.1 (only Form 10-K and 10-K/A figures), §4 (every response saved with its
retrieval time) and the security review (never store request headers). Inputs are small hand-made examples in
the shape of the SEC files.
"""

import copy
from datetime import datetime, timezone

import pytest

from src.data.evidence import provenance, tickers_subset, trim_companyfacts, trim_submissions


def entry(form, val, end="2025-12-31"):
    return {"start": "2025-01-01", "end": end, "val": val, "accn": f"acc-{form}-{val}", "fy": 2025, "fp": "FY",
            "form": form, "filed": "2026-02-20"}


COMPANYFACTS = {
    "cik": 21344,
    "entityName": "COCA COLA CO",
    "facts": {
        "dei": {
            "EntityCommonStockSharesOutstanding": {
                "label": "Entity Common Stock, Shares Outstanding",
                "units": {"shares": [entry("10-K", 4300), entry("10-Q", 4310)]},
            }
        },
        "us-gaap": {
            "Revenues": {
                "label": "Revenues",
                "description": "Amount of revenue.",
                "units": {"USD": [entry("10-K", 47941), entry("10-Q", 12000), entry("10-K/A", 47950), entry("8-K", 1)]},
            },
            "OnlyQuarterly": {"label": "Only in 10-Q", "units": {"USD": [entry("10-Q", 5)]}},
            "MixedUnits": {"label": "Two units", "units": {"USD": [entry("10-Q", 7)], "pure": [entry("10-K", 0.2)]}},
        },
    },
}


def test_only_annual_report_entries_are_kept():
    revenue = trim_companyfacts(COMPANYFACTS)["facts"]["us-gaap"]["Revenues"]["units"]["USD"]
    assert [e["form"] for e in revenue] == ["10-K", "10-K/A"]
    assert [e["val"] for e in revenue] == [47941, 47950]


def test_concepts_and_units_left_empty_are_dropped():
    us_gaap = trim_companyfacts(COMPANYFACTS)["facts"]["us-gaap"]
    assert "OnlyQuarterly" not in us_gaap
    assert list(us_gaap["MixedUnits"]["units"]) == ["pure"]


def test_the_sec_structure_labels_and_entry_fields_are_kept():
    trimmed = trim_companyfacts(COMPANYFACTS)
    assert trimmed["cik"] == 21344 and trimmed["entityName"] == "COCA COLA CO"
    revenue = trimmed["facts"]["us-gaap"]["Revenues"]
    assert revenue["label"] == "Revenues" and revenue["description"] == "Amount of revenue."
    assert revenue["units"]["USD"][0] == entry("10-K", 47941)


def test_cover_page_facts_keep_every_form():
    # dei:EntityCommonStockSharesOutstanding comes from "the latest filing" (SPEC §6); which one is S2's decision.
    shares = trim_companyfacts(COMPANYFACTS)["facts"]["dei"]["EntityCommonStockSharesOutstanding"]["units"]["shares"]
    assert [e["form"] for e in shares] == ["10-K", "10-Q"]


def test_trimming_does_not_change_the_downloaded_data():
    original = copy.deepcopy(COMPANYFACTS)
    trim_companyfacts(COMPANYFACTS)
    assert COMPANYFACTS == original


SUBMISSIONS = {
    "cik": "0000021344",
    "name": "COCA COLA CO",
    "sic": "2080",
    "sicDescription": "Beverages",
    "fiscalYearEnd": "1231",
    "tickers": ["KO"],
    "filings": {
        "recent": {
            "accessionNumber": ["a1", "a2", "a3", "a4"],
            "form": ["10-Q", "10-K", "8-K", "10-K/A"],
            "filingDate": ["2026-04-28", "2026-02-20", "2026-02-10", "2025-03-01"],
            "reportDate": ["2026-03-31", "2025-12-31", "", "2024-12-31"],
            "primaryDocument": ["q.htm", "k.htm", "e.htm", "ka.htm"],
        },
        "files": [{"name": "CIK0000021344-submissions-001.json"}],
    },
}


def test_submissions_keep_only_annual_reports_with_columns_aligned():
    recent = trim_submissions(SUBMISSIONS)["filings"]["recent"]
    assert recent["form"] == ["10-K", "10-K/A"]
    assert recent["accessionNumber"] == ["a2", "a4"]
    assert recent["filingDate"] == ["2026-02-20", "2025-03-01"]
    assert recent["primaryDocument"] == ["k.htm", "ka.htm"]


def test_submissions_keep_the_header_and_drop_the_older_pages():
    trimmed = trim_submissions(SUBMISSIONS)
    assert (trimmed["name"], trimmed["sic"], trimmed["fiscalYearEnd"]) == ("COCA COLA CO", "2080", "1231")
    assert "files" not in trimmed["filings"]
    assert SUBMISSIONS["filings"]["recent"]["form"] == ["10-Q", "10-K", "8-K", "10-K/A"]  # input unchanged


def test_submissions_with_misaligned_columns_are_refused():
    broken = copy.deepcopy(SUBMISSIONS)
    broken["filings"]["recent"]["filingDate"].pop()
    with pytest.raises(ValueError, match="aligned"):
        trim_submissions(broken)


TICKERS = {
    "0": {"cik_str": 320193, "ticker": "AAPL", "title": "Apple Inc."},
    "1": {"cik_str": 21344, "ticker": "KO", "title": "COCA COLA CO"},
    "2": {"cik_str": 1, "ticker": "XYZ", "title": "Other"},
}


def test_the_ticker_list_is_cut_to_the_demo_companies():
    assert tickers_subset(TICKERS, ["KO", "AAPL"]) == {"0": TICKERS["0"], "1": TICKERS["1"]}


def test_an_unknown_ticker_is_reported():
    with pytest.raises(KeyError, match="NOPE"):
        tickers_subset(TICKERS, ["KO", "NOPE"])


def test_provenance_records_source_time_and_checksum_but_never_request_headers():
    record = provenance(
        url="https://data.sec.gov/submissions/CIK0000021344.json",
        retrieved=datetime(2026, 11, 18, 14, 5, tzinfo=timezone.utc),
        raw=b'{"cik": "0000021344"}',
        trimmed="only Form 10-K and 10-K/A filings",
    )
    assert record == {
        "source": "https://data.sec.gov/submissions/CIK0000021344.json",
        "retrieved": "2026-11-18T14:05:00+00:00",
        # Expected size and checksum computed outside Python: printf '%s' '<raw>' | wc -c ; ... | shasum -a 256
        "raw_bytes": 21,
        "raw_sha256": "8edc71091265ff6245e63cf1c6d7755169e5d7fc1e6b29870b94514633b472ce",
        "trimmed": "only Form 10-K and 10-K/A filings",
    }
