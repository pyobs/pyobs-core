# Event delivery moves from presence auto-subscribe to explicit pubsub subscription

status: proposed
date: 2026-08-16

## Context and Problem Statement

The LogEvent double-delivery investigation (`specs/plans/2026-08-08-logevent-double-delivery-investigation.md`,
`logevent-double-delivery-fix-discussion.md`) established that event delivery in `XmppComm`
already rides entirely on XEP-0163 presence auto-subscribe, via the server-provisioned shared
roster (`srg_user_add @all@`). `add_interest()`'s `+notify` disco/caps declaration — the thing
that looks like it expresses "I want this event type" — has no effect on delivery at all;
delivery is decided at the presence layer before caps is ever consulted. Dropping
`add_interest()` (the near-term fix for the `ms` double-send bug) removes a duplicate wire
message, but does not introduce any filtering, because none existed: every module already
receives and parses every other module's events regardless of whether it registered a handler,
and only drops them afterward at the application layer (`_send_event_to_module`, `comm.py:677`).

The behavior that `add_interest()` implied — deliver an event type only to clients that actually
declared interest in it — never worked, and can't work as long as delivery is gated by presence
subscription: presence is a binary per-JID-pair relationship (subscribed or not), so it can't
express "receive `LogEvent` but not `FocusEvent`" from the same publisher. That granularity has
to live at the pubsub-node/subscription level.

Presence already does other work in `XmppComm`: `_got_presence_update` /
`_fire_presence_callbacks` (`xmppcomm.py:693`) track module liveness/state (online/offline/error),
independent of events entirely. It was never free to repurpose as a delivery filter — it's
already doing something else.

## Considered Options

* Leave delivery as-is: every module receives every event over the wire and filters at the
  application layer. Zero delivery-layer change, but the network/parse cost scales with fleet
  size × event volume, paid by every module for events nobody there wants.
* Narrower shared-roster groups (per-module opt-in groups instead of one `@all@`), keeping
  presence as the delivery gate. Coarser than per-event-type (a module either gets everything
  from a peer or nothing), and leaves presence doing double duty (liveness + delivery).
* Explicit XEP-0060 pubsub subscription per event type, decoupled from presence: change PEP
  node `access_model` from the implicit `presence` (auto-subscribe) default to `open` (or
  `whitelist`), keep the shared roster doing only what it already does (liveness tracking), and
  have each module explicitly subscribe to a peer's event nodes for exactly the event classes
  in its own `_event_handlers`.

## Decision Outcome

Chosen option: explicit pubsub subscription per event type, decoupled from presence.

- It matches the semantics `add_interest()`'s `+notify` declaration always implied but never
  actually delivered on.
- Presence keeps its one existing job (liveness/state); pubsub subscription becomes the one and
  only thing gating delivery. No more hidden coupling via ejabberd's PEP auto-subscribe
  convenience.
- No new client dependency: `xep_0060` (PubSub) is already registered in `XmppClient`
  (`xmppclient.py:61`) alongside `xep_0163`, and slixmpp's `XEP_0060.subscribe()` /
  `.unsubscribe()` / `.set_node_config()` already exist.

Narrower shared-roster groups were rejected as a stepping-stone at best: pyobs's own
double-delivery discussion doc concludes this is "probably why interest was added in the first
place — intent was filtering, but the roster defeats it," i.e. a variant of this has effectively
already been tried in spirit for events, and it doesn't reach per-event-type granularity.
Leaving delivery as-is was rejected because it doesn't address the actual driving concern
(bandwidth/parse overhead scaling with fleet size), which is the whole reason this ADR exists.

### Consequences

* Good, because filtering finally exists at the delivery layer — bandwidth/parse savings
  proportional to how narrow each module's `_event_handlers` actually is.
* Good, because presence and pubsub subscription each go back to a single, non-overloaded job.
* Bad, because this changes delivery semantics fleet-wide: every site's ejabberd
  `mod_pubsub.default_node_config.access_model` needs updating
  (`scripts/xmpp/install-ejabberd.sh`), and every module needs the new subscribe/unsubscribe
  client logic before cutover. Per the implementation plan
  (`specs/plans/2026-08-16-explicit-pubsub-event-subscriptions.md`), this is a coordinated
  cutover per site (maintenance window), not a staged/mixed-version rollout — old
  (presence-based) and new (explicit-subscribe) modules are not expected to interoperate.
* Unresolved, because whether ejabberd's `node_pep` plugin actually honors
  `default_node_config.access_model` the same way generic pubsub nodes do — rather than
  hardcoding presence-based auto-subscribe regardless of node config — is not yet verified. This
  has to be confirmed against the `tests/xmpp/docker-compose.yml` harness before any production
  ejabberd config changes; see the implementation plan's open questions.
