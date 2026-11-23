# Team

| Member | Name | GitHub | Assistant | Area (SPEC §12, `docs/architecture.md`) | Backup |
|---|---|---|---|---|---|
| A | Igor Willms | @BossToGo | Claude Code | Repository, CI, shared data shapes, SEC data layer, evidence, coverage report, demo snapshot | D |
| C | Florian Spitzer | @florian-spitzer | Claude Code | Dividend and valuation checks (`app/src/checks/dividend.py`, `app/src/checks/valuation.py`), valuation engine (`app/src/valuation/`), Excel cross-check model (`docs/crosscheck/`) | B |
| D | Simon Armengaud | @simonarmengaud | Claude Code | Interface and theme (`app/main.py`, `app/ui/` except `texts.yaml`, `app/.streamlit/`), gates, demo mode with A, strengths and points to watch on screen, app tests | A |
| E | Emma Riggi | @EmmaRiggi | Claude Code | Excel export (`app/src/export.py`), plain-language texts (`app/ui/texts.yaml`), business plan, slides, README, question bank, `AI-USAGE.md` coordination | — |

**Your guide:** `docs/members/member-<your letter>.md`: what you own, your slices in order with dates, the exact
prompts to give your assistant, and what only you can do. Start there.

## Your first task: add your own line (SPEC §12, rule 1)

This first pull request proves that your commits are linked to your GitHub account. Individual contribution
(15 points) is read only from the repository history, so do it from **your own laptop**.

1. Accept the invitation: https://github.com/BossToGo/filing-scorecard/invitations
2. Check that git uses your name and an e-mail that is verified on your GitHub account (GitHub → Settings →
   Emails):
   ```bash
   git config --global user.name
   git config --global user.email
   ```
   The repository is public and its history is never rewritten, so this e-mail stays visible. To keep your
   private address out: on that GitHub page tick "Keep my email addresses private", set git to the no-reply
   address shown there (`git config --global user.email 12345678+username@users.noreply.github.com`), then
   tick "Block command line pushes that expose my email". Your commits still count for your account.
3. **Clone** the repository (do not fork it: commits on a fork do not count for the group repository):
   ```bash
   git clone https://github.com/BossToGo/filing-scorecard.git
   ```
4. Open the `filing-scorecard` folder in VS Code, start your assistant there (`claude` in the terminal) and
   paste this, filled in:

   > I am member [B/C/D/E], [my name], GitHub [@username], and I use [Claude Code / Cline]. Read AGENTS.md,
   > docs/team.md and docs/members/member-[my letter].md. Create the branch [letter]/S0-team-[my first name]
   > from the latest main and add my line to the table in docs/team.md, nothing else. Show me the diff. After I
   > approve, commit it under my own git identity, push the branch and open a pull request using the template.
   > If the gh command is missing, tell me and I will use the "Compare & pull request" button on GitHub. Leave
   > the Explain-back for me to write.

5. Write the Explain-back yourself, then ask a teammate to approve the pull request on GitHub. If GitHub says
   your branch has conflicts (another member's line went in first), tell your assistant: "Bring the latest main
   into my branch, keep both rows in docs/team.md, run the tests and push."
6. Tell Igor (A) your letter and GitHub username. Igor adds you to `.github/CODEOWNERS`, so GitHub asks you to
   review every change to your folders.

Members and areas: A to E as in SPEC §12. If the group has four members, E's work is shared out; if six,
D's interface work is split in two.
