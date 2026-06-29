from __future__ import annotations

from abc import ABCMeta, abstractmethod
from dataclasses import dataclass, field
from typing import Annotated, Any

from ..utils.enums import Unit
from ..utils.time import Time
from .IMotion import IMotion


@dataclass
class RotationState:
    rotation: Annotated[float, Unit.DEGREES]
    time: Time = field(default_factory=Time.now)


class IRotation(IMotion, metaclass=ABCMeta):
    """The module controls a device that can rotate."""

    __module__ = "pyobs.interfaces"

    state = RotationState

    @abstractmethod
    async def set_rotation(self, angle: Annotated[float, Unit.DEGREES], **kwargs: Any) -> None:
        """Sets the rotation angle to the given value in degrees."""
        ...


__all__ = ["IRotation", "RotationState"]
