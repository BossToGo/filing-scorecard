"""Tests never use the network (SPEC rule 14.10). The guard lives in `app/tests/conftest.py`. Owner: A."""

import socket

import pytest


def test_an_outside_connection_is_blocked():
    with pytest.raises(RuntimeError, match="network"):
        socket.create_connection(("93.184.215.14", 443), timeout=1)


def test_a_raw_socket_connection_is_blocked():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        with pytest.raises(RuntimeError, match="network"):
            sock.connect(("93.184.215.14", 443))


def test_a_name_lookup_is_blocked():
    with pytest.raises(RuntimeError, match="network"):
        socket.getaddrinfo("data.sec.gov", 443)


def test_connections_to_this_computer_still_work():
    # Python's own machinery (e.g. asyncio on Windows) talks to 127.0.0.1; that must keep working.
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server:
        server.bind(("127.0.0.1", 0))
        server.listen(1)
        with socket.create_connection(server.getsockname(), timeout=2):
            pass
