# Plan: Explicit pubsub subscriptions for event delivery

Status: implemented, closed (merged 2026-08-16, PR #761); rollout to production sites not yet
started

Client-side implementation validated against the live `tests/xmpp/docker-compose.yml` harness
(`tests/integration/test_xmpp_event_subscriptions.py`, 9 tests) plus the full existing XMPP
integration suite (30/30 passing) — confirms no ejabberd config change is needed and that a peer
with no registered handler never receives the wire message at all, not just "receives and drops."

Decision record: `specs/adrs/0012-event-delivery-explicit-pubsub-subscription-not-presence.md`.
Background: `specs/plans/2026-08-16-logevent-double-delivery-fix-discussion.md`,
`specs/plans/2026-08-08-logevent-double-delivery-investigation.md`.

## Problem

See the ADR for full context. Summary: today every module receives every other module's events
over the wire regardless of interest, because delivery rides on PEP presence auto-subscribe
(shared roster `@all@`), and filtering only ever happens after the fact at the application layer.
This plan moves events onto the same mechanism `XmppComm` already uses for state — the shared
`pubsub.<domain>` component with explicit XEP-0060 subscribe/unsubscribe
(`_subscribe_state`/`_subscribe_with_retry`/`_unsubscribe_state`, `xmppcomm.py:1120-1199`) — so
delivery is gated by real subscription instead of presence.

Rollout mode (per discussion, 2026-08-16): coordinated cutover — every module at a site moves to
the new release together. Not staged/mixed-version (old PEP-publishing and new
`pubsub.<domain>`-publishing modules cannot interoperate). Scope: all event types from day one,
not just `LogEvent`. No server-side ejabberd config change is needed (see ADR) — the rollout unit
is "restart pyobs modules," not "restart ejabberd."

## Design

### Node naming

New helper, mirroring `_state_node`:

```python
@staticmethod
def _event_node(module: str, event_class: type[Event]) -> str:
    return f"pyobs:event:{module}:{event_class.__name__}:{event_class.version}"
```

### Publishing (`send_event`, `xmppcomm.py:763`)

Replace the `xep_0163.publish(...)` call (implicit PEP, own bare JID) with an explicit publish to
`self._pubsub_service`, mirroring `_set_state` (`xmppcomm.py:964`):

```python
node = self._event_node(self._module.name, event.__class__)
await self._safe_send(self.client.plugin["xep_0060"].publish, self._pubsub_service, node, payload=stanza)
```

### Subscribing

Two trigger points, same as the state pattern but per-peer since (unlike state, which is
requested from one named module) an event handler wants events from *every* publisher:

- **Peer comes online** (`_got_online`, `xmppcomm.py:610`, after the peer is added to
  `self._online_clients`): for every event class currently in `self._event_handlers`, subscribe
  to that peer's event node.
- **New handler registered while peers are already online** (`_register_events`, called from
  `Comm.register_event()` every time, both at startup and later): for every event class being
  registered with a handler, subscribe to that event's node on every peer already in
  `self._online_clients`.

Both call a shared retry-subscribe helper mirroring `_subscribe_with_retry` — background task,
capped-backoff retry, since the peer may not have published (and therefore auto-created the
node) yet:

```python
async def _subscribe_event_with_retry(self, peer_module: str, event_class: type[Event]) -> None:
    node = self._event_node(peer_module, event_class)
    key = (peer_module, event_class)
    if key in self._event_subscriptions:
        return
    self._event_subscriptions.add(key)
    attempt = 0
    while key in self._event_subscriptions:
        try:
            await self._safe_send(self.client.plugin["xep_0060"].subscribe, self._pubsub_service, node)
            return
        except (slixmpp.exceptions.IqError, slixmpp.exceptions.IqTimeout):
            attempt += 1
            await asyncio.sleep(_retry_delay(attempt))
```

`self._event_subscriptions: set[tuple[str, type[Event]]]` tracks desired (peer, event) pairs so:
a peer flapping online/offline/online doesn't queue duplicate retry loops, and unsubscribe (below)
can cancel a still-retrying subscribe by removing the key, same as `_state_node_handlers`'s
membership check does for state.

### Unsubscribing

- **Last handler for an event class removed** (`unregister_event()`, `comm.py:458`): new hook
  `_unregister_events(events)`, called only for event classes whose handler list just became
  empty (mirrors the existing `_events_subscribed.discard(ev)` condition). For each such event
  class, unsubscribe from that event's node on every currently online peer, and drop the
  corresponding `(peer, event_class)` keys from `_event_subscriptions`.
- **Peer goes offline** (`_jid_got_offline`, `xmppcomm.py:720`): no explicit unsubscribe call —
  same reasoning as the state pattern (subscriptions are keyed on the peer's persistent bare JID
  account, not the session), confirmed in testing (harness step 5 below) rather than assumed.

### `comm.py` changes

- `unregister_event()`: track which event classes actually lost their last handler this call,
  and call the new `_unregister_events(events)` hook for those (mirrors the existing
  `_register_events(events, handler)` call in `register_event()`). Base `Comm._unregister_events`
  is a no-op `pass`, same as the existing `_register_events` base.

### Removed / unchanged

- `add_interest()` and PEP publish/subscribe for events — removed entirely, not just the
  double-send call. Events no longer touch `xep_0163` at all.
- `xep_0030.add_feature` for event types stays — unrelated discovery advertising (used by
  pyobs-web-client per the `_event_role` comment, `xmppcomm.py:40`), not a delivery mechanism.
- `ModuleOpenedEvent` / `ModuleClosedEvent` — generated locally in `_got_online` /
  `_jid_got_offline` via direct `_send_event_to_module` calls, never touched pubsub either way.
  Unaffected; confirm in testing (step 6 below) rather than assume.

## Testing / validation (`tests/xmpp/docker-compose.yml` harness)

No ejabberd config change needed (see ADR), so `tests/xmpp/ejabberd.yml` is unchanged. The
existing two registered test users (`camera`, `observer`) are insufficient for the core filtering
assertion, which needs a publisher plus one subscriber-with-handler plus one
subscriber-without-handler; add a third registered user (`control`) to
`tests/xmpp/docker-compose.yml`'s `CTL_ON_START`, same idempotent `!`-prefixed pattern as the
existing two.

1. Core behavior: `camera` registers a `LogEvent` handler, `observer` does not. `control`
   publishes a `LogEvent`. Confirm `camera` receives it, and confirm `observer` never even gets
   the wire message — spy on `observer`'s `_handle_event_sync` (always invoked for every incoming
   event message regardless of app-level handler, today) and assert it's never called, rather than
   asserting only "no handler fired" (which passing today too, for the wrong reason — no handler
   registered at all, not because delivery was filtered).
2. Regression guard: confirm no duplicate delivery — the `add_interest()`/PEP mechanism that
   caused the `ms` double-send is gone entirely now, not just one call site.
3. Late subscribe: `camera` registers a `LogEvent` handler *after* `control` has already been
   online and publishing for a while. Confirm `camera` starts receiving once its subscribe
   retry-loop succeeds, without needing a reconnect.
4. Unregister: `camera` calls `unregister_event()` for `LogEvent`. Confirm no further `LogEvent`
   messages arrive at `camera` after the unsubscribe completes.
5. Restart: `camera` restarts (new session, same bare JID). Confirm events resume without manual
   resubscription — `camera`'s own startup re-subscribes to already-online peers, and peers'
   `_got_online` handling re-subscribes to `camera` when it reappears. Also confirms no stale
   subscription cleanup is needed server-side.
6. Confirm `ModuleOpenedEvent`/`ModuleClosedEvent` still fire normally (sanity check, not expected
   to need any change, since they bypass pubsub entirely).

## Rollout (coordinated cutover, per site)

1. Ship the pyobs-core client-side change; every module at a site must be running the new version
   before that site's cutover — mixed old/new is not supported (ADR decision, and now a hard
   protocol incompatibility, not just a design choice, since old and new use different pubsub
   mechanisms entirely).
2. Restart every module at the site together so they all pick up the new client code at once.
   No ejabberd config change or restart is needed.
3. Order: dev/`ms` first (already the site used for the double-delivery fix's own validation),
   then IAG50, then remaining sites one at a time. Reuse the monitoring approach from the
   double-delivery fix's rollback plan — watch for modules going silent on events they should be
   receiving.
4. Rollback: roll back the pyobs-core release on that site's modules. Delivery reverts to the old
   PEP/presence path immediately (no ejabberd state to revert) — no data loss.

## Post-merge fixes (review, 2026-08-16)

Found and fixed on top of the original implementation before merge:

- **`_got_online`/`_register_events` over-subscribed to peers that never publish the event.** Both
  subscribed to every online peer's node for every event type a module handles, regardless of
  whether that peer actually sends it — e.g. a camera's `BadWeatherEvent` handler would
  retry-subscribe to `admin:BadWeatherEvent` forever, spamming "still failing to subscribe" on a
  node that would never be created. Fixed by gating the subscribe loops on the peer's disco#info
  `role="send"` advertisement (`_event_role`/`_get_disco_info`, already shipped for
  `pyobs-web-client`'s benefit but previously unread by `pyobs-core` itself): `_get_interfaces`
  now also parses the peer's `<event role="...">` schema elements into a `_peer_sent_events`
  cache, and a subscribe is only attempted for `(peer, event_class)` pairs the peer actually
  declares. Two new tests: a peer that never advertises `send` for an event type is never
  subscribed to (confirmed this fails without the fix), and the flip side — a peer that declares
  an event handler-less (send-only) still gets subscribed to and delivers normally.
- The earlier local-event over-subscription and module-less `send_event` crash (see the PR's
  review history) were fixed in the same round that produced the 4→7 test count; the fix above
  brought it to 9.

Also dropped an unrelated `graphify-out/` regen commit that had gotten mixed into the branch
before merge (rebased out, not part of this plan's diff).
