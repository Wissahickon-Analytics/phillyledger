import sys
from collections.abc import Generator

import pytest
import pytest_socket

REFUSED_AUDIT_EVENTS = frozenset(
    {
        "socket.__new__",
        "socket.getaddrinfo",
        "socket.gethostbyname",
        "socket.gethostbyaddr",
        "socket.getnameinfo",
    }
)
_marked_test_running = False


def _refuse_sockets(event: str, _args: tuple[object, ...]) -> None:
    if event in REFUSED_AUDIT_EVENTS and not _marked_test_running:
        raise pytest_socket.SocketBlockedError(f"A test tried to use {event}.")


def pytest_configure() -> None:
    # pytest-socket first blocks after test modules import. This call covers names bound by
    # "from socket import socket" at import.
    pytest_socket.disable_socket()
    # pytest-socket swaps module names such as socket.socket, only from each test's setup to its
    # teardown. CPython raises these audit events inside the socket constructor and the resolver
    # functions, so no name or fixture phase skips them.
    sys.addaudithook(_refuse_sockets)


@pytest.hookimpl(wrapper=True)
def pytest_runtest_protocol(item: pytest.Item) -> Generator[None, object, object]:
    global _marked_test_running
    _marked_test_running = item.get_closest_marker("enable_socket") is not None
    try:
        return (yield)
    finally:
        _marked_test_running = False
