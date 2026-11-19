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
| AC6 | F7 | Tier 2 build, synthetic company, share price USD 30.00 | The user types a starting growth of 10% in the valuation detail | A second fair value labelled "with your assumptions" appears; the automatic fair value (USD 19.74), the implied starting growth (25.00%) and the scores (5 of 6, 4 of 6, 6 of 6, 2 of 6) stay the same; the typed value shows as `assumption` (user) (§8.7) | open |
| AC7 | F5 | Network switched off, demo mode on | The user opens each of the five demo companies | Each opens without an error | open |
| AC8 | F6 | Tier 2 build, synthetic company with the synthetic benchmarks | The scorecard opens | P4 pass, P5 fail, D2 pass (share price USD 30.00); each benchmark shows the industry group, the route used, the number of firms and the source file | open |
| AC9 | F7 | Tier 2 build, synthetic company, share price USD 30.00 | The scorecard opens | Fair value USD 19.74 per share; implied starting growth 25.00% labelled "describes the price, it is not a forecast"; scores 5 of 6, 4 of 6, 6 of 6, 2 of 6 (SPEC v2.3 Appendix A; C's recalculation pending) | open |
| AC10 | F7 | Any company, no share price | The scorecard opens | The valuation area shows "insufficient data" and asks for a share price; the other areas still show | open |
| AC11 | F8 | Synthetic company loaded | The user downloads the Excel file | A test reopens it: three sheets (report, figures, sources); every figure equals the screen | open |
| AC12 | F9 | Tier 3 build, synthetic company, share price USD 30.00 | The scorecard opens | Strengths G1, G2, G3, G6, G7; points to watch W5, W6, W11, W12, all minor; each opens its check (SPEC v2.3 §9 and Appendix A; B's recalculation pending) | open |
| AC13 | F4 | Any loaded company | The user looks for a way to change a figure, the industry or a check result | There is none: the only inputs are the ticker, the share price, the demo switch and, in the valuation detail, the optional starting growth and tax rate (§1, §3) | open |

## Screens (how each was checked)

| Id | Screen / state | Expected | Test | Browser check | Looked at by |
|---|---|---|---|---|---|
| V1 | Scorecard, laptop width | Header and score chart visible without scrolling; a unit on every input and figure | AppTest (S17) | not installed | pending |
| V2 | Each error state (unknown ticker, unsupported, source unreachable, no price) | The message says how to fix the problem | AppTest (S11) | not installed | pending |
| V3 | Synthetic company anywhere in the app | "SYNTHETIC DATA" mark visible | AppTest (S10) | not installed | pending |
| V4 | A missing figure in a check or table | Shown as "n/a" with the reason, never as 0 | unit test on the display layer (S10) | not installed | pending |

## Calculations (known answers)

Source: SPEC Appendix A (synthetic company, USD millions; shares 100 million; price USD 30.00; risk-free 4.0%,
premium 5.0%, tax 21%, terminal growth 2.5%, starting growth limited to −10%..+20%, beta limited to 0.8..2.0; benchmarks: unlevered beta 0.90, ROE 15%, operating margin 18%,
P/E 20.0, EV/EBITDA 13.0, P/B 4.0, market dividend yield 1.5%).

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
| CALC-V1 | Below fair value | 30.00 against 19.74 | fail | C | open, v2.3 value (assistant's independent script), C's recalculation pending |
| CALC-V2 | Well below fair value | 30.00 against 0.80 × 19.74 = 15.79 | fail | C | open, v2.3 value (assistant's independent script), C's recalculation pending |
| CALC-V3 | P/E vs industry | 3,000 ÷ 140 | 21.43 > 20.0 → fail | C | open, sign-off pending |
| CALC-V4 | EV/EBITDA vs industry | (3,000 + 450 − 120) ÷ (208 + 65) = 3,330 ÷ 273 | 12.20 < 13.0 → pass | C | open, sign-off pending |
| CALC-V5 | P/B vs industry | 3,000 ÷ 820 | 3.66 < 4.0 → pass | C | open, sign-off pending |
| CALC-V6 | Price against the fair value at the growth cap (§7 V6, v2.3) | Same valuation with g1 = 20% (growth 20%, 15.625%, 11.25%, 6.875%, 2.5%): fair value USD 26.91; 30.00 > 26.91 | fail | C | open, v2.3 value (assistant's independent script), C's recalculation pending |
| CALC-W1 | Levered beta | 0.90 × (1 + 0.79 × 450 ÷ 3,000) = 0.90 × 1.1185; inside the 0.8–2.0 limits | 1.00665 | C | open, sign-off pending |
| CALC-W2 | Cost of equity | 4.0% + 1.00665 × 5.0% | 9.0333% | C | open, sign-off pending |
| CALC-W3 | Cost of debt | 26 ÷ ((440 + 450) ÷ 2) = 26 ÷ 445; after tax × 0.79 | 5.8427%; 4.6157% | C | open, sign-off pending |
| CALC-W4 | Cost of capital | Weights 3,000 ÷ 3,450 = 86.9565%, 13.0435%; 0.869565 × 9.0333% + 0.130435 × 4.6157% | 8.4571% | C | open, sign-off pending |
| CALC-F1 | Forecast inputs | g1 = 6.7790% (inside −10% to +20%); gT = 2.5%; g(t) = 6.7790%, 5.7092%, 4.6395%, 3.5697%, 2.5000%; margin 16.0%; D&A 5.0%; capex 85 ÷ 1,300 = 6.5385%; NWC (540 − 120) − (360 − 50) = 110 → 8.4615% | as listed | C | open, v2.3 value (assistant's independent script), C's recalculation pending |
| CALC-F2 | Free cash flows, years 1–5 | SPEC Appendix A table (v2.3) | 146.65, 156.20, 164.70, 171.91, 177.59; discounted 135.21, 132.79, 129.10, 124.24, 118.34 (sum 639.68) | C | open, v2.3 value (assistant's independent script), C's recalculation pending |
| CALC-F3 | Terminal value | 206.04 × 1.025 ÷ 0.084571; both §8.3 forms agree | 2,497.16; discounted 1,664.02 (72.2% of EV) | C | open, v2.3 value (assistant's independent script), C's recalculation pending |
| CALC-F4 | Fair value per share | Enterprise value 639.68 + 1,664.02 = 2,303.69 (sum of unrounded values); equity 2,303.69 − 450 + 120 = 1,973.69; ÷ 100 | USD 19.74 | C | open, v2.3 value (assistant's independent script), C's recalculation pending |
| CALC-F5 | Implied starting growth at USD 30.00 | Bisection on g1 in −20% to +50%, same fade, cap not applied, bracket narrowed to 0.000001 | 25.00% (24.996%) | C | open, v2.3 value (assistant's independent script), C's recalculation pending |
| CALC-S | Area scores (tier 2) | Passes per area from the rows above | 5 of 6, 4 of 6, 6 of 6, 2 of 6 | B and C | open, sign-off pending |
| CALC-G | Strengths and points to watch (tier 3) | SPEC v2.3 §9 rules on the rows above; SPEC Appendix A table | Shown: G1, G2 (8.78% a year), G3 (17.83% against 15%), G6 (8.0 times), G7; W5 (540 against 570), W6 (40.24%), W11 (52.0% above the estimate), W12 (V6 fails; implied 25.00% against the 20% cap and the company's 6.78%) | B | open, v2.3 value (assistant), B's recalculation pending |

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
| E12 | Zero debt | H4 (no debt in both years), H5, H6 (no debt and no interest) pass; the cost of capital equals the cost of equity | open |
| E13 | Cost of debt outside risk-free to risk-free + 8 points | Risk-free + 1.5 points used, labelled `assumption`, warning (§8.1) | open |
| E14 | No starting growth in −20% to +50% matches the price | No change of sign: "more than 50%" or "less than −20%"; no number reported; no check depends on it (§8.4) | open |
| E15 | Terminal value above 75% of enterprise value | Warning in the header (§10) | open |
| E16 | Ticker outside the verified universe | Report shown, marked "not verified" (§2, §10) | open |
| E17 | Industry not found in the lookup or the fallback table | Benchmarks `missing`; dependent checks "insufficient data"; no user override (§9.1, v2.3) | open |
| E18 | Past revenue growth above the cap (Nvidia: 68.3% a year, FY2022 to FY2026) or below the floor | Starting growth 20% (or −10%), labelled `assumption`; the note gives the growth before the limit; warning in the header (§8.2, §10) | open |
| E19 | Operating income FY0 ≤ 0, first-year free cash flow ≤ 0, equity value ≤ 0, or cost of capital ≤ terminal growth | No fair value, reverse DCF or sensitivity; V1, V2, V6 `not_applicable` with the reason in plain words; V3 to V5 still assessed (§8.6) | open |
| E20 | Levered beta outside 0.8 to 2.0 | Beta set to the limit, labelled `assumption`, the note gives the value before the limit; warning (§8.1, §10) | open |
| E21 | Basic share counts of FY0 and FY-1 not from the same 10-K (e.g. FY-1 missing from the latest filing) | G10 and W14 not shown; from the same 10-K they compare like with like even after a stock split (§9) | open |
| E22 | A valuation input is missing (e.g. depreciation) or fewer than five fiscal years resolve | No fair value; V1, V2, V6 `insufficient_data` naming the missing input; checked before the cases of E19 (§8.6) | open |
| E23 | A company burns cash but holds short-term investments | W15 uses cash and short-term investments (§6); without any investment tag, cash alone and the text says "no short-term investments reported" | open |

## Planted errors (each one a test that must catch it, §5.4)

| Id | Planted error | Expected | Status |
|---|---|---|---|
| PE1 | A nine-month figure read as a year | Rejected: period outside 350–380 days | open |
| PE2 | Thousands read as millions (or dollars as millions) | Caught by the unit rule and a reconciliation figure | open |
| PE3 | Wrong fiscal-year label (prior-year comparative carrying the filing's `fy`) | Fiscal year taken from the period end date (§5.3.2) | open |
| PE4 | Restated figure | Latest filed value, original kept (§5.3.4) | open |
| PE5 | Sign flipped (e.g. capital expenditure positive vs negative) | Caught by a test on the sign convention | open |
| PE6 | Percent against decimal | Ratios stored as decimals; a test fails on 40 instead of 0.40 | open |
