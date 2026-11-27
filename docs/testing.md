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

# Part C verification

## Break-it round (S18), part C: deliberate breaks

Each formula of `dividend.py`, `valuation.py` and `equity_method.py` was broken on purpose with the kinds of SPEC
§15 (a term dropped, inputs swapped, the wrong year, a comparison changed), and guards (negative, zero, missing or
non-finite inputs) were removed or weakened. After each break the full suite was run and the code restored. A break
counts as caught when at least one test fails. Run on 26 November on `main` f7b46c9 (1,268 tests): one change at a
time, in throwaway clones, four at once; `git status` was clean after each restore (for the rerun of the missed
breaks: clean under `app/src`, the new tests being the only change). Controls: an unchanged copy passed, and a
reversed D1 comparison was caught. `main` 025ef0f (#62, #65, #66) was brought in afterwards: C's three source files
are unchanged by it and all 1,347 tests pass; the breaks were not rerun on it. Every caught break fails at least one of part C's own tests, so a screen test that
once failed under load (`test_amazon_d1_shows_its_explanation_once_in_the_row`) never decides a result.

### D1–D6 (dividend checks)

| Break | Check | What was broken | Caught by (failing tests) |
|---|---|---|---|
| D1-a | D1 | comparison: a zero dividend passes | 13: `test_1_a_labelled_nil_means_no_dividend_paid`, `test_2_a_reported_zero_in_fy0_means_no_dividend_paid` and 11 more |
| D1-b | D1 | D2-D6 not applicable whenever D1 does not pass, also when its figure is missing | 3: `test_3_missing_fy0_dividends_are_insufficient_data_never_no_dividend`, `test_a_negative_fy0_dividend_is_insufficient_data_everywhere` and 1 more |
| D2-a | D2 | term dropped: share count left out of the market value | 7: `test_appendix_a_d2_with_share_price_and_market_yield`, `test_s9_e9_yield_equal_to_the_market_yield_fails` and 5 more |
| D2-b | D2 | inputs swapped: market value / dividends | 7: `test_appendix_a_d2_with_share_price_and_market_yield`, `test_s9_e9_yield_equal_to_the_market_yield_fails` and 5 more |
| D2-c | D2 | comparison: a yield equal to the market's passes | 3: `test_s9_e9_yield_equal_to_the_market_yield_fails`, `test_s9_t2_a_yield_equal_to_the_market_yield_by_hand_fails` and 1 more |
| D3-a | D3 | wrong year: each year compared with two years earlier | 5: `test_6_d3_a_rise_from_a_year_of_zero_is_never_a_cut`, `test_appendix_a_synthetic_company` and 3 more |
| D3-b | D3 | comparison: a fall of exactly 10% is a cut | 1: `test_4_d3_a_fall_of_exactly_10_percent_is_not_a_cut` |
| D3-c | D3 | wrong period: only the latest step is looked at | 4: `test_appendix_a_synthetic_company`, `test_t2_to_t4_d3_looks_at_every_step_year_on_year` and 2 more |
| D4-a | D4 | wrong year: compared with one year earlier | 5: `test_each_check_lists_the_figures_its_rule_uses`, `test_b_a_negative_dividend_in_fy_minus_2_blocks_only_d3` and 3 more |
| D4-b | D4 | comparison: an unchanged dividend passes | 1: `test_8_d4_a_dividend_equal_to_four_years_earlier_did_not_grow` |
| D5-a | D5 | inputs swapped: net income / dividends | 13: `test_9_d5_fails_at_exactly_90_percent_and_when_net_income_is_zero_or_negative`, `test_11_a_changed_payout_limit_changes_d5` and 11 more |
| D5-b | D5 | comparison: exactly 90% passes | 1: `test_9_d5_fails_at_exactly_90_percent_and_when_net_income_is_zero_or_negative` |
| D5-c | D5 | wrong year: D5 uses the year before FY0 | 11: `test_each_check_lists_the_figures_its_rule_uses`, `test_3_missing_fy0_dividends_are_insufficient_data_never_no_dividend` and 9 more |
| D6-a | D6 | term dropped: capital expenditure not deducted | 5: `test_10_d6_dividends_against_operating_cash_flow_minus_capex`, `test_b_a_negative_dividend_in_fy_minus_2_blocks_only_d3` and 3 more |
| D6-abs | D6 | sign ignored: the size of a negative free cash flow is used | 1: `test_10_d6_dividends_against_operating_cash_flow_minus_capex` |
| D6-b | D6 | comparison: dividends equal to free cash flow fail | 1: `test_10_d6_dividends_against_operating_cash_flow_minus_capex` |
| D6-c | D6 | wrong year: D6 uses the year before FY0 | 11: `test_each_check_lists_the_figures_its_rule_uses`, `test_3_missing_fy0_dividends_are_insufficient_data_never_no_dividend` and 9 more |
| D-FY0 | D1–D6 | wrong year: the oldest five fiscal years are taken instead of the latest five | **none at first**; now 1: `test_with_six_fiscal_years_the_checks_use_the_latest_five` |

### Dividend guards removed or weakened

| Break | Check | What was broken | Caught by (failing tests) |
|---|---|---|---|
| GD-negative-dividend | D1–D6 | guard removed: negative dividends paid accepted | 3: `test_a_negative_fy0_dividend_is_insufficient_data_everywhere`, `test_b_a_negative_dividend_in_fy_minus_2_blocks_only_d3` and 1 more |
| GD-negative-capex | D6 | guard removed: negative capital expenditure accepted | 2: `test_t1_a_negative_capex_is_a_sign_error_and_d6_is_insufficient_data`, `test_the_sign_warning_is_named_only_for_a_figure_read_from_a_filing` |
| GD-missing-figure | D1–D6 | guard removed: a missing figure is read as zero | 7: `test_3_missing_fy0_dividends_are_insufficient_data_never_no_dividend`, `test_5_d3_with_a_year_missing_is_insufficient_data` and 5 more |
| GD-no-years | D1–D6 | guard removed: company without a fiscal year | 1: `test_a_company_without_any_fiscal_year_is_insufficient_data_everywhere` |
| GD-D3-years | D3 | guard removed: D3 with fewer than five years | 1: `test_7_with_only_four_fiscal_years_d3_and_d4_are_insufficient_data` |
| GD-D4-years | D4 | guard removed: D4 with fewer than five years | 1: `test_7_with_only_four_fiscal_years_d3_and_d4_are_insufficient_data` |
| GD-D3-zero-year | D3 | guard removed: D3 divides by a year of zero | 3: `test_6_d3_a_rise_from_a_year_of_zero_is_never_a_cut`, `test_c_d3_passes_with_no_value_when_every_step_starts_from_zero` and 1 more |
| GD-D5-loss | D5 | guard removed: D5 divides by a loss | 1: `test_9_d5_fails_at_exactly_90_percent_and_when_net_income_is_zero_or_negative` |
| GD-D5-zero | D5 | guard weakened: net income of exactly zero | 1: `test_9_d5_fails_at_exactly_90_percent_and_when_net_income_is_zero_or_negative` |
| GD-D2-price-none | D2 | guard removed: D2 without a share price | 71: `test_the_six_results_come_in_order_d1_to_d6`, `test_each_check_lists_the_figures_its_rule_uses` and 69 more |
| GD-D2-price-zero | D2 | guard removed: D2 with a price of zero or below | 2: `test_r_d2_bad_inputs_give_insufficient_data_naming_them` and 1 more |
| GD-D2-price-nan | D2 | guard removed: D2 with a price that is not a number | 2: `test_r_d2_bad_inputs_give_insufficient_data_naming_them` and 1 more |
| GD-D2-yield-zero | D2 | guard removed: D2 with a market yield of zero or below | 2: `test_r_d2_bad_inputs_give_insufficient_data_naming_them` and 1 more |
| GD-D2-shares-zero | D2 | guard removed: D2 with a share count of zero or below | 2: `test_r_d2_bad_inputs_give_insufficient_data_naming_them` and 1 more |
| GD-D2-dividend-blocked | D2 | guard removed: D2 ignores an unusable dividend figure | 1: `test_r_d2_with_dividends_fy0_missing_is_insufficient_data_naming_them` |
| GD-D2-price-negative | D2 | guard weakened: D2 accepts a negative share price | 1: `test_r_d2_bad_inputs_give_insufficient_data_naming_them` |
| GD-D2-yield-negative | D2 | guard weakened: D2 accepts a negative market yield | 1: `test_r_d2_bad_inputs_give_insufficient_data_naming_them` |
| GD-D2-shares-negative | D2 | guard weakened: D2 accepts a negative share count | 1: `test_r_d2_bad_inputs_give_insufficient_data_naming_them` |

### V1–V6 (valuation checks)

| Break | Check | What was broken | Caught by (failing tests) |
|---|---|---|---|
| V1-a | V1 | comparison: a price equal to the estimate passes | 3: `test_s9_e2_price_equal_to_the_estimate_and_to_the_estimate_at_the_cap`, `test_t_differences_of_one_part_in_a_trillion_are_ties` and 1 more |
| V1-b | V1 | inputs swapped: estimate below price | 7: `test_appendix_a_synthetic_company`, `test_appendix_a_valuation_area_score` and 5 more |
| V2-a | V2 | term dropped: the 80% left out | 9: `test_appendix_a_synthetic_company`, `test_s9_e2_price_equal_to_the_estimate_and_to_the_estimate_at_the_cap` and 7 more |
| V2-b | V2 | comparison: a price exactly at 80% fails | 3: `test_s9_e3_price_exactly_at_80_percent_of_the_estimate`, `test_t_differences_of_one_part_in_a_trillion_are_ties` and 1 more |
| V3-a | V3, V4 | inputs swapped: net income / market value (V3 and V4) | 13: `test_appendix_a_synthetic_company`, `test_appendix_a_valuation_area_score` and 11 more |
| V3-b | V3, V4 | comparison: a ratio equal to the benchmark passes (V3 and V4) | 6: `test_s9_e5_price_to_earnings_equal_to_both_benchmarks_fails`, `test_v1_v2_v6_take_the_engines_status_and_reason` and 4 more |
| V4-a | V4 | wrong benchmark: V4 uses the industry price to earnings | 9: `test_appendix_a_synthetic_company`, `test_appendix_a_valuation_area_score` and 7 more |
| V4-b | V3, V4 | term dropped: price per share instead of market value (V3 and V4) | 13: `test_appendix_a_synthetic_company`, `test_appendix_a_valuation_area_score` and 11 more |
| V5-a | V5 | inputs swapped: equity / market value | 7: `test_appendix_a_synthetic_company`, `test_s9_e7_price_to_book_equal_to_the_benchmark_fails` and 5 more |
| V5-b | V5 | comparison: a ratio equal to the benchmark passes | 5: `test_s9_e7_price_to_book_equal_to_the_benchmark_fails`, `test_v1_v2_v6_take_the_engines_status_and_reason` and 3 more |
| V6-a | V6 | wrong estimate: V6 uses the company's own growth instead of the cap | 10: `test_appendix_a_synthetic_company`, `test_appendix_a_valuation_area_score` and 8 more |
| V6-b | V6 | comparison: a price equal to the estimate at the cap fails | 4: `test_s9_e2_price_equal_to_the_estimate_and_to_the_estimate_at_the_cap`, `test_s9_e4_price_equal_to_the_estimate_at_the_cap` and 2 more |
| V-FY0 | V3–V5 | wrong year: earnings and equity of the oldest year instead of FY0 | 7: `test_appendix_a_synthetic_company`, `test_appendix_a_valuation_area_score` and 5 more |
| GAP-a | gap (G7, W8) | inputs swapped: gap divided by the price (G7, W8) | 2: `test_appendix_a_gap_to_the_estimate_for_g7_and_w8`, `test_s9_e1_gap_below_the_estimate` |
| GAP-b | gap (G7, W8) | sign flipped: estimate minus price | 3: `test_appendix_a_gap_to_the_estimate_for_g7_and_w8`, `test_s9_e1_gap_below_the_estimate` and 1 more |
| TIE-a | V1–V6 | tie allowance removed: computer rounding counts as a difference | 4: `test_s9_t1_a_price_to_earnings_equal_to_the_benchmark_by_hand_fails`, `test_t_differences_of_one_part_in_a_trillion_are_ties` and 2 more |

### Valuation-check guards removed or weakened

| Break | Check | What was broken | Caught by (failing tests) |
|---|---|---|---|
| GV-price-none | V1–V6 | guard removed: no share price | 34: `test_without_a_share_price_the_whole_area_is_insufficient_data`, `test_coca_cola_has_no_header_warning_and_its_reading_note_is_on_the_sources_page_e15` and 32 more |
| GV-price-zero | V1–V6 | guard removed: price of zero or below | 2: `test_r1_a_price_that_is_not_above_zero_makes_the_whole_area_insufficient_data` and 1 more |
| GV-price-nan | V1–V6 | guard removed: price that is not a number | 2: `test_r1_a_price_that_is_not_above_zero_makes_the_whole_area_insufficient_data` and 1 more |
| GV-shares-missing | V1–V6 | guard removed: share count missing | 1: `test_without_a_share_count_the_whole_area_is_insufficient_data` |
| GV-shares-zero | V1–V6 | guard removed: share count of zero or below | 2: `test_r2_a_share_count_not_above_zero_makes_the_whole_area_insufficient_data` and 1 more |
| GV-shares-negative | V1–V6 | guard weakened: negative share count accepted | 1: `test_r2_a_share_count_not_above_zero_makes_the_whole_area_insufficient_data` |
| GV-no-years | V1–V6 | guard removed: company without a fiscal year | **none at first**; now 1: `test_a_company_without_any_fiscal_year_is_insufficient_data_in_the_whole_area` |
| GV-engine-status | V1, V2, V6 | guard weakened: V1, V2, V6 ignore that the model does not fit | 2: `test_v1_v2_v6_take_the_engines_status_and_reason`, `test_igor_6_the_real_engines_status_and_reason_reach_v1_v2_and_v6` |
| GV-earnings-missing | V3, V4 | guard removed: missing net income | 1: `test_a_missing_figure_gives_insufficient_data` |
| GV-earnings-zero | V3, V4 | guard removed: net income of zero | 2: `test_s9_e6_no_earnings_fails_v3_and_v4_without_a_ratio`, `test_igor_4_zero_earnings_fail_even_without_benchmarks` |
| GV-earnings-loss | V3, V4 | guard removed: a loss gives a negative ratio | 2: `test_s9_e6_no_earnings_fails_v3_and_v4_without_a_ratio`, `test_s9_e6_no_earnings_fails_even_without_benchmarks` |
| GV-equity-missing | V5 | guard removed: missing equity | 1: `test_a_missing_figure_gives_insufficient_data` |
| GV-equity-zero | V5 | guard removed: equity of zero | 1: `test_s9_e8_zero_or_negative_equity_fails_v5_without_a_ratio` |
| GV-equity-negative | V5 | guard removed: negative equity gives a negative ratio | 2: `test_s9_e8_zero_or_negative_equity_fails_v5_without_a_ratio`, `test_mcdonalds_negative_equity_fails_v5_even_without_the_benchmark` |
| GV-benchmark-none | V3–V5 | guard removed: no benchmark | 4: `test_a_missing_benchmark_gives_insufficient_data`, `test_nvidia_growth_at_the_cap_v6_uses_the_same_estimate_as_v1` and 2 more |
| GV-benchmark-missing | V3–V5 | guard removed: benchmark marked missing | 3: `test_r3_a_benchmark_marked_missing_gives_insufficient_data_with_its_reason` and 2 more |
| GV-benchmark-negative | V3–V5 | guard weakened: negative benchmark accepted | 3: `test_r4_a_benchmark_of_zero_or_below_gives_insufficient_data` and 2 more |
| GV-benchmark-zero | V3–V5 | guard weakened: benchmark of exactly zero accepted | 3: `test_r4_a_benchmark_of_zero_or_below_gives_insufficient_data` and 2 more |
| GV-price-negative | V1–V6 | guard weakened: negative share price accepted | 1: `test_r1_a_price_that_is_not_above_zero_makes_the_whole_area_insufficient_data` |

### Valuation engine formulas (`app/src/valuation/equity_method.py`)

| Break | Check | What was broken | Caught by (failing tests) |
|---|---|---|---|
| BETA-a | beta (§8.1) | term dropped: no tax in re-levering the beta | 21: `test_appendix_a_synthetic_company`, `test_appendix_a_gap_to_the_estimate_for_g7_and_w8` and 19 more |
| BETA-b | beta (§8.1) | inputs swapped: equity / debt | 26: `test_appendix_a_synthetic_company`, `test_appendix_a_valuation_area_score` and 24 more |
| BETA-c | beta (§8.1) | limit removed: no upper limit on the beta | 5: `test_e20_a_beta_outside_the_limits_is_set_to_the_limit_labelled_and_recorded`, `test_e20_a_beta_just_past_the_limit_is_not_printed_as_the_limit` and 3 more |
| BETA-d | beta (§8.1) | limit removed: no lower limit on the beta | 4: `test_e20_a_beta_outside_the_limits_is_set_to_the_limit_labelled_and_recorded`, `test_e12_with_zero_debt_a_low_unlevered_beta_is_still_limited` and 2 more |
| KE-a | cost of equity (§8.1) | term dropped: risk-free rate left out of the cost of equity | 22: `test_appendix_a_synthetic_company`, `test_appendix_a_valuation_area_score` and 20 more |
| KE-b | cost of equity (§8.1) | term dropped: beta left out of the cost of equity | 19: `test_appendix_a_synthetic_company`, `test_appendix_a_gap_to_the_estimate_for_g7_and_w8` and 17 more |
| FCF-a | free cash flow (§8.2) | sign: capital expenditure added to the cash flow | 25: `test_appendix_a_synthetic_company`, `test_appendix_a_valuation_area_score` and 23 more |
| FCF-b | free cash flow (§8.2) | term dropped: capital expenditure not deducted | 24: `test_appendix_a_synthetic_company`, `test_appendix_a_valuation_area_score` and 22 more |
| FCF0-a | starting free cash flow (§8.2) | wrong year: margin applied to the revenue of FY-1 | 16: `test_appendix_a_synthetic_company`, `test_appendix_a_gap_to_the_estimate_for_g7_and_w8` and 14 more |
| FCF0-b | starting free cash flow (§8.2) | wrong years: margin over the first three years | 16: `test_appendix_a_synthetic_company`, `test_appendix_a_gap_to_the_estimate_for_g7_and_w8` and 14 more |
| FCF0-c | starting free cash flow (§8.2) | wrong period: FY0 alone instead of three years | 24: `test_appendix_a_synthetic_company`, `test_appendix_a_gap_to_the_estimate_for_g7_and_w8` and 22 more |
| G1-a | starting growth (§8.2) | five intervals instead of four | 25: `test_appendix_a_synthetic_company`, `test_appendix_a_gap_to_the_estimate_for_g7_and_w8` and 23 more |
| G1-b | starting growth (§8.2) | inputs swapped: first / last revenue | 27: `test_appendix_a_synthetic_company`, `test_appendix_a_gap_to_the_estimate_for_g7_and_w8` and 25 more |
| G1-c | starting growth (§8.2) | wrong year: growth from FY-3 | 25: `test_appendix_a_synthetic_company`, `test_appendix_a_gap_to_the_estimate_for_g7_and_w8` and 23 more |
| G1-d | starting growth (§8.2) | limit removed: no growth cap | 6: `test_e18_past_growth_above_the_cap_starts_at_the_cap_with_the_growth_note`, `test_past_growth_just_beyond_a_limit_is_still_labelled_as_limited` and 4 more |
| G1-e | starting growth (§8.2) | limit removed: no growth floor | 3: `test_past_growth_just_beyond_a_limit_is_still_labelled_as_limited`, `test_e18_past_growth_below_the_floor_starts_at_the_floor_with_the_growth_note` and 1 more |
| G1-f | starting growth (§8.2) | rounding allowance at a limit removed | 2: `test_past_growth_exactly_at_a_limit_is_not_labelled_as_limited` and 1 more |
| PATH-a | growth decay (§8.2) | wrong year: growth already decayed in year 1 | 16: `test_appendix_a_synthetic_company`, `test_appendix_a_gap_to_the_estimate_for_g7_and_w8` and 14 more |
| PATH-b | growth decay (§8.2) | term dropped: half-life ignored | 18: `test_appendix_a_synthetic_company`, `test_appendix_a_valuation_area_score` and 16 more |
| DISC-a | discounting (§8.3) | discounted one year too little (beginning of year) | 15: `test_appendix_a_synthetic_company`, `test_appendix_a_gap_to_the_estimate_for_g7_and_w8` and 13 more |
| DISC-b | discounting (§8.3) | growth not compounded: every year grows from FCF0 | 17: `test_appendix_a_synthetic_company`, `test_appendix_a_valuation_area_score` and 15 more |
| TV-a | terminal value (§8.3) | term dropped: no (1 + gT) in the terminal value | 13: `test_appendix_a_synthetic_company`, `test_appendix_a_gap_to_the_estimate_for_g7_and_w8` and 11 more |
| TV-b | terminal value (§8.3) | term dropped: terminal growth missing from the denominator | 13: `test_appendix_a_synthetic_company`, `test_appendix_a_gap_to_the_estimate_for_g7_and_w8` and 11 more |
| TV-c | terminal value (§8.3) | terminal value discounted one year too far | 13: `test_appendix_a_synthetic_company`, `test_appendix_a_gap_to_the_estimate_for_g7_and_w8` and 11 more |
| PV-a | present value (§8.3) | term dropped: present value without the terminal value | 15: `test_appendix_a_synthetic_company`, `test_appendix_a_valuation_area_score` and 13 more |
| TVS-a | terminal value share | terminal value share divided by the forecast sum instead of the total | 1: `test_f3_terminal_value_discounted_and_its_share` |
| GT-a | terminal growth (§8.3) | limit removed: terminal growth is always the risk-free rate | 18: `test_appendix_a_synthetic_company`, `test_appendix_a_gap_to_the_estimate_for_g7_and_w8` and 16 more |
| GT-b | terminal growth (§8.3) | limit only: terminal growth ignores a low risk-free rate | 1: `test_terminal_growth_is_the_risk_free_rate_when_that_is_below_2_5_percent` |
| EQ-a | equity value (§8.3) | sign: minority interests added | 4: `test_e19_equity_value_zero_or_below_after_minority_interests_means_not_applicable`, `test_e19_minority_case_carries_no_line_about_a_valuation_that_never_ran` and 2 more |
| EQ-b | equity value (§8.3) | term dropped: minority interests not deducted | 4: `test_e19_equity_value_zero_or_below_after_minority_interests_means_not_applicable`, `test_e19_minority_case_carries_no_line_about_a_valuation_that_never_ran` and 2 more |
| FV-a | value per share (§8.3) | term dropped: present value per share, minority interests lost | 1: `test_a_minority_interest_is_subtracted_from_the_present_value` |
| FV-b | value per share (§8.3) | inputs swapped: shares / equity value | 13: `test_appendix_a_synthetic_company`, `test_appendix_a_gap_to_the_estimate_for_g7_and_w8` and 11 more |
| CAP-a | estimate at the cap (V6) | wrong growth: the cap value uses the company's own growth | 7: `test_appendix_a_synthetic_company`, `test_appendix_a_valuation_area_score` and 5 more |
| CAP-b | estimate at the cap (V6) | term dropped: minority interests not deducted at the cap | 1: `test_a_minority_interest_is_subtracted_from_the_present_value` |
| FIT-a | model fits (§8.6) | comparison: free cash flow of exactly zero fits the model | 1: `test_e19_no_free_cash_flow_over_three_years_means_not_applicable` |
| FIT-b | model fits (§8.6) | test removed: negative starting free cash flow is valued | 2: `test_e19_no_free_cash_flow_over_three_years_means_not_applicable` and 1 more |
| FIT-c | model fits (§8.6) | comparison: equity value of exactly zero fits the model | **none at first**; now 1: `test_e19_an_equity_value_of_exactly_zero_means_not_applicable` |
| FIT-d | model fits (§8.6) | test removed: negative equity value is shown | 2: `test_e19_equity_value_zero_or_below_after_minority_interests_means_not_applicable`, `test_e19_minority_case_carries_no_line_about_a_valuation_that_never_ran` |
| E-wrong-year-debt | beta (§8.1) | wrong year: financial debt of the oldest year | 27: `test_appendix_a_synthetic_company`, `test_appendix_a_gap_to_the_estimate_for_g7_and_w8` and 25 more |
| E-wrong-year-minority | equity value (§8.3) | wrong year: minority interest of the oldest year | 57: `test_appendix_a_synthetic_company`, `test_appendix_a_valuation_area_score` and 55 more |
| E-FY0 | years used (§7) | wrong years: the oldest five fiscal years instead of the latest five | **none at first**; now 1: `test_with_six_fiscal_years_the_valuation_uses_the_latest_five` |

### Valuation engine guards removed or weakened

| Break | Check | What was broken | Caught by (failing tests) |
|---|---|---|---|
| GE-five-years | inputs (§8.6) | guard removed: fewer than five fiscal years | 4: `test_e22_a_missing_input_means_no_fair_value_and_names_it`, `test_e22_with_four_fiscal_years_the_missing_market_inputs_are_named_too` and 2 more |
| GE-missing-figure | inputs (§8.6) | guard removed: a missing figure is read as zero | 10: `test_igor_6_the_real_engines_status_and_reason_reach_v1_v2_and_v6`, `test_e22_a_missing_input_means_no_fair_value_and_names_it` and 8 more |
| GE-negative-capex | inputs (§8.6) | guard removed: negative capital expenditure accepted | 2: `test_e22_a_missing_input_means_no_fair_value_and_names_it`, `test_a_negative_capex_not_read_from_a_filing_does_not_point_to_a_sign_warning` |
| GE-negative-debt | inputs (§8.6) | guard removed: negative financial debt accepted | 1: `test_e22_a_missing_input_means_no_fair_value_and_names_it` |
| GE-revenue-zero | inputs (§8.6) | guard removed: revenue of zero or below accepted | 4: `test_e22_a_missing_input_means_no_fair_value_and_names_it` and 3 more |
| GE-shares-zero | inputs (§8.6) | guard removed: share count of zero or below accepted | 1: `test_e22_a_missing_input_means_no_fair_value_and_names_it` |
| GE-negative-shares | inputs (§8.6) | guard weakened: negative share count or revenue accepted | 2: `test_e22_a_missing_input_means_no_fair_value_and_names_it` and 1 more |
| GE-negative-share-count | inputs (§8.6) | guard weakened: negative share count accepted (revenue guard kept) | **none at first**; now 1: `test_e22_a_missing_input_means_no_fair_value_and_names_it` |
| GE-price-none | inputs (§8.6) | guard removed: no share price | 39: `test_e22_a_missing_input_means_no_fair_value_and_names_it`, `test_e22_with_four_fiscal_years_the_missing_market_inputs_are_named_too` and 37 more |
| GE-price-nan | inputs (§8.6) | guard removed: price that is not a number | 3: `test_e22_a_share_price_that_is_not_a_finite_number_means_no_fair_value` and 2 more |
| GE-price-negative | inputs (§8.6) | guard weakened: negative share price accepted | **none at first**; now 1: `test_e22_a_missing_input_means_no_fair_value_and_names_it` |
| GE-market-none | inputs (§8.6) | guard removed: no risk-free rate or beta | 5: `test_e22_a_missing_input_means_no_fair_value_and_names_it`, `test_e22_every_missing_input_is_named_not_only_the_first` and 3 more |
| GE-market-missing | inputs (§8.6) | guard removed: rate or beta marked missing | 7: `test_e22_a_missing_risk_free_fact_counts_like_no_risk_free_rate`, `test_today_each_area_is_either_not_merged_or_six_results_in_order` and 5 more |
| GE-beta-negative | inputs (§8.6) | guard weakened: negative industry beta accepted | **none at first**; now 1: `test_e22_a_missing_input_means_no_fair_value_and_names_it` |
| GE-forecast-rate | growth, forecast | guard removed: cost of equity not above terminal growth | **none at first**; now 2: `test_a_cost_of_equity_not_above_terminal_growth_is_refused` and 1 more |
| GE-forecast-rate-eq | growth, forecast | guard weakened: cost of equity equal to terminal growth | **none at first**; now 1: `test_a_cost_of_equity_not_above_terminal_growth_is_refused` |
| GE-g1-years | growth, forecast | guard removed: starting_growth() with fewer than five years | **none at first**; now 1: `test_starting_growth_refuses_a_company_with_only_four_fiscal_years` |
| GE-g1-unusable | growth, forecast | guard removed: starting_growth() with unusable revenue | **none at first**; now 3: `test_starting_growth_refuses_unusable_revenue` and 2 more |
| GE-fy0-note | FY0 line (§8.6) | comparison: FY0 free cash flow of exactly zero called negative | **none at first**; now 1: `test_a_free_cash_flow_of_exactly_zero_in_fy0_is_not_called_negative` |

**Summary:** 131 deliberate breaks in C's area, 119 caught by the tests that existed, 12 not. Tests were
added for all 12 (14 test cases), and each of those breaks now fails at least one of them. No app code changed. The new
tests expect only what the rule itself says (a status, the years used, an error), with no worked numbers.

**No unit guard, dismissed in writing:** the dividend checks, the valuation checks and the engine do not check a
figure's unit, so there was no such guard to remove. Units are fixed where the data enters: the resolver reads US
dollar figures (SPEC §5.3.5) and the benchmark loader refuses a row whose unit is not `pure`. A later change there
that handed over a wrong unit would not be noticed by C's code.

The independent read-only review of C's code by a member of another area (SPEC §15) is still to come.

# Part A verification

## Break-it round (S18), part A: deliberate breaks

Each formula and guard of A's data layer and overview was broken on purpose, one small change at a time, with the
kinds of SPEC §15 (a term dropped, inputs swapped, the wrong year or tag, a comparison changed, a "missing is never
zero" guard removed, a rounding or a denominator changed); so were A's tag map and settings, the rules that keep the
FRED key and the SEC User-Agent secret, and the S10d chart code of PR #70. After each break the full suite ran and
the code was restored. A break counts as caught when at least one test fails. Run on 27 November with a small script
in throwaway clones, four at once, never in a working checkout: 255 breaks on `main` 3ed71fc (1,347 tests) and 54
breaks of `charts()` and `_fixed` on PR #70's head 1181e53 (1,382 tests), before #70 was merged. The script
checked that every edit matched its line of code exactly once, and `git status` was clean after every restore (for
the reruns, clean apart from the new tests). Controls: the unchanged clones passed (1,347 and 1,382). No break made
the suite hang. A break that only other owners' tests caught is marked "(D's)"; every other caught break fails at
least one of A's own tests.

### Resolver (`app/src/data/resolver.py`)

| Break | Check | What was broken | Caught by (failing tests) |
|---|---|---|---|
| RES-flow-350 | rule 1 | comparison: a flow of exactly 350 days left out | 1: `test_a_flow_must_cover_350_to_380_days[2025-01-15-True]` |
| RES-flow-380 | rule 1 | comparison: a flow of exactly 380 days left out | 1: `test_a_flow_must_cover_350_to_380_days[2024-12-16-True]` |
| RES-flow-nine-months | rule 1 | lower limit removed: nine months read as a year | 2: `test_a_flow_must_cover_350_to_380_days[2025-01-16-False]`, `test_planted_a_nine_month_figure_is_never_read_as_a_year` |
| RES-flow-long | rule 1 | upper limit removed: a period longer than a year read as one | 1: `test_a_flow_must_cover_350_to_380_days[2024-12-15-False]` |
| RES-forms | rule 1 | form filter removed: 10-Q and other forms read | 4: `test_figures_from_quarterly_reports_are_ignored`, `test_shares_come_from_the_cover_page_of_the_latest_annual_report` and 2 more |
| RES-instant-start | rule 3 | a figure with a start date (a flow) read as a balance | 1: `test_a_balance_filed_with_a_start_date_is_not_used` |
| RES-amendment-loses | rule 4 | on the same day the original wins over the amendment | 1: `test_an_amendment_filed_the_same_day_wins_whatever_its_accession_number` |
| RES-earliest-filing | rule 4 | wrong filing: the earliest instead of the latest | 6: `test_coca_cola_2018_revenue_restatement_as_shown_in_session_5`, `test_a_comparative_labelled_with_a_later_fiscal_year_lands_in_its_own_year` and 4 more |
| RES-order-accession | rule 4 | filing order by accession number instead of filing date | 2: `test_an_amendment_filed_the_same_day_wins_whatever_its_accession_number`, `test_planted_a_restated_figure_uses_the_latest_filing_and_keeps_the_original` |
| RES-restated-1pc | rule 4 | comparison: a restatement of exactly 1% warned | **none at first**; now 1: `test_a_restatement_of_exactly_one_percent_is_not_more_than_one_percent` |
| RES-restated-warning | rule 4 | RESTATED warning dropped (note kept) | 2: `test_coca_cola_2018_revenue_restatement_as_shown_in_session_5`, `test_planted_a_restated_figure_uses_the_latest_filing_and_keeps_the_original` |
| RES-restated-any-period | rule 4 | the original taken from any period with that end date | 1: `test_two_annual_periods_ending_the_same_day_are_not_a_restatement` |
| RES-reldiff-min | rules 4, 7 | wrong denominator: difference divided by the smaller value | **none at first**; now 4: `test_a_restatement_of_exactly_one_percent_is_not_more_than_one_percent`, `test_one_percent_is_measured_against_the_larger_of_the_two_values` and 2 more |
| RES-reldiff-sign | rules 4, 7 | sign: the denominator without abs | **none at first**; now 1: `test_a_restated_loss_is_compared_by_size_and_warned` |
| RES-tag-last | rule 7 | wrong tag order: the last tag with a value wins | 12: `test_ac16_coca_cola_key_figures_coverage_and_balance_sheet_are_shown`, `test_mcdonalds_depreciation_is_the_cash_flow_statement_total` and 10 more |
| RES-conflict-1pc | rule 7 | comparison: tags exactly 1% apart flagged | **none at first**; now 1: `test_tags_exactly_one_percent_apart_are_noted_but_not_flagged` |
| RES-samedef-default | rule 7 | default flipped: tags of the same definition never flagged | 2: `test_two_tags_with_different_values_are_flagged_and_the_first_in_the_list_is_used`, `test_tags_that_should_agree_still_raise_a_conflict` |
| RES-samedef-ignored | rule 7 | same_definition ignored: fallbacks of another definition flagged | 2: `test_fallback_tags_with_a_different_definition_are_noted_but_not_warned`, `test_interest_on_debt_only_below_total_interest_is_not_a_conflict` |
| RES-later-larger-term | rule 7 | term dropped: later tag flagged when above 50% of the value, not 150% | 1: `test_interest_on_debt_only_below_total_interest_is_not_a_conflict` |
| RES-later-larger-eq | rule 7 | comparison: a later tag exactly 50% larger flagged | **none at first**; now 1: `test_a_later_interest_tag_exactly_50_percent_larger_is_not_flagged` |
| RES-override-warns | rule 7 | a documented company override still raises TAG_CONFLICT | 1: `test_mcdonalds_depreciation_is_the_cash_flow_statement_total` |
| RES-other-tag-note | rule 7 | the other tag's different value not noted | 4: `test_two_tags_with_different_values_are_flagged_and_the_first_in_the_list_is_used`, `test_a_small_difference_between_tags_is_recorded_without_a_warning` and 2 more |
| RES-override-note | rule 7 | the company override not noted on the figure | 1: `test_a_company_override_changes_the_tag_order_and_explains_why` |
| RES-outflow-sign | SIGN | SIGN warning for a negative payment dropped | 2: `test_planted_a_negative_capital_expenditure_is_kept_as_filed_and_flagged`, `test_a_negative_dividend_payment_is_flagged_too` |
| RES-outflow-zero | SIGN | comparison: a payment of zero flagged as a sign error | **none at first**; now 1: `test_a_payment_of_exactly_zero_is_not_a_sign_error` |
| RES-positive-only | SIGN | guard removed: a negative interest expense used | 1: `test_planted_a_negative_interest_expense_is_flagged_and_not_used` |
| RES-positive-zero | SIGN | comparison: a reported zero interest expense made missing | **none at first**; now 1: `test_a_reported_zero_interest_expense_is_kept` |
| RES-period-start | Fact | period start of a flow dropped | 1: `test_closed_rows_show_the_check_s_own_sentence_not_two_numbers` (D's); now also `test_a_flow_keeps_its_period_start_and_a_balance_has_none` |
| RES-accession-original | Fact | wrong source: the original filing's accession on a restated figure | 2: `test_a_comparative_labelled_with_a_later_fiscal_year_lands_in_its_own_year`, `test_planted_a_restated_figure_uses_the_latest_filing_and_keeps_the_original` |
| RES-nonusd-item | rule 5 | NON_USD warning and reason dropped for a line item | 1: `test_a_figure_in_another_currency_is_missing_and_flagged` |
| RES-nonusd-company | rule 5 | NON_USD dropped for a company filing in another currency | 1: `test_a_company_filing_only_in_another_currency_is_flagged_as_such` |
| RES-first-unit | rule 5 | currency ignored: the first unit found is read, whatever it is | 2: `test_a_figure_in_another_currency_is_missing_and_flagged`, `test_a_company_filing_only_in_another_currency_is_flagged_as_such` |
| RES-gap-380 | rule 2 | comparison: year ends exactly 380 days apart counted as a gap | **none at first**; now 1: `test_year_ends_exactly_380_days_apart_are_not_a_gap` |
| RES-gap-ignored | rule 2 | guard removed: years across a missing year kept | 1: `test_a_gap_between_fiscal_years_ends_the_window_and_is_flagged` |
| RES-fychange-350 | rule 2 | comparison: year ends exactly 350 days apart counted as overlapping | **none**; not observable, see the dismissals below |
| RES-fychange-ignored | rule 2 | guard removed: an overlapping 12-month period kept (FY_CHANGE) | 1: `test_a_change_of_fiscal_year_end_does_not_create_overlapping_years` |
| RES-six-years | rule 2 | off by one: six fiscal years instead of five | 10: `test_ac16_coca_cola_key_figures_coverage_and_balance_sheet_are_shown`, `test_amazon_pays_no_dividend_labelled_as_nil_in_every_year` and 8 more |
| RES-four-years | rule 2 | off by one: four fiscal years instead of five | 30: `test_ac16_coca_cola_key_figures_coverage_and_balance_sheet_are_shown`, `test_coca_cola_2018_revenue_restatement_as_shown_in_session_5` and 28 more |
| RES-newest-first | rule 2 | order: fiscal years newest first, so FY0 is the oldest | 14: `test_an_absent_bridge_item_is_treated_as_nil_and_labelled`, `test_a_reported_bridge_item_is_used` and 12 more |
| RES-oldest-five | rule 2 | wrong years: the oldest five fiscal years instead of the latest | 201: `test_ac16_coca_cola_key_figures_coverage_and_balance_sheet_are_shown`, `test_each_key_figure_says_reported_or_derived` and 199 more |
| RES-fy-items | rule 2 | fiscal years found from revenue only | **none at first**; now 1: `test_a_year_without_revenue_is_still_a_fiscal_year` |
| RES-derived-warning | DERIVED | DERIVED warning dropped | 3: `test_gross_profit_is_derived_when_not_reported`, `test_depreciation_and_amortisation_are_added_when_only_the_parts_are_reported` and 1 more |
| RES-derive-first | §6 | the derivation used even when the figure is reported | 3: `test_mcdonalds_depreciation_is_the_cash_flow_statement_total`, `test_a_combined_depreciation_tag_wins_over_the_parts` and 1 more |
| RES-gross-sign | §6 | sign: gross profit = revenue + cost of revenue | 1: `test_gross_profit_is_derived_when_not_reported` |
| RES-gross-missing-zero | §6 | missing is never zero: a missing cost of revenue read as zero | 1: `test_a_derived_figure_with_a_missing_input_stays_missing_and_says_why` |
| RES-equity-minority-sign | §6 | sign: equity = total equity + minority interest | 1: `test_equity_is_derived_from_total_equity_minus_minority_interest_when_not_reported` |
| RES-equity-minority-dropped | §6 | term dropped: minority interest not deducted from total equity | 1: `test_equity_is_derived_from_total_equity_minus_minority_interest_when_not_reported` |
| RES-equity-nci-sign | §6 | guard removed: total equity used as equity when minority interests seem to exist | 2: `test_equity_stays_missing_when_minority_interest_exists_but_is_not_reported_that_year`, `test_equity_stays_missing_when_profit_shows_a_minority_share` |
| RES-nci-profitloss | §6 | ProfitLoss ≠ NetIncomeLoss no longer a sign of minority interests | 1: `test_equity_stays_missing_when_profit_shows_a_minority_share` |
| RES-nci-other-years | §6 | minority interest of another year no longer a sign | 1: `test_equity_stays_missing_when_minority_interest_exists_but_is_not_reported_that_year` |
| RES-total-equity-sign | §6 | sign: total equity = equity − minority interest | 2: `test_total_liabilities_are_derived_from_assets_minus_total_equity`, `test_derived_liabilities_leave_out_temporary_equity` |
| RES-liab-temporary | §6 | term dropped: temporary equity not deducted from liabilities | 1: `test_derived_liabilities_leave_out_temporary_equity` |
| RES-liab-sign | §6 | sign: liabilities = assets + total equity | 2: `test_total_liabilities_are_derived_from_assets_minus_total_equity`, `test_negative_equity_is_subtracted_with_its_sign` |
| RES-liab-missing-zero | §6 | missing is never zero: missing total equity read as zero | **none at first**; now 1: `test_total_liabilities_without_total_equity_stay_missing` |
| RES-da-first-part | §6 | guard removed: D&A derived without its first part (Depreciation) | 1: `test_amortisation_alone_does_not_make_a_depreciation_figure` |
| RES-da-other-years | §6 | guard removed: a part reported in other years counted as nil | 1: `test_an_amortisation_missing_this_year_but_reported_in_another_is_not_counted_as_nil` |
| RES-nil-evidence-ignored | Q1 | evidence ignored: a company with only declared dividends shown as paying none | 1: `test_a_dividend_declared_per_share_is_evidence_and_the_years_stay_missing` |
| RES-nil-evidence-zero | Q1 | comparison: a zero under an evidence tag counts as a dividend | 1: `test_a_declared_dividend_of_zero_is_no_evidence` |
| RES-nil-window | Q1 | wrong period: evidence older than the five years counts | 1: `test_a_dividend_paid_before_the_five_years_is_no_evidence` |
| RES-nil-window-after | Q1 | wrong period: evidence after FY0 counts | **none at first**; now 1: `test_a_dividend_declared_after_the_five_years_is_no_evidence` |
| RES-nil-forms | Q1 | evidence from 10-Qs counts | **none at first**; now 1: `test_a_dividend_shown_only_in_a_quarterly_report_is_no_evidence` |
| RES-nil-other-reason | Q1 | a dividend missing for another reason (not US dollars) turned nil | **none at first**; now 1: `test_dividends_filed_only_in_another_currency_stay_missing_never_nil` |
| RES-nil-any-all | Q1 | a company with an amount in some years shown as paying none in all | **none at first**; now 1: `test_reported_zero_dividends_in_some_years_keep_the_other_years_missing` |
| RES-nil-kind | Q1 | nil dividend labelled reported instead of assumption | 126: `test_ac17_amazon_shows_no_dividend_paid`, `test_the_radar_labels_each_area_with_its_share_or_why_it_is_off_the_shape` and 124 more |
| RES-nil-warning | Q1 | NIL_DIVIDEND warning dropped | 1: `test_a_company_with_no_dividend_in_any_year_pays_none_labelled` |
| RES-switch | TAG_SWITCH | comparison: TAG_SWITCH only for three tags or more | 2: `test_a_tag_that_changes_between_years_is_noted_as_a_switch`, `test_a_switch_between_the_combined_tag_and_the_parts_is_flagged` |
| RES-switch-parts | TAG_SWITCH | a figure built from parts not counted as its own tag | 1: `test_a_switch_between_the_combined_tag_and_the_parts_is_flagged` |
| RES-debt-samedef | debt | finance-lease definitions treated as the same | 1: `test_current_debt_is_not_the_difference_of_two_tags_with_different_definitions` |
| RES-debt-seagate | debt | guard removed: a total below its non-current part used | 1: `test_a_reported_total_below_its_own_non_current_part_is_not_used_as_the_total` |
| RES-debt-seagate-tol | debt | sign: tolerance added, a total equal to its non-current part refused | 1: `test_a_company_without_current_maturities_keeps_its_commercial_paper` |
| RES-debt-total-plus-current | debt | double count: current maturities added to the reported total | 4: `test_mcdonalds_debt_matches_its_balance_sheets[2025-39973-0]`, `test_the_reported_total_long_term_debt_is_used_with_short_term_borrowings` and 2 more |
| RES-debt-parts-sign | debt | sign: non-current − current | 6: `test_without_a_total_the_non_current_and_current_parts_are_added`, `test_commercial_paper_is_added_when_there_is_no_short_term_borrowings_total` and 4 more |
| RES-debt-check-dropped | debt | DEBT_CHECK for a total differing from its parts dropped | 1: `test_a_total_that_disagrees_with_its_parts_is_flagged` |
| RES-debt-incomplete | debt | DEBT_INCOMPLETE warning dropped | 2: `test_a_missing_current_portion_is_not_counted_as_zero`, `test_debt_current_does_not_fill_the_gap_of_a_non_current_only_debt` |
| RES-debt-no-short | debt | term dropped: short-term borrowings not added | 8: `test_the_reported_total_long_term_debt_is_used_with_short_term_borrowings`, `test_without_a_total_the_non_current_and_current_parts_are_added` and 6 more |
| RES-debt-short-is-current | debt | guard removed: short-term borrowings equal to current maturities added again | 4: `test_short_term_borrowings_that_are_the_current_part_of_the_total_are_not_added_twice`, `test_short_term_borrowings_equal_to_the_tagged_current_maturities_are_one_line_not_two` and 2 more |
| RES-debt-short-is-current-tol | debt | comparison: exactly 1% apart no longer the same line | **none at first**; now 1: `test_short_term_borrowings_exactly_1_percent_from_the_current_maturities_are_the_same_line` |
| RES-debt-inside | debt | company override ignored: McDonald's short-term debt added again | 4: `test_mcdonalds_debt_matches_its_balance_sheets[2025-39973-0]`, `test_mcdonalds_debt_matches_its_balance_sheets[2024-38424-0]` and 2 more |
| RES-debt-missing-zero | debt | missing is never zero: no long-term debt tag read as zero long-term debt | 3: `test_debt_current_alone_is_not_passed_off_as_total_debt`, `test_short_term_borrowings_alone_are_not_passed_off_as_total_debt` and 1 more |
| RES-debt-short-parts | debt | short-term parts: only the first counted | 1: `test_commercial_paper_is_added_when_there_is_no_short_term_borrowings_total` |
| RES-debt-cp-twice | debt | double count: commercial paper added to ShortTermBorrowings | 1: `test_commercial_paper_is_not_added_twice_when_short_term_borrowings_include_it` |
| RES-debt-tesla | debt | Tesla rule removed: total + DebtCurrent never checked against the principal | 1: `test_a_long_term_total_that_is_only_the_non_current_part_is_completed_with_debt_current` |
| RES-debt-tesla-warning | debt | DEBT_CHECK dropped when the principal settles nothing | 1: `test_without_a_principal_to_decide_the_debt_is_flagged` |
| RES-debt-current-above | debt | DEBT_CHECK dropped for current debt above total debt | **none at first**; now 1: `test_current_debt_above_total_debt_raises_its_own_check` |
| RES-debt-current-no-short | debt | term dropped: short-term borrowings left out of current debt | 6: `test_the_reported_total_long_term_debt_is_used_with_short_term_borrowings`, `test_without_a_total_the_non_current_and_current_parts_are_added` and 4 more |
| RES-debt-micron | debt | guard removed: current part from two tags of different definitions | 1: `test_current_debt_is_not_the_difference_of_two_tags_with_different_definitions` |
| RES-debt-mcd-current-sign | debt | sign: McDonald's current debt = non-current − total | 3: `test_mcdonalds_debt_matches_its_balance_sheets[2023-39345-2192]`, `test_with_the_override_current_debt_on_the_balance_sheet_still_counts` and 1 more |
| RES-minority-gap | §8.3 | minority interest reported for FY-1 but not FY0 treated as nil | 2: `test_a_minority_interest_reported_for_the_year_before_but_not_this_year_is_missing_not_nil`, `test_total_equity_above_equity_without_a_minority_interest_tag_is_recorded` |
| RES-bridge-year | §8.3 | wrong year: bridge items of the oldest fiscal year | 7: `test_an_absent_bridge_item_is_treated_as_nil_and_labelled`, `test_a_reported_bridge_item_is_used` and 5 more |
| RES-bridge-kind | §8.3 | an absent bridge item labelled reported instead of assumption | 1: `tests/integration/test_resolver_demo.py` |
| RES-untagged-sign | §8.3 | comparison reversed: MINORITY_UNTAGGED when total equity is not above equity | 2: `test_total_equity_above_equity_without_a_minority_interest_tag_is_recorded`, `test_total_equity_within_1_percent_of_equity_is_not_recorded` |
| RES-untagged-abs | §8.3 | abs dropped: with negative equity any difference is flagged | **none at first**; now 1: `test_negative_equity_within_1_percent_of_total_equity_is_not_recorded` |
| RES-minority-gap-year | §8.3 | wrong year: the minority gap looks at FY0 instead of FY-1 | 1: `test_a_minority_interest_reported_for_the_year_before_but_not_this_year_is_missing_not_nil` |
| RES-cover-day0 | shares | comparison: a cover count dated on the fiscal year end accepted | **none at first**; now 1: `test_a_cover_count_dated_on_the_fiscal_year_end_is_not_the_latest_annual_reports` |
| RES-cover-200 | shares | comparison: a cover count exactly 200 days after the year end refused | **none at first**; now 1: `test_a_cover_count_is_used_up_to_200_days_after_the_year_end[2026-07-19-True]` |
| RES-cover-window | shares | window removed: a stale cover count used (Mastercard) | 1: `test_a_cover_page_count_from_an_older_annual_report_is_not_used` |
| RES-cover-earliest | shares | wrong filing: the earliest cover count in the window | **none at first**; now 1: `test_the_cover_count_of_an_amended_annual_report_wins` |
| RES-shares-plausible | shares | guard removed: an average filed in millions used | 1: `test_an_implausibly_small_share_count_is_missing` |
| RES-shares-plausible-eq | shares | comparison: exactly 100,000 shares refused | **none at first**; now 1: `test_an_average_of_exactly_100000_shares_is_plausible` |
| RES-average-warning | shares | AVERAGE_SHARES warning dropped | 2: `test_without_a_cover_page_count_the_diluted_average_is_used_with_a_warning`, `test_a_cover_page_count_from_an_older_annual_report_is_not_used` |
| RES-shares-year | shares | wrong year: shares looked up against FY-1 | 6: `test_shares_come_from_the_cover_page_of_the_latest_annual_report`, `test_without_a_cover_page_count_the_diluted_average_is_used_with_a_warning` and 4 more |
| RES-latest-10k | company | wrong date: the earliest 10-K filing date as the latest | 9: `test_ac16_coca_cola_key_figures_coverage_and_balance_sheet_are_shown`, `test_ac16_coca_cola_filing_details` and 7 more |
| RES-latest-10k-forms | company | a 10-Q date counted as the latest 10-K | **none at first**; now 1: `test_the_latest_10k_date_ignores_a_later_quarterly_report` |
| RES-cik-pad | company | company number not padded to 10 digits | **none at first**; now 1: `test_a_short_company_number_is_padded_to_ten_digits` |

104 breaks, 80 caught by the earlier tests.

### Tag map (`app/src/data/tag_map.yaml`)

| Break | Check | What was broken | Caught by (failing tests) |
|---|---|---|---|
| TAG-revenue-order | tag map | wrong tag order: revenue from contracts before Revenues | **none at first**; now 1: `test_the_tag_listed_first_in_spec_6_is_used_when_both_are_filed[revenue-filed0-1040000000]` |
| TAG-capex-order | tag map | wrong tag order: productive assets before PP&E | **none at first**; now 1: `test_the_tag_listed_first_in_spec_6_is_used_when_both_are_filed[capital_expenditure-filed1-85000000]` |
| TAG-netincome-order | tag map | wrong tag order: ProfitLoss (with minority share) first | 7: `test_ac16_coca_cola_key_figures_coverage_and_balance_sheet_are_shown`, `test_ac16_coca_cola_overview` and 5 more |
| TAG-dividend-ordinary | tag map | tag dropped: PaymentsOfOrdinaryDividends | 1: `test_dividends_filed_as_payments_of_ordinary_dividends_are_found` |
| TAG-interest-order | tag map | wrong tag order: InterestAndDebtExpense first | 1: `test_interest_and_debt_expense_only_fills_gaps_after_the_debt_interest_tag` |
| TAG-cash-order | tag map | wrong tag order: cash including restricted cash first | **none at first**; now 1: `test_the_tag_listed_first_in_spec_6_is_used_when_both_are_filed[cash-filed2-100000000]` |
| TAG-debt-total | tag map | tag dropped: LongTermDebt as the long-term total | 18: `test_mcdonalds_debt_matches_its_balance_sheets[2025-39973-0]`, `test_mcdonalds_debt_matches_its_balance_sheets[2024-38424-0]` and 16 more |
| TAG-debt-noncurrent-order | tag map | wrong tag order: debt with finance leases first (non-current) | **none at first**; now 1: `test_the_tag_listed_first_in_spec_6_is_used_when_both_are_filed[financial_debt-filed3-450000000]` |
| TAG-mcd-da | tag map | McDonald's D&A override removed | 1: `test_mcdonalds_depreciation_is_the_cash_flow_statement_total` |
| TAG-mcd-debt | tag map | McDonald's debt override switched off | 3: `test_mcdonalds_debt_matches_its_balance_sheets[2025-39973-0]`, `test_mcdonalds_debt_matches_its_balance_sheets[2024-38424-0]` and 1 more |
| TAG-positive-only | tag map | interest expense no longer positive-only | 1: `test_planted_a_negative_interest_expense_is_flagged_and_not_used` |
| TAG-capex-outflow | tag map | capital expenditure no longer an outflow (no SIGN warning) | 1: `test_planted_a_negative_capital_expenditure_is_kept_as_filed_and_flagged` |
| TAG-revenue-samedef | tag map | revenue fallbacks treated as the same definition | **none at first**; now 1: `test_the_tag_listed_first_in_spec_6_is_used_when_both_are_filed[revenue-filed0-1040000000]` |
| TAG-later-larger | tag map | later-larger limit for interest 500% instead of 50% | 1: `test_interest_net_of_interest_income_is_caught_by_a_much_larger_later_tag` |
| TAG-nil-evidence | tag map | declared-dividend tags dropped from the evidence list | 1: `test_a_dividend_declared_per_share_is_evidence_and_the_years_stay_missing` |
| TAG-cover-tag | tag map | cover-page share tag misspelt: never found | 10: `test_every_demo_company_resolves_five_fiscal_years[KO]`, `test_every_demo_company_resolves_five_fiscal_years[AAPL]` and 8 more |
| TAG-average-basic | tag map | wrong tag: basic instead of diluted average shares | 3: `test_without_a_cover_page_count_the_diluted_average_is_used_with_a_warning`, `test_a_cover_page_count_from_an_older_annual_report_is_not_used` and 1 more |
| TAG-da-parts-order | tag map | D&A parts swapped: amortisation required, depreciation optional | 4: `test_depreciation_alone_is_used_when_no_amortisation_is_reported_and_says_so`, `test_amortisation_alone_does_not_make_a_depreciation_figure` and 2 more |
| TAG-liab-less | tag map | temporary-equity tags removed from total liabilities | 1: `test_derived_liabilities_leave_out_temporary_equity` |

19 breaks, 14 caught by the earlier tests.

### A's settings (`app/settings.yaml`, section `data`)

| Break | Check | What was broken | Caught by (failing tests) |
|---|---|---|---|
| SET-flow-min | settings | flow period minimum 365 days: 52-week years dropped | 199: `test_ac16_coca_cola_key_figures_coverage_and_balance_sheet_are_shown`, `test_company_figures_keep_fiscal_year_ended` and 197 more |
| SET-years | settings | four fiscal years instead of five | 28: `test_ac16_coca_cola_key_figures_coverage_and_balance_sheet_are_shown`, `test_amazon_pays_no_dividend_labelled_as_nil_in_every_year` and 26 more |
| SET-restated | settings | restatement warning at 10% instead of 1% | 2: `test_coca_cola_2018_revenue_restatement_as_shown_in_session_5`, `test_planted_a_restated_figure_uses_the_latest_filing_and_keeps_the_original` |
| SET-cover | settings | cover-page window 400 days instead of 200 | **none at first**; now 1: `test_a_cover_count_is_used_up_to_200_days_after_the_year_end[2026-07-20-False]` |
| SET-min-shares | settings | minimum plausible share count 0 | 1: `test_an_implausibly_small_share_count_is_missing` |
| SET-rf-years | settings | risk-free average over ten years instead of five | **none at first**; now 1: `test_the_real_settings_average_five_years` |
| SET-forms | settings | 10-Q added to the annual forms | 4: `test_figures_from_quarterly_reports_are_ignored`, `test_shares_come_from_the_cover_page_of_the_latest_annual_report` and 2 more |
| SET-rate | settings | 20 requests per second, above the SEC's limit | 2: `test_the_real_settings_are_five_per_second_and_three_retries`, `test_settings_are_loaded_as_plain_values_per_section` |
| SET-retries | settings | no retries | 1: `test_the_real_settings_are_five_per_second_and_three_retries` |
| SET-tag-conflict | settings | tag conflict warning at 50% instead of 1% | 1: `test_two_tags_with_different_values_are_flagged_and_the_first_in_the_list_is_used` |
| SET-debt-check | settings | debt check at 10% instead of 1% | 1: `test_a_total_that_disagrees_with_its_parts_is_flagged` |

11 breaks, 9 caught by the earlier tests.

### Entry point (`app/src/data/company.py`)

| Break | Check | What was broken | Caught by (failing tests) |
|---|---|---|---|
| COM-demo-guard | demo | guard removed: any folder name reaches the file system (KO/../AAPL) | 3: `test_demo_mode_only_opens_the_listed_demo_companies[KO/../AAPL]`, `test_demo_mode_only_opens_the_listed_demo_companies[MCD/]` and 1 more |
| COM-upper | demo | ticker not upper-cased | 1: `test_demo_mode_still_opens_the_demo_companies_however_they_are_typed` |
| COM-retrieved-file | demo | wrong file: retrieval time of submissions.json instead of companyfacts.json | **none at first**; now 1: `test_demo_data_carry_the_retrieval_time_of_the_company_facts` |
| COM-demo-years | demo | years not passed on in demo mode | 1: `test_coca_cola_2018_revenue_restatement_as_shown_in_session_5` |
| COM-live-retrieved | live | wrong file: live retrieval time of the submissions | **none at first**; now 1: `test_live_data_carry_the_retrieval_time_of_the_company_facts` |
| COM-live-years | live | years not passed on live | **none at first**; now 1: `test_live_data_keep_the_number_of_years_asked_for` |

6 breaks, 3 caught by the earlier tests.

### Risk-free rate (`app/src/data/fred.py`)

| Break | Check | What was broken | Caught by (failing tests) |
|---|---|---|---|
| FRED-window-year | S2b | off by one: four-year window instead of five | 3: `test_the_request_asks_for_five_years_of_dgs10_with_the_key_as_a_parameter`, `test_the_window_follows_the_setting` and 1 more |
| FRED-window-feb29 | S2b | 29 February becomes 1 February | 1: `test_five_years_before_29_february_is_28_february` |
| FRED-percent | S2b | units: percent not divided by 100 | 14: `test_the_rate_is_the_average_of_the_days_with_a_value`, `test_the_rate_is_the_mean_not_the_middle_value` and 12 more |
| FRED-denominator | S2b | wrong denominator: one day too many | 9: `test_the_rate_is_the_average_of_the_days_with_a_value`, `test_the_rate_is_the_mean_not_the_middle_value` and 7 more |
| FRED-dot-zero | S2b | missing is never zero: a day without a value read as 0% | 6: `test_the_rate_is_the_average_of_the_days_with_a_value`, `test_the_rate_is_the_mean_not_the_middle_value` and 4 more |
| FRED-plausible-low | S2b | comparison: an average of exactly 0% accepted | 1: `test_an_average_outside_0_to_20_percent_is_not_used[zero]` |
| FRED-plausible-high | S2b | comparison: an average of exactly 20% accepted | 1: `test_an_average_outside_0_to_20_percent_is_not_used[20` |
| FRED-plausible | S2b | guard removed: any average accepted | 5: `test_an_average_outside_0_to_20_percent_is_not_used[negative]`, `test_an_average_outside_0_to_20_percent_is_not_used[zero]` and 3 more |
| FRED-finite | S2b | guard removed: a value that is not a finite number accepted | 1: `test_an_unusable_answer_uses_the_saved_value[NaN]` |
| FRED-duplicate-day | S2b | guard removed: a day appearing twice accepted | 1: `test_an_unusable_answer_uses_the_saved_value[same` |
| FRED-empty | S2b | guard removed: an answer without values | 2: `test_an_unusable_answer_uses_the_saved_value[empty]`, `test_an_unusable_answer_uses_the_saved_value[only` |
| FRED-unsorted | S2b | days not sorted: first and last day wrong | 1: `test_rows_out_of_date_order_give_the_same_rate_and_period` |
| FRED-period-swap | S2b | inputs swapped: period start and end | 11: `test_the_rate_is_the_average_of_the_days_with_a_value`, `test_the_rate_is_the_mean_not_the_middle_value` and 9 more |
| FRED-memory | S2b | memory ignored: every call downloads again | 1: `test_one_download_per_day` |
| FRED-pause-ignored | S2b | pause after a failure ignored | 1: `test_after_a_failed_download_fred_is_asked_again_only_after_ten_minutes` |
| FRED-pause-reversed | S2b | comparison reversed: pause applies only after it has ended | 1: `test_after_a_failed_download_fred_is_asked_again_only_after_ten_minutes` |
| FRED-pause-length | S2b | no pause recorded after a failure | 1: `test_after_a_failed_download_fred_is_asked_again_only_after_ten_minutes` |
| FRED-pause-60 | S2b | pause of one minute instead of ten | **none at first**; now 1: `test_the_pause_after_a_failure_is_ten_minutes` |
| FRED-demo | S2b | demo mode downloads | 5: `test_demo_mode_after_a_live_download_still_uses_the_saved_value`, `test_a_live_download_after_demo_mode_is_not_the_saved_value` and 3 more |
| FRED-no-saved-zero | S2b | missing is never zero: no saved value gives 0% | 1: `test_without_a_saved_value_the_rate_is_missing_not_zero` |
| FRED-key-format | S2b | guard removed: a key in the wrong format used | 1: `test_a_key_in_the_wrong_format_is_never_sent` |
| FRED-key-quotes | S2b | quotes around the key not removed | **none at first**; now 1: `test_quotes_around_the_key_in_the_environment_are_removed` |
| FRED-key-in-message | S2b, secret | secret: the key written into the reason | 1: `test_a_key_in_the_wrong_format_is_never_sent` |
| FRED-error-details | S2b, secret | secret: an unexpected error's message kept (may hold the address with the key) | 1: `test_the_key_appears_nowhere_in_the_result[any` |
| FRED-request-error | S2b, secret | secret: the web library's error message kept | 1: `test_the_key_appears_nowhere_in_the_result[no` |
| FRED-redirects | S2b, secret | redirects followed (the key would go to another address) | 1: `test_the_request_asks_for_five_years_of_dgs10_with_the_key_as_a_parameter` |
| FRED-status | S2b | guard removed: an HTTP error answer read | 2: `test_an_unusable_answer_uses_the_saved_value[key`, `test_an_unusable_answer_uses_the_saved_value[server` |
| FRED-env-ignored | S2b | the key in the environment ignored | 1: `test_the_key_can_come_from_the_environment` |
| FRED-bom | S2b | a settings file saved with a byte-order mark not read | **none**; not observable, see the dismissals below |
| FRED-timeout | S2b | no time limit on the request | 1: `test_the_request_asks_for_five_years_of_dgs10_with_the_key_as_a_parameter` |

30 breaks, 27 caught by the earlier tests.

### SEC client (`app/src/data/sec_client.py`)

| Break | Check | What was broken | Caught by (failing tests) |
|---|---|---|---|
| SEC-agent-header | SPEC §4 | User-Agent not sent | 2: `test_every_request_carries_the_declared_user_agent`, `test_the_user_agent_does_not_show_in_the_client_or_its_errors` |
| SEC-limiter-no-pause | SPEC §4 | rate limiter never pauses | 3: `test_requests_are_spaced_to_at_most_five_per_second`, `test_two_clients_sharing_the_app_s_limiter_stay_within_the_limit` and 1 more |
| SEC-limiter-interval | SPEC §4 | wrong interval: twice the allowed rate | 3: `test_requests_are_spaced_to_at_most_five_per_second`, `test_two_clients_sharing_the_app_s_limiter_stay_within_the_limit` and 1 more |
| SEC-limiter-first | SPEC §4 | pause measured from the first request only | 2: `test_requests_are_spaced_to_at_most_five_per_second`, `test_the_limits_come_from_settings_yaml` |
| SEC-max-limit | SPEC §4 | guard removed: more than 10 requests per second accepted | 1: `test_impossible_limits_are_refused_when_the_client_is_made[options1]` |
| SEC-max-10 | SPEC §4 | comparison: exactly 10 per second refused | **none at first**; now 1: `test_ten_requests_per_second_the_secs_own_limit_is_allowed` |
| SEC-retries-off-by-one | SPEC §4 | off by one: three attempts instead of four | 6: `test_the_limits_come_from_settings_yaml`, `test_after_three_retries_the_source_is_unreachable_and_the_message_says_what_to_do` and 4 more |
| SEC-backoff | SPEC §4 | pause between retries always 1 second | 5: `test_a_temporary_failure_is_retried_with_a_growing_pause`, `test_after_three_retries_the_source_is_unreachable_and_the_message_says_what_to_do` and 3 more |
| SEC-sleep-last | SPEC §4 | a pause after the last attempt too | 6: `test_the_limits_come_from_settings_yaml`, `test_after_three_retries_the_source_is_unreachable_and_the_message_says_what_to_do` and 4 more |
| SEC-429 | SPEC §4 | HTTP 429 (too many requests) not retried | 1: `test_a_temporary_failure_is_retried_with_a_growing_pause` |
| SEC-403 | SPEC §4 | HTTP 403 no longer SecRefused | 1: `test_a_refusal_by_the_sec_is_not_retried_and_points_to_the_user_agent` |
| SEC-404 | SPEC §4 | HTTP 404 no longer NotFound | 1: `test_a_page_that_does_not_exist_is_not_retried` |
| SEC-not-json | SPEC §4 | an answer that is not JSON accepted | 3: `test_an_answer_that_is_not_a_json_object_is_retried_then_unreachable_and_never_cached[<html>Request`, `test_an_answer_that_is_not_a_json_object_is_retried_then_unreachable_and_never_cached[null]` and 1 more |
| SEC-cache-checksum | SPEC §4 | cache checksum not checked: a damaged entry used | 1: `test_a_damaged_cache_entry_is_downloaded_again[other_raw]` |
| SEC-cache-source | SPEC §4 | cache source not checked: another address's file reused | **none at first**; now 1: `test_a_cache_entry_saved_for_another_address_is_downloaded_again` |
| SEC-refresh | SPEC §4 | refresh ignored: always the cache | 2: `test_refresh_downloads_again_and_replaces_the_cache`, `test_a_refreshed_ticker_list_is_used_for_lookups` |
| SEC-cik-11 | SPEC §4 | an 11-digit company number accepted | 1: `test_a_malformed_sec_number_is_refused[12345678901]` |
| SEC-cik-pad | SPEC §4 | company number not padded to 10 digits | 7: `test_the_user_agent_does_not_show_in_the_client_or_its_errors`, `test_a_page_that_does_not_exist_is_not_retried` and 5 more |
| SEC-ticker-dot | SPEC §4 | BRK.B not normalised to BRK-B | 2: `test_a_class_share_ticker_with_a_dot_is_found`, `test_a_ticker_listed_twice_for_different_companies_is_reported_not_guessed` |
| SEC-ambiguous | SPEC §4 | guard removed: a ticker matching two companies takes the first | 1: `test_a_ticker_listed_twice_for_different_companies_is_reported_not_guessed` |
| SEC-agent-example | SPEC §4 | the example User-Agent accepted | 1: `test_a_missing_example_or_unreadable_user_agent_is_refused_without_showing_it[Firstname` |
| SEC-agent-control | SPEC §4, secret | guard removed: a line break in the User-Agent (header injection) | **none at first**; now 2: `test_a_line_break_or_delete_character_is_refused_even_where_the_pattern_would_match[Test`, `test_a_line_break_or_delete_character_is_refused_even_where_the_pattern_would_match[Test\x7fPerson` |
| SEC-agent-del | SPEC §4 | the DEL character accepted in the User-Agent | **none at first**; now 1: `test_a_line_break_or_delete_character_is_refused_even_where_the_pattern_would_match[Test\x7fPerson` |
| SEC-agent-ascii | SPEC §4 | a curly quote or accent accepted in the User-Agent | 2: `test_a_missing_example_or_unreadable_user_agent_is_refused_without_showing_it[Test`, `test_a_missing_example_or_unreadable_user_agent_is_refused_without_showing_it[J\xfcrgen` |
| SEC-agent-email | SPEC §4 | no e-mail required in the User-Agent | 1: `test_a_missing_example_or_unreadable_user_agent_is_refused_without_showing_it[Test` |
| SEC-agent-repr | secret | secret: the User-Agent shown in a repr | 1: `test_the_user_agent_does_not_show_in_the_client_or_its_errors` |
| SEC-agent-in-message | secret | secret: the User-Agent written into the error message | 3: `test_a_missing_example_or_unreadable_user_agent_is_refused_without_showing_it[Firstname`, `test_a_missing_example_or_unreadable_user_agent_is_refused_without_showing_it[Test` and 1 more |
| SEC-agent-env | SPEC §4 | the User-Agent in the environment ignored | 3: `test_the_user_agent_comes_from_the_environment_or_the_env_file`, `test_the_limits_come_from_settings_yaml` and 1 more |
| SEC-utf16 | SPEC §4 | a UTF-16 settings file read as if UTF-8 | **none**; not observable, see the dismissals below |
| SEC-agent-quotes | SPEC §4 | quotes around the User-Agent not removed | 2: `test_quotes_around_the_user_agent_are_removed["Test`, `test_quotes_around_the_user_agent_are_removed['Test` |
| SEC-bom | SPEC §4 | a settings file with a byte-order mark: the mark kept | **none**; not observable, see the dismissals below |
| SEC-timeout | SPEC §4 | no time limit on the request | 1: `test_every_request_carries_the_declared_user_agent` |

32 breaks, 26 caught by the earlier tests.

### Overview (`app/src/overview.py`, S10c)

| Break | Check | What was broken | Caught by (failing tests) |
|---|---|---|---|
| OV-bn-1 | S10c | comparison: exactly USD 1 bn written in millions | 1: `test_amounts_switch_to_billions_from_one_billion[1000-USD` |
| OV-bn-abs | S10c | abs dropped: a loss of billions written in millions | 1: `test_amounts_switch_to_billions_from_one_billion[-1500-USD` |
| OV-minus | S10c | a hyphen instead of the minus sign | 2: `test_negative_free_cash_flow_shows_both_amounts_and_no_percentage`, `test_amounts_switch_to_billions_from_one_billion[-1500-USD` |
| OV-bn-decimals | S10c | billions with one decimal instead of two | 10: `test_ac16_coca_cola_key_figures_coverage_and_balance_sheet_are_shown`, `test_the_chart_has_a_table_view_with_the_same_figures` and 8 more |
| OV-m-scale | S10c | wrong denominator: millions divided by a thousand | 9: `test_the_chart_has_a_table_view_with_the_same_figures`, `test_synthetic_key_figures_with_their_change_on_the_year_before` and 7 more |
| OV-fcf-sign | S10c | sign: free cash flow = cash flow + capex | 11: `test_ac16_coca_cola_key_figures_coverage_and_balance_sheet_are_shown`, `test_the_chart_has_a_table_view_with_the_same_figures` and 9 more |
| OV-fcf-negative-capex | S10c | guard removed: a negative capex used | 1: `test_negative_capital_expenditure_is_a_sign_error_not_a_bigger_cash_flow` |
| OV-fcf-missing-zero | S10c | missing is never zero: missing capex read as zero | **none at first**; now 1: `test_missing_capital_expenditure_leaves_free_cash_flow_open_never_zero` |
| OV-margin-zero-revenue | S10c | comparison: margin on zero revenue | 1: `test_revenue_at_zero_gives_no_margin` |
| OV-margin-swap | S10c | inputs swapped: revenue / operating income | 3: `test_ac16_coca_cola_key_figures_coverage_and_balance_sheet_are_shown`, `test_synthetic_key_figures_with_their_change_on_the_year_before` and 1 more |
| OV-pp-scale | S10c | units: margin change not in percentage points | 3: `test_ac16_coca_cola_key_figures_coverage_and_balance_sheet_are_shown`, `test_synthetic_key_figures_with_their_change_on_the_year_before` and 1 more |
| OV-change-zero-base | S10c | comparison: a change from zero computed | 1: `test_a_prior_year_of_exactly_zero_gives_not_meaningful` |
| OV-change-denominator | S10c | wrong denominator: change divided by the latest year | 5: `test_ac16_coca_cola_key_figures_coverage_and_balance_sheet_are_shown`, `test_synthetic_key_figures_with_their_change_on_the_year_before` and 3 more |
| OV-change-unrounded | S10c | direction from the unrounded change (+0.0% shown as up) | **none at first**; now 1: `test_a_change_that_rounds_to_zero_is_shown_without_an_arrow` |
| OV-pp-unrounded | S10c | margin direction from the unrounded change | **none at first**; now 1: `test_a_change_that_rounds_to_zero_is_shown_without_an_arrow` |
| OV-fy1 | S10c | wrong year: change against two years earlier | 6: `test_ac16_coca_cola_key_figures_coverage_and_balance_sheet_are_shown`, `test_synthetic_key_figures_with_their_change_on_the_year_before` and 4 more |
| OV-oldest-five | S10c | wrong years: the oldest five fiscal years | **none at first**; now 1: `test_with_six_fiscal_years_the_overview_covers_the_latest_five` |
| OV-fy0 | S10c | wrong year: FY0 is the oldest of the five | 25: `test_ac16_coca_cola_key_figures_coverage_and_balance_sheet_are_shown`, `test_ac18_a_missing_figure_shows_na_with_its_reason_never_zero` and 23 more |
| OV-margin-decimals | S10c | margin with no decimal | 3: `test_ac16_coca_cola_key_figures_coverage_and_balance_sheet_are_shown`, `test_synthetic_key_figures_with_their_change_on_the_year_before` and 1 more |
| OV-key-missing-zero | S10c | missing is never zero: a missing key figure shown as 0 | 3: `test_ac18_missing_operating_cash_flow_leaves_free_cash_flow_and_coverage_open`, `test_revenue_at_zero_gives_no_margin` and 1 more |
| OV-series-scale | S10c | comparison: a series peaking at exactly USD 1 bn in millions | **none at first**; now 1: `test_a_series_reaching_exactly_one_billion_is_drawn_in_billions` |
| OV-series-gap-zero | S10c | missing is never zero: a gap in the chart drawn as zero | 1: `test_ac18_missing_operating_cash_flow_leaves_free_cash_flow_and_coverage_open` |
| OV-series-table-zero | S10c | missing is never zero: a gap in the table written as USD 0 m | 1: `test_ac18_missing_operating_cash_flow_leaves_free_cash_flow_and_coverage_open` |
| OV-series-abs | S10c | abs dropped: a large loss does not set the scale | **none at first**; now 1: `test_a_loss_of_more_than_one_billion_sets_the_scale_too` |
| OV-end-label | S10c | wrong year: the end label shows the first value | 2: `test_each_line_carries_its_last_value_for_the_end_of_the_chart`, `test_a_missing_last_value_has_no_end_label` |
| OV-years-label | S10c | off by one: chart years one year early | 2: `test_the_chart_has_a_table_view_with_the_same_figures`, `test_synthetic_five_years_of_free_cash_flow` |
| OV-fy-label | S10c | off by one: FY label one year late | 5: `test_ac16_coca_cola_key_figures_coverage_and_balance_sheet_are_shown`, `test_ac18_a_missing_figure_shows_na_with_its_reason_never_zero` and 3 more |
| OV-years-text | S10c | wrong year: the years covered start at FY-3 | 1: `test_the_fiscal_year_end_and_the_years_covered_are_written_for_the_header` |
| OV-cov-negative-dividend | S10c | guard removed: negative dividends read as a payment | 1: `test_negative_dividends_are_a_sign_error_never_no_dividend_paid` |
| OV-cov-zero-dividend | S10c | guard removed: zero dividends divided by | 9: `test_ac17_amazon_shows_no_dividend_paid`, `test_amazon_panel_says_no_dividend_paid` and 7 more |
| OV-cov-equal | S10c | comparison: free cash flow equal to dividends not covering | 1: `test_free_cash_flow_equal_to_the_dividends_covers_them_exactly` |
| OV-cov-ratio | S10c | inputs swapped: dividends / free cash flow | 5: `test_ac16_coca_cola_key_figures_coverage_and_balance_sheet_are_shown`, `test_synthetic_dividend_coverage` and 3 more |
| OV-cov-share-cap | S10c | bar share not limited to 1 | 1: `test_synthetic_dividend_coverage` |
| OV-cov-bar-cap | S10c | bar width not limited to 100% | 1: `test_synthetic_dividend_coverage` |
| OV-cov-gap-abs | S10c | abs dropped: a negative gap | 3: `test_ac16_coca_cola_key_figures_coverage_and_balance_sheet_are_shown`, `test_ac16_coca_cola_overview` and 1 more |
| OV-cov-zero-fcf | S10c | comparison: free cash flow of zero called negative | 1: `test_free_cash_flow_of_exactly_zero_covers_none_of_the_dividends` |
| OV-cov-negative-gap | S10c | term dropped: gap with negative free cash flow is the dividends alone | 1: `test_negative_free_cash_flow_shows_both_amounts_and_no_percentage` |
| OV-cov-reason | S10c | reason for missing coverage dropped | **none at first**; now 1: `test_missing_dividends_give_the_reason_coverage_is_not_available` |
| OV-cov-comma | S10c | coverage percent without thousands comma | 1: `test_coverage_above_1000_percent_is_written_with_a_thousands_separator` |
| OV-cov-equal-label | S10c | equal free cash flow and dividends labelled 'above' | 1: `test_free_cash_flow_equal_to_the_dividends_covers_them_exactly` |
| OV-current-zero | S10c | comparison: current ratio with zero current liabilities | 1: `test_current_liabilities_at_zero_give_no_current_ratio` |
| OV-current-swap | S10c | inputs swapped: current liabilities / current assets | 3: `test_ac16_coca_cola_key_figures_coverage_and_balance_sheet_are_shown`, `test_synthetic_balance_sheet_figures` and 1 more |
| OV-balance-missing-zero | S10c | missing is never zero: a missing balance figure shown as USD 0 m | 1: `test_a_figure_with_no_entry_at_all_is_missing_never_zero` |
| OV-filing-records | S10c | records counted as line items | 2: `test_ac16_coca_cola_key_figures_coverage_and_balance_sheet_are_shown`, `test_ac16_coca_cola_filing_details` |
| OV-day-format | S10c | dates with a leading zero (01 January) | **none at first**; now 1: `test_dates_are_written_without_a_leading_zero` |
| OV-area-denominator | S10c | wrong denominator: passed ÷ six checks instead of ÷ assessed | 3: `test_the_share_of_assessed_checks_passed_per_area_for_the_radar`, `test_the_radar_closes_and_fills_only_when_all_four_areas_are_scored` and 1 more |
| OV-area-na-on-shape | S10c | an area with a not-applicable check put on the radar | 3: `test_the_radar_labels_each_area_with_its_share_or_why_it_is_off_the_shape`, `test_an_area_with_a_check_that_does_not_apply_stays_off_the_radar` and 1 more |
| OV-area-unassessed | S10c | an area with nothing assessed put on the radar | 29: `test_the_panel_shows_the_radar_and_explains_it_without_repeating_the_marks`, `test_the_radar_labels_each_area_with_its_share_or_why_it_is_off_the_shape` and 27 more |
| OV-area-count | S10c | wrong denominator: 'of 6 assessed' counts every check | 2: `test_an_area_with_a_check_that_does_not_apply_stays_off_the_radar`, `test_no_dividend_counts_one_assessed_check_and_five_that_do_not_apply` |
| OV-area-share-text | S10c | share truncated instead of rounded (2/3 shown as 66%) | 1: `test_the_share_of_assessed_checks_passed_per_area_for_the_radar` |
| OV-marks-insufficient | S10c | insufficient data marked as a fail | 1: `test_each_area_lists_its_six_marks_in_order` |
| OV-radar-filled | S10c | radar filled with three areas | 19: `test_the_panel_shows_the_radar_and_explains_it_without_repeating_the_marks`, `test_the_radar_fills_only_a_complete_shape_and_never_draws_through_the_centre` and 17 more |
| OV-radar-edges | S10c | an area off the shape crossed: scored areas joined across the gap | 3: `test_the_radar_fills_only_a_complete_shape_and_never_draws_through_the_centre`, `test_an_area_off_the_shape_breaks_the_line_at_its_axis_never_through_the_centre` and 1 more |

53 breaks, 45 caught by the earlier tests.

### Overview charts (`charts()` and `_fixed`, S10d, PR #70's head 1181e53)

| Break | Check | What was broken | Caught by (failing tests) |
|---|---|---|---|
| CH-fixed-half-even | _fixed | a half rounded to even (34.265 → 34.26) | 2: `test_end_labels_of_lines_ending_close_together_do_not_overlap`, `test_a_line_end_label_rounds_a_half_as_the_texts_do` |
| CH-fixed-half-down | _fixed | a half rounded down | 4: `test_end_labels_of_lines_ending_close_together_do_not_overlap`, `test_coca_cola_balance_sheet_split` and 2 more |
| CH-fixed-binary | _fixed | the stored binary value rounded (34.275 → 34.27) | 2: `test_coca_cola_balance_sheet_split`, `test_a_line_end_label_rounds_a_half_as_the_texts_do` |
| CH-fixed-comma | _fixed | no thousands comma | **none at first**; now 1: `test_amounts_per_share_of_a_thousand_or_more_have_a_thousands_comma` |
| CH-percent-minus | writers | a hyphen instead of the minus sign in percentages | **none at first**; now 1: `test_negative_percentages_and_ratios_use_the_minus_sign` |
| CH-times-decimals | writers | ratios with one decimal instead of two | 2: `test_the_valuation_comes_first_with_the_price_against_the_estimate`, `test_price_ratios_against_the_industry_and_the_market` |
| CH-per-share-decimals | writers | per-share amounts with one decimal instead of two | 3: `test_the_valuation_comes_first_with_the_price_against_the_estimate`, `test_the_share_price_against_the_estimate_with_its_zones` and 1 more |
| CH-versus-equal | writers | comparison: equal values called above | **none at first**; now 1: `test_short_term_assets_equal_to_short_term_liabilities_read_equal_to` |
| CH-scaled | writers | comparison: a chart peaking at exactly USD 1 bn in millions | **none at first**; now 1: `test_a_chart_reaching_exactly_one_billion_is_drawn_in_billions` |
| CH-flow-zero-revenue | money flow | comparison: zero revenue accepted | **none at first**; now 1: `test_revenue_of_zero_gives_no_flow_chart` |
| CH-flow-zero-profit | money flow | comparison: a profit of zero accepted | **none at first**; now 1: `test_an_operating_profit_of_zero_gives_no_flow_chart` |
| CH-flow-income-above | money flow | guard removed: operating income above revenue | **none at first**; now 1: `test_operating_income_above_revenue_gives_no_flow_chart` |
| CH-flow-gross-range | money flow | guard removed: gross profit outside operating income to revenue | **none at first**; now 1: `test_a_gross_profit_above_revenue_is_not_drawn_as_a_step` |
| CH-flow-cost-of-revenue | money flow | wrong term: cost of revenue = revenue − operating income | 1: `test_coca_cola_revenue_flows_through_gross_profit` |
| CH-flow-opex | money flow | wrong term: operating expenses = revenue − operating income | 1: `test_coca_cola_revenue_flows_through_gross_profit` |
| CH-flow-share | money flow | wrong denominator: net income ÷ operating income | 3: `test_every_area_has_its_charts_and_each_chart_says_what_it_shows`, `test_the_synthetic_company_revenue_flows_to_net_income_in_one_cost_step` and 1 more |
| CH-flow-net-equal | money flow | comparison: net income equal to operating income takes the other-income branch | **none at first**; now 1: `test_net_income_equal_to_operating_income_has_no_other_step` |
| CH-flow-interest-sign | money flow | sign: interest, tax and other = net − operating income | 2: `test_the_synthetic_company_revenue_flows_to_net_income_in_one_cost_step`, `test_coca_cola_revenue_flows_through_gross_profit` |
| CH-flow-zero-flows | money flow | zero flows drawn | **none at first**; now 1: `test_net_income_equal_to_operating_income_has_no_other_step` |
| CH-flow-derived-note | money flow | the worked-out gross profit not said | 1: `test_a_worked_out_gross_profit_says_so_under_the_flow` |
| CH-position-guard | position | guard removed: total liabilities below current liabilities | **none at first**; now 1: `test_total_liabilities_below_current_liabilities_leave_long_term_open` |
| CH-position-long | position | term dropped: long-term liabilities = total liabilities | 2: `test_financial_position_of_the_synthetic_company`, `test_financial_position_of_coca_cola_in_billions` |
| CH-parts-negative | split | guard removed: a negative part drawn | **none at first**; now 1: `test_a_negative_part_is_named_as_not_in_the_data` |
| CH-parts-zero | split | a part of zero drawn | 1: `test_the_synthetic_balance_sheet_split` |
| CH-parts-rest-whole | split | wrong total: other liabilities from total assets | 3: `test_the_synthetic_balance_sheet_split`, `test_coca_cola_balance_sheet_split` and 1 more |
| CH-parts-overlap | split | overlap note dropped | 1: `test_parts_larger_than_the_total_leave_no_negative_other_part` |
| CH-parts-share | split | wrong denominator: share of the side's own total | 4: `test_ac17_amazon_shows_no_dividend_paid`, `test_the_synthetic_balance_sheet_split` and 2 more |
| CH-split-zero-assets | split | comparison: total assets of zero accepted | **none at first**; now 1: `test_total_assets_of_zero_give_no_split` |
| CH-split-equity-sign | split | sign: equity = liabilities − assets | 3: `test_the_synthetic_balance_sheet_split`, `test_coca_cola_balance_sheet_split` and 1 more |
| CH-split-equity-zero | split | comparison: equity of zero drawn | **none at first**; now 1: `test_equity_of_exactly_zero_is_said_and_not_drawn` |
| CH-split-minority-label | split | minority label reversed | 2: `test_the_synthetic_balance_sheet_split`, `test_coca_cola_balance_sheet_split` |
| CH-split-claims-total | split | claims total always total assets (wrong with negative equity) | 1: `test_negative_equity_is_said_in_words_and_never_drawn_as_a_part` |
| CH-debt-zero-equity | debt | comparison: debt to equity with zero equity | **none at first**; now 1: `test_equity_of_zero_makes_debt_to_equity_not_meaningful` |
| CH-debt-ratio | debt | inputs swapped: equity / debt | 3: `test_every_area_has_its_charts_and_each_chart_says_what_it_shows`, `test_debt_equity_and_cash_over_five_years` and 1 more |
| CH-debt-first-year | debt | wrong year: compared with FY-3 | 2: `test_debt_equity_and_cash_over_five_years`, `test_coca_cola_debt_to_equity_in_words` |
| CH-debt-then-guard | debt | guard removed: earlier ratio with equity at or below zero | **none at first**; now 1: `test_an_earlier_year_with_negative_equity_gives_no_earlier_ratio` |
| CH-debt-equity-series | debt | wrong line item: total equity drawn as shareholder equity | **none at first**; now 1: `test_the_equity_line_is_the_shareholders_equity_without_minority_interests` |
| CH-lines-gap-zero | debt | missing is never zero: a gap drawn as zero | 1: `test_ac18_missing_operating_cash_flow_leaves_free_cash_flow_and_coverage_open` |
| CH-div-all-known | dividends | missing is never zero: no dividend said with a year missing | **none at first**; now 1: `test_no_dividend_in_four_years_and_one_year_missing_is_not_no_dividend` |
| CH-div-covered-equal | dividends | comparison: free cash flow equal to dividends not covering | **none at first**; now 1: `test_free_cash_flow_equal_to_the_dividends_covers_them` |
| CH-payout-negative | payout | guard removed: negative dividends give a payout | **none at first**; now 1: `test_negative_dividends_give_no_payout` |
| CH-payout-zero | payout | zero dividends give a payout of 0% | 3: `test_ac17_amazon_shows_no_dividend_paid`, `test_amazon_shows_no_payout_ring_and_says_why` and 1 more |
| CH-payout-zero-net | payout | comparison: payout with net income of zero | **none at first**; now 1: `test_net_income_of_zero_gives_no_payout` |
| CH-payout-ratio | payout | inputs swapped: net income / dividends | 4: `test_every_area_has_its_charts_and_each_chart_says_what_it_shows`, `test_dividends_against_free_cash_flow_over_five_years` and 2 more |
| CH-payout-cap | payout | ring not limited to a full circle | 1: `test_a_payout_above_net_income_fills_the_ring_and_says_so` |
| CH-payout-more-equal | payout | comparison: exactly 100% called more than the profit | **none at first**; now 1: `test_a_payout_of_exactly_100_percent_is_not_more_than_the_profit` |
| CH-price-zero-estimate | price | comparison: an estimate of zero drawn | **none at first**; now 1: `test_an_estimate_of_zero_gives_no_price_chart` |
| CH-price-gap | price | inputs swapped: estimate ÷ price | 3: `test_the_valuation_comes_first_with_the_price_against_the_estimate`, `test_the_share_price_against_the_estimate_with_its_zones` and 1 more |
| CH-price-axis | price | axis ends at the largest value (no room above) | 1: `test_the_share_price_against_the_estimate_with_its_zones` |
| CH-assessed | price, ratios | an insufficient-data check with a value drawn | **none**; not observable, see the dismissals below |
| CH-against-value | ratios | benchmark bar from the company's value | 1: `test_price_ratios_against_the_industry_and_the_market` |
| CH-yield-percent | yield | units: yield not multiplied by 100 | 1: `test_dividend_yield_against_the_market_in_percent` |
| CH-years | charts | wrong years: the oldest five | **none at first**; now 1: `test_with_six_fiscal_years_the_charts_use_the_latest_five` |
| CH-fy0 | charts | wrong year: FY-1 as the latest | 19: `test_every_area_has_its_charts_and_each_chart_says_what_it_shows`, `test_amazon_shows_no_payout_ring_and_says_why` and 17 more |

54 breaks, 29 caught by the earlier tests. #70 was merged (`main` 47d9c93) while this round ran, with the same
`overview.py`; the 23 new tests are in `test_overview_charts.py` and were run again against the 25 breaks there.

### Breaks no test can see: dismissed in writing

- **RES-fychange-350** (year ends exactly 350 days apart counted as overlapping): a year counts from 350 days,
  measured from its start date to its end date (rule 1), so two year ends 350 days apart occur only when the newer
  year starts on or before the older year's end date, that is, when the two periods overlap. Whether a one-day
  overlap is a change of fiscal year end (FY_CHANGE) is written nowhere, so no expected result can come from a rule;
  years that follow each other never reach this boundary.
- **SEC-utf16** (the explicit UTF-16 check removed): a UTF-16 file starts with the bytes FF FE or FE FF, which are
  never valid UTF-8, so reading it as UTF-8 fails with the same message
  (`test_an_env_file_saved_as_utf16_by_windows_gives_a_clear_message` passes either way). The check stays: it says why.
- **FRED-bom, SEC-bom** (a byte-order mark kept): python-dotenv 1.2.4, pinned in `requirements.txt`, removes a
  leading byte-order mark itself, so reading the file as `utf-8` instead of `utf-8-sig` changes nothing. The two
  tests written for these breaks (a `.env` saved by Notepad as "UTF-8 with BOM" still works) are kept as the Windows
  requirement; they do not catch the breaks.
- **CH-assessed** (an insufficient-data check with a value drawn): `CheckResult` (`src/contracts.py`) refuses a value
  on a check that was not assessed, so the status test in `_assessed` changes nothing.

### What the round found

- **A real bug, fixed in its own pull request (#77)** (the round itself changed no app code): rule 1 measured a year from its start
  date to its end date, SPEC §5.3.9 measured a gap from year end to year end. A last fiscal year of exactly 380 days by
  rule 1's count (16 December 2024 to 31 December 2025) after a year ending on 15 December 2024 puts the two year
  ends 381 days apart: the resolver flags FY_GAP and keeps only the latest year, although no year is missing. Rare (a
  fiscal year extended by about two weeks) and on the cautious side (the checks show "insufficient data"), but wrong.
  #77 counts a gap as rule 1 counts a year and clarifies SPEC §5.3.9; no company in the saved SEC cache had the case.
- **Two weak tests, now backed by new ones:** `test_current_debt_larger_than_total_debt_is_flagged` passed on another
  DEBT_CHECK (the one for a total the principal cannot settle), so dropping the check went unnoticed; and
  `test_after_a_failed_download_fred_is_asked_again_only_after_ten_minutes` counts from `fred.FAILURE_PAUSE_SECONDS`
  itself, so a one-minute pause passed. The new tests name the warning's words and use 600 seconds.
- **Two of Igor's decisions (27 November) made rules testable:** "more than 1%" (SPEC §5.3.4, §5.3.7) is 1% of the
  larger of the two values (`docs/architecture.md`); a change that rounds to 0.0% or 0.0 pp is shown without an arrow
  (`docs/acceptance.md`, S10c).
- **Untested before:** the tag order of SPEC §6 for revenue, capital expenditure, cash and non-current debt (the five
  demo companies give the same values either way), the exact boundaries of the 1%, 50%, 200-day and 100,000-share
  limits, and the FRED and SEC settings files saved with quotes or a byte-order mark.

**Summary:** 309 deliberate breaks in A's area. On `main`, 255: 204 caught by the earlier tests, 47 by the 48 test
cases added in A's test files (`test_resolver.py`, `test_company.py`, `test_fred.py`, `test_sec_client.py`,
`test_overview.py`), each seen failing with its break, and 4 not observable, dismissed above. In the chart code of
PR #70, 54: 29 caught, 24 by 23 new tests in `test_overview_charts.py`, each seen failing with its break, 1
dismissed; the tests were added only after #70 was merged (Igor's decision of 27 November: never pushed to #70,
where a push would dismiss its approval). No app code changed. Expected results are the rules cited in each test (SPEC §5.3, §6, §8.3,
`tag_map.yaml`, `settings.yaml`, `docs/acceptance.md`), with the arithmetic in a comment, never the code's output.

The independent read-only review of A's code by a member of another area (SPEC §15): Simon (D) reviewed and approved
#75 on 27 November.
