# Implementation plan

Source: `SPEC.md` §13 (slices, owners, timeline) and §2 (tiers, cut list). One slice at a time, one branch per
slice named `<member>/<slice-id>-<short-name>` (e.g. `b/S5-past-checks`), one pull request reviewed by a teammate
(first reviewer: the backup, §12). A tier starts only when the previous one is released, except S4 and S8, which
the SPEC timetable starts on Thursday 19 (see open question Q2). After every slice: update the status and the
progress log below, and append to `AI-USAGE.md`.

**Release check (§13.1, run by A or the backup D):** all tests green in the workflow; the app starts in demo mode
with the network off; the five demo companies open without an error; the README run commands still work. Then tag
`main` (`v0.1`, `v0.2`, `v0.3`) and record the date here.

## Slices

Status values: `todo`, `in progress`, `done (<date>, commit <short hash>)`, `blocked: <reason>`.

### Tier 0: foundation (Wed 18 – Thu 19 November)

| # | Slice | Owner | Depends on | Done when (evidence) | Acceptance | Status |
|---|---|---|---|---|---|---|
| S0 | Repository bootstrap, in four steps below | A, agreed by all | – | Five merged pull requests from five accounts (each adds a line to `docs/team.md`); a deliberately failing test turns the check red, then green | – | in progress |
| S0.1 | Repository created from the starter, `SPEC.md` v2 added, teammates invited | A | – | Public repo on GitHub; commit linked to A's account | – | done (2026-11-18, commit 149180c) |
| S0.2 | Product documents: product, architecture, acceptance, plan (this file) | A | S0.1 | Pull request reviewed by a teammate | – | in progress |
| S0.3 | Walking skeleton: pinned requirements, `app/main.py` shows one page, one passing test, layering test, `app/.env.example`, `app/settings.yaml` (one section per owner), `app/src/contracts.py` (§11), `.github/workflows/tests.yml`, pull request template, `docs/team.md`; SPEC §11–12 amended for the `app/` layout | A | S0.2 | Tests pass locally and in the workflow; the app starts and the first page loads | V1 (partly) | todo |
| S0.4 | Branch protection on `main` (1 approval, test check required, no bypassing) and one `docs/team.md` pull request per member | A, then everyone | S0.3 | Five merged team pull requests; red-then-green demonstration recorded in the progress log | – | todo |
| S0b | Sample data on day one: saved company facts and submissions for the five demo companies in `app/evidence/demo/` | A | S0.3 | Files load in a test with the network off | AC7 (partly) | todo |
| S0c | Synthetic company of SPEC Appendix A as `app/tests/fixtures/synthetic_co.yaml`; each owner recalculates their rows by hand | All, collected by A | S0.3 | Merged with five sign-offs in the pull request; CALC rows in `docs/acceptance.md` marked signed off | CALC-* | todo |

### Tier 1: release v0.1 "Filing scorecard" (target Sun 22 November)

| # | Slice | Owner | Depends on | Done when (evidence) | Acceptance | Status |
|---|---|---|---|---|---|---|
| S1 | SEC client and cache: ticker lookup, submissions, company facts, declared User-Agent, ≤ 5 requests per second, three retries | A | S0 | Tests run without network on saved files; a real download works from A's laptop | E4 | todo |
| S2 | Line-item resolver with sources (§5, §6) | A | S1, S0b | Tests for every rule in §5.3 and every planted mistake in §5.4 | E5–E8, PE1–PE6 | todo |
| S3 | Coverage report over about 100 non-financial companies from at least 8 industries → `docs/coverage.md`; the 30 companies of the verified universe → `app/data/universe.csv` | A | S2 | Table exists; go/no-go decided at office hours Fri 20 (§13.4) | E16 | todo |
| S5 | Past performance checks P1–P6 (P4, P5 "not assessed" until S4) | B | S0c | Appendix A values reproduced; edge cases tested | AC3, CALC-P* | todo |
| S6 | Financial health checks H1–H6 | B | S0c | Same | AC3, AC6, CALC-H*, E9, E12 | todo |
| S7 | Dividend checks D1–D6 (D2 "not assessed" until S4 and a share price) | C | S0c | Same | AC3, CALC-D*, E10, E11 | todo |
| S10 | Interface: input bar, header, score chart, expandable checks, sources page, overrides | D | S0c, then S2 | `streamlit run` works; app test opens the synthetic company and finds a known score | AC1, AC3–AC6, V1, V3, V4 | todo |
| S11 | Gates (§10) and error messages | D | S2 | One test per stop and warn case | AC2, E1–E3, E15, V2 | todo |
| S14 | Demo mode on the five saved companies | A with D | S2, S10 | App runs with the network switched off | AC7 | todo |
| S15 | Reconciliation: six figures (revenue, operating income, net income, total assets, operating cash flow, dividends paid) per member for one demo company, read from the 10-K with page and accession number | All, coordinated by E | S2 | 30 figures match the resolver within USD 0.5 million | – | todo |
| S16a | Plain-language texts for the 18 tier 1 checks | E | S10 | Each check shows its text; reviewed by the check's owner | AC4 | todo |

### Tier 2: release v0.2 "Valuation" (target Wed 25 November)

| # | Slice | Owner | Depends on | Done when (evidence) | Acceptance | Status |
|---|---|---|---|---|---|---|
| S4 | Extraction script, benchmark CSV, industry lookup and fallback table (§4, §9.1); starts Thu 19 with the day-one look at `indname.xls`, in parallel with S5 | B | S0 | Loader tests; three benchmark values and three company-to-group matches compared by hand with the source files | AC8, E17 | todo |
| S8 | Cost of capital, forecast, terminal value, reverse calculation, sensitivity; starts Thu 19 on the synthetic company, with C's Excel model | C | S0c | Matches C's separate Excel model and Appendix A; property tests pass | CALC-W*, CALC-F*, E12–E14 | todo |
| S9 | Valuation checks V1–V6; switch on P4, P5, D2 | C with B | S8, S4 | Appendix A values reproduced | AC8, AC9, CALC-V*, CALC-S | todo |
| S10b | Interface: share price input, valuation detail, industry with route and number of firms, override dropdown | D | S8, S4 | App test finds the fair value of the synthetic company | AC9, AC10 | todo |
| S13 | Excel export | D | S10 | Export reopened by a test; figures equal the screen | AC11 | todo |
| S16b | Texts for the valuation checks and the industry explanations | E | S10b | Reviewed by C | – | todo |

### Tier 3: release v0.3 "Five forces" (feature freeze Thu 26 November, 20:00)

| # | Slice | Owner | Depends on | Done when (evidence) | Acceptance | Status |
|---|---|---|---|---|---|---|
| S12 | Five forces panel (§9) | D with B | S4 | Indicator tests; override survives recalculation | AC12 | todo |
| S17 | End-to-end app test: demo ticker, a known score, a known figure, a known fair value | D | S14 | Passes twice in a row in the workflow | AC1, V1 | todo |

### After the freeze: fixes only (Fri 27 November – Tue 1 December)

| # | Slice | Owner | Depends on | Done when (evidence) | Status |
|---|---|---|---|---|---|
| S18 | Break-it round: independent read-only review of each area; a deliberate break of every formula | Each owner; reviewer from another area | v0.2 | `docs/testing.md` lists each break and the test that caught it; every finding is a failing test or a written dismissal | todo |
| S19 | README and fresh-clone test on one Windows and one Mac laptop, by a member who did not write the README | E writes, two members test | v0.3 | Works from the README alone on both | todo |
| S20 | Business plan (Markdown → PDF), slides, recorded fallback demo, question bank | E leads, all contribute (from Sat 21) | – | Files on `main` before the deadline | todo |

Cut list if a release slips by more than a day (§2): watchlist → five forces panel → sensitivity table → Excel
export. The tier 1 scorecard and the sources page are never cut. Everything on `main` by Tue 1 December, 12:00.

## Progress log

| Date | Slice | What changed | Checks run and results | Open problems |
|---|---|---|---|---|
| 2026-11-18 | S0.1 | Public repo `BossToGo/filing-scorecard` created; starter 0.3.0 and `SPEC.md` v2 committed to `main` (149180c); `Greg3334444` and `florian-spitzer` invited with write access | Commit linked to A's GitHub account; SPEC structure checked (21 sections, 24 checks, 25 slices); starter scanned for secrets: none | Two members not yet known; invitations expire after 7 days |
| 2026-11-18 | S0.2 | Product interview run from `SPEC.md`, asking only §16; four documents drafted on branch `a/S0-product-docs` | SPEC Appendix A recomputed by an independent script: all values agree within rounding | Q1–Q8 below |

## Known problems and open questions

Raised during the product interview on 2026-11-18. Each one is decided by the group and, if it changes the SPEC,
fixed by a pull request to `SPEC.md`.

- **Q1. Missing versus nil for dividends and debt** (§5.2 against §7, §8.3). A company that never paid a dividend
  may have no dividend tag at all; under §5.2 that is `missing`, so D1 shows "insufficient data" instead of "no
  dividend paid" (Amazon, a demo company). A company with no debt may have no debt tags, so H4–H6 "no debt: pass"
  never triggers and the valuation is blocked. Proposal: extend the §8.3 rule ("not reported, treated as nil",
  labelled and listed on the sources page) to dividends paid and to debt, when the rest of that year's statement
  resolves. Decide by: B and C with A, before S6 and S7.
- **Q2. Tier rule against the timetable.** §0.6, §2 and §13.3 say a tier never starts before the previous release,
  but §13.2 starts S4 (B) and S8 (C) on Thursday 19. An assistant following §0.6 would refuse that work. Proposal:
  state the exception for S4 and S8 in §0.6. Decide by: group.
- **Q3. H4 with negative equity** (§7). H3, P4 and V5 say "equity ≤ 0: fail"; H4 says nothing, and McDonald's, a
  demo company, is expected to have negative equity. Decide by: B.
- **Q4. Reverse DCF for loss-making companies** (§8.4, §15). "Fair value rises with g" holds only when margins are
  positive: with a −5% operating margin, the synthetic company's fair value falls from −5.62 at g = −20% to −50.63
  at g = +50% (USD per share). Proposal: the bisection checks the sign at both ends and does not assume a direction;
  the property test applies only to positive margins; the app says "not meaningful" when the margin is zero or
  negative. Decide by: C.
- **Q5. Debt tags may double count** (§6). `CommercialPaper` is often part of `ShortTermBorrowings`; `DebtCurrent`
  is not in the list. Written from memory: check on real files in S2 and S3. Decide by: A.
- **Q6. Terminal growth barely moves the sensitivity grid** (§8.5). With return on new capital equal to the cost of
  capital, terminal value = operating profit after tax × (1 + gT) ÷ cost of capital, so ±1 point of gT moves the
  synthetic fair value only from USD 21.50 to 21.86, against 18.81 to 25.32 for ±1 point of cost of capital. Not a
  bug: session 5 slide 33 says the same. Prepare the explanation for questions. Owner: C.
- **Q7. Team letters and names.** A is Igor. Members B to E and their GitHub accounts: [to confirm at the group
  meeting]; `Greg3334444` and `florian-spitzer` invited. Product name (§16.7): [to confirm].
- **Q8. Overlap with the session 5 demo** (§16.3): [to confirm with the instructor].
