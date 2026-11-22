import pytest_socket


def pytest_configure() -> None:
    # pytest-socket blocks only from each test's setup, after test modules import, and lifts the
    # block at teardown. This call covers names bound by "from socket import socket" at import.
    pytest_socket.disable_socket()
