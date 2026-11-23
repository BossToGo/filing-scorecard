# Product: Filing Scorecard (working title, SPEC 16.7 [to confirm])

Status: agreed on 2026-11-18 by Igor (member A) on the basis of `SPEC.md` version 2; confirmed by the group
through the review of the pull request that adds this file. Updated on 2026-11-19 for `SPEC.md` version 2.3
(Igor's product direction: retail bank customers, fully automatic, strengths and points to watch instead of five
forces); the group confirms it by approving the SPEC v2.3 pull request. Updated on 2026-11-22 for `SPEC.md`
version 2.4 (the MVP is the five demo companies, one workflow end to end), approved by the group in pull request #20.
Updated on 2026-11-23 for `SPEC.md` version 2.4.2 (the screen design of `docs/design/`), approved by the group
through the pull request that adds that folder.

**`SPEC.md` has the final say.** This file summarises it for the assistant and the team. If the two disagree,
`SPEC.md` wins and this file is corrected by pull request. Section numbers below (§) point to `SPEC.md`.

## Problem and customers

- **Customer:** a retail bank that offers the scorecard to its customers next to its order screen; the **user**
  is the bank's customer who is about to buy a US stock and wants a quick, objective first look (§1).
- **Problem today:** reading annual reports takes hours and knowledge most retail investors do not have; free
  websites mix reported figures with forecasts and rarely show sources; the bank wants to help without giving
  advice (§1).
- **Success looks like:** choosing a company and typing the share price gives a one-page scorecard in under a minute
  (seconds in demo mode) that needs no checking by the user: every figure passed the automatic checks or is shown
  as "not assessed", and each one can be traced to its filing, tag and filing date on the sources page.

## Main user journey

1. The user opens the app and sees the input bar: ticker, share price (USD; the only figure the user types; without it the valuation area and the dividend yield check show "insufficient data"), demo mode.
2. They pick one of the five demo companies (or type another ticker, outside the MVP) and type the share price (in a bank, the price would come from the bank's own quote).
3. The app fetches the company's SEC filings (or reads saved data in demo mode), runs the data-quality gates
   (§10), and shows the header, the score chart, the strengths and points to watch and the 24 checks (§3, §7, §9).
4. They open a check to see the rule in plain words, the formula, the input figures with fiscal years and the
   link to the filing. Nothing is corrected by hand: a figure that cannot be read is "not assessed" (§1).
5. They read the valuation detail: the estimate per share against the price and how it was built (and, when the
   growth limit applies, a factual growth note). They can check the sources page and download the Excel file. The share price is the only input
   (§1, §8.7).

## Screens and visuals

Look: a panel in a bank's buy step that reads like a research note: one score chart, the failed checks next to it
(strengths and points to watch from tier 3), one tab per area with expandable checks and tables. Calm, one accent
colour, no gradients, glow, shadows or emoji; a light and a dark theme with the same structure (the app follows the
viewer's system setting; the viewer switches in the app menu); colours defined once in `app/.streamlit/config.toml` so
a bank can apply its brand (§3). Layout, marks, texts and states: `docs/design/design-spec.md` and its mockup. Used on a phone: no (laptop demo). Visual reference: the way Simply Wall St
presents results (areas, ticks, strengths and risks), in our own design. We do **not** use Simply Wall St's name,
the word "snowflake", their radar-chart design or their text (§1, rule 14.16). Wording is information, not
advice: never "buy", "sell" or "undervalued" (§3).

| Screen | Purpose | The user sees first | Cards / charts / tables (unit, period) | The user can | Loading / empty / error |
|---|---|---|---|---|---|
| Scorecard (main page) | First-pass view of one company | Header: company, industry and how it was found, fiscal year end, latest 10-K date, retrieval date, and only two warnings ("not fully checked", "old annual report"; the rest on the sources page, §10); then the score chart | Score chart (4 areas, passes out of 6) with a legend; the failed checks next to it; one tab per area: its score, one sentence, key figures and its checks, each a sentence with the company's figures, expandable to rule, working, inputs (USD m, fiscal year) and filing link; the sources page as the last tab | Pick one of the five demo companies or type another ticker; type the share price (USD); switch demo mode; open a check | Loading: "Fetching SEC filings…". Unknown ticker, unsupported company (bank, insurer, REIT, non-USD, non-10-K), source unreachable: a message that says how to fix it (§3) |
| Valuation detail (tier 2, on the main page) | Show how the fair value was built | Fair value per share against the share price (USD) | Tables: cost of equity build-up (%), 10-year free cash flow forecast (USD m), actual revenue growth (%); the growth note when the growth limit applies | Nothing to type: the share price in the input bar is the only input | No share price: the whole area shows "insufficient data, enter a share price". Model does not fit (§8.6): no fair value, the reason in plain words |
| Strengths and points to watch (tier 3, next to the score chart) | Say in plain words what the numbers mean | Up to five strengths and five points to watch, important ones first | List of short statements with the company's numbers, each linked to its check or figures (§9) | Open the check behind a statement | Inputs missing: the statement is not shown (never guessed) |
| Sources page | Trace every number | One row per figure | Table: metric, value, unit, period, kind, tag, form, accession, filed, retrieved, note | Filter by kind; follow the link to the filing | Missing figures listed with the reason and the checks they block |
| Export (tier 2) | Take the work away | Download button | Excel file, two sheets: scorecard; figures and sources | Download | Disabled until a company is loaded |

Agreed visuals:

1. **Score chart** (design in `docs/design/`, SPEC 2.4.2 §3). Question: "how does the company do in each area?"
   One row of six marks per area. Passed: accent square with a tick; failed: text-colour square with a cross;
   "not assessed" (insufficient data): dashed outline; "does not apply": thin outline with a dash. Told apart by
   shape and by the label "4 passed of 5 assessed, 1 not assessed", never by colour alone; a legend says the scores
   are not a rating of the share and not advice. No radar chart.
2. **Check details**: tables, not charts. Every figure with unit and fiscal year; missing figures shown as "n/a"
   with the reason, never as 0.
3. The synthetic test company always carries a "SYNTHETIC DATA" mark.

Interface rules (§3): a unit on every input and figure; the key result at the top without scrolling; every error
message says how to fix the problem.

## MVP features (must have)

**The MVP (SPEC v2.4 §2):** the customer picks one of five companies (Coca-Cola, Apple, Nvidia, McDonald's,
Amazon), types the share price and gets the scorecard; every check opens to its rule, its figures and the filing
they come from. Order of work: the screen and the 18 checks (v0.1), then the fair value (v0.2); F8 and F9 only if
v0.2 is released before the feature freeze.

| Id | Feature | Tier | Why the customer needs it |
|---|---|---|---|
| F1 | Ticker in → header with industry, warnings and the stop rules of §10 | 1 | Knows at once whether the company is supported and what to watch |
| F2 | 18 checks: past performance, financial health, dividend (§7) | 1 | The first-pass view itself |
| F3 | Sources page: every figure with tag, filing, filing date, retrieval time, kind (§5) | 1 | The trail from number to filing that Excel copying lacks; never cut |
| F4 | Fully automatic: no figure is typed or corrected by the user; a figure that does not resolve or pass the checks is "not assessed" (§1) | 1 | The user can trust the page without checking it |
| F5 | Offline demo mode on saved data for five companies | 1 | Reliable demo; no network needed |
| F6 | Benchmarks for the industry groups of the five demo companies and for the whole US market; P4, P5, D2 switch on (§4, §9.1) | 2 | Company compared with its industry |
| F7 | Valuation: 6 checks, equity-method DCF (operating cash flow − capex from the three-year margin, cost of equity) with growth limited to 30% and decaying over 10 years, "model does not fit" rules; V4 compares the P/E with the whole US market (§7, §8) | 2 | Is the price demanding? |
| F8 | Excel export, two sheets: scorecard; figures and sources | 2, only if v0.2 is released before the freeze | Take the result away |
| F9 | Strengths and points to watch: plain-language statements from fixed rules (§9) | 3, only if v0.2 is released before the freeze | What the numbers mean, in words a retail customer understands |

Cut list if time runs short, in this order (§2): strengths and points to watch → Excel export.
F1 to F3 are never cut.

## Explicitly not in the MVP

- Watchlist comparing several companies, sensitivity table, user-adjustable growth or tax rate: dropped in SPEC
  v2.3 to keep the product simple (§2, §8.5, §8.7).
- Companies other than the five demo companies (SPEC v2.4 §2): they can be looked up and are marked as §10 says,
  but no further work goes into them; their known problems are listed as limitations in the README.
- Buy or sell recommendations, analyst forecasts, live share prices, news (§1, §2).
- Manual correction of figures or of the industry, and Porter's five forces (§2, version 2.3).
- Automatic share price from Yahoo Finance: decided 2026-11-18, typed in only (§16.2).
- Banks, insurers and real estate investment trusts (SEC industry codes 6000 to 6799); companies that do not file
  10-K reports in US dollars under US accounting rules (§2).
- Accounts, payments, a database, deployment to a server (§2, §11).
- Any AI model inside the app: every number comes from tested Python code (§1, rule 14.7).

## Data and calculations

| Data | Source | Freshness | Licence / terms checked? |
|---|---|---|---|
| Ticker → company number | SEC `company_tickers.json` | Downloaded once, cached | SEC fair access: declared User-Agent; we stay at or below 5 requests per second (SEC limit 10) (§4) |
| Company name, industry code, fiscal year end, filings | SEC `submissions` API | Per company, cached with retrieval time | Same |
| Financial statement figures | SEC `companyfacts` API (10-K and 10-K/A only) | Per company, cached with retrieval time | Same |
| Risk-free rate | FRED series `DGS10` | Average of the last five years of daily values, downloaded when needed; a dated fallback in `settings.yaml` for demo mode, a missing key or no network (SPEC §4) | FRED terms [to confirm in slice S2b] |
| Industry benchmarks and company → industry | Damodaran US datasets, January 2026 edition, extracted once to CSV (§4) | Fixed for the project | Allowed by the instructor (reported by Igor, 2026-11-18); attribution in the README; the full `indname.xls` is not committed |
| Share price | Typed in by the user (USD) | At the moment of use | – |
| Saved SEC data for the demo | Trimmed company facts for five companies in the repository | Snapshot date recorded | Committing a demo version: allowed for now (Igor, 2026-11-18) |

| Number the app shows | Formula | Units | Source of inputs |
|---|---|---|---|
| The 24 checks P1–V6 | §7, one rule each, thresholds in `settings.yaml` | Ratios stored as decimals, shown as %; amounts stored in USD, shown in USD m | Resolved SEC figures (§5, §6), benchmarks, typed price |
| Cost of equity | §8.1: risk-free + industry beta re-levered with the company's debt (limits 0.8–2.0) × 5.0% premium | % | FRED or setting, benchmarks, SEC figures, price |
| Fair value per share | §8.2–8.3 (equity method): starting free cash flow = three-year free-cash-flow margin × latest revenue; 10-year forecast with starting growth = past revenue growth limited to −10%..+30%, its gap to terminal growth halving every 2 years; terminal value; − reported minority interests; ÷ shares. Not shown when the model does not fit (§8.6) | USD per share | SEC figures (operating cash flow, capex, revenue, minority interests, shares), cost of equity |
| Strengths and points to watch | §9: 15 statements (G1–G7, W1–W8) from the checks, threshold in `settings.yaml` | Statements with the company's numbers | Check results, SEC figures |
| Area scores | Number of passes, always with the number assessed | "x passed of y assessed" | Check results |

Kinds of number (§5.2): `reported`, `derived`, `assumption`, `missing`. **Missing is never zero and never guessed.**
Known-answer examples: `docs/acceptance.md` (from SPEC Appendix A).

## Capabilities

| Capability | Needed? | Notes |
|---|---|---|
| Accounts / sign-in | no | §2 |
| Per-user saved data | no | Nothing is saved; the share price lasts for the session only |
| File uploads | no | |
| Payments | no | |
| Must be online for others | no | Runs on a laptop from the README; demo mode needs no network (§11) |

## Team and constraints

- Team: five members, areas in §12: A Igor (`BossToGo`), B Greg (`Greg3334444`), C Flo (`florian-spitzer`), D Simon
  (`Simonarmengaud`), E Emma (`EmmaRiggi`). Each member adds their own line to `docs/team.md` in their first pull
  request (§12 rule 1).
- Experience: finance students; most build through an AI coding assistant (Claude Code or Cline).
- Time: release v0.1 on Tue 24 November, v0.2 with the feature freeze on Thu 26 November at 20:00 (SPEC v2.4);
  deadline Tue 1 December 2026, 23:59, state of `main`; presentation Wed 2 December (§13.3).
- Budget: 0. Free data only; public GitHub repository (free tests and branch protection).
- Rules: `AGENTS.md`, then `SPEC.md` (hard rules §14), course AI-use disclosure in `AI-USAGE.md`, SEC fair access.
