"""Tests for pyobsd's PID-file mode: module selection, PID file handling, status and stop.

They pin down today's behavior before the code moves into a separate backend for the systemd mode (see
specs/plans/2026-11-25-pyobsd-systemd-mode.md). The stop tests use real child processes, since that is
the behavior the planned stop timeout changes."""

from __future__ import annotations

import json
import os
import signal
import subprocess
import sys
import threading
import time
from pathlib import Path
from typing import Any

import pytest

from pyobs.cli import pyobsd
from pyobs.cli.pyobsd import PyobsDaemon


@pytest.fixture
def dirs(tmp_path: Path) -> tuple[Path, Path, Path]:
    config, run, log = tmp_path / "config", tmp_path / "run", tmp_path / "log"
    config.mkdir()
    run.mkdir()
    return config, run, log


def make_daemon(dirs: tuple[Path, Path, Path], configs: tuple[str, ...] | list[str] = (), **kwargs: Any) -> PyobsDaemon:
    config, run, log = dirs
    for name in configs:
        (config / name).write_text("class: pyobs.modules.test.StandAlone\n")
    daemon = PyobsDaemon(str(config), str(run), str(log), **kwargs)
    daemon._pyobs_exec = "pyobs"
    return daemon


def write_pid(dirs: tuple[Path, Path, Path], name: str, pid: int | str) -> Path:
    pid_file = dirs[1] / f"{name}.pid"
    pid_file.write_text(f"{pid}\n")
    return pid_file


def dead_pid() -> int:
    """PID of a process that has already exited and been reaped."""
    proc = subprocess.Popen([sys.executable, "-c", "pass"])
    proc.wait()
    return proc.pid


# ── module selection and names ───────────────────────────────────────────────


def test_list_configs_sorted_and_skips_shared(dirs) -> None:
    daemon = make_daemon(dirs, ["camera.yaml", "_dome.yaml", "acl.shared.yaml", "telescope.yaml", "notes.txt"])
    assert daemon._list_configs() == ["_dome", "camera", "telescope"]


def test_start_without_modules_starts_only_active(dirs, mocker) -> None:
    daemon = make_daemon(dirs, ["camera.yaml", "_dome.yaml", "telescope.yaml"])
    start_service = mocker.patch.object(PyobsDaemon, "_start_service")

    daemon.start()

    assert [c.args[0] for c in start_service.call_args_list] == ["camera", "telescope"]


def test_start_disabled_module_explicitly(dirs, mocker) -> None:
    """A disabled module can still be started by name, e.g. for testing."""
    daemon = make_daemon(dirs, ["_dome.yaml"])
    start_service = mocker.patch.object(PyobsDaemon, "_start_service")

    daemon.start(["_dome"])

    start_service.assert_called_once_with("_dome")


def test_start_unknown_module_exits(dirs, mocker) -> None:
    daemon = make_daemon(dirs, ["camera.yaml"])
    start_service = mocker.patch.object(PyobsDaemon, "_start_service")

    with pytest.raises(SystemExit) as exc:
        daemon.start(["nope"])

    assert exc.value.code == 1
    start_service.assert_not_called()


def test_start_skips_running_module(dirs, mocker, capsys) -> None:
    daemon = make_daemon(dirs, ["camera.yaml"])
    write_pid(dirs, "camera", os.getpid())
    start_service = mocker.patch.object(PyobsDaemon, "_start_service")

    daemon.start(["camera"])

    start_service.assert_not_called()
    assert "camera already running." in capsys.readouterr().out


def test_pid_and_log_file_strip_underscore(dirs) -> None:
    config, run, log = dirs
    daemon = make_daemon(dirs)
    assert daemon._pid_file("_dome") == str(run / "dome.pid")
    assert daemon._log_file("_dome") == str(log / "dome.log")
    assert daemon._config_file("_dome") == str(config / "_dome.yaml")


# ── PID handling ─────────────────────────────────────────────────────────────


def test_running_pid_missing_file(dirs) -> None:
    daemon = make_daemon(dirs)
    assert daemon._running_pid("camera") is None


def test_running_pid_garbage_file(dirs) -> None:
    daemon = make_daemon(dirs)
    write_pid(dirs, "camera", "not-a-pid")
    assert daemon._running_pid("camera") is None


def test_running_pid_live(dirs) -> None:
    daemon = make_daemon(dirs)
    write_pid(dirs, "camera", os.getpid())
    assert daemon._running_pid("camera") == os.getpid()


def test_running_pid_removes_stale_file(dirs) -> None:
    daemon = make_daemon(dirs)
    pid_file = write_pid(dirs, "camera", dead_pid())

    assert daemon._running_pid("camera") is None
    assert not pid_file.exists()


def test_status_json(dirs, capsys) -> None:
    """Running and stopped modules, a disabled module matched to its stripped PID file, and an orphaned PID
    file without a config."""
    daemon = make_daemon(dirs, ["camera.yaml", "telescope.yaml", "_dome.yaml"])
    write_pid(dirs, "camera", os.getpid())
    write_pid(dirs, "dome", os.getpid())
    write_pid(dirs, "orphan", os.getpid())

    daemon.status(print_json=True)
    result = json.loads(capsys.readouterr().out)

    assert sorted(result) == ["_dome", "camera", "orphan", "telescope"]
    assert result["telescope"] == {"running": False}
    for name in ("camera", "_dome", "orphan"):
        assert result[name]["running"] is True
        assert result[name]["pid"] == os.getpid()
        assert result[name]["cpu"] is None  # only measured with --cpu-interval
        assert result[name]["uptime"] > 0
        assert result[name]["rss_mb"] > 0


def test_status_json_drops_stale_pid(dirs, capsys) -> None:
    daemon = make_daemon(dirs, ["camera.yaml"])
    pid_file = write_pid(dirs, "camera", dead_pid())

    daemon.status(print_json=True)

    assert json.loads(capsys.readouterr().out) == {"camera": {"running": False}}
    assert not pid_file.exists()


# ── stop with real processes ─────────────────────────────────────────────────

# Stand-in for a daemonized pyobs module: installs its SIGTERM handler, then writes its PID file, then
# idles. Modes:
#   exit:   exits on SIGTERM.
#   ignore: ignores SIGTERM, like a module that hangs on shutdown.
#   slow:   on SIGTERM writes a deadline <extend> s from now into its stop file (like
#           pyobs.utils.shutdown.extend_stop_timeout), then exits <delay> s later.
_FAKE_MODULE = """
import os, signal, sys, time
pid_file, mode, extend, delay = sys.argv[1], sys.argv[2], float(sys.argv[3]), float(sys.argv[4])
exit_at = None
def on_term(*_):
    global exit_at
    if mode == "slow":
        with open(pid_file + ".stopping", "w") as f:
            f.write(str(time.time() + extend))
        exit_at = time.time() + delay
    else:
        sys.exit(0)
signal.signal(signal.SIGTERM, signal.SIG_IGN if mode == "ignore" else on_term)
with open(pid_file + ".tmp", "w") as f:
    f.write(str(os.getpid()))
os.rename(pid_file + ".tmp", pid_file)
while exit_at is None or time.time() < exit_at:
    time.sleep(0.02)
"""


@pytest.fixture
def fake_module(dirs):
    procs: list[subprocess.Popen[bytes]] = []

    def start(name: str, mode: str = "exit", extend: float = 0.0, delay: float = 0.0) -> subprocess.Popen[bytes]:
        pid_file = dirs[1] / f"{name}.pid"
        proc = subprocess.Popen([sys.executable, "-c", _FAKE_MODULE, str(pid_file), mode, str(extend), str(delay)])
        procs.append(proc)
        # pyobs daemonizes, so pyobsd is never its parent. Here the test is the parent, and a dead but
        # unreaped child would still look alive to os.kill(pid, 0). Reap it as soon as it exits.
        threading.Thread(target=proc.wait, daemon=True).start()
        for _ in range(100):
            if pid_file.exists():
                return proc
            time.sleep(0.05)
        raise RuntimeError("fake module did not write its PID file")

    yield start

    for proc in procs:
        if proc.poll() is None:
            proc.kill()


def wait_dead(proc: subprocess.Popen[bytes], timeout: float = 5.0) -> None:
    deadline = time.monotonic() + timeout
    while proc.poll() is None and time.monotonic() < deadline:
        time.sleep(0.05)


def test_stop_graceful(dirs, fake_module) -> None:
    daemon = make_daemon(dirs, ["camera.yaml"])
    proc = fake_module("camera")

    daemon.stop(["camera"])

    wait_dead(proc)
    assert proc.returncode == 0  # exited through its SIGTERM handler, not killed
    assert not (dirs[1] / "camera.pid").exists()


def test_stop_kills_after_timeout(dirs, fake_module) -> None:
    """A module that ignores SIGTERM and asks for no extra time gets SIGKILL after stop_timeout."""
    daemon = make_daemon(dirs, ["camera.yaml"], stop_timeout=0.3)
    proc = fake_module("camera", mode="ignore")

    start = time.monotonic()
    daemon.stop(["camera"])
    elapsed = time.monotonic() - start

    wait_dead(proc)
    assert proc.returncode == -9  # SIGKILL
    assert 0.3 <= elapsed < 2.0
    assert not (dirs[1] / "camera.pid").exists()


def test_stop_timeout_default(dirs) -> None:
    assert make_daemon(dirs)._stop_timeout == 30.0


def test_stop_waits_for_requested_deadline(dirs, fake_module) -> None:
    """A module that asks for more time (stop file) is not killed when stop_timeout runs out."""
    daemon = make_daemon(dirs, ["camera.yaml"], stop_timeout=0.1)
    proc = fake_module("camera", mode="slow", extend=5.0, delay=0.8)

    daemon.stop(["camera"])

    wait_dead(proc)
    assert proc.returncode == 0  # exited on its own after 0.8 s, not killed after 0.1 s
    assert not (dirs[1] / "camera.pid").exists()
    assert not (dirs[1] / "camera.pid.stopping").exists()


def test_stop_announces_long_wait(dirs, fake_module, capsys) -> None:
    daemon = make_daemon(dirs, ["camera.yaml"], stop_timeout=0.1)
    fake_module("camera", mode="slow", extend=600.0, delay=0.3)

    daemon.stop(["camera"])

    assert "camera is shutting down, waiting up to 10 min." in capsys.readouterr().out


def test_stop_kills_after_requested_deadline(dirs, fake_module) -> None:
    """The requested deadline is a limit too: a module that outlives it gets SIGKILL."""
    daemon = make_daemon(dirs, ["camera.yaml"], stop_timeout=0.1)
    proc = fake_module("camera", mode="slow", extend=0.6, delay=30.0)

    start = time.monotonic()
    daemon.stop(["camera"])
    elapsed = time.monotonic() - start

    wait_dead(proc)
    assert proc.returncode == -9
    assert 0.5 <= elapsed < 3.0
    assert not (dirs[1] / "camera.pid.stopping").exists()


def test_stop_ignores_expired_stop_file(dirs, fake_module) -> None:
    """A stop file from an earlier run with a deadline in the past does not extend anything."""
    daemon = make_daemon(dirs, ["camera.yaml"], stop_timeout=0.2)
    proc = fake_module("camera", mode="ignore")
    (dirs[1] / "camera.pid.stopping").write_text(str(time.time() - 100))

    start = time.monotonic()
    daemon.stop(["camera"])

    wait_dead(proc)
    assert proc.returncode == -9
    assert time.monotonic() - start < 2.0


def test_stop_no_wait(dirs, fake_module) -> None:
    daemon = make_daemon(dirs, ["camera.yaml"], stop_timeout=0.1)
    proc = fake_module("camera", mode="slow", extend=5.0, delay=0.5)

    start = time.monotonic()
    daemon.stop(["camera"], wait=False)

    assert time.monotonic() - start < 0.3
    assert proc.poll() is None  # still shutting down
    wait_dead(proc)
    assert proc.returncode == 0


def test_stop_sends_sigterm_to_all_before_waiting(dirs, fake_module, mocker) -> None:
    """One module with a long shutdown must not delay SIGTERM for the others."""
    daemon = make_daemon(dirs, ["camera.yaml", "telescope.yaml"], stop_timeout=0.1)
    camera = fake_module("camera", mode="slow", extend=5.0, delay=0.5)
    telescope = fake_module("telescope")
    kill = mocker.spy(pyobsd.os, "kill")
    wait = mocker.spy(PyobsDaemon, "_wait_stopped")

    daemon.stop()

    # both got SIGTERM, and there was one wait for both together, not one per module
    sigterms = sorted(c.args[0] for c in kill.call_args_list if c.args[1] == signal.SIGTERM)
    assert sigterms == sorted([camera.pid, telescope.pid])
    assert wait.call_count == 1
    assert wait.call_args.args[1] == {"camera": camera.pid, "telescope": telescope.pid}
    wait_dead(camera)
    wait_dead(telescope)
    assert camera.returncode == 0
    assert telescope.returncode == 0


def test_start_removes_stale_stop_file(dirs, mocker) -> None:
    daemon = make_daemon(dirs, ["camera.yaml"])
    stop_file = dirs[1] / "camera.pid.stopping"
    stop_file.write_text(str(time.time() + 1000))
    mocker.patch("subprocess.Popen")
    mocker.patch.object(PyobsDaemon, "_read_pid", return_value=12345)
    mocker.patch.object(PyobsDaemon, "_is_alive", return_value=True)

    daemon._start_service("camera")

    assert not stop_file.exists()


def test_stop_without_modules_stops_all_running(dirs, fake_module) -> None:
    daemon = make_daemon(dirs, ["camera.yaml", "telescope.yaml", "_dome.yaml"])
    camera = fake_module("camera")
    dome = fake_module("dome")  # disabled, but running (started by name)

    daemon.stop()

    wait_dead(camera)
    wait_dead(dome)
    assert camera.returncode == 0
    assert dome.returncode == 0
    assert list(dirs[1].glob("*.pid")) == []


def test_stop_not_running(dirs, capsys) -> None:
    daemon = make_daemon(dirs, ["camera.yaml"])
    daemon.stop(["camera"])
    assert "camera is not running." in capsys.readouterr().out
