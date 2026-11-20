# Member A: Igor Willms (@BossToGo)

**You own:** the repository and CI (`.github/`), the product documents (`docs/product.md`, `architecture.md`,
`acceptance.md`, `plan.md`, `team.md`, `coverage.md`, `members/`), `app/src/contracts.py`, `app/src/data/`,
`app/evidence/`, `app/data/universe.csv`, `app/scripts/coverage.py`, `app/tests/fixtures/`, the `data` section of
`app/settings.yaml`, `app/README.md`, `app/requirements.txt`. **Backup:** D, Simon (first reviewer of your PRs, and you of
theirs). **Reconciliation company:** Coca-Cola (KO).

Claude Code runs your slices under the delegation recorded in `docs/architecture.md` (2026-11-18). The list
"Only you" below is what it cannot do for you.

## Your slices, in order

| When | Slice | Done when (SPEC §13.2) |
|---|---|---|
| Wed 18 | S0: PRs #1 (docs), #2 (skeleton), #3 (SPEC v2.1) reviewed and merged; `main` protected; teammates' `docs/team.md` PRs merged; their usernames added to `.github/CODEOWNERS` | Five merged team PRs; a deliberately failing test turns the check red, then green |
| Thu 19 | S0b: saved SEC files for the five demo companies in `app/evidence/demo/` | Files load in a test with the network off |
| Thu 19 | S0c: synthetic company fixture, [PR #5](https://github.com/BossToGo/filing-scorecard/pull/5); record each owner's sign-off comment under `sign_off` in `app/tests/fixtures/synthetic_co.yaml`, with a link (B: P and H rows and the statements, C: D, V, W, F rows, D: AC3, E: CALC-S). As soon as SPEC v2.3 is merged: bring `main` into the branch and update the fixture to the v2.3 Appendix A (equity-method valuation working, no override or user-input entries, the expected statements for B), with the rule 14.6 reason in the PR | Merged with five sign-offs in the PR |
| Thu 19 | S1: SEC client and cache | Tests run without network on saved files; a real download works from your laptop |
| Fri 20 | S2: line-item resolver with sources; also the reconciliation file format in `app/tests/reconciliation/README.md`, so B to E can fill in theirs | Tests for every rule in SPEC §5.3 and every planted mistake in §5.4 |
| Fri 20 | S3: coverage report → `docs/coverage.md`, verified universe → `app/data/universe.csv` | Go/no-go decided at office hours, 16:00–18:00 (SPEC §13.4) |
| Sat 21–Sun 22 | S14 with D: demo mode; release check and tag **v0.1** (Sun evening) | App runs with the network off |
| Wed 25 | Release check and tag **v0.2** | – |
| Mon 23–Wed 25 | S2b, before Greg's S12 (SPEC v2.3 §11): the `Statement` shape in `app/src/contracts.py`, and the "overrides" wording in `contracts.py` updated (Simon's review of #2); the FRED `DGS10` download (latest value with its date, cached; settings fallback for demo mode, a missing key or no network; SPEC §4), branch `a/S2b-statement` | Contract tests pass; the FRED client tested on a saved response, network off |
| Thu 26, 20:00 | Feature freeze; release check and tag **v0.3** | – |
| Sat 21–Sun 29 | **Business plan section:** data dependencies, failure modes and the controls built into the app, in `docs/business-plan/sections/A-data-and-controls.md` (Emma, E, assembles the plan; prompt in `docs/members/README.md`) | Draft by Sun 22; final by Sun 29 |
| Fri 27–Sun 29 | S18, break-it round: a member from another area reviews your code read-only; you break each of your formulas once on purpose and record each break and the test that caught it in `docs/testing.md` | Every finding is a failing test or a written dismissal |

**Release check (SPEC §13.1):** all tests green on GitHub; app started in demo mode with the network off; the
five demo companies open without an error; the README run commands still work. Then tag `main` and record the date
in `docs/plan.md`.

**Slice prompt** (replace the slice id and branch):

> /build-feature I am member A, working on slice [S0b] of SPEC.md. Read AGENTS.md, docs/members/member-A.md, the
> SPEC sections this slice names, docs/plan.md and docs/acceptance.md. Use the branch [a/S0b-demo-data] from the
> latest main. Plan this slice, name the files and the tests you will write first, then go ahead under my
> delegation. Ask me for every expected value.

## Only you

1. **Explain-back** on every one of your PRs (#1, #2, #3 now): three sentences in your own words.
2. **Create `app/.env`** before S0b (`cd app`, `cp .env.example .env`, then put your own name and e-mail in
   `SEC_USER_AGENT` with an editor). Never paste it into the chat.
3. **Expected values for the resolver (S2):** read them yourself from Coca-Cola's latest 10-K on sec.gov (figure,
   page, accession number). The session 5 slides give one to check against: KO revenue FY2025, USD 47,941 m,
   accession 0001628280-26-010047.
4. **Reconciliation (S15), Coca-Cola:** revenue, operating income, net income, total assets, operating cash flow,
   dividends paid for the latest fiscal year, read by hand from the 10-K with page and accession number. Do not let
   the assistant read them for you: this is the independent check.
5. **Decide** Q5 (debt tags) after S2; Q1 (missing versus nil) with Greg and Flo (Amazon has no dividend tag at all (confirmed in the saved SEC files); `docs/plan.md`, open questions).
6. **Approve** every teammate's first PR quickly, review at least two PRs a week, Simon's (D) first.
7. **Office hours, Fri 20:** present the coverage table and the KO reconciliation; record the go/no-go.
8. **Your e-mail:** your commits so far show your personal e-mail in this public repository; history is never
   rewritten (rule 14.14). Decide whether to switch future commits to your GitHub no-reply address (steps in
   `docs/team.md`, step 2).
9. **Before the presentation:** send E five likely questions and answers on your area (Sun 29); walk the team
   through your area (Mon 30).

## Today's group meeting: agenda

1. Agree `SPEC.md` (approve PR #3, the `app/` layout) and decide Q2 (S4 and S8 start early).
2. Letters agreed: B Greg, C Flo, D Simon, E Emma. Approve SPEC v2.2 (PR #3): the Excel export goes to Emma, the
   five forces indicators to Greg, one business plan section to each member. Ask who uses Claude Code or Cline
   (SPEC §16.6).
3. Confirm the reconciliation companies: A KO, B Apple, C Nvidia, D McDonald's, E Amazon.
4. Everyone: accept the invitation, then their `docs/team.md` PR today (instructions in `docs/team.md`).
5. Product name (SPEC §16.7); who asks the instructor about the overlap with the session 5 demo (§16.3).
6. SPEC v2.3 (19 November): retail bank customers, fully automatic, strengths and points to watch instead of five
   forces, equity method with growth decay. Everyone reads it and one teammate approves the pull request; ask the instructor
   at office hours (§16.8).
