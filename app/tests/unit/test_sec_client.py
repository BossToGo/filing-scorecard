"""SEC client and cache (slice S1). Owner: A.

Expected behaviour from SPEC §4: a declared User-Agent on every request, at most 5 requests per second (the
`data` section of settings.yaml), three retries with a growing pause, then the input is unreachable; every raw
response saved with its retrieval time and reused, so nothing is downloaded twice. Responses come from the saved
demo files through a fake connection: no network. Known answer: Coca-Cola's SEC number 0000021344 (session 5,
slide 30).
"""

import json
from datetime import datetime, timezone
from pathlib import Path

import pytest
import requests

from src.data.sec_client import (
    FACTS_URL,
    SUBMISSIONS_URL,
    TICKERS_URL,
    MissingUserAgent,
    NotFound,
    SecClient,
    SecError,
    SourceUnreachable,
    UnknownTicker,
    check_user_agent,
    user_agent_from_env,
)

DEMO = Path(__file__).resolve().parents[2] / "evidence" / "demo"
AGENT = "Test Person test.person@example.org"
KO = "0000021344"
NOW = datetime(2026, 11, 18, 15, 0, tzinfo=timezone.utc)


class Response:
    def __init__(self, status, content=b""):
        self.status_code = status
        self.content = content


class Session:
    """Answers each URL with the next scripted response (or raises the scripted exception)."""

    def __init__(self, script):
        self.script = {url: list(items) for url, items in script.items()}
        self.calls = []

    def get(self, url, headers=None, timeout=None):
        self.calls.append({"url": url, "headers": dict(headers or {}), "timeout": timeout})
        item = self.script[url].pop(0)
        if isinstance(item, Exception):
            raise item
        return item


class Clock:
    def __init__(self):
        self.t = 1000.0
        self.sleeps = []

    def monotonic(self):
        return self.t

    def sleep(self, seconds):
        self.sleeps.append(round(seconds, 6))
        self.t += seconds


def saved(*parts):
    return DEMO.joinpath(*parts).read_bytes()


def ok(*parts):
    return Response(200, saved(*parts))


def client(script, tmp_path, clock=None, **options):
    clock = clock or Clock()
    session = Session(script)
    sec = SecClient(AGENT, tmp_path / "cache", session=session, clock=clock.monotonic, sleep=clock.sleep,
                    now=lambda: NOW, **options)
    return sec, session, clock


SUB_KO = SUBMISSIONS_URL.format(cik=KO)
FACTS_KO = FACTS_URL.format(cik=KO)


# --- the declared identity ------------------------------------------------------------------------------------


def test_every_request_carries_the_declared_user_agent(tmp_path):
    sec, session, _ = client({SUB_KO: [ok("KO", "submissions.json")]}, tmp_path)
    sec.submissions(KO)
    assert session.calls[0]["headers"]["User-Agent"] == AGENT
    assert session.calls[0]["url"] == "https://data.sec.gov/submissions/CIK0000021344.json"
    assert session.calls[0]["timeout"] > 0


@pytest.mark.parametrize(
    "agent",
    [None, "", "   ", "Firstname Lastname firstname.lastname@example.com", "Test Person", "Test “Person” t@x.org"],
)
def test_a_missing_example_or_unreadable_user_agent_is_refused_without_showing_it(agent):
    with pytest.raises(MissingUserAgent) as error:
        check_user_agent(agent)
    assert "SEC_USER_AGENT" in str(error.value)
    if agent and agent.strip():
        assert agent not in str(error.value)


def test_the_user_agent_comes_from_the_environment_or_the_env_file(tmp_path, monkeypatch):
    env_file = tmp_path / ".env"
    env_file.write_text('SEC_USER_AGENT="File Person file.person@example.org"\n', encoding="utf-8")
    monkeypatch.delenv("SEC_USER_AGENT", raising=False)
    assert user_agent_from_env(env_file) == "File Person file.person@example.org"
    monkeypatch.setenv("SEC_USER_AGENT", AGENT)  # an inline setting wins over the file
    assert user_agent_from_env(env_file) == AGENT


def test_the_user_agent_is_never_written_to_the_cache(tmp_path):
    sec, _, _ = client({SUB_KO: [ok("KO", "submissions.json")], FACTS_KO: [ok("KO", "companyfacts.json")]}, tmp_path)
    sec.submissions(KO)
    sec.companyfacts(KO)
    for path in (tmp_path / "cache").iterdir():
        text = path.read_text(encoding="utf-8")
        assert AGENT not in text and "test.person@example.org" not in text


# --- at most 5 requests per second -----------------------------------------------------------------------------


def test_requests_are_spaced_to_at_most_five_per_second(tmp_path):
    script = {SUB_KO: [ok("KO", "submissions.json")], FACTS_KO: [ok("KO", "companyfacts.json")],
              TICKERS_URL: [ok("tickers.json")]}
    sec, _, clock = client(script, tmp_path)
    sec.submissions(KO)
    sec.companyfacts(KO)
    sec.ticker_list()
    assert clock.sleeps == [0.2, 0.2]


def test_the_limit_comes_from_settings_yaml(tmp_path, monkeypatch):
    monkeypatch.setenv("SEC_USER_AGENT", AGENT)
    sec = SecClient.from_settings(cache_dir=tmp_path, env_file=tmp_path / "no.env")
    assert sec.max_per_second == 5 and sec.retries == 3


# --- three retries with a growing pause, then unreachable ------------------------------------------------------


def test_a_temporary_failure_is_retried_with_a_growing_pause(tmp_path):
    sec, session, clock = client({SUB_KO: [Response(503), Response(429), ok("KO", "submissions.json")]}, tmp_path)
    assert sec.submissions(KO).data["cik"] == KO
    assert len(session.calls) == 3
    assert clock.sleeps == [1, 2]


def test_a_connection_error_is_retried(tmp_path):
    sec, session, clock = client({SUB_KO: [requests.ConnectionError("down"), ok("KO", "submissions.json")]}, tmp_path)
    assert sec.submissions(KO).data["name"]
    assert clock.sleeps == [1]


def test_after_three_retries_the_source_is_unreachable_and_the_message_says_what_to_do(tmp_path):
    sec, session, clock = client({SUB_KO: [Response(503)] * 4}, tmp_path)
    with pytest.raises(SourceUnreachable, match="demo mode"):
        sec.submissions(KO)
    assert len(session.calls) == 4  # the first try and three retries
    assert clock.sleeps == [1, 2, 4]
    assert not (tmp_path / "cache" / f"submissions_{KO}.json").exists()


def test_a_page_that_does_not_exist_is_not_retried(tmp_path):
    url = SUBMISSIONS_URL.format(cik="0000000001")
    sec, session, clock = client({url: [Response(404)]}, tmp_path)
    with pytest.raises(NotFound):
        sec.submissions("1")
    assert len(session.calls) == 1 and clock.sleeps == []


def test_an_answer_that_is_not_json_is_refused_and_not_cached(tmp_path):
    sec, _, _ = client({SUB_KO: [Response(200, b"<html>Request rate threshold exceeded</html>")]}, tmp_path)
    with pytest.raises(SecError, match="JSON"):
        sec.submissions(KO)
    assert not (tmp_path / "cache" / f"submissions_{KO}.json").exists()


# --- every raw response saved with its retrieval time; nothing downloaded twice --------------------------------


def test_a_download_is_saved_with_its_retrieval_time_and_reused(tmp_path):
    sec, session, _ = client({SUB_KO: [ok("KO", "submissions.json")]}, tmp_path)
    first = sec.submissions(KO)
    again = sec.submissions(KO)
    assert len(session.calls) == 1
    assert (first.from_cache, again.from_cache) == (False, True)
    assert again.data == first.data
    assert again.retrieved == first.retrieved == NOW
    cache = tmp_path / "cache"
    assert (cache / f"submissions_{KO}.json").read_bytes() == saved("KO", "submissions.json")
    record = json.loads((cache / f"submissions_{KO}.provenance.json").read_text(encoding="utf-8"))
    assert record["source"] == SUB_KO and record["retrieved"] == "2026-11-18T15:00:00+00:00"
    assert first.provenance == record


def test_refresh_downloads_again(tmp_path):
    sec, session, _ = client({SUB_KO: [ok("KO", "submissions.json"), ok("KO", "submissions.json")]}, tmp_path)
    sec.submissions(KO)
    assert sec.submissions(KO, refresh=True).from_cache is False
    assert len(session.calls) == 2


# --- ticker lookup ---------------------------------------------------------------------------------------------


def test_a_ticker_is_turned_into_the_ten_digit_sec_number(tmp_path):
    sec, session, _ = client({TICKERS_URL: [ok("tickers.json")]}, tmp_path)
    assert sec.cik_for("KO") == KO  # session 5, slide 30
    assert sec.cik_for(" ko ") == KO
    assert sec.company_name("KO") == "COCA COLA CO"
    assert len(session.calls) == 1  # the ticker list is downloaded once


def test_a_class_share_ticker_with_a_dot_is_found(tmp_path):
    tickers = json.dumps({"0": {"cik_str": 1067983, "ticker": "BRK-B", "title": "BERKSHIRE HATHAWAY INC"}}).encode()
    sec, _, _ = client({TICKERS_URL: [Response(200, tickers)]}, tmp_path)
    assert sec.cik_for("brk.b") == "0001067983"


def test_an_unknown_ticker_says_how_to_fix_it(tmp_path):
    sec, _, _ = client({TICKERS_URL: [ok("tickers.json")]}, tmp_path)
    with pytest.raises(UnknownTicker, match="spelling"):
        sec.cik_for("NOPE")


@pytest.mark.parametrize("cik", ["21344", 21344, "0000021344"])
def test_the_sec_number_is_padded_to_ten_digits(tmp_path, cik):
    sec, session, _ = client({SUB_KO: [ok("KO", "submissions.json")]}, tmp_path)
    sec.submissions(cik)
    assert session.calls[0]["url"].endswith("CIK0000021344.json")


@pytest.mark.parametrize("cik", ["CIK21344", "-1", "12345678901", ""])
def test_a_malformed_sec_number_is_refused(tmp_path, cik):
    sec, session, _ = client({}, tmp_path)
    with pytest.raises(ValueError):
        sec.submissions(cik)
    assert session.calls == []
