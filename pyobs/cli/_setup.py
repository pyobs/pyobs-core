"""``pyobsd setup``: set up a host for pyobsd, run as root.

Creates the user and the directories, and writes the ``pyobsd`` section of /etc/pyobs.yaml. Every question has a
command line option, so it can run unattended. See specs/plans/2026-11-25-pyobsd-systemd-mode.md.
"""

from __future__ import annotations

import glob
import grp
import os
import pwd
import re
import shutil
import subprocess
import sys
from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Any

import psutil
import yaml

from ._cli import PYOBSD_MODES, config_file_candidates
from ._systemd_files import (
    MODULE_NAME_PATTERN,
    SystemdPaths,
    SystemdSettings,
    file_differs,
    installed_files,
    read_shutdown_timeout,
    render_shutdown_dropin,
)

# shutdown timeout for reboots in minutes, if the host has cooled cameras
DEFAULT_SHUTDOWN_TIMEOUT = 60

# the file setup writes
SETUP_CONFIG_FILE = os.path.join("/", "etc", "pyobs.yaml")

# directories below the base path, as (key in the pyobsd section, default)
_DIRECTORIES = [("config_path", "config"), ("log_path", "log"), ("run_path", "run"), (None, "storage")]

_DEFAULTS: dict[str, Any] = {
    "mode": "pid",
    "chuid": "pyobs:pyobs",
    "path": "/opt/pyobs",
    "syslog": True,
    "file_log": False,
}


class SetupError(Exception):
    """An error that stops setup before or during the changes."""


@dataclass
class SetupOptions:
    """Answers given on the command line. None means: not given, ask or take the default."""

    mode: str | None = None
    user: str | None = None
    create_user: bool | None = None
    path: str | None = None
    syslog: bool | None = None
    file_log: bool | None = None
    # minutes, 0 for none
    shutdown_timeout: int | None = None
    yes: bool = False
    strict: bool = False


@dataclass
class _Action:
    description: str
    run: Callable[[], None]


@dataclass
class _Plan:
    actions: list[_Action] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    notes: list[str] = field(default_factory=list)


class Setup:
    """Asks the questions, prints what it will do, and does it.

    Args:
        options: Answers from the command line.
        file_config: Content of the active config file, for the current values.
        config_file: The file to write, /etc/pyobs.yaml.
        interactive: Whether questions may be asked. Defaults to stdin being a terminal and no ``-y``.
        input_func: Reads an answer, for tests.
        pyobsd_exec: The pyobsd the unit runs, defaults to this one.
        systemd_paths: Where the systemd mode's files go, for tests.
    """

    def __init__(
        self,
        options: SetupOptions,
        file_config: dict[str, Any],
        config_file: str = SETUP_CONFIG_FILE,
        interactive: bool | None = None,
        input_func: Callable[[str], str] = input,
        pyobsd_exec: str | None = None,
        systemd_paths: SystemdPaths = SystemdPaths(),
    ):
        self._pyobsd_exec = pyobsd_exec
        self._systemd_paths = systemd_paths
        self._options = options
        section = file_config.get("pyobsd")
        self._current: dict[str, Any] = section if isinstance(section, dict) else {}
        self._config_file = config_file
        self._interactive = (not options.yes and sys.stdin.isatty()) if interactive is None else interactive
        self._input = input_func

    def __call__(self) -> int:
        """Run the setup, return the exit code."""
        try:
            if os.geteuid() != 0:
                raise SetupError("pyobsd setup must run as root.")
            plan = self._plan()
            self._print_plan(plan)
            if plan.actions and self._interactive and not self._ask_bool("Continue?", False):
                print("Nothing changed.")
                return 1
            for action in plan.actions:
                action.run()
            print("Done." if plan.actions else "Nothing to do.")
            return 1 if plan.warnings and self._options.strict else 0
        except SetupError as e:
            print(f"Error: {e}")
            return 1
        except (OSError, subprocess.CalledProcessError) as e:
            print(f"Error: {e}")
            return 1

    # ── questions ─────────────────────────────────────────────────────────────

    def _default(self, key: str) -> Any:
        return self._current.get(key, _DEFAULTS[key])

    def _ask(self, question: str, default: str) -> str:
        answer = self._input(f"{question} [{default}]: ").strip()
        return answer or default

    def _ask_bool(self, question: str, default: bool) -> bool:
        while True:
            answer = self._input(f"{question} [{'Y/n' if default else 'y/N'}]: ").strip().lower()
            if not answer:
                return default
            if answer in ("y", "yes"):
                return True
            if answer in ("n", "no"):
                return False

    def _resolve(self, given: Any, key: str, ask: Callable[[Any], Any]) -> Any:
        """The option if given, else the answer to the question, else the default."""
        if given is not None:
            return given
        default = self._default(key)
        return ask(default) if self._interactive else default

    def _ask_mode(self, default: str) -> str:
        while True:
            answer = self._ask(f"Mode ({' or '.join(PYOBSD_MODES)})", default)
            if answer in PYOBSD_MODES:
                return answer
            print(f"Must be one of: {', '.join(PYOBSD_MODES)}.")

    # ── plan ──────────────────────────────────────────────────────────────────

    def _plan(self) -> _Plan:
        o = self._options
        plan = _Plan()

        # 1. mode
        mode = self._resolve(o.mode, "mode", self._ask_mode)
        if mode not in PYOBSD_MODES:
            raise SetupError(f"Unknown mode {mode!r}, must be one of: {', '.join(PYOBSD_MODES)}.")

        # 2. user and group
        chuid = self._resolve(o.user, "chuid", lambda d: self._ask("User and group (user:group)", d))
        user, _, group = str(chuid).partition(":")
        group = group or user
        if not user:
            raise SetupError("No user given.")
        chuid = f"{user}:{group}"

        # 3. base path
        path = self._resolve(o.path, "path", lambda d: self._ask("Base path", d))
        path = os.path.abspath(str(path))

        # user, needs the path as home
        self._plan_user(plan, user, group, path)

        # 4. logging
        syslog = self._resolve(o.syslog, "syslog", lambda d: self._ask_bool("Log to the systemd journal?", d))
        file_log = self._resolve(
            o.file_log, "file_log", lambda d: self._ask_bool("Also write log files to the log directory?", d)
        )

        # directories
        dirs: dict[str | None, str] = {}
        for key, default in _DIRECTORIES:
            sub = str(self._current.get(key, default)) if key else default
            dirs[key] = os.path.join(path, sub)
            self._plan_directory(plan, dirs[key], user, group)

        # config file
        values = {"mode": mode, "chuid": chuid, "path": path, "syslog": bool(syslog), "file_log": bool(file_log)}
        self._plan_config_file(plan, values)

        # 5. systemd mode: unit, generator, polkit rule, shutdown drop-ins, journal group, checks
        if mode == "systemd":
            settings = SystemdSettings(
                pyobsd_exec=self._pyobsd_exec or find_pyobsd_exec(),
                config_path=dirs["config_path"],
                run_path=dirs["run_path"],
                user=user,
                group=group,
            )
            self._plan_systemd(plan, settings)
        else:
            self._plan_remove_systemd(plan)

        # config files that hide ours, or that we hide
        self._check_shadowing(plan, user)
        return plan

    def _plan_systemd(self, plan: _Plan, settings: SystemdSettings) -> None:
        paths = self._systemd_paths
        reload = False

        # unit, generator, polkit rule
        for filename, (content, mode) in installed_files(settings, paths).items():
            if file_differs(filename, content) is not False:
                verb = "Update" if os.path.exists(filename) else "Write"
                plan.actions.append(_Action(f"{verb} {filename}", _writer(filename, content, mode)))
                reload = reload or filename != paths.polkit_rule

        # shutdown timeout for reboots
        minutes = self._ask_shutdown_timeout(read_shutdown_timeout(paths))
        for filename in paths.shutdown_dropins:
            if minutes:
                content = render_shutdown_dropin(minutes)
                if file_differs(filename, content) is not False:
                    description = f"Write {filename} (JobTimeoutSec={minutes}min)"
                    plan.actions.append(_Action(description, _writer(filename, content, 0o644)))
                    reload = True
            elif os.path.exists(filename):
                plan.actions.append(_Action(f"Remove {filename}", _remover(filename, remove_empty_dir=True)))
                reload = True

        if reload:
            plan.actions.append(_Action("Run systemctl daemon-reload", _runner(["systemctl", "daemon-reload"])))

        # journal, for "pyobsd logs" and web-admin as that user
        if not _in_group(settings.user, "systemd-journal"):
            cmd = ["usermod", "-aG", "systemd-journal", settings.user]
            plan.actions.append(_Action(f"Add {settings.user} to the group systemd-journal", _runner(cmd)))

        # checks, no changes
        if not _unit_exists("polkit.service"):
            plan.warnings.append(
                "polkitd is not installed, so only root can start and stop modules. Install it: apt install polkitd"
            )
        if _unit_enabled("pyobs.service"):
            plan.warnings.append(
                "The old pyobs.service is enabled and starts the modules in PID-file mode at boot. Disable it: "
                "systemctl disable pyobs.service"
            )
        running = _running_pid_files(settings.run_path)
        if running:
            plan.warnings.append(
                f"Modules still running in PID-file mode: {', '.join(running)}. Stop them: pyobsd --mode pid stop"
            )
        invalid = [
            m for m in _module_names(settings.config_path) if not re.fullmatch(MODULE_NAME_PATTERN, m.removeprefix("_"))
        ]
        if invalid:
            plan.warnings.append(
                f"These module names can't be unit names, so the modules can't run: {', '.join(invalid)}. "
                "Use only letters, digits and _.:-"
            )

    def _plan_remove_systemd(self, plan: _Plan) -> None:
        """PID-file mode: remove what the systemd mode installed, so a reboot doesn't start the modules as units."""
        paths = self._systemd_paths
        # (file, whether its directory is ours alone and can go when empty)
        files = [(paths.unit, False), (paths.generator, True), (paths.polkit_rule, False)]
        files += [(d, True) for d in paths.shutdown_dropins]
        installed = [(f, own) for f, own in files if os.path.exists(f)]
        if not installed:
            return

        # removing the unit of a running module would leave it running without its unit file
        active = _active_units("pyobs@*.service")
        if active:
            raise SetupError(
                f"Modules are running as systemd units: {', '.join(active)}. Stop them first: "
                "systemctl stop 'pyobs@*'"
            )

        for filename, own in installed:
            plan.actions.append(_Action(f"Remove {filename} (systemd mode)", _remover(filename, remove_empty_dir=own)))
        if any(f != paths.polkit_rule for f, _ in installed):
            plan.actions.append(_Action("Run systemctl daemon-reload", _runner(["systemctl", "daemon-reload"])))

    def _ask_shutdown_timeout(self, current: int | None) -> int:
        """Minutes, 0 for none."""
        given = self._options.shutdown_timeout
        if given is not None:
            if given < 0:
                raise SetupError("The shutdown timeout must not be negative.")
            return given
        if not self._interactive:
            return current or 0
        if not self._ask_bool("Cooled cameras on this host (longer timeout for reboots)?", current is not None):
            return 0
        while True:
            answer = self._ask("Shutdown timeout for reboots in minutes", str(current or DEFAULT_SHUTDOWN_TIMEOUT))
            if answer.isdigit() and int(answer) > 0:
                return int(answer)
            print("Must be a positive number of minutes.")

    def _plan_user(self, plan: _Plan, user: str, group: str, home: str) -> None:
        if _user_exists(user):
            if not _group_exists(group):
                raise SetupError(f"Group {group!r} does not exist.")
            return
        if group != user and not _group_exists(group):
            raise SetupError(f"Group {group!r} does not exist, create it first.")

        # create it?
        create = self._options.create_user
        if create is None and self._interactive:
            create = self._ask_bool(f"User {user!r} does not exist. Create it?", True)
        if not create:
            raise SetupError(f"User {user!r} does not exist (use --create-user to create it).")

        if group == user:
            cmd = ["adduser", "--system", "--group", "--home", home, user]
        else:
            cmd = ["adduser", "--system", "--ingroup", group, "--home", home, user]
        plan.actions.append(_Action(f"Create user: {' '.join(cmd)}", lambda: _run(cmd)))

    def _plan_directory(self, plan: _Plan, directory: str, user: str, group: str) -> None:
        if os.path.islink(directory):
            # e.g. config linked into a git checkout: don't change owners in there
            if not os.path.isdir(directory):
                raise SetupError(f"{directory} is a symlink to a missing directory.")
            if _owner(directory) != (user, group):
                plan.warnings.append(
                    f"{directory} is a symlink, its target is not owned by {user}:{group}. Not changed, check that "
                    f"{user} can read it."
                )
            return
        if not os.path.isdir(directory):
            plan.actions.append(
                _Action(f"Create {directory}, owned by {user}:{group}", lambda: _make_dir(directory, user, group))
            )
            return
        if _owner(directory) != (user, group):
            plan.actions.append(
                _Action(f"Change owner of {directory} to {user}:{group}", lambda: _chown(directory, user, group))
            )

    def _plan_config_file(self, plan: _Plan, values: dict[str, Any]) -> None:
        cfg: dict[str, Any] = {}
        if os.path.exists(self._config_file):
            with open(self._config_file) as f:
                loaded = yaml.safe_load(f)
            if loaded is None:
                loaded = {}
            if not isinstance(loaded, dict):
                raise SetupError(f"{self._config_file} does not contain a YAML mapping.")
            cfg = loaded

        old = cfg.get("pyobsd")
        old = old if isinstance(old, dict) else {}
        # other keys in the section (e.g. stop_timeout) stay
        new = {**old, **values}
        if new == old and "pyobsd" in cfg:
            return

        changes = [
            f"    {k}: {old[k]!r} -> {new[k]!r}" if k in old else f"    {k}: {new[k]!r} (new)"
            for k in new
            if old.get(k, object()) != new[k]
        ]
        new_cfg = {**cfg, "pyobsd": new}
        description = f"Write pyobsd section of {self._config_file}:\n" + "\n".join(changes)

        if os.path.exists(self._config_file):
            backup = self._config_file + ".bak"
            plan.notes.append(
                f"{self._config_file} is rewritten as plain YAML: its comments and formatting are lost, the values "
                f"stay. The old file is copied to {backup}."
            )

            def write() -> None:
                shutil.copy2(self._config_file, backup)
                _write_yaml(self._config_file, new_cfg)

            plan.actions.append(_Action(description, write))
        else:
            plan.actions.append(_Action(description, lambda: _write_yaml(self._config_file, new_cfg)))

    def _check_shadowing(self, plan: _Plan, user: str) -> None:
        candidates = config_file_candidates()
        ours = os.path.abspath(self._config_file)
        index = next((i for i, c in enumerate(candidates) if os.path.abspath(c) == ours), len(candidates))

        # files before ours in the lookup order hide it: root's, and the one of the pyobs user
        earlier = list(candidates[:index])
        try:
            home = pwd.getpwnam(user).pw_dir
            earlier.append(os.path.join(home, ".config", "pyobs.yaml"))
        except KeyError:
            pass
        for c in dict.fromkeys(os.path.abspath(c) for c in earlier):
            if c != ours and os.path.exists(c):
                plan.warnings.append(f"{c} exists and is used instead of {self._config_file}. Remove it or merge it.")

        # files after ours are hidden by it
        for c in candidates[index + 1 :]:
            if os.path.exists(c) and isinstance(_read_yaml(c).get("pyobsd"), dict):
                plan.warnings.append(
                    f"{c} has a pyobsd section, which is ignored since {self._config_file} exists. Move it there."
                )

    # ── output ────────────────────────────────────────────────────────────────

    def _print_plan(self, plan: _Plan) -> None:
        if plan.actions:
            print("pyobsd setup will:")
            for action in plan.actions:
                print(f"- {action.description}")
        for note in plan.notes:
            print(f"Note: {note}")
        for warning in plan.warnings:
            print(f"Warning: {warning}")


def find_pyobsd_exec() -> str:
    """The pyobsd executable for the unit: this one, else the one in $PATH."""
    if os.path.basename(sys.argv[0]) == "pyobsd" and os.path.exists(sys.argv[0]):
        return os.path.abspath(sys.argv[0])
    found = shutil.which("pyobsd")
    if found is None:
        raise SetupError("Could not find the pyobsd executable.")
    return os.path.abspath(found)


def _writer(filename: str, content: str, mode: int) -> Callable[[], None]:
    def write() -> None:
        os.makedirs(os.path.dirname(filename), exist_ok=True)
        _write_file(filename, content, mode)

    return write


def _remover(filename: str, remove_empty_dir: bool = False) -> Callable[[], None]:
    def remove() -> None:
        os.remove(filename)
        if remove_empty_dir:
            try:
                os.rmdir(os.path.dirname(filename))
            except OSError:
                # not empty
                pass

    return remove


def _runner(cmd: list[str]) -> Callable[[], None]:
    return lambda: _run(cmd)


def _module_names(config_path: str) -> list[str]:
    files = sorted(glob.glob(os.path.join(config_path, "*.yaml")))
    return [os.path.basename(f)[: -len(".yaml")] for f in files if not f.endswith(".shared.yaml")]


def _running_pid_files(run_path: str) -> list[str]:
    """Modules with a PID file whose process is alive."""
    running = []
    for pid_file in sorted(glob.glob(os.path.join(run_path, "*.pid"))):
        try:
            with open(pid_file) as f:
                pid = int(f.read().strip())
        except (OSError, ValueError):
            continue
        if psutil.pid_exists(pid):
            running.append(os.path.basename(pid_file)[: -len(".pid")])
    return running


# ── system helpers, patched in tests ──────────────────────────────────────────


def _in_group(user: str, group: str) -> bool:
    try:
        g = grp.getgrnam(group)
        return user in g.gr_mem or pwd.getpwnam(user).pw_gid == g.gr_gid
    except KeyError:
        return False


def _unit_exists(unit: str) -> bool:
    out = subprocess.run(["systemctl", "list-unit-files", unit], capture_output=True, text=True)
    return unit in out.stdout


def _active_units(pattern: str) -> list[str]:
    """Units matching the pattern that are running, starting or stopping."""
    cmd = ["systemctl", "list-units", "--plain", "--no-legend", "--state=active,activating,deactivating", pattern]
    try:
        out = subprocess.run(cmd, capture_output=True, text=True)
    except FileNotFoundError:
        # no systemd
        return []
    return [line.split()[0] for line in out.stdout.splitlines() if line.strip()]


def _unit_enabled(unit: str) -> bool:
    out = subprocess.run(["systemctl", "is-enabled", unit], capture_output=True, text=True)
    return out.stdout.strip() == "enabled"


def _user_exists(user: str) -> bool:
    try:
        pwd.getpwnam(user)
        return True
    except KeyError:
        return False


def _group_exists(group: str) -> bool:
    try:
        grp.getgrnam(group)
        return True
    except KeyError:
        return False


def _owner(path: str) -> tuple[str | None, str | None]:
    """User and group name of a file, None for an unknown id."""
    st = os.stat(path)
    try:
        user: str | None = pwd.getpwuid(st.st_uid).pw_name
    except KeyError:
        user = None
    try:
        group: str | None = grp.getgrgid(st.st_gid).gr_name
    except KeyError:
        group = None
    return user, group


def _run(cmd: list[str]) -> None:
    subprocess.run(cmd, check=True)


def _make_dir(directory: str, user: str, group: str) -> None:
    os.makedirs(directory, exist_ok=True)
    _chown(directory, user, group)


def _chown(directory: str, user: str, group: str) -> None:
    shutil.chown(directory, user, group)


def _read_yaml(filename: str) -> dict[str, Any]:
    try:
        with open(filename) as f:
            cfg = yaml.safe_load(f)
    except (OSError, yaml.YAMLError):
        return {}
    return cfg if isinstance(cfg, dict) else {}


def _write_yaml(filename: str, cfg: dict[str, Any]) -> None:
    _write_file(filename, yaml.safe_dump(cfg, sort_keys=False, default_flow_style=False), 0o644)


def _write_file(filename: str, content: str, mode: int) -> None:
    tmp = filename + ".tmp"
    with open(tmp, "w") as f:
        f.write(content)
    os.chmod(tmp, mode)
    os.replace(tmp, filename)
