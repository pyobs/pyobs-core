import logging
import time


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
        self._time_of_last_error = 0
        self._last_error_message = ""

    def error(self, msg: str, *args, **kwargs) -> None:
        """Log an error message."""

        # we log, if last message is old enough or text changed
        if self._time_of_last_error - time.time() > self._min_interval or msg != self._last_error_message:
            self._log.log(self._error_level, msg, *args, **kwargs)

        # store it
        self._time_of_last_error = time.time()
        self._last_error_message = msg

    def resolve(self, msg: str, *args, **kwargs):
        """Resolve an error."""

        # only log, if we had an actual error
        if self._time_of_last_error > 0:
            self._log.log(self._resolved_level, msg, *args, **kwargs)

        # reset
        self._time_of_last_error = 0
        self._last_error_message = ""


__all__ = ["ResolvableErrorLogger"]
