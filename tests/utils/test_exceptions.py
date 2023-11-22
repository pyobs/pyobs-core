import asyncio
import pytest
from pyobs.utils import exceptions as exc
from pyobs.utils.exceptions import PyObsError


pytest_plugins = ("pytest_asyncio",)


def setup_function() -> None:
    exc.clear()


def test_log() -> None:
    exc.MotionError()
    # should still be empty, since exception was not registered
    assert len(exc._local_exceptions) == 0


def test_register() -> None:
    async def cb(exception: PyObsError) -> None:
        pass

    exc.register_exception(exc.MotionError, 5, callback=cb)
    assert len(exc._handlers) == 1


def test_empty() -> None:
    assert len(exc._local_exceptions) == 0
    assert len(exc._handlers) == 0


@pytest.mark.asyncio
async def test_callback() -> None:
    event = asyncio.Event()

    async def cb(exception: PyObsError) -> None:
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

    async def cb(exception: PyObsError) -> None:
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

    async def cb(exception: PyObsError) -> None:
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
    # get triggered after 3 MotionErrors
    exc.register_exception(exc.MotionError, 3, throw=True)

    # raise two, shouldn't do anything
    exc.MotionError()
    exc.MotionError()
    await asyncio.sleep(0.01)

    # one InvocationError should trigger MotionError
    with pytest.raises(exc.SevereError) as exc_info:
        raise exc.InvocationError(module="test", exception=exc.MotionError())
    assert isinstance(exc_info.value, exc.SevereError)
    assert isinstance(exc_info.value.exception, exc.InvocationError)
    assert isinstance(exc_info.value.exception.exception, exc.MotionError)


def test_remote_module() -> None:
    # get triggered after 3 MotionErrors
    exc.register_exception(exc.MotionError, 1, module="test", throw=True)

    # raise, shouldn't do anything
    exc.MotionError()
    exc.MotionError()

    # same with other remote errors with other module
    exc.InvocationError(module="wrong", exception=exc.MotionError())
    exc.InvocationError(module="wrong", exception=exc.MotionError())

    # but with correct module, it should
    with pytest.raises(exc.SevereError) as exc_info:
        raise exc.InvocationError(module="test", exception=exc.MotionError())
    assert isinstance(exc_info.value, exc.SevereError)
    assert isinstance(exc_info.value.exception, exc.InvocationError)
    assert isinstance(exc_info.value.exception.exception, exc.MotionError)
