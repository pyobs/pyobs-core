# Plan: pre-create pubsub event/state nodes at module startup

Status: **proposed**

Tracks #824. Repos: pyobs-core.

Background: `2026-08-16-explicit-pubsub-event-subscriptions.md` moved event delivery onto
explicit XEP-0060 subscriptions against the shared `pubsub.<domain>` service; nodes are
named `pyobs:event:{module}:{Event}:{version}` (`_event_node`, `xmppcomm.py:929`) and
`pyobs:state:{module}:{Interface}:{version}` (`_state_node`, `xmppcomm.py:1102`).

## Problem

Pubsub nodes are only created by the server when the publisher publishes to them for the
first time (lazy auto-create). Before that, a subscribe attempt fails with
`item-not-found`, which is why both subscribe paths retry indefinitely in background
tasks (`_subscribe_event_with_retry`, `xmppcomm.py:942-968`; `_subscribe_with_retry`,
`xmppcomm.py:1293-1338`). Consequences:

- A consumer cannot complete a subscription — and therefore cannot receive anything —
  until the producer has sent that event/state once (e.g. a client that connects before
  the camera's first exposure can never subscribe to `camera:NewImageEvent` until that
  first image exists).
- The retry machinery is the only thing bridging that gap, and #824 shows it is not
  robust: `_retry_delay` (`xmppcomm.py:52-60`) overflows at attempt 1024, the retry task
  dies, and the `(peer, event)` key stays in `_event_subscriptions`, permanently marking
  the pair subscribed while nothing is subscribed and nothing is retrying. The state path
  has the same stuck-state class of bug (`_state_node_handlers`, `xmppcomm.py:1348`).

## Design

### Phase 1 — pre-create own nodes at startup (the core change)

A module creates its own event and state nodes during startup, so they exist *before* the
first publish — and, importantly, *before* the module announces presence, so peers that
react to it in `_got_online` (`xmppcomm.py:669-746`) land their subscriptions on the first
attempt.

- **New helper `_create_node(node)`**: `await self._safe_send(self.client.plugin["xep_0060"].create_node, self._pubsub_service, node)`.
  `create_node` is standard XEP-0060 (no item, no event). Wrap in
  `except slixmpp.exceptions.IqError` → `log.debug(...)` and continue: the realistic
  error is `<conflict/>` on restart (nodes persist server-side with `persist_items`), and
  a permission denial should degrade gracefully to today's lazy auto-create, never block
  startup. `_safe_send` already bounds the call (`xmppcomm.py:1055-1096`); IqError
  propagates to our handler, IqTimeout is retried there, so a dead server cannot hang
  `open()` beyond its existing budget.
- **Event nodes** — in `XmppComm._register_events` (`xmppcomm.py:889`), in the
  `handler is None` branch (send-only declaration): for each `ev` in `events`, if
  `self._module is not None`, create `self._event_node(self._module.name, ev)`. This is
  the moment a module declares what it publishes (`Comm.register_event`, `comm.py:452`
  puts the class into `_events_sent`); module `_open()`s call it after `comm.open()`
  (e.g. `basecamera.py:126`, `weather.py:92`) and before `startup()` announces presence.
  Local events never reach `_register_events` (`comm.py:455`), so nothing changes there.
- **State nodes** — in `XmppComm.open()` (`xmppcomm.py:276`), next to the disco-feature
  loop that already knows the exact set (`xmppcomm.py:352-356`): for each `i` in
  `self._module.interfaces` with `i.has_own_state()`, create
  `self._state_node(self._module.name, i)`.
- **No config form**: pre-created nodes inherit the server's `default_node_config`, the
  same settings auto-created nodes get today (test ejabberd.yml: `max_items: 1`,
  `persist_items: true`, `deliver_payloads: true`), so effective behavior is identical —
  an empty node delivers nothing until the first publish, and a late subscriber still
  gets only the latest item.
- **Out of scope**: module-less comms (GUI, admin tools) create no nodes — they only
  subscribe; their own publish set is not part of this plan.
- **Bonus side-effect**: `_get_derived_events` expansion (`comm.py:437`) means peers
  subscribe to every `role="send"`-advertised node (`xmppcomm.py:740-746`), including
  derived classes that may never be published; pre-creating the full declared set removes
  the "retry forever on a node that will never be created" case for the module's own
  nodes too.

The retry loops stay as a backstop: a subscriber that starts *before* the publisher's
startup finishes creating nodes, or while the publisher is offline, still needs them.

### Phase 2 — harden the retry machinery (issue #824)

Small, separable from Phase 1, but they are what make the backstop trustworthy:

- **Clamp the exponent in `_retry_delay`** (`xmppcomm.py:60`):
  `return random.uniform(0, min(cap, base * (2 ** min(attempt, 60))))`.
  `2**60 ≈ 1.15e18` is far above any real cap and well inside float range, so
  `min()` now protects the computation as intended. Fixes the `OverflowError` at every
  call site (`xmppcomm.py:968, 1089, 1093, 1239, 1318`).
- **Discard the key on abnormal exit in `_subscribe_event_with_retry`** (`xmppcomm.py:942-968`):
  wrap the retry `while` loop in `try/except Exception`: on an unexpected exception,
  `self._event_subscriptions.discard(key)` (key added at `:953`, guard read at `:951`),
  then re-raise so the failure surfaces once via the task-exception logger
  (`_log_task_exception`, `xmppcomm.py:63`). A later `register_event`/`_got_online`
  re-subscribes from scratch instead of short-circuiting on the stale key — the reporter's
  own suggested behavior in #824.
- **Same treatment for state**: `_subscribe_with_retry` (`xmppcomm.py:1293-1338`) has the
  identical stuck-state class of bug — if the task dies, the `_state_node_handlers` entry
  (created at `:1348`) is never cleaned and `_subscribe_state` short-circuits at
  `:1342-1346`, so live state updates are lost forever. On unexpected exception:
  `log.exception(...)`, remove `node` from `_state_node_handlers`, re-raise. (The exponent
  clamp is the primary protection; this is belt-and-braces. Note the callback-append path
  at `:1344`: a later re-subscribe registers only the latest callback — acceptable for a
  catastrophic, unexpected failure, and strictly better than permanent silent loss.)

## Checklist

### Phase 1: node pre-creation

- [ ] `_create_node(node)` helper on `XmppComm`: `_safe_send(xep_0060.create_node, ...)`,
      `IqError` → debug log, never raise.
- [ ] Event nodes: `XmppComm._register_events` handler-`None` branch, guarded on
      `self._module is not None`.
- [ ] State nodes: `XmppComm.open()` next to the disco-feature loop (`xmppcomm.py:352-356`),
      for `has_own_state()` interfaces.
- [ ] Confirm local events still bypass pubsub entirely (they never reach `_register_events`).
- [ ] Unit test: `_event_node`/`_state_node` naming unchanged.
- [ ] Integration test: publisher starts and never publishes → node exists server-side
      (subscribe succeeds / `get_nodes` shows it).

### Phase 2: retry hardening (#824)

- [ ] `_retry_delay` exponent clamp (`xmppcomm.py:60`).
- [ ] `_subscribe_event_with_retry`: discard key on abnormal exit, re-raise.
- [ ] `_subscribe_with_retry`: drop `_state_node_handlers` entry on abnormal exit, re-raise.
- [ ] Unit tests: `_retry_delay(1024)` / `_retry_delay(10**6)` return a float in `[0, cap]`
      (would overflow before the fix).
- [ ] Integration regression: simulated retry-task failure leaves the pair re-subscribable.

## Testing / validation (`tests/xmpp/docker-compose.yml` harness)

Extend the existing `tests/integration/test_xmpp_event_subscriptions.py` pattern:

1. **Subscribe before first publish**: `observer` subscribes to `camera`'s
   `NewImageEvent` node after `camera` started but *before* `camera` ever publishes;
   assert the subscribe succeeds (previously it retried until the first publish).
2. **First event still delivered** after the pre-created-node subscription lands
   (delivery semantics unchanged).
3. **Restart**: `camera` restarts (same bare JID) → `<conflict/>` tolerated, no error
   spam, existing and new subscriptions keep working.
4. **Subscriber before publisher**: `observer` connects first, `camera` starts later →
   `observer`'s retry lands as soon as `camera`'s startup pre-creates the node, without
   any publish having happened.
5. **#824 regression (event)**: after the retry task fails abnormally, a fresh
   registration re-subscribes successfully (old code: short-circuits on the stale key).
6. Full existing unit + XMPP integration suite stays green (1600+ unit tests currently
   passing).

## Rollout

- **No protocol change, no node-naming change, rolling-upgrade compatible.** Old modules
  still lazy-create on first publish; new modules pre-create. Mixed fleets work: the
  retry loops bridge any ordering.
- **Server ACL**: creating nodes on the shared pubsub service requires
  `access_createnode` for the module's JID. The test ejabberd allows all local users
  (`tests/xmpp/ejabberd.yml:23`); for production, verify the pubsub ACL permits module
  JIDs. If it doesn't, Phase 1 degrades gracefully (creation logs, lazy creation
  continues) — Phase 2 still ships independently.
- **Changelog**: add entries under the next `CHANGELOG.rst` dev heading when this lands
  (dev releases are exempt from `scripts/check_changelog.sh`).
