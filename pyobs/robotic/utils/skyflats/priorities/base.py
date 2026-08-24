from abc import ABCMeta, abstractmethod

from pyobs.utils.serialization import PolymorphicBaseModel


class SkyflatPriorities(PolymorphicBaseModel, metaclass=ABCMeta):
    """Base class for sky flat priorities."""

    @abstractmethod
    async def __call__(self) -> dict[tuple[str, tuple[int, int]], float]: ...


__all__ = ["SkyflatPriorities"]
