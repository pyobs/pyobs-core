"""pyobsd's systemd mode: every module is an instance of the template unit ``pyobs@.service``.

The unit, the generator for the boot-time links and the polkit rule come from ``pyobsd setup``. Here, pyobsd only
calls ``systemctl`` on ``pyobs@<module>.service``, as root or as the user the polkit rule allows. See
specs/plans/2026-11-25-pyobsd-systemd-mode.md.
"""

from __future__ import annotations

import glob
import json
import os
import re
import subprocess
import sys
import time
from typing import Any

import psutil

from pyobs.utils.shutdown import parse_status_deadline

from ._systemd_files import MODULE_NAME_PATTERN
from .pyobsd import _KILL_WAIT_SECONDS, PyobsDaemonBase

UNIT_TEMPLATE = "pyobs@{}.service"
UNIT_GLOB = "pyobs@*.service"

# properties read by status, in one "systemctl show" call for all units
_SHOW_PROPERTIES = ["Id", "ActiveState", "SubState", "MainPID", "NRestarts", "StatusText", "Result"]


class SystemdDaemon(PyobsDaemonBase):
    """systemd mode: runs modules as instances of pyobs@.service and asks systemd for their state."""

    # ── helpers ───────────────────────────────────────────────────────────────

    @classmethod
    def _unit(cls, module: str) -> str:
        """The unit of a module, named after its active name, so that renaming the config doesn't change it."""
        return UNIT_TEMPLATE.format(cls._strip_disabled(module))

    @staticmethod
    def _module_of_unit(unit: str) -> str:
        return unit.removeprefix("pyobs@").removesuffix(".service")

    @staticmethod
    def _valid_name(module: str) -> bool:
        return re.fullmatch(MODULE_NAME_PATTERN, module) is not None

    def _systemctl(self, *args: str, capture: bool = False) -> subprocess.CompletedProcess[str]:
        cmd = ["systemctl", *args]
        if self._verbose:
            print(f"[DEBUG] Executing: {' '.join(cmd)}")
        try:
            return subprocess.run(cmd, capture_output=capture, text=True)
        except FileNotFoundError:
            self._error("systemctl not found, the systemd mode needs systemd.")
            raise

    def _show(self, units: list[str]) -> dict[str, dict[str, str]]:
        """Properties of the units, by unit name."""
        if not units:
            return {}
        out = self._systemctl("show", "-p", ",".join(_SHOW_PROPERTIES), "--", *units, capture=True)
        result: dict[str, dict[str, str]] = {}
        # one block per unit, separated by empty lines
        for block in out.stdout.strip().split("\n\n"):
            props = dict(line.split("=", 1) for line in block.splitlines() if "=" in line)
            if "Id" in props:
                result[props["Id"]] = props
        return result

    def _active_units(self) -> list[str]:
        """pyobs units that are running, starting or stopping."""
        out = self._systemctl(
            "list-units",
            "--plain",
            "--no-legend",
            "--state=active,activating,deactivating,reloading",
            UNIT_GLOB,
            capture=True,
        )
        return sorted(line.split()[0] for line in out.stdout.splitlines() if line.strip())

    def _pid_mode_pids(self) -> dict[str, int]:
        """Modules still running with a PID file from the PID-file mode, by active name."""
        pids = {}
        for pid_file in glob.glob(os.path.join(self._run_path, "*.pid")):
            try:
                with open(pid_file) as f:
                    pid = int(f.read().strip())
            except (OSError, ValueError):
                continue
            if psutil.pid_exists(pid):
                pids[self._module(pid_file)] = pid
        return pids

    def _resolve(self, modules: list[str]) -> list[str]:
        """Config names for the given names ("foo" or "_foo"), exits for an unknown or invalid one."""
        resolved = []
        for name in modules:
            module = self._find_config(name)
            if module is None:
                self._error(f"Module {name!r} does not exist.")
                raise SystemExit(1)
            if not self._valid_name(self._strip_disabled(module)):
                self._error(f"Module name {module!r} can't be a unit name, use only letters, digits and _.:-")
            resolved.append(module)
        return resolved

    def _enabled_modules(self) -> list[str]:
        """All modules without a leading underscore, skipping (with a warning) names that can't be unit names."""
        modules = []
        for module in self._list_configs():
            if module.startswith("_"):
                continue
            if not self._valid_name(module):
                print(f"Skipping {module!r}: not a valid unit name, use only letters, digits and _.:-", file=sys.stderr)
                continue
            modules.append(module)
        return modules

    def _units_or_active(self, modules: list[str] | None) -> list[str]:
        """Units of the given modules, or all active pyobs units."""
        if modules:
            return [self._unit(m) for m in self._resolve(modules)]
        return self._active_units()

    def _refuse_pid_mode(self, modules: list[str]) -> None:
        """Exits if one of the modules still runs in PID-file mode, so it can't run twice."""
        pid_mode = self._pid_mode_pids()
        running = [m for m in modules if self._strip_disabled(m) in pid_mode]
        if running:
            self._error(
                f"Still running in PID-file mode: {', '.join(running)}. Stop first: pyobsd --mode pid stop "
                + " ".join(running)
            )

    # ── public commands ───────────────────────────────────────────────────────

    def start(self, modules: list[str] | None = None, wait: bool = True) -> None:
        modules = self._resolve(modules) if modules else self._enabled_modules()
        if not modules:
            print("No modules to start.")
            return
        self._refuse_pid_mode(modules)

        units = [self._unit(m) for m in modules]
        states = self._show(units)
        to_start = []
        for module, unit in zip(modules, units):
            if states.get(unit, {}).get("ActiveState") in ("active", "reloading"):
                print(f"{module} already running.")
            else:
                to_start.append(unit)
        if not to_start:
            return

        # after 5 failed starts in 5 min, systemd refuses every start until the counter is reset, also a manual one
        failed = [u for u in to_start if states.get(u, {}).get("ActiveState") == "failed"]
        if failed:
            self._systemctl("reset-failed", "--", *failed)

        # one call for all, like at boot: systemd starts them in parallel and returns once all sent READY=1, or
        # with --no-block once the jobs are queued (then a failing start shows only in status and logs)
        print(f"Starting {', '.join(self._module_of_unit(u) for u in to_start)}...")
        args = ["start"] if wait else ["start", "--no-block"]
        if self._systemctl(*args, "--", *to_start).returncode != 0:
            failed = [
                self._module_of_unit(u)
                for u, props in self._show(to_start).items()
                if props.get("ActiveState") != "active"
            ]
            names = ", ".join(failed) if failed else "some modules"
            self._error(f"Could not start {names}, see: pyobsd logs <module>")

    def stop(self, modules: list[str] | None = None, wait: bool = True) -> None:
        units = self._units_or_active(modules)
        if not units:
            return
        print(f"Stopping {', '.join(self._module_of_unit(u) for u in units)}...")
        args = ["stop"] if wait else ["stop", "--no-block"]
        try:
            result = self._systemctl(*args, "--", *units)
        except KeyboardInterrupt:
            # the stop job runs in systemd, not here
            print("\nStopped waiting.")
            for unit in units:
                print(f'{self._module_of_unit(unit)} keeps shutting down in the background, see "pyobsd status".')
            sys.exit(130)
        if result.returncode != 0:
            sys.exit(1)

    def kill(self, modules: list[str] | None = None) -> None:
        """SIGKILL right away, then a stop, so that Restart=on-failure doesn't start the module again."""
        units = self._units_or_active(modules)
        if not units:
            return
        states = self._show(units)
        running = [u for u in units if states.get(u, {}).get("MainPID", "0") != "0"]
        for unit in units:
            if unit not in running:
                print(f"{self._module_of_unit(unit)} is not running.")
        if not running:
            return

        print(f"Killing {', '.join(self._module_of_unit(u) for u in running)}...")
        self._systemctl("kill", "-s", "SIGKILL", "--", *running)
        self._systemctl("stop", "--no-block", "--", *running)

        # SIGKILL can't end a process stuck in the kernel until that call returns
        deadline = time.time() + _KILL_WAIT_SECONDS
        alive = running
        while alive and time.time() < deadline:
            time.sleep(0.2)
            states = self._show(alive)
            alive = [u for u in alive if states.get(u, {}).get("ActiveState") not in ("inactive", "failed")]
        for unit in alive:
            pid = states.get(unit, {}).get("MainPID", "?")
            name = self._module_of_unit(unit)
            print(f"{name} (PID {pid}) is still alive after SIGKILL, probably stuck in a driver call.")
        if alive:
            sys.exit(1)
        # SIGKILL leaves the unit "failed", but it was stopped on purpose
        self._systemctl("reset-failed", "--", *running)

    def restart(self, modules: list[str] | None = None, kill: bool = False, wait: bool = True) -> None:
        if kill:
            # kill() waits until they are gone (a few seconds at most), so the start can't cancel a stop job
            self.kill(modules=modules)
            self.start(modules=modules, wait=wait)
            return
        if not modules:
            # like the PID-file mode: all running ones stop, then all enabled ones start
            if wait:
                self.stop()
                self.start()
            else:
                self._restart_all_no_wait()
            return

        resolved = self._resolve(modules)
        self._refuse_pid_mode(resolved)
        units = [self._unit(m) for m in resolved]
        print(f"Restarting {', '.join(self._module_of_unit(u) for u in units)}...")
        args = ["restart"] if wait else ["restart", "--no-block"]
        if self._systemctl(*args, "--", *units).returncode != 0:
            self._error("Could not restart all modules, see: pyobsd logs <module>")

    def _restart_all_no_wait(self) -> None:
        """restart() without names and without waiting. A stop and then a start without waiting would queue a
        start job that cancels the stop job of the same unit, so: running and enabled ones restart, running and
        disabled ones stop, the other enabled ones start."""
        enabled = {self._unit(m): m for m in self._enabled_modules()}
        self._refuse_pid_mode(list(enabled.values()))
        active = self._active_units()
        to_stop = [u for u in active if u not in enabled]
        to_restart = [u for u in active if u in enabled]
        to_start = [m for u, m in enabled.items() if u not in active]
        if to_stop:
            # by unit, its config may be gone
            print(f"Stopping {', '.join(self._module_of_unit(u) for u in to_stop)}...")
            if self._systemctl("stop", "--no-block", "--", *to_stop).returncode != 0:
                self._error("Could not stop all modules, see: pyobsd logs <module>")
        if to_restart:
            print(f"Restarting {', '.join(self._module_of_unit(u) for u in to_restart)}...")
            if self._systemctl("restart", "--no-block", "--", *to_restart).returncode != 0:
                self._error("Could not restart all modules, see: pyobsd logs <module>")
        if to_start:
            self.start(to_start, wait=False)

    def _known_modules(self) -> list[str]:
        """All configs, plus active units without a config (renamed or removed since)."""
        configs = self._list_configs()
        by_active = {self._strip_disabled(m): m for m in configs}
        active = {self._module_of_unit(u) for u in self._active_units()}
        return sorted(set(configs) | {by_active.get(m, m) for m in active})

    def _known_units(self, modules: list[str]) -> dict[str, str]:
        """Units of the given modules by module, skipping names that can't be unit names."""
        return {m: self._unit(m) for m in modules if self._valid_name(self._strip_disabled(m))}

    def status(self, print_json: bool = False, cpu_interval: float | None = None) -> None:
        configs = self._list_configs()
        by_active = {self._strip_disabled(m): m for m in configs}
        modules = self._known_modules()
        units = self._known_units(modules)
        props = self._show(list(units.values()))

        # leftovers from the PID-file mode
        pid_mode = self._pid_mode_pids()
        for name in pid_mode:
            module = by_active.get(name, name)
            if module not in modules:
                modules.append(module)
        modules.sort()
        if pid_mode:
            print(
                f"Warning: still running in PID-file mode: {', '.join(sorted(pid_mode))}. Stop them: pyobsd --mode pid "
                "stop",
                file=sys.stderr,
            )

        entries: dict[str, dict[str, Any]] = {}
        for module in modules:
            entry: dict[str, Any] = {"mode": "systemd", "enabled": not module.startswith("_") and module in configs}
            pid_mode_pid = pid_mode.get(self._strip_disabled(module))
            unit = units.get(module)
            p = props.get(unit, {}) if unit else {}
            pid = int(p.get("MainPID", "0") or 0)

            if pid == 0 and pid_mode_pid is not None:
                entry.update(mode="pid", running=True, state="running", stop_deadline=None, pid=pid_mode_pid)
            else:
                entry.update(self._state(p, pid))
                entry["restarts"] = int(p.get("NRestarts", "0") or 0)
            if unit is None:
                entry["error"] = "not a valid unit name"
            entries[module] = entry

        pids = [e["pid"] for e in entries.values() if e.get("running")]
        cpu_by_pid = self._sample_cpu_percent(pids, cpu_interval) if cpu_interval else {}
        for entry in entries.values():
            if entry.get("running"):
                entry["cpu"] = cpu_by_pid.get(entry["pid"])
                entry.update(self._process_info(entry["pid"]))

        if print_json:
            print(json.dumps(entries))
            return

        now = time.time()
        print(f"{'module':<30}  {'status':<8}  {'uptime':>12}  {'cpu':>6}  {'rss':>8}")
        print("-" * 72)
        for module, e in entries.items():
            if not e.get("running"):
                state = e["state"] + (f" ({e['error']})" if "error" in e else "")
                state += " (restarting)" if e.get("restarting") else ""
                state += f"  ({e['restarts']} restarts)" if e.get("restarts") else ""
                print(f"{module:<30}  {state:<8}")
                continue
            cpu = e.get("cpu")
            cpu_str = f"{cpu:>5.1f}%" if cpu is not None else f"{'-':>6}"
            state = e["state"] if e["mode"] == "systemd" else "running (pid mode)"
            extra = ""
            deadline = e.get("stop_deadline")
            if deadline is not None and deadline > now:
                extra += f"  (up to {self._fmt_wait(deadline - now)})"
            if e.get("restarts"):
                extra += f"  ({e['restarts']} restarts)"
            print(
                f"{module:<30}  {state:<8}  {self._fmt_uptime(e['uptime']):>12}  {cpu_str}  {e['rss_mb']:>6.1f} MB"
                f"{extra}"
            )

    @staticmethod
    def _state(props: dict[str, str], pid: int) -> dict[str, Any]:
        """running/state/stop_deadline/pid from a unit's properties."""
        active = props.get("ActiveState", "inactive")
        deadline = None
        if active == "deactivating":
            state = "stopping"
            deadline = parse_status_deadline(props.get("StatusText", ""))
        elif active == "activating" and props.get("SubState") == "auto-restart":
            # failed, systemd starts it again after RestartSec
            state = "failed"
        elif active == "activating":
            state = "starting"
        elif active in ("active", "reloading"):
            state = "running"
        elif active == "failed":
            state = "failed"
        else:
            state = "stopped"
        result: dict[str, Any] = {"running": pid != 0, "state": state, "stop_deadline": deadline}
        if active == "activating" and props.get("SubState") == "auto-restart":
            result["restarting"] = True
        if pid:
            result["pid"] = pid
        return result

    def logs(self, args: list[str]) -> None:
        """journalctl for the units: includes everything the module wrote to stdout/stderr, not only its log."""
        remainder = list(args)
        if remainder and remainder[0] == "--":
            remainder.pop(0)
        if remainder and self._find_config(remainder[0]) is not None:
            units = [self._unit(remainder.pop(0))]
        else:
            # one -u per unit, not UNIT_GLOB: journalctl matches a glob against every unit in the journal, which
            # takes seconds to minutes on a large journal (#1122)
            units = list(dict.fromkeys(self._known_units(self._known_modules()).values()))
            if not units:
                self._error("No modules.")
        cmd = ["journalctl", *(a for u in units for a in ("-u", u)), *remainder]
        if self._verbose:
            print(f"[DEBUG] Executing: {' '.join(cmd)}")
        os.execvp("journalctl", cmd)
