from abc import ABCMeta, abstractmethod
from typing import Any

from pyobs.object import Object


class Publisher(Object, metaclass=ABCMeta):
    @abstractmethod
    async def __call__(self, **kwargs: Any) -> None:
        """Publish the given results.

        Args:
            **kwargs: Results to publish.
        """
        ...


__all__ = ["Publisher"]
