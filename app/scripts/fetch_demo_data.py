"""One-off download of the saved demo data (slice S0b), and its re-trimming without the network (slice S2c). Owner: A.

Run from app/:   .venv/bin/python scripts/fetch_demo_data.py          (Windows: .venv\\Scripts\\python ...)

Downloads, for the five demo companies (SPEC §13.2), the SEC submissions and company facts files, plus the
submissions file of JPMorgan (the company that must be refused) and the SEC ticker list, through the app's SEC
client (`src/data/sec_client.py`: declared User-Agent from app/.env, rate limit, retries, raw responses cached in
app/.cache/sec/ and reused; `--refresh` downloads again).

Trimmed copies go to app/evidence/demo/ (committed; never edited by hand). An existing evidence file is never
overwritten, with one exception:

    .venv/bin/python scripts/fetch_demo_data.py --retrim-from-cache .cache/sec

trims the five companies' company facts again from the raw downloads in that folder, keeping the quarterly reports
too (slice S2c, issue #71 item 1). No network and no app/.env are used. Each raw file must have exactly the size and
SHA-256 checksum written in the company's provenance.json, so the new file comes from the very same download. All five
are checked before any file is written, and each file is swapped in whole; only companyfacts.json and the "trimmed"
line of its record change.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
from datetime import date
from pathlib import Path

APP = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(APP))

from src.data.evidence import (  # noqa: E402
    DEMO_FORMS,
    check_same_download,
    tickers_subset,
    trim_companyfacts,
    trim_submissions,
)
from src.data.sec_client import SecClient, SecError  # noqa: E402

DEMO = ["KO", "AAPL", "NVDA", "MCD", "AMZN"]
REFUSED = ["JPM"]  # a bank: only its submissions file is needed to show that it is refused
EVIDENCE = APP / "evidence" / "demo"
FACTS_TRIMMED = "only Form 10-K, 10-K/A, 10-Q and 10-Q/A entries (dei: all forms)"


def _shown(path: Path) -> str:
    return str(path.relative_to(APP)) if path.is_relative_to(APP) else str(path)


def write(path: Path, data: dict) -> None:
    """Write JSON to a temporary file in the same folder, then swap it in, so an interrupted run never leaves a
    half-written evidence file."""
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(path.name + ".tmp")
    temporary.write_text(json.dumps(data, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
    os.replace(temporary, path)
    print(f"  saved   {_shown(path)} ({path.stat().st_size:,} bytes)")


def save(path: Path, data: dict) -> None:
    if path.exists():
        print(f"  kept    {_shown(path)} (evidence is never overwritten)")
        return
    write(path, data)


def retrim_from_cache(cache: Path, evidence: Path = EVIDENCE, tickers: list[str] = DEMO) -> None:
    """Re-trim the companyfacts.json files from the recorded raw downloads in `cache` (no network). Every company is
    checked before anything is written: one raw file that is not the recorded download leaves the whole set as it
    was (review of PR #72)."""
    checked = []
    for ticker in tickers:  # first pass: read and check, write nothing
        record_path = evidence / ticker / "provenance.json"
        record = json.loads(record_path.read_text(encoding="utf-8"))
        if not re.fullmatch(r"\d{10}", str(record["cik"])):
            raise ValueError(f"{ticker}: the company number {record['cik']!r} in provenance.json is not 10 digits; "
                             "nothing was written")
        facts_record = next(f for f in record["files"] if f["file"] == "companyfacts.json")
        raw = (cache / f"companyfacts_{record['cik']}.json").read_bytes()
        try:
            check_same_download(raw, facts_record)
        except ValueError as error:
            raise ValueError(f"{ticker}: {error}; nothing was written") from None
        checked.append((ticker, record_path, record, facts_record, raw))
    for ticker, record_path, record, facts_record, raw in checked:  # second pass: write
        print(ticker)
        write(evidence / ticker / "companyfacts.json", trim_companyfacts(json.loads(raw), DEMO_FORMS))
        facts_record["trimmed"] = (f"{FACTS_TRIMMED}; re-trimmed on {date.today().isoformat()} from this same "
                                   "download, size and SHA-256 checksum checked (slice S2c, issue #71)")
        write(record_path, record)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("--refresh", action="store_true", help="download again instead of using app/.cache/sec/")
    parser.add_argument("--retrim-from-cache", type=Path, metavar="DIR",
                        help="re-trim the company facts from the recorded raw downloads in DIR, without the network")
    args = parser.parse_args()
    if args.retrim_from_cache:
        try:
            retrim_from_cache(args.retrim_from_cache)
        except (OSError, ValueError) as error:
            sys.exit(str(error))
        return
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
                save(EVIDENCE / ticker / "companyfacts.json", trim_companyfacts(facts.data, DEMO_FORMS))
                records.append({**facts.provenance, "file": "companyfacts.json", "trimmed": FACTS_TRIMMED})
            save(EVIDENCE / ticker / "provenance.json", {"ticker": ticker, "cik": cik, "files": records})
    except SecError as error:
        sys.exit(str(error))


if __name__ == "__main__":
    main()
