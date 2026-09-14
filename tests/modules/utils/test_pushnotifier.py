from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import pytest

from pyobs.comm import Comm
from pyobs.events import LogEvent, ModuleOpenedEvent, TestEvent
from pyobs.interfaces import ICooling, IMotion, IPushNotifications
from pyobs.interfaces.IMotion import MotionState
from pyobs.interfaces.interface import registered_interfaces
from pyobs.modules.utils.pushnotifier import PushNotifier, _Alert
from pyobs.utils.enums import MotionStatus


def make_pushnotifier(**kwargs: object) -> PushNotifier:
    comm = MagicMock(spec=Comm)
    comm.name = "pushnotifier"
    return PushNotifier(credentials_file="/pyobs/firebase-credentials.json", comm=comm, **kwargs)


# ── interface registration ───────────────────────────────────────────────────


def test_interface_is_registered() -> None:
    assert "IPushNotifications" in registered_interfaces()


def test_interface_has_no_own_state() -> None:
    assert IPushNotifications.has_own_state() is False


def test_register_device_is_rpc_dispatchable() -> None:
    pn = make_pushnotifier()
    assert "register_device" in pn._methods


# ── register_device ──────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_register_device_stores_by_sender() -> None:
    pn = make_pushnotifier()
    pn._vfs = MagicMock()
    pn._vfs.write_yaml = AsyncMock()

    await pn.register_device("token-1", sender="tim")

    assert pn._devices["tim"][0]["token"] == "token-1"
    assert pn._devices["tim"][0]["platform"] == "android"
    pn._vfs.write_yaml.assert_awaited_once_with("/pyobs/pushnotifier.yaml", pn._devices)


@pytest.mark.asyncio
async def test_register_device_replaces_same_token() -> None:
    pn = make_pushnotifier()
    pn._vfs = MagicMock()
    pn._vfs.write_yaml = AsyncMock()

    await pn.register_device("token-1", sender="tim")
    await pn.register_device("token-1", platform="android", sender="tim")

    assert len(pn._devices["tim"]) == 1


@pytest.mark.asyncio
async def test_register_device_keeps_multiple_devices_per_sender() -> None:
    pn = make_pushnotifier()
    pn._vfs = MagicMock()
    pn._vfs.write_yaml = AsyncMock()

    await pn.register_device("token-phone", sender="tim")
    await pn.register_device("token-tablet", sender="tim")

    assert {d["token"] for d in pn._devices["tim"]} == {"token-phone", "token-tablet"}


# ── log event handling (§2b) ─────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_process_log_entry_enqueues_error() -> None:
    pn = make_pushnotifier()
    entry = LogEvent(time="t", level="ERROR", filename="f", function="fn", line=1, message="boom")

    handled = await pn._process_log_entry(entry, "camera1")

    assert handled is True
    alert = pn._alert_queue.get_nowait()
    assert alert.title == "camera1: ERROR"
    assert alert.body == "boom"


@pytest.mark.asyncio
async def test_process_log_entry_enqueues_critical() -> None:
    pn = make_pushnotifier()
    entry = LogEvent(time="t", level="CRITICAL", filename="f", function="fn", line=1, message="fatal")

    await pn._process_log_entry(entry, "camera1")

    assert pn._alert_queue.qsize() == 1


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
    pn._alert_queue = __import__("asyncio").Queue(maxsize=1)
    pn._enqueue_alert("a", "1")

    pn._enqueue_alert("b", "2")  # queue full, should be dropped, not raise

    assert pn._alert_queue.qsize() == 1
    assert pn._alert_queue.get_nowait() == _Alert(title="a", body="1")


@pytest.mark.asyncio
async def test_send_to_all_devices_only_targets_android(mocker) -> None:
    pn = make_pushnotifier()
    pn._fcm_app = MagicMock()
    pn._devices = {
        "tim": [
            {"token": "android-token", "platform": "android"},
            {"token": "ios-token", "platform": "ios"},
        ]
    }
    sent_tokens: list[str] = []

    def fake_send(message: object, app: object) -> None:
        sent_tokens.append(message.token)

    messaging_mock = MagicMock()
    messaging_mock.send = MagicMock(side_effect=fake_send)
    messaging_mock.Message = MagicMock(side_effect=lambda notification, token: MagicMock(token=token))
    mocker.patch.dict("sys.modules", {"firebase_admin.messaging": messaging_mock})

    await pn._send_to_all_devices(_Alert(title="t", body="b"))

    assert sent_tokens == ["android-token"]


@pytest.mark.asyncio
async def test_send_to_all_devices_noop_without_fcm_app() -> None:
    pn = make_pushnotifier()
    pn._fcm_app = None
    pn._devices = {"tim": [{"token": "x", "platform": "android"}]}

    # must not raise even though there's no app to send through
    await pn._send_to_all_devices(_Alert(title="t", body="b"))
