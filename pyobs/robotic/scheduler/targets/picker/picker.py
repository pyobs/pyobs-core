import abc
from typing import TYPE_CHECKING

from pyobs.utils.serialization import PolymorphicBaseModel
from pyobs.utils.time import Time

if TYPE_CHECKING:
    from pyobs.robotic.scheduler.targets import Target, SiderealTarget


class Picker(PolymorphicBaseModel, metaclass=abc.ABCMeta):
    """A helper class for picking a target from a list."""

    @abc.abstractmethod
    async def __call__(self, time: Time) -> Target: ...


__all__ = ["Picker"]
