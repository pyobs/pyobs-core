# Plan: Per-user push notification preferences in `PushNotifier`

Status: implemented, uncommitted (2026-09-18) — pyobs-core half only; the pyobs-web-client toggle
UI + the get/set preference calls are still to do. Two departures from the draft as written: the
methods shipped with `push`-prefixed names (`register_push_device`, `get_push_preferences`,
`set_push_preferences`) rather than the draft's `register_device`/`set_preferences`, and a
`get_push_preferences` getter was added (the draft only had the setter) so a client can read back
the account's current selection. The setter signature stays `list[PushNotificationType]` (an
invalid/unknown stored value fails loudly) and tolerates plain string values at runtime via
`PushNotificationType(t)`.

Issues: pyobs-web-client#57 (originating — "Allow users to choose which push notification
types they receive"); pyobs-core#902 (the `PushNotifier` tracking issue, still open). This plan
covers only the **pyobs-core** half of #57; the pyobs-web-client companion (toggle UI + the
`set_push_preferences` RPC call) is listed at the end and tracked separately.

## Problem

`pyobs/modules/utils/pushnotifier.py` was deliberately built with "one fixed rule set for the whole
deployment" (`specs/design/push-notification-module.md:51-53`): every registered device receives
every qualifying alert — module `ERROR` state, `ERROR` log events, and `CRITICAL` log events — with
no way to opt out of any of the three. That decision is recorded as an explicit non-goal in the
design doc (`:58-59`) and deferred in #902 ("Per-user alert preferences").

The web client cannot fix this on its own: it is a pure consumer of FCM pushes, and `PushNotifier`
sends *notification* messages (`messaging.Notification(...)`, `pushnotifier.py:255-261`) that the
Android system tray displays itself while the app is backgrounded or closed. No client code runs
then (`pyobs-web-client/specs/design/native-app-shell-capacitor.md:127-128`), so any real filtering
must live server-side in `PushNotifier`, per the "local-only" caveat already flagged in #57.

## Goal

Let each user choose which of the three currently-shipped alert kinds they receive, enforced at
send time in `PushNotifier`, keyed by the same caller identity (`sender` JID) the module already
uses for registration and ACL. Existing behavior is preserved: a user who never sets a preference
still gets everything (all-on default).

## Considered options

**Per-user vs. per-device preferences.** #57 says "users", and registration is already
per-user-with-multiple-devices (`_devices` is `dict[sender, list[device]]`, `pushnotifier.py:56`,
`280`). A user's phone and tablet should share one preference. **Chosen: per-user (per `sender`
JID).** Rejected: per-device, which would force a user to set the same choice once per device and
muddle the "I want X off" intent.

**New RPC vs. extending `register_push_device`.** `register_push_device(token, platform)` is per-device, and
the client dedupes it (`pyobs-web-client/src/composables/usePushNotifications.ts:44,53-55`), so a
preference change would not re-fire it. Preferences are also valid *before* any device registers
(set them, then register later). **Chosen: a new `set_push_preferences` method** on `IPushNotifications`,
keyed by `sender` like `register_push_device`. `register_push_device` stays unchanged.

**Storage shape.** Current file is `{sender: [device, ...]}`. Options: (a) restructure to
`{sender: {"devices": [...], "preferences": [...]}}` with a one-time migration in `open()`; (b) a
second parallel file for preferences. **Chosen: (a)** — one file for one module's state, and the
module has only shipped in 2026-09-14 (`5b688528`), is not yet in a tagged release, and is deployed
on exactly one site (monet.saao.ac.za, Tim's device), so the migration surface is trivially small.
Rejected: (b), which splits one module's state across two files for no benefit.

**Default: all-on vs. opt-in.** **Chosen: all-on** — byte-for-byte backward compatible with what
ships today (nothing changes for any existing device until a preference is explicitly set), and
avoids a silent "I stopped getting alerts" surprise. Rejected: opt-in, which would change behavior
for every currently-registered device on upgrade. *Needs Tim's confirmation* — #57 lists this as an
open question.

**Enum location.** Follow the `TrackingMode` precedent (`pyobs/interfaces/ITrackingMode.py:12-18`):
the enum is defined in the interface file that uses it, exported via `__all__`. **Chosen:**
`PushNotificationType` lives in `IPushNotifications.py`. Rejected: `pyobs/utils/enums.py` (shared
enums like `ModuleState`/`ImageType`), since this type is consumed only by `IPushNotifications` +
`PushNotifier`, exactly like `TrackingMode` is only consumed by `ITrackingMode` + its module.

**Wire type.** `types: list[PushNotificationType]` (a `StrEnum`). The XMPP serializer already
advertises enum-typed params as `enum(Name)` in disco#info (`pyobs/comm/xmpp/serializer.py:453`),
so the web client can build the toggle UI from the schema rather than hardcoding the three names.
Rejected: `list[str]` — works but loses the self-documenting, typo-proof enum and the automatic
disco#info advertisement.

## Decision

### 1. `PushNotificationType` enum + new RPC — `IPushNotifications.py`

```python
from enum import StrEnum

class PushNotificationType(StrEnum):
    """Distinct alert kinds PushNotifier can emit, one opt-in/out toggle each.

    Extensible: future kinds (bad weather, roof open, guiding lost) become new
    members here; existing stored preferences are unaffected because they are
    stored as the enum's string values and unknown values simply never match.
    """
    MODULE_ERROR = "module_error"
    LOG_ERROR = "log_error"
    LOG_CRITICAL = "log_critical"


class IPushNotifications(Interface, metaclass=ABCMeta):
    """The module accepts device registrations for push notifications."""

    __module__ = "pyobs.interfaces"

    @abstractmethod
    async def register_push_device(self, token: str, platform: str = "android", **kwargs: Any) -> None:
        ...  # unchanged

    @abstractmethod
    async def set_push_preferences(self, types: list[PushNotificationType], **kwargs: Any) -> None:
        """Set which notification types this caller wants to receive.

        Keyed by the calling account (`sender`), not by device -- applies to every
        device that account has registered, present and future. A caller that never
        calls this receives all types (all-on default). Calling with an empty list
        opts out of everything.
        """
        ...
```

`__all__` gains `"PushNotificationType"`.

### 2. Tag alerts with a kind — `pushnotifier.py`

`_Alert` gets a required `kind` field; both enqueue sites pass it:

```python
@dataclass
class _Alert:
    kind: PushNotificationType
    title: str
    body: str
```

- `_make_state_callback` (`:152-157`):
  `self._enqueue_alert(PushNotificationType.MODULE_ERROR, f"{module}: ERROR", f"{iface.__name__} reports an ERROR state.")`
- `_process_log_entry` (`:172-186`): derive the kind from `entry.level` —
  `PushNotificationType.LOG_CRITICAL` when `entry.level == "CRITICAL"`, else
  `PushNotificationType.LOG_ERROR` — and enqueue with it.

`_enqueue_alert` signature becomes `_enqueue_alert(kind, title, body)`.

### 3. Storage restructure + migration — `open()` / `register_push_device` / `set_push_preferences`

`_STORAGE_FILE` becomes `{sender: {"devices": [...], "preferences": [str, ...]}}`. `_ALL_TYPES =
[t.value for t in PushNotificationType]` is the module-level default set.

In `open()` (currently `:66-70`), normalize legacy entries on load:

```python
raw = await self.vfs.read_yaml(_STORAGE_FILE)
self._devices = {
    sender: ({"devices": value} if isinstance(value, list) else value)
    for sender, value in raw.items()
}
```

Legacy list-shaped entries are wrapped as `{"devices": value}` with no `preferences` key; the
reader treats an absent `preferences` key as all-on. No write-back of the migrated shape is needed
(the next `register_push_device`/`set_push_preferences` persists the new shape).

`register_push_device` (`:270-283`) writes into the `devices` sub-key:

```python
sender = kwargs.get("sender", "")
entry = self._devices.setdefault(sender, {"devices": []})
devices = entry.setdefault("devices", [])
devices[:] = [d for d in devices if d.get("token") != token]
devices.append({"token": token, "platform": platform, "registered_at": Time.now().isot})
await self.vfs.write_yaml(_STORAGE_FILE, self._devices)
```

New `set_push_preferences`:

```python
async def set_push_preferences(self, types: list[PushNotificationType], **kwargs: Any) -> None:
    sender = kwargs.get("sender", "")
    entry = self._devices.setdefault(sender, {"devices": []})
    entry["preferences"] = [t.value for t in types]
    await self.vfs.write_yaml(_STORAGE_FILE, self._devices)
```

### 4. Filter at send time — `_send_to_all_devices` (`:232-268`)

Replace the flat all-users token list with per-sender fan-out that skips devices whose user has
disabled the alert's kind:

```python
tokens = [
    device["token"]
    for entry in self._devices.values()
    for device in entry.get("devices", [])
    if device.get("platform", "android") == "android"
    and alert.kind.value in entry.get("preferences", _ALL_TYPES)
]
```

`entry.get("preferences", _ALL_TYPES)` implements the all-on default for both freshly-created and
legacy (never-set) entries. An explicitly empty list means "opted out of everything".

### 5. Dedup key includes kind — `_sender_thread` (`:200-230`)

The single global dedup stays correct — for stable preferences a given `(kind, title, body)` always
targets the same recipient subset — but the key must distinguish kinds, since a `module_error`
alert and a `log_error` alert can plausibly share a title/body. Change:

```python
last: tuple[PushNotificationType, str, str] | None = None
...
key = (alert.kind, alert.title, alert.body)
```

The pre-existing "exact-string dedup doesn't catch a retry loop whose message text changes each
time" caveat (`push-notification-module.md:162-166`) stays out of scope here.

## Tests

### Existing coverage to update (`tests/modules/utils/test_pushnotifier.py`)

The `_devices` shape and `_Alert` construction change ripple through most of the file:

- `test_register_push_device_stores_by_sender` / `..._replaces_same_token` / `..._keeps_multiple_devices_per_sender`
  (`:43-76`) — `pn._devices["tim"][0]` → `pn._devices["tim"]["devices"][0]`.
- `test_process_log_entry_enqueues_error` / `..._critical` (`:83-102`) — assert `alert.kind` in
  addition to title/body.
- `test_state_callback_enqueues_on_error_status` (`:129-137`) — assert `alert.kind ==
  PushNotificationType.MODULE_ERROR`.
- `test_enqueue_alert_drops_when_queue_full` (`:211-219`) — construct `_Alert` with a `kind`.
- `test_send_to_all_devices_only_targets_android` / `..._noop_without_fcm_app` (`:223-254`) —
  `_devices` values become `{"devices": [...], "preferences": [...]}`; `_Alert` gains `kind`.
- `test_interface_is_registered` etc. — add `assert "set_push_preferences" in pn._methods`
  (mirrors `test_register_push_device_is_rpc_dispatchable`, `:34-36`).

### New tests required

- `set_push_preferences` stores the type list under `sender` and writes YAML (mirrors
  `test_register_push_device_stores_by_sender`).
- `set_push_preferences` with `[]` opts out of everything — `_send_to_all_devices` targets zero tokens
  for a matching alert.
- Filtering: a user who disabled `module_error` receives `log_error` alerts but not `module_error`
  alerts (build `_devices` with two senders, assert the emitted token list).
- All-on default: an entry with no `preferences` key (legacy/migrated) receives every kind.
- Migration: `open()` reading a legacy `{sender: [devices]}` file produces
  `{sender: {"devices": [...]}}` and sends to those devices.
- Dedup includes kind: two consecutive alerts with the same title/body but different `kind` are both
  sent (not deduped); two with the same `(kind, title, body)` are deduped.
- `pyrefly` on the touched files (this repo uses `ruff`/`pyrefly`, not `mypy`).

## Consequences

- **Good:** filtering is enforced server-side, so it works while the app is closed/backgrounded —
  the only case #57 actually cares about. Backward compatible: nothing changes for existing devices
  until a preference is set.
- **Good:** the `enum(PushNotificationType)` advertisement means the web client can render toggles
  from the schema (no hardcoded type list), and future types are additive.
- **Neutral:** storage file changes shape with a read-time migration. Low risk — the module is not
  yet in a tagged release and is deployed on a single site with a single device; the migration
  touches one real file.
- **Neutral:** preferences are per pyobs account (`sender` JID), not per human. Two accounts on one
  device (or one account on two devices) get one preference each, matching "users" in #57 and the
  existing registration keying.
- **Risk:** no `IPushNotifications` capabilities advertising which types this deployment actually
  emits. The three kinds are fixed in code for now; if a future type lands, old clients won't
  surface a toggle for it until re-synced — acceptable because types are additive and default-on.
- **Out of scope:** severity thresholds / per-module allow- and deny-lists (the `telegram.py`
  per-user `/loglevel` shape, `push-notification-module.md:58-59`); bad-weather / roof-open /
  guiding-lost kinds; stale-token pruning and the exact-string dedup caveat — all remain as today.

## Companion change (pyobs-web-client — out of scope here)

`usePushNotifications.ts` gains a `set_push_preferences` call wired to a SettingsView toggle row, reading
the available kinds from `mod.interfaces['IPushNotifications'].commands['set_push_preferences']`'s param
schema. Because registration is deduped by `registeredWith`, this is a *separate* RPC (not a
re-register), fired on toggle change and on reconnect after both modules and token exist.

## Docs

- Update `specs/design/push-notification-module.md`: move "per-user alert preferences" out of
  Non-goals (`:58-59`) into a short "v2" section describing this design; amend the "one fixed rule
  set" decision (`:51-53`) and the dedup note (`:203-205`'s companion line here) to reflect the new
  per-user fan-out.
- Update `specs/steering/fleet-open-items.md`'s issues-table row for pyobs-web-client#57
  (`:296`) to note the pyobs-core half is now planned.
- Add a note to pyobs-core#902 (or file a follow-up) so the "Explicitly deferred — per-user alert
  preferences" line no longer reads as untouched.
