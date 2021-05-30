import logging


class DuplicateFilter(logging.Filter):
    """Logging filter that removes duplicate entries.

    Should be used with new logger, e.g.:
        log = logging.getLogger('filtered_logger')
        log.addFilter(DuplicateFilter())
        log.info('Test')
    """

    def __init__(self, *args, **kwargs):
        logging.Filter.__init__(self, *args, **kwargs)
        self.last_log = ''

    def filter(self, record):
        if record.getMessage() != getattr(self, "last_log", None):
            self.last_log = record.getMessage()
            return True
        return False


__all__ = ['DuplicateFilter']
