## B. Users, market and alternatives

### Who uses it and who pays

Filing Scorecard has two customers, as in any business-to-business-to-consumer product:

| | Who | What they want | What they get |
|---|---|---|---|
| **User** | A retail customer of a bank who is about to buy shares of a large US company through the bank's online order screen | A quick, objective first look at the company's accounts, without hours of reading and without a sales pitch | A one-page scorecard of 24 pass/fail checks in four areas, each one traceable to the figure in the company's annual report (10-K) |
| **Buyer** | The bank (its online brokerage or retail investment unit) | To help customers invest with more information while giving no investment advice, and to keep them on its own platform | A licensed add-on displayed next to its order screen, priced per bank (section C) |

**Typical user.** Our users invest their own money, choose their own stocks and place their orders themselves.
In the AMF's 2024 survey of active French investors, 67% placed their orders through a traditional bank and 47%
said they look for information themselves before investing (Emma's evidence table, items 6 and 7). Many of them
do not have the training to read accounts: US investors answered on average 5.3 of 11 investor-knowledge
questions correctly (FINRA Foundation, 2025, p. 29; evidence table item 9). The scorecard is built for this
person: it uses plain sentences, shows every figure with its year and unit, and never says "buy" or "sell".

**Why a bank pays rather than the investor.** The user meets the scorecard at the moment of the order, inside the
bank's app. A bank already distributes third-party research to its brokerage customers in this way: Morningstar
research is offered on InvestoPro, the trading platform launched by MarketWall and Intesa Sanpaolo (section C).
The bank benefits from better-informed customers and a stronger platform. Whether a bank will pay for this
particular feature is untested; the pilot in section C is designed to find out.

**Who is not a user.** Professional analysts already have paid terminals and read filings in full. Our product
is not built for them, and it covers no banks, insurers or property companies (SPEC §2).

### How big the market is

We start with one country, France, because the evidence on its retail investors is public and our team studies
there; the same logic applies to any European bank that lets its customers buy US shares.

| Indicator | Figure | Source |
|---|---|---|
| French individuals who bought shares in Q2 2025 | 688,000 people, the highest level since 2020 | AMF, 22 July 2025 |
| French individuals who bought or sold EU-listed shares in Q2 2025 | 834,000 people | AMF, 22 July 2025 |
| French adults who say they are interested in investing in shares | 34% of 2,120 people surveyed (19 September–3 October 2025), the highest since the survey began in 2017 | AMF Baromètre 2025, press release of 17 December 2025 |

**What these figures mean for us.** Hundreds of thousands of people in France alone buy shares every quarter,
two thirds of active investors place their orders through a traditional bank (evidence table item 7), and
interest in shares is at its highest since 2017. This is our own reading of these figures, not a forecast: the
number of share buyers who need simple, reliable information is large and, on the AMF's figures, rising. We do not know how many of these investors buy US shares: [source needed].

**Market size, estimated.** The buyer is a bank, so the market is counted in banks, not in investors:

> Revenue potential = number of banks with an online share-order service × annual licence per bank (€24,000,
> section C).

The number of French and European retail banks offering online share orders is [source needed]; we have not
counted them yet, so we give no total. As an illustration only: each bank signed at the proposed licence brings
€24,000 a year, and 10 banks would bring €240,000 a year. This is not a forecast.

### Alternatives today and how we differ

| Alternative | Cost to the user | What it gives | Its limit for our user |
|---|---|---|---|
| Read the 10-K yourself (SEC EDGAR) | Free | Complete, official figures | Long and technical: 10-K reports were more than six times longer in 2014 than in 1995 (evidence table item 2), and few investors open them (item 1) |
| Free finance websites and broker app summaries | Free | Prices, ratios, news | Reported figures are mixed with analyst forecasts, and the source of a number is rarely shown (SPEC §1) |
| Social media and influencers | Free | Fast opinions | Unchecked; 26% of US investors use influencer recommendations (evidence table item 3a) |
| General AI chatbots | Free or low monthly fee | A written summary on request | Can state wrong figures with confidence and does not show which filing a number came from; the same question can give a different answer |
| Simply Wall St (subscription) | Free plan with limits; paid Premium and Unlimited plans (prices not shown on its public plans page, checked 24 November 2026) | Visual company analysis with pass/fail checks | Paid by the investor, outside the bank's order screen; its model is the public inspiration for our checks (SPEC §1) |
| Morningstar Investor (subscription) | USD 249 a year (US price at launch, Morningstar press release of 16 June 2022; the current price may differ) | Analyst research, ratings and fair values | Paid by the investor; relies on analysts' forecasts and opinions, which our product deliberately does not use |

**Our position.** Filing Scorecard is the only option in this table that is (1) free to the user, (2) inside the
bank's order screen at the moment of decision, and (3) traceable: every number links to the filing, the
reporting line and the filing date, and a figure that cannot be read is shown as "not assessed", never guessed.
It uses no forecasts and no AI model at run time, so the same company always gets the same scorecard and every
result can be checked by hand. That is what makes it acceptable for a bank to show next to an order button.

**What competitors do better.** Subscription services cover thousands of companies worldwide and have years of
history; our MVP covers five large US companies, reconciled by hand against their 10-Ks. Growing coverage while
keeping every figure verified is the main work after the MVP (section E, next steps).

### Sources (accessed 24 November 2026 unless stated)

- Evidence table items 1, 2, 3a, 6, 7 and 9: see Emma's section (E), "Problem and evidence", with full references.
- Intesa Sanpaolo / InvestoPro precedent: see Flo's section (C), "Business model".
- AMF (22 July 2025). "L'activité des investisseurs particuliers actifs sur les actions au plus haut depuis 2020".
  https://www.amf-france.org/fr/actualites-publications/actualites/lactivite-des-investisseurs-particuliers-actifs-sur-les-actions-au-plus-haut-depuis-2020
- AMF (17 December 2025). "Baromètre AMF 2025 : en quête d'autonomie, les Français sont nombreux à recourir à
  l'intelligence artificielle au moment d'investir", press release.
  https://www.amf-france.org/fr/actualites-publications/communiques/communiques-de-lamf/barometre-amf-2025-en-quete-dautonomie-les-francais-sont-nombreux-recourir-lintelligence
- Simply Wall St. Plans. https://simplywall.st/plans
- Morningstar (16 June 2022). "Morningstar Investor Connects Individual Investors' Portfolio Management to
  Morningstar Research", press release.
  https://newsroom.morningstar.com/news/news-details/2022/Morningstar-Investor-Connects-Individual-Investors-Portfolio-Management-to-Morningstar-Research/default.aspx
- Project specification, SPEC.md §1 and §2: https://github.com/BossToGo/filing-scorecard/blob/main/SPEC.md
