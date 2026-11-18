# Member C: [name] ([@github])

**You own:** `app/src/checks/dividend.py`, `app/src/checks/valuation.py`, `app/src/valuation/`, the separate Excel
cross-check model in `docs/crosscheck/`, the `dividend` and `valuation` sections of `app/settings.yaml`, and your
tests. **Backup:** B (you review B's PRs first, B reviews yours). **Reconciliation company:** Nvidia (NVDA).

## Your slices, in order

| When | Slice | Done when (SPEC §13.2) |
|---|---|---|
| Wed 18 | Accept the invitation; your `docs/team.md` PR (steps in `docs/team.md`) | Merged |
| Thu 19 | **Excel cross-check model** of the valuation (SPEC §8) for the synthetic company, built by you from the SPEC formulas, **not** from the code. Save it in `docs/crosscheck/` | Matches SPEC Appendix A, or you report the difference |
| Thu 19 | **Sign-off for S0c:** recalculate rows CALC-D1–D6, CALC-V1–V6, CALC-W1–W4 and CALC-F1–F5 of `docs/acceptance.md` (your Excel model counts) | Your sign-off comment on A's S0c PR |
| Thu 19 → Wed 25 | S8: cost of capital, forecast, terminal value, reverse DCF, sensitivity, branch `c/S8-valuation-engine` | Matches your Excel model and Appendix A; property tests pass |
| Sat 21–Sun 22 | S7: dividend checks D1–D6 (D2 "not assessed" until S4 and a share price), branch `c/S7-dividend-checks` | Appendix A values reproduced; edge cases tested |
| Mon 23–Wed 25 | S9 with B: valuation checks V1–V6; switch on D2, branch `c/S9-valuation-checks` | Appendix A values reproduced |
| Fri 27–Sun 29 | S18, break-it round: a member from another area reviews your code read-only; you break each of your formulas once on purpose and record each break and the test that caught it in `docs/testing.md` | Every finding is a failing test or a written dismissal |

**Slice prompt** (replace the slice, sections and branch):

> /build-feature I am member C, working on slice [S8] of SPEC.md. Read AGENTS.md, docs/members/member-C.md,
> SPEC.md sections [8, 11 and 15], docs/plan.md and the [CALC-W and CALC-F] rows of docs/acceptance.md. Use the
> branch [c/S8-valuation-engine] from the latest main. Plan this slice only, name the files you will touch and the
> tests you will write first, and wait for my go-ahead. I will give you the expected values. Do not change files
> outside my folders.

Sections per slice: S7 → §5, §7 (dividend), §11; S8 → §8, §11, §15 (property tests); S9 → §7 (valuation), §8.4.

## Rules for your area

- Valuation and checks are pure functions: no network, no interface (SPEC §11). The risk-free rate comes in as an
  input (FRED or `settings.yaml`); downloading it is A's data layer.
- Property tests with Hypothesis (SPEC §15): the cost of capital lies between the after-tax cost of debt and the
  cost of equity; with no debt it equals the cost of equity; the two terminal value forms agree; putting the
  implied growth back into the forecast returns the share price.
- Reverse DCF: **never** adjust assumptions to match the price; "no solution in the range" is a valid answer
  (SPEC §8.4).
- If D1 fails, D2 to D6 are "not applicable" and the area shows "no dividend paid", score 0 (SPEC §7).

## Only you

1. **Expected values:** your own Excel model and hand working. The assistant never supplies them.
2. **FRED terms of use:** read them before S8 and note the result in `docs/architecture.md` (ask A to merge it).
3. **Reconciliation (S15), Nvidia:** revenue, operating income, net income, total assets, operating cash flow,
   dividends paid, read by hand from the latest 10-K with page and accession number. Not by the assistant.
4. **Decide** Q4 (reverse DCF for loss-making companies) and Q1 (missing versus nil, with B and A); prepare the
   answer to Q6 (why terminal growth barely moves the sensitivity table) for the presentation.
5. **Explain-back** on each PR; at least two reviews a week, B's first.
6. **Before the presentation:** five likely questions and answers on your area to E (Sun 29); walk-through (Mon 30).

## If you are blocked

- Everything you build runs on the synthetic company fixture (`app/tests/fixtures/`, from S0c). You do not need
  real SEC data until the integration tests.
