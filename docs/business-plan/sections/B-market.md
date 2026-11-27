## Users, market and alternatives

### Who uses it and who pays

| | Who | What they want | What they get |
|---|---|---|---|
| **User** | A customer of a European retail bank who is about to buy shares in a US company | A quick, objective first look at the company before placing the order | A one-page scorecard of pass/fail checks, every number traceable to the company's annual report (see The solution) |
| **Buyer** | The European retail bank that offers the scorecard next to its order screen | To help its customers without giving investment advice | A licensed add-on: a one-off integration fee and an annual licence per bank; customers use it at no extra charge (see Business model) |

**Typical user.** We use France as the example market. In a 2024 survey of active French investors, 67% placed
their orders through a traditional bank, and 47% said they look for information themselves before investing
(AMF, 2024). Problem and evidence describes how much financial knowledge these investors have.

**Why the bank pays.** There is a precedent for a bank's trading platform offering third-party research: in March
2022, AnalytixInsight announced that Morningstar research would be available on InvestoPro, the trading platform
launched by MarketWall and Intesa Sanpaolo (AnalytixInsight, 2022). The announcement does not say who pays for
it, and whether a bank will pay for this particular feature is untested (see Business model).

**Out of scope.** The product covers no banks, insurers or real estate investment trusts (REITs; see The solution).

### How big the market is

Example market: France.

| Indicator | Figure | Source |
|---|---|---|
| French individuals who bought shares in Q2 2025 | 688,000 people, the highest level since 2020 | AMF (2025a) |
| French individuals who bought or sold EU-listed shares in Q2 2025 | 834,000 people | AMF (2025a) |
| French adults who say they are interested in investing in shares | 34% of 2,120 people surveyed (19 September–3 October 2025), the highest since the survey began in 2017 | AMF (2025b) |

**What these figures show.** In France, several hundred thousand individuals bought shares in a single quarter
of 2025, most active investors place their orders through a traditional bank, and the share of adults interested
in shares is the highest since 2017. How many of these investors buy US shares is not known from these sources.

**Market size.** These figures count investors, but the buyer is a bank, so the market is counted in banks:

> Revenue potential = number of banks with an online share-order service × annual licence per bank (€24,000,
> see Business model).

We have not yet counted the European retail banks that offer online share orders, so this plan gives no market
total.

### Alternatives today and how we differ

| Alternative | Cost to the user | What it gives | Its limit for our user |
|---|---|---|---|
| Read the 10-K yourself (SEC EDGAR) | Free | Complete, official figures | Long and technical, and rarely read (see Problem and evidence) |
| Free finance websites | Free | Prices, ratios, news | In our team's own experience, they rarely show which filing a figure comes from |
| Social media and influencers | Free | Opinions | Unchecked (see Problem and evidence) |
| General AI chatbots | Free and paid versions exist (team's own observation) | A written answer on request | Already used: 11% of French adults turn to AI for information before investing, measured for the first time in 2025 (AMF, 2025b). In our team's own experience, an answer does not come with the filing behind each figure |
| Simply Wall St | Free plan with limits; paid Premium and Unlimited plans (prices not shown on its public plans page, checked 24 November 2026) (Simply Wall St, n.d.-a) | Company analysis with a fixed set of pass/fail checks, documented in its public model (Simply Wall St, n.d.-b) | A subscription the user pays for |
| Morningstar Investor | USD 249 a year (US price at launch; the current price may differ) (Morningstar, 2022) | Morningstar research and portfolio tools (Morningstar, 2022) | A subscription the user pays for; our product uses no analyst forecasts (see The solution) |

**How we differ.** Filing Scorecard combines three things: it is free for the user (see Business model), it is shown in
the bank's order screen, and every number links to its filing, reporting line and filing date, with a figure
that cannot be read shown as "not assessed", never guessed (see Systems view and risks). It uses no forecasts and no AI
model when it runs, so the same company always gets the same scorecard (see The solution).

**Limit.** The prototype covers five large US companies. Before submission, six figures of each company are
checked by hand against its 10-K, 30 in all (see Systems view and risks).

### References

AMF (2024, October). "Nouveaux investisseurs, nouvelles pratiques d'investissement", *Lettre de l'Observatoire de l'épargne de l'AMF*, n° 58. Autorité des marchés financiers. https://www.amf-france.org/fr/actualites-publications/publications/observatoire-de-lepargne/lettres-de-lobservatoire-de-lepargne/lettre-de-lobservatoire-de-lepargne-de-lamf-ndeg58-octobre-2024 ; PDF: https://www.amf-france.org/sites/institutionnel/files/private/2025-06/loe-58_juin-2025.pdf (accessed 21 November 2026).

AMF (2025a, 22 July). *L'activité des investisseurs particuliers actifs sur les actions au plus haut depuis 2020*. Autorité des marchés financiers. https://www.amf-france.org/fr/actualites-publications/actualites/lactivite-des-investisseurs-particuliers-actifs-sur-les-actions-au-plus-haut-depuis-2020

AMF (2025b, 17 December). *Baromètre AMF 2025 : en quête d'autonomie, les Français sont nombreux à recourir à l'intelligence artificielle au moment d'investir*, press release. Autorité des marchés financiers. https://www.amf-france.org/fr/actualites-publications/communiques/communiques-de-lamf/barometre-amf-2025-en-quete-dautonomie-les-francais-sont-nombreux-recourir-lintelligence (accessed 24 November 2026).

AnalytixInsight (2022, 1 March). *Morningstar research and market data for InvestoPro, Gemina platform now utilized by two European banks*. https://www.analytixinsight.com/news/morningstar-research-and-market-data-for-investopro-gemina-platform-now-utilized-by-two-european-banks

Morningstar (2022, 16 June). *Morningstar Investor connects individual investors' portfolio management to Morningstar research*, press release. https://newsroom.morningstar.com/news/news-details/2022/Morningstar-Investor-Connects-Individual-Investors-Portfolio-Management-to-Morningstar-Research/default.aspx

Simply Wall St (n.d.-a). *Plans*. https://simplywall.st/plans (accessed 24 November 2026).

Simply Wall St (n.d.-b). *Company analysis model*. https://github.com/SimplyWallSt/Company-Analysis-Model ; licence: https://github.com/SimplyWallSt/Company-Analysis-Model#license
