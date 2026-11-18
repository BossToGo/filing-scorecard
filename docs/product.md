# Product: Filing Scorecard (working title, SPEC 16.7 [to confirm])

Status: agreed on 2026-11-18 by Igor (member A) on the basis of `SPEC.md` version 2; confirmed by the group
through the review of the pull request that adds this file.

**`SPEC.md` has the final say.** This file summarises it for the assistant and the team. If the two disagree,
`SPEC.md` wins and this file is corrected by pull request. Section numbers below (§) point to `SPEC.md`.

## Problem and customers

- **Customer:** an analyst at a small asset manager, wealth adviser, family office or investment club with no
  Bloomberg or FactSet licence (§1).
- **Problem today:** the first look at a US company takes hours of copying figures from 10-K reports into Excel,
  is done differently by each analyst, and leaves no trail from a number back to its filing (§1).
- **Success looks like:** typing a ticker gives a one-page scorecard in under a minute (seconds in demo mode),
  and every figure on it can be traced to its filing, tag and filing date on the sources page.

## Main user journey

1. The analyst opens the app on a laptop and sees the input bar: ticker, share price (USD, optional), demo mode.
2. They type a ticker (and, for valuation, the share price they want to test).
3. The app fetches the company's SEC filings (or reads saved data in demo mode), runs the data-quality gates
   (§10), and shows the header, the score chart and the 24 checks (§3, §7).
4. They open a check to see the rule, formula, input figures with fiscal years and the link to the filing; they
   override a figure if they disagree, and the scores recalculate at once.
5. They read the valuation detail and the five forces panel, check the sources page, and download the Excel file.

## Screens and visuals

Look: a dashboard with one score chart, expandable checks and tables. Used on a phone: no (laptop demo).
Visual references: none. We do **not** use Simply Wall St's name, the word "snowflake", their radar-chart design
or their text (§1, rule 14.16).

| Screen | Purpose | The user sees first | Cards / charts / tables (unit, period) | The user can | Loading / empty / error |
|---|---|---|---|---|---|
| Scorecard (main page) | First-pass view of one company | Header: company, industry and how it was found, fiscal year end, latest 10-K date, retrieval date, warnings; then the score chart | Score chart (4 areas, passes out of 6); 24 checks, each expandable to rule, formula, inputs (USD m, fiscal year) and filing link | Type ticker and share price (USD); switch demo mode; open a check; override a figure | Loading: "Fetching SEC filings…". Unknown ticker, unsupported company (bank, insurer, REIT, non-USD, non-10-K), source unreachable: a message that says how to fix it (§3) |
| Valuation detail (tier 2, on the main page) | Show how the fair value was built | Fair value per share against the share price (USD) | Tables: cost of capital build-up (%), 5-year forecast (USD m), growth implied by the price next to actual growth (%), sensitivity grid (USD per share) | Override the forecast ratios and g | No share price: the whole area shows "insufficient data, enter a share price" |
| Five forces panel (tier 3, on the main page) | Quantitative indicators per force | Five rows: force, suggested rating | Table of indicators with units, company against industry | Confirm or override each rating, with a note | Benchmark missing: "insufficient data" with the reason |
| Sources page | Trace every number | One row per figure | Table: metric, value, unit, period, kind, tag, form, accession, filed, retrieved, note | Filter by kind; follow the link to the filing | Missing figures listed with the reason and the checks they block |
| Export (tier 2) | Take the work away | Download button | Excel file, three sheets: report, figures, sources | Download | Disabled until a company is loaded |

Agreed visuals:

1. **Score chart** [design details to confirm by member D]. Question: "how does the company do in each area?"
   Horizontal bars, one per area, on a fixed 0 to 6 scale. Passes filled; fails, "insufficient data" and "not
   applicable" told apart by pattern and by a text label such as "4 of 5 assessed, 1 with insufficient data"
   (§3), never by colour alone. No radar chart.
2. **Check details**: tables, not charts. Every figure with unit and fiscal year; missing figures shown as "n/a"
   with the reason, never as 0.
3. **Sensitivity grid**: a table of fair value per share (USD) for cost of capital ± 1 point against terminal
   growth ± 1 point (steps of 0.5); the base case marked in text.
4. The synthetic test company always carries a "SYNTHETIC DATA" mark.

Interface rules (§3): a unit on every input and figure; the key result at the top without scrolling; every error
message says how to fix the problem.

## MVP features (must have)

| Id | Feature | Tier | Why the customer needs it |
|---|---|---|---|
| F1 | Ticker in → header with industry, warnings and the stop rules of §10 | 1 | Knows at once whether the company is supported and what to watch |
| F2 | 18 checks: past performance, financial health, dividend (§7) | 1 | The first-pass view itself |
| F3 | Sources page: every figure with tag, filing, filing date, retrieval time, kind (§5) | 1 | The trail from number to filing that Excel copying lacks; never cut |
| F4 | Manual override of any figure, instant recalculation | 1 | The analyst stays in control of disputed figures |
| F5 | Offline demo mode on saved data for five companies | 1 | Reliable demo; no network needed |
| F6 | Industry lookup and benchmarks; P4, P5, D2 switch on (§4, §9.1) | 2 | Company compared with its industry |
| F7 | Valuation: 6 checks, DCF, reverse DCF, sensitivity (§7, §8) | 2 | Is the price demanding? |
| F8 | Excel export: report, figures, sources | 2 | Fits the analyst's existing workflow |
| F9 | Five forces panel with suggested rating and analyst override (§9) | 3 | Structured view of the industry |

Cut list if time runs short, in this order (§2): watchlist → five forces panel → sensitivity table → Excel export.
F1 to F3 are never cut.

## Explicitly not in the MVP

- Watchlist comparing several companies: stretch, only after release v0.3 (§2).
- Buy or sell recommendations, analyst forecasts, live share prices, news (§1, §2).
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
| Risk-free rate | FRED series `DGS10` | Latest value; or typed into `settings.yaml` | FRED terms [to confirm in slice S8] |
| Industry benchmarks and company → industry | Damodaran US datasets, January 2026 edition, extracted once to CSV (§4) | Fixed for the project | Allowed by the instructor (reported by Igor, 2026-11-18); attribution in the README; the full `indname.xls` is not committed |
| Share price | Typed in by the user (USD) | At the moment of use | – |
| Saved SEC data for the demo | Trimmed company facts for five companies in the repository | Snapshot date recorded | Committing a demo version: allowed for now (Igor, 2026-11-18) |

| Number the app shows | Formula | Units | Source of inputs |
|---|---|---|---|
| The 24 checks P1–V6 | §7, one rule each, thresholds in `settings.yaml` | Ratios stored as decimals, shown as %; amounts stored in USD, shown in USD m | Resolved SEC figures (§5, §6), benchmarks, typed price |
| Cost of capital | §8.1: risk-free + re-levered industry beta × 5.0% premium; cost of debt from filings; 21% tax | % | FRED or setting, benchmarks, SEC figures, price |
| Fair value per share | §8.2–8.3: 5-year forecast at growth g, terminal value with return on new capital = cost of capital, bridge to equity, ÷ shares | USD per share | As above |
| Growth implied by the price | §8.4: bisection on g in −20% to +50%; "no solution" if none | % per year | As above |
| Area scores | Number of passes, always with the number assessed | "x of y assessed" | Check results |

Kinds of number (§5.2): `reported`, `derived`, `assumption`, `missing`. **Missing is never zero and never guessed.**
Known-answer examples: `docs/acceptance.md` (from SPEC Appendix A).

## Capabilities

| Capability | Needed? | Notes |
|---|---|---|
| Accounts / sign-in | no | §2 |
| Per-user saved data | no | Overrides last for the session only |
| File uploads | no | |
| Payments | no | |
| Must be online for others | no | Runs on a laptop from the README; demo mode needs no network (§11) |

## Team and constraints

- Team: five members, areas in §12: A Igor (`BossToGo`), B Greg (`Greg3334444`), C Flo (`florian-spitzer`), D Simon
  (`Simonarmengaud`), E Emma (`EmmaRiggi`). Each member adds their own line to `docs/team.md` in their first pull
  request (§12 rule 1).
- Experience: finance students; most build through an AI coding assistant (Claude Code or Cline).
- Time: tier releases on Sun 22, Wed 25 and Thu 26 November (feature freeze 20:00); deadline Tue 1 December 2026,
  23:59, state of `main`; presentation Wed 2 December (§13.3).
- Budget: 0. Free data only; public GitHub repository (free tests and branch protection).
- Rules: `AGENTS.md`, then `SPEC.md` (hard rules §14), course AI-use disclosure in `AI-USAGE.md`, SEC fair access.
