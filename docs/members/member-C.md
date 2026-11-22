# Member C: Flo (@florian-spitzer)

**You own:** `app/src/checks/dividend.py`, `app/src/checks/valuation.py`, `app/src/valuation/`, the separate Excel
cross-check model in `docs/crosscheck/`, the `dividend` and `valuation` sections of `app/settings.yaml`, and your
tests. **Backup:** B, Greg (you review Greg's PRs first, Greg reviews yours). **Reconciliation company:** Nvidia (NVDA).

## Your slices, in order

**Timeline (SPEC v2.4, 22 November):** the MVP is the five demo companies, one workflow end to end. Release v0.1 on **Tuesday 24** (the screen and the 18 checks), v0.2 with the feature freeze on **Thursday 26 at 20:00** (the fair value). The strengths and points to watch (S12) and the Excel export (S13) are built only if v0.2 is released before the freeze.

| When | Slice | Done when (SPEC §13.2) |
|---|---|---|
| Thu 19–Sun 22 | **Excel cross-check model** of the valuation (SPEC §8, equity method) for the synthetic company, built from the SPEC formulas, not from the code | Done: PR #14 (fair value USD 20.13; USD 37.37 at the 30% cap) |
| Thu 19–Sun 22 | **Sign-off for S0c:** rows CALC-D1–D6, CALC-V1–V6, CALC-W1–W2 and CALC-F1–F4 | Done: recorded in PR #5 |
| Sun 22–Tue 24 | S7: dividend checks D1–D6 (D2 "not assessed" until S4 and a share price), branch `c/S7-dividend-checks` | Appendix A values reproduced; edge cases tested; Amazon shows "no dividend paid" once #21 is merged |
| Sun 22–Tue 24 | S15, reconciliation of Nvidia: six figures read by hand from the latest 10-K ("Only you" below; format in `app/tests/reconciliation/README.md`) | `app/tests/reconciliation/NVDA.yaml` merged; 6 of 6 match |
| Now → Thu 26 | S8: the equity method (SPEC §8): cost of equity (beta limited to 0.8–2.0), starting free cash flow from the three-year margin, starting growth capped at −10% to +30% and decaying towards terminal growth (half-life 2 years, 10 years), terminal value at year 10, minus reported minority interests, "model does not fit" (§8.6), the growth note when the growth limit applies. No cost of debt, no sensitivity table, no implied growth, no user inputs. Branch `c/S8-valuation-engine` | Matches your Excel model and Appendix A; property tests pass; one test per case of §8.6 |
| Wed 25–Thu 26 | S9 with B: valuation checks V1–V6; switch on D2, branch `c/S9-valuation-checks` | Appendix A values reproduced |
| Sat 21–Sun 29 | **Business plan section:** business model, in `docs/business-plan/sections/C-business-model.md` (Emma, E, assembles the plan; prompt in `docs/members/README.md`) | Draft now (first planned for Sun 22); final by Sun 29 |
| Fri 27–Sun 29 | S18, break-it round: a member from another area reviews your code read-only; you break each of your formulas once on purpose and record each break and the test that caught it in `docs/testing.md` | Every finding is a failing test or a written dismissal |

**Slice prompt** (replace the slice, sections and branch):

> /build-feature I am member C, working on slice [S8] of SPEC.md. Read AGENTS.md, docs/members/member-C.md,
> SPEC.md sections [8, 11 and 15], docs/plan.md and the [CALC-W and CALC-F] rows of docs/acceptance.md. Use the
> branch [c/S8-valuation-engine] from the latest main. Plan this slice only, name the files you will touch and the
> tests you will write first, and wait for my go-ahead. I will give you the expected values. Do not change files
> outside my folders.

Sections per slice: S7 → §5, §7 (dividend), §11; S8 → §8.1–8.3, §8.6, §11, §15 (property tests); S9 → §7 (valuation),
§8.6. (§8.4, §8.5 and §8.7 are cut in v2.3.)

**How to sign off (S0c):** recalculate your rows on paper or in Excel, then post a review comment on
[PR #5](https://github.com/BossToGo/filing-scorecard/pull/5): the rows, the date, how you calculated, and any
difference. A records it under `sign_off` in `app/tests/fixtures/synthetic_co.yaml`, with a link to your
comment. Until then the fixture refuses your rows with the error `NotSignedOff`, naming you.

## Rules for your area

- **Real data:** the saved SEC files in `app/evidence/demo/<TICKER>/companyfacts.json` (PR #6: KO, AAPL, NVDA,
  MCD, AMZN; JPM must be refused). Read `app/evidence/demo/README.md` first: what the files contain and the
  traits already confirmed. Never download anything in your code or tests.
- **Thresholds:** `from src.settings import load_settings`, then `load_settings()["dividend"]["max_payout_ratio"]` gives 0.90 (PR #7).
  Never hard-code a threshold; a misspelt name raises a `KeyError` naming the section.
- Never import `src.data.sec_client`: only A's data layer talks to the SEC; your code receives `CompanyData`.
- **Loading a company** (PR #8): `from src.data.company import load_company`, then
  `load_company("MCD", demo=True)` gives `CompanyData` from the saved files, with no network (`DEMO_TICKERS`:
  KO, AAPL, NVDA, MCD, AMZN). The latest fiscal year is `data.fiscal_years("revenue")[-1]`. Shares come from
  `data.latest("shares")`, never `data.fact("shares", fy0)`, which is None by design (plan Q12). A `missing`
  figure has value None and its reason in `.note`; a `derived` one has its formula and sources in `.note`.
- **Real cases for your edge-case tests:** Amazon pays no dividend: once #21 is merged, its `dividends_paid` is 0
  in every year, kind `assumption`, note "not reported, treated as nil", warning `NIL_DIVIDEND` (SPEC v2.4 §7,
  plan Q1), so D1 fails and the area shows "no dividend paid"; McDonald's equity is negative (USD −1,791 million at FY2025), so V5 fails with "negative equity".
- Use the line-item names in `LINE_ITEMS` and the units in `UNITS` from `app/src/contracts.py` (e.g.
  `net_income`; amounts stay in USD as filed, never millions).
- "Not assessed" (D2 until S4 and a share price) is the status `insufficient_data` with the reason in the explanation
  (decision Q9 in `docs/plan.md`).
- Appendix A values for your tests come from `synthetic.expected_check("D3")` and
  `synthetic.expected_valuation("cost_of_equity")` in `app/tests/fixtures/synthetic.py`. It refuses a row until your sign-off is recorded (rule 14.5).
- Valuation and checks are pure functions: no network, no interface (SPEC §11). The risk-free rate comes in as an
  input (FRED or `settings.yaml`); downloading it is A's data layer.
- Property tests with Hypothesis (SPEC §15): with no debt the levered beta equals the unlevered beta (within the
  limits); fair value rises with the starting growth and falls with the cost of equity whenever the starting free
  cash flow is positive; g(t) moves towards terminal growth every year and never crosses it; the beta stays within
  its limits.
- **Free cash flow (SPEC v2.3 §8.2):** operating cash flow − capital expenditure. Starting free cash flow = (sum
  of free cash flow FY-2 to FY0 ÷ sum of revenue FY-2 to FY0) × revenue FY0 (`fcf_base_years` = 3). Then
  FCF(t) = FCF(t − 1) × (1 + g(t)) for t = 1 to 10.
- **Growth:** starting growth g1 = past revenue growth FY-4 to FY0, limited to `growth_floor` (−10%) and
  `growth_cap` (+30%), then g(t) = gT + (g1 − gT) × 0.5^((t − 1) ÷ 2): the gap to terminal growth halves every
  `growth_half_life_years` (2). Real case: Nvidia's past growth is 68.3% a year, so its g1 is the cap, with a note
  giving 68.3% and the growth note in the valuation detail.
- **Terminal value and equity value (§8.3):** FCF(10) × (1 + gT) ÷ (cost of equity − gT); end-of-year discounting,
  terminal value discounted at t = 10; equity value = present value − reported minority interests (nil if not
  reported, labelled); ÷ shares. **Never** adjust assumptions to match a price.
- **§8.6, two tests in order:** first, a missing valuation input (revenue FY-4 to FY0, operating cash flow and capex of
  the last three years, financial debt FY0 for the levered beta, shares, the industry beta), or revenue FY0 or
  FY-4 ≤ 0, or fewer than five years → V1, V2, V6 `insufficient_data` naming it; then the model-fit cases (starting free cash flow ≤ 0, or
  equity value ≤ 0) → no fair value, V1, V2, V6 `not_applicable` with the reason. V3 to V5 are still assessed. Your
  module returns these reasons; Simon's interface only displays them.
- **V4 (v2.3):** price to earnings below the **whole US market** (Greg's benchmark file: trailing or current, never
  forward). **V6:** share price ≤ fair value with g1 set to `growth_cap` (synthetic company: USD 37.37, so pass).
- If D1 fails, D2 to D6 are "not applicable" and the area shows "no dividend paid", score 0 (SPEC §7).

## Only you

1. **Expected values:** your own Excel model and hand working. The assistant never supplies them.
2. **FRED terms of use:** read them before S8 and note the result in `docs/architecture.md` (ask A to merge it).
   **Settings:** confirm `fcf_base_years` (3), `forecast_years` (10), `growth_floor` (−10%), `growth_cap` (+30%),
   `growth_half_life_years` (2), `beta_min` (0.8) and `beta_max` (2.0) in the `valuation` section of `app/settings.yaml`, each with a one-line reason (change them if
   you have a better one).
3. **Reconciliation (S15), Nvidia:** revenue, operating income, net income, total assets, operating cash flow,
   dividends paid, read by hand from the latest 10-K with page and accession number. Not by the assistant.
4. **Q1 is decided** (SPEC v2.4 §7, approved by you in #20): a company with no dividend under any dividend entry in
   the five years pays none (Amazon); any sign of a dividend keeps the years `missing`.
5. **Explain-back** on each PR; at least two reviews a week, Greg's (B) first.
6. **Before the presentation:** five likely questions and answers on your area to E (Sun 29); walk-through (Mon 30).

## If you are blocked

- Everything you build runs on the synthetic company fixture (`app/tests/fixtures/`, from S0c). You do not need
  real SEC data until the integration tests.
