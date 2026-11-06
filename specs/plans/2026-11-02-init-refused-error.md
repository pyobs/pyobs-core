# Plan: InitRefusedError for init() refusals on a precondition

Date: 2026-11-02

Status: implemented in pyobs-core (2.23.0) and pyobs-brot (PR #101 merged); brot not released yet

Repos: pyobs-core, pyobs-brot

Issue: [pyobs-core #1034](https://github.com/pyobs/pyobs-core/issues/1034). Follows
[2026-11-02-init-aborted-error.md](2026-11-02-init-aborted-error.md) (#1031).

## Problem

pyobs-brot raises `InitError` for deliberate refusals such as "Weather seems to be bad."
(`brottelescope.py`, `brotroof.py`, `brotdome.py`). `InitError` is a `MotionError`, and `BaseTelescope` and
`BaseDome` escalate three `MotionError` in 600 s to `ModuleState.ERROR`. Three refusals in ten minutes disable a
healthy module until restart. `BaseRoof` registers no such handler, so roofs are not affected in core.

## Decision

New `InitRefusedError(PyobsError)`, a sibling of `InitAbortedError` with the same treatment: not a
`MotionError`/`InitError`, excluded from the synthetic `RemoteError` bucket in `Module._counts_as_remote_error`.

Reusing `InitAbortedError` was considered and rejected: "aborted" means an init that was already running was
cut short, while a refusal happens before anything starts, and callers may want to tell the two apart (a
refusal says "retry when the precondition holds", an abort says "somebody stopped it"). The price is one more
class, and callers on older cores see it as `UnclassifiedError` (cosmetic), as with `InitAbortedError`.

## Steps

- [x] pyobs-core: add `InitRefusedError`, extend `_counts_as_remote_error`, update `IMotion.init()` Raises, API
  and recipe docs, changelog.
- [x] pyobs-core tests: refusals leave telescope and dome READY while `InitError` still escalates; remote
  classification; RPC round trip.
- [x] pyobs-core released as 2.23.0.
- [x] pyobs-brot ([#101](https://github.com/pyobs/pyobs-brot/pull/101)): raise `InitRefusedError` for the weather
  refusal in telescope, roof and dome (the error-state and powerup failures stay `InitError`: they are device
  faults), core pin raised to `>=2.23.0`.
- [ ] Release brot, then deploy it together with core 2.23.0.

## Notes

`DummyRoof.init()` wraps every failure in `InitError`, including "another motion is in progress". That is
a simulator wrapping an exception, not a deliberate refusal, and no escalation is registered on roofs, so it
is left alone.
