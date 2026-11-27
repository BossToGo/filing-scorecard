"""The risk-free rate: FRED DGS10, averaged over the last five years, or the dated fallback (slice S2b, SPEC §4,
§8.1). Owner: A.

No test uses the network: FRED's answers come from fake sessions built on `tests/fixtures/fred_dgs10_small.json`,
a hand-made answer in the shape FRED documents (https://fred.stlouisfed.org/docs/api/fred/series_observations.html),
not a real download. No test reads the real app/.env or the real key: `tests/conftest.py` points the module at a
file that does not exist and removes FRED_API_KEY; tests that need a key write their own file.

Expected values:
- the average of the fixture's six days (one without a value): Igor's hand working, 24 November 2026;
- the second, uneven set (its mean differs from its median): Igor's hand working, 24 November 2026;
- percent to decimal: DGS10 is in percent (FRED series page, read on 24 November 2026), so 4.50 is 0.045;
- dates and request parameters: read off the fixture and the calendar;
- the fallback: the test's own settings below (Appendix A's risk-free rate of 4.0%), not the app's output.
"""

import json
from datetime import date, datetime
from pathlib import Path

import pytest
import requests

from src.data import fred
from src.settings import load_settings

FIXTURE = Path(__file__).resolve().parents[1] / "fixtures" / "fred_dgs10_small.json"
KEY = "0123456789abcdef0123456789abcdef"  # made up, in FRED's format (32 lower-case letters and digits)
TODAY = date(2026, 11, 24)
SETTINGS = {
    "valuation": {"risk_free_rate": 0.04},
    "data": {"risk_free_average_years": 5, "risk_free_fallback_period": [date(2020, 11, 20), date(2025, 11, 20)]},
}

# Igor's hand working (24 November 2026): the five days with a value, 4.13, 4.12, 4.09, 4.15 and 4.11, average 4.12%;
# the day without a value is left out. As a decimal: 0.0412.
IGOR_AVERAGE = 0.0412
# Igor's hand working (24 November 2026) for the uneven set 4.00, 4.00, (no value), 5.00: 0.04333 as he wrote it,
# so it is compared to half a unit of its last digit (the tolerance rule of docs/acceptance.md). The middle value,
# 0.04, would fail.
IGOR_SECOND_AVERAGE = 0.04333


class FakeResponse:
    def __init__(self, status_code=200, content=b""):
        self.status_code = status_code
        self.content = content


class FakeSession:
    """Records every request; answers with the given response or raises the given error."""

    def __init__(self, response=None, error=None):
        self.response, self.error, self.requests = response, error, []

    def get(self, url, params=None, **options):
        self.requests.append({"url": url, "params": dict(params or {}), **options})
        if self.error is not None:
            raise self.error
        return self.response


UNEXPECTED_REQUESTS = []


class NoNetwork(FakeSession):
    """For cases that must not download. fred.py catches every error itself, so the request is also recorded and
    checked after each test (re-review of S2b)."""

    def get(self, url, params=None, **options):
        UNEXPECTED_REQUESTS.append(url)
        raise AssertionError("this case must not download anything")


@pytest.fixture(autouse=True)
def _no_unexpected_request():
    UNEXPECTED_REQUESTS.clear()
    yield
    assert UNEXPECTED_REQUESTS == [], "a case that must not download anything sent a request"


class Clock:
    def __init__(self, start=1000.0):
        self.now = start

    def __call__(self):
        return self.now


def fixture_rows():
    return json.loads(FIXTURE.read_text(encoding="utf-8"))["observations"]


def answer(observations=None, status_code=200):
    data = json.loads(FIXTURE.read_text(encoding="utf-8"))
    if observations is not None:
        data["observations"] = observations
    return FakeResponse(status_code, json.dumps(data).encode("utf-8"))


def row(day, value):
    return {"realtime_start": "2026-11-24", "realtime_end": "2026-11-24", "date": day, "value": value}


@pytest.fixture
def key_file(tmp_path):
    path = tmp_path / "with_key.env"
    path.write_text(f'FRED_API_KEY="{KEY}"\n', encoding="utf-8")
    return path


def live(session, env_file, today=TODAY, settings=SETTINGS, clock=None):
    options = {"clock": clock} if clock else {}
    return fred.risk_free_rate(demo=False, env_file=env_file, session=session, today=today, settings=settings,
                               **options)


# --- live: the average of the days with a value ------------------------------------------------------------------


def test_the_rate_is_the_average_of_the_days_with_a_value(key_file):
    rate = live(FakeSession(answer()), key_file)

    assert rate.value == pytest.approx(IGOR_AVERAGE)
    assert (rate.kind, rate.unit, rate.tag, rate.form) == ("derived", "pure", "DGS10", "FRED")


def test_the_rate_is_the_mean_not_the_middle_value(key_file):
    uneven = [row("2026-11-17", "4.00"), row("2026-11-18", "4.00"), row("2026-11-19", "."), row("2026-11-20", "5.00")]

    rate = live(FakeSession(answer(uneven)), key_file)

    assert rate.value == pytest.approx(IGOR_SECOND_AVERAGE, abs=0.000005)


def test_the_period_runs_from_the_first_to_the_last_day_with_a_value(key_file):
    rate = live(FakeSession(answer()), key_file)

    assert (rate.period_start, rate.period_end) == (date(2026, 11, 16), date(2026, 11, 23))
    assert "5 daily values" in rate.note
    assert isinstance(rate.retrieved, datetime)


def test_days_without_a_value_at_either_end_are_not_part_of_the_period(key_file):
    rows = [row("2026-11-13", "."), *fixture_rows(), row("2026-11-26", ".")]  # 26 November: Thanksgiving

    rate = live(FakeSession(answer(rows)), key_file)

    assert (rate.period_start, rate.period_end) == (date(2026, 11, 16), date(2026, 11, 23))
    assert rate.value == pytest.approx(IGOR_AVERAGE)


def test_rows_out_of_date_order_give_the_same_rate_and_period(key_file):
    rate = live(FakeSession(answer(list(reversed(fixture_rows())))), key_file)

    assert (rate.period_start, rate.period_end) == (date(2026, 11, 16), date(2026, 11, 23))
    assert rate.value == pytest.approx(IGOR_AVERAGE)


def test_percent_becomes_a_decimal(key_file):
    rate = live(FakeSession(answer([row("2026-11-23", "4.50")])), key_file)

    assert rate.value == pytest.approx(0.045)


def test_the_request_asks_for_five_years_of_dgs10_with_the_key_as_a_parameter(key_file):
    session = FakeSession(answer())

    live(session, key_file)

    [request] = session.requests
    assert request["url"] == "https://api.stlouisfed.org/fred/series/observations"
    assert request["params"] == {
        "series_id": "DGS10",
        "api_key": KEY,
        "file_type": "json",
        "observation_start": "2021-11-24",
    }
    assert request["timeout"] > 0
    assert request["allow_redirects"] is False  # a redirect would carry the key to another address


def test_the_window_follows_the_setting(key_file):
    three_years = {**SETTINGS, "data": {**SETTINGS["data"], "risk_free_average_years": 3}}
    session = FakeSession(answer())

    live(session, key_file, settings=three_years)

    assert session.requests[0]["params"]["observation_start"] == "2023-11-24"


def test_five_years_before_29_february_is_28_february():
    assert fred.window_start(date(2028, 2, 29), 5) == date(2023, 2, 28)


def test_the_key_can_come_from_the_environment(monkeypatch, tmp_path):
    monkeypatch.setenv("FRED_API_KEY", KEY)
    session = FakeSession(answer())

    live(session, tmp_path / "absent.env")

    assert session.requests[0]["params"]["api_key"] == KEY


# --- one download per day, kept in memory --------------------------------------------------------------------------


def test_one_download_per_day(key_file):
    session = FakeSession(answer())

    first = live(session, key_file)
    again = live(session, key_file)
    assert len(session.requests) == 1
    assert again == first

    live(session, key_file, today=date(2026, 11, 25))
    assert len(session.requests) == 2


def test_after_a_failed_download_fred_is_asked_again_only_after_ten_minutes(key_file):
    clock = Clock()
    assert live(FakeSession(error=requests.ConnectionError("no route")), key_file, clock=clock).kind == "assumption"

    working = FakeSession(answer())
    clock.now += fred.FAILURE_PAUSE_SECONDS - 1
    paused = live(working, key_file, clock=clock)
    assert paused.kind == "assumption" and "reached" in paused.note
    assert working.requests == []

    clock.now += 1
    assert live(working, key_file, clock=clock).kind == "derived"
    assert len(working.requests) == 1


def test_a_failure_pauses_only_its_own_day(key_file):
    clock = Clock()
    live(FakeSession(error=requests.ConnectionError("no route")), key_file, clock=clock)

    assert live(FakeSession(answer()), key_file, today=date(2026, 11, 25), clock=clock).kind == "derived"


def test_a_successful_download_ends_the_pause(key_file):
    clock = Clock()
    live(FakeSession(error=requests.ConnectionError("no route")), key_file, clock=clock)
    clock.now += fred.FAILURE_PAUSE_SECONDS

    assert live(FakeSession(answer()), key_file, clock=clock).kind == "derived"
    assert fred._FAILED == {}


def test_a_key_added_later_is_used_at_once(tmp_path, key_file):
    assert live(NoNetwork(), tmp_path / "absent.env").kind == "assumption"

    assert live(FakeSession(answer()), key_file).kind == "derived"


def test_demo_mode_after_a_live_download_still_uses_the_saved_value(key_file):
    assert live(FakeSession(answer()), key_file).kind == "derived"

    rate = fred.risk_free_rate(demo=True, env_file=key_file, session=NoNetwork(), today=TODAY, settings=SETTINGS)

    check_fallback(rate, "demo mode")


def test_a_live_download_after_demo_mode_is_not_the_saved_value(key_file):
    fred.risk_free_rate(demo=True, env_file=key_file, session=NoNetwork(), today=TODAY, settings=SETTINGS)
    session = FakeSession(answer())

    assert live(session, key_file).kind == "derived"
    assert len(session.requests) == 1


# --- the dated fallback ----------------------------------------------------------------------------------------------


def check_fallback(rate, reason_words):
    assert (rate.kind, rate.value, rate.unit) == ("assumption", 0.04, "pure")
    assert (rate.period_start, rate.period_end) == (date(2020, 11, 20), date(2025, 11, 20))
    assert "2020-11-20" in rate.note and "2025-11-20" in rate.note
    assert reason_words in rate.note
    # The note is shown to customers on the sources page: no file, setting or team names (security review of S2b).
    for internal in ("app/.env", "FRED_API_KEY", "settings.yaml", "member A"):
        assert internal not in rate.note


def test_demo_mode_uses_the_saved_value_without_the_network(key_file):
    rate = fred.risk_free_rate(demo=True, env_file=key_file, session=NoNetwork(), today=TODAY, settings=SETTINGS)

    check_fallback(rate, "demo mode")


def test_no_key_uses_the_saved_value_without_the_network(tmp_path):
    empty = tmp_path / "empty.env"
    empty.write_text("SEC_USER_AGENT=\"A Student a.student@example.org\"\nFRED_API_KEY=\n", encoding="utf-8")

    check_fallback(live(NoNetwork(), empty), "no FRED key")


def test_a_key_in_the_wrong_format_is_never_sent(tmp_path):
    placeholder = tmp_path / "placeholder.env"
    placeholder.write_text("FRED_API_KEY=your-fred-key-here\n", encoding="utf-8")

    rate = live(NoNetwork(), placeholder)

    check_fallback(rate, "not in FRED's format")
    assert "your-fred-key-here" not in rate.note


@pytest.mark.parametrize(
    "session, reason_words",
    [
        (FakeSession(error=requests.ConnectionError(f"Max retries exceeded with url: /x?api_key={KEY}")), "reached"),
        (FakeSession(error=requests.Timeout(f"read timed out: /x?api_key={KEY}")), "reached"),
        (FakeSession(error=RuntimeError(f"something else went wrong: /x?api_key={KEY}")), "could not be used"),
        (FakeSession(FakeResponse(400, f'{{"error_message": "bad api_key {KEY}"}}'.encode())), "HTTP 400"),
        (FakeSession(FakeResponse(500, b"server error")), "HTTP 500"),
        (FakeSession(FakeResponse(200, b"<html>busy</html>")), "could not be read"),
        (FakeSession(FakeResponse(200, b"[" * 200_000)), "could not be"),
        (FakeSession(answer([])), "no values"),
        (FakeSession(answer([row("2026-11-23", ".")])), "no values"),
        (FakeSession(answer([row("2026-11-23", "4.1x")])), "could not be read"),
        (FakeSession(answer([row("2026-11-23", "NaN")])), "could not be read"),
        (FakeSession(answer([row("2026-11-23", None)])), "could not be read"),
        (FakeSession(answer([{"date": "2026-11-23"}])), "could not be read"),
        (FakeSession(answer([row("2026-11-20", "4.00"), row("2026-11-20", "4.00")])), "appears twice"),
        (FakeSession(answer([row("2026-11-20", "4.00"), row("2026-11-20", "4.10")])), "appears twice"),
    ],
    ids=["no connection", "timeout", "any other error", "key refused", "server error", "not JSON",
         "nested too deep", "empty", "only gaps", "not a number", "NaN", "null value", "no value field",
         "same day twice", "same day, two values"],
)
def test_an_unusable_answer_uses_the_saved_value(key_file, session, reason_words):
    rate = live(session, key_file)

    check_fallback(rate, reason_words)


@pytest.mark.parametrize(
    "values",
    [["-0.50"], ["0.00"], ["20.00"], ["25.00"], ["1e308", "1e308"]],
    ids=["negative", "zero", "20 percent", "above 20 percent", "too large to add up"],
)
def test_an_average_outside_0_to_20_percent_is_not_used(key_file, values):
    rows = [row(f"2026-11-{16 + i}", value) for i, value in enumerate(values)]

    rate = live(FakeSession(answer(rows)), key_file)

    check_fallback(rate, "plausible range")


@pytest.mark.parametrize("value, expected", [("0.01", 0.0001), ("19.99", 0.1999)], ids=["0.01 percent", "19.99 percent"])
def test_an_average_just_inside_the_limits_is_used(key_file, value, expected):
    rate = live(FakeSession(answer([row("2026-11-23", value)])), key_file)

    assert rate.kind == "derived"
    assert rate.value == pytest.approx(expected)


# --- the key never leaves the request --------------------------------------------------------------------------------


@pytest.mark.parametrize(
    "session",
    [
        FakeSession(answer()),
        FakeSession(error=requests.ConnectionError(f"Max retries exceeded with url: /x?api_key={KEY}")),
        FakeSession(error=RuntimeError(f"something else went wrong: /x?api_key={KEY}")),
        FakeSession(FakeResponse(400, f'{{"error_message": "bad api_key {KEY}"}}'.encode())),
    ],
    ids=["success", "no connection", "any other error", "key refused"],
)
def test_the_key_appears_nowhere_in_the_result(key_file, session):
    rate = live(session, key_file)

    assert KEY not in repr(rate)
    assert KEY not in repr(fred._MEMORY) and KEY not in repr(fred._FAILED)


# --- missing is never zero --------------------------------------------------------------------------------------------


def test_without_a_saved_value_the_rate_is_missing_not_zero():
    no_value = {**SETTINGS, "valuation": {"risk_free_rate": None}}

    rate = fred.risk_free_rate(demo=True, session=NoNetwork(), today=TODAY, settings=no_value)

    assert rate.kind == "missing" and rate.value is None
    assert "demo mode" in rate.note


def test_the_saved_value_names_the_treasury_as_its_source(key_file):
    # FRED's terms forbid storing FRED data (item (p)), so the saved average is computed from the US Treasury's own
    # public-domain file (Flo's review of PR #42; decided by Igor, 24 November). Its label must say so.
    rate = fred.risk_free_rate(demo=True, env_file=key_file, session=NoNetwork(), today=TODAY, settings=SETTINGS)

    assert (rate.tag, rate.form) == ("10 Yr", "US Treasury")
    assert "US Treasury's Daily Treasury Par Yield Curve Rates" in rate.note
    assert "FRED" not in rate.note


# --- the saved value in app/settings.yaml -----------------------------------------------------------------------------


def test_the_saved_fallback_is_set_and_dated():
    settings = load_settings()
    value = settings["valuation"]["risk_free_rate"]
    start, end = settings["data"]["risk_free_fallback_period"]

    assert value is not None and 0 < value < 0.2, "a decimal, e.g. 0.042 for 4.2%"
    assert isinstance(start, date) and isinstance(end, date)
    assert 4.9 < (end - start).days / 365.25 < 5.1, "the period covers five years"


def test_the_interface_gets_the_rate_from_the_company_module():
    from src.data.company import risk_free_rate

    assert risk_free_rate is fred.risk_free_rate


def test_the_interface_gets_freds_notice_from_the_company_module():
    # FRED's terms require the notice on screen; the interface may import only src.data.company (layering test).
    from src.data import company

    assert company.FRED_NOTICE == (
        "This product uses the FRED® API but is not endorsed or certified by the Federal Reserve Bank of St. Louis."
    )
    assert "FRED_NOTICE" in company.__all__



# --- S18 break-it round (27 November 2026): breaks no earlier test caught ------------------------------------------
# Each test failed against its deliberate break in a throwaway copy and passes on the unchanged code, except where its
# comment says otherwise.


def test_the_pause_after_a_failure_is_ten_minutes(key_file):
    # FRED-pause-60. The earlier test counts from fred.FAILURE_PAUSE_SECONDS itself, so a shorter pause passed. Igor's
    # decision (24 November, module docstring): ten minutes. At 599 seconds FRED is not asked; at 600 it is.
    clock = Clock()
    live(FakeSession(error=requests.ConnectionError("no route")), key_file, clock=clock)
    working = FakeSession(answer())

    clock.now += 599
    assert live(working, key_file, clock=clock).kind == "assumption" and working.requests == []
    clock.now += 1
    assert live(working, key_file, clock=clock).kind == "derived"


def test_quotes_around_the_key_in_the_environment_are_removed(monkeypatch, tmp_path):
    # FRED-key-quotes. A key set with its quotes (FRED_API_KEY="..." typed in a Windows shell) is still the key, as for
    # SEC_USER_AGENT (test_quotes_around_the_user_agent_are_removed).
    monkeypatch.setenv("FRED_API_KEY", f'"{KEY}"')
    session = FakeSession(answer())

    assert live(session, tmp_path / "absent.env").kind == "derived"
    assert session.requests[0]["params"]["api_key"] == KEY


def test_a_settings_file_saved_with_a_byte_order_mark_is_read(tmp_path):
    # Windows Notepad saves "UTF-8 with BOM"; the key in such a file must still be found. Written for the break
    # FRED-bom, which it does not catch: python-dotenv removes the mark itself, so that break changes nothing.
    env_file = tmp_path / "bom.env"
    env_file.write_text(f'FRED_API_KEY="{KEY}"\n', encoding="utf-8-sig")
    session = FakeSession(answer())

    assert live(session, env_file).kind == "derived"
    assert session.requests[0]["params"]["api_key"] == KEY


def test_the_real_settings_average_five_years(key_file):
    # SET-rf-years. SPEC v2.3 §4 and §8.1 (decided by Igor, 20 November): the last five years. With the real
    # settings.yaml, 24 November 2026 asks FRED from 24 November 2021.
    session = FakeSession(answer())

    live(session, key_file, settings=load_settings())

    assert session.requests[0]["params"]["observation_start"] == "2021-11-24"
