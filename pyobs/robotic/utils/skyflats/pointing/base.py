from abc import abstractmethod, ABCMeta

from pyobs.interfaces import IPointingAltAz
from pyobs.utils.serialization import PolymorphicBaseModel


class SkyFlatsBasePointing(PolymorphicBaseModel, metaclass=ABCMeta):
    """Base class for flat pointings."""

    __module__ = "pyobs.utils.skyflats.pointing"

    @abstractmethod
    async def __call__(self, telescope: IPointingAltAz) -> None:
        """Move telescope.

        Args:
            telescope: Telescope to use.
        """
        ...

    async def reset(self) -> None:
        """Reset pointing."""
        pass


__all__ = ["SkyFlatsBasePointing"]
