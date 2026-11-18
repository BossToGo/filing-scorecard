"""Coverage report (slice S3). Owner: A.

Run from app/:   .venv/bin/python scripts/coverage.py        (Windows: .venv\\Scripts\\python ...)

Needs SEC_USER_AGENT in app/.env. The first run downloads about 250 SEC files (cached in app/.cache/sec/, reused
afterwards); later runs need no network. Writes docs/coverage.md and app/data/universe.csv. Do not edit those two
files by hand: change the rules here or in src/data/coverage.py, then run again.

Selection rule (no hand-picking): the SEC's ticker list in its own order, which lists the largest companies first;
keep the first `coverage_companies` companies (settings.yaml) that are not a second share class of a company already
taken, not a bank, insurer or real estate trust (SEC industry codes 6000 to 6799, SPEC §2), and that file Form 10-K
reports (foreign companies filing 20-F or 40-F are out of scope).
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
    industry,
    verification_problems,
)
from src.data.resolver import resolve  # noqa: E402
from src.data.sec_client import NotFound, SecClient, SecError  # noqa: E402
from src.settings import load_settings  # noqa: E402

REPORT = APP.parent / "docs" / "coverage.md"
PRETAX_TAGS = ("IncomeLossFromContinuingOperationsBeforeIncomeTaxesExtraordinaryItemsNoncontrollingInterest",
               "IncomeLossFromContinuingOperationsBeforeIncomeTaxesMinorityInterestAndIncomeLossFromEquityMethodInvestments")
UNIVERSE = APP / "data" / "universe.csv"


def pct(x: float) -> str:
    return f"{x * 100:.0f}%"


def problem_type(problem: str) -> str:
    if problem.startswith("resolver warning"):
        return problem.split(":")[0]
    if " missing for " in problem:
        return problem.split(" missing for ")[0] + " missing"
    for words in ("balance sheet does not balance", "latest annual report older", "only", "revenue",
                  "current assets above", "cash above", "current liabilities above"):
        if problem.startswith(words):
            return words if words != "only" else "fewer than five fiscal years"
    return problem


def pretax_at(facts: dict, end: date) -> bool:
    """True if pre-tax income is filed for the fiscal year ending `end` (for the operating-income what-if only)."""
    for tag in PRETAX_TAGS:
        for e in facts.get("facts", {}).get("us-gaap", {}).get(tag, {}).get("units", {}).get("USD", []):
            if e.get("form") in ("10-K", "10-K/A") and e["end"] == end.isoformat() and "start" in e and \
                    350 <= (end - date.fromisoformat(e["start"])).days <= 380:
                return True
    return False


def longest_year(company) -> int:
    """Longest annual period among the company's revenue figures, as end − start in days: 364 for a 52-week year,
    370 for a 53-week year."""
    return max(((f.period_end - f.period_start).days for y in company.fiscal_years("revenue")
                if (f := company.fact("revenue", y)) is not None and f.period_start), default=0)


def load(sec: SecClient, cik: str, ticker: str):
    submissions = sec.submissions(cik)
    facts = sec.companyfacts(cik)
    return submissions, resolve(ticker, facts.data, submissions.data, facts.retrieved)


def main() -> None:
    settings = load_settings()
    data_settings, gates = settings["data"], settings["gates"]
    wanted = data_settings["coverage_companies"]
    today = date.today()
    try:
        sec = SecClient.from_settings()
        tickers = sec.ticker_list()
    except SecError as error:
        sys.exit(str(error))

    taken, skipped, seen, whatif = [], [], set(), {}
    for entry in tickers.data.values():
        if len(taken) == wanted:
            break
        ticker, cik = entry["ticker"], f"{entry['cik_str']:010d}"
        if cik in seen:
            skipped.append((ticker, "second share class of a company already taken"))
            continue
        seen.add(cik)
        try:
            submissions = sec.submissions(cik).data
            sic = int(submissions.get("sic") or 0)
            if 6000 <= sic <= 6799:
                skipped.append((ticker, f"financial company, SEC industry code {sic} (SPEC §2)"))
                continue
            forms = Counter(submissions.get("filings", {}).get("recent", {}).get("form", []))
            if not forms.get("10-K"):
                annual = next((f for f in ("20-F", "40-F") if forms.get(f)), "no annual report")
                skipped.append((ticker, f"files {annual}, not Form 10-K"))
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

    core_now, core_all = coverage(taken, CORE), coverage(taken, CORE, all_years=True)
    sec_now, sec_all = coverage(taken, SECONDARY), coverage(taken, SECONDARY, all_years=True)
    tier1_now = coverage(taken, TIER1)
    verdict = decision(core_now, sec_now, data_settings["coverage_core_threshold"],
                       data_settings["coverage_secondary_threshold"])
    oi_whatif = core_now["operating_income"] + sum(whatif.values()) / len(taken)
    verdict_whatif = decision({**core_now, "operating_income": oi_whatif}, sec_now,
                              data_settings["coverage_core_threshold"], data_settings["coverage_secondary_threshold"])

    def problems(company):
        return verification_problems(company, today, gates["balance_sheet_tolerance"], gates["stale_report_months"],
                                     data_settings["fiscal_years"])

    checked = [(c, problems(c)) for c in taken]
    verified = [c for c, p in checked if not p]
    universe = choose_universe(verified, data_settings["universe_size"], data_settings["universe_min_industries"])

    demo_status = []
    sample = {c.ticker: (c, p) for c, p in checked}
    for ticker in DEMO_TICKERS:
        if ticker in sample:
            company, found = sample[ticker]
        else:
            company = load(sec, sec.cik_for(ticker), ticker)[1]
            found = problems(company)
        demo_status.append((ticker, ticker in sample, company in universe, found))

    UNIVERSE.parent.mkdir(parents=True, exist_ok=True)
    with UNIVERSE.open("w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["ticker", "cik", "name", "sic", "sic_description", "industry", "fiscal_year_end",
                         "fy0_end", "latest_10k_filed"])
        for c in universe:
            writer.writerow([c.ticker, c.cik, c.name, c.sic, c.sic_description, industry(c), c.fiscal_year_end,
                             c.fiscal_years("revenue")[-1], c.latest_10k_filed])

    industries_sample = Counter(industry(c) for c in taken)
    industries_universe = Counter(industry(c) for c in universe)
    reasons = Counter(problem_type(p) for _, ps in checked for p in set(problem_type(x) for x in ps))
    lines = [
        "# Coverage report (slice S3)",
        "",
        f"Generated by `app/scripts/coverage.py` on {today} from SEC data retrieved through the app's SEC client "
        "(cached in `app/.cache/sec/`). Do not edit by hand: change the rules, then run the script again.",
        "",
        "## Method",
        "",
        f"- **Sample:** the first {len(taken)} companies of the SEC ticker list, in the SEC's own order (largest "
        "first), that are not a second share class, not a bank, insurer or real estate trust (SEC industry codes "
        "6000 to 6799) and that file Form 10-K reports. No hand-picking. Skipped while selecting: "
        f"{len(skipped)} (listed at the end).",
        f"- **Industries:** {len(industries_sample)} SEC major groups (first two digits of the industry code) in the "
        f"sample; SPEC asks for at least {data_settings['universe_min_industries']}.",
        "- **Resolved** means the resolver (`app/src/data/resolver.py`) gives a reported or derived figure, never a "
        "guess. The go/no-go uses the latest fiscal year (FY0); the five-year column is stricter.",
        "- **Limitation:** the sample is made of very large companies; smaller companies may file less complete "
        "data. The rules are the same for any ticker; companies outside the verified universe are shown as "
        "\"not verified\" (SPEC §2).",
        "",
        "## Go/no-go (SPEC §13.4)",
        "",
        "| Line item | Group | FY0 resolved | All five years | Threshold | Met |",
        "|---|---|---|---|---|---|",
    ]
    for group, now, all_, threshold in (("core", core_now, core_all, data_settings["coverage_core_threshold"]),
                                        ("debt, interest, depreciation", sec_now, sec_all,
                                         data_settings["coverage_secondary_threshold"])):
        for metric in now:
            lines.append(f"| {metric} | {group} | {pct(now[metric])} | {pct(all_[metric])} | {pct(threshold)} | "
                         f"{'yes' if now[metric] >= threshold else '**no**'} |")
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
        f"{len(whatif)} companies file no operating income for their latest fiscal year: their income statements go "
        "straight to pre-tax income (e.g. " + ", ".join(sorted(whatif)[:6]) + "). If the group allows operating income "
        "= pre-tax income + interest expense for them (labelled `derived`, an approximation of EBIT that includes "
        f"other non-operating items), {sum(whatif.values())} of them would resolve: operating income FY0 "
        f"{pct(core_now['operating_income'])} → {pct(oi_whatif)}, and the SPEC §13.4 rule would give "
        f"**{verdict_whatif}**. Not built: it changes what P5, P6, H6 and V4 measure, so it is the group's decision "
        "(SPEC §6, `AGENTS.md` rule 1). Either way, the demo uses only the verified universe below.",
        "",
        f"## Verified universe ({len(universe)} companies, `app/data/universe.csv`)",
        "",
        "Verified (SPEC §13.4): every tier 1 figure resolves in each of the five fiscal years (no dividend at all "
        "counts as \"no dividend paid\", plan Q1); the accounting checks pass (reported liabilities + equity within "
        f"{pct(gates['balance_sheet_tolerance'])} of assets; current assets ≤ total assets; cash ≤ current assets; "
        "current liabilities ≤ total liabilities; revenue above zero); no resolver warning that puts a figure in doubt "
        "(NON_USD, FY_CHANGE, DEBT_CHECK, DEBT_INCOMPLETE, SIGN, or TAG_CONFLICT on a tier 1 figure); latest annual report "
        f"not older than {gates['stale_report_months']} months. Verified in the sample: {len(verified)} of "
        f"{len(taken)}. Chosen: the first {data_settings['universe_size']} in list order, with at least "
        f"{data_settings['universe_min_industries']} industries ({len(industries_universe)} covered).",
        "",
        "| # | Ticker | Company | Industry (SIC) | FY0 end |",
        "|---|---|---|---|---|",
    ]
    lines += [f"| {i} | {c.ticker} | {c.name} | {c.sic} {c.sic_description or ''} | {c.fiscal_years('revenue')[-1]} |"
              for i, c in enumerate(universe, start=1)]
    lines += ["", "## Demo companies (SPEC §13.2)", "", "| Ticker | In the sample | In the verified universe | "
              "Why not verified |", "|---|---|---|---|"]
    lines += [f"| {t} | {'yes' if s else 'no'} | {'yes' if u else 'no'} | {'; '.join(p) if p else '–'} |"
              for t, s, u, p in demo_status]
    week53 = [c for c in universe if longest_year(c) >= 370]
    lines += ["", "Verified companies with a 53-week year (the trait Apple was chosen for, SPEC §13.2), should the "
              "group swap Apple: " + (", ".join(f"{c.ticker} ({longest_year(c)} days)" for c in week53) or "none")
              + "."]
    lines += ["", "## Why companies are not verified", "", "| Reason | Companies |", "|---|---|"]
    lines += [f"| {reason} | {n} |" for reason, n in reasons.most_common()]
    lines += ["", f"## All {len(taken)} companies", "", "| # | Ticker | Company | SIC | Verified | Problems |",
              "|---|---|---|---|---|---|"]
    lines += [f"| {i} | {c.ticker} | {c.name} | {c.sic} | {'yes' if not p else 'no'} | "
              f"{'; '.join(sorted(set(problem_type(x) for x in p))) if p else '–'} |"
              for i, (c, p) in enumerate(checked, start=1)]
    lines += ["", "## Skipped while selecting", "", "| Ticker | Reason |", "|---|---|"]
    lines += [f"| {t} | {r} |" for t, r in skipped]
    REPORT.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"\n{len(taken)} companies, {len(verified)} verified, universe {len(universe)}; decision: {verdict}")
    print(f"wrote {REPORT.relative_to(APP.parent)} and {UNIVERSE.relative_to(APP.parent)}")


if __name__ == "__main__":
    main()
