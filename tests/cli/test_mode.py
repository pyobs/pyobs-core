"""Tests for the pyobsd mode switch (pyobsd.mode, --mode, $PYOBSD_MODE) and for pyobs refusing --pid-file in
systemd mode, see specs/plans/2026-11-25-pyobsd-systemd-mode.md."""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

import pytest

from pyobs.cli import _cli, pyobsd
from pyobs.cli._cli import pyobsd_mode
from pyobs.cli.pyobs import PyobsCLI
from pyobs.cli.pyobsd import PidFileDaemon, PyobsDaemon


@pytest.fixture(autouse=True)
def no_host_config(monkeypatch) -> None:
    """Keep the config file and $PYOBSD_MODE of the machine running the tests out of them."""
    monkeypatch.delenv("PYOBSD_MODE", raising=False)
    monkeypatch.setattr(_cli, "find_config_file", lambda: None)


def use_config(monkeypatch, tmp_path: Path, text: str) -> None:
    config_file = tmp_path / "pyobs.yaml"
    config_file.write_text(text)
    monkeypatch.setattr(_cli, "find_config_file", lambda: str(config_file))


# ── pyobsd_mode ──────────────────────────────────────────────────────────────


def test_mode_default() -> None:
    assert pyobsd_mode({}) == "pid"
    assert pyobsd_mode({"pyobsd": {"path": "/opt/pyobs"}}) == "pid"
    assert pyobsd_mode({"pyobsd": None}) == "pid"


def test_mode_from_config() -> None:
    assert pyobsd_mode({"pyobsd": {"mode": "systemd"}}) == "systemd"
    assert pyobsd_mode({"pyobsd": {"mode": "pid"}}) == "pid"


def test_mode_env_overrides_config(monkeypatch) -> None:
    monkeypatch.setenv("PYOBSD_MODE", "pid")
    assert pyobsd_mode({"pyobsd": {"mode": "systemd"}}) == "pid"
    monkeypatch.setenv("PYOBSD_MODE", "systemd")
    assert pyobsd_mode({}) == "systemd"


def test_mode_unknown(monkeypatch) -> None:
    with pytest.raises(ValueError, match="pyobsd.mode in the config file"):
        pyobsd_mode({"pyobsd": {"mode": "docker"}})
    monkeypatch.setenv("PYOBSD_MODE", "docker")
    with pytest.raises(ValueError, match=r"\$PYOBSD_MODE"):
        pyobsd_mode({})


# ── config file ──────────────────────────────────────────────────────────────


def test_load_config_keeps_whole_file(monkeypatch, tmp_path) -> None:
    """Each CLI takes only its own keys from its section, but file_config has all of it."""
    use_config(monkeypatch, tmp_path, "pyobs:\n  log_level: debug\n  unknown: 1\npyobsd:\n  mode: systemd\n")
    cli = PyobsCLI()
    cli._load_config()
    assert cli._config == {"log_level": "debug"}
    assert cli.file_config["pyobsd"] == {"mode": "systemd"}


def test_load_config_empty_file(monkeypatch, tmp_path) -> None:
    use_config(monkeypatch, tmp_path, "")
    cli = PyobsCLI()
    cli._load_config()
    assert cli._config == {}
    assert cli.file_config == {}


# ── pyobs: guard against --pid-file ──────────────────────────────────────────


def run_pyobs(monkeypatch, mocker, *args: str) -> tuple[Any, Any]:
    start_daemon = mocker.patch.object(PyobsCLI, "_start_daemon")
    application = mocker.patch.object(PyobsCLI, "application")
    monkeypatch.setattr(sys, "argv", ["pyobs", *args, "module.yaml"])
    PyobsCLI()()
    return start_daemon, application


def test_pyobs_pid_file_in_pid_mode(monkeypatch, mocker) -> None:
    start_daemon, _ = run_pyobs(monkeypatch, mocker, "--pid-file", "run/module.pid")
    start_daemon.assert_called_once()


def test_pyobs_pid_file_refused_in_systemd_mode(monkeypatch, mocker, tmp_path) -> None:
    use_config(monkeypatch, tmp_path, "pyobsd:\n  mode: systemd\n")
    with pytest.raises(SystemExit) as exc:
        run_pyobs(monkeypatch, mocker, "--pid-file", "run/module.pid")
    assert "pyobsd mode: systemd" in str(exc.value.code)
    assert "PYOBSD_MODE=pid" in str(exc.value.code)


def test_pyobs_pid_file_allowed_with_env_override(monkeypatch, mocker, tmp_path) -> None:
    use_config(monkeypatch, tmp_path, "pyobsd:\n  mode: systemd\n")
    monkeypatch.setenv("PYOBSD_MODE", "pid")
    start_daemon, _ = run_pyobs(monkeypatch, mocker, "--pid-file", "run/module.pid")
    start_daemon.assert_called_once()


def test_pyobs_foreground_in_systemd_mode(monkeypatch, mocker, tmp_path) -> None:
    """Without --pid-file (as the unit starts it), pyobs runs in systemd mode."""
    use_config(monkeypatch, tmp_path, "pyobsd:\n  mode: systemd\n")
    start_daemon, application = run_pyobs(monkeypatch, mocker)
    start_daemon.assert_not_called()
    application.return_value.run.assert_called_once()


def test_pyobs_pid_file_with_unknown_mode(monkeypatch, mocker, tmp_path) -> None:
    use_config(monkeypatch, tmp_path, "pyobsd:\n  mode: docker\n")
    with pytest.raises(SystemExit) as exc:
        run_pyobs(monkeypatch, mocker, "--pid-file", "run/module.pid")
    assert "Unknown pyobsd mode 'docker'" in str(exc.value.code)


# ── pyobsd: --mode ───────────────────────────────────────────────────────────


def run_pyobsd(monkeypatch, tmp_path, *args: str) -> None:
    monkeypatch.setattr(
        sys, "argv", ["pyobsd", "-p", str(tmp_path), "-c", "config", "-r", "run", "-l", "log", *args, "list"]
    )
    pyobsd.main()


def test_pyobsd_old_name() -> None:
    assert PyobsDaemon is PidFileDaemon


def test_pyobsd_pid_mode_by_default(monkeypatch, mocker, tmp_path) -> None:
    list_modules = mocker.patch.object(PidFileDaemon, "list_modules")
    run_pyobsd(monkeypatch, tmp_path)
    list_modules.assert_called_once()


def test_pyobsd_systemd_mode_not_implemented(monkeypatch, mocker, tmp_path, capsys) -> None:
    use_config(monkeypatch, tmp_path, "pyobsd:\n  mode: systemd\n")
    list_modules = mocker.patch.object(PidFileDaemon, "list_modules")
    with pytest.raises(SystemExit) as exc:
        run_pyobsd(monkeypatch, tmp_path)
    assert exc.value.code == 1
    assert "systemd mode is not implemented" in capsys.readouterr().out
    list_modules.assert_not_called()


def test_pyobsd_mode_option_overrides_config(monkeypatch, mocker, tmp_path) -> None:
    use_config(monkeypatch, tmp_path, "pyobsd:\n  mode: systemd\n")
    list_modules = mocker.patch.object(PidFileDaemon, "list_modules")
    run_pyobsd(monkeypatch, tmp_path, "--mode", "pid")
    list_modules.assert_called_once()


def test_pyobsd_unknown_mode_in_config(monkeypatch, tmp_path, capsys) -> None:
    use_config(monkeypatch, tmp_path, "pyobsd:\n  mode: docker\n")
    with pytest.raises(SystemExit) as exc:
        run_pyobsd(monkeypatch, tmp_path)
    assert exc.value.code == 2
    assert "Unknown pyobsd mode 'docker'" in capsys.readouterr().err


def test_pid_mode_passes_mode_to_pyobs(mocker, tmp_path) -> None:
    """pyobsd in PID-file mode (e.g. --mode pid on a systemd host) sets $PYOBSD_MODE=pid for the module, so the
    guard in pyobs lets it start."""
    popen = mocker.patch("subprocess.Popen")
    mocker.patch.object(PidFileDaemon, "_read_pid", return_value=12345)
    mocker.patch.object(PidFileDaemon, "_is_alive", return_value=True)
    daemon = PidFileDaemon(str(tmp_path / "config"), str(tmp_path / "run"), str(tmp_path / "log"))
    daemon._pyobs_exec = "pyobs"

    daemon._start_service("camera")

    assert popen.call_args.kwargs["env"]["PYOBSD_MODE"] == "pid"
