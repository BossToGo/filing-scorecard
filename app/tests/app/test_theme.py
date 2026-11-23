"""Theme file (SPEC §3: every colour defined once in `app/.streamlit/config.toml`; audit security #10). Owner: D."""

import re
import tomllib
from pathlib import Path

APP = Path(__file__).resolve().parents[2]
CONFIG = APP / ".streamlit" / "config.toml"
COLOUR = re.compile(r"#[0-9a-fA-F]{3,8}\b|\brgba?\(")


def test_usage_statistics_are_off():
    assert tomllib.loads(CONFIG.read_text(encoding="utf-8"))["browser"]["gatherUsageStats"] is False


def test_one_accent_colour_and_the_page_colours_are_in_the_theme():
    theme = tomllib.loads(CONFIG.read_text(encoding="utf-8"))["theme"]
    for name in ("primaryColor", "backgroundColor", "secondaryBackgroundColor", "textColor"):
        assert COLOUR.match(theme[name]), name


def test_no_colour_is_written_in_the_interface_code():
    files = [APP / "main.py", *sorted((APP / "ui").glob("*.py"))]
    found = {f.name: COLOUR.findall(f.read_text(encoding="utf-8")) for f in files}
    assert {name: hits for name, hits in found.items() if hits} == {}
