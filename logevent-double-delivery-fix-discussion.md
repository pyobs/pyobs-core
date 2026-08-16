# Discussion: LogEvent double-delivery fix — should we drop add_interest()?

Notes from a working discussion with Tim, 2026-08-16. Companion to
`2026-08-08-logevent-double-delivery-investigation.md`.

## Proposed fix (from the investigation, point 15)

Drop `add_interest()` in `XmppComm._register_events()` (`pyobs/comm/xmpp/xmppcomm.py:813`).

Mechanism (confirmed from production debug logs): one publish triggers two
`ejabberd_sm:route_message` sends to the same session — one bare-JID-addressed (implicit,
roster-presence path), one resource-addressed (explicit interest via `add_interest()`).
Removing `add_interest()` eliminates the second send, leaving the single bare-JID copy.

## Would the fix break working systems?

In practice no, with a narrow edge case to verify first.

`add_interest()` only adds a `+notify` disco feature declaring *receive*-interest. Dropping it
removes the explicit-interest delivery path and relies entirely on implicit roster-presence
delivery (XEP-0163 `auto-subscribe`), which requires a presence subscription (`from`/`both`) from
subscriber to publisher.

Why that's safe for normal pyobs deployments:

- `XmppComm` never sends or auto-approves presence subscription requests. The only way a pyobs
  deployment has presence at all is server-side provisioning — the shared-roster setup
  (`srg_create` / `srg_user_add @all@`).
- Therefore: if a deployment works today, it already has mutual presence, and implicit delivery
  already suffices (proven by `watch_log_events_no_interest.py` — zero duplicates, all events
  received).

The one case that would break: a subscriber with no roster/presence subscription to the publisher,
where `+notify` interest was the only thing delivering. Under pyobs's `access_model: presence` PEP
nodes (the default), such a subscriber wouldn't receive anything anyway, so it doesn't represent a
currently-working system to regress.

So the caveat is real but almost certainly theoretical for pyobs: the risk exists only in a
non-standard config (e.g. `access_model: open` + no shared roster) that pyobs doesn't ship.

Verification step before the change: confirm no deployment config in the wild (IAG sites, SAAO,
etc.) sets a non-`presence` PEP access model or skips shared roster. That's a config check, not a
code question.

`access_model` isn't set anywhere in pyobs's XMPP code — it's purely an ejabberd/mod_pubsub
server-side default. So this isn't provable from the pyobs codebase alone; it has to be checked
per deployment:

- For each site (IAG Göttingen, IAG50, SAAO, monet-south, any others in production): check
  `mod_pubsub` config for `access_model` (default is `presence` unless overridden) and confirm
  shared roster is provisioned (`srg_list` / `srg_get_members @all@` showing all pyobs JIDs).
- If any site deviates (non-`presence` access model, or a subscriber without shared-roster
  membership), do not drop `add_interest()` there without first confirming that subscriber
  actually receives events today — if it does via the interest path, dropping it regresses that
  site.

## Monitoring / rollback plan

If a site turns out to have a non-standard config the check above missed, dropping
`add_interest()` would silently stop delivery to any client that relied on the interest path —
no error, just missing events.

- After deploying the fix to a site, watch that site's clients for gaps: any module that stops
  receiving expected events (log subscribers going quiet, missed state-change events) in the
  hours after rollout is the signal.
- Rollout order: `ms` first (where the bug reproduces and the fix has a clear before/after via
  `watch_log_events_no_interest.py`), then other sites one at a time rather than all at once, so a
  regression is traceable to a specific deployment's config.
- Rollback is trivial: re-adding the `add_interest()` call (`xmppcomm.py:813`) restores prior
  behavior immediately, no data migration involved.

## Did we ever need add_interest()?

Essentially no, given pyobs's setup.

`add_interest()` only affects *receiving* (declares `+notify` in disco#info/caps so a publisher
knows you want that node). It has no effect on publishing. Delivery to a pyobs client never
depended on it, because delivery rides on the roster-presence path (`auto-subscribe`), not the
caps-interest path.

It was added as "correct XEP-0163 client behavior" but was always redundant for delivery in pyobs.
It hasn't broken other servers because on every server except `ms` the routing apparently ignores
the interest path; only `ms` honors both, producing the duplicate.

Caveats:

- Holds only because pyobs uses shared roster (mutual presence) + `presence` access model. Both
  held in every config inspected so far, but that's "every config we inspected," not a proof.
- The exact reason `ms` routes both while identical configs elsewhere don't is still unresolved
  (the point-15 "why now" mystery). Dropping `add_interest()` fixes the symptom and is harmless
  elsewhere, but sidesteps that question rather than answering it.

## Was shared roster a bad idea?

No — it's the right tool for a different problem than the one it's being asked to solve here.

Shared roster (`srg_user_add @all@`) gives every module mutual presence with zero per-pair config,
which is exactly what you want for discovery/reachability in a fleet where modules come and go.
The mismatch is that presence subscription is binary per pair (subscribed or not) — it can't
express "receive LogEvent but not FocusEvent" from the same publisher. That granularity has to
live at the pubsub-node/subscription level, not the roster level.

So the roster decision was sound for connectivity. `add_interest()` was presumably added later on
the assumption it would filter delivery on top of that roster, and it can't: delivery is already
decided at the presence layer (auto-subscribe) before caps/interest is ever consulted.

## How could real interest-based filtering be achieved?

Two options, not a small tweak either way.

**Explicit pubsub subscriptions per event node.** Instead of relying on presence auto-subscribe,
each module issues a `pubsub#subscribe` IQ only for the event types in its own
`_event_handlers`, and unsubscribes when a handler is removed. Pair that with
`access_model: whitelist` (or similar) instead of `presence`, so delivery is gated by actual
subscription, not roster membership. This is the option that actually matches what
`add_interest()`'s `+notify` declaration implied in the first place — actual interest maps to
actual delivery. Cost: real protocol work, subscribe/unsubscribe lifecycle tied to handler
registration, and losing the free convenience XEP-0163 auto-subscribe currently gives you.

**Narrower shared rosters** instead of one `@all@` group — e.g. per-module opt-in groups. Coarser
(per-module, not per-event-type), but much less invasive than rewriting the subscription model.

If bandwidth/parsing overhead is the actual problem worth solving, the explicit-subscription
route is the only one that does what `add_interest()` originally implied; the roster split above
is compatible with it but doesn't by itself give per-event-type granularity. This changes
delivery semantics for every deployment, not just `ms` — worth an ADR before touching it, not a
follow-on patch to the double-delivery fix.

## Can roster and pubsub delivery be split?

Yes — and presence already has an independent job that makes this the cleaner design anyway.

`_got_presence_update` / `_fire_presence_callbacks` (`xmppcomm.py:693`) use presence for module
liveness/state tracking (online/offline/error), entirely separate from event delivery. Presence
subscription isn't free to repurpose as a delivery filter — it's already doing something else.

The split: keep shared roster exactly as is (still needed for liveness tracking across the
fleet), and change PEP nodes from `access_model: presence` to `access_model: whitelist` (or
`open`), so delivery no longer piggybacks on presence subscription at all — it depends only on
explicit pubsub subscribe/unsubscribe per node (see "explicit pubsub subscriptions per event
node" option above). That decouples "am I reachable/alive" (roster/presence) from "do I want this
event type" (pubsub subscription), which were only ever coupled because `presence` access_model
is ejabberd's default, not because pyobs needs them coupled.

## Consequence: are all events sent to all clients?

Yes, at the delivery layer.

ejabberd's PEP `auto-subscribe` delivers a publisher's events to anyone with a presence
subscription (`both`/`from`) to them. The shared roster (`srg_user_add @all@`) gives every user
mutual presence with every other user, so every client is auto-subscribed to every other client's
PEP nodes.

- **Network/XMPP layer**: all events go to all clients in the roster. Interest/caps does not
  filter delivery (interest just adds a second copy, it never narrowed the first).
- **Application layer**: pyobs only acts on events it registered a handler for. `_handle_event`
  parses everything, but `_send_event_to_module` (`comm.py:677`) drops it if the class isn't in
  `_event_handlers`.

Implications:

1. Bandwidth: every module already receives and parses every other module's events, interest or
   not. Dropping `add_interest()` won't change that, because delivery rides on the roster.
2. Real event filtering to reduce network chatter would require replacing shared-roster `@all@`
   with per-contact rosters — a much bigger change, and probably why interest was added in the
   first place (intent was filtering, but the roster defeats it).
