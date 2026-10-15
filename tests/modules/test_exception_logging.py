import asyncio
import logging
from typing import Any
from unittest.mock import AsyncMock

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


@pytest.mark.asyncio
async def test_ancestor_resolved_remote_fault_counts_for_domain_and_remote_handlers() -> None:
    """A fault whose leaf class was not imported arrives as its core ancestor (see rpc.reconstruct_fault) and
    counts towards handlers registered for that ancestor with module=, and, unchanged, towards RemoteError
    handlers with module=. Handlers without module= only count locally raised exceptions."""
    from pyobs.comm.xmpp.rpc import reconstruct_fault

    module = _AbortableModule(exc.FocusError("unused"))
    domain, remote = [], []

    async def on_domain(exception: exc.PyobsError) -> None:
        domain.append(exception)

    async def on_remote(exception: exc.PyobsError) -> None:
        remote.append(exception)

    module._register_exception(exc.MotionError, 1, module="telescope", callback=on_domain)
    module._register_exception(exc.RemoteError, 1, module="telescope", callback=on_remote)

    fault = reconstruct_fault("plugin.NotImported", "stuck", ["pyobs.utils.exceptions.MotionError"], "telescope")
    module._record_exception(fault)
    await asyncio.sleep(0.01)

    assert domain == [fault]
    assert remote == [fault]


@pytest.mark.asyncio
@pytest.mark.parametrize("fault_kind", ["core", "leaf", "fallback"])
async def test_expected_remote_pointing_faults_only_trigger_explicit_handlers(fault_kind):
    from pyobs.comm.xmpp.rpc import reconstruct_fault
    from pyobs.modules.telescope.basetelescope import AltitudeLimitError

    if fault_kind == "fallback":
        fault = reconstruct_fault(
            "unimported_driver.PointingRejected",
            "below limit",
            ["pyobs.utils.exceptions.PointingLimitError"],
            "telescope",
        )
        assert type(fault) is exc.PointingLimitError
        assert fault.original_type == "unimported_driver.PointingRejected"
    else:
        cls = exc.PointingLimitError if fault_kind == "core" else AltitudeLimitError
        fault = cls("below limit", remote_module="telescope")
    assert fault.remote_module == "telescope"
    module = _AbortableModule(fault)
    broad, domain, ancestor, leaf = (AsyncMock() for _ in range(4))
    module._register_exception(exc.RemoteError, 3, module="telescope", callback=broad)
    module._register_exception(exc.PointingLimitError, 3, module="telescope", callback=domain)
    module._register_exception(exc.PyobsError, 3, module="telescope", callback=ancestor)
    if fault_kind == "leaf":
        module._register_exception(AltitudeLimitError, 3, module="telescope", callback=leaf)

    for _ in range(3):
        with pytest.raises(type(fault)) as raised:
            await module.execute("abort", sender="tester")
        assert raised.value is fault
        await asyncio.sleep(0)

    assert (exc.RemoteError, "telescope") not in module._remote_exception_log
    broad.assert_not_awaited()
    domain.assert_awaited_once_with(fault)
    ancestor.assert_awaited_once_with(fault)
    if fault_kind == "leaf":
        leaf.assert_awaited_once_with(fault)


@pytest.mark.asyncio
async def test_local_pointing_faults_still_trigger_explicit_handlers():
    fault = exc.PointingLimitError("below limit")
    module = _AbortableModule(fault)
    broad, domain = AsyncMock(), AsyncMock()
    module._register_exception(exc.RemoteError, 3, callback=broad)
    module._register_exception(exc.PointingLimitError, 3, callback=domain)
    for _ in range(3):
        with pytest.raises(exc.PointingLimitError):
            await module.execute("abort", sender="tester")
        await asyncio.sleep(0)
    broad.assert_not_awaited()
    domain.assert_awaited_once_with(fault)


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "fault_type", [exc.RemoteTimeoutError, exc.GrabImageError, exc.MotionError, exc.UnclassifiedError]
)
async def test_expected_fault_does_not_advance_or_retrigger_remote_threshold(fault_type):
    module = _AbortableModule(exc.FocusError("unused"))
    callback = AsyncMock()
    module._register_exception(exc.RemoteError, 3, timespan=600, module="telescope", callback=callback)
    rejected = exc.PointingLimitError("below limit", remote_module="telescope")
    failure = fault_type("failed", remote_module="telescope")
    for count in range(1, 4):
        module._record_exception(failure)
        await asyncio.sleep(0)
        assert len(module._remote_exception_log[(exc.RemoteError, "telescope")]) == count
        assert callback.await_count == (1 if count == 3 else 0)
        module._record_exception(rejected)
        await asyncio.sleep(0)
        assert len(module._remote_exception_log[(exc.RemoteError, "telescope")]) == count
        assert callback.await_count == (1 if count == 3 else 0)
    callback.assert_awaited_once_with(failure)


@pytest.mark.asyncio
async def test_remote_threshold_retains_timespan_and_counter_scoping(mocker):
    clock = mocker.patch("pyobs.modules.module.time.time", return_value=1000.0)
    module = _AbortableModule(exc.FocusError("unused"))
    other = _AbortableModule(exc.FocusError("unused"))
    callback, local, other_callback = AsyncMock(), AsyncMock(), AsyncMock()
    module._register_exception(exc.RemoteError, 3, timespan=600, module="telescope", callback=callback)
    module._register_exception(exc.RemoteError, 3, timespan=600, callback=local)
    other._register_exception(exc.RemoteError, 3, timespan=600, module="telescope", callback=other_callback)
    failure = exc.RemoteTimeoutError("failed", remote_module="telescope")
    for _ in range(2):
        module._record_exception(failure)
    clock.return_value = 1601.0
    module._record_exception(failure)
    await asyncio.sleep(0)
    callback.assert_not_awaited()
    for _ in range(3):
        module._record_exception(exc.GrabImageError("camera failed", remote_module="camera"))
        module._record_exception(exc.PointingLimitError("rejected", remote_module="telescope"))
    await asyncio.sleep(0)
    callback.assert_not_awaited()
    for _ in range(2):
        module._record_exception(failure)
        await asyncio.sleep(0)
    callback.assert_awaited_once_with(failure)
    local.assert_not_awaited()
    other_callback.assert_not_awaited()
    assert other._remote_exception_log == {}
