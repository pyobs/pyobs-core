"""#1031: an init() that was aborted on purpose must not escalate the telescope module to ERROR."""

from __future__ import annotations

import asyncio
from typing import Any

import pytest

from pyobs.modules.module import Module
from pyobs.utils import exceptions as exc
from pyobs.utils.enums import ModuleState
from tests.modules.telescope.test_dummyradectelescope import make_dummyradectelescope


def _make_failing(error: exc.PyobsError) -> Any:
    tel = make_dummyradectelescope()

    async def _init(**kwargs: Any) -> None:
        raise error

    tel._methods["init"] = (_init, tel._methods["init"][1], tel._methods["init"][2])
    tel._state = ModuleState.READY
    return tel


@pytest.mark.asyncio
async def test_aborted_init_does_not_escalate() -> None:
    tel = _make_failing(exc.InitAbortedError("Startup of telescope was interrupted."))
    for _ in range(4):
        with pytest.raises(exc.InitAbortedError):
            await tel.execute("init", sender="t")
        await asyncio.sleep(0.01)
    assert tel._state == ModuleState.READY


@pytest.mark.asyncio
async def test_failed_init_still_escalates() -> None:
    tel = _make_failing(exc.InitError("PLC refused"))
    for _ in range(3):
        with pytest.raises(exc.InitError):
            await tel.execute("init", sender="t")
        await asyncio.sleep(0.01)
    assert tel._state == ModuleState.ERROR
    with pytest.raises(exc.ModuleError):
        await tel.execute("init", sender="t")


def test_hierarchy() -> None:
    assert not issubclass(exc.InitAbortedError, exc.MotionError)
    assert not issubclass(exc.InitAbortedError, exc.InitError)
    assert not issubclass(exc.InitAbortedError, exc.AbortedError)


@pytest.mark.asyncio
async def test_remote_aborted_init_only_triggers_explicit_handlers() -> None:
    fault = exc.InitAbortedError("interrupted", remote_module="telescope")
    assert not Module._counts_as_remote_error(fault)
    assert Module._counts_as_remote_error(exc.InitError("x", remote_module="telescope"))
