# Event-loop lag watchdog lives on `Module`, not `Comm` or `Application`

status: accepted
date: 2026-07-27

## Context and Problem Statement

A production incident on `pyobs-iag50`: modules restarting together saw disco#info capability-fetch
queries between them (`XmppComm._get_capabilities`) get no reply for a full 10s timeout, three
attempts in a row. The leading hypothesis for a while was a blocking call somewhere in a module (or
one of its background tasks) freezing that module's entire event loop — which would stop it from
answering peers' requests in time, and stop its own outgoing sends from getting acked, without
raising anything locally. Confirming or ruling that out required reconstructing it indirectly: cross-
referencing which module was the common factor across several peers' timeout warnings, working
backward through retry/backoff timing math to figure out when the first attempt must have started,
and reasoning about whether that lined up with the module still booting. That's a slow, manual, easy-
to-get-wrong process, and it doesn't scale to "check the log and know immediately."

What was missing: a way for a module to notice and report, from inside itself, that its own event
loop had stalled — turning "peers timing out trying to reach this module" from a mystery requiring
cross-module log archaeology into a direct, first-party log line at the source.

A second, smaller decision came up once the mechanism existed: whether to log on every periodic
check while a stall is ongoing, or only when it starts and when it clears.

## Considered Options

**Where the watchdog lives:**
* `Comm` (e.g. `XmppComm`) — where the actual observed symptom (XMPP timeouts) shows up
* `Application` — owns the event loop directly (`self._loop`), and is genuinely one-per-process even
  under `MultiModule` (where several child `Module`s share a single loop)
* `Module`, via the existing `Object.add_background_task()` mechanism

**Logging shape once a stall is detected:**
* Level-triggered — log on every periodic check for as long as the lag stays over threshold
* Edge-triggered — log once when a stall starts, once more (with total duration) when it clears

## Decision Outcome

Chosen: **`Module`**, implemented as a background task (`_watch_event_loop_lag`) registered via
`add_background_task` in `Module.__init__`; and **edge-triggered** logging.

`Comm` was rejected because the failure mode is generic — any blocking call anywhere in the module or
one of its background tasks, not something specific to XMPP or any other transport. A module with no
real `Comm` at all (`DummyComm`) deserves the same protection, and putting this on `Comm` would mean
reimplementing it per subclass instead of once, shared.

`Application` was rejected despite the appealing "exactly one per event loop" property: it isn't
`Object`-based, so it has none of `add_background_task`'s existing lifecycle management for free —
auto-start on `open()`, auto-cancel on `close()`, restart-on-crash with a runaway-failure cutoff, and
automatic `PYOBS_MODULE` log-context tagging via the same `module_name` ContextVar every other
background task already uses. Building an equivalent by hand in `Application` for one task isn't
worth it, especially since `Application`'s `module_factory` path doesn't even have a resolved module
name to tag logs with until the factory resolves.

`Module` reuses all of that infrastructure as-is, and matches the established pattern already used
throughout the codebase (`FocusModel._update`, `BrotDome._update_status`, etc.) — a background task
registered in `__init__`, started/stopped automatically with the module's own lifecycle.

Edge-triggered logging was chosen because a single continuous block only ever produces one check
anyway (the watchdog task itself can't run until the block clears, so there's nothing to log more
than once), but a *sustained-yet-fluctuating* overload — still yielding briefly, but staying over
threshold across many consecutive checks — would otherwise log once per check for as long as it
lasts. Logging once on the way in and once on the way out (with the total duration) gives the same
information without the spam.

### Consequences

* Good, because it gives a direct, first-party signal ("this module's own event loop stalled for
  Xs") at the module actually responsible, instead of requiring the kind of manual cross-module log
  reconstruction that motivated this in the first place.
* Good, because it costs nothing new to build or maintain beyond the watchdog's own ~15 lines — full
  lifecycle management and log tagging come from infrastructure that already existed.
* Neutral, because under `MultiModule`, every child module shares one process's event loop, so each
  running its own watchdog means a single real stall gets reported once per child module, not once
  per process. Redundant, but not wrong — every report is independently true (every child was
  equally stalled) — and cheaper to accept than building genuine single-instance-per-process
  bookkeeping into `Application` just to deduplicate.
* Bad, because this only detects *that* the loop stalled and roughly *how long* — never *which*
  coroutine or line caused it. Localizing to a specific call needs asyncio's own debug mode
  (`loop.set_debug(True)`, `slow_callback_duration`), deliberately not folded into this always-on
  watchdog since debug mode adds per-callback timing overhead everywhere it's enabled — it's a
  "flip on temporarily once the tripwire fires" tool, not something to leave on permanently the way
  this watchdog is meant to be.
