# Part B verification
P1–P6 use sourced facts; money stays in USD and ratios remain decimal values.
Each check computes one exact fraction and uses it for both the result and the figure shown (Igor's review of #28).
Independent boundary workings are in comments in `app/tests/unit/test_past_b.py`.
`app/tests/unit/test_b_appendix_a.py` checks P1–P6 against Appendix A (value, compared-with figure, result); it
skips until B's sign-off is recorded in the fixture, then switches on by itself. AC3 and the tier 2 area score
(signed off by D and E) run now. With the sign-off simulated locally, P2–P6 matched and a P6-on-total-assets
mutant was caught; P1 waits for the fixture's `compared_with` to read 4 (the rule's minimum), not 5.
Rules adopted by Greg on 23 November: P3 fails on a latest-year loss; P4 fails on known nonpositive equity first.
P3 also fails on a known loss in FY-4 or FY-1 when another year is missing (Flo's open point, 24 November).
Missing data is never zero; fiscal gaps are not compressed.
Run from `app/`: `.venv/bin/python -m pytest -q` (24 November, PR head after merging main: 771 passed, 6 skipped).
Still open: Greg's sign-off on #5 and his Explain-backs.
