## Systems view and risks

For the bank, the main question is whether customers can trust the figures and understand their limits, which we address through traceable sources, checks on the calculations and warnings when information is incomplete or outdated.

### What the app depends on

The app uses four main inputs:

| Source | What we use | Freshness and fallback |
|---|---|---|
| SEC EDGAR | Five years of financial figures, share counts and filing dates | Updated when the company files its annual report. Saved copies are available, and the demonstration can run offline. |
| Damodaran’s industry tables | Industry betas, profitability, P/E, P/B and dividend-yield comparisons, plus market benchmarks | Updated each January; we use the January 2026 edition (Damodaran, 2026b). We save the tables with their date, but they can approach a year old between updates. |
| FRED | The ten-year US Treasury rate, averaged over five years for the discount rate | The underlying series is published daily. The app downloads the daily 10-year yields and computes the five-year average itself, kept in memory only, as FRED’s terms require (see Business model). If FRED cannot be reached, and in the demonstration, it uses a dated five-year average computed from the US Treasury’s own daily yield-curve rates (US Department of the Treasury, n.d.). |
| Share price | The price used in valuation comparisons | Customers enter it themselves in the prototype. In a bank deployment, it would come from the bank’s quote. |

Saved copies help keep the app available during an outage. However, availability and freshness are different: a calculation can still run using information that no longer reflects current conditions.

In a bank deployment, a wrong number or an outdated table reaches customers through the bank’s own teams and the data providers above (see How the bank changes).

### What can go wrong

The app could select the wrong filing entry, reporting period, unit or sign, or handle a restated figure incorrectly. A company may not report a required figure, and annual reports or industry comparisons may become outdated. External sources can also become unavailable.

There are risks beyond the data itself. The valuation model does not suit every company, customers can mistype a price, and a score shown beside an order screen may be mistaken for investment advice.

The most serious risk is an undetected error that makes a company appear financially stronger or cheaper than it is. Customers may place particular trust in information displayed by their bank, making a misleading result more likely to influence an investment decision.

### How we control these risks

- **Wrong figures:** The sources page identifies the filing, accession number and line item behind each financial input. Accounting checks help identify inconsistencies, including whether assets equal liabilities plus equity within a 1% tolerance.
- **Missing figures:** Missing information stays missing and is never replaced with zero. Checks that require it show “not assessed”, with the reason.
- **Limited verification:** Team members reconciled six figures for each of the five demonstration companies by hand against their annual reports, and all 30 match. Any other ticker displays “not fully checked”.
- **Old information and outages:** Annual reports more than 15 months old display “Latest annual report is old”. Saved industry tables and rate fallbacks retain their dates. For bank deployment, these dates should be clearly visible wherever older inputs affect a result.
- **Unsuitable companies:** The app does not produce an estimate when the cash flow model does not fit.
- **Price errors:** Manual entry remains a weakness of the prototype. Using the bank’s quote and validating any remaining manual entries are proposed controls for deployment.
- **Misinterpretation:** The app avoids trading recommendations and calls its valuation result “the estimate”, never “fair value”. A test keeps advice words such as “buy”, “sell”, “undervalued”, “cheap” and “expensive” out of every check text.

Validation includes more than 1,000 automated tests, 727 cross-checks of figures against an independent route in the same filings for 30 large companies, and an independent spreadsheet model built by a team member (Filing Scorecard team, 2026a).

The app uses no AI internally and no analyst forecasts. Its calculations are repeatable, but they still depend on correct inputs and appropriate assumptions. We built it with AI coding assistants, so we kept people in charge of the numbers: the expected result of every tested calculation comes from a team member’s own hand working or a cited source, never from the code’s output; every change is reviewed by a teammate before it is merged; and our AI-usage log in the repository records where the AI was wrong and how we caught it.

### Limits we admit

The demonstration covers five large US companies, testing has focused on large US companies, and coverage is limited to US filers. Banks, insurers and REITs are outside scope. In this version, industry averages exist only for the industries of the five demonstration companies, so other tickers show “not assessed” for the industry comparisons. Annual reports may miss recent developments, while industry tables can become dated between yearly updates.

The scorecard helps customers understand reported information. It does not remove investment risk or provide investment advice.

### References

Damodaran, A. (2026b, January). *Industry datasets, January 2026 edition* (betas, margins, return on equity, P/E, P/B, dividend yields). https://pages.stern.nyu.edu/~adamodar/pc/datasets/ (accessed 22 November 2026).

Federal Reserve Bank of St. Louis (n.d.). *FRED terms of use*. https://fred.stlouisfed.org/legal/terms/ (accessed 24 November 2026; cited as FRED, n.d.)

Filing Scorecard team (2026a). *Project repository: specification, tests and reconciliation records*. https://github.com/BossToGo/filing-scorecard

US Department of the Treasury (n.d.). *Daily Treasury par yield curve rates*. https://home.treasury.gov/resource-center/data-chart-center/interest-rates/TextView?type=daily_treasury_yield_curve (accessed 24 November 2026).
