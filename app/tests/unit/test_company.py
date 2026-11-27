"""`src.data.company`: the one module the interface imports from the data layer (SPEC §11). Owner: A.

Simon's review of PR #7: the interface must recognise the SEC errors (e.g. `SourceUnreachable` for acceptance E4)
without importing `src.data.sec_client`, so `src.data.company` makes them available next to `load_company`.
"""

import json
from datetime import datetime, timezone
from types import SimpleNamespace

import pytest

from src.data import company, sec_client

ERRORS = ("SecError", "SourceUnreachable", "SecRefused", "MissingUserAgent", "UnknownTicker", "NotFound", "InvalidCik")


@pytest.mark.parametrize("name", ERRORS)
def test_every_sec_error_is_available_from_the_interface_entry_point(name):
    assert getattr(company, name) is getattr(sec_client, name)
    assert name in company.__all__


def test_the_entry_point_lists_what_the_interface_may_use():
    assert {"load_company", "DEMO_TICKERS"} <= set(company.__all__)


@pytest.mark.parametrize("typed", ["KO/../AAPL", "MCD/", "../demo/KO", "/etc", "KO\\..\\AAPL", ""])
def test_demo_mode_only_opens_the_listed_demo_companies(typed):
    # Security review of 21 November 2026: "KO/../AAPL" loaded Apple under the name typed, and "MCD/" loaded
    # McDonald's without its company-specific rule. The typed text never reaches the file system.
    with pytest.raises(company.UnknownTicker):
        company.load_company(typed, demo=True)


def test_demo_mode_still_opens_the_demo_companies_however_they_are_typed():
    assert company.load_company(" ko ", demo=True).ticker == "KO"
    assert company.load_company("JPM", demo=True).ticker == "JPM"  # kept so that the app can refuse a bank


# --- S18 break-it round (27 November 2026): breaks no earlier test caught ------------------------------------------
# Each test failed against its deliberate break in a throwaway copy and passes on the unchanged code.

SUBMISSIONS_AT = datetime(2026, 11, 18, 9, 0, tzinfo=timezone.utc)
FACTS_AT = datetime(2026, 11, 18, 10, 30, tzinfo=timezone.utc)
SUBMISSIONS = {"cik": "0000000001", "name": "TEST CO", "filings": {"recent": {"form": ["10-K"],
                                                                                "filingDate": ["2026-02-20"]}}}


def facts():
    """Revenue for 2021 to 2025, in the SEC's layout (one 10-K value per year)."""
    rows = [{"start": f"{y}-01-01", "end": f"{y}-12-31", "val": 1000 + y, "accn": f"a-{y}", "fy": y, "fp": "FY",
             "form": "10-K", "filed": f"{y + 1}-02-20"} for y in range(2021, 2026)]
    return {"cik": 1, "entityName": "TEST CO", "facts": {"us-gaap": {"Revenues": {"units": {"USD": rows}}}}}


def test_demo_data_carry_the_retrieval_time_of_the_company_facts(tmp_path, monkeypatch):
    # COM-retrieved-file. The figures come from companyfacts.json, so their retrieval time is that file's (SPEC §5.1).
    # In the saved demo data both files share one time, so a folder of our own gives them different times.
    folder = tmp_path / "KO"
    folder.mkdir()
    (folder / "submissions.json").write_text(json.dumps(SUBMISSIONS), encoding="utf-8")
    (folder / "companyfacts.json").write_text(json.dumps(facts()), encoding="utf-8")
    (folder / "provenance.json").write_text(json.dumps({"files": [
        {"file": "submissions.json", "retrieved": SUBMISSIONS_AT.isoformat()},
        {"file": "companyfacts.json", "retrieved": FACTS_AT.isoformat()}]}), encoding="utf-8")
    monkeypatch.setattr(company, "DEMO_DIR", tmp_path)
    assert company.load_company("KO", demo=True).retrieved == FACTS_AT


class FakeClient:
    """Stands in for SecClient: answers from memory, never the network."""

    def cik_for(self, ticker):
        return "0000000001"

    def submissions(self, cik):
        return SimpleNamespace(data=SUBMISSIONS, retrieved=SUBMISSIONS_AT)

    def companyfacts(self, cik):
        return SimpleNamespace(data=facts(), retrieved=FACTS_AT)


def test_live_data_carry_the_retrieval_time_of_the_company_facts():
    # COM-live-retrieved. As in demo mode: the figures' retrieval time is the company facts download's.
    assert company.load_company("TST", client=FakeClient()).retrieved == FACTS_AT


def test_live_data_keep_the_number_of_years_asked_for():
    # COM-live-years. `years` reaches the resolver live as in demo mode: three years asked, 2023 to 2025 kept.
    data = company.load_company("TST", client=FakeClient(), years=3)
    assert [d.year for d in data.fiscal_years("revenue")] == [2023, 2024, 2025]
