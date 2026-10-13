# Event subclasses outside `pyobs.events` get no handler and can't be deserialized

Status: implemented (2026-10-12), all open questions answered with the recommendation.

Repos: pyobs-core

## Context

#952 item 4. Checked against `develop` (`95a0c47e`); line numbers below are for that commit,
not v2.14.2.

`Comm._get_derived_events` (`comm.py:414-429`) returns every class in
`inspect.getmembers(pyobs.events, inspect.isclass)` that is a subclass of the given one.
"Derived" means: `register_event(X, handler)` (`comm.py:431-460`) puts the handler into
`_event_handlers` for X *and* every subclass found, because dispatch is by exact class
(`_send_event_to_module`, `comm.py:705`: `event.__class__ in self._event_handlers`). Without a
handler the same list goes into `_events_sent`.

Callers of `_get_derived_events`: `register_event` (`comm.py:441`) and `unregister_event`
(`comm.py:485`), nothing else. Downstream, everything works on the expanded list:

- `_events_sent`/`_events_subscribed` feed the rich `<event role=...>` disco#info elements
  (`xmppcomm.py:1306-1312`), which peers parse into `_peer_sent_events` (`xmppcomm.py:581`).
- `XmppComm._register_events` (`xmppcomm.py:988-1019`) adds `urn:pyobs:event:<name>:<version>`
  features, subscribes to `pyobs:event:<module>:<name>:<version>` on online peers that send it,
  or pre-creates the own node for send-only declarations.
- `XmppComm._got_online` (`xmppcomm.py:836-842`) subscribes for every key in `_event_handlers`
  the peer advertises as sent. `ev.local` events are skipped everywhere.
- `LocalComm._register_events` and `DummyComm` do nothing; `LocalComm.send_event` passes the
  event object directly to every client's `_send_event_to_module`.

What breaks for a class defined outside `pyobs.events` (verified at runtime on develop):

1. `register_event(Y)` for `class Y(Event)` defined elsewhere: `_get_derived_events(Y)` is `[]`.
   No handler, not in `_events_sent`/`_events_subscribed`, no disco feature, no node, no
   subscription. Applies to all transports, including `LocalComm` and `DummyComm`, and to the
   sender's own local dispatch.
2. `register_event(NewImageEvent, h)` with a plugin `class Y(NewImageEvent)`: the expansion is
   `[NewImageEvent]` only, so A never subscribes to B's Y node and never dispatches a Y.
3. Receiving side (XMPP only): `EventFactory.from_dict` (`event.py:38-84`) resolves `"type"` by
   `getattr` on the packages in `EventFactory.packages = ["pyobs.events"]`, so a Y payload returns
   `None` and `_handle_event` (`xmppcomm.py:1177`) drops it silently. Fixing only the expansion
   would therefore still lose Y over XMPP. `LocalComm` doesn't serialize, so it only needs (1)/(2).

No registry for events exists. `Interface` has one (`interface.py:4-42`, `__init_subclass__`,
keyed by `__name__`, `TypeError` on a name clash, `get_registered_interface`), and so does
`PyobsError` (`utils/exceptions.py:37-64`, keyed by qualified name).

Nothing relies on the restriction: `EventFactory.packages` is never modified (pyobs-core and the
sibling checkouts under `~/code/pyobs`), no test defines an `Event` subclass, and no sibling
checkout defines one either. `tests/comm/test_events.py:1-13` only *documents* the restriction
in its docstring (why it uses real `pyobs.events` classes).

Note: the wire `"type"` and the pubsub node id carry only `__name__` and `version`, not the
module. Two event classes with the same name already collide on the node id today, so the
registry has to be keyed by name and reject clashes.

## Proposed changes

1. **`pyobs/events/event.py`**: module-level `_REGISTRY: dict[str, type[Event]]`,
   `Event.__init_subclass__` registers every subclass by `__name__`, `Event` itself registered
   after the class body. Clash with a class of different `__module__`/`__qualname__` raises
   `TypeError` (same message style as `Interface`); same module and qualname replaces the entry
   (module reload, a test redefining its class). Add `get_registered_event(name)` and
   `registered_events()`, export them.
2. **`EventFactory.from_dict`**: resolve the class via `get_registered_event(obj_dict["type"])`
   instead of walking `packages`. Drop `EventFactory.packages`. Rest unchanged.
3. **`Comm._get_derived_events`**: `[cls for cls in registered_events().values() if
   issubclass(cls, event)]`, drop the `inspect`/`pyobs.events` import there if unused. Order is
   registration order, so the result stays deterministic.
4. **Import order**: expansion stays at `register_event` time. A subclass imported after the call
   is not covered. Document that in the `register_event` docstring. No dispatch-time MRO walk
   (see Open question 2).
5. **`tests/comm/test_events.py`**: update the module docstring, which describes the old
   restriction.

`XmppComm`, `LocalComm`, `DummyComm` stay unchanged; they already work on the expanded list.

## Tests

All unit tests, no ejabberd:

- `tests/test_events.py`: a `class _PluginEvent(Event)` defined in the test module is returned
  by `get_registered_event("_PluginEvent")`; `EventFactory.from_dict(_PluginEvent().to_json())`
  returns a `_PluginEvent` with uuid/timestamp kept; a subclass with data and its own `from_dict`
  round-trips; unknown type still returns `None`.
- Same file: defining a second class with an existing name in another module (create via
  `type(...)` with a different `__module__`) raises `TypeError`; redefining with the same
  module/qualname does not.
- `tests/comm/test_events.py` (bare `Comm.__new__` pattern): `register_event(_PluginEvent, h)`
  puts `h` into `_event_handlers[_PluginEvent]`, `_send_event_to_module(_PluginEvent(), "x")`
  calls it; `unregister_event` removes it.
- Same file: `class _PluginImage(NewImageEvent)` in the test module; `register_event(NewImageEvent,
  h)` covers both, and a `_PluginImage` is dispatched to `h` (the item 4 regression test).
- Same file: handler-less `register_event(_PluginEvent)` adds it to `_events_sent`.
- `tests/comm/local/test_localcomm.py`: two `LocalComm`s, A registers a handler for
  `NewImageEvent`, B sends `_PluginImage`; A's handler runs.
- `tests/comm/test_xmppcomm_event_payload.py`: `_handle_event` with a `_PluginEvent` payload
  dispatches it (today: dropped by `EventFactory`).
- Existing expansion behaviour unchanged: `register_event(MoveEvent, h)` still covers
  `MoveRaDecEvent`/`MoveAltAzEvent`.

## Open questions

1. **Name clash: raise or warn?** Recommend raise `TypeError`, like `Interface`. Two classes with
   one name already share a pubsub node and a wire type, so a warning would hide real
   misdelivery. Risk: a plugin that today defines an event named like a core one fails at import
   instead of silently not working; none found in the local checkouts.
2. **Handle subclasses imported after `register_event`?** Recommend no. Over XMPP the receiver
   must import Y anyway or `EventFactory` can't build it, and subscriptions are per concrete node,
   so a dispatch-time MRO walk would only help `LocalComm` and would call a handler twice when it
   is registered for both X and Y. Plugin event classes are normally imported with the module
   class, long before `open()`.
3. **Keep `EventFactory.packages` as a fallback?** Recommend dropping it: nothing sets it, and
   with the registry every importable `Event` subclass is found already. Removing a public class
   attribute is technically an API change; mention it in the changelog.
4. **Should B's handler-less `register_event(X)` keep advertising every imported subclass of X as
   sent?** Recommend yes for now, it's today's behaviour for core subclasses (e.g. `MoveEvent`).
   With the registry it can also include plugin subclasses B merely imported, which pre-creates
   a few extra nodes. Revisit only if that shows up in practice.

## Not verified

- No live XMPP run with a plugin event between two modules; the failure chain is from code
  reading plus a runtime check of `_get_derived_events` and `EventFactory.from_dict` on develop.
- Plugin repos outside `~/code/pyobs` (other observatories' private packages) may define event
  subclasses; a name clash with a core event would start raising at import (Open question 1).
- Whether ejabberd auto-creates a node when B publishes Y without ever registering it (today's
  case 1). Irrelevant after the fix, since registration then pre-creates the node.

## Out of scope

#952 item 7 (old state item after restart) and item 8 (module-specific `PyobsError` arriving as
`UnclassifiedError`). Same "class must be imported on the receiving side" limitation as item 8
applies to events after this change, by design.
