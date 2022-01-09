import asyncio
from typing import Optional

import pytest

from pyobs.utils import exceptions as exc
from pyobs.utils.exceptions import PyObsError


def setup_function() -> None:
    exc.clear()


def test_log() -> None:
    exc.MotionError()
    # should contain MotionError and PyObsError
    assert len(exc._local_exceptions) == 2


def test_register() -> None:
    def cb(exception: PyObsError, module: Optional[str] = None) -> None:
        pass

    exc.register_exception(exc.MotionError, 5, callback=cb)
    assert len(exc._handlers) == 1


def test_empty() -> None:
    assert len(exc._local_exceptions) == 0
    assert len(exc._handlers) == 0


def test_callback() -> None:
    event = asyncio.Event()

    def cb(exception: PyObsError, module: Optional[str] = None) -> None:
        assert isinstance(exception, exc.MotionError)
        assert module is None
        event.set()

    # get triggered after 3 MotionErrors
    exc.register_exception(exc.MotionError, 3, callback=cb)

    # 1st is fine
    exc.MotionError()
    assert event.is_set() is False

    # 2nd is fine
    exc.MotionError()
    assert event.is_set() is False

    # 3rd triggers callback
    exc.MotionError()
    assert event.is_set() is True


def test_raise() -> None:
    event = asyncio.Event()

    def cb(exception: PyObsError, module: Optional[str] = None) -> None:
        assert isinstance(exception, exc.MotionError)
        assert module is None
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


async def test_timespan() -> None:
    event = asyncio.Event()

    def cb(exception: PyObsError, module: Optional[str] = None) -> None:
        assert isinstance(exception, exc.MotionError)
        assert module is None
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
    with pytest.raises(exc.SevereError):
        raise exc.MotionError()
    assert event.is_set()


def test_remote() -> None:
    # get triggered after 3 MotionErrors
    exc.register_exception(exc.MotionError, 3, throw=True)

    # raise two, shouldn't do anything
    exc.MotionError()
    exc.MotionError()

    # one RemoteError should trigger MotionError
    with pytest.raises(exc.SevereError) as exc_info:
        raise exc.RemoteError(module="test", exception=exc.MotionError())
    assert isinstance(exc_info.value, exc.SevereError)
    assert isinstance(exc_info.value.exception, exc.RemoteError)
    assert isinstance(exc_info.value.exception.exception, exc.MotionError)


def test_remote_module() -> None:
    # get triggered after 3 MotionErrors
    exc.register_exception(exc.MotionError, 1, module="test", throw=True)

    # raise, shouldn't do anything
    exc.MotionError()
    exc.MotionError()

    # same with other remote errors with other module
    exc.RemoteError(module="wrong", exception=exc.MotionError())
    exc.RemoteError(module="wrong", exception=exc.MotionError())

    # but with correct module, it should
    with pytest.raises(exc.SevereError) as exc_info:
        raise exc.RemoteError(module="test", exception=exc.MotionError())
    assert isinstance(exc_info.value, exc.SevereError)
    assert isinstance(exc_info.value.exception, exc.RemoteError)
    assert isinstance(exc_info.value.exception.exception, exc.MotionError)
