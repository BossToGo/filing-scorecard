"""SEC client and cache (slice S1). Owner: A.

Expected behaviour from SPEC §4: a declared User-Agent (name and e-mail) on every request, never stored or shown;
at most `max_requests_per_second` requests per second for the whole app (settings.yaml); three retries with a
growing pause, then the input is unreachable; every raw response saved with its retrieval time and reused, so
nothing is downloaded twice. Responses come from the saved demo files through a fake connection: no network.
Known answer: Coca-Cola's SEC number 0000021344 (session 5, slide 30).
"""

import json
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest
import requests

import src.data.sec_client as sec_client
from src.data.sec_client import (
    FACTS_URL,
    SUBMISSIONS_URL,
    TICKERS_URL,
    InvalidCik,
    MissingUserAgent,
    NotFound,
    RateLimiter,
    SecClient,
    SecError,
    SecRefused,
    SourceUnreachable,
    UnknownTicker,
    check_user_agent,
    user_agent_from_env,
)

DEMO = Path(__file__).resolve().parents[2] / "evidence" / "demo"
AGENT = "Test Person test.person@example.org"
KO = "0000021344"
START = datetime(2026, 11, 18, 15, 0, tzinfo=timezone.utc)


class Response:
    def __init__(self, status, content=b""):
        self.status_code = status
        self.content = content


class Session:
    """Answers each URL with the next scripted response (or raises the scripted exception)."""

    def __init__(self, script=None):
        self.script = {url: list(items) for url, items in (script or {}).items()}
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


class Now:
    """A wall clock that moves one minute every time it is read."""

    def __init__(self):
        self.calls = 0

    def __call__(self):
        self.calls += 1
        return START + timedelta(minutes=self.calls - 1)


def saved(*parts):
    return DEMO.joinpath(*parts).read_bytes()


def ok(*parts):
    return Response(200, saved(*parts))


def client(script, tmp_path, clock=None, now=None, **options):
    clock = clock or Clock()
    session = Session(script)
    sec = SecClient(AGENT, tmp_path / "cache", session=session, clock=clock.monotonic, sleep=clock.sleep,
                    now=now or Now(), **options)
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
    [
        None,
        "",
        "   ",
        "Firstname Lastname firstname.lastname@example.com",  # the example of .env.example
        "Test Person",  # no e-mail
        "test.person@example.org",  # no name
        "Test Person @",  # not an e-mail
        "Test “Person” t@x.org",  # curly quotes typed by the Mac
        "Jürgen Müller j@x.org",  # accented letters
        "Test Person\nX-Evil: 1 t@x.org",  # a line break would inject a header
    ],
)
def test_a_missing_example_or_unreadable_user_agent_is_refused_without_showing_it(agent):
    with pytest.raises(MissingUserAgent) as error:
        check_user_agent(agent)
    assert "SEC_USER_AGENT" in str(error.value)
    if agent and agent.strip():
        assert agent.strip() not in str(error.value)


@pytest.mark.parametrize("quoted", ['"Test Person test.person@example.org"', "'Test Person test.person@example.org'"])
def test_quotes_around_the_user_agent_are_removed(quoted):
    assert check_user_agent(quoted) == AGENT


def test_the_user_agent_comes_from_the_environment_or_the_env_file(tmp_path, monkeypatch):
    env_file = tmp_path / ".env"
    env_file.write_text('SEC_USER_AGENT="File Person file.person@example.org"\n', encoding="utf-8")
    monkeypatch.delenv("SEC_USER_AGENT", raising=False)
    assert user_agent_from_env(env_file) == "File Person file.person@example.org"
    monkeypatch.setenv("SEC_USER_AGENT", AGENT)  # an inline setting wins over the file
    assert user_agent_from_env(env_file) == AGENT


def test_an_env_file_saved_as_utf16_by_windows_gives_a_clear_message(tmp_path, monkeypatch):
    env_file = tmp_path / ".env"
    env_file.write_text(f'SEC_USER_AGENT="{AGENT}"\n', encoding="utf-16")
    monkeypatch.delenv("SEC_USER_AGENT", raising=False)
    with pytest.raises(MissingUserAgent, match="UTF-8"):
        user_agent_from_env(env_file)


def test_the_user_agent_is_never_written_to_the_cache(tmp_path):
    sec, _, _ = client({SUB_KO: [ok("KO", "submissions.json")], FACTS_KO: [ok("KO", "companyfacts.json")]}, tmp_path)
    sec.submissions(KO)
    sec.companyfacts(KO)
    for path in (tmp_path / "cache").iterdir():
        text = path.read_text(encoding="utf-8")
        assert AGENT not in text and "test.person@example.org" not in text


def test_the_user_agent_does_not_show_in_the_client_or_its_errors(tmp_path):
    url404 = SUBMISSIONS_URL.format(cik="0000000001")
    sec, session, _ = client({SUB_KO: [Response(503)] * 4, url404: [Response(404)], FACTS_KO: [Response(403)]}, tmp_path)
    assert AGENT not in repr(vars(sec)) and AGENT not in repr(sec)
    messages = []
    for call in (lambda: sec.submissions(KO), lambda: sec.submissions("1"), lambda: sec.companyfacts(KO)):
        with pytest.raises(SecError) as error:
            call()
        messages.append(str(error.value))
    assert all(AGENT not in m and "test.person" not in m for m in messages)
    assert all(c["headers"]["User-Agent"] == AGENT for c in session.calls)  # retries included


# --- at most 5 requests per second, for the whole app ----------------------------------------------------------


def test_requests_are_spaced_to_at_most_five_per_second(tmp_path):
    script = {SUB_KO: [ok("KO", "submissions.json")], FACTS_KO: [ok("KO", "companyfacts.json")],
              TICKERS_URL: [ok("tickers.json")]}
    sec, _, clock = client(script, tmp_path)
    sec.submissions(KO)
    sec.companyfacts(KO)
    sec.ticker_list()
    assert clock.sleeps == [0.2, 0.2]


def test_two_clients_sharing_the_app_s_limiter_stay_within_the_limit(tmp_path):
    clock = Clock()
    limiter = RateLimiter(clock=clock.monotonic, sleep=clock.sleep)
    first = SecClient(AGENT, tmp_path / "a", session=Session({SUB_KO: [ok("KO", "submissions.json")]}),
                      limiter=limiter, sleep=clock.sleep, now=Now())
    second = SecClient(AGENT, tmp_path / "b", session=Session({SUB_KO: [ok("KO", "submissions.json")]}),
                       limiter=limiter, sleep=clock.sleep, now=Now())
    first.submissions(KO)
    second.submissions(KO)
    assert clock.sleeps == [0.2]


def test_clients_made_by_the_app_share_one_limiter(tmp_path):
    assert SecClient(AGENT, tmp_path)._limiter is SecClient(AGENT, tmp_path)._limiter


def test_the_limits_come_from_settings_yaml(tmp_path, monkeypatch):
    monkeypatch.setenv("SEC_USER_AGENT", AGENT)
    monkeypatch.setattr(sec_client, "load_settings", lambda: {"data": {"max_requests_per_second": 2, "retries": 1}})
    clock = Clock()
    session = Session({SUB_KO: [Response(503), Response(503)], FACTS_KO: [ok("KO", "companyfacts.json")]})
    sec = SecClient.from_settings(cache_dir=tmp_path, env_file=tmp_path / "no.env", session=session,
                                  clock=clock.monotonic, sleep=clock.sleep, now=Now())
    with pytest.raises(SourceUnreachable):
        sec.submissions(KO)
    assert len(session.calls) == 2 and clock.sleeps == [1]  # one retry only
    sec.companyfacts(KO)
    assert clock.sleeps == [1, 0.5]  # 2 per second: 0.5 s since the last attempt, which followed the 1 s pause


def test_the_real_settings_are_five_per_second_and_three_retries(tmp_path, monkeypatch):
    monkeypatch.setenv("SEC_USER_AGENT", AGENT)
    sec = SecClient.from_settings(cache_dir=tmp_path, env_file=tmp_path / "no.env")
    assert sec.max_per_second == 5 and sec.retries == 3


@pytest.mark.parametrize("options", [{"max_per_second": 0}, {"max_per_second": 11}, {"retries": -1}, {"retries": 1.5}])
def test_impossible_limits_are_refused_when_the_client_is_made(tmp_path, options):
    with pytest.raises(ValueError):
        SecClient(AGENT, tmp_path, **options)


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
    with pytest.raises(SourceUnreachable, match="demo mode") as error:
        sec.submissions(KO)
    assert len(session.calls) == 4  # the first try and three retries
    assert clock.sleeps == [1, 2, 4]
    assert "4 attempts" in str(error.value)
    assert not (tmp_path / "cache" / f"submissions_{KO}.json").exists()


def test_with_no_retries_there_is_one_attempt_and_no_pause(tmp_path):
    sec, session, clock = client({SUB_KO: [Response(503)]}, tmp_path, retries=0)
    with pytest.raises(SourceUnreachable, match="1 attempt"):
        sec.submissions(KO)
    assert len(session.calls) == 1 and clock.sleeps == []


def test_a_refusal_by_the_sec_is_not_retried_and_points_to_the_user_agent(tmp_path):
    sec, session, clock = client({SUB_KO: [Response(403)]}, tmp_path)
    with pytest.raises(SecRefused, match="SEC_USER_AGENT") as error:
        sec.submissions(KO)
    assert len(session.calls) == 1 and clock.sleeps == []
    assert "retries" not in str(error.value)


def test_a_page_that_does_not_exist_is_not_retried(tmp_path):
    url = SUBMISSIONS_URL.format(cik="0000000001")
    sec, session, clock = client({url: [Response(404)]}, tmp_path)
    with pytest.raises(NotFound):
        sec.submissions("1")
    assert len(session.calls) == 1 and clock.sleeps == []


@pytest.mark.parametrize("body", [b"<html>Request rate threshold exceeded</html>", b"null", b"[]"])
def test_an_answer_that_is_not_a_json_object_is_retried_then_unreachable_and_never_cached(tmp_path, body):
    sec, session, clock = client({SUB_KO: [Response(200, body)] * 4}, tmp_path)
    with pytest.raises(SourceUnreachable, match="not JSON"):
        sec.submissions(KO)
    assert len(session.calls) == 4 and clock.sleeps == [1, 2, 4]
    assert not (tmp_path / "cache" / f"submissions_{KO}.json").exists()


# --- every raw response saved with its retrieval time; nothing downloaded twice --------------------------------


def test_a_download_is_saved_with_its_retrieval_time_and_reused_by_a_later_run(tmp_path):
    now = Now()
    sec, session, _ = client({SUB_KO: [ok("KO", "submissions.json")]}, tmp_path, now=now)
    first = sec.submissions(KO)
    # A later run of the app: a new client on the same cache folder, with a connection that must not be used.
    later = SecClient(AGENT, tmp_path / "cache", session=Session(), clock=Clock().monotonic, sleep=Clock().sleep,
                      now=now)
    again = later.submissions(KO)
    assert len(session.calls) == 1
    assert (first.from_cache, again.from_cache) == (False, True)
    assert again.data == first.data
    assert again.retrieved == first.retrieved == START  # the saved time, not the time of reading
    cache = tmp_path / "cache"
    assert (cache / f"submissions_{KO}.json").read_bytes() == saved("KO", "submissions.json")
    record = json.loads((cache / f"submissions_{KO}.provenance.json").read_text(encoding="utf-8"))
    assert record["source"] == SUB_KO and record["retrieved"] == "2026-11-18T15:00:00+00:00"
    assert first.provenance == record


def test_refresh_downloads_again_and_replaces_the_cache(tmp_path):
    newer = json.dumps({"cik": KO, "name": "COCA COLA CO (newer)"}).encode()
    sec, session, _ = client({SUB_KO: [ok("KO", "submissions.json"), Response(200, newer)]}, tmp_path)
    first = sec.submissions(KO)
    refreshed = sec.submissions(KO, refresh=True)
    assert refreshed.from_cache is False and refreshed.retrieved > first.retrieved
    cached = sec.submissions(KO)
    assert cached.from_cache and cached.data["name"] == "COCA COLA CO (newer)"
    assert cached.retrieved == refreshed.retrieved
    assert len(session.calls) == 2


@pytest.mark.parametrize("damage", ["cut_raw", "cut_provenance", "no_provenance", "no_raw", "other_raw"])
def test_a_damaged_cache_entry_is_downloaded_again(tmp_path, damage):
    sec, session, _ = client({SUB_KO: [ok("KO", "submissions.json"), ok("KO", "submissions.json")]}, tmp_path)
    sec.submissions(KO)
    raw = tmp_path / "cache" / f"submissions_{KO}.json"
    meta = tmp_path / "cache" / f"submissions_{KO}.provenance.json"
    if damage == "cut_raw":  # e.g. the computer stopped while writing
        raw.write_bytes(raw.read_bytes()[:100])
    elif damage == "cut_provenance":
        meta.write_text(meta.read_text(encoding="utf-8")[:20], encoding="utf-8")
    elif damage == "no_provenance":
        meta.unlink()
    elif damage == "no_raw":
        raw.unlink()
    else:  # new raw data next to an old provenance record: the checksum no longer matches
        raw.write_bytes(json.dumps({"cik": KO, "name": "something else"}).encode())
    again = sec.submissions(KO)
    assert again.from_cache is False and again.data["name"] == "COCA COLA CO"
    assert len(session.calls) == 2
    assert not list((tmp_path / "cache").glob("*.tmp"))


# --- ticker lookup ---------------------------------------------------------------------------------------------


def tickers(*entries):
    return Response(200, json.dumps({str(i): e for i, e in enumerate(entries)}).encode())


def test_a_ticker_is_turned_into_the_ten_digit_sec_number(tmp_path):
    sec, session, _ = client({TICKERS_URL: [ok("tickers.json")]}, tmp_path)
    assert sec.cik_for("KO") == KO  # session 5, slide 30
    assert sec.cik_for(" ko ") == KO
    assert sec.company_name("KO") == "COCA COLA CO"
    assert len(session.calls) == 1  # the ticker list is downloaded once


def test_a_class_share_ticker_with_a_dot_is_found(tmp_path):
    sec, _, _ = client({TICKERS_URL: [tickers({"cik_str": 1067983, "ticker": "BRK-B", "title": "BERKSHIRE"})]},
                       tmp_path)
    assert sec.cik_for("brk.b") == "0001067983"


def test_a_ticker_listed_twice_for_different_companies_is_reported_not_guessed(tmp_path):
    sec, _, _ = client({TICKERS_URL: [tickers({"cik_str": 1, "ticker": "AB.C", "title": "One"},
                                              {"cik_str": 2, "ticker": "AB-C", "title": "Two"})]}, tmp_path)
    with pytest.raises(SecError, match="more than one"):
        sec.cik_for("AB-C")


def test_a_refreshed_ticker_list_is_used_for_lookups(tmp_path):
    sec, _, _ = client({TICKERS_URL: [tickers({"cik_str": 1, "ticker": "AAA", "title": "A"}),
                                      tickers({"cik_str": 2, "ticker": "BBB", "title": "B"})]}, tmp_path)
    assert sec.cik_for("AAA") == "0000000001"
    sec.ticker_list(refresh=True)
    assert sec.cik_for("BBB") == "0000000002"


def test_an_unknown_ticker_says_how_to_fix_it(tmp_path):
    sec, _, _ = client({TICKERS_URL: [ok("tickers.json")]}, tmp_path)
    with pytest.raises(UnknownTicker, match="spelling"):
        sec.cik_for("NOPE")


@pytest.mark.parametrize("cik", ["21344", 21344, "0000021344"])
def test_the_sec_number_is_padded_to_ten_digits(tmp_path, cik):
    sec, session, _ = client({SUB_KO: [ok("KO", "submissions.json")]}, tmp_path)
    sec.submissions(cik)
    assert session.calls[0]["url"].endswith("CIK0000021344.json")


@pytest.mark.parametrize("cik", ["CIK21344", "-1", "12345678901", "", "٢١٣٤٤"])
def test_a_malformed_sec_number_is_refused(tmp_path, cik):
    sec, session, _ = client({}, tmp_path)
    with pytest.raises(InvalidCik):
        sec.submissions(cik)
    assert session.calls == []
