import logging
import time
from typing import Any


class ResolvableErrorLogger:
    def __init__(
        self,
        logger: logging.Logger,
        error_level: int = logging.ERROR,
        resolved_level: int = logging.INFO,
        min_interval: int = 600,
    ):
        """Logging for resolvable errors.

        Args:
            logger: Logger to use.
            error_level: Log level for error.
            resolved_level: Log level for resolved message.
            min_interval: Minimum interval between error logs in seconds.
        """
        self._log = logger
        self._error_level = error_level
        self._resolved_level = resolved_level
        self._min_interval = min_interval
        self._time_of_last_error = 0.0
        self._last_error_message = ""

    def error(self, msg: str, *args: Any, **kwargs: Any) -> None:
        """Log an error message."""

        now = time.time()
        # we log, if last message is old enough or text changed
        if now - self._time_of_last_error > self._min_interval or msg != self._last_error_message:
            self._log.log(self._error_level, msg, *args, **kwargs)
            # Only remember what we actually logged, and when: min_interval has to measure the
            # gap between logs, not between calls. Storing every (suppressed) call's timestamp
            # would let a recurring error polled every few seconds push it forward forever and
            # never re-log, even though the comparison here is what decides that.
            self._time_of_last_error = now
            self._last_error_message = msg

    def resolve(self, msg: str, *args: Any, **kwargs: Any) -> None:
        """Resolve an error."""

        # only log, if we had an actual error
        if self._time_of_last_error > 0:
            self._log.log(self._resolved_level, msg, *args, **kwargs)

        # reset
        self._time_of_last_error = 0
        self._last_error_message = ""


__all__ = ["ResolvableErrorLogger"]
