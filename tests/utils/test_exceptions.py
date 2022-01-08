import asyncio
from typing import Optional, Type, cast

import pytest

from pyobs.utils import exceptions as exc
from pyobs.utils.exceptions import PyObsException


def setup_function() -> None:
    exc.clear()


def test_log() -> None:
    exc.MotionError()
    # should contain MotionError and PyObsException
    assert len(exc._local_exceptions) == 2


def test_register() -> None:
    def cb(exception: PyObsException, module: Optional[str] = None) -> None:
        pass

    exc.register_exception(exc.MotionError, 5, cb)
    assert len(exc._handlers) == 1


def test_empty() -> None:
    assert len(exc._local_exceptions) == 0
    assert len(exc._handlers) == 0


def test_callback() -> None:
    event = asyncio.Event()

    def cb(exception: PyObsException, module: Optional[str] = None) -> None:
        assert isinstance(exception, exc.MotionError)
        assert module is None
        event.set()

    # get triggered after 3 MotionErrors
    exc.register_exception(exc.MotionError, 3, cb)

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

    def cb(exception: PyObsException, module: Optional[str] = None) -> None:
        assert isinstance(exception, exc.MotionError)
        assert module is None
        event.set()

    # get triggered after 2 MotionErrors
    exc.register_exception(exc.MotionError, 2, cb, throw=True)

    # 1st is fine
    exc.MotionError()

    # 2nd raises SevereException
    with pytest.raises(exc.SevereException) as exc_info:
        raise exc.MotionError()

    # nested exception is MotionError
    assert isinstance(exc_info.value, exc.SevereException)
    assert isinstance(exc_info.value.exception, exc.MotionError)


async def test_timespan() -> None:
    event = asyncio.Event()

    def cb(exception: PyObsException, module: Optional[str] = None) -> None:
        assert isinstance(exception, exc.MotionError)
        assert module is None
        event.set()

    # get triggered after 3 MotionErrors
    exc.register_exception(exc.MotionError, 3, cb, timespan=0.1, throw=True)

    # raise two and wait a little
    exc.MotionError()
    exc.MotionError()
    await asyncio.sleep(0.11)
    exc.MotionError()

    # raise two more
    exc.MotionError()
    exc.MotionError()
    with pytest.raises(exc.SevereException):
        raise exc.MotionError()
