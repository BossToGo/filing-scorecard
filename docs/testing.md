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

## Break-it round (S18), part B: deliberate breaks

Each formula of `past.py` and `health.py` was broken on purpose, twice per check, with the kinds of SPEC §15 (a
term dropped, inputs swapped, the wrong year, a comparison changed); then the full suite was run and the code
restored. A break counts as caught when at least one test fails. Run on 26 November on `main` 94f7d20 (1,240
tests); one line changed at a time, and `git status` confirmed the source was restored after each break.

### P1–P6 (past performance)

| Break | Check | What was broken | Caught by (failing tests) |
|---|---|---|---|
| P1-a | P1 | comparison: at least 4 → more than 4 | 1: `test_profitability_requires_four_strictly_positive_years_and_all_inputs` |
| P1-b | P1 | a zero profit counted as profitable | 1: `test_profitability_requires_four_strictly_positive_years_and_all_inputs` |
| P2-a | P2 | wrong year: latest vs one year earlier | 2: `test_p2_compares_with_four_years_earlier_not_the_year_before`, `test_missing_year_is_not_silently_replaced_by_an_older_year` |
| P2-b | P2 | term dropped: latest profit need not be positive | 1: `test_a_recent_loss_never_passes_earnings_growth` |
| P3-a | P3 | wrong period: 3-year instead of 4-year growth | 4: `test_nonzero_equal_compound_growth_does_not_pass_acceleration`, `test_geometric_growth_uses_four_intervals_and_distinguishes_acceleration` and 2 more |
| P3-b | P3 | comparison: equal growth passes | 4: `test_equal_profits_are_not_growth_or_acceleration`, `test_nonzero_equal_compound_growth_does_not_pass_acceleration` and 2 more |
| P4-a | P4 | term dropped: closing equity instead of the average | 2: `test_appendix_a_past_performance_and_health[P4]`, `test_roe_is_invariant_to_redistributing_opening_and_closing_equity` |
| P4-b | P4 | comparison: equal to the industry passes | 2: `test_matching_benchmarks_fail_because_industry_rules_are_strict`, `test_decimal_amount_equal_to_decimal_industry_ratio_does_not_pass[P4-net_income]` |
| P5-a | P5 | inputs swapped: revenue / operating income | 4: `test_appendix_a_past_performance_and_health[P5]`, `test_tier_2_past_performance_score_with_benchmarks` and 2 more |
| P5-b | P5 | comparison: equal to the industry passes | 2: `test_matching_benchmarks_fail_because_industry_rules_are_strict`, `test_decimal_amount_equal_to_decimal_industry_ratio_does_not_pass[P5-operating_income]` |
| P6-a | P6 | term dropped: total assets without current liabilities | 5: `test_appendix_a_past_performance_and_health[P6]`, `test_ac3_tier_1_past_performance_score_of_the_synthetic_company` and 3 more |
| P6-b | P6 | wrong year: latest operating income used for both years | 6: `test_appendix_a_past_performance_and_health[P6]`, `test_ac3_tier_1_past_performance_score_of_the_synthetic_company` and 4 more |

All 12 caught. P2-a (FY-1 instead of FY-4) was at first caught by one test only, and not by Appendix A, where both
years are below FY0; `test_p2_compares_with_four_years_earlier_not_the_year_before` was added for it.

