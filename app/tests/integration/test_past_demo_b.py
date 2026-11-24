"""B's saved-demo regressions, not Greg's personal Apple/Appendix A sign-off.

Source: McDonald's FY2025 10-K, accession 0000063908-26-000035,
us-gaap:StockholdersEquity at 2025-12-31 = USD -1,791,000,000 in the
saved SEC companyfacts. Greg adopted the negative-equity-first rule on
23 November 2026 following Flo's review; no ROE division is meaningful.
"""
from src.checks.past import past_checks
from src.data.company import load_company
from src.settings import load_settings


def test_mcdonalds_negative_equity_fails_roe_without_an_industry_benchmark():
    data = load_company("MCD", demo=True)
    equity = data.latest("equity")
    assert equity.value == -1_791_000_000
    assert equity.accession == "0000063908-26-000035"
    check = next(r for r in past_checks(data, settings=load_settings()["past_performance"])
                 if r.check_id == "P4")
    assert check.status == "fail"
    assert check.value is None and check.threshold is None
    assert "negative equity" in check.explanation.lower()
    assert equity in check.inputs
    assert all(f.kind != "missing" for f in check.inputs)
