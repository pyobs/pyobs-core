# Restrict `Proxy` access to `async with`; remove `await self.proxy(...)`

status: accepted
date: 2026-07-01

## Context and Problem Statement

Once `Proxy` gained live state (`.get_state(interface)`, kept current via a PubSub
subscription that `Comm` tears down on the remote module's disconnect), a `Proxy` held across
time by module code became a liability. Module code commonly wrote
`camera = await self.proxy("camera", ICooling)` once and kept the reference in a long-lived
task or instance attribute. If the remote module disconnected and reconnected — possibly with
a different interface set — that stashed reference could go stale: `.state` would silently
freeze at its last known value with no signal anything had changed, since the object itself
wasn't the one evicted (`Comm` evicts its own cache entry, not references module code already
holds).

A dual-mode design (support both `await self.proxy(...)` for backward compatibility and
`async with self.proxy(...) as x:` for the new state-aware pattern) was drafted first as a
reasonable middle ground. It left the actual problem optional: module code could still choose
the old form and reintroduce the stale-reference gotcha.

## Considered Options

* Dual-mode: keep `await self.proxy(...)` working, add `async with` as the recommended
  alternative
* Single-mode: remove `await self.proxy(...)` entirely, making `async with` the only way to
  obtain a proxy
* Explicit lifecycle API: keep `await self.proxy(...)`, add `Proxy.close()` (or make `Proxy`
  itself an async context manager) that module code must call/enter explicitly

## Decision Outcome

Chosen option: single-mode. `await self.proxy(...)` is removed — `_ProxyContext.__await__` is
dropped, so a stray `await self.proxy(...)` becomes a hard `TypeError` rather than something
that quietly keeps compiling and running against a stale assumption. `async with
self.proxy("camera", ICooling) as camera:` becomes the only way to obtain a proxy; `safe_proxy`
and the new `has_proxy()` (for the pure existence/type-check case, which never returns a
`Proxy` at all and so doesn't need `async with`) follow the same shape.

The explicit-lifecycle option was rejected because it requires every call site to remember to
close/enter something it previously just held onto — the same discipline problem as the
dual-mode option, just relocated to a different API. `async with` closes the gap by
construction: there is no long-lived reference to forget to release, because the block's own
scope is the only place a resolved proxy is held.

This is a one-time migration cost across `pyobs-core` and downstream repos — every
`x = await self.proxy(...)` call site needs rewriting. Handled as a largely mechanical codemod;
branches with early returns out of the middle of a block needed manual attention for the
indentation change. See `specs/design/pyobs_2_0_wire_protocol.md`'s "Migration patterns from
real call sites" for the shapes that came up (multiple proxies in a loop, a conditionally-needed
proxy used later in the same method via `contextlib.AsyncExitStack`).

### Consequences

* Good, because the indefinite-drift case — a proxy silently going stale for hours because
  code stashed it in `self._camera` once — is closed off at the type level, not just discouraged
  by convention
* Good, because `has_proxy()` still covers the common "is this the right type" check without
  forcing `async with ... as x: pass` ceremony where the resolved object is never used
* Neutral, because a narrower window remains *within* one `async with` block — the remote
  module could still disconnect between `__aenter__` resolving the proxy and a later line
  reading `.state` — but this window is far smaller and harder to hit than an indefinitely-held
  reference
* Bad, because it is a breaking API change requiring every existing call site (in this repo and
  every downstream driver repo) to be rewritten before upgrading
