"""Tests for "pyobsd exec <module>", which the systemd unit runs (see specs/plans/2026-11-25-pyobsd-systemd-mode.md)."""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

import pytest

from pyobs.cli import _cli, pyobsd
from pyobs.cli.pyobsd import PidFileDaemon


@pytest.fixture(autouse=True)
def no_host_config(monkeypatch) -> None:
    """Keep the config file and $PYOBSD_MODE of the machine running the tests out of them."""
    monkeypatch.delenv("PYOBSD_MODE", raising=False)
    monkeypatch.setattr(_cli, "find_config_file", lambda: None)


@pytest.fixture
def execv(mocker):
    return mocker.patch.object(pyobsd.os, "execv")


def make_daemon(tmp_path: Path, configs: list[str], **kwargs: Any) -> PidFileDaemon:
    config = tmp_path / "config"
    config.mkdir()
    for name in configs:
        (config / name).write_text("class: pyobs.modules.test.StandAlone\n")
    daemon = PidFileDaemon(str(config), str(tmp_path / "run"), str(tmp_path / "log"), **kwargs)
    daemon._pyobs_exec = "/usr/bin/pyobs"
    return daemon


def test_exec(tmp_path, execv) -> None:
    daemon = make_daemon(tmp_path, ["camera.yaml"])

    daemon.exec_module("camera")

    execv.assert_called_once_with(
        "/usr/bin/pyobs",
        ["/usr/bin/pyobs", "--log-level", "info", "--stop-timeout", "30.0", str(tmp_path / "config" / "camera.yaml")],
    )


def test_exec_options(tmp_path, execv) -> None:
    """Same options as in PID-file mode, but no --pid-file, so pyobs stays in the foreground."""
    daemon = make_daemon(tmp_path, ["camera.yaml"], log_level="debug", syslog=True, file_log=True, stop_timeout=60)

    daemon.exec_module("camera")

    cmd = execv.call_args.args[1]
    assert "--pid-file" not in cmd
    assert cmd[1:] == [
        "--log-level",
        "debug",
        "--stop-timeout",
        "60",
        str(tmp_path / "config" / "camera.yaml"),
        "--log-file",
        str(tmp_path / "log" / "camera.log"),
        "--syslog",
    ]
    assert (tmp_path / "log").is_dir()


@pytest.mark.parametrize("name", ["camera", "_camera"])
def test_exec_disabled(tmp_path, execv, name) -> None:
    """The unit runs with the active name, also for a disabled config (started without enabling it). The log
    file keeps the active name."""
    daemon = make_daemon(tmp_path, ["_camera.yaml"], file_log=True)

    daemon.exec_module(name)

    cmd = execv.call_args.args[1]
    assert str(tmp_path / "config" / "_camera.yaml") in cmd
    assert str(tmp_path / "log" / "camera.log") in cmd


def test_exec_prefers_enabled(tmp_path, execv) -> None:
    daemon = make_daemon(tmp_path, ["camera.yaml", "_camera.yaml"])

    daemon.exec_module("camera")

    assert str(tmp_path / "config" / "camera.yaml") in execv.call_args.args[1]


def test_exec_ignores_shared(tmp_path, execv) -> None:
    daemon = make_daemon(tmp_path, ["camera.shared.yaml"])

    with pytest.raises(SystemExit):
        daemon.exec_module("camera.shared")
    execv.assert_not_called()


def test_exec_unknown(tmp_path, execv, capsys) -> None:
    daemon = make_daemon(tmp_path, ["camera.yaml"])

    with pytest.raises(SystemExit) as exc:
        daemon.exec_module("dome")

    assert exc.value.code == 1
    assert "Module 'dome' does not exist." in capsys.readouterr().out
    execv.assert_not_called()


def test_cli_exec_in_systemd_mode(tmp_path, execv, monkeypatch) -> None:
    """exec works in systemd mode, the other commands don't yet."""
    (tmp_path / "config").mkdir()
    (tmp_path / "config" / "camera.yaml").write_text("class: pyobs.modules.test.StandAlone\n")
    monkeypatch.setenv("PYOBSD_MODE", "systemd")
    monkeypatch.setattr(sys, "argv", ["pyobsd", "-p", str(tmp_path), "exec", "camera"])

    pyobsd.main()

    execv.assert_called_once()
    assert str(tmp_path / "config" / "camera.yaml") in execv.call_args.args[1]


def test_exec_not_in_help(monkeypatch, capsys) -> None:
    monkeypatch.setattr(sys, "argv", ["pyobsd", "--help"])
    with pytest.raises(SystemExit):
        pyobsd.main()
    out = capsys.readouterr().out
    assert "{start,stop,restart,status,list,logs,setup}" in out
    assert "exec" not in out
