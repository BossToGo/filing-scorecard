"""Reading what the user types (SPEC §3 item 1; issue #32 point 1). Owner: D.

The share price is the only figure the user types. "182.50" and "182,50" are both read as USD 182.50; a comma is a
decimal point only when one or two digits follow it, so "1,234" (1234 or 1.234 dollars?) is refused, never guessed.
"""

from __future__ import annotations

import re

HOW = "Type the price in US dollars, e.g. 1234 or 182.50"
_NUMBER = re.compile(r"-?\d+(?:\.\d+)?")
_DECIMAL_COMMA = re.compile(r"-?\d+,\d{1,2}")


class PriceError(ValueError):
    """The typed price cannot be used; the message says how to type it."""


def parse_price(typed: str) -> float | None:
    """The typed share price in USD, or None when nothing was typed (then the price checks are not assessed)."""
    text = typed.strip()
    if not text:
        return None
    if "," in text:
        if "." in text or not _DECIMAL_COMMA.fullmatch(text):
            raise PriceError(HOW)
        text = text.replace(",", ".")
    if not _NUMBER.fullmatch(text):
        raise PriceError(HOW)
    price = float(text)
    if price <= 0:
        raise PriceError(f"The price must be greater than 0. {HOW}")
    return price
