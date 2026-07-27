# Finding a specific module's logs on a `pyobsd`-managed host

`journalctl -u <module-name>` does not work against a `pyobsd`-managed deployment — not even
`journalctl -u pyobsd` itself. Use `pyobsd logs <module>` instead (or the raw `journalctl` fields
it wraps, below), not `-u`.

## Why `-u` doesn't work

`pyobsd` (`pyobs/cli/pyobsd.py`) runs each configured module as its own OS process
(`_start_service`, `pyobsd.py:318-341`), spawned via `subprocess.Popen(..., start_new_session=True)`
— deliberately detached from `pyobsd`'s own process group. Neither `pyobsd` nor the individual
modules are registered as systemd units; there is no unit named `mastermind`, `telescope`, or
`pyobsd` for `-u` to match against.

`journalctl -u <name>` filters on `_SYSTEMD_UNIT`, which is one of journald's **trusted fields**:
populated by journald itself from the kernel/cgroup metadata of the process that submitted the
message, precisely so a process can't spoof which unit it belongs to. A client (including pyobs's
own logging handler) cannot set `_SYSTEMD_UNIT` directly — journald ignores/overrides any
underscore-prefixed field a client tries to supply. If the writing process was never launched as a
systemd unit in the first place, `_SYSTEMD_UNIT` is simply absent, and no `-u` value will ever
match it.

## What actually identifies a module in the journal

Instead, `pyobs` tags every log record with its own **untrusted** (freely settable) journald
fields, via `PyobsJournaldLogHandler` (`pyobs/application.py:110-133`), active whenever a module is
started with `syslog=True` (`pyobsd`'s own default — `pyobsd.py:55`, `default=... True`):

- `SYSLOG_IDENTIFIER=pyobs` — constant, set in the handler's `__init__` (`application.py:122-123`).
- `PYOBS_MODULE=<module-name>` — per-record, injected by `PyobsJournaldLogHandler._format_record`
  (`application.py:125-128`) from the `pyobs_module` context var/log-record attribute that
  `ModuleNameFilter` stamps onto every record.

## How to actually query it

`pyobsd` already wraps this — use it instead of raw `journalctl`:

```
pyobsd logs <module> [journalctl-args...]
```

(`pyobsd.py:301-314` — it execs into `journalctl SYSLOG_IDENTIFIER=pyobs PYOBS_MODULE=<module>
<your extra args>`, e.g. `pyobsd logs mastermind -f` or `pyobsd logs mastermind --since ... --until
...`.)

Equivalent raw form, if `pyobsd` isn't on hand:

```
journalctl SYSLOG_IDENTIFIER=pyobs PYOBS_MODULE=<module-name> --since ... --until ...
```

`_COMM`/`_PID` (also trusted, but populated regardless of systemd-unit status) are a fallback if
you know the actual process — e.g. `ps aux | grep pyobsd` — but they identify a *process*, not a
module, and one module's own code paths (e.g. a robotic script class run inline by a task runner)
can legitimately share a PID with the module that invoked it.

## If real `-u` support is ever wanted

`_SYSTEMD_UNIT` can only ever reflect genuine systemd/cgroup membership, never be set by the app.
To make `-u` work, something has to actually put each module under systemd's management:

- Give each module (or `pyobsd` itself) a real unit/service file, or
- Wrap the launch in a transient scope, e.g. `systemd-run --scope --unit=mastermind pyobsd ...`,
  so systemd creates a real cgroup for it.

Neither is in place today; `PYOBS_MODULE=`/`pyobsd logs` is the practical path until one is.

## How this was found

Surfaced 2026-07-24 while triaging a `mastermind` task failure relayed to Matrix: the underlying
`log.exception()` call (`pyobs/modules/robotic/mastermind.py:177`) was initially assumed missing
locally because `journalctl -u mastermind`/`-u robotic` came back empty, which briefly looked like
evidence of a second, unmanaged scheduler process. It wasn't — the log was there all along, just
findable only via `PYOBS_MODULE=mastermind`.
