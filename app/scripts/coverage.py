"""Coverage report (slice S3). Owner: A.

Run from app/:   .venv/bin/python scripts/coverage.py        (Windows: .venv\\Scripts\\python ...)

Needs SEC_USER_AGENT in app/.env. The first run downloads about 250 SEC files (cached in app/.cache/sec/, reused
afterwards); later runs need no network. Writes docs/coverage.md and app/data/universe.csv. Do not edit those two
files by hand: change the rules here or in src/data/coverage.py, then run again.

Selection rule (no hand-picking, `selection_problem` in src/data/coverage.py): the SEC's ticker list in its own
order, which lists the largest companies first; keep the first `coverage_companies` companies (settings.yaml) that
are not a second share class of a company already taken, not a bank, insurer or real estate trust (SEC industry
codes 6000 to 6799, SPEC §2), and that file Form 10-K reports.
"""

from __future__ import annotations

import csv
import sys
from collections import Counter
from datetime import date
from pathlib import Path

APP = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(APP))

from src.data.company import DEMO_TICKERS  # noqa: E402
from src.data.coverage import (  # noqa: E402
    CORE,
    SECONDARY,
    TIER1,
    choose_universe,
    coverage,
    decision,
    depends_on_q1,
    industry,
    longest_year,
    pretax_at,
    problem_type,
    selection_problem,
    verification_problems,
)
from src.data.resolver import resolve  # noqa: E402
from src.data.sec_client import NotFound, SecClient, SecError  # noqa: E402
from src.settings import load_settings  # noqa: E402

REPORT = APP.parent / "docs" / "coverage.md"
UNIVERSE = APP / "data" / "universe.csv"


def pct(x: float) -> str:
    return f"{x * 100:.0f}%"


def main() -> None:
    settings = load_settings()
    data_settings, gates = settings["data"], settings["gates"]
    wanted, years = data_settings["coverage_companies"], data_settings["fiscal_years"]
    today = date.today()
    try:
        sec = SecClient.from_settings()
        tickers = sec.ticker_list()
    except SecError as error:
        sys.exit(str(error))

    taken, skipped, seen, examined, whatif = [], [], set(), [], {}
    for entry in tickers.data.values():
        if len(taken) == wanted:
            break
        ticker, cik = entry["ticker"], f"{entry['cik_str']:010d}"
        examined.append(ticker)
        if cik in seen:
            skipped.append((ticker, "second share class of a company already taken"))
            continue
        seen.add(cik)
        try:
            submissions = sec.submissions(cik).data
            problem = selection_problem(submissions)
            if problem:
                skipped.append((ticker, problem))
                continue
            facts = sec.companyfacts(cik)
        except NotFound:
            skipped.append((ticker, "no company facts at the SEC"))
            continue
        except SecError as error:
            sys.exit(f"Stopped at {ticker}: {error}")
        company = resolve(ticker, facts.data, submissions, facts.retrieved)
        taken.append(company)
        fy = company.fiscal_years("revenue")
        if fy and company.fact("operating_income", fy[-1]).value is None:
            interest = company.fact("interest_expense", fy[-1])
            whatif[ticker] = pretax_at(facts.data, fy[-1]) and interest is not None and interest.value is not None
        print(f"{len(taken):3d} {ticker:6s} {company.name[:40]}", flush=True)

    core_now, core_all = coverage(taken, CORE), coverage(taken, CORE, all_years=True, years=years)
    sec_now, sec_all = coverage(taken, SECONDARY), coverage(taken, SECONDARY, all_years=True, years=years)
    tier1_now = coverage(taken, TIER1)
    thresholds = data_settings["coverage_core_threshold"], data_settings["coverage_secondary_threshold"]
    verdict = decision(core_now, sec_now, *thresholds)
    oi_whatif = core_now["operating_income"] + sum(whatif.values()) / len(taken)
    verdict_whatif = decision({**core_now, "operating_income": oi_whatif}, sec_now, *thresholds)
    no_years = [c.ticker for c in taken if not c.fiscal_years("revenue")]

    def problems(company):
        return verification_problems(company, today, gates["balance_sheet_tolerance"], gates["stale_report_months"],
                                     years)

    checked = [(c, problems(c)) for c in taken]
    verified = [c for c, p in checked if not p]
    universe = choose_universe(verified, data_settings["universe_size"], data_settings["universe_min_industries"])

    demo_status = []
    sample = {c.ticker: (c, p) for c, p in checked}
    for ticker in DEMO_TICKERS:
        if ticker in sample:
            company, found = sample[ticker]
        else:
            cik = sec.cik_for(ticker)
            facts, submissions = sec.companyfacts(cik), sec.submissions(cik)
            company = resolve(ticker, facts.data, submissions.data, facts.retrieved)
            found = problems(company)
        demo_status.append((company, ticker in sample, company in universe, found))

    UNIVERSE.parent.mkdir(parents=True, exist_ok=True)
    with UNIVERSE.open("w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f, lineterminator="\n")
        writer.writerow(["ticker", "cik", "name", "sic", "sic_description", "industry", "fiscal_year_end",
                         "fy0_end", "latest_10k_filed", "verified_only_if_plan_q1"])
        for c in universe:
            writer.writerow([c.ticker, c.cik, c.name, c.sic, c.sic_description, industry(c), c.fiscal_year_end,
                             c.fiscal_years("revenue")[-1], c.latest_10k_filed, "yes" if depends_on_q1(c) else "no"])

    def q1(c):
        return " (no dividend: plan Q1)" if depends_on_q1(c) else ""

    industries_sample = Counter(industry(c) for c in taken)
    industries_universe = Counter(industry(c) for c in universe)
    reasons = Counter(kind for _, ps in checked for kind in {problem_type(p) for p in ps})
    week53 = [c for c in universe if longest_year(c) >= 370]
    lines = [
        "# Coverage report (slice S3)",
        "",
        f"Generated by `app/scripts/coverage.py` on {today} (also the date used for the \"older than "
        f"{gates['stale_report_months']} months\" check) from SEC data retrieved through the app's SEC client and "
        "cached in `app/.cache/sec/`. Do not edit by hand: change the rules, then run the script again.",
        "",
        "## Method",
        "",
        f"- **Sample:** the first {len(taken)} companies of the SEC ticker list, in the SEC's own order (largest "
        "first), that are not a second share class, not a bank, insurer or real estate trust (SEC industry codes "
        "6000 to 6799) and that file Form 10-K reports. No hand-picking. Ticker list retrieved "
        f"{tickers.provenance['retrieved']}, SHA-256 `{tickers.provenance['raw_sha256'][:16]}…` (the SEC reorders "
        f"it over time). Examined in this order ({len(examined)}): {', '.join(examined)}. Skipped while selecting: "
        f"{len(skipped)}, listed with reasons at the end.",
        f"- **Industries:** {len(industries_sample)} SEC major groups (first two digits of the industry code) in the "
        f"sample; SPEC asks for at least {data_settings['universe_min_industries']}.",
        "- **Resolved** means the resolver (`app/src/data/resolver.py`) gives a reported or derived figure, never a "
        f"guess. The go/no-go uses the latest fiscal year (FY0); the stricter column needs all {years} fiscal years.",
        "- **Limitation:** the sample is made of very large companies; smaller companies may file less complete "
        "data. The rules are the same for any ticker; companies outside the verified universe are shown as "
        "\"not verified\" (SPEC §2).",
        "",
        "## Go/no-go (SPEC §13.4)",
        "",
        f"| Line item | Group | FY0 resolved | All {years} years | Threshold | Met |",
        "|---|---|---|---|---|---|",
    ]
    for group, now, all_, threshold in (("core", core_now, core_all, thresholds[0]),
                                        ("debt, interest, depreciation", sec_now, sec_all, thresholds[1])):
        for metric in now:
            lines.append(f"| {metric} | {group} | {pct(now[metric])} | {pct(all_[metric])} | {pct(threshold)} | "
                         f"{'yes' if now[metric] >= threshold else '**no**'} |")
    unresolved_oi = round((1 - core_now["operating_income"]) * len(taken))
    lines += [
        "",
        f"**Result by the SPEC §13.4 rule: {verdict}.** The decision itself is taken by the group at the office hours "
        "of Friday 20 November.",
        "",
        "Other tier 1 figures, FY0 resolved: " + ", ".join(f"{m} {pct(r)}" for m, r in tier1_now.items()
                                                            if m not in CORE + SECONDARY) + ".",
        "",
        "### Option for the group: operating income where the income statement has no such line",
        "",
        f"Operating income is unresolved for {unresolved_oi} companies: {len(whatif)} file no operating income for "
        "their latest fiscal year, their income statements going straight to pre-tax income (e.g. "
        + ", ".join(sorted(whatif)[:6]) + ")"
        + (f", and {len(no_years)} {'has' if len(no_years) == 1 else 'have'} no US-dollar annual data at all "
           f"({', '.join(no_years)})" if no_years else "")
        + ". If the group allows operating income = pre-tax income + interest expense for the first group "
        f"(labelled `derived`), {sum(whatif.values())} of them would resolve: operating income FY0 "
        f"{pct(core_now['operating_income'])} → {pct(oi_whatif)}, and the SPEC §13.4 rule would give "
        f"**{verdict_whatif}**. This is an approximation, not EBIT: it includes other non-operating items, and some "
        "companies' interest expense includes a financing arm's (e.g. Deere) or may be reported net. Not built: it "
        "changes what P5, P6, H6 and V4 measure, so it is the group's decision (SPEC §6, `AGENTS.md` rule 1). Either "
        "way, the demo uses only the verified universe below.",
        "",
        f"## Verified universe ({len(universe)} companies, `app/data/universe.csv`)",
        "",
        f"Verified (SPEC §13.4): every tier 1 figure resolves in each of the {years} fiscal years; the accounting "
        f"checks pass (reported liabilities + equity within {pct(gates['balance_sheet_tolerance'])} of assets; current "
        "assets ≤ total assets; cash ≤ current assets; current liabilities ≤ total liabilities; revenue above zero); "
        "no resolver warning that puts a tier 1 figure in doubt (NON_USD, FY_CHANGE, DEBT_CHECK, DEBT_INCOMPLETE, "
        "SIGN, or TAG_CONFLICT on a tier 1 figure); latest annual report not older than "
        f"{gates['stale_report_months']} months; and the share count and the latest fiscal year's depreciation and "
        "amortisation (for V4) resolve (lean SPEC v2.3 §13.4). A company with no dividend in any year "
        "counts as \"no dividend paid\", "
        "which assumes plan Q1 is accepted: such companies are marked. (The debt half of Q1 is not applied: a company "
        f"with no debt tag is not verified.) Verified in the sample: {len(verified)} of {len(taken)}. Chosen: the "
        f"first {data_settings['universe_size']} in list order, with at least "
        f"{data_settings['universe_min_industries']} industries ({len(industries_universe)} covered).",
        "",
        "| # | Ticker | Company | Industry (SIC) | FY0 end |",
        "|---|---|---|---|---|",
    ]
    lines += [f"| {i} | {c.ticker}{q1(c)} | {c.name} | {c.sic} {c.sic_description or ''} | "
              f"{c.fiscal_years('revenue')[-1]} |" for i, c in enumerate(universe, start=1)]
    lines += ["", "## Demo companies (SPEC §13.2)", "", "| Ticker | In the sample | In the verified universe | "
              "Why not verified |", "|---|---|---|---|"]
    lines += [f"| {c.ticker}{q1(c)} | {'yes' if s else 'no'} | {'yes' if u else 'no'} | {'; '.join(p) if p else '–'} |"
              for c, s, u, p in demo_status]
    lines += ["", "Verified companies with a 53-week year (the trait Apple was chosen for, SPEC §13.2), should the "
              "group swap Apple: " + (", ".join(f"{c.ticker} ({longest_year(c)} days)" for c in week53) or "none")
              + "."]
    lines += ["", "## Why companies are not verified", "", "| Reason | Companies |", "|---|---|"]
    lines += [f"| {reason} | {n} |" for reason, n in reasons.most_common()]
    lines += ["", f"## All {len(taken)} companies", "", "| # | Ticker | Company | SIC | Verified | Problems |",
              "|---|---|---|---|---|---|"]
    lines += [f"| {i} | {c.ticker} | {c.name} | {c.sic} | {'yes' + q1(c) if not p else 'no'} | "
              f"{'; '.join(sorted({problem_type(x) for x in p})) if p else '–'} |"
              for i, (c, p) in enumerate(checked, start=1)]
    lines += ["", "## Skipped while selecting", "", "| Ticker | Reason |", "|---|---|"]
    lines += [f"| {t} | {r} |" for t, r in skipped]
    REPORT.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"\n{len(taken)} companies, {len(verified)} verified, universe {len(universe)}; decision: {verdict}; "
          f"with the operating-income option: {verdict_whatif}")
    print(f"wrote {REPORT.relative_to(APP.parent)} and {UNIVERSE.relative_to(APP.parent)}")


if __name__ == "__main__":
    main()
