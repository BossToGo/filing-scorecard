"""The synthetic company's market inputs for the screen tests (tier 2, SPEC Appendix A; slice S10b). Owner: D.

The values are the Appendix A inputs from `tests/fixtures/synthetic_co.yaml` (share price USD 30.00, risk-free rate
4.0%, unlevered beta 0.90 and the other synthetic benchmarks), signed off by C (Flo, 21 November 2026, #5). They are
inputs, not expected results. The industry name, the route and the number of firms are test labels: Appendix A has
no industry group, and AC8 only asks that the screen shows them.
"""

from __future__ import annotations

from datetime import date

from src.benchmarks.loader import BenchmarkData
from src.contracts import Fact
from tests.fixtures import synthetic

FY0 = date(2025, 12, 31)
PRICE = synthetic.inputs()["share_price"]  # USD 30.00
INDUSTRY = "Synthetic industry (test)"
ROUTE = "synthetic benchmarks"
FIRMS = 12
SOURCE_FILE = "SPEC.md Appendix A (synthetic)"
_B = synthetic.inputs()["benchmarks"]


def _fact(metric: str, value: float) -> Fact:
    return Fact(metric, value, "pure", None, FY0, "assumption", None, SOURCE_FILE, None, None, None,
                f"{metric} of the synthetic company (SYNTHETIC DATA: SPEC Appendix A)")


def benchmarks() -> BenchmarkData:
    """B's `BenchmarkData` shape, filled with the Appendix A benchmarks."""
    industry = (_fact("unlevered_beta", _B["unlevered_beta"]), _fact("roe", _B["return_on_equity"]),
                _fact("operating_margin", _B["operating_margin"]), _fact("pe", _B["price_to_earnings"]),
                _fact("pb", _B["price_to_book"]))
    market = (_fact("pe", _B["market_price_to_earnings"]), _fact("dividend_yield", _B["market_dividend_yield"]))
    return BenchmarkData(INDUSTRY, ROUTE, FIRMS, SOURCE_FILE, industry, market)


def risk_free() -> Fact:
    return Fact("risk_free_rate", synthetic.inputs()["settings"]["risk_free_rate"], "pure", None, FY0, "assumption",
                None, None, None, None, None, "Risk-free rate of the synthetic company (SYNTHETIC DATA: SPEC Appendix A)")
