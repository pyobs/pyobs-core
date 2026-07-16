import asyncio

import pytest

from pyobs.utils import exceptions as exc
from pyobs.utils.exceptions import PyobsError

pytest_plugins = ("pytest_asyncio",)


def setup_function() -> None:
    exc.clear()


def test_log() -> None:
    exc.MotionError()
    # should still be empty, since exception was not registered
    assert len(exc._local_exceptions) == 0


def test_register() -> None:
    async def cb(exception: PyobsError) -> None:
        pass

    exc.register_exception(exc.MotionError, 5, callback=cb)
    assert len(exc._handlers) == 1


def test_empty() -> None:
    assert len(exc._local_exceptions) == 0
    assert len(exc._handlers) == 0


@pytest.mark.asyncio
async def test_callback() -> None:
    event = asyncio.Event()

    async def cb(exception: PyobsError) -> None:
        assert isinstance(exception, exc.MotionError)
        event.set()

    # get triggered after 3 MotionErrors
    exc.register_exception(exc.MotionError, 3, callback=cb)

    # 1st is fine
    exc.MotionError()
    await asyncio.sleep(0.01)
    assert event.is_set() is False

    # 2nd is fine
    exc.MotionError()
    await asyncio.sleep(0.01)
    assert event.is_set() is False

    # 3rd triggers callback
    exc.MotionError()
    await asyncio.sleep(0.01)
    assert event.is_set() is True


@pytest.mark.asyncio
async def test_raise() -> None:
    event = asyncio.Event()

    async def cb(exception: PyobsError) -> None:
        assert isinstance(exception, exc.MotionError)
        event.set()

    # get triggered after 2 MotionErrors
    exc.register_exception(exc.MotionError, 2, callback=cb, throw=True)

    # 1st is fine
    exc.MotionError()

    # 2nd raises SevereError
    with pytest.raises(exc.SevereError) as exc_info:
        raise exc.MotionError()

    # nested exception is MotionError
    assert isinstance(exc_info.value, exc.SevereError)
    assert isinstance(exc_info.value.exception, exc.MotionError)


@pytest.mark.asyncio
async def test_timespan() -> None:
    event = asyncio.Event()

    async def cb(exception: PyobsError) -> None:
        assert isinstance(exception, exc.MotionError)
        event.set()

    # get triggered after 3 MotionErrors
    exc.register_exception(exc.MotionError, 3, callback=cb, timespan=0.1, throw=True)

    # raise two and wait a little
    exc.MotionError()
    exc.MotionError()
    await asyncio.sleep(0.11)
    exc.MotionError()

    # raise two more
    exc.MotionError()
    exc.MotionError()
    await asyncio.sleep(0.01)
    with pytest.raises(exc.SevereError):
        raise exc.MotionError()
    assert event.is_set()


@pytest.mark.asyncio
async def test_remote() -> None:
    # a domain exception reconstructed from a fault carries remote_module (set by rpc.py's
    # _on_jabber_rpc_method_fault, see Assessment §A) instead of arriving wrapped in InvocationError
    exc.register_exception(exc.MotionError, 3, module="test", throw=True)

    # raise two, shouldn't do anything
    exc.MotionError(remote_module="test")
    exc.MotionError(remote_module="test")
    await asyncio.sleep(0.01)

    # third one from the same remote module triggers escalation
    with pytest.raises(exc.SevereError) as exc_info:
        raise exc.MotionError(remote_module="test")
    assert isinstance(exc_info.value, exc.SevereError)
    assert isinstance(exc_info.value.exception, exc.MotionError)


def test_remote_broad_remote_error_handler_still_fires_regardless_of_specific_type() -> None:
    # AutoFocusSeries-style usage: register_exception(exc.RemoteError, ..., module=X) should still
    # fire on a remote failure of any specific type, even though that type no longer literally
    # subclasses RemoteError now that faults raise as their real type instead of wrapped
    exc.register_exception(exc.RemoteError, 1, module="camera", throw=True)

    with pytest.raises(exc.SevereError) as exc_info:
        raise exc.GrabImageError("could not grab", remote_module="camera")
    assert isinstance(exc_info.value, exc.SevereError)
    assert isinstance(exc_info.value.exception, exc.GrabImageError)


def test_forbidden_error() -> None:
    error = exc.ForbiddenError(
        "Caller 'scheduler' is not permitted to invoke 'reset_usb'.",
        sender="scheduler",
        method="reset_usb",
        module="scheduler",
    )
    assert isinstance(error, exc.RemoteError)
    assert error.sender == "scheduler"
    assert error.method == "reset_usb"
    assert error.module == "scheduler"


def test_remote_module() -> None:
    # get triggered after 1 MotionError specifically from module "test"
    exc.register_exception(exc.MotionError, 1, module="test", throw=True)

    # local (non-remote) MotionErrors shouldn't count
    exc.MotionError()
    exc.MotionError()

    # MotionErrors from a different remote module shouldn't count either
    exc.MotionError(remote_module="wrong")
    exc.MotionError(remote_module="wrong")

    # but one from the correct module should trigger
    with pytest.raises(exc.SevereError) as exc_info:
        raise exc.MotionError(remote_module="test")
    assert isinstance(exc_info.value, exc.SevereError)
    assert isinstance(exc_info.value.exception, exc.MotionError)
