"""Blocks the network for the whole test session (SPEC rule 14.10). Owner: A.

`app/tests/conftest.py` installs it before any test file is imported and removes it at the end. Outside
connections, name lookups and UDP messages raise `NetworkBlocked`, and every attempt is recorded in `ATTEMPTS`,
so a test whose code catches the error (e.g. "source unreachable → missing") still fails afterwards.
Connections to this computer (127.0.0.1) keep working, because Python's own machinery needs them.
"""

import socket

LOCAL_HOSTS = {"127.0.0.1", "::1", "localhost", None, "", b"127.0.0.1", b"localhost"}
ATTEMPTS: list = []
_REAL: dict = {}


class NetworkBlocked(RuntimeError):
    """Raised when code under test tries to reach the network."""


def _host(address):
    return address[0] if isinstance(address, tuple) else address


def _block(host):
    ATTEMPTS.append(host)
    raise NetworkBlocked(
        f"Tests must not use the network (SPEC rule 14.10). Tried to reach {host!r}. "
        "Use saved files from app/evidence/ or app/tests/fixtures/ instead."
    )


def _is_local(sock, address):
    unix = getattr(socket, "AF_UNIX", None)
    return (unix is not None and sock.family == unix) or _host(address) in LOCAL_HOSTS


def _connect(sock, address):
    if not _is_local(sock, address):
        _block(_host(address))
    return _REAL["connect"](sock, address)


def _connect_ex(sock, address):
    if not _is_local(sock, address):
        _block(_host(address))
    return _REAL["connect_ex"](sock, address)


def _sendto(sock, data, *args):
    address = args[-1]
    if not _is_local(sock, address):
        _block(_host(address))
    return _REAL["sendto"](sock, data, *args)


def _lookup(name):
    def guarded(host, *args, **kwargs):
        if host not in LOCAL_HOSTS:
            _block(host)
        return _REAL[name](host, *args, **kwargs)

    return guarded


def install():
    if _REAL:
        return
    _REAL.update(
        connect=socket.socket.connect,
        connect_ex=socket.socket.connect_ex,
        sendto=socket.socket.sendto,
        getaddrinfo=socket.getaddrinfo,
        gethostbyname=socket.gethostbyname,
        gethostbyname_ex=socket.gethostbyname_ex,
    )
    socket.socket.connect = _connect
    socket.socket.connect_ex = _connect_ex
    socket.socket.sendto = _sendto
    for name in ("getaddrinfo", "gethostbyname", "gethostbyname_ex"):
        setattr(socket, name, _lookup(name))


def uninstall():
    if not _REAL:
        return
    socket.socket.connect = _REAL["connect"]
    socket.socket.connect_ex = _REAL["connect_ex"]
    socket.socket.sendto = _REAL["sendto"]
    for name in ("getaddrinfo", "gethostbyname", "gethostbyname_ex"):
        setattr(socket, name, _REAL[name])
    _REAL.clear()


def is_installed() -> bool:
    return bool(_REAL)
