# Acceptance criteria

Each criterion is checkable: a starting state, an action, an expected result. Status: `open`, `passing
(test: <test name>)`, `checked by hand on <date>`, or `failing`. Section numbers (§) point to `SPEC.md`.

## Main user journey

| Id | Feature | Given | When | Then | Status |
|---|---|---|---|---|---|
| AC1 | F1 | Demo mode on | The user types `KO` | The header shows The Coca-Cola Company, its industry and how the industry was found, fiscal year end, latest 10-K date, retrieval date, and any warnings | open |
| AC2 | F1 | Any mode | The user types `JPM` | "Not supported" with the reason (bank, SEC industry code in 6000–6799); no scores shown | open |
| AC3 | F2 | Tier 1 build, synthetic company, no share price | The scorecard opens | Past performance 4 passed of 4 assessed (P4, P5 "not assessed": status `insufficient_data`, no benchmark yet); financial health 4 of 6; dividend 5 passed of 5 assessed (D2 "not assessed") | partly passing (dividend 5 of 5 assessed, D2 not assessed; test: test_ac3_tier_1_dividend_score_of_the_synthetic_company); past performance and financial health: S5, S6 |
| AC4 | F2 | Any loaded company | The user opens a check | It shows the result, the rule in plain words, the formula, the input figures with units and fiscal years, and a link to the filing | open |
| AC5 | F3 | Any loaded company | The user opens the sources page | One row per figure with metric, value, unit, period, kind, tag, form, accession, filing date, retrieval time and note; each missing figure shows its reason and the checks it blocks | open |
| AC6 | F4 | Synthetic company loaded | The user overrides FY2025 cash from 120 to 140 (USD m) | H3 becomes pass ((450 − 140) ÷ 820 = 310 ÷ 820 = 37.80% < 40%); financial health 5 of 6; the figure shows as `assumption` on the sources page | open |
| AC7 | F5 | Network switched off, demo mode on | The user opens each of the five demo companies | Each opens without an error | open |
| AC8 | F6 | Tier 2 build, synthetic company with the synthetic benchmarks | The scorecard opens | P4 pass, P5 fail, D2 pass (share price USD 30.00); each benchmark shows the industry group, the route used, the number of firms and the source file | open |
| AC9 | F7 | Tier 2 build, synthetic company, share price USD 30.00 | The scorecard opens | Fair value USD 21.68 per share; implied growth 14.10% labelled "describes the price, it is not a forecast"; scores 5 of 6, 4 of 6, 6 of 6, 2 of 6 | open |
| AC10 | F7 | Any company, no share price | The scorecard opens | The valuation area shows "insufficient data" and asks for a share price; the other areas still show | open |
| AC11 | F8 | Synthetic company loaded | The user downloads the Excel file | A test reopens it: three sheets (report, figures, sources); every figure equals the screen | open |
| AC12 | F9 | Tier 3 build, any company | The user overrides a force's rating and writes a note, then changes an input | The override and note survive the recalculation and appear in the export | open |

## Screens (how each was checked)

| Id | Screen / state | Expected | Test | Browser check | Looked at by |
|---|---|---|---|---|---|
| V1 | Scorecard, laptop width | Header and score chart visible without scrolling; a unit on every input and figure | AppTest (S17) | not installed | pending |
| V2 | Each error state (unknown ticker, unsupported, source unreachable, no price) | The message says how to fix the problem | AppTest (S11) | not installed | pending |
| V3 | Synthetic company anywhere in the app | "SYNTHETIC DATA" mark visible | AppTest (S10) | not installed | pending |
| V4 | A missing figure in a check or table | Shown as "n/a" with the reason, never as 0 | unit test on the display layer (S10) | not installed | pending |

## Calculations (known answers)

Source: SPEC Appendix A (synthetic company, USD millions; shares 100 million; price USD 30.00; risk-free 4.0%,
premium 5.0%, tax 21%, terminal growth 2.5%; benchmarks: unlevered beta 0.90, ROE 15%, operating margin 18%,
P/E 20.0, EV/EBITDA 13.0, P/B 4.0, market dividend yield 1.5%).

**Rule 14.5:** these values may be used in tests only after the owner named in each row has recalculated them by
hand or in Excel and signed off in slice S0c. In code: `tests.fixtures.synthetic.expected_check("P3")` refuses to
return a value until A has recorded its owner's sign-off (a review comment on the S0c pull request) under
`sign_off` in `app/tests/fixtures/synthetic_co.yaml`. Owners: B for P and H rows and the strengths and
points to watch, C for D, V, W and F rows, D for AC3, E for CALC-S. If a recalculation disagrees, the recalculation wins and SPEC
Appendix A is corrected by pull request. Tolerance: half a unit of the last digit shown.

Independent cross-check (not a sign-off): on 2026-11-18 Claude recomputed every row below in a separate script
that shares no code with the app. All agree within the rounding shown (discounted terminal value 1,842.19 against
1,842.20, a rounding difference).

| Id | Number | Hand working (SPEC Appendix A) | Expected | Owner | Status |
|---|---|---|---|---|---|
| CALC-P1 | Years profitable | Net income 100, 115, 105, 128, 140: all > 0 | 5 of 5 → pass | B | open, sign-off pending |
| CALC-P2 | Earnings grew | 140 > 100 and 140 > 0 | pass | B | open, sign-off pending |
| CALC-P3 | Growth accelerating | 140 ÷ 128 − 1 = 9.375%; (140 ÷ 100)^(1/4) − 1 = 8.776% | 9.375% > 8.776% → pass | B | open, sign-off pending |
| CALC-P4 | ROE vs industry | 140 ÷ ((750 + 820) ÷ 2) = 140 ÷ 785 | 17.83% > 15% → pass | B | open, sign-off pending |
| CALC-P5 | Margin vs industry | 208 ÷ 1,300 | 16.00% < 18% → fail | B | open, sign-off pending |
| CALC-P6 | Return on capital improved | 208 ÷ (1,750 − 360) = 208 ÷ 1,390; FY-3: 170 ÷ (1,480 − 310) = 170 ÷ 1,170 | 14.96% > 14.53% → pass | B | open, sign-off pending |
| CALC-H1 | Short-term cover | 540 > 360 | pass | B | open, sign-off pending |
| CALC-H2 | Long-term cover | 540 against 930 − 360 = 570 | fail | B | open, sign-off pending |
| CALC-H3 | Moderate debt | (450 − 120) ÷ 820 = 330 ÷ 820 | 40.24% ≥ 40% → fail | B | open, sign-off pending |
| CALC-H4 | Debt falling | 450 ÷ 820 = 54.88% against 400 ÷ 600 = 66.67% | pass | B | open, sign-off pending |
| CALC-H5 | Debt covered by cash flow | 215 ÷ 450 | 47.78% ≥ 20% → pass | B | open, sign-off pending |
| CALC-H6 | Interest covered | 208 ÷ 26 | 8.0 ≥ 5 → pass | B | open, sign-off pending |
| CALC-D1 | Pays a dividend | 56 > 0 | pass | C | passing (test: test_appendix_a_synthetic_company[D1]); signed off by C on PR #5 |
| CALC-D2 | Yield above market | 56 ÷ (30.00 × 100) = 56 ÷ 3,000 | 1.867% > 1.5% → pass | C | signed off by C on PR #5; open: D2 is "not assessed" until S9 adds the share price and the market yield (test: test_appendix_a_d2_is_not_assessed_without_share_price_and_benchmark) |
| CALC-D3 | No large cut | Changes: +10%, +9.09%, −6.25% (48 to 45), +24.44% | largest fall −6.25% → pass | C | passing (test: test_appendix_a_synthetic_company[D3]); signed off by C on PR #5 |
| CALC-D4 | Dividend grew | 56 > 40 | pass | C | passing (test: test_appendix_a_synthetic_company[D4]); signed off by C on PR #5 |
| CALC-D5 | Covered by earnings | 56 ÷ 140 | 40% < 90% → pass | C | passing (test: test_appendix_a_synthetic_company[D5]); signed off by C on PR #5 |
| CALC-D6 | Covered by cash | 56 ≤ 215 − 85 = 130 | pass | C | passing (test: test_appendix_a_synthetic_company[D6]); signed off by C on PR #5 |
| CALC-V1 | Below fair value | 30.00 against 21.68 | fail | C | open, sign-off pending |
| CALC-V2 | Well below fair value | 30.00 against 0.80 × 21.68 = 17.34 | fail | C | open, sign-off pending |
| CALC-V3 | P/E vs industry | 3,000 ÷ 140 | 21.43 > 20.0 → fail | C | open, sign-off pending |
| CALC-V4 | EV/EBITDA vs industry | (3,000 + 450 − 120) ÷ (208 + 65) = 3,330 ÷ 273 | 12.20 < 13.0 → pass | C | open, sign-off pending |
| CALC-V5 | P/B vs industry | 3,000 ÷ 820 | 3.66 < 4.0 → pass | C | open, sign-off pending |
| CALC-V6 | Implied vs actual growth | Implied 14.10% (§8.4); actual (1,300 ÷ 1,000)^(1/4) − 1 = 6.78% | fail | C | open, sign-off pending |
| CALC-W1 | Levered beta | 0.90 × (1 + 0.79 × 450 ÷ 3,000) = 0.90 × 1.1185 | 1.00665 | C | open, sign-off pending |
| CALC-W2 | Cost of equity | 4.0% + 1.00665 × 5.0% | 9.0333% | C | open, sign-off pending |
| CALC-W3 | Cost of debt | 26 ÷ ((440 + 450) ÷ 2) = 26 ÷ 445; after tax × 0.79 | 5.8427%; 4.6157% | C | open, sign-off pending |
| CALC-W4 | Cost of capital | Weights 3,000 ÷ 3,450 = 86.9565%, 13.0435%; 0.869565 × 9.0333% + 0.130435 × 4.6157% | 8.4571% | C | open, sign-off pending |
| CALC-F1 | Forecast inputs | g = 6.7790%; margin 16.0%; D&A 5.0%; capex 85 ÷ 1,300 = 6.5385%; NWC (540 − 120) − (360 − 50) = 110 → 8.4615% | as listed | C | open, sign-off pending |
| CALC-F2 | Free cash flows, years 1–5 | SPEC Appendix A table | 146.65, 156.59, 167.20, 178.54, 190.64 | C | open, sign-off pending |
| CALC-F3 | Terminal value | 228.10 × 1.025 ÷ 0.084571; both §8.3 forms agree | 2,764.55; discounted 1,842.20 (73.8% of EV) | C | open, sign-off pending |
| CALC-F4 | Fair value per share | EV 655.46 + 1,842.20 = 2,497.65; equity 2,497.65 − 450 + 120 = 2,167.65; ÷ 100 | USD 21.68 | C | open, sign-off pending |
| CALC-F5 | Implied growth at USD 30.00 | Bisection on g in −20% to +50% | 14.10% | C | open, sign-off pending |
| CALC-S | Area scores (tier 2) | Passes per area from the rows above | 5 of 6, 4 of 6, 6 of 6, 2 of 6 | B and C | open, sign-off pending |

### S7 edge cases (test companies)

Hand working by Flo (C), 22 November 2026, given in his S7 session; written down here by Claude Code, **to be checked by Flo before the pull request**. Test companies in `app/tests/unit/test_dividend_checks.py`: dividends paid in USD millions, FY-4 → FY0; every figure not listed is net income 500, operating cash flow 600 and capital expenditure 100 in every year. Rules and decisions: `app/src/checks/dividend.py`.

| Id | Test company | Hand working | Expected | Test |
|---|---|---|---|---|
| S7-1 | Nil in all five years, labelled (Amazon's shape, PR #21) | 0 > 0 is false: D1 fails, so D2–D6 are not applicable | D1 fail; D2–D6 not applicable | `test_1_a_labelled_nil_means_no_dividend_paid` |
| S7-2 | 30, 32, 34, 36, 0 (reported zero) | 0 > 0 is false | D1 fail; D2–D6 not applicable | `test_2_a_reported_zero_in_fy0_means_no_dividend_paid` |
| S7-3 | 30, 32, 34, 36, missing | FY0 missing: D1 insufficient; D2 not assessed; D3–D6 each use FY0 | all six insufficient data | `test_3_missing_fy0_dividends_are_insufficient_data_never_no_dividend` |
| S7-4a | 50, 50, 50, 50, 45 | 45 < 0.9 × 50 = 45 is false: no cut; 45 ÷ 50 − 1 = −10.00% | D3 pass, −10.00% | `test_4_d3_a_fall_of_exactly_10_percent_is_not_a_cut` |
| S7-4b | 50, 50, 50, 50, 44.9 | 44.9 < 45: a cut; 44.9 ÷ 50 − 1 = −10.20% | D3 fail, −10.20% | `test_4_d3_a_fall_of_exactly_10_percent_is_not_a_cut` |
| S7-5 | 30, 32, missing, 36, 38 | FY-2 missing; D3 uses all five years | D3 insufficient data | `test_5_d3_with_a_year_missing_is_insufficient_data` |
| S7-6 | 0, 30, 35, 38, 40 | 0 → 30 not counted; 35 ÷ 30 − 1 = 16.67%, 38 ÷ 35 − 1 = 8.57%, 40 ÷ 38 − 1 = 5.26%; no cut | D3 pass, +5.26% | `test_6_d3_a_rise_from_a_year_of_zero_is_never_a_cut` |
| S7-7 | Only four years: 32, 34, 36, 38 (FY-3 to FY0) | FY-4 not in the data, so missing | D3, D4 insufficient data | `test_7_with_only_four_fiscal_years_d3_and_d4_are_insufficient_data` |
| S7-8 | 40, 42, 41, 40, 40 | 40 > 40 is false | D4 fail, 40 against 40 | `test_8_d4_a_dividend_equal_to_four_years_earlier_did_not_grow` |
| S7-9 | 80, 82, 84, 86, 90; net income FY0 100, then 0, then −50 | 90 ÷ 100 = 90.00%, not < 90%; net income ≤ 0: fail, no ratio | D5 fail (90.00%); fail; fail | `test_9_d5_fails_at_exactly_90_percent_and_when_net_income_is_zero_or_negative` |
| S7-10 | 120, 122, 124, 126, 130; FY0 (a) cash flow 215, capex 85; (b) capex missing; (c) 100, 150 | (a) 130 ≤ 215 − 85 = 130; (b) capex missing; (c) 130 ≤ 100 − 150 = −50 is false | D6 (a) pass, 130 against 130; (b) insufficient data; (c) fail, 130 against −50 | `test_10_d6_dividends_against_operating_cash_flow_minus_capex` |
| S7-11 | 30, 32, 34, 36, 40; net income FY0 100; payout limit 30% | 40 ÷ 100 = 40% < 30% is false | D5 fail, 40% against 30% | `test_11_a_changed_payout_limit_changes_d5` |
| S7-A | 30, 32, 34, 36, −10 | Negative FY0 payment: sign error; every check uses FY0 | all six insufficient data | `test_a_negative_fy0_dividend_is_insufficient_data_everywhere` |
| S7-B | 30, 32, −34, 36, 38 | Only D3 uses FY-2; 38 > 0; 38 > 30; 38 ÷ 500 = 7.60%; 38 ≤ 500 | D1 pass; D2, D3 insufficient data; D4, D5, D6 pass | `test_b_a_negative_dividend_in_fy_minus_2_blocks_only_d3` |
| S7-C | 0, 0, 0, 0, 5 | Every step starts at 0, so none is counted; no cut | D3 pass, no value | `test_c_d3_passes_with_no_value_when_every_step_starts_from_zero` |
| S7-T1 | 120, 122, 124, 126, 130; FY0 cash flow 100, capex −50 | Negative capex: sign error, used by D6 only; 130 > 0; four rises; 130 > 120; 130 ÷ 500 = 26% | D1, D3, D4, D5 pass; D6 insufficient data | `test_t1_a_negative_capex_is_a_sign_error_and_d6_is_insufficient_data` |
| S7-T2 | 50, 40, 45, 50, 55 | 40 < 45: a cut; 40 ÷ 50 − 1 = −20.00% | D3 fail, −20.00% | `test_t2_to_t4_d3_looks_at_every_step_year_on_year` |
| S7-T3 | 30, 0, 30, 32, 34 | 0 < 27: a cut; 0 ÷ 30 − 1 = −100.00%; 0 → 30 not counted | D3 fail, −100.00% | `test_t2_to_t4_d3_looks_at_every_step_year_on_year` |
| S7-T4 | 100, 92, 84.64, 90, 95 | 92 < 90 and 84.64 < 82.8 are false; each fall −8.00% year on year (from the peak it would be −15.36%) | D3 pass, −8.00% | `test_t2_to_t4_d3_looks_at_every_step_year_on_year` |
| S7-T5 | −30, 32, 34, 36, 38 | Negative FY-4 blocks D3 and D4 only; 38 ÷ 500 = 7.60%; 38 ≤ 500 | D1, D5, D6 pass; D3, D4 insufficient data | `test_t5_a_negative_fy_minus_4_dividend_blocks_only_d3_and_d4` |
| S7-T6 | missing, 32, 34, 36, 38 | FY-4 missing | D3, D4 insufficient data | `test_t6_a_missing_fy_minus_4_dividend_blocks_d3_and_d4` |
| S7-T7 | 30, 32, 34, 36, 38; net income FY0 missing | D5 uses net income FY0; 38 ≤ 600 − 100 | D5 insufficient data; D6 pass | `test_t7_missing_net_income_blocks_d5_only` |
| S7-T8 | 50, 50, 50, 50, 40; cut limit 25% | 40 < 0.75 × 50 = 37.5 is false; 40 ÷ 50 − 1 = −20.00% | D3 pass, −20.00% against −25% | `test_t8_a_changed_cut_limit_changes_d3` |
| S7-T9 | 30, 32, 34, 36, 36, with FY0 replaced by 40 of kind `assumption` (no manual overrides in tier 1; this tests the kind, not a feature) | 40 > 0; the 40 is the figure used | D1 pass, value 40 | `test_t9_a_positive_dividend_typed_in_by_a_user_passes_d1` |
| S7-T10 | 30, 32, missing, 36, 38 | 38 > 0; 38 > 30; 7.60%; 38 ≤ 500 | D1, D4, D5, D6 pass | `test_t10_a_missing_middle_year_leaves_d1_d4_d5_d6_assessed` |
| S7-T11 | Only four years: 32, 34, 36, 38 | 38 > 0; 7.60%; 38 ≤ 500 | D1, D5, D6 pass | `test_t11_with_four_fiscal_years_d1_d5_d6_are_still_assessed` |
| S7-T12 | Coca-Cola FY2025, Igor's hand reading (`KO.yaml`): dividends 8,779, net income 13,107 | 8,779 ÷ 13,107 = 66.98% < 90% | D5 pass, 66.98% | `test_coca_cola_dividend_covered_by_earnings_in_fiscal_year_2025` |
| S7-R1 | 30, 32, 34, 36, 36, with FY0 replaced by 0 of kind `assumption` that is not the plan Q1 nil | 0 > 0 is false; only the data layer's nil gets the "treated as nil" sentence | D1 fail, shown as "USD 0"; D2–D6 not applicable | `test_a_zero_assumption_that_is_not_the_nil_is_shown_as_a_plain_zero` |
| S7-R2 | 120, 122, 124, 126, 130, with FY0 capex replaced by −50 of kind `assumption` | Negative payment, but not read from a filing, so no SIGN warning to point to | D6 insufficient data, "a payment is a positive amount" | `test_the_sign_warning_is_named_only_for_a_figure_read_from_a_filing` |

## Edge cases and errors

| Id | Situation | Expected behaviour | Status |
|---|---|---|---|
| E1 | Unknown ticker | Message: ticker not found, check the spelling; no crash | open |
| E2 | Bank, insurer or REIT (SEC code 6000–6799), e.g. JPM | Stop: "not supported" and why (§10) | open |
| E3 | Not in US dollars, no 10-K data, or fewer than three fiscal years | Stop with the reason (§10) | open |
| E4 | SEC unreachable | Three retries with a growing pause, then the input is `missing`; message suggests demo mode | partly passing (test: test_after_three_retries_the_source_is_unreachable_and_the_message_says_what_to_do); `load_company` passes the error on, the interface shows its message and offers demo mode: slice S11 |
| E5 | A required figure is missing | `missing` with reason; checks that need it show "insufficient data"; never 0, never guessed (§5.2) | passing (tests: test_a_line_item_without_a_company_wide_figure_is_missing_with_a_reason, test_a_derived_figure_with_a_missing_input_stays_missing_and_says_why); the check side: S5–S9 |
| E6 | Two fallback tags give different values for the same period | Figure flagged on the sources page, not chosen silently (§5.3.7) | passing (test: test_two_tags_with_different_values_are_flagged_and_the_first_in_the_list_is_used) |
| E7 | Restated figure differs from the original by more than 1% | Latest filed value used; both shown with a warning (§5.3.4) | passing (test: test_planted_a_restated_figure_uses_the_latest_filing_and_keeps_the_original; KO 2018: test_coca_cola_2018_revenue_restatement_as_shown_in_session_5) |
| E8 | 53-week fiscal year | Kept: flow periods of 350 to 380 days are accepted (§5.3.1) | passing (test: test_a_flow_must_cover_350_to_380_days; Apple: test_apple_has_a_53_week_fiscal_year) |
| E9 | Negative equity | H3, P4, V5 fail with the note "negative equity"; warning in the header (§7, §10). H4: see open question in `docs/plan.md` | open |
| E10 | Net income zero or below | V3 and D5 fail; P2 fails | partly passing (D5, test: test_9_d5_fails_at_exactly_90_percent_and_when_net_income_is_zero_or_negative); V3: S9; P2: S5 |
| E11 | No dividend | D1 fails; D2 to D6 `not applicable`; area shows "no dividend paid", score 0 | partly passing (tests: test_1_a_labelled_nil_means_no_dividend_paid, test_2_a_reported_zero_in_fy0_means_no_dividend_paid); Amazon on real data after PR #21; the area display: S10 |
| E12 | Zero debt | H4 (no debt in both years), H5, H6 (no debt and no interest) pass; the cost of capital equals the cost of equity | open |
| E13 | Cost of debt outside risk-free to risk-free + 8 points | Risk-free + 1.5 points used, labelled `assumption`, warning (§8.1) | open |
| E14 | No growth in −20% to +50% matches the price | "No solution in the range"; no number reported (§8.4) | open |
| E15 | Terminal value above 75% of enterprise value | Warning in the header (§10) | open |
| E16 | Ticker outside the verified universe | Report shown, marked "not verified" (§2, §10) | open |
| E17 | Industry not found in the lookup or the fallback table | Benchmarks `missing`; dependent checks "insufficient data"; user can choose the group (§9.1) | open |

## Planted errors (each one a test that must catch it, §5.4)

| Id | Planted error | Expected | Status |
|---|---|---|---|
| PE1 | A nine-month figure read as a year | Rejected: period outside 350–380 days | passing (test: test_planted_a_nine_month_figure_is_never_read_as_a_year) |
| PE2 | Thousands read as millions (or dollars as millions) | Caught by the unit rule and a reconciliation figure | passing (tests: test_planted_amounts_are_kept_in_dollars_exactly_as_filed, test_only_units_as_filed_are_accepted); reconciliation: S15, Coca-Cola 6 of 6 match (`app/tests/reconciliation/KO.yaml`), 4 companies to do |
| PE3 | Wrong fiscal-year label (prior-year comparative carrying the filing's `fy`) | Fiscal year taken from the period end date (§5.3.2) | passing (tests: test_planted_a_wrong_fiscal_year_label_is_ignored, test_a_comparative_labelled_with_a_later_fiscal_year_lands_in_its_own_year) |
| PE4 | Restated figure | Latest filed value, original kept (§5.3.4) | passing (test: test_planted_a_restated_figure_uses_the_latest_filing_and_keeps_the_original) |
| PE5 | Sign flipped (e.g. capital expenditure positive vs negative) | Caught by a test on the sign convention | passing (tests: test_planted_a_negative_capital_expenditure_is_kept_as_filed_and_flagged, test_a_positive_payment_raises_no_sign_warning) |
| PE6 | Percent against decimal | Ratios stored as decimals; a test fails on 40 instead of 0.40 | passing for settings (test: test_rates_are_decimals_not_percentages); the checks: S5–S9 |
