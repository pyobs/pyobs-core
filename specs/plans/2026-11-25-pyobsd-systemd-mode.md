# Plan: systemd mode for pyobsd

Status: proposed
Repos: pyobs-core, pyobs-web-admin

## Summary

Add a second mode to pyobsd that hands module processes to systemd user units of the pyobs user, instead
of daemonizing `pyobs` with python-daemon and tracking PID files. Modules start on boot, get restarted on
failure, and their stdout/stderr (tracebacks before logging is up, crashes in C drivers) end up in the
journal. The old PID-file mode stays the default and is not changed. pyobs-web-admin calls `pyobsd` as a
subprocess in systemd mode instead of using its own process code, without depending on pyobs-core as a
Python package.

## Decisions

- **Mode switch** in the shared config file (`~/.config/pyobs.yaml`, `/etc/pyobs.yaml`,
  `/opt/pyobs/storage/pyobs.yaml`, first found wins, as today):
  ```yaml
  pyobsd:
    mode: systemd   # or "pid" (default)
  ```
  Plus a `--mode` CLI option like the other global keys. web-admin reads the same key via
  `_pyobsd_config()` (it already does that for `syslog`).
- **User units, not system units.** Units run under the pyobs user's own systemd manager, kept alive on boot
  with `loginctl enable-linger pyobs`. web-admin (`User=pyobs`) can then use `systemctl --user` without
  polkit or sudo.
- **One template unit** `~pyobs/.config/systemd/user/pyobs@.service`, one instance per module
  (`pyobs@<module>`). No per-module unit files.
- **The filename stays the source of truth** for enabled/disabled: `foo.yaml` is enabled, `_foo.yaml` is
  disabled. The systemd enable state follows it and is never edited on its own.
- **No new pyobsd commands.** Installing the unit and syncing enable state happen automatically on every
  pyobsd call in systemd mode (see below). Activate/deactivate stays a rename of the config file.
- **No `pyobs.target`.** Instances are `WantedBy=default.target`, so all enabled modules start on boot.
  "Start/stop all" is handled by pyobsd as today.
- **web-admin calls `pyobsd`** through a new `PYOBSD_EXEC` setting (like `PYOBS_EXEC`), only in
  systemd mode. The PID-file code path in web-admin stays as it is.

## Design

### Template unit

Rendered by pyobsd from its config (paths, log level, syslog), roughly:

```ini
[Unit]
Description=pyobs module %i
ConditionPathExists=<config_path>/%i.yaml
StartLimitIntervalSec=300
StartLimitBurst=5

[Service]
Type=exec
EnvironmentFile=-/etc/default/pyobs
WorkingDirectory=<run_path>
ExecStart=<pyobs_exec> --log-level <log_level> [--syslog] [--log-file <log_path>/%i.log] <config_path>/%i.yaml
Restart=on-failure
RestartSec=10
TimeoutStopSec=15

[Install]
WantedBy=default.target
```

- `ConditionPathExists` covers a config renamed in git with no pyobsd call before the next reboot: the
  still-enabled instance is skipped instead of failing.
- No `--pid-file`, so `pyobs` stays in the foreground (`pyobs/cli/pyobs.py:101`).
- `TimeoutStopSec=15` instead of the default 90 s. Today pyobsd sends SIGKILL after 5 s. 15 s gives
  modules more time for a clean shutdown. Open for discussion.
- `--log-file` with `%i`: for an underscore module started manually, the PID-file mode strips the
  underscore (`_strip_disabled`). Using `%i` directly would write `_foo.log`. Either accept that or render
  the file-log path differently. Decide during implementation.

### Automatic sync on every pyobsd call (systemd mode only)

1. Render the expected unit text, compare it with the file on disk. If it is missing or differs, write it
   and run `systemctl --user daemon-reload`. A new pyobs-core version or changed config then updates the
   unit on the next call.
2. Compare the non-underscore configs with the symlinks in
   `~pyobs/.config/systemd/user/default.target.wants/pyobs@*.service`. Run `systemctl --user enable` /
   `disable` only for differences. Reading the symlinks is only a directory listing, so this is cheap enough
   for web-admin's status polling.
3. Check that `/var/lib/systemd/linger/<user>` exists. If not, print a warning (enabling linger needs root
   and is a one-time setup step, see docs).

Writes only happen on a mismatch, and all steps are idempotent.

### Which user manager

- If pyobsd runs as the configured user (`chuid`, default `pyobs`): plain `systemctl --user`.
- If it runs as root (`sudo pyobsd`): `systemctl --user -M <user>@` and write the unit file into the
  user's home with the right owner. **Check:** `-M user@` for user managers needs systemd 248 or newer
  (not verified). Run `systemctl --version` on all hosts.
- Any other user: refuse with an error.

### Commands in systemd mode

| command | PID-file mode (unchanged) | systemd mode |
|---|---|---|
| `start [m...]` | spawn `pyobs --pid-file` | `systemctl --user start pyobs@m`; no args: all non-underscore modules |
| `stop [m...]` | SIGTERM, then SIGKILL | `systemctl --user stop pyobs@m`; no args: all active `pyobs@*` |
| `restart [m...]` | stop, sleep, start | `systemctl --user restart pyobs@m` |
| `status [--json]` | PID files + psutil | `systemctl --user show -p ActiveState,SubState,MainPID,UnitFileState,NRestarts pyobs@m`, psutil on `MainPID` for uptime/rss/cpu |
| `list` | configs | unchanged |
| `logs` | journalctl | unchanged (same `SYSLOG_IDENTIFIER`/`PYOBS_MODULE` match) |

- `status --json`: keep the current top-level shape (`{module: {...}}`) so old consumers keep working.
  Add `mode` and `enabled` per module, plus `restarts` (`NRestarts`) and `state` (`failed` vs
  `inactive`) in systemd mode.
- `show` takes several units in one call, so status costs one `systemctl` call, not one per module.
- If PID files with live processes still exist in systemd mode (leftovers from the old mode), `status`
  lists them as `running (pid mode)` and prints a warning, so a half-migrated host is visible.

### Logging

`setup_logging` in `pyobs/application.py` always adds a stderr `StreamHandler`. Under systemd, stderr goes
to the journal, so with `--syslog` every line would be in the journal twice (once tagged with
`PYOBS_MODULE`, once untagged from stderr). Fix in pyobs-core: if `syslog` is on and `JOURNAL_STREAM` is
set (systemd sets it when stdout/stderr go to the journal, see `man systemd.exec`), skip the
`StreamHandler`. Output written directly to stderr (uncaught tracebacks, C libraries) still reaches the
journal via the unit's stderr stream, which is the point.

### Network at boot

User units cannot order themselves after system targets like `network-online.target`. First check whether
the XMPP comm reconnects on its own if the server is not reachable at startup. If it does, nothing else is
needed. If the module exits instead, `Restart=on-failure` covers it. Only if neither is enough, add an
optional `ExecStartPre=` (`nm-online -s -q --timeout=60` or
`/usr/lib/systemd/systemd-networkd-wait-online --timeout=60`) via a key in the pyobsd config.

### pyobs-web-admin

In systemd mode (`_pyobsd_config().get("mode") == "systemd"`):

- `start_module`, `stop_module`, `restart_module` run `PYOBSD_EXEC start|stop|restart <name>` and
  return its exit code and output.
- `get_module_status`, `get_module_stats` read `pyobsd status --json`, cached for one request/poll
  cycle so the module list does one subprocess call, not one per module.
- `activate_module` / `deactivate_module`: rename as today, then call `pyobsd status` (or stop first, as
  today) so the enable state is synced right away.
- `config_stale` and `get_module_versions` take PID and create time from the status JSON instead of the
  PID file.
- `deploy/pyobs-web-admin.service`: add `Environment=XDG_RUNTIME_DIR=/run/user/<uid>` so
  `systemctl --user` reaches the pyobs user manager from gunicorn. **Check** whether that alone is
  enough or `DBUS_SESSION_BUS_ADDRESS` is also needed.
- The PID-file code path stays as it is. Moving it to pyobsd as well is a possible later step, not part
  of this plan.

### Old `pyobs.service`

The system unit that runs `pyobsd start` (`Type=forking`) is not needed in systemd mode. Doc change only:
disable it when switching a host. It stays in the repo for the PID-file mode.

## Steps

- [ ] pyobs-core: `mode` config key and `--mode` option, mode-specific backends in `pyobsd.py`
      (current code moves into the PID-file backend without behavior changes).
- [ ] pyobs-core: unit rendering, unit file sync, enable sync, linger check, user manager selection.
- [ ] pyobs-core: systemd backend for start/stop/restart/status, extended `status --json`.
- [ ] pyobs-core: skip the stderr `StreamHandler` when `syslog` and `JOURNAL_STREAM` are set.
- [ ] pyobs-core tests: unit rendering, sync (tmp dirs, mocked `systemctl`), status JSON parsing, PID-file
      mode unchanged (`tests/cli/test_pyobsd.py` has only 4 tests today, so add tests for the old mode
      before refactoring).
- [ ] pyobs-core docs: `cli.rst`, `installing.rst` (linger, switching a host), CHANGELOG.
- [ ] Check on one host: systemd version, comm reconnect at boot, journal without duplicates, reboot
      starts enabled modules only.
- [ ] Release pyobs-core.
- [ ] pyobs-web-admin: `PYOBSD_EXEC`, systemd-mode branch in `services.py`, deploy unit env, tests.
- [ ] Release pyobs-web-admin, switch hosts one by one.

## Switching a host

1. `pyobsd stop` (PID-file mode).
2. `loginctl enable-linger pyobs` (as root).
3. Set `mode: systemd` in the pyobsd config, disable the old `pyobs.service`.
4. `pyobsd start` (installs the unit, enables the instances, starts them).
5. Restart pyobs-web-admin.

## Open questions

- `TimeoutStopSec` value (15 s proposed).
- File-log name for underscore modules started manually (`%i` vs stripped name).
- Does web-admin need a version check on pyobsd (e.g. refuse systemd mode if `status --json` has no
  `mode` field), or is "systemd mode requires pyobs-core >= X" in the docs enough?
