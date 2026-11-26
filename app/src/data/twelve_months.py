"""The latest figures: twelve months to the latest quarterly report, and the latest balance sheet. Owner: A.
Slice S2c (issue #71, item 1). Called by `src.data.resolver.resolve`, which stores the result in `CompanyData.recent`.

Twelve months ending at the latest quarter (revenue, net income, operating cash flow, capital expenditure):

    last fiscal year (10-K) + this year's year to date (10-Q) − last year's year to date (same 10-Q)

- The latest quarter is the latest end date of a 10-Q year to date that starts the day after the latest fiscal year
  end, under the revenue, net income or operating cash flow tags (the line items that also define fiscal years).
- The year to date must use the same tag as the fiscal-year figure (the definitions may differ between tags), and
  last year's year to date is the comparison column of the same 10-Q: it starts on the fiscal year's first day and
  covers the same quarters (its length within `ytd_length_tolerance_days` of this year's).
- Fiscal years still come from the 10-K alone (`annual_forms`): the "twelve months ended" totals that Amazon's 10-Qs
  also file are never read as a year, and a 10-Q twelve-month total is never read as a year to date.
- When the 10-K is the latest report (no 10-Q after it), the twelve months are that fiscal year, and the balances
  are those of its fiscal year end.
- Any part missing makes the figure `missing` with its reason: never the fiscal year alone, never zero.

Latest balance sheet: financial debt and minority interest follow the annual rules (`tag_map.yaml`, SPEC §6, §8.3)
at the latest quarter end; shares come from the cover page of the latest 10-Q (else the latest annual count, said in
the note). Warnings about these figures go into their notes, never into `CompanyData.warnings`, which the gates read.
"""

from __future__ import annotations

import dataclasses
from datetime import date, timedelta

from src.contracts import CompanyData, Fact

FLOWS = ("revenue", "net_income", "operating_cash_flow", "capital_expenditure")
QUARTER_ITEMS = ("revenue", "net_income", "operating_cash_flow")  # as FISCAL_YEAR_ITEMS in the resolver
BALANCES = ("financial_debt", "minority_interest")
LATEST_IS_10K = "the 10-K is the latest report (no 10-Q after it), so the last twelve months are this fiscal year"


def _order(e: dict) -> tuple:
    """Filing order, the same as the resolver's: later filing date first; on the same day an amendment; then
    accession."""
    return e["filed"], e.get("form", "").endswith("/A"), e["accn"]


def _days(e: dict) -> int:
    return (date.fromisoformat(e["end"]) - date.fromisoformat(e["start"])).days


def _money(value: float) -> str:
    return f"{value:,.0f}"


def _with_note(fact: Fact, extra: str) -> Fact:
    return dataclasses.replace(fact, note="; ".join(part for part in (fact.note, extra) if part))


class _Latest:
    def __init__(self, annual: CompanyData, latest, settings: dict):
        self.annual, self.latest, self.settings = annual, latest, settings  # latest: a resolver reading 10-Qs too
        self.quarterly = set(settings["quarterly_forms"])
        years = annual.fiscal_years("revenue")
        self.fy0 = years[-1] if years else None

    def missing(self, metric: str, end: date, reason: str, unit: str = "USD") -> Fact:
        return Fact(metric, None, unit, None, end, "missing", None, None, None, None, self.annual.retrieved, reason)

    def ytd_entries(self, tag: str) -> list[dict]:
        """10-Q entries of one tag that start on the day after the latest fiscal year end (this year's year to date)."""
        start = (self.fy0 + timedelta(days=1)).isoformat()
        return [e for e in self.latest.us_gaap.get(tag, {}).get("units", {}).get("USD", [])
                if e.get("form") in self.quarterly and e.get("start") == start]

    def latest_quarter(self) -> dict | None:
        """The 10-Q entry that marks the latest quarter: the latest year-to-date end, then the latest filing."""
        found = [e for metric in QUARTER_ITEMS for tag in self.latest.spec(metric)["tags"]
                 for e in self.ytd_entries(tag)]
        return max(found, key=lambda e: (e["end"], *_order(e))) if found else None

    # --- the twelve months ----------------------------------------------------------------------------------------

    def twelve_months(self, metric: str, q_end: date) -> Fact:
        year = self.annual.fact(metric, self.fy0)
        if year is None or year.kind == "missing":
            why = year.note if year is not None else "no figure"
            return self.missing(metric, q_end, f"the fiscal year ending {self.fy0} has no figure ({why}), so the "
                                               f"twelve months to {q_end} cannot be worked out")
        if year.kind != "reported" or year.period_start is None:
            return self.missing(metric, q_end, f"the fiscal-year figure for {self.fy0} is {year.kind}, not reported "
                                               "under one tag, so no 10-Q year to date can be matched to it")
        tag = year.tag
        current = [e for e in self.ytd_entries(tag) if date.fromisoformat(e["end"]) == q_end]
        if not current:
            return self.missing(metric, q_end, f"no year to date to {q_end} under {tag} in a 10-Q (the fiscal year "
                                               f"uses {tag}), so the twelve months cannot be worked out")
        ytd = max(current, key=_order)
        days = _days(ytd)
        columns = [e for e in self.latest.us_gaap[tag]["units"]["USD"]
                   if e["accn"] == ytd["accn"] and e.get("start") == year.period_start.isoformat()
                   and date.fromisoformat(e["end"]) < self.fy0]
        if not columns:
            return self.missing(metric, q_end, f"the 10-Q {ytd['accn']} has no comparison column for last year's "
                                               f"year to date under {tag}, so the twelve months cannot be worked out")
        prior = min(columns, key=lambda e: abs(_days(e) - days))
        if abs(_days(prior) - days) > self.settings["ytd_length_tolerance_days"]:
            return self.missing(metric, q_end, f"last year's year to date in the 10-Q {ytd['accn']} covers "
                                               f"{_days(prior)} days and this year's {days} days: not the same "
                                               "quarters, so the twelve months cannot be worked out")
        prior_end = date.fromisoformat(prior["end"])
        note = (f"last twelve months = fiscal year to {self.fy0} ({tag} {_money(year.value)}, {year.form} "
                f"{year.accession}) + year to date to {q_end} ({tag} {_money(ytd['val'])}, {ytd['form']} "
                f"{ytd['accn']}) − year to date to {prior_end} ({tag} {_money(prior['val'])}, same {ytd['form']})")
        return Fact(metric, year.value + ytd["val"] - prior["val"], "USD", prior_end + timedelta(days=1), q_end,
                    "derived", None, None, None, date.fromisoformat(ytd["filed"]), self.annual.retrieved, note)

    # --- the latest balance sheet ---------------------------------------------------------------------------------

    def balances(self, q_end: date) -> dict[str, Fact]:
        before = len(self.latest.warnings)
        debt, _ = self.latest.debt(q_end)
        debt_warnings = self.latest.warnings[before:]
        before = len(self.latest.warnings)
        self.latest.bridge_items(q_end, self.fy0)  # all bridge items: keep only the warnings about minority interest
        minority = self.latest.items["minority_interest"][q_end]
        minority_warnings = [w for w in self.latest.warnings[before:] if "minority" in w.lower()]
        return {"financial_debt": _with_note(debt, "; ".join(debt_warnings)),
                "minority_interest": _with_note(minority, "; ".join(minority_warnings))}

    def shares(self, quarter: dict) -> Fact:
        tag = self.latest.map["shares"]["cover_tag"]
        cover = [e for e in self.latest.dei.get(tag, {}).get("units", {}).get("shares", [])
                 if e["accn"] == quarter["accn"]]
        if cover:
            e = max(cover, key=lambda e: e["end"])
            return Fact("shares", e["val"], "shares", None, date.fromisoformat(e["end"]), "reported", f"dei:{tag}",
                        e["form"], e["accn"], date.fromisoformat(e["filed"]), self.annual.retrieved,
                        "cover page of the latest quarterly report")
        annual = self.annual.latest("shares")
        why = f"the latest quarterly report ({quarter['accn']}) has no cover-page share count"
        if annual is None:
            return self.missing("shares", date.fromisoformat(quarter["end"]), f"{why}, nor has the annual data",
                                unit="shares")
        return _with_note(annual, f"{why}: the count of the latest annual report is used")

    # --- all of them ------------------------------------------------------------------------------------------------

    def run(self) -> dict[str, Fact]:
        if self.fy0 is None:
            return {}  # no annual figures at all (NO_ANNUAL_DATA or NON_USD): nothing to start from
        quarter = self.latest_quarter()
        if quarter is None:
            return self.from_the_10k()
        q_end = date.fromisoformat(quarter["end"])
        recent = {metric: self.twelve_months(metric, q_end) for metric in FLOWS}
        recent.update(self.balances(q_end))
        recent["shares"] = self.shares(quarter)
        return recent

    def from_the_10k(self) -> dict[str, Fact]:
        recent = {}
        for metric in FLOWS:
            fact = self.annual.fact(metric, self.fy0)
            recent[metric] = (_with_note(fact, LATEST_IS_10K) if fact is not None else
                              self.missing(metric, self.fy0, f"no figure for the fiscal year ending {self.fy0}"))
        for metric in BALANCES:
            fact = self.annual.fact(metric, self.fy0)
            recent[metric] = fact or self.missing(metric, self.fy0, f"no figure at the fiscal year end {self.fy0}")
        recent["shares"] = self.annual.latest("shares") or self.missing("shares", self.fy0, "no share count in the "
                                                                        "annual data", unit="shares")
        return recent


def recent_figures(annual: CompanyData, latest, settings: dict) -> dict[str, Fact]:
    """The latest figures of one company, keyed by line item (see the module docstring). `annual` is the resolved
    annual data; `latest` is a resolver of the same company facts that also reads `quarterly_forms`."""
    return _Latest(annual, latest, settings).run()
