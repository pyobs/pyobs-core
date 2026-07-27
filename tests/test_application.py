"""Tests for Application's module_factory path (see specs/plans/gui-interactive-login.md) and
that the existing config-file path keeps working unchanged."""

from __future__ import annotations

import asyncio
import signal
from typing import Any
from unittest.mock import AsyncMock, MagicMock

import pytest

from pyobs.application import Application
from pyobs.modules import Module


def make_bare_application(**attrs: Any) -> Application:
    """Construct an Application without running __init__ (which creates and installs a real
    event loop) -- pokes just the attributes the method under test needs."""
    app = Application.__new__(Application)
    for key, value in attrs.items():
        setattr(app, key, value)
    return app


# ── __init__ validation ──────────────────────────────────────────────────────


def test_init_requires_config_or_module_factory() -> None:
    with pytest.raises(ValueError, match="Exactly one"):
        Application()


def test_init_rejects_both_config_and_module_factory() -> None:
    with pytest.raises(ValueError, match="Exactly one"):
        Application(config="foo.yaml", module_factory=AsyncMock(), loop_module_class=Module)


def test_init_requires_loop_module_class_with_module_factory() -> None:
    with pytest.raises(ValueError, match="loop_module_class"):
        Application(module_factory=AsyncMock())


# ── config path unchanged ─────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_init_config_path_constructs_module_synchronously(tmp_path) -> None:
    config = tmp_path / "test_module.yaml"
    config.write_text("class: pyobs.modules.Module\n")

    app = Application(config=str(config))

    assert isinstance(app._module, Module)
    assert app._module_factory is None
    app._loop.close()


# ── module_factory path ──────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_init_module_factory_defers_module_construction() -> None:
    factory = AsyncMock(return_value=MagicMock(spec=Module))

    app = Application(module_factory=factory, loop_module_class=Module)

    assert app._module is None
    assert app._module_factory is factory
    factory.assert_not_awaited()
    app._loop.close()


@pytest.mark.asyncio
async def test_main_resolves_module_from_factory_and_runs_it() -> None:
    module = MagicMock(spec=Module)
    module.startup = AsyncMock()
    module.main = AsyncMock()
    module.close = AsyncMock()
    factory = AsyncMock(return_value=module)

    app = make_bare_application(_module=None, _module_factory=factory)
    await app._main()

    factory.assert_awaited_once()
    assert app._module is module
    module.startup.assert_awaited_once()
    module.main.assert_awaited_once()
    module.close.assert_awaited_once()


@pytest.mark.asyncio
async def test_main_does_not_call_factory_when_module_already_set() -> None:
    """Config path: _module is already set in __init__, so _main() must not touch the factory."""
    module = MagicMock(spec=Module)
    module.startup = AsyncMock()
    module.main = AsyncMock()
    module.close = AsyncMock()
    factory = AsyncMock()

    app = make_bare_application(_module=module, _module_factory=factory)
    await app._main()

    factory.assert_not_awaited()
    module.startup.assert_awaited_once()


@pytest.mark.asyncio
async def test_main_handles_factory_raising_gracefully() -> None:
    """gui-interactive-login.md's open question: does module_factory raising (e.g. user closes
    the login window without connecting) shut down cleanly instead of propagating? It must not
    try to close() a module that was never built."""
    factory = AsyncMock(side_effect=RuntimeError("login window closed"))

    app = make_bare_application(_module=None, _module_factory=factory)

    await app._main()  # must not raise -- caught internally, same as any other _main() failure

    assert app._module is None


# ── signal handling before the factory resolves ───────────────────────────────


@pytest.mark.asyncio
async def test_signal_handler_before_factory_resolves_cancels_main_task() -> None:
    """A signal arriving while module_factory is still pending (e.g. a login dialog still open)
    has nothing to Module.quit() -- it must cancel the pending wait directly instead, and must
    not raise trying to call quit() on a None module."""
    # _loop is a stand-in, not the real running loop: _signal_handler() calls self._loop.stop()
    # in production that's fine (Application.run() owns a dedicated loop for exactly this), but
    # here it would stop pytest-asyncio's own driving loop out from under the test itself.
    # main_task still needs to be a real Task on the real running loop to be cancellable/awaitable.
    real_loop = asyncio.get_running_loop()

    async def never_resolves() -> None:
        await asyncio.Future()

    main_task = real_loop.create_task(never_resolves())

    app = make_bare_application(_module=None, _loop=MagicMock(), _main_task=main_task)

    app._signal_handler(signal.SIGTERM)

    assert main_task.cancelling() > 0
    app._loop.stop.assert_called_once()
    with pytest.raises(asyncio.CancelledError):
        await main_task
