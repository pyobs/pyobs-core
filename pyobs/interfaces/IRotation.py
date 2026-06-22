from abc import ABCMeta, abstractmethod
from typing import Annotated, Any

from ..utils.enums import Unit
from .IMotion import IMotion


class IRotation(IMotion, metaclass=ABCMeta):
    """The module controls a device that can rotate."""

    __module__ = "pyobs.interfaces"

    @abstractmethod
    async def set_rotation(self, angle: Annotated[float, Unit.DEGREES], **kwargs: Any) -> None:
        """Sets the rotation angle to the given value in degrees."""
        ...

    @abstractmethod
    async def get_rotation(self) -> Annotated[float, Unit.DEGREES]:
        """Returns the current rotation angle."""
        ...


__all__ = ["IRotation"]
