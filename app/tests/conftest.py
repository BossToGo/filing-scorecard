"""Shared test setup. Owner: A.

Tests never use the network (SPEC rule 14.10): every test runs with outside connections and name lookups
blocked, so a test that tries to download something fails at once with a clear message. Use the saved files in
`app/evidence/` or `app/tests/fixtures/` instead. Connections to this computer (127.0.0.1) still work, because
Python's own machinery needs them.
"""

import socket

import pytest

_LOCAL_HOSTS = {"127.0.0.1", "::1", "localhost", None}
_MESSAGE = (
    "Tests must not use the network (SPEC rule 14.10). Tried to reach {!r}. "
    "Use saved files from app/evidence/ or app/tests/fixtures/ instead."
)


def _host(address):
    return address[0] if isinstance(address, tuple) else address


@pytest.fixture(autouse=True)
def _no_network(monkeypatch):
    real_connect = socket.socket.connect
    real_connect_ex = socket.socket.connect_ex
    real_getaddrinfo = socket.getaddrinfo
    unix = getattr(socket, "AF_UNIX", None)

    def allowed(sock, address):
        return (unix is not None and sock.family == unix) or _host(address) in _LOCAL_HOSTS

    def connect(sock, address):
        if not allowed(sock, address):
            raise RuntimeError(_MESSAGE.format(_host(address)))
        return real_connect(sock, address)

    def connect_ex(sock, address):
        if not allowed(sock, address):
            raise RuntimeError(_MESSAGE.format(_host(address)))
        return real_connect_ex(sock, address)

    def getaddrinfo(host, *args, **kwargs):
        if host not in _LOCAL_HOSTS:
            raise RuntimeError(_MESSAGE.format(host))
        return real_getaddrinfo(host, *args, **kwargs)

    monkeypatch.setattr(socket.socket, "connect", connect)
    monkeypatch.setattr(socket.socket, "connect_ex", connect_ex)
    monkeypatch.setattr(socket, "getaddrinfo", getaddrinfo)
