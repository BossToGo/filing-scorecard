# Member B: Greg (@Greg3334444)

**You own:** `app/src/benchmarks/`, `app/scripts/extract_benchmarks.py`, `app/scripts/requirements-scripts.txt`, the
industry files in `app/data/` (`benchmarks_us_2026.csv`, `industry_lookup_us_2026.csv`, `sic_to_damodaran.csv`),
`app/src/checks/past.py`, `app/src/checks/health.py`, `app/src/highlights.py` (strengths and points to watch,
SPEC v2.3 §9), `docs/benchmarks.md`, the `benchmarks`, `past_performance`, `financial_health` and `highlights`
sections of `app/settings.yaml`, and your tests.
**Backup:** C, Flo (you review Flo's PRs first, Flo reviews yours). **Reconciliation company:** Apple (AAPL).

## Your slices, in order

**Timeline (SPEC v2.4, 22 November):** the MVP is the five demo companies, one workflow end to end. Release v0.1 on **Tuesday 24** (the screen and the 18 checks), v0.2 with the feature freeze on **Thursday 26 at 20:00** (the fair value). The strengths and points to watch (S12) and the Excel export (S13) are built only if v0.2 is released before the freeze.

| When | Slice | Done when (SPEC §13.2) |
|---|---|---|
| Sun 22 | Your `docs/team.md` PR (#22): write your Explain-back | Merged |
| As soon as possible, before S5 | **Sign-off for S0c:** recalculate rows CALC-P1 to CALC-P6 and CALC-H1 to CALC-H6 of `docs/acceptance.md`, and the "Strengths and points to watch" table of SPEC Appendix A, by hand or in Excel | Your sign-off comment on PR #5 (merged on 22 November; comments still work); A records it in a follow-up PR, which unlocks your rows |
| Sun 22–Tue 24 | S5: past performance checks P1–P6 (P4, P5 "not assessed" until S4), branch `b/S5-past-checks` | SPEC Appendix A values reproduced; edge cases tested |
| Sun 22–Tue 24 | S6: financial health checks H1–H6, branch `b/S6-health-checks` | Same |
| Sun 22–Tue 24 | S15, reconciliation of Apple: six figures read by hand from the latest 10-K ("Only you" below; format in `app/tests/reconciliation/README.md`) | `app/tests/reconciliation/AAPL.yaml` merged; 6 of 6 match |
| Wed 25–Thu 26 | S4, smaller since SPEC v2.4: the benchmark table `app/data/benchmarks_us_2026.csv` for the industry groups of the five demo companies and the whole-market row, each value with its source file, sheet and row; each company's group read from Damodaran's `indname.xls` (write the file's sheet and column names in `docs/benchmarks.md`). The extraction script, the lookup for other tickers and the fallback table are optional, after v0.2. Branch `b/S4-benchmarks` | Loader tests; three benchmark values and the five company-to-group matches re-read from the source files by a second member |
| Wed 25–Thu 26 | S9 with C: switch on P4 and P5 | SPEC Appendix A values reproduced |
| Thu 26, only if v0.2 is released before the freeze | S12: strengths and points to watch in `app/src/highlights.py` (SPEC §9: 15 rules, G1–G7 and W1–W8, threshold `margin_drop_min` in the `highlights` section of `app/settings.yaml`), branch `b/S12-highlights`; Simon (D) shows them, Emma (E) writes the texts | One test per statement (shown, not shown, input missing); the synthetic company's statements match SPEC Appendix A |
| Sat 21–Sun 29 | **Business plan section:** users, market and alternatives, in `docs/business-plan/sections/B-market.md` (Emma, E, assembles the plan; prompt in `docs/members/README.md`) | Draft now (first planned for Sun 22); final by Sun 29 |
| Fri 27–Sun 29 | S18, break-it round: a member from another area reviews your code read-only; you break each of your formulas once on purpose and record each break and the test that caught it in `docs/testing.md` | Every finding is a failing test or a written dismissal |

**Slice prompt** (replace the slice, sections and branch):

> /build-feature I am member B, working on slice [S5] of SPEC.md. Read AGENTS.md, docs/members/member-B.md,
> SPEC.md sections [5, 7 and 11], docs/plan.md and the [CALC-P] rows of docs/acceptance.md. Use the branch
> [b/S5-past-checks] from the latest main. Plan this slice only, name the files you will touch and the tests you
> will write first, and wait for my go-ahead. I will give you the expected values. Do not change files outside my
> folders.

Sections per slice: S5 → §5, §7 (past performance), §11; S6 → §5, §7 (financial health), §11; S4 → §4, §9.1, §11
and `docs/benchmarks.md`; S12 → §7, §9, §11 and SPEC Appendix A ("Strengths and points to watch").

**How to sign off (S0c):** recalculate your rows on paper or in Excel, then post a review comment on
[PR #5](https://github.com/BossToGo/filing-scorecard/pull/5): the rows, the date, how you calculated, and any
difference. A records it under `sign_off` in `app/tests/fixtures/synthetic_co.yaml`, with a link to your
comment. Until then the fixture refuses your rows with the error `NotSignedOff`, naming you.

## Rules for your area

- **Real data:** the saved SEC files in `app/evidence/demo/<TICKER>/companyfacts.json` (PR #6: KO, AAPL, NVDA,
  MCD, AMZN; JPM must be refused). Read `app/evidence/demo/README.md` first: what the files contain and the
  traits already confirmed. Never download anything in your code or tests.
- **Thresholds:** `from src.settings import load_settings`, then `load_settings()["financial_health"]["max_net_debt_to_equity"]` gives 0.40 (PR #7).
  Never hard-code a threshold; a misspelt name raises a `KeyError` naming the section.
- Never import `src.data.sec_client`: only A's data layer talks to the SEC; your code receives `CompanyData`.
- **Loading a company** (PR #8): `from src.data.company import load_company`, then
  `load_company("MCD", demo=True)` gives `CompanyData` from the saved files, with no network (`DEMO_TICKERS`:
  KO, AAPL, NVDA, MCD, AMZN). The latest fiscal year is `data.fiscal_years("revenue")[-1]`. Shares come from
  `data.latest("shares")`, never `data.fact("shares", fy0)`, which is None by design (plan Q12). A `missing`
  figure has value None and its reason in `.note`; a `derived` one has its formula and sources in `.note`.
- **Real cases for your edge-case tests:** Apple's interest expense is missing for FY2024 to FY2026, so H6 is
  "insufficient data"; McDonald's equity is negative (USD −1,791 million at FY2025), so H3 and P4 fail with
  "negative equity".
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
- **S4 since SPEC v2.4:** no script is needed for the five demo companies. Read each value from Damodaran's files
  and write it in the CSV with its source file, sheet and row. For each benchmark, write the column you chose and
  why in the `benchmarks` section of `app/settings.yaml`. S4 also records the **whole-US-market price to earnings** from `pedata.xls` (for V4, SPEC v2.3: trailing or current,
  never forward), from the whole-market row without financial companies, the same column as V3; record the row and
  column in `settings.yaml`. Check the market P/E and the market dividend yield by hand too. `vebitda.xls` is no
  longer needed.
  Never extract a column built from analyst forecasts (for example expected growth in `pedata.xls`, SPEC §4).
- **Strengths and points to watch (S12, SPEC v2.3 §9)** replace the five forces panel: 15 statements, all from
  check results you and Flo already compute (e.g. W5 is "H5 fails") plus one simple indicator (W2, operating
  margin down by at least 1 point against the year before). No new data is needed; Igor (A) only adds the
  `Statement` shape in `app/src/contracts.py` (slice S2b). A statement is shown only when every check it names
  passed or failed and every figure it uses is present; a ratio with a denominator ≤ 0 is not computed. Your
  function returns `Statement` objects only; the wording is Emma's (`app/ui/texts.yaml`), written within S12 and
  reviewed by you.

## Only you

1. **Expected values:** your own hand working for every check (Appendix A rows first, then edge cases).
2. **Benchmark table (S4):** read every value and the five company groups from Damodaran's files yourself; a
   second member re-reads three values and the five groups.
3. **Reconciliation (S15), Apple:** revenue, operating income, net income, total assets, operating cash flow,
   dividends paid, read by hand from the latest 10-K with page and accession number. Not by the assistant.
4. **Recalculate** the "Strengths and points to watch" table of SPEC Appendix A (v2.3) before S12, and post it
   with your S0c sign-off or in the S12 pull request.
5. **Decide** Q3 (H4 when equity is negative; McDonald's is a demo company): see `docs/plan.md`. Q1 is decided
   (SPEC v2.4 §7: Amazon shows "no dividend paid").
6. **Explain-back** on each PR; at least two reviews a week, Flo's (C) first.
7. **Before the presentation:** five likely questions and answers on your area to E (Sun 29); walk-through (Mon 30).

## If you are blocked

- Everything you need is on `main`: the synthetic company fixture (`app/tests/fixtures/`, S0c) for the Appendix A
  values, and `load_company(..., demo=True)` for the five real companies.
- Damodaran's file differs from the SPEC: write what it really contains in `docs/benchmarks.md` and follow the
  fallback in SPEC §9.1 (risk R3).
