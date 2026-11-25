# Acceptance criteria

Each criterion is checkable: a starting state, an action, an expected result. Status: `open`, `passing
(test: <test name>)`, `checked by hand on <date>`, or `failing`. Section numbers (§) point to `SPEC.md`.

## Main user journey

| Id | Feature | Given | When | Then | Status |
|---|---|---|---|---|---|
| AC1 | F1 | Demo mode on | The user picks Coca-Cola from the five demo companies (or types `KO`) | The header shows the company's name as the SEC lists it (COCA COLA CO), its industry and how the industry was found, fiscal year end, latest 10-K date, retrieval date, and any warnings | partly passing on `main`: name as the SEC lists it, SEC industry, latest fiscal year end, latest 10-K date, retrieval date (`test_coca_cola_header_shows_the_sec_name_ac1`, `test_header_shows_the_latest_fiscal_year_end_from_the_data`) and the two warnings, built by S11 (`tests/unit/test_gates.py`, `test_a_company_outside_the_five_shows_not_fully_checked_in_the_header_e16`); how the industry was found waits for #27 |
| AC2 | F1 | Any mode | The user types `JPM` | "Not supported" with the reason (bank, SEC industry code in 6000–6799); no scores shown | passes on branch `d/S11-gates` (`test_jpmorgan_is_stopped_by_its_industry_code`, `test_jpmorgan_is_not_supported_and_shows_no_score_ac2`) |
| AC3 | F2 | Tier 1 build, synthetic company, no share price | The scorecard opens | Past performance 4 passed of 4 assessed (P4, P5 "not assessed": status `insufficient_data`, no benchmark yet); financial health 4 of 6; dividend 5 passed of 5 assessed (D2 "not assessed") | passing: the three scores from the check modules (`tests/unit/test_b_appendix_a.py` `test_ac3_tier_1_past_performance_score_of_the_synthetic_company` and `test_ac3_tier_1_financial_health_score_of_the_synthetic_company`, B's #28 and #29; `tests/unit/test_dividend_checks.py` `test_ac3_tier_1_dividend_score_of_the_synthetic_company`, C's #23); on screen on branch `d/S10-design` (PR #54): `tests/app/test_scorecard.py` `test_ac3_scores_on_screen` and `test_ac3_rows_name_what_is_not_assessed_and_the_failed_checks`, still with hand-built check results (switch to the modules in S17) |
| AC4 | F2 | Any loaded company | The user opens a check | It shows the result, the rule in plain words, the formula, the input figures with units and fiscal years, and a link to the filing | passes on branch `d/S10-interface` (`test_a_closed_check_row_shows_mark_result_and_check_ac4`, `test_an_open_check_shows_its_figures_with_units_and_fiscal_year_ac4`); plain-language rule once E's `texts.yaml` (#17) is merged |
| AC5 | F3 | Any loaded company | The user opens the sources page | One row per figure with metric, value, unit, period, kind, tag, form, accession, filing date, retrieval time and note; each missing figure shows its reason and the checks it blocks | passes on branch `d/S10-interface` (`test_sources_page_one_row_per_figure_ac5`) |
| AC6 | F4 | Any loaded company | The user looks for an input other than the ticker, the share price and the demo switch | There is none: no way to change a figure, the industry, an assumption or a check result; the scorecard is the same for every user (§1, §3, §8.7) | open |
| AC7 | F5 | Network switched off, demo mode on | The user opens each of the five demo companies | Each opens without an error | passes on branch `a/S14-demo-mode` (`tests/integration/test_demo_mode_ac7.py`): each of the five opens through `main.py` with the network blocked, with no crash, no error, no network attempt, its SEC name shown, no "not fully checked" and its checks listed |
| AC8 | F6 | Tier 2 build, synthetic company with the synthetic benchmarks | The scorecard opens | P4 pass, P5 fail, D2 pass (share price USD 30.00); each benchmark shows the industry group, the route used, the number of firms and the source file | open |
| AC9 | F7 | Tier 2 build, synthetic company, share price USD 30.00 | The scorecard opens | Fair value USD 20.13 per share (equity method); scores 5 of 6, 4 of 6, 6 of 6, 3 of 6 (SPEC v2.3 Appendix A; fair value signed off by C, scores by E, 21 November) | open |
| AC10 | F7 | Any company, no share price | The scorecard opens | The valuation area shows "insufficient data" and asks for a share price; the other areas still show | open |
| AC11 | F8 | Synthetic company loaded | The user downloads the Excel file | A test reopens it: two sheets (the scorecard; the figures with their sources, §3 item 8); every figure equals the screen | open |
| AC12 | F2 | Demo mode, Coca-Cola (KO) | The scorecard opens | The overview above the tabs shows revenue USD 47.94 bn (+1.9% vs FY2024), operating margin 28.7% (+7.5 pp), net income USD 13.11 bn (+23.3%), free cash flow USD 5.30 bn (+11.7%), each marked reported or derived; dividend coverage 60.3%, dividends USD 3.48 bn above free cash flow; current ratio 1.46× (hand working below, "Overview (S10c)") | passing on branch `a/S10c-overview` (`tests/unit/test_overview.py`, `tests/app/test_overview_screen.py`); hand working checked by Igor, 25 November |
| AC13 | F2 | Demo mode, Amazon (AMZN) | The scorecard opens | Dividend coverage reads "No dividend paid", never 0% | passing on branch `a/S10c-overview` (`tests/unit/test_overview.py`, `tests/app/test_overview_screen.py`); hand working checked by Igor, 25 November |
| AC14 | F2 | Any company with a figure missing | The scorecard opens | Each overview figure that needs it shows "n/a" with the reason, never 0; the five-year chart leaves a gap and its table shows "n/a" | passing on branch `a/S10c-overview` (`tests/unit/test_overview.py`, `tests/app/test_overview_screen.py`); hand working checked by Igor, 25 November |
| AC12 | F9 | Tier 3 build, synthetic company, share price USD 30.00 | The scorecard opens | Strengths G1, G2, G3, G5, G6; points to watch W3, W4, W8, all minor; each opens its check (SPEC v2.3 §9 and Appendix A; B's recalculation pending) | open |

## Screens (how each was checked)

| Id | Screen / state | Expected | Test | Browser check | Looked at by |
|---|---|---|---|---|---|
| V1 | Scorecard, laptop width | Header and score chart visible without scrolling; a unit on every input and figure | AppTest (S17) | not installed | pending |
| V2 | Each error state (unknown ticker, unsupported, source unreachable, no price) | The message says how to fix the problem | AppTest (S11): `tests/app/test_gates_screen.py` passes for unknown ticker, unsupported, source unreachable, any other reading error, an empty ticker and an invalid price; "needs a share price" comes with S10b | not installed | pending |
| V3 | Synthetic company anywhere in the app | "SYNTHETIC DATA" mark visible | AppTest (S10): `test_synthetic_data_mark_v3` passes | not installed | pending |
| V4 | A missing figure in a check or table | Shown as "n/a" with the reason, never as 0 | unit test on the display layer (S10): `test_missing_figure_shows_n_a_with_its_reason_never_zero` and the AppTest `test_apple_missing_interest_expense_is_n_a_with_its_reason_never_zero_v4` pass | not installed | pending |

## Calculations (known answers)

Source: SPEC Appendix A (synthetic company, USD millions; shares 100 million; price USD 30.00; risk-free 4.0%,
premium 5.0%, tax 21% (beta only), terminal growth 2.5%, free cash flow margin over three years, starting growth limited to −10%..+30% and halving its gap to 2.5% every 2 years over 10 years, beta limited to 0.8..2.0; benchmarks: unlevered beta 0.90, ROE 15%, operating margin 18%,
P/E 20.0 (industry) and 24.0 (whole US market), P/B 4.0, market dividend yield 1.5%).

**Rule 14.5:** these values may be used in tests only after the owner named in each row has recalculated them by
hand or in Excel and signed off in slice S0c. In code: `tests.fixtures.synthetic.expected_check("P3")` refuses to
return a value until A has recorded its owner's sign-off (a review comment on the S0c pull request) under
`sign_off` in `app/tests/fixtures/synthetic_co.yaml`. Owners: B for P and H rows and, with a separate record
(`B_statements`), the strengths and points to watch, C for D, V, W and F rows, D for AC3, E for CALC-S. If a recalculation disagrees, the recalculation wins and SPEC
Appendix A is corrected by pull request. Tolerance: half a unit of the last digit shown.

Independent cross-checks (not sign-offs): the version 2.3 rows below were recomputed by Claude in a separate script
that shares no code with the app (20 November), and again from the SPEC formulas alone by a reviewer agent in the
audit of 21 November. Both agree with every value and every pass or fail shown. C's own Excel model
(`docs/crosscheck/`, pull request #14) is the human recalculation that rule 14.5 asks for. The unrounded values
behind the rounded working: free cash flow of year 10 166.7541; sum of discounted cash flows 911.2065; discounted
terminal value 1,101.7463.

| Id | Number | Hand working (SPEC Appendix A) | Expected | Owner | Status |
|---|---|---|---|---|---|
| CALC-P1 | Years profitable | Net income 100, 115, 105, 128, 140: all > 0 | 5 of 5 (at least 4) → pass | B | signed off by B (Greg), 24 November 2026: [P4, P5 his own hand working; the other rows Simon's hand working of 19 November, compared by Greg](https://github.com/BossToGo/filing-scorecard/pull/5#pullrequestreview-6039789536) |
| CALC-P2 | Earnings grew | 140 > 100 and 140 > 0 | pass | B | signed off by B (Greg), 24 November 2026: [P4, P5 his own hand working; the other rows Simon's hand working of 19 November, compared by Greg](https://github.com/BossToGo/filing-scorecard/pull/5#pullrequestreview-6039789536) |
| CALC-P3 | Growth accelerating | 140 ÷ 128 − 1 = 9.375%; (140 ÷ 100)^(1/4) − 1 = 8.776% | 9.375% > 8.776% → pass | B | signed off by B (Greg), 24 November 2026: [P4, P5 his own hand working; the other rows Simon's hand working of 19 November, compared by Greg](https://github.com/BossToGo/filing-scorecard/pull/5#pullrequestreview-6039789536) |
| CALC-P4 | ROE vs industry | 140 ÷ ((750 + 820) ÷ 2) = 140 ÷ 785 | 17.83% > 15% → pass | B | signed off by B (Greg), 24 November 2026: [P4, P5 his own hand working; the other rows Simon's hand working of 19 November, compared by Greg](https://github.com/BossToGo/filing-scorecard/pull/5#pullrequestreview-6039789536) |
| CALC-P5 | Margin vs industry | 208 ÷ 1,300 | 16.00% < 18% → fail | B | signed off by B (Greg), 24 November 2026: [P4, P5 his own hand working; the other rows Simon's hand working of 19 November, compared by Greg](https://github.com/BossToGo/filing-scorecard/pull/5#pullrequestreview-6039789536) |
| CALC-P6 | Return on capital improved | 208 ÷ (1,750 − 360) = 208 ÷ 1,390; FY-3: 170 ÷ (1,480 − 310) = 170 ÷ 1,170 | 14.96% > 14.53% → pass | B | signed off by B (Greg), 24 November 2026: [P4, P5 his own hand working; the other rows Simon's hand working of 19 November, compared by Greg](https://github.com/BossToGo/filing-scorecard/pull/5#pullrequestreview-6039789536) |
| CALC-H1 | Short-term cover | 540 > 360 | pass | B | signed off by B (Greg), 24 November 2026: [P4, P5 his own hand working; the other rows Simon's hand working of 19 November, compared by Greg](https://github.com/BossToGo/filing-scorecard/pull/5#pullrequestreview-6039789536) |
| CALC-H2 | Long-term cover | 540 against 930 − 360 = 570 | fail | B | signed off by B (Greg), 24 November 2026: [P4, P5 his own hand working; the other rows Simon's hand working of 19 November, compared by Greg](https://github.com/BossToGo/filing-scorecard/pull/5#pullrequestreview-6039789536) |
| CALC-H3 | Moderate debt | (450 − 120) ÷ 820 = 330 ÷ 820 | 40.24% ≥ 40% → fail | B | signed off by B (Greg), 24 November 2026: [P4, P5 his own hand working; the other rows Simon's hand working of 19 November, compared by Greg](https://github.com/BossToGo/filing-scorecard/pull/5#pullrequestreview-6039789536) |
| CALC-H4 | Debt falling | 450 ÷ 820 = 54.88% against 400 ÷ 600 = 66.67% | pass | B | signed off by B (Greg), 24 November 2026: [P4, P5 his own hand working; the other rows Simon's hand working of 19 November, compared by Greg](https://github.com/BossToGo/filing-scorecard/pull/5#pullrequestreview-6039789536) |
| CALC-H5 | Debt covered by cash flow | 215 ÷ 450 | 47.78% ≥ 20% → pass | B | signed off by B (Greg), 24 November 2026: [P4, P5 his own hand working; the other rows Simon's hand working of 19 November, compared by Greg](https://github.com/BossToGo/filing-scorecard/pull/5#pullrequestreview-6039789536) |
| CALC-H6 | Interest covered | 208 ÷ 26 | 8.0 ≥ 5 → pass | B | signed off by B (Greg), 24 November 2026: [P4, P5 his own hand working; the other rows Simon's hand working of 19 November, compared by Greg](https://github.com/BossToGo/filing-scorecard/pull/5#pullrequestreview-6039789536) |
| CALC-D1 | Pays a dividend | 56 > 0 | pass | C | passing (test: test_appendix_a_synthetic_company[D1]); signed off by C on PR #5 |
| CALC-D2 | Yield above market | 56 ÷ (30.00 × 100) = 56 ÷ 3,000 | 1.867% > 1.5% → pass | C | signed off by C on PR #5; open: D2 is "not assessed" until S9 adds the share price and the market yield (test: test_appendix_a_d2_is_not_assessed_without_share_price_and_benchmark) |
| CALC-D3 | No large cut | Changes: +10%, +9.09%, −6.25% (48 to 45), +24.44% | largest fall −6.25% → pass | C | passing (test: test_appendix_a_synthetic_company[D3]); signed off by C on PR #5 |
| CALC-D4 | Dividend grew | 56 > 40 | pass | C | passing (test: test_appendix_a_synthetic_company[D4]); signed off by C on PR #5 |
| CALC-D5 | Covered by earnings | 56 ÷ 140 | 40% < 90% → pass | C | passing (test: test_appendix_a_synthetic_company[D5]); signed off by C on PR #5 |
| CALC-D6 | Covered by cash | 56 ≤ 215 − 85 = 130 | pass | C | passing (test: test_appendix_a_synthetic_company[D6]); signed off by C on PR #5 |
| CALC-V1 | Below fair value | 30.00 against 20.13 | fail | C | signed off by C (Flo, 21 November 2026, review comment on pull request #5; his Excel model in #14); the tests come with S7 to S9 |
| CALC-V2 | Well below fair value | 30.00 against 0.80 × 20.13 = 16.10 | fail | C | signed off by C (Flo, 21 November 2026, review comment on pull request #5; his Excel model in #14); the tests come with S7 to S9 |
| CALC-V3 | P/E vs industry | 3,000 ÷ 140 | 21.43 > 20.0 → fail | C | signed off by C (Flo, 21 November 2026, review comment on pull request #5; his Excel model in #14); the tests come with S7 to S9 |
| CALC-V4 | P/E vs the whole US market (v2.3) | 3,000 ÷ 140 = 21.43 against the synthetic market P/E 24.0 | 21.43 < 24.0 → pass | C | signed off by C (Flo, 21 November 2026, review comment on pull request #5; his Excel model in #14); the tests come with S7 to S9 |
| CALC-V5 | P/B vs industry | 3,000 ÷ 820 | 3.66 < 4.0 → pass | C | signed off by C (Flo, 21 November 2026, review comment on pull request #5; his Excel model in #14); the tests come with S7 to S9 |
| CALC-V6 | Price against the fair value at the growth cap (§7 V6) | Same valuation with g1 = 30% (growth 30%, 21.9%, 16.25%, 12.2%, 9.4%, 7.4%, 5.9%, 4.9%, 4.2%, 3.7%): USD 37.37; 30.00 ≤ 37.37 | pass | C | signed off by C (Flo, 21 November 2026, review comment on pull request #5; his Excel model in #14); the fair value at the cap (37.37) passes on branch `c/S8-valuation-engine` (test_v6_input_fair_value_with_starting_growth_at_the_cap); the check itself comes with S9 |
| CALC-W1 | Levered beta | 0.90 × (1 + 0.79 × 450 ÷ 3,000) = 0.90 × 1.1185; inside the 0.8–2.0 limits | 1.00665 | C | signed off by C (Flo, 21 November 2026, review comment on pull request #5; his Excel model in #14); passes on branch `c/S8-valuation-engine` (test_w1_levered_beta) |
| CALC-W2 | Cost of equity | 4.0% + 1.00665 × 5.0% | 9.03325% | C | signed off by C (Flo, 21 November 2026, review comment on pull request #5; his Excel model in #14); passes on branch `c/S8-valuation-engine` (test_w2_cost_of_equity) |
| CALC-F1 | Starting free cash flow | (75 + 115 + 130) ÷ (1,150 + 1,210 + 1,300) = 320 ÷ 3,660 = 8.7432%; × 1,300 | 113.66 | C | signed off by C (Flo, 21 November 2026, review comment on pull request #5; his Excel model in #14); passes on branch `c/S8-valuation-engine` (test_f1_base_free_cash_flows_margin_and_starting_free_cash_flow) |
| CALC-F2 | Free cash flows, years 1–10 | g(t) = 2.5% + 4.2790% × 0.5^((t − 1) ÷ 2); discounted at 9.03325% | 121.37, 128.07, 134.01, 139.39, 144.37, 149.07, 153.59, 158.01, 162.39, 166.75; discounted 111.31, 107.73, 103.39, 98.63, 93.69, 88.72, 83.84, 79.11, 74.56, 70.22 (sum 911.21) | C | signed off by C (Flo, 21 November 2026, review comment on pull request #5; his Excel model in #14); passes on branch `c/S8-valuation-engine` (test_f2_the_ten_forecast_years, test_f2_sum_of_discounted_free_cash_flows) |
| CALC-F3 | Terminal value | 166.75 × 1.025 ÷ (0.0903325 − 0.025) | 2,616.20; discounted 1,101.75 (54.7% of the total) | C | signed off by C (Flo, 21 November 2026, review comment on pull request #5; his Excel model in #14); passes on branch `c/S8-valuation-engine` (test_f3_terminal_value_discounted_and_its_share) |
| CALC-F4 | Fair value per share | Equity value 911.21 + 1,101.75 − minority interests 0 = 2,012.95; ÷ 100 | USD 20.13 | C | signed off by C (Flo, 21 November 2026, review comment on pull request #5; his Excel model in #14); passes on branch `c/S8-valuation-engine` (test_f4_equity_value_and_fair_value_per_share) |
| CALC-S | Area scores (tier 2) | Passes per area from the rows above | 5 of 6, 4 of 6, 6 of 6, 3 of 6 (v2.3: V6 now passes) | E (counts the passes of B's and C's rows; the fixture's `expected_scores()` waits for E) | signed off by E (Emma, 21 November 2026, review comment on pull request #5: 5, 4, 6, 3) |
| CALC-G | Strengths and points to watch (tier 3) | SPEC v2.3 §9 rules on the rows above; SPEC Appendix A table | Shown: G1, G2 (8.78% a year), G3 (17.83% against 15%), G5 (8.0 times), G6; W3 (H2: 540 against 570), W4 (40.24%), W8 (49.0% above the estimate; V6 passes, so no second clause) | B | open, v2.3 value (assistant), B's recalculation pending |

### S7 edge cases (test companies)

Hand working by Flo (C), 22 November 2026, given in his S7 session; written down here by Claude Code and checked by Flo on 22 November 2026 (one wording corrected, S7-A). Test companies in `app/tests/unit/test_dividend_checks.py`: dividends paid in USD millions, FY-4 → FY0; every figure not listed is net income 500, operating cash flow 600 and capital expenditure 100 in every year. Rules and decisions: `app/src/checks/dividend.py`.

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
| S7-A | 30, 32, 34, 36, −10 | Negative FY0 payment: sign error. The negative FY0 dividend makes D1 and D3–D6 insufficient data because each uses that figure. D2 is already insufficient data because it is unassessed in S7 | all six insufficient data | `test_a_negative_fy0_dividend_is_insufficient_data_everywhere` |
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
| S7-T13 | Coca-Cola FY2025, Igor's hand reading (`KO.yaml`): dividends 8,779, operating cash flow 7,408, capital expenditure 2,112 | 8,779 ≤ 7,408 − 2,112 = 5,296 is false | D6 fail, 8,779 against 5,296 | `test_coca_cola_dividend_not_covered_by_cash_in_fiscal_year_2025` |
| S7-T14 | Amazon, saved SEC data (no dividend under any dividend tag; nil, labelled, A's #21) | Nil counts as 0; 0 > 0 is false, so D1 fails and D2–D6 are not applicable (rule of S7-1) | D1 fail, "no dividend paid"; D2–D6 not applicable | `test_amazon_shows_no_dividend_paid` |
| S7-R1 | 30, 32, 34, 36, 36, with FY0 replaced by 0 of kind `assumption` that is not the plan Q1 nil | 0 > 0 is false; only the data layer's nil gets the "treated as nil" sentence | D1 fail, shown as "USD 0"; D2–D6 not applicable | `test_a_zero_assumption_that_is_not_the_nil_is_shown_as_a_plain_zero` |
| S7-R2 | 120, 122, 124, 126, 130, with FY0 capex replaced by −50 of kind `assumption` | Negative payment, but not read from a filing, so no SIGN warning to point to | D6 insufficient data, "a payment is a positive amount" | `test_the_sign_warning_is_named_only_for_a_figure_read_from_a_filing` |

### Risk-free rate (S2b, owner A)

| ID | Input | Working | Expected | Test (`app/tests/unit/test_fred.py`) |
|---|---|---|---|---|
| S2b-RF1 | Fixture `fred_dgs10_small.json`: 4.13, 4.12, (no value), 4.09, 4.15, 4.11 (percent) | Igor's hand working, 24 November 2026: the five days with a value average 4.12% (sum 20.60 ÷ 5); ÷ 100 | 0.0412 | `test_the_rate_is_the_average_of_the_days_with_a_value` |
| S2b-RF2 | 4.00, 4.00, (no value), 5.00 (percent): mean and median differ | Igor's hand working, 24 November 2026: the three days with a value average 0.04333 as a decimal (the middle value would be 0.04); compared to half a unit of its last digit | 0.04333 | `test_the_rate_is_the_mean_not_the_middle_value` |
| S2b-RF3 | One day, 4.50 | DGS10 is in percent (FRED series page, 24 November 2026) | 0.045 | `test_percent_becomes_a_decimal` |
| S2b-RF4 | The saved fallback in `settings.yaml` | US Treasury, Daily Treasury Par Yield Curve Rates, column `10 Yr`, 2021-11-24 to 2026-11-20: 1,247 days with a value, sum 4,900.29, average 3.92966%. To repeat: download the yearly CSV files 2021 to 2026 (`https://home.treasury.gov/resource-center/data-chart-center/interest-rates/daily-treasury-rates.csv/<year>/all?type=daily_treasury_yield_curve&field_tdr_date_value=<year>&page&_format=csv`), keep the days in the period, average the `10 Yr` column, ÷ 100. Computed on 24 November 2026 by a separate script; the same 1,247 days and the same value on every day as FRED DGS10 (checked against FRED's download and the app's live average, 3.9297%, the same day). Taken from the Treasury because FRED's terms forbid storing FRED data (`docs/architecture.md`); saved rounded | 0.0393 | `test_the_saved_fallback_is_set_and_dated` (range and five-year period); the source label: `test_the_saved_value_names_the_treasury_as_its_source` |
### S8 cases (synthetic company, changed one figure at a time)

Hand working by Flo (C), 24 November 2026, from his Excel model (`docs/crosscheck/valuation-crosscheck.xlsx`), given
in his S8 session; written down here by Claude Code, and recalculated independently by Claude Code with a separate
script from the SPEC §8 formulas (not the app's code): all agree. Everything not listed is Appendix A. Tests in
`app/tests/unit/test_valuation_engine.py`.

| Id | Change | Hand working | Expected | Test |
|---|---|---|---|---|
| S8-a | Unlevered beta 1.9 | 1.9 × (1 + (1 − 0.21) × 450 ÷ (30 × 100)) | 2.12515 before the limit; 2.0 used (`beta_max`) | `test_e20_a_beta_outside_the_limits_is_set_to_the_limit_labelled_and_recorded` |
| S8-b | Unlevered beta 0.5 | 0.5 × (1 + (1 − 0.21) × 450 ÷ (30 × 100)) | 0.55925 before the limit; 0.8 used (`beta_min`) | same |
| S8-c | Revenue FY2021 300 | (1,300 ÷ 300)^(1/4) − 1 | 44.2798% (shown 44.3%); 30% used | `test_e18_past_growth_above_the_cap_starts_at_the_cap_with_the_growth_note` |
| S8-d | Revenue FY2021 3,000 | (1,300 ÷ 3,000)^(1/4) − 1 | −18.8655% (shown "fell 18.9%"); −10% used | `test_e18_past_growth_below_the_floor_starts_at_the_floor_with_the_growth_note` |
| S8-e | Minority interest 100 | 2,012.95283165 − 100; ÷ 100 million shares | Equity value 1,912.95283165; USD 19.12952832 (19.13) | `test_a_minority_interest_is_subtracted_from_the_present_value` |
| S8-f | Risk-free rate 2.0% (workbook sheet "Valuation (rf 2%)", added by Flo on 24 November 2026: its own risk-free cell G22, every other input from "Inputs") | gT = min(2.0%, 2.5%); cost of equity 2.0% + 1.00665 × 5.0%; growth path, forecast and terminal value recalculated | gT 2.0%; cost of equity 7.03325%; FCF0 113.66120219; sum of discounted 989.58369563; terminal value 3,271.42402094, discounted 1,657.86709202; equity value 2,647.45078766; USD 26.47450788 (26.47) | `test_terminal_growth_is_the_risk_free_rate_when_that_is_below_2_5_percent` |
| S8-g | Nvidia, saved SEC data (FY2022 to FY2026, SPEC §8.2) | (215,938 ÷ 26,914)^(1/4) − 1 | 68.3014% (shown 68.3%); 30% used | `test_e18_nvidia_past_growth_is_capped_and_the_note_gives_68_3_percent` |

The other S8 edge cases need no number: the rule itself (a limited value equals its setting; a missing input gives
"insufficient data" naming it; FCF0 ≤ 0 or equity value ≤ 0 gives "not applicable") or a relation inside one run.

### Overview (S10c, owner A)

Formulas: change = FY0 ÷ FY-1 − 1 (shown to one decimal); operating margin = operating income ÷ revenue; change in
margin in percentage points (pp); free cash flow = operating cash flow − capital expenditure (as in §8 and D6);
dividend coverage = free cash flow ÷ dividends paid; current ratio = current assets ÷ current liabilities. Amounts of
USD 1 bn or more in USD bn with two decimals, smaller ones in USD m with none. Edge rules (Igor, 25 November):
FY-1 at or below zero gives "not meaningful" instead of a change; negative free cash flow shows both amounts and
"free cash flow was negative", never a negative coverage; revenue or current liabilities missing or at or below zero
give "n/a" with the reason; a dividend treated as nil reads "No dividend paid".

**Synthetic company** (USD m, SPEC Appendix A line items):

| Figure | Hand working | Expected |
|---|---|---|
| Revenue | 1,300; 1,300 ÷ 1,210 − 1 = 0.07438 | USD 1.30 bn, +7.4% |
| Operating margin | 208 ÷ 1,300 = 16.00%; 190 ÷ 1,210 = 15.70%; 16.00 − 15.70 = 0.30 | 16.0%, +0.3 pp |
| Net income | 140; 140 ÷ 128 − 1 = 0.09375 | USD 140 m, +9.4% |
| Free cash flow | 215 − 85 = 130; 195 − 80 = 115; 130 ÷ 115 − 1 = 0.13043 | USD 130 m, +13.0% |
| Five-year free cash flow | 160 − 60 = 100; 175 − 70 = 105; 150 − 75 = 75; 195 − 80 = 115; 215 − 85 = 130 | 100, 105, 75, 115, 130 |
| Dividend coverage | 130 ÷ 56 = 2.3214; 130 − 56 = 74 | 232.1%; free cash flow USD 74 m above dividends |
| Current ratio | 540 ÷ 360 = 1.50 | 1.50× |

**Coca-Cola** (USD m, FY2025 and FY2024 columns of the FY2025 10-K, accession 0001628280-26-010047):

| Figure | Hand working | Expected |
|---|---|---|
| Revenue | 47,941; 47,941 ÷ 47,061 − 1 = 0.01870 | USD 47.94 bn, +1.9% |
| Operating margin | 13,762 ÷ 47,941 = 28.71%; 9,992 ÷ 47,061 = 21.23%; 28.71 − 21.23 = 7.47 | 28.7%, +7.5 pp |
| Net income | 13,107; 13,107 ÷ 10,631 − 1 = 0.23290 | USD 13.11 bn, +23.3% |
| Free cash flow | 7,408 − 2,112 = 5,296; 6,805 − 2,064 = 4,741; 5,296 ÷ 4,741 − 1 = 0.11706 | USD 5.30 bn, +11.7% |
| Dividend coverage | 5,296 ÷ 8,779 = 0.60326; 8,779 − 5,296 = 3,483 | 60.3%; dividends USD 3.48 bn above free cash flow |
| Current ratio | 31,044 ÷ 21,281 = 1.4588 | 1.46× |

Checked by hand: Igor (A), 25 November 2026, every value above with a calculator from the listed figures; all match (rule 14.5).

## Edge cases and errors

| Id | Situation | Expected behaviour | Status |
|---|---|---|---|
| E1 | Unknown ticker | Message: ticker not found, check the spelling; no crash | passes on branch `d/S11-gates` (`test_unknown_ticker_live_e1`, `test_a_ticker_outside_the_demo_data_in_demo_mode`) |
| E2 | Bank, insurer or REIT (SEC code 6000–6799), e.g. JPM | Stop: "not supported" and why (§10) | passes on branch `d/S11-gates` (`test_industry_codes_at_the_bounds_are_stopped`, `test_industry_codes_outside_the_bounds_empty_or_not_a_number_pass`) |
| E3 | Not in US dollars, no 10-K data, or fewer than three fiscal years | Stop with the reason (§10) | passes on branch `d/S11-gates` (`test_no_annual_figures_stop_a_company_outside_the_industry_range`, `test_a_company_filing_in_another_currency_is_stopped`, `test_two_fiscal_years_are_too_few`) |
| E4 | SEC unreachable | Three retries with a growing pause, then the input is `missing`; message suggests demo mode | passes: the client part (`test_after_three_retries_the_source_is_unreachable_and_the_message_says_what_to_do`); the customer message with demo mode on branch `d/S11-gates` (`test_sec_unreachable_suggests_demo_mode_e4`) |
| E5 | A required figure is missing | `missing` with reason; checks that need it show "insufficient data"; never 0, never guessed (§5.2) | passing (tests: test_a_line_item_without_a_company_wide_figure_is_missing_with_a_reason, test_a_derived_figure_with_a_missing_input_stays_missing_and_says_why); the check side: S5–S9 |
| E6 | Two fallback tags give different values for the same period | Figure flagged on the sources page, not chosen silently (§5.3.7) | passing (test: test_two_tags_with_different_values_are_flagged_and_the_first_in_the_list_is_used) |
| E7 | Restated figure differs from the original by more than 1% | Latest filed value used; both shown with a warning (§5.3.4) | passing (test: test_planted_a_restated_figure_uses_the_latest_filing_and_keeps_the_original; KO 2018: test_coca_cola_2018_revenue_restatement_as_shown_in_session_5) |
| E8 | 53-week fiscal year | Kept: flow periods of 350 to 380 days are accepted (§5.3.1) | passing (test: test_a_flow_must_cover_350_to_380_days; Apple: test_apple_has_a_53_week_fiscal_year) |
| E9 | Negative equity | H3, H4, P4, V5 fail with the note "negative equity"; recorded on the sources page, no header warning (§7, §10). H4 decided by Greg on 23 November (plan Q3): known equity ≤ 0 in FY0 or FY-4 fails first | passing for H3, H4, P4 on McDonald's saved data (`test_mcdonalds_known_negative_equity_fails_leverage_checks`, `test_mcdonalds_negative_equity_fails_roe_without_an_industry_benchmark`); V5: C |
| E10 | Net income zero or below | V3, V4 and D5 fail; P2 fails | partly passing (D5, test: test_9_d5_fails_at_exactly_90_percent_and_when_net_income_is_zero_or_negative); V3, V4: S9; P2: S5 |
| E11 | No dividend | D1 fails; D2 to D6 `not applicable`; area shows "no dividend paid", score 0 | passing for the checks (tests: test_1_a_labelled_nil_means_no_dividend_paid, test_2_a_reported_zero_in_fy0_means_no_dividend_paid; Amazon on real data: test_amazon_shows_no_dividend_paid); the area display passes on branch `d/S10-design` (PR #54): `tests/app/test_scorecard.py` `test_amazon_dividend_row_reads_no_dividend_paid_0_passed_of_1_assessed` ("No dividend paid", "0 passed of 1 assessed", five does-not-apply marks; Simon's hand check of 25 November 2026) |
| E12 | Zero debt | H4 (no debt in both years), H5 pass; H6 passes when interest is reported as 0, or when debt is reported as 0 and interest is missing (no ratio invented; an assumed or derived zero debt does not count); the levered beta equals the unlevered beta, kept within the limits 0.8 to 2.0 | passing for H4, H5, H6 (`test_h4_no_debt_in_both_years_passes_even_without_equity`, `test_h5_zero_debt_passes_without_cash_flow`, `test_h6_reported_zero_debt_passes_with_missing_interest_without_filling_it`, `test_h6_assumed_zero_debt_does_not_turn_missing_interest_into_zero`); beta: C |
| E15 | A warning that is not for the customer (e.g. a restated or derived figure) | Not in the header; listed on the sources page next to the figure (§10) | passes on branch `d/S11-gates` (`test_coca_cola_has_no_header_warning_and_its_reading_note_is_on_the_sources_page_e15`) |
| E16 | Any ticker other than the five demo companies | Report shown with the header warning "not fully checked" (§2, §10); the five demo companies, Apple included, never show it | passes on branch `d/S11-gates` (`test_a_ticker_that_is_not_a_demo_company_is_not_fully_checked`, `test_a_company_outside_the_five_shows_not_fully_checked_in_the_header_e16`) |
| E17 | Industry not found in the lookup or the fallback table | Benchmarks `missing`; dependent checks "insufficient data"; no user override (§9.1, v2.3) | open |
| E18 | Past revenue growth above the cap (Nvidia: 68.3% a year, FY2022 to FY2026) or below the floor | Starting growth 30% (or −10%), labelled `assumption`; the note gives the growth before the limit; the valuation detail adds the growth note (§8.2, §8.3) | partly passes: the engine part on branch `c/S8-valuation-engine` (test_e18_*, Nvidia included); shown in the valuation detail with S10b |
| E19 | Three-year free cash flow zero or negative, or equity value ≤ 0 after minority interests | No fair value; V1, V2, V6 `not_applicable` with the reason in plain words; V3 to V5 still assessed (§8.6) | partly passes: the engine gives no fair value and the reason on branch `c/S8-valuation-engine` (test_e19_*); V1, V2, V6 `not_applicable` come with S9 |
| E20 | Levered beta outside 0.8 to 2.0 | Beta set to the limit, labelled `assumption`, the note gives the value before the limit; a record on the sources page, not a header warning (§8.1, §10) | passes in the engine on branch `c/S8-valuation-engine` (test_e20_a_beta_outside_the_limits_is_set_to_the_limit_labelled_and_recorded): a BETA_LIMIT record for the sources page, as SPEC §10 says (not a header warning), the beta printed with enough decimals not to look like the limit (2.003, not 2.00), and the cost of equity uses the limited beta; shown with S10b |
| E22 | A valuation input is missing (e.g. the operating cash flow of one of the last three years, or the debt) or fewer than five fiscal years resolve | No fair value; V1, V2, V6 `insufficient_data` naming the missing input; checked before the cases of E19 (§8.6) | partly passes: the engine gives no fair value and names every missing input, before the E19 cases, on branch `c/S8-valuation-engine` (test_e22_*, 20 cases); V1, V2, V6 `insufficient_data` come with S9 |

## Planted errors (each one a test that must catch it, §5.4)

| Id | Planted error | Expected | Status |
|---|---|---|---|
| PE1 | A nine-month figure read as a year | Rejected: period outside 350–380 days | passing (test: test_planted_a_nine_month_figure_is_never_read_as_a_year) |
| PE2 | Thousands read as millions (or dollars as millions) | Caught by the unit rule and a reconciliation figure | passing (tests: test_planted_amounts_are_kept_in_dollars_exactly_as_filed, test_only_units_as_filed_are_accepted); reconciliation: S15, Coca-Cola 6 of 6 match (`app/tests/reconciliation/KO.yaml`), Nvidia 6 of 6 match (`NVDA.yaml`), 3 companies to do |
| PE3 | Wrong fiscal-year label (prior-year comparative carrying the filing's `fy`) | Fiscal year taken from the period end date (§5.3.2) | passing (tests: test_planted_a_wrong_fiscal_year_label_is_ignored, test_a_comparative_labelled_with_a_later_fiscal_year_lands_in_its_own_year) |
| PE4 | Restated figure | Latest filed value, original kept (§5.3.4) | passing (test: test_planted_a_restated_figure_uses_the_latest_filing_and_keeps_the_original) |
| PE5 | Sign flipped (e.g. capital expenditure positive vs negative) | Caught by a test on the sign convention | passing (tests: test_planted_a_negative_capital_expenditure_is_kept_as_filed_and_flagged, test_a_positive_payment_raises_no_sign_warning); a negative interest expense is flagged and not used (test: test_planted_a_negative_interest_expense_is_flagged_and_not_used) |
| PE6 | Percent against decimal | Ratios stored as decimals; a test fails on 40 instead of 0.40 | passing for settings (test: test_rates_are_decimals_not_percentages); the checks: S5–S9 |
