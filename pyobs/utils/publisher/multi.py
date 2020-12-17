from typing import List, Union
import logging

from .publisher import Publisher


log = logging.getLogger(__name__)


class MultiPublisher(Publisher):
    """Forwards a message to multiple publishers."""

    def __init__(self, publishers: List[Union[Publisher, dict]] = None, *args, **kwargs):
        """Initialize new multi publisher.

        Args:
            publishers: Publishers to forwards messages to.
        """
        Publisher.__init__(self, *args, **kwargs)

        # store
        self._publishers: List[Publisher] = [] if publishers is None else [self._add_child_object(p) for p in publishers]

    def __call__(self, **kwargs):
        """Publish the given results.

        Args:
            **kwargs: Results to publish.
        """

        # loop all publishers
        for p in self._publishers:
            # forward message
            p(**kwargs)


__all__ = ['MultiPublisher']
