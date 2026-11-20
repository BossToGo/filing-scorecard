"""The layering rule of SPEC §11, checked on every pull request. Owner: A.

- Nothing in `app/src` imports the interface (`app/main.py`, `app/ui`, Streamlit, Plotly).
- The logic (checks, valuation, five forces, gates) never touches the network: no network library, no import of
  the data layer `src.data`, no dynamic imports that could hide one.
- The benchmark loader reads only the extracted CSV files: no network library either.

Limits: this reads imports, not behaviour; a call such as `pandas.read_csv(url)` is caught at run time by the
network guard of the tests instead.
"""

import ast
from pathlib import Path

import pytest

APP = Path(__file__).resolve().parents[2]
SRC = APP / "src"

INTERFACE = {"ui", "main", "streamlit", "plotly"}
NETWORK = {"requests", "urllib", "urllib3", "http", "httpx", "aiohttp", "socket", "ssl", "yfinance", "fredapi"}
LOGIC_FORBIDDEN = NETWORK | {"src.data", "importlib"}
# The interface reaches the data layer only through src.data.company (SPEC §11; Simon's review of PR #7).
INTERFACE_FORBIDDEN = NETWORK | {"src.data.sec_client", "src.data.resolver", "importlib"}
LOGIC = [SRC / "checks", SRC / "valuation", SRC / "forces.py", SRC / "gates.py"]
BENCHMARKS = [SRC / "benchmarks"]


def module_name(path: Path) -> str:
    """Dotted module name of a file under app/, e.g. app/src/checks/past.py -> src.checks.past."""
    parts = list(path.relative_to(APP).with_suffix("").parts)
    if parts[-1] == "__init__":
        parts = parts[:-1]
    return ".".join(parts)


def imported_modules(source: str, module: str = "", is_package: bool = False) -> set[str]:
    """Every module a file imports, as full dotted names; relative imports resolved; dynamic imports flagged."""
    package = module if is_package else module.rpartition(".")[0]
    names = set()
    for node in ast.walk(ast.parse(source)):
        if isinstance(node, ast.Import):
            names.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom):
            if node.level:
                base = package.split(".")
                base = base[: len(base) - (node.level - 1)] if node.level > 1 else base
                prefix = ".".join(p for p in base if p)
                target = ".".join(p for p in (prefix, node.module or "") if p)
            else:
                target = node.module or ""
            names.add(target)
            names.update(f"{target}.{alias.name}" for alias in node.names if alias.name != "*")
        elif isinstance(node, ast.Call) and getattr(node.func, "id", None) == "__import__":
            names.add("importlib")  # a dynamic import counts as importlib
    return names


def violations(names: set[str], forbidden: set[str]) -> set[str]:
    return {n for n in names for f in forbidden if n == f or n.startswith(f + ".")}


def python_files(*paths: Path) -> list[Path]:
    files = []
    for path in paths:
        if path.is_file():
            files.append(path)
        elif path.is_dir():
            files.extend(sorted(path.rglob("*.py")))
    return files


def check(path: Path, forbidden: set[str]) -> set[str]:
    return violations(
        imported_modules(path.read_text(encoding="utf-8"), module_name(path), path.name == "__init__.py"), forbidden
    )


# --- the import reader catches what it must (see it fail first) -------------------------------------------------


@pytest.mark.parametrize(
    "source, module, expected",
    [
        ("import requests", "src.checks.past", {"requests"}),
        ("import urllib.request", "src.checks.past", {"urllib.request"}),
        ("from src.data.sec_client import fetch", "src.valuation.wacc", {"src.data.sec_client", "src.data.sec_client.fetch"}),
        ("from src import data", "src.valuation.wacc", {"src.data"}),
        ("from ..data import sec_client", "src.valuation.wacc", {"src.data", "src.data.sec_client"}),
        ("from ..data.fred import latest", "src.checks.past", {"src.data.fred", "src.data.fred.latest"}),
        ("import importlib\nimportlib.import_module('requests')", "src.checks.past", {"importlib"}),
        ("x = __import__('requests')", "src.checks.past", {"importlib"}),
        ("from src.contracts import Fact\nfrom . import health", "src.checks.past", set()),
    ],
)
def test_the_import_reader_finds_forbidden_imports(source, module, expected):
    assert violations(imported_modules(source, module), LOGIC_FORBIDDEN) == expected


def test_the_import_reader_finds_interface_imports():
    assert violations(imported_modules("import streamlit as st\nfrom ui import pages", "src.gates"), INTERFACE) == {
        "streamlit",
        "ui",
        "ui.pages",
    }


# --- the rules, on the real files --------------------------------------------------------------------------------


def ids(path):
    return str(path.relative_to(APP)) if path else "none-yet"


@pytest.mark.parametrize("path", python_files(SRC), ids=ids)
def test_src_never_imports_the_interface(path):
    found = check(path, INTERFACE)
    assert not found, f"{ids(path)} imports {sorted(found)}; app/src must not import the interface (SPEC §11)"


@pytest.mark.parametrize("path", python_files(*LOGIC), ids=ids)
def test_logic_never_touches_the_network_or_the_data_layer(path):
    found = check(path, LOGIC_FORBIDDEN)
    assert not found, (
        f"{ids(path)} imports {sorted(found)}; checks, valuation, forces and gates are pure functions "
        "(SPEC §11): the data comes in as CompanyData, they never fetch it"
    )


@pytest.mark.parametrize("path", python_files(*BENCHMARKS), ids=ids)
def test_the_benchmark_loader_reads_files_only(path):
    found = check(path, NETWORK)
    assert not found, f"{ids(path)} imports {sorted(found)}; the app reads only the extracted CSV (SPEC §4)"


@pytest.mark.parametrize("path", python_files(APP / "main.py", APP / "ui"), ids=ids)
def test_the_interface_never_calls_the_network_itself(path):
    found = check(path, NETWORK)
    assert not found, f"{ids(path)} imports {sorted(found)}; the interface asks src.data for data (SPEC §11)"


@pytest.mark.parametrize("source, expected", [
    ("from src.data.sec_client import SourceUnreachable", {"src.data.sec_client", "src.data.sec_client.SourceUnreachable"}),
    ("from src.data.company import load_company, SourceUnreachable", set()),
])
def test_the_import_reader_finds_data_layer_imports_in_the_interface(source, expected):
    assert violations(imported_modules(source, "ui.page"), INTERFACE_FORBIDDEN) == expected


@pytest.mark.parametrize("path", python_files(APP / "main.py", APP / "ui"), ids=ids)
def test_the_interface_uses_only_src_data_company(path):
    found = check(path, INTERFACE_FORBIDDEN)
    assert not found, (f"{ids(path)} imports {sorted(found)}; the interface imports load_company and the SEC errors from "
                       "src.data.company only (SPEC §11)")
