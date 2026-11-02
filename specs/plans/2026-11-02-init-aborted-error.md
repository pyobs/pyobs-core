# Plan: InitAbortedError for deliberately aborted init()

Date: 2026-11-02

Status: implemented in pyobs-core (PR pending), pyobs-brot change on a separate branch; not released

Repos: pyobs-core, pyobs-brot

Issue: [pyobs-core #1031](https://github.com/pyobs/pyobs-core/issues/1031). Follow-up for other `InitError`
refusals: [pyobs-core #1034](https://github.com/pyobs/pyobs-core/issues/1034).

## Problem

`BaseTelescope` escalates three `MotionError` in 600 s to `ModuleState.ERROR`
(`basetelescope.py`, `_register_exception(exc.MotionError, 3, timespan=600, ...)`). `InitError` is a
`MotionError`, and pyobs-brot raises it when a park/stop interrupts a startup on purpose (the
weather-protection path parks a telescope that is still starting up). Three such aborts disable a healthy
module until restart.

## Decision

New `InitAbortedError(PyobsError)` in `pyobs/utils/exceptions.py`, modeled on `PointingLimitError`: a direct
`PyobsError` child, so it is neither a `MotionError` nor an `InitError`, and it is excluded from the
synthetic `RemoteError` bucket in `Module._counts_as_remote_error`. `AbortedError` is not reused: it means
"the caller cancelled its own operation via abort()" and is documented for focus, acquisition and stack
aborts. Special-casing `InitError` by cause was rejected: escalation counts by type and has no notion of why an
exception was raised.

## Steps

- [x] pyobs-core: add `InitAbortedError`, extend `_counts_as_remote_error`, update `IMotion.init()` Raises, API
  and recipe docs.
- [x] pyobs-core tests: three aborted inits leave the module READY, three `InitError` still escalate; remote
  fault classification; RPC round trip (no bases on the wire; an older core receives `UnclassifiedError`
  with `original_type`).
- [ ] pyobs-brot: raise `InitAbortedError` where startup was interrupted (`brottelescope.py`), update
  `tests/test_initialization.py`, raise the core pin to the release that ships the class.
- [ ] Release core (minor), then brot, then deploy both together on the telescope hosts. Callers on older
  cores see the new error as `UnclassifiedError` (cosmetic). No backport: the class has to exist on the
  raising host.
- [ ] Changelog entry: tracked in [#1037](https://github.com/pyobs/pyobs-core/issues/1037).

## Notes

No caller in pyobs-core or the local sibling repos catches `InitError`/`MotionError` around `init()`, so no
handling is lost. Other deliberate refusals in brot ("Weather seems to be bad.") still raise `InitError` and
can escalate the same way (#1034).
