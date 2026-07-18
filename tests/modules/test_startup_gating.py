"""Tests for the ModuleState.STARTING guard in Module.execute() and the Module.startup()
helper that transitions a module out of it once open() has fully finished.
"""

from __future__ import annotations

from typing import Any

import pytest

from pyobs.interfaces import IAbortable, IStartStop
from pyobs.modules import Module
from pyobs.utils import exceptions as exc
from pyobs.utils.enums import ModuleState


class _AbortableModule(Module, IAbortable):
    """Minimal test module with one guarded (non-whitelisted) RPC method."""

    def __init__(self, **kwargs: Any):
        Module.__init__(self, **kwargs)
        self.aborted = False

    async def abort(self, **kwargs: Any) -> None:
        self.aborted = True


class _StartStopModule(Module, IStartStop):
    """Module implementing IStartStop, whose abstract `start(**kwargs)` RPC method has the
    same name as Module's lifecycle helper -- regression coverage for that collision (see
    DEV_STARTUP.md, "Post-landing regression")."""

    def __init__(self, **kwargs: Any):
        Module.__init__(self, **kwargs)
        self.running = False

    async def start(self, **kwargs: Any) -> None:
        self.running = True

    async def stop(self, **kwargs: Any) -> None:
        self.running = False

    async def is_running(self, **kwargs: Any) -> bool:
        return self.running


def test_module_starts_in_starting_state() -> None:
    """A freshly constructed module hasn't been started yet."""
    module = _AbortableModule()
    assert module._state == ModuleState.STARTING


@pytest.mark.asyncio
async def test_execute_rejects_non_whitelisted_call_while_starting() -> None:
    """A regular RPC method must be rejected while the module is still STARTING."""
    module = _AbortableModule()

    with pytest.raises(exc.ModuleStartingError):
        await module.execute("abort", sender="tester")

    assert module.aborted is False


@pytest.mark.asyncio
@pytest.mark.parametrize("method", ["get_permitted_methods", "reset_error"])
async def test_execute_allows_whitelisted_calls_while_starting(method: str) -> None:
    """Introspection/recovery methods must stay callable during STARTING."""
    module = _AbortableModule()

    result = await module.execute(method, sender="tester")

    assert result is not None


@pytest.mark.asyncio
async def test_start_transitions_to_ready_and_unblocks_execute() -> None:
    """Module.startup() must run the full open() chain and then flip STARTING -> READY."""
    module = _AbortableModule(own_comm=False)

    await module.startup()

    assert module._state == ModuleState.READY
    await module.execute("abort", sender="tester")
    assert module.aborted is True


@pytest.mark.asyncio
async def test_open_alone_does_not_reach_ready() -> None:
    """Calling open() directly (bypassing startup()) must leave the module in STARTING --
    this is the exact gap that broke MultiModule sub-modules before startup() existed."""
    module = _AbortableModule(own_comm=False)

    await module.open()

    assert module._state == ModuleState.STARTING
    with pytest.raises(exc.ModuleStartingError):
        await module.execute("abort", sender="tester")


@pytest.mark.asyncio
async def test_startup_reaches_ready_on_module_implementing_istartstop() -> None:
    """Module.startup() must be the lifecycle helper actually called by MultiModule/
    Application, not IStartStop.start() -- a name collision would silently call the RPC
    command instead, leaving the module stuck in STARTING forever (real regression, caught
    via a pyobs-gui full.yaml run: a DummyAutoGuiding module never reached READY)."""
    module = _StartStopModule(own_comm=False)

    await module.startup()

    assert module._state == ModuleState.READY
    assert module.running is False  # startup() must not have invoked IStartStop.start()

    await module.execute("start", sender="tester")
    assert module.running is True
