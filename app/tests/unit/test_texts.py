"""`app/ui/texts.yaml`: the plain-language text of every check, tier 1 and valuation (SPEC §3 item 4, §7, S16a, S16b).

Owner: E. The texts are E's own words; this test checks that each check has one, that none gives advice, and that
the thresholds written in the texts still equal the values in `app/settings.yaml`.
"""

import re
from pathlib import Path

import yaml

APP = Path(__file__).resolve().parents[2]
TEXTS = APP / "ui" / "texts.yaml"
SETTINGS = APP / "settings.yaml"

CHECKS = [f"{area}{n}" for area in "PHDV" for n in range(1, 7)]  # P1 ... D6 (tier 1), V1 ... V6 (SPEC §2, §7)
ADVICE_WORDS = re.compile(  # information, not advice; SPEC §3 says "the estimate", never "fair value" (#32, #39)
    r"\b(buy|sell|undervalued|fair\s+value|cheap|expensive)\b", re.IGNORECASE
)


def load(path):
    return yaml.safe_load(path.read_text(encoding="utf-8"))


def percent(value):
    return f"{round(value * 100, 6):g}%"  # 0.40 -> "40%"


# Check -> (settings section, setting name, how the value is written in the text)
THRESHOLDS_IN_TEXTS = {
    "P1": ("past_performance", "p1_min_profitable_years", lambda v: f"{v} of the last 5"),
    "H3": ("financial_health", "max_net_debt_to_equity", percent),
    "H5": ("financial_health", "min_operating_cash_flow_to_debt", percent),
    "H6": ("financial_health", "min_interest_cover", lambda v: f"{v:g} times"),
    "D3": ("dividend", "max_dividend_cut", percent),
    "D5": ("dividend", "max_payout_ratio", percent),
    "V2": ("valuation", "well_below_fair_value", percent),
    "V6": ("valuation", "growth_cap", percent),
}


def test_every_check_has_a_name_and_a_rule():
    texts = load(TEXTS)
    problems = []
    for check in CHECKS:
        entry = texts.get(check)
        if not isinstance(entry, dict):
            problems.append(f"{check}: no text")
            continue
        for field in ("name", "rule"):
            if not isinstance(entry.get(field), str) or not entry[field].strip():
                problems.append(f"{check}: '{field}' is missing or empty")
    assert not problems, "\n".join(problems)


def test_no_text_gives_advice():
    found = [
        f"{check}.{field}: {text!r}"
        for check, entry in load(TEXTS).items()
        for field, text in entry.items()
        if ADVICE_WORDS.search(text)
    ]
    assert not found, "Information, not advice (SPEC §1):\n" + "\n".join(found)


def test_thresholds_in_texts_match_settings():
    # If a threshold changes in settings.yaml, this fails and names the text E must update.
    texts, settings = load(TEXTS), load(SETTINGS)
    problems = []
    for check, (section, name, written) in THRESHOLDS_IN_TEXTS.items():
        expected = written(settings[section][name]["value"])
        if expected not in texts[check]["rule"]:
            problems.append(f"{check}: the text should say {expected!r} ({section}.{name} in settings.yaml)")
    assert not problems, "\n".join(problems)
