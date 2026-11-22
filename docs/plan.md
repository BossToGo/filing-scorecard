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
| S0.3 | Walking skeleton: pinned requirements, `app/main.py` shows one page, one passing test, layering test, `app/.env.example`, `app/settings.yaml` (one section per owner), `app/src/contracts.py` (§11), `.github/workflows/tests.yml`, pull request template, `CODEOWNERS`, `docs/team.md`, team rules in `AGENTS.md`; SPEC §11–12 amended for the `app/` layout (separate pull request) | A | S0.2 | Tests pass locally and in the workflow; the app starts and the first page loads | V1 (partly) | in progress |
| S0.4 | Branch protection on `main` (1 approval, test check required, no bypassing) and one `docs/team.md` pull request per member | A, then everyone | S0.3 | Five merged team pull requests; red-then-green demonstration recorded in the progress log | – | todo |
| S0b | Sample data on day one: saved company facts and submissions for the five demo companies in `app/evidence/demo/` | A | S0.3 | Files load in a test with the network off | AC7 (partly) | done (2026-11-20, PR #6, merge 787a9d9) |
| S0c | Synthetic company of SPEC Appendix A (version 2.3) as `app/tests/fixtures/synthetic_co.yaml`, loader `app/tests/fixtures/synthetic.py`; each owner recalculates their rows by hand and posts the result as a review comment on the S0c pull request; A records it in the file (B: P and H rows and the statements; C: D, V, W, F rows; D: AC3; E: CALC-S) | All, collected by A | S0.3 | Merged with five sign-offs in the pull request; CALC rows in `docs/acceptance.md` marked signed off | CALC-*, AC3 | in progress: fixture on version 2.3; C, D and E signed off and recorded; B's sign-off missing (his rows stay locked); pull request #5 open |

### Tier 1: release v0.1 "Filing scorecard" (target Sun 22 November)

| # | Slice | Owner | Depends on | Done when (evidence) | Acceptance | Status |
|---|---|---|---|---|---|---|
| S1 | SEC client and cache: ticker lookup, submissions, company facts, declared User-Agent, ≤ 5 requests per second, three retries | A | S0 | Tests run without network on saved files; a real download works from A's laptop | E4 (client part) | in progress: client done, reviewed and tested; pull request open |
| S2 | Line-item resolver with sources (§5, §6) | A | S1, S0b | Tests for every rule in §5.3 and every planted mistake in §5.4 | E5–E8, PE1–PE6 | in progress: resolver done, reviewed and tested; pull request open |
| S3 | Coverage report over about 100 non-financial companies from at least 8 industries → `docs/coverage.md`; the 30 companies of the verified universe → `app/data/universe.csv` | A | S2 | Table exists; go/no-go decided at office hours Fri 20 (§13.4) | E16 | in progress: report and universe done, pull request open; go/no-go at office hours |
| S5 | Past performance checks P1–P6 (P4, P5 "not assessed" until S4) | B | S0c | Appendix A values reproduced; edge cases tested | AC3, CALC-P* | todo |
| S6 | Financial health checks H1–H6 | B | S0c | Same | AC3, AC6, CALC-H*, E9, E12 | todo |
| S7 | Dividend checks D1–D6 (D2 "not assessed" until S4 and a share price) | C | S0c | Same | AC3, CALC-D*, E10, E11 | in progress: D1–D6 built and tested (edge cases from Flo's hand working, Coca-Cola against Igor's hand reading); Appendix A tests wait for #5, Amazon for #21 |
| S10 | Interface: input bar, header, score chart, expandable checks, sources page, overrides | D | S0c, then S2 | `streamlit run` works; app test opens the synthetic company and finds a known score | AC1, AC3–AC6, V1, V3, V4 | todo |
| S11 | Gates (§10) and error messages | D | S2 | One test per stop and warn case | AC2, E1–E4, E15, V2 | todo |
| S14 | Demo mode on the five saved companies | A with D | S2, S10 | App runs with the network switched off | AC7 | todo |
| S15 | Reconciliation: six figures (revenue, operating income, net income, total assets, operating cash flow, dividends paid) per member for one demo company, read from the 10-K with page and accession number | All, coordinated by E | S2 | 30 figures match the resolver within USD 0.5 million | – | in progress (KO done: 6 of 30) |
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
| 2026-11-18 | S3 | Coverage report `docs/coverage.md` and verified universe `app/data/universe.csv` (30 companies, 12 industries) from the first 100 non-financial 10-K filers of the SEC list (no hand-picking; 64 skipped with reasons); `app/src/data/coverage.py` (rates, §13.4 decision, verification, choice of 30), `app/scripts/coverage.py`; tag map extended from the evidence (equity from total equity for 9 companies, cash including restricted cash for 7, InterestAndDebtExpense for 3; fallbacks of another definition noted, not warned) | Tests first: 345 passed; first run 14 verified, after the evidence-based tag changes 36; a reviewer agent then found two figures that were too optimistic (Linde's interest net of interest income; equity derived where minority interests exist untagged, GE Vernova), fixed with tests first: 33 verified, universe of 30 in 13 industries (Amazon and Tesla only if Q1 is accepted); result by the §13.4 rule: change scope (operating income 83% < 90%); with the labelled pre-tax income + interest derivation: 97%, go as planned | Q13 for the group at office hours |
| 2026-11-18 | S2 | Resolver `app/src/data/resolver.py`, tag map `app/src/data/tag_map.yaml`, entry point `app/src/data/company.py` (`load_company(ticker, demo=...)`), `CompanyData.latest()` for shares; Q11 tag gaps resolved from the real files; McDonald's debt and depreciation checked in its 10-Ks and written as cited overrides | Tests first: one per §5.3 rule and §5.4 planted mistake, plus cited known answers (session 5 slides 29, 30, 33; McDonald's 10-Ks); two reviewer agents found a blocker in the first debt rule (McDonald's FY2023 37,501 instead of 39,345) and about 15 other problems, all fixed with tests first; eight planted bugs each caught; pytest: 286 passed | Finance leases in debt (Q5) and the share-count source (Q12) for the group |
| 2026-11-18 | S1 | SEC client `app/src/data/sec_client.py` (ticker lookup, submissions, company facts; declared User-Agent never stored or shown; one rate limiter for the whole app, 5 per second from `settings.yaml`; retries 1, 2, 4 s; atomic cache checked by SHA-256; clear error types for S2) and settings loader `app/src/settings.py`; download script now uses the client | Tests first on the saved files with a fake connection and clock; two reviewer agents (code, tests) found 3 major and about 10 minor problems, all fixed with tests first; three planted bugs each caught; pytest: 207 passed; live check from A's laptop: MSFT ticker lookup and submissions downloaded, then read from the cache | S2 must turn `SourceUnreachable` into a `missing` figure (E4) |
| 2026-11-18 | S0b | Real SEC data for KO, AAPL, NVDA, MCD, AMZN (submissions, company facts) and JPM (submissions) downloaded with A's declared User-Agent (12 requests, ≤ 4 per second), trimmed to annual reports, saved in `app/evidence/demo/` with provenance; script `app/scripts/fetch_demo_data.py`, trimming rules `app/src/data/evidence.py` | Trimming tests written first and seen failing; checksum expected value computed with `shasum`, not Python; offline tests on the saved files: 35 passed (network blocked); known answer KO FY2025 revenue = session 5 slide 30; no file contains A's name or e-mail; pytest: 147 passed | Tag gaps found (Q11): KO debt after 2023, NVDA and AMZN capex, AAPL interest after 2023 |
| 2026-11-18 | S0c | Synthetic company fixture on branch `a/S0c-synthetic-fixture`: every input and expected value of SPEC Appendix A in `synthetic_co.yaml`; `synthetic.py` turns it into `CompanyData` (amounts in USD) and hands out an expected value only after its owner has signed off (rule 14.5) | Cross-check tests compare every cell with the tables in `SPEC.md` itself; five planted copying errors (a revenue figure, swapped digits, a flipped result, a forecast cell, the tax rate) each made a test fail; pytest: 136 passed | B, C, D and E must recalculate and sign off before S5 to S10 use the values |
| 2026-11-18 | S0.3 review | Three read-only reviewer agents (code, tests, security): no blocker, about 20 findings. Fixed: `CompanyData` picklable for Streamlit's cache; numpy numbers accepted; reported facts need tag, form, accession and a filed unit (no "USD m"); a check with a missing input cannot pass or fail; network guard switched on for the whole session, also records swallowed attempts; layering test reads full module names, relative and dynamic imports, and covers the interface; workflow runs on `main` never cancelled, `setup-python@v6`, no stored token, bash on Windows; `.gitignore` patterns inside `app/`; `CODEOWNERS` lines for the guardrail files; Python range stated as 3.11 to 3.14 | pytest: 100 passed; planted bypasses caught (guard switched off: 8 failed; a swallowed network error fails the test) | Skipped, with reason: pinning actions to commit hashes and a hashed lock file (more complexity for the team than the risk of a student repository with no secrets); subprocess network calls (no code uses them) |
| 2026-11-18 | S0.3 | Walking skeleton on branch `a/S0-skeleton`: shared data shapes with built-in rules, network guard for tests, layering test, `settings.yaml` with SPEC starting values, first page, CI on Linux and Windows, pull request template, `CODEOWNERS`, `docs/team.md`, team rules in `AGENTS.md` | Tests written first and seen failing (7 failed, 1 error); then pytest: 51 passed locally (Python 3.14.6, macOS); environment rebuilt from `requirements.txt` alone: 51 passed, `pip check` clean | CI result on GitHub: see the pull request |
| 2026-11-19 | S3 follow-up | Valuation inputs: depreciation and amortisation falls back to Depreciation + AmortizationOfIntangibleAssets (derived; missing if the amortisation is reported in another year but not this one); current debt from DebtCurrent when only a long-term total is reported, with the principal (DebtInstrumentCarryingAmount) deciding whether that total includes it, else DEBT_CHECK; current debt above total debt is a DEBT_CHECK; the verified universe now also needs the latest year's depreciation, current debt and share count (SPEC v2.3 §8.6, §13.4 in PR #10). **Bug found by the review and fixed:** Tesla's LongTermDebt is only its non-current debt, so its total debt was 19% too low (6,584 instead of 8,153, USD m) | Tests written first and seen failing (7, then 8 after the review); pytest: 369 passed; a read-only code review (1 blocker, 2 major, 8 minor: all fixed except the optional non-current + DebtCurrent completion); coverage report regenerated from the cache: depreciation FY0 73% → 94%; 31 verified (was 33): Tesla and Texas Instruments out (amortisation reported in an earlier year, none for the latest), Starbucks and CVS in; 13 industries; the demo candidates KO, NVDA, MCD, AMZN, COST, PEP all verified | Group: complete non-current-only debt with DebtCurrent (would verify more companies); derived depreciation can be below the cash flow line (labelled) |
| 2026-11-19 | S3 second-source audit | Each figure of the 30 verified companies compared with an independent route in the same filings (727 comparisons: balance-sheet total, EPS × shares, cash-flow sum, gross profit, pre-tax − tax, debt against face value and maturity schedule, interest paid, dividends per share, cover page against average shares). **Three bugs found and fixed:** Mastercard's (and Visa's) share count came from a 2009/2010 cover page (110 million instead of 906 million, about 8 times too few): a cover page now counts only within 200 days after the fiscal year end, else the diluted average with AVERAGE_SHARES, and fewer than 100,000 shares is missing; Marvell's short-term borrowings were its current maturities counted twice (debt 4,970 instead of 4,471, USD m); Walmart's and Thermo Fisher's calculated liabilities included temporary equity (about 0.2%) | Tests written first and seen failing (4); pytest: 374 passed; audit after the fixes: 29 differences left, each explained (face value against balance-sheet value, capitalised interest, share issuance, dividend timing, company definitions, McDonald's averages filed in millions, held-for-sale cash); universe unchanged (31 verified, 30 chosen) | Group, plan Q5: interest includes finance-lease interest while debt excludes finance leases (Microsoft); Altria's revenue includes excise taxes, Philip Morris's does not (P5) |
| 2026-11-20 | S3 (lean v2.3) | The verified universe no longer needs current financial debt (equity method); it still needs the share count and the latest depreciation (for V4) | Test first (seen failing); pytest: 373 passed; coverage regenerated: still 31 verified, the same 30 chosen | – |
| 2026-11-20 | S3 (lean v2.3 round 2) | The verified universe no longer needs depreciation (V4 now compares the P/E with the whole market): only tier 1 figures, the accounting checks, no blocking warning, a recent report and a share count | Test first (seen failing); pytest: 372 passed; coverage regenerated: 33 verified; Tesla and Texas Instruments back in the 30, Starbucks and CVS out; the demo candidates (KO, NVDA, MCD, AMZN, COST, PEP) all in | – |
| 2026-11-20 | S2 | Simon's review of #7: the interface imports `load_company` and the SEC error classes from `src.data.company` only, never `src.data.sec_client`; the errors are re-exported there and a layering test forbids the direct import | Tests first (8 failed), then pytest: 298 passed | – |
| 2026-11-21 | S15 | Reconciliation format (`app/tests/reconciliation/README.md`, the S2 leftover) and its test: every `<TICKER>.yaml` is checked for completeness and compared with the app within USD 0.5 million and against the same accession number; Igor's Coca-Cola record added | Tests first: with no record, with the validator switched off (12 failed) and with a wrong revenue (47,900: failed); then 6 of 6 Coca-Cola figures match exactly; pytest: see the pull request | B, C, D and E add their files (Apple, Nvidia, McDonald's, Amazon) |
| 2026-11-22 | S0c | Fixture rewritten for SPEC v2.3 (lean): valuation rows of the equity method (fair value 20.13; 37.37 at the growth cap; ten-year forecast), V4 against the market P/E, valuation score 3, the 15 strengths and points to watch with their overview, the v2.3 settings and benchmarks; the cash override of v2.2 removed (AC6 is no longer a calculation); cost of equity stored as 9.03325% so that it is not on the tolerance edge (audit). Sign-offs for the v2.3 values recorded with their links: C (Flo, 21 November), D (Simon, AC3), E (Emma, 21 November) | The v2.2 fixture failed 9 tests against the v2.3 Appendix A (seen failing); 13 copying errors planted one at a time, each caught; pytest: 455 passed. The Appendix A values were recomputed independently three times (A's script, a reviewer agent on 21 November, C's Excel model) | B's sign-off for the P and H rows and the statements; the group decides whether #5 merges with B's rows still locked |
| 2026-11-22 | S0 | **SPEC v2.4, MVP scope (Igor):** the product is one workflow that works end to end for the five demo companies (pick a company, type the price, scorecard, check, filing); other tickers stay possible but outside the MVP, with their known problems as README limitations; benchmarks as a small cited table for the five companies' industries (S4 shrinks); plan Q1 (no dividend line: nil only without any dividend evidence) and Q13 (go with the five; Apple kept; operating income not derived) decided; new dates: v0.1 Tuesday 24, v0.2 with the feature freeze Thursday 26 at 20:00; strengths, points to watch and the export only if v0.2 is released before the freeze | Data of the five demo companies checked on 22 November: Coca-Cola, Nvidia and McDonald's complete; Apple without interest expense after fiscal 2023; Amazon without dividends. No code changed; pytest: see the pull request | The group approves the pull request; `docs/plan.md` slice dates, the member guides and `docs/product.md` follow in PR #4; A builds the Q1 rule (PR #18's pending test then passes) |
| 2026-11-21 | S8 (Excel model) | C's separate Excel cross-check model `docs/crosscheck/valuation-crosscheck.xlsx`, built by Flo from the SPEC v2.3 formulas (equity method, version of 20 November), not from the code: inputs from Appendix A, cost of equity, three-year free cash flow margin, growth limit and decay, ten-year forecast, terminal value, a second sheet with g1 at the 30% cap, and the sign-off rows CALC-D1–D6, CALC-V1–V6, CALC-W1–W2, CALC-F1–F4 | Fair value USD 20.13 and USD 37.37 at the growth cap; every row agrees with `docs/acceptance.md` (Appendix A v2.3) | Sign-off comment on #5 by C; S8 code not started |
| 2026-11-22 | S7 | Dividend checks D1–D6 in `app/src/checks/dividend.py` (pure function `dividend_checks(data, settings)`): D1 fails on a labelled nil (plan Q1) or a reported zero, with "no dividend paid" and D2–D6 not applicable; a missing FY0 gives insufficient data, never "no dividend paid"; D2 not assessed until S9; thresholds from `settings.yaml`. Decisions by Flo: D3 counts a cut as "this year < 90% × last year" (no division: a rise from zero is never a cut; the value is the lowest change from a year above zero); a fiscal year not in the data is a missing input; D5 with net income ≤ 0 fails with the reason and no ratio | Tests first, seen failing (module missing): 21 unit tests on small test companies with Flo's hand-worked expected values (re-checked by hand by Claude: all agree) and Coca-Cola's D1 against Igor's hand reading (USD 8,779 million, accession 0001628280-26-010047); six planted bugs each caught by a test; pytest: 428 passed. Run on the five demo companies: Coca-Cola fails D6 (dividends 8,779 above operating cash flow − capex 5,296, USD m, both as in `KO.yaml`); Amazon insufficient data until #21 | Appendix A tests (D1, D3–D6, D2 not assessed) wait for #5; Amazon's "no dividend paid" on real data waits for #21. For Flo: a negative dividend (sign error, `SIGN` warning) fails D1 under the literal rule and would show "no dividend paid"; D3 when no earlier year is above zero has no test yet |
| 2026-11-22 | S7 (edge cases) | Both open points decided by Flo: a negative dividends paid figure (a sign error, SPEC §5.4, kept as filed by the data layer with a `SIGN` warning) is never flipped (§5.2: never guessed); every check that uses that year is insufficient data, naming the sign. D3 passes with no value when no step starts from a year above zero (0, 0, 0, 0, 5) | Checked first: SPEC §5.2, §5.4 and the resolver's tested rule (kept as filed, flagged); none of the 225 dividend-payment entries in the saved files of the five demo companies is negative. Tests first with Flo's hand results (negative FY0: all six insufficient data; negative FY-2: only D3); two failed as expected, then passed; eight planted bugs each caught; pytest: 431 passed; the demo companies' results unchanged | Appendix A tests wait for #5; Amazon for #21; PE5 in `docs/acceptance.md` (A's row) could also name the two dividend sign tests |

## Known problems and open questions

Raised during the product interview on 2026-11-18. Each one is decided by the group and, if it changes the SPEC,
fixed by a pull request to `SPEC.md`.

- **Q1. Missing versus nil for dividends and debt** (§5.2 against §7, §8.3). A company that never paid a dividend
  may have no dividend tag at all; under §5.2 that is `missing`, so D1 shows "insufficient data" instead of "no
  dividend paid" (Amazon, a demo company). A company with no debt may have no debt tags, so H4–H6 "no debt: pass"
  never triggers and the valuation is blocked. Proposal: extend the §8.3 rule ("not reported, treated as nil",
  labelled and listed on the sources page) to dividends paid and to debt, when the rest of that year's statement
  resolves. Decide by: B and C with A, before S6 and S7. **Decided in SPEC v2.4 §7 (22 November), for the
  group's approval:** nil only when no dividend appears under any dividend tag in any of the five years and none is
  declared per share (Amazon); otherwise `missing`. The debt half stays open (not needed for the five demo companies).
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
- **Q5. Debt tags may double count** (§6). Decided by A in S2 (2026-11-18), rule in `app/src/data/tag_map.yaml`:
  the reported total long-term debt is used when there is one; short-term borrowings are `ShortTermBorrowings`,
  else commercial paper + other short-term borrowings; a cited company override says when they sit inside long-term
  debt (McDonald's, from its 10-Ks); no long-term debt tag means debt is missing. Still open for the group: Coca-Cola's
  tags from 2024 include finance leases, other companies' finance leases (Amazon 12,286 million) are not counted.
- **Q6. Terminal growth barely moves the sensitivity grid** (§8.5). With return on new capital equal to the cost of
  capital, terminal value = operating profit after tax × (1 + gT) ÷ cost of capital, so ±1 point of gT moves the
  synthetic fair value only from USD 21.50 to 21.86, against 18.81 to 25.32 for ±1 point of cost of capital. Not a
  bug: session 5 slide 33 says the same. Prepare the explanation for questions. Owner: C.
- **Q7. Team letters and names.** A is Igor. Members B to E and their GitHub accounts: [to confirm at the group
  meeting]; `Greg3334444` and `florian-spitzer` invited. Product name (§16.7): [to confirm].
- **Q8. Overlap with the session 5 demo** (§16.3): [to confirm with the instructor].
- **Q11. Tag gaps in the real filings** (found in S0b, details in `app/evidence/demo/README.md`). With the SPEC §6
  tags: Coca-Cola's debt is missing for FY2024–FY2025 (its debt tags stop at 2023), so the course's own running
  example could not be valued; Nvidia's and Amazon's capital expenditure tag stops in 2012 and 2016; Apple's
  interest expense stops after FY2023; Apple's `Revenues` stops in 2018, so fallbacks must be tried per fiscal
  year. Resolved in S2: the KO debt and NVDA/AMZN capex tags are in the tag map, fallbacks run per fiscal year,
  Apple's interest expense is honestly missing (H6 "insufficient data"), and McDonald's depreciation uses a cited
  override (its 10-K's cash flow total, 2,199 million, not the SG&A part, 457). S3 measures coverage on about 100
  companies. Q1 is confirmed: Amazon has no dividend tag at all.
- **Q12. Share count source** (SPEC §6 "latest filing"). Decided by A for now: the cover page of the latest annual
  report, as SPEC §5.3.1 allows only 10-K figures; a later 10-Q cover count would be more recent. Shares are stored
  at the cover-page date: use `data.latest("shares")`. The group can change this by a pull request to SPEC §6.
- **Q13. Go/no-go at office hours, Fri 20 November** (`docs/coverage.md`). By the SPEC §13.4 rule the result is
  "change scope": operating income resolves for 83% of the 100 companies (needs 90%), because 16 large
  companies (pharma, oil, GE, IBM, Deere...) have no operating-income line. Option: allow operating income =
  pre-tax income + interest expense for them, labelled `derived` → 97%, "go as planned". It changes what P5,
  P6, H6 and V4 measure, so the group decides. Also: Apple is not verified (no interest expense after FY2023);
  keep it as a demo of "insufficient data" or swap it for a verified 53-week company (Costco, PepsiCo, Intel...).
  Decide by: group, with the instructor. **Decided in SPEC v2.4 §13.4 (22 November), for the group's approval:**
  the MVP is the five demo companies; operating income is not derived; Apple stays, as the "insufficient data"
  example.
- **Q9. "Not assessed" (SPEC §2) has no status of its own in SPEC §11.** Decided by A for now: such a check has the
  status `insufficient_data` with an explanation ("not assessed: needs an industry benchmark", tier 1), which the
  display rule of §3 already counts as not assessed ("4 of 5 assessed, 1 with insufficient data"). Documented in
  `app/src/contracts.py`. The group can change it by a pull request to SPEC §11 before S5 and S7.
- **Q10. Repository settings for S0.4 (Igor to approve each).** Protect `main`: pull request required, 1 approval,
  dismiss stale approvals, approval of the most recent push, required check `test` (from GitHub Actions), no
  bypassing; "require review from code owners" once member D, A's backup, is co-owner of the guardrail files
  (A cannot approve his own pull requests). Also: secret scanning with push protection (free on public
  repositories) and approval before workflows run for outside contributors. Igor's commits so far show his
  personal e-mail address (public repository, history never rewritten); he may switch to his GitHub noreply
  address for future commits.
