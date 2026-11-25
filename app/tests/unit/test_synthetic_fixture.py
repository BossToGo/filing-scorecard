"""The synthetic company fixture is a faithful copy of SPEC.md Appendix A (version 2.3, equity method), and its
expected values stay locked until their owner signs off (SPEC rule 14.5). Owner: A (slice S0c).

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
    "Depreciation and amortisation (not used since version 2.3)": "depreciation_amortization",
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

    def found(pattern, group=1):
        match = re.search(pattern, text)
        assert match, pattern
        return float(match.group(group))

    other, settings, bench = FIXTURE["other_inputs"], FIXTURE["settings"], FIXTURE["benchmarks"]
    assert other["current_financial_debt_fy2025"] == found(r"current financial debt FY2025 = (\d+)")
    assert other["shares_millions"] == found(r"shares = (\d+) million")
    assert other["share_price_usd"] == found(r"share price = USD ([\d.]+)")
    assert settings["risk_free_rate"] == pytest.approx(found(r"risk-free rate ([\d.]+)%") / 100)
    assert settings["equity_risk_premium"] == pytest.approx(found(r"equity risk premium ([\d.]+)%") / 100)
    assert settings["tax_rate"] == pytest.approx(found(r"tax rate ([\d.]+)%") / 100)
    assert settings["terminal_growth"] == pytest.approx(found(r"terminal growth ([\d.]+)%") / 100)
    assert settings["fcf_base_years"] == 3 and "free cash flow margin over the last three fiscal years" in text
    limits = r"starting growth limited to (-?[\d.]+)% to \+([\d.]+)%"
    assert settings["growth_floor"] == pytest.approx(found(limits) / 100)
    assert settings["growth_cap"] == pytest.approx(found(limits, 2) / 100)
    decay = r"half-life of (\d+) years over (\d+) years"
    assert settings["growth_half_life_years"] == found(decay) and settings["forecast_years"] == found(decay, 2)
    beta = r"beta limited to ([\d.]+) to ([\d.]+)"
    assert settings["beta_min"] == found(beta) and settings["beta_max"] == found(beta, 2)
    assert set(settings) == {"risk_free_rate", "equity_risk_premium", "tax_rate", "terminal_growth", "fcf_base_years",
                             "growth_floor", "growth_cap", "growth_half_life_years", "forecast_years", "beta_min",
                             "beta_max"}
    assert bench["unlevered_beta"] == found(r"unlevered beta ([\d.]+)")
    assert bench["return_on_equity"] == pytest.approx(found(r"return on equity ([\d.]+)%") / 100)
    assert bench["operating_margin"] == pytest.approx(found(r"operating margin ([\d.]+)%") / 100)
    earnings = r"price to earnings ([\d.]+) \(industry\) and ([\d.]+) \(whole US market\)"
    assert bench["price_to_earnings"] == found(earnings) and bench["market_price_to_earnings"] == found(earnings, 2)
    assert bench["price_to_book"] == found(r"price to book ([\d.]+)")
    assert bench["market_dividend_yield"] == pytest.approx(found(r"market dividend yield ([\d.]+)%") / 100)
    assert set(bench) == {"unlevered_beta", "return_on_equity", "operating_margin", "price_to_earnings",
                          "market_price_to_earnings", "price_to_book", "market_dividend_yield"}  # no EV/EBITDA (v2.3)
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


WORKING = plain(APPENDIX_A[APPENDIX_A.index("**Valuation working"):APPENDIX_A.index("**Strengths and points to watch")])


def test_the_valuation_working_matches_appendix_a():
    for name, entry in FIXTURE["expected_valuation"].items():
        if name in ("forecast", "base_free_cash_flows", "model_fits"):
            continue
        assert re.search(rf"(?<![\d.]){re.escape(shown(entry['value'], entry['decimals']))}(?![\d])", WORKING), name


def test_the_base_years_and_the_model_fit_match_appendix_a():
    valuation = FIXTURE["expected_valuation"]
    assert valuation["base_free_cash_flows"]["values"] == [75, 115, 130]
    assert "150 - 75 = 75; 195 - 80 = 115; 215 - 85 = 130" in WORKING
    assert valuation["model_fits"]["value"] is True and "The model fits" in WORKING
    assert "no fair value" not in WORKING


def test_the_forecast_table_matches_appendix_a():
    rows = [r for r in table_rows(APPENDIX_A) if r[0] in {str(year) for year in range(1, 11)}]
    assert [r[0] for r in rows] == [str(year) for year in range(1, 11)]
    forecast = FIXTURE["expected_valuation"]["forecast"]
    assert forecast["growth"] == [float(plain(r[1]).rstrip("%")) for r in rows]
    for column, key in enumerate(["free_cash_flow", "discounted"], start=2):
        assert forecast[key] == [float(plain(r[column])) for r in rows], key


def test_the_valuation_rows_agree_with_each_other():
    # Arithmetic on the figures shown, with the rounding they are shown at: a copying slip between rows fails here.
    checks, valuation = FIXTURE["expected_checks"], FIXTURE["expected_valuation"]
    fair_value = valuation["fair_value_per_share"]["value"]
    assert checks["V1"]["compared_with"] == fair_value
    assert checks["V2"]["compared_with"] == pytest.approx(0.8 * fair_value, abs=0.005)
    assert checks["V6"]["compared_with"] == valuation["fair_value_at_growth_cap"]["value"]
    assert checks["V3"]["value"] == checks["V4"]["value"]  # the same price to earnings, two benchmarks
    shares = FIXTURE["other_inputs"]["shares_millions"]
    assert valuation["equity_value"]["value"] / shares == pytest.approx(fair_value, abs=0.005)
    assert sum(valuation["forecast"]["discounted"]) == pytest.approx(
        valuation["sum_of_discounted_cash_flows"]["value"], abs=0.05)  # ten values rounded to 0.01


STATEMENT_ROWS = [r for r in table_rows(APPENDIX_A) if re.fullmatch(r"[GW]\d(, [GW]\d)*", r[0])]


def test_the_strengths_and_points_to_watch_match_appendix_a():
    in_spec = {key: cells[1] == "yes" for cells in STATEMENT_ROWS for key in cells[0].split(", ")}
    statements = {k: v for k, v in FIXTURE["expected_statements"].items() if k != "overview"}
    assert sorted(in_spec) == [f"G{n}" for n in range(1, 8)] + [f"W{n}" for n in range(1, 9)]  # 15 statements
    assert all(cells[1] in ("yes", "no") for cells in STATEMENT_ROWS)
    assert {key: entry["shown"] for key, entry in statements.items()} == in_spec
    why = {key: plain(cells[2]) for cells in STATEMENT_ROWS for key in cells[0].split(", ")}
    for key, entry in statements.items():
        if "value" in entry:
            assert shown(entry["value"], entry["decimals"]) + "%" in why[key], key


def test_the_overview_matches_appendix_a_and_the_statements():
    match = re.search(r"Overview: strengths ([GW\d, ]+); points to watch ([GW\d, ]+) \(", APPENDIX_A)
    assert match
    overview = FIXTURE["expected_statements"]["overview"]
    assert overview["strengths"] == match.group(1).split(", ")
    assert overview["points_to_watch"] == match.group(2).split(", ")
    shown_now = [k for k, v in FIXTURE["expected_statements"].items() if k != "overview" and v["shown"]]
    assert sorted(overview["strengths"] + overview["points_to_watch"]) == sorted(shown_now)


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
        ("B", lambda: synthetic.expected_check("H3")),
        ("B", synthetic.expected_statements),
        ("C", lambda: synthetic.expected_check("V6")),
        ("C", lambda: synthetic.expected_valuation("cost_of_equity")),
        ("D", synthetic.expected_tier1),
        ("E", synthetic.expected_scores),
    ],
)
def test_each_owner_s_values_stay_locked_until_they_sign_off(monkeypatch, owner, call):
    monkeypatch.setitem(FIXTURE, "sign_off", {"B": "x", "C": "x", "D": "x", "E": "x", owner: None})
    monkeypatch.setattr(synthetic, "_load", lambda: FIXTURE)
    with pytest.raises(synthetic.NotSignedOff, match=owner):
        call()


def test_there_are_five_sign_offs_counting_a_who_collects_them():
    # Rule 14.6, agreed by Igor on 24 November 2026: B's sign-off of that day covers CALC-P1–P6 and CALC-H1–H6 only,
    # so the strengths and points to watch (CALC-G, also B's) get their own record, B_statements, and stay locked
    # until B checks them. Before, one record "B" unlocked all three.
    assert set(FIXTURE["sign_off"]) == {"B", "B_statements", "C", "D", "E"}


def test_a_recorded_sign_off_names_the_person_the_date_and_the_comment_on_the_pull_request():
    for owner, record in FIXTURE["sign_off"].items():
        if record is not None:  # None: that owner's values stay locked
            assert re.fullmatch(r"[A-Z][\w .'-]+, 20\d\d-\d\d-\d\d.*, https://github\.com/BossToGo/filing-scorecard/"
                                r"pull/5#pullrequestreview-\d+", record), owner


def test_the_override_of_version_2_2_is_gone():
    # SPEC v2.3: the share price is the only input, so no figure can be overridden (docs/acceptance.md AC6).
    assert "expected_override" not in FIXTURE and not hasattr(synthetic, "expected_override")


def test_the_tier1_values_match_docs_acceptance():
    acceptance = plain((APP.parent / "docs" / "acceptance.md").read_text(encoding="utf-8"))
    ac3 = next(line for line in acceptance.splitlines() if line.startswith("| AC3 "))
    tier1 = FIXTURE["expected_tier1"]
    assert "4 passed of 4 assessed" in ac3 and "financial health 4 of 6" in ac3 and "5 passed of 5 assessed" in ac3
    assert tier1["scores"]["past_performance"] == {"passed": 4, "assessed": 4}
    assert tier1["scores"]["financial_health"] == {"passed": 4, "assessed": 6}
    assert tier1["scores"]["dividend"] == {"passed": 5, "assessed": 5}
    assert all(check in ac3 for check in tier1["not_assessed"])


def test_expected_values_are_available_after_sign_off(monkeypatch):
    monkeypatch.setitem(FIXTURE["sign_off"], "B", "Test Person, 2026-11-19")
    monkeypatch.setattr(synthetic, "_load", lambda: FIXTURE)
    assert synthetic.expected_check("P3")["value"] == 9.375
    assert synthetic.tolerance(synthetic.expected_check("P3")) == pytest.approx(0.0005)


def test_the_statements_stay_locked_after_b_signs_off_only_the_p_and_h_rows(monkeypatch):
    monkeypatch.setitem(FIXTURE["sign_off"], "B", "Test Person, 2026-11-24")
    monkeypatch.setitem(FIXTURE["sign_off"], "B_statements", None)
    monkeypatch.setattr(synthetic, "_load", lambda: FIXTURE)
    assert synthetic.expected_check("P3")["value"] == 9.375
    with pytest.raises(synthetic.NotSignedOff, match="strengths and points to watch"):
        synthetic.expected_statements()


def test_the_statements_are_handed_out_after_b_signs_off(monkeypatch):
    # Rule 14.6, agreed by Igor on 24 November 2026: the statements now need their own record, B_statements
    # (see test_there_are_five_sign_offs_counting_a_who_collects_them); before, B's record alone handed them out.
    monkeypatch.setitem(FIXTURE["sign_off"], "B", "Test Person, 2026-11-22")
    monkeypatch.setitem(FIXTURE["sign_off"], "B_statements", "Test Person, 2026-11-22")
    monkeypatch.setattr(synthetic, "_load", lambda: FIXTURE)
    statements = synthetic.expected_statements()
    assert statements["W8"] == {"shown": True, "value": 49.0, "unit": "%", "decimals": 1}
    assert statements["overview"]["points_to_watch"] == ["W3", "W4", "W8"]
