# Question bank

Five likely jury questions and answers per area (SPEC §12, working rule 10). Each owner writes their area; Emma (E) edits the whole.

## A: the SEC and FRED data, missing figures and the overview (Igor)

**1. Where do your company figures come from, and how can a reader check one?**
From the SEC's EDGAR database: the figures each company files in machine-readable form with its annual report (Form
10-K), for five fiscal years. Every figure keeps its source: the label it was filed under (its "tag"), the form, the
accession number (the SEC's reference for one filing), the filing date, the period and the day we downloaded it. The
Sources tab shows one row per figure with all of these, and an open check links to the filing on sec.gov. Example:
Coca-Cola's revenue of USD 47.94 bn for 2025 is the 47,941 million on page 61 of its 10-K, accession
0001628280-26-010047; I checked it on that page myself. Each member read six figures for one of the five companies
from the printed 10-K: all 30 match the app within USD 0.5 million. Before that, we compared each figure of 30
companies with a second route in the same filing (for example earnings per share × shares against net income): 727
comparisons. They found three bugs, all fixed with tests first; the worst was Mastercard's share count, taken from a
2009/2010 cover page and about eight times too low. Any ticker other than our five shows "not fully checked".

**2. What happens when a figure is missing, or a company files it differently?**
A missing figure stays missing: never zero, never guessed. Our shared data shapes refuse a missing value stored as a
number, so the rule is enforced by the code, not only written down. A check that needs the figure shows "not assessed"
with the reason, and the overview shows "n/a" with the reason. Amazon reads "No dividend paid" only because none of
nine dividend tags has a value in any of its five years; with any trace of a dividend, the years stay missing.
Companies also file the same line under different tags, so each line item has a short list of tags tried in order
(Apple stopped using `Revenues` in 2018). If two tags give different values for the same year, the Sources tab flags
it; nothing is chosen silently. A restated figure uses the latest filing and keeps the original. On 21 November four
reviewer agents audited the project: 1 blocker and 19 major findings (nine of them on screens not built yet). The
blocker was ours: debt counted twice when a company also files its current maturities as short-term borrowings (AMD,
IBM, T-Mobile). We reproduced each data finding on 100 saved companies, wrote a failing test, then fixed it; the five
demo companies' figures did not change. A few findings stay open and are listed in our plan, for example companies
whose recent years were restated after a spin-off but not the older ones (GE); none of the 30 companies we verified is
affected.

**3. Which risk-free rate do you use, and why don't you store it?**
The average of the 10-year US Treasury yield over the last five years, from FRED (the St. Louis Fed's database, series
DGS10), downloaded when the app needs it. An average because the estimate is sensitive to the rate: on our test
company, 4.0% gives USD 20.13 a share and 5.07% gives USD 17.26, about 14% less. On 24 November the live download gave
1,247 daily values with an average of 3.9297%, the same to every digit as a separate script on FRED's public file.
FRED's terms forbid storing its data without written consent (Flo pointed this out), so the live average stays only in
the running app's memory for the day. For the offline demo, without a key or when FRED cannot be reached, the app uses
a saved, dated value from the US Treasury's own daily yields, which are public domain: 3.93% for 24 November 2021 to
20 November 2026, the same 1,247 days with the same value on every day. The Valuation tab shows the rate with its
source and period. The limit: a bank is commercial use, which needs FRED's written consent or another source (business
plan, section A).

**4. How do the overview's figures and charts get their numbers, and how did you check them?**
Every number and sentence of the overview is computed in one file, `src/overview.py`, from the same SEC figures as the
checks; the screen code only draws. So each value can be tested without the screen. On `main` since 25 and 26
November: key figures with the change on the year before, a five-year chart of revenue, net income and free cash flow
with a table view, dividend coverage, the balance sheet, filing details and the radar of checks by area. Their
expected values were worked by hand for the test company and Coca-Cola, and I checked them: for example Coca-Cola's
revenue USD 47.94 bn (+1.9% on 2024), free cash flow USD 5.30 bn (+11.7%), and free cash flow covering 60.3% of the
dividends paid. The edge rules are mine: a change from a year at or below zero is "not meaningful", negative free cash
flow shows both amounts and no percentage, and a missing figure is "n/a" with its reason and a gap in the chart. The
new charts, one section per area with the valuation first (pull request #70), are in review, not merged yet. Their
values were worked by hand for the test company, Coca-Cola and McDonald's, and I checked them with a calculator on 27
November: all match. A separate AI agent also recomputed every chart value for the five companies and the test company
from the raw 10-K entries. It found three small faults (two labels 0.01 off, a wrong unit in two subtitles, a note
that was not true for McDonald's), all fixed with tests.

**5. Why does the app read only annual reports, and what changes with the quarterly reports?**
*(Status on 27 November, before the group's answer on issue #71 at 18:00; to be updated after it.)*
The checks compare five full fiscal years, so the data layer takes figures only from the 10-K annual reports, and a
yearly figure must cover 350 to 380 days; a nine-month figure is never read as a year. A report filed more than 15
months before the data was read shows "Latest annual report is old" in the header. The cost is that an annual report
can be almost a year old. Coca-Cola's free cash flow was USD 4.7 bn in 2024 and USD 5.3 bn in 2025, two years with
one-off payments that its 10-Ks explain, and at the 25 November price of USD 97.59 our estimate was USD 31.80.
**Built, in review (pull request #72, not merged):** the data layer also reads the quarterly reports (10-Q) and gives
the last twelve months: the last annual figure + this year's year to date − last year's year to date, both from the
same 10-Q. Coca-Cola, twelve months to 2 October 2026: operating cash flow USD 16,227 m − capital expenditure USD
1,945 m = free cash flow USD 14,282 m. Amazon's 10-Q prints its own twelve-month totals, and they match the formula to
the million; I checked the hand working with a calculator. These figures are kept apart, so no existing figure, check
or warning changes, and a part that cannot be trusted (for example last year's figure restated) makes the figure
missing, never zero. **Still a proposal:** starting the valuation from these twelve months, long-run growth equal to
the risk-free rate, and Damodaran's published market risk premium (4.41%) instead of the course's 5%. That is C's
model and the group's decision; without agreement, v0.2 keeps today's method and the business plan explains the gap.

## B: benchmarks, past performance (P1–P6) and financial health (H1–H6) (Greg)

**1. Where do your industry figures come from, and why should we trust them?**
From Professor Aswath Damodaran's (NYU) US industry datasets, January 2026 edition, which are free and widely used
in teaching and practice. We use 36 figures: six measures (return on equity, operating margin, unlevered beta,
price to earnings, price to book, dividend yield) for the industries of our five companies and for the whole US
market. Each figure is stored with its workbook, sheet, row, column and a checksum of the original file, and a
second member (Flo) re-read a sample of values and the five industry groups in the original files. The app only
reads our small table, never the spreadsheets, and uses no analyst forecasts. The limit: for a real bank product
the data would need a commercial licence (business plan, next steps).

**2. Apple passes "return on equity above its industry" against an industry figure of about 0%. Isn't that too easy?**
Yes, it is a weak bar, and we say so. Damodaran's figure for Apple's industry, Computers/Peripherals, is −0.17%
(McDonald's industry is 0.10%). We show the published figure as it is: we don't raise it to zero or replace it with
another number, because that would be our own choice, not a sourced figure. The app shows the comparison and its
source, so the reader can see how low the bar was. Apple's own return on equity is about 142%.

**3. Why does McDonald's fail several debt and return checks?**
Because its shareholders' equity is negative: USD −1,791 million at the end of 2025 (its 10-K, page 41). A ratio
with negative equity is meaningless, so return on equity (P4), net debt to equity (H3) and the debt trend (H4) fail
with the note "negative equity" and no ratio is shown. This rule is in the SPEC (I decided the debt-trend case, H4,
on 23 November) and is tested on McDonald's real data.

**4. What happens when a figure is missing from the annual report?**
The check shows "not assessed" and the reason. A missing figure is never treated as zero and never guessed.
Example: Apple's interest expense is not in its SEC data for fiscal years 2024 to 2026, so interest cover (H6) is
"not assessed" for Apple. For a company outside our five, there is no industry group, so the seven checks that need
an industry figure or the industry beta are "not assessed" too.

**5. How do you know your calculations are right?**
Five ways. First, the expected results of all 12 checks on a made-up test company were worked out by hand (Simon
for ten of them, I did P4 and P5 myself and compared the rest) and signed off before the code was trusted. Second,
the comparisons use exact fractions, so a value exactly at a limit (like 40% or 5 times) never passes or fails by a
rounding error. Third, in the break-it round I broke each formula on purpose, 28 times (a wrong year, a dropped
term, swapped inputs, a changed comparison), and a test caught every one. Fourth, Flo, from another area, then
tried to break my checks independently; every case he raised is now covered by a test, the 30 benchmark values are
pinned to Damodaran's published tables, and no result changed. Fifth, I checked six of Apple's figures by hand
against its printed 10-K: all six match the app.

**6. Why do V3 and V4 (price to earnings below the industry and below the US market) pass for all five companies?**
Because the comparison figures are high in this edition. Damodaran's US market P/E, excluding financial companies,
is 60.3 (January 2026): it is an average of the P/Es of profitable companies, so many small companies with very
high P/Es pull it up. We kept this column on purpose: its earnings period is documented as the latest fiscal year,
the same basis as our own company P/E, and we did not change data after the feature freeze. So "below the market
P/E" is a low bar in this edition, and we say so openly rather than hide it.
