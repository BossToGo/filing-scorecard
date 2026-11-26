# Question bank

Five likely jury questions and answers per area (SPEC §12, working rule 10). Each owner writes their area; Emma (E) edits the whole.

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
