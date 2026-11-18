"""Tests for the shared data shapes (SPEC §11) and the number rules of SPEC §5.

Owner: A. The expected behaviour comes from SPEC §5.1, §5.2, §5.3.2 and §11, not from the code.
"""

import dataclasses
import math
from datetime import date, datetime

import pytest

from src.contracts import CHECK_IDS, CheckResult, CompanyData, Fact

FY2025 = date(2025, 12, 31)
FY2024 = date(2024, 12, 31)


def reported(metric="revenue", value=1300.0, period_end=FY2025, **overrides):
    fields = dict(
        metric=metric,
        value=value,
        unit="USD",
        period_start=date(period_end.year, 1, 1),
        period_end=period_end,
        kind="reported",
        tag="Revenues",
        form="10-K",
        accession="0000000000-26-000001",
        filed=date(2026, 2, 20),
        retrieved=datetime(2026, 11, 18, 12, 0),
    )
    fields.update(overrides)
    return Fact(**fields)


def missing(metric="revenue", period_end=FY2025, note="not reported in any 10-K"):
    return Fact(
        metric=metric,
        value=None,
        unit="USD",
        period_start=None,
        period_end=period_end,
        kind="missing",
        tag=None,
        form=None,
        accession=None,
        filed=None,
        retrieved=None,
        note=note,
    )


# --- Fact: the four kinds of number (SPEC §5.2) ---------------------------------


def test_a_reported_fact_keeps_every_source_field():
    fact = reported()
    assert fact.value == 1300.0
    assert fact.tag == "Revenues"
    assert fact.accession == "0000000000-26-000001"


def test_missing_is_never_zero():
    with pytest.raises(ValueError, match="never zero"):
        Fact(**{**dataclasses.asdict(missing()), "value": 0.0})


def test_a_missing_fact_needs_a_reason():
    with pytest.raises(ValueError, match="reason"):
        missing(note="")


def test_a_number_that_is_not_missing_needs_a_value():
    with pytest.raises(ValueError, match="kind='missing'"):
        reported(value=None)


@pytest.mark.parametrize("bad", [math.nan, math.inf, -math.inf])
def test_nan_and_infinity_are_rejected_so_missing_data_cannot_hide(bad):
    with pytest.raises(ValueError, match="finite"):
        reported(value=bad)


def test_true_or_false_is_not_a_number():
    with pytest.raises(TypeError):
        reported(value=True)


def test_an_integer_value_is_stored_as_a_float():
    fact = reported(value=1300)
    assert fact.value == 1300.0
    assert isinstance(fact.value, float)


def test_a_derived_fact_records_its_formula():
    with pytest.raises(ValueError, match="formula"):
        reported(kind="derived", tag=None, note="")


def test_an_assumption_says_where_it_comes_from():
    with pytest.raises(ValueError, match="setting or override"):
        reported(kind="assumption", tag=None, note="")


def test_a_reported_fact_names_its_tag():
    with pytest.raises(ValueError, match="tag"):
        reported(tag=None)


def test_an_unknown_kind_is_rejected():
    with pytest.raises(ValueError, match="kind"):
        reported(kind="estimated")


def test_a_period_cannot_start_after_it_ends():
    with pytest.raises(ValueError, match="period"):
        reported(period_start=date(2026, 1, 1), period_end=FY2025)


def test_facts_cannot_be_changed_after_creation():
    fact = reported()
    with pytest.raises(dataclasses.FrozenInstanceError):
        fact.value = 0.0


# --- CheckResult ----------------------------------------------------------------


def test_there_are_exactly_24_check_ids():
    assert len(CHECK_IDS) == 24
    assert CHECK_IDS[0] == "P1" and CHECK_IDS[-1] == "V6"


def test_a_check_result_accepts_a_known_check_and_status():
    result = CheckResult("H6", "pass", 8.0, 5.0, (reported(),), "Interest covered 8.0 times")
    assert result.status == "pass"


@pytest.mark.parametrize("check_id", ["P7", "X1", "p1", ""])
def test_an_unknown_check_id_is_rejected(check_id):
    with pytest.raises(ValueError, match="check id"):
        CheckResult(check_id, "pass", None, None, (), "text")


def test_an_unknown_status_is_rejected():
    with pytest.raises(ValueError, match="status"):
        CheckResult("P1", "not assessed", None, None, (), "text")


def test_inputs_given_as_a_list_are_stored_as_a_tuple():
    result = CheckResult("P1", "pass", None, None, [reported()], "text")
    assert isinstance(result.inputs, tuple)


def test_inputs_must_be_facts():
    with pytest.raises(TypeError):
        CheckResult("P1", "pass", None, None, (1300.0,), "text")


def test_a_check_result_explains_itself():
    with pytest.raises(ValueError, match="explanation"):
        CheckResult("P1", "pass", None, None, (), "  ")


# --- CompanyData: per line item, fiscal-year end date → Fact (SPEC §11) ----------


def company(items):
    return CompanyData(
        ticker="SYN",
        cik="0000000001",
        name="Synthetic Co. (SYNTHETIC DATA)",
        sic="2080",
        sic_description="Beverages",
        fiscal_year_end="1231",
        latest_10k_filed=date(2026, 2, 20),
        retrieved=datetime(2026, 11, 18, 12, 0),
        items=items,
    )


def test_a_fact_is_found_by_line_item_and_fiscal_year_end():
    fact = reported()
    data = company({"revenue": {FY2025: fact}})
    assert data.fact("revenue", FY2025) is fact
    assert data.fact("revenue", FY2024) is None
    assert data.fact("net_income", FY2025) is None


def test_fiscal_years_are_listed_oldest_first():
    data = company({"revenue": {FY2025: reported(), FY2024: reported(period_end=FY2024)}})
    assert data.fiscal_years("revenue") == [FY2024, FY2025]


def test_a_fact_filed_under_the_wrong_fiscal_year_is_rejected():
    # SPEC §5.3.2: the fiscal year comes from the period end date, never from a label.
    with pytest.raises(ValueError, match="fiscal year"):
        company({"revenue": {FY2024: reported(period_end=FY2025)}})


def test_a_fact_filed_under_the_wrong_line_item_is_rejected():
    with pytest.raises(ValueError, match="line item"):
        company({"net_income": {FY2025: reported(metric="revenue")}})


@pytest.mark.parametrize("cik", ["21344", "00000213445", "CIK0000021344"])
def test_the_company_number_has_ten_digits(cik):
    with pytest.raises(ValueError, match="10 digits"):
        CompanyData("KO", cik, "The Coca-Cola Company", None, None, None, None, None, {})


def test_company_data_cannot_be_changed_in_place():
    data = company({"revenue": {FY2025: reported()}})
    with pytest.raises(TypeError):
        data.items["revenue"][FY2025] = missing()
    with pytest.raises(TypeError):
        data.items["cash"] = {}


def test_an_override_returns_new_company_data_and_keeps_the_original():
    original = reported(value=120.0, metric="cash", tag="CashAndCashEquivalentsAtCarryingValue")
    data = company({"cash": {FY2025: original}})
    override = Fact(
        **{**dataclasses.asdict(original), "value": 140.0, "kind": "assumption", "note": "user override"}
    )
    changed = data.with_fact(override)
    assert changed.fact("cash", FY2025).value == 140.0
    assert data.fact("cash", FY2025).value == 120.0
