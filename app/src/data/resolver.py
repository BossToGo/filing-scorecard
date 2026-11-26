"""Line-item resolver (SPEC §5, §6). Owner: A. Slice S2.

    from src.data.resolver import resolve
    data = resolve("KO", companyfacts_json, submissions_json, retrieved)     # -> CompanyData

Turns the SEC's company facts into `CompanyData`: for each line item of `tag_map.yaml` and each of the latest
`fiscal_years` fiscal years (settings.yaml), one `Fact` with its source. Pure: no network. The rules of SPEC §5.3:
1. only Form 10-K and 10-K/A; a flow covers 350 to 380 days (53-week years kept; nine months never read as a year);
2. the fiscal year comes from the period end date, never from the `fy` label; after a change of fiscal year end,
   a 12-month period overlapping a later fiscal year is left out (FY_CHANGE);
3. balances are taken at the fiscal year end date itself;
4. a period filed several times: the latest filing is used (an amendment wins on the same day), the original of
   the same period is kept in the note, a difference above 1% is a warning;
5. only US dollars: a figure filed only in another currency is missing and flagged;
6. nothing is added up from segments: no company-wide figure means `missing`;
7. tags are tried in order for every fiscal year; any other tag's different value is noted, above 1% flagged.
Amounts stay in USD exactly as filed. Missing figures are never zero and say why; a derived figure with a missing
input stays missing.

Warnings in `CompanyData.warnings` start with a code, so the gates (slice S11) can act on them:
RESTATED, TAG_CONFLICT, TAG_SWITCH, NON_USD, FY_CHANGE, DERIVED, DEBT_CHECK, DEBT_INCOMPLETE, AVERAGE_SHARES,
SIGN, NO_ANNUAL_DATA.

Shares are stored at their own date (the cover page of the latest annual report): use `data.latest("shares")`.

The latest figures (slice S2c, issue #71 item 1) are in `data.recent`, worked out by src/data/twelve_months.py from
the 10-Qs (`quarterly_forms`); they change nothing above: the fiscal years and their figures come from the 10-K alone.
"""

from __future__ import annotations

import dataclasses
from datetime import date, datetime, timedelta
from functools import lru_cache
from pathlib import Path

import yaml

from src.contracts import CompanyData, Fact
from src.data.filings import FISCAL_YEAR_ITEMS
from src.data.filings import filing_order as _order
from src.data.filings import money as _money
from src.data.filings import relative_difference as _relative_difference
from src.data.twelve_months import recent_figures
from src.settings import load_settings

TAG_MAP_FILE = Path(__file__).with_name("tag_map.yaml")


@lru_cache(maxsize=1)
def load_tag_map(path: Path = TAG_MAP_FILE) -> dict:
    return yaml.safe_load(path.read_text(encoding="utf-8"))


def _source(fact: Fact) -> str:
    return f"{fact.tag} {_money(fact.value)} ({fact.accession})"


class _Resolver:
    def __init__(self, ticker, companyfacts, submissions, retrieved, settings, tag_map, years, forms=None):
        facts = (companyfacts or {}).get("facts", {})
        self.us_gaap, self.dei = facts.get("us-gaap", {}), facts.get("dei", {})
        self.ticker, self.submissions, self.retrieved = ticker, submissions, retrieved
        self.settings, self.map = settings, tag_map
        self.overrides = tag_map.get("overrides", {}).get(ticker, {})
        # The annual figures read only the annual forms (rule 1). The latest balance sheet (slice S2c) passes the
        # quarterly forms too and uses only the balance-sheet rules (`reported` for balances, `debt`): such a
        # resolver must never work out fiscal years, as it would read 10-Q twelve-month totals as years (Amazon).
        self.forms = set(forms or settings["annual_forms"])
        self.balance_sheet_only = forms is not None
        self.years = years or settings["fiscal_years"]
        self.items: dict[str, dict[date, Fact]] = {}
        self.warnings: list[str] = []

    # --- reading company facts ---------------------------------------------------------------------------------

    def _annual(self, tag: str, kind: str, unit: str = "USD", taxonomy: str = "us-gaap") -> dict[date, list[dict]]:
        """Annual-report entries of one tag and unit, grouped by period end date (rules 1 and 3)."""
        source = self.us_gaap if taxonomy == "us-gaap" else self.dei
        groups: dict[date, list[dict]] = {}
        for e in source.get(tag, {}).get("units", {}).get(unit, []):
            if e.get("form") not in self.forms:
                continue
            end = date.fromisoformat(e["end"])
            if kind == "flow":
                if "start" not in e:
                    continue
                days = (end - date.fromisoformat(e["start"])).days
                if not self.settings["flow_period_min_days"] <= days <= self.settings["flow_period_max_days"]:
                    continue
            elif "start" in e:
                continue
            groups.setdefault(end, []).append(e)
        return groups

    def _other_currencies(self, tags: list[str], kind: str, fy_end: date | None = None) -> list[str]:
        found = set()
        for tag in tags:
            for unit in self.us_gaap.get(tag, {}).get("units", {}):
                if unit != "USD" and (groups := self._annual(tag, kind, unit)) and (fy_end is None or fy_end in groups):
                    found.add(unit)
        return sorted(found)

    def spec(self, metric: str) -> dict:
        """The line item's entry in tag_map.yaml, with a company override of its tag order if there is one."""
        spec = self.map["line_items"][metric]
        override = self.overrides.get(metric)
        return {**spec, "tags": override["tags"], "override": override["reason"]} if override else spec

    # --- facts --------------------------------------------------------------------------------------------------

    def _missing(self, metric, fy_end, reason, unit="USD") -> Fact:
        return Fact(metric, None, unit, None, fy_end, "missing", None, None, None, None, self.retrieved, reason)

    def _derived(self, metric, value, fy_end, formula, unit="USD") -> Fact:
        return Fact(metric, value, unit, None, fy_end, "derived", None, None, None, None, self.retrieved, formula)

    def reported(self, metric: str, spec: dict, fy_end: date, unit: str = "USD") -> Fact | None:
        """The first tag with an annual value for this fiscal year (rule 7), or None."""
        kind = spec["kind"]
        candidates = []
        for tag in spec["tags"]:
            entries = self._annual(tag, kind, unit).get(fy_end)
            if entries:
                latest = max(entries, key=_order)
                original = min((e for e in entries if e.get("start") == latest.get("start")), key=_order)
                candidates.append((tag, latest, original))
        if not candidates:
            return None
        tag, latest, original = candidates[0]
        value, notes = latest["val"], []
        if spec.get("override"):
            notes.append(f"company-specific tag order: {spec['override']}")
        if original is not latest and original["val"] != value:
            notes.append(f"restated: first filed {_money(original['val'])} ({original['accn']}, {original['filed']}), "
                         f"latest {_money(value)} ({latest['accn']}, {latest['filed']})")
            if _relative_difference(value, original["val"]) > self.settings["restatement_warning"]:
                self.warnings.append(f"RESTATED: {metric} {fy_end}: first filed {_money(original['val'])}, "
                                     f"now {_money(value)}; both on the sources page")
        for other_tag, other, _ in candidates[1:]:
            if other["val"] != value:
                notes.append(f"also filed under {other_tag}: {_money(other['val'])}")
                differs = (_relative_difference(value, other["val"]) > self.settings["tag_conflict_warning"]
                           and spec.get("same_definition", True))  # fallbacks of another definition: noted only
                much_larger = ("later_larger_warning" in spec and value > 0
                               and other["val"] > value * (1 + spec["later_larger_warning"]))
                if (differs or much_larger) and not spec.get("override"):  # an override documents a difference
                    self.warnings.append(f"TAG_CONFLICT: {metric} {fy_end}: {tag} {_money(value)} used, "
                                         f"{other_tag} gives {_money(other['val'])}")
        if spec.get("outflow") and value < 0:
            self.warnings.append(f"SIGN: {metric} {fy_end} is negative ({_money(value)}); a payment is filed as a "
                                 "positive amount, check the filing")
        if spec.get("positive_only") and value < 0:  # e.g. interest expense: a ratio built on it would change sign
            self.warnings.append(f"SIGN: {metric} {fy_end} is negative ({_money(value)}); an expense is filed as a "
                                 "positive amount, so the figure is not used; check the filing")
            return self._missing(metric, fy_end, f"{tag} is filed as a negative amount ({_money(value)}, "
                                 f"{latest['accn']}): its sign cannot be relied on, so the figure is not used")
        return Fact(
            metric=metric,
            value=value,
            unit=unit,
            period_start=date.fromisoformat(latest["start"]) if kind == "flow" else None,
            period_end=fy_end,
            kind="reported",
            tag=tag,
            form=latest["form"],
            accession=latest["accn"],
            filed=date.fromisoformat(latest["filed"]),
            retrieved=self.retrieved,
            note="; ".join(notes),
        )

    def reported_or_missing(self, metric: str, spec: dict, fy_end: date, why_not_derived: str = "") -> Fact:
        fact = self.reported(metric, spec, fy_end)
        if fact is not None:
            return fact
        currencies = self._other_currencies(spec["tags"], spec["kind"], fy_end)
        if currencies:
            self.warnings.append(f"NON_USD: {metric} {fy_end} is filed in {', '.join(currencies)}, not US dollars")
            return self._missing(metric, fy_end, f"filed in {', '.join(currencies)}, not US dollars (SPEC §5.3.5)")
        reason = f"no annual 10-K value under {', '.join(spec['tags'])} for the fiscal year ending {fy_end}"
        return self._missing(metric, fy_end, reason + (f"; {why_not_derived}" if why_not_derived else ""))

    # --- fiscal years -----------------------------------------------------------------------------------------

    def fiscal_year_ends(self) -> list[date]:
        tags = [tag for metric in FISCAL_YEAR_ITEMS for tag in self.spec(metric)["tags"]]
        ends: set[date] = set()
        for tag in tags:
            ends.update(self._annual(tag, "flow"))
        if not ends:
            currencies = self._other_currencies(tags, "flow")
            if currencies:
                self.warnings.append(f"NON_USD: the company files its annual figures in {', '.join(currencies)}, not "
                                     "US dollars, so it is not supported (SPEC §5.3.5)")
            else:
                self.warnings.append("NO_ANNUAL_DATA: no annual 10-K figures found")
            return []
        kept: list[date] = []
        newer: date | None = None  # the period end looked at just before, kept or left out
        for end in sorted(ends, reverse=True):
            gap, newer = newer is not None and (newer - end).days > self.settings["flow_period_max_days"], end
            if gap:
                # A missing year (or a transition period filed on another form): "four years earlier" would span
                # more than four years, so the window ends at the gap (audit of 21 November 2026). The period left
                # out at a change of year end is not a gap: that case keeps its older years, flagged FY_CHANGE.
                self.warnings.append(f"FY_GAP: no annual 10-K figures between the fiscal years ending {end} and "
                                     f"{kept[-1]}: only the years after the gap are used")
                break
            if kept and (kept[-1] - end).days < self.settings["flow_period_min_days"]:
                self.warnings.append(f"FY_CHANGE: the 12-month period ending {end} overlaps the fiscal year ending "
                                     f"{kept[-1]}: the company changed its fiscal year end, so that period is left out")
                continue
            kept.append(end)
            if len(kept) == self.years:
                break
        return sorted(kept)

    # --- the whole company ------------------------------------------------------------------------------------

    def collect_warnings(self, rule, *args):
        """Run one rule (e.g. `self.debt`) and return (its result, the warnings it raised), taken out of
        `self.warnings`: the latest figures (slice S2c) keep their warnings in their notes, not in
        CompanyData.warnings."""
        before = len(self.warnings)
        result = rule(*args)
        raised = self.warnings[before:]
        del self.warnings[before:]
        return result, raised

    def run(self) -> CompanyData:
        if self.balance_sheet_only:
            raise RuntimeError("this resolver also reads 10-Qs: it serves the latest balance sheet only and must never "
                               "work out fiscal years (their twelve-month totals would be read as years)")
        fy_ends = self.fiscal_year_ends()
        derived_used: dict[str, list[date]] = {}
        for fy_end in fy_ends:
            for metric in self.map["line_items"]:
                spec = self.spec(metric)
                if spec.get("bridge"):
                    continue
                fact, why_not = self.reported(metric, spec, fy_end), ""
                if fact is None:
                    fact, why_not = self.derive(metric, fy_end)
                    if fact is not None and metric in ("gross_profit", "total_liabilities", "equity",
                                                       "depreciation_amortization"):
                        derived_used.setdefault(metric, []).append(fy_end)
                if fact is None:
                    fact = self.reported_or_missing(metric, spec, fy_end, why_not)
                self.items.setdefault(metric, {})[fy_end] = fact
            debt, current = self.debt(fy_end)
            self.items.setdefault("financial_debt", {})[fy_end] = debt
            self.items.setdefault("current_financial_debt", {})[fy_end] = current
        self.no_dividend_at_all(fy_ends)
        for metric, ends in derived_used.items():
            self.warnings.append(f"DERIVED: {metric} is calculated, not reported, for {', '.join(map(str, ends))}")
        self.tag_switches()
        if fy_ends:
            self.bridge_items(fy_ends[-1], fy_ends[-2] if len(fy_ends) > 1 else None)
            self.shares(fy_ends[-1])
        return self.company_data()

    def no_dividend_at_all(self, fy_ends: list[date]) -> None:
        """Plan Q1 (SPEC v2.4 §7): no dividend amount in any fiscal year and no sign of a dividend under any evidence
        tag (tag_map.yaml) means the company pays none: each year becomes nil, labelled. Otherwise nothing changes."""
        evidence = self.spec("dividends_paid").get("nil_without_evidence")
        facts = [self.items.get("dividends_paid", {}).get(end) for end in fy_ends]
        if not evidence or not facts or any(f is None or f.kind != "missing" or not f.note.startswith("no annual 10-K")
                                            for f in facts):
            return  # an amount in some year, or missing for another reason (e.g. not US dollars): left as it is
        start = fy_ends[0] - timedelta(days=self.settings["flow_period_max_days"])
        for tag in evidence:
            for entries in self.us_gaap.get(tag, {}).get("units", {}).values():
                if any(e.get("form") in self.forms and start < date.fromisoformat(e["end"]) <= fy_ends[-1]
                       and (e.get("val") or 0) > 0 for e in entries):
                    return  # a sign of a dividend: the years stay missing, so the checks show "insufficient data"
        note = (f"no dividend under any of {', '.join(evidence)} in the five fiscal years: not reported, treated as "
                "nil, so no dividend paid (SPEC §7, plan Q1)")
        for end in fy_ends:
            self.items["dividends_paid"][end] = Fact("dividends_paid", 0, "USD", None, end, "assumption", None, None,
                                                     None, None, self.retrieved, note)
        self.warnings.append("NIL_DIVIDEND: no dividend reported in the five fiscal years: treated as nil, so the "
                             "dividend area shows \"no dividend paid\" (plan Q1)")

    def derive(self, metric: str, fy_end: date) -> tuple[Fact | None, str]:
        """SPEC §6 derivations, used only when the line item is not reported: (fact, "") or (None, why not)."""

        def value(name):
            fact = self.items.get(name, {}).get(fy_end)
            return None if fact is None or fact.value is None else fact.value

        def not_derivable(*names):
            missing = [n for n in names if value(n) is None]
            return None, f"not derivable: {' and '.join(missing)} missing"

        if metric == "gross_profit":
            revenue, cost = value("revenue"), value("cost_of_revenue")
            if revenue is None or cost is None:
                return not_derivable("revenue", "cost_of_revenue")
            return self._derived(metric, revenue - cost, fy_end, "revenue − cost_of_revenue"), ""
        if metric == "equity":
            total = self.reported("total_equity", self.spec("total_equity"), fy_end)
            if total is None:
                return None, "not derivable: no total equity reported either"
            minority = self.reported("minority_interest", self.spec("minority_interest"), fy_end)
            if minority is not None:
                return self._derived(metric, total.value - minority.value, fy_end,
                                     f"total_equity ({_source(total)}) − minority_interest ({_source(minority)})"), ""
            sign = self._minority_sign(fy_end)
            if sign:
                return None, f"not derivable: total equity includes non-controlling interests ({sign}) that are " \
                             "not reported for this year"
            return self._derived(metric, total.value, fy_end, f"total_equity ({_source(total)}); it includes any "
                                 "non-controlling interests, none reported separately"), ""
        if metric == "total_equity":
            equity = value("equity")
            if equity is None:
                return not_derivable("equity")
            minority = self.reported("minority_interest", self.spec("minority_interest"), fy_end)
            if minority is not None:
                return self._derived(metric, equity + minority.value, fy_end,
                                     f"equity + minority_interest ({_source(minority)})"), ""
            return self._derived(metric, equity, fy_end,
                                 "equity; no non-controlling interests reported, so none are added"), ""
        if metric == "total_liabilities":
            assets, total_equity = value("total_assets"), value("total_equity")
            if assets is None or total_equity is None:
                return not_derivable("total_assets", "total_equity")
            less = self.spec(metric).get("less")
            temporary = self.reported(f"{metric} (temporary equity)", {"kind": "instant", "tags": less,
                                                                        "same_definition": False}, fy_end) if less else None
            if temporary is not None:
                return self._derived(metric, assets - total_equity - temporary.value, fy_end,
                                     f"total_assets − total_equity − temporary equity ({_source(temporary)})"), ""
            return self._derived(metric, assets - total_equity, fy_end, "total_assets − total_equity"), ""
        parts = self.spec(metric).get("parts")
        if parts:  # e.g. depreciation and amortisation: the sum of its parts when no combined tag is reported
            kind = self.spec(metric)["kind"]
            found = {tag: self.reported(f"{metric} ({tag})", {"kind": kind, "tags": [tag]}, fy_end) for tag in parts}
            if found[parts[0]] is None:
                return None, f"not derivable: {parts[0]} not reported either"
            notes = []
            for tag, fact in found.items():
                if fact is not None:
                    notes.append(_source(fact))
                    continue
                other_years = [end for end, entries in self._annual(tag, kind).items()
                               if end != fy_end and any(e["val"] for e in entries)]
                if other_years:  # a part that exists in other years is not assumed to be zero in this one
                    return None, f"not derivable: {tag} is reported for {max(other_years)} but not for this year"
                notes.append(f"{tag} not reported, counted as nil")
            total = sum(fact.value for fact in found.values() if fact is not None)
            return self._derived(metric, total, fy_end, " + ".join(notes) + "; the sum of these parts may be below "
                                 "the cash flow statement's line, which can hold other items"), ""
        return None, ""

    def _minority_sign(self, fy_end: date) -> str:
        """Why non-controlling interests seem to exist although none is reported at fy_end ("" if no sign)."""
        for tag in self.map["line_items"]["minority_interest"]["tags"]:
            other_years = [end for end in self._annual(tag, "instant") if end != fy_end]
            if other_years:
                return f"{tag} is reported for {max(other_years)}"
        profit = self._annual("ProfitLoss", "flow").get(fy_end)
        net = self._annual("NetIncomeLoss", "flow").get(fy_end)
        if profit and net and max(profit, key=_order)["val"] != max(net, key=_order)["val"]:
            return "ProfitLoss differs from NetIncomeLoss"
        return ""

    def tag_switches(self) -> None:
        """Warn when a line item's tag changes within the window: the definition may change between years."""
        for metric, by_year in self.items.items():
            parts = self.map["line_items"].get(metric, {}).get("parts")
            pseudo = " + ".join(parts) if parts else None  # a figure built from parts counts as its own "tag"
            used = [(end, fact.tag if fact.kind == "reported" else pseudo) for end, fact in sorted(by_year.items())
                    if fact.kind == "reported" or (pseudo and fact.kind == "derived")]
            if len({tag for _, tag in used}) > 1:
                parts = ", ".join(f"{tag} for {end}" for end, tag in used)
                self.warnings.append(f"TAG_SWITCH: {metric}: {parts}; the definition may differ between years")

    def debt(self, fy_end: date) -> tuple[Fact, Fact]:
        """Financial debt and its current part (SPEC §6; plan Q5; rules in tag_map.yaml). Operating leases out."""
        parts, override = self.map["debt"], self.overrides.get("debt", {})
        inside = override.get("short_term_inside_long_term_debt", False)

        def part(label, tags):  # the fallbacks differ by finance leases: noted, not warned (plan Q5)
            return self.reported(f"financial_debt ({label})",
                                 {"kind": "instant", "tags": tags, "same_definition": False}, fy_end)

        noncurrent = part("non-current", parts["long_term_noncurrent"])
        current = part("current maturities", parts["long_term_current"])
        total = part("total long-term", parts["long_term_total"])
        short_total = part("short-term borrowings", parts["short_term_total"])
        short_parts = [f for tag in parts["short_term_parts"] if (f := part(tag, [tag])) is not None]

        tolerance = self.settings["debt_check_warning"]

        def same_definition(a, b):  # the newer tag names include finance leases, the older ones do not (plan Q5)
            return ("CapitalLeaseObligations" in a.tag) == ("CapitalLeaseObligations" in b.tag)

        # A "total" smaller than its own non-current part is not a total (Seagate 2022: 964 against 5,062, audit of
        # 21 November 2026): it is flagged and left out, and the parts below are used.
        if (total is not None and noncurrent is not None and not inside and same_definition(total, noncurrent)
                and total.value < noncurrent.value * (1 - tolerance)):
            self.warnings.append(f"DEBT_CHECK: {fy_end}: {total.tag} {_money(total.value)} is below its non-current "
                                 f"part {_money(noncurrent.value)}, so it is not used as the total; check the 10-K")
            total = None
        comparable = total is not None and noncurrent is not None and same_definition(total, noncurrent)

        notes = [f"company-specific: {override['reason']}"] if inside else []
        if total is not None:
            long_term = total.value
            notes.append(_source(total))
            if noncurrent is not None and current is not None and not inside:
                parts_sum = noncurrent.value + current.value
                if _relative_difference(total.value, parts_sum) > tolerance:
                    self.warnings.append(f"DEBT_CHECK: {fy_end}: total long-term debt {_money(total.value)} differs "
                                         f"from non-current + current {_money(parts_sum)}; check the 10-K")
        elif noncurrent is not None and current is not None:
            long_term = noncurrent.value + current.value
            notes += [_source(noncurrent), _source(current)]
        elif noncurrent is not None:
            long_term = noncurrent.value
            notes += [_source(noncurrent), "no current portion reported"]
            self.warnings.append(f"DEBT_INCOMPLETE: {fy_end}: no current portion of long-term debt reported; debt "
                                 "may be understated")
        else:
            long_term = None

        if inside and total is not None and noncurrent is not None:
            maturities, maturities_note = total.value - noncurrent.value, \
                f"current debt on the balance sheet = {total.tag} − {noncurrent.tag}"
        elif current is not None:
            maturities, maturities_note = current.value, _source(current)
        elif comparable:
            maturities, maturities_note = total.value - noncurrent.value, f"{total.tag} − {noncurrent.tag}"
        else:
            maturities, maturities_note = None, ""
        why_no_current = "current maturities of long-term debt not reported"
        if maturities is None and total is not None and noncurrent is not None and not comparable:
            # Micron: LongTermDebt (without finance leases) minus LongTermDebtAndCapitalLeaseObligations (with them)
            # would be negative. The difference of two definitions is not a current part.
            why_no_current = (f"not derivable: of {total.tag} and {noncurrent.tag} only one includes finance leases, "
                              "so their difference is not the current part of the debt")
        # Only a long-term total and no current maturities: DebtCurrent (all current debt) gives the current part,
        # and the principal (DebtInstrumentCarryingAmount) tells whether the total already includes it (Tesla's
        # LongTermDebt does not). Without a principal that settles it, the debt is flagged.
        all_current = None
        if maturities is None and total is not None and noncurrent is None and not inside:
            all_current = part("all current debt", parts.get("current_total", []))
        total_is_noncurrent = False
        if all_current is not None:
            principal = part("principal", parts.get("principal_check", []))

            def close(value):
                return principal is not None and principal.value and \
                    _relative_difference(value, principal.value) <= tolerance

            if close(total.value + all_current.value) and not close(total.value):
                total_is_noncurrent = True
                long_term = total.value + all_current.value
                notes.append(f"{_source(all_current)} ({total.tag} is only the non-current part: the sum is within "
                             f"{tolerance:.0%} of the principal {_source(principal)})")
            elif not close(total.value):
                self.warnings.append(f"DEBT_CHECK: {fy_end}: cannot tell whether {total.tag} {_money(total.value)} "
                                     f"includes the current debt {_source(all_current)}; check the 10-K")

        # Short-term borrowings equal (within the tolerance) to the current maturities of long-term debt are that same
        # balance-sheet line filed under a second name, whether the maturities are tagged (AMD, IBM, T-Mobile: audit of
        # 21 November 2026) or are total − non-current (Marvell). They are already counted, so nothing is added.
        short_is_current_part = (not inside and short_total is not None and short_total.value > 0
                                 and maturities is not None and maturities > 0
                                 and _relative_difference(maturities, short_total.value) <= tolerance)
        if inside:
            short_term, short_notes = 0, ["short-term borrowings classified inside long-term debt"]
        elif short_is_current_part:
            short_term, short_notes = 0, [f"nothing added for {_source(short_total)}: it is the current part of "
                                          f"long-term debt ({maturities_note}), already counted inside it"]
        elif total_is_noncurrent:
            short_term, short_notes = 0, ["short-term borrowings are inside DebtCurrent"]
        elif short_total is not None:
            short_term, short_notes = short_total.value, [_source(short_total)]
        elif short_parts:
            short_term, short_notes = sum(f.value for f in short_parts), [_source(f) for f in short_parts]
        else:
            short_term, short_notes = 0, ["no short-term borrowings reported"]

        if long_term is None:
            found = [_source(f) for f in [short_total, *short_parts, current] if f is not None]
            reason = ("no long-term debt tag (" + ", ".join([*parts["long_term_total"], *parts["long_term_noncurrent"]])
                      + ")" + (f"; found only {', '.join(found)}, which alone would understate debt" if found else ""))
            return (self._missing("financial_debt", fy_end, reason),
                    self._missing("current_financial_debt", fy_end, reason))
        debt = self._derived("financial_debt", long_term + short_term, fy_end, " + ".join(notes + short_notes))
        if all_current is not None:
            current_debt = self._derived("current_financial_debt", all_current.value, fy_end,
                                         f"{_source(all_current)}: all current debt, short-term borrowings included")
        elif maturities is not None:
            current_debt = self._derived("current_financial_debt", maturities + short_term, fy_end,
                                         " + ".join([maturities_note, *short_notes]))
        else:
            return debt, self._missing("current_financial_debt", fy_end, why_no_current)
        if current_debt.value > debt.value:
            self.warnings.append(f"DEBT_CHECK: {fy_end}: current debt {_money(current_debt.value)} is larger than "
                                 f"total debt {_money(debt.value)}; check the 10-K")
        return debt, current_debt

    def bridge_items(self, fy0: date, previous: date | None = None) -> None:
        for metric in self.map["line_items"]:
            spec = self.spec(metric)
            if not spec.get("bridge"):
                continue
            fact = self.reported(metric, spec, fy0)
            if fact is None and metric == "minority_interest":
                fact = self._minority_gap(spec, fy0, previous)
            self.items.setdefault(metric, {})[fy0] = fact or Fact(
                metric, 0, "USD", None, fy0, "assumption", None, None, None, None, self.retrieved,
                f"not reported under {', '.join(spec['tags'])}, treated as nil (SPEC §8.3)")

    def _minority_gap(self, spec: dict, fy0: date, previous: date | None) -> Fact | None:
        """SPEC v2.3 §8.3, when no minority interest is reported for FY0: missing if it was reported for FY-1 (it
        cannot be assumed to have vanished); a record if total equity shows one; else None (treated as nil)."""
        for tag in spec["tags"]:
            before = self._annual(tag, "instant").get(previous) if previous else None
            if before:
                last = max(before, key=_order)
                return self._missing("minority_interest", fy0, f"{tag} {_money(last['val'])} ({last['accn']}) is "
                                     f"reported for {previous} but nothing for {fy0}: not treated as nil (SPEC §8.3)")
        total, equity = (self.items.get(name, {}).get(fy0) for name in ("total_equity", "equity"))
        if (total is not None and equity is not None and total.kind == equity.kind == "reported"
                and total.value - equity.value > self.settings["minority_untagged_warning"] * abs(equity.value)):
            self.warnings.append(
                f"MINORITY_UNTAGGED: {fy0}: total equity {_money(total.value)} is above equity {_money(equity.value)} "
                f"but no {', '.join(spec['tags'])} is reported, so none is subtracted in the valuation (SPEC §8.3)")
        return None

    def shares(self, fy0: date) -> None:
        tags = self.map["shares"]
        every_cover = [e for entries in self._annual(tags["cover_tag"], "instant", "shares", "dei").values()
                       for e in entries]
        # Only the cover page of the latest annual report counts: dated after the fiscal year end, within a window.
        cover = [e for e in every_cover
                 if 0 < (date.fromisoformat(e["end"]) - fy0).days <= self.settings["cover_page_max_days"]]
        stale = (f"; the latest cover-page count ({max(every_cover, key=_order)['end']}, "
                 f"{max(every_cover, key=_order)['accn']}) is not from the latest annual report"
                 if every_cover and not cover else "")
        if cover:
            latest = max(cover, key=_order)
            when = date.fromisoformat(latest["end"])
            self.items["shares"] = {when: Fact(
                "shares", latest["val"], "shares", None, when, "reported", f"dei:{tags['cover_tag']}", latest["form"],
                latest["accn"], date.fromisoformat(latest["filed"]), self.retrieved,
                "cover page of the latest annual report")}
            return
        average = self.reported("shares", {"kind": "flow", "tags": [tags["average_tag"]]}, fy0, unit="shares")
        if average is not None and average.value < self.settings["min_plausible_shares"]:
            self.items["shares"] = {fy0: self._missing(
                "shares", fy0, f"{tags['average_tag']} is {average.value:,} shares, implausibly few: probably filed in "
                f"millions{stale}", unit="shares")}
            return
        if average is not None:
            self.items["shares"] = {fy0: self._derived(
                "shares", average.value, fy0, f"diluted weighted average of the fiscal year ({_source(average)}), "
                f"not a period-end count{stale}", unit="shares")}
            self.warnings.append("AVERAGE_SHARES: the share count is the diluted average of the fiscal year, not a "
                                 "period-end figure")
            return
        self.items["shares"] = {fy0: self._missing("shares", fy0, f"no {tags['cover_tag']} on the cover page and no "
                                                                  f"{tags['average_tag']}{stale}", unit="shares")}

    def company_data(self) -> CompanyData:
        recent = self.submissions.get("filings", {}).get("recent", {})
        annual_dates = [d for f, d in zip(recent.get("form", []), recent.get("filingDate", [])) if f in self.forms]
        return CompanyData(
            ticker=self.ticker,
            cik=str(self.submissions["cik"]).zfill(10),
            name=self.submissions.get("name", self.ticker),
            sic=self.submissions.get("sic") or None,
            sic_description=self.submissions.get("sicDescription") or None,
            fiscal_year_end=self.submissions.get("fiscalYearEnd") or None,
            latest_10k_filed=date.fromisoformat(max(annual_dates)) if annual_dates else None,
            retrieved=self.retrieved,
            items=self.items,
            warnings=tuple(dict.fromkeys(self.warnings)),
        )


def resolve(ticker: str, companyfacts: dict | None, submissions: dict, retrieved: datetime | None = None, *,
            settings: dict | None = None, tag_map: dict | None = None, years: int | None = None) -> CompanyData:
    """CompanyData for one company from its SEC companyfacts and submissions JSON (SPEC §5, §6), with its latest
    figures in `recent` (slice S2c: twelve months to the latest 10-Q, latest balance sheet; src/data/twelve_months.py)."""
    symbol = ticker.strip().upper()
    settings = settings or load_settings()["data"]
    tag_map = tag_map or load_tag_map()
    annual = _Resolver(symbol, companyfacts, submissions, retrieved, settings, tag_map, years).run()
    latest = _Resolver(symbol, companyfacts, submissions, retrieved, settings, tag_map, years,
                       forms=[*settings["annual_forms"], *settings["quarterly_forms"]])
    return dataclasses.replace(annual, recent=recent_figures(annual, latest, settings))
