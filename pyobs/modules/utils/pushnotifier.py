from __future__ import annotations

import asyncio
import logging
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

from pyobs.events import Event, LogEvent, ModuleOpenedEvent
from pyobs.interfaces import Interface, IPushNotifications, PushNotificationType
from pyobs.modules import Module
from pyobs.utils.time import Time

if TYPE_CHECKING:
    from firebase_admin import App

log = logging.getLogger(__name__)

# Maximum number of alerts to buffer before dropping new ones. Keeps RAM bounded during bursts.
_QUEUE_MAX = 200

# Log levels that trigger a push notification.
_ALERT_LOG_LEVELS = {"ERROR", "CRITICAL"}

# All notification types, i.e. what a caller that never set a preference receives. Stored as the
# enum's string values, matching what `set_push_preferences` persists.
_ALL_TYPES = [t.value for t in PushNotificationType]

# Timeout for blocking Firebase SDK calls run in a thread -- bounds the wait so a hung network
# call can't stall the sender thread (and thus the alert queue) forever.
_FIREBASE_CALL_TIMEOUT = 15.0

# Per-request HTTP timeout passed to the Firebase SDK. It bounds both the OAuth token refresh and
# the FCM send (the SDK default is 120 s); kept below _FIREBASE_CALL_TIMEOUT so a single hung
# request finishes inside the wait_for window instead of being abandoned to its default.
_FIREBASE_HTTP_TIMEOUT = 10

# Storage file for registered devices.
_STORAGE_FILE = "/pyobs/pushnotifier.yaml"

# FCM caps the whole message at 4096 bytes; reserve room for the token (~160 bytes), the title
# ("{sender}: {level}") and the JSON envelope before budgeting the body.
_MAX_BODY_BYTES = 3600

# Appended when a body had to be truncated to fit _MAX_BODY_BYTES (inclusive of its own bytes).
_TRUNCATION_MARKER = "…"


@dataclass
class _Alert:
    kind: PushNotificationType
    title: str
    body: str


def _notification_body(message: str) -> str:
    """Reduce a log message to a push-notification body that fits FCM's 4 KB message limit.

    A formatted traceback carries the exception on its final line, so for a multi-line message the
    body becomes "first non-empty line -- last non-empty line", keeping both the human-facing
    message and the exception summary. Single-line messages pass through unchanged. The result is
    truncated to `_MAX_BODY_BYTES` on a UTF-8 codepoint boundary.

    Args:
        message: The `LogEvent.message` to reduce.

    Returns:
        A body that encodes to at most `_MAX_BODY_BYTES` bytes.
    """
    lines = [line for line in message.split("\n") if line.strip()]
    if not lines:
        return ""

    first, last = lines[0], lines[-1]
    body = f"{first} — {last}" if first != last else first

    encoded = body.encode("utf-8")
    if len(encoded) <= _MAX_BODY_BYTES:
        return body

    # byte-slice then lossy-decode: never splits a multibyte codepoint in half. The marker is
    # budgeted inside the limit rather than appended on top of it.
    budget = _MAX_BODY_BYTES - len(_TRUNCATION_MARKER.encode("utf-8"))
    return encoded[:budget].decode("utf-8", errors="ignore") + _TRUNCATION_MARKER


class PushNotifier(Module, IPushNotifications):
    """Relays fleet-wide module-`ERROR` state and `ERROR`/`CRITICAL` log events to mobile devices
    via Firebase Cloud Messaging (Android only in v1 -- see specs/design/push-notification-module.md).

    Each caller may opt out of individual alert kinds via `set_push_preferences`; a caller that
    never does receives all of them. `get_push_preferences` returns the current selection.
    """

    __module__ = "pyobs.modules.utils"

    def __init__(self, credentials_file: str, **kwargs: Any):
        """Initialize a new push notifier.

        Args:
            credentials_file: VFS path to the Firebase service-account credentials JSON file
                (e.g. "/pyobs/firebase-credentials.json"). Distinct from and never overlapping
                with the client-side google-services.json/API key.
        """
        Module.__init__(self, **kwargs)

        self._credentials_file = credentials_file
        self._devices: dict[str, dict[str, Any]] = {}
        self._alert_queue: asyncio.Queue[_Alert] = asyncio.Queue(maxsize=_QUEUE_MAX)
        self._fcm_app: App | None = None

        self.add_background_task(self._sender_thread)

    async def open(self) -> None:
        """Open module."""
        await Module.open(self)

        # load registered devices, migrating the legacy {sender: [devices]} shape in place -- a
        # value that is still a bare list predates per-user preferences, and gets wrapped with an
        # absent `preferences` key, which the reader treats as "all types on".
        try:
            raw = await self.vfs.read_yaml(_STORAGE_FILE)
        except FileNotFoundError:
            raw = {}
        self._devices = {
            sender: ({"devices": value} if isinstance(value, list) else value) for sender, value in (raw or {}).items()
        }

        # init Firebase
        await self._init_firebase()

        # subscribe to state of all currently connected clients, and react to new ones
        for client in self.comm.clients:
            await self._subscribe_client(client)
        await self.comm.register_event(ModuleOpenedEvent, self._on_module_opened)

        # listen to log events
        await self.comm.register_event(LogEvent, self._process_log_entry)

    async def close(self) -> None:
        """Close module."""
        await Module.close(self)

        if self._fcm_app is not None:
            import firebase_admin

            # delete_app() -> messaging service close() calls asyncio.run() internally, which
            # raises if called from within a running event loop (our own) -- run it in a thread.
            try:
                await asyncio.wait_for(
                    asyncio.to_thread(firebase_admin.delete_app, self._fcm_app), timeout=_FIREBASE_CALL_TIMEOUT
                )
            except Exception:
                log.exception("Failed to cleanly shut down Firebase app.")
            self._fcm_app = None

    async def _init_firebase(self) -> None:
        """Load the service-account credentials and initialize the Firebase app.

        Runs blocking Firebase SDK calls in a thread -- never call firebase_admin directly on
        the event loop (see specs/steering/blocking-sdk-calls-must-not-run-on-the-event-loop.md).
        """
        try:
            import firebase_admin
            from firebase_admin import credentials

            cred_dict = await self.vfs.read_yaml(self._credentials_file)

            def _init() -> App:
                cred = credentials.Certificate(cred_dict)
                # unique app name -- the default name collides if more than one PushNotifier
                # instance (e.g. in tests) initializes firebase_admin in the same process
                return firebase_admin.initialize_app(
                    cred, name=f"pushnotifier-{id(self)}", options={"httpTimeout": _FIREBASE_HTTP_TIMEOUT}
                )

            self._fcm_app = await asyncio.wait_for(asyncio.to_thread(_init), timeout=_FIREBASE_CALL_TIMEOUT)

        except Exception:
            log.exception("Could not initialize Firebase, push notifications are disabled.")
            self._fcm_app = None

    async def _subscribe_client(self, module: str) -> None:
        """Subscribe to state updates for every state-bearing interface of the given module.

        Args:
            module: Name of the module to subscribe to.
        """
        if module == self.comm.name:
            return

        try:
            interfaces = await self.comm.get_interfaces(module)
        except Exception:
            log.exception("Could not get interfaces for %s.", module)
            return

        for iface in interfaces:
            if not iface.has_own_state():
                continue
            await self.comm.subscribe_state(module, iface, self._make_state_callback(module, iface))

    def _make_state_callback(self, module: str, iface: type[Interface]) -> Any:
        """Build a state-update callback bound to a specific module/interface.

        Args:
            module: Name of the module this callback is for.
            iface: Interface this callback is for.
        """

        def _callback(state: Any) -> None:
            status = getattr(state, "status", None)
            if status is not None and str(status).upper() == "ERROR":
                self._enqueue_alert(
                    PushNotificationType.MODULE_ERROR,
                    f"{module}: ERROR",
                    f"{iface.__name__} reports an ERROR state.",
                )

        return _callback

    async def _on_module_opened(self, event: Event, sender: str) -> bool:
        """React to other modules connecting, subscribing to their state.

        Args:
            event: The event.
            sender: Name of sender.
        """
        if sender == self.comm.name or not isinstance(event, ModuleOpenedEvent):
            return False

        await self._subscribe_client(sender)
        return True

    async def _process_log_entry(self, entry: Event, sender: str) -> bool:
        """Process a new log entry, alerting on ERROR/CRITICAL.

        Args:
            entry: The log event.
            sender: Name of sender.
        """
        if not isinstance(entry, LogEvent):
            return False

        # never alert on our own log output: on LocalComm our own ERROR logs (e.g. a failed send)
        # would otherwise re-enter this queue as new alerts. XMPP already drops own-module events.
        if sender == self.comm.name:
            return False

        if entry.level not in _ALERT_LOG_LEVELS:
            return False

        kind = PushNotificationType.LOG_CRITICAL if entry.level == "CRITICAL" else PushNotificationType.LOG_ERROR
        # reduce at enqueue time so both the queued alert and the dedup key hold the concise form
        self._enqueue_alert(kind, f"{sender}: {entry.level}", _notification_body(entry.message))
        return True

    def _enqueue_alert(self, kind: PushNotificationType, title: str, body: str) -> None:
        """Queue an alert for sending, dropping it if the queue is full.

        Args:
            kind: Notification type of the alert.
            title: Alert title.
            body: Alert body.
        """
        if self._alert_queue.full():
            log.warning("Push notification queue full, dropping alert.")
            return
        self._alert_queue.put_nowait(_Alert(kind=kind, title=title, body=body))

    async def _sender_thread(self) -> None:
        """Drain the alert queue and send notifications one at a time.

        Consecutive duplicate alerts (same kind, title and body) are suppressed. A single global
        dedup (rather than Telegram's per-user one) is enough: for stable preferences a given
        alert always targets the same recipient subset, so anyone who would receive a repeat
        already received the original.
        """
        last: tuple[PushNotificationType, str, str] | None = None
        repeat_count = 0

        while True:
            alert = await self._alert_queue.get()

            try:
                key = (alert.kind, alert.title, alert.body)
                if key == last:
                    repeat_count += 1
                    continue

                if repeat_count > 0:
                    log.info("Suppressed %d repeat push notification(s).", repeat_count)
                    repeat_count = 0
                last = key

                await self._send_to_all_devices(alert)

            except Exception:
                log.exception("Failed to send push notification.")

            finally:
                self._alert_queue.task_done()

    @staticmethod
    def _wants(entry: dict[str, Any], kind: PushNotificationType) -> bool:
        """Whether the user an entry belongs to wants the given notification kind.

        An entry with no `preferences` key at all (never set, or migrated from the legacy storage
        shape) receives everything; an explicitly empty list means opted out of all kinds.
        """
        prefs = entry.get("preferences")
        return kind.value in (_ALL_TYPES if prefs is None else prefs)

    async def _send_to_all_devices(self, alert: _Alert) -> None:
        """Send an alert to every registered Android device whose owner wants this kind.

        Args:
            alert: The alert to send.
        """
        if self._fcm_app is None:
            return

        tokens = [
            device["token"]
            for entry in self._devices.values()
            for device in entry.get("devices", [])
            if device.get("platform", "android") == "android" and self._wants(entry, alert.kind)
        ]
        if not tokens:
            return

        def _send() -> tuple[list[tuple[str, Exception]], list[str]]:
            """Send to every token in a worker thread, returning failures and unregistered tokens.

            Runs in a thread (never on the event loop); the caller logs and prunes on the loop.
            """
            from firebase_admin import messaging
            from firebase_admin.exceptions import NotFoundError

            failed: list[tuple[str, Exception]] = []
            dead: list[str] = []
            for token in tokens:
                try:
                    messaging.send(
                        messaging.Message(
                            notification=messaging.Notification(title=alert.title, body=alert.body),
                            token=token,
                        ),
                        app=self._fcm_app,
                    )
                except NotFoundError:
                    # covers messaging.UnregisteredError (a NotFoundError subclass): FCM reports
                    # the token as unregistered, so drop it instead of retrying it forever
                    dead.append(token)
                except Exception as e:
                    failed.append((token, e))
            return failed, dead

        try:
            failed, dead = await asyncio.wait_for(asyncio.to_thread(_send), timeout=_FIREBASE_CALL_TIMEOUT)
        except TimeoutError:
            log.error("Sending push notifications timed out.")
            return

        if failed:
            # one log line per alert (not per device), but keep the first failure's traceback
            log.error(
                "Failed to send push notification to %d of %d device(s): %s",
                len(failed),
                len(tokens),
                ", ".join(token for token, _ in failed),
                exc_info=failed[0][1],
            )
        if dead:
            await self._prune_tokens(dead)

    async def _prune_tokens(self, tokens: list[str]) -> None:
        """Drop tokens FCM reported as unregistered and persist the change.

        Args:
            tokens: Tokens to remove from storage.
        """
        dead = set(tokens)
        removed = 0
        for entry in self._devices.values():
            devices = entry.get("devices", [])
            before = len(devices)
            devices[:] = [d for d in devices if d.get("token") not in dead]
            removed += before - len(devices)

        if removed:
            log.warning("Pruned %d unregistered push notification device token(s).", removed)
            await self.vfs.write_yaml(_STORAGE_FILE, self._devices)

    async def register_push_device(self, token: str, platform: str = "android", **kwargs: Any) -> None:
        """Register a device to receive push notifications.

        Args:
            token: FCM/APNs device token.
            platform: Device platform ("android" or "ios").
        """
        sender = kwargs.get("sender", "")

        entry = self._devices.setdefault(sender, {"devices": []})
        devices = entry.setdefault("devices", [])
        devices[:] = [d for d in devices if d.get("token") != token]
        devices.append({"token": token, "platform": platform, "registered_at": Time.now().isot})

        await self.vfs.write_yaml(_STORAGE_FILE, self._devices)

    async def get_push_preferences(self, **kwargs: Any) -> list[PushNotificationType]:
        """Return the notification types the calling account currently receives.

        A caller that has never set a preference returns all types (all-on default).
        """
        sender = kwargs.get("sender", "")

        entry = self._devices.get(sender)
        prefs = entry.get("preferences") if entry is not None else None
        values = _ALL_TYPES if prefs is None else prefs
        return [PushNotificationType(v) for v in values]

    async def set_push_preferences(self, types: list[PushNotificationType], **kwargs: Any) -> None:
        """Set which notification types the calling account wants to receive.

        Args:
            types: Notification types to receive; an empty list opts out of everything.
        """
        sender = kwargs.get("sender", "")

        entry = self._devices.setdefault(sender, {"devices": []})
        entry["preferences"] = [PushNotificationType(t).value for t in types]

        await self.vfs.write_yaml(_STORAGE_FILE, self._devices)


__all__ = ["PushNotifier"]
