"""The 24 checks (SPEC §7). Owners: B for `past.py` and `health.py` (S5, S6); C for `dividend.py` and
`valuation.py` (S7, S9).

Each check is a pure function: `CompanyData` (plus benchmarks and settings) in, `CheckResult` out. No network,
no interface imports (enforced by tests/unit/test_architecture.py).
"""
