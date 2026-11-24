## B. Users, market and alternatives

### Who uses it and who pays

| | Who | What they want | What they get |
|---|---|---|---|
| **User** | A retail bank's customer who is about to buy a US stock (SPEC §1) | A quick, objective first look at the company (SPEC §1) | A one-page scorecard of 24 pass/fail checks in four areas, every number traceable to its filing (SPEC §1) |
| **Buyer** | The retail bank that offers the scorecard next to its order screen (SPEC §1) | To help its customers without giving investment advice (SPEC §1) | A licensed add-on, with a one-off integration fee and an annual licence per bank; customers use it at no extra charge (section C) |

**Typical user.** In the AMF's 2024 survey of active French investors, 67% placed their orders through a
traditional bank and 47% said they look for information themselves before investing (Emma's evidence table,
items 6 and 7). US investors answered on average 5.3 of 11 investor-knowledge questions correctly (FINRA
Foundation, 2025, p. 29; evidence table item 9). The scorecard uses plain sentences, shows every figure with its
year and unit, and never says "buy" or "sell" (SPEC §3).

**Why the bank pays.** Banks already distribute third-party research to their trading customers: Morningstar
research is offered on InvestoPro, the trading platform launched by MarketWall and Intesa Sanpaolo (section C).
Whether a bank will pay for this particular feature is untested (section C).

**Out of scope.** The product covers no banks, insurers or real estate investment trusts (SPEC §2).

### How big the market is

| Indicator | Figure | Source |
|---|---|---|
| French individuals who bought shares in Q2 2025 | 688,000 people, the highest level since 2020 | AMF, 22 July 2025 |
| French individuals who bought or sold EU-listed shares in Q2 2025 | 834,000 people | AMF, 22 July 2025 |
| French adults who say they are interested in investing in shares | 34% of 2,120 people surveyed (19 September–3 October 2025), the highest since the survey began in 2017 | AMF Baromètre 2025, press release of 17 December 2025 |

**What these figures show.** In France, several hundred thousand individuals bought shares in a single quarter
of 2025, 67% of active investors place their orders through a traditional bank (evidence table item 7), and the
share of adults interested in shares is the highest since 2017. How many of these investors buy US shares:
[source needed].

**Market size.** The buyer is a bank, so the market is counted in banks, not in investors:

> Revenue potential = number of banks with an online share-order service × annual licence per bank (€24,000,
> section C).

The number of retail banks offering online share orders: [source needed]. We have not counted them yet, so we
give no total.

### Alternatives today and how we differ

| Alternative | Cost to the user | What it gives | Its limit for our user |
|---|---|---|---|
| Read the 10-K yourself (SEC EDGAR) | Free | Complete, official figures | Long and technical: 10-K reports were more than six times longer in 2014 than in 1995 (evidence table item 2), and few investors open them (item 1) |
| Free finance websites | Free | Prices, ratios, news | Reported figures are mixed with forecasts, and the source of a number is rarely shown (SPEC §1) |
| Social media and influencers | Free | Opinions | Unchecked; 26% of US investors use influencer recommendations (evidence table item 3a) |
| General AI chatbots | [source needed] | A written answer on request | In our team's own experience building this product, AI assistants made mistakes in figures and calculations that our tests caught (`AI-USAGE.md`) |
| Simply Wall St | Free plan with limits; paid Premium and Unlimited plans (prices not shown on its public plans page, checked 24 November 2026) | Company analysis with a fixed set of pass/fail checks (SPEC §1) | A subscription the user pays for; its public model is the inspiration for our checks (SPEC §1) |
| Morningstar Investor | USD 249 a year (US price at launch, Morningstar press release of 16 June 2022; the current price may differ) | Morningstar research and portfolio tools (same press release) | A subscription the user pays for; our product uses no analyst forecasts (SPEC §1) |

**How we differ.** Filing Scorecard combines three things: it is free for the user (section C), it is shown in
the bank's order screen (SPEC §1), and every number links to its filing, reporting line and filing date, with a
figure that cannot be read shown as "not assessed", never guessed (SPEC §1, §5). It uses no forecasts and no AI
model at run time, so the same company always gets the same scorecard (SPEC §1).

**Limit.** The MVP covers five large US companies, each reconciled by hand against its 10-K (SPEC §2, v2.4).

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
