"""Tests for pyobs.utils.shutdown: the stop file for pyobsd's PID-file mode and the systemd notification."""

from __future__ import annotations

import socket
import subprocess
import sys
import time
from collections.abc import Iterator
from pathlib import Path

import pytest

from pyobs.utils import shutdown


@pytest.fixture(autouse=True)
def no_stop_file(monkeypatch: pytest.MonkeyPatch) -> Iterator[None]:
    monkeypatch.delenv("NOTIFY_SOCKET", raising=False)
    shutdown.set_stop_file(None)
    shutdown.clear_stop_file()
    yield
    shutdown.set_stop_file(None)
    shutdown.clear_stop_file()


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
        before = time.time()
        shutdown.extend_stop_timeout(90.5)
        extend, status = sock.recv(1024).decode().split("\n")
        assert extend == "EXTEND_TIMEOUT_USEC=90500000"
        # the deadline in the status text, for "pyobsd status"
        assert status.startswith("STATUS=stopping, deadline ")
        deadline = shutdown.parse_status_deadline(status.removeprefix("STATUS="))
        # sent with 3 decimals
        assert deadline is not None and before + 90.5 - 0.001 <= deadline <= time.time() + 90.5 + 0.001


@pytest.mark.parametrize("text", ["", "stopping", "stopping, deadline x", "running"])
def test_parse_status_deadline_invalid(text: str) -> None:
    assert shutdown.parse_status_deadline(text) is None


def test_parse_status_deadline() -> None:
    assert shutdown.parse_status_deadline("stopping, deadline 1764150000.500") == 1764150000.5


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


# ── in-memory deadline ───────────────────────────────────────────────────────


def test_current_deadline_without_stop_file() -> None:
    """The deadline is also kept without a stop file, for the watchdog (e.g. a module run in the foreground)."""
    shutdown.clear_stop_file()
    assert shutdown.current_deadline() is None

    before = time.time()
    shutdown.extend_stop_timeout(60.0)
    deadline = shutdown.current_deadline()
    assert deadline is not None and before + 60.0 <= deadline <= time.time() + 60.0

    shutdown.mark_stopping()  # does not shorten it
    assert shutdown.current_deadline() == deadline

    shutdown.clear_stop_file()
    assert shutdown.current_deadline() is None


# ── watchdog, in a child process, since it ends the process ──────────────────

_WATCHDOG = """
import sys, time
from pyobs.utils import shutdown
stop_timeout, extend, run_for = float(sys.argv[1]), float(sys.argv[2]), float(sys.argv[3])
shutdown.start_watchdog(stop_timeout, grace=0.1, interval=0.05)
shutdown.start_watchdog(1000.0)  # second call does nothing
if extend > 0:
    shutdown.extend_stop_timeout(extend)
time.sleep(run_for)
"""


def run_watchdog(stop_timeout: float, extend: float, run_for: float) -> tuple[int, float]:
    start = time.monotonic()
    proc = subprocess.run(
        [sys.executable, "-c", _WATCHDOG, str(stop_timeout), str(extend), str(run_for)], timeout=30, check=False
    )
    return proc.returncode, time.monotonic() - start


def test_watchdog_ends_hanging_shutdown() -> None:
    code, elapsed = run_watchdog(stop_timeout=0.3, extend=0.0, run_for=20.0)
    assert code == 1
    assert elapsed < 10.0


def test_watchdog_respects_extension() -> None:
    """A deadline asked for with extend_stop_timeout() counts, like for pyobsd."""
    code_short, _ = run_watchdog(stop_timeout=0.2, extend=1.5, run_for=1.0)
    assert code_short == 0  # finished within the extension, so not ended after 0.2 s

    code_long, _ = run_watchdog(stop_timeout=0.2, extend=0.5, run_for=20.0)
    assert code_long == 1


def test_watchdog_lets_finished_shutdown_exit() -> None:
    code, _ = run_watchdog(stop_timeout=5.0, extend=0.0, run_for=0.1)
    assert code == 0
