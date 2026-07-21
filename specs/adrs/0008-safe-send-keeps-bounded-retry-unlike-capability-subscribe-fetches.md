# `_safe_send` keeps a bounded retry budget; capability/subscribe fetches don't

status: accepted
date: 2026-07-21

## Context and Problem Statement

Three retry loops in `XmppComm` all handle the same underlying problem — an IQ round-trip that
didn't get a timely reply, possibly because many modules are doing the same thing at once (a
fleet-wide restart) and end up retrying in lockstep against each other. All three now use jittered,
capped exponential backoff (`_retry_delay()`) instead of a fixed inter-attempt wait, for the same
reason: a fixed wait keeps every module's retries synchronized, repeatedly re-hammering the server
at the same instants.

Where they differ: `_get_capabilities()` and `_subscribe_with_retry()` retry *indefinitely* — they
only stop when the peer actually goes offline (`_get_capabilities`) or the last subscriber
unsubscribes (`_subscribe_with_retry`). `_safe_send()` still gives up after a fixed budget
(`_safe_send_attempts`, currently 5) and raises `IqTimeout` to its caller. Read next to each
other, the inconsistency looks like an oversight — shouldn't all three either retry forever or
all give up eventually?

## Considered Options

* Make all three retry indefinitely, for consistency
* Make all three give up after a fixed budget, for consistency
* Keep the difference: unlimited retry for capability/subscribe fetches, bounded retry-then-raise
  for `_safe_send`

## Decision Outcome

Chosen option: keep the difference, because the three calls have genuinely different failure
semantics for their callers, not just superficially different code shapes.

`_get_capabilities()` and `_subscribe_with_retry()` both run as detached background tasks
(`asyncio.create_task(...)` from `_subscribe_state()`/`_got_online()`) with no caller awaiting
their result — nothing is blocked while they retry, and "give up permanently" was the actual bug
being fixed (`25cbaad2`): a peer merely slow to respond during a fleet-wide restart would
otherwise never get its capabilities/state fetched again short of a full disconnect/reconnect.
Retrying indefinitely has no caller-visible cost here, since there is no caller waiting.

`_safe_send()` is different: it's called synchronously, awaited, from code paths that include a
module's own `open()` (e.g. every `comm.set_state(...)`/`comm.send_event(...)` call during
startup). `open()` blocking indefinitely because a `send_event()` inside it never gives up is
exactly the failure mode `_safe_send_timeout`'s own comment already warns about — referencing
the #664/#666 hang where a slow-shaper server turned a single stuck call into the entire module
never reaching "Started successfully." Retrying indefinitely here would trade "occasionally
raises IqTimeout, caller can react" for "occasionally hangs the caller forever," which is a
strictly worse failure mode for anything that must eventually return.

Jitter applies equally to both cases regardless of this difference — decorrelating synchronized
retries helps whether the loop is bounded or not, so there was no reason to withhold it from
`_safe_send` just because it keeps its budget.

### Consequences

* Good, because `_safe_send`'s callers (including `open()`) keep a bounded worst-case wait
  instead of a code path that could hang a module indefinitely, matching the reasoning that
  already motivated `_safe_send_timeout`'s existence
* Good, because capability/subscribe fetches no longer permanently give up on a peer that was
  merely slow once, without needing the same unbounded-wait tradeoff to apply to `_safe_send`
* Neutral, because this means the three retry loops are deliberately inconsistent with each
  other — a future reader comparing them side by side should consult this record rather than
  "fixing" the inconsistency by making them uniform
* Bad, because `_safe_send`'s bounded budget means a caller can still see `IqTimeout` during a
  genuinely bad but recoverable-if-you-wait-longer situation (e.g. a very slow but not dead
  shaper) — the tradeoff is deliberate, not free
