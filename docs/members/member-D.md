# Member D: Simon (@Simonarmengaud)

**You own:** `app/main.py`, `app/ui/` (except `texts.yaml`, which is Emma's), including the strengths and points
to watch on screen, the theme file `app/.streamlit/config.toml`, `app/src/gates.py`, `app/tests/app/`, the `gates` section of `app/settings.yaml`. **Backup:** A, Igor (you
review Igor's PRs first, Igor reviews yours; you run the release check if Igor cannot). **Reconciliation company:** McDonald's (MCD).

## Your slices, in order

| When | Slice | Done when (SPEC §13.2) |
|---|---|---|
| Wed 18 | Accept the invitation; your `docs/team.md` PR (steps in `docs/team.md`) | Merged |
| Thu 19 | **Sign-off for S0c:** recalculate AC3 of `docs/acceptance.md` (the tier 1 scores of the synthetic company) | Your sign-off comment on PR #5 |
| Thu 19 → Sun 22 | S10: input bar, header, score chart (one bar of six blocks per area), expandable checks, sources page, theme file; start on the synthetic company, then on real data after A's S2. Branch `d/S10-interface` | `streamlit run` works; an app test opens the synthetic company and finds a known score |
| Sat 21–Sun 22 | S11: gates (SPEC §10) and error messages, including E4 (SEC unreachable), branch `d/S11-gates` | One test per stop and warn case |
| Sat 21–Sun 22 | S14 with A: demo mode on the five saved companies | App runs with the network off |
| Mon 23–Wed 25 | S10b: share price input; valuation detail: cost of equity build-up with each assumption and its source, the 10-year free cash flow table, fair value against the price, the company's actual growth and, for fast growers, the "cautious estimate" line (SPEC §8.3); the reasons when the model does not fit (§8.6); industry with route and number of firms. No sensitivity table, no implied growth, no user inputs | App test finds the fair value of the synthetic company |
| Mon 23–Wed 25 | "Download Excel" button that calls Emma's export (S13, `app/src/export.py`) | The button downloads the file Emma's test checks |
| Thu 26 | S12 with B: the strengths and points to watch next to the score chart, from Greg's `app/src/highlights.py` with Emma's texts (SPEC §9: up to five of each, important first); S17: end-to-end app test | The synthetic company shows the statements of SPEC Appendix A; S17 passes twice in a row on GitHub |
| Sat 21–Sun 29 | **Business plan section:** the solution, with screenshots, in `docs/business-plan/sections/D-solution.md` (Emma, E, assembles the plan; prompt in `docs/members/README.md`) | Draft by Sun 22; final by Sun 29 |
| Fri 27–Sun 29 | S18, break-it round: a member from another area reviews your code read-only; you break each of your formulas once on purpose and record each break and the test that caught it in `docs/testing.md` | Every finding is a failing test or a written dismissal |

**Slice prompt** (replace the slice, sections and branch):

> /build-feature I am member D, working on slice [S10] of SPEC.md. Read AGENTS.md, docs/members/member-D.md,
> SPEC.md sections [3, 10 and 11], docs/product.md ("Screens and visuals"), docs/plan.md and the [AC1–AC6, V1–V4]
> rows of docs/acceptance.md. Use the branch [d/S10-interface] from the latest main. Use the design-interface
> skill for the screens. Plan this slice only, name the files you will touch and the tests you will write first,
> and wait for my go-ahead. I will give you the expected values. Do not change files outside my folders.

Sections per slice: S10 → §3, §5.1, §11; S11 → §10; S10b → §3, §8 (especially 8.6 and 8.7), §9.1; S12 → §3,
§9; S17 → §15.

**How to sign off (S0c):** recalculate your rows on paper or in Excel, then post a review comment on
[PR #5](https://github.com/BossToGo/filing-scorecard/pull/5): the rows, the date, how you calculated, and any
difference. A records it under `sign_off` in `app/tests/fixtures/synthetic_co.yaml`, with a link to your
comment. Until then the fixture refuses your rows with the error `NotSignedOff`, naming you.

## Rules for your area

- **Real data:** the saved SEC files in `app/evidence/demo/<TICKER>/companyfacts.json` (PR #6: KO, AAPL, NVDA,
  MCD, AMZN; JPM must be refused). Read `app/evidence/demo/README.md` first: what the files contain and the
  traits already confirmed. Never download anything in your code or tests.
- **Thresholds:** `from src.settings import load_settings`, then `load_settings()["gates"]["stale_report_months"]` gives 15 (PR #7).
  Never hard-code a threshold; a misspelt name raises a `KeyError` naming the section.
- Never import `src.data.sec_client`: only A's data layer talks to the SEC; your code receives `CompanyData`.
- **Loading a company** (PR #8): `from src.data.company import load_company`, then
  `load_company("MCD", demo=True)` gives `CompanyData` from the saved files, with no network (`DEMO_TICKERS`:
  KO, AAPL, NVDA, MCD, AMZN). The latest fiscal year is `data.fiscal_years("revenue")[-1]`. Shares come from
  `data.latest("shares")`, never `data.fact("shares", fy0)`, which is None by design (plan Q12). A `missing`
  figure has value None and its reason in `.note`; a `derived` one has its formula and sources in `.note`.
- **Warnings for your gates (S11):** `data.warnings` holds strings "CODE: message", with the codes RESTATED,
  TAG_CONFLICT, NON_USD, FY_CHANGE, DERIVED, DEBT_CHECK, DEBT_INCOMPLETE, AVERAGE_SHARES, SIGN and NO_ANNUAL_DATA.
  JPMorgan loads with its header only (SEC industry code 6021), so your gate refuses it by industry code.
  Acceptance E4 is yours: `load_company` raises `SourceUnreachable`; show its message and suggest demo mode.
- **SEC errors for your messages (S11)**, all subclasses of `SecError` in `src.data.sec_client` (PR #7);
  each message already says how to fix the problem: `SourceUnreachable` is temporary (the figure becomes
  missing, suggest demo mode); `MissingUserAgent` and `SecRefused` mean fix `app/.env` or wait;
  `UnknownTicker`, `NotFound` and `InvalidCik` mean the company does not exist. The interface reaches the
  data layer through A's S2 and S14, never `SecClient` directly.
- AC3 values for your app tests come from `synthetic.expected_tier1()` in `app/tests/fixtures/synthetic.py`, once
  your sign-off is recorded.
- **No overrides anywhere (SPEC v2.3):** no figure override, no industry dropdown, no rating override. The only
  inputs are the ticker, the share price (USD, greater than 0) and the demo switch (SPEC §3, AC6). Each invalid
  entry gets a message that says how to fix it.
- **Header warnings (SPEC v2.3 §10):** show only "not fully checked" (outside the verified universe) and "latest
  annual report is old". Every other warning goes on the sources page next to its figure.
- Figures arrive in USD with a unit from `UNITS` (`app/src/contracts.py`); show amounts in USD m through one
  tested formatting function, never ad hoc in a page. A check with status `insufficient_data` shows its
  explanation ("not assessed until …" or the missing input), never a score.
- The interface **shows** numbers it receives from `app/src/`; it never computes, rounds or fills them in
  (SPEC §11). A missing figure shows "n/a" with the reason, never 0.
- **Score chart:** one bar of six blocks per area, passes filled, the other results told apart by pattern and
  text ("4 of 5 assessed, 1 with insufficient data"). **No radar chart, nothing that looks like Simply Wall St**
  (SPEC §1, rule 14.16): we present results the way they do (areas, ticks, strengths and points to watch) in our
  own design. Confirm the design in `docs/product.md` (marked "to confirm by member D").
- **Look (SPEC §3):** calm and light, one accent colour, no gradients, glow or emoji; every colour defined once in
  `app/.streamlit/config.toml`, so a bank could apply its own brand. Wording is information, not advice: never
  "buy", "sell" or "undervalued".
- A unit on every input and figure; the key result visible without scrolling; every error message says how to fix
  it (SPEC §3). The synthetic company always shows "SYNTHETIC DATA".
- Plain-language texts come from E's `app/ui/texts.yaml`: agree the key names with E before S16a.
- App tests use Streamlit's `AppTest` (no browser), in `app/tests/app/`.

## Only you

1. **Expected values** for your app tests: your own reading of `docs/acceptance.md` and hand working.
2. **Look at the screens yourself** at laptop width before each PR (tests do not show what the page looks like).
3. **Reconciliation (S15), McDonald's:** revenue, operating income, net income, total assets, operating cash flow,
   dividends paid, read by hand from the latest 10-K with page and accession number. Not by the assistant.
4. **Demo safety (risk R8):** with Emma (E), record the fallback demo video on Mon 30; keep a second laptop with the
   repository cloned.
5. **Explain-back** on each PR; at least two reviews a week, Igor's (A) first.
6. **Before the presentation:** five likely questions and answers on your area to E (Sun 29); walk-through (Mon 30).

## If you are blocked

- No real data yet? Build everything on the synthetic company fixture (`app/tests/fixtures/`, from S0c); switch to
  real data when A's S2 is merged (risk R4).
