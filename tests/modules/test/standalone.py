import asyncio
import logging

import pytest

from pyobs.modules.test import StandAlone
from pyobs.utils import exceptions as exc


def test_default():
    module = StandAlone()
    assert module._message == "Hello world"
    assert module._interval == 10


@pytest.mark.asyncio
async def test_loop(mocker, caplog):
    mocker.patch("asyncio.sleep", return_value=None)
    module = StandAlone("Testmessage", 3)

    with caplog.at_level(logging.INFO):
        await module._loop()

    assert caplog.messages[0] == "Testmessage"
    asyncio.sleep.assert_called_once_with(3)


@pytest.mark.asyncio
async def test_background_task():
    module = StandAlone()
    assert module._message_func in module._background_tasks


@pytest.mark.asyncio
async def test_get_permitted_methods_default():
    module = StandAlone()
    methods = await module.get_permitted_methods()
    assert set(methods) == set(module.methods.keys())
    assert "reset_error" in methods


def test_acl_default_open():
    module = StandAlone()
    assert module._acl_allow is None
    assert module._acl_deny is None
    assert module._acl_mode == "enforce"


def test_acl_allow():
    module = StandAlone(acl={"allow": {"scheduler": ["expose", "abort"]}})
    assert module._acl_allow == {"scheduler": ["expose", "abort"]}
    assert module._acl_deny is None
    assert module._acl_mode == "enforce"


def test_acl_deny():
    module = StandAlone(acl={"deny": ["legacy_gui"]})
    assert module._acl_allow is None
    assert module._acl_deny == ["legacy_gui"]


def test_acl_log_mode():
    module = StandAlone(acl={"mode": "log", "allow": {"scheduler": "*"}})
    assert module._acl_mode == "log"


def test_acl_allow_and_deny_mutually_exclusive():
    with pytest.raises(ValueError):
        StandAlone(acl={"allow": {"scheduler": "*"}, "deny": ["legacy_gui"]})


def test_acl_invalid_mode():
    with pytest.raises(ValueError):
        StandAlone(acl={"allow": {"scheduler": "*"}, "mode": "bogus"})


@pytest.mark.asyncio
async def test_execute_no_acl_allows_everyone():
    module = StandAlone()
    assert await module.execute("reset_error", sender="anyone") is True


@pytest.mark.asyncio
async def test_execute_allow_permits_listed_method():
    module = StandAlone(acl={"allow": {"scheduler": ["reset_error"]}})
    assert await module.execute("reset_error", sender="scheduler") is True


@pytest.mark.asyncio
async def test_execute_allow_denies_unlisted_method():
    module = StandAlone(acl={"allow": {"scheduler": ["set_config_value"]}})
    with pytest.raises(exc.ForbiddenError):
        await module.execute("reset_error", sender="scheduler")


@pytest.mark.asyncio
async def test_execute_allow_denies_unknown_sender():
    module = StandAlone(acl={"allow": {"scheduler": "*"}})
    with pytest.raises(exc.ForbiddenError):
        await module.execute("reset_error", sender="stranger")


@pytest.mark.asyncio
async def test_execute_allow_star_permits_any_method():
    module = StandAlone(acl={"allow": {"mastermind": "*"}})
    assert await module.execute("reset_error", sender="mastermind") is True


@pytest.mark.asyncio
async def test_execute_deny_blocks_listed_sender():
    module = StandAlone(acl={"deny": ["legacy_gui"]})
    with pytest.raises(exc.ForbiddenError):
        await module.execute("reset_error", sender="legacy_gui")


@pytest.mark.asyncio
async def test_execute_deny_allows_other_senders():
    module = StandAlone(acl={"deny": ["legacy_gui"]})
    assert await module.execute("reset_error", sender="anyone_else") is True


@pytest.mark.asyncio
async def test_execute_log_mode_never_raises_but_warns(caplog):
    module = StandAlone(acl={"mode": "log", "allow": {"scheduler": ["set_config_value"]}})
    with caplog.at_level(logging.WARNING):
        result = await module.execute("reset_error", sender="stranger")
    assert result is True
    assert any("stranger" in m and "reset_error" in m for m in caplog.messages)


@pytest.mark.asyncio
async def test_execute_get_permitted_methods_exempt_from_acl():
    module = StandAlone(acl={"allow": {"scheduler": ["set_config_value"]}})
    # a denied sender must still be able to ask what it's permitted to do
    methods = await module.execute("get_permitted_methods", sender="stranger")
    assert methods == []


@pytest.mark.asyncio
async def test_get_permitted_methods_allow():
    module = StandAlone(acl={"allow": {"scheduler": ["reset_error", "set_config_value"]}})
    methods = await module.get_permitted_methods(sender="scheduler")
    assert set(methods) == {"reset_error", "set_config_value"}


@pytest.mark.asyncio
async def test_get_permitted_methods_deny():
    module = StandAlone(acl={"deny": ["legacy_gui"]})
    assert await module.get_permitted_methods(sender="legacy_gui") == []
    assert set(await module.get_permitted_methods(sender="anyone")) == set(module.methods.keys())


@pytest.mark.asyncio
async def test_get_permitted_methods_log_mode_returns_all():
    module = StandAlone(acl={"mode": "log", "allow": {"scheduler": ["set_config_value"]}})
    methods = await module.get_permitted_methods(sender="stranger")
    assert set(methods) == set(module.methods.keys())
