# Member E: Emma (@EmmaRiggi)

**You own:** `app/src/export.py` (the Excel export, S13) and its tests, `README.md` (root), `docs/business-plan/`, `docs/slides/`, `docs/qa-bank.md`, `app/ui/texts.yaml` (the
plain-language text of the 24 checks and of every strength and point to watch, SPEC v2.3 §9), and the coordination of `AI-USAGE.md` (everyone adds lines; you write its
summary). You also review **every user-facing text**, coordinate the reconciliation (S15) and guard the scope (risk
R11). **Reconciliation company:** Amazon (AMZN). Your work counts only if it is in the repository: commit it through
pull requests, like everyone else (SPEC §12). The Excel export is your code feature: every member contributes code.

## Your tasks, in order

**Timeline (SPEC v2.4, 22 November):** the MVP is the five demo companies, one workflow end to end. Release v0.1 on **Tuesday 24** (the screen and the 18 checks), v0.2 with the feature freeze on **Thursday 26 at 20:00** (the fair value). The strengths and points to watch (S12) and the Excel export (S13) are built only if v0.2 is released before the freeze.

| When | Task | Done when |
|---|---|---|
| Thu 19 → Sun 22 | **Sources for the problem evidence:** read the published studies listed under "Problem evidence" below (and any you add), and note each figure you will use with its source, date and unit. No user interviews (decided by Igor, 21 November): the course brief does not require them | Each figure in the problem section has a source you have read |
| Thu 19 | **Sign-off for S0c:** CALC-S (the four area scores) | Done: recorded in PR #5 |
| Sun 22–Tue 24 | S16a: texts for the 18 tier 1 checks in `app/ui/texts.yaml` (key names agreed with Simon, D), plus a test in `app/tests/unit/test_texts.py` that every check has a text (PR #17) | Each check shows its text; reviewed by the check's owner |
| Sun 22–Tue 24 | S15: collect the five reconciliation files (A: KO, done in #16; B: AAPL; C: NVDA; D: MCD; you: AMZN) | 30 figures match the app within USD 0.5 million |
| Sat 21 → Tue 24 | **Business plan:** write problem and evidence, how roles and decisions change in a firm (the bank that offers the add-on to its customers), SDG 9 and next steps; assemble everyone's sections from `docs/business-plan/sections/` into `docs/business-plan/business-plan.md` and the PDF (contents: SPEC §17) | Draft by Tue 24 (SPEC v2.4 §13.3); final by Sun 29; PDF on `main` |
| Wed 25–Thu 26 | S16b: texts for the valuation checks, the industry explanations and the growth note | Reviewed by C |
| Thu 26, only if v0.2 is released before the freeze | **S13: Excel export, your code feature.** `app/src/export.py` writes one Excel file with **two sheets**: the scorecard (scores, checks, strengths and points to watch, valuation) and the figures with their sources (SPEC §3 item 8); a test reopens it and compares every figure. Branch `e/S13-excel-export`; Simon (D) adds the download button. Within S12: texts for the 15 strengths and points to watch (agree the key names with Greg and Simon) | AC11: export reopened by a test; figures equal the screen. Statement texts reviewed by B |
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
> SPEC.md sections 3 and 7. Write in app/ui/texts.yaml, for each tier 1 check, the rule in plain words for a bank
> customer with no finance training, with the unit and no number that the app computes. Information, not advice:
> never "buy", "sell" or "undervalued". Use the key names agreed with D. Use the
> branch e/S16a-check-texts from the latest main. Do not change files outside my folders.

**Prompt for the Excel export (S13):**

> /build-feature I am member E, working on slice S13 of SPEC.md. Read AGENTS.md, docs/members/member-E.md,
> SPEC.md sections 3 (item 8), 5.1 and 11, docs/plan.md and AC11 in docs/acceptance.md. Use the branch
> e/S13-excel-export from the latest main. Plan this slice only: a function in app/src/export.py that writes the
> prepared scorecard and the figures with their sources into one Excel file with two sheets, and a test that reopens the file and
> compares every figure. It must not compute any number itself (SPEC §11). Name the files and the tests you will
> write first, and wait for my go-ahead. I will give you the expected values. Do not change files outside my
> folders.

## What the README must say (SPEC §17)

What it does and for whom; install and run in a few commands (copy from `app/README.md`); data and interfaces
used; assumptions (currency, units, fiscal-year convention, 21% tax rate, 5.0% equity risk premium); known
limitations (SPEC v2.4: the MVP is the five demo companies; other tickers can be looked up, and their known
problems from `docs/plan.md` are listed here); which data is saved or synthetic; who it is for (retail bank customers, as an add-on a bank offers;
SPEC v2.3 §1). **Citations:** the scoring idea follows the publicly documented
Simply Wall St analysis model, including the strengths and points to watch and the "model does not fit" rule
(`https://github.com/SimplyWallSt/Company-Analysis-Model`; never their name in the app, the word "snowflake",
their design or text);
Professor Damodaran's datasets (attribution); SEC EDGAR; the session 5 valuation conventions.

## Only you

1. **Problem evidence** for the business plan, from published studies (starting list below), each read by you before
   you cite it, plus the team's own experience, labelled as such (SPEC §17; never invent a figure, rule 17).
2. **Reconciliation (S15), Amazon:** revenue, operating income, net income, total assets, operating cash flow,
   dividends paid (Amazon is expected to pay none: write what the filing shows), read by hand from the latest
   10-K with page and accession number. Not by the assistant.
3. **Scope guard:** any new idea after Tue 24 goes into "next steps" of the business plan, not into the app.
4. **Explain-back** on each PR; review every user-facing text and at least two other PRs a week.

## Problem evidence: starting sources (checked on the original pages, 21 November)

Read each source yourself before citing it, and quote figures with their date and population. What they support:
most retail investors cannot judge a company, many decide on social media and fear of missing out, almost nobody
reads the annual report, and attention-driven buying loses money.

- SEC staff, *Study Regarding Financial Literacy Among Investors* (August 2012, Dodd-Frank §917): retail investors
  lack basic financial literacy; investors prefer disclosures in a visual format (bullets, charts, graphs).
  https://www.sec.gov/files/917-financial-literacy-study-part1.pdf
- European Commission, Eurobarometer on financial literacy (published 18 July 2023): 18% of EU citizens have a high
  level of financial literacy, 64% medium, 18% low.
  https://finance.ec.europa.eu/news/eurobarometer-survey-reveals-low-levels-financial-literacy-across-eu-2023-07-18_en
- FINRA Foundation, *Investors in the United States* (2024 survey, 2,861 investors; published December 2025): 5.3
  of 11 investing questions answered correctly on average; 26% use social media influencers' recommendations (61% of
  those under 35). https://www.finra.org/media-center/newsreleases/2025/new-finra-foundation-research-examines-shifting-investor-behaviors
- FINRA Foundation and CFA Institute, *Gen Z and Investing* (published May 2023; survey November/December 2022,
  2,872 people): social media is US Gen Z investors' top source (48%); 41% of US Gen Z investors cite fear of
  missing out as a factor in starting to invest (CFA Institute press release); 50% say they have made an investment
  driven by it (FINRA news release). Quote the one that fits your sentence, with its exact wording.
  https://www.finrafoundation.org/sites/finrafoundation/files/Gen-Z-and-Investing.pdf
  https://www.finra.org/media-center/newsreleases/2023/finra-foundation-cfa-institute-research-focuses-gen-z-investors
- FCA, *Understanding self-directed investors* (March 2021): newer investors are often driven by the thrill and
  status of investing. https://www.fca.org.uk/news/press-releases/fca-warns-younger-investors-are-taking-big-financial-risks
- Loughran and McDonald (2017), "The Use of EDGAR Filings by Investors", *Journal of Behavioral Finance* 18(2):
  the average firm's 10-K is requested only 28.4 times from the SEC right after filing (caveat: professionals also
  read filings through paid terminals). https://ideas.repec.org/a/taf/hbhfxx/v18y2017i2p231-248.html
- Barber, Huang, Odean and Schwarz (2022), "Attention-Induced Trading and Returns: Evidence from Robinhood Users",
  *Journal of Finance* 77(6): the stocks most bought each day by app users show −4.7% abnormal returns over the
  next 20 days. https://econpapers.repec.org/RePEc:bla:jfinan:v:77:y:2022:i:6:p:3141-3190

These studies show the problem, not that customers will use our app: say that the app helps people check a company
before buying, not that it stops investing on hype. Why a bank would offer the add-on is Greg's section (users,
market and alternatives) and needs its own sources.
