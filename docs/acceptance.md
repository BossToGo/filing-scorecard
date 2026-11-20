# Acceptance criteria

Each criterion is checkable: a starting state, an action, an expected result. Status: `open`, `passing
(test: <test name>)`, `checked by hand on <date>`, or `failing`. Section numbers (§) point to `SPEC.md`.

## Main user journey

| Id | Feature | Given | When | Then | Status |
|---|---|---|---|---|---|
| AC1 | F1 | Demo mode on | The user types `KO` | The header shows The Coca-Cola Company, its industry and how the industry was found, fiscal year end, latest 10-K date, retrieval date, and any warnings | open |
| AC2 | F1 | Any mode | The user types `JPM` | "Not supported" with the reason (bank, SEC industry code in 6000–6799); no scores shown | open |
| AC3 | F2 | Tier 1 build, synthetic company, no share price | The scorecard opens | Past performance 4 passed of 4 assessed (P4, P5 "not assessed": status `insufficient_data`, no benchmark yet); financial health 4 of 6; dividend 5 passed of 5 assessed (D2 "not assessed") | open |
| AC4 | F2 | Any loaded company | The user opens a check | It shows the result, the rule in plain words, the formula, the input figures with units and fiscal years, and a link to the filing | open |
| AC5 | F3 | Any loaded company | The user opens the sources page | One row per figure with metric, value, unit, period, kind, tag, form, accession, filing date, retrieval time and note; each missing figure shows its reason and the checks it blocks | open |
| AC6 | F4 | Any loaded company | The user looks for an input other than the ticker, the share price and the demo switch | There is none: no way to change a figure, the industry, an assumption or a check result; the scorecard is the same for every user (§1, §3, §8.7) | open |
| AC7 | F5 | Network switched off, demo mode on | The user opens each of the five demo companies | Each opens without an error | open |
| AC8 | F6 | Tier 2 build, synthetic company with the synthetic benchmarks | The scorecard opens | P4 pass, P5 fail, D2 pass (share price USD 30.00); each benchmark shows the industry group, the route used, the number of firms and the source file | open |
| AC9 | F7 | Tier 2 build, synthetic company, share price USD 30.00 | The scorecard opens | Fair value USD 20.13 per share (equity method); scores 5 of 6, 4 of 6, 6 of 6, 3 of 6 (SPEC v2.3 Appendix A; C's recalculation pending) | open |
| AC10 | F7 | Any company, no share price | The scorecard opens | The valuation area shows "insufficient data" and asks for a share price; the other areas still show | open |
| AC11 | F8 | Synthetic company loaded | The user downloads the Excel file | A test reopens it: three sheets (report, figures, sources); every figure equals the screen | open |
| AC12 | F9 | Tier 3 build, synthetic company, share price USD 30.00 | The scorecard opens | Strengths G1, G2, G3, G5, G6; points to watch W3, W4, W8, all minor; each opens its check (SPEC v2.3 §9 and Appendix A; B's recalculation pending) | open |

## Screens (how each was checked)

| Id | Screen / state | Expected | Test | Browser check | Looked at by |
|---|---|---|---|---|---|
| V1 | Scorecard, laptop width | Header and score chart visible without scrolling; a unit on every input and figure | AppTest (S17) | not installed | pending |
| V2 | Each error state (unknown ticker, unsupported, source unreachable, no price) | The message says how to fix the problem | AppTest (S11) | not installed | pending |
| V3 | Synthetic company anywhere in the app | "SYNTHETIC DATA" mark visible | AppTest (S10) | not installed | pending |
| V4 | A missing figure in a check or table | Shown as "n/a" with the reason, never as 0 | unit test on the display layer (S10) | not installed | pending |

## Calculations (known answers)

Source: SPEC Appendix A (synthetic company, USD millions; shares 100 million; price USD 30.00; risk-free 4.0%,
premium 5.0%, tax 21% (beta only), terminal growth 2.5%, free cash flow margin over three years, starting growth limited to −10%..+30% and halving its gap to 2.5% every 2 years over 10 years, beta limited to 0.8..2.0; benchmarks: unlevered beta 0.90, ROE 15%, operating margin 18%,
P/E 20.0 (industry) and 24.0 (whole US market), P/B 4.0, market dividend yield 1.5%).

**Rule 14.5:** these values may be used in tests only after the owner named in each row has recalculated them by
hand or in Excel and signed off in slice S0c. If a recalculation disagrees, the recalculation wins and SPEC
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
| CALC-D1 | Pays a dividend | 56 > 0 | pass | C | open, sign-off pending |
| CALC-D2 | Yield above market | 56 ÷ (30.00 × 100) = 56 ÷ 3,000 | 1.867% > 1.5% → pass | C | open, sign-off pending |
| CALC-D3 | No large cut | Changes: +10%, +9.09%, −6.25% (48 to 45), +24.44% | largest fall −6.25% → pass | C | open, sign-off pending |
| CALC-D4 | Dividend grew | 56 > 40 | pass | C | open, sign-off pending |
| CALC-D5 | Covered by earnings | 56 ÷ 140 | 40% < 90% → pass | C | open, sign-off pending |
| CALC-D6 | Covered by cash | 56 ≤ 215 − 85 = 130 | pass | C | open, sign-off pending |
| CALC-V1 | Below fair value | 30.00 against 20.13 | fail | C | open, v2.3 value (assistant's independent script), C's recalculation pending |
| CALC-V2 | Well below fair value | 30.00 against 0.80 × 20.13 = 16.10 | fail | C | open, v2.3 value (assistant's independent script), C's recalculation pending |
| CALC-V3 | P/E vs industry | 3,000 ÷ 140 | 21.43 > 20.0 → fail | C | open, sign-off pending |
| CALC-V4 | P/E vs the whole US market (v2.3) | 3,000 ÷ 140 = 21.43 against the synthetic market P/E 24.0 | 21.43 < 24.0 → pass | C | open, v2.3 value (assistant's independent script), C's recalculation pending |
| CALC-V5 | P/B vs industry | 3,000 ÷ 820 | 3.66 < 4.0 → pass | C | open, sign-off pending |
| CALC-V6 | Price against the fair value at the growth cap (§7 V6) | Same valuation with g1 = 30% (growth 30%, 21.9%, 16.2%, 12.2%, 9.4%, 7.4%, 5.9%, 4.9%, 4.2%, 3.7%): USD 37.37; 30.00 ≤ 37.37 | pass | C | open, v2.3 value (assistant's independent script), C's recalculation pending |
| CALC-W1 | Levered beta | 0.90 × (1 + 0.79 × 450 ÷ 3,000) = 0.90 × 1.1185; inside the 0.8–2.0 limits | 1.00665 | C | open, sign-off pending |
| CALC-W2 | Cost of equity | 4.0% + 1.00665 × 5.0% | 9.0333% | C | open, sign-off pending |
| CALC-F1 | Starting free cash flow | (75 + 115 + 130) ÷ (1,150 + 1,210 + 1,300) = 320 ÷ 3,660 = 8.7432%; × 1,300 | 113.66 | C | open, v2.3 value (assistant's independent script), C's recalculation pending |
| CALC-F2 | Free cash flows, years 1–10 | g(t) = 2.5% + 4.2790% × 0.5^((t − 1) ÷ 2); discounted at 9.0333% | 121.37, 128.07, 134.01, 139.39, 144.37, 149.07, 153.59, 158.01, 162.39, 166.75; discounted 111.31, 107.73, 103.39, 98.63, 93.69, 88.72, 83.84, 79.11, 74.56, 70.22 (sum 911.21) | C | open, v2.3 value (assistant's independent script), C's recalculation pending |
| CALC-F3 | Terminal value | 166.75 × 1.025 ÷ (0.0903325 − 0.025) | 2,616.20; discounted 1,101.75 (54.7% of the total) | C | open, v2.3 value (assistant's independent script), C's recalculation pending |
| CALC-F4 | Fair value per share | Equity value 911.21 + 1,101.75 − minority interests 0 = 2,012.95; ÷ 100 | USD 20.13 | C | open, v2.3 value (assistant's independent script), C's recalculation pending |
| CALC-S | Area scores (tier 2) | Passes per area from the rows above | 5 of 6, 4 of 6, 6 of 6, 3 of 6 (v2.3: V6 now passes) | B and C | open, sign-off pending (E's earlier check gave 2 of 6 for valuation under the old rules) |
| CALC-G | Strengths and points to watch (tier 3) | SPEC v2.3 §9 rules on the rows above; SPEC Appendix A table | Shown: G1, G2 (8.78% a year), G3 (17.83% against 15%), G5 (8.0 times), G6; W3 (H2: 540 against 570), W4 (40.24%), W8 (49.0% above the estimate; V6 passes, so no second clause) | B | open, v2.3 value (assistant), B's recalculation pending |

## Edge cases and errors

| Id | Situation | Expected behaviour | Status |
|---|---|---|---|
| E1 | Unknown ticker | Message: ticker not found, check the spelling; no crash | open |
| E2 | Bank, insurer or REIT (SEC code 6000–6799), e.g. JPM | Stop: "not supported" and why (§10) | open |
| E3 | Not in US dollars, no 10-K data, or fewer than three fiscal years | Stop with the reason (§10) | open |
| E4 | SEC unreachable | Three retries with a growing pause, then the input is `missing`; message suggests demo mode | open |
| E5 | A required figure is missing | `missing` with reason; checks that need it show "insufficient data"; never 0, never guessed (§5.2) | open |
| E6 | Two fallback tags give different values for the same period | Figure flagged on the sources page, not chosen silently (§5.3.7) | open |
| E7 | Restated figure differs from the original by more than 1% | Latest filed value used; both shown with a warning (§5.3.4) | open |
| E8 | 53-week fiscal year | Kept: flow periods of 350 to 380 days are accepted (§5.3.1) | open |
| E9 | Negative equity | H3, P4, V5 fail with the note "negative equity"; warning in the header (§7, §10). H4: see open question in `docs/plan.md` | open |
| E10 | Net income zero or below | V3 and D5 fail; P2 fails | open |
| E11 | No dividend | D1 fails; D2 to D6 `not applicable`; area shows "no dividend paid", score 0 | open |
| E12 | Zero debt | H4 (no debt in both years), H5, H6 (no debt and no interest) pass; the levered beta equals the unlevered beta | open |
| E15 | A warning that is not for the customer (e.g. a restated or derived figure) | Not in the header; listed on the sources page next to the figure (§10) | open |
| E16 | Ticker outside the verified universe | Report shown, marked "not verified" (§2, §10) | open |
| E17 | Industry not found in the lookup or the fallback table | Benchmarks `missing`; dependent checks "insufficient data"; no user override (§9.1, v2.3) | open |
| E18 | Past revenue growth above the cap (Nvidia: 68.3% a year, FY2022 to FY2026) or below the floor | Starting growth 30% (or −10%), labelled `assumption`; the note gives the growth before the limit; the valuation detail adds the "cautious estimate" line (§8.2, §8.3) | open |
| E19 | Three-year free cash flow zero or negative, or equity value ≤ 0 after minority interests | No fair value; V1, V2, V6 `not_applicable` with the reason in plain words; V3 to V5 still assessed (§8.6) | open |
| E20 | Levered beta outside 0.8 to 2.0 | Beta set to the limit, labelled `assumption`, the note gives the value before the limit; warning (§8.1, §10) | open |
| E22 | A valuation input is missing (e.g. depreciation) or fewer than five fiscal years resolve | No fair value; V1, V2, V6 `insufficient_data` naming the missing input; checked before the cases of E19 (§8.6) | open |

## Planted errors (each one a test that must catch it, §5.4)

| Id | Planted error | Expected | Status |
|---|---|---|---|
| PE1 | A nine-month figure read as a year | Rejected: period outside 350–380 days | open |
| PE2 | Thousands read as millions (or dollars as millions) | Caught by the unit rule and a reconciliation figure | open |
| PE3 | Wrong fiscal-year label (prior-year comparative carrying the filing's `fy`) | Fiscal year taken from the period end date (§5.3.2) | open |
| PE4 | Restated figure | Latest filed value, original kept (§5.3.4) | open |
| PE5 | Sign flipped (e.g. capital expenditure positive vs negative) | Caught by a test on the sign convention | open |
| PE6 | Percent against decimal | Ratios stored as decimals; a test fails on 40 instead of 0.40 | open |
