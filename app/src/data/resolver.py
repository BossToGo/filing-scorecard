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
"""

from __future__ import annotations

from datetime import date, datetime
from functools import lru_cache
from pathlib import Path

import yaml

from src.contracts import CompanyData, Fact
from src.settings import load_settings

TAG_MAP_FILE = Path(__file__).with_name("tag_map.yaml")
FISCAL_YEAR_ITEMS = ("revenue", "net_income", "operating_cash_flow")


@lru_cache(maxsize=1)
def load_tag_map(path: Path = TAG_MAP_FILE) -> dict:
    return yaml.safe_load(path.read_text(encoding="utf-8"))


def _relative_difference(a: float, b: float) -> float:
    if a == b:
        return 0.0
    return abs(a - b) / max(abs(a), abs(b))


def _money(value: float) -> str:
    return f"{value:,.0f}"


def _source(fact: Fact) -> str:
    return f"{fact.tag} {_money(fact.value)} ({fact.accession})"


def _order(e: dict) -> tuple:
    """Filing order: later filing date first; on the same day an amendment after the original; then accession."""
    return e["filed"], e.get("form") == "10-K/A", e["accn"]


class _Resolver:
    def __init__(self, ticker, companyfacts, submissions, retrieved, settings, tag_map, years):
        facts = (companyfacts or {}).get("facts", {})
        self.us_gaap, self.dei = facts.get("us-gaap", {}), facts.get("dei", {})
        self.ticker, self.submissions, self.retrieved = ticker, submissions, retrieved
        self.settings, self.map = settings, tag_map
        self.overrides = tag_map.get("overrides", {}).get(ticker, {})
        self.forms = set(settings["annual_forms"])
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
        for end in sorted(ends, reverse=True):
            if kept and (kept[-1] - end).days < self.settings["flow_period_min_days"]:
                self.warnings.append(f"FY_CHANGE: the 12-month period ending {end} overlaps the fiscal year ending "
                                     f"{kept[-1]}: the company changed its fiscal year end, so that period is left out")
                continue
            kept.append(end)
            if len(kept) == self.years:
                break
        return sorted(kept)

    # --- the whole company ------------------------------------------------------------------------------------

    def run(self) -> CompanyData:
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
                    if fact is not None and metric in ("gross_profit", "total_liabilities", "equity"):
                        derived_used.setdefault(metric, []).append(fy_end)
                if fact is None:
                    fact = self.reported_or_missing(metric, spec, fy_end, why_not)
                self.items.setdefault(metric, {})[fy_end] = fact
            debt, current = self.debt(fy_end)
            self.items.setdefault("financial_debt", {})[fy_end] = debt
            self.items.setdefault("current_financial_debt", {})[fy_end] = current
        for metric, ends in derived_used.items():
            self.warnings.append(f"DERIVED: {metric} is calculated, not reported, for {', '.join(map(str, ends))}")
        self.tag_switches()
        if fy_ends:
            self.bridge_items(fy_ends[-1])
            self.shares(fy_ends[-1])
        return self.company_data()

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
            return self._derived(metric, assets - total_equity, fy_end, "total_assets − total_equity"), ""
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
            used = [(end, fact.tag) for end, fact in sorted(by_year.items()) if fact.kind == "reported"]
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

        notes = [f"company-specific: {override['reason']}"] if inside else []
        if total is not None:
            long_term = total.value
            notes.append(_source(total))
            if noncurrent is not None and current is not None and not inside:
                parts_sum = noncurrent.value + current.value
                if _relative_difference(total.value, parts_sum) > self.settings["debt_check_warning"]:
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
        elif total is not None and noncurrent is not None:
            maturities, maturities_note = total.value - noncurrent.value, f"{total.tag} − {noncurrent.tag}"
        else:
            maturities, maturities_note = None, ""

        if inside:
            short_term, short_notes = 0, ["short-term borrowings classified inside long-term debt"]
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
        if maturities is None:
            return debt, self._missing("current_financial_debt", fy_end,
                                       "current maturities of long-term debt not reported")
        return debt, self._derived("current_financial_debt", maturities + short_term, fy_end,
                                   " + ".join([maturities_note, *short_notes]))

    def bridge_items(self, fy0: date) -> None:
        for metric in self.map["line_items"]:
            spec = self.spec(metric)
            if not spec.get("bridge"):
                continue
            fact = self.reported(metric, spec, fy0) or Fact(
                metric, 0, "USD", None, fy0, "assumption", None, None, None, None, self.retrieved,
                f"not reported under {', '.join(spec['tags'])}, treated as nil (SPEC §8.3)")
            self.items.setdefault(metric, {})[fy0] = fact

    def shares(self, fy0: date) -> None:
        tags = self.map["shares"]
        cover = [e for entries in self._annual(tags["cover_tag"], "instant", "shares", "dei").values() for e in entries]
        if cover:
            latest = max(cover, key=_order)
            when = date.fromisoformat(latest["end"])
            self.items["shares"] = {when: Fact(
                "shares", latest["val"], "shares", None, when, "reported", f"dei:{tags['cover_tag']}", latest["form"],
                latest["accn"], date.fromisoformat(latest["filed"]), self.retrieved,
                "cover page of the latest annual report")}
            return
        average = self.reported("shares", {"kind": "flow", "tags": [tags["average_tag"]]}, fy0, unit="shares")
        if average is not None:
            self.items["shares"] = {fy0: self._derived(
                "shares", average.value, fy0, f"diluted weighted average of the fiscal year ({_source(average)}), "
                "not a period-end count", unit="shares")}
            self.warnings.append("AVERAGE_SHARES: the share count is the diluted average of the fiscal year, not a "
                                 "period-end figure")
            return
        self.items["shares"] = {fy0: self._missing("shares", fy0, f"no {tags['cover_tag']} on the cover page and no "
                                                                  f"{tags['average_tag']}", unit="shares")}

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
    """CompanyData for one company from its SEC companyfacts and submissions JSON (SPEC §5, §6)."""
    return _Resolver(ticker.strip().upper(), companyfacts, submissions, retrieved,
                     settings or load_settings()["data"], tag_map or load_tag_map(), years).run()
