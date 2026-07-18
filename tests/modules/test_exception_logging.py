import asyncio
import logging
from typing import Any

import pytest

from pyobs.interfaces import IAbortable
from pyobs.modules import Module
from pyobs.utils import exceptions as exc
from pyobs.utils.enums import ModuleState


class _AbortableModule(Module, IAbortable):
    """Minimal test module whose abort() raises whatever exception it's given.

    Starts in ModuleState.READY rather than the real STARTING default -- these tests
    exercise execute()'s exception classification/logging, not startup gating (that's
    covered separately in tests/modules/test_startup_gating.py).
    """

    def __init__(self, to_raise: Exception, **kwargs: Any):
        Module.__init__(self, **kwargs)
        self._to_raise = to_raise
        self._state = ModuleState.READY

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
async def test_call_id_is_attached_to_the_exception_and_included_in_the_log_line(caplog):
    module = _AbortableModule(exc.FocusError("could not focus"))

    with caplog.at_level(logging.INFO):
        with pytest.raises(exc.FocusError) as exc_info:
            await module.execute("abort", sender="tester", call_id="42")

    assert exc_info.value.call_id == "42"
    record = next(r for r in caplog.records if "Exception was raised in call to abort" in r.message)
    assert "call_id=42" in record.message


@pytest.mark.asyncio
async def test_call_id_omitted_from_log_line_when_not_given(caplog):
    module = _AbortableModule(exc.FocusError("could not focus"))

    with caplog.at_level(logging.INFO):
        with pytest.raises(exc.FocusError) as exc_info:
            await module.execute("abort", sender="tester")

    assert exc_info.value.call_id is None
    record = next(r for r in caplog.records if "Exception was raised in call to abort" in r.message)
    assert "call_id" not in record.message


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
async def test_non_pyobs_error_is_wrapped_as_unclassified_and_logs_as_error_with_traceback(caplog):
    # a raw builtin (or vendor SDK exception) wasn't part of the deliberate PyobsError contract --
    # it always logs loud, and the caller receives UnclassifiedError, not the original type
    module = _AbortableModule(ValueError("driver blew up"))

    with caplog.at_level(logging.INFO):
        with pytest.raises(exc.UnclassifiedError) as exc_info:
            await module.execute("abort", sender="tester")

    assert exc_info.value.original_type == "builtins.ValueError"
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


def test_disable_exception_logging_rejects_unclassified_error():
    module = _AbortableModule(exc.FocusError("could not focus"))
    with pytest.raises(ValueError):
        module._disable_exception_logging(exc.UnclassifiedError)


@pytest.mark.asyncio
async def test_execute_never_substitutes_the_raised_type() -> None:
    # no more construction-time metaclass magic: raising FocusError always raises FocusError,
    # however many times it recurs -- severity escalation only ever fires a callback now
    module = _AbortableModule(exc.FocusError("could not focus"))
    module._register_exception(exc.FocusError, 2, callback=None)

    for _ in range(5):
        with pytest.raises(exc.FocusError):
            await module.execute("abort", sender="tester")


@pytest.mark.asyncio
async def test_register_exception_fires_callback_after_limit_reached() -> None:
    module = _AbortableModule(exc.FocusError("could not focus"))
    seen = []

    async def callback(exception: exc.PyobsError) -> None:
        seen.append(exception)

    module._register_exception(exc.FocusError, 2, callback=callback)

    with pytest.raises(exc.FocusError):
        await module.execute("abort", sender="tester")
    await asyncio.sleep(0.01)
    assert seen == []

    with pytest.raises(exc.FocusError):
        await module.execute("abort", sender="tester")
    await asyncio.sleep(0.01)
    assert len(seen) == 1
    assert isinstance(seen[0], exc.FocusError)


@pytest.mark.asyncio
async def test_register_exception_respects_timespan() -> None:
    module = _AbortableModule(exc.FocusError("could not focus"))
    seen = []

    async def callback(exception: exc.PyobsError) -> None:
        seen.append(exception)

    module._register_exception(exc.FocusError, 2, timespan=0.05, callback=callback)

    with pytest.raises(exc.FocusError):
        await module.execute("abort", sender="tester")
    await asyncio.sleep(0.1)  # first occurrence ages out of the timespan

    with pytest.raises(exc.FocusError):
        await module.execute("abort", sender="tester")
    await asyncio.sleep(0.01)
    assert seen == []  # only one occurrence within the timespan, limit not reached


@pytest.mark.asyncio
async def test_register_exception_is_instance_scoped_not_shared_across_modules() -> None:
    # two Module instances watching the same exception type must not share counters
    module_a = _AbortableModule(exc.FocusError("could not focus"))
    module_b = _AbortableModule(exc.FocusError("could not focus"))
    seen_a: list[exc.PyobsError] = []
    seen_b: list[exc.PyobsError] = []

    async def callback_a(exception: exc.PyobsError) -> None:
        seen_a.append(exception)

    async def callback_b(exception: exc.PyobsError) -> None:
        seen_b.append(exception)

    module_a._register_exception(exc.FocusError, 2, callback=callback_a)
    module_b._register_exception(exc.FocusError, 2, callback=callback_b)

    with pytest.raises(exc.FocusError):
        await module_a.execute("abort", sender="tester")
    await asyncio.sleep(0.01)
    assert seen_a == []
    assert seen_b == []  # module_b's count is untouched by module_a's occurrence

    with pytest.raises(exc.FocusError):
        await module_a.execute("abort", sender="tester")
    await asyncio.sleep(0.01)
    assert len(seen_a) == 1
    assert seen_b == []


@pytest.mark.asyncio
async def test_register_exception_remote_error_fires_regardless_of_specific_type() -> None:
    # AutoFocusSeries-style usage: _register_exception(exc.RemoteError, ..., module=X) should still
    # fire on a remote failure of any specific type, even though that type no longer literally
    # subclasses RemoteError now that faults raise as their real type instead of wrapped
    module = _AbortableModule(exc.GrabImageError("could not grab", remote_module="camera"))
    seen = []

    async def callback(exception: exc.PyobsError) -> None:
        seen.append(exception)

    module._register_exception(exc.RemoteError, 1, module="camera", callback=callback)

    with pytest.raises(exc.GrabImageError):
        await module.execute("abort", sender="tester")
    await asyncio.sleep(0.01)
    assert len(seen) == 1
    assert isinstance(seen[0], exc.GrabImageError)


@pytest.mark.asyncio
async def test_register_exception_remote_module_scoping() -> None:
    module = _AbortableModule(exc.FocusError("could not focus", remote_module="wrong"))
    seen = []

    async def callback(exception: exc.PyobsError) -> None:
        seen.append(exception)

    module._register_exception(exc.FocusError, 1, module="test", callback=callback)

    # wrong remote module -- shouldn't count
    with pytest.raises(exc.FocusError):
        await module.execute("abort", sender="tester")
    await asyncio.sleep(0.01)
    assert seen == []
