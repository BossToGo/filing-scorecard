## How the bank changes

| | Today | With the scorecard |
|---|---|---|
| **Customer** | Does not read the annual reports, which are long and technical; may buy a share because the company is well known, because it is trending, or because of an article seen online. | Sees four areas (past performance, financial health, dividend, valuation) and up to 24 checks, each figure linked to the source it comes from (mostly the annual report), so it can be checked. |
| **Bank** | Has no neutral, sourced view of the company's accounts to offer next to its order screen. | Offers factual information, the same for every customer, without any investment advice. |

The tool will change not only what the customer sees but also what the bank must do to provide it. Several teams in the bank must take on new tasks. These roles are derived from our product design (they have not yet been tested in a bank).

- **Data and IT** connects the tool to the bank's own share quote (instead of the price typed by hand in the demo), updates the data, and checks each new annual report.
- **Model validation and risk** reviews the thresholds used by the checks, the tests, and the hand reconciliation of the figures. Because the calculation uses fixed rules and no AI, the same inputs always give the same result, which can be audited.
- **Compliance** confirms that the tool stays information, never advice, and approves showing scores next to the order screen.
- **Advisers and customer service** can explain what the scorecard shows when a customer asks, for example why a check says "insufficient data" or why a company shows "no dividend paid".
- **Product owner** decides where and how the tool appears in the app (next to the order screen) and which companies are shown.

So, the customer remains the only one who decides on the investment: the tool will never recommend buying or selling. What changes is that the customer now has a checking step before placing the order. They see which checks the company passes or fails and can trace each figure back to its source, although this does not guarantee a good investment decision.

The bank, for its part, has new decisions to make: which companies to show (only those that have been verified, or others too, labelled "not fully checked"), and how often to update the data. It must also decide how to handle a figure that looks wrong (our product's rule is that a figure is never corrected by hand: the reading rule in the app is corrected, then the app is tested again).

Our aim for the customer is that they understand what they are buying and can check for themselves where every figure they are shown comes from. We aim for all customers to have the same information, whether they are beginners or experienced, at no cost to them.

Our aim for the bank is to be more transparent with its customers, by offering a neutral product that is the same for everyone, and possibly to save its advisers time, which a pilot would need to measure.

A pilot would show whether these aims are met, for example by measuring how many customers open the scorecard before buying, which checks they look at most, and which questions they ask advisers most often.

The tool also has limits. It does not replace investment advice and does not adapt to each customer's needs, so the bank keeps all its usual responsibilities towards its customers. The product only covers companies that file annual reports (10-K) with the SEC; it does not work for banks, insurers or real estate investment trusts (REITs), whose accounts are built differently, so the checks do not apply to them. Finally, it is still a prototype: the demo covers five companies, which is enough to test the workflow but too few for a customer rollout (see next steps).
