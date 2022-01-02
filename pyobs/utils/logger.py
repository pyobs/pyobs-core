import logging
from typing import Any


class DuplicateFilter(logging.Filter):
    """Logging filter that removes duplicate entries.

    Should be used with new logger, e.g.:
        log = logging.getLogger('filtered_logger')
        log.addFilter(DuplicateFilter())
        log.info('Test')
    """

    def __init__(self, *args: Any, **kwargs: Any):
        logging.Filter.__init__(self, *args, **kwargs)
        self.last_log = ""

    def filter(self, record: Any) -> bool:
        if record.getMessage() != getattr(self, "last_log", None):
            self.last_log = record.getMessage()
            return True
        return False


__all__ = ["DuplicateFilter"]
