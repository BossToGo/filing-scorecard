# Member E: [name] ([@github])

**You own:** `README.md` (root), `docs/business-plan/`, `docs/slides/`, `docs/qa-bank.md`, `app/ui/texts.yaml` (the
plain-language text of the 24 checks), and the coordination of `AI-USAGE.md` (everyone adds lines; you write its
summary). You also review **every user-facing text**, coordinate the reconciliation (S15) and guard the scope (risk
R11). **Reconciliation company:** Amazon (AMZN). Your work counts only if it is in the repository: commit it as
Markdown through pull requests, like everyone else (SPEC §12).

## Your tasks, in order

| When | Task | Done when |
|---|---|---|
| Wed 18 | Accept the invitation; your `docs/team.md` PR (steps in `docs/team.md`) | Merged |
| Thu 19 | Book 3 to 5 **user interviews** (analysts, advisers, investment-club members); notes without names in `docs/business-plan/interviews.md` | Interviews booked |
| Thu 19 | **Sign-off for S0c:** recalculate CALC-S (the four area scores) in `docs/acceptance.md` | Your sign-off comment on PR #5 (it unlocks `synthetic.expected_scores()` for the app tests) |
| Sat 21 → | **Business plan** draft in `docs/business-plan/business-plan.md` (contents: SPEC §17); everyone contributes | Draft by Sun 22; final by Sun 29; PDF on `main` |
| Sat 21–Sun 22 | S16a: texts for the 18 tier 1 checks in `app/ui/texts.yaml` (agree the key names with D) | Each check shows its text; reviewed by the check's owner |
| Sat 21–Sun 22 | S15: collect the five reconciliation files (A: KO, B: AAPL, C: NVDA, D: MCD, you: AMZN) | 30 figures match the app within USD 0.5 million |
| Mon 23–Wed 25 | S16b: texts for the valuation checks and the industry explanations | Reviewed by C |
| Fri 27–Sun 29 | **README** final; S19: two members who did not write it install the app from the README alone, one on Windows, one on Mac | Works on both |
| Fri 27–Sun 29 | **Slides** in `docs/slides/` (SPEC §17: problem 1 min, live demo 3–4, how we built and checked it 1–2, transformation and SDG 9 2, next steps); **question bank** `docs/qa-bank.md` (five questions and answers per area, sent by each owner) | On `main` |
| Fri 27–Sun 29 | S18, break-it round: review one code area read-only (A assigns it), with the break-it prompt in `docs/members/README.md` | Each finding is a failing test or a written dismissal in `docs/testing.md` |
| Mon 30 | Two timed rehearsals; record the fallback demo with D | Recording saved |
| Tue 1 Dec | Handout section 11 checklist; `AI-USAGE.md` summary complete; everything on `main` by 12:00 | Done |

**How to sign off (S0c):** recalculate your rows on paper or in Excel, then post a review comment on
[PR #5](https://github.com/BossToGo/filing-scorecard/pull/5): the rows, the date, how you calculated, and any
difference. A records it under `sign_off` in `app/tests/fixtures/synthetic_co.yaml`, with a link to your
comment. Until then the fixture refuses your rows with the error `NotSignedOff`, naming you.

**Prompt for writing** (replace the task and file):

> I am member E, working on [the business plan section "problem and evidence"] in [docs/business-plan/business-plan.md].
> Read AGENTS.md, docs/members/member-E.md, SPEC.md sections [1 and 17] and docs/product.md. Use only facts from
> these files and from sources I give you. Invent no figure, statistic, source or quote (SPEC rule 14.17): write
> [source needed] where one is missing, and label every estimate with how it was derived. Use the branch
> [e/S20-business-plan] from the latest main. Do not change files outside my folders.

**Prompt for the check texts (S16a):**

> /build-feature I am member E, working on slice S16a of SPEC.md. Read AGENTS.md, docs/members/member-E.md and
> SPEC.md section 7. Write in app/ui/texts.yaml, for each tier 1 check, the rule in plain words for an analyst who
> is not a programmer, with the unit and no number that the app computes. Use the key names agreed with D. Use the
> branch e/S16a-check-texts from the latest main. Do not change files outside my folders.

## What the README must say (SPEC §17)

What it does and for whom; install and run in a few commands (copy from `app/README.md`); data and interfaces
used; assumptions (currency, units, fiscal-year convention, 21% tax rate, 5.0% equity risk premium); known
limitations; which data is saved or synthetic. **Citations:** the scoring idea follows the publicly documented
Simply Wall St analysis model (cite it; never their name in the app, the word "snowflake", their design or text);
Professor Damodaran's datasets (attribution); SEC EDGAR; the session 5 valuation conventions.

## Only you

1. **User interviews** and their notes: real evidence for the business plan, without personal data in the repo.
2. **Reconciliation (S15), Amazon:** revenue, operating income, net income, total assets, operating cash flow,
   dividends paid (Amazon is expected to pay none: write what the filing shows), read by hand from the latest
   10-K with page and accession number. Not by the assistant.
3. **Scope guard:** any new idea after Tue 24 goes into "next steps" of the business plan, not into the app.
4. **Explain-back** on each PR; review every user-facing text and at least two other PRs a week.
