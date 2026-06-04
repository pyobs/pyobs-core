from __future__ import annotations

from typing import Union, Any
import logging

from .publisher import Publisher


log = logging.getLogger(__name__)


class MultiPublisher(Publisher):
    """Forwards a message to multiple publishers."""

    def __init__(self, publishers: list[Publisher | dict[str, Any]] | None = None, **kwargs: Any):
        """Initialize new multi publisher.

        Args:
            publishers: Publishers to forward messages to.
        """
        Publisher.__init__(self, **kwargs)

        # store
        self._publishers: list[Publisher] = (
            [] if publishers is None else [self.add_child_object(p, Publisher) for p in publishers]
        )

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
