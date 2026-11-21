# Member guides

One page per member: what you own, what you do and when, and the exact prompts to give your assistant.
`SPEC.md` has the final say; if a guide and the SPEC disagree, the SPEC wins and the guide is fixed.

| Member | Guide | Area in one line |
|---|---|---|
| A, Igor (@BossToGo) | [member-A.md](member-A.md) | Repository, CI, shared data shapes, SEC data layer, demo data, releases |
| B, Greg (@Greg3334444) | [member-B.md](member-B.md) | Industry benchmarks, past performance and financial health checks, strengths and points to watch |
| C, Flo (@florian-spitzer) | [member-C.md](member-C.md) | Dividend and valuation checks, valuation engine (equity method, growth decay, "model does not fit"), Excel cross-check |
| D, Simon (@Simonarmengaud) | [member-D.md](member-D.md) | Interface and theme, gates, demo mode with A, strengths and points to watch on screen, app tests |
| E, Emma (@EmmaRiggi) | [member-E.md](member-E.md) | Excel export (code), business plan, slides, README, check and statement texts, AI-usage report, question bank |

**SPEC v2.3 (19 November):** the product is for retail bank customers and fully automatic. The share price is the
only required input; nobody corrects figures by hand; five forces is replaced by strengths and points to watch
(SPEC §9). Read SPEC §1, §3 and the sections of your slices before your next prompt.

## Every work session, the same seven steps

1. Open the `filing-scorecard` folder in VS Code and start your assistant (`claude` in the terminal).
2. Paste the slice prompt from your guide. The assistant brings the latest `main` into your branch first.
3. Read its plan. Say "go" only if it touches nothing outside your folders.
4. When it asks for expected values, give **your own** hand working (paper or Excel). Never accept numbers the
   assistant worked out with the code it is testing.
5. Check that it showed the new tests **failing** first, then all tests passing.
6. Paste the closing prompt below, read the diff, approve the commit, then write the **Explain-back** in the pull
   request yourself: three sentences, your own words.
7. Ask your reviewer (your backup first) to approve on GitHub. Nobody merges their own work unreviewed.

**Closing prompt (same for everyone):**

> /test-and-check, then /review-changes for this slice. Fix only findings inside my folders and list the others
> for their owners. Then update my slice in docs/plan.md (status and progress log) and add a line to AI-USAGE.md.
> Show me the diff. After my OK, commit under my git identity, push, and open the pull request with the template.
> Leave the Explain-back for me. If git reports a conflict in docs/plan.md or AI-USAGE.md, keep both versions'
> rows.

**Business plan section (everyone writes one; the topic is in your guide):**

> I am member [letter], writing my business plan section "[topic]" in
> docs/business-plan/sections/[letter]-[topic].md. Read AGENTS.md, SPEC.md sections 1 and 17, docs/product.md and
> my guide in docs/members/. Use only facts from these files and from sources I give you. Invent no figure,
> statistic, source or quote (SPEC rule 14.17): write [source needed] where one is missing, and label every
> estimate with how it was derived. Use the branch [letter]/S20-bp-[topic] from the latest main. Change no other
> file.

**Reviewing a teammate's pull request (at least two a week, from other areas):**

> Do not change any file. Review pull request #[number] against SPEC.md sections [numbers]: list possible bugs,
> missing tests and anything outside the author's folders, each with file and line. Then help me write my review
> comment in my own words.

**Break-it round, S18 (Fri 27–Sun 29), when you review another member's area** (SPEC Appendix B):

> Do not change any file. You did not write this code. Assume it contains a bug and prove it. What it must do:
> [paste the relevant section of SPEC.md, not the code's comments]. For each suspected bug give the file and line,
> an input that shows it, the result the spec requires and the result the code gives. If you find nothing, say
> what you checked and what you did not check. Then: here are the tests; describe a bug that all of them would
> miss.

A finding counts only when it becomes a failing test, or is dismissed in writing in `docs/testing.md`.

## Never

- Commit to `main`, force-push, or merge without an approval.
- Edit another member's folder: describe the change for its owner (a GitHub issue or a message).
- Let the assistant invent an expected value, edit a failing test, or change a number in `SPEC.md`.
- Put a key, a password or your `app/.env` into a chat, a file or a screenshot.
- Fork the repository: work in your own clone, from your own laptop, under your own git name.
