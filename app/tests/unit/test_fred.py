"""The risk-free rate: FRED DGS10, averaged over the last five years, or the dated fallback (slice S2b, SPEC §4,
§8.1). Owner: A.

No test uses the network: FRED's answers come from fake sessions built on `tests/fixtures/fred_dgs10_small.json`,
a hand-made answer in the shape FRED documents (https://fred.stlouisfed.org/docs/api/fred/series_observations.html),
not a real download. No test reads the real app/.env: each one points the module at a file in a temporary folder.

Expected values:
- the average of the fixture's six days (one without a value): Igor's hand working, 24 November 2026;
- percent to decimal: DGS10 is in percent (FRED series page, read on 24 November 2026), so 4.50 is 0.045;
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


class NoNetwork(FakeSession):
    def get(self, url, params=None, **options):
        raise AssertionError("this case must not download anything")


def answer(observations=None, status_code=200):
    data = json.loads(FIXTURE.read_text(encoding="utf-8"))
    if observations is not None:
        data["observations"] = observations
    return FakeResponse(status_code, json.dumps(data).encode("utf-8"))


@pytest.fixture(autouse=True)
def no_real_env(tmp_path, monkeypatch):
    monkeypatch.delenv("FRED_API_KEY", raising=False)
    monkeypatch.setattr(fred, "ENV_FILE", tmp_path / "absent.env")
    fred.forget()
    yield
    fred.forget()


@pytest.fixture
def key_file(tmp_path):
    path = tmp_path / "with_key.env"
    path.write_text(f'FRED_API_KEY="{KEY}"\n', encoding="utf-8")
    return path


def live(session, env_file, today=TODAY, settings=SETTINGS):
    return fred.risk_free_rate(demo=False, env_file=env_file, session=session, today=today, settings=settings)


# --- live: the average of the days with a value ------------------------------------------------------------------


def test_the_rate_is_the_average_of_the_days_with_a_value(key_file):
    rate = live(FakeSession(answer()), key_file)

    assert rate.value == pytest.approx(IGOR_AVERAGE)
    assert (rate.kind, rate.unit, rate.tag, rate.form) == ("derived", "pure", "DGS10", "FRED")


def test_the_period_runs_from_the_first_to_the_last_day_with_a_value(key_file):
    rate = live(FakeSession(answer()), key_file)

    assert (rate.period_start, rate.period_end) == (date(2026, 11, 16), date(2026, 11, 23))
    assert "5 daily values" in rate.note
    assert isinstance(rate.retrieved, datetime)


def test_percent_becomes_a_decimal(key_file):
    rate = live(FakeSession(answer([{"date": "2026-11-23", "value": "4.50"}])), key_file)

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


def test_a_failed_download_is_tried_again_on_the_next_call(key_file):
    failing = FakeSession(error=requests.ConnectionError("no route"))
    assert live(failing, key_file).kind == "assumption"

    working = FakeSession(answer())
    assert live(working, key_file).kind == "derived"


# --- the dated fallback ----------------------------------------------------------------------------------------------


def check_fallback(rate, reason_words):
    assert (rate.kind, rate.value, rate.unit) == ("assumption", 0.04, "pure")
    assert (rate.period_start, rate.period_end) == (date(2020, 11, 20), date(2025, 11, 20))
    assert "2020-11-20" in rate.note and "2025-11-20" in rate.note
    assert reason_words in rate.note


def test_demo_mode_uses_the_saved_value_without_the_network(key_file):
    rate = fred.risk_free_rate(demo=True, env_file=key_file, session=NoNetwork(), today=TODAY, settings=SETTINGS)

    check_fallback(rate, "demo mode")


def test_no_key_uses_the_saved_value_without_the_network(tmp_path):
    empty = tmp_path / "empty.env"
    empty.write_text("SEC_USER_AGENT=\"A Student a.student@example.org\"\nFRED_API_KEY=\n", encoding="utf-8")

    check_fallback(live(NoNetwork(), empty), "FRED_API_KEY")


def test_a_key_in_the_wrong_format_is_never_sent(tmp_path):
    placeholder = tmp_path / "placeholder.env"
    placeholder.write_text("FRED_API_KEY=your-fred-key-here\n", encoding="utf-8")

    rate = live(NoNetwork(), placeholder)

    check_fallback(rate, "32 lower-case letters and digits")
    assert "your-fred-key-here" not in rate.note


@pytest.mark.parametrize(
    "session, reason_words",
    [
        (FakeSession(error=requests.ConnectionError(f"Max retries exceeded with url: /x?api_key={KEY}")), "reached"),
        (FakeSession(error=requests.Timeout(f"read timed out: /x?api_key={KEY}")), "reached"),
        (FakeSession(FakeResponse(400, f'{{"error_message": "bad api_key {KEY}"}}'.encode())), "HTTP 400"),
        (FakeSession(FakeResponse(500, b"server error")), "HTTP 500"),
        (FakeSession(FakeResponse(200, b"<html>busy</html>")), "could not be read"),
        (FakeSession(answer([])), "no values"),
        (FakeSession(answer([{"date": "2026-11-23", "value": "."}])), "no values"),
        (FakeSession(answer([{"date": "2026-11-23", "value": "4.1x"}])), "could not be read"),
    ],
    ids=["no connection", "timeout", "key refused", "server error", "not JSON", "empty", "only gaps", "not a number"],
)
def test_an_unusable_answer_uses_the_saved_value(key_file, session, reason_words):
    rate = live(session, key_file)

    check_fallback(rate, reason_words)


# --- the key never leaves the request --------------------------------------------------------------------------------


@pytest.mark.parametrize(
    "session",
    [
        FakeSession(answer()),
        FakeSession(error=requests.ConnectionError(f"Max retries exceeded with url: /x?api_key={KEY}")),
        FakeSession(FakeResponse(400, f'{{"error_message": "bad api_key {KEY}"}}'.encode())),
    ],
    ids=["success", "no connection", "key refused"],
)
def test_the_key_appears_nowhere_in_the_result(key_file, session):
    rate = live(session, key_file)

    assert KEY not in repr(rate)
    assert all(KEY not in repr(remembered) for remembered in fred._MEMORY.items())


# --- missing is never zero --------------------------------------------------------------------------------------------


def test_without_a_saved_value_the_rate_is_missing_not_zero():
    no_value = {**SETTINGS, "valuation": {"risk_free_rate": None}}

    rate = fred.risk_free_rate(demo=True, session=NoNetwork(), today=TODAY, settings=no_value)

    assert rate.kind == "missing" and rate.value is None
    assert "demo mode" in rate.note


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
