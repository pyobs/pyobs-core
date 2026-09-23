from __future__ import annotations

import asyncio
from unittest.mock import AsyncMock, MagicMock

import pytest

from pyobs.comm import Comm
from pyobs.events import LogEvent, ModuleOpenedEvent, TestEvent
from pyobs.interfaces import ICooling, IMotion, IPushNotifications, PushNotificationType
from pyobs.interfaces.IMotion import MotionState
from pyobs.interfaces.interface import registered_interfaces
from pyobs.modules import Module
from pyobs.modules.utils.pushnotifier import (
    _FIREBASE_HTTP_TIMEOUT,
    _MAX_BODY_BYTES,
    PushNotifier,
    _Alert,
    _notification_body,
)
from pyobs.utils.enums import MotionStatus


def make_pushnotifier(**kwargs: object) -> PushNotifier:
    comm = MagicMock(spec=Comm)
    comm.name = "pushnotifier"
    return PushNotifier(credentials_file="/pyobs/firebase-credentials.json", comm=comm, **kwargs)


def patch_messaging(mocker) -> list[str]:
    """Patch `firebase_admin.messaging` so sends are recorded instead of delivered.

    Returns the list `_send_to_all_devices` appends the target token of each attempted send to.
    """
    sent_tokens: list[str] = []

    def fake_send(message: object, app: object) -> None:
        sent_tokens.append(message.token)

    messaging_mock = MagicMock()
    messaging_mock.send = MagicMock(side_effect=fake_send)
    messaging_mock.Message = MagicMock(side_effect=lambda notification, token: MagicMock(token=token))
    mocker.patch.dict("sys.modules", {"firebase_admin.messaging": messaging_mock})
    return sent_tokens


# ── interface registration ───────────────────────────────────────────────────


def test_interface_is_registered() -> None:
    assert "IPushNotifications" in registered_interfaces()


def test_interface_has_no_own_state() -> None:
    assert IPushNotifications.has_own_state() is False


def test_register_push_device_is_rpc_dispatchable() -> None:
    pn = make_pushnotifier()
    assert "register_push_device" in pn._methods


def test_set_push_preferences_is_rpc_dispatchable() -> None:
    pn = make_pushnotifier()
    assert "set_push_preferences" in pn._methods


def test_get_push_preferences_is_rpc_dispatchable() -> None:
    pn = make_pushnotifier()
    assert "get_push_preferences" in pn._methods


# ── register_push_device ──────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_register_push_device_stores_by_sender() -> None:
    pn = make_pushnotifier()
    pn._vfs = MagicMock()
    pn._vfs.write_yaml = AsyncMock()

    await pn.register_push_device("token-1", sender="tim")

    assert pn._devices["tim"]["devices"][0]["token"] == "token-1"
    assert pn._devices["tim"]["devices"][0]["platform"] == "android"
    pn._vfs.write_yaml.assert_awaited_once_with("/pyobs/pushnotifier.yaml", pn._devices)


@pytest.mark.asyncio
async def test_register_push_device_replaces_same_token() -> None:
    pn = make_pushnotifier()
    pn._vfs = MagicMock()
    pn._vfs.write_yaml = AsyncMock()

    await pn.register_push_device("token-1", sender="tim")
    await pn.register_push_device("token-1", platform="android", sender="tim")

    assert len(pn._devices["tim"]["devices"]) == 1


@pytest.mark.asyncio
async def test_register_push_device_keeps_multiple_devices_per_sender() -> None:
    pn = make_pushnotifier()
    pn._vfs = MagicMock()
    pn._vfs.write_yaml = AsyncMock()

    await pn.register_push_device("token-phone", sender="tim")
    await pn.register_push_device("token-tablet", sender="tim")

    assert {d["token"] for d in pn._devices["tim"]["devices"]} == {"token-phone", "token-tablet"}


# ── push preferences ─────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_set_push_preferences_stores_by_sender() -> None:
    pn = make_pushnotifier()
    pn._vfs = MagicMock()
    pn._vfs.write_yaml = AsyncMock()

    await pn.set_push_preferences([PushNotificationType.LOG_ERROR], sender="tim")

    assert pn._devices["tim"]["preferences"] == ["log_error"]
    pn._vfs.write_yaml.assert_awaited_once_with("/pyobs/pushnotifier.yaml", pn._devices)


@pytest.mark.asyncio
async def test_set_push_preferences_does_not_touch_devices() -> None:
    pn = make_pushnotifier()
    pn._vfs = MagicMock()
    pn._vfs.write_yaml = AsyncMock()
    pn._devices = {"tim": {"devices": [{"token": "t1", "platform": "android"}]}}

    await pn.set_push_preferences([], sender="tim")

    assert pn._devices["tim"]["preferences"] == []
    assert pn._devices["tim"]["devices"] == [{"token": "t1", "platform": "android"}]


@pytest.mark.asyncio
async def test_get_push_preferences_defaults_to_all_types() -> None:
    pn = make_pushnotifier()
    pn._devices = {}

    result = await pn.get_push_preferences(sender="tim")

    assert result == [
        PushNotificationType.MODULE_ERROR,
        PushNotificationType.LOG_ERROR,
        PushNotificationType.LOG_CRITICAL,
    ]


@pytest.mark.asyncio
async def test_get_push_preferences_returns_stored_selection() -> None:
    pn = make_pushnotifier()
    pn._devices = {"tim": {"devices": [], "preferences": ["log_error", "log_critical"]}}

    result = await pn.get_push_preferences(sender="tim")

    assert result == [PushNotificationType.LOG_ERROR, PushNotificationType.LOG_CRITICAL]


@pytest.mark.asyncio
async def test_get_push_preferences_returns_empty_when_opted_out_of_everything() -> None:
    pn = make_pushnotifier()
    pn._devices = {"tim": {"devices": [], "preferences": []}}

    result = await pn.get_push_preferences(sender="tim")

    assert result == []


# ── log event handling (§2b) ─────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_process_log_entry_enqueues_error() -> None:
    pn = make_pushnotifier()
    entry = LogEvent(time="t", level="ERROR", filename="f", function="fn", line=1, message="boom")

    handled = await pn._process_log_entry(entry, "camera1")

    assert handled is True
    alert = pn._alert_queue.get_nowait()
    assert alert.kind == PushNotificationType.LOG_ERROR
    assert alert.title == "camera1: ERROR"
    assert alert.body == "boom"


@pytest.mark.asyncio
async def test_process_log_entry_enqueues_critical() -> None:
    pn = make_pushnotifier()
    entry = LogEvent(time="t", level="CRITICAL", filename="f", function="fn", line=1, message="fatal")

    await pn._process_log_entry(entry, "camera1")

    assert pn._alert_queue.qsize() == 1
    assert pn._alert_queue.get_nowait().kind == PushNotificationType.LOG_CRITICAL


@pytest.mark.asyncio
async def test_process_log_entry_ignores_info() -> None:
    pn = make_pushnotifier()
    entry = LogEvent(time="t", level="INFO", filename="f", function="fn", line=1, message="fine")

    handled = await pn._process_log_entry(entry, "camera1")

    assert handled is False
    assert pn._alert_queue.qsize() == 0


@pytest.mark.asyncio
async def test_process_log_entry_ignores_non_log_events() -> None:
    pn = make_pushnotifier()

    handled = await pn._process_log_entry(TestEvent(), "camera1")

    assert handled is False
    assert pn._alert_queue.qsize() == 0


@pytest.mark.asyncio
async def test_process_log_entry_ignores_own_module_logs() -> None:
    pn = make_pushnotifier()  # comm.name == "pushnotifier"
    entry = LogEvent(time="t", level="ERROR", filename="f", function="fn", line=1, message="boom")

    handled = await pn._process_log_entry(entry, "pushnotifier")

    assert handled is False
    assert pn._alert_queue.qsize() == 0


# ── notification body reduction (FCM 4 KB message limit) ─────────────────────

_TRACEBACK_MESSAGE = (
    "Failed to send push notification to a device.\n"
    "Traceback (most recent call last):\n"
    '  File "/opt/pyobs/venv/lib/python3.13/site-packages/requests/adapters.py", line 729, in send\n'
    "    raise ConnectionError(e, request=request)\n"
    "requests.exceptions.ConnectionError: HTTPSConnectionPool(host='oauth2.googleapis.com', port=443)"
)


@pytest.mark.asyncio
async def test_process_log_entry_body_reduces_traceback_to_first_and_last_line() -> None:
    pn = make_pushnotifier()
    entry = LogEvent(time="t", level="ERROR", filename="f", function="fn", line=1, message=_TRACEBACK_MESSAGE)

    await pn._process_log_entry(entry, "camera1")

    assert pn._alert_queue.get_nowait().body == (
        "Failed to send push notification to a device. — "
        "requests.exceptions.ConnectionError: HTTPSConnectionPool(host='oauth2.googleapis.com', port=443)"
    )


@pytest.mark.asyncio
async def test_process_log_entry_body_keeps_plain_single_line_message() -> None:
    pn = make_pushnotifier()
    entry = LogEvent(time="t", level="ERROR", filename="f", function="fn", line=1, message="boom")

    await pn._process_log_entry(entry, "camera1")

    assert pn._alert_queue.get_nowait().body == "boom"


def test_notification_body_uses_non_empty_lines() -> None:
    assert _notification_body("\n\nfirst\n\nlast\n\n") == "first — last"


def test_notification_body_single_line_is_unchanged() -> None:
    assert _notification_body("boom") == "boom"


def test_notification_body_empty_message() -> None:
    assert _notification_body("") == ""
    assert _notification_body("\n \n") == ""


def test_notification_body_reduces_long_traceback_below_limit() -> None:
    """The MONET/S incident: a raw traceback over FCM's 4 KB limit must reduce to a short body."""
    frames = "\n".join(f'  File "/app/mod{i}.py", line {i}, in fn{i}' for i in range(500))
    message = (
        f"Failed to send push notification to a device.\nTraceback (most recent call last):\n{frames}\nValueError: boom"
    )

    body = _notification_body(message)

    assert len(message.encode("utf-8")) > 4096
    assert body == "Failed to send push notification to a device. — ValueError: boom"
    assert len(body.encode("utf-8")) <= _MAX_BODY_BYTES


def test_notification_body_caps_when_exception_line_itself_is_huge() -> None:
    message = 'boom\nTraceback (most recent call last):\n  File "f", line 1, in fn\nValueError: ' + "x" * 10000

    body = _notification_body(message)

    assert len(body.encode("utf-8")) <= _MAX_BODY_BYTES
    assert body.endswith("…")
    assert body.startswith("boom — ValueError: ")


def test_notification_body_cap_does_not_split_multibyte_character() -> None:
    # "ä" is 2 bytes, so an odd byte budget lands mid-codepoint unless the decode is lossy
    body = _notification_body("ä" * (_MAX_BODY_BYTES * 2))

    assert len(body.encode("utf-8")) <= _MAX_BODY_BYTES
    assert body.endswith("…")
    assert "\ufffd" not in body  # no replacement chars => no split codepoint


# ── module-ERROR state detection (§2a) ───────────────────────────────────────


def test_state_callback_enqueues_on_error_status() -> None:
    pn = make_pushnotifier()
    callback = pn._make_state_callback("telescope", IMotion)

    callback(MotionState(status=MotionStatus.ERROR))

    alert = pn._alert_queue.get_nowait()
    assert alert.kind == PushNotificationType.MODULE_ERROR
    assert alert.title == "telescope: ERROR"
    assert "IMotion" in alert.body


def test_state_callback_ignores_non_error_status() -> None:
    pn = make_pushnotifier()
    callback = pn._make_state_callback("telescope", IMotion)

    callback(MotionState(status=MotionStatus.IDLE))

    assert pn._alert_queue.qsize() == 0


def test_state_callback_ignores_state_without_status() -> None:
    pn = make_pushnotifier()
    callback = pn._make_state_callback("cooler", ICooling)

    # CoolingState has no `status` field at all -- must not crash
    callback(MagicMock(spec=[]))

    assert pn._alert_queue.qsize() == 0


@pytest.mark.asyncio
async def test_subscribe_client_skips_self() -> None:
    pn = make_pushnotifier()
    pn.comm.subscribe_state = AsyncMock()

    await pn._subscribe_client(pn.comm.name)

    pn.comm.subscribe_state.assert_not_awaited()


@pytest.mark.asyncio
async def test_subscribe_client_only_subscribes_state_bearing_interfaces() -> None:
    pn = make_pushnotifier()
    # IMotion defines its own state (has_own_state() == True); IPushNotifications defines none
    # (pure RPC interface) -- only the former should get a state subscription.
    pn.comm.get_interfaces = AsyncMock(return_value=[IMotion, IPushNotifications])
    pn.comm.subscribe_state = AsyncMock()

    await pn._subscribe_client("telescope")

    pn.comm.subscribe_state.assert_awaited_once()
    args = pn.comm.subscribe_state.await_args[0]
    assert args[0] == "telescope"
    assert args[1] is IMotion


@pytest.mark.asyncio
async def test_on_module_opened_subscribes_other_modules() -> None:
    pn = make_pushnotifier()
    pn._subscribe_client = AsyncMock()

    handled = await pn._on_module_opened(ModuleOpenedEvent(), "telescope")

    assert handled is True
    pn._subscribe_client.assert_awaited_once_with("telescope")


@pytest.mark.asyncio
async def test_on_module_opened_ignores_self() -> None:
    pn = make_pushnotifier()
    pn._subscribe_client = AsyncMock()

    handled = await pn._on_module_opened(ModuleOpenedEvent(), pn.comm.name)

    assert handled is False
    pn._subscribe_client.assert_not_awaited()


# ── debounce / dedup (§4) ─────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_enqueue_alert_drops_when_queue_full() -> None:
    pn = make_pushnotifier()
    pn._alert_queue = asyncio.Queue(maxsize=1)
    pn._enqueue_alert(PushNotificationType.LOG_ERROR, "a", "1")

    pn._enqueue_alert(PushNotificationType.LOG_ERROR, "b", "2")  # queue full, should be dropped, not raise

    assert pn._alert_queue.qsize() == 1
    assert pn._alert_queue.get_nowait() == _Alert(PushNotificationType.LOG_ERROR, "a", "1")


@pytest.mark.asyncio
async def test_sender_thread_dedups_same_kind_and_sends_different_kind() -> None:
    pn = make_pushnotifier()
    pn._send_to_all_devices = AsyncMock()

    task = asyncio.create_task(pn._sender_thread())
    try:
        pn._enqueue_alert(PushNotificationType.LOG_ERROR, "t", "b")
        pn._enqueue_alert(PushNotificationType.LOG_ERROR, "t", "b")  # consecutive duplicate -> suppressed
        pn._enqueue_alert(PushNotificationType.LOG_CRITICAL, "t", "b")  # different kind -> sent
        await pn._alert_queue.join()
    finally:
        task.cancel()
        with pytest.raises(asyncio.CancelledError):
            await task

    sent_kinds = [call.args[0].kind for call in pn._send_to_all_devices.await_args_list]
    assert sent_kinds == [PushNotificationType.LOG_ERROR, PushNotificationType.LOG_CRITICAL]


# ── sending / per-user filtering ─────────────────────────────────────────────


@pytest.mark.asyncio
async def test_send_to_all_devices_only_targets_android(mocker) -> None:
    pn = make_pushnotifier()
    pn._fcm_app = MagicMock()
    pn._devices = {
        "tim": {
            "devices": [
                {"token": "android-token", "platform": "android"},
                {"token": "ios-token", "platform": "ios"},
            ]
        }
    }
    sent_tokens = patch_messaging(mocker)

    await pn._send_to_all_devices(_Alert(PushNotificationType.LOG_ERROR, "t", "b"))

    assert sent_tokens == ["android-token"]


@pytest.mark.asyncio
async def test_send_to_all_devices_filters_by_preference(mocker) -> None:
    pn = make_pushnotifier()
    pn._fcm_app = MagicMock()
    pn._devices = {
        "tim": {
            "devices": [{"token": "tim-token", "platform": "android"}],
            "preferences": ["log_error"],
        },
        "anna": {
            "devices": [{"token": "anna-token", "platform": "android"}],
            "preferences": ["module_error"],
        },
    }
    sent_tokens = patch_messaging(mocker)

    await pn._send_to_all_devices(_Alert(PushNotificationType.MODULE_ERROR, "t", "b"))

    assert sent_tokens == ["anna-token"]


@pytest.mark.asyncio
async def test_send_to_all_devices_empty_preferences_opts_out_of_everything(mocker) -> None:
    pn = make_pushnotifier()
    pn._fcm_app = MagicMock()
    pn._devices = {
        "tim": {
            "devices": [{"token": "tim-token", "platform": "android"}],
            "preferences": [],
        }
    }
    sent_tokens = patch_messaging(mocker)

    await pn._send_to_all_devices(_Alert(PushNotificationType.LOG_ERROR, "t", "b"))

    assert sent_tokens == []


@pytest.mark.asyncio
async def test_send_to_all_devices_all_on_when_preferences_absent(mocker) -> None:
    pn = make_pushnotifier()
    pn._fcm_app = MagicMock()
    pn._devices = {"tim": {"devices": [{"token": "tim-token", "platform": "android"}]}}
    sent_tokens = patch_messaging(mocker)

    for kind in PushNotificationType:
        await pn._send_to_all_devices(_Alert(kind, "t", "b"))

    assert sent_tokens == ["tim-token"] * len(PushNotificationType)


@pytest.mark.asyncio
async def test_send_to_all_devices_noop_without_fcm_app() -> None:
    pn = make_pushnotifier()
    pn._fcm_app = None
    pn._devices = {"tim": {"devices": [{"token": "x", "platform": "android"}]}}

    # must not raise even though there's no app to send through
    await pn._send_to_all_devices(_Alert(PushNotificationType.LOG_ERROR, "t", "b"))


@pytest.mark.asyncio
async def test_send_to_all_devices_logs_one_error_per_alert(mocker, caplog) -> None:
    pn = make_pushnotifier()
    pn._fcm_app = MagicMock()
    pn._devices = {
        "tim": {
            "devices": [
                {"token": "t1", "platform": "android"},
                {"token": "t2", "platform": "android"},
            ]
        }
    }

    messaging_mock = MagicMock()
    messaging_mock.send = MagicMock(side_effect=RuntimeError("network down"))
    mocker.patch.dict("sys.modules", {"firebase_admin.messaging": messaging_mock})

    with caplog.at_level("ERROR", logger="pyobs.modules.utils.pushnotifier"):
        await pn._send_to_all_devices(_Alert(PushNotificationType.LOG_ERROR, "t", "b"))

    errors = [r for r in caplog.records if r.levelname == "ERROR"]
    assert len(errors) == 1
    assert "2 of 2" in errors[0].getMessage()


@pytest.mark.asyncio
async def test_send_to_all_devices_prunes_unregistered_tokens(mocker) -> None:
    # UnregisteredError is a NotFoundError subclass, so exercising NotFoundError covers the real
    # FCM "unregistered token" signal that _send_to_all_devices actually catches.
    from firebase_admin.exceptions import NotFoundError

    pn = make_pushnotifier()
    pn._fcm_app = MagicMock()
    pn._vfs = MagicMock()
    pn._vfs.write_yaml = AsyncMock()
    pn._devices = {
        "tim": {
            "devices": [
                {"token": "dead-token", "platform": "android"},
                {"token": "live-token", "platform": "android"},
            ]
        }
    }

    def fake_send(message: object, app: object) -> None:
        if getattr(message, "token", None) == "dead-token":
            raise NotFoundError("The registration token is not valid")
        # live token: success

    messaging_mock = MagicMock()
    messaging_mock.send = MagicMock(side_effect=fake_send)
    messaging_mock.Message = MagicMock(side_effect=lambda notification, token: MagicMock(token=token))
    mocker.patch.dict("sys.modules", {"firebase_admin.messaging": messaging_mock})

    await pn._send_to_all_devices(_Alert(PushNotificationType.LOG_ERROR, "t", "b"))

    assert pn._devices["tim"]["devices"] == [{"token": "live-token", "platform": "android"}]
    pn._vfs.write_yaml.assert_awaited_once_with("/pyobs/pushnotifier.yaml", pn._devices)


@pytest.mark.asyncio
async def test_init_firebase_passes_http_timeout(mocker) -> None:
    pn = make_pushnotifier()
    pn._vfs = MagicMock()
    pn._vfs.read_yaml = AsyncMock(return_value={"type": "service_account"})

    init = mocker.patch("firebase_admin.initialize_app", return_value=MagicMock())
    mocker.patch("firebase_admin.credentials.Certificate", return_value=MagicMock())

    await pn._init_firebase()

    init.assert_called_once()
    assert init.call_args.kwargs["options"] == {"httpTimeout": _FIREBASE_HTTP_TIMEOUT}


# ── storage migration ────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_open_migrates_legacy_storage_shape(mocker) -> None:
    pn = make_pushnotifier()
    pn._vfs = MagicMock()
    pn._vfs.read_yaml = AsyncMock(return_value={"tim": [{"token": "t1", "platform": "android"}]})
    mocker.patch.object(pn.comm, "clients", [])
    pn.comm.register_event = AsyncMock()
    mocker.patch.object(Module, "open", AsyncMock())
    mocker.patch.object(PushNotifier, "_init_firebase", AsyncMock())

    await pn.open()

    assert pn._devices == {"tim": {"devices": [{"token": "t1", "platform": "android"}]}}


@pytest.mark.asyncio
async def test_open_keeps_current_storage_shape(mocker) -> None:
    pn = make_pushnotifier()
    storage = {"tim": {"devices": [{"token": "t1", "platform": "android"}], "preferences": ["log_error"]}}
    pn._vfs = MagicMock()
    pn._vfs.read_yaml = AsyncMock(return_value=storage)
    mocker.patch.object(pn.comm, "clients", [])
    pn.comm.register_event = AsyncMock()
    mocker.patch.object(Module, "open", AsyncMock())
    mocker.patch.object(PushNotifier, "_init_firebase", AsyncMock())

    await pn.open()

    assert pn._devices == storage


# ── close() ───────────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_close_shuts_down_firebase_app(mocker) -> None:
    pn = make_pushnotifier()
    mocker.patch.object(Module, "close", AsyncMock())
    app = MagicMock()
    pn._fcm_app = app

    firebase_admin_mock = MagicMock()
    firebase_admin_mock.delete_app = MagicMock()
    mocker.patch.dict("sys.modules", {"firebase_admin": firebase_admin_mock})

    await pn.close()

    firebase_admin_mock.delete_app.assert_called_once_with(app)
    assert pn._fcm_app is None


@pytest.mark.asyncio
async def test_close_survives_firebase_cleanup_failure(mocker) -> None:
    # reproduces a real production bug: firebase_admin.delete_app() -> messaging service
    # close() calls asyncio.run() internally, which raises RuntimeError when invoked from
    # within our own already-running event loop if not offloaded to a thread.
    pn = make_pushnotifier()
    mocker.patch.object(Module, "close", AsyncMock())
    pn._fcm_app = MagicMock()

    firebase_admin_mock = MagicMock()
    firebase_admin_mock.delete_app = MagicMock(
        side_effect=RuntimeError("asyncio.run() cannot be called from a running event loop")
    )
    mocker.patch.dict("sys.modules", {"firebase_admin": firebase_admin_mock})

    await pn.close()  # must not raise

    assert pn._fcm_app is None


@pytest.mark.asyncio
async def test_close_noop_without_fcm_app(mocker) -> None:
    pn = make_pushnotifier()
    mocker.patch.object(Module, "close", AsyncMock())
    pn._fcm_app = None

    await pn.close()  # must not raise or try to import firebase_admin
