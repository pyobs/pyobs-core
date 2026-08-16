# Plan: Explicit pubsub subscriptions for event delivery

Status: proposed

Decision record: `specs/adrs/0012-event-delivery-explicit-pubsub-subscription-not-presence.md`.
Background: `logevent-double-delivery-fix-discussion.md`,
`specs/plans/2026-08-08-logevent-double-delivery-investigation.md`.

## Problem

See the ADR for the full context. Summary: today every module receives every other module's
events over the wire regardless of interest, because delivery rides on presence auto-subscribe
(shared roster `@all@`), and filtering only ever happens after the fact at the application layer.
This plan replaces that with real delivery-layer filtering: explicit XEP-0060 pubsub
subscriptions per event type, with PEP node `access_model` moved off `presence` so delivery no
longer piggybacks on the roster.

Rollout mode (per discussion, 2026-08-16): coordinated cutover — a site's ejabberd config and all
its modules move together in one maintenance window. Not staged/mixed-version. Scope: all event
types from day one, not just `LogEvent`.

## Open questions to resolve before writing production config

- Does ejabberd's `node_pep` plugin actually honor `mod_pubsub.default_node_config.access_model`,
  or is presence-based auto-subscribe hardcoded into that plugin regardless of node config? This
  determines whether the server-side change below is achievable via `default_node_config` at all,
  or whether nodes need per-node `configure` at creation time instead. **Resolve against the
  `tests/xmpp/docker-compose.yml` harness (step 1 below) before touching
  `scripts/xmpp/install-ejabberd.sh` or any production site.**
- `open` vs `whitelist` access_model: with `open`, any JID can subscribe without owner approval;
  with `whitelist`, the node owner (each module, for its own events) must explicitly approve each
  subscriber via `set_affiliations`. Given the fleet is already a closed, mutually-trusted set
  (server-provisioned accounts + shared roster), `open` is the simpler match and is the working
  assumption below — but this is a trust-model call, not just a technical one. Flag for sign-off,
  don't just default to it silently.
- Does a stale pubsub subscription (peer's bare JID persists across module restarts) ever need
  explicit cleanup, or does ejabberd handle it transparently since the JID is the same account
  before and after restart? Expected: no cleanup needed, subscriptions are keyed on JID not
  session — verify in testing (step 6 below) rather than assume.

## Design

### Server-side: ejabberd PEP node access model

Change `modules.mod_pubsub.default_node_config.access_model` from the implicit `presence`
default to `open`, in two places:

1. `tests/xmpp/ejabberd.yml` — the test harness, changed first so the open questions above can
   actually be answered before anything production-facing is touched.
2. `scripts/xmpp/install-ejabberd.sh` — add a new idempotent step (following the existing
   pattern of steps 1–6b: a single `yq eval -i` merged into the existing
   `modules.mod_pubsub.default_node_config` map, not a wholesale replace, so it composes with the
   `max_items`/`persist_items`/`send_last_published_item` keys already set by the test config's
   equivalent block). Runs through the script's existing backup/validate/restart/rollback
   machinery unchanged — no new failure-handling needed, that's already there.

### Client-side: `pyobs/comm/xmpp/xmppcomm.py` + `pyobs/comm/comm.py`

- `_register_events` (`xmppcomm.py:802`): `add_interest()` is already gone (separate near-term
  fix). Leave `xep_0030.add_feature` as-is — that's unrelated discovery advertising (used by
  pyobs-web-client per the `_event_role` comment at `xmppcomm.py:40`), not a delivery mechanism.
- New: subscribe to a peer's event nodes when that peer comes online. Hook into the existing
  `_got_online` handler (`xmppcomm.py:~630`, after interfaces are resolved for the JID) — for
  every event class currently in `self._event_handlers`, call
  `self.client.plugin["xep_0060"].subscribe(peer_bare_jid, node=f"urn:pyobs:event:{ev.__name__}:{ev.version}")`.
- New: handle handlers registered *after* startup. `Comm.register_event()` (`comm.py`) can be
  called any time, not just at connect. When a new event class gains its first handler, walk
  `self._online_clients` and subscribe to that event's node on each already-online peer — same
  call as above, just triggered from `register_event()` instead of `_got_online`.
- New: unsubscribe when the last handler for an event class is removed.
  `unregister_event()` (`comm.py:~474`, where `_events_subscribed.discard(ev)` already happens)
  — call `xep_0060.unsubscribe(...)` for that event's node on each currently-online peer. No
  bookkeeping needed for offline peers: a fresh subscribe cycle happens next time each comes
  online via `_got_online`, so there's nothing stale to clean up on their side either.
- `_got_offline` / `_jid_got_offline`: no explicit unsubscribe call on our side. Confirm in
  testing (step 6) that this doesn't leave clutter — expected not to, since the subscription is
  keyed on the peer's persistent bare JID, not the session that created it.
- `xep_0060.subscribe()` must be safe to call repeatedly for the same (peer, node) pair — e.g. a
  reconnect re-running `_got_online` for a peer already subscribed to. Per XEP-0060 this should be
  idempotent (re-subscribing returns the existing subscription), but verify against the harness
  rather than assume (step 4).

### Removed / unchanged

- `add_interest()` — already removed by the separate double-delivery fix; not reintroduced here.
- `ModuleOpenedEvent` / `ModuleClosedEvent` — generated locally in `_got_online` /
  `_jid_got_offline` via direct `_send_event_to_module` calls, not via pubsub. Unaffected by this
  change; confirm in testing (step 7) rather than assume.

## Testing / validation (`tests/xmpp/docker-compose.yml` harness)

1. Set `access_model: open` in `tests/xmpp/ejabberd.yml`, bring up the compose harness. This is
   also how the first open question above gets answered — if PEP delivery doesn't change
   behavior at all with this set, the plugin isn't honoring it and the design needs revisiting.
2. Core behavior: client A registers a `LogEvent` handler, client B does not. Publish a
   `LogEvent` from client C. Confirm A receives it and B never sees the wire message at all (not
   "receives and drops" — this is the actual change from today, where B currently does receive
   and silently discard it).
3. Regression guard: confirm no duplicate delivery reappears — the `add_interest()` mechanism
   that caused the `ms` double-send must stay removed, and this change must not reintroduce a
   second delivery path.
4. Late subscribe: module A registers a handler *after* module C has already been online and
   publishing for a while. Confirm A starts receiving once its subscribe IQ completes, without
   needing a reconnect.
5. Unregister: A calls `unregister_event()` for `LogEvent`. Confirm no further `LogEvent`
   messages arrive at A after the unsubscribe completes.
6. Restart: module A restarts (new session, same bare JID). Confirm events resume without manual
   resubscription — A's own startup re-subscribes to already-online peers, and peers' `_got_online`
   handling re-subscribes to A when A reappears. Also confirms the third open question (no stale
   subscription cleanup needed).
7. Confirm `ModuleOpenedEvent`/`ModuleClosedEvent` still fire normally (they bypass pubsub
   entirely, so this is a sanity check, not expected to need any change).

## Rollout (coordinated cutover, per site)

1. Ship the pyobs-core client-side change; every module at a site must be running the new version
   before that site's cutover — mixed old/new is not supported (ADR decision).
2. Run `scripts/xmpp/install-ejabberd.sh` against the site with the new access_model step. This
   restarts ejabberd (existing script behavior) — schedule a maintenance window.
3. Restart every module at the site so they pick up the new client code and run their
   subscribe-on-peer-online logic against the now-`open` nodes.
4. Order: dev/`ms` first (already the site used for the double-delivery fix's own validation),
   then IAG50, then remaining sites one at a time. Reuse the monitoring approach from the
   double-delivery fix's rollback plan — watch for modules going silent on events they should be
   receiving.
5. Rollback: revert `access_model` to `presence` (re-run the install script after reverting the
   config, or restore its `.bak.<timestamp>` file) and roll back the pyobs-core release on that
   site's modules. Delivery reverts to today's auto-subscribe "everyone gets everything" — no
   data loss.
