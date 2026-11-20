"""One-off download of the saved demo data (slice S0b). Owner: A.

Run from app/:   .venv/bin/python scripts/fetch_demo_data.py          (Windows: .venv\\Scripts\\python ...)

Downloads, for the five demo companies (SPEC §13.2), the SEC submissions and company facts files, plus the
submissions file of JPMorgan (the company that must be refused) and the SEC ticker list. Follows the SEC rules of
SPEC §4: a declared User-Agent read from app/.env (SEC_USER_AGENT, never printed or saved), at most 4 requests per
second, three retries with a growing pause, every raw response saved with its retrieval time in app/.cache/sec/
(git-ignored) and reused, so nothing is downloaded twice (`--refresh` downloads again).

Trimmed copies go to app/evidence/demo/ (committed; never edited by hand). An existing evidence file is never
overwritten.

The proper SEC client with tests comes in slice S1; this script only fills the evidence folder on day one.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

import requests
from dotenv import load_dotenv

APP = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(APP))

from src.data.evidence import provenance, tickers_subset, trim_companyfacts, trim_submissions  # noqa: E402

DEMO = ["KO", "AAPL", "NVDA", "MCD", "AMZN"]
REFUSED = ["JPM"]  # a bank: only its submissions file is needed to show that it is refused
TICKERS_URL = "https://www.sec.gov/files/company_tickers.json"
SUBMISSIONS_URL = "https://data.sec.gov/submissions/CIK{cik}.json"
FACTS_URL = "https://data.sec.gov/api/xbrl/companyfacts/CIK{cik}.json"
CACHE = APP / ".cache" / "sec"
EVIDENCE = APP / "evidence" / "demo"
MIN_INTERVAL = 0.25  # seconds between requests: at most 4 per second (SPEC §4 allows 5, the SEC 10)
RETRIES = 3

_last_request = 0.0


def user_agent() -> str:
    load_dotenv(APP / ".env")
    agent = os.environ.get("SEC_USER_AGENT", "").strip().strip('"')
    if not agent.isascii():
        sys.exit(
            "SEC_USER_AGENT in app/.env contains a character that is not plain ASCII, often a curly quote “ ” typed "
            'by the Mac. Retype the line with straight quotes: SEC_USER_AGENT="Your Name your@email". '
            "(The value is not printed.)"
        )
    if "@" not in agent or "example.com" in agent:
        sys.exit(
            "SEC_USER_AGENT is missing, unreadable or still the example. Create app/.env from app/.env.example and "
            'put your own name and e-mail there with straight quotes: SEC_USER_AGENT="Your Name your@email" '
            "(the SEC requires it). The value is never printed or saved."
        )
    return agent


def download(session: requests.Session, url: str, name: str, refresh: bool) -> tuple[bytes, dict]:
    """The raw bytes of `url` and their provenance, from the cache when possible."""
    global _last_request
    raw_path, meta_path = CACHE / f"{name}.json", CACHE / f"{name}.provenance.json"
    if raw_path.exists() and meta_path.exists() and not refresh:
        print(f"  cached  {url}")
        return raw_path.read_bytes(), json.loads(meta_path.read_text(encoding="utf-8"))
    for attempt in range(RETRIES + 1):
        wait = MIN_INTERVAL - (time.monotonic() - _last_request)
        if wait > 0:
            time.sleep(wait)
        _last_request = time.monotonic()
        try:
            response = session.get(url, timeout=30)
            if response.status_code == 200:
                break
            problem = f"HTTP {response.status_code}"
            if response.status_code not in (429, 500, 502, 503, 504):
                sys.exit(f"{url}: {problem}; not retried")
        except requests.RequestException as error:
            problem = type(error).__name__
        if attempt == RETRIES:
            sys.exit(f"{url}: {problem} after {RETRIES} retries; nothing saved for it")
        pause = 2**attempt
        print(f"  {problem}, retrying in {pause} s")
        time.sleep(pause)
    retrieved = datetime.now(timezone.utc).replace(microsecond=0)
    raw = response.content
    record = provenance(url, retrieved, raw, trimmed="")
    CACHE.mkdir(parents=True, exist_ok=True)
    raw_path.write_bytes(raw)
    meta_path.write_text(json.dumps(record, indent=1) + "\n", encoding="utf-8")
    print(f"  fetched {url} ({len(raw):,} bytes)")
    return raw, record


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

    session = requests.Session()
    session.headers.update({"User-Agent": user_agent(), "Accept-Encoding": "gzip, deflate"})

    print("SEC ticker list")
    raw, record = download(session, TICKERS_URL, "company_tickers", args.refresh)
    subset = tickers_subset(json.loads(raw), DEMO + REFUSED)
    save(EVIDENCE / "tickers.json", subset)
    save(EVIDENCE / "tickers.provenance.json", {**record, "trimmed": f"only the tickers {DEMO + REFUSED}"})
    cik = {entry["ticker"]: f"{entry['cik_str']:010d}" for entry in subset.values()}

    for ticker in DEMO + REFUSED:
        print(ticker)
        records = []
        raw, record = download(session, SUBMISSIONS_URL.format(cik=cik[ticker]), f"submissions_{cik[ticker]}", args.refresh)
        save(EVIDENCE / ticker / "submissions.json", trim_submissions(json.loads(raw)))
        records.append({**record, "file": "submissions.json", "trimmed": "only Form 10-K and 10-K/A in filings.recent; older pages dropped"})
        if ticker in DEMO:
            raw, record = download(session, FACTS_URL.format(cik=cik[ticker]), f"companyfacts_{cik[ticker]}", args.refresh)
            save(EVIDENCE / ticker / "companyfacts.json", trim_companyfacts(json.loads(raw)))
            records.append({**record, "file": "companyfacts.json", "trimmed": "only Form 10-K and 10-K/A entries (dei: all forms)"})
        save(EVIDENCE / ticker / "provenance.json", {"ticker": ticker, "cik": cik[ticker], "files": records})


if __name__ == "__main__":
    main()
