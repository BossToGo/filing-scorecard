"""The layering rule of SPEC §11, checked on every pull request.

`app/ui` calls `app/src`; nothing in `app/src` imports the interface; the logic (checks, valuation, five forces,
gates) never touches the network. Owner: A.
"""

import ast
from pathlib import Path

import pytest

APP = Path(__file__).resolve().parents[2]
SRC = APP / "src"

INTERFACE = {"ui", "main", "streamlit", "plotly"}
NETWORK = {"requests", "urllib", "urllib3", "http", "httpx", "aiohttp", "socket", "yfinance"}
LOGIC = [SRC / "checks", SRC / "valuation", SRC / "forces.py", SRC / "gates.py"]


def imported_top_level_names(source: str) -> set[str]:
    names = set()
    for node in ast.walk(ast.parse(source)):
        if isinstance(node, ast.Import):
            names.update(alias.name.split(".")[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module and node.level == 0:
            names.add(node.module.split(".")[0])
    return names


def python_files(*paths: Path) -> list[Path]:
    files = []
    for path in paths:
        if path.is_file():
            files.append(path)
        elif path.is_dir():
            files.extend(sorted(path.rglob("*.py")))
    return files


def test_the_import_reader_finds_forbidden_imports():
    # The rule is only useful if the reader catches a violation (see it fail first).
    source = "import requests\nfrom ui.pages import header\nfrom src.contracts import Fact\nfrom . import past\n"
    assert imported_top_level_names(source) == {"requests", "ui", "src"}


@pytest.mark.parametrize("path", python_files(SRC), ids=lambda p: str(p.relative_to(APP)))
def test_src_never_imports_the_interface(path):
    forbidden = imported_top_level_names(path.read_text(encoding="utf-8")) & INTERFACE
    assert not forbidden, f"{path.relative_to(APP)} imports {sorted(forbidden)}; app/src must not import the interface"


@pytest.mark.parametrize("path", python_files(*LOGIC) or [None], ids=lambda p: str(p.relative_to(APP)) if p else "none-yet")
def test_logic_never_touches_the_network(path):
    if path is None:
        pytest.skip("no logic modules yet")
    forbidden = imported_top_level_names(path.read_text(encoding="utf-8")) & NETWORK
    assert not forbidden, (
        f"{path.relative_to(APP)} imports {sorted(forbidden)}; checks, valuation, forces and gates are pure "
        "functions (SPEC §11): pass data in, never fetch it"
    )
