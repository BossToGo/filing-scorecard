# Saved demo data (slice S0b)

Real SEC data for the five demo companies (SPEC §13.2), saved so that nobody needs the network: demo mode, every
test and every member's work run on these files. **Never edit them by hand** (SPEC §11, `evidence/`).

| Folder | Company | Files |
|---|---|---|
| `KO/` | The Coca-Cola Company | `submissions.json`, `companyfacts.json`, `provenance.json` |
| `AAPL/` | Apple Inc. | same |
| `NVDA/` | NVIDIA Corp. | same |
| `MCD/` | McDonald's Corp. | same |
| `AMZN/` | Amazon.com, Inc. | same |
| `JPM/` | JPMorgan Chase & Co. (a bank: must be refused) | `submissions.json`, `provenance.json` |
| `tickers.json` | The six entries of the SEC ticker list | with `tickers.provenance.json` |

- **Source:** SEC EDGAR (`www.sec.gov/files/company_tickers.json`, `data.sec.gov/submissions/`,
  `data.sec.gov/api/xbrl/companyfacts/`), downloaded on 2026-11-18. Each `provenance.json` records the address,
  the retrieval time (UTC), the size and SHA-256 checksum of the raw download, and how it was trimmed. Request
  headers (`SEC_USER_AGENT`) are never stored.
- **Trimmed, structure unchanged:** company facts keep only entries from Form 10-K, 10-K/A, 10-Q and 10-Q/A;
  cover-page (`dei`) facts keep every form. Submissions list only the 10-K and 10-K/A filings. The JSON layout is
  the SEC's own, so the resolver reads saved and live data the same way. The fiscal years come from the 10-K entries
  alone (SPEC §5.3.1); the 10-Q entries serve only the latest figures (`CompanyData.recent`, slice S2c).
- **Re-trimmed on 2026-11-26 (slice S2c, issue #71 item 1):** until then the company facts kept the 10-K entries
  only. They were trimmed again, without the network, from the very downloads of 2026-11-18 kept in
  `app/.cache/sec/`: `.venv/bin/python scripts/fetch_demo_data.py --retrim-from-cache .cache/sec` (run from `app/`)
  refuses a raw file whose size or SHA-256 checksum differs from its `provenance.json`, then rewrites only
  `companyfacts.json` and the "trimmed" line of its record. The checksums, retrieval times and submissions files are
  unchanged; every demo company's annual figures and warnings are identical with and without the 10-Q entries
  (`app/tests/integration/test_twelve_months_demo.py`). The five files grew from about 12 MB to about 33 MB.
- **Made by:** `app/scripts/fetch_demo_data.py` (run from `app/`; needs `SEC_USER_AGENT` in `app/.env`). Raw
  downloads stay in `app/.cache/sec/` (git-ignored). Use is allowed for the demo "for now" (decision log,
  2026-11-18, SPEC §16.4).
- **Checked by:** `app/tests/integration/test_demo_evidence.py` and `test_twelve_months_demo.py` (network blocked).

## What the real files show (2026-11-18)

Structure, as SPEC §4 asks to check before writing a parser: `companyfacts.json` = `{cik, entityName, facts:
{dei, us-gaap: {Tag: {label, description, units: {USD | shares | USD/shares | pure: [entries]}}}}}`; each entry
has `start` (flows only), `end`, `val`, `accn`, `fy`, `fp`, `form`, `filed` and sometimes `frame`.
`submissions.json` has `cik`, `name`, `sic`, `sicDescription`, `fiscalYearEnd` ("MMDD") and `filings.recent` as
aligned columns (`accessionNumber`, `filingDate`, `reportDate`, `form`, `primaryDocument`, ...).

Known answer: Coca-Cola FY2025 revenue (`Revenues`, 2025-01-01 to 2025-12-31) = USD 47,941,000,000, accession
0001628280-26-010047, filed 2026-02-20, exactly as in session 5, slide 30.

Traits confirmed (SPEC §13.2): Apple has 53-week years (annual periods of 370 days); Nvidia's cover-page share
count jumps from 2.5 to 24.4 billion with the 10-for-1 split of 2024; McDonald's equity is negative
(USD −1,791 million at 2025-12-31); Amazon reports no dividend tag at all. Amazon also split (20-for-1, 2022:
cover-page shares 0.5 → 10.2 billion), a second split company for rule §5.3.8.

Tag findings for slices S2 and S3 (latest annual period end found with the SPEC §6 tags):

| Line item | Finding | Consequence |
|---|---|---|
| Revenue | Apple's `Revenues` stops in 2018, then `RevenueFromContractWithCustomerExcludingAssessedTax`; Amazon has no `Revenues` | The fallback list must be tried **per fiscal year**, not once per company |
| Financial debt | Coca-Cola's `LongTermDebtNoncurrent`, `LongTermDebtCurrent`, `LongTermDebt` stop at 2023-12-31, `ShortTermBorrowings` at 2022; only `CommercialPaper` reaches 2025 | With the SPEC tags, KO debt is missing for FY2024–FY2025 and its valuation would be blocked: find the tags KO uses now (plan Q11) |
| Capital expenditure | `PaymentsToAcquirePropertyPlantAndEquipment` stops in 2012 (Nvidia) and 2016 (Amazon) | Another capex tag is needed for both (plan Q11) |
| Interest expense | Apple's `InterestExpense` stops at FY2023; Nvidia moves to `InterestExpenseNonoperating` | Apple's H6 would be "insufficient data" from FY2024 unless another tag is found |
| Dividends paid | McDonald's uses `PaymentsOfDividendsCommonStock` (the fallback works); Amazon has none | Q1: "missing" versus "no dividend paid" |
| Total liabilities | No `Liabilities` tag for Coca-Cola, McDonald's, Amazon | The SPEC's derivation (assets − total equity) is needed |
| Debt current part | `DebtCurrent` exists for Nvidia and McDonald's; Nvidia's equals `LongTermDebtCurrent` (999 million) | Supports Q5: avoid double counting |
