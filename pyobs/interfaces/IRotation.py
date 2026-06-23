from abc import ABCMeta, abstractmethod
from dataclasses import dataclass, field
from typing import Annotated, Any

from ..utils.enums import Unit
from ..utils.time import Time
from .IMotion import IMotion


class IRotation(IMotion, metaclass=ABCMeta):
    """The module controls a device that can rotate."""

    __module__ = "pyobs.interfaces"

    @dataclass
    class State:
        rotation: Annotated[float, Unit.DEGREES]
        time: Time = field(default_factory=Time.now)

    @abstractmethod
    async def set_rotation(self, angle: Annotated[float, Unit.DEGREES], **kwargs: Any) -> None:
        """Sets the rotation angle to the given value in degrees."""
        ...

    @abstractmethod
    async def get_rotation(self) -> Annotated[float, Unit.DEGREES]:
        """Returns the current rotation angle."""
        ...


__all__ = ["IRotation"]
