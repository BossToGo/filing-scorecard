"""Reading what the user types (SPEC §3 item 1; issue #32 point 1). Owner: D.

The share price is the only figure the user types. "182.50" and "182,50" are both read as USD 182.50. At most two
decimals, after a point or a comma: "1,234" and "1.234" (1234 or 1.234 dollars? in France "1.234" means 1234) are
refused, never guessed.
"""

from __future__ import annotations

import re

HOW = "Type the price in US dollars, e.g. 1234 or 182.50"
_PRICE = re.compile(r"-?\d+(?:[.,]\d{1,2})?")


class PriceError(ValueError):
    """The typed price cannot be used; the message says how to type it."""


def parse_price(typed: str) -> float | None:
    """The typed share price in USD, or None when nothing was typed (then the price checks are not assessed)."""
    text = typed.strip()
    if not text:
        return None
    if not _PRICE.fullmatch(text):
        raise PriceError(HOW)
    price = float(text.replace(",", "."))
    if price <= 0:
        raise PriceError(f"The price must be greater than 0. {HOW}")
    return price
