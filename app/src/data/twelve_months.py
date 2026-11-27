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
     the 10-K year may be on another basis and the sum could mix two: missing (S&P Global, 2026). This is careful
     on purpose: CrowdStrike's 10-K was itself restated, so its figure could have been worked out;
   - a period that is not 364 to 366 days long says so (on both paths); the fiscal-year figure's own note is kept;
     a negative payment is flagged (SIGN) in the note.
   Fiscal years still come from the 10-K alone, so the "twelve months ended" totals of Amazon's 10-Qs are never a
   year, and a 10-Q twelve-month total is never a year to date.
3. The latest balance sheet, at the 10-Q's period end: financial debt by the annual rules; minority interest
   reported in the 10-Q, else nil only if the fiscal year end has none (or 0), and an untagged one is noted
   (MINORITY_UNTAGGED); shares from the cover page of a 10-Q for that quarter. When the 10-Q has none of these, the
   figure at the fiscal year end is used, dated and said in the note (never nil, never a guess).
4. When the SEC's filing list (submissions) names a later 10-Q than its company facts hold, every figure says so.

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


def _length_note(start: date | None, end: date) -> str:
    """"" for a period of 364 to 366 days (counted inclusively), else a sentence saying how long it is."""
    if start is None:
        return ""
    length = (end - start).days + 1
    if 364 <= length <= 366:
        return ""
    return f"the period covers {length} days, not a calendar year: the company's quarters do not end on the same day " \
           "each year"


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

    def latest_10q(self) -> tuple[date, set[str], date] | None:
        """The period end of the latest 10-Q after the latest fiscal year, the accession numbers of the 10-Qs (and
        10-Q/As) for that quarter, and the latest of their filing dates. Any period counts, not only a year to date
        starting the next day, so a later 10-Q is never hidden behind the 10-K (review of PR #72)."""
        later = [e for metric in FISCAL_YEAR_ITEMS for tag in self.reader.spec(metric)["tags"]
                 for e in self.quarterly_entries(tag) if date.fromisoformat(e["end"]) > self.fy0]
        if not later:
            return None
        q_end = max(date.fromisoformat(e["end"]) for e in later)
        quarter = [e for e in later if date.fromisoformat(e["end"]) == q_end]
        return q_end, {e["accn"] for e in quarter}, max(date.fromisoformat(e["filed"]) for e in quarter)

    def unseen_10q(self, used_filed: date | None) -> str:
        """A note when the SEC's filing list names a 10-Q filed after the report used that its company facts do not
        hold yet (Southern Company, NextEra in November 2026). The demo's saved filing lists hold 10-Ks only."""
        recent = self.reader.submissions.get("filings", {}).get("recent", {})
        listed = [(day, accn) for form, day, accn in zip(recent.get("form", []), recent.get("filingDate", []),
                                                         recent.get("accessionNumber", []))
                  if form in self.quarterly and (used_filed is None or date.fromisoformat(day) > used_filed)]
        if not listed:
            return ""
        known = {e["accn"] for concept in self.reader.us_gaap.values()
                 for entries in concept.get("units", {}).values() for e in entries}
        unseen = sorted((day, accn) for day, accn in listed if accn not in known)
        if not unseen:
            return ""
        day, accn = unseen[-1]
        return (f"the 10-Q filed {day} ({accn}) is not yet in the SEC's company facts: this figure is from an "
                "earlier report")

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
        entries = self.quarterly_entries(year.tag)
        ytd, prior, notes = self.year_to_date(year, entries, q_end)
        if prior is None:
            return self.missing(metric, q_end, notes)  # `notes` holds the reason
        value, period_start = year.value + ytd["val"] - prior["val"], date.fromisoformat(prior["end"]) + timedelta(1)
        notes += [_length_note(period_start, q_end), self.sign_note(metric, value),
                  f"fiscal-year figure: {year.note}" if year.note else ""]
        formula = (f"last twelve months = fiscal year to {self.fy0} ({year.tag} {money(year.value)}, {year.form} "
                   f"{year.accession}) + year to date to {q_end} ({year.tag} {money(ytd['val'])}, {ytd['form']} "
                   f"{ytd['accn']}) − year to date to {prior['end']} ({year.tag} {money(prior['val'])}, same "
                   f"{ytd['form']})")
        # `filed` is the 10-Q's filing date: the figure is as of that report (tag, form and accession stay empty, as
        # for every derived figure; the three sources are in the note).
        note = "; ".join(n for n in [formula, *notes] if n)
        return Fact(metric, value, "USD", period_start, q_end, "derived", None, None, None,
                    date.fromisoformat(ytd["filed"]), self.annual.retrieved, note)

    def year_to_date(self, year: Fact, entries: list[dict], q_end: date) -> tuple[dict | None, dict | None, list | str]:
        """(this year's year to date, last year's, a list of notes), or (…, None, the reason as a str)."""
        tag, start = year.tag, self.fy0 + timedelta(days=1)
        current = [e for e in entries if e["start"] == start.isoformat() and e["end"] == q_end.isoformat()]
        if not current:
            return None, None, (f"no year to date to {q_end} under {tag} starting {start} (the day after the fiscal "
                                f"year end {self.fy0}) in a 10-Q; the fiscal year uses {tag}, so the twelve months "
                                "cannot be worked out")
        ytd = max(current, key=filing_order)
        prior, reason = self.comparison_column(year, entries, ytd)
        if prior is None:
            return ytd, None, reason
        usable, note = self.restatement(year, entries, ytd, prior)
        if not usable:
            return ytd, None, note
        return ytd, prior, [note]

    def comparison_column(self, year: Fact, entries: list[dict], ytd: dict) -> tuple[dict | None, str]:
        """Last year's year to date in the same 10-Q, covering the same quarters, or (None, why not)."""
        days = _days(ytd)
        columns = [e for e in entries if e["accn"] == ytd["accn"] and e["start"] == year.period_start.isoformat()
                   and date.fromisoformat(e["end"]) < self.fy0]
        if not columns:
            return None, (f"the 10-Q {ytd['accn']} has no comparison column for last year's year to date under "
                          f"{year.tag}, so the twelve months cannot be worked out")
        prior = min(columns, key=lambda e: abs(_days(e) - days))
        if abs(_days(prior) - days) > self.settings["ytd_length_tolerance_days"]:
            return None, (f"last year's year to date in the 10-Q {ytd['accn']} covers {_days(prior)} days and this "
                          f"year's {days} days: not the same quarters, so the twelve months cannot be worked out")
        return prior, ""

    def restatement(self, year: Fact, entries: list[dict], ytd: dict, prior: dict) -> tuple[bool, str]:
        """(True, "" or a note) when the comparison column equals its first filing or is within 1% of it; else
        (False, the reason the twelve months cannot be worked out)."""
        first = min((e for e in entries if e["start"] == prior["start"] and e["end"] == prior["end"]),
                    key=filing_order)
        if first["val"] == prior["val"]:
            return True, ""
        limit = self.settings["restatement_warning"]
        if relative_difference(first["val"], prior["val"]) > limit:
            return False, (f"last year's year to date to {prior['end']} under {year.tag} was first filed as "
                    f"{money(first['val'])} ({first['accn']}, {first['filed']}) and is restated to "
                    f"{money(prior['val'])} in the 10-Q {ytd['accn']}; the fiscal year from the 10-K "
                    f"({money(year.value)}) may be on another basis, so the sum could mix two bases: the twelve months "
                    "cannot be worked out")
        return True, (f"last year's year to date first filed {money(first['val'])} ({first['accn']}), "
                      f"{money(prior['val'])} in this 10-Q: within {limit:.0%}, used")

    def sign_note(self, metric: str, value: float) -> str:
        if self.reader.spec(metric).get("outflow") and value < 0:
            return f"SIGN: the twelve months are negative ({money(value)}); a payment is filed as a positive amount, " \
                   "check the filings"
        return ""

    # --- the latest balance sheet ---------------------------------------------------------------------------------

    def fall_back(self, year: Fact, what: str, q_end: date) -> Fact:
        """The fiscal-year-end figure when the 10-Q has none, dated and said (Igor, 27 November, review of #72)."""
        return _with_note(year, f"the latest quarterly report (to {q_end}) gives no {what}: the figure at the fiscal "
                                f"year end {self.fy0} is used")

    def debt(self, q_end: date) -> Fact:
        (debt, _), raised = self.reader.collect_warnings(self.reader.debt, q_end)
        debt = _with_note(debt, "; ".join(raised))
        year = self.annual.fact("financial_debt", self.fy0)
        if debt.kind == "missing" and year is not None and year.kind != "missing":
            return self.fall_back(year, f"debt ({debt.note})", q_end)
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
            return self.fall_back(year, f"minority interest ({tags})", q_end)
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
        if annual is None:
            return self.missing("shares", q_end, f"the latest quarterly report (to {q_end}) has no cover-page share "
                                                 "count, nor has the annual data", unit="shares")
        return _with_note(annual, f"the latest quarterly report (to {q_end}) has no cover-page share count: the "
                                  "latest annual figure is used")

    # --- all of them ------------------------------------------------------------------------------------------------

    def run(self) -> dict[str, Fact]:
        if self.fy0 is None:
            return {}  # no annual figures at all (NO_ANNUAL_DATA or NON_USD): nothing to start from
        latest = self.latest_10q()
        if latest is None:
            recent, used_filed = self.from_the_10k(), self.annual.latest_10k_filed
        else:
            q_end, accessions, used_filed = latest
            recent = {metric: self.twelve_months(metric, q_end) for metric in FLOWS}
            recent["financial_debt"] = self.debt(q_end)
            recent["minority_interest"] = self.minority(q_end)
            recent["shares"] = self.shares(q_end, accessions)
        unseen = self.unseen_10q(used_filed)
        return {metric: _with_note(fact, unseen) for metric, fact in recent.items()}

    def from_the_10k(self) -> dict[str, Fact]:
        recent = {}
        for metric in FLOWS:
            fact = self.annual.fact(metric, self.fy0)
            recent[metric] = (_with_note(fact, "; ".join(n for n in (LATEST_IS_10K, _length_note(fact.period_start,
                                                                                              fact.period_end)) if n))
                              if fact is not None else
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
