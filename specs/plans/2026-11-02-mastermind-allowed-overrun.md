# Plan: restore `Mastermind.allowed_overrun`

Status: **implemented** (pyobs-core#1022)
Repos: pyobs-core

## Problem

`allowed_overrun` was stored but never read since de4d8c3a ("asyncio fixes"), which dropped the check
`Time.now() > task.end + allowed_overrun`. A task ran to its last frame however far past its window.

## Decisions

- Deadline is the scheduled window end plus `allowed_overrun` (as in the removed code and the docs). The window end
  is saved before `observation.end` is overwritten with `now + duration`.
- `asyncio.timeout()` instead of `wait_for`, so a `TimeoutError` raised by the task itself (e.g. RPC timeout)
  stays a normal failure (`FAILED`); only the overrun gives `ABORTED`.
- Event stays `TaskFailedEvent` (no wire change); now registered in `open()`.
- `allowed_overrun=None` disables the check.
- `stop()` is unchanged (out of scope).

## Risks / follow-up

- Behaviour change: the default of 300 s now takes effect, hardest for `can_start_late` tasks that start late.
- Scripts have no cleanup on `CancelledError`: guider and telescope tracking stay on, remote exposures continue.
  Follow-up: `try/finally` cleanup in `LcoDefaultScript.run` and other scripts.
