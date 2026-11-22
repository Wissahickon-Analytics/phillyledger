import socket
from pathlib import Path
from socket import socket as early_bound_socket

import pytest
import pytest_socket


def test_working_directory_is_empty() -> None:
    assert list(Path.cwd().iterdir()) == []


def test_sockets_are_blocked() -> None:
    with pytest.raises(pytest_socket.SocketBlockedError):
        socket.socket()


def test_early_bound_socket_is_blocked() -> None:
    with pytest.raises(pytest_socket.SocketBlockedError):
        early_bound_socket()
