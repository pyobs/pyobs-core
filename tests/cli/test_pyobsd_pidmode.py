"""Tests for pyobsd's PID-file mode: module selection, PID file handling, status and stop.

They pin down today's behavior before the code moves into a separate backend for the systemd mode (see
specs/plans/2026-11-25-pyobsd-systemd-mode.md). The stop tests use real child processes, since that is
the behavior the planned stop timeout changes."""

from __future__ import annotations

import json
import os
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
# idles. With "ignore" it ignores SIGTERM, like a module that takes too long to shut down.
_FAKE_MODULE = """
import os, signal, sys, time
pid_file, mode = sys.argv[1], sys.argv[2]
signal.signal(signal.SIGTERM, signal.SIG_IGN if mode == "ignore" else lambda *_: sys.exit(0))
with open(pid_file + ".tmp", "w") as f:
    f.write(str(os.getpid()))
os.rename(pid_file + ".tmp", pid_file)
while True:
    time.sleep(0.05)
"""


@pytest.fixture
def fake_module(dirs):
    procs: list[subprocess.Popen[bytes]] = []

    def start(name: str, mode: str = "exit") -> subprocess.Popen[bytes]:
        pid_file = dirs[1] / f"{name}.pid"
        proc = subprocess.Popen([sys.executable, "-c", _FAKE_MODULE, str(pid_file), mode])
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


def test_stop_kills_after_timeout(dirs, fake_module, mocker) -> None:
    """A module that ignores SIGTERM gets SIGKILL once the wait runs out (50 x 0.1 s today). time.sleep in
    pyobsd is patched out so the wait runs out at once."""
    daemon = make_daemon(dirs, ["camera.yaml"])
    proc = fake_module("camera", mode="ignore")
    time.sleep(0.2)  # make sure the SIG_IGN handler is in place before SIGTERM arrives
    mocker.patch.object(pyobsd.time, "sleep")

    daemon.stop(["camera"])

    wait_dead(proc)
    assert proc.returncode == -9  # SIGKILL
    assert not (dirs[1] / "camera.pid").exists()


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
