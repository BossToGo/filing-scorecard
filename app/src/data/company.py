"""One entry point for the interface: a company's data, live from the SEC or from the saved demo data. Owner: A.

    from src.data.company import load_company
    data = load_company("KO", demo=True)       # CompanyData, no network
    data = load_company("KO")                  # live: needs SEC_USER_AGENT in app/.env

Errors are `SecError`s whose messages say how to fix the problem. The interface imports them from here, never from
src.data.sec_client (SPEC §11; a layering test enforces it):

    from src.data.company import load_company, SourceUnreachable, UnknownTicker
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path

from src.contracts import CompanyData
from src.data.resolver import resolve
from src.data.sec_client import (
    InvalidCik,
    MissingUserAgent,
    NotFound,
    SecClient,
    SecError,
    SecRefused,
    SourceUnreachable,
    UnknownTicker,
)

__all__ = ["load_company", "DEMO_TICKERS", "DEMO_DIR", "SecError", "SourceUnreachable", "SecRefused",
           "MissingUserAgent", "UnknownTicker", "NotFound", "InvalidCik"]

DEMO_DIR = Path(__file__).resolve().parents[2] / "evidence" / "demo"
DEMO_TICKERS = ("KO", "AAPL", "NVDA", "MCD", "AMZN")  # plus JPM, which the app must refuse


def _read(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def load_company(ticker: str, *, demo: bool = False, client: SecClient | None = None,
                 years: int | None = None) -> CompanyData:
    symbol = ticker.strip().upper()
    if demo:
        folder = DEMO_DIR / symbol
        if not (folder / "submissions.json").exists():
            raise UnknownTicker(
                f"{symbol!r} is not in the demo data, which has {', '.join(DEMO_TICKERS)} and JPM. Switch demo mode "
                "off to look up other companies."
            )
        facts_path = folder / "companyfacts.json"
        provenance = _read(folder / "provenance.json")
        facts_record = next((f for f in provenance["files"] if f["file"] == "companyfacts.json"), provenance["files"][0])
        return resolve(symbol, _read(facts_path) if facts_path.exists() else None, _read(folder / "submissions.json"),
                       datetime.fromisoformat(facts_record["retrieved"]), years=years)
    client = client or SecClient.from_settings()
    cik = client.cik_for(symbol)
    submissions = client.submissions(cik)
    facts = client.companyfacts(cik)
    return resolve(symbol, facts.data, submissions.data, facts.retrieved, years=years)
