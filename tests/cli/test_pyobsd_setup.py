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
from pyobs.cli._systemd_files import SystemdPaths


class FakeSystem:
    """Users, groups and file owners, instead of the real ones."""

    def __init__(self, users: set[str], groups: set[str]):
        self.users = users
        self.groups = groups
        self.owners: dict[str, tuple[str, str]] = {}
        self.commands: list[list[str]] = []
        self.journal: set[str] = set()
        self.units: set[str] = {"polkit.service"}
        self.enabled: set[str] = set()
        self.active: set[str] = set()

    def run(self, cmd: list[str]) -> None:
        self.commands.append(cmd)
        if cmd[0] == "adduser":
            self.users.add(cmd[-1])
            if "--group" in cmd:
                self.groups.add(cmd[-1])
        if cmd[:3] == ["usermod", "-aG", "systemd-journal"]:
            self.journal.add(cmd[-1])

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

    # systemd mode
    monkeypatch.setattr(_setup, "_in_group", lambda u, g: g == "systemd-journal" and u in fake.journal)
    monkeypatch.setattr(_setup, "_unit_exists", lambda u: u in fake.units)
    monkeypatch.setattr(_setup, "_unit_enabled", lambda u: u in fake.enabled)
    monkeypatch.setattr(_setup, "_active_units", lambda pattern: sorted(fake.active))

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
    kwargs.setdefault("pyobsd_exec", "/venv/bin/pyobsd")
    kwargs.setdefault("systemd_paths", systemd_paths(tmp_path))
    return Setup(options, file_config or {}, config_file=str(tmp_path / "etc" / "pyobs.yaml"), **kwargs)


def systemd_paths(tmp_path: Path) -> SystemdPaths:
    etc = tmp_path / "etc"
    return SystemdPaths(
        unit=str(etc / "systemd" / "system" / "pyobs@.service"),
        generator=str(etc / "systemd" / "system-generators" / "pyobs-generator"),
        polkit_rule=str(etc / "polkit-1" / "rules.d" / "50-pyobs.rules"),
        shutdown_dropins=(
            str(etc / "systemd" / "system" / "reboot.target.d" / "pyobs.conf"),
            str(etc / "systemd" / "system" / "poweroff.target.d" / "pyobs.conf"),
        ),
    )


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


# ── systemd mode ─────────────────────────────────────────────────────────────


def systemd_opts(tmp_path: Path, **kwargs: Any) -> SetupOptions:
    kwargs.setdefault("mode", "systemd")
    return opts(tmp_path, **kwargs)


def test_systemd_new_host(system, tmp_path) -> None:
    paths = systemd_paths(tmp_path)
    assert make_setup(tmp_path, systemd_opts(tmp_path))() == 0

    base = tmp_path / "pyobs"
    unit = Path(paths.unit).read_text()
    assert f"ConditionPathExists=|{base}/config/%i.yaml" in unit
    assert f"WorkingDirectory={base}/run" in unit
    assert "ExecStart=/venv/bin/pyobsd exec %i" in unit
    assert "User=pyobs\nGroup=pyobs\n" in unit
    assert "After=network-online.target ejabberd.service" in unit
    assert "[Install]" not in unit
    assert os.stat(paths.generator).st_mode & 0o777 == 0o755
    assert 'subject.user == "pyobs"' in Path(paths.polkit_rule).read_text()
    assert read_config(tmp_path)["pyobsd"]["mode"] == "systemd"

    # no shutdown timeout by default
    assert not any(os.path.exists(d) for d in paths.shutdown_dropins)
    assert ["systemctl", "daemon-reload"] in system.commands
    assert ["usermod", "-aG", "systemd-journal", "pyobs"] in system.commands


def test_systemd_second_run_changes_nothing(system, tmp_path, capsys) -> None:
    assert make_setup(tmp_path, systemd_opts(tmp_path, shutdown_timeout=60))() == 0
    system.commands.clear()
    capsys.readouterr()

    assert make_setup(tmp_path, systemd_opts(tmp_path), file_config=read_config(tmp_path))() == 0
    assert "Nothing to do." in capsys.readouterr().out
    assert system.commands == []
    # the shutdown timeout is kept, read from the drop-in
    assert "JobTimeoutSec=60min" in Path(systemd_paths(tmp_path).shutdown_dropins[0]).read_text()


def test_systemd_changed_user_updates_files(system, tmp_path, capsys) -> None:
    assert make_setup(tmp_path, systemd_opts(tmp_path))() == 0
    system.users.add("obs")
    system.groups.add("obs")
    system.commands.clear()
    capsys.readouterr()

    assert make_setup(tmp_path, systemd_opts(tmp_path, user="obs"))() == 0
    out = capsys.readouterr().out
    paths = systemd_paths(tmp_path)
    assert f"Update {paths.unit}" in out
    assert f"Update {paths.polkit_rule}" in out
    assert f"Update {paths.generator}" not in out
    assert "User=obs" in Path(paths.unit).read_text()
    assert ["systemctl", "daemon-reload"] in system.commands


def test_systemd_only_polkit_rule_changed_needs_no_reload(system, tmp_path) -> None:
    assert make_setup(tmp_path, systemd_opts(tmp_path))() == 0
    Path(systemd_paths(tmp_path).polkit_rule).write_text("old")
    system.commands.clear()
    assert make_setup(tmp_path, systemd_opts(tmp_path))() == 0
    assert ["systemctl", "daemon-reload"] not in system.commands


def test_systemd_shutdown_timeout(system, tmp_path) -> None:
    paths = systemd_paths(tmp_path)
    assert make_setup(tmp_path, systemd_opts(tmp_path, shutdown_timeout=90))() == 0
    for dropin in paths.shutdown_dropins:
        assert "[Unit]\nJobTimeoutSec=90min\n" in Path(dropin).read_text()

    # --no-shutdown-timeout removes them
    system.commands.clear()
    assert make_setup(tmp_path, systemd_opts(tmp_path, shutdown_timeout=0))() == 0
    assert not any(os.path.exists(d) for d in paths.shutdown_dropins)
    assert ["systemctl", "daemon-reload"] in system.commands


def test_systemd_negative_shutdown_timeout(system, tmp_path) -> None:
    assert make_setup(tmp_path, systemd_opts(tmp_path, shutdown_timeout=-1))() == 1
    assert not (tmp_path / "etc" / "pyobs.yaml").exists()


def test_systemd_interactive_shutdown_timeout(system, tmp_path) -> None:
    # mode, user, journal?, log files?, cooled cameras?, minutes (invalid, then default), continue?
    ask = answers("systemd", "", "", "", "y", "abc", "", "y")
    setup = make_setup(tmp_path, SetupOptions(path=str(tmp_path / "pyobs")), interactive=True, input_func=ask)
    assert setup() == 0
    assert "JobTimeoutSec=60min" in Path(systemd_paths(tmp_path).shutdown_dropins[0]).read_text()


def test_systemd_journal_member_not_added_again(system, tmp_path) -> None:
    system.journal.add("pyobs")
    assert make_setup(tmp_path, systemd_opts(tmp_path))() == 0
    assert not any(c[0] == "usermod" for c in system.commands)


def test_systemd_warnings(system, tmp_path, capsys, monkeypatch) -> None:
    system.units.clear()
    system.enabled.add("pyobs.service")
    run = tmp_path / "pyobs" / "run"
    run.mkdir(parents=True)
    (run / "camera.pid").write_text(f"{os.getpid()}\n")
    (run / "gone.pid").write_text("999999999\n")
    config = tmp_path / "pyobs" / "config"
    config.mkdir()
    for name in ("camera", "_telescope", "bad name", "x.shared"):
        (config / f"{name}.yaml").write_text("{}\n")

    assert make_setup(tmp_path, systemd_opts(tmp_path))() == 0
    out = capsys.readouterr().out
    assert "polkitd is not installed" in out
    assert "systemctl disable pyobs.service" in out
    assert "Modules still running in PID-file mode: camera." in out
    assert "can't be unit names, so the modules can't run: bad name." in out

    assert make_setup(tmp_path, systemd_opts(tmp_path, strict=True))() == 1


def test_pid_mode_has_no_systemd_checks(system, tmp_path, capsys) -> None:
    system.units.clear()
    assert make_setup(tmp_path, opts(tmp_path))() == 0
    assert "polkitd" not in capsys.readouterr().out
    assert not os.path.exists(systemd_paths(tmp_path).unit)


# ── generator ────────────────────────────────────────────────────────────────


@pytest.mark.skipif(sys.platform != "linux", reason="needs sh")
def test_generator_script(tmp_path) -> None:
    import subprocess

    from pyobs.cli._systemd_files import SystemdSettings, render_generator

    config = tmp_path / "my config"
    config.mkdir()
    for name in ("camera", "_telescope", "bad name", "x.shared", "a.b-c:d"):
        (config / f"{name}.yaml").write_text("{}\n")
    script = tmp_path / "gen"
    paths = SystemdPaths()
    script.write_text(render_generator(SystemdSettings("/x/pyobsd", str(config), "/run", "pyobs", "pyobs"), paths))
    out = tmp_path / "normal"

    result = subprocess.run(["sh", str(script), str(out), str(tmp_path / "early"), str(tmp_path / "late")])
    assert result.returncode == 0
    wants = out / "multi-user.target.wants"
    assert sorted(os.listdir(wants)) == ["pyobs@a.b-c:d.service", "pyobs@camera.service"]
    assert os.readlink(wants / "pyobs@camera.service") == paths.unit


@pytest.mark.skipif(sys.platform != "linux", reason="needs sh")
def test_generator_script_without_config_dir(tmp_path) -> None:
    import subprocess

    from pyobs.cli._systemd_files import SystemdSettings, render_generator

    script = tmp_path / "gen"
    script.write_text(render_generator(SystemdSettings("/x", str(tmp_path / "missing"), "/run", "pyobs", "pyobs")))
    result = subprocess.run(["sh", str(script), str(tmp_path / "normal"), "", ""])
    assert result.returncode == 0
    assert not (tmp_path / "normal").exists()


# ── other calls in systemd mode ──────────────────────────────────────────────


def test_check_installed(system, tmp_path) -> None:
    from pyobs.cli._systemd_files import SystemdSettings, check_installed

    paths = systemd_paths(tmp_path)
    settings = SystemdSettings(
        "/venv/bin/pyobsd", str(tmp_path / "pyobs" / "config"), str(tmp_path / "pyobs" / "run"), "pyobs", "pyobs"
    )
    assert len(check_installed(settings, paths)) == 3
    assert make_setup(tmp_path, systemd_opts(tmp_path))() == 0
    assert check_installed(settings, paths) == []
    Path(paths.unit).write_text("old")
    assert check_installed(settings, paths) == [f"{paths.unit} is outdated, run pyobsd setup as root."]


def test_check_installed_skips_unreadable(tmp_path, monkeypatch) -> None:
    from pyobs.cli import _systemd_files

    monkeypatch.setattr(_systemd_files, "file_differs", lambda f, c: None)
    settings = _systemd_files.SystemdSettings("/x", "/c", "/r", "pyobs", "pyobs")
    assert _systemd_files.check_installed(settings, systemd_paths(tmp_path)) == []


def test_cli_warns_in_systemd_mode(monkeypatch, tmp_path, capsys) -> None:
    from pyobs.cli import _systemd_files

    config_file = tmp_path / "pyobs.yaml"
    config_file.write_text("pyobsd:\n  mode: systemd\n")
    monkeypatch.setattr(_cli, "find_config_file", lambda: str(config_file))
    monkeypatch.setattr(_setup, "find_pyobsd_exec", lambda: "/venv/bin/pyobsd")
    monkeypatch.setattr(_systemd_files, "check_installed", lambda s: [f"{s.user} {s.config_path} missing"])
    monkeypatch.setattr(sys, "argv", ["pyobsd", "-p", "/srv/pyobs", "--chuid", "obs", "list"])
    from pyobs.cli._systemd_daemon import SystemdDaemon

    monkeypatch.setattr(SystemdDaemon, "__init__", lambda self, *a, **k: None)
    monkeypatch.setattr(SystemdDaemon, "list_modules", lambda self: None)
    pyobsd.main()
    assert "Warning: obs /srv/pyobs/config missing" in capsys.readouterr().err


def test_cli_passes_shutdown_timeout(monkeypatch, mocker) -> None:
    monkeypatch.setattr(_cli, "find_config_file", lambda: None)
    mocker.patch.object(Setup, "__call__", return_value=0)
    init = mocker.spy(Setup, "__init__")
    for args, expected in ((["--shutdown-timeout", "45"], 45), (["--no-shutdown-timeout"], 0), ([], None)):
        monkeypatch.setattr(sys, "argv", ["pyobsd", "setup", *args])
        with pytest.raises(SystemExit):
            pyobsd.main()
        assert init.call_args[0][1].shutdown_timeout == expected


# ── back to PID-file mode ────────────────────────────────────────────────────


def test_pid_mode_removes_systemd_files(system, tmp_path, capsys) -> None:
    paths = systemd_paths(tmp_path)
    assert make_setup(tmp_path, systemd_opts(tmp_path, shutdown_timeout=60))() == 0
    system.commands.clear()

    assert make_setup(tmp_path, opts(tmp_path, mode="pid"))() == 0
    for f in (paths.unit, paths.generator, paths.polkit_rule, *paths.shutdown_dropins):
        assert not os.path.exists(f)
    # the generator's and the drop-ins' directories go, the shared ones stay
    assert not os.path.exists(os.path.dirname(paths.generator))
    assert not any(os.path.exists(os.path.dirname(d)) for d in paths.shutdown_dropins)
    assert os.path.isdir(os.path.dirname(paths.unit))
    assert os.path.isdir(os.path.dirname(paths.polkit_rule))
    assert ["systemctl", "daemon-reload"] in system.commands
    assert read_config(tmp_path)["pyobsd"]["mode"] == "pid"

    # nothing left to do
    capsys.readouterr()
    assert make_setup(tmp_path, opts(tmp_path, mode="pid"))() == 0
    assert "Nothing to do." in capsys.readouterr().out


def test_pid_mode_keeps_other_files_in_shared_dirs(system, tmp_path) -> None:
    paths = systemd_paths(tmp_path)
    assert make_setup(tmp_path, systemd_opts(tmp_path, shutdown_timeout=60))() == 0
    other = Path(paths.shutdown_dropins[0]).parent / "other.conf"
    other.write_text("[Unit]\n")
    assert make_setup(tmp_path, opts(tmp_path, mode="pid"))() == 0
    assert other.exists()


def test_pid_mode_refuses_with_running_units(system, tmp_path, capsys) -> None:
    paths = systemd_paths(tmp_path)
    assert make_setup(tmp_path, systemd_opts(tmp_path))() == 0
    system.active.add("pyobs@camera.service")

    assert make_setup(tmp_path, opts(tmp_path, mode="pid"))() == 1
    assert "running as systemd units: pyobs@camera.service" in capsys.readouterr().out
    assert os.path.exists(paths.unit)
    assert read_config(tmp_path)["pyobsd"]["mode"] == "systemd"


def test_pid_mode_only_polkit_rule_needs_no_reload(system, tmp_path) -> None:
    paths = systemd_paths(tmp_path)
    Path(paths.polkit_rule).parent.mkdir(parents=True)
    Path(paths.polkit_rule).write_text("old")
    assert make_setup(tmp_path, opts(tmp_path))() == 0
    assert not os.path.exists(paths.polkit_rule)
    assert ["systemctl", "daemon-reload"] not in system.commands


def test_removed_shutdown_dropins_take_their_dirs(system, tmp_path) -> None:
    paths = systemd_paths(tmp_path)
    assert make_setup(tmp_path, systemd_opts(tmp_path, shutdown_timeout=60))() == 0
    assert make_setup(tmp_path, systemd_opts(tmp_path, shutdown_timeout=0))() == 0
    assert not any(os.path.exists(os.path.dirname(d)) for d in paths.shutdown_dropins)


# ── symlinked directories ────────────────────────────────────────────────────


def test_symlinked_dir_owner_is_not_changed(system, tmp_path, capsys) -> None:
    target = tmp_path / "checkout" / "config"
    target.mkdir(parents=True)
    (tmp_path / "pyobs").mkdir()
    (tmp_path / "pyobs" / "config").symlink_to(target)

    assert make_setup(tmp_path, opts(tmp_path))() == 0
    assert str(target) not in system.owners
    assert str(tmp_path / "pyobs" / "config") not in system.owners
    assert "config is a symlink, its target is not owned by pyobs:pyobs" in capsys.readouterr().out


def test_symlinked_dir_with_right_owner(system, tmp_path, capsys) -> None:
    target = tmp_path / "checkout" / "config"
    target.mkdir(parents=True)
    (tmp_path / "pyobs").mkdir()
    (tmp_path / "pyobs" / "config").symlink_to(target)
    system.owners[str(tmp_path / "pyobs" / "config")] = ("pyobs", "pyobs")

    assert make_setup(tmp_path, opts(tmp_path))() == 0
    assert "is a symlink" not in capsys.readouterr().out


def test_broken_symlink_is_an_error(system, tmp_path, capsys) -> None:
    (tmp_path / "pyobs").mkdir()
    (tmp_path / "pyobs" / "config").symlink_to(tmp_path / "missing")
    assert make_setup(tmp_path, opts(tmp_path))() == 1
    assert "symlink to a missing directory" in capsys.readouterr().out
