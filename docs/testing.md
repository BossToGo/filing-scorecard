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
