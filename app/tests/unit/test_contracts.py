"""Tests for the shared data shapes (SPEC §11) and the number rules of SPEC §5.

Owner: A. The expected behaviour comes from SPEC §5.1, §5.2, §5.3.2, §7 and §11, not from the code.
"""

import copy
import dataclasses
import math
import pickle
from datetime import date, datetime

import numpy as np
import pytest

from src.contracts import CHECK_IDS, LINE_ITEMS, UNITS, CheckResult, CompanyData, Fact

FY2025 = date(2025, 12, 31)
FY2024 = date(2024, 12, 31)


def reported(metric="revenue", value=1300.0, period_end=FY2025, **overrides):
    fields = dict(
        metric=metric,
        value=value,
        unit="USD",
        period_start=date(period_end.year, 1, 1) if isinstance(period_end, date) else None,
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


def missing(metric="revenue", period_end=FY2025, note="not reported in any 10-K", **overrides):
    fields = dict(
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
    fields.update(overrides)
    return Fact(**fields)


# --- Fact: the four kinds of number (SPEC §5.2) ---------------------------------------------------------------


def test_a_reported_fact_keeps_every_source_field():
    fact = reported()
    assert fact.value == 1300.0
    assert fact.tag == "Revenues"
    assert fact.accession == "0000000000-26-000001"


@pytest.mark.parametrize("value", [0.0, 0, 1300.0])
def test_missing_never_carries_a_value_not_even_zero(value):
    with pytest.raises(ValueError, match="never zero"):
        missing(value=value)


def test_a_missing_fact_needs_a_reason():
    with pytest.raises(ValueError, match="reason"):
        missing(note="")


def test_a_number_that_is_not_missing_needs_a_value():
    with pytest.raises(ValueError, match="kind='missing'"):
        reported(value=None)


@pytest.mark.parametrize("bad", [math.nan, math.inf, -math.inf, np.nan])
def test_nan_and_infinity_are_rejected_so_missing_data_cannot_hide(bad):
    with pytest.raises(ValueError, match="finite"):
        reported(value=bad)


@pytest.mark.parametrize("bad", [True, "1300", [1300]])
def test_true_false_text_and_lists_are_not_numbers(bad):
    with pytest.raises(TypeError):
        reported(value=bad)


@pytest.mark.parametrize("value", [1300, np.int64(1300), np.float64(1300.0)])
def test_integers_and_numpy_numbers_are_stored_as_plain_floats(value):
    fact = reported(value=value)
    assert fact.value == 1300.0
    assert type(fact.value) is float


def test_a_valid_derived_fact_is_accepted():
    fact = reported(kind="derived", tag=None, form=None, accession=None, note="revenue − cost of revenue")
    assert fact.kind == "derived"


def test_a_derived_fact_records_its_formula():
    with pytest.raises(ValueError, match="formula"):
        reported(kind="derived", tag=None, note="")


def test_a_valid_assumption_is_accepted():
    fact = reported(kind="assumption", tag=None, form=None, accession=None, note="user override")
    assert fact.kind == "assumption"


def test_an_assumption_says_where_it_comes_from():
    with pytest.raises(ValueError, match="setting or override"):
        reported(kind="assumption", tag=None, note="")


@pytest.mark.parametrize("field", ["tag", "form", "accession"])
def test_a_reported_fact_names_its_tag_form_and_accession(field):
    # SPEC §5.1: every number carries its source. Non-SEC sources put their name in `form` (e.g. "SYNTHETIC").
    with pytest.raises(ValueError, match=field):
        reported(**{field: ""})


@pytest.mark.parametrize("unit", ["", "USD m", "USD millions", "EUR", "%"])
def test_only_units_as_filed_are_accepted(unit):
    # SPEC §5.3.5 and §5.4: amounts stay in USD as filed; "dollars read as millions" must not be storable.
    with pytest.raises(ValueError, match="unit"):
        reported(unit=unit)


def test_the_accepted_units_are_listed():
    assert UNITS == ("USD", "USD/shares", "shares", "pure", "days")


def test_an_unknown_kind_is_rejected():
    with pytest.raises(ValueError, match="kind"):
        reported(kind="estimated")


def test_a_period_cannot_start_after_it_ends():
    with pytest.raises(ValueError, match="period"):
        reported(period_start=date(2026, 1, 1), period_end=FY2025)


@pytest.mark.parametrize("bad", ["2025-12-31", datetime(2025, 12, 31)])
def test_period_dates_are_dates(bad):
    with pytest.raises(TypeError, match="date"):
        reported(period_end=bad, period_start=None)
    with pytest.raises(TypeError, match="date"):
        reported(period_start=bad)


def test_the_filing_date_is_a_date_and_the_retrieval_time_a_datetime():
    with pytest.raises(TypeError, match="filed"):
        reported(filed="2026-02-20")
    with pytest.raises(TypeError, match="retrieved"):
        reported(retrieved=date(2026, 11, 18))


def test_facts_cannot_be_changed_after_creation():
    fact = reported()
    with pytest.raises(dataclasses.FrozenInstanceError):
        fact.value = 0.0


# --- CheckResult ------------------------------------------------------------------------------------------------


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
    # "Not assessed" (SPEC §2) is shown for insufficient_data; it is not a separate status (SPEC §11).
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


@pytest.mark.parametrize("bad", [math.nan, math.inf, np.float64("inf")])
def test_a_check_value_or_threshold_is_finite(bad):
    with pytest.raises(ValueError, match="finite"):
        CheckResult("H6", "pass", bad, 5.0, (), "text")
    with pytest.raises(ValueError, match="finite"):
        CheckResult("H6", "pass", 8.0, bad, (), "text")


@pytest.mark.parametrize("status", ["pass", "fail"])
def test_a_check_with_a_missing_input_cannot_pass_or_fail(status):
    # SPEC §7: an input is missing → insufficient data.
    with pytest.raises(ValueError, match="insufficient_data"):
        CheckResult("H3", status, 0.378, 0.40, (reported(), missing()), "text")


@pytest.mark.parametrize("status", ["insufficient_data", "not_applicable"])
def test_a_check_that_was_not_assessed_has_no_value(status):
    with pytest.raises(ValueError, match="no value"):
        CheckResult("D2", status, 0.0187, None, (missing(),), "text")


def test_insufficient_data_with_a_missing_input_is_accepted():
    result = CheckResult("P4", "insufficient_data", None, None, (missing(),), "Not assessed: needs a benchmark")
    assert result.value is None


# --- CompanyData: per line item, fiscal-year end date → Fact (SPEC §11) ----------------------------------------


def company(items, warnings=()):
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
        warnings=warnings,
    )


def test_the_line_items_follow_spec_section_6():
    assert LINE_ITEMS[:3] == ("revenue", "cost_of_revenue", "gross_profit")
    assert {"financial_debt", "current_financial_debt", "dividends_paid", "shares"} <= set(LINE_ITEMS)
    assert len(LINE_ITEMS) == len(set(LINE_ITEMS))


def test_an_unknown_line_item_is_rejected():
    with pytest.raises(ValueError, match="line item"):
        company({"netIncome": {FY2025: reported(metric="netIncome")}})


def test_a_fact_is_found_by_line_item_and_fiscal_year_end():
    fact = reported()
    data = company({"revenue": {FY2025: fact}})
    assert data.fact("revenue", FY2025) is fact
    assert data.fact("revenue", FY2024) is None
    assert data.fact("net_income", FY2025) is None


def test_latest_gives_the_fact_at_the_latest_date_of_a_line_item():
    # Shares are stored at their cover-page date, a few weeks after the fiscal year end.
    shares = reported(metric="shares", value=4_300_000_000, unit="shares", period_start=None,
                      period_end=date(2026, 2, 18), tag="dei:EntityCommonStockSharesOutstanding")
    data = company({"revenue": {FY2025: reported(), FY2024: reported(period_end=FY2024)},
                    "shares": {date(2026, 2, 18): shares}})
    assert data.latest("shares") is shares
    assert data.latest("revenue").period_end == FY2025
    assert data.latest("cash") is None


def test_fiscal_years_are_listed_oldest_first():
    data = company({"revenue": {FY2025: reported(), FY2024: reported(period_end=FY2024)}})
    assert data.fiscal_years("revenue") == [FY2024, FY2025]


def test_a_fact_stored_under_another_fiscal_year_end_is_rejected():
    # The key must equal the fact's own period end date. (That the period end, not the `fy` label, decides the
    # fiscal year in the first place — SPEC §5.3.2 — is tested in the resolver, slice S2.)
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
    with pytest.raises(TypeError):
        data.items["revenue"].clear()


def test_changing_the_source_dict_later_does_not_change_company_data():
    source = {"revenue": {FY2025: reported()}}
    data = company(source)
    source["revenue"][FY2024] = reported(period_end=FY2024)
    source["cash"] = {}
    assert data.fiscal_years("revenue") == [FY2025]
    assert "cash" not in data.items


def test_company_data_can_be_cached_copied_and_exported():
    # Streamlit's st.cache_data pickles return values; the export and sources page use dataclasses.asdict.
    data = company({"revenue": {FY2025: reported()}}, warnings=("negative equity",))
    for clone in (pickle.loads(pickle.dumps(data)), copy.deepcopy(data)):
        assert clone == data
        with pytest.raises(TypeError):
            clone.items["cash"] = {}
    assert dataclasses.asdict(data)["items"]["revenue"][FY2025]["value"] == 1300.0


def test_an_override_changes_one_fact_and_keeps_everything_else():
    cash_2024 = reported(metric="cash", value=100.0, period_end=FY2024, period_start=None, tag="Cash")
    cash_2025 = reported(metric="cash", value=120.0, period_start=None, tag="Cash")
    debt_2025 = reported(metric="financial_debt", value=450.0, period_start=None, tag="LongTermDebt")
    data = company({"cash": {FY2024: cash_2024, FY2025: cash_2025}, "financial_debt": {FY2025: debt_2025}},
                   warnings=("negative equity",))
    override = dataclasses.replace(cash_2025, value=140.0, kind="assumption", note="user override, was 120")

    changed = data.with_fact(override)

    assert changed.fact("cash", FY2025).value == 140.0
    assert changed.fact("cash", FY2025).kind == "assumption"
    assert changed.fact("cash", FY2024) is cash_2024
    assert changed.fact("financial_debt", FY2025) is debt_2025
    assert (changed.ticker, changed.cik, changed.name, changed.warnings) == (data.ticker, data.cik, data.name,
                                                                             data.warnings)
    assert data.fact("cash", FY2025) is cash_2025  # the original is unchanged
    with pytest.raises(TypeError):
        changed.items["cash"][FY2025] = cash_2025
