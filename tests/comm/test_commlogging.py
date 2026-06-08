from __future__ import annotations

import logging
from unittest.mock import MagicMock

import pytest

from pyobs.comm.commlogging import CommLoggingHandler
from pyobs.events import LogEvent


@pytest.fixture
def comm() -> MagicMock:
    c = MagicMock()
    c.log_message = MagicMock()
    return c


@pytest.fixture
def handler(comm: MagicMock) -> CommLoggingHandler:
    return CommLoggingHandler(comm)


# ── emit ──────────────────────────────────────────────────────────────────────


def test_emit_calls_log_message(handler: CommLoggingHandler, comm: MagicMock) -> None:
    record = logging.LogRecord(
        name="test",
        level=logging.INFO,
        pathname="/some/path/module.py",
        lineno=42,
        msg="hello world",
        args=(),
        exc_info=None,
        func="test_func",
    )
    handler.emit(record)
    comm.log_message.assert_called_once()


def test_emit_sends_log_event(handler: CommLoggingHandler, comm: MagicMock) -> None:
    record = logging.LogRecord(
        name="test",
        level=logging.WARNING,
        pathname="/some/path/module.py",
        lineno=10,
        msg="something wrong",
        args=(),
        exc_info=None,
        func="run",
    )
    handler.emit(record)
    event = comm.log_message.call_args[0][0]
    assert isinstance(event, LogEvent)


def test_emit_uses_basename_of_pathname(handler: CommLoggingHandler, comm: MagicMock) -> None:
    record = logging.LogRecord(
        name="test",
        level=logging.INFO,
        pathname="/deep/nested/path/mymodule.py",
        lineno=1,
        msg="test",
        args=(),
        exc_info=None,
        func="f",
    )
    handler.emit(record)
    event = comm.log_message.call_args[0][0]
    assert event.filename == "mymodule.py"
    assert "/" not in event.filename


def test_emit_level_name(handler: CommLoggingHandler, comm: MagicMock) -> None:
    for level, name in [
        (logging.DEBUG, "DEBUG"),
        (logging.INFO, "INFO"),
        (logging.WARNING, "WARNING"),
        (logging.ERROR, "ERROR"),
    ]:
        comm.log_message.reset_mock()
        record = logging.LogRecord(
            name="test", level=level, pathname="f.py", lineno=1, msg="msg", args=(), exc_info=None, func="f"
        )
        handler.emit(record)
        event = comm.log_message.call_args[0][0]
        assert event.level == name


def test_emit_line_number(handler: CommLoggingHandler, comm: MagicMock) -> None:
    record = logging.LogRecord(
        name="test", level=logging.INFO, pathname="f.py", lineno=99, msg="test", args=(), exc_info=None, func="f"
    )
    handler.emit(record)
    event = comm.log_message.call_args[0][0]
    assert event.line == 99


def test_emit_formats_message(handler: CommLoggingHandler, comm: MagicMock) -> None:
    record = logging.LogRecord(
        name="test",
        level=logging.INFO,
        pathname="f.py",
        lineno=1,
        msg="hello %s",
        args=("world",),
        exc_info=None,
        func="f",
    )
    handler.emit(record)
    event = comm.log_message.call_args[0][0]
    assert "hello world" in event.message


def test_emit_uses_record_created_as_iso_time(handler: CommLoggingHandler, comm: MagicMock) -> None:
    record = logging.LogRecord(
        name="test", level=logging.INFO, pathname="f.py", lineno=1, msg="test", args=(), exc_info=None, func="f"
    )
    handler.emit(record)
    event = comm.log_message.call_args[0][0]
    # time should be ISO format parseable by astropy Time
    from datetime import UTC, datetime

    from pyobs.utils.time import Time

    expected = datetime.fromtimestamp(record.created, tz=UTC).strftime("%Y-%m-%dT%H:%M:%S.%f")
    assert event.time == expected
    assert Time(event.time) is not None  # must be parseable
    # must not be a raw float (regression guard)
    with pytest.raises(ValueError):
        float(event.time)


def test_via_logging_integration(comm: MagicMock) -> None:
    """Handler works correctly when attached to a real logger."""
    handler = CommLoggingHandler(comm)
    logger = logging.getLogger("test_commlogging_integration")
    logger.addHandler(handler)
    logger.setLevel(logging.DEBUG)

    logger.info("integration test message")

    comm.log_message.assert_called_once()
    event = comm.log_message.call_args[0][0]
    assert "integration test message" in event.message
    logger.removeHandler(handler)
