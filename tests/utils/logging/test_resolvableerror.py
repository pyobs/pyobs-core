import logging

from pyobs.utils.logging.resolvableerror import ResolvableErrorLogger


def create_logger():
    # create logger
    logger = logging.getLogger("test_logger")
    logger.setLevel(logging.DEBUG)

    # create console handler and set level to debug
    ch = logging.StreamHandler()
    ch.setLevel(logging.DEBUG)

    # create formatter
    formatter = logging.Formatter("%(levelname)s - %(message)s")

    # add formatter to ch
    ch.setFormatter(formatter)

    # add ch to logger
    logger.addHandler(ch)
    return logger


def test_logger(capsys):
    # init
    logger = create_logger()
    rel = ResolvableErrorLogger(logger)

    # logging resolve should do nothing
    rel.resolve("Resolve")
    _, err = capsys.readouterr()
    assert err == ""

    # logging error gives the error message
    rel.error("Some error")
    _, err = capsys.readouterr()
    assert "ERROR - Some error" in err

    # Same should give nothing
    rel.error("Some error")
    _, err = capsys.readouterr()
    assert err == ""

    # logging new error gives the error message
    rel.error("Some new error")
    _, err = capsys.readouterr()
    assert "ERROR - Some new error" in err

    # logging resolve should output
    rel.resolve("Resolved")
    _, err = capsys.readouterr()
    assert "INFO - Resolved" in err


class _FakeTime:
    """Stand-in for the `time` module whose clock the test advances by hand."""

    def __init__(self, now: float = 1000.0) -> None:
        self.now = now

    def time(self) -> float:
        return self.now


def test_identical_error_is_relogged_after_min_interval(capsys, monkeypatch):
    logger = create_logger()
    rel = ResolvableErrorLogger(logger, min_interval=600)
    clock = _FakeTime()
    monkeypatch.setattr("pyobs.utils.logging.resolvableerror.time", clock)

    rel.error("Some error")
    _, err = capsys.readouterr()
    assert "ERROR - Some error" in err

    # min_interval measures the gap between logs, not between calls: polling the same error
    # every few seconds neither re-logs nor pushes the deadline further out
    clock.now += 10
    rel.error("Some error")
    clock.now += 10
    rel.error("Some error")
    _, err = capsys.readouterr()
    assert err == ""

    # ...but once min_interval has passed since that log, the reminder goes out
    clock.now += 620
    rel.error("Some error")
    _, err = capsys.readouterr()
    assert "ERROR - Some error" in err


def test_resolve_is_silent_when_no_error_was_ever_logged(capsys, monkeypatch):
    logger = create_logger()
    rel = ResolvableErrorLogger(logger)
    clock = _FakeTime()
    monkeypatch.setattr("pyobs.utils.logging.resolvableerror.time", clock)

    rel.resolve("Resolved")
    _, err = capsys.readouterr()
    assert err == ""
