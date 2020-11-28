import logging

from .publisher import Publisher


log = logging.getLogger(__name__)


class LogPublisher(Publisher):
    def __init__(self, level: str = 'info', *args, **kwargs):
        """Initialize new log publisher.

        Args:
            level: Level to log on.
        """
        Publisher.__init__(self, *args, **kwargs)

        # set and check level
        if not hasattr(log, level):
            raise ValueError('Unknown log level.')
        self._log_function = getattr(log, level)

    def __call__(self, **kwargs):
        """Publish the given results.

        Args:
            **kwargs: Results to publish.
        """

        # build string
        s = ', '.join(['{0}={1}'.format(k, v) for k, v in kwargs.items()])

        # log it
        self._log_function(s)


__all__ = ['LogPublisher']
