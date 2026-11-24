# Member A: Igor Willms (@BossToGo)

**You own:** the repository and CI (`.github/`), the product documents (`docs/product.md`, `architecture.md`,
`acceptance.md`, `plan.md`, `team.md`, `coverage.md`, `members/`), `app/src/contracts.py`, `app/src/data/`,
`app/evidence/`, `app/data/universe.csv`, `app/scripts/coverage.py`, `app/tests/fixtures/`, the `data` section of
`app/settings.yaml`, `app/README.md`, `app/requirements.txt`. **Backup:** D, Simon (first reviewer of your PRs, and you of
theirs). **Reconciliation company:** Coca-Cola (KO).

Claude Code runs your slices under the delegation recorded in `docs/architecture.md` (2026-11-18). The list
"Only you" below is what it cannot do for you.

## Your slices, in order

**Timeline (SPEC v2.4, 22 November):** the MVP is the five demo companies, one workflow end to end. Release v0.1 on **Tuesday 24** (the screen and the 18 checks), v0.2 with the feature freeze on **Thursday 26 at 20:00** (the fair value). The strengths and points to watch (S12) and the Excel export (S13) are built only if v0.2 is released before the freeze.

| When | Slice | Done when (SPEC §13.2) |
|---|---|---|
| Wed 18–Sat 21 | S0, S0b, S1, S2, S3 | Done: PRs #1, #2, #3, #6, #7, #8, #9. S0.4 still open: Greg's team PR #22 and the red-then-green demonstration |
| Sun 22 | S0c: synthetic company fixture | Done: [PR #5](https://github.com/BossToGo/filing-scorecard/pull/5), merged with four sign-offs; record Greg's sign-off (B: P and H rows and the statements) in a small follow-up PR when he posts it |
| Sun 22–Tue 24 | Your open data-layer PRs: audit fixes (#19), Amazon's "no dividend paid" (#21, plan Q1), the reconciliation rule (#18); after each merge, bring `main` into the others and keep both sides' log rows | Merged |
| Sun 22–Tue 24 | S14 with D: demo mode; release check and tag **v0.1** (Tue evening) | App runs with the network off |
| Wed 25–Thu 26 | S2b: the `Statement` shape in `app/src/contracts.py` and its "overrides" wording (Simon's review of #2); the FRED `DGS10` download of the last five years and its average (cached with the period; settings fallback for demo mode, a missing key or no network; SPEC §4), branch `a/S2b-statement` | Contract tests pass; the FRED client tested on a saved response, network off |
| Thu 26, 20:00 | Feature freeze; release check and tag **v0.2** (if the valuation is not merged, v0.1 is what we present, SPEC v2.4 §13.3) | – |
| Sat 21–Sun 29 | **Business plan section:** data dependencies, failure modes and the controls built into the app, in `docs/business-plan/sections/A-data-and-controls.md` | Draft in #15; final by Sun 29 |
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

1. **Explain-back** on every one of your PRs: three sentences in your own words.
2. **FRED key (S2b):** put your own key in `app/.env` as `FRED_API_KEY` yourself; never paste it into the chat.
3. **Expected values** for every new data-layer rule: your own reading of the filing (figure, page, accession
   number), as for Coca-Cola. Reconciliation (S15), Coca-Cola: done (#16, read by hand).
4. **Decide** Q5 (debt tags): still open for the group, not needed for the five demo companies (`docs/plan.md`).
5. **Approve** teammates' PRs quickly, review at least two PRs a week, Simon's (D) first.
6. **Releases:** run the release check yourself and tag v0.1 (Tue 24) and v0.2 (Thu 26, 20:00).
7. **Your e-mail:** your commits so far show your personal e-mail in this public repository; history is never
   rewritten (rule 14.14). Decide whether to switch future commits to your GitHub no-reply address (steps in
   `docs/team.md`, step 2).
8. **Before the presentation:** send E five likely questions and answers on your area (Sun 29); walk the team
   through your area (Mon 30).
