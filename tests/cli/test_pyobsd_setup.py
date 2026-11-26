"""Tests for ``pyobsd setup`` (pyobs/cli/_setup.py), with tmp dirs and the system calls mocked."""

from __future__ import annotations

import os
import sys
from collections.abc import Iterator
from pathlib import Path
from typing import Any

import pytest
import yaml

from pyobs.cli import _cli, _setup, pyobsd
from pyobs.cli._setup import Setup, SetupOptions


class FakeSystem:
    """Users, groups and file owners, instead of the real ones."""

    def __init__(self, users: set[str], groups: set[str]):
        self.users = users
        self.groups = groups
        self.owners: dict[str, tuple[str, str]] = {}
        self.commands: list[list[str]] = []

    def run(self, cmd: list[str]) -> None:
        self.commands.append(cmd)
        if cmd[0] == "adduser":
            self.users.add(cmd[-1])
            if "--group" in cmd:
                self.groups.add(cmd[-1])

    def chown(self, directory: str, user: str, group: str) -> None:
        self.owners[os.path.abspath(directory)] = (user, group)


@pytest.fixture
def system(monkeypatch, tmp_path) -> FakeSystem:
    fake = FakeSystem({"pyobs"}, {"pyobs"})
    monkeypatch.setattr(os, "geteuid", lambda: 0)
    monkeypatch.setattr(_setup, "_user_exists", lambda u: u in fake.users)
    monkeypatch.setattr(_setup, "_group_exists", lambda g: g in fake.groups)
    monkeypatch.setattr(_setup, "_run", fake.run)
    monkeypatch.setattr(_setup, "_chown", fake.chown)

    # owner of a directory: what chown set, else root
    monkeypatch.setattr(_setup, "_owner", lambda d: fake.owners.get(os.path.abspath(d), ("root", "root")))

    # no real config files in the lookup order
    monkeypatch.setattr(
        _setup,
        "config_file_candidates",
        lambda: [str(tmp_path / "home" / ".config" / "pyobs.yaml"), str(tmp_path / "etc" / "pyobs.yaml")],
    )
    (tmp_path / "etc").mkdir()
    return fake


def answers(*lines: str) -> Any:
    """An input function giving these answers, one per question."""
    it: Iterator[str] = iter(lines)

    def ask(prompt: str) -> str:
        print(prompt)
        return next(it)

    return ask


def make_setup(
    tmp_path: Path, options: SetupOptions, file_config: dict[str, Any] | None = None, **kwargs: Any
) -> Setup:
    kwargs.setdefault("interactive", False)
    return Setup(options, file_config or {}, config_file=str(tmp_path / "etc" / "pyobs.yaml"), **kwargs)


def read_config(tmp_path: Path) -> dict[str, Any]:
    return yaml.safe_load((tmp_path / "etc" / "pyobs.yaml").read_text())


def opts(tmp_path: Path, **kwargs: Any) -> SetupOptions:
    kwargs.setdefault("path", str(tmp_path / "pyobs"))
    return SetupOptions(**kwargs)


# ── unattended ───────────────────────────────────────────────────────────────


def test_new_host(system, tmp_path) -> None:
    assert make_setup(tmp_path, opts(tmp_path))() == 0

    base = tmp_path / "pyobs"
    for sub in ("config", "log", "run", "storage"):
        assert (base / sub).is_dir()
        assert system.owners[str(base / sub)] == ("pyobs", "pyobs")
    assert read_config(tmp_path) == {
        "pyobsd": {"mode": "pid", "chuid": "pyobs:pyobs", "path": str(base), "syslog": True, "file_log": False}
    }
    assert not (tmp_path / "etc" / "pyobs.yaml.bak").exists()


def test_options_are_written(system, tmp_path) -> None:
    system.users.add("obs")
    system.groups.add("staff")
    options = opts(tmp_path, user="obs:staff", syslog=False, file_log=True)
    assert make_setup(tmp_path, options)() == 0
    section = read_config(tmp_path)["pyobsd"]
    assert section["chuid"] == "obs:staff"
    assert section["syslog"] is False
    assert section["file_log"] is True
    assert system.owners[str(tmp_path / "pyobs" / "run")] == ("obs", "staff")


def test_second_run_changes_nothing(system, tmp_path, capsys) -> None:
    assert make_setup(tmp_path, opts(tmp_path))() == 0
    before = (tmp_path / "etc" / "pyobs.yaml").read_text()
    capsys.readouterr()

    assert make_setup(tmp_path, opts(tmp_path), file_config=read_config(tmp_path))() == 0
    assert "Nothing to do." in capsys.readouterr().out
    assert (tmp_path / "etc" / "pyobs.yaml").read_text() == before
    assert not (tmp_path / "etc" / "pyobs.yaml.bak").exists()


def test_defaults_from_current_config(system, tmp_path) -> None:
    system.users.add("obs")
    system.groups.add("obs")
    current = {"pyobsd": {"chuid": "obs", "file_log": True}}
    assert make_setup(tmp_path, opts(tmp_path), file_config=current)() == 0
    section = read_config(tmp_path)["pyobsd"]
    assert section["chuid"] == "obs:obs"
    assert section["file_log"] is True


def test_existing_file_keeps_other_values_and_gets_backup(system, tmp_path, capsys) -> None:
    config_file = tmp_path / "etc" / "pyobs.yaml"
    old = "# comment\npyobs:\n  log_level: debug\npyobsd:\n  stop_timeout: 60\n  syslog: false\n"
    config_file.write_text(old)

    assert make_setup(tmp_path, opts(tmp_path, syslog=True))() == 0

    out = capsys.readouterr().out
    assert "comments and formatting are lost" in out
    assert "syslog: False -> True" in out
    cfg = read_config(tmp_path)
    assert cfg["pyobs"] == {"log_level": "debug"}
    assert cfg["pyobsd"]["stop_timeout"] == 60
    assert cfg["pyobsd"]["syslog"] is True
    assert (tmp_path / "etc" / "pyobs.yaml.bak").read_text() == old


def test_wrong_owner_is_fixed(system, tmp_path) -> None:
    (tmp_path / "pyobs" / "config").mkdir(parents=True)
    (tmp_path / "pyobs" / "config" / "camera.yaml").write_text("x: 1\n")
    assert make_setup(tmp_path, opts(tmp_path))() == 0
    assert system.owners[str(tmp_path / "pyobs" / "config")] == ("pyobs", "pyobs")
    assert (tmp_path / "pyobs" / "config" / "camera.yaml").read_text() == "x: 1\n"


def test_not_root(system, tmp_path, monkeypatch, capsys) -> None:
    monkeypatch.setattr(os, "geteuid", lambda: 1000)
    assert make_setup(tmp_path, opts(tmp_path))() == 1
    assert "must run as root" in capsys.readouterr().out
    assert not (tmp_path / "etc" / "pyobs.yaml").exists()


def test_systemd_mode_not_implemented_yet(system, tmp_path, capsys) -> None:
    assert make_setup(tmp_path, opts(tmp_path, mode="systemd"))() == 1
    assert "not implemented" in capsys.readouterr().out
    assert not (tmp_path / "etc" / "pyobs.yaml").exists()


# ── user ─────────────────────────────────────────────────────────────────────


def test_missing_user_unattended_is_an_error(system, tmp_path, capsys) -> None:
    system.users.clear()
    assert make_setup(tmp_path, opts(tmp_path))() == 1
    assert "--create-user" in capsys.readouterr().out
    assert system.commands == []
    assert not (tmp_path / "pyobs").exists()
    assert not (tmp_path / "etc" / "pyobs.yaml").exists()


def test_create_user(system, tmp_path) -> None:
    system.users.clear()
    system.groups.clear()
    assert make_setup(tmp_path, opts(tmp_path, create_user=True))() == 0
    assert system.commands == [["adduser", "--system", "--group", "--home", str(tmp_path / "pyobs"), "pyobs"]]


def test_create_user_in_existing_group(system, tmp_path) -> None:
    system.groups.add("staff")
    options = opts(tmp_path, user="obs:staff", create_user=True)
    assert make_setup(tmp_path, options)() == 0
    assert system.commands == [["adduser", "--system", "--ingroup", "staff", "--home", str(tmp_path / "pyobs"), "obs"]]


def test_missing_group(system, tmp_path, capsys) -> None:
    assert make_setup(tmp_path, opts(tmp_path, user="pyobs:staff"))() == 1
    assert "Group 'staff' does not exist" in capsys.readouterr().out


# ── interactive ──────────────────────────────────────────────────────────────


def test_interactive(system, tmp_path) -> None:
    system.users.clear()
    system.groups.clear()
    base = str(tmp_path / "base")
    # mode, user, path, create user?, journal?, log files?, continue?
    ask = answers("", "", base, "y", "n", "y", "y")
    setup = Setup(
        SetupOptions(), {}, config_file=str(tmp_path / "etc" / "pyobs.yaml"), interactive=True, input_func=ask
    )
    assert setup() == 0
    section = read_config(tmp_path)["pyobsd"]
    assert section == {"mode": "pid", "chuid": "pyobs:pyobs", "path": base, "syslog": False, "file_log": True}
    assert system.commands[0][0] == "adduser"


def test_interactive_options_are_not_asked(system, tmp_path, capsys) -> None:
    options = opts(tmp_path, mode="pid", user="pyobs", syslog=True, file_log=False)
    setup = make_setup(tmp_path, options, interactive=True, input_func=answers("y"))
    assert setup() == 0
    out = capsys.readouterr().out
    assert "Continue?" in out
    assert "Mode" not in out


def test_interactive_no_changes_on_no(system, tmp_path) -> None:
    setup = make_setup(
        tmp_path,
        opts(tmp_path, mode="pid", user="pyobs", syslog=True, file_log=False),
        interactive=True,
        input_func=answers("n"),
    )
    assert setup() == 1
    assert not (tmp_path / "etc" / "pyobs.yaml").exists()
    assert not (tmp_path / "pyobs").exists()


def test_interactive_invalid_mode_is_asked_again(system, tmp_path) -> None:
    ask = answers("docker", "pid", "", "", "", "y")
    setup = make_setup(tmp_path, SetupOptions(path=str(tmp_path / "pyobs")), interactive=True, input_func=ask)
    assert setup() == 0


# ── shadowing config files ───────────────────────────────────────────────────


def test_warns_about_earlier_config_file(system, tmp_path, capsys) -> None:
    earlier = tmp_path / "home" / ".config" / "pyobs.yaml"
    earlier.parent.mkdir(parents=True)
    earlier.write_text("pyobsd: {}\n")
    assert make_setup(tmp_path, opts(tmp_path))() == 0
    assert f"Warning: {earlier} exists and is used instead" in capsys.readouterr().out


def test_strict_makes_warnings_errors(system, tmp_path) -> None:
    earlier = tmp_path / "home" / ".config" / "pyobs.yaml"
    earlier.parent.mkdir(parents=True)
    earlier.write_text("pyobsd: {}\n")
    assert make_setup(tmp_path, opts(tmp_path, strict=True))() == 1
    # the changes are still made
    assert (tmp_path / "etc" / "pyobs.yaml").exists()


def test_warns_about_later_pyobsd_section(system, tmp_path, monkeypatch, capsys) -> None:
    later = tmp_path / "storage" / "pyobs.yaml"
    later.parent.mkdir()
    later.write_text("pyobsd:\n  chuid: pyobs\n")
    monkeypatch.setattr(_setup, "config_file_candidates", lambda: [str(tmp_path / "etc" / "pyobs.yaml"), str(later)])
    assert make_setup(tmp_path, opts(tmp_path))() == 0
    assert f"Warning: {later} has a pyobsd section, which is ignored" in capsys.readouterr().out


# ── CLI ──────────────────────────────────────────────────────────────────────


def test_cli_passes_options(monkeypatch, mocker, tmp_path) -> None:
    monkeypatch.setattr(_cli, "find_config_file", lambda: None)
    call = mocker.patch.object(Setup, "__call__", return_value=0)
    init = mocker.spy(Setup, "__init__")
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "pyobsd",
            "setup",
            "--mode",
            "pid",
            "--user",
            "obs:staff",
            "--no-create-user",
            "--path",
            "/srv/pyobs",
            "--no-syslog",
            "--file-log",
            "-y",
            "--strict",
        ],
    )
    with pytest.raises(SystemExit) as exc:
        pyobsd.main()
    assert exc.value.code == 0
    call.assert_called_once()
    options: SetupOptions = init.call_args[0][1]
    assert options == SetupOptions(
        mode="pid",
        user="obs:staff",
        create_user=False,
        path="/srv/pyobs",
        syslog=False,
        file_log=True,
        yes=True,
        strict=True,
    )


def test_cli_options_not_given_are_none(monkeypatch, mocker) -> None:
    monkeypatch.setattr(_cli, "find_config_file", lambda: None)
    mocker.patch.object(Setup, "__call__", return_value=0)
    init = mocker.spy(Setup, "__init__")
    monkeypatch.setattr(sys, "argv", ["pyobsd", "setup"])
    with pytest.raises(SystemExit):
        pyobsd.main()
    assert init.call_args[0][1] == SetupOptions()


def test_cli_setup_runs_with_unknown_mode_in_config(monkeypatch, mocker, tmp_path) -> None:
    """setup can fix a config file with an unknown mode, so it doesn't fail on it."""
    config_file = tmp_path / "pyobs.yaml"
    config_file.write_text("pyobsd:\n  mode: docker\n")
    monkeypatch.setattr(_cli, "find_config_file", lambda: str(config_file))
    mocker.patch.object(Setup, "__call__", return_value=0)
    monkeypatch.setattr(sys, "argv", ["pyobsd", "setup"])
    with pytest.raises(SystemExit) as exc:
        pyobsd.main()
    assert exc.value.code == 0


def test_cli_setup_runs_in_systemd_mode(monkeypatch, mocker, tmp_path) -> None:
    config_file = tmp_path / "pyobs.yaml"
    config_file.write_text("pyobsd:\n  mode: systemd\n")
    monkeypatch.setattr(_cli, "find_config_file", lambda: str(config_file))
    call = mocker.patch.object(Setup, "__call__", return_value=0)
    monkeypatch.setattr(sys, "argv", ["pyobsd", "setup"])
    with pytest.raises(SystemExit):
        pyobsd.main()
    call.assert_called_once()
