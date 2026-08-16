# Event delivery moves from PEP presence auto-subscribe to explicit pubsub subscription

status: proposed
date: 2026-08-16

## Context and Problem Statement

The LogEvent double-delivery investigation (`specs/plans/2026-08-08-logevent-double-delivery-investigation.md`,
`logevent-double-delivery-fix-discussion.md`) established that event delivery in `XmppComm`
already rides entirely on XEP-0163 PEP presence auto-subscribe, via the server-provisioned
shared roster (`srg_user_add @all@`). `add_interest()`'s `+notify` disco/caps declaration — the
thing that looks like it expresses "I want this event type" — has no effect on delivery at all;
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

`XmppComm` already solves this exact problem for a different payload: module *state*. State
delivery does not use PEP at all. It uses a separate, already-configured shared pubsub
component, `pubsub.<domain>` (`self._pubsub_service`, `xmppcomm.py:240`), with plain XEP-0060
explicit subscribe/unsubscribe and node names that encode the publishing module
(`_state_node(module, interface)`, `_subscribe_state`/`_subscribe_with_retry`/`_unsubscribe_state`,
`xmppcomm.py:1120-1199`). This has been running in production for state delivery already —
proof that explicit-subscription delivery over `pubsub.<domain>` works with the ejabberd config
pyobs already ships, with no server-side changes needed.

## Considered Options

* Leave delivery as-is: every module receives every event over the wire and filters at the
  application layer. Zero delivery-layer change, but the network/parse cost scales with fleet
  size × event volume, paid by every module for events nobody there wants.
* Narrower shared-roster groups (per-module opt-in groups instead of one `@all@`), keeping
  presence as the delivery gate. Coarser than per-event-type (a module either gets everything
  from a peer or nothing), and leaves presence doing double duty (liveness + delivery).
* Explicit subscription on PEP: keep publishing events via XEP-0163 (each module's own bare JID
  as an implicit pubsub service), but change PEP node `access_model` from the implicit `presence`
  (auto-subscribe) default to `open`, and have each module explicitly subscribe to a peer's event
  nodes. Rejected below.
* Move events onto the same mechanism state already uses: publish to `pubsub.<domain>` under a
  node name that encodes the publisher (`pyobs:event:{module}:{EventClass}:{version}`), and have
  each module explicitly subscribe to a peer's event nodes there, mirroring
  `_subscribe_state`/`_subscribe_with_retry`/`_unsubscribe_state` almost exactly.

## Decision Outcome

Chosen option: move events onto `pubsub.<domain>`, mirroring the existing state-node mechanism.

- It matches the semantics `add_interest()`'s `+notify` declaration always implied but never
  actually delivered on.
- Presence keeps its one existing job (liveness/state); explicit pubsub subscription becomes the
  one and only thing gating delivery, for both state and events, via the same service.
- No new client dependency and no new pattern: `xep_0060` (PubSub) is already registered in
  `XmppClient` (`xmppclient.py:61`), and the subscribe/retry/unsubscribe code shape already
  exists and is already proven for state — this is substantially a reuse, not new design.
- No server-side ejabberd config change required at all. `pubsub.<domain>` and its
  `access_createnode`/`plugins: [flat]` config already exist in both the test harness
  (`tests/xmpp/ejabberd.yml`) and production (`scripts/xmpp/install-ejabberd.sh`'s
  `ejabberd-contrib` baseline), because state delivery already depends on them.

The PEP-`access_model` option was rejected: it depends on unverified behavior of ejabberd's
`node_pep` plugin (whether it actually honors `default_node_config.access_model` the way generic
pubsub nodes do, or hardcodes presence-based auto-subscribe regardless of node config) — a real
risk with no way to de-risk it other than to test against a live server, when a mechanism that
sidesteps the question entirely (because it isn't PEP) already exists in this same file and
already works. Narrower shared-roster groups were rejected as a stepping-stone at best: pyobs's
own double-delivery discussion doc concludes this is "probably why interest was added in the
first place — intent was filtering, but the roster defeats it," i.e. a variant of this has
effectively already been tried in spirit for events, and it doesn't reach per-event-type
granularity. Leaving delivery as-is was rejected because it doesn't address the actual driving
concern (bandwidth/parse overhead scaling with fleet size), which is the whole reason this ADR
exists.

### Consequences

* Good, because filtering finally exists at the delivery layer — bandwidth/parse savings
  proportional to how narrow each module's `_event_handlers` actually is.
* Good, because presence and pubsub subscription each go back to a single, non-overloaded job.
* Good, because no ejabberd config or restart is needed at any site — this is a client-only
  change, unlike the PEP-`access_model` option, which would have required a coordinated
  server+client cutover per site.
* Bad, because publish and subscribe both need every module's own module name embedded in the
  node id (`_event_node(module, event_class)`, mirroring `_state_node`), where PEP delivery never
  needed to know the publisher's identity explicitly (it published to its own implicit service).
  This is a mechanical addition, not a design risk — `_state_node` already does the same thing.
* Bad, because old (PEP/presence-based) and new (explicit `pubsub.<domain>`) modules cannot
  interoperate during a rollout: an old-code publisher never publishes to `pubsub.<domain>`, and
  a new-code subscriber never subscribes via PEP/presence. Per the implementation plan
  (`specs/plans/2026-08-16-explicit-pubsub-event-subscriptions.md`), this requires a coordinated
  fleet restart onto the new pyobs-core release per site, not a staged rollout — but with no
  ejabberd config change involved, that coordination is now "restart pyobs modules," not "restart
  ejabberd."
