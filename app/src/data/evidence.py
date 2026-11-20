"""Trimming downloaded SEC files into the saved evidence for the offline demo (slice S0b). Owner: A.

Pure functions, no network. The trimmed files keep the SEC's own JSON structure, so the resolver (slice S2) reads
saved demo data and live data the same way. Rules:
- company facts: only entries from annual reports (Form 10-K, 10-K/A, SPEC §5.3.1); cover-page (`dei`) facts keep
  every form, because SPEC §6 takes the share count from "the latest filing";
- submissions: only the annual reports in the list of recent filings, columns kept aligned; older pages dropped;
- provenance: the source address, retrieval time, size and SHA-256 checksum of the raw download (SPEC §4). Never
  the request headers: they hold the SEC_USER_AGENT name and e-mail.
"""

from __future__ import annotations

import hashlib
from datetime import datetime

ANNUAL_FORMS: tuple[str, ...] = ("10-K", "10-K/A")
KEEP_ALL_FORMS: tuple[str, ...] = ("dei",)


def trim_companyfacts(raw: dict, forms: tuple[str, ...] = ANNUAL_FORMS) -> dict:
    """A copy of a companyfacts file with only annual-report entries; concepts or units left empty are dropped."""
    trimmed = {key: value for key, value in raw.items() if key != "facts"}
    facts = {}
    for taxonomy, concepts in raw.get("facts", {}).items():
        kept = {}
        for tag, concept in concepts.items():
            units = {}
            for unit, entries in concept.get("units", {}).items():
                chosen = [dict(e) for e in entries if taxonomy in KEEP_ALL_FORMS or e.get("form") in forms]
                if chosen:
                    units[unit] = chosen
            if units:
                kept[tag] = {**{k: v for k, v in concept.items() if k != "units"}, "units": units}
        if kept:
            facts[taxonomy] = kept
    trimmed["facts"] = facts
    return trimmed


def trim_submissions(raw: dict, forms: tuple[str, ...] = ANNUAL_FORMS) -> dict:
    """A copy of a submissions file listing only annual reports among the recent filings, columns aligned."""
    recent = raw["filings"]["recent"]
    lengths = {len(column) for column in recent.values()}
    if len(lengths) > 1:
        raise ValueError(f"the columns of filings.recent are not aligned (lengths {sorted(lengths)})")
    keep = [i for i, form in enumerate(recent["form"]) if form in forms]
    trimmed = {key: value for key, value in raw.items() if key != "filings"}
    trimmed["filings"] = {"recent": {name: [column[i] for i in keep] for name, column in recent.items()}}
    return trimmed


def tickers_subset(raw: dict, tickers: list[str]) -> dict:
    """The entries of company_tickers.json for the given tickers, with their original keys."""
    wanted = {t.upper() for t in tickers}
    subset = {key: value for key, value in raw.items() if value["ticker"].upper() in wanted}
    missing = wanted - {value["ticker"].upper() for value in subset.values()}
    if missing:
        raise KeyError(f"tickers not in the SEC list: {sorted(missing)}")
    return subset


def provenance(url: str, retrieved: datetime, raw: bytes, trimmed: str) -> dict:
    """Where and when a file was downloaded, and how it was trimmed. Never includes request headers."""
    return {
        "source": url,
        "retrieved": retrieved.isoformat(),
        "raw_bytes": len(raw),
        "raw_sha256": hashlib.sha256(raw).hexdigest(),
        "trimmed": trimmed,
    }
