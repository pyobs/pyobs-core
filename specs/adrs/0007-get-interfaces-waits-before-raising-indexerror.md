# `XmppComm.get_interfaces()` waits briefly for an undiscovered client before raising

status: accepted
date: 2026-07-21

## Context and Problem Statement

`XmppComm.get_interfaces(client)` looked up a peer's discovered interfaces with a raw dict
subscript, `return await self._interface_cache[client]`. That cache entry is only created by
`_got_online()`, the presence handler — and `_got_online()` itself does real work before
resolving it (a disco#info network round-trip to the peer) after first creating the entry. A
caller's own background task can start running before presence for a given peer has even been
processed at all, let alone resolved, especially right after the caller's own module starts up
(background tasks begin as soon as the module opens; presence-driven peer discovery is a
separate, concurrent process with no ordering guarantee relative to it). In that window, the
dict subscript raised a bare `KeyError` instantly — not "peer not found," but "peer not
discovered *yet*," a fundamentally transient condition indistinguishable from a real absence by
the exception alone.

Compounding this: `get_interfaces()`'s own docstring already promises `Raises: IndexError: If
client cannot be found`, and `_get_client()` (`comm.py`) already has `except IndexError: return
None` specifically to handle a genuinely-missing client gracefully. But since the actual
implementation raised `KeyError`, that graceful path never engaged — the `KeyError` fell through
to `_resolve_proxy()`'s own `except KeyError: raise ValueError(...)` instead, producing a
messier "Could not get proxy for X" traceback than the clean path that already existed one level
up, waiting unused.

Observed directly: `pyobs-iagvt`'s `SunCamera`, starting up next to an already-online
`fibercamera`, hit exactly this — one `KeyError`-turned-`ValueError` on its very first
`_publish_camera_state()` tick, purely because that tick's timing happened to win the race
against `fibercamera`'s presence still being processed.

## Considered Options

* Fix only the exception type (raise `IndexError` instead of `KeyError`) and leave the
  fail-instantly behavior as-is — callers still see an error on every race loss, just a cleaner
  one
* Wait indefinitely for the client to appear — removes the race entirely, but a genuinely
  offline/nonexistent peer would then hang the caller forever
* Poll for the entry for a short, bounded window before giving up, and raise the already-promised
  `IndexError` if it never appears

## Decision Outcome

Chosen option: bounded poll (20 attempts, 0.25s apart — 5s total) before raising `IndexError`.
Fixing only the exception type would still surface an error for every instance of this
completely ordinary startup race, just with a cleaner message — it doesn't address the actual
problem, which is that "not discovered yet" and "genuinely not found" were being treated
identically. Waiting indefinitely trades a fast, wrong failure for a slow, silent hang, which is
worse for a peer that really is offline or misconfigured. A short bounded wait resolves the
common case (peer is online, discovery just hasn't finished) silently and correctly, while still
failing within a reasonable, human-noticeable time for the uncommon case (peer genuinely isn't
there) — and now via the exception type (`IndexError`) that `_get_client()` was already written
to expect, so the existing graceful-`None` path actually does something for the first time.

### Consequences

* Good, because a module starting up next to already-online peers no longer logs a spurious
  error purely from timing — confirmed directly against the `SunCamera`/`fibercamera` case that
  motivated this
* Good, because `_get_client()`'s existing `except IndexError: return None` finally does what it
  was written to do, instead of being dead code that never matched what was actually raised
* Neutral, because 5s is a guess at "long enough for ordinary presence processing, short enough
  to still fail promptly" — not derived from a measured distribution of real discovery latency;
  revisit if either false-positive timeouts or unacceptably slow failure-for-real-absence show up
  in practice
* Bad, because a caller that wants to distinguish "genuinely offline" from "slow to discover"
  still can't from the `IndexError` alone — both look identical once the wait expires
