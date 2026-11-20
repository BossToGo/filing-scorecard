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
| S0b | Sample data on day one: saved company facts and submissions for the five demo companies in `app/evidence/demo/` | A | S0.3 | Files load in a test with the network off | AC7 (partly) | in progress: data saved and tested; pull request open |
| S0c | Synthetic company of SPEC Appendix A as `app/tests/fixtures/synthetic_co.yaml`; each owner recalculates their rows by hand | All, collected by A | S0.3 | Merged with five sign-offs in the pull request; CALC rows in `docs/acceptance.md` marked signed off | CALC-* | todo |

### Tier 1: release v0.1 "Filing scorecard" (target Sun 22 November)

| # | Slice | Owner | Depends on | Done when (evidence) | Acceptance | Status |
|---|---|---|---|---|---|---|
| S1 | SEC client and cache: ticker lookup, submissions, company facts, declared User-Agent, ≤ 5 requests per second, three retries | A | S0 | Tests run without network on saved files; a real download works from A's laptop | E4 | todo |
| S2 | Line-item resolver with sources (§5, §6) | A | S1, S0b | Tests for every rule in §5.3 and every planted mistake in §5.4 | E5–E8, PE1–PE6 | todo |
| S3 | Coverage report over about 100 non-financial companies from at least 8 industries → `docs/coverage.md`; the 30 companies of the verified universe → `app/data/universe.csv` | A | S2 | Table exists; go/no-go decided at office hours Fri 20 (§13.4) | E16 | todo |
| S5 | Past performance checks P1–P6 (P4, P5 "not assessed" until S4) | B | S0c | Appendix A values reproduced; edge cases tested | AC3, CALC-P* | todo |
| S6 | Financial health checks H1–H6 | B | S0c | Same | AC3, CALC-H*, E9, E12 | todo |
| S7 | Dividend checks D1–D6 (D2 "not assessed" until S4 and a share price) | C | S0c | Same | AC3, CALC-D*, E10, E11 | todo |
| S10 | Interface: input bar, header, score chart (six-block bars), expandable checks, sources page, theme file `app/.streamlit/config.toml` (SPEC v2.3 §3) | D | S0c, then S2 | `streamlit run` works; app test opens the synthetic company and finds a known score | AC1, AC3–AC5, V1, V3, V4 | todo |
| S11 | Gates (§10) and error messages | D | S2 | One test per stop and warn case | AC2, E1–E3, E15, V2 | todo |
| S14 | Demo mode on the five saved companies | A with D | S2, S10 | App runs with the network switched off | AC7 | todo |
| S15 | Reconciliation: six figures (revenue, operating income, net income, total assets, operating cash flow, dividends paid) per member for one demo company, read from the 10-K with page and accession number | All, coordinated by E | S2 | 30 figures match the resolver within USD 0.5 million | – | todo |
| S16a | Plain-language texts for the 18 tier 1 checks, written for a retail reader | E | S10 | Each check shows its text; reviewed by the check's owner | AC4 | todo |

### Tier 2: release v0.2 "Valuation" (target Wed 25 November)

| # | Slice | Owner | Depends on | Done when (evidence) | Acceptance | Status |
|---|---|---|---|---|---|---|
| S4 | Extraction script, benchmark CSV, industry lookup; fallback table only if generated from SEC codes in his file, never by hand (SPEC v2.3 §4, §9.1); starts Thu 19 with the day-one look at `indname.xls`, in parallel with S5 | B | S0 | Loader tests; three benchmark values and three company-to-group matches compared by hand with the source files; every verified company matched or the gap reported | AC8, E17 | todo |
| S2b | Before S12: the `Statement` shape in `app/src/contracts.py` and the "overrides" wording there updated; the FRED `DGS10` download with cache and settings fallback (SPEC v2.3 §4, §11) | A | S0 | Contract tests pass; the FRED client tested on a saved response with the network off; the fallback used when the key or the network is missing | – | todo |
| S8 | Equity method (SPEC v2.3 §8): cost of equity (beta limited to 0.8–2.0), starting free cash flow from the three-year margin, starting growth capped at −10%..+30% and decaying towards terminal growth (half-life 2 years, 10 years), terminal value, reported minority interests, when the model does not fit; starts Thu 19 on the synthetic company, with C's Excel model | C | S0c | Matches C's separate Excel model and Appendix A (valuation rows recalculated by C first: they changed in v2.3); property tests pass; one test per case of §8.6 | CALC-W*, CALC-F*, E12, E18–E20, E22 | todo |
| S9 | Valuation checks V1–V6 (V4 against the whole US market, V6 against the fair value at the 30% growth cap, SPEC v2.3); switch on P4, P5, D2 | C with B | S8, S4 | Appendix A values reproduced; the `insufficient_data` and `not_applicable` cases of §8.6 tested | AC8, AC9, CALC-V*, CALC-S | todo |
| S10b | Interface: share price input, valuation detail (cost of equity build-up, 10-year free cash flow table, fair value against the price, growth note when the growth limit applies), the reasons of §8.6, industry with route and number of firms; no sensitivity table, no implied growth, no user inputs | D | S8, S4 | App test finds the fair value of the synthetic company | AC6, AC9, AC10 | todo |
| S13 | Excel export, two sheets: scorecard; figures and sources | E | S10 | Export reopened by a test; figures equal the screen | AC11 | todo |
| S16b | Texts for the valuation checks and the industry explanations | E | S10b | Reviewed by C | – | todo |

### Tier 3: release v0.3 "Strengths and points to watch" (feature freeze Thu 26 November, 20:00)

| # | Slice | Owner | Depends on | Done when (evidence) | Acceptance | Status |
|---|---|---|---|---|---|---|
| S12 | Strengths and points to watch (SPEC v2.3 §9: 15 statements from the checks) | B (rules, `app/src/highlights.py`) with D (on screen) and E (texts, reviewed by B) | S2b, S4, S5–S9 | One test per statement (shown, not shown, input missing); the synthetic company's statements match Appendix A | AC12, CALC-G | todo |
| S17 | End-to-end app test: demo ticker, a known score, a known figure, a known fair value | D | S14 | Passes twice in a row in the workflow | AC1, V1 | todo |

### After the freeze: fixes only (Fri 27 November – Tue 1 December)

| # | Slice | Owner | Depends on | Done when (evidence) | Status |
|---|---|---|---|---|---|
| S18 | Break-it round: independent read-only review of each area; a deliberate break of every formula | Each owner; reviewer from another area | v0.2 | `docs/testing.md` lists each break and the test that caught it; every finding is a failing test or a written dismissal | todo |
| S19 | README and fresh-clone test on one Windows and one Mac laptop, by a member who did not write the README | E writes, two members test | v0.3 | Works from the README alone on both | todo |
| S20 | Business plan (Markdown → PDF), slides, recorded fallback demo, question bank | E leads and edits; each member writes one section (SPEC §17) | – | Files on `main` before the deadline | todo |

Cut list if a release slips by more than a day (§2): strengths and points to watch → Excel export. The tier 1 scorecard and the sources page are never cut. Everything on `main` by Tue 1 December, 12:00.

## Progress log

| Date | Slice | What changed | Checks run and results | Open problems |
|---|---|---|---|---|
| 2026-11-18 | S0.1 | Public repo `BossToGo/filing-scorecard` created; starter 0.3.0 and `SPEC.md` v2 committed to `main` (149180c); `Greg3334444` and `florian-spitzer` invited with write access | Commit linked to A's GitHub account; SPEC structure checked (21 sections, 24 checks, 25 slices); starter scanned for secrets: none | Two members not yet known; invitations expire after 7 days |
| 2026-11-18 | S0.2 | Product interview run from `SPEC.md`, asking only §16; four documents drafted on branch `a/S0-product-docs` | SPEC Appendix A recomputed by an independent script: all values agree within rounding | Q1–Q8 below |
| 2026-11-18 | S0b | Real SEC data for KO, AAPL, NVDA, MCD, AMZN (submissions, company facts) and JPM (submissions) downloaded with A's declared User-Agent (12 requests, ≤ 4 per second), trimmed to annual reports, saved in `app/evidence/demo/` with provenance; script `app/scripts/fetch_demo_data.py`, trimming rules `app/src/data/evidence.py` | Trimming tests written first and seen failing; checksum expected value computed with `shasum`, not Python; offline tests on the saved files: 35 passed (network blocked); known answer KO FY2025 revenue = session 5 slide 30; no file contains A's name or e-mail; pytest: 147 passed | Tag gaps found (Q11): KO debt after 2023, NVDA and AMZN capex, AAPL interest after 2023 |
| 2026-11-18 | S0.3 review | Three read-only reviewer agents (code, tests, security): no blocker, about 20 findings. Fixed: `CompanyData` picklable for Streamlit's cache; numpy numbers accepted; reported facts need tag, form, accession and a filed unit (no "USD m"); a check with a missing input cannot pass or fail; network guard switched on for the whole session, also records swallowed attempts; layering test reads full module names, relative and dynamic imports, and covers the interface; workflow runs on `main` never cancelled, `setup-python@v6`, no stored token, bash on Windows; `.gitignore` patterns inside `app/`; `CODEOWNERS` lines for the guardrail files; Python range stated as 3.11 to 3.14 | pytest: 100 passed; planted bypasses caught (guard switched off: 8 failed; a swallowed network error fails the test) | Skipped, with reason: pinning actions to commit hashes and a hashed lock file (more complexity for the team than the risk of a student repository with no secrets); subprocess network calls (no code uses them) |
| 2026-11-18 | S0.3 | Walking skeleton on branch `a/S0-skeleton`: shared data shapes with built-in rules, network guard for tests, layering test, `settings.yaml` with SPEC starting values, first page, CI on Linux and Windows, pull request template, `CODEOWNERS`, `docs/team.md`, team rules in `AGENTS.md` | Tests written first and seen failing (7 failed, 1 error); then pytest: 51 passed locally (Python 3.14.6, macOS); environment rebuilt from `requirements.txt` alone: 51 passed, `pip check` clean | CI result on GitHub: see the pull request |
| 2026-11-18 | S0 | Member guides in `docs/members/` (A to E) and a shared seven-step session routine; onboarding in `docs/team.md` fixed after the code review (no CODEOWNERS edit by new members, conflict and no-`gh` instructions, no-reply e-mail) | Scripted check against plan, acceptance and architecture: no gaps after two fixes | Names of B to E still [to confirm] |
| 2026-11-18 | S0 | Names and final roles: B Greg, C Flo, D Simon, E Emma; Excel export (S13) moved from D to E, five forces indicators from D to B, one business plan section per member; guides, owner table and `CODEOWNERS` updated (SPEC v2.2 in PR #3) | Script: names, usernames and owners agree across SPEC, guides, `CODEOWNERS`, plan; 100 tests pass | Group approves PR #3 |
| 2026-11-19 | S0 | SPEC v2.3 (Igor's product direction): retail bank customers; fully automatic, share price the only required input, optional growth and tax for a second fair value only; no figure or industry overrides; five forces replaced by strengths and points to watch (S12, B); growth limit and fade, beta limits, "model does not fit" rules (S8, C); member guides, product summary and owners updated; `forces` renamed `highlights` in `settings.yaml`, the layering test and `CODEOWNERS` | Appendix A valuation recalculated by an independent script that first reproduced the v2.2 values (21.68, 14.10%): fair value 19.74, implied starting growth 25.00%; pytest on this branch: see the pull request | Group approves the SPEC v2.3 pull request; instructor asked at office hours (§16.8); C and B recalculate their new Appendix A rows |
| 2026-11-20 | S0 | **Lean SPEC v2.3**, agreed by the group: equity method (operating cash flow − capex from the three-year margin, cost of equity, minus minority interests) instead of the firm method; growth the price implies kept as a display line; sensitivity table and the user's growth and tax inputs cut (share price the only input); 15 strengths and points to watch from the checks only (S2b shrinks to the `Statement` shape); fallback industry table generated only; customers see two warnings, the rest on the sources page; two-sheet export; watchlist dropped. Guides, product summary, acceptance criteria and settings updated | Appendix A recalculated for the equity method by an independent script (fair value 19.65, 26.07 at the cap, implied 26.97%; scores unchanged) and by a separate reviewer agent; settings test written first and seen failing; pytest: see the pull request | Instructor's view on the equity method (§16.8); Flo recalculates the valuation rows, Greg the statement table |
| 2026-11-20 | S0 | **Lean SPEC v2.3, round 2** (after re-checking Simply Wall St's published model): starting growth capped at 30% and decaying exponentially towards terminal growth (half-life 2 years) over 10 years; V4 = P/E below the whole US market instead of EV/EBITDA (no depreciation, cash or enterprise value in the valuation); growth the price implies cut; only reported minority interests subtracted; verified universe without depreciation. Risk-free rate unchanged, pending Igor's decision (fixed 5-year average vs live FRED) | Appendix A recalculated by an independent script: fair value 20.13, 37.37 at the cap, V6 passes, valuation 3 of 6; settings test written first and seen failing; pytest 148 passed | Flo recalculates the valuation rows, Emma the scores (valuation now 3 of 6), Greg extracts the market P/E |
| 2026-11-20 | S0 | Risk-free rate: **live FRED kept** (Igor), not a fixed average; demo mode, a missing key or an unreachable FRED use the dated value in `settings.yaml`; the FRED client joins A's S2b | – | Igor gets a free FRED key and adds `FRED_API_KEY` to his own `app/.env` |

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
  negative. Decide by: C. **Answered by SPEC v2.3 §8.6 (2026-11-19):** operating income ≤ 0 (or first-year free
  cash flow ≤ 0, or equity value ≤ 0) → no fair value and no reverse DCF, V1, V2, V6 `not_applicable` with the
  reason; the property test therefore applies only where the model fits. With the equity method of the lean v2.3
  (20 November) the value always rises with growth when the starting free cash flow is positive.
- **Q5. Debt tags may double count** (§6). `CommercialPaper` is often part of `ShortTermBorrowings`; `DebtCurrent`
  is not in the list. Written from memory: check on real files in S2 and S3. Decide by: A.
- **Q6. Terminal growth barely moves the sensitivity grid** (§8.5). With return on new capital equal to the cost of
  capital, terminal value = operating profit after tax × (1 + gT) ÷ cost of capital, so ±1 point of gT moves the
  synthetic fair value only from USD 21.50 to 21.86, against 18.81 to 25.32 for ±1 point of cost of capital. Not a
  bug: session 5 slide 33 says the same. Prepare the explanation for questions. Owner: C. **Closed 2026-11-20:** the
  sensitivity table is cut in the lean SPEC v2.3, and the firm method's terminal value is no longer used.
- **Q7. Team letters and names.** Decided 2026-11-18: A Igor (`BossToGo`), B Greg (`Greg3334444`), C Flo
  (`florian-spitzer`), D Simon (`Simonarmengaud`), E Emma (`EmmaRiggi`); all invited. Product name (§16.7):
  [to confirm].
- **Q8. Overlap with the session 5 demo** (§16.3): [to confirm with the instructor].
- **Q11. Tag gaps in the real filings** (found in S0b, details in `app/evidence/demo/README.md`). With the SPEC §6
  tags: Coca-Cola's debt is missing for FY2024–FY2025 (its debt tags stop at 2023), so the course's own running
  example could not be valued; Nvidia's and Amazon's capital expenditure tag stops in 2012 and 2016; Apple's
  interest expense stops after FY2023; Apple's `Revenues` stops in 2018, so fallbacks must be tried per fiscal
  year. Decide by: A in S2 (tag map) and S3 (coverage), before the go/no-go of Fri 20. Q1 is confirmed: Amazon
  has no dividend tag at all.
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
