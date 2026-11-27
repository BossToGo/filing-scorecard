## Business model

### What our demo proves

Filing Scorecard shows how a retail investor could check a company’s accounts before placing an order. In our demo, the customer selects one of five US companies and enters the share price. Someone looking at a dividend can open the check, see the cash paid and follow the link to the annual filing. As of 23 November, the release plan lists 18 checks on past performance, financial health and dividend for the first release and six further checks on valuation for the second. The demo illustrates a workflow a bank could offer beside its order screen using its own share quote. (Filing Scorecard team, 2026b)

A European retail bank is the buyer and its brokerage customers are the users; we use France as the example market. The appeal for the bank is that customers can inspect the evidence behind a score while they are considering a stock. In March 2022, AnalytixInsight announced that Morningstar research would be available on InvestoPro, the trading platform launched by MarketWall and Intesa Sanpaolo. That precedent supports the choice of distribution channel. A bank’s willingness to pay for this particular feature remains untested. (AnalytixInsight, 2022)

### What a bank would need

The five companies in our proof of concept give a bank enough scope to evaluate the workflow. Before a customer rollout, the bank would need a verified list of stocks relevant to its customers, a connection to its own quote feed, production hosting, security testing and compliance approval for displaying scores beside an order. Next steps covers implementation. The following data and licensing conditions affect the business case.

- **Industry benchmarks.** Aswath Damodaran says his published data are openly available and users who acknowledge him as the source need no separate permission from him. Through his NYU affiliation, he has access to S&P Capital IQ and Bloomberg and explains that his providers protect their company-level data. For a commercial rollout, we would budget for a feed whose licence covers the industry figures and company classifications shown to customers. The commercial licence is not priced yet. (Damodaran, 2026a)
- **Treasury rate.** FRED’s general licence is for personal, non-commercial use, and any commercial use needs the Federal Reserve Bank of St. Louis’s prior written consent (item (j) of its terms). Item (p) of its prohibitions also requires written consent to store or cache FRED content (FRED, n.d.). The design therefore does not cache the download: the app fetches the rate when needed, keeps the five-year average in memory only and falls back to a dated value saved with the app. That value comes from the US Treasury’s own public yield-curve data, not from FRED (US Department of the Treasury, n.d.). For commercial use we would seek FRED’s written clearance or take the rate from a source that permits it (Filing Scorecard team, 2026b).
- **Access to filings.** SEC filing data is public and free to use under the SEC’s fair-access rules. The project limits requests for SEC filings to five per second, below the SEC’s published maximum of ten. (Filing Scorecard team, 2026b; SEC, n.d.)
- **Scoring method.** Simply Wall St licenses its model document, `MODEL.markdown`, under CC BY-NC-SA 4.0. “NC” means non-commercial. A paid product would need Simply Wall St’s permission to reuse or adapt the licensed material, or it would need its own independently developed method. (Simply Wall St, n.d.-b)

### Build or buy

In our team’s experience, five finance students built the prototype in about two weeks using AI coding assistants. That makes an in-house prototype a credible option for a bank with engineers supporting its order screen. A production service would also require the verification and approvals described above. When a new annual report appears, someone still has to check that the app picked the right figures, investigate discrepancies and maintain the links customers rely on. When the app misreads a figure, the fix goes into the app’s rules and is tested again; no one overwrites a figure by hand (Filing Scorecard team, 2026b). The bank would own that work under an internal build. We assume one working day to verify each company’s annual filing, or €600 per stock per year. Each additional stock adds that work for an in-house team. A provider serving several banks that cover the same stock could check the filing once and share the cost across those banks. Each bank would still need its own integration and approval.

If the bank buys, we propose a **one-off integration fee plus an annual licence per bank**, with customers using the feature at no extra charge. The licence would cover an agreed set of stocks, filing updates and support. The bank could compare the provider’s offer with its own cost of covering the same companies to the same standard.

### Rough pilot costs and indicative price

We price the pilot in euros for a European bank. The estimate covers one order screen and five companies for a year, assuming the bank supplies its quote feed and production hosting. We use **€600 per working day** as a planning rate, rounded from Malt France’s published **€594/day** average for experienced Python freelancers. Malt does not specify VAT treatment alongside that figure. Our estimates exclude VAT. The days are task-based planning assumptions for a prospective pilot. We have no measured bank integration times. (Malt France, 2026)

| Work | How we estimated it | Supplier cost per pilot |
|---|---|---:|
| Connect and hand over the pilot | 4 days for the quote feed and order screen, 2 for branding, 4 for acceptance testing and handover | €6,000 once |
| Verify and update the data | 1 day per company for its annual filing review, plus 7 days across the year for benchmark updates and discrepancies | €7,200/year |
| Maintain the software and support the bank | An average of half a day per month for fixes and release tests, plus half a day a month for bank questions | €7,200/year |
| Run a supplier test server | One OVHcloud VPS-1 from €3.81/month before VAT with a 12-month commitment paid upfront (€4.49/month without) × 12 months | From €46/year |
| **Total identified costs** | **10 integration days, then 24 working days and one test server per year** | **About €20,450 in year one and €14,450 on renewal** |

The server estimate uses the advertised entry price. The bank would budget its own hosting, security review and staff time separately. (OVHcloud France, 2026)

**Indicative price.** We would charge €6,000 for integration, which covers the ten setup days, and propose an annual licence of €24,000 per bank (€30,000 in year one). The identified recurring costs come to about €14,450 a year. As a planning judgement, we would reserve roughly 40% of the fee because we still need to price data rights, legal and security work, sales and overhead. That leaves 60% for the costs in the table. Dividing €14,450 by 60% gives roughly €24,000. At that price, about €9,550 remains each year to cover those unpriced items before any profit. An extra day of support per month would use €7,200 of that amount, leaving about €2,350. Supplier quotes and measured support time would determine whether the proposed fee is viable.

### References

AnalytixInsight (2022, 1 March). *Morningstar research and market data for InvestoPro, Gemina platform now utilized by two European banks*. https://www.analytixinsight.com/news/morningstar-research-and-market-data-for-investopro-gemina-platform-now-utilized-by-two-european-banks

Damodaran, A. (2026a, January). *Data update 1 for 2026*. https://aswathdamodaran.substack.com/p/data-update-1-for-2026-the-push-and

Federal Reserve Bank of St. Louis (n.d.). *FRED terms of use*. https://fred.stlouisfed.org/legal/terms/ (accessed 24 November 2026; cited as FRED, n.d.)

Filing Scorecard team (2026b). *Project specification*, version 2.4.2. https://github.com/BossToGo/filing-scorecard/blob/main/SPEC.md

Malt France (2026, 23 November). *Baromètre des tarifs: développeur back-end Python*. https://www.malt.fr/t/barometre-tarifs/tech/developpeur-backend/developpeur-python

OVHcloud France (2026, 23 November). *VPS*. https://www.ovhcloud.com/fr/vps/

SEC (n.d.). *Webmaster frequently asked questions* (access policy). https://www.sec.gov/about/webmaster-frequently-asked-questions

Simply Wall St (n.d.-b). *Company analysis model*. https://github.com/SimplyWallSt/Company-Analysis-Model ; licence: https://github.com/SimplyWallSt/Company-Analysis-Model#license

US Department of the Treasury (n.d.). *Daily Treasury par yield curve rates*. https://home.treasury.gov/resource-center/data-chart-center/interest-rates/TextView?type=daily_treasury_yield_curve (accessed 24 November 2026).
