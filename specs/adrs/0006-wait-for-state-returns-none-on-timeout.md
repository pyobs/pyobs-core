# `Proxy.wait_for_state()` returns `None` on timeout instead of raising

status: accepted
date: 2026-07-21

## Context and Problem Statement

`Proxy.wait_for_state(interface, timeout=10.0)` (`pyobs/comm/proxy.py`) subscribes to a peer's
state for `interface` and waits for the first update, for callers that want "the current value,
or wait a moment if it hasn't arrived yet." Its implementation wrapped the wait in
`asyncio.wait_for(event.wait(), timeout=timeout)` with no `except TimeoutError` of its own — if
the peer never published within the timeout, `TimeoutError` propagated straight out to the
caller.

Every caller of `wait_for_state()` found in the codebase — `waitformotion.py`, `weatheraware.py`,
`pyobs-iagvt`'s `SunCamera` (`_get_gain`/`_get_exposure_time`) among others — does
`state = await proxy.wait_for_state(...)` immediately followed by `X if state is not None else Y`.
That pattern only makes sense if the method is expected to return `None` on timeout; a caller
who actually wanted "raise if not available in time" would have no reason to write the
`is not None` check at all, since a raised exception would prevent ever reaching it. Confirmed
directly: `SunCamera`'s `_publish_camera_state()` background task hit this as a real
production `TimeoutError` — a peer being reachable and correctly implementing an interface, just
not having published a first value yet, turned into an ERROR-level traceback every 5s instead of
the graceful "0.0, try again next tick" the surrounding code obviously intended.

## Considered Options

* Leave `wait_for_state()` raising `TimeoutError` on timeout, and fix every caller to catch it
  explicitly around each call site
* Make `wait_for_state()` catch its own internal `TimeoutError` and return `None`
  (`self._state.get(interface)`, which is `None` if nothing was ever received), matching what
  every caller already assumes

## Decision Outcome

Chosen option: catch `TimeoutError` inside `wait_for_state()` itself and return `None`. Every
caller already treats a `None` result as "not available yet" — fixing this at every call site
individually would mean auditing and wrapping each one in a `try`/`except TimeoutError` that
does exactly the same thing (`except TimeoutError: state = None`), which is strictly more code
for the same outcome, and leaves the trap in place for the next caller who reads the method name
("wait *for* state" reads as "wait until you get it or tell me you didn't," not "wait or blow
up") and reasonably assumes the same non-raising contract everyone else already did.

This was checked against every call site before deciding, not assumed: none of them wanted the
raise. If a future caller genuinely needs "raise if this doesn't arrive in time" semantics, that
belongs to that caller (`asyncio.wait_for(proxy.wait_for_state(...), timeout=...)` around the
call, or a distinct method), not to `wait_for_state()`'s default behavior.

### Consequences

* Good, because every existing caller's `is not None` handling now actually reflects a reachable
  code path instead of being unreachable dead code that only looked like defensive programming
* Good, because a peer that's merely slow to publish (own startup, restart, momentary hiccup) no
  longer produces an unhandled exception in whatever background loop is polling it
* Neutral, because the `finally: await self._comm.unsubscribe_state(...)` cleanup already ran
  regardless of the old raise — this change doesn't touch subscription lifecycle, only what the
  caller sees afterward
* Bad, because a caller that genuinely wants to distinguish "peer published `None`-ish/falsy
  state" from "peer never published at all" still can't, from the return value alone — both look
  identical. No caller in the codebase currently needs that distinction; if one ever does, it
  needs a different method or an explicit sentinel, not a reversion of this decision
