# Hand reconciliation (slice S15)

Each member reads six figures of one demo company **by hand** from its latest 10-K and saves them here as
`<TICKER>.yaml`. `test_reconciliation.py` then checks that the app reads the same figures, from the same filing,
within USD 0.5 million (SPEC §13.2, S15). This is the independent check of the data layer: a person reading the
filing, not a program. Emma (E) coordinates; the format and the test are Igor's (A).

**Optional seventh figure:** `capital_expenditure` ("Purchases of property, plant and equipment" on the cash flow
statement, written as the positive amount) when a check owner needs it, compared with the app in the same way.
Coca-Cola has it, for D6 (Flo's S7 review). The other files need only the six.

| Member | Company | File | Status |
|---|---|---|---|
| A, Igor | Coca-Cola | `KO.yaml` | done, 6 of 6 match, plus capital expenditure (7 of 7) |
| B, Greg | Apple | `AAPL.yaml` | to do |
| C, Flo | Nvidia | `NVDA.yaml` | done, 6 of 6 match (PR #30) |
| D, Simon | McDonald's | `MCD.yaml` | done, 6 of 6 match (PR #38) |
| E, Emma | Amazon | `AMZN.yaml` | done, 6 of 6 match (PR #50) |

## Rules

- **Every figure is confirmed by you, on the page.** Read the figures yourself, or let a tool extract them first:
  that is allowed only if you then confirm every value and line name on the printed page yourself, and say so in
  `how_read` and `AI-USAGE.md` (as `KO.yaml` does). An unconfirmed tool reading never counts.
- **Never change a figure to match the app.** If the test fails, recheck the page; if your reading is right, the
  app has a bug: tell Igor (A) and open an issue. That is the point of the check (SPEC §13.5, R6).
- Branch `<member>/S15-reconciliation-<ticker>`, e.g. `b/S15-reconciliation-aapl`; one file per pull request.

## Steps

1. **Find the filing.** `https://www.sec.gov/cgi-bin/browse-edgar?action=getcompany&CIK=<CIK>&type=10-K` (CIK:
   Apple 0000320193, Nvidia 0001045810, McDonald's 0000063908, Amazon 0001018724). Take the **latest 10-K**; its
   fiscal year is the app's latest year (FY0).
2. **Note the accession number** from the filing index (e.g. `0001628280-26-010047`), the filing date and the
   fiscal year end (the date of the latest balance sheet: Apple and Nvidia do not end in December).
3. **Open the main document** and find the income statement, the balance sheet and the cash flow statement. For
   each figure, write the value, the page number **printed on the page** (not the browser's or PDF viewer's page)
   and the line's name exactly as printed.

| Figure | Where | Watch out |
|---|---|---|
| `revenue` | Income statement | The total (net sales, net revenues); the latest year's column |
| `operating_income` | Income statement | – |
| `net_income` | Income statement | The line for the company's own shareholders, not the one including non-controlling interests |
| `total_assets` | Balance sheet | At the fiscal year end |
| `operating_cash_flow` | Cash flow statement | The total of the operating activities section |
| `dividends_paid` | Cash flow statement, financing | Written as a **positive** number (the filing shows it in parentheses) |

**Units:** write USD millions. If a statement is in thousands, divide by 1,000 and say so in a `note`.
**No such line** (e.g. a company that pays no dividend): `value: null`, the page of the statement you checked,
`line_in_filing: none`, and a `note` saying what the filing shows. The test then expects the app to show none too.
For dividends, "none" in the app means the nil of plan Q1 (a value of 0 labelled "treated as nil", pull request
#21), so the customer sees "no dividend paid" (SPEC §7, D1); for any other figure it means missing, never 0. The nil
only applies when the filing shows no dividend under any tag: a payer that uses another tag name is never shown as
paying none.

## Template

```yaml
company: AAPL
read_by: Greg (B)
date_read: 2026-11-22
how_read: Read by hand from the printed pages of the 10-K below.
accession: 0000000000-26-000000
filed: 2026-10-31
fiscal_year_end: 2026-09-26
document: https://www.sec.gov/Archives/edgar/data/...
unit: USD millions
figures:
  revenue:             {value: , page: , line_in_filing: ""}
  operating_income:    {value: , page: , line_in_filing: ""}
  net_income:          {value: , page: , line_in_filing: ""}
  total_assets:        {value: , page: , line_in_filing: ""}
  operating_cash_flow: {value: , page: , line_in_filing: ""}
  dividends_paid:      {value: , page: , line_in_filing: ""}
```

The accession, dates and document link in the template are placeholders: replace every one with what your filing
shows. `KO.yaml` is a filled-in example.

## Run the check

`cd app` then `.venv/bin/python -m pytest tests/reconciliation` (Windows: `.venv\Scripts\python -m pytest
tests/reconciliation`). The test names the file, the figure, your value and page, and the app's value and source.
