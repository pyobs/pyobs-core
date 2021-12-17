from typing import Any

from pyobs.object import Object


class Publisher(Object):
    def __init__(self, **kwargs: Any):
        Object.__init__(self, **kwargs)

    def __call__(self, **kwargs: Any) -> None:
        """Publish the given results.

        Args:
            **kwargs: Results to publish.
        """
        raise NotImplementedError


__all__ = ['Publisher']
