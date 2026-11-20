"""One-off download of the saved demo data (slice S0b). Owner: A.

Run from app/:   .venv/bin/python scripts/fetch_demo_data.py          (Windows: .venv\\Scripts\\python ...)

Downloads, for the five demo companies (SPEC §13.2), the SEC submissions and company facts files, plus the
submissions file of JPMorgan (the company that must be refused) and the SEC ticker list, through the app's SEC
client (`src/data/sec_client.py`: declared User-Agent from app/.env, rate limit, retries, raw responses cached in
app/.cache/sec/ and reused; `--refresh` downloads again).

Trimmed copies go to app/evidence/demo/ (committed; never edited by hand). An existing evidence file is never
overwritten.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

APP = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(APP))

from src.data.evidence import tickers_subset, trim_companyfacts, trim_submissions  # noqa: E402
from src.data.sec_client import SecClient, SecError  # noqa: E402

DEMO = ["KO", "AAPL", "NVDA", "MCD", "AMZN"]
REFUSED = ["JPM"]  # a bank: only its submissions file is needed to show that it is refused
EVIDENCE = APP / "evidence" / "demo"


def save(path: Path, data: dict) -> None:
    if path.exists():
        print(f"  kept    {path.relative_to(APP)} (evidence is never overwritten)")
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"  saved   {path.relative_to(APP)} ({path.stat().st_size:,} bytes)")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("--refresh", action="store_true", help="download again instead of using app/.cache/sec/")
    args = parser.parse_args()
    try:
        sec = SecClient.from_settings()
        print("SEC ticker list")
        tickers = sec.ticker_list(refresh=args.refresh)
        subset = tickers_subset(tickers.data, DEMO + REFUSED)
        save(EVIDENCE / "tickers.json", subset)
        save(EVIDENCE / "tickers.provenance.json", {**tickers.provenance, "trimmed": f"only the tickers {DEMO + REFUSED}"})
        for ticker in DEMO + REFUSED:
            print(ticker)
            cik = sec.cik_for(ticker)
            records = []
            submissions = sec.submissions(cik, refresh=args.refresh)
            save(EVIDENCE / ticker / "submissions.json", trim_submissions(submissions.data))
            records.append({**submissions.provenance, "file": "submissions.json",
                            "trimmed": "only Form 10-K and 10-K/A in filings.recent; older pages dropped"})
            if ticker in DEMO:
                facts = sec.companyfacts(cik, refresh=args.refresh)
                save(EVIDENCE / ticker / "companyfacts.json", trim_companyfacts(facts.data))
                records.append({**facts.provenance, "file": "companyfacts.json",
                                "trimmed": "only Form 10-K and 10-K/A entries (dei: all forms)"})
            save(EVIDENCE / ticker / "provenance.json", {"ticker": ticker, "cik": cik, "files": records})
    except SecError as error:
        sys.exit(str(error))


if __name__ == "__main__":
    main()
