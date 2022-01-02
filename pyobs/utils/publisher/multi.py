from typing import List, Union, Any, Optional, Dict
import logging

from .publisher import Publisher


log = logging.getLogger(__name__)


class MultiPublisher(Publisher):
    """Forwards a message to multiple publishers."""

    def __init__(self, publishers: Optional[List[Union[Publisher, Dict[str, Any]]]] = None, **kwargs: Any):
        """Initialize new multi publisher.

        Args:
            publishers: Publishers to forwards messages to.
        """
        Publisher.__init__(self, **kwargs)

        # store
        self._publishers: List[Publisher] = [] if publishers is None else [self.add_child_object(p) for p in publishers]

    async def __call__(self, **kwargs: Any) -> None:
        """Publish the given results.

        Args:
            **kwargs: Results to publish.
        """

        # loop all publishers
        for p in self._publishers:
            # forward message
            await p(**kwargs)


__all__ = ["MultiPublisher"]
