# Member B: Greg (@Greg3334444)

**You own:** `app/src/benchmarks/`, `app/scripts/extract_benchmarks.py`, `app/scripts/requirements-scripts.txt`, the
industry files in `app/data/` (`benchmarks_us_2026.csv`, `industry_lookup_us_2026.csv`, `sic_to_damodaran.csv`),
`app/src/checks/past.py`, `app/src/checks/health.py`, `app/src/forces.py` (five forces indicators and suggested
ratings), `docs/benchmarks.md`, the `benchmarks`, `past_performance`, `financial_health` and `forces` sections of
`app/settings.yaml`, and your tests.
**Backup:** C, Flo (you review Flo's PRs first, Flo reviews yours). **Reconciliation company:** Apple (AAPL).

## Your slices, in order

| When | Slice | Done when (SPEC §13.2) |
|---|---|---|
| Wed 18 | Accept the invitation; your `docs/team.md` PR (steps in `docs/team.md`) | Merged |
| Thu 19 | **Day-one task (30 min, no code):** open Damodaran's `indname.xls`; write its sheet and column names in `docs/benchmarks.md`; say whether it has a ticker column (in which format, e.g. `NasdaqGS:AAPL`) and SEC industry codes (SPEC §9.1) | `docs/benchmarks.md` merged |
| Thu 19 | **Sign-off for S0c:** recalculate rows CALC-P1 to CALC-P6 and CALC-H1 to CALC-H6 of `docs/acceptance.md` by hand or in Excel | Your sign-off comment on PR #5 |
| Sat 21–Sun 22 | S5: past performance checks P1–P6 (P4, P5 "not assessed" until S4), branch `b/S5-past-checks` | SPEC Appendix A values reproduced; edge cases tested |
| Sat 21–Sun 22 | S6: financial health checks H1–H6, branch `b/S6-health-checks` | Same |
| Thu 19 → Wed 25 | S4: extraction script, benchmark CSV, industry lookup and fallback table, branch `b/S4-benchmarks` | Loader tests; three benchmark values and three company-to-group matches compared by hand with the source files |
| Mon 23–Wed 25 | S9 with C: switch on P4 and P5 | SPEC Appendix A values reproduced |
| Thu 26 | S12: five forces indicators and suggested ratings in `app/src/forces.py` (SPEC §9), branch `b/S12-five-forces`; Simon (D) shows them on screen | Indicator tests pass; override survives recalculation |
| Sat 21–Sun 29 | **Business plan section:** users, market and alternatives, in `docs/business-plan/sections/B-market.md` (Emma, E, assembles the plan; prompt in `docs/members/README.md`) | Draft by Sun 22; final by Sun 29 |
| Fri 27–Sun 29 | S18, break-it round: a member from another area reviews your code read-only; you break each of your formulas once on purpose and record each break and the test that caught it in `docs/testing.md` | Every finding is a failing test or a written dismissal |

**Slice prompt** (replace the slice, sections and branch):

> /build-feature I am member B, working on slice [S5] of SPEC.md. Read AGENTS.md, docs/members/member-B.md,
> SPEC.md sections [5, 7 and 11], docs/plan.md and the [CALC-P] rows of docs/acceptance.md. Use the branch
> [b/S5-past-checks] from the latest main. Plan this slice only, name the files you will touch and the tests you
> will write first, and wait for my go-ahead. I will give you the expected values. Do not change files outside my
> folders.

Sections per slice: S5 → §5, §7 (past performance), §11; S6 → §5, §7 (financial health), §11; S4 → §4, §9.1, §11
and `docs/benchmarks.md`; S12 → §9, §11.

**How to sign off (S0c):** recalculate your rows on paper or in Excel, then post a review comment on
[PR #5](https://github.com/BossToGo/filing-scorecard/pull/5): the rows, the date, how you calculated, and any
difference. A records it under `sign_off` in `app/tests/fixtures/synthetic_co.yaml`, with a link to your
comment. Until then the fixture refuses your rows with the error `NotSignedOff`, naming you.

## Rules for your area

- **Real data:** the saved SEC files in `app/evidence/demo/<TICKER>/companyfacts.json` (PR #6: KO, AAPL, NVDA,
  MCD, AMZN; JPM must be refused). Read `app/evidence/demo/README.md` first: what the files contain and the
  traits already confirmed. Never download anything in your code or tests.
- Use the line-item names in `LINE_ITEMS` and the units in `UNITS` from `app/src/contracts.py` (e.g.
  `net_income`; amounts stay in USD as filed, never millions).
- "Not assessed" (P4 and P5 until S4) is the status `insufficient_data` with the reason in the explanation
  (decision Q9 in `docs/plan.md`).
- Appendix A values for your tests come from `synthetic.expected_check("P3")` in
  `app/tests/fixtures/synthetic.py`. It refuses a row until your sign-off is recorded (rule 14.5).
- Checks are pure functions: `CompanyData` (plus benchmarks and settings) in, `CheckResult` out (SPEC §11). Use
  the shapes in `app/src/contracts.py`; if you need a change there, ask A.
- A missing input gives "insufficient data", never a guess. Equity ≤ 0 fails P4 and H3 with the note "negative
  equity" (SPEC §7).
- The app reads only your CSV files, never Damodaran's `.xls` (SPEC §4). The full `indname.xls` is never committed.
- For each benchmark, write the column you chose and why in the `benchmarks` section of `app/settings.yaml`.

## Only you

1. **Expected values:** your own hand working for every check (Appendix A rows first, then edge cases).
2. **Benchmark check:** compare three benchmark values and three company-to-group matches with the source files
   yourself (S4).
3. **Reconciliation (S15), Apple:** revenue, operating income, net income, total assets, operating cash flow,
   dividends paid, read by hand from the latest 10-K with page and accession number. Not by the assistant.
4. **Decide** Q3 (H4 when equity is negative) and Q1 (missing versus nil, with Flo and Igor; Amazon has no dividend tag at all (confirmed in the saved SEC files)): see `docs/plan.md`.
5. **Explain-back** on each PR; at least two reviews a week, Flo's (C) first.
6. **Before the presentation:** five likely questions and answers on your area to E (Sun 29); walk-through (Mon 30).

## If you are blocked

- No data layer yet? Work on the synthetic company fixture (`app/tests/fixtures/`, from S0c). Your checks need
  nothing else.
- Damodaran's file differs from the SPEC: write what it really contains in `docs/benchmarks.md` and follow the
  fallback in SPEC §9.1 (risk R3).
