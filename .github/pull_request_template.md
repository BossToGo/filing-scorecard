<!-- Title: "S<id>: <what>", e.g. "S5: past performance checks P1–P6". One slice per pull request (docs/plan.md). -->

**Slice:** S__ · **Member:** _ (A–E) · **Branch:** `<member>/<slice-id>-<short-name>`

**What:** <!-- one or two sentences -->

**Why:** <!-- which SPEC section or plan slice this delivers -->

**Checked:** <!-- tests run and their result (e.g. "pytest: 63 passed"); numbers checked by hand, against what -->

**Files:** <!-- the main files touched -->

**AI use:** <!-- tool and what it did; also add a line to AI-USAGE.md -->

**Explain-back:** <!-- three sentences in YOUR OWN words on how the code works. Not written by the AI (SPEC §12 rule 4). -->

### Checklist (SPEC §12, §14)

- [ ] Only files in my own folders (`docs/architecture.md`, "Folder layout and owners"), or the owner agreed
- [ ] Tests written first and seen failing; all tests pass: `cd app` then `.venv/bin/python -m pytest` (Windows: `.venv\Scripts\python -m pytest`)
- [ ] Expected values come from my own hand working or a cited source, never from running the code (rule 14.5)
- [ ] No failing test or expected value edited without a written reason below (rule 14.6)
- [ ] No secrets, no `.env`, no network in tests
- [ ] `docs/plan.md` (status and progress log) and `AI-USAGE.md` updated
