import shutil
import sys
import tempfile
from collections.abc import Generator
from pathlib import Path

import pytest
import pytest_socket
from hypothesis import settings
from hypothesis.configuration import set_hypothesis_home_dir

REFUSED_AUDIT_EVENTS = frozenset(
    {
        "socket.__new__",
        "socket.getaddrinfo",
        "socket.gethostbyname",
        "socket.gethostbyaddr",
        "socket.getnameinfo",
    }
)
HYPOTHESIS_HOME = pytest.StashKey[Path]()
_marked_test_running = False

settings.register_profile("phillyledger", database=None, derandomize=True, deadline=None)
settings.load_profile("phillyledger")


def _refuse_sockets(event: str, _args: tuple[object, ...]) -> None:
    if event in REFUSED_AUDIT_EVENTS and not _marked_test_running:
        raise pytest_socket.SocketBlockedError(f"A test tried to use {event}.")


def pytest_configure(config: pytest.Config) -> None:
    # pytest-socket first blocks after test modules import. This call covers names bound by
    # "from socket import socket" at import.
    pytest_socket.disable_socket()
    # pytest-socket swaps module names such as socket.socket, only from each test's setup to its
    # teardown. CPython raises these audit events inside the socket constructor and the resolver
    # functions, so no name or fixture phase skips them.
    sys.addaudithook(_refuse_sockets)
    # Hypothesis writes .hypothesis/constants under the working directory it was imported in,
    # from collection on, even with database=None.
    home = Path(tempfile.mkdtemp(prefix="hypothesis-"))
    config.stash[HYPOTHESIS_HOME] = home
    set_hypothesis_home_dir(home)


def pytest_unconfigure(config: pytest.Config) -> None:
    home = config.stash.get(HYPOTHESIS_HOME, None)
    if home is not None:
        shutil.rmtree(home, ignore_errors=True)


@pytest.hookimpl(wrapper=True)
def pytest_runtest_protocol(item: pytest.Item) -> Generator[None, object, object]:
    global _marked_test_running
    _marked_test_running = item.get_closest_marker("enable_socket") is not None
    try:
        return (yield)
    finally:
        _marked_test_running = False
