"""The valuation tab and the share price on the screen (Streamlit AppTest; slice S10b, AC8 to AC10). Owner: D.

The synthetic company at tier 2 (share price USD 30.00, risk-free rate 4.0%, unlevered beta 0.90; inputs in
`synthetic_market.py`). Expected values only from the signed-off fixture: the estimate from C
(`expected_valuation`), the scores from E (`expected_scores`), P4, P5 and D2 from B and C (`expected_check`). The
screen computes nothing: it shows what `ui.results.run_checks` returns.
"""

from __future__ import annotations

from streamlit.testing.v1 import AppTest

from tests.app.synthetic_market import FIRMS, INDUSTRY, PRICE, ROUTE, SOURCE_FILE
from tests.fixtures import synthetic


def tier2_page(price):
    from tests.app import synthetic_market
    from tests.fixtures import synthetic
    from ui.results import run_checks
    from ui.scorecard import render_scorecard
    from ui.sources import render_sources

    data = synthetic.company_data()
    run = run_checks(data, price, demo=True, benchmarks=synthetic_market.benchmarks(),
                     risk_free=synthetic_market.risk_free())
    with render_scorecard(data, run.results, price, market=run.market):
        render_sources(data, run.results, price=price)


def run(price=PRICE) -> AppTest:
    return AppTest.from_function(tier2_page, kwargs={"price": price}).run(timeout=30)


def tab_text(tab) -> str:
    return "\n".join(str(e.value) for kind in ("markdown", "caption", "info", "warning") for e in getattr(tab, kind))


def valuation_tab(app: AppTest):
    return app.tabs[3]


def test_ac9_the_estimate_per_share_against_the_typed_price():
    expected = synthetic.expected_valuation("fair_value_per_share")  # USD 20.13, signed off by C
    shown = tab_text(valuation_tab(run()))
    assert f"USD {expected['value']:.2f} per share" in shown
    assert "USD 30.00" in shown and "The estimate" in shown


def test_ac9_the_four_scores_on_the_chart():
    shown = "\n".join(str(m.value) for m in run().markdown)
    for passed in synthetic.expected_scores().values():  # 5, 4, 6 and 3 of 6, signed off by E
        assert f"{passed} passed of 6 assessed" in shown


def test_ac8_p4_p5_and_d2_are_assessed_with_the_price_and_benchmarks():
    from ui.scorecard import ICONS, load_texts

    labels = [e.label for e in run().expander]
    texts = load_texts()
    for check_id in ("P4", "P5", "D2"):
        icon = ICONS[synthetic.expected_check(check_id)["result"]]
        assert any(label.startswith(icon) and f"**{texts[check_id]['name']}.**" in label for label in labels), check_id


def test_ac8_the_industry_group_its_route_and_number_of_firms_and_the_source():
    shown = tab_text(valuation_tab(run()))
    assert INDUSTRY in shown and ROUTE in shown and f"{FIRMS} firms" in shown and SOURCE_FILE in shown


def test_the_cost_of_equity_build_up_shows_each_step_with_its_note_and_fred_notice():
    from src.data.company import FRED_NOTICE

    tab = valuation_tab(run())
    tables = [t.value for t in tab.table]
    build_up = next(t for t in tables if "Step" in t.columns)
    steps = " ".join(build_up["Step"])
    for step in ("Risk-free rate", "Equity risk premium", "Industry unlevered beta", "Levered beta", "Cost of equity"):
        assert step in steps
    assert "Risk-free rate of the synthetic company" in " ".join(build_up["Source"])  # the Fact's own note
    assert FRED_NOTICE in tab_text(tab)


def test_the_ten_year_table_has_ten_years():
    tables = [t.value for t in valuation_tab(run()).table]
    forecast = next(t for t in tables if "Year" in t.columns)
    assert list(forecast["Year"]) == list(range(1, 11))


def test_never_fair_value_on_the_screen():
    app = run()
    shown = tab_text(valuation_tab(app)).lower() + " ".join(e.label.lower() for e in app.expander)
    tables = " ".join(t.value.to_string().lower() for t in valuation_tab(app).table)
    for word in ("fair value", "fair_value"):
        assert word not in shown and word not in tables


def test_ac10_no_price_needs_a_share_price_and_the_other_areas_still_show():
    app = run(price=None)
    assert "Needs a share price" in tab_text(valuation_tab(app))
    shown = "\n".join(str(m.value) for m in app.markdown)
    assert "passed of 6 assessed" in shown  # past performance and health still scored


def test_the_sources_page_lists_the_typed_price_as_an_assumption():
    table = run().dataframe[-1].value
    price = table[table["Metric"] == "share_price"]
    assert list(price["Kind"]) == ["assumption"] and list(price["Value"]) == ["USD 30.00"]


def test_without_a_price_the_sources_page_has_no_price_row():
    table = run(price=None).dataframe[-1].value
    assert "share_price" not in set(table["Metric"])


# --- through main.py, a demo company (no network: demo mode is on by default) ------------------------------------

def show(ticker: str, price: str) -> AppTest:
    from pathlib import Path

    app = AppTest.from_file(str(Path(__file__).resolve().parents[2] / "main.py")).run(timeout=30)
    app.selectbox(key="company").set_value(ticker)
    app.text_input(key="price").set_value(price)
    app.button(key="show").click()
    return app.run(timeout=60)


def test_main_coca_cola_with_a_price_shows_the_overview_the_estimate_and_the_typed_price_row():
    app = show("KO", "65.40")
    assert not app.exception
    assert "Checks by area" in "\n".join(str(m.value) for m in app.markdown)  # Igor's overview panel (#60)
    valuation = tab_text(valuation_tab(app))
    assert "The estimate" in valuation and "USD 65.40" in valuation
    table = app.dataframe[-1].value
    assert list(table[table["Metric"] == "share_price"]["Value"]) == ["USD 65.40"]


def test_main_coca_cola_without_a_price_needs_a_share_price_ac10():
    app = show("KO", "")
    assert not app.exception
    assert "Needs a share price" in tab_text(valuation_tab(app))


# --- Igor's review of #63, point 1: benchmarks in the open checks (Coca-Cola, demo mode, price USD 65.40) ----------
# Expected values read by hand from B's file app/data/benchmarks_us_2026.csv (KO rows, Beverage (Soft); market rows)
# and Igor's example (P5: "20.5%", "as of 5 January 2026", no sec.gov link); the risk-free rate is the saved value
# 0.0393 of settings.yaml (period ending 20 November 2026).

import re  # noqa: E402

SEC_ACCESSION = re.compile(r"\d{10}-\d{2}-\d{6}")


def open_check(app: AppTest, check_id: str):
    from ui.scorecard import _plain_name, load_texts

    name = _plain_name(check_id, load_texts())
    return next(e for e in app.expander if f"**{name}.**" in e.label)


def figure(check, label: str):
    table = check.table[0].value
    rows = table[table["Figure"] == label]
    assert len(rows) == 1, (label, list(table["Figure"]))
    return rows.iloc[0]


def test_igor_p5_the_industry_margin_reads_20_5_percent_as_of_5_january_2026():
    p5 = open_check(show("KO", "65.40"), "P5")
    margin = figure(p5, "Operating margin")
    assert (margin["Value"], margin["Period"]) == ("20.5%", "as of 5 January 2026")


def test_benchmark_values_and_dates_in_the_open_checks():
    app = show("KO", "65.40")
    expected = {  # check: (figure, value, period)
        "P4": ("Return on equity", "30.9%", "as of 5 January 2026"),   # 0.30916
        "D2": ("Dividend yield", "1.1%", "as of 5 January 2026"),      # market 0.01104
        "V3": ("Price to earnings", "37.1 times", "as of 5 January 2026"),   # industry 37.113
        "V4": ("Price to earnings", "60.3 times", "as of 5 January 2026"),   # market 60.258
        "V5": ("Price to book", "6.9 times", "as of 5 January 2026"),        # 6.869
        "V1": ("Industry unlevered beta", "0.56", "as of 5 January 2026"),   # 0.55567
    }
    for check_id, (label, value, period) in expected.items():
        row = figure(open_check(app, check_id), label)
        assert (row["Value"], row["Period"]) == (value, period), check_id
    rate = figure(open_check(app, "V1"), "Risk-free rate")
    assert (rate["Value"], rate["Period"]) == ("3.93%", "as of 20 November 2026")


def test_company_figures_keep_fiscal_year_ended():
    p5 = open_check(show("KO", "65.40"), "P5")
    table = p5.table[0].value
    company = table[table["Figure"] != "Operating margin"]
    assert len(company) and all(p.startswith("fiscal year ended ") for p in company["Period"])


def test_the_filing_line_links_only_sec_filings_never_a_benchmark():
    app = show("KO", "65.40")
    for check_id in ("P4", "P5", "D2", "V1", "V3", "V4", "V5"):
        lines = [m.value for m in open_check(app, check_id).markdown if m.value.startswith("**Filing:**")]
        for line in lines:
            assert "Damodaran" not in line and ".xls" not in line, check_id
            assert all(SEC_ACCESSION.fullmatch(a) for a in re.findall(r"\[([^\]]+)\]", line)), check_id


def test_the_valuation_tab_benchmark_table_uses_the_same_format():
    tables = [t.value for t in valuation_tab(show("KO", "65.40")).table]
    bench = next(t for t in tables if "Benchmark" in t.columns)
    shown = dict(zip(bench["Benchmark"] + " / " + bench["Group"], bench["Value"]))
    assert shown["Operating margin / Beverage (Soft)"] == "20.5%"
    assert shown["Price to earnings / Beverage (Soft)"] == "37.1 times"
    assert shown["Industry unlevered beta / Beverage (Soft)"] == "0.56"
    assert shown["Price to earnings / Whole US market"] == "60.3 times"


def test_the_typed_price_is_not_an_input_of_any_check():
    """Flo's decision d (S8 docstring): V1-V6 name the price in their texts, never as a Fact. Confirmed, not built."""
    from src.data.company import load_company
    from ui.results import run_checks

    run = run_checks(load_company("KO", demo=True), 65.40, demo=True)
    metrics = {f.metric for area in run.results.values() for r in area for f in r.inputs}
    assert not {m for m in metrics if "price" in m}
