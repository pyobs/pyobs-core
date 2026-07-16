import logging

from pyobs.utils import exceptions as exc


def test_log_only_logs_once() -> None:
    calls = []

    class _FakeLogger:
        def log(self, level, message, **kwargs) -> None:  # type: ignore[no-untyped-def]
            calls.append((level, message))

    error = exc.FocusError("could not focus")
    error.log(_FakeLogger(), "INFO", "first")
    error.log(_FakeLogger(), "ERROR", "second")

    assert len(calls) == 1
    assert calls[0] == (logging.INFO, "first")


def test_resolve_finds_registered_subclass() -> None:
    qualified_name = f"{exc.FocusError.__module__}.{exc.FocusError.__qualname__}"
    assert exc.PyobsError.resolve(qualified_name) is exc.FocusError


def test_resolve_returns_none_for_unregistered_name() -> None:
    assert exc.PyobsError.resolve("builtins.ValueError") is None
    assert exc.PyobsError.resolve("some.module.that.was.never.imported.WeatherDataError") is None


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
