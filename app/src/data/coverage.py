"""Coverage report logic (SPEC §13.2 S3, §13.4). Owner: A. Pure functions over SEC JSON and `CompanyData`; the
downloads and the report files are in app/scripts/coverage.py.

- `selection_problem`: why a company of the SEC list is not in the sample (None: it is);
- `coverage`: the share of companies whose latest fiscal year (or every one of five) resolves for a line item;
- `decision`: the go/no-go of SPEC §13.4 from the two groups of line items;
- `verification_problems`: why a company is not in the verified universe (empty list: verified): every tier 1
  figure resolves in every fiscal year and passes the accounting checks, and a share count resolves (lean SPEC v2.3
  §8.6 and §13.4, PR #10);
- `choose_universe`: the verified companies to demo, in list order, with at least `min_industries` industries;
- helpers for the report: `problem_type`, `depends_on_q1`, `longest_year`, `pretax_at`.
"""

from __future__ import annotations

import re
from collections import Counter
from datetime import date

from src.contracts import CompanyData, Fact

# SPEC §13.4, first group: each must resolve for at least 90% of the companies.
CORE = ("revenue", "operating_income", "net_income", "total_assets", "current_assets", "current_liabilities",
        "equity", "operating_cash_flow", "capital_expenditure")
# SPEC §13.4, second group: at least 70%.
SECONDARY = ("financial_debt", "interest_expense", "depreciation_amortization")
# The figures the 18 tier 1 checks read (SPEC §7: P1–P6, H1–H6, D1–D6).
TIER1 = ("revenue", "operating_income", "net_income", "interest_expense", "total_assets", "current_assets",
         "current_liabilities", "total_liabilities", "equity", "cash", "financial_debt", "operating_cash_flow",
         "capital_expenditure", "dividends_paid")
# Resolver warnings that put a tier 1 figure in doubt (src/data/resolver.py). A restatement alone does not; an
# average share count matters only from tier 2 on; a TAG_CONFLICT counts only when it is about a tier 1 figure.
BLOCKING = ("NON_USD", "FY_CHANGE", "FY_GAP", "DEBT_CHECK", "DEBT_INCOMPLETE", "SIGN", "NO_ANNUAL_DATA")
# Valuation inputs that are not tier 1 figures (lean SPEC v2.3 §8.6, §13.4, PR #10): none any more. Revenue, operating
# cash flow, capex and debt are tier 1 figures already, in every year; depreciation and current debt are no longer used
# by any check. Shares are checked separately: they are keyed at the cover-page date (CompanyData.latest).
VALUATION: tuple[str, ...] = ()
PRETAX_TAGS = ("IncomeLossFromContinuingOperationsBeforeIncomeTaxesExtraordinaryItemsNoncontrollingInterest",
               "IncomeLossFromContinuingOperationsBeforeIncomeTaxesMinorityInterestAndIncomeLossFromEquityMethodInvestments")


def _resolved(fact: Fact | None) -> bool:
    return fact is not None and fact.value is not None


def selection_problem(submissions: dict) -> str | None:
    """Why a company of the SEC list is left out of the sample (SPEC §2), or None if it is kept."""
    sic = int(submissions.get("sic") or 0)
    if 6000 <= sic <= 6799:
        return f"financial company, SEC industry code {sic} (SPEC §2)"
    forms = Counter(submissions.get("filings", {}).get("recent", {}).get("form", []))
    if not forms.get("10-K"):
        foreign = next((f for f in ("20-F", "40-F") if forms.get(f)), None)
        if foreign:
            return f"files {foreign}, not Form 10-K (foreign company)"
        return "no Form 10-K filed under this SEC number (e.g. a new holding company)"
    return None


def coverage(companies: list[CompanyData], metrics, all_years: bool = False, years: int = 5) -> dict[str, float]:
    """Share of companies whose latest fiscal year (or, with all_years, each of `years` fiscal years) resolves."""
    rates = {}
    for metric in metrics:
        count = 0
        for data in companies:
            found = data.fiscal_years(metric)
            if not found or (all_years and len(found) < years):
                continue
            checked = found if all_years else found[-1:]
            count += all(_resolved(data.fact(metric, y)) for y in checked)
        rates[metric] = count / len(companies) if companies else 0.0
    return rates


def decision(core_rates: dict, secondary_rates: dict, core_threshold: float, secondary_threshold: float) -> str:
    """SPEC §13.4: 'go as planned', 'go with manual fields' or 'change scope'."""
    if min(core_rates.values()) < core_threshold:
        return "change scope"
    if min(secondary_rates.values()) < secondary_threshold:
        return "go with manual fields"
    return "go as planned"


def _add_months(day: date, months: int) -> date:
    month = day.month - 1 + months
    year, month = day.year + month // 12, month % 12 + 1
    for last in (31, 30, 29, 28):
        try:
            return date(year, month, min(day.day, last))
        except ValueError:
            continue
    raise ValueError(day)


def verification_problems(data: CompanyData, today: date, balance_tolerance: float, stale_months: int,
                          years: int = 5) -> list[str]:
    """Why the company is not verified; an empty list means verified (SPEC §13.4)."""
    problems: list[str] = []
    fiscal_years = data.fiscal_years("revenue")
    if len(fiscal_years) < years:
        problems.append(f"only {len(fiscal_years)} fiscal years, {years} needed")

    for metric in TIER1:
        gaps = [y for y in fiscal_years if not _resolved(data.fact(metric, y))]
        if metric == "dividends_paid" and fiscal_years and len(gaps) == len(fiscal_years):
            continue  # no dividend in any year: "no dividend paid" if plan Q1 is accepted (see depends_on_q1)
        if gaps:
            problems.append(f"{metric} missing for {', '.join(map(str, gaps))}")

    if fiscal_years:
        fy0 = fiscal_years[-1]
        for metric in VALUATION:
            if not _resolved(data.fact(metric, fy0)):
                problems.append(f"{metric} missing for {fy0} (valuation input, SPEC v2.3 §8.6)")
        if not _resolved(data.latest("shares")):
            problems.append("shares missing for the latest annual report (valuation input, SPEC v2.3 §8.6)")

    for y in fiscal_years:
        def value(metric):
            fact = data.fact(metric, y)
            return fact.value if _resolved(fact) else None

        revenue, assets, current_assets = value("revenue"), value("total_assets"), value("current_assets")
        liabilities, current_liabilities, cash = value("total_liabilities"), value("current_liabilities"), value("cash")
        if revenue is not None and revenue <= 0:
            problems.append(f"revenue {y} is not positive")
        if assets is not None and current_assets is not None and current_assets > assets:
            problems.append(f"current assets above total assets in {y}")
        if cash is not None and current_assets is not None and cash > current_assets:
            problems.append(f"cash above current assets in {y}")
        if liabilities is not None and current_liabilities is not None and current_liabilities > liabilities:
            problems.append(f"current liabilities above total liabilities in {y}")
        liabilities_fact = data.fact("total_liabilities", y)
        equity = value("total_equity") if value("total_equity") is not None else value("equity")
        if (liabilities_fact is not None and liabilities_fact.kind == "reported" and assets and equity is not None
                and abs(assets - (liabilities + equity)) > balance_tolerance * abs(assets)):
            problems.append(f"balance sheet does not balance in {y}: assets {assets:,.0f} against liabilities "
                            f"{liabilities:,.0f} + equity {equity:,.0f}")

    for warning in data.warnings:
        code, _, rest = warning.partition(":")
        about = rest.strip().split(" ")[0] if rest.strip() else ""
        if code in BLOCKING or (code == "TAG_CONFLICT" and about in TIER1):
            problems.append(f"resolver warning {warning}")

    if data.latest_10k_filed is None or _add_months(data.latest_10k_filed, stale_months) < today:
        problems.append(f"latest annual report older than {stale_months} months")
    return problems


def depends_on_q1(data: CompanyData) -> bool:
    """True if the company reports no dividend in any fiscal year: verified only if plan Q1 is accepted."""
    years = data.fiscal_years("revenue")
    return bool(years) and not any(_resolved(data.fact("dividends_paid", y)) for y in years)


def problem_type(problem: str) -> str:
    """The kind of a verification problem, for counting (applying it twice changes nothing)."""
    if problem.startswith("resolver warning"):
        return problem.split(":")[0]
    if " missing for " in problem:
        return problem.split(" missing for ")[0] + " missing"
    if problem.startswith("only ") and "fiscal years" in problem:
        return "fewer than five fiscal years"
    if " is not positive" in problem:
        return problem.split(" ")[0] + " not positive"
    if problem.startswith("balance sheet does not balance"):
        return "balance sheet does not balance"
    return re.sub(r" in \d{4}-\d{2}-\d{2}.*$", "", problem)


def industry(data: CompanyData) -> str:
    """The SEC major group: the first two digits of the industry code (SIC)."""
    return data.sic[:2] if data.sic else "unknown"


def longest_year(data: CompanyData) -> int:
    """Longest annual period among the revenue figures, as end − start in days: 364 for 52 weeks, 370 for 53."""
    return max(((f.period_end - f.period_start).days for y in data.fiscal_years("revenue")
                if (f := data.fact("revenue", y)) is not None and f.period_start), default=0)


def pretax_at(companyfacts: dict, end: date) -> bool:
    """True if pre-tax income is filed in a 10-K for the fiscal year ending `end` (for the report's what-if only)."""
    for tag in PRETAX_TAGS:
        for e in companyfacts.get("facts", {}).get("us-gaap", {}).get(tag, {}).get("units", {}).get("USD", []):
            if e.get("form") in ("10-K", "10-K/A") and e["end"] == end.isoformat() and "start" in e and \
                    350 <= (end - date.fromisoformat(e["start"])).days <= 380:
                return True
    return False


def choose_universe(candidates: list[CompanyData], size: int, min_industries: int) -> list[CompanyData]:
    """The first `size` verified companies in list order; if they cover fewer than `min_industries` industries,
    the last-listed company of the most represented industry is replaced by the next company of a new industry."""
    chosen = list(range(min(size, len(candidates))))
    used = set(chosen)
    while len({industry(candidates[i]) for i in chosen}) < min_industries:
        covered = {industry(candidates[i]) for i in chosen}
        new = next((i for i in range(len(candidates)) if i not in used and industry(candidates[i]) not in covered), None)
        counts = Counter(industry(candidates[i]) for i in chosen)
        top = max(counts, key=counts.get) if counts else None
        if new is None or top is None or counts[top] < 2:
            break
        chosen.remove(max(i for i in chosen if industry(candidates[i]) == top))
        chosen.append(new)
        used.add(new)
    return [candidates[i] for i in sorted(chosen)]
