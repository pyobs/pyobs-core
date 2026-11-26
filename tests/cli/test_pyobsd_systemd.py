"""Tests for pyobsd's systemd mode (pyobs/cli/_systemd_daemon.py), with systemctl faked."""

from __future__ import annotations

import json
import os
import subprocess
from pathlib import Path
from typing import Any

import pytest

from pyobs.cli import _systemd_daemon
from pyobs.cli._systemd_daemon import SystemdDaemon


class FakeSystemctl:
    """Units with properties; records every call and changes states like systemd would."""

    def __init__(self) -> None:
        self.units: dict[str, dict[str, str]] = {}
        self.calls: list[list[str]] = []
        self.fail_start: set[str] = set()
        self.next_pid = 1000

    def unit(self, name: str, state: str = "inactive", pid: int = 0, **props: str) -> None:
        self.units[f"pyobs@{name}.service"] = {"ActiveState": state, "MainPID": str(pid), **props}

    def __call__(self, cmd: list[str], capture_output: bool = False, text: bool = False) -> Any:
        assert cmd[0] == "systemctl"
        args = cmd[1:]
        self.calls.append(args)
        verb = args[0]
        units = args[args.index("--") + 1 :] if "--" in args else []
        out, rc = "", 0
        if verb == "show":
            blocks = []
            for u in units:
                p = {"Id": u, "ActiveState": "inactive", "SubState": "dead", "MainPID": "0", "NRestarts": "0"}
                p.update(self.units.get(u, {}))
                blocks.append("\n".join(f"{k}={v}" for k, v in p.items()))
            out = "\n\n".join(blocks) + "\n"
        elif verb == "list-units":
            out = "".join(
                f"{u} loaded {p['ActiveState']} running pyobs module\n"
                for u, p in sorted(self.units.items())
                if p["ActiveState"] in ("active", "activating", "deactivating")
            )
        elif verb in ("start", "restart"):
            for u in units:
                if u in self.fail_start:
                    self.units[u] = {"ActiveState": "failed", "MainPID": "0"}
                    rc = 1
                else:
                    self.next_pid += 1
                    self.units[u] = {"ActiveState": "active", "MainPID": str(self.next_pid)}
        elif verb == "stop":
            for u in units:
                self.units[u] = {"ActiveState": "inactive", "MainPID": "0"}
        elif verb == "kill":
            pass
        return subprocess.CompletedProcess(cmd, rc, stdout=out, stderr="")

    def verbs(self) -> list[list[str]]:
        """Calls that change something."""
        return [c for c in self.calls if c[0] not in ("show", "list-units")]


@pytest.fixture
def systemctl(monkeypatch) -> FakeSystemctl:
    fake = FakeSystemctl()
    monkeypatch.setattr(_systemd_daemon.subprocess, "run", fake)
    monkeypatch.setattr(_systemd_daemon.time, "sleep", lambda s: None)
    return fake


def make_daemon(tmp_path: Path, configs: list[str]) -> SystemdDaemon:
    config = tmp_path / "config"
    config.mkdir()
    for c in configs:
        (config / c).write_text("{}\n")
    (tmp_path / "run").mkdir()
    daemon = SystemdDaemon(str(config), str(tmp_path / "run"), str(tmp_path / "log"))
    daemon._pyobs_exec = "pyobs"
    return daemon


# ── start ────────────────────────────────────────────────────────────────────


def test_start_all_enabled_in_one_call(systemctl, tmp_path) -> None:
    daemon = make_daemon(tmp_path, ["camera.yaml", "telescope.yaml", "_dome.yaml", "comm.shared.yaml"])
    daemon.start()
    assert systemctl.verbs() == [["start", "--", "pyobs@camera.service", "pyobs@telescope.service"]]


def test_start_disabled_module_by_name(systemctl, tmp_path) -> None:
    daemon = make_daemon(tmp_path, ["_dome.yaml"])
    for name in ("dome", "_dome"):
        systemctl.units.clear()
        systemctl.calls.clear()
        daemon.start([name])
        # the unit is named after the active name
        assert systemctl.verbs() == [["start", "--", "pyobs@dome.service"]]


def test_start_skips_running(systemctl, tmp_path, capsys) -> None:
    daemon = make_daemon(tmp_path, ["camera.yaml", "telescope.yaml"])
    systemctl.unit("camera", "active", 123)
    daemon.start()
    assert "camera already running." in capsys.readouterr().out
    assert systemctl.verbs() == [["start", "--", "pyobs@telescope.service"]]


def test_start_resets_failed(systemctl, tmp_path) -> None:
    """A failed unit gets reset-failed first, otherwise systemd refuses the start after hitting the start limit."""
    daemon = make_daemon(tmp_path, ["camera.yaml", "telescope.yaml", "dome.yaml"])
    systemctl.unit("camera", "failed", Result="start-limit-hit")
    systemctl.unit("telescope", "active", 123)
    daemon.start()
    assert systemctl.verbs() == [
        ["reset-failed", "--", "pyobs@camera.service"],
        ["start", "--", "pyobs@camera.service", "pyobs@dome.service"],
    ]


def test_start_unknown_module(systemctl, tmp_path, capsys) -> None:
    daemon = make_daemon(tmp_path, ["camera.yaml"])
    with pytest.raises(SystemExit) as exc:
        daemon.start(["dome"])
    assert exc.value.code == 1
    assert "'dome' does not exist" in capsys.readouterr().out
    assert systemctl.verbs() == []


def test_start_invalid_name(systemctl, tmp_path, capsys) -> None:
    daemon = make_daemon(tmp_path, ["bad name.yaml", "camera.yaml"])
    with pytest.raises(SystemExit):
        daemon.start(["bad name"])
    assert "can't be a unit name" in capsys.readouterr().out

    # without names, it's skipped with a warning
    daemon.start()
    assert "Skipping 'bad name'" in capsys.readouterr().err
    assert systemctl.verbs() == [["start", "--", "pyobs@camera.service"]]


def test_start_failure(systemctl, tmp_path, capsys) -> None:
    daemon = make_daemon(tmp_path, ["camera.yaml", "telescope.yaml"])
    systemctl.fail_start.add("pyobs@camera.service")
    with pytest.raises(SystemExit) as exc:
        daemon.start()
    assert exc.value.code == 1
    assert "Could not start camera, see: pyobsd logs" in capsys.readouterr().out


def test_start_refuses_module_running_in_pid_mode(systemctl, tmp_path, capsys) -> None:
    daemon = make_daemon(tmp_path, ["camera.yaml"])
    (tmp_path / "run" / "camera.pid").write_text(f"{os.getpid()}\n")
    with pytest.raises(SystemExit):
        daemon.start()
    assert "Still running in PID-file mode: camera" in capsys.readouterr().out
    assert systemctl.verbs() == []


# ── stop, kill, restart ──────────────────────────────────────────────────────


def test_stop_all_active(systemctl, tmp_path) -> None:
    daemon = make_daemon(tmp_path, ["camera.yaml", "telescope.yaml"])
    systemctl.unit("camera", "active", 123)
    # running, but its config was removed since
    systemctl.unit("old", "active", 124)
    daemon.stop()
    assert systemctl.verbs() == [["stop", "--", "pyobs@camera.service", "pyobs@old.service"]]


def test_stop_no_wait(systemctl, tmp_path) -> None:
    daemon = make_daemon(tmp_path, ["camera.yaml"])
    daemon.stop(["camera"], wait=False)
    assert systemctl.verbs() == [["stop", "--no-block", "--", "pyobs@camera.service"]]


def test_stop_nothing_running(systemctl, tmp_path) -> None:
    daemon = make_daemon(tmp_path, ["camera.yaml"])
    daemon.stop()
    assert systemctl.verbs() == []


def test_kill_then_stop(systemctl, tmp_path) -> None:
    """A stop after SIGKILL, so that Restart=on-failure doesn't start it again."""
    daemon = make_daemon(tmp_path, ["camera.yaml", "telescope.yaml"])
    systemctl.unit("camera", "deactivating", 123)
    daemon.kill(["camera", "telescope"])
    assert systemctl.verbs() == [
        ["kill", "-s", "SIGKILL", "--", "pyobs@camera.service"],
        ["stop", "--no-block", "--", "pyobs@camera.service"],
        # SIGKILL leaves it "failed", but it was stopped on purpose
        ["reset-failed", "--", "pyobs@camera.service"],
    ]


def test_kill_stuck(systemctl, tmp_path, monkeypatch, capsys) -> None:
    daemon = make_daemon(tmp_path, ["camera.yaml"])
    systemctl.unit("camera", "deactivating", 123)
    real = systemctl.__call__

    # the process doesn't go away
    def stuck(cmd: list[str], **kwargs: Any) -> Any:
        result = real(cmd, **kwargs)
        systemctl.unit("camera", "deactivating", 123)
        return result

    monkeypatch.setattr(_systemd_daemon.subprocess, "run", stuck)
    times = iter(range(0, 100))
    monkeypatch.setattr(_systemd_daemon.time, "time", lambda: float(next(times)))
    with pytest.raises(SystemExit):
        daemon.kill(["camera"])
    assert "camera (PID 123) is still alive after SIGKILL" in capsys.readouterr().out


def test_restart_by_name(systemctl, tmp_path) -> None:
    daemon = make_daemon(tmp_path, ["camera.yaml"])
    daemon.restart(["camera"])
    assert systemctl.verbs() == [["restart", "--", "pyobs@camera.service"]]


def test_restart_all_is_stop_then_start(systemctl, tmp_path) -> None:
    """Like the PID-file mode: all running ones stop, all enabled ones start."""
    daemon = make_daemon(tmp_path, ["camera.yaml", "_dome.yaml"])
    systemctl.unit("dome", "active", 123)
    daemon.restart()
    assert systemctl.verbs() == [["stop", "--", "pyobs@dome.service"], ["start", "--", "pyobs@camera.service"]]


def test_restart_kill(systemctl, tmp_path) -> None:
    daemon = make_daemon(tmp_path, ["camera.yaml"])
    systemctl.unit("camera", "active", 123)
    daemon.restart(["camera"], kill=True)
    assert [c[0] for c in systemctl.verbs()] == ["kill", "stop", "reset-failed", "start"]


# ── status ───────────────────────────────────────────────────────────────────


def test_status_json(systemctl, tmp_path, capsys) -> None:
    daemon = make_daemon(tmp_path, ["camera.yaml", "telescope.yaml", "_dome.yaml", "focus.yaml", "roof.yaml"])
    pid = os.getpid()
    systemctl.unit("camera", "active", pid, NRestarts="2")
    systemctl.unit("telescope", "failed")
    systemctl.unit("dome", "deactivating", pid, StatusText="stopping, deadline 1764150000.500")
    systemctl.unit("focus", "activating", pid)

    daemon.status(print_json=True)
    result = json.loads(capsys.readouterr().out)

    assert sorted(result) == ["_dome", "camera", "focus", "roof", "telescope"]
    cam = result["camera"]
    assert (cam["mode"], cam["enabled"], cam["running"], cam["state"], cam["pid"], cam["restarts"]) == (
        "systemd",
        True,
        True,
        "running",
        pid,
        2,
    )
    assert cam["stop_deadline"] is None
    assert cam["uptime"] > 0 and cam["rss_mb"] > 0 and cam["cpu"] is None
    assert result["telescope"] == {
        "mode": "systemd",
        "enabled": True,
        "running": False,
        "state": "failed",
        "stop_deadline": None,
        "restarts": 0,
    }
    assert result["_dome"]["enabled"] is False
    assert result["_dome"]["state"] == "stopping"
    assert result["_dome"]["stop_deadline"] == 1764150000.5
    assert result["focus"]["state"] == "starting"
    assert result["roof"]["state"] == "stopped"


def test_status_waiting_for_restart_is_failed(systemctl, tmp_path, capsys) -> None:
    daemon = make_daemon(tmp_path, ["camera.yaml"])
    systemctl.unit("camera", "activating", SubState="auto-restart", NRestarts="3")
    daemon.status(print_json=True)
    entry = json.loads(capsys.readouterr().out)["camera"]
    assert (entry["state"], entry["running"], entry["restarting"], entry["restarts"]) == ("failed", False, True, 3)
    daemon.status()
    assert "failed (restarting)  (3 restarts)" in capsys.readouterr().out


def test_status_one_show_call(systemctl, tmp_path) -> None:
    daemon = make_daemon(tmp_path, ["a.yaml", "b.yaml", "c.yaml"])
    daemon.status(print_json=True)
    assert [c[0] for c in systemctl.calls].count("show") == 1


def test_status_unit_without_config(systemctl, tmp_path, capsys) -> None:
    daemon = make_daemon(tmp_path, ["camera.yaml"])
    systemctl.unit("old", "active", os.getpid())
    daemon.status(print_json=True)
    result = json.loads(capsys.readouterr().out)
    assert result["old"]["state"] == "running"
    assert result["old"]["enabled"] is False


def test_status_pid_mode_leftover(systemctl, tmp_path, capsys) -> None:
    daemon = make_daemon(tmp_path, ["camera.yaml"])
    (tmp_path / "run" / "camera.pid").write_text(f"{os.getpid()}\n")

    daemon.status(print_json=True)
    out = capsys.readouterr()
    result = json.loads(out.out)
    assert result["camera"]["mode"] == "pid"
    assert result["camera"]["running"] is True
    assert result["camera"]["pid"] == os.getpid()
    assert "still running in PID-file mode: camera" in out.err

    daemon.status()
    assert "running (pid mode)" in capsys.readouterr().out


def test_status_text(systemctl, tmp_path, capsys, monkeypatch) -> None:
    daemon = make_daemon(tmp_path, ["camera.yaml", "telescope.yaml", "bad name.yaml"])
    systemctl.unit("camera", "deactivating", os.getpid(), StatusText="stopping, deadline 2000.0", NRestarts="1")
    monkeypatch.setattr(_systemd_daemon.time, "time", lambda: 1000.0)
    daemon.status()
    out = capsys.readouterr().out
    assert "stopping" in out and "(up to 17 min)" in out and "(1 restarts)" in out
    assert "telescope" in out and "stopped" in out
    assert "not a valid unit name" in out


# ── logs ─────────────────────────────────────────────────────────────────────


def test_logs_uses_units(systemctl, tmp_path, monkeypatch) -> None:
    daemon = make_daemon(tmp_path, ["camera.yaml", "_dome.yaml"])
    calls = []
    monkeypatch.setattr(_systemd_daemon.os, "execvp", lambda f, args: calls.append(args))
    daemon.logs(["camera", "-f"])
    daemon.logs(["--", "_dome"])
    daemon.logs(["-n", "10"])
    assert calls == [
        ["journalctl", "-u", "pyobs@camera.service", "-f"],
        ["journalctl", "-u", "pyobs@dome.service"],
        ["journalctl", "-u", "pyobs@*.service", "-n", "10"],
    ]
