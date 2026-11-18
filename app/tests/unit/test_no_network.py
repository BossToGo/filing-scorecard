"""Tests never use the network (SPEC rule 14.10). The guard lives in `app/tests/network_guard.py` and is switched
on for the whole test session by `app/tests/conftest.py`. Owner: A."""

import socket

import pytest

from tests import network_guard

# Checked when this file is imported, before any test or fixture runs (module and session fixtures included).
GUARD_ON_AT_IMPORT = network_guard.is_installed()


def test_the_guard_is_on_before_any_test_or_fixture_runs():
    assert GUARD_ON_AT_IMPORT


def forget_attempts_since(count):
    # These tests trigger the guard on purpose; forget their attempts so the after-test check does not fail them.
    del network_guard.ATTEMPTS[count:]


def test_an_outside_connection_is_blocked():
    before = len(network_guard.ATTEMPTS)
    with pytest.raises(network_guard.NetworkBlocked, match="network"):
        socket.create_connection(("93.184.215.14", 443), timeout=1)
    forget_attempts_since(before)


def test_a_raw_socket_connection_is_blocked():
    before = len(network_guard.ATTEMPTS)
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        with pytest.raises(network_guard.NetworkBlocked):
            sock.connect(("93.184.215.14", 443))
        with pytest.raises(network_guard.NetworkBlocked):
            sock.connect_ex(("93.184.215.14", 443))
    forget_attempts_since(before)


@pytest.mark.parametrize("lookup", [socket.getaddrinfo, socket.gethostbyname, socket.gethostbyname_ex])
def test_a_name_lookup_is_blocked(lookup):
    before = len(network_guard.ATTEMPTS)
    args = ("data.sec.gov", 443) if lookup is socket.getaddrinfo else ("data.sec.gov",)
    with pytest.raises(network_guard.NetworkBlocked):
        lookup(*args)
    forget_attempts_since(before)


def test_a_udp_message_out_is_blocked():
    before = len(network_guard.ATTEMPTS)
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
        with pytest.raises(network_guard.NetworkBlocked):
            sock.sendto(b"x", ("93.184.215.14", 53))
    forget_attempts_since(before)


def test_a_swallowed_network_error_is_still_recorded():
    # Code that catches every exception (e.g. "source unreachable → missing", SPEC E4) must not hide that it
    # tried the network: every attempt is recorded, and conftest fails the test afterwards.
    before = len(network_guard.ATTEMPTS)
    try:
        socket.getaddrinfo("data.sec.gov", 443)
    except Exception:
        pass
    assert network_guard.ATTEMPTS[before:] == ["data.sec.gov"]
    forget_attempts_since(before)


def test_connections_to_this_computer_still_work():
    # Python's own machinery (e.g. asyncio on Windows) talks to 127.0.0.1; that must keep working.
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server:
        server.bind(("127.0.0.1", 0))
        server.listen(1)
        with socket.create_connection(server.getsockname(), timeout=2):
            pass
