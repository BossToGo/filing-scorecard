# Part B verification
P1–P6 use sourced facts; money stays in USD and ratios remain decimal values.
Independent boundary workings are in comments in `app/tests/unit/test_past_b.py`.
These labelled synthetic examples do not use locked Appendix A answers.
Greg adopted Flo's rule changes on 23 November:
- P3: a latest-year loss with positive comparison profits fails.
- P4: known nonpositive equity fails before missing benchmarks or other inputs.
Missing data is never zero; fiscal gaps are not compressed.
The saved McDonald's negative-equity regression tests P4 without a benchmark.
Tests were seen failing before the fixes; final suite on main `b5520b6`: 752 passed.
Run from `app/`: `.venv/bin/python -m pytest -q`.
Personal calculations, source reading, Explain-backs and fixture-gated acceptance remain pending.
Shared rule/status records, formal teammate approval and merge remain open.
