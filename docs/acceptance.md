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
| AC8 | F6 | Tier 2 build, synthetic company with the synthetic benchmarks | The scorecard opens | P4 pass, P5 fail, D2 pass (share price USD 30.00); each benchmark shows the industry group, the route used, the number of firms and the source file | screen side passing on main (#63, 26 November); Simon looked at KO with and without a price (tests: test_ac8_p4_p5_and_d2_get_the_benchmarks_and_the_price, test_ac8_p4_p5_and_d2_are_assessed_with_the_price_and_benchmarks, test_ac8_the_industry_group_its_route_and_number_of_firms_and_the_source) |
| AC9 | F7 | Tier 2 build, synthetic company, share price USD 30.00 | The scorecard opens | The estimate USD 20.13 per share (equity method; `fair_value` in the code, SPEC §3); scores 5 of 6, 4 of 6, 6 of 6, 3 of 6 (SPEC v2.3 Appendix A; the estimate signed off by C, scores by E, 21 November) | screen side passing on main (#63, 26 November); Simon looked at KO with and without a price (tests: test_ac9_the_estimate_and_the_four_scores, test_ac9_the_estimate_per_share_against_the_typed_price, test_ac9_the_four_scores_on_the_chart) |
| AC10 | F7 | Any company, no share price | The scorecard opens | The valuation area shows "insufficient data" and asks for a share price; the other areas still show | check side passing on main (#52) (test: test_without_a_share_price_the_whole_area_is_insufficient_data: all six checks "insufficient data", the text asks for the share price); the screen passing on main (#63, 26 November); Simon looked at KO with and without a price (tests: test_ac10_no_price_needs_a_share_price_and_the_other_areas_still_show, test_main_coca_cola_without_a_price_needs_a_share_price_ac10) |
| AC11 | F8 | Synthetic company loaded | The user downloads the Excel file | A test reopens it: two sheets (the scorecard; the figures with their sources, §3 item 8); every figure equals the screen | open |
| AC16 | F2 | Demo mode, Coca-Cola (KO) | The scorecard opens | The overview above the tabs shows revenue USD 47.94 bn (+1.9% vs FY2024), operating margin 28.7% (+7.5 pp), net income USD 13.11 bn (+23.3%), free cash flow USD 5.30 bn (+11.7%), each marked reported or derived; dividend coverage 60.3%, dividends USD 3.48 bn above free cash flow; current ratio 1.46× (hand working below, "Overview (S10c)") | passing on `main` (#58, 25 November) (`tests/unit/test_overview.py`, `tests/app/test_overview_screen.py`); hand working checked by Igor, 25 November |
| AC17 | F2 | Demo mode, Amazon (AMZN) | The scorecard opens | Dividend coverage reads "No dividend paid", never 0% | passing on `main` (#58, 25 November) (`tests/unit/test_overview.py`, `tests/app/test_overview_screen.py`); hand working checked by Igor, 25 November |
| AC18 | F2 | Any company with a figure missing | The scorecard opens | Each overview figure that needs it shows "n/a" with the reason, never 0; the five-year chart leaves a gap and its table shows "n/a" | passing on `main` (#58, 25 November) (`tests/unit/test_overview.py`, `tests/app/test_overview_screen.py`); hand working checked by Igor, 25 November |
| AC19 | F2 | Tier 1, synthetic company (SPEC Appendix A statuses) | The scorecard opens | The overview's panel "Checks by area" shows a radar with past performance 100% (4 ÷ 4), financial health 67% (4 ÷ 6), dividend 100% (5 ÷ 5) and valuation "Not part of this version" off the shape: the line joins only neighbouring scored areas (financial health with past performance, and with dividend), never past performance with dividend across the centre, and the shape is not filled; with all four scored it is closed and filled. Next to it, a short text on how to read it; no rows of marks (those are in the score chart). "Not a rating of the share and not advice." under the radar; Amazon's dividend axis reads "No dividend paid"; no total and no area to read first (agreed by the whole group on #60, 26 November; panel without its own rows, Igor, 26 November) | passing on `main` (#60, 26 November) (`tests/unit/test_scorecard_summary.py`, `tests/app/test_overview_screen.py`) |
| AC20 | F7 | Demo mode, Coca-Cola (KO), share price USD 97.59 | The scorecard opens | The valuation comes first on the page: the share price and the estimate (V1's own figures) on one scale with the zones "80% of the estimate or less" (V2's mark), "80% to 100% of the estimate" and "Above the estimate", the estimate at the growth cap (V6) marked, and the sentence "The share price you typed, USD 97.59, is 206.9% above the estimate of USD 31.80."; price to earnings 32.02× against 37.11× for the industry and 60.26× for the US market (V3, V4), price to book 13.05× against 6.87× for the industry (V5). Without a price, the checks' reason instead of the chart; no advice words | passing on branch `a/S10d-overview-charts` (`tests/unit/test_overview_charts.py`, `tests/app/test_overview_screen.py`) |
| AC21 | F2 | Demo mode, Coca-Cola (KO) | The scorecard opens | Under the radar, one section per area of the main screen, each chart with one sentence and its figures as a table ("Figures"): where the revenue goes (revenue USD 47.94 bn to cost of revenue 18.40 and gross profit 29.54, to operating expenses 15.78 and operating income 13.76, to interest, tax and other 0.655 and net income 13.11, 27.3% of revenue); the balance sheet split (cash 9.8%, financial debt 43.4%, equity 32.7% of total assets USD 104.82 bn); short-term assets against short- and long-term liabilities; debt, equity and cash over five years (debt 141.4% of equity in FY2025, 185.9% in FY2021); dividends against free cash flow (covered in 3 of 5 years, not in FY2024 and FY2025); earnings payout 67.0%; dividend yield 2.09% against 1.10% for the US market. Hand working: "Overview charts (S10d)" below | passing on branch `a/S10d-overview-charts` (`tests/unit/test_overview_charts.py`, `tests/app/test_overview_screen.py`) |
| AC22 | F2 | McDonald's (negative equity), Amazon (no dividend), a loss or a missing figure | The scorecard opens | Negative equity is said in words and never drawn as a part ("...liabilities are larger than assets, so equity is negative (USD −1.79 bn)."; debt to equity "not meaningful"); no dividend gives no payout ring and "No dividend paid in FY2025."; a loss gives no flow chart and says why; parts larger than their total leave no negative "other" part; a missing figure is "n/a" with its reason, never 0; the charts take no background colour of their own, so a theme switch leaves no dark box | passing on branch `a/S10d-overview-charts` (`tests/unit/test_overview_charts.py`, `tests/app/test_overview_screen.py`) |
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
| CALC-P1 | Consistently profitable | Net income 100, 115, 105, 128, 140: all > 0 | 5 of 5 (at least 4) → pass | B | signed off by B (Greg), 24 November 2026: [P4, P5 his own hand working; the other rows Simon's hand working of 19 November, compared by Greg](https://github.com/BossToGo/filing-scorecard/pull/5#pullrequestreview-6039789536) |
| CALC-P2 | Growing profit | 140 > 100 and 140 > 0 | pass | B | signed off by B (Greg), 24 November 2026: [P4, P5 his own hand working; the other rows Simon's hand working of 19 November, compared by Greg](https://github.com/BossToGo/filing-scorecard/pull/5#pullrequestreview-6039789536) |
| CALC-P3 | Profit growth is speeding up | 140 ÷ 128 − 1 = 9.375%; (140 ÷ 100)^(1/4) − 1 = 8.776% | 9.375% > 8.776% → pass | B | signed off by B (Greg), 24 November 2026: [P4, P5 his own hand working; the other rows Simon's hand working of 19 November, compared by Greg](https://github.com/BossToGo/filing-scorecard/pull/5#pullrequestreview-6039789536) |
| CALC-P4 | Return on equity above its industry | 140 ÷ ((750 + 820) ÷ 2) = 140 ÷ 785 | 17.83% > 15% → pass | B | signed off by B (Greg), 24 November 2026: [P4, P5 his own hand working; the other rows Simon's hand working of 19 November, compared by Greg](https://github.com/BossToGo/filing-scorecard/pull/5#pullrequestreview-6039789536) |
| CALC-P5 | Margin above its industry | 208 ÷ 1,300 | 16.00% < 18% → fail | B | signed off by B (Greg), 24 November 2026: [P4, P5 his own hand working; the other rows Simon's hand working of 19 November, compared by Greg](https://github.com/BossToGo/filing-scorecard/pull/5#pullrequestreview-6039789536) |
| CALC-P6 | Return on capital improved | 208 ÷ (1,750 − 360) = 208 ÷ 1,390; FY-3: 170 ÷ (1,480 − 310) = 170 ÷ 1,170 | 14.96% > 14.53% → pass | B | signed off by B (Greg), 24 November 2026: [P4, P5 his own hand working; the other rows Simon's hand working of 19 November, compared by Greg](https://github.com/BossToGo/filing-scorecard/pull/5#pullrequestreview-6039789536) |
| CALC-H1 | Short-term liabilities covered | 540 > 360 | pass | B | signed off by B (Greg), 24 November 2026: [P4, P5 his own hand working; the other rows Simon's hand working of 19 November, compared by Greg](https://github.com/BossToGo/filing-scorecard/pull/5#pullrequestreview-6039789536) |
| CALC-H2 | Long-term liabilities covered | 540 against 930 − 360 = 570 | fail | B | signed off by B (Greg), 24 November 2026: [P4, P5 his own hand working; the other rows Simon's hand working of 19 November, compared by Greg](https://github.com/BossToGo/filing-scorecard/pull/5#pullrequestreview-6039789536) |
| CALC-H3 | Moderate debt | (450 − 120) ÷ 820 = 330 ÷ 820 | 40.24% ≥ 40% → fail | B | signed off by B (Greg), 24 November 2026: [P4, P5 his own hand working; the other rows Simon's hand working of 19 November, compared by Greg](https://github.com/BossToGo/filing-scorecard/pull/5#pullrequestreview-6039789536) |
| CALC-H4 | Debt falling against equity | 450 ÷ 820 = 54.88% against 400 ÷ 600 = 66.67% | pass | B | signed off by B (Greg), 24 November 2026: [P4, P5 his own hand working; the other rows Simon's hand working of 19 November, compared by Greg](https://github.com/BossToGo/filing-scorecard/pull/5#pullrequestreview-6039789536) |
| CALC-H5 | Debt covered by cash flow | 215 ÷ 450 | 47.78% ≥ 20% → pass | B | signed off by B (Greg), 24 November 2026: [P4, P5 his own hand working; the other rows Simon's hand working of 19 November, compared by Greg](https://github.com/BossToGo/filing-scorecard/pull/5#pullrequestreview-6039789536) |
| CALC-H6 | Interest well covered | 208 ÷ 26 | 8.0 ≥ 5 → pass | B | signed off by B (Greg), 24 November 2026: [P4, P5 his own hand working; the other rows Simon's hand working of 19 November, compared by Greg](https://github.com/BossToGo/filing-scorecard/pull/5#pullrequestreview-6039789536) |
| CALC-D1 | Pays a dividend | 56 > 0 | pass | C | passing (test: test_appendix_a_synthetic_company[D1]); signed off by C on PR #5 |
| CALC-D2 | Dividend yield above the US market | 56 ÷ (30.00 × 100) = 56 ÷ 3,000 | 1.867% > 1.5% → pass | C | passing on branch `c/S9-valuation-checks` (test: test_appendix_a_d2_with_share_price_and_market_yield); signed off by C on PR #5. Without the share price or the market yield D2 stays "not assessed" (test: test_appendix_a_d2_is_not_assessed_without_share_price_and_benchmark) |
| CALC-D3 | No large dividend cut | Changes: +10%, +9.09%, −6.25% (48 to 45), +24.44% | largest fall −6.25% → pass | C | passing (test: test_appendix_a_synthetic_company[D3]); signed off by C on PR #5 |
| CALC-D4 | Dividend grew | 56 > 40 | pass | C | passing (test: test_appendix_a_synthetic_company[D4]); signed off by C on PR #5 |
| CALC-D5 | Dividend covered by profit | 56 ÷ 140 | 40% < 90% → pass | C | passing (test: test_appendix_a_synthetic_company[D5]); signed off by C on PR #5 |
| CALC-D6 | Dividend covered by cash | 56 ≤ 215 − 85 = 130 | pass | C | passing (test: test_appendix_a_synthetic_company[D6]); signed off by C on PR #5 |
| CALC-V1 | Price below the cash-flow estimate (SPEC §7 wording of 24 November; was "Below fair value") | 30.00 against 20.13 | fail | C | passing on branch `c/S9-valuation-checks` (test: test_appendix_a_synthetic_company[V1]); signed off by C (Flo, 21 November 2026, review comment on pull request #5; his Excel model in #14) |
| CALC-V2 | Price at or below 80% of the estimate (SPEC §7 wording of 24 November; was "Well below fair value") | 30.00 against 0.80 × 20.13 = 16.10 | fail | C | passing on branch `c/S9-valuation-checks` (test: test_appendix_a_synthetic_company[V2]); signed off by C (Flo, 21 November 2026, review comment on pull request #5; his Excel model in #14) |
| CALC-V3 | P/E vs industry | 3,000 ÷ 140 | 21.43 > 20.0 → fail | C | passing on branch `c/S9-valuation-checks` (test: test_appendix_a_synthetic_company[V3]); signed off by C (Flo, 21 November 2026, review comment on pull request #5; his Excel model in #14) |
| CALC-V4 | P/E vs the whole US market (v2.3) | 3,000 ÷ 140 = 21.43 against the synthetic market P/E 24.0 | 21.43 < 24.0 → pass | C | passing on branch `c/S9-valuation-checks` (test: test_appendix_a_synthetic_company[V4]); signed off by C (Flo, 21 November 2026, review comment on pull request #5; his Excel model in #14) |
| CALC-V5 | P/B vs industry | 3,000 ÷ 820 | 3.66 < 4.0 → pass | C | passing on branch `c/S9-valuation-checks` (test: test_appendix_a_synthetic_company[V5]); signed off by C (Flo, 21 November 2026, review comment on pull request #5; his Excel model in #14) |
| CALC-V6 | Price against the fair value at the growth cap (§7 V6) | Same valuation with g1 = 30% (growth 30%, 21.9%, 16.25%, 12.2%, 9.4%, 7.4%, 5.9%, 4.9%, 4.2%, 3.7%): USD 37.37; 30.00 ≤ 37.37 | pass | C | signed off by C (Flo, 21 November 2026, review comment on pull request #5; his Excel model in #14); the fair value at the cap (37.37) passes on branch `c/S8-valuation-engine` (test_v6_input_fair_value_with_starting_growth_at_the_cap); the check passes on branch `c/S9-valuation-checks` (test: test_appendix_a_synthetic_company[V6]) |
| CALC-W1 | Levered beta | 0.90 × (1 + 0.79 × 450 ÷ 3,000) = 0.90 × 1.1185; inside the 0.8–2.0 limits | 1.00665 | C | signed off by C (Flo, 21 November 2026, review comment on pull request #5; his Excel model in #14); passes on branch `c/S8-valuation-engine` (test_w1_levered_beta) |
| CALC-W2 | Cost of equity | 4.0% + 1.00665 × 5.0% | 9.03325% | C | signed off by C (Flo, 21 November 2026, review comment on pull request #5; his Excel model in #14); passes on branch `c/S8-valuation-engine` (test_w2_cost_of_equity) |
| CALC-F1 | Starting free cash flow | (75 + 115 + 130) ÷ (1,150 + 1,210 + 1,300) = 320 ÷ 3,660 = 8.7432%; × 1,300 | 113.66 | C | signed off by C (Flo, 21 November 2026, review comment on pull request #5; his Excel model in #14); passes on branch `c/S8-valuation-engine` (test_f1_base_free_cash_flows_margin_and_starting_free_cash_flow) |
| CALC-F2 | Free cash flows, years 1–10 | g(t) = 2.5% + 4.2790% × 0.5^((t − 1) ÷ 2); discounted at 9.03325% | 121.37, 128.07, 134.01, 139.39, 144.37, 149.07, 153.59, 158.01, 162.39, 166.75; discounted 111.31, 107.73, 103.39, 98.63, 93.69, 88.72, 83.84, 79.11, 74.56, 70.22 (sum 911.21) | C | signed off by C (Flo, 21 November 2026, review comment on pull request #5; his Excel model in #14); passes on branch `c/S8-valuation-engine` (test_f2_the_ten_forecast_years, test_f2_sum_of_discounted_free_cash_flows) |
| CALC-F3 | Terminal value | 166.75 × 1.025 ÷ (0.0903325 − 0.025) | 2,616.20; discounted 1,101.75 (54.7% of the total) | C | signed off by C (Flo, 21 November 2026, review comment on pull request #5; his Excel model in #14); passes on branch `c/S8-valuation-engine` (test_f3_terminal_value_discounted_and_its_share) |
| CALC-F4 | Fair value per share | Equity value 911.21 + 1,101.75 − minority interests 0 = 2,012.95; ÷ 100 | USD 20.13 | C | signed off by C (Flo, 21 November 2026, review comment on pull request #5; his Excel model in #14); passes on branch `c/S8-valuation-engine` (test_f4_equity_value_and_fair_value_per_share) |
| CALC-S | Area scores (tier 2) | Passes per area from the rows above | 5 of 6, 4 of 6, 6 of 6, 3 of 6 (v2.3: V6 now passes) | E (counts the passes of B's and C's rows; the fixture's `expected_scores()` waits for E) | signed off by E (Emma, 21 November 2026, review comment on pull request #5: 5, 4, 6, 3); valuation 3 of 6 passing on branch `c/S9-valuation-checks` (test: test_appendix_a_valuation_area_score) |
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

### Latest figures: twelve months to the latest 10-Q and the latest balance sheet (S2c, owner A; issue #71, item 1)

Rule: twelve months = last fiscal year (10-K) + this year's year to date (10-Q) − last year's year to date (the
comparison column of the same 10-Q); when the 10-K is the latest report, that fiscal year. Figures in USD million,
read from the SEC company facts downloaded on 18 November 2026 (`app/.cache/sec/`, the same files as the demo data),
each with its tag and accession number; the arithmetic written out by Claude Code on 26 November 2026, recalculated
by a separate read-only script that does not use the app's code (not committed), and re-read independently from the
raw files by the code and test reviewer agents on 27 November (every value matches). **Status: checked by Igor
with a calculator on 27 November 2026, every row: all match (rule 14.5).** Amazon's 10-Q states its own twelve-month totals (S2c-AMZN): an
independent source for three of its figures. Tests: `app/tests/integration/test_twelve_months_demo.py`; the rule
itself on a hand-made company in `app/tests/unit/test_twelve_months.py` (its arithmetic written in the test).

| ID | Company, period | Working (fiscal year + year to date − last year's year to date) | Expected |
|---|---|---|---|
| S2c-KO | Coca-Cola, 2025-09-27 to 2026-10-02. 10-K 0001628280-26-010047 (FY2025); 10-Q 0001628280-26-067844 (nine months to 2026-10-02 and to 2025-09-26) | revenue (`Revenues`) 47,941 + 39,232 − 36,119; net income (`NetIncomeLoss`) 13,107 + 12,358 − 10,836; operating cash flow (`NetCashProvidedByUsedInOperatingActivities`) 7,408 + 12,471 − 3,652; capital expenditure (`PaymentsToAcquirePropertyPlantAndEquipment`) 2,112 + 1,063 − 1,230 | 51,054; 14,629; 16,227; 1,945 (free cash flow 16,227 − 1,945 = 14,282, as in #71) |
| S2c-AMZN | Amazon, 2025-10-01 to 2026-09-30. 10-K 0001018724-26-000004 (FY2025); 10-Q 0001018724-26-000040 (nine months to 2026-09-30 and to 2025-09-30) | revenue (`RevenueFromContractWithCustomerExcludingAssessedTax`) 716,924 + 584,069 − 503,538; net income 77,670 + 113,587 − 56,478; operating cash flow 139,514 + 113,841 − 85,055; capital expenditure (`PaymentsToAcquireProductiveAssets`) 131,819 + 175,670 − 92,297. The same 10-Q states "twelve months ended September 30, 2026": net income 134,779, operating cash flow 168,300, capital expenditure 215,192 | 797,455; 134,779; 168,300; 215,192 |
| S2c-MCD | McDonald's, 2025-10-01 to 2026-09-30. 10-K 0000063908-26-000035 (FY2025); 10-Q 0000063908-26-000083 (nine months) | revenue (`Revenues`) 26,885 + 20,773 − 19,876; net income 8,563 + 6,831 − 6,399; operating cash flow 10,551 + 8,254 − 7,854; capital expenditure (`PaymentsToAcquirePropertyPlantAndEquipment`) 3,365 + 2,401 − 2,306 | 27,782; 8,995; 10,951; 3,460 |
| S2c-NVDA | Nvidia, 2025-07-28 to 2026-07-26. 10-K 0001045810-26-000021 (fiscal year 2025-01-27 to 2026-01-25); 10-Q 0001045810-26-000075 (six months to 2026-07-26 and to 2025-07-27) | revenue (`Revenues`) 215,938 + 177,837 − 90,805; net income 120,067 + 118,010 − 45,197; operating cash flow 102,718 + 74,421 − 42,779; capital expenditure (`PaymentsToAcquireProductiveAssets`) 6,042 + 4,434 − 3,122 | 302,970; 192,880; 134,360; 7,354 |
| S2c-AAPL | Apple, fiscal year 2025-09-28 to 2026-09-26: the 10-K 0000320193-26-000026 (filed 2026-11-03) is the latest report, no 10-Q after it | the fiscal year itself: revenue (`RevenueFromContractWithCustomerExcludingAssessedTax`), net income, operating cash flow, capital expenditure (`PaymentsToAcquirePropertyPlantAndEquipment`) | 478,834; 132,175; 145,097; 9,041 |
| S2c-BS-KO | Coca-Cola, balance sheet 2026-10-02 (10-Q 0001628280-26-067844); cover page 2026-10-26 | debt: `LongTermDebtAndCapitalLeaseObligationsIncludingCurrentMaturities` 41,546 (= non-current 36,623 + current 4,923); no short-term borrowings under the tags of `tag_map.yaml` (the 10-Q tags USD 73 m of loans and notes payable as `NotesAndLoansPayable`, which the debt rules do not read; agreed by Igor, 26 November: same rules as the annual figures); minority interest `MinorityInterest` 2,161; shares 4,301,902,335 | debt 41,546; minority 2,161; shares 4,301,902,335 |
| S2c-BS-AMZN | Amazon, 2026-09-30 (10-Q 0001018724-26-000040); cover 2026-10-21 | debt: `LongTermDebt` 180,887 (non-current 173,125 + current 6,827 = 179,952, within 1%) + `ShortTermBorrowings` 380; no minority interest tagged in any report: nil | debt 181,267; minority 0 (nil); shares 10,813,138,306 |
| S2c-BS-MCD | McDonald's, 2026-09-30 (10-Q 0000063908-26-000083); cover dated 2026-09-30 | debt: `LongTermDebtNoncurrent` 39,820, the only debt tag in the 10-Q; McDonald's classifies short-term debt inside long-term debt (company override in `tag_map.yaml`), so nothing is added (the figure's note still says "no current portion reported"; agreed by Igor, 26 November); no minority interest: nil | debt 39,820; minority 0 (nil); shares 705,784,744 |
| S2c-BS-NVDA | Nvidia, 2026-07-26 (10-Q 0001045810-26-000075); cover 2026-08-21 | debt: `LongTermDebt` 33,366 (= 32,366 + 1,000), no short-term borrowings; no minority interest: nil | debt 33,366; minority 0 (nil); shares 24,100,000,000 |
| S2c-BS-AAPL | Apple, 2026-09-26 (the 10-K, as for the annual figures); cover 2026-10-23 | debt: `LongTermDebt` 78,114 (= 68,208 + 9,906) + `CommercialPaper` 1,997; no minority interest: nil | debt 80,111; minority 0 (nil); shares 14,532,182,000 |

Rule cases from the review of PR #72 (27 November 2026). Each one is a unit test on the hand-made company, with its
arithmetic, in `app/tests/unit/test_twelve_months.py`. The real cases were checked on the cached downloads of
18 November (not committed, so not a test):

| Case | Real company (USD m) | Expected |
|---|---|---|
| Last year's year to date restated in this 10-Q by more than 1% | S&P Global: nine months 2025 first filed 11,420 (0000064040-25-000167), 10,117 in the 2026 10-Q (0000064040-26-000058); its FY2025 10-K (15,336) did not restate 2024, so 15,336 + 11,074 − 10,117 = 16,293 would mix two bases, and no figure on one basis can be built from the filings (its 2026 nine months, 11,074, are recast too). CrowdStrike's net income (−187.9 first filed, −174.4 restated) is a careful miss: its FY2026 10-K had itself restated FY2025 (−19.3 to −15.2), so it may be on the same basis; the rule does not try to tell (second review round, 27 November) | missing, both values in the reason, which says the 10-K year *may* be on another basis |
| A 10-Q after the 10-K, but no year to date starting the day after the fiscal year end (e.g. a fiscal year end moved) | none of the 100 cached companies | the four twelve-month figures missing; debt, minority interest and shares from that 10-Q |
| No debt tag in the 10-Q | Caterpillar 36,210 and Western Digital 1,052 at their fiscal year ends | the fiscal-year-end debt, dated, said in the note (Igor, 27 November) |
| Minority interest: 0 in the 10-K, nothing in the 10-Q | Dell | nil |
| Minority interest missing at the fiscal year end (reported the year before), nothing in the 10-Q | Eli Lilly (79.5 at 2024-12-31) | missing |
| Minority interest reported at the fiscal year end (not 0), nothing in the 10-Q | Southern Company (2,851 at 2025-12-31; 10-Q to 2026-03-31) | the fiscal-year-end figure, dated and said (Igor, 27 November, second round), as for debt and shares |
| The 10-K is the latest report and its year runs 53 weeks | Micron (2025-08-29 to 2026-09-03), Disney (2025-09-28 to 2026-10-03): 371 days | the fiscal year, its note saying "371 days" |
| The synthetic company of Appendix A (annual data only, built by hand, not by the resolver) | – | its FY2025 figures, written out in `tests/fixtures/synthetic.py` with a note (Flo's request on #72, #71 item 6) |
| The SEC's filing list names a 10-Q its company facts do not hold yet | Southern Company (10-Q filed 2026-11-05), NextEra (filed 2026-10-21): figures to 2026-03-31 | figures from the latest 10-Q in the company facts, every note naming the missing 10-Q |
| No minority interest tagged, total equity above equity by more than 1% at the quarter end | Uber (28,575 against equity) | nil, with MINORITY_UNTAGGED in the note |
| The 10-Q uses another tag than the 10-K's fiscal-year figure | ADP revenue, Marriott capital expenditure (5 figures of 400 in the 100 companies) | missing (the definitions may differ) |

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
give "n/a" with the reason; a dividend treated as nil reads "No dividend paid". A change that rounds to 0.0% or
0.0 pp is unchanged and shown without an up or down arrow (Igor, 27 November, S18): revenue 1,000 → 1,000.4 is
1,000.4 ÷ 1,000 − 1 = 0.04%, shown "+0.0%" with no arrow (`test_a_change_that_rounds_to_zero_is_shown_without_an_arrow`).

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

### Overview charts (S10d, owner A)

Formulas (Igor, 26 November: the usual chart for each question, our own design and words, rule 14.16): where the
revenue goes = revenue → cost of revenue (revenue − gross profit) and gross profit → operating expenses (gross profit
− operating income) and operating income → interest, tax and other (operating income − net income) and net income;
without a gross profit, one step "operating costs" (revenue − operating income); net income above operating income
comes in as "other income, net". Long-term liabilities = total liabilities − current liabilities. Balance sheet
split: each part ÷ total assets; parts not reported separately stay in "other assets" or "other liabilities" (named
in a note: "not in the data as a separate figure"), equity = total assets − total liabilities, never drawn when at
or below zero; the balance sheet is drawn as two block charts (assets; liabilities and equity), each block's area its
amount. A gross profit that the data layer works out (Amazon files none) is said under the flow. Debt to equity = financial
debt ÷ shareholder equity. Earnings payout = dividends paid ÷ net income. The valuation and ratio charts show the
checks' own figures (V1, V2, V3, V4, V5, V6, D2). Percentages to one decimal; a half is rounded away from zero, as by
hand (34.275 gives 34.28; Python's own format gave 34.27, fixed in `src/overview.py`).

**Synthetic company** (USD m, SPEC Appendix A line items, FY2025 and FY2021):

| Figure | Hand working | Expected |
|---|---|---|
| Where the revenue goes | 1,300 − 208 = 1,092; 208 − 140 = 68; 140 ÷ 1,300 = 0.10769 | operating costs USD 1.09 bn, operating income USD 208 m, interest, tax and other USD 68 m, net income USD 140 m, 10.8% of revenue |
| Financial position | 540; 360; 930 − 360 = 570 | above short-term liabilities, below long-term liabilities |
| Balance sheet split | 120 ÷ 1,750 = 6.857%; 1,750 − 120 = 1,630 → 93.143%; 450 ÷ 1,750 = 25.714%; 930 − 450 = 480 → 27.429%; 1,750 − 930 = 820 → 46.857% | 6.9%, 93.1%; 25.7%, 27.4%, 46.9% |
| Debt to equity | 450 ÷ 820 = 0.54878; 400 ÷ 600 = 0.66667 | 54.9% in FY2025, 66.7% in FY2021 |
| Dividends against free cash flow | free cash flow 100, 105, 75, 115, 130 against dividends 40, 44, 48, 45, 56 | covered in all 5 years |
| Earnings payout | 56 ÷ 140 = 0.40 | 40.0% |
| Share price against the estimate (results built by hand) | 30 ÷ 20.13 − 1 = 0.49031; 0.8 × 20.13 = 16.104; 15 ÷ 20.13 − 1 = −0.25484 | 49.0% above; 80% mark USD 16.10; 25.5% below |

**Coca-Cola** (USD m, FY2025 10-K, accession 0001628280-26-010047; FY2021 to FY2024 columns of the earlier 10-Ks):

| Figure | Hand working | Expected |
|---|---|---|
| Where the revenue goes | 47,941 − 29,544 = 18,397; 29,544 − 13,762 = 15,782; 13,762 − 13,107 = 655; 13,107 ÷ 47,941 = 0.27340 | 18.40 bn, 29.54 bn, 15.78 bn, 13.76 bn, 655 m, 13.11 bn, 27.3% |
| Financial position | 31,044; 21,281; 70,541 − 21,281 = 49,260 | USD 31.04 bn, 21.28 bn, 49.26 bn |
| Balance sheet split | of 104,816: cash 10,270 (9.798%), receivables 3,038 (2.898%), inventory 4,425 (4.222%), PP&E 9,613 (9.171%), investments 20,235 (19.305%), other 104,816 − 47,581 = 57,235 (54.605%); debt 45,492 (43.402%), other liabilities 70,541 − 45,492 = 25,049 (23.898%), equity 104,816 − 70,541 = 34,275 (32.700%) | 9.8%, 2.9%, 4.2%, 9.2%, 19.3%, 54.6% (USD 57.24 bn); 43.4%, 23.9%, 32.7% (USD 34.28 bn) |
| Debt to equity | 45,492 ÷ 32,169 = 1.41416; 42,761 ÷ 22,999 = 1.85926 | 141.4% in FY2025, 185.9% in FY2021 |
| Dividends against free cash flow | 11,258, 9,534, 9,747, 4,741, 5,296 against 7,252, 7,616, 7,952, 8,359, 8,779 | covered in 3 of 5 years; not in FY2024 and FY2025 |
| Earnings payout | 8,779 ÷ 13,107 = 0.66979 | 67.0% |

**McDonald's** (USD m, FY2025 10-K filed 24 February 2026): total assets 59,515, total liabilities 61,306, so equity
59,515 − 61,306 = −1,791 (negative, not drawn); financial debt 39,973 ÷ 59,515 = 0.67165 → 67.2%; cash 774 ÷ 59,515 =
0.01300 → 1.3%.

Worked by Claude Code from the listed figures. Checked by hand: Igor (A), 27 November 2026, every value above with a
calculator from the listed figures, and the McDonald's right-hand column (39,973 + 1,149 + 20,184 = 61,306) and
Amazon's equity (411.065 → USD 411.07 bn); all match (rule 14.5). The synthetic dividend yield 56 ÷ 3,000 was checked
to one decimal (1.9%); the screen shows two, 1.87%, as D2 does.

### S9 edge cases (test cases and real companies)

Hand working by Flo (C), 25 November 2026, given in his S9 session; written down here by Claude Code and recomputed by
Claude Code by hand (all agree). Prices and estimates in USD per share; in S9-E5 to S9-E10 the market value is 20.00 × 100
million shares = USD 2,000 million. Tests in `app/tests/unit/test_valuation_checks.py` (S9-E1 to S9-E8),
`app/tests/unit/test_dividend_checks.py` (S9-E9, S9-E10) and `app/tests/integration/test_valuation_demo.py` (real companies).

| Id | Case | Hand working | Expected | Test |
|---|---|---|---|---|
| S9-T1 | Review round 2 (ties): price 2.01, 1,000,000 shares, net income USD 100,000, industry P/E 20.1 (case found by the code reviewer; worked by Flo) | 2.01 × 1,000,000 = 2,010,000; ÷ 100,000 = 20.1, not below 20.1 | V3 fail, shown "20.10 against 20.10" | `test_s9_t1_a_price_to_earnings_equal_to_the_benchmark_by_hand_fails` |
| S9-T2 | Review round 2 (ties): dividends USD 30,150, price 2.01, 1,000,000 shares, market yield 1.5% (worked by Flo) | 30,150 ÷ 2,010,000 = 0.015, exactly 1.5%, not above 1.5% | D2 fail, shown "1.50% against 1.50%" | `test_s9_t2_a_yield_equal_to_the_market_yield_by_hand_fails` |
| S9-R9 | Review of 25 November: V2 with `well_below_fair_value` set to 50%; price 12.00, estimate 20.00 (proposed by Claude Code, confirmed by Flo) | 0.5 × 20.00 = 10.00; 12.00 ≤ 10.00 no | V2 fail, threshold 10.00 | `test_s9_r9_v2_reads_its_share_of_the_estimate_from_the_settings` |
| S9-W8 | Synthetic company (Appendix A), price 30.00; the unrounded estimate from Flo's Excel model (sheet "Valuation", cell G17); the gap in cell I17, added by Flo on 25 November 2026 after Igor's review of #52 | Flo (25 November 2026): In Excel, I calculated the gap as =(30-G17)/G17 on the Valuation sheet, using the unrounded estimate in G17 (displayed as USD 20.13). Rounded to one decimal place, the USD 30.00 share price is 49.0% above the estimate. | 49.0% above the estimate (the G7/W8 figure; SPEC Appendix A shows the same for W8) | `test_appendix_a_gap_to_the_estimate_for_g7_and_w8` |
| S9-E1 | Price 15.00, estimate 20.00 | (15.00 − 20.00) ÷ 20.00 = −25.0% | "25.0% below the estimate" | `test_s9_e1_gap_below_the_estimate` |
| S9-E2 | Price 20.00, estimate 20.00, estimate at the cap 20.00 | V1: 20.00 < 20.00 no; V2: 20.00 ≤ 0.80 × 20.00 = 16.00 no; V6: 20.00 ≤ 20.00 yes | V1 fail, V2 fail, V6 pass; "at the estimate" | `test_s9_e2_price_equal_to_the_estimate_and_to_the_estimate_at_the_cap` |
| S9-E3 | Price 16.00, estimate 20.00 | V1: 16.00 < 20.00; V2: 16.00 ≤ 16.00 (exactly at the threshold) | V1 pass, V2 pass | `test_s9_e3_price_exactly_at_80_percent_of_the_estimate` |
| S9-E4 | Price 25.00, estimate at the cap 25.00 | 25.00 ≤ 25.00 | V6 pass | `test_s9_e4_price_equal_to_the_estimate_at_the_cap` |
| S9-E5 | Net income USD 100 million; industry and market P/E 20.0 | 2,000 ÷ 100 = 20.0, not below 20.0 | V3 fail, V4 fail | `test_s9_e5_price_to_earnings_equal_to_both_benchmarks_fails` |
| S9-E6 | Net income USD 0, then USD −50 million | no earnings / a loss | V3 fail, V4 fail, no P/E (also without benchmarks) | `test_s9_e6_no_earnings_fails_v3_and_v4_without_a_ratio`, `test_s9_e6_no_earnings_fails_even_without_benchmarks` |
| S9-E7 | Equity USD 500 million; industry P/B 4.0 | 2,000 ÷ 500 = 4.0, not below 4.0 | V5 fail | `test_s9_e7_price_to_book_equal_to_the_benchmark_fails` |
| S9-E8 | Equity USD 0, then USD −1,791 million | – | V5 fail, no P/B, "equity is zero" / "negative equity" (also without the benchmark) | `test_s9_e8_zero_or_negative_equity_fails_v5_without_a_ratio` |
| S9-E9 | Dividends USD 30 million; market yield 1.50% | 30 ÷ 2,000 = 1.50%, not above 1.50% | D2 fail | `test_s9_e9_yield_equal_to_the_market_yield_fails` |
| S9-E10 | Dividends USD 20 million; market yield 1.50% | 20 ÷ 2,000 = 1.00% | D2 fail | `test_s9_e10_yield_below_the_market_yield_fails` |
| S9-MCD | McDonald's, FY2025 10-K (accession 0000063908-26-000035), Consolidated Balance Sheet, printed page 41, "Total shareholders' equity (deficit)" (1,791), read by Flo; the saved SEC data agree | equity USD −1,791 million at 31 December 2025 | V5 fail, "negative equity", even without the benchmark | `test_mcdonalds_negative_equity_fails_v5_even_without_the_benchmark` |
| S9-NVDA | Nvidia, saved SEC data: past growth 68.3% a year (S8-g), above the 30% cap | the estimate at the cap is the estimate itself | a price below it: V1 and V6 pass; above it: both fail; V6 says it uses the same estimate as V1 | `test_nvidia_growth_at_the_cap_v6_uses_the_same_estimate_as_v1` |

Flo's decisions for S9 (25 November 2026), in the docstring of `app/src/checks/valuation.py`: (a) a price equal to
the estimate fails V1 and reads "at the estimate"; (b) V6 keeps its own ≤ rule when growth is already at the cap and
says so; (c) a missing share price or share count makes the whole area "insufficient data", then net income ≤ 0 or
equity ≤ 0 fails before a missing benchmark is looked at; (d) the share price is the user's input, not a `Fact`. The
missing-figure cases need no number: the rule itself ("insufficient data" naming the figure). Two tests use a
relation, not a number: doubling the share count doubles P/E and P/B and halves the dividend yield (added after a
planted bug that ignored the share count passed every other test).

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
| E8a | A fiscal year end moved by about two weeks: a last year of 380 days (16 December 2024 to 31 December 2025) after a year ending 15 December 2024 | No gap: the earlier years are kept and no `FY_GAP` is raised, because a gap is counted as §5.3.1 counts a year (§5.3.9, clarified on 27 November); a next year end 382 days after the last (16 days not covered) is a gap | passing (test: test_a_gap_is_counted_the_way_a_year_is) |
| E9 | Negative equity | H3, H4, P4, V5 fail with the note "negative equity"; recorded on the sources page, no header warning (§7, §10). H4 decided by Greg on 23 November (plan Q3): known equity ≤ 0 in FY0 or FY-4 fails first | passing for H3, H4, P4 on McDonald's saved data (`test_mcdonalds_known_negative_equity_fails_leverage_checks`, `test_mcdonalds_negative_equity_fails_roe_without_an_industry_benchmark`); V5: check side passing on branch `c/S9-valuation-checks` (test: test_mcdonalds_negative_equity_fails_v5_even_without_the_benchmark) |
| E10 | Net income zero or below | V3, V4 and D5 fail; P2 fails | partly passing (D5, test: test_9_d5_fails_at_exactly_90_percent_and_when_net_income_is_zero_or_negative); V3, V4: check side passing on branch `c/S9-valuation-checks` (tests: test_s9_e6_no_earnings_fails_v3_and_v4_without_a_ratio, test_igor_4_zero_earnings_fail_even_without_benchmarks); P2: S5 |
| E11 | No dividend | D1 fails; D2 to D6 `not applicable`; area shows "no dividend paid", score 0 | passing for the checks (tests: test_1_a_labelled_nil_means_no_dividend_paid, test_2_a_reported_zero_in_fy0_means_no_dividend_paid; Amazon on real data: test_amazon_shows_no_dividend_paid); the area display passes on branch `d/S10-design` (PR #54): `tests/app/test_scorecard.py` `test_amazon_dividend_row_reads_no_dividend_paid_0_passed_of_1_assessed` ("No dividend paid", "0 passed of 1 assessed", five does-not-apply marks; Simon's hand check of 25 November 2026) |
| E12 | Zero debt | H4 (no debt in both years), H5 pass; H6 passes when interest is reported as 0, or when debt is reported as 0 and interest is missing (no ratio invented; an assumed or derived zero debt does not count); the levered beta equals the unlevered beta, kept within the limits 0.8 to 2.0 | passing for H4, H5, H6 (`test_h4_no_debt_in_both_years_passes_even_without_equity`, `test_h5_zero_debt_passes_without_cash_flow`, `test_h6_reported_zero_debt_passes_with_missing_interest_without_filling_it`, `test_h6_assumed_zero_debt_does_not_turn_missing_interest_into_zero`); beta: C |
| E15 | A warning that is not for the customer (e.g. a restated or derived figure) | Not in the header; listed on the sources page next to the figure (§10) | passes on branch `d/S11-gates` (`test_coca_cola_has_no_header_warning_and_its_reading_note_is_on_the_sources_page_e15`) |
| E16 | Any ticker other than the five demo companies | Report shown with the header warning "not fully checked" (§2, §10); the five demo companies, Apple included, never show it | passes on branch `d/S11-gates` (`test_a_ticker_that_is_not_a_demo_company_is_not_fully_checked`, `test_a_company_outside_the_five_shows_not_fully_checked_in_the_header_e16`) |
| E17 | Industry not found in the lookup or the fallback table | Benchmarks `missing`; dependent checks "insufficient data"; no user override (§9.1, v2.3) | open |
| E18 | Past revenue growth above the cap (Nvidia: 68.3% a year, FY2022 to FY2026) or below the floor | Starting growth 30% (or −10%), labelled `assumption`; the note gives the growth before the limit; the valuation detail adds the growth note (§8.2, §8.3) | partly passes: the engine part on branch `c/S8-valuation-engine` (test_e18_*, Nvidia included); shown in the valuation detail with S10b |
| E19 | Three-year free cash flow zero or negative, or equity value ≤ 0 after minority interests | No fair value; V1, V2, V6 `not_applicable` with the reason in plain words; V3 to V5 still assessed (§8.6) | partly passes: the engine gives no fair value and the reason on branch `c/S8-valuation-engine` (test_e19_*); V1, V2, V6 `not_applicable` with the engine's reason: check side passing on branch `c/S9-valuation-checks` (test: test_igor_6_the_real_engines_status_and_reason_reach_v1_v2_and_v6); V3 to V5 still assessed (test: test_v1_v2_v6_take_the_engines_status_and_reason) |
| E20 | Levered beta outside 0.8 to 2.0 | Beta set to the limit, labelled `assumption`, the note gives the value before the limit; a record on the sources page, not a header warning (§8.1, §10) | passes in the engine on branch `c/S8-valuation-engine` (test_e20_a_beta_outside_the_limits_is_set_to_the_limit_labelled_and_recorded): a BETA_LIMIT record for the sources page, as SPEC §10 says (not a header warning), the beta printed with enough decimals not to look like the limit (2.003, not 2.00), and the cost of equity uses the limited beta; shown with S10b |
| E22 | A valuation input is missing (e.g. the operating cash flow of one of the last three years, or the debt) or fewer than five fiscal years resolve | No fair value; V1, V2, V6 `insufficient_data` naming the missing input; checked before the cases of E19 (§8.6) | partly passes: the engine gives no fair value and names every missing input, before the E19 cases, on branch `c/S8-valuation-engine` (test_e22_*, 20 cases); V1, V2, V6 `insufficient_data` with the engine's reason: check side passing on branch `c/S9-valuation-checks` (test: test_igor_6_the_real_engines_status_and_reason_reach_v1_v2_and_v6) |

## Planted errors (each one a test that must catch it, §5.4)

| Id | Planted error | Expected | Status |
|---|---|---|---|
| PE1 | A nine-month figure read as a year | Rejected: period outside 350–380 days | passing (test: test_planted_a_nine_month_figure_is_never_read_as_a_year) |
| PE2 | Thousands read as millions (or dollars as millions) | Caught by the unit rule and a reconciliation figure | passing (tests: test_planted_amounts_are_kept_in_dollars_exactly_as_filed, test_only_units_as_filed_are_accepted); reconciliation: S15, Coca-Cola 6 of 6 match (`app/tests/reconciliation/KO.yaml`), Nvidia 6 of 6 match (`NVDA.yaml`), 3 companies to do |
| PE3 | Wrong fiscal-year label (prior-year comparative carrying the filing's `fy`) | Fiscal year taken from the period end date (§5.3.2) | passing (tests: test_planted_a_wrong_fiscal_year_label_is_ignored, test_a_comparative_labelled_with_a_later_fiscal_year_lands_in_its_own_year) |
| PE4 | Restated figure | Latest filed value, original kept (§5.3.4) | passing (test: test_planted_a_restated_figure_uses_the_latest_filing_and_keeps_the_original) |
| PE5 | Sign flipped (e.g. capital expenditure positive vs negative) | Caught by a test on the sign convention | passing (tests: test_planted_a_negative_capital_expenditure_is_kept_as_filed_and_flagged, test_a_positive_payment_raises_no_sign_warning); a negative interest expense is flagged and not used (test: test_planted_a_negative_interest_expense_is_flagged_and_not_used) |
| PE6 | Percent against decimal | Ratios stored as decimals; a test fails on 40 instead of 0.40 | passing for settings (test: test_rates_are_decimals_not_percentages); the checks: S5–S9 |
