"""S4: the fixed January 2026 US benchmarks, read only from the small cited CSV.

    benchmarks = load_benchmarks("KO")
    benchmarks.fact("roe")               # company industry's unadjusted ROE
    benchmarks.market_fact("pe")         # US market excluding financials, for V4

Unknown tickers have missing industry facts, while market facts remain available.
No network, Excel dependency, SIC fallback or user override is used at runtime.
"""

from __future__ import annotations

import csv
import math
import re
from dataclasses import dataclass
from datetime import date, datetime
from pathlib import Path

from src.contracts import Fact

DATA_FILE = Path(__file__).resolve().parents[2] / "data" / "benchmarks_us_2026.csv"
AS_OF = date(2026, 1, 5)
SOURCE_BASE = "https://pages.stern.nyu.edu/~adamodar/pc/datasets/"
SOURCE_COLUMNS = {
    "unlevered_beta": ("betas.xls", "Unlevered beta"),
    "roe": ("roe.xls", "ROE (unadjusted)"),
    "operating_margin": ("margin.xls", "Pre-tax Unadjusted Operating Margin"),
    "pe": ("pedata.xls", "Current PE"),
    "pb": ("pbvdata.xls", "PBV"),
    "dividend_yield": ("divfund.xls", "Dividend Yield"),
}
# V4 matches the app's non-financial universe; D2 keeps the total-market dividend yield.
MARKET_GROUPS = {metric: "Total Market" for metric in SOURCE_COLUMNS}
MARKET_GROUPS["pe"] = "Total Market (without financials)"
FIELDS = {
    "ticker", "industry", "metric", "value", "unit", "num_firms", "as_of", "retrieved_at",
    "source_file", "source_sheet", "source_row", "source_column", "source_url", "source_sha256",
    "lookup_sheet", "lookup_row", "lookup_exchange_ticker", "lookup_country", "lookup_sha256",
}


class BenchmarkDataError(ValueError):
    """The extract is malformed; restore the checked-in January 2026 benchmark CSV."""


def _missing(metric: str, reason: str) -> Fact:
    return Fact(metric, None, "pure", None, AS_OF, "missing", None, None, None, None, None, reason)


@dataclass(frozen=True)
class BenchmarkData:
    industry: str | None
    route: str
    num_firms: int | None
    lookup_source: str
    industry_facts: tuple[Fact, ...]
    market_facts: tuple[Fact, ...]
    warnings: tuple[str, ...] = ()

    def fact(self, metric: str) -> Fact:
        """Industry figure with provenance, or an explicitly missing Fact."""
        if metric not in SOURCE_COLUMNS:
            raise KeyError(f"Unknown benchmark metric {metric!r}")
        return next((f for f in self.industry_facts if f.metric == metric),
                    _missing(metric, "Industry benchmark missing: no cited demo-company match or metric row."))

    def market_fact(self, metric: str) -> Fact:
        """Metric's specified market group; unknown companies retain market comparisons."""
        if metric not in SOURCE_COLUMNS:
            raise KeyError(f"Unknown benchmark metric {metric!r}")
        return next((f for f in self.market_facts if f.metric == metric),
                    _missing(metric, "Whole US market benchmark missing: no Total Market metric row."))


def _positive_integer(text: str) -> int:
    if not text.isascii() or not text.isdecimal() or int(text) < 1:
        raise ValueError("expected a positive integer")
    return int(text)


def _fact(row: dict[str, str]) -> Fact:
    metric = row["metric"]
    if metric not in SOURCE_COLUMNS:
        raise ValueError("unsupported metric or forecast column")
    filename, column = SOURCE_COLUMNS[metric]
    if (row["source_file"], row["source_column"]) != (filename, column):
        raise ValueError("source file/column differs from the documented metric definition")
    if row["source_sheet"] != "Industry Averages" or row["source_url"] != SOURCE_BASE + filename:
        raise ValueError("unexpected source sheet or URL")
    _positive_integer(row["source_row"])
    _positive_integer(row["num_firms"])
    if not re.fullmatch(r"[0-9a-f]{64}", row["source_sha256"]):
        raise ValueError("missing source workbook checksum")
    if row["unit"] != "pure" or date.fromisoformat(row["as_of"]) != AS_OF:
        raise ValueError("expected decimal ratios/multiples from January 2026")
    retrieved = datetime.fromisoformat(row["retrieved_at"])
    if retrieved.tzinfo is None:
        raise ValueError("retrieval timestamp needs its timezone")
    if not row["industry"].strip():
        raise ValueError("industry name missing")
    note = (f"Damodaran US, {row['industry']}, {row['num_firms']} firms; {filename}, "
            f"{row['source_sheet']}, row {row['source_row']}, column {column}; "
            f"as of {AS_OF}; {row['source_url']}; SHA-256 {row['source_sha256']}.")
    if not row["value"].strip():
        return Fact(metric, None, "pure", None, AS_OF, "missing", column, filename,
                    f"Damodaran:{AS_OF}:{filename}:{row['source_row']}", None, retrieved,
                    f"Source benchmark cell is blank. {note}")
    value = float(row["value"])
    if not math.isfinite(value):
        raise ValueError("benchmark value must be finite; blank means missing")
    return Fact(metric, value, "pure", None, AS_OF, "reported", column, filename,
                f"Damodaran:{AS_OF}:{filename}:{row['source_row']}", None, retrieved, note)


def load_benchmarks(ticker: str, *, path: Path = DATA_FILE) -> BenchmarkData:
    """Load the MVP table. Missing files become missing data; corrupt files fail clearly."""
    symbol = ticker.strip().upper()
    try:
        with Path(path).open(newline="", encoding="utf-8") as source:
            reader = csv.DictReader(source)
            if reader.fieldnames is None or set(reader.fieldnames) != FIELDS or len(reader.fieldnames) != len(FIELDS):
                raise BenchmarkDataError("Invalid benchmark columns; restore app/data/benchmarks_us_2026.csv.")
            rows = list(reader)
    except FileNotFoundError:
        return BenchmarkData(None, "missing", None, "", (), (),
                             ("Benchmark CSV absent: restore app/data/benchmarks_us_2026.csv.",))
    except (UnicodeError, csv.Error, OSError) as error:
        raise BenchmarkDataError("Cannot read benchmark CSV; restore app/data/benchmarks_us_2026.csv.") from error

    seen: set[tuple[str, str]] = set()
    matches: dict[str, tuple[str, str, str, str, str, str]] = {}
    industry_facts, market_facts = [], []
    industry = lookup_source = None
    firms = None
    for line, row in enumerate(rows, 2):
        try:
            if set(row) != FIELDS or any(value is None for value in row.values()):
                raise ValueError("wrong number of columns")
            key = row["ticker"], row["metric"]
            if key in seen:
                raise ValueError("duplicate company/metric benchmark row")
            seen.add(key)
            fact = _fact(row)
            if row["ticker"]:
                if row["ticker"] not in {"KO", "AAPL", "NVDA", "MCD", "AMZN"}:
                    raise ValueError("only five demo tickers belong in the MVP extract")
                _positive_integer(row["lookup_row"])
                if (row["lookup_sheet"] != "By company name" or row["lookup_country"] != "United States"
                        or row["lookup_exchange_ticker"].split(":")[-1] != row["ticker"]
                        or ":" not in row["lookup_exchange_ticker"]
                        or not re.fullmatch(r"[0-9a-f]{64}", row["lookup_sha256"])):
                    raise ValueError("invalid company lookup provenance")
                match = (row["industry"], row["num_firms"], row["lookup_sheet"], row["lookup_row"],
                         row["lookup_exchange_ticker"], row["lookup_sha256"])
                if row["ticker"] in matches and matches[row["ticker"]] != match:
                    raise ValueError("company maps to inconsistent industry or lookup provenance")
                matches[row["ticker"]] = match
                if row["ticker"] == symbol:
                    industry, firms = row["industry"], int(row["num_firms"])
                    lookup_source = (f"{SOURCE_BASE}indname.xls, {row['lookup_sheet']}, "
                                     f"row {row['lookup_row']}, {row['lookup_exchange_ticker']}; "
                                     f"retrieved {row['retrieved_at']}; SHA-256 {row['lookup_sha256']}")
                    industry_facts.append(fact)
            else:
                if row["industry"] != MARKET_GROUPS[row["metric"]]:
                    raise ValueError("market benchmark group differs from SPEC §7's metric-specific selection")
                market_facts.append(fact)
        except (ValueError, TypeError, KeyError) as error:
            raise BenchmarkDataError(f"Invalid benchmark CSV at line {line}: {error}; restore the cited extract.") from error
    return BenchmarkData(industry, "Damodaran lookup" if industry else "missing", firms,
                         lookup_source or "", tuple(industry_facts), tuple(market_facts))
