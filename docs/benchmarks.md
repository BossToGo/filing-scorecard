# Industry and US-market benchmarks

The app reads `app/data/benchmarks_us_2026.csv`: 36 selected cells covering six metrics
for KO, AAPL, NVDA, MCD and AMZN, plus six market cells. It never downloads data or
opens Excel at runtime. Ratios are decimals, multiples are unscaled, and both use unit `pure`.

## Sources and CSV schema

Source: Aswath Damodaran, NYU Stern, **US industry datasets, January 2026**.
The six metric workbooks show **5 January 2026** as their update date; the extract
was retrieved on **22 November 2026**. The [data catalogue](https://pages.stern.nyu.edu/~adamodar/New_Home_Page/data.html)
contains the originals. Original workbooks are not app or test dependencies; the full
company-level lookup workbook is not committed.

Each CSV row is keyed by `(ticker, metric)`; a blank ticker denotes the selected market group.
All 19 columns are required:

| Fields | Meaning |
|---|---|
| `ticker`, `industry`, `metric`, `value`, `unit`, `num_firms` | Company/group, metric, unrounded value and group size; blank `value` means missing |
| `as_of`, `retrieved_at` | Source date and timezone-aware retrieval timestamp |
| `source_file`, `source_sheet`, `source_row`, `source_column`, `source_url`, `source_sha256` | Original workbook, sheet, one-based Excel row, exact column header, URL and checksum |
| `lookup_sheet`, `lookup_row`, `lookup_exchange_ticker`, `lookup_country`, `lookup_sha256` | Company-industry match provenance; blank for market rows |

The CSV holds all 36 cell references and original workbook checksums. `settings.yaml`
records the source choices and reasons; these describe the fixed extract, not user overrides.

## Selected columns and market groups

All metric cells come from the workbook's `Industry Averages` sheet.

| Metric | Original workbook | Selected column | Definition / consumer |
|---|---|---|---|
| `unlevered_beta` | [betas.xls](https://pages.stern.nyu.edu/~adamodar/pc/datasets/betas.xls) | Unlevered beta | Ordinary unlevered beta for cost of equity, not the cash-corrected column |
| `roe` | [roe.xls](https://pages.stern.nyu.edu/~adamodar/pc/datasets/roe.xls) | ROE (unadjusted) | P4; stated net income/book equity, without capitalising R&D |
| `operating_margin` | [margin.xls](https://pages.stern.nyu.edu/~adamodar/pc/datasets/margin.xls) | Pre-tax Unadjusted Operating Margin | P5; stated operating income/revenue before tax, including stock compensation |
| `pe` | [pedata.xls](https://pages.stern.nyu.edu/~adamodar/pc/datasets/pedata.xls) | Current PE (D) | V3/V4; latest fiscal-year EPS, not forward earnings; proposed G change remains unresolved below |
| `pb` | [pbvdata.xls](https://pages.stern.nyu.edu/~adamodar/pc/datasets/pbvdata.xls) | PBV | V5; market equity/stated book equity |
| `dividend_yield` | [divfund.xls](https://pages.stern.nyu.edu/~adamodar/pc/datasets/divfund.xls) | Dividend Yield | D2; dividends/market equity, not dividend payout/earnings |

**V4 uses `Total Market (without financials)`, `pedata.xls!D104`:**
60.258294591721196, 4,822 firms. **D2 uses `Total Market`, `divfund.xls!F103`:**
0.011040267773068387, 5,994 firms, including non-payers. The other market metrics
also use `Total Market`; market group selection is metric-specific.

Current PE is an equal-weight average over profitable firms; industry ROE and margins
use aggregate amounts. Company P4 uses average opening/closing equity, so its comparison
with the source's book-equity definition is approximate. Retain source definitions and
dates in the display. **ROE limitation:** Computers/Peripherals is about **−0.17%**
(`roe.xls`, row 29; decimal −0.0017413160406024974), and Restaurant/Dining is about
**0.10%** (row 77; decimal 0.0010275118300474612). These are weak industry hurdles:
beating them alone is not strong evidence of profitability. Preserve the source values;
do not floor negative ROE at zero or substitute an R&D-adjusted or forecast figure.

## Five company-industry mappings

Source: [indname.xls](https://pages.stern.nyu.edu/~adamodar/pc/datasets/indname.xls),
sheet `By company name`; match `Exchange:Ticker` exactly and require `Country = United States`.
Read the `Industry Group` column, not `Primary Sector` or a hand-written SIC fallback.

| Ticker | Source ticker | Industry Group | Excel row | Industry firms |
|---|---|---|---:|---:|
| KO | NYSE:KO | Beverage (Soft) | 42201 | 27 |
| AAPL | NasdaqGS:AAPL | Computers/Peripherals | 2722 | 36 |
| NVDA | NasdaqGS:NVDA | Semiconductor | 29696 | 66 |
| MCD | NYSE:MCD | Restaurant/Dining | 26031 | 64 |
| AMZN | NasdaqGS:AMZN | Retail (General) | 2034 | 23 |

The lookup header has no explicit edition date: its recorded retrieval time and checksum
identify the source; no update date is invented.

Flo's [23 November 2026 review](https://github.com/BossToGo/filing-scorecard/pull/27#pullrequestreview-6018965630)
records matching all five mappings and four benchmark cells: `betas.xls!F20`,
`margin.xls!F30`, `divfund.xls!F103` and `pedata.xls!D104`. The required second-member
source reread is complete. This records Flo's evidence, not Greg's own reading or formal merge approval.

## Loader API and missing data

```python
from src.benchmarks.loader import BenchmarkDataError, load_benchmarks
benchmarks = load_benchmarks("KO")
industry_roe = benchmarks.fact("roe")          # Fact; decimal ratio
market_pe = benchmarks.market_fact("pe")       # Fact; multiple
industry_inputs = {fact.metric: fact for fact in benchmarks.industry_facts}
# Display industry, route, num_firms and lookup_source; Fact.note holds source details.
```

Unknown tickers have `industry=None`, `route="missing"` and missing industry Facts;
market Facts remain available. An absent CSV makes both unavailable and adds a warning,
without fabricating provenance. A blank source cell returns `kind="missing"`, `value=None`
while retaining its source details. Reported zeros and negative ROE stay numeric.

Duplicate rows, invalid metadata, wrong units/edition/column, inconsistent mappings or
unreadable/corrupt files raise `BenchmarkDataError`. The interface should show its restore
instruction. An unknown metric raises `KeyError`. The loader has no network or `.env` access.

From `app/`, preview with `.venv/bin/python -c 'from src.benchmarks.loader import load_benchmarks; print(load_benchmarks("KO"))'`;
run `.venv/bin/python -m pytest -q tests/unit/test_benchmarks_b.py` for loader checks.

## Unresolved: aggregate P/E column G

Flo proposes G for V3 and V4, accepting its unspecified earnings period with a disclosed
limitation. This needs explicit team/SPEC adoption; publication retains D under the
current SPEC and Igor's instruction. The original `pedata.xls`, rechecked on 23 November,
defines it in `Variables & FAQ!B9:C9` as summed market equity / summed net income
across all firms, including losses. Its checksum matches the CSV's cited workbook.
These verified values are research only; the CSV, loader and settings still use D:

| Industry/group | Cell | G value (multiple) |
|---|---|---:|
| Beverage (Soft) | G18 | 26.924737541014668 |
| Computers/Peripherals | G29 | 36.18062098268398 |
| Semiconductor | G86 | 77.4164147724544 |
| Restaurant/Dining | G77 | 36.35796947677858 |
| Retail (General) | G81 | 43.042549035410175 |
| Total Market (without financials) | G104 | 38.629311655272794 |

The FAQ specifies latest fiscal-year EPS for D (`B6`) and trailing-twelve-month EPS
for E (`B7`), but not G's earnings period. The workbook has no formulas to trace it;
the [public table](https://pages.stern.nyu.edu/~adamodar/New_Home_Page/datafile/pedata.html)
also leaves it unspecified. The [general January methodology](https://pages.stern.nyu.edu/adamodar/New_Home_Page/datacurrent.html)
says updates generally use recent trailing figures; applying that to G is an inference.
Switch only after source clarification, or an explicit team/SPEC decision accepting the
published aggregate benchmark with its period unspecified and disclosed. Do not label
G as confirmed fiscal-year or trailing P/E. Igor owns the shared SPEC change.
