# Member C: Flo (@florian-spitzer)

**You own:** `app/src/checks/dividend.py`, `app/src/checks/valuation.py`, `app/src/valuation/`, the separate Excel
cross-check model in `docs/crosscheck/`, the `dividend` and `valuation` sections of `app/settings.yaml`, and your
tests. **Backup:** B, Greg (you review Greg's PRs first, Greg reviews yours). **Reconciliation company:** Nvidia (NVDA).

## Your slices, in order

| When | Slice | Done when (SPEC §13.2) |
|---|---|---|
| Wed 18 | Accept the invitation; your `docs/team.md` PR (steps in `docs/team.md`) | Merged |
| Thu 19 | **Excel cross-check model** of the valuation (SPEC §8, version 2.3: growth falls in equal steps from the starting growth to terminal growth) for the synthetic company, built by you from the SPEC formulas, **not** from the code. Save it in `docs/crosscheck/` | Matches SPEC Appendix A v2.3 (fair value USD 19.74, implied starting growth 25.00%), or you report the difference |
| Thu 19 | **Sign-off for S0c:** recalculate rows CALC-D1–D6, CALC-V1–V6, CALC-W1–W4 and CALC-F1–F5 of `docs/acceptance.md` (your Excel model counts) | Your sign-off comment on PR #5 |
| Thu 19 → Wed 25 | S8: cost of capital (beta limited to 0.8–2.0), forecast with the growth limit (−10% to +20%) and fade, terminal value, reverse DCF on the starting growth, sensitivity, "model does not fit" rules (§8.6), the user's own growth and tax rate for a second fair value (§8.7), branch `c/S8-valuation-engine` | Matches your Excel model and Appendix A; property tests pass; one test per case of §8.6 |
| Sat 21–Sun 22 | S7: dividend checks D1–D6 (D2 "not assessed" until S4 and a share price), branch `c/S7-dividend-checks` | Appendix A values reproduced; edge cases tested |
| Mon 23–Wed 25 | S9 with B: valuation checks V1–V6; switch on D2, branch `c/S9-valuation-checks` | Appendix A values reproduced |
| Sat 21–Sun 29 | **Business plan section:** business model, in `docs/business-plan/sections/C-business-model.md` (Emma, E, assembles the plan; prompt in `docs/members/README.md`) | Draft by Sun 22; final by Sun 29 |
| Fri 27–Sun 29 | S18, break-it round: a member from another area reviews your code read-only; you break each of your formulas once on purpose and record each break and the test that caught it in `docs/testing.md` | Every finding is a failing test or a written dismissal |

**Slice prompt** (replace the slice, sections and branch):

> /build-feature I am member C, working on slice [S8] of SPEC.md. Read AGENTS.md, docs/members/member-C.md,
> SPEC.md sections [8, 11 and 15], docs/plan.md and the [CALC-W and CALC-F] rows of docs/acceptance.md. Use the
> branch [c/S8-valuation-engine] from the latest main. Plan this slice only, name the files you will touch and the
> tests you will write first, and wait for my go-ahead. I will give you the expected values. Do not change files
> outside my folders.

Sections per slice: S7 → §5, §7 (dividend), §11; S8 → §8.1–8.7, §11, §15 (property tests); S9 → §7 (valuation),
§8.4, §8.6.

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
- **Real cases for your edge-case tests:** Amazon's dividends paid are `missing` (no tag at all; Q1 decides what
  D1 shows); McDonald's equity is negative (USD −1,791 million at FY2025), so V5 fails with "negative equity".
- Use the line-item names in `LINE_ITEMS` and the units in `UNITS` from `app/src/contracts.py` (e.g.
  `net_income`; amounts stay in USD as filed, never millions).
- "Not assessed" (D2 until S4 and a share price) is the status `insufficient_data` with the reason in the explanation
  (decision Q9 in `docs/plan.md`).
- Appendix A values for your tests come from `synthetic.expected_check("D3")` and
  `synthetic.expected_valuation("cost_of_capital")` in `app/tests/fixtures/synthetic.py`. It refuses a row until your sign-off is recorded (rule 14.5).
- Valuation and checks are pure functions: no network, no interface (SPEC §11). The risk-free rate comes in as an
  input (FRED or `settings.yaml`); downloading it is A's data layer.
- Property tests with Hypothesis (SPEC §15): the cost of capital lies between the after-tax cost of debt and the
  cost of equity; with no debt it equals the cost of equity; the two terminal value forms agree; putting the
  implied growth back into the forecast returns the share price; g(5) equals terminal growth; the beta stays
  within its limits; the user's assumptions never change a check result.
- **Growth (SPEC v2.3 §8.2):** starting growth g1 = past revenue growth FY-4 to FY0, limited to `growth_floor` and
  `growth_cap` (settings), then g(t) = g1 + (gT − g1) × (t − 1) ÷ 4. Real case: Nvidia's past growth is 68.3% a
  year (FY2022 to FY2026), so its g1 is the cap, with a note giving 68.3%.
- Reverse DCF: **never** adjust assumptions to match the price; "no solution in the range" is a valid answer
  (SPEC §8.4). It searches the starting growth with the same fade; the cap does not apply to the search.
- **§8.6, two tests in order:** first, a missing valuation input (or revenue FY0 ≤ 0, or fewer than five years)
  → V1, V2, V6 `insufficient_data` naming it; then the model-fit cases (operating income FY0 ≤ 0, first-year free
  cash flow ≤ 0, equity value ≤ 0, cost of capital ≤ terminal growth) → no fair value, no reverse DCF, no
  sensitivity, V1, V2, V6 `not_applicable` with the reason. V3 to V5 are still assessed. Your module returns these
  reasons and the valuation warnings; Simon's gates only display them.
- **V6 (v2.3):** share price ≤ fair value with g1 set to `growth_cap` (synthetic company: USD 26.91, so fail).
  The implied growth no longer decides any check; the bisection needs a change of sign between −20% and +50%,
  never assumes a direction, and stops at a bracket below 0.000001.
- **Conventions (§8.3, §8.5):** end-of-year discounting, terminal value discounted at t = 5, valuation date the
  end of FY0; the sensitivity grid's terminal growth axis also moves the fade target; cells with cost of capital ≤
  terminal growth show "n/a".
- **User's assumptions (§8.7):** your valuation function takes the starting growth and the tax rate as optional
  parameters; the checks always call it with the automatic values. The interface (Simon) shows the second fair
  value.
- If D1 fails, D2 to D6 are "not applicable" and the area shows "no dividend paid", score 0 (SPEC §7).

## Only you

1. **Expected values:** your own Excel model and hand working. The assistant never supplies them.
2. **FRED terms of use:** read them before S8 and note the result in `docs/architecture.md` (ask A to merge it).
   **Settings:** confirm `growth_floor` (−10%), `growth_cap` (+20%), `beta_min` (0.8) and `beta_max` (2.0) in the
   `valuation` section of `app/settings.yaml`, each with a one-line reason (change them if you have a better one).
3. **Reconciliation (S15), Nvidia:** revenue, operating income, net income, total assets, operating cash flow,
   dividends paid, read by hand from the latest 10-K with page and accession number. Not by the assistant.
4. **Decide** Q1 (missing versus nil, with Greg and Igor, before S7: Amazon has no dividend tag at all (confirmed in the saved SEC files), so Q1 decides whether its D1 shows "no dividend paid" or "insufficient data"); prepare the
   answer to Q6 (why terminal growth barely moves the sensitivity table) for the presentation.
5. **Explain-back** on each PR; at least two reviews a week, Greg's (B) first.
6. **Before the presentation:** five likely questions and answers on your area to E (Sun 29); walk-through (Mon 30).

## If you are blocked

- Everything you build runs on the synthetic company fixture (`app/tests/fixtures/`, from S0c). You do not need
  real SEC data until the integration tests.
