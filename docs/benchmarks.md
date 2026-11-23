# Member B: industry benchmarks and handoff

## Publication refresh, 23 November 2026

Greg explicitly requested publication of the prepared fixes. Refreshed against latest main `cbd6957`:
**527 tests passed**, with real `.env` access and external networking guarded. The current main's
non-benchmark settings and other members' log entries are preserved. This updates draft PR #27;
source re-reading, Greg's Explain-back and teammate approval remain prerequisites for merge.

## Stress-audit repair, 22 November 2026

A blank cell now retains its source column, workbook, source-cell identifier and retrieval timestamp,
while its value remains `None` and its kind remains `missing`. An entirely absent source file still
has no fabricated provenance. A new regression was observed failing before the fix; the complete
S4 suite now passes **526 tests** (30 benchmark tests). No benchmark value, source selection,
setting or company-to-industry match changed. This repair is local and awaits its own commit approval;
the previously published S4 draft is PR #27. Human second-member source review remains pending.

Owner A handoff: record this test-first source-trace repair against S4/AC8/E17 in the plan and
acceptance evidence. B has not edited A-owned plan, acceptance or architecture documents.

Status on 22 November 2026: Greg approved the S4 commit, branch publication and draft pull request in chat.
A second member's source re-reading, teammate approval and green GitHub checks remain required for merge.
This is not a claim that S4 is already on main.

Refreshed for the S9 handoff on latest `main` (`ab86bf0`, including #19, #21 and #24): **525 tests passed**.
Only B's source files, benchmark settings section and AI-use entries were brought into this separate
`b/S4-benchmarks-ready` checkout; newer A changes were retained. A read-only check of S7 PR #23
(`de41bdc`) passed all **531 tests**. The reviewed dividend module was also exercised with latest-main
demo data and S4 Facts for all five companies: Amazon's nil/no-dividend state and Coca-Cola's cash-flow
dividend failure behaved as specified, with zero external network attempts. C still owns S9 activation.

## Dataset and definitions

The MVP uses only Coca-Cola, Apple, Nvidia, McDonald's and Amazon, plus the specified US market rows.
**V4's Current PE excludes financials** (SPEC §7); **D2's dividend yield uses Total Market**, including
non-payers. The market group is metric-specific, rather than one group for every ratio.
It does not build the optional all-company lookup, generated SIC fallback or extraction script.
The app reads `app/data/benchmarks_us_2026.csv`; it never opens Excel or downloads benchmarks at runtime.
The table is long-form: one company/metric per row, and an empty ticker for the whole market. It contains
36 selected cells, not the full company-level workbook. Ratios are decimals; multiples also use unit `pure`.

Initial verification: 484 tests passed in the complete offline suite after review. Three read-only reviewer agents
(code, tests, security) found one shared minor issue: corrupt text could escape the documented error type.
A new regression was seen failing, then decoding/CSV/file-read errors were wrapped in `BenchmarkDataError`.
All three re-reviewed the fix and reported pass. The code/test reviewers independently compared all 36
cells, the five matches and source checksums to the original Excel files with no differences. Those AI
checks do **not** replace the required human second-member source reading.

The later grading audit caught a missed requirement: the initial market P/E cell included financials.
Two new tests failed first (the correct original cell and the required settings metadata), then V4's input
was corrected to `pedata.xls`, `Industry Averages`, **D104**, `Total Market (without financials)`, Current PE
**60.258294591721196**, **4,822 firms**. D2 remains `divfund.xls` F103, Total Market dividend yield.
No existing test expectation or student-verified answer was changed. Source-column/group/row choices are
now recorded with reasons in B's `benchmarks` section of `settings.yaml`, as §7 requires; tests check
them against the extract. These are documentation of the frozen source choices, not a runtime override.
Security re-review passed. Final code/test rechecking of this correction uses same-conversation source
comparison because the separate reviewer agents reached their usage limit; it is not called independent.
Final evidence after that correction: **486** tests passed in this slice; **548** passed in the combined
B checkout. The network-blocked five-company API journey still passes. These are automated/API checks,
not the pending human source sign-off or screen verification.

Source: [Damodaran's data page](https://pages.stern.nyu.edu/~adamodar/New_Home_Page/data.html).
The six US industry workbooks identify **5 January 2026** as their update date. They were downloaded once
on 22 November 2026. Every CSV row preserves its workbook, sheet, one-based Excel row, exact column,
URL, source date, retrieval timestamp, number of firms and SHA-256 checksum. Files are in temporary
analysis storage only; they are not dependencies for tests or the app.

| Metric key | Original workbook | Exact column | Used for / reason |
|---|---|---|---|
| `unlevered_beta` | `betas.xls` | Unlevered beta | C's cost of equity. The ordinary unlevered column, as named in SPEC §4; not the cash-corrected column or a company regression beta. |
| `roe` | `roe.xls` | ROE (unadjusted) | P4. Uses stated net income and book equity, without capitalising R&D. |
| `operating_margin` | `margin.xls` | Pre-tax Unadjusted Operating Margin | P5. Matches the company's stated operating-income/revenue calculation, before tax and with stock compensation included. |
| `pe` | `pedata.xls` | Current PE | C's V3 uses the company industry; V4 uses Total Market (without financials), D104. The latest-fiscal-year earnings basis matches FY0. No forward estimates. |
| `pb` | `pbvdata.xls` | PBV | C's V5. Market equity relative to stated book equity. |
| `dividend_yield` | `divfund.xls` | Dividend Yield | C's D2 uses the whole-market row, including firms that pay no dividend. |

These are industry statistics, not interchangeable estimates of an individual company's ratios. In
particular, Current PE is an average over profitable firms, while ROE and margins use aggregate amounts.
Company P4 uses average opening/closing equity; Damodaran's industry ROE uses his stated book-equity
definition. The comparison is approximate and must retain its definition and date on screen. Apple's
industry ROE is negative in this source. It is preserved, not changed to zero or replaced by the R&D-adjusted
column. No analyst forecast column is extracted.

The provider's [usage notes](https://pages.stern.nyu.edu/~adamodar/New_Home_Page/datahistory.html)
describe the timing, definitions and limitations. `docs/architecture.md` records Igor's report of instructor
permission (18 November); SPEC §16 still lists the original question. A should reconcile that document status.
The README attribution belongs to E; suggested wording: “Industry statistics and classifications: Aswath
Damodaran, NYU Stern, US industry datasets, January 2026. Source definitions and retrieval details are in
docs/benchmarks.md and the benchmark CSV.”

## Industry lookup inspected

`indname.xls` has three sheets: `By industry`, `By company name`, `By geography`. Each has 48,157 rows
including the header and eight columns: `Company Name`, `Exchange:Ticker`, `Industry Group`,
`Primary Sector`, `SIC Code`, `Country`, `Broad Group`, `Sub Group`. Tickers include their exchange prefix;
SEC industry codes are present. The five selected matches require `Country = United States` and an exact
ticker suffix. Neither the broad primary sector nor a hand-written SIC mapping is substituted.

| Company | Source ticker | Industry group | `By company name` row | Firms in industry |
|---|---|---|---|---|
| KO | NYSE:KO | Beverage (Soft) | 42201 | 27 |
| AAPL | NasdaqGS:AAPL | Computers/Peripherals | 2722 | 36 |
| NVDA | NasdaqGS:NVDA | Semiconductor | 29696 | 66 |
| MCD | NYSE:MCD | Restaurant/Dining | 26031 | 64 |
| AMZN | NasdaqGS:AMZN | Retail (General) | 2034 | 23 |

The lookup workbook itself has no explicit edition date in the inspected header. Its retrieval date and
checksum are recorded, rather than inventing a separate update date. The entire workbook is not committed.

## Independent source review still needed

A second teammate should open the original workbooks, select `Industry Averages`, and record the cells below.
These values were extracted by Codex from the originals, not personally re-read by Greg or a second member.

| Original cell | Meaning | Extracted value (decimal) | Human reviewer/date |
|---|---|---|---|
| `betas.xls`, F20 | Beverage (Soft), unlevered beta | 0.5556711918551647 | pending |
| `margin.xls`, F30 | Computers/Peripherals, pre-tax unadjusted operating margin | 0.22484874696685003 | pending |
| `divfund.xls`, F103 | Total Market, dividend yield | 0.011040267773068387 | pending |
| `pedata.xls`, D104 | Total Market (without financials), Current PE (additional check after audit) | 60.258294591721196 | pending |

The same reviewer must re-read **all five** industry matches in the lookup table above (SPEC v2.4 S4).
Do not sign off by comparing the CSV with itself. Open the linked source workbooks:
[betas](https://pages.stern.nyu.edu/~adamodar/pc/datasets/betas.xls),
[margins](https://pages.stern.nyu.edu/~adamodar/pc/datasets/margin.xls),
[ROE](https://pages.stern.nyu.edu/~adamodar/pc/datasets/roe.xls),
[P/E](https://pages.stern.nyu.edu/~adamodar/pc/datasets/pedata.xls),
[P/B](https://pages.stern.nyu.edu/~adamodar/pc/datasets/pbvdata.xls),
[dividends](https://pages.stern.nyu.edu/~adamodar/pc/datasets/divfund.xls),
[industry lookup](https://pages.stern.nyu.edu/~adamodar/pc/datasets/indname.xls).

## API for C and D

```python
from src.benchmarks.loader import load_benchmarks, BenchmarkDataError

benchmarks = load_benchmarks("KO")
industry_roe = benchmarks.fact("roe")          # Fact, value is a decimal
market_pe = benchmarks.market_fact("pe")       # Fact, value is a multiple
industry_inputs = {fact.metric: fact for fact in benchmarks.industry_facts}
# Display: benchmarks.industry, benchmarks.route, benchmarks.num_firms,
# benchmarks.lookup_source; each Fact carries the source details in note.
```

For an unlisted ticker, `industry` is `None`, `route` is `missing`, and industry facts are `missing` with
reasons. Whole-market facts remain available for D2 and V4. A missing CSV makes both kinds unavailable with
a warning. A blank value is missing; a reported zero or negative ROE stays numeric. Duplicate rows, wrong
units, another source edition, an undocumented source column or invalid source metadata raise
`BenchmarkDataError` explaining how to restore the extract. D should catch this error and show the reason.
The loader does not read `.env` and has no network imports or new runtime dependencies.

Preview from `app/`:

```sh
.venv/bin/python -c 'from src.benchmarks.loader import load_benchmarks; b=load_benchmarks("KO"); print(b.industry, b.route, b.num_firms); print(b.fact("roe")); print(b.market_fact("pe"))'
.venv/bin/python -m pytest -q tests/unit/test_benchmarks_b.py
```

The existing main page is still the walking skeleton; B has not edited D's interface. This slice's journey is
the local data-to-benchmark API, including an unknown ticker and missing-file path. There is no screen change
to inspect. App integration is a handoff to D, not a browser check performed by B.

## Owner A's document updates

B has not edited A-owned product, plan, architecture, acceptance or synthetic-fixture files. Suggested updates
for A after review:

- S4: “implementation and source-based tests prepared; second-member three-cell and five-match review pending”.
- AC8/E17: loader handles the MVP matches and unknown industry; screen and C's checks remain unverified.
- Progress log: selected 36 source cells; January 2026 edition, original cell/lookup references retained;
  tests first (missing loader import observed), then passing benchmark tests; the V4 market-row correction
  and explicit source settings were also tested first; human review pending.
- Record Greg's 22 November request to delegate routine Part B implementation, testing and preparation.
  It does not authorise personal calculation sign-off, risk acceptance, another owner's edits or future commits.
- Reconcile older product/acceptance descriptions (manual overrides, five forces, old valuation and release dates)
  with SPEC v2.4. These discrepancies predate B's work; SPEC remains the source of truth.

## Remaining Part B work

- S0: [PR #22](https://github.com/BossToGo/filing-scorecard/pull/22), visible as Greg's contribution;
  own Explain-back, teammate review and merge pending.
- S0c: Greg must personally recalculate P1-P6/H1-H6, and the statements if the optional S12 is retained.
  The expected-value gate must remain locked until A records his genuine sign-off.
- S5/S6: prepare logic and rule/property tests; Appendix A known-answer acceptance waits for S0c.
- S15: Greg personally reads Apple's six figures, page numbers and line labels. A template is in
  `app/tests/reconciliation/README.md`; no Apple figures have been certified by B yet.
- S9: B's part is providing benchmark facts to P4/P5. Dividend and valuation code remains C's area.
- S12: conditional on the v0.2 release before feature freeze and A's `Statement` contract. No premature
  optional implementation or shared-contract change.
- S18: a teammate reviews B's work and Greg reviews other areas. AI review does not substitute for his own
  required GitHub reviews.
- S20: B drafts users, market and alternatives for E to integrate; five likely B questions for the shared bank.
  E owns those destination files. No market size, customer validation or personal explanation is invented.

## Published review evidence

At Greg's request, Codex posted a [technical review on PR #5](https://github.com/BossToGo/filing-scorecard/pull/5#issuecomment-7081781992).
It records 71 passing fixture/reconciliation tests, confirms B's expected values remain locked, and gives A
the verified stale acceptance criteria to correct. It explicitly identifies the AI assistance and does not
claim Greg's personal calculation sign-off or approve the pull request.
