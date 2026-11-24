"""Reading the typed share price (`app/ui/inputs.py`, SPEC §3 item 1, issue #32 point 1; slice S10). Owner: D.

Expected results and messages are Simon's (D), 23 November 2026. At most two decimals, after a point or a comma:
"1,234" and "1.234" could each be 1234 or 1.234 dollars (in France "1.234" means 1234), so both are refused
instead of guessed. Simon's look at the app: "1.234" had been read as USD 1.23 (fixed the same day).
"""

import pytest

from ui.inputs import PriceError, parse_price

HOW = "Type the price in US dollars, e.g. 1234 or 182.50"
POSITIVE = "The price must be greater than 0. " + HOW


@pytest.mark.parametrize("typed, price", [
    ("182.50", 182.50),
    ("182,50", 182.50),
    ("182,5", 182.5),
    ("182", 182.0),
    (" 182.50 ", 182.50),
    ("182.5", 182.5),
    ("1234", 1234.0),
])
def test_accepted_prices(typed, price):
    assert parse_price(typed) == price


def test_empty_means_no_price_not_an_error():
    assert parse_price("") is None
    assert parse_price("   ") is None


@pytest.mark.parametrize("typed", ["1,234.50", "1,234", "1.234", "182.555"])
def test_ambiguous_thousands_are_refused(typed):
    with pytest.raises(PriceError) as refused:
        parse_price(typed)
    assert str(refused.value) == HOW


@pytest.mark.parametrize("typed", ["0", "-5"])
def test_zero_or_negative_is_refused(typed):
    with pytest.raises(PriceError) as refused:
        parse_price(typed)
    assert str(refused.value) == POSITIVE


def test_not_a_number_is_refused():
    with pytest.raises(PriceError) as refused:
        parse_price("abc")
    assert str(refused.value) == HOW
