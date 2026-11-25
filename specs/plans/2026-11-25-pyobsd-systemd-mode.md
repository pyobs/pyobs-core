# Plan: systemd mode for pyobsd

Status: in progress. Stop handling for the PID-file mode is released (pyobs-core 2.29.0/2.29.1, pyobs-web-admin
2.4.0). The systemd mode itself is not started. Scope for now: pyobs-core only, the pyobs-web-admin part comes
later.
Repos: pyobs-core, pyobs-web-admin

## Summary

Add a second mode to pyobsd that hands module processes to systemd user units of the pyobs user, instead
of daemonizing `pyobs` with python-daemon and tracking PID files. Modules start on boot, get restarted on
failure, and their stdout/stderr (tracebacks before logging is up, crashes in C drivers) end up in the
journal. The old PID-file mode stays the default and is not changed. pyobs-web-admin will call `pyobsd` as a
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
- **One template unit** `~pyobs/.config/systemd/user/pyobs@.service`, one instance per module. No per-module
  unit files.
- **The instance is named after the active name** (`pyobs@foo` for both `foo.yaml` and `_foo.yaml`), like the
  PID and log files in PID-file mode (`_strip_disabled`). Renaming a config to disable it then does not change
  the unit name of a running module.
- **The filename stays the source of truth** for enabled/disabled: `foo.yaml` is enabled, `_foo.yaml` is
  disabled. The systemd enable state follows it and is never edited on its own.
- **No new user-facing pyobsd commands.** Installing the unit and syncing enable state happen automatically on
  every pyobsd call in systemd mode (see below). Activate/deactivate stays a rename of the config file. The unit
  uses a hidden `pyobsd exec <module>` (see "Template unit").
- **No `pyobs.target`.** Instances are `WantedBy=default.target`, so all enabled modules start on boot.
  "Start/stop all" is handled by pyobsd as today.
- **`pyobs --pid-file` refuses to start in systemd mode**, see "Guard against PID-file starts".
- **web-admin calls `pyobsd`** through a new `PYOBSD_EXEC` setting (like `PYOBS_EXEC`), only in
  systemd mode. The PID-file code path in web-admin stays as it is. Deferred, see "pyobs-web-admin".

## Design

### Template unit

Rendered by pyobsd from its config (paths, log level, syslog), roughly:

```ini
[Unit]
Description=pyobs module %i
ConditionPathExists=|<config_path>/%i.yaml
ConditionPathExists=|<config_path>/_%i.yaml
StartLimitIntervalSec=300
StartLimitBurst=5

[Service]
Type=notify
NotifyAccess=main
EnvironmentFile=-/etc/default/pyobs
WorkingDirectory=<run_path>
ExecStart=<pyobsd_exec> exec %i
Restart=on-failure
RestartSec=10
TimeoutStartSec=120
TimeoutStopSec=30

[Install]
WantedBy=default.target
```

- The two `ConditionPathExists=|` lines are ORed (`man systemd.unit`, "Conditions and Asserts"). They cover a
  config removed in git with no pyobsd call before the next reboot: the still-enabled instance is skipped
  instead of failing.
- `pyobsd exec <module>` looks up `<module>.yaml`, then `_<module>.yaml`, and `exec`s `pyobs` with the
  options from the pyobsd config (`--log-level`, `--syslog`, `--log-file <log_path>/<module>.log`,
  `--stop-timeout`). `exec` keeps the same PID, so pyobs is the main process and `Type=notify` works. The
  lookup lives next to `_strip_disabled` and can be tested, instead of a `sh -c` in the unit. Cost: pyobsd's
  own startup time on every module start.
- No `--pid-file`, so `pyobs` stays in the foreground (`pyobs/cli/pyobs.py`).
- `Type=notify`, because `EXTEND_TIMEOUT_USEC` is only documented for `Type=notify`/`notify-reload`
  (see "Stop timeout" below). `NotifyAccess=main` is implied by `Type=notify`, but set explicitly.
- `TimeoutStartSec=120` is set explicitly, so it does not depend on the default of the user manager (90 s
  unless changed). See "Network at boot" for what happens when the XMPP server is down.
- `TimeoutStopSec=30` is the limit for modules that do not ask for more time. Modules with a long
  shutdown (cooled cameras) extend it themselves.

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
  user's home with the right owner. I believe `-M user@` for user managers needs systemd 248 or newer
  (not verified against the changelog). Debian 13 ships 257.
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

- Module names given as `_foo` map to the instance `pyobs@foo`. `pyobsd start _foo` starts it without
  enabling it.
- `status --json`: keep the current top-level shape (`{module: {...}}`) so old consumers keep working.
  `state` (`running`/`stopping`/`stopped`) and `stop_deadline` already exist in both modes (PR #1096).
  Add `mode` and `enabled` per module, plus `restarts` (`NRestarts`) in systemd mode, and `failed` as an
  extra `state` value there (instead of `stopped`, for a unit that failed).
- `show` takes several units in one call, so status costs one `systemctl` call, not one per module.
- If PID files with live processes still exist in systemd mode (leftovers from the old mode), `status`
  lists them as `running (pid mode)` and prints a warning, so a half-migrated host is visible.

### Guard against PID-file starts

On a host in systemd mode, anything that still starts modules the old way (an old web-admin, an old pyobsd, a
manual `pyobs --pid-file`) would start a second process next to `pyobs@foo`. Both log in with the same JID, and
the one that gets kicked with `conflict` shuts down.

So `PyobsCLI.run()` checks, before `_start_daemon`: if `pid_file` is set and the pyobsd config says
`mode: systemd`, exit with an error like "this host runs pyobs modules under systemd (pyobsd mode: systemd),
use pyobsd start <module>". `pyobs` and `pyobsd` already read the same file in `CLI._load_config`
(`pyobs/cli/_cli.py`), each only its own section today. The guard reads `pyobsd.mode` from it, with a helper
shared with pyobsd.

- The unit starts `pyobs` without `--pid-file`, so the guard does not affect systemd mode itself.
- `PYOBSD_MODE=pid` in the environment overrides the config, to test the PID-file mode on a systemd host.
  `_load_env` only covers the reading CLI's own keys, so pyobs checks this one explicitly.
- Not covered: a `pyobs` from an older pyobs-core in another environment. systemd mode needs a current
  pyobs-core on the host anyway.
- The config lookup depends on the user (`~/.config` first). Docs: put `mode` in `/etc/pyobs.yaml` or in the
  pyobs user's file, not in root's, so `sudo pyobsd`, pyobsd as the pyobs user and web-admin all see the same
  mode.

### Logging

`setup_logging` in `pyobs/application.py` always adds a stderr `StreamHandler`. Under systemd, stderr goes
to the journal, so with `--syslog` every line would be in the journal twice (once tagged with
`PYOBS_MODULE`, once untagged from stderr). Fix in pyobs-core: if `syslog` is on and `JOURNAL_STREAM` is
set (systemd sets it when stdout/stderr go to the journal, see `man systemd.exec`), skip the
`StreamHandler`. Output written directly to stderr (uncaught tracebacks, C libraries) still reaches the
journal via the unit's stderr stream, which is the point.

### Readiness (`READY=1`)

With `Type=notify`, systemd waits for `READY=1` and counts the start as failed if it does not arrive
within `TimeoutStartSec` (`man systemd.service`, `TimeoutStartSec=`). `Application` sends `READY=1` once
the module is open. `systemctl start` then only succeeds if the module actually came up. A module whose
`open()` takes long (camera init) can extend the start timeout with the same `EXTEND_TIMEOUT_USEC`
message.

### Stop timeout (both modes)

Done in #1096 for both modes. `CoolingRampMixin.close()` warms the sensor up before closing
(`cooling_warmup_on_close`, default on), which can take most of an hour from a low setpoint.

`pyobs.utils.shutdown.extend_stop_timeout(seconds)` is called once by `CoolingRampMixin.close()`, right before
the warm-up, with the full warm-up timeout plus a margin.

- **systemd mode** (`$NOTIFY_SOCKET` set): sends `EXTEND_TIMEOUT_USEC=<seconds * 1e6>`. Per `sd_notify(3)`
  (since systemd 236) the value is the window within which the next message has to arrive, so a single
  message with the full timeout covers the whole warm-up. The first one must arrive before
  `TimeoutStopSec` (30 s) runs out after SIGTERM. Checked: after SIGTERM, `Application` goes straight to
  `module.close()`, and in every camera using the mixin (asi, fli, flipro, qhyccd, sbig, dummy) the mixin's
  `close()` runs first. Before `extend_stop_timeout()` it only estimates the timeout, with at most two SDK
  reads, each limited to 5 s by the drivers. So about 10 s in the worst case. Plain AF_UNIX datagram socket, a
  leading `@` means abstract namespace, so no libsystemd dependency is needed.
- **old mode** (`--pid-file` given): writes the deadline to `<pid_file>.stopping`, as wall-clock epoch
  seconds. pyobsd and web-admin wait while the process is alive and the deadline has not passed, and only send
  SIGKILL after that. Without the file they use `stop_timeout` (default 30 s).
- Neither set (foreground run, tests): no-op.

On the first signal the module also starts a watchdog that ends the process after the deadline (or
`--stop-timeout`) plus 5 s, so a hanging shutdown ends even when nobody waits to send SIGKILL. `Application`
calls `shutdown.mark_stopping()` on SIGTERM, which marks every stopping module (stop file in old mode,
`STOPPING=1` under systemd). `pyobsd status` shows `stopping` with the remaining time.

**Reboots:** the user manager itself is stopped with `user@.service`'s `TimeoutStopUSec` (2 min by default).
A reboot therefore still cuts the warm-up after 2 min, unless the host gets a root drop-in for
`user@<uid>.service` with a longer `TimeoutStopSec`. Doc step, part of switching a host with cooled cameras.

### Restart without warm-up: dropped

A restart runs the full warm-up (stop, then start). Skipping it was considered (SIGUSR1 for restart, a
restart flag on `Module.quit()`, `RestartForceExitStatus=` in the unit) and dropped for now: the warm-up
on close exists because many SDKs switch the cooler off on close, so skipping it would cool down or warm
up the sensor abruptly. That is only safe for cameras whose cooler keeps running after close, which is
still open per vendor (see `2026-11-11-shared-cooling-ramp.md`).

### Network at boot

User units cannot order themselves after system targets like `network-online.target`, and hosts with ifupdown
have no wait-online tool for an `ExecStartPre=`. Not needed: `XmppComm.open()` waits for the server instead of
exiting. slixmpp (1.17) retries a failed connect, DNS errors included, with a backoff of up to 300 s
(`reschedule_connection_attempt`), and `XmppComm._connect` waits for that in `wait_connect()`. The module only
quits on bad credentials or a JID conflict. Checked in the code, not tested with the server down.

Since `READY=1` only comes after `open()`, a server that is down for longer than `TimeoutStartSec` makes
systemd count the start as failed, stop the module and start it again after `RestartSec`. That is one start
every ~130 s, so `StartLimitBurst=5` in 300 s is never reached and the module keeps trying until the server is
back.

### pyobs-web-admin (deferred)

Not part of the current scope. Until this is done, web-admin on a host in systemd mode cannot start modules:
its Start runs `pyobs --pid-file`, which the guard refuses.

In systemd mode (`_pyobsd_config().get("mode") == "systemd"`):

- `start_module`, `restart_module` run `PYOBSD_EXEC start|restart <name>` and return its exit code
  and output. `stop_module` uses `pyobsd stop --no-wait` (exists since #1096).
- `get_module_status`, `get_module_stats` read `pyobsd status --json`, cached for one request/poll
  cycle so the module list does one subprocess call, not one per module.
- No version comparison: if web-admin is in systemd mode and the status JSON has no `mode` field, pyobsd on the
  host is too old. web-admin then shows an error ("systemd mode needs pyobs-core >= X") and refuses
  start/stop/restart.
- `activate_module` / `deactivate_module`: rename as today, then call `pyobsd status` (or stop first, as
  today) so the enable state is synced right away.
- `config_stale` and `get_module_versions` take PID and create time from the status JSON instead of the
  PID file.
- `deploy/pyobs-web-admin.service`: add `Environment=XDG_RUNTIME_DIR=/run/user/<uid>` so
  `systemctl --user` reaches the pyobs user manager from gunicorn. The pyobs uid differs per host, so
  `deploy.sh` has to fill it in. **Check** whether that alone is enough or `DBUS_SESSION_BUS_ADDRESS` is also
  needed.
- The PID-file code path stays as it is (done in 2.4.0: `stopping` state, non-blocking stop, kill, restart as a
  detached job).

### Old `pyobs.service`

The system unit that runs `pyobsd start` (`Type=forking`) is not needed in systemd mode. It stays in the
repo for the PID-file mode. If a host has it installed, it has to be disabled when switching.

## Steps

- [x] pyobs-core: `sd_notify` helper (no libsystemd, `pyobs.utils.shutdown`), `extend_stop_timeout()` for
      both modes, called once from `CoolingRampMixin.close()` before the warm-up, `.stopping` removed at the
      end of `Application.run()`, `mark_stopping()` on SIGTERM (#1096).
- [x] pyobs-core, old mode: honor `<pid_file>.stopping` in pyobsd `stop`, configurable `stop_timeout`
      instead of the fixed 5 s, `--no-wait` for `stop`, `restart` prints how long it waits, `stopping`
      state in `status` (#1096).
- [x] pyobs-core tests for the PID-file mode before refactoring (`tests/cli/test_pyobsd_pidmode.py`, e9a0084a).
- [x] pyobs-web-admin, old mode: non-blocking stop, `stopping` state, kill, restart as a background job
      (2.4.0).
- [ ] pyobs-core: `mode` config key, `--mode` option and `PYOBSD_MODE`, mode-specific backends in `pyobsd.py`
      (current code moves into the PID-file backend without behavior changes).
- [ ] pyobs-core: guard in `PyobsCLI.run()` against `--pid-file` in systemd mode, sharing the mode lookup with
      pyobsd.
- [ ] pyobs-core: `pyobsd exec <module>` (config lookup by active name, options from the pyobsd config).
- [ ] pyobs-core: unit rendering, unit file sync, enable sync, linger check, user manager selection.
- [ ] pyobs-core: systemd backend for start/stop/restart/status, extended `status --json`.
- [ ] pyobs-core: skip the stderr `StreamHandler` when `syslog` and `JOURNAL_STREAM` are set.
- [ ] pyobs-core: send `READY=1` after the module is open (systemd mode only).
- [ ] pyobs-core tests: unit rendering, sync (tmp dirs, mocked `systemctl`), status JSON parsing, guard,
      `exec` lookup.
- [ ] pyobs-core docs: `cli.rst`, `installing.rst` (linger, where to put `mode`, reboot drop-in, switching a
      host), CHANGELOG.
- [ ] Check on one host: comm reconnect at boot with the server down, journal without duplicates, reboot
      starts enabled modules only.
- [ ] Release pyobs-core.

Later:

- [ ] pyobs-web-admin: `PYOBSD_EXEC`, systemd-mode branch in `services.py`, `mode` check, deploy unit env,
      tests.
- [ ] Release pyobs-web-admin.

## Switching a host

1. `pyobsd stop` (PID-file mode).
2. `loginctl enable-linger pyobs` (as root). On hosts with cooled cameras, also a drop-in for
   `user@<uid>.service` with a longer `TimeoutStopSec`, so a reboot does not cut the warm-up.
3. Set `mode: systemd` in the pyobsd config (`/etc/pyobs.yaml` or the pyobs user's file), disable the old
   `pyobs.service` if installed.
4. `pyobsd start` (installs the unit, enables the instances, starts them).
5. web-admin: until it supports systemd mode, its Start/Restart fail on this host (see the guard).

## Open questions

- Which other modules have a long shutdown and should call `extend_stop_timeout()`? Only `CoolingRampMixin` is
  known so far. No telescope parks on close. Check pyftscontrol's `FTSControl.shutdown()` (called from
  pyobs-iagvt's `ftsraw` on close).
