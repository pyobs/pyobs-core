# Plan: systemd mode for pyobsd

Status: in progress. Stop handling for the PID-file mode is released (pyobs-core 2.29.0/2.29.1, pyobs-web-admin
2.4.0). Mode switch, guard, `READY=1`, journal dedup, `pyobsd exec` and the exit code are merged (#1105, #1106,
#1107), `pyobsd setup` for the PID-file mode is in review. The systemd backend is not started. Scope for now:
pyobs-core only, the pyobs-web-admin part comes later.
Repos: pyobs-core, pyobs-web-admin

## Summary

Add a second mode to pyobsd that hands module processes to systemd system units running as the pyobs user,
instead of daemonizing `pyobs` with python-daemon and tracking PID files. Modules start on boot, get restarted
on failure, and their stdout/stderr (tracebacks before logging is up, crashes in C drivers) end up in the
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
  Plus `--mode` and `$PYOBSD_MODE` (#1105). web-admin reads the same key via `_pyobsd_config()` (it already
  does that for `syslog`).
- **System units, not user units** (ADR 0020). One template unit `/etc/systemd/system/pyobs@.service` with
  `User=`/`Group=` from `chuid`, one instance per module. No per-module unit files.
- **The instance is named after the active name** (`pyobs@foo` for both `foo.yaml` and `_foo.yaml`), like the
  PID and log files in PID-file mode (`_strip_disabled`). Renaming a config to disable it then does not change
  the unit name of a running module.
- **The filename is the only source of truth** for enabled/disabled: `foo.yaml` is enabled, `_foo.yaml` is
  disabled. A systemd generator turns that into the boot-time wants links. `systemctl enable`/`disable` is
  never used.
- **polkit, not sudo**, for the pyobs user: start, stop, restart and kill on `pyobs@*.service` only.
- **`pyobsd setup` installs, everybody else uses.** One new command, run as root, sets up a host for either
  mode: directories, user, `/etc/pyobs.yaml`, and in systemd mode unit, generator and polkit rule (see
  "pyobsd setup"). No other call writes outside the module directories: in systemd mode, pyobsd only compares
  the installed files and warns ("run pyobsd setup").
- Activate/deactivate stays a rename of the config file. The unit uses the hidden `pyobsd exec <module>`
  (#1106).
- **`pyobs --pid-file` refuses to start in systemd mode** (#1105).
- **web-admin calls `pyobsd`** through a new `PYOBSD_EXEC` setting (like `PYOBS_EXEC`), only in systemd mode.
  The PID-file code path in web-admin stays as it is. Deferred, see "pyobs-web-admin".

## Design

### Template unit

Rendered by pyobsd from its config (paths, user, group), roughly:

```ini
[Unit]
Description=pyobs module %i
Wants=network-online.target
After=network-online.target ejabberd.service
ConditionPathExists=|<config_path>/%i.yaml
ConditionPathExists=|<config_path>/_%i.yaml
StartLimitIntervalSec=300
StartLimitBurst=5

[Service]
Type=notify
NotifyAccess=main
User=<user>
Group=<group>
EnvironmentFile=-/etc/default/pyobs
WorkingDirectory=<run_path>
ExecStart=<pyobsd_exec> exec %i
Restart=on-failure
RestartSec=10
TimeoutStartSec=120
TimeoutStopSec=30
```

- No `[Install]` section, the generator creates the wants links (see "Enable state").
- `After=ejabberd.service`, without `Wants=`: on a host with a local ejabberd, modules start after it and stop
  before it, so on a reboot a camera keeps its XMPP connection during the warm-up and modules log out cleanly.
  On a host without it, `After=` does nothing. Whether ejabberd already accepts connections when systemd counts
  it as started depends on its unit type (not checked); the XMPP retry covers the gap. An `after:` list in the
  pyobsd config for other dependencies only if a host needs one.
- The two `ConditionPathExists=|` lines are ORed (`man systemd.unit`, "Conditions and Asserts"). They cover a
  module started by hand whose config was removed since.
- `User=`/`Group=` come from `chuid` (default `pyobs:pyobs`). systemd sets `HOME`, `USER` and `LOGNAME` for
  `User=` (`man systemd.exec`), so the module gets the same environment as with pyobsd's `Popen(user=...)`.
- `pyobsd exec <module>` looks up `<module>.yaml`, then `_<module>.yaml`, and `exec`s `pyobs` with the
  options from the pyobsd config. `exec` keeps the PID, so pyobs is the main process and `Type=notify` works.
- No `--pid-file`, so `pyobs` stays in the foreground.
- `Type=notify`: the module sends `READY=1` once it is open (#1106), and `EXTEND_TIMEOUT_USEC` is only
  documented for `Type=notify`/`notify-reload`.
- `Restart=on-failure` restarts after an error only: `pyobs` exits with 1 after an error and 0 after a normal
  stop, also by signal (#1107).
- `TimeoutStartSec=120` is set explicitly. See "Network at boot" for what happens when the XMPP server is down.
- `TimeoutStopSec=30` is the limit for modules that do not ask for more time. Modules with a long shutdown
  (cooled cameras) extend it themselves.
- Module names must be valid unit instance names without escaping (`[A-Za-z0-9_.-]`, plus `:`). pyobsd refuses
  others with an error, instead of escaping them (which the polkit rule and web-admin would then have to
  undo).

### Enable state: generator

A root-installed generator, `/etc/systemd/system-generators/pyobs-generator` (shell script, rendered by pyobsd
with the config path), runs at boot and on every `daemon-reload` (`man systemd.generator`). For every
`<config_path>/*.yaml` without a leading underscore and not ending in `.shared.yaml`, it creates
`<normal_dir>/multi-user.target.wants/pyobs@<name>.service` pointing to `/etc/systemd/system/pyobs@.service`.

- No `systemctl enable`/`disable`, so no privileges needed to change the enable state: renaming the config
  is enough. It takes effect at the next boot (or `daemon-reload`), which is the only time the wants links
  matter.
- Generators run very early at boot, before most file systems are mounted. The config directory has to be on
  the root file system. On all hosts checked, `/opt/pyobs` is.
- The script must be fast and must not fail: a missing config directory means no links.
- `pyobsd status` shows `enabled` from the filename, not from systemd (`UnitFileState` is `generated`, or
  empty for a disabled module).

### polkit rule

`/etc/polkit-1/rules.d/50-pyobs.rules`, rendered by pyobsd with the user name:

```js
polkit.addRule(function(action, subject) {
    if (action.id == "org.freedesktop.systemd1.manage-units" &&
        subject.user == "<user>" &&
        /^pyobs@[A-Za-z0-9_.:-]+\.service$/.test(action.lookup("unit") || "") &&
        ["start", "stop", "restart", "kill", "reset-failed"].indexOf(action.lookup("verb")) >= 0) {
        return polkit.Result.YES;
    }
});
```

- Checked on a host (systemd 257, polkitd 126, with a test unit and rule, as pyobs via `runuser` without a
  login session, like web-admin): start, restart, `kill -s SIGKILL`, reset-failed and `stop --no-block` on the
  matching unit were allowed. Denied: the same calls on a unit whose name doesn't match, verbs not in the list
  (`reload`, `freeze`), `daemon-reload`, `enable`, and everything once the rule was removed. So systemd passes
  `unit` and `verb`, and `kill`/`reset-failed` use those verb names. `polkit.log()` output did not show up in
  the journal (probably debug level only), so the values were only seen through allow/deny.
- `daemon-reload` and unit-file changes stay root-only.
- Needs polkitd, which is missing on most hosts so far (doc step).

### pyobsd setup

`pyobsd setup` sets up a host, for both modes. Run as root, idempotent, safe to re-run (e.g. after a pyobs-core
upgrade, to update the unit). It replaces the manual steps in `installing.rst` (`adduser`, `mkdir`, config
file).

**Questions**, each with the current value as default (from the active config file, else the built-in
default):

1. Mode: `pid` or `systemd` (default `pid`).
2. User and group (`chuid`, default `pyobs:pyobs`). If the user doesn't exist, offer to create it
   (`adduser --system --group --home <path> <user>`).
3. Base path (default `/opt/pyobs`).
4. Logging: journal (`syslog`, default on), log files in `log/` (`file_log`, default off).
5. systemd mode only: cooled cameras on this host? If yes, the shutdown timeout for reboots in minutes (default
   60).

Then a summary of every action, `Continue? [y/N]`, and only then changes.

**Unsupervised:** every question has a command line option, so `setup` can run without anyone answering
(deploy scripts):

| question | option |
|---|---|
| mode | `--mode pid\|systemd` |
| user and group | `--user <user>[:<group>]` |
| create a missing user | `--create-user` / `--no-create-user` |
| base path | `--path <dir>` |
| journal | `--syslog` / `--no-syslog` |
| log files | `--file-log` / `--no-file-log` |
| cooled cameras, shutdown timeout | `--shutdown-timeout <min>` / `--no-shutdown-timeout` |
| `Continue?` | `-y` |

- A question given as an option is not asked. With `-y`, or if stdin is not a terminal, nothing is asked:
  options not given take their default (current value, else built-in default), and the summary is printed
  but not confirmed.
- Exception: a missing user is never created without `--create-user`. Unsupervised, a missing user without
  that option is an error, before any change.
- Exit code 0 if everything is set up, 1 on an error, so a deploy script can check it. Warnings from the checks
  (polkitd, old `pyobs.service`, PID files) don't change the exit code, but `--strict` makes them errors.

**Actions, both modes:**

- Create the user, if confirmed.
- Create `<path>/config`, `log`, `run`, `storage` if missing, owned by the user and group. Existing
  directories keep their content; only a wrong owner on them is fixed.
- Write the answers into the `pyobsd` section of `/etc/pyobs.yaml`. A new file is just written. An existing
  file is rewritten with plain `yaml` (no `ruamel.yaml` dependency): other sections keep their values, the
  keys `setup` asks for are replaced in the `pyobsd` section, other keys there (e.g. `stop_timeout`) stay.
  Comments and formatting are lost, so before `Continue?` the summary warns about that and shows the diff of the
  values, and the old file is copied to `/etc/pyobs.yaml.bak` before writing.
- Warn if a config file earlier in the lookup order exists (`~/.config/pyobs.yaml` of root or of the user),
  since it would hide `/etc/pyobs.yaml`. `/opt/pyobs/storage/pyobs.yaml` comes after it, so its `pyobsd`
  section would be ignored; warn about that too.

**Actions, systemd mode only:**

1. Render unit, generator and polkit rule, compare each with the file on disk, write the ones that are missing
   or differ. If unit or generator changed, run `systemctl daemon-reload`.
2. Add the user to `systemd-journal` (needed for `pyobsd logs` and web-admin's log view as that user).
3. With a shutdown timeout: a drop-in raising `JobTimeoutSec` of `reboot.target` and `poweroff.target`.
4. Checks, no changes, each printing the command that fixes it: polkitd installed (`apt install polkitd`, not
   run by pyobsd), old `pyobs.service` still enabled, PID files of running modules from the old mode.

**Not done:** installing packages, installing pyobs itself, writing module configs.

**Other calls in systemd mode:** compare unit, generator and polkit rule with what `setup` would write, and warn
if something is missing or outdated. Commands that change state are refused by polkit for anyone but root and
the configured user; `status` and `list` work for everybody.

### Commands in systemd mode

| command | PID-file mode (unchanged) | systemd mode |
|---|---|---|
| `start [m...]` | spawn `pyobs --pid-file` | `systemctl start pyobs@m`; no args: all non-underscore modules |
| `stop [m...]` | SIGTERM, then SIGKILL | `systemctl stop pyobs@m`; no args: all active `pyobs@*` |
| `stop --kill` | SIGKILL | `systemctl kill -s SIGKILL pyobs@m` |
| `stop --no-wait` | SIGTERM only | `systemctl stop --no-block pyobs@m` |
| `restart [m...]` | stop, sleep, start | `systemctl restart pyobs@m` |
| `status [--json]` | PID files + psutil | `systemctl show -p ActiveState,SubState,MainPID,NRestarts pyobs@m...`, psutil on `MainPID` for uptime/rss/cpu |
| `list` | configs | unchanged |
| `logs` | journalctl | unchanged (same `SYSLOG_IDENTIFIER`/`PYOBS_MODULE` match) |

- Module names given as `_foo` map to the instance `pyobs@foo`. `pyobsd start _foo` starts it once, it does not
  start at boot.
- `systemctl start` blocks until `READY=1` or `TimeoutStartSec`, so a module that fails to open is reported as
  a failed start.
- `status --json`: keep the current top-level shape (`{module: {...}}`) so old consumers keep working.
  `state` (`running`/`stopping`/`stopped`) and `stop_deadline` already exist in both modes (#1096). Add `mode`
  and `enabled` per module, plus `restarts` (`NRestarts`) in systemd mode, and `failed` as an extra `state`
  value there (instead of `stopped`, for a unit that failed). Where `stop_deadline` comes from in systemd mode
  (or whether it stays `null`) is to be decided during implementation.
- `show` takes several units in one call, so status costs one `systemctl` call, not one per module.
- If PID files with live processes still exist in systemd mode (leftovers from the old mode), `status` lists
  them as `running (pid mode)` and prints a warning, so a half-migrated host is visible.

### Guard against PID-file starts

Done in #1105: `pyobs --pid-file` exits with an error if the config says `mode: systemd`, unless
`PYOBSD_MODE=pid`. pyobsd in PID-file mode sets that for the modules it starts. Not covered: a `pyobs` from an
older pyobs-core in another environment.

The config lookup depends on the user (`~/.config` first). Docs: put `mode` in `/etc/pyobs.yaml`, not in
root's or pyobs's own file, so pyobsd as root, pyobsd as pyobs and web-admin all see the same mode.

### Logging

Done in #1106: with `--syslog`, a module skips the stderr handler when stderr is the journal
(`$JOURNAL_STREAM` matches stderr's device and inode). Output written directly to stderr (uncaught tracebacks,
C libraries) still reaches the journal.

### Readiness (`READY=1`)

Done in #1106: `Application` sends `READY=1` after `startup()`. systemd counts the start as failed if it does
not arrive within `TimeoutStartSec` (`man systemd.service`). A module whose `open()` takes long (camera init)
can extend the start timeout with `EXTEND_TIMEOUT_USEC`. Since #1107, a module whose startup fails exits right
away with 1, so systemd sees the failure without waiting for the timeout.

### Stop timeout (both modes)

Done in #1096 for both modes. `CoolingRampMixin.close()` warms the sensor up before closing
(`cooling_warmup_on_close`, default on), which can take most of an hour from a low setpoint.

`pyobs.utils.shutdown.extend_stop_timeout(seconds)` is called once by `CoolingRampMixin.close()`, right before
the warm-up, with the full warm-up timeout plus a margin.

- **systemd mode** (`$NOTIFY_SOCKET` set): sends `EXTEND_TIMEOUT_USEC=<seconds * 1e6>`. Per `sd_notify(3)`
  (since systemd 236) the value is the window within which the next message has to arrive, so a single
  message with the full timeout covers the whole warm-up. The first one must arrive before `TimeoutStopSec`
  (30 s) runs out after SIGTERM. Checked: after SIGTERM, `Application` goes straight to `module.close()`, and
  in every camera using the mixin (asi, fli, flipro, qhyccd, sbig, dummy) the mixin's `close()` runs first.
  Before `extend_stop_timeout()` it only estimates the timeout, with at most two SDK reads, each limited to 5 s
  by the drivers. So about 10 s in the worst case.
- **old mode** (`--pid-file` given): writes the deadline to `<pid_file>.stopping`. pyobsd and web-admin wait
  while the process is alive and the deadline has not passed.
- Neither set (foreground run, tests): no-op.

On the first signal the module also starts a watchdog that ends the process after the deadline (or
`--stop-timeout`) plus 5 s. `Application` calls `shutdown.mark_stopping()` on SIGTERM (stop file in old
mode, `STOPPING=1` under systemd).

**Reboots:** with system units, the unit's own stop timeout applies on shutdown too, including the extension.
But `reboot.target` and `poweroff.target` have `JobTimeoutSec=30min` with a forced reboot/poweroff
(Debian 13, checked on a host). A reboot therefore cuts a warm-up after 30 min at the latest. On hosts with
cooled cameras, a drop-in can raise it (doc step). **Check** on a host: a reboot during a warm-up waits for it.

### Restart without warm-up: dropped

A restart runs the full warm-up (stop, then start). Skipping it was considered and dropped for now: the
warm-up on close exists because many SDKs switch the cooler off on close, so skipping it would cool down or
warm up the sensor abruptly. See `2026-11-11-shared-cooling-ramp.md`.

### Network at boot

`Wants=`/`After=network-online.target` orders the start after the network is up, as far as the host's network
setup reports it (ifupdown's `networking.service` waits for the `auto` interfaces only). The rest is covered
by `XmppComm.open()`, which waits for the server instead of exiting: slixmpp (1.17) retries a failed connect,
DNS errors included, with a backoff of up to 300 s, and `XmppComm._connect` waits for that in
`wait_connect()`. The module only quits on bad credentials or a JID conflict. Checked in the code, not tested
with the server down.

Since `READY=1` only comes after `open()`, a server that is down for longer than `TimeoutStartSec` makes
systemd count the start as failed, stop the module and start it again after `RestartSec`. That is one start
every ~130 s, so `StartLimitBurst=5` in 300 s is never reached and the module keeps trying until the server is
back. A module whose startup fails right away (bad config) hits the start limit after 5 tries and stays
`failed`.

### pyobs-web-admin (deferred)

Not part of the current scope. Until this is done, web-admin on a host in systemd mode cannot start modules:
its Start runs `pyobs --pid-file`, which the guard refuses.

In systemd mode (`_pyobsd_config().get("mode") == "systemd"`):

- `start_module`, `restart_module` run `PYOBSD_EXEC start|restart <name>` and return its exit code and
  output. `stop_module` uses `pyobsd stop --no-wait`.
- `get_module_status`, `get_module_stats` read `pyobsd status --json`, cached for one request/poll cycle so
  the module list does one subprocess call, not one per module.
- No version comparison: if web-admin is in systemd mode and the status JSON has no `mode` field, pyobsd on the
  host is too old. web-admin then shows an error ("systemd mode needs pyobs-core >= X") and refuses
  start/stop/restart.
- `activate_module` / `deactivate_module`: rename as today. That sets the boot behavior via the generator,
  nothing else to sync.
- `config_stale` and `get_module_versions` take PID and create time from the status JSON instead of the PID
  file.
- web-admin runs as the pyobs user, so the polkit rule covers it. No extra environment needed for `systemctl`
  (system bus).
- The PID-file code path stays as it is.

### Old `pyobs.service`

The system unit that runs `pyobsd start` (`Type=forking`) is not needed in systemd mode. It stays in the repo
for the PID-file mode. If a host has it installed, it has to be disabled when switching.

## Considered

User units under the pyobs user's own systemd instance, kept alive with linger. Dropped, see ADR 0020: without
linger they stop together with that instance, a reboot cuts a warm-up after 2 min, and they can't order after
`network-online.target`.

## Steps

- [x] pyobs-core: `sd_notify` helper, `extend_stop_timeout()` for both modes, `mark_stopping()` on SIGTERM
      (#1096).
- [x] pyobs-core, old mode: honor `<pid_file>.stopping` in pyobsd `stop`, `stop_timeout`, `--no-wait`,
      `stopping` state in `status` (#1096).
- [x] pyobs-core tests for the PID-file mode before refactoring (`tests/cli/test_pyobsd_pidmode.py`).
- [x] pyobs-web-admin, old mode: non-blocking stop, `stopping` state, kill, restart as a background job
      (2.4.0).
- [x] pyobs-core: `mode` config key, `--mode` option and `PYOBSD_MODE`, PID-file backend (#1105).
- [x] pyobs-core: guard in `PyobsCLI.run()` against `--pid-file` in systemd mode (#1105).
- [x] pyobs-core: `pyobsd exec <module>` (#1106).
- [x] pyobs-core: skip the stderr `StreamHandler` when `syslog` and `JOURNAL_STREAM` are set (#1106).
- [x] pyobs-core: send `READY=1` after the module is open (#1106).
- [x] pyobs-core: exit code 1 after an error, exit after a failed startup (#1107).
- [x] Check on a host: polkit gets `unit`/`verb` for `manage-units`, verbs of `kill`/`reset-failed`.
- [x] pyobs-core: `pyobsd setup` for both modes: questions and flags, user, directories, `/etc/pyobs.yaml`,
      shadowing config check; `installing.rst` uses it (own PR, before the systemd parts).
- [ ] pyobs-core: `pyobsd setup` in systemd mode: render and install unit, generator and polkit rule, journal
      group, shutdown drop-in, checks; other calls compare and warn.
- [ ] pyobs-core: systemd backend for start/stop/restart/kill/status, extended `status --json`, module name
      check.
- [ ] pyobs-core tests: setup (tmp dirs, mocked `adduser`/`systemctl`, answers via flags and stdin),
      rendering, generator script, status JSON parsing.
- [ ] pyobs-core docs: `cli.rst`, `installing.rst` (polkitd, journal group, where to put `mode`, shutdown
      drop-in, switching a host), CHANGELOG.
- [ ] Check on one host: comm reconnect at boot with the server down, journal without duplicates, reboot
      starts enabled modules only, reboot during a warm-up.
- [ ] Release pyobs-core.

Later:

- [ ] pyobs-web-admin: `PYOBSD_EXEC`, systemd-mode branch in `services.py`, `mode` check, tests.
- [ ] Release pyobs-web-admin.

## Switching a host

1. `pyobsd stop` (PID-file mode).
2. As root: `apt install polkitd` if missing.
3. `pyobsd setup`, answer `systemd` (and the shutdown timeout on hosts with cooled cameras). Disable the old
   `pyobs.service` if `setup` reports it.
4. `pyobsd start` (starts the enabled modules).
5. web-admin: until it supports systemd mode, its Start/Restart fail on this host (see the guard).

A new host: `pip install pyobs-core` (plus plugins), `pyobsd setup`, module configs into `config/`,
`pyobsd start`.

## Open questions

- Which other modules have a long shutdown and should call `extend_stop_timeout()`? Only `CoolingRampMixin` is
  known so far. Check pyftscontrol's `FTSControl.shutdown()` (called from pyobs-iagvt's `ftsraw` on close).
