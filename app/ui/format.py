"""How numbers are written on screen (SPEC §3, §11; audit ux #10). Owner: D.

The interface never changes a value it receives. These functions only choose how many decimals to show, and show
enough of them that a value never looks equal to, or on the other side of, the threshold it is compared with:
39.96% against a 40% limit reads "39.96%", never "40.0%". Amounts arrive in USD and are shown in USD millions.
A missing figure reads "n/a" with its reason, never 0 (acceptance V4).
"""

from __future__ import annotations

from dataclasses import dataclass

from src.contracts import Fact

NO_VALUE = "no value"  # a pass or fail that comes without a number (e.g. D3 with no cut at all)
NIL_DIVIDEND = "no dividend paid"  # dividends "not reported, treated as nil" (SPEC §7, plan Q1)
EXTRA_DECIMALS = 4  # at most this many decimals beyond the default, to tell a value from its threshold


@dataclass(frozen=True)
class _Style:
    scale: float  # from the stored unit to the shown unit (USD -> USD m, decimal -> percent)
    decimals: int  # default number of decimals
    template: str  # where the number goes


STYLES = {
    "usd": _Style(1e-6, 0, "USD {} m"),
    "percent": _Style(100.0, 1, "{}%"),
    "times": _Style(1.0, 1, "{} times"),
    "years": _Style(1.0, 0, "{} of 5 years"),
    "usd_per_share": _Style(1.0, 2, "USD {} per share"),
}

# What `CheckResult.value` and `.threshold` hold for each check, read from the check modules (B: PRs #28 and #29;
# C: PR #23). Ratios arrive as decimals (0.4024), amounts in USD. V1-V6 are provisional until C's S9 (v0.2).
CHECK_UNITS = {
    "P1": "years", "P2": "usd", "P3": "percent", "P4": "percent", "P5": "percent", "P6": "percent",
    "H1": "usd", "H2": "usd", "H3": "percent", "H4": "percent", "H5": "percent", "H6": "times",
    "D1": "usd", "D2": "percent", "D3": "percent", "D4": "usd", "D5": "percent", "D6": "usd",
    "V1": "usd_per_share", "V2": "usd_per_share", "V3": "times", "V4": "times", "V5": "times",
    "V6": "usd_per_share",
}


def _write(number: float, style: _Style, decimals: int) -> str:
    text = f"{number * style.scale:,.{decimals}f}"
    if text.lstrip("-").strip("0.,") == "":  # "-0.0" -> "0.0"
        text = text.lstrip("-")
    return style.template.format(text)


def _sign(a: float, b: float) -> int:
    return (a > b) - (a < b)


def _decimals(value: float, threshold: float, style: _Style) -> int:
    """The fewest decimals (from the default) at which the shown numbers compare like the real ones."""
    for decimals in range(style.decimals, style.decimals + EXTRA_DECIMALS + 1):
        shown = round(value * style.scale, decimals), round(threshold * style.scale, decimals)
        if _sign(*shown) == _sign(value, threshold):
            return decimals
    return style.decimals + EXTRA_DECIMALS


def check_value(check_id: str, value: float | None, threshold: float | None) -> tuple[str, str]:
    """A check's value and its threshold as shown, e.g. ("39.96%", "40.0%"); "" when there is no threshold.

    The threshold keeps the default decimals unless it needs the value's decimals to keep the order right."""
    style = STYLES[CHECK_UNITS[check_id]]
    decimals = against_decimals = style.decimals
    if value is not None and threshold is not None:
        decimals = _decimals(value, threshold, style)
        shown_pair = round(value * style.scale, decimals), round(threshold * style.scale, style.decimals)
        if _sign(*shown_pair) != _sign(value, threshold):
            against_decimals = decimals
    shown = NO_VALUE if value is None else _write(value, style, decimals)
    against = "" if threshold is None else _write(threshold, style, against_decimals)
    return shown, against


def usd_m(amount: float, decimals: int = 0) -> str:
    """An amount in USD, shown in USD millions: 2,112,000,000 -> "USD 2,112 m"."""
    return _write(amount, STYLES["usd"], decimals)


def share_price(price: float) -> str:
    """The share price the user typed, in USD with two decimals: 65.4 -> "USD 65.40"."""
    return f"USD {price:,.2f}"


def in_style(value: float, style: str) -> str:
    """A value in one of STYLES with its default decimals: 0.20525 "percent" -> "20.5%", 37.113 "times" -> "37.1 times"."""
    return _write(value, STYLES[style], STYLES[style].decimals)


def rate(value: float) -> str:
    """A rate stored as a decimal, shown as a percent with two decimals: 0.0903325 -> "9.03%" (S10b)."""
    return _write(value, _Style(100.0, 2, "{}%"), 2)


def beta(value: float) -> str:
    """A beta, with two decimals: 1.00665 -> "1.01" (S10b)."""
    return f"{value:,.2f}"


def fact_value(fact: Fact) -> str:
    """One figure as shown in a check or on the sources page."""
    if fact.kind == "missing" or fact.value is None:
        return f"n/a: {fact.note}" if fact.note else "n/a"
    if fact.metric == "dividends_paid" and fact.kind == "assumption" and fact.value == 0:
        return NIL_DIVIDEND
    value = fact.value
    if fact.unit == "USD":
        return usd_m(value)
    if fact.unit == "USD/shares":
        return f"USD {value:,.2f} per share"
    if fact.unit == "shares":
        return f"{value / 1e6:,.1f} m shares"
    if fact.unit == "days":
        return f"{value:,.0f} days"
    return f"{value:,.2f}"  # "pure": a ratio or multiple without a unit
