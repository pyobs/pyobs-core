"""Tests for running a module under systemd: READY=1 once the module is open, and no stderr log handler when
stderr goes to the journal anyway (see specs/plans/2026-11-25-pyobsd-systemd-mode.md)."""

from __future__ import annotations

import logging
import os
import sys
from pathlib import Path
from typing import Any
from unittest.mock import AsyncMock, MagicMock

import logging_journald
import pytest

from pyobs import application
from pyobs.application import Application, _stderr_is_journal
from pyobs.modules import Module

# ── READY=1 ──────────────────────────────────────────────────────────────────


def make_module(**kwargs: Any) -> MagicMock:
    module = MagicMock(spec=Module)
    module.startup = AsyncMock(**kwargs)
    module.main = AsyncMock()
    module.close = AsyncMock()
    return module


def make_app(module: MagicMock) -> Application:
    app = Application.__new__(Application)
    app._module = module
    app._module_factory = None
    return app


@pytest.mark.asyncio
async def test_ready_after_startup(mocker) -> None:
    notify = mocker.patch.object(application.shutdown, "notify")
    module = make_module()
    # READY=1 must come after startup() and before main()
    module.main.side_effect = lambda: notify.assert_called_once_with("READY=1")

    await make_app(module)._main()

    module.startup.assert_awaited_once()
    module.main.assert_awaited_once()


@pytest.mark.asyncio
async def test_no_ready_if_startup_fails(mocker) -> None:
    notify = mocker.patch.object(application.shutdown, "notify")
    module = make_module(side_effect=RuntimeError("no camera"))

    await make_app(module)._main()

    notify.assert_not_called()
    module.main.assert_not_awaited()


# ── stderr and the journal ───────────────────────────────────────────────────


@pytest.fixture
def stderr_file(tmp_path: Path, monkeypatch):
    """Returns a function that makes a file stderr and returns the JOURNAL_STREAM value systemd would set for it.
    It has to be called in the test itself, pytest's output capturing replaces sys.stderr after the fixtures."""
    with open(tmp_path / "stderr", "w") as f:

        def use() -> str:
            monkeypatch.setattr(sys, "stderr", f)
            st = os.fstat(f.fileno())
            return f"{st.st_dev}:{st.st_ino}"

        yield use


def test_stderr_is_journal(stderr_file, monkeypatch) -> None:
    monkeypatch.setenv("JOURNAL_STREAM", stderr_file())
    assert _stderr_is_journal()


def test_stderr_is_journal_not_set(stderr_file, monkeypatch) -> None:
    stderr_file()
    monkeypatch.delenv("JOURNAL_STREAM", raising=False)
    assert not _stderr_is_journal()


def test_stderr_is_journal_inherited(stderr_file, monkeypatch) -> None:
    """A child process inherits JOURNAL_STREAM, but its stderr may go elsewhere."""
    device, inode = stderr_file().split(":")
    monkeypatch.setenv("JOURNAL_STREAM", f"{device}:{int(inode) + 1}")
    assert not _stderr_is_journal()


@pytest.mark.parametrize("value", ["", "garbage", "1:2:3", "a:b"])
def test_stderr_is_journal_invalid(stderr_file, monkeypatch, value) -> None:
    stderr_file()
    monkeypatch.setenv("JOURNAL_STREAM", value)
    assert not _stderr_is_journal()


def test_stderr_is_journal_no_stderr(monkeypatch) -> None:
    monkeypatch.setenv("JOURNAL_STREAM", "1:2")
    monkeypatch.setattr(sys, "stderr", None)
    assert not _stderr_is_journal()


class FakeJournaldLogHandler(logging.Handler):
    """Stands in for logging_journald's handler, so the tests don't need a journal."""

    LEVELS: dict[int, int] = {}

    def __init__(self, identifier: str = "", **kwargs: Any) -> None:
        super().__init__()


def handler_types(monkeypatch, mocker, tmp_path: Path, syslog: bool) -> list[str]:
    monkeypatch.setattr(logging_journald, "JournaldLogHandler", FakeJournaldLogHandler)
    basic_config = mocker.patch.object(application.logging, "basicConfig")
    config = tmp_path / "test_module.yaml"
    config.write_text("class: pyobs.modules.Module\n")

    app = Application(config=str(config), syslog=syslog)
    app._loop.close()

    return [type(h).__name__ for h in basic_config.call_args.kwargs["handlers"]]


@pytest.mark.asyncio
async def test_no_stream_handler_under_journal(stderr_file, monkeypatch, mocker, tmp_path) -> None:
    monkeypatch.setenv("JOURNAL_STREAM", stderr_file())
    assert handler_types(monkeypatch, mocker, tmp_path, syslog=True) == ["PyobsJournaldLogHandler"]


@pytest.mark.asyncio
async def test_stream_handler_without_syslog(stderr_file, monkeypatch, mocker, tmp_path) -> None:
    """Without --syslog, stderr is the only way into the journal, so it stays."""
    monkeypatch.setenv("JOURNAL_STREAM", stderr_file())
    assert handler_types(monkeypatch, mocker, tmp_path, syslog=False) == ["StreamHandler"]


@pytest.mark.asyncio
async def test_stream_handler_outside_journal(stderr_file, monkeypatch, mocker, tmp_path) -> None:
    stderr_file()
    monkeypatch.delenv("JOURNAL_STREAM", raising=False)
    assert handler_types(monkeypatch, mocker, tmp_path, syslog=True) == ["StreamHandler", "PyobsJournaldLogHandler"]


# ── exit code ────────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_main_not_failed() -> None:
    app = make_app(make_module())
    app._failed = False
    await app._main()
    assert not app._failed


@pytest.mark.asyncio
@pytest.mark.parametrize("step", ["startup", "main", "close"])
async def test_main_failed(step) -> None:
    module = make_module()
    getattr(module, step).side_effect = RuntimeError("broken")
    app = make_app(module)
    app._failed = False

    await app._main()

    assert app._failed
    module.close.assert_awaited_once()


@pytest.mark.asyncio
async def test_main_failed_factory() -> None:
    app = make_app(MagicMock())
    app._module = None
    app._module_factory = AsyncMock(side_effect=RuntimeError("login window closed"))
    app._failed = False

    await app._main()

    assert app._failed


def run_app(tmp_path: Path, mocker, **module_kwargs: Any) -> int:
    """Application.run() with a real event loop and a module with the given startup/main/close."""
    config = tmp_path / "test_module.yaml"
    config.write_text("class: pyobs.modules.Module\n")
    app = Application(config=str(config))
    assert app._module is not None
    for name, kwargs in module_kwargs.items():
        mocker.patch.object(app._module, name, AsyncMock(**kwargs))
    return app.run()


def test_run_exit_code_0(tmp_path, mocker) -> None:
    assert run_app(tmp_path, mocker, startup={}, main={}, close={}) == 0


def test_run_exit_code_1(tmp_path, mocker) -> None:
    assert run_app(tmp_path, mocker, startup={"side_effect": RuntimeError("no camera")}, close={}) == 1


def test_run_exit_code_after_signal(tmp_path, mocker) -> None:
    """A stop by signal is a normal end: 0, unless closing the module fails."""
    import signal

    def main_until_signal(app: Application) -> Any:
        async def main() -> None:
            app._signal_handler(signal.SIGTERM)

        return main

    for close, code in (({}, 0), ({"side_effect": RuntimeError("warm-up failed")}, 1)):
        config = tmp_path / "test_module.yaml"
        config.write_text("class: pyobs.modules.Module\n")
        app = Application(config=str(config))
        assert app._module is not None
        mocker.patch.object(app._module, "startup", AsyncMock())
        mocker.patch.object(app._module, "main", AsyncMock(side_effect=main_until_signal(app)))
        mocker.patch.object(app._module, "close", AsyncMock(**close))
        mocker.patch.object(application.shutdown, "start_watchdog")
        mocker.patch.object(application.shutdown, "mark_stopping")
        assert app.run() == code


def test_run_signal_during_startup(tmp_path, mocker) -> None:
    """A signal while startup() still waits (e.g. for an unreachable XMPP server) ends the wait and closes the
    module, instead of hanging until SIGKILL (#1114). A stop by signal is a normal end: 0."""
    import asyncio
    import signal

    config = tmp_path / "test_module.yaml"
    config.write_text("class: pyobs.modules.Module\n")
    app = Application(config=str(config))
    assert app._module is not None

    async def startup_until_signal() -> None:
        app._signal_handler(signal.SIGTERM)
        await asyncio.Future()

    mocker.patch.object(app._module, "startup", AsyncMock(side_effect=startup_until_signal))
    main = mocker.patch.object(app._module, "main", AsyncMock())
    close = mocker.patch.object(app._module, "close", AsyncMock())
    mocker.patch.object(application.shutdown, "start_watchdog")
    mocker.patch.object(application.shutdown, "mark_stopping")
    assert app.run() == 0
    main.assert_not_awaited()
    close.assert_awaited_once()


def test_run_signal_while_xmpp_unreachable(tmp_path, mocker) -> None:
    """Same with a real XmppComm whose server doesn't answer: SIGTERM ends the module within seconds (#1114)."""
    import signal
    import socket
    import time

    # a port nothing listens on
    with socket.socket() as sock:
        sock.bind(("127.0.0.1", 0))
        port = sock.getsockname()[1]

    config = tmp_path / "test_module.yaml"
    config.write_text(
        "class: pyobs.modules.Module\n"
        "comm:\n"
        "  class: pyobs.comm.xmpp.XmppComm\n"
        "  jid: test@localhost\n"
        "  password: nothing\n"
        f"  server: 127.0.0.1:{port}\n"
    )
    app = Application(config=str(config))
    mocker.patch.object(application.shutdown, "start_watchdog")
    mocker.patch.object(application.shutdown, "mark_stopping")
    app._loop.call_later(1.0, app._signal_handler, signal.SIGTERM)
    # without the fix, run() would hang here forever: end it after 15 s, so the test fails instead
    app._loop.call_later(15.0, lambda: app._main_task.cancel())

    t0 = time.monotonic()
    assert app.run() == 0
    assert time.monotonic() - t0 < 10
