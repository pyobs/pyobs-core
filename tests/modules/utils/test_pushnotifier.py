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
from pyobs.modules.utils.pushnotifier import PushNotifier, _Alert
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
