# Part B verification
P1–P6 and H1–H6 use sourced facts; money stays USD and ratios remain decimal values.
Each check computes one exact fraction and uses it for both the result and the figure shown (Igor's review of #28).
Independent boundary workings are in comments in `test_past_b.py` and `test_health_b.py` under `app/tests/unit/`.
`test_b_appendix_a.py` checks P1–H6 against Appendix A (value, compared-with figure, result); B's sign-off of
24 November is recorded in the fixture (#46), so it runs. AC3 and tier 2 area scores (signed off by D and E) run too.
Rules adopted by Greg on 23 November: P3 fails on a latest-year loss; P4, H3 and H4 fail on known nonpositive
equity first; H6 passes on reported zero debt with missing interest (no ratio invented).
P3 also fails on a known loss in FY-4 or FY-1 when another year is missing (Flo's open point, 24 November).
Saved-demo regressions cover MCD P4/H3/H4 and AAPL's missing-interest H6.
Missing data is never zero; fiscal gaps are not compressed.
Run from `app/`: `.venv/bin/python -m pytest -q`.
Sign-off on #5 and Explain-backs on #22, #27, #28 and #29: done (24 November). Benchmarks: `test_benchmarks_b.py`.
