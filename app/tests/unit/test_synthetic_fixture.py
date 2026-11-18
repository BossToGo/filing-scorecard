"""The synthetic company fixture is a faithful copy of SPEC.md Appendix A, and its expected values stay locked
until their owner signs off (SPEC rule 14.5). Owner: A (slice S0c).

These tests compare the fixture with the tables in SPEC.md itself, so a copying mistake in
`tests/fixtures/synthetic_co.yaml` fails here instead of reaching the checks.
"""

import re
from datetime import date
from pathlib import Path

import pytest
import yaml

from tests.fixtures import synthetic

APP = Path(__file__).resolve().parents[2]
SPEC = (APP.parent / "SPEC.md").read_text(encoding="utf-8")
APPENDIX_A = SPEC[SPEC.index("## Appendix A") : SPEC.index("## Appendix B")]
FIXTURE = yaml.safe_load((APP / "tests" / "fixtures" / "synthetic_co.yaml").read_text(encoding="utf-8"))

ROW_TO_METRIC = {
    "Revenue": "revenue",
    "Operating income": "operating_income",
    "Interest expense": "interest_expense",
    "Net income": "net_income",
    "Depreciation and amortisation": "depreciation_amortization",
    "Capital expenditure": "capital_expenditure",
    "Operating cash flow": "operating_cash_flow",
    "Dividends paid": "dividends_paid",
    "Total assets": "total_assets",
    "Current assets": "current_assets",
    "Current liabilities": "current_liabilities",
    "Cash": "cash",
    "Financial debt": "financial_debt",
    "Equity": "equity",
    "Total liabilities": "total_liabilities",
}


def plain(text: str) -> str:
    """SPEC text with thousands separators removed and the typographic minus turned into '-'."""
    return re.sub(r"(?<=\d),(?=\d{3})", "", text).replace("−", "-")


def numbers(text: str) -> list[str]:
    return re.findall(r"-?\d+(?:\.\d+)?", plain(text))


def table_rows(text: str) -> list[list[str]]:
    return [[c.strip() for c in line.strip().strip("|").split("|")] for line in text.splitlines() if line.startswith("|")]


def shown(value: float, decimals: int) -> str:
    return f"{value:.{decimals}f}"


# --- inputs ---------------------------------------------------------------------------------------------------


def test_the_financial_table_matches_appendix_a():
    rows = {r[0]: [float(n) for n in numbers(" ".join(r[1:]))] for r in table_rows(APPENDIX_A) if r[0] in ROW_TO_METRIC}
    assert len(rows) == 15
    for label, metric in ROW_TO_METRIC.items():
        assert FIXTURE["line_items"][metric] == rows[label], label


def test_the_other_inputs_settings_and_benchmarks_match_appendix_a():
    text = plain(APPENDIX_A)

    def found(pattern):
        match = re.search(pattern, text)
        assert match, pattern
        return float(match.group(1))

    other, settings, bench = FIXTURE["other_inputs"], FIXTURE["settings"], FIXTURE["benchmarks"]
    assert other["current_financial_debt_fy2025"] == found(r"current financial debt FY2025 = (\d+)")
    assert other["shares_millions"] == found(r"shares = (\d+) million")
    assert other["share_price_usd"] == found(r"share price = USD ([\d.]+)")
    assert settings["risk_free_rate"] == pytest.approx(found(r"risk-free rate ([\d.]+)%") / 100)
    assert settings["equity_risk_premium"] == pytest.approx(found(r"equity risk premium ([\d.]+)%") / 100)
    assert settings["tax_rate"] == pytest.approx(found(r"tax rate ([\d.]+)%") / 100)
    assert settings["terminal_growth"] == pytest.approx(found(r"terminal growth ([\d.]+)%") / 100)
    assert bench["unlevered_beta"] == found(r"unlevered beta ([\d.]+)")
    assert bench["return_on_equity"] == pytest.approx(found(r"return on equity ([\d.]+)%") / 100)
    assert bench["operating_margin"] == pytest.approx(found(r"operating margin ([\d.]+)%") / 100)
    assert bench["price_to_earnings"] == found(r"price to earnings ([\d.]+)")
    assert bench["ev_to_ebitda"] == found(r"enterprise value to EBITDA ([\d.]+)")
    assert bench["price_to_book"] == found(r"price to book ([\d.]+)")
    assert bench["market_dividend_yield"] == pytest.approx(found(r"market dividend yield ([\d.]+)%") / 100)
    assert "no non-controlling interests, preferred shares or equity-method investments" in text
    assert other["minority_interest"] == other["preferred_stock"] == other["equity_method_investments"] == 0


# --- expected results -----------------------------------------------------------------------------------------


EXPECTED_ROWS = {r[0]: r for r in table_rows(APPENDIX_A) if re.fullmatch(r"[PHDV][1-6]", r[0])}


def test_all_24_checks_are_in_the_fixture_and_in_appendix_a():
    assert set(EXPECTED_ROWS) == set(FIXTURE["expected_checks"])
    assert len(EXPECTED_ROWS) == 24


@pytest.mark.parametrize("check_id", sorted(FIXTURE["expected_checks"]))
def test_each_expected_check_matches_appendix_a(check_id):
    entry = FIXTURE["expected_checks"][check_id]
    _, value_cell, result_cell = EXPECTED_ROWS[check_id]
    assert entry["result"] == result_cell
    cell_numbers = numbers(value_cell)
    assert shown(entry["value"], entry["decimals"]) in cell_numbers, f"{check_id}: {value_cell}"
    if "compared_with" in entry:
        assert any(float(n) == entry["compared_with"] for n in cell_numbers), f"{check_id}: {value_cell}"
    assert entry["owner"] == ("B" if check_id[0] in "PH" else "C")


def test_the_scores_match_appendix_a():
    match = re.search(
        r"past performance (\d) of 6, financial health (\d) of 6, dividend (\d) of 6, valuation (\d) of 6", APPENDIX_A
    )
    assert match
    assert list(FIXTURE["expected_scores"].values()) == [int(g) for g in match.groups()]


def test_the_valuation_working_matches_appendix_a():
    working = plain(APPENDIX_A[APPENDIX_A.index("**Valuation working**") :])
    for name, entry in FIXTURE["expected_valuation"].items():
        if name == "forecast":
            continue
        assert re.search(rf"(?<![\d.]){re.escape(shown(entry['value'], entry['decimals']))}(?![\d])", working), name


def test_the_forecast_table_matches_appendix_a():
    rows = [r for r in table_rows(APPENDIX_A) if r[0] in {"1", "2", "3", "4", "5"}]
    assert len(rows) == 5
    forecast = FIXTURE["expected_valuation"]["forecast"]
    for column, key in enumerate(["revenue", "operating_profit_after_tax", "free_cash_flow", "discounted"], start=1):
        assert forecast[key] == [float(plain(r[column])) for r in rows], key


# --- the loader -----------------------------------------------------------------------------------------------


def test_the_company_is_labelled_synthetic():
    data = synthetic.company_data()
    assert "SYNTHETIC DATA" in data.name


def test_the_loader_converts_millions_to_dollars_and_keeps_the_fiscal_year():
    data = synthetic.company_data()
    revenue = data.fact("revenue", date(2025, 12, 31))
    assert revenue.value == 1_300_000_000.0
    assert revenue.unit == "USD"
    assert revenue.period_start == date(2025, 1, 1)
    assert data.fact("cash", date(2021, 12, 31)).value == 80_000_000.0
    assert data.fact("cash", date(2021, 12, 31)).period_start is None  # a balance at one date
    assert data.fiscal_years("net_income") == [date(y, 12, 31) for y in range(2021, 2026)]


def test_the_loader_adds_shares_and_current_debt_for_the_latest_year():
    data = synthetic.company_data()
    assert data.fact("shares", date(2025, 12, 31)).value == 100_000_000.0
    assert data.fact("shares", date(2025, 12, 31)).unit == "shares"
    assert data.fact("current_financial_debt", date(2025, 12, 31)).value == 50_000_000.0


def test_every_synthetic_fact_says_where_it_comes_from():
    data = synthetic.company_data()
    for by_year in data.items.values():
        for fact in by_year.values():
            assert fact.form == "SYNTHETIC" and "SPEC Appendix A" in fact.note


def test_expected_values_stay_locked_until_the_owner_signs_off(monkeypatch):
    monkeypatch.setitem(FIXTURE["sign_off"], "B", None)
    monkeypatch.setattr(synthetic, "_load", lambda: FIXTURE)
    with pytest.raises(synthetic.NotSignedOff, match="B"):
        synthetic.expected_check("P3")


@pytest.mark.parametrize(
    "owner, call",
    [
        ("C", lambda: synthetic.expected_check("V6")),
        ("C", lambda: synthetic.expected_valuation("cost_of_capital")),
        ("D", synthetic.expected_tier1),
        ("D", synthetic.expected_override),
        ("E", synthetic.expected_scores),
    ],
)
def test_each_owner_s_values_stay_locked_until_they_sign_off(monkeypatch, owner, call):
    monkeypatch.setitem(FIXTURE, "sign_off", {"B": "x", "C": "x", "D": "x", "E": "x", owner: None})
    monkeypatch.setattr(synthetic, "_load", lambda: FIXTURE)
    with pytest.raises(synthetic.NotSignedOff, match=owner):
        call()


def test_there_are_five_sign_offs_counting_a_who_collects_them():
    assert set(FIXTURE["sign_off"]) == {"B", "C", "D", "E"}


def test_the_tier1_and_override_values_match_docs_acceptance():
    acceptance = plain((APP.parent / "docs" / "acceptance.md").read_text(encoding="utf-8"))
    ac3 = next(line for line in acceptance.splitlines() if line.startswith("| AC3 "))
    ac6 = next(line for line in acceptance.splitlines() if line.startswith("| AC6 "))
    tier1 = FIXTURE["expected_tier1"]
    assert "4 passed of 4 assessed" in ac3 and "financial health 4 of 6" in ac3 and "5 passed of 5 assessed" in ac3
    assert tier1["scores"]["past_performance"] == {"passed": 4, "assessed": 4}
    assert tier1["scores"]["financial_health"] == {"passed": 4, "assessed": 6}
    assert tier1["scores"]["dividend"] == {"passed": 5, "assessed": 5}
    assert all(check in ac3 for check in tier1["not_assessed"])
    override = FIXTURE["expected_override"]
    assert f"from {override['cash_from']} to {override['cash_to']}" in ac6
    assert f"= {shown(override['H3']['value'], override['H3']['decimals'])}%" in ac6
    assert f"financial health {override['financial_health_passed']} of 6" in ac6


def test_expected_values_are_available_after_sign_off(monkeypatch):
    monkeypatch.setitem(FIXTURE["sign_off"], "B", "Test Person, 2026-11-19")
    monkeypatch.setattr(synthetic, "_load", lambda: FIXTURE)
    assert synthetic.expected_check("P3")["value"] == 9.375
    assert synthetic.tolerance(synthetic.expected_check("P3")) == pytest.approx(0.0005)
