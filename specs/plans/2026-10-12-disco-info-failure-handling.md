# XMPP: failed disco#info treated as "no interfaces", silent event drops

Status: implemented (2026-10-12), all open questions answered with the recommendation. Deviation: the
retry also gets cancelled for all peers in `_disconnected`, and `_got_online` was split into
`_got_online` (retry handling) and `_process_online` (the actual work, also called by the retry).

Repos: pyobs-core

## Context

#952 items 3, 5 and 6 (items 1 and 2 fixed in PR #955). Checked against `develop` (`d7da2ad2`);
line numbers below are for that commit, not v2.14.2.

Items 3 and 5 have one cause: `XmppComm._get_interfaces` (`xmppcomm.py:511`) returns `[]` both
for "peer answered, but has no IModule" and for "disco#info failed". `_got_online` then acts on
`[]` as if the peer were a non-pyobs client.

What actually happens on a failed disco#info:

1. `_safe_send` (`xmppcomm.py:1117`) retries only `IqTimeout`/own `TimeoutError`, 5 attempts x
   15 s plus jittered waits (~80 s). `IqError` is not retried at all and returns `[]` at once.
   The "3 attempts" in the issue is the recursion at `xmppcomm.py:560-566`, which only runs when
   disco#info *answered* without IModule, not on errors.
2. `_peer_sent_events[jid]` is never set (`xmppcomm.py:547` is after the early return).
3. `_got_online` (`xmppcomm.py:718-727`) resolves the `_interface_cache` future with `[]` and
   returns early: the peer is not added to `_online_clients`, no presence callbacks fire, no
   `ModuleOpenedEvent`, no event subscriptions. So the peer is invisible, not only its events.
4. Nothing retries. slixmpp fires `got_online` only when the bare JID had no available resource
   before (`slixmpp/roster/item.py:372-379`), and `_got_presence_update` (`changed_status`)
   ignores JIDs not in `_online_clients` (`xmppcomm.py:804`). Recovery needs the peer to go
   offline and come back.
5. `_register_events` (`xmppcomm.py:931-933`) only loops `_online_clients`, so a peer stuck in
   this state is also skipped for handlers registered later. No separate fix needed there once
   `_got_online` succeeds eventually; it then subscribes to every handler in `_event_handlers`.
6. Item 5: `Comm._get_client` (`comm.py:133-154`) awaits `get_interfaces`, gets `[]`, and caches
   `Proxy(self, client, [])` in `_proxies`. It is only evicted by `_client_disconnected`
   (`comm.py:269`, on `ModuleClosedEvent` from `_jid_got_offline`). Every
   `proxy(name, ITelescope)` until then fails with "not of requested type".

Also found:

- `_get_interfaces` raises a bare `IndexError` on a malformed answer (`xmppcomm.py:535-536`).
  In `_got_online` that escapes the handler and leaves the future pending, so every later
  `get_interfaces()`/`proxy()` for that JID hangs (no timeout on `await self._interface_cache[client]`,
  `xmppcomm.py:509`). Same bug class as the one `test_got_online_resolves_future_when_no_interfaces_found`
  covers for `[]`.
- `_jid_got_offline` pops `_interface_features` but not `_peer_sent_events` (`xmppcomm.py:847`).
  Stale but harmless today, since a successful disco#info overwrites it.

Item 6: `_handle_event` drops events with `time.time() - event.timestamp > 30` without a log line
(`xmppcomm.py:1109-1112`). Offline-stored messages are already filtered by the `<delay>` check
above it, so this branch mostly catches clock skew and late delivery, both worth seeing.

Callers of `get_interfaces`/`_get_interfaces` (all checked):

- `XmppComm._got_online` is the only caller of `_get_interfaces`.
- `Comm._get_client` catches `IndexError` and returns `None` (`comm.py:137`), which
  `_resolve_proxy` turns into `ValueError("Could not create proxy ...")`.
- `XmppComm._supports_interface` via `Comm.clients_with_interface` (`comm.py:308`, used by
  `mixins/fitsheader.py:45`): only iterates `self.clients`, so a failed peer is never queried.
- `PushNotifier` (`modules/utils/pushnotifier.py:192`) catches `Exception`.
- `LocalComm.get_interfaces` returns `[]` for a client without module; `DummyComm` similar.

## Proposed changes

1. **`XmppComm._get_interfaces`** returns `list[str] | None`:
   - `None` on `IqError`/`IqTimeout` (after `_safe_send`'s retries), on `info is None`, and on
     the `TypeError` path (replaces `raise IndexError()`).
   - `[]` stays for "answered, no IModule after the existing 3 x 5 s retries" (genuinely not a
     pyobs module). Recursion passes `None` through.
2. **`XmppComm._got_online`**, on `None`:
   - log a warning once (`"disco#info for %s failed (%s), retrying in background"`),
   - fail the pending `_interface_cache` future with `IndexError` (and mark it retrieved), then
     pop the entry, so waiters and later callers get `IndexError` -> `proxy()` raises
     "Could not create proxy" instead of a wrong-type error or a hang,
   - start `_retry_discovery(msg)` as a task in a new `self._discovery_retries: dict[str, Task]`,
     unless one is already running for that JID, and return.
   On success, cancel/drop any `_discovery_retries[jid]` entry.
3. **New `XmppComm._retry_discovery(msg)`**: loop with `_retry_delay(attempt)` (1 s base, 30 s
   cap, same as `_subscribe_event_with_retry`), stop when the JID went offline or is already in
   `_online_clients`, otherwise re-run `_got_online(msg)`. Warning again at attempt 30, info on
   recovery. Unbounded while the peer is present, like the event/state subscribe loops.
4. **`XmppComm._jid_got_offline`**: cancel and pop `_discovery_retries[jid]`, pop
   `_peer_sent_events[jid]`.
5. **`Comm._get_client`**: do not store a `Proxy` with an empty interface list in `_proxies`;
   return it uncached. Backend-independent guard for item 5 (LocalComm and the remaining XMPP
   `[]` case).
6. **`XmppComm._handle_event`**: before the 30 s drop, `log.info("Dropping %s from %s, %.1f s old.",
   type(event).__name__, from_module, age)`.

`_register_events` (`xmppcomm.py:932`) stays unchanged, see Context 5.

## Tests

All unit tests, no ejabberd, using the bare `XmppComm.__new__` pattern from
`tests/comm/test_presence.py`:

- `_get_interfaces` returns `None` when `_safe_send` raises `IqTimeout`, `None` on `IqError`,
  `None` on a malformed answer, `[]` when the answer has no IModule (patch `asyncio.sleep`).
  Fits `tests/comm/test_version_mismatch.py`.
- `_got_online` with `_get_interfaces` -> `None`: JID not in `clients`, no `ModuleOpenedEvent`,
  `get_interfaces(jid)` raises `IndexError` within the 5 s presence wait (not `[]`, no hang),
  one retry task registered.
- Retry recovers: `_get_interfaces` returns `None` then `["IModule"]` with `_peer_sent_events`
  set to `{("NewImageEvent", v)}` and a `NewImageEvent` handler registered: peer ends up in
  `clients`, `_subscribe_event_with_retry("camera", NewImageEvent)` is started,
  `ModuleOpenedEvent` sent. This is the item 3 regression test.
- `_jid_got_offline` during a pending retry cancels the task and pops `_peer_sent_events`.
- Second `_got_online` for a JID with a running retry does not start a second task.
- Existing `test_got_online_resolves_future_when_no_interfaces_found` (`[]` path) unchanged.
- `Comm._get_client` with a `DummyComm` subclass whose `get_interfaces` returns `[]` first and
  `[ITelescope]` second: second `proxy(name, ITelescope)` succeeds (item 5 regression test).
- `_handle_event` with a 31 s old event logs the drop (caplog) and does not dispatch; 29 s old
  dispatches. Fits `tests/comm/test_xmppcomm_event_payload.py`.

## Open questions

1. **Return `None` or raise from `_get_interfaces`?** Recommend `None`: private, one caller,
   and the existing `[]` contract stays readable next to it.
2. **Retry bounded or forever?** Recommend forever with 30 s cap while presence holds, same as
   `_subscribe_event_with_retry`/`_subscribe_with_retry`. A bounded retry reintroduces the
   "stuck until reconnect" state.
3. **Treat "answered, no IModule" as failure too?** Recommend no. Interfaces are advertised
   before presence is sent (`xmppcomm.py:371`, inferred from the connect order, not traced), so
   a pyobs module should never answer without IModule; the case is non-pyobs clients.
4. **Should `get_interfaces` callers wait for the retry (keep a pending future) or fail fast?**
   Recommend fail fast. The retry can run for minutes, and `get_interfaces` has no timeout on
   the future, so waiting would hang `proxy()` callers that already have their own retry loops.
5. **Log level for dropped old events?** Recommend `info`. Unverified: whether ejabberd's
   `send_last_published_item` delivers an old item on every fresh subscribe without `<delay>`
   (#952 item 7 suggests it can). If so, `info` adds one line per subscribe after a restart;
   then `debug` plus a warning above e.g. 120 s is the fallback.
6. **Uncached empty proxy in `Comm._get_client` also changes `LocalComm`?** Recommend yes,
   an empty proxy is useless to cache and re-querying `LocalComm` is cheap.

## Not verified

- No live reproduction of the race (both modules up in the same second, disco#info timeout).
  The chain above is from reading the code.
- Whether the reported disco#info failures were `IqTimeout` (~80 s budget exhausted) or
  `IqError` (no retry at all). If `IqError`, e.g. `service-unavailable` from a peer whose
  session is not fully up, the background retry covers it either way.

## Out of scope

#952 item 4 (`_get_derived_events` only walks `pyobs.events`), item 7 (old state item after
restart) and item 8 (module-specific `PyobsError` arriving as `UnclassifiedError`).
