# Push notification relay module (`PushNotifier`)

Status: sketch — decided direction and v1 scope, not yet built. Written 2026-09-09 after
confirming (against current code) that the wire-protocol prerequisite this depended on is already
satisfied, and that RPC handlers can already access caller identity via `**kwargs: Any` (§3) —
both were open questions in earlier drafts, now resolved by reading the actual dispatch code.
Nothing here has been implemented yet.

Repos: pyobs-core (module implementation, all new code); pyobs-web-client (one small addition —
the device-token registration call from `usePushNotifications.ts`)

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

- **Module `ERROR` state only.** Weather and `CRITICAL` log alerts are real future scope (both
  already wire-available, per above) but deliberately deferred — prove the FCM plumbing on the
  simplest, most safety-critical signal first, add the other two as a fast-follow once that's
  solid.
- **One fixed rule set for the whole deployment, not per-user thresholds.** No per-user
  preferences RPC, no per-user filter config — every registered device gets every module-`ERROR`
  alert. Registration only needs a device token, nothing else.

## Non-goals (this sketch)

- Bad weather / `CRITICAL` log alerts — real, scoped above, not this pass.
- Per-user alert preferences (severity, module allow/deny-list) — `telegram.py`'s per-user
  `/loglevel` is the shape this *could* take later; not now.
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

### 2. Detecting module `ERROR` — the actual hard part, not the FCM call

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

### 3. Device registration

A public async method on the module — any pyobs client can call it via the standard comm proxy
RPC mechanism (the same XEP-0009 machinery `pyobs-web-client` already re-implements for every
other module call):

```python
async def register_device(self, token: str, platform: str = "android", **kwargs: Any) -> None:
    sender = kwargs.get("sender", "")
    ...
```

**Confirmed 2026-09-09** (was an open question in an earlier draft of this sketch): an RPC handler
*does* get the caller's identity, via the same mechanism `Module.execute()` already uses for ACL
checks — `pyobs/comm/xmpp/rpc.py`'s `_on_jabber_rpc_method_call` calls
`self._handler.execute(pmethod, *params, sender=iq["from"].user, call_id=call_id)` for every RPC;
`execute()` binds those against the target method's own signature, so a method that declares
`**kwargs: Any` receives `sender`/`call_id` in it. `get_permitted_methods(self, **kwargs: Any)`
already does exactly this. `register_device` just needs the same `**kwargs: Any` — no new
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

A flapping module (brief ERROR↔READY toggling) shouldn't spam a push per transition. Reuse
`Telegram`'s `asyncio.Queue` + `add_background_task`-driven sender-thread shape, including its
duplicate-suppression logic (`_log_sender_thread`'s `last_messages`/`repeat_counts`) — same
problem, same fix.

### 5. Sending

FCM HTTP v1 API against the already-provisioned Firebase project (`pyobs-51a29`), using a
**server-side service-account credential** — a new secret, distinct from and never overlapping
with the client-side `google-services.json`/API key already checked into
`pyobs-web-client/android/app/`. New optional dependency (likely `firebase-admin`), added to
`pyproject.toml`'s `full` extras group alongside `python-telegram-bot`/`matrix-nio`.

## Open questions — not resolved here, flagged for actual design/implementation

- **Stale/uninstalled-app tokens.** FCM returns an "unregistered" error on send to a dead token;
  the module should prune those, not accumulate them forever. Not designed here.
- **Which modules/interfaces count.** Mirroring `DashboardView.vue`'s triage exactly means
  alerting on *any* interface's `ERROR`, fleet-wide, with no allow/deny-list — same blast radius
  as what the dashboard already surfaces. Worth confirming that's actually the desired v1 alert
  surface (vs., say, only modules with real hardware) before building.
