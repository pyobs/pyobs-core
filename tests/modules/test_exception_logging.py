import logging
from typing import Any

import pytest

from pyobs.interfaces import IAbortable
from pyobs.modules import Module
from pyobs.utils import exceptions as exc


def setup_function() -> None:
    # isolate from any severity-escalation handlers other test modules may have registered --
    # register_exception's state is process-global (see DESIGN_exception_handling.md's Assessment §C)
    exc.clear()


class _AbortableModule(Module, IAbortable):
    """Minimal test module whose abort() raises whatever exception it's given."""

    def __init__(self, to_raise: Exception, **kwargs: Any):
        Module.__init__(self, **kwargs)
        self._to_raise = to_raise

    async def abort(self, **kwargs: Any) -> None:
        raise self._to_raise


@pytest.mark.asyncio
async def test_domain_exception_logs_as_info_without_traceback_by_default(caplog):
    module = _AbortableModule(exc.FocusError("could not focus"))

    with caplog.at_level(logging.INFO):
        with pytest.raises(exc.FocusError):
            await module.execute("abort", sender="tester")

    record = next(r for r in caplog.records if "Exception was raised in call to abort" in r.message)
    assert record.levelname == "INFO"
    assert not record.exc_info


@pytest.mark.asyncio
async def test_module_error_always_logs_as_error_with_traceback(caplog):
    module = _AbortableModule(exc.ModuleError("broken"))

    with caplog.at_level(logging.INFO):
        with pytest.raises(exc.ModuleError):
            await module.execute("abort", sender="tester")

    record = next(r for r in caplog.records if "Exception was raised in call to abort" in r.message)
    assert record.levelname == "ERROR"
    assert record.exc_info is not None


@pytest.mark.asyncio
async def test_severe_error_always_logs_as_error_with_traceback(caplog):
    module = _AbortableModule(exc.SevereError(exception=exc.FocusError("could not focus")))

    with caplog.at_level(logging.INFO):
        with pytest.raises(exc.SevereError):
            await module.execute("abort", sender="tester")

    record = next(r for r in caplog.records if "Exception was raised in call to abort" in r.message)
    assert record.levelname == "ERROR"
    assert record.exc_info is not None


@pytest.mark.asyncio
async def test_disable_exception_logging_suppresses_the_local_line(caplog):
    module = _AbortableModule(exc.FocusError("could not focus"))
    module._disable_exception_logging(exc.FocusError)

    with caplog.at_level(logging.INFO):
        with pytest.raises(exc.FocusError):
            await module.execute("abort", sender="tester")

    assert not any("Exception was raised in call to abort" in r.message for r in caplog.records)


@pytest.mark.asyncio
async def test_disable_exception_logging_covers_subclasses():
    module = _AbortableModule(exc.FocusError("could not focus"))
    module._disable_exception_logging(exc.PyobsError)
    assert isinstance(exc.FocusError("x"), module._disabled_exception_logging)


def test_disable_exception_logging_rejects_module_error():
    module = _AbortableModule(exc.FocusError("could not focus"))
    with pytest.raises(ValueError):
        module._disable_exception_logging(exc.ModuleError)


def test_disable_exception_logging_rejects_severe_error():
    module = _AbortableModule(exc.FocusError("could not focus"))
    with pytest.raises(ValueError):
        module._disable_exception_logging(exc.SevereError)
