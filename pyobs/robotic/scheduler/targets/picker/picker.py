import abc
from astropy.coordinates import SkyCoord

from pyobs.utils.serialization import PolymorphicBaseModel


class Picker(PolymorphicBaseModel, metaclass=abc.ABCMeta):
    """A helper class for picking a target from a list."""

    @abc.abstractmethod
    async def __call__(self) -> tuple[str, SkyCoord]: ...


__all__ = ["Picker"]
