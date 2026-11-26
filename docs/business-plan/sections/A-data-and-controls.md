**A4 Systems view and risks**

Our app gives the customers of a European retail bank (France is our example market) a clearer picture of a company before they place a stock order. It uses 24 checks covering past performance, financial health, dividends and valuation. For the bank, the main question is whether customers can trust the figures and understand their limits. We address this through traceable sources, checks on the calculations and warnings when information is incomplete or outdated.

**A. What the app depends on**

The app uses four main inputs:

| Source | What we use | Freshness and fallback |
|---|---|---|
| SEC EDGAR | Five years of financial figures, share counts and filing dates | Updated when the company files its annual report. Saved copies are available, and the demonstration can run offline. |
| Damodaran’s industry tables | Industry betas, profitability, P/E, P/B and dividend-yield comparisons, plus market benchmarks | Updated each January; we use the January 2026 edition (Damodaran, 2026). We save the tables with their date, but they can approach a year old between updates. |
| FRED | The ten-year US Treasury rate, averaged over five years for the discount rate | The underlying series is published daily. The app downloads the five-year average when needed and keeps it only in memory, because FRED’s terms require written consent to store its data (FRED, n.d.). If FRED cannot be reached, and in the demonstration, it uses a dated five-year average computed from the US Treasury’s own daily yield-curve rates (US Department of the Treasury, n.d.). |
| Share price | The price used in valuation comparisons | Customers enter it themselves in the prototype. In a bank deployment, it would come from the bank’s quote. |

Saved copies help keep the app available during an outage. However, availability and freshness are different: a calculation can still run using information that no longer reflects current conditions.

Beyond the customers who read the scorecard, a bank deployment involves its brokerage team, which owns the order screen and the quote feed; its IT team, which hosts the app and keeps the saved data current; its compliance team, which approves showing scores beside an order and makes sure they stay information, not advice; and the data providers above. A wrong number or an outdated table therefore reaches customers through the bank’s own channel.

**B. What can go wrong**

The app could select the wrong filing entry, reporting period, unit or sign, or handle a restated figure incorrectly. A company may not report a required figure, and annual reports or industry comparisons may become outdated. External sources can also become unavailable.

There are risks beyond the data itself. The valuation model does not suit every company, customers can mistype a price, and a score shown beside an order screen may be mistaken for investment advice.

The most serious risk is an undetected error that makes a company appear financially stronger or cheaper than it is. Customers may place particular trust in information displayed by their bank, making a misleading result more likely to influence an investment decision.

**C. How we control these risks**

- **Wrong figures:** The sources page identifies the filing, accession number and line item behind each financial input. Accounting checks help identify inconsistencies, including whether assets equal liabilities plus equity within a 1% tolerance.
- **Missing figures:** Missing information stays missing and is never replaced with zero. Checks that require it show “not assessed”, with the reason.
- **Limited verification:** Team members reconciled six figures for each of the five demonstration companies by hand against their annual reports, and all 30 match. Any other ticker displays “not fully checked”.
- **Old information and outages:** Annual reports more than 15 months old display “Latest annual report is old”. Saved industry tables and rate fallbacks retain their dates. For bank deployment, these dates should be clearly visible wherever older inputs affect a result.
- **Unsuitable companies:** The app does not produce an estimate when the cash flow model does not fit.
- **Price errors:** Manual entry remains a weakness of the prototype. Using the bank’s quote and validating any remaining manual entries are proposed controls for deployment.
- **Misinterpretation:** The app avoids trading recommendations and calls its valuation result “the estimate”, never “fair value”. A test keeps advice words such as “buy”, “sell”, “undervalued”, “cheap” and “expensive” out of every check text.

Validation includes more than 1,000 automated tests, 727 cross-checks of figures against an independent route in the same filings for 30 large companies, and an independent spreadsheet model built by a team member (Filing Scorecard team, 2026).

The app uses no AI internally and no analyst forecasts. Its calculations are repeatable, but they still depend on correct inputs and appropriate assumptions. We built it with AI coding assistants, so we kept people in charge of the numbers: the expected result of every tested calculation comes from a team member’s own hand working or a cited source, never from the code’s output; every change is reviewed by a teammate before it is merged; and our AI-usage log in the repository records where the AI was wrong and how we caught it.

**D. Limits we admit**

The demonstration covers five large US companies, testing has focused on large US companies, and coverage is limited to US filers. Banks, insurers and real estate investment trusts (REITs) are outside scope. In this version, industry averages exist only for the industries of the five demonstration companies, so other tickers show “not assessed” for the industry comparisons. Annual reports may miss recent developments, while industry tables can become dated between yearly updates.

The scorecard helps customers understand reported information. It does not remove investment risk or provide investment advice.

**References**

Damodaran, A. (2026, January). *Industry datasets, January 2026 edition* (betas, margins, return on equity, P/E, P/B, dividend yields). https://pages.stern.nyu.edu/~adamodar/pc/datasets/

Federal Reserve Bank of St. Louis (n.d.). *FRED terms of use*. https://fred.stlouisfed.org/legal/terms/ (cited as FRED, n.d.)

Filing Scorecard team (2026). *Project repository: specification, tests and reconciliation records*. https://github.com/BossToGo/filing-scorecard

US Department of the Treasury (n.d.). *Daily Treasury par yield curve rates*. https://home.treasury.gov/resource-center/data-chart-center/interest-rates/TextView?type=daily_treasury_yield_curve
