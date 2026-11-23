import socket
from pathlib import Path
from socket import socket as early_bound_socket

import pytest
import pytest_socket


@pytest.fixture(scope="module")
def module_setup_listing() -> list[Path]:
    return list(Path.cwd().iterdir())


def test_working_directory_is_empty(module_setup_listing: list[Path]) -> None:
    assert list(Path.cwd().iterdir()) == []
    assert module_setup_listing == []


def test_sockets_are_blocked() -> None:
    with pytest.raises(pytest_socket.SocketBlockedError):
        socket.socket()
    with pytest.raises(pytest_socket.SocketBlockedError):
        socket.SocketType()


def test_early_bound_socket_is_blocked() -> None:
    with pytest.raises(pytest_socket.SocketBlockedError):
        early_bound_socket()
