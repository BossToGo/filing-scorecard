"""Line-item resolver (SPEC §5, §6). Owner: A. Slice S2.

    from src.data.resolver import resolve
    data = resolve("KO", companyfacts_json, submissions_json, retrieved)     # -> CompanyData

Turns the SEC's company facts into `CompanyData`: for each line item of `tag_map.yaml` and each of the latest
`fiscal_years` fiscal years (settings.yaml), one `Fact` with its source. Pure: no network. The rules of SPEC §5.3:
1. only Form 10-K and 10-K/A; a flow covers 350 to 380 days (53-week years kept; nine months never read as a year);
2. the fiscal year comes from the period end date, never from the `fy` label;
3. balances are taken at the fiscal year end date itself;
4. a period filed several times: the latest filing is used, the original is kept in the note, a difference above
   1% is a warning;
5. only US dollars: a figure filed only in another currency is missing and flagged;
6. nothing is added up from segments: no company-wide figure means `missing`;
7. tags are tried in order for every fiscal year; two tags that disagree for one period are flagged.
Amounts stay in USD exactly as filed. Missing figures are never zero and say why.

Warnings in `CompanyData.warnings` start with a code, so the gates (slice S11) can act on them:
RESTATED, TAG_CONFLICT, NON_USD, DERIVED, AVERAGE_SHARES, SIGN, NO_ANNUAL_DATA.

Shares are stored at their own date (the cover page of the latest annual report, a few weeks after the fiscal
year end): use `data.fiscal_years("shares")[-1]` to find them.
"""

from __future__ import annotations

from dataclasses import dataclass
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


@dataclass(frozen=True)
class _Pick:
    tag: str
    latest: dict
    original: dict


class _Resolver:
    def __init__(self, ticker, companyfacts, submissions, retrieved, settings, tag_map, years):
        facts = (companyfacts or {}).get("facts", {})
        self.us_gaap, self.dei = facts.get("us-gaap", {}), facts.get("dei", {})
        self.ticker, self.submissions, self.retrieved = ticker, submissions, retrieved
        self.settings, self.map = settings, tag_map
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

    @staticmethod
    def _pick(tag: str, entries: list[dict]) -> _Pick:
        order = sorted(entries, key=lambda e: (e["filed"], e["accn"]))
        return _Pick(tag, latest=order[-1], original=order[0])

    def _other_currencies(self, tags: list[str], fy_end: date, kind: str) -> list[str]:
        found = set()
        for tag in tags:
            for unit in self.us_gaap.get(tag, {}).get("units", {}):
                if unit != "USD" and fy_end in self._annual(tag, kind, unit):
                    found.add(unit)
        return sorted(found)

    # --- facts --------------------------------------------------------------------------------------------------

    def _fact(self, metric, pick: _Pick, fy_end, kind, unit="USD", tag_label=None, note="") -> Fact:
        e = pick.latest
        return Fact(
            metric=metric,
            value=e["val"],
            unit=unit,
            period_start=date.fromisoformat(e["start"]) if kind == "flow" else None,
            period_end=fy_end,
            kind="reported",
            tag=tag_label or pick.tag,
            form=e["form"],
            accession=e["accn"],
            filed=date.fromisoformat(e["filed"]),
            retrieved=self.retrieved,
            note=note,
        )

    def _missing(self, metric, fy_end, reason, unit="USD") -> Fact:
        return Fact(metric, None, unit, None, fy_end, "missing", None, None, None, None, self.retrieved, reason)

    def _derived(self, metric, value, fy_end, formula, unit="USD") -> Fact:
        return Fact(metric, value, unit, None, fy_end, "derived", None, None, None, None, self.retrieved, formula)

    def spec(self, metric: str) -> dict:
        """The line item's entry in tag_map.yaml, with a company override of its tag order if there is one."""
        spec = self.map["line_items"][metric]
        override = self.map.get("overrides", {}).get(self.ticker, {}).get(metric)
        return {**spec, "tags": override["tags"], "override": override["reason"]} if override else spec

    def reported(self, metric: str, spec: dict, fy_end: date) -> Fact | None:
        """The first tag with an annual value for this fiscal year (rule 7), or None."""
        kind, tags = spec["kind"], spec["tags"]
        picks = [self._pick(tag, groups[fy_end]) for tag in tags
                 if fy_end in (groups := self._annual(tag, kind))]
        if not picks:
            return None
        first, notes = picks[0], []
        if spec.get("override"):
            notes.append(f"company-specific tag order: {spec['override']}")
        value = first.latest["val"]
        if first.original is not first.latest and first.original["val"] != value:
            original = first.original
            notes.append(f"restated: first filed {_money(original['val'])} ({original['accn']}, {original['filed']}), "
                         f"latest {_money(value)} ({first.latest['accn']}, {first.latest['filed']})")
            if _relative_difference(value, original["val"]) > self.settings["restatement_warning"]:
                self.warnings.append(f"RESTATED: {metric} {fy_end}: first filed {_money(original['val'])}, "
                                     f"now {_money(value)}; both on the sources page")
        for other in picks[1:]:
            other_value = other.latest["val"]
            if _relative_difference(value, other_value) > self.settings["tag_conflict_warning"]:
                notes.append(f"also filed under {other.tag}: {_money(other_value)}")
                if not spec.get("override"):  # an override documents a known difference; no second warning
                    self.warnings.append(f"TAG_CONFLICT: {metric} {fy_end}: {first.tag} {_money(value)} used, "
                                         f"{other.tag} gives {_money(other_value)}")
        if spec.get("outflow") and value < 0:
            self.warnings.append(f"SIGN: {metric} {fy_end} is negative ({_money(value)}); a payment is filed as a "
                                 "positive amount, check the filing")
        return self._fact(metric, first, fy_end, kind, note="; ".join(notes))

    def reported_or_missing(self, metric: str, spec: dict, fy_end: date) -> Fact:
        fact = self.reported(metric, spec, fy_end)
        if fact is not None:
            return fact
        currencies = self._other_currencies(spec["tags"], fy_end, spec["kind"])
        if currencies:
            self.warnings.append(f"NON_USD: {metric} {fy_end} is filed in {', '.join(currencies)}, not US dollars")
            return self._missing(metric, fy_end, f"filed in {', '.join(currencies)}, not US dollars (SPEC §5.3.5)")
        return self._missing(metric, fy_end, f"no annual 10-K value under {', '.join(spec['tags'])} for the fiscal "
                                             f"year ending {fy_end}")

    # --- fiscal years -----------------------------------------------------------------------------------------

    def fiscal_year_ends(self) -> list[date]:
        ends: set[date] = set()
        for metric in FISCAL_YEAR_ITEMS:
            for tag in self.map["line_items"][metric]["tags"]:
                ends.update(self._annual(tag, "flow"))
        return sorted(ends)[-self.years:]

    # --- the whole company ------------------------------------------------------------------------------------

    def run(self) -> CompanyData:
        fy_ends = self.fiscal_year_ends()
        if not fy_ends:
            self.warnings.append("NO_ANNUAL_DATA: no annual 10-K figures found")
        line_items = self.map["line_items"]
        derived_used: dict[str, list[date]] = {}
        for fy_end in fy_ends:
            for metric in line_items:
                spec = self.spec(metric)
                if spec.get("bridge"):
                    continue
                fact = self.reported(metric, spec, fy_end)
                if fact is None:
                    fact = self.derive(metric, fy_end)
                    if fact is not None and fact.kind == "derived" and metric in ("gross_profit", "total_liabilities"):
                        derived_used.setdefault(metric, []).append(fy_end)
                if fact is None:
                    fact = self.reported_or_missing(metric, spec, fy_end)
                self.items.setdefault(metric, {})[fy_end] = fact
            debt, current = self.debt(fy_end)
            self.items.setdefault("financial_debt", {})[fy_end] = debt
            self.items.setdefault("current_financial_debt", {})[fy_end] = current
        for metric, ends in derived_used.items():
            self.warnings.append(f"DERIVED: {metric} is calculated, not reported, for {', '.join(map(str, ends))}")
        if fy_ends:
            self.bridge_items(fy_ends[-1])
            self.shares(fy_ends[-1])
        return self.company_data()

    def derive(self, metric: str, fy_end: date) -> Fact | None:
        """SPEC §6 derivations, used only when the line item is not reported. None if not derivable."""

        def value(name):
            fact = self.items.get(name, {}).get(fy_end)
            return None if fact is None or fact.value is None else fact.value

        if metric == "gross_profit":
            revenue, cost = value("revenue"), value("cost_of_revenue")
            if revenue is not None and cost is not None:
                return self._derived(metric, revenue - cost, fy_end, "revenue − cost_of_revenue")
        if metric == "total_equity":
            equity = value("equity")
            if equity is not None:
                minority = self.reported("minority_interest", self.map["line_items"]["minority_interest"], fy_end)
                if minority is not None:
                    return self._derived(metric, equity + minority.value, fy_end,
                                         "equity + minority_interest (MinorityInterest)")
                return self._derived(metric, equity, fy_end,
                                     "equity; no non-controlling interests reported, so none are added")
        if metric == "total_liabilities":
            assets, total_equity = value("total_assets"), value("total_equity")
            if assets is not None and total_equity is not None:
                return self._derived(metric, assets - total_equity, fy_end, "total_assets − total_equity")
        return None

    def debt(self, fy_end: date) -> tuple[Fact, Fact]:
        """Financial debt and its current part (SPEC §6; plan Q5). Operating leases excluded."""
        parts = self.map["debt"]

        def first(tags):
            for tag in tags:
                groups = self._annual(tag, "instant")
                if fy_end in groups:
                    return tag, self._pick(tag, groups[fy_end]).latest["val"]
            return None, None

        nc_tag, noncurrent = first(parts["long_term_noncurrent"])
        cur_tag, current = first(parts["long_term_current"])
        total_tag, total = first(parts["long_term_total"])
        st_tag, short_total = first(parts["short_term_total"])
        short_parts = [(tag, v) for tag in parts["short_term_parts"] for t, v in [first([tag])] if v is not None]
        if all(v is None for v in (noncurrent, current, total, short_total)) and not short_parts:
            reason = "no debt tag in the annual report (" + ", ".join(
                [*parts["long_term_noncurrent"], *parts["long_term_total"], *parts["short_term_total"]]) + ")"
            return self._missing("financial_debt", fy_end, reason), self._missing("current_financial_debt", fy_end,
                                                                                  reason)
        if noncurrent is not None and total is not None and \
                _relative_difference(total, noncurrent) <= self.settings["debt_inside_tolerance"]:
            note = (f"{nc_tag} {_money(noncurrent)} equals {total_tag} {_money(total)}: current maturities and "
                    "short-term borrowings are classified inside long-term debt, so nothing more is added")
            return (self._derived("financial_debt", noncurrent, fy_end, note),
                    self._derived("current_financial_debt", 0, fy_end,
                                  "0: current maturities and short-term borrowings are classified inside long-term debt"))
        terms, current_terms = [], []
        if noncurrent is not None:
            long_term = noncurrent + (current or 0)
            terms.append(f"{nc_tag} {_money(noncurrent)}")
            if current is not None:
                terms.append(f"{cur_tag} {_money(current)}")
                current_terms.append((f"{cur_tag} {_money(current)}", current))
            else:
                terms.append("no current portion reported")
        elif total is not None:
            long_term = total
            terms.append(f"{total_tag} {_money(total)}")
            if current is not None:
                current_terms.append((f"{cur_tag} {_money(current)}", current))
        else:
            long_term = current or 0
            if current is not None:
                terms.append(f"{cur_tag} {_money(current)}")
                current_terms.append((f"{cur_tag} {_money(current)}", current))
        if short_total is not None:
            short_term = short_total
            terms.append(f"{st_tag} {_money(short_total)}")
            current_terms.append((f"{st_tag} {_money(short_total)}", short_total))
        else:
            short_term = sum(v for _, v in short_parts)
            for tag, v in short_parts:
                terms.append(f"{tag} {_money(v)}")
                current_terms.append((f"{tag} {_money(v)}", v))
        debt = self._derived("financial_debt", long_term + short_term, fy_end, " + ".join(terms))
        current_value = sum(v for _, v in current_terms)
        current_note = " + ".join(t for t, _ in current_terms) or "no current debt reported"
        return debt, self._derived("current_financial_debt", current_value, fy_end, current_note)

    def bridge_items(self, fy0: date) -> None:
        for metric, spec in self.map["line_items"].items():
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
            pick = self._pick(tags["cover_tag"], cover)
            when = date.fromisoformat(pick.latest["end"])
            self.items["shares"] = {when: self._fact("shares", pick, when, "instant", unit="shares",
                                                     tag_label=f"dei:{tags['cover_tag']}",
                                                     note="cover page of the latest annual report")}
            return
        average = self._annual(tags["average_tag"], "flow", "shares")
        if fy0 in average:
            pick = self._pick(tags["average_tag"], average[fy0])
            self.items["shares"] = {fy0: self._derived(
                "shares", pick.latest["val"], fy0, f"diluted weighted average of the fiscal year "
                f"({tags['average_tag']}, {pick.latest['accn']}), not a period-end count", unit="shares")}
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
