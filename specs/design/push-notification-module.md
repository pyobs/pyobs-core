# Push notification relay module (`PushNotifier`)

Status: implemented. Written 2026-09-09 after confirming (against current code) that the
wire-protocol prerequisite this depended on is already satisfied, and that RPC handlers can
already access caller identity via `**kwargs: Any` (§3) — both were open questions in earlier
drafts, now resolved by reading the actual dispatch code. Revised 2026-09-14: `ERROR`/`CRITICAL`
log events folded into v1 scope (§2b), alongside module `ERROR` state. Bad weather / roof-open
stays deferred. Built 2026-09-14/15 (`5b688528`, `90b7ded1`) as `pyobs.modules.utils.PushNotifier`
implementing the new `IPushNotifications` interface; `pyobs-web-client`'s `register_push_device`
call
landed the same way (`31538b7`). Both on `develop`, no PR (committed directly). Two of the three
open questions below are still genuinely open as shipped — see the note under each.
Revised (v2) 2026-09-18: per-user notification-type preferences added — the "one fixed rule set"
v1 decision below is now superseded, §6. Plan:
`specs/plans/2026-09-18-pushnotifier-per-user-preferences.md`; originating issue
pyobs-web-client#57.
Revised (v3): production incident on MONET/S documented below — the FCM 4 KB payload limit, the
notifier's own-log feedback/amplification and the abandoned-send timeout were all fixed 2026-09-23
(payload cap, own-log self-skip, per-alert failure logging, `httpTimeout`, and dead-token pruning);
see "Confirmed defects (MONET/S incident)".

Repos: pyobs-core (module implementation, all new code); pyobs-web-client (device-token
registration from `usePushNotifications.ts`, plus the v2 preference call — still to do)

Tracking issue: pyobs-core#902 (previously #884, closed for an unrelated reason — see below).

## Context

`pyobs-web-client/specs/design/native-app-shell-capacitor.md`'s Push Notifications section and
`pyobs-web-client/specs/steering/open-items.md` both flag the same gap: the client-side spike
(`usePushNotifications.ts`, live-verified end-to-end against a real Firebase project, `pyobs-51a29`)
obtains a device token and can receive a manually-sent test push, but nothing server-side ever
triggers one. `pyobs-core/specs/design/mobile-app-and-shared-ts-client-core.md` (superseded as a
whole, kept as historical record) scoped the intended alert triggers: module `ERROR` transitions,
bad weather with the roof open, guiding lost, `CRITICAL` log events — and noted "keep these
distinguishable on the wire" as an actionable prerequisite.

**Checked 2026-09-09: that prerequisite is already satisfied**, no wire-protocol change needed.
`pyobs/events/log.py`'s `LogEvent` already carries `level: str`, and `pyobs/comm/commlogging.py`'s
`CommLoggingHandler.emit()` passes `rec.levelname` straight through unfiltered — `CRITICAL`
included. `pyobs/utils/enums.py`'s `ModuleState.ERROR` and `pyobs/events/badweather.py`'s
`BadWeatherEvent` already exist and publish the same way. What's missing is purely the relay: a
component that watches these already-available signals and turns a qualifying one into an actual
push.

Discussed with Tim (2026-09-09) — decided **against** the XEP-0357/ejabberd relay route the
original design doc assumed (`mod_push` server config + a separate service translating ejabberd's
push payload to FCM/APNs). Instead: **a new `pyobs` module**, since it gets these events the same
way any other pyobs client does — no ejabberd config, no separate relay process.

## Decided for v1 (confirmed with Tim before writing this sketch)

- **Module `ERROR` state, plus `ERROR`/`CRITICAL` log events.** Bad weather with the roof open is
  real future scope (already wire-available, per above — `BadWeatherEvent`) but deliberately
  deferred — prove the FCM plumbing on these two signals first, add weather as a fast-follow once
  that's solid. Log events are folded in now rather than deferred with weather because the
  detection side is nearly free: `LogEvent` already carries `level`, and
  `Telegram._process_log_entry`'s `self.comm.register_event(LogEvent, ...)` is a five-minute port
  (§2b) — unlike module-`ERROR` detection (§2a), which is genuinely the hard part of this module.
- **One fixed rule set for the whole deployment, not per-user thresholds.** No per-user
  preferences RPC, no per-user filter config — every registered device gets every module-`ERROR`
  alert. Registration only needs a device token, nothing else. **Superseded in v2** (§6): per-user
  opt-in/out per notification *type* is now supported; what remains deliberately absent is a
  per-user *severity* threshold / module allow- and deny-lists.

## Non-goals (this sketch)

- Bad weather / roof-open alerts — real, scoped above, not this pass.
- ~~Per-user alert preferences (severity, module allow/deny-list)~~ — **partly done in v2** (§6:
  per-user type opt-in/out, which is what pyobs-web-client#57 asked for). Severity thresholds and
  module allow/deny-lists (`telegram.py`'s per-user `/loglevel` shape) remain deferred.
- iOS/APNs — blocked on the same Apple Developer Program account + Mac access constraint as
  `pyobs-web-client`'s Phase 4 (`specs/plans/2026-09-06-mobile-first-redesign.md`). FCM/Android
  only for v1.
- Any new client UI beyond what already exists — `SettingsView.vue`'s existing diagnostic panel
  (token/error/last-received) is enough for now.

## Design

Closest existing precedent in this codebase: `pyobs/modules/utils/telegram.py`. Same overall
shape — a `Module` subclass that opens a channel to an external notification service and
subscribes to pyobs events — worth reading side by side with this sketch.

### 1. Module shape

`pyobs/modules/utils/pushnotifier.py`, `class PushNotifier(Module)`. `open()` registers for the
relevant state updates (see §2); `close()` tears them down — mirrors `Telegram.open()`/`close()`.

### 2a. Detecting module `ERROR` — the actual hard part, not the FCM call

There is no single fleet-wide "a module errored" event. Each interface publishes its own state
object with its own `status` field (`comm.py`'s `subscribe_state(module, interface, callback)` is
scoped to one module + one interface at a time) — confirmed by reading
`pyobs-web-client/src/views/DashboardView.vue`'s `triageFor()`, which already solves exactly this
problem client-side: it discovers each connected module's interfaces, subscribes state for every
state-bearing one, and flags `status.toUpperCase() === 'ERROR'` on any of them as attention-worthy
(`DashboardView.vue` around line 112).

`PushNotifier` needs the same shape server-side: enumerate `self.comm.clients` (as `Telegram` does
for its `/modules` command), discover each module's interfaces, `subscribe_state(module, interface,
callback)` for every state-bearing one, and treat any `status.upper() == "ERROR"` transition as
alert-worthy. This is the bulk of the new code, not the notification-sending part — flagged here so
it isn't underestimated as "just subscribe to an event."

### 2b. Detecting log `ERROR`/`CRITICAL` events — the easy part

Unlike §2a, this is a near-direct port of existing code. `Telegram.open()` does
`self.comm.register_event(LogEvent, self._process_log_entry)`; `PushNotifier` registers the same
way. The handler differs only in what counts as alert-worthy: instead of Telegram's per-user
`loglevel` threshold, it's a fixed check — `entry.level in ("ERROR", "CRITICAL")` — matching the
"one fixed rule set for the whole deployment" decision above. `entry.message` and the `sender`
argument (the emitting module's client name, per `comm.py`'s event dispatch — not the RPC-caller
JID that §3's `register_push_device` sees) give the alert its title/body.

### 3. Device registration

A public async method on the module — any pyobs client can call it via the standard comm proxy
RPC mechanism (the same XEP-0009 machinery `pyobs-web-client` already re-implements for every
other module call):

```python
async def register_push_device(self, token: str, platform: str = "android", **kwargs: Any) -> None:
    sender = kwargs.get("sender", "")
    ...
```

**Confirmed 2026-09-09** (was an open question in an earlier draft of this sketch): an RPC handler
*does* get the caller's identity, via the same mechanism `Module.execute()` already uses for ACL
checks — `pyobs/comm/xmpp/rpc.py`'s `_on_jabber_rpc_method_call` calls
`self._handler.execute(pmethod, *params, sender=iq["from"].user, call_id=call_id)` for every RPC;
`execute()` binds those against the target method's own signature, so a method that declares
`**kwargs: Any` receives `sender`/`call_id` in it. `get_permitted_methods(self, **kwargs: Any)`
already does exactly this. `register_push_device` just needs the same `**kwargs: Any` — no new
mechanism, no separate identity scheme to design.

Storage: VFS-backed YAML, same pattern as `Telegram._save_storage`/`self.vfs.write_yaml(...)` —
`/pyobs/pushnotifier.yaml`, keyed by `sender` (the caller's JID user-part, same identity ACL
gating already treats as canonical), each value a list of `{token, platform, registered_at}`
entries — a list, not a single value, since one account's phone and tablet both registering must
both receive alerts.

**Client-side counterpart** (the only `pyobs-web-client` change this needs): once
`usePushNotifications.ts`'s `registration` listener has a token, call this RPC. Right now that
token only lands in local reactive state and `SettingsView.vue`'s diagnostic panel — this closes
exactly the gap the composable's own comment already names ("associating a token with an account
server-side is a later, not-yet-designed step").

### 4. Debounce / dedup

Two independent sources, one debounce problem. A flapping module (brief ERROR↔READY toggling)
shouldn't spam a push per transition (§2a); a module stuck retrying and logging the same `ERROR`
in a loop shouldn't either (§2b). Reuse `Telegram`'s `asyncio.Queue` + `add_background_task`-driven
sender-thread shape, including its duplicate-suppression logic (`_log_sender_thread`'s
`last_messages`/`repeat_counts`) — same problem, same fix, both sources feeding the same queue.

### 5. Sending

FCM HTTP v1 API against the already-provisioned Firebase project (`pyobs-51a29`), using a
**server-side service-account credential** — a new secret, distinct from and never overlapping
with the client-side `google-services.json`/API key already checked into
`pyobs-web-client/android/app/`. New optional dependency (likely `firebase-admin`), added to
`pyproject.toml`'s `full` extras group alongside `python-telegram-bot`/`matrix-nio`.

### 6. Per-user type preferences (v2)

Added 2026-09-18 (pyobs-web-client#57; plan `specs/plans/2026-09-18-pushnotifier-per-user-preferences.md`).
v1's "one fixed rule set" decision is superseded for *type selection* only — severity thresholds
and module allow/deny-lists stay out of scope.

The three alert kinds v1 already emits become a `PushNotificationType(StrEnum)` defined in
`IPushNotifications.py` (`MODULE_ERROR`, `LOG_ERROR`, `LOG_CRITICAL`), exported alongside the
interface. Like `TrackingMode`, the enum lands on the wire as `enum(PushNotificationType)` in
disco#info's `<types>` block, so a client can render its toggles from the schema rather than
hardcoding the names.

Preferences are **per calling account** (`sender` JID, the same identity `register_push_device`
and ACL gating already key on), not per device — every device an account registers shares one
preference. A `set_push_preferences(types: list[PushNotificationType], **kwargs: Any)` RPC stores
the chosen values, and `get_push_preferences(**kwargs)` returns the current selection (all types
when unset) so a client can render the account's actual state on connect. Both are deliberately
separate from `register_push_device`, which stays per-device and is deduped client-side, so a
preference change can't ride on it. Storage is still the single
`/pyobs/pushnotifier.yaml`, restructured to `{sender: {"devices": [...], "preferences": [...]}}`
with a read-time migration wrapping the legacy list shape.

**Default is all-on**: a sender with no `preferences` key (never set, or migrated) receives every
kind — byte-for-byte the v1 behavior, so nothing changes for an existing device until a preference
is set. An explicitly empty list means opted out of everything. Filtering happens at send time in
`_send_to_all_devices`, per sender, which is the only place it can work: the app runs no code while
closed or backgrounded, so the system tray would otherwise show whatever FCM delivered.

This is what makes §4's single global dedup still correct: for stable preferences a given alert
targets the same recipient subset every time, so anyone who would receive a repeat already received
the original. The dedup key gains the alert kind (`(kind, title, body)`) — two alerts with the same
title/body but different kinds are distinct.

**Client side (pyobs-web-client): done 2026-09-18** — the toggle UI in `SettingsView.vue` plus the
`get_push_preferences`/`set_push_preferences` calls (read on connect, write on toggle); plan
`pyobs-web-client/specs/plans/2026-09-18-push-notification-preferences.md`.

## Open questions — not resolved here, flagged for actual design/implementation

- **Stale/uninstalled-app tokens. Resolved 2026-09-23.** FCM reports a dead token as unregistered
  (`UNREGISTERED` → `messaging.UnregisteredError`, a `NotFoundError` subclass). `_send_to_all_devices`
  now catches `NotFoundError` per token, drops those tokens from `self._devices`, and persists via
  `vfs.write_yaml` (`_prune_tokens`). Deliberately does **not** prune on `InvalidArgumentError`,
  which also covers "message too large" and other non-token problems.
- **Which modules/interfaces count.** Mirroring `DashboardView.vue`'s triage exactly means
  alerting on *any* interface's `ERROR`, fleet-wide, with no allow/deny-list — same blast radius
  as what the dashboard already surfaces. **Resolved as shipped**: implemented exactly this way
  (`status.upper() == "ERROR"` on any state-bearing interface), no allow/deny-list added.
- **Log-message dedup key.** Telegram's `last_messages` dedup keys on exact message-string equality
  per user. For a retry loop logging `ERROR` with a changing detail (a timestamp, an exception
  `repr`, a retry count in the text), exact-match dedup won't catch it and every retry pushes
  separately. **Still open** — `_sender_thread`'s dedup key is `(kind, title, body)`. The 2026-09-23
  body reduction to "first non-empty line — last non-empty line" makes repeated *identical*
  exceptions dedup correctly (the traceback tail no longer differs), but a changing detail inside
  the exception message still defeats it.

## Confirmed defects (MONET/S incident)

During a partial network outage (`OSError: [Errno 113] No route to host` against
`oauth2.googleapis.com:443` while `fcm.googleapis.com` remained reachable) the notifier stopped
delivering and produced a burst of interleaved `Sending push notifications timed out.` /
`Failed to send push notification to a device.` errors, ending in FCM
`InvalidArgumentError: Message is too large. The maximum is 4K (4096 bytes).` Three confirmed
defects, all three now fixed (2026-09-23):

- **Unbounded payload — the 400. FIXED 2026-09-23** (plan
  `specs/plans/2026-09-23-pushnotifier-payload-size-cap.md`). `_send` used to pass the raw log
  message straight through as the notification body (`messaging.Notification(title=...,
  body=alert.body)`), where `alert.body` was `LogEvent.message` — i.e. a full formatted traceback,
  easily ≈4 KB. FCM's 4096-byte cap applies to the *whole serialized message* (token + title +
  body + JSON envelope), not the body alone, so exactly the highest-value alerts (crashes,
  tracebacks) could never be delivered. `_process_log_entry` now reduces the message to "first
  non-empty line — last non-empty line" (the human-facing message plus the `ExceptionType:
  message` tail a traceback ends with) and byte-caps it to `_MAX_BODY_BYTES` (3600, reserving room
  for token/title/envelope) on a UTF-8 codepoint boundary. This also makes the `(kind, title,
  body)` dedup below work for repeated identical exceptions.
- **Own-log feedback / amplification. FIXED 2026-09-23.** One failed alert used to log one `ERROR`
  *per device token* (`_send_to_all_devices`'s per-token `except Exception: log.exception(...)`),
  and those ERROR records are re-published fleet-wide as `LogEvent`s (`commlogging.py`).
  `_process_log_entry` did not skip the notifier's own module — unlike
  `_subscribe_client`/`_on_module_opened`, which check `self.comm.name`. On `LocalComm`
  (`send_event` fans out to *every* client including the publisher), a notifier in a single-process
  `MultiModule` therefore re-received its own send-failure tracebacks and re-enqueued them as new
  alerts; XMPP already drops own-module events (`xmppcomm.py:1088`). Two fixes: `_process_log_entry`
  now returns early when `sender == self.comm.name` (mirroring the existing checks), and
  `_send_to_all_devices` logs **once per alert** (count + token list + the first failure's
  traceback) instead of once per token — the worker thread returns the failures, the event loop
  logs them.
- **Timeout doesn't cancel the work. FIXED 2026-09-23.** `asyncio.wait_for(asyncio.to_thread(_send),
  timeout=_FIREBASE_CALL_TIMEOUT)` (15 s) abandons the thread on timeout — `to_thread` can't be
  cancelled — while `firebase_admin`'s default HTTP timeout is 120 s (`_http_client.py:
  DEFAULT_TIMEOUT_SECONDS`). A dead network therefore left each abandoned send running for up to
  120 s × N tokens. Fix: `initialize_app(..., options={"httpTimeout": _FIREBASE_HTTP_TIMEOUT}`
  (= 10 s), which bounds every request — both the OAuth token refresh (via
  `google/auth/transport/requests.py:615-619`, which threads the timeout into the credential
  refresh) and the FCM send (`_http_client.py:132-133`) — so a single hung request finishes inside
  the 15 s `wait_for` window. Per-token `wait_for` bounding (so one slow token can't abandon the
  whole batch for N > 1) remains a possible follow-up.

Note: the self-skip in `_process_log_entry` was chosen over `pyobs_no_forward`, which would also
hide "push sending is failing" from every other log consumer (Telegram, fluentlogger, the GUI). The
"Log-message dedup key" open question above is what lets a retry/feedback loop defeat
`(kind, title, body)` exact-match dedup; the body reduction in the first bullet narrows that hole
for repeated identical exceptions but does not close it.
