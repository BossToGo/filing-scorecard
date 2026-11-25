"""Valuation checks on real companies, from the saved SEC data with the network off (slice S9). Owner: C (Flo).

Where the expected results come from:
- McDonald's: equity of USD −1,791 million at 31 December 2025, read by Flo from the FY2025 10-K ("Total
  shareholders' equity (deficit)", printed page 41, accession 0000063908-26-000035), so V5 fails with "negative
  equity" (SPEC §7), even without the industry benchmark (Flo's decision c).
- Nvidia: past revenue growth of 68.3% a year (SPEC §8.2), above the 30% cap, so the estimate at the cap is the
  estimate itself and V6 says so (Flo's decision b). The prices are chosen below and above the estimate; the rule
  says V1 and V6 then agree.
The industry beta and the benchmarks are test values (B's benchmark file, #27, is not merged yet); none of the
expected results depends on them.
"""

from __future__ import annotations

from datetime import date

from src.checks.valuation import valuation_checks
from src.contracts import Fact
from src.data.company import load_company, risk_free_rate
from src.settings import load_settings
from src.valuation.equity_method import value_company

SETTINGS = load_settings()


def given(value: float, metric: str) -> Fact:
    return Fact(metric, value, "pure", None, date(2026, 1, 5), "assumption", None, None, None, None, None,
                f"{metric}: a test value, not B's benchmark (test data)")


def checks(ticker: str, price: float, *, industry_pb: Fact | None):
    data = load_company(ticker, demo=True)
    valuation = value_company(data, SETTINGS, share_price=price, risk_free_rate=risk_free_rate(demo=True),
                              unlevered_beta=given(1.0, "unlevered_beta"))
    found = valuation_checks(data, SETTINGS, valuation, share_price=price, industry_pe=given(20.0, "pe"),
                             market_pe=given(20.0, "pe"), industry_pb=industry_pb)
    return valuation, {r.check_id: r for r in found}


def test_mcdonalds_negative_equity_fails_v5_even_without_the_benchmark():
    for pb in (given(4.0, "pb"), None):
        _, r = checks("MCD", 300.0, industry_pb=pb)
        assert (r["V5"].status, r["V5"].value) == ("fail", None)
        assert "negative equity" in r["V5"].explanation
        equity = [f for f in r["V5"].inputs if f.metric == "equity"]
        assert [f.period_end for f in equity] == [date(2025, 12, 31)]
        assert equity[0].value == -1_791 * 1_000_000  # Flo's reading of the 10-K, printed page 41 (USD, not millions)


def test_nvidia_growth_at_the_cap_v6_uses_the_same_estimate_as_v1():
    valuation, _ = checks("NVDA", 100.0, industry_pb=None)
    assert valuation.status == "ok"
    assert valuation.fair_value_at_growth_cap.value == valuation.fair_value.value
    line = "The company's starting growth is already at the 30% cap, so V6 uses the same estimate as V1."
    estimate = valuation.fair_value.value
    for price, status in ((0.5 * estimate, "pass"), (2.0 * estimate, "fail")):
        _, r = checks("NVDA", price, industry_pb=None)
        assert (r["V1"].status, r["V6"].status) == (status, status)
        assert line in r["V6"].explanation
