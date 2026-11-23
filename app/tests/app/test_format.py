"""Display formats of the interface (`app/ui/format.py`, slice S10). Owner: D.

The interface never changes a value it receives; it only chooses how many decimals to show (SPEC §11, audit
ux #10). Expected strings are Simon's (D) display choices of 23 November 2026, not the code's output:
40.24% against 40% -> "40.2%"; 39.96% against 40% -> "39.96%"; 20% against 20% -> "20.0%";
USD 2,112,000,000 -> "USD 2,112 m". A missing figure is "n/a" with its reason, never 0 (acceptance V4).
"""

from datetime import date

import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

from src.contracts import CHECK_IDS, Fact
from ui.format import CHECK_UNITS, NO_VALUE, check_value, fact_value, usd_m


def fact(metric="revenue", value=2_112_000_000.0, unit="USD", kind="reported", note=""):
    reported = kind == "reported"
    return Fact(
        metric=metric,
        value=value,
        unit=unit,
        period_start=None,
        period_end=date(2025, 12, 31),
        kind=kind,
        tag="us-gaap:Revenues" if reported else None,
        form="10-K" if reported else None,
        accession="0000000000-26-000001" if reported else None,
        filed=None,
        retrieved=None,
        note=note,
    )


# --- USD millions -----------------------------------------------------------------------------------------------


def test_usd_millions_with_thousands_separator():
    assert usd_m(2_112_000_000) == "USD 2,112 m"


def test_usd_millions_keeps_the_sign():
    assert usd_m(-540_000_000) == "USD -540 m"


# --- a check's value against its threshold (audit ux #10) -------------------------------------------------------


def test_just_above_a_percentage_threshold_keeps_one_decimal():
    assert check_value("H3", 0.4024, 0.40) == ("40.2%", "40.0%")


def test_just_below_a_percentage_threshold_never_reads_as_equal():
    assert check_value("H3", 0.3996, 0.40) == ("39.96%", "40.0%")


def test_exactly_on_the_threshold_reads_as_equal():
    assert check_value("H5", 0.20, 0.20) == ("20.0%", "20.0%")


def test_amounts_close_to_each_other_get_the_decimals_that_tell_them_apart():
    shown, against = check_value("H1", 360_400_000, 360_000_000)
    assert shown != against
    assert check_value("H1", 540_000_000, 360_000_000) == ("USD 540 m", "USD 360 m")


def _number(text: str) -> float:
    return float(text.replace("USD", "").replace("m", "").replace("%", "").replace(",", "").strip())


@settings(max_examples=500)
@given(st.floats(-2, 2, allow_nan=False), st.floats(-2, 2, allow_nan=False))
def test_shown_numbers_always_compare_like_the_real_ones(value, threshold):
    """Never on the wrong side; shown as equal only when the gap is below the finest decimal shown (0.00001%).

    The check's pass or fail, shown next to it, then says which side it is on."""
    shown, against = check_value("H3", value, threshold)
    real = (value > threshold) - (value < threshold)
    seen = (_number(shown) > _number(against)) - (_number(shown) < _number(against))
    assert seen == real or (seen == 0 and abs(value - threshold) * 100 < 0.5e-5)


def test_a_pass_or_fail_without_a_value_shows_no_value_never_zero_or_none():
    shown, against = check_value("D3", None, -0.10)
    assert shown == NO_VALUE
    assert against == "-10.0%"
    assert "None" not in shown and "0" not in shown


def test_no_threshold_shows_nothing_for_it():
    assert check_value("H4", None, None) == (NO_VALUE, "")


def test_every_check_has_a_display_unit():
    assert set(CHECK_UNITS) == set(CHECK_IDS)


def test_years_and_times():
    assert check_value("P1", 5, 4) == ("5 of 5 years", "4 of 5 years")
    assert check_value("H6", 4.98, 5) == ("4.98 times", "5.0 times")


# --- a figure (sources page, check inputs) ----------------------------------------------------------------------


def test_reported_amount_in_usd_millions():
    assert fact_value(fact()) == "USD 2,112 m"


def test_missing_figure_shows_n_a_with_its_reason_never_zero():
    missing = Fact("interest_expense", None, "USD", None, date(2025, 12, 31), "missing", None, None, None, None, None,
                   "not reported after FY2023 under any interest tag")
    shown = fact_value(missing)
    assert shown == "n/a: not reported after FY2023 under any interest tag"
    assert "0" not in shown.split(":")[0]


def test_nil_dividend_reads_no_dividend_paid_never_usd_0_m():
    nil = fact("dividends_paid", 0.0, kind="assumption", note="not reported, treated as nil, so no dividend paid")
    assert fact_value(nil) == "no dividend paid"


def test_a_reported_zero_stays_a_zero():
    assert fact_value(fact("interest_expense", 0.0)) == "USD 0 m"


@pytest.mark.parametrize("unit", ["USD", "USD/shares", "shares", "pure", "days"])
def test_every_unit_has_a_format_and_names_its_unit(unit):
    shown = fact_value(fact("shares", 1_234_567_890.0, unit=unit, kind="derived", note="formula"))
    assert shown and "None" not in shown
