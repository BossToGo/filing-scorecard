# AI usage

How AI tools were used in this project. Claude Code adds entries as the work happens; the team reviews them, and
completes the summary before hand-in.

## Summary (complete before hand-in)

- **Tools:** <e.g. Claude Code (model shown by `/model`), any chat assistant>
- **What AI did:** <code, tests, debugging, design proposals, documents>
- **What we decided ourselves:** <product scope, stack choice, acceptance criteria, ...>
- **How we checked AI output:** <tests, reviewer agents, hand checks of numbers, trying the app>
- **One example where the AI was wrong or misleading, and how we caught it:** <...>

## Log

| Date | Who asked | What the AI contributed | How it was checked | Accepted / changed / rejected |
|---|---|---|---|---|
| 2026-11-18 | Igor (A) | `SPEC.md` version 2 was drafted with Claude from the project handout and the session slides (SPEC §17) | Group review at the meeting of 18 November and through pull requests | pending group review |
| 2026-11-18 | Igor (A) | Claude Code (Claude Opus 5.5) created the repository from the course starter, added `SPEC.md` unchanged, invited two teammates | Igor approved the commit, the public repository and the invitations before each step; SPEC structure counted (21 sections, 24 checks, 25 slices); starter scanned for secrets (none); GitHub confirmed the commit is linked to Igor's account | accepted |
| 2026-11-18 | Igor (A) | Claude Code recomputed every value of SPEC Appendix A in a separate script and reviewed the SPEC for gaps | All values agree with Appendix A within rounding; six gaps logged as Q1–Q6 in `docs/plan.md` for the group to decide. Does not replace the owners' own recalculation (SPEC rule 14.5) | accepted as open questions |
| 2026-11-18 | Igor (A) | **AI was misleading, then corrected:** Claude first listed "terminal growth barely moves the sensitivity table" as a SPEC gap. Reading the session 5 slides (slide 33) showed it is the expected result when return on new capital equals the cost of capital, a course convention | Checked against the course slides; the item was reworded as a question to prepare for the presentation (Q6), not a bug | changed |
| 2026-11-18 | Igor (A) | Claude Code ran the starter's product interview from `SPEC.md` (only §16 asked) and drafted `docs/product.md`, `architecture.md`, `acceptance.md`, `plan.md` | Every section traced to a SPEC section; acceptance values copied from Appendix A and compared by script; reviewed by Igor and by a teammate in the pull request | pending review |
