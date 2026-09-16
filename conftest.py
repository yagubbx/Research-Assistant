"""Disable real networking for every test, including course smoke tests."""

import socket

import pytest


@pytest.fixture(autouse=True)
def deny_network(monkeypatch):
    """Mock transports must intercept all external requests before sockets."""
    connect = socket.socket.connect
    connect_ex = socket.socket.connect_ex

    def guard(original):
        def denied(sock, address):
            # Windows asyncio creates its wakeup socketpair over loopback.
            if isinstance(address, tuple) and address[0] in {"127.0.0.1", "::1"}:
                return original(sock, address)
            if sock.family == getattr(socket, "AF_UNIX", None):
                return original(sock, address)
            raise AssertionError("Tests must not access external networks")
        return denied

    monkeypatch.setattr(socket.socket, "connect", guard(connect))
    monkeypatch.setattr(socket.socket, "connect_ex", guard(connect_ex))
