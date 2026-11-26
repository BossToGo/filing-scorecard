"""The saved demo data (slice S0b) loads with the network off and is what it claims to be. Owner: A.

Runs with the network blocked like every test (tests/network_guard.py). Known answer from a cited source:
Coca-Cola's FY2025 revenue as shown in session 5, slide 30 (USD 47,941,000,000, accession 0001628280-26-010047,
filed 2026-02-20). The company traits are the reasons each company was chosen (SPEC §13.2).
"""

import json
import re
from datetime import date
from pathlib import Path

import pytest

DEMO_DIR = Path(__file__).resolve().parents[2] / "evidence" / "demo"
DEMO = ["KO", "AAPL", "NVDA", "MCD", "AMZN"]
REFUSED = ["JPM"]
ANNUAL = {"10-K", "10-K/A"}
QUARTERLY = {"10-Q", "10-Q/A"}  # kept since slice S2c (issue #71, item 1)


def load(*parts):
    return json.loads(DEMO_DIR.joinpath(*parts).read_text(encoding="utf-8"))


def annual_entries(facts, tag, unit="USD"):
    return [e for e in facts["facts"]["us-gaap"].get(tag, {}).get("units", {}).get(unit, []) if e["form"] in ANNUAL]


TICKERS = {entry["ticker"]: entry for entry in load("tickers.json").values()}


def test_the_ticker_list_holds_exactly_the_demo_companies_and_jpmorgan():
    assert set(TICKERS) == set(DEMO + REFUSED)


@pytest.mark.parametrize("ticker", DEMO + REFUSED)
def test_every_file_belongs_to_the_same_company(ticker):
    cik = f"{TICKERS[ticker]['cik_str']:010d}"
    assert load(ticker, "provenance.json")["cik"] == cik
    assert load(ticker, "submissions.json")["cik"] == cik
    if ticker in DEMO:
        assert f"{load(ticker, 'companyfacts.json')['cik']:010d}" == cik


@pytest.mark.parametrize("ticker", DEMO)
def test_company_facts_hold_only_annual_and_quarterly_report_figures(ticker):
    # Changed in slice S2c with Igor's agreement (26 November 2026; rule 14.6). Reason: issue #71, item 1 — the
    # twelve months to the latest quarter need the 10-Q figures, so the demo files keep Form 10-Q and 10-Q/A too.
    # The test used to assert `forms <= ANNUAL`; other forms (8-K, S-1, ...) are still left out.
    facts = load(ticker, "companyfacts.json")
    forms = {e["form"] for concept in facts["facts"]["us-gaap"].values() for entries in concept["units"].values()
             for e in entries}
    assert forms <= ANNUAL | QUARTERLY


@pytest.mark.parametrize("ticker", DEMO)
def test_company_facts_hold_the_quarterly_reports_since_the_latest_annual_report(ticker):
    # Every demo company filed at least one 10-Q in 2026 (Apple's latest report is its 10-K of 3 November 2026).
    facts = load(ticker, "companyfacts.json")
    quarterly_filed = {e["filed"] for concept in facts["facts"]["us-gaap"].values()
                       for entries in concept["units"].values() for e in entries if e["form"] in QUARTERLY}
    assert any(day.startswith("2026-") for day in quarterly_filed)


# The SHA-256 of the raw company facts downloaded on 18 November 2026 (the slice S0b records). Re-trimming for
# slice S2c had to start from these very files: the checksums must not change.
RAW_SHA256 = {
    "KO": "87a4173fcd3d662d18d19e0e885095aa5e3812b74c54d1ee55808ff1540a8081",
    "AAPL": "f085735b4d08fb116ade18d24247ffabe11df8eb52eae6556b165831f15ef1ad",
    "AMZN": "acddb7c0a6973a1fd08372de3b292298a34eae7f42a7eedc4bdebd3ac659c8fd",
    "MCD": "426688e51562a0bf08a4ede782fbaa7ff97eed5c18477bcffab165b3d5743359",
    "NVDA": "19ef503a5770f5660964b3c3aea6937579d9b359da344afe6a9adf59c63d26ff",
}


@pytest.mark.parametrize("ticker", DEMO)
def test_the_company_facts_come_from_the_download_of_18_november(ticker):
    record = next(f for f in load(ticker, "provenance.json")["files"] if f["file"] == "companyfacts.json")
    assert record["raw_sha256"] == RAW_SHA256[ticker]
    assert record["retrieved"].startswith("2026-11-18T")


@pytest.mark.parametrize("ticker", DEMO)
def test_the_company_facts_record_says_the_quarterly_reports_are_kept(ticker):
    record = next(f for f in load(ticker, "provenance.json")["files"] if f["file"] == "companyfacts.json")
    assert "10-Q" in record["trimmed"] and "checksum" in record["trimmed"]


@pytest.mark.parametrize("ticker", DEMO + REFUSED)
def test_the_filing_list_holds_only_annual_reports(ticker):
    recent = load(ticker, "submissions.json")["filings"]["recent"]
    assert set(recent["form"]) <= ANNUAL
    assert len({len(column) for column in recent.values()}) == 1


@pytest.mark.parametrize("ticker", DEMO + REFUSED)
def test_every_file_records_its_source_and_time_but_no_request_headers(ticker):
    record = load(ticker, "provenance.json")
    expected_files = {"submissions.json", "companyfacts.json"} if ticker in DEMO else {"submissions.json"}
    assert {f["file"] for f in record["files"]} == expected_files
    for f in record["files"]:
        assert f["source"].startswith("https://data.sec.gov/")
        assert re.fullmatch(r"[0-9a-f]{64}", f["raw_sha256"])
        assert f["retrieved"].endswith("+00:00")
        assert set(f) == {"file", "source", "retrieved", "raw_bytes", "raw_sha256", "trimmed"}
    text = DEMO_DIR.joinpath(ticker, "provenance.json").read_text(encoding="utf-8").lower()
    assert "user-agent" not in text and "user_agent" not in text and "@" not in text


def test_coca_cola_fy2025_revenue_matches_the_course_snapshot():
    # Known answer from a cited source: session 5, slide 30.
    entries = [e for e in annual_entries(load("KO", "companyfacts.json"), "Revenues")
               if e["start"] == "2025-01-01" and e["end"] == "2025-12-31"]
    assert {(e["val"], e["accn"], e["filed"], e["form"]) for e in entries} == {
        (47_941_000_000, "0001628280-26-010047", "2026-02-20", "10-K")
    }


def test_jpmorgan_is_a_bank_and_must_be_refused():
    # SPEC §2: SEC industry codes 6000 to 6799 are not supported.
    assert 6000 <= int(load("JPM", "submissions.json")["sic"]) <= 6799


@pytest.mark.parametrize("ticker", DEMO)
def test_the_demo_companies_are_supported_industries(ticker):
    assert not 6000 <= int(load(ticker, "submissions.json")["sic"]) <= 6799


# --- the traits each company was chosen for (SPEC §13.2: "to be confirmed, not assumed") -----------------------


def test_apple_has_a_53_week_fiscal_year():
    facts = load("AAPL", "companyfacts.json")
    lengths = {(date.fromisoformat(e["end"]) - date.fromisoformat(e["start"])).days
               for e in annual_entries(facts, "RevenueFromContractWithCustomerExcludingAssessedTax")}
    assert any(length > 365 for length in lengths) and all(350 <= length <= 380 for length in lengths if length > 300)


def test_nvidia_share_count_jumps_with_its_2024_split():
    shares = load("NVDA", "companyfacts.json")["facts"]["dei"]["EntityCommonStockSharesOutstanding"]["units"]["shares"]
    by_date = {e["end"]: e["val"] for e in shares if e["form"] in ANNUAL}
    assert by_date["2025-02-21"] / by_date["2024-02-16"] > 9  # 10-for-1 split, June 2024


def test_mcdonalds_has_negative_equity():
    entries = annual_entries(load("MCD", "companyfacts.json"), "StockholdersEquity")
    latest = max(entries, key=lambda e: (e["end"], e["filed"]))
    assert latest["val"] < 0


def test_amazon_reports_no_dividend_tag_at_all():
    # Open question Q1: under SPEC §5.2 this is "missing", not "no dividend paid".
    us_gaap = load("AMZN", "companyfacts.json")["facts"]["us-gaap"]
    assert "PaymentsOfDividends" not in us_gaap and "PaymentsOfDividendsCommonStock" not in us_gaap
