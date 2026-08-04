# Plan: Advertise event send/subscribe role in disco#info

Status: pyobs-core landed, pyobs-web-client pending
Repos: pyobs-core, pyobs-web-client

## Problem

`Comm.register_event(event_class, handler=None)` is the single entry point for a module
declaring interest in an event: called without a handler when a module only *sends* the event
(e.g. `basecamera.py` registering `NewImageEvent`), and with a handler when it *subscribes*
(e.g. `basecamera.py` registering `BadWeatherEvent, self._abort_weather`). Both cases are folded
into one undifferentiated set, `Comm._registered_events` (`pyobs/comm/comm.py:437`), with no
record of which. `XmppComm._get_disco_info` (`pyobs/comm/xmpp/xmppcomm.py:988`) then publishes
that whole set as `<event>` schema elements — so today's disco#info advertises the union of
send and subscribe with no way to tell which is which.

This isn't a hypothetical gap — confirmed live against a real ejabberd + `pyobs-core` 2.0
backend, not just read from source: with every weather-emitting module (`MockWeather`/`Weather`)
fully offline, `BadWeatherEvent` still showed up in a `pyobs-web-client` prototype's disco#info
parse, attributed to `camera` — a `DummyCamera` module that only *subscribes* to it
(`BaseCamera.open()` unconditionally calls `register_event(BadWeatherEvent, self._abort_weather)`)
and never emits it. From a client with no way to tell send from subscribe, that's
indistinguishable from `camera` being a real source of the event — the exact ambiguity this plan
exists to fix, reproduced first-hand rather than assumed from reading `comm.py`.

`pyobs-web-client` hit this while prototyping the send-event tool that motivated this plan (see
`pyobs-web-client/specs/design/events-page-send-tool.md` — as of this writing, that prototype was
built far enough to confirm the problem live, then reverted pending this fix, so treat any
`EventsView.vue`/`useXmpp.ts` line references there as describing intent, not present-tense
committed code):

- The intended `fetchModuleInfo` behavior parses every `<event>` element from disco#info and
  subscribes to *all* of them via PubSub, under the assumption that each one is "every event this
  module publishes." Events a module only registered to *receive* (`register_event(X, handler)`)
  would get a pointless subscribe attempt against a node the module never publishes on.
- The send-event tool wants to let you pick "which module reacts to `BadWeatherEvent`" so you can
  test e.g. whether a roof module parks safely — but since disco#info can't tell sender from
  subscriber, the prototype gave up on a module-scoped picker and flattened to "the union of
  every currently-online module's own declared events," unable to say which declaring module (if
  any) was the real source versus just a reactor.

Both are downstream of the same fix. `pyobs-web-client` has no Python runtime and can't import
`pyobs.events` to get the full event catalog the way `pyobs-gui` does (its schema entirely comes
from live disco#info) — so a `role` attribute isn't just an introspection nicety there, it's the
only way that project can ever answer "what can I safely send to this module" or "who actually
emits this event" at all.

Separately: `Comm.unregister_event` (`pyobs/comm/comm.py:455`) only removes a handler from
`_event_handlers`; it never touches `_registered_events`. A module that unsubscribes from an
event keeps advertising it forever. Fixing this is folded into this plan since it's the same
code path and the new `role="subscribe"` advertisement would otherwise go stale on unregister.

## Architecture

Replace the single `_registered_events: set[type[Event]]` with two sets, populated based on
whether `register_event` was called with a handler:

- `_events_sent: set[type[Event]]` — event classes registered with `handler=None`
- `_events_subscribed: set[type[Event]]` — event classes registered with a handler

A module in both sets for the same event class (sends and self-consumes) is legitimate and
requires no special-casing — it's just membership in both sets.

`_get_disco_info` iterates the union and tags each `<event>` element with a `role` attribute
computed from set membership: `"send"`, `"subscribe"`, or `"send subscribe"` (space-separated,
XML-idiomatic for multi-valued attributes). This is additive to the existing element — existing
XML consumers ignore unknown attributes, so it's backward compatible for anything that doesn't
already special-case `role`. `pyobs-gui` doesn't parse the raw `<event>` XML at all
(`pyobs_gui/mainwindow.py` only calls `Comm.register_event(...)`, same as any other module), so
it's unaffected. `pyobs-web-client` does parse it directly and needs updating in the same
change — see the `pyobs-web-client` rows below.

For unregister: `unregister_event` removes the event class from `_events_subscribed` once no
handlers remain for it (mirroring the existing per-handler removal from `_event_handlers`). No
explicit republish step is needed — `_get_disco_info` is computed fresh on every disco#info
query (it strips and re-appends its `<event>`/`<capabilities>`/`<interface>` elements each call,
see the existing dedup loop at the top of the method), so the next query already reflects the
narrowed or dropped role. If the event class is still in `_events_sent` (module still declares it
sends the event), it stays advertised with `role="send"`.

`LocalComm` has no disco#info equivalent (no XMPP peer discovery), so this only touches
`XmppComm`. `Comm._registered_events` itself (the base-class attribute) is replaced by the two
sets in all subclasses that reference it.

## File Map

pyobs-core:

| File | Change |
|---|---|
| `pyobs/comm/comm.py` | Replaced `_registered_events` with `_events_sent`/`_events_subscribed`; `register_event` populates one or both based on `handler is None`; `unregister_event` removes from `_events_subscribed` when no handlers remain for the class |
| `pyobs/comm/xmpp/xmppcomm.py` | New pure helper `_event_role(ev_cls, events_sent, events_subscribed)`; `_get_disco_info` iterates `_events_sent \| _events_subscribed` and sets the `role` attribute via that helper. `serializer.py` was left untouched — the attribute is set post-hoc on the element `_event_schema_to_xml` already returns |
| `tests/comm/test_events.py` | Rewrote the old "leaves registered events intact" test (asserted the pre-fix union behavior) into three tests: drops subscribed role when last handler removed, keeps subscribed role while other handlers remain, leaves sent role untouched by unregister |
| `tests/comm/test_event_role.py` | New — unit tests for `_event_role` (send-only, subscribe-only, both, unrelated event) |
| `CHANGELOG.rst` | Entry added under `v2.0.0.dev53 (unreleased)` |

pyobs-web-client:

| File | Change |
|---|---|
| `src/pyobs-codec.ts` | `EventSchema` gains a `role: 'send' \| 'subscribe' \| 'send subscribe'` field parsed from the new attribute |
| `src/composables/useXmpp.ts` | `fetchModuleInfo` (`L129-180`) only PubSub-subscribes to schemas whose role includes `'send'`, instead of subscribing to every advertised event |
| `src/views/EventsView.vue` | Send-event tool's `eventOptions` (`L65-77`) can now filter/label by role — surface which module(s) actually *receive* a given event, addressing the comment at `L18-28` about the shown module usually being the wrong one |
| `src/__tests__/pyobs-codec.spec.ts` | Test coverage for `role` parsing |

## Tasks

pyobs-core:

- [x] Replace `Comm._registered_events` with `_events_sent` / `_events_subscribed`
- [x] Update `register_event` to populate the correct set(s)
- [x] Update `unregister_event` to drop the event from `_events_subscribed` once its last
      handler is removed, leaving `_events_sent` membership untouched
- [x] `XmppComm._get_disco_info`: emit `role` attribute from set membership (via new
      `_event_role` helper)
- [x] Confirmed no explicit republish step needed — `_get_disco_info` runs fresh per query
- [x] Test coverage: `tests/comm/test_events.py` (set-membership semantics) and
      `tests/comm/test_event_role.py` (role string computation)
- [x] `CHANGELOG.rst` entry
- [ ] Grep any other sibling repo (hardware-driver plugins, `pyobs-polaris`) for
      `urn:pyobs:event` before landing, now that `pyobs-web-client` has confirmed at least one
      external consumer depends on the raw XML shape

pyobs-web-client (blocked on the pyobs-core `role` attribute landing):

- [ ] Parse `role` into `EventSchema` in `pyobs-codec.ts`
- [ ] `fetchModuleInfo`: only subscribe to PubSub nodes for schemas with `role` including `send`
- [ ] `EventsView.vue`: use role to fix the module-picker gap described in the `L18-28` comment —
      show which module(s) actually handle a selected event, not just whichever happens to
      advertise it
- [ ] Test coverage in `pyobs-codec.spec.ts`
