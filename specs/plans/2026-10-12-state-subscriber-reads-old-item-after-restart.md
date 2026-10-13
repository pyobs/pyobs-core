# A fresh state subscriber reads the old process's item after a module restart

Status: waiting for evidence (2026-10-12); nothing implemented

Repos: pyobs-core

## Context

#952 item 7, as filed: "On ejabberd, a fresh subscriber to a state node after a module restart
received the OLD process's item (38.7 s old, twice) although the new process had published.
Observation only, not traced; `get_items(max_items=1)` at xmppcomm.py#L1174" (v2.14.2).

What we know: only this report. No log, no node or interface name, no information on how the age
was measured. Everything below was done by reading code on `develop` (`5ff43e6b`); nothing was run
against a server. Each statement is marked **[code]** (read from code), **[inferred]** (follows
from code but not tested) or **[unverified]**.

## Findings

### Subscribe path (`pyobs/comm/xmpp/xmppcomm.py`)

- **[code]** `_subscribe_state` (1501) adds the node to `_state_node_handlers` and starts
  `_subscribe_with_retry` (1436) as a background task. If the node is already subscribed, the new
  callback gets a one-off read through `_fetch_and_dispatch_state` (1237) instead.
- **[code]** `_subscribe_with_retry` retries the subscribe IQ with `_retry_delay` (52, jittered,
  capped at 30 s). After it succeeds, it calls `get_items(max_items=1)` (1485-1486) and passes the
  returned item to all callbacks of the node. `_fetch_and_dispatch_state` does the same (1246-1247).
- **[code]** Live notifications are handled synchronously in `_handle_event_sync` (1103, state
  branch 1119-1128). Notifications with a `<delay>` element are dropped (1121), so the last item
  that ejabberd sends on subscribe is ignored, and the `get_items` result is the only initial value.
- **[code]** State has no age check, no process identity and no ordering check. Events, by
  contrast, are dropped when older than 30 s (1180-1185). The only freshness tool for state is the
  opt-in `max_age` of `Proxy.get_state` (`proxy.py:176`) and `Proxy.wait_for_state`
  (`proxy.py:207`), which uses the state's `time` field. Not all state classes have one.

### Publish path

- **[code]** `_set_state` (1263) publishes without an item id. slixmpp then omits the id
  (`xep_0060/pubsub.py`, `publish(..., id=None)`), so the server generates a new one each time.
  No item id is reused, and a new process never overwrites the old process's item.
- **[code]** State nodes are not created up front (only event nodes, `_create_node` at 1051,
  called at 1016). They are created on first publish with the server's default node config. Nothing
  purges or retracts state items on restart, so the old process's items stay on the node.
- **[code]** When a restarted module first publishes depends on the module. Some publish only in
  background loops, e.g. `BaseTelescope` publishes alt/az in `_update_celestial_headers`
  (`basetelescope.py:881`), called from a loop that sleeps 30 s (`basetelescope.py:862`). Nothing
  makes a module publish its states before `mark_ready()` (`module.py:907`) or before a subscriber
  reads the node.

### Explanations, ranked

1. **Read before publish.** The subscriber read the node before the new process's first item
   reached ejabberd, so the newest item was still the old one. **[inferred]** from the publish path
   above. "Had published" in the report may mean the publisher's view, not the server's.
   *Confirmed by:* timestamps of the publisher's first publish (IQ acknowledged) and of the
   subscriber's `get_items` for the same node.
2. **Old value overwrites new in the subscriber.** If the `get_items` result (old item) and the
   live notification for the new item arrive in the same read, the synchronous notification
   handler runs first, and the resumed `get_items` coroutine then dispatches the old item on top.
   The subscriber stays stale until the next publish, which for rarely changing states may be never.
   **[inferred]**, depends on slixmpp's dispatch order (not verified).
   *Confirmed by:* a subscriber log that shows both deliveries, the new one first.
3. **ejabberd returns a non-newest item.** XEP-0060 says `max_items` returns the most recent items;
   a backend, cache or cluster setup might not. **[unverified]**
   *Confirmed by:* the raw `get_items` response (item id) and the server's `mod_pubsub` settings
   (backend, `last_item_cache`, default `max_items`).
4. **Stale proxy cache.** Low. The proxy cache is cleared on presence unavailable:
   `_jid_got_offline` (897) sends a local `ModuleClosedEvent` (921), and
   `Comm._client_disconnected` (`comm.py:262`) calls `clear_state()` (`comm.py:273`). A truly fresh
   subscriber has no cache at all. **[code]**
   *Confirmed by:* the subscriber not having seen the old process go offline (no unavailable
   presence logged).

### The 38.7 s

It matches no timer in the code: `_retry_delay` is capped at 30 s and jittered, `_safe_send`
waits 15 s per attempt (240) for up to 5 attempts (238), the telescope's celestial loop sleeps
30 s. **[inferred]** Most likely it is the time since the old process's last publish plus the
restart time. That a 30 s publisher yields an item 38.7 s old fits a restart gap. Seeing the same
number twice cannot be explained without the log.

### Relation to the ejabberd shaper notes

Plausible, not proven. Earlier incidents on our own deployments showed ejabberd queueing stanzas
per connection (shaper throttling, a c2s socket stall) and releasing them in bursts. That would
delay the new process's publish (explanation 1) and make it more likely that the `get_items` result
and a live notification arrive in one read (explanation 2).

## Evidence requested

A comment on #952 on 2026-10-12
(https://github.com/pyobs/pyobs-core/issues/952#issuecomment-6130076814) asked for:

- the subscriber's log with timestamps, showing whether the new item was also delivered live and
  in which order relative to the `get_items` result;
- the node name (module and interface);
- the restarted module's log around its first publish;
- how the 38.7 s age was measured;
- the server's `mod_pubsub` settings.

## Candidate fixes

### (a) Skip a stale initial read if a live item arrived meanwhile (cheap)

Only implement if the log shows explanation 2. Cost: about 15 lines and unit tests, no server.

- [ ] `_handle_event_sync`: increment a per-node counter (`self._state_live_seq[node]`) for each
      dispatched live state item.
- [ ] `_subscribe_with_retry`: read the counter before `get_items`; after the result arrives,
      skip the dispatch if the counter changed.
- [ ] `_fetch_and_dispatch_state`: same check.
- [ ] Clean up the counter in `_unsubscribe_state` when the node's last callback goes.

Tests (unit, no ejabberd):

- [ ] A live notification dispatched while `get_items` is pending: the callback sees only the
      live item, the `get_items` item is not dispatched.
- [ ] No live notification: the `get_items` item is dispatched as today.
- [ ] Same two cases for `_fetch_and_dispatch_state`.
- [ ] Counter removed after the last unsubscribe.

### (b) Keep the newer of two values

When both values have a `time` field, dispatch the `get_items` item only if it is newer than the
last live one. Cost: small, but only works for state classes with `time`, so it covers fewer
cases than (a).

### (c) Publish own states before `mark_ready()`

Make every module publish its current states in `open()`, before presence goes out, so the
newest item on each node is from the new process. Fixes explanation 1. Cost: extra IQs per
interface at startup, exactly where the shaper notes say startup is already sensitive, plus a
change to every module that publishes only in loops. Purging own state nodes on open has the same
cost.

### (d) Process id in the payload

Rejected: every state payload and every consumer (including non-Python clients) would change, for
a check that (a) to (c) cover more cheaply.

## Decision

No decision yet. If the log points to a cause and a fix among (a) to (c) is chosen, an ADR is
written for it.

## Not verified

- slixmpp's dispatch order for a synchronous handler vs a resolved IQ future in the same read
  (explanation 2).
- ejabberd's `max_items` ordering and default node config (`max_items`, `persist_items`,
  `last_item_cache`) on the reporter's server.
- Which node and interface the report concerns, and how the 38.7 s age was measured.

## Out of scope

#952 items 1 to 6 and 8 (done).
