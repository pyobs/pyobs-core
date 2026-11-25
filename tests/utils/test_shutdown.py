"""Tests for pyobs.utils.shutdown: the stop file for pyobsd's PID-file mode and the systemd notification."""

from __future__ import annotations

import socket
import time
from collections.abc import Iterator
from pathlib import Path

import pytest

from pyobs.utils import shutdown


@pytest.fixture(autouse=True)
def no_stop_file(monkeypatch: pytest.MonkeyPatch) -> Iterator[None]:
    monkeypatch.delenv("NOTIFY_SOCKET", raising=False)
    shutdown.set_stop_file(None)
    yield
    shutdown.set_stop_file(None)


def test_stop_file_for() -> None:
    assert shutdown.stop_file_for("/opt/pyobs/run/camera.pid") == "/opt/pyobs/run/camera.pid.stopping"


def test_extend_without_anything_is_a_noop(tmp_path: Path) -> None:
    shutdown.extend_stop_timeout(60.0)
    assert list(tmp_path.iterdir()) == []


def test_extend_writes_deadline(tmp_path: Path) -> None:
    stop_file = tmp_path / "camera.pid.stopping"
    shutdown.set_stop_file(str(stop_file))

    before = time.time()
    shutdown.extend_stop_timeout(600.0)
    after = time.time()

    deadline = shutdown.read_stop_deadline(str(stop_file))
    assert deadline is not None
    # written with millisecond precision
    assert before + 600.0 - 0.001 <= deadline <= after + 600.0 + 0.001
    assert [p.name for p in tmp_path.iterdir()] == ["camera.pid.stopping"]  # no temp file left behind


def test_extend_twice_keeps_latest(tmp_path: Path) -> None:
    stop_file = tmp_path / "camera.pid.stopping"
    shutdown.set_stop_file(str(stop_file))
    shutdown.extend_stop_timeout(600.0)
    shutdown.extend_stop_timeout(10.0)
    deadline = shutdown.read_stop_deadline(str(stop_file))
    assert deadline is not None and deadline < time.time() + 11.0


def test_extend_into_missing_directory_does_not_raise(tmp_path: Path) -> None:
    shutdown.set_stop_file(str(tmp_path / "missing" / "camera.pid.stopping"))
    shutdown.extend_stop_timeout(60.0)


def test_clear_stop_file(tmp_path: Path) -> None:
    stop_file = tmp_path / "camera.pid.stopping"
    shutdown.set_stop_file(str(stop_file))
    shutdown.clear_stop_file()  # nothing there yet, must not raise
    shutdown.extend_stop_timeout(60.0)
    shutdown.clear_stop_file()
    assert not stop_file.exists()


def test_mark_stopping_writes_now(tmp_path: Path) -> None:
    stop_file = tmp_path / "camera.pid.stopping"
    shutdown.set_stop_file(str(stop_file))

    before = time.time()
    shutdown.mark_stopping()

    deadline = shutdown.read_stop_deadline(str(stop_file))
    assert deadline is not None
    assert before - 0.001 <= deadline <= time.time() + 0.001


def test_mark_stopping_keeps_later_deadline(tmp_path: Path) -> None:
    stop_file = tmp_path / "camera.pid.stopping"
    shutdown.set_stop_file(str(stop_file))
    shutdown.extend_stop_timeout(600.0)

    shutdown.mark_stopping()

    deadline = shutdown.read_stop_deadline(str(stop_file))
    assert deadline is not None and deadline > time.time() + 590


def test_mark_stopping_notifies_systemd(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    address = str(tmp_path / "notify")
    with _receiver(address) as sock:
        monkeypatch.setenv("NOTIFY_SOCKET", address)
        shutdown.mark_stopping()
        assert sock.recv(1024) == b"STOPPING=1"


@pytest.mark.parametrize("content", ["", "soon", "12:30"])
def test_read_stop_deadline_invalid(tmp_path: Path, content: str) -> None:
    stop_file = tmp_path / "camera.pid.stopping"
    stop_file.write_text(content)
    assert shutdown.read_stop_deadline(str(stop_file)) is None


def test_read_stop_deadline_missing(tmp_path: Path) -> None:
    assert shutdown.read_stop_deadline(str(tmp_path / "nope")) is None


def _receiver(address: str) -> socket.socket:
    sock = socket.socket(socket.AF_UNIX, socket.SOCK_DGRAM)
    sock.bind(address)
    sock.settimeout(2.0)
    return sock


def test_notify_path_socket(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    address = str(tmp_path / "notify")
    with _receiver(address) as sock:
        monkeypatch.setenv("NOTIFY_SOCKET", address)
        shutdown.extend_stop_timeout(90.5)
        assert sock.recv(1024) == b"EXTEND_TIMEOUT_USEC=90500000"


def test_notify_abstract_socket(monkeypatch: pytest.MonkeyPatch) -> None:
    name = f"pyobs-test-{time.monotonic_ns()}"
    with _receiver("\0" + name) as sock:
        monkeypatch.setenv("NOTIFY_SOCKET", "@" + name)
        assert shutdown.notify("READY=1") is True
        assert sock.recv(1024) == b"READY=1"


def test_notify_without_socket(monkeypatch: pytest.MonkeyPatch) -> None:
    assert shutdown.notify("READY=1") is False


@pytest.mark.parametrize("address", ["relative/path", "vsock:2:1234"])
def test_notify_unsupported_address(monkeypatch: pytest.MonkeyPatch, address: str) -> None:
    monkeypatch.setenv("NOTIFY_SOCKET", address)
    assert shutdown.notify("READY=1") is False


def test_notify_unreachable_socket_does_not_raise(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("NOTIFY_SOCKET", str(tmp_path / "nobody-listens"))
    assert shutdown.notify("READY=1") is False
