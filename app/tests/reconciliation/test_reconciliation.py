"""Hand reconciliation (slice S15): figures read by a team member from the 10-K, compared with the app.

Owner of the format and of this test: A. Each member owns their own `<TICKER>.yaml` (format in README.md). The app
side uses the saved demo data, so the network stays blocked.

The test checks that every file is complete and that the app reads the same figure, from the same filing, within
USD 0.5 million (SPEC §13.2, S15). A mismatch is a bug to fix before anything else is merged (SPEC §13.5, R6): never
edit a file to match the app.
"""

import re
from datetime import date
from functools import lru_cache
from pathlib import Path

import pytest
import yaml

from src.data.company import DEMO_TICKERS, load_company

FOLDER = Path(__file__).parent
FIGURES = ("revenue", "operating_income", "net_income", "total_assets", "operating_cash_flow", "dividends_paid")
OPTIONAL = ("capital_expenditure",)  # read when a check owner needs it (D6, Flo's S7 review); compared the same way
TOLERANCE_MILLIONS = 0.5  # SPEC §13.2, S15
MEMBER = re.compile(r"^\S.* \([A-E]\)$")  # e.g. "Igor (A)": a team member, never an assistant
ACCESSION = re.compile(r"^\d{10}-\d{2}-\d{6}$")


def record_paths() -> list[Path]:
    return sorted(FOLDER.glob("*.yaml"))


def load(path: Path) -> dict:
    return yaml.safe_load(path.read_text(encoding="utf-8"))


def as_date(value: object) -> date | None:
    try:
        return value if isinstance(value, date) else date.fromisoformat(str(value))
    except ValueError:
        return None


def problems(record: dict, ticker: str) -> list[str]:
    """What is wrong with one reconciliation file; an empty list when it is complete."""
    found = []
    if record.get("company") != ticker:
        found.append(f"company should be {ticker!r}, the file name")
    if ticker not in DEMO_TICKERS:
        found.append(f"{ticker} is not a demo company ({', '.join(DEMO_TICKERS)})")
    if not MEMBER.match(str(record.get("read_by", ""))):
        found.append("read_by should name the team member who read the filing, e.g. 'Igor (A)'")
    for key in ("date_read", "fiscal_year_end"):
        if as_date(record.get(key)) is None:
            found.append(f"{key} should be a date, e.g. 2026-11-21")
    if not ACCESSION.match(str(record.get("accession", ""))):
        found.append("accession should look like 0001628280-26-010047")
    if record.get("unit") != "USD millions":
        found.append("unit should be 'USD millions'")
    figures = record.get("figures") or {}
    if not set(FIGURES) <= set(figures) <= set(FIGURES + OPTIONAL):
        found.append(f"figures should be exactly {', '.join(FIGURES)}, plus optionally {', '.join(OPTIONAL)}")
    for name, figure in figures.items():
        figure = figure or {}
        value, page = figure.get("value"), figure.get("page")
        if value is not None and not isinstance(value, (int, float)):
            found.append(f"{name}: value should be a number in USD millions, or null if the filing has no such line")
        if value is None and not figure.get("note"):
            found.append(f"{name}: a null value needs a note saying what the filing shows")
        if not isinstance(page, int) or isinstance(page, bool) or page < 1:
            found.append(f"{name}: page should be the page number printed in the filing")
        if not str(figure.get("line_in_filing") or "").strip():
            found.append(f"{name}: line_in_filing should be the line's name as printed")
    return found


@lru_cache(maxsize=None)
def app_data(ticker: str):
    return load_company(ticker, demo=True)


PATHS = record_paths()
PAIRS = [(path, name) for path in PATHS for name in FIGURES + OPTIONAL if name in (load(path).get("figures") or {})]


def test_the_folder_holds_at_least_one_reconciliation():
    assert PATHS, f"no <TICKER>.yaml in {FOLDER}"


@pytest.mark.parametrize("path", PATHS, ids=lambda p: p.stem)
def test_each_reconciliation_file_is_complete(path):
    assert problems(load(path), path.stem) == []


@pytest.mark.parametrize("path, name", PAIRS, ids=lambda x: x.stem if isinstance(x, Path) else x)
def test_the_app_reads_the_same_figure_from_the_same_filing(path, name):
    record = load(path)
    by_hand = record["figures"][name]
    fact = app_data(path.stem).fact(name, as_date(record["fiscal_year_end"]))
    app_value = None if fact is None or fact.value is None else fact.value / 1_000_000
    if by_hand["value"] is None:
        # The filing has no such line (e.g. no dividends): the app must show none either, as missing or as nil.
        assert app_value in (None, 0), f"{name}: the filing shows none, the app shows {app_value:,.1f}"
        return
    assert app_value is not None, f"{name}: read by hand as {by_hand['value']:,}, missing in the app"
    assert abs(app_value - by_hand["value"]) <= TOLERANCE_MILLIONS, (
        f"{name}: read by hand {by_hand['value']:,} on page {by_hand['page']}, app {app_value:,.1f} "
        f"({fact.tag}, accession {fact.accession})")
    assert fact.accession == record["accession"], (
        f"{name}: the app took the figure from filing {fact.accession}, the hand reading from {record['accession']}")


GOOD = {
    "company": "KO", "read_by": "Igor (A)", "date_read": "2026-11-21", "fiscal_year_end": "2025-12-31",
    "accession": "0001628280-26-010047", "unit": "USD millions",
    "figures": {name: {"value": 1.0, "page": 61, "line_in_filing": "Line"} for name in FIGURES},
}


def changed(**changes) -> dict:
    record = yaml.safe_load(yaml.safe_dump(GOOD))
    for key, value in changes.items():
        if key in FIGURES:
            record["figures"][key].update(value)
        else:
            record[key] = value
    return record


def test_a_complete_record_has_no_problems():
    assert problems(changed(), "KO") == []


@pytest.mark.parametrize("record, expected", [
    (changed(read_by="Codex assistant"), "read_by"),
    (changed(unit="USD thousands"), "unit"),
    (changed(accession="2026-010047"), "accession"),
    (changed(fiscal_year_end="31/12/2025"), "fiscal_year_end"),
    (changed(revenue={"page": None}), "revenue: page"),
    (changed(dividends_paid={"value": None}), "dividends_paid: a null value needs a note"),
    (changed(net_income={"value": "13,107"}), "net_income: value"),
    (changed(total_assets={"line_in_filing": " "}), "total_assets: line_in_filing"),
    (changed(company="AAPL"), "company"),
], ids=["assistant-as-reader", "thousands", "accession", "date-format", "no-page", "null-without-note",
        "value-as-text", "no-line-name", "wrong-company"])
def test_an_incomplete_record_is_named(record, expected):
    assert any(problem.startswith(expected) for problem in problems(record, "KO")), problems(record, "KO")


def test_a_figure_missing_from_the_record_is_named():
    record = changed()
    del record["figures"]["dividends_paid"]
    assert any(problem.startswith("figures should be exactly") for problem in problems(record, "KO"))


def test_a_company_outside_the_demo_data_is_named():
    assert any("not a demo company" in problem for problem in problems(changed(company="TSLA"), "TSLA"))


def test_capital_expenditure_may_be_read_as_a_seventh_figure():
    # Flo (C) asked for Coca-Cola's capital expenditure to test D6 against a figure read by hand (S7 review).
    record = changed()
    record["figures"]["capital_expenditure"] = {"value": 1.0, "page": 64, "line_in_filing": "Line"}
    assert problems(record, "KO") == []


def test_an_unknown_figure_is_named():
    record = changed()
    record["figures"]["goodwill"] = {"value": 1.0, "page": 63, "line_in_filing": "Goodwill"}
    assert any(problem.startswith("figures should be exactly") for problem in problems(record, "KO"))


def test_every_figure_in_a_file_is_compared_with_the_app():
    for path in PATHS:
        compared = {name for p, name in PAIRS if p == path}
        assert compared == set(load(path)["figures"]), path.stem

