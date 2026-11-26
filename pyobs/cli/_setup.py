"""``pyobsd setup``: set up a host for pyobsd, run as root.

Creates the user and the directories, and writes the ``pyobsd`` section of /etc/pyobs.yaml. Every question has a
command line option, so it can run unattended. See specs/plans/2026-11-25-pyobsd-systemd-mode.md.
"""

from __future__ import annotations

import grp
import os
import pwd
import shutil
import subprocess
import sys
from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Any

import yaml

from ._cli import PYOBSD_MODES, config_file_candidates

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
    """

    def __init__(
        self,
        options: SetupOptions,
        file_config: dict[str, Any],
        config_file: str = SETUP_CONFIG_FILE,
        interactive: bool | None = None,
        input_func: Callable[[str], str] = input,
    ):
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
        if mode == "systemd":
            raise SetupError("The systemd mode is not implemented in this version of pyobsd setup yet.")

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
        for key, default in _DIRECTORIES:
            sub = str(self._current.get(key, default)) if key else default
            self._plan_directory(plan, os.path.join(path, sub), user, group)

        # config file
        values = {"mode": mode, "chuid": chuid, "path": path, "syslog": bool(syslog), "file_log": bool(file_log)}
        self._plan_config_file(plan, values)

        # config files that hide ours, or that we hide
        self._check_shadowing(plan, user)
        return plan

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


# ── system helpers, patched in tests ──────────────────────────────────────────


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
    tmp = filename + ".tmp"
    with open(tmp, "w") as f:
        yaml.safe_dump(cfg, f, sort_keys=False, default_flow_style=False)
    os.chmod(tmp, 0o644)
    os.replace(tmp, filename)
