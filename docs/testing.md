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

### H1–H6 (financial health)

| Break | Check | What was broken | Caught by (failing tests) |
|---|---|---|---|
| H1-a | H1 | comparison: equal assets pass | 1: `test_six_checks_and_strict_cover_and_debt_boundaries` |
| H1-b | H1 | inputs swapped | 3: `test_appendix_a_past_performance_and_health[H1]`, `test_ac3_tier_1_financial_health_score_of_the_synthetic_company` and 1 more |
| H2-a | H2 | term dropped: total liabilities instead of long-term | 4: `test_appendix_a_past_performance_and_health[H2]`, `test_h2_subtracts_the_current_portion_from_total_liabilities` and 2 more |
| H2-b | H2 | sign: liabilities plus current liabilities | 4: `test_appendix_a_past_performance_and_health[H2]`, `test_h2_subtracts_the_current_portion_from_total_liabilities` and 2 more |
| H3-a | H3 | term dropped: gross debt, cash not deducted | 4: `test_appendix_a_past_performance_and_health[H3]`, `test_h3_uses_cash_and_is_not_gross_debt_to_equity` and 2 more |
| H3-b | H3 | comparison: exactly at the 40% limit passes | 3: `test_six_checks_and_strict_cover_and_debt_boundaries`, `test_h3_uses_cash_and_is_not_gross_debt_to_equity` and 1 more |
| H4-a | H4 | comparison: an unchanged share passes | 2: `test_six_checks_and_strict_cover_and_debt_boundaries`, `test_equal_decimal_debt_ratios_are_not_falling` |
| H4-b | H4 | wrong year: latest equity used for the old ratio | 5: `test_appendix_a_past_performance_and_health[H4]`, `test_ac3_tier_1_financial_health_score_of_the_synthetic_company` and 3 more |
| H5-a | H5 | comparison: exactly 20% fails | 2: `test_h5_includes_exactly_twenty_percent`, `test_decimal_cash_flow_equal_to_twenty_percent_passes_the_inclusive_rule` |
| H5-b | H5 | divide by the sum: debt plus cash | 5: `test_appendix_a_past_performance_and_health[H5]`, `test_h3_nonpositive_equity_fails_without_dividing[0]` and 3 more |
| H6-a | H6 | comparison: exactly 5 times fails | 4: `test_six_checks_and_strict_cover_and_debt_boundaries`, `test_h6_does_not_require_debt_when_operating_profit_and_interest_are_known` and 2 more |
| H6-b | H6 | inputs swapped: interest / operating income | 7: `test_appendix_a_past_performance_and_health[H6]`, `test_ac3_tier_1_financial_health_score_of_the_synthetic_company` and 5 more |

All 12 caught. The exact boundaries (equal assets for H1, 40% for H3, an unchanged share for H4, 20% for H5,
5 times for H6) are tested directly, so a changed comparison is caught even where Appendix A is not at the boundary.

### S4 (benchmark loader, `app/src/benchmarks/loader.py`)

| Break | Check | What was broken | Caught by (failing tests) |
|---|---|---|---|
| S4-a | S4 | units: a ratio read as a percent (x100) | 2: `test_three_original_source_cells_keep_their_values_and_provenance`, `test_v4_market_pe_excludes_financials_but_d2_yield_uses_the_whole_market` |
| S4-b | S4 | blank cell read as zero instead of missing | 2: `test_blank_benchmark_is_missing_and_a_real_zero_is_preserved`, `test_blank_source_cell_preserves_its_structured_provenance` |
| S4-c | S4 | wrong company: every company gets the first industry in the file | 9: `test_demo_industries_match_the_original_lookup[KO-Beverage`, `test_demo_industries_match_the_original_lookup[AAPL-Computers/Peripherals-36]` and 7 more |
| S4-d | S4 | wrong market group: V4 compared with the market including financials | 14: `test_demo_industries_match_the_original_lookup[KO-Beverage`, `test_demo_industries_match_the_original_lookup[AAPL-Computers/Peripherals-36]` and 12 more |

All 4 caught: a percent read as a decimal, a blank cell turned into zero, a company given another company's
industry, and V4's market row with financial companies.

**Summary:** 28 deliberate breaks in B's area, 28 caught, 1 test added. The independent read-only review of B's
code by a member of another area (SPEC §15) is still to come.

## Break-it round (S18), part B: Flo's read-only review and what was done

Flo (C) reviewed P1–P6, H1–H6 and the benchmark loader read-only on 26 November (#64): no wrong result for the five
companies; 16 deliberate breaks of his own, none caught at the time. Every finding is now a test or a written
answer (SPEC §15).

| # | Finding | Done |
|---|---|---|
| 1 | H5: the size of the ratio (`abs`) passed all tests | Test: operating cash flow −50 against debt 100 fails (`test_h5_negative_operating_cash_flow_fails`) |
| 2 | P6: comparing sizes without the sign passed | Test: −20% now against −10% three years earlier fails (`test_p6_a_worse_return_fails_even_when_both_years_are_losses`) |
| 3 | A mistyped benchmark value passed | Test: the 30 ROE, margin, P/E, P/B and unlevered-beta values and firm counts match Damodaran's own web tables of the January 2026 edition (`test_benchmark_value_matches_damodarans_published_table`); Flo's five typos are each caught. The six dividend yields are not on those pages and stay checked against `divfund.xls` only |
| 4 | Guards removed without a failure: full-year flows, negative debt (H3–H5), negative revenue (P5), negative capital employed (P6), a benchmark in a wrong unit | One test each; the nine breaks are now caught |
| 5 | P3 said "faster" when profit fell | Fixed: "the latest change is higher than the average". Whether P3 should pass when profit fell by less than its average decline is the SPEC §7 formula (latest change > average change), kept as written |
| 6 | H6's "reported zero debt" exception cannot apply | Kept, no change: the data layer always gives financial debt as `derived` (the sum of debt lines) or `missing` (`resolver.py`, `debt()`), so a company with no debt and no interest gets "insufficient data", the cautious result. The rule is SPEC §7 and works if debt is ever reported directly |
| 7 | Industry ROE −0.17% and 0.10% | Confirmed against Damodaran's web table (finding 3); the weak hurdle is recorded in `docs/benchmarks.md` |
| 8 | H6 passes on any zero interest; SPEC says "reported as 0" | Kept, no change: interest expense is only `reported` or `missing` in the data layer and in the five companies' saved data, so any zero is a reported zero; an assumed zero appears only in the rule tests' made-up company, and changing the rule would mean editing one of those tests (rule 14.6) for no real case |
| 9 | After a change of fiscal year end, some checks are "insufficient data" | Kept: SPEC §5.3 rule 9 ends the five-year window at the gap, so "four years earlier" is never a different period |
| 10 | Negative figures read oddly (H3 "about −1.36% of equity", H6 "covered … −5.00 times") | Fixed: H3 names net cash, H6 with an operating loss says there was no operating profit to pay interest; every negative is written with "−" |
| 11 | P1 is "insufficient data" with one year missing | Kept: a missing input is never guessed (SPEC §5.2); four known profitable years out of five are not five known years |

No P or H result changed for the five companies or Appendix A (72 of 72 identical); only sentences did.

