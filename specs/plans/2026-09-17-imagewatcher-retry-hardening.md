# Plan: Harden ImageWatcher's retry behavior

Status: implemented, closed — landed on `develop` in `061d4f78`. Two departures from this doc's
design as written: (a) `error_after` ended up keyword-only (Python requires either `*` or a
default after params that have defaults), documented in the constructor docstring rather than in
the signature alone; (b) it was initially left with **no default** as designed below, but that
broke every deployed `ImageWatcher` config on upgrade (`TypeError: missing ... 'error_after'`) —
see "Post-implementation follow-up" at the end, which added a 1800s default and made the param
optional.
Issues: none — found by inspection while reviewing `ImageWatcher` at Tim's request.

## Problem

`pyobs/modules/image/imagewatcher.py`'s `_worker` (lines 194-283) has two failure modes with
opposite, both-wrong behavior:

1. **Destination-write / `process_extra` failures** (`imagewatcher.py:255-269`) retry forever, on a
   fixed `wait_time` interval, with no logging above `WARNING` and no cap. A destination that's
   down for a day produces a day of `WARNING`s and never surfaces as an actionable alert.
2. **Everything else** — reading the source file (line 209), `vfs.remove` returning falsy having
   already thrown, `cleanup_extra` raising — is caught by the outer `except Exception: log.exception
   ("Something went wrong.")` at line 282, logged, and **dropped**: no re-queue, so a single
   transient read glitch (e.g. NFS hiccup, file briefly locked) loses the file's processing
   permanently.

## Goal

- Bound the destination-write retry loop: keep retrying (these repos copy to remote destinations —
  `pyobs-archive`, NFS mounts — whose realistic downtime isn't known ahead of time and varies by
  deployment), back off instead of hammering every `wait_time`, and log `ERROR` exactly once per
  failure episode once it's been failing long enough to be worth alerting on (this is exactly the
  kind of module-`ERROR` event `pyobs.modules.utils.PushNotifier`
  (`specs/design/push-notification-module.md`) now surfaces fleet-wide).
- Never truly give up / never move files to a `failed/` dir — mark failure state internally instead
  (in-memory, keyed by filename), so nothing needs manual recovery and there's no VFS-`move`-doesn't-
  exist or watcher-re-detects-the-failed-dir landmine (see prior discussion in this conversation).
- Fix the opposite bug: give read failures the same bounded-retry treatment instead of dropping the
  file on the first transient error.
- Distinguish terminal from transient failures by exception type (not by read-vs-write call site —
  `watchpath` goes through the same VFS abstraction as destinations, so a read failure isn't
  reliably more "permanent" than a write failure; what's actually predictable is the exception
  type). A terminal failure logs `ERROR` immediately and is never re-queued; a transient one gets
  the bounded-backoff-forever treatment above.

## Considered options

**Give-up threshold: attempt count vs. elapsed time.** A fixed `max_retries` count is meaningless
here because the retry interval itself grows (backoff) — the wall-clock time to reach N attempts
depends on the backoff shape, and how long a destination can legitimately be down varies by
deployment (no real number to bake in). **Chosen: elapsed time since first failure**
(`error_after: int`, required with no default as first shipped — see below and the follow-up
section at the end) — directly expresses "alert once this has
been broken longer than a normal transient outage for this deployment," independent of backoff
shape. Attempt count is still tracked (for the backoff exponent and for log context) but doesn't
drive the alert decision.

**Where retry state lives.** Considered widening the queue tuple to `(filename, ready_at, attempt)`.
Rejected: breaks every existing test that destructures `_queue.get_nowait()` as a 2-tuple
(`tests/modules/image/test_imagewatcher.py` — a dozen+ call sites), for no benefit, since we also
need `first_failed_at` and `alerted` alongside `attempt`, which doesn't fit a queue tuple cleanly
anyway. **Chosen:** a small `_RetryState` dataclass in a new `self._retry: dict[str, _RetryState]`,
keyed by filename, populated on first failure and popped on success. Queue stays a 2-tuple,
unchanged.

**Unifying the two failure sites.** The write-loop's own `try/except` (lines 252-258) and the
`process_extra` bool-check (261-263) currently build the retry re-queue inline; the outer
`except Exception` (282) does something different (log-and-drop) for everything else. Extracting
the whole per-file body into `_process_file(filename)` — which either returns normally or raises —
lets `_worker` own a single retry/success decision, instead of three separate sites with different
behavior. `process_extra() -> False` becomes `raise RuntimeError(...)` inside `_process_file` so it
funnels through the same path as a real exception.

**Terminal vs. transient classification.** By exception type, not call site: `FileNotFoundError`,
`PermissionError`, `IsADirectoryError` are terminal wherever they occur (deleted file, wrong
permissions — no amount of retrying fixes either, whether hit reading `watchpath` or writing a
destination); everything else (`OSError`, timeouts, connection errors) is treated as transient
wherever it occurs. This is deliberately coarse — some `OSError` subtypes (e.g. an NFS stale file
handle) aren't unambiguously one or the other — but it's a real, inspectable signal, unlike
call-site, which isn't. `_handle_failure` needs the actual exception object (not just `str(e)`) to
classify it, so `_process_file`'s caller passes `e`, not `str(e)`.

**`cleanup_extra` / `vfs.remove` after a successful transfer — deliberately *not* folded into the
retry loop.** By the time `cleanup_extra` runs, the file has already been removed from the watch
directory and copied to every destination. Re-queueing on a `cleanup_extra` failure would re-run
the *entire* pipeline — re-reading a file that's already gone (guaranteed read failure) and
re-writing already-successfully-written destinations — which is actively wrong, not just wasteful.
**Decision:** keep `vfs.remove` failure as today (log `WARNING`, continue — non-fatal, file stays in
place for whatever removed it to retry) and give `cleanup_extra` exceptions their own `try/except`
that logs `ERROR` immediately with no retry, instead of falling into the generic outer catch that
currently swallows it as `WARNING`-equivalent (`log.exception` without an explicit level reads as
error-ish already, but it's undifferentiated from every other failure — this makes the
non-retryable case explicit and visible).

## Decision

### 1. `_RetryState` and constructor params — `imagewatcher.py`

```python
@dataclass
class _RetryState:
    attempts: int = 0
    first_failed_at: float = field(default_factory=time.time)
    alerted: bool = False
```

New `__init__` params:

- `error_after: int = 1800` — seconds a file may keep failing before the one-time `ERROR` log.
  Originally shipped with **no default** on the reasoning that every deployment's destinations
  (`pyobs-archive`, an NFS mount, whatever else) have different realistic outage windows; that
  proved wrong in practice — see "Post-implementation follow-up" at the end.
- `backoff_cap: int = 3600` — max seconds between retries (1h).

`self._retry: dict[str, _RetryState] = {}`

### 2. Extract `_process_file`, simplify `_worker`

```python
async def _worker(self) -> None:
    while True:
        filename, ready_at = await self._queue.get()
        wait = ready_at - time.time()
        if wait > 0:
            await asyncio.sleep(wait)
        log.info("Working on file %s...", filename)
        try:
            await self._process_file(filename)
        except Exception as e:
            self._handle_failure(filename, e)
        else:
            self._retry.pop(filename, None)
```

`_process_file(filename)` is today's per-file body (read → fits parse → per-destination
write/`process_extra` → remove → `cleanup_extra`), with:

- the inner `try/except` around the destination write (lines 252-258) removed — the exception now
  propagates naturally to `_worker`'s `except`, which is the only place that decides retry-vs-not;
- `if not await self.process_extra(filename): raise RuntimeError(f"process_extra rejected {filename}")`
  replacing the `success = False; break` dance;
- the post-remove `cleanup_extra` call wrapped in its own `try/except Exception: log.error(...)`
  that does **not** re-raise (see "deliberately not folded in" above) — a `cleanup_extra` failure
  is logged and the file stays processed (removed from watch dir, copied to destinations).

### 3. `_handle_failure` — the unified retry/alert decision

```python
_TERMINAL_EXCEPTIONS = (FileNotFoundError, PermissionError, IsADirectoryError)


def _handle_failure(self, filename: str, exc: Exception) -> None:
    if isinstance(exc, self._TERMINAL_EXCEPTIONS):
        log.error("Giving up on %s, unrecoverable error: %s", filename, exc)
        self._retry.pop(filename, None)
        return  # not re-queued -- watch modes only ever re-detect a file that's new/changed

    state = self._retry.setdefault(filename, _RetryState())
    state.attempts += 1
    elapsed = time.time() - state.first_failed_at
    delay = min(self._wait_time * 2**state.attempts, self._backoff_cap)
    if elapsed >= self._error_after and not state.alerted:
        log.error(
            "Still failing on %s after %.0fs of retries (attempt %d): %s",
            filename, elapsed, state.attempts, exc,
        )
        state.alerted = True
    else:
        log.warning("Retrying %s (attempt %d, next in %ds): %s", filename, state.attempts, delay, exc)
    self._queue.put_nowait((filename, time.time() + delay))
```

For a terminal failure, the file is left exactly where it is in `watchpath` (never removed, never
re-queued) — inotify won't re-fire on it (no new `CLOSE_WRITE` event) and poll mode won't pick it
up again either (it's not "new" in the next scan's diff), so it stays visibly present as a stuck
file rather than vanishing, without looping forever trying to fix something retrying can't fix.

Retry state resets naturally on module restart (in-memory only) — `open()`'s existing directory
rescan re-adds any file still sitting in `watchpath`, starting a fresh `_RetryState`. If the
underlying problem is still broken, it re-fails and re-alerts on its own schedule; this is
considered correct (a restart is a legitimate new observation point), not a bug to guard against.

## Tests

### Existing coverage that needs updating, not just re-run

- Every `_worker` test in `tests/modules/image/test_imagewatcher.py` (lines 109, 134, 158, 191,
  233, 270, 298, 338, 403, 430, +more) pre-seeds the queue with a 2-tuple and drives `_worker()`
  directly — unaffected by the queue-shape decision above (still a 2-tuple), but several construct
  failure scenarios (e.g. line 298's `/watch/corrupt.fits`) whose current assertion is probably
  "file dropped, not re-queued" or "no re-queue call" — these need updating to assert a re-queue
  with backoff instead, once the behavior changes.
- Any test currently asserting on the outer `except Exception: log.exception("Something went
  wrong.")` log line specifically will need updating for the new `_handle_failure` log format.

### New tests required

- `_handle_failure`: attempt count increments, delay follows `min(wait_time * 2**attempts,
  backoff_cap)`, `ERROR` fires exactly once when `elapsed >= error_after` (not on every subsequent
  retry), `state.alerted` prevents a second `ERROR` for the same episode.
- Success after failure clears `self._retry[filename]` — reprocess the same filename successfully
  and assert it's popped (next failure on that filename starts `attempts` back at 1, not continuing
  the old count).
- Read failure (`vfs.open_file` raising a transient `OSError` on the read side) now re-queues
  instead of dropping — direct regression test for the bug that started this.
- Terminal exceptions (`FileNotFoundError`/`PermissionError`/`IsADirectoryError`) are not re-queued
  regardless of which phase raises them — test at least one from the read side and one from the
  write side, to lock in that classification is by type, not call site. Assert `ERROR` is logged
  immediately (not gated on `error_after`) and `self._retry` has no entry left for that filename.
- `cleanup_extra` raising: file is NOT re-queued (assert `_queue` empty after), `ERROR` is logged,
  and — importantly — confirm the file was already removed from the watch dir / copied to
  destinations before `cleanup_extra` ran (i.e., this isn't treated as a processing failure).
- `pyrefly` check on the touched file (this repo uses `ruff`/`pyrefly`, not `mypy`).

## Consequences

- **Good:** the two known-wrong failure modes (unbounded silent retry, zero-retry drop) both get
  fixed with one mechanism instead of two patches.
- **Good:** matches the existing `PushNotifier`/module-`ERROR` alerting path Tim just shipped — the
  one-time `ERROR` log is exactly the signal that pipeline is designed to catch, so this gets fleet
  alerting on stuck `ImageWatcher` destinations for free, no new wiring.
- **Neutral:** `error_after` is keyword-only and (since the follow-up below) optional, defaulting to
  1800s; a config that wants a tighter or looser alert threshold sets it explicitly. `backoff_cap`
  keeps a default (1h) since it's a cap, not a deployment-specific alert threshold.
- **Risk:** `_retry` is unbounded in principle (one entry per currently-failing filename) — not a
  real concern at expected scale (a handful of files failing at once, not thousands), but worth a
  one-line note if it's ever pointed at a much higher-throughput watch directory.
- **Risk:** the terminal-exception list is a coarse, hardcoded guess (`FileNotFoundError`/
  `PermissionError`/`IsADirectoryError`) — an exception type we didn't anticipate but that's
  actually permanent (e.g. a malformed `pattern`-driven destination path that always raises the
  same `ValueError`) still gets the transient bounded-retry-forever treatment. Acceptable since the
  cost of misclassifying transient-as-terminal (silently stuck file, no more retries) is worse than
  misclassifying terminal-as-transient (wasted retries, but still alerted via `error_after`).
- **Out of scope:** `vfs.remove` returning falsy after a successful copy is left exactly as today
  (log `WARNING`, continue) — not part of what Tim asked to harden, and changing it has its own
  design questions (retry just the remove? forever?) that weren't discussed.

## Post-implementation follow-up (2026-09-18): `error_after` gets a default

Making `error_after` mandatory was the one part of this design that didn't survive contact with
deployment. The first `ImageWatcher` started after `061d4f78` landed died at construction:

```
TypeError: ImageWatcher.__init__() missing 1 required keyword-only argument: 'error_after'
```

None of the existing configs set it — not the MONET north/south ones, `pyobs-monti`,
`pyobs-iag50`, `pyobs-iagvt`, or `pytel-dev` — so every deployment would have to be edited before
its next restart, and the failure mode is a module that won't come up at all rather than a module
with a suboptimal alert threshold.

**Decision:** default it to `error_after: int = 1800` (30 minutes) and drop the "must be set per
config" requirement. The reasoning that there's "no researched number" was too strict: the value
only controls *when the one-time `ERROR` alert fires*, not whether retrying continues (it does,
indefinitely, under `backoff_cap`). A 30-minute default is defensible for the deployments seen so
far as the point where a transient outage stops looking transient, and any deployment that wants
to page sooner or later overrides it in its own config — which is now an optimization rather than
a precondition for the module starting.

**Changes:** `pyobs/modules/image/imagewatcher.py` (default + docstring),
`tests/modules/image/test_imagewatcher.py` (`test_constructor_requires_error_after` replaced by
`test_constructor_defaults_error_after`, asserting the 1800s default; all other tests already pass
`error_after` explicitly and were unaffected). No config changes were needed — which was the point.
