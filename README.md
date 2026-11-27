# Filing Scorecard

A one-page first look at a US company, built only from its annual reports filed with the SEC (Form 10-K). It is
made for a retail bank to show its customers next to the order screen, when they are about to buy a US stock. You
pick a company and type the share price, and you get 24 pass/fail checks in four areas (past performance,
financial health, dividend, valuation). Every figure can be traced to its filing.

**Information, not advice.** The app gives no recommendation. It uses no analyst forecasts, no live prices and no AI:
every number comes from tested Python code. The scores are not a rating of the share. A figure that cannot be read or
does not pass the checks is shown as "not assessed" with the reason, never as zero and never guessed.

## What you see

1. **Input bar:** one of the five demo companies (Coca-Cola KO, Apple AAPL, Nvidia NVDA, McDonald's MCD, Amazon
   AMZN) or another ticker; the share price in USD, the only figure you type; the demo-mode switch.
2. **Header:** company, industry, fiscal year end, date of the latest 10-K, retrieval date, and the warnings "not
   fully checked" or "old annual report" when they apply.
3. **Overview:** key figures for the latest fiscal year with the change on the year before, a radar of the four
   areas, and charts over five years with a table view.
4. **Score chart:** six marks per area ("4 passed of 5 assessed, 1 not assessed"), with the failed checks listed
   next to it.
5. **One tab per area:** each check opens to its rule in plain words, the formula, the input figures with their
   fiscal years, and a link to the filing. The Valuation tab shows the estimate per share against the typed
   price, and how the estimate was built.
6. **Sources tab:** every figure with its SEC tag, form, accession number, filing date, retrieval time and kind
   (reported, derived, assumption, missing).

Without a share price, the valuation area and the dividend-yield check show "insufficient data". Strengths and
points to watch, and an Excel export, were planned but not built in this version (`docs/plan.md`, S12 and S13).
They are in the business plan's next steps (`docs/business-plan/sections/E-next-steps.md`).

## Install (once)

You need Git and Python 3.11 to 3.14 (newer versions are not tested). The app uses its own environment in
`app/.venv` and never changes your Anaconda or system Python.

**Windows (PowerShell):**

```powershell
git clone https://github.com/BossToGo/filing-scorecard.git
cd filing-scorecard\app
py -0p                     # lists your Pythons; use one from 3.11 to 3.14 in the next line
py -3.13 -m venv .venv
.venv\Scripts\python -m pip install -r requirements.txt
copy .env.example .env
```

**Mac (Terminal):**

```bash
git clone https://github.com/BossToGo/filing-scorecard.git
cd filing-scorecard/app
python3 --version          # must be 3.11 to 3.14
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
cp .env.example .env
```

For live SEC data, open `app/.env` in an editor and put **your own** name and e-mail in `SEC_USER_AGENT` (the SEC
requires it). Never commit `.env` and never paste it into a chat. Demo mode and the tests need nothing in it.
If `python3` or `py` is too old, see `app/README.md` for using Anaconda's Python.

## Run

From the `app` folder:

```bash
.venv\Scripts\python -m streamlit run main.py      # Windows
.venv/bin/python -m streamlit run main.py          # Mac
```

Open http://localhost:8501, pick a company, type a share price (e.g. 70.00), and press **Show scorecard**.

## Demo mode

Demo mode is on by default. It reads saved SEC data for the five demo companies (`app/evidence/demo/`, downloaded
on 2026-11-18), so it needs no network and no `.env`. It uses the saved risk-free rate, labelled as an assumption.
Switch it off to fetch the latest filings live, or to look up another ticker (this needs `SEC_USER_AGENT`).

## Data used and their terms

- **SEC EDGAR** (`company_tickers.json`, `submissions`, `companyfacts`; 10-K and 10-K/A only): public data under
  the SEC's fair-access rules. The app declares a User-Agent and stays at 5 requests per second (the limit is 10).
- **FRED**, series DGS10 (10-year Treasury yield): the risk-free rate is the average of the last five years. The
  key is optional and personal, and use is personal and non-commercial only: a bank would need FRED's written
  consent. *This product uses the FRED® API but is not endorsed or certified by the Federal Reserve Bank of St.
  Louis.*
- **US Treasury**, Daily Treasury Par Yield Curve Rates (public domain): the saved fallback rate, because FRED's
  terms forbid storing FRED data.
- **Aswath Damodaran**, NYU Stern, US industry datasets, January 2026 edition: industry benchmarks and unlevered
  beta. Their use was allowed by the instructor. Each value in `app/data/benchmarks_us_2026.csv` names its source
  file, sheet, row and column.

Full citations and links: `app/README.md`, "Data sources".

**Saved or synthetic data:** the demo snapshot of the five companies; the benchmark table; the dated fallback rate
(`app/settings.yaml`). The tests also use **Synthetic Co.**, an invented company (SPEC Appendix A), marked
"SYNTHETIC DATA" wherever it appears.

## Assumptions

All values are in `app/settings.yaml`, each with its reason. The method is in `SPEC.md` §5 to §8.

| Assumption | Value |
|---|---|
| Currency | USD only; companies reporting in another currency are not supported |
| Units | Amounts stored in USD and shown in USD m (or bn); ratios stored as decimals and shown as % |
| Fiscal year | FY0 is the latest fiscal year in the latest 10-K; checks use FY-4 to FY0; a year lasts 350 to 380 days, so 53-week years count |
| Risk-free rate | Five-year average of daily DGS10 values; without FRED, 3.93% (Treasury, 2021-11-24 to 2026-11-20) |
| Equity risk premium | 5.0%, the course's session 5 convention. **To revisit after #71** |
| Beta | Industry unlevered beta, re-levered with the company's debt and market value, limited to 0.8 to 2.0 |
| Tax rate | 21% US federal rate, used only to re-lever the beta |
| Starting free cash flow | (Operating cash flow − capital expenditure) as a margin of revenue over the last three fiscal years, × FY0 revenue. **To revisit after #71** |
| Growth | Starts at the revenue growth FY-4 to FY0, limited to −10% to +30%; its gap to long-run growth halves every 2 years over 10 years |
| Long-run growth | The lower of the risk-free rate and 2.5%. **To revisit after #71** |
| Equity value | Discounted cash flows and terminal value, minus reported minority interests, ÷ shares; valuation date the end of FY0 |

## Limitations

- **Not supported:** banks, insurers and real estate investment trusts (SEC industry codes 6000 to 6799), and
  companies that do not file 10-K reports in USD under US accounting rules. The app says "not supported" and why.
- **Other tickers are outside the MVP.** They can be looked up and are marked "not fully checked". Known problems:
  debt filed under unusual tags, and years restated after a spin-off.
- **Changed fiscal year end:** a company that changed its fiscal year end keeps its older years (flagged
  `FY_CHANGE` on the sources page), so one year-on-year step can be longer than twelve months. The four-year
  revenue growth can then be slightly overstated. None of the five demo companies is affected.
- **Gaps in the filings:** Apple's SEC data has no interest expense after fiscal 2023, and Amazon pays no
  dividend, so the checks that need these figures say why they are not assessed.
- **Benchmarks:** fixed at Damodaran's January 2026 edition. His industry return on equity is close to zero for
  Computers/Peripherals (−0.17%) and Restaurant/Dining (0.10%), so the return-on-equity check sets almost no bar
  there.
- **The typed price moves the estimate:** it sets the market value of equity used to re-lever the beta.
- **Not modelled:** net borrowing, cash beyond the interest it earns, stock-based pay, preferred dividends, minority
  interests that are not tagged as such, and state taxes.
- **Dated data:** the demo snapshot, the benchmarks and the fallback rate are not refreshed automatically.

## How it was checked

- **Automated tests** (pytest and Hypothesis): 1,382 pass on `main` (27 November). They run on every pull request on
  Linux and Windows with Python 3.11 and 3.14, with the network blocked. Run them with
  `.venv\Scripts\python -m pytest` (Windows) or `.venv/bin/python -m pytest` (Mac) from `app`.
- **Expected values worked out by hand**, never taken from the app: each check's owner recalculated their rows of
  the synthetic company of SPEC Appendix A (`docs/acceptance.md`).
- **Hand reconciliation:** each member read six figures of one demo company from the printed 10-K. All 30 match the
  app, from the same filing (`app/tests/reconciliation/`).
- **Break-it rounds and reviews:** deliberate errors planted in the formulas, and a test added for each one that no
  test caught (`docs/testing.md`). A teammate approves every pull request, and read-only reviewer agents
  reviewed the larger slices.

## AI use

The team built the app with AI coding assistants (Claude Code, and Codex for member B). We wrote the specification
first, planned each slice, wrote the tests first and had reviewer agents check the work. The app itself contains no
AI. One mistake that was caught: the assistant's first debt rule counted a missing current portion of debt as zero
(McDonald's FY2023: USD 37,501 m instead of 39,345 m). A reviewer agent found it, and the rule was rewritten and
tested against McDonald's balance sheets. All entries are in [`AI-USAGE.md`](AI-USAGE.md).

## Credits

**Team** (`docs/team.md`):

- A, Igor Willms: repository, CI, SEC data layer, demo snapshot.
- B, Greg: industry benchmarks, past-performance and financial-health checks.
- C, Florian Spitzer: dividend and valuation checks, valuation engine.
- D, Simon Armengaud: interface, theme, data-quality gates, app tests.
- E, Emma Riggi: plain-language texts, README, business plan, slides, `AI-USAGE.md`.

**Method:** the pass/fail checks per area and parts of the valuation (ten years of growth slowing towards the
long-run rate, the beta limits, no estimate without positive free cash flow) are adapted from the publicly documented
Simply Wall St Company Analysis Model, https://github.com/SimplyWallSt/Company-Analysis-Model (its model document is
licensed CC BY-NC-SA 4.0). The cost of equity follows the conventions of the course's session 5 (the build-up and
the 5% equity risk premium). The thresholds, the texts, the screen and the code are the team's own.

**Data:** SEC EDGAR; FRED, Federal Reserve Bank of St. Louis; US Department of the Treasury; Aswath Damodaran, NYU
Stern.

## Repository

`app/` is the application (developer notes in `app/README.md`). `SPEC.md` is the specification. `docs/` holds the
product, architecture, plan, acceptance and testing documents, and the business plan.
`AI-USAGE.md` is the AI disclosure.
