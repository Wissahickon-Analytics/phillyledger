import pytest_socket


def pytest_configure() -> None:
    pytest_socket.disable_socket()
