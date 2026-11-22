**A4 Systems view and risks**

Our app gives bank customers a clearer picture of a company before they place a stock order. It uses 24 checks covering past performance, financial health, dividends and valuation. For the bank, the main question is whether customers can trust the figures and understand their limits. We address this through traceable sources, checks on the calculations and warnings when information is incomplete or outdated.

**A. What the app depends on**

The app uses four main inputs:

| Source | What we use | Freshness and fallback |
|---|---|---|
| SEC EDGAR | Five years of financial figures, share counts and filing dates | Updated when the company files its annual report. Saved copies are available, and the demonstration can run offline. |
| Damodaran’s industry tables | Industry betas, profitability, P/E and P/B comparisons, plus market benchmarks | Generally updated each January. We save the tables with their date, but they can approach a year old between updates. |
| FRED | The ten-year US Treasury rate, averaged over five years for the discount rate | The underlying series is published daily. The app downloads the data when needed and uses a dated fallback if the source is unavailable. |
| Share price | The price used in valuation comparisons | Customers enter it themselves in the prototype. In a bank deployment, it would come from the bank’s quote. |

Saved copies help keep the app available during an outage. However, availability and freshness are different: a calculation can still run using information that no longer reflects current conditions.

**B. What can go wrong**

The app could select the wrong filing entry, reporting period, unit or sign, or handle a restated figure incorrectly. A company may not report a required figure, and annual reports or industry comparisons may become outdated. External sources can also become unavailable.

There are risks beyond the data itself. The valuation model does not suit every company, customers can mistype a price, and a score shown beside an order screen may be mistaken for investment advice.

The most serious risk is an undetected error that makes a company appear financially stronger or cheaper than it is. Customers may place particular trust in information displayed by their bank, making a misleading result more likely to influence an investment decision.

**C. How we control these risks**

- **Wrong figures:** The sources page identifies the filing, accession number and line item behind each financial input. Accounting checks help identify inconsistencies, including whether assets equal liabilities plus equity within a 1% tolerance.
- **Missing figures:** Missing information stays missing and is never replaced with zero. Checks that require it display “insufficient data”.
- **Limited verification:** The app has a verified set of 30 companies. Other tickers display “not fully checked”.
- **Old information and outages:** Annual reports more than 15 months old display “old annual report”. Saved industry tables and rate fallbacks retain their dates. For bank deployment, these dates should be clearly visible wherever older inputs affect a result.
- **Unsuitable companies:** The app does not produce a fair value when the cash flow model does not fit.
- **Price errors:** Manual entry remains a weakness of the prototype. Using the bank’s quote and validating any remaining manual entries are proposed controls for deployment.
- **Misinterpretation:** The app avoids trading recommendations and presents fair value as an estimate based on model assumptions.

Validation includes more than 380 automated tests, a second-source check covering 727 figures, and an independent spreadsheet model built by a team member. Before submission, the five team members will also reconcile 30 figures directly with the filings.

The app uses no AI internally and no analyst forecasts. Its calculations are repeatable, but they still depend on correct inputs and appropriate assumptions.

**D. Limits we admit**

Testing has focused on large US companies, and coverage is limited to US filers. Banks, insurers and real estate companies are outside scope. Annual reports may miss recent developments, while industry tables can become dated between yearly updates.

The scorecard helps customers understand reported information. It does not remove investment risk or provide investment advice.
