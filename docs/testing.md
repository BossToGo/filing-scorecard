# Part B verification
P1–P6 and H1–H6 use sourced facts; money stays USD and ratios remain decimal values.
Independent boundary workings are in comments in `test_past_b.py` and `test_health_b.py` under `app/tests/unit/`.
These labelled synthetic examples do not use locked Appendix A answers.
Greg adopted Flo's four rule changes on 23 November:
- P3: a latest-year loss with positive comparison profits fails.
- P4: known nonpositive equity fails before missing benchmarks or inputs.
- H4: known nonpositive equity at either endpoint fails before missing/zero-debt exceptions.
- H6: reported zero debt with missing interest passes; interest stays missing and no ratio is invented.
Missing/assumed/derived zero debt cannot invoke H6's exception; known interest still uses coverage.
Saved-demo regressions cover MCD P4/H3/H4 and AAPL's missing-interest H6.
Tests failed before the fixes; final suite on main `b5520b6`: 819 passed; run `.venv/bin/python -m pytest -q` from `app/`.
Personal calculations, source reading, Explain-backs and fixture-gated acceptance remain pending.
Shared rule/status records, G methodology, formal approval and merge remain open; browser journey reported separately.
