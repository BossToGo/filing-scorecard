"""The latest figures: twelve months to the latest quarterly report, and the latest balance sheet. Owner: A.
Slice S2c (issue #71, item 1). Called by `src.data.resolver.resolve`, which stores the result in `CompanyData.recent`.

1. The latest 10-Q: the latest end date of any 10-Q (or 10-Q/A) period after the latest fiscal year end, under the
   revenue, net income or operating cash flow tags. None: the 10-K is the latest report, so the twelve months are
   that fiscal year and the balances those of its fiscal year end.
2. Twelve months to that 10-Q (revenue, net income, operating cash flow, capital expenditure):

       last fiscal year (10-K) + this year's year to date (10-Q) − last year's year to date (same 10-Q)

   - this year's year to date starts the day after the fiscal year end and uses the fiscal-year figure's own tag
     (the definitions may differ between tags); after a change of fiscal year end there is none: missing;
   - last year's is the comparison column of the same 10-Q: it starts on the fiscal year's first day and covers the
     same quarters (its length within `ytd_length_tolerance_days` of this year's);
   - if that comparison column was restated (it differs from its first filing by more than `restatement_warning`),
     the 10-K year is on the earlier basis and the sum would mix two bases: missing (S&P Global, 2026);
   - a period that is not 364 to 366 days long says so; the fiscal-year figure's own note is kept; a negative
     payment is flagged (SIGN) in the note.
   Fiscal years still come from the 10-K alone, so the "twelve months ended" totals of Amazon's 10-Qs are never a
   year, and a 10-Q twelve-month total is never a year to date.
3. The latest balance sheet, at the 10-Q's period end: financial debt by the annual rules (none in the 10-Q: the
   debt at the fiscal year end, said in the note); minority interest reported in the 10-Q, else nil only if the
   fiscal year end has none (or 0), else missing, and an untagged one is noted (MINORITY_UNTAGGED); shares from the
   cover page of a 10-Q for that quarter, else the latest annual figure, said in the note.

Any part missing makes the figure `missing` with its reason, never zero. Warnings about these figures go into their
notes, never into `CompanyData.warnings`, which the gates read.
"""

from __future__ import annotations

import dataclasses
from datetime import date, timedelta
from typing import TYPE_CHECKING

from src.contracts import CompanyData, Fact
from src.data.filings import FISCAL_YEAR_ITEMS, filing_order, money, relative_difference

if TYPE_CHECKING:  # only for the type hint: the resolver imports this module
    from src.data.resolver import _Resolver

FLOWS = ("revenue", "net_income", "operating_cash_flow", "capital_expenditure")
LATEST_IS_10K = "the 10-K is the latest report (no 10-Q after it), so the last twelve months are this fiscal year"


def _days(e: dict) -> int:
    return (date.fromisoformat(e["end"]) - date.fromisoformat(e["start"])).days


def _with_note(fact: Fact, extra: str) -> Fact:
    return dataclasses.replace(fact, note="; ".join(part for part in (fact.note, extra) if part))


class _Latest:
    def __init__(self, annual: CompanyData, reader: _Resolver, settings: dict):
        # `reader` is a resolver of the same company facts that also reads the 10-Qs (balance-sheet rules only).
        self.annual, self.reader, self.settings = annual, reader, settings
        self.quarterly = set(settings["quarterly_forms"])
        years = annual.fiscal_years("revenue")
        self.fy0 = years[-1] if years else None

    def missing(self, metric: str, end: date, reason: str, unit: str = "USD") -> Fact:
        return Fact(metric, None, unit, None, end, "missing", None, None, None, None, self.annual.retrieved, reason)

    def quarterly_entries(self, tag: str) -> list[dict]:
        return [e for e in self.reader.us_gaap.get(tag, {}).get("units", {}).get("USD", [])
                if e.get("form") in self.quarterly and "start" in e]

    def latest_10q(self) -> tuple[date, set[str]] | None:
        """The period end of the latest 10-Q after the latest fiscal year, and the accession numbers of the 10-Qs
        (and 10-Q/As) for that quarter. Any period counts, not only a year to date starting the next day, so a later
        10-Q is never hidden behind the 10-K (review of PR #72)."""
        later = [e for metric in FISCAL_YEAR_ITEMS for tag in self.reader.spec(metric)["tags"]
                 for e in self.quarterly_entries(tag) if date.fromisoformat(e["end"]) > self.fy0]
        if not later:
            return None
        q_end = max(date.fromisoformat(e["end"]) for e in later)
        return q_end, {e["accn"] for e in later if date.fromisoformat(e["end"]) == q_end}

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
        tag, start = year.tag, self.fy0 + timedelta(days=1)
        entries = self.quarterly_entries(tag)
        current = [e for e in entries if e["start"] == start.isoformat() and e["end"] == q_end.isoformat()]
        if not current:
            return self.missing(metric, q_end, f"no year to date to {q_end} under {tag} starting {start} (the day "
                                               f"after the fiscal year end {self.fy0}) in a 10-Q; the fiscal year "
                                               f"uses {tag}, so the twelve months cannot be worked out")
        ytd = max(current, key=filing_order)
        days = _days(ytd)
        columns = [e for e in entries if e["accn"] == ytd["accn"] and e["start"] == year.period_start.isoformat()
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
        notes = []
        first = min((e for e in entries if e["start"] == prior["start"] and e["end"] == prior["end"]),
                    key=filing_order)
        if first["val"] != prior["val"]:
            if relative_difference(first["val"], prior["val"]) > self.settings["restatement_warning"]:
                return self.missing(metric, q_end, (
                    f"last year's year to date to {prior_end} under {tag} was first filed as {money(first['val'])} "
                    f"({first['accn']}, {first['filed']}) and is restated to {money(prior['val'])} in the 10-Q "
                    f"{ytd['accn']}; the fiscal year from the 10-K ({money(year.value)}) is on the earlier basis, so "
                    "the sum would mix two bases: the twelve months cannot be worked out"))
            notes.append(f"last year's year to date first filed {money(first['val'])} ({first['accn']}), "
                         f"{money(prior['val'])} in this 10-Q: within {self.settings['restatement_warning']:.0%}, used")
        value, period_start = year.value + ytd["val"] - prior["val"], prior_end + timedelta(days=1)
        length = (q_end - period_start).days + 1
        if not 364 <= length <= 366:
            notes.append(f"the period covers {length} days, not a calendar year: the company's quarters do not end on "
                         "the same day each year")
        if self.reader.spec(metric).get("outflow") and value < 0:
            notes.append(f"SIGN: the twelve months are negative ({money(value)}); a payment is filed as a positive "
                         "amount, check the filings")
        if year.note:
            notes.append(f"fiscal-year figure: {year.note}")
        formula = (f"last twelve months = fiscal year to {self.fy0} ({tag} {money(year.value)}, {year.form} "
                   f"{year.accession}) + year to date to {q_end} ({tag} {money(ytd['val'])}, {ytd['form']} "
                   f"{ytd['accn']}) − year to date to {prior_end} ({tag} {money(prior['val'])}, same {ytd['form']})")
        # `filed` is the 10-Q's filing date: the figure is as of that report (tag, form and accession stay empty, as
        # for every derived figure; the three sources are in the note).
        return Fact(metric, value, "USD", period_start, q_end, "derived", None, None, None,
                    date.fromisoformat(ytd["filed"]), self.annual.retrieved, "; ".join([formula, *notes]))

    # --- the latest balance sheet ---------------------------------------------------------------------------------

    def debt(self, q_end: date) -> Fact:
        (debt, _), raised = self.reader.collect_warnings(self.reader.debt, q_end)
        debt = _with_note(debt, "; ".join(raised))
        year = self.annual.fact("financial_debt", self.fy0)
        if debt.kind == "missing" and year is not None and year.kind != "missing":
            # Like the share count: the latest figure there is, dated and said (Igor, 27 November, review of #72).
            return _with_note(year, f"the latest quarterly report (to {q_end}) gives no debt ({debt.note}): the "
                                    f"debt at the fiscal year end {self.fy0} is used")
        return debt

    def minority(self, q_end: date) -> Fact:
        spec = self.reader.spec("minority_interest")
        fact, raised = self.reader.collect_warnings(self.reader.reported, "minority_interest", spec, q_end)
        if fact is not None:
            return _with_note(fact, "; ".join(raised))
        tags, year = ", ".join(spec["tags"]), self.annual.fact("minority_interest", self.fy0)
        if year is None or year.kind == "missing":
            why = year.note if year is not None else "none"
            return self.missing("minority_interest", q_end, f"no {tags} in the latest quarterly report (to {q_end}), "
                                                            f"and the figure at the fiscal year end {self.fy0} is "
                                                            f"missing too ({why}): not treated as nil (SPEC §8.3)")
        if year.kind == "reported" and year.value != 0:
            return self.missing("minority_interest", q_end, f"{year.tag} {money(year.value)} ({year.accession}) is "
                                                            f"reported at the fiscal year end {self.fy0} but not in "
                                                            f"the latest quarterly report (to {q_end}): not treated "
                                                            "as nil (SPEC §8.3)")
        at_year_end = "the 10-K reports 0" if year.kind == "reported" else "none is reported"
        nil = Fact("minority_interest", 0, "USD", None, q_end, "assumption", None, None, None, None,
                   self.annual.retrieved, f"not reported under {tags} in the latest quarterly report (to {q_end}), "
                                          f"and {at_year_end} at the fiscal year end {self.fy0}: treated as nil "
                                          "(SPEC §8.3)")
        return _with_note(nil, self.untagged_minority(q_end))

    def untagged_minority(self, q_end: date) -> str:
        """The annual MINORITY_UNTAGGED check at the quarter end: total equity above equity, no minority interest."""
        total, _ = self.reader.collect_warnings(self.reader.reported, "total_equity",
                                                self.reader.spec("total_equity"), q_end)
        equity, _ = self.reader.collect_warnings(self.reader.reported, "equity", self.reader.spec("equity"), q_end)
        if (total is not None and equity is not None and total.kind == equity.kind == "reported"
                and total.value - equity.value > self.settings["minority_untagged_warning"] * abs(equity.value)):
            return (f"MINORITY_UNTAGGED: {q_end}: total equity {money(total.value)} is above equity "
                    f"{money(equity.value)} but no minority interest is reported, so none is subtracted (SPEC §8.3)")
        return ""

    def shares(self, q_end: date, accessions: set[str]) -> Fact:
        tag = self.reader.map["shares"]["cover_tag"]
        cover = [e for e in self.reader.dei.get(tag, {}).get("units", {}).get("shares", [])
                 if e["accn"] in accessions]  # any 10-Q or 10-Q/A for the latest quarter
        if cover:
            e = max(cover, key=lambda e: (filing_order(e), e["end"]))
            return Fact("shares", e["val"], "shares", None, date.fromisoformat(e["end"]), "reported", f"dei:{tag}",
                        e["form"], e["accn"], date.fromisoformat(e["filed"]), self.annual.retrieved,
                        "cover page of the latest quarterly report")
        annual = self.annual.latest("shares")
        why = f"the latest quarterly report (to {q_end}) has no cover-page share count"
        if annual is None:
            return self.missing("shares", q_end, f"{why}, nor has the annual data", unit="shares")
        return _with_note(annual, f"{why}: the latest annual figure is used")

    # --- all of them ------------------------------------------------------------------------------------------------

    def run(self) -> dict[str, Fact]:
        if self.fy0 is None:
            return {}  # no annual figures at all (NO_ANNUAL_DATA or NON_USD): nothing to start from
        latest = self.latest_10q()
        if latest is None:
            return self.from_the_10k()
        q_end, accessions = latest
        recent = {metric: self.twelve_months(metric, q_end) for metric in FLOWS}
        recent["financial_debt"] = self.debt(q_end)
        recent["minority_interest"] = self.minority(q_end)
        recent["shares"] = self.shares(q_end, accessions)
        return recent

    def from_the_10k(self) -> dict[str, Fact]:
        recent = {}
        for metric in FLOWS:
            fact = self.annual.fact(metric, self.fy0)
            recent[metric] = (_with_note(fact, LATEST_IS_10K) if fact is not None else
                              self.missing(metric, self.fy0, f"no figure for the fiscal year ending {self.fy0}"))
        for metric in ("financial_debt", "minority_interest"):
            fact = self.annual.fact(metric, self.fy0)
            recent[metric] = fact or self.missing(metric, self.fy0, f"no figure at the fiscal year end {self.fy0}")
        recent["shares"] = self.annual.latest("shares") or self.missing("shares", self.fy0, "no share count in the "
                                                                        "annual data", unit="shares")
        return recent


def recent_figures(annual: CompanyData, reader: _Resolver, settings: dict) -> dict[str, Fact]:
    """The latest figures of one company, keyed by line item (see the module docstring). `annual` is the resolved
    annual data; `reader` is a resolver of the same company facts that also reads `quarterly_forms`."""
    return _Latest(annual, reader, settings).run()
