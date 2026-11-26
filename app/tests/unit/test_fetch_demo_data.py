"""Re-trimming the saved demo data from cached downloads (slice S2c; review of PR #72). Owner: A.

`scripts/fetch_demo_data.py --retrim-from-cache` may rewrite evidence only from the very downloads the evidence
records. Rules tested here, in a temporary folder (never the real `app/evidence/`): every company's raw file is
checked before any file is written, so one bad file leaves the whole set unchanged; a company number that is not
ten digits is refused; a good run rewrites only `companyfacts.json` and the "trimmed" line of its record.
"""

import hashlib
import importlib.util
import json
from pathlib import Path

import pytest

SCRIPT = Path(__file__).resolve().parents[2] / "scripts" / "fetch_demo_data.py"
spec = importlib.util.spec_from_file_location("fetch_demo_data", SCRIPT)
fetch_demo_data = importlib.util.module_from_spec(spec)
spec.loader.exec_module(fetch_demo_data)


def raw_facts(cik):
    return {"cik": int(cik), "entityName": f"CO {cik}", "facts": {"us-gaap": {"Revenues": {"label": "Revenues", "units": {
        "USD": [{"start": "2025-01-01", "end": "2025-12-31", "val": 100, "accn": "a", "fy": 2025, "fp": "FY",
                 "form": "10-K", "filed": "2026-02-20"},
                {"start": "2026-01-01", "end": "2026-09-30", "val": 80, "accn": "b", "fy": 2026, "fp": "Q3",
                 "form": "10-Q", "filed": "2026-10-28"},
                {"start": "2026-01-01", "end": "2026-09-30", "val": 1, "accn": "c", "fy": 2026, "fp": "Q3",
                 "form": "8-K", "filed": "2026-10-28"}]}}}}}


def setup(tmp_path, ciks):
    """Evidence and cache folders for companies T0, T1, ...; returns (cache, evidence, tickers)."""
    cache, evidence, tickers = tmp_path / "cache", tmp_path / "evidence", []
    cache.mkdir()
    for i, cik in enumerate(ciks):
        ticker = f"T{i}"
        raw = json.dumps(raw_facts(cik if cik.isdigit() else "1")).encode("utf-8")
        (cache / f"companyfacts_{cik}.json").write_bytes(raw)
        folder = evidence / ticker
        folder.mkdir(parents=True)
        (folder / "companyfacts.json").write_text("OLD", encoding="utf-8")
        record = {"ticker": ticker, "cik": cik, "files": [
            {"source": "https://data.sec.gov/x", "retrieved": "2026-11-18T14:00:00+00:00", "raw_bytes": len(raw),
             "raw_sha256": hashlib.sha256(raw).hexdigest(), "trimmed": "only Form 10-K", "file": "companyfacts.json"}]}
        (folder / "provenance.json").write_text(json.dumps(record), encoding="utf-8")
        tickers.append(ticker)
    return cache, evidence, tickers


def test_a_good_run_rewrites_the_company_facts_and_the_trimmed_line_only(tmp_path):
    cache, evidence, tickers = setup(tmp_path, ["0000000001", "0000000002"])
    fetch_demo_data.retrim_from_cache(cache, evidence, tickers)
    saved = json.loads((evidence / "T0" / "companyfacts.json").read_text(encoding="utf-8"))
    assert [e["form"] for e in saved["facts"]["us-gaap"]["Revenues"]["units"]["USD"]] == ["10-K", "10-Q"]
    record = json.loads((evidence / "T0" / "provenance.json").read_text(encoding="utf-8"))["files"][0]
    assert "10-Q" in record["trimmed"] and "checksum" in record["trimmed"]
    assert record["retrieved"] == "2026-11-18T14:00:00+00:00"  # the record of the download itself is unchanged


def test_one_cached_file_that_is_not_the_recorded_download_leaves_every_file_unchanged(tmp_path):
    cache, evidence, tickers = setup(tmp_path, ["0000000001", "0000000002", "0000000003"])
    (cache / "companyfacts_0000000003.json").write_bytes(b'{"changed": true}')  # the third company's file differs
    with pytest.raises(ValueError):
        fetch_demo_data.retrim_from_cache(cache, evidence, tickers)
    for ticker in tickers:  # nothing written, not even for the first two companies
        assert (evidence / ticker / "companyfacts.json").read_text(encoding="utf-8") == "OLD"
        assert "only Form 10-K" in (evidence / ticker / "provenance.json").read_text(encoding="utf-8")


def test_a_company_number_that_is_not_ten_digits_is_refused(tmp_path):
    cache, evidence, tickers = setup(tmp_path, ["0000000001", "21344"])  # leading zeros missing
    with pytest.raises(ValueError, match="10 digits"):
        fetch_demo_data.retrim_from_cache(cache, evidence, tickers)
    assert (evidence / "T0" / "companyfacts.json").read_text(encoding="utf-8") == "OLD"
