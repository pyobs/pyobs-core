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
Type=notify
NotifyAccess=main
EnvironmentFile=-/etc/default/pyobs
WorkingDirectory=<run_path>
ExecStart=<pyobs_exec> --log-level <log_level> [--syslog] [--log-file <log_path>/%i.log] <config_path>/%i.yaml
Restart=on-failure
RestartSec=10
TimeoutStopSec=30

[Install]
WantedBy=default.target
```

- `ConditionPathExists` covers a config renamed in git with no pyobsd call before the next reboot: the
  still-enabled instance is skipped instead of failing.
- No `--pid-file`, so `pyobs` stays in the foreground (`pyobs/cli/pyobs.py:101`).
- `Type=notify`, because `EXTEND_TIMEOUT_USEC` is only documented for `Type=notify`/`notify-reload`
  (see "Stop timeout" below). `NotifyAccess=main` is implied by `Type=notify`, but set explicitly.
- `TimeoutStopSec=30` is the limit for modules that do not ask for more time. Modules with a long
  shutdown (cooled cameras) extend it themselves.
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
  user's home with the right owner. I believe `-M user@` for user managers needs systemd 248 or newer
  (not verified against the changelog). All checked hosts run 257, see "Hosts".
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
  `state` (`running`/`stopping`/`stopped`) and `stop_deadline` already exist in both modes (PR #1096).
  Add `mode` and `enabled` per module, plus `restarts` (`NRestarts`) in systemd mode, and `failed` as an
  extra `state` value there (instead of `stopped`, for a unit that failed).
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

### Readiness (`READY=1`)

With `Type=notify`, systemd waits for `READY=1` and counts the start as failed if it does not arrive
within `TimeoutStartSec` (`man systemd.service`, `TimeoutStartSec=`). `Application` sends `READY=1` once
the module is open. `systemctl start` then only succeeds if the module actually came up. A module whose
`open()` takes long (camera init) can extend the start timeout with the same `EXTEND_TIMEOUT_USEC`
message.

### Stop timeout (both modes)

`CoolingRampMixin.close()` warms the sensor up before closing (`cooling_warmup_on_close`, default on),
with a timeout estimated from the current setpoint (`pyobs/mixins/coolingramp.py:168`): from -20 degC at
1 degC/min about 49 min. Today pyobsd and web-admin send SIGKILL 5 s after SIGTERM, so a stop through either
of them kills a camera in the middle of its warm-up. This affects asi, fli, flipro, qhyccd and dummycamera,
and needs fixing in the old mode too.

New helper in pyobs-core, e.g. `pyobs.utils.shutdown.extend_stop_timeout(seconds)`, called by
`CoolingRampMixin.close()` (and by any other module with a long shutdown). One call is enough: `close()`
computes the full warm-up timeout before it starts waiting (`pyobs/mixins/coolingramp.py:143-148`), so it
calls `extend_stop_timeout(timeout + margin)` once, right before `asyncio.wait_for`.

- **systemd mode** (`$NOTIFY_SOCKET` set): sends `EXTEND_TIMEOUT_USEC=<seconds * 1e6>`. Per `sd_notify(3)`
  (since systemd 236) the value is the window within which the next message has to arrive, so a single
  message with the full timeout covers the whole warm-up. The first one must arrive before
  `TimeoutStopSec` (30 s) runs out after SIGTERM. **Check:** that nothing else in a module's shutdown runs
  before the mixin's `close()` and takes longer than that. Plain AF_UNIX datagram socket, a leading `@`
  means abstract namespace, so no libsystemd dependency is needed.
- **old mode** (`--pid-file` given): writes the deadline to `<pid_file>.stopping`, as wall-clock epoch
  seconds (not `time.monotonic()`, since another process reads it). pyobsd and web-admin wait while the
  process is alive and the deadline has not passed, and only send SIGKILL after that. Without the file
  they keep a short default (made configurable, e.g. `stop_timeout` in the pyobsd config, default 30 s).
- Neither set (foreground run, tests): no-op.

How the helper gets the PID file path: `PyobsCLI` passes its whole config, `pid_file` included, into
`Application(**kwargs)` (`pyobs/cli/pyobs.py:80`). `Application` hands it to a module-level setting in the
helper, so the mixin calls the helper without knowing about `Application`. In systemd mode the helper only
needs `$NOTIFY_SOCKET` from the environment.

Cleanup: `Application.run()` removes `<pid_file>.stopping` at the end of its shutdown, and pyobsd removes it
together with the PID file once the process is gone. A file left behind by a crashed module is ignored once
its deadline has passed (and a crashed module is not alive, so nothing waits for it anyway).

**`pyobsd restart` in old mode blocks** for the whole stop, so on a camera up to the full warm-up. That is
fine for the CLI, as long as pyobsd prints how long it will wait (e.g. "camera is shutting down, waiting up
to 48 min") instead of hanging silently.

**web-admin stop must not block.** A stop can take close to an hour, which a gunicorn worker cannot wait
for. In both modes web-admin sends the stop (`systemctl --user stop --no-block`, or SIGTERM), returns
immediately, and shows the module as `stopping` until it is gone (systemd: `ActiveState=deactivating`;
old mode: process alive and `.stopping` file present). The SIGKILL after the deadline then happens on the
next status poll in old mode.

**`stopping` state (done in PR #1096, pyobsd side).** `Application` calls `shutdown.mark_stopping()` on
SIGTERM: it writes "now" as the deadline (or keeps a later one), which extends nothing but marks every
stopping module, not only those that asked for more time, and sends `STOPPING=1` under systemd.
`pyobsd status` shows `stopping` plus the remaining time, `status --json` has `state` and `stop_deadline`
and keeps `running: true` while the process is alive. web-admin should read `state`, show `stopping` in
the list, disable start while stopping, and maybe offer "kill now" for a module that hangs.

**web-admin restart must not block either**, and it cannot simply return early, since the start has to
wait for the stop. In systemd mode `systemctl --user restart --no-block` does that. In old mode web-admin
runs the restart as a background job, the same way package updates already run (detached process, lock
file, status: `update_package_start` in `modules/services.py`).

**Reboots:** the user manager itself is stopped with `user@.service`'s `TimeoutStopUSec`, 2 min on ms.
A reboot therefore still cuts the warm-up after 2 min, unless each host gets a root drop-in for
`user@<uid>.service` with a longer `TimeoutStopSec`. Doc step, part of switching a host.

### Restart without warm-up: dropped

A restart runs the full warm-up (stop, then start). Skipping it was considered (SIGUSR1 for restart, a
restart flag on `Module.quit()`, `RestartForceExitStatus=` in the unit) and dropped for now: the warm-up
on close exists because many SDKs switch the cooler off on close, so skipping it would cool down or warm
up the sensor abruptly. That is only safe for cameras whose cooler keeps running after close, which is
still open per vendor (see `2026-11-11-shared-cooling-ramp.md`).

### Network at boot

User units cannot order themselves after system targets like `network-online.target`. All hosts except
iag50cam use ifupdown (no NetworkManager, no networkd), so `nm-online` / `systemd-networkd-wait-online` in
an `ExecStartPre=` would not help there. First check whether the XMPP comm reconnects on its own if the
server is not reachable at startup. If it does, nothing else is needed. If the module exits instead,
`Restart=on-failure` covers it.

### pyobs-web-admin

In systemd mode (`_pyobsd_config().get("mode") == "systemd"`):

- `start_module`, `restart_module` run `PYOBSD_EXEC start|restart <name>` and return its exit code
  and output. `stop_module` does not wait (see "Stop timeout"), so pyobsd `stop` needs a non-blocking
  variant for this (e.g. a `--no-wait` option, not a new command).
- `get_module_status`, `get_module_stats` read `pyobsd status --json`, cached for one request/poll
  cycle so the module list does one subprocess call, not one per module.
- `activate_module` / `deactivate_module`: rename as today, then call `pyobsd status` (or stop first, as
  today) so the enable state is synced right away.
- `config_stale` and `get_module_versions` take PID and create time from the status JSON instead of the
  PID file.
- `deploy/pyobs-web-admin.service`: add `Environment=XDG_RUNTIME_DIR=/run/user/<uid>` so
  `systemctl --user` reaches the pyobs user manager from gunicorn. The pyobs uid differs per host
  (1000, 1001, 702234), so `deploy.sh` has to fill it in. **Check** whether that alone is enough or
  `DBUS_SESSION_BUS_ADDRESS` is also needed.
- The PID-file code path stays as it is. Moving it to pyobsd as well is a possible later step, not part
  of this plan.

### Old `pyobs.service`

The system unit that runs `pyobsd start` (`Type=forking`) is not needed in systemd mode. It stays in the
repo for the PID-file mode. It is not installed on any of the checked hosts, so nothing to disable there.

### Hosts (checked 2026-11-25)

| host | systemd | pyobs uid | linger | web-admin | modules running | network |
|---|---|---|---|---|---|---|
| ms (monet.monets) | 257 | 1000 | no | active | 15 | ifupdown |
| mn (monet.monetn) | 257 | 1000 | no | inactive | 0 | ifupdown |
| iag50srv | 257 | 1001 | no | active | 14 | ifupdown |
| iagvtsrv | 257 | 702234 | no | active | 10 | ifupdown, pyobs in `/usr/bin` |
| iag50cam | 257 | 1000 | no | active | 1 | NetworkManager |

All Debian 13, persistent journal, old `pyobs.service` not installed. Not checked: astro159 (ssh key
rejected), cloudcover and musegc (timeout), siderostat-mini (only offers ssh-rsa/ssh-dss host keys).
labcourse has no pyobs.

## Steps

- [ ] pyobs-core: `mode` config key and `--mode` option, mode-specific backends in `pyobsd.py`
      (current code moves into the PID-file backend without behavior changes).
- [ ] pyobs-core: unit rendering, unit file sync, enable sync, linger check, user manager selection.
- [ ] pyobs-core: systemd backend for start/stop/restart/status, extended `status --json`.
- [ ] pyobs-core: skip the stderr `StreamHandler` when `syslog` and `JOURNAL_STREAM` are set.
- [ ] pyobs-core: `sd_notify` helper (no libsystemd), `READY=1` after open, `extend_stop_timeout()` for
      both modes (PID file path passed in by `Application`), called once from `CoolingRampMixin.close()`
      before the warm-up, `.stopping` removed at the end of `Application.run()`.
- [ ] pyobs-core, old mode: honor `<pid_file>.stopping` in pyobsd `stop`, configurable `stop_timeout`
      instead of the fixed 5 s, `--no-wait` for `stop`, `restart` prints how long it waits. Adapt
      `test_stop_kills_after_timeout` in `tests/cli/test_pyobsd_pidmode.py`.
- [x] pyobs-core tests for the PID-file mode before refactoring (`tests/cli/test_pyobsd_pidmode.py`, e9a0084a).
- [ ] pyobs-core tests: unit rendering, sync (tmp dirs, mocked `systemctl`), status JSON parsing.
- [ ] pyobs-core docs: `cli.rst`, `installing.rst` (linger, switching a host), CHANGELOG.
- [ ] Check on one host: systemd version, comm reconnect at boot, journal without duplicates, reboot
      starts enabled modules only.
- [ ] Release pyobs-core.
- [ ] pyobs-web-admin, old mode: non-blocking stop, `stopping` state, SIGKILL only after the
      `.stopping` deadline or `stop_timeout`, restart as a background job.
- [ ] pyobs-web-admin: `PYOBSD_EXEC`, systemd-mode branch in `services.py`, deploy unit env, tests.
- [ ] Release pyobs-web-admin, switch hosts one by one.

## Switching a host

1. `pyobsd stop` (PID-file mode).
2. `loginctl enable-linger pyobs` (as root). On hosts with cooled cameras, also a drop-in for
   `user@<uid>.service` with a longer `TimeoutStopSec`, so a reboot does not cut the warm-up.
3. Set `mode: systemd` in the pyobsd config, disable the old `pyobs.service`.
4. `pyobsd start` (installs the unit, enables the instances, starts them).
5. Restart pyobs-web-admin.

## Open questions

- File-log name for underscore modules started manually (`%i` vs stripped name).
- Does web-admin need a version check on pyobsd (e.g. refuse systemd mode if `status --json` has no
  `mode` field), or is "systemd mode requires pyobs-core >= X" in the docs enough?
- Is mn expected to have no modules and no web-admin running?
- Which other modules have a long shutdown and should call `extend_stop_timeout()` (telescope or dome
  parking on close?). Not checked.
