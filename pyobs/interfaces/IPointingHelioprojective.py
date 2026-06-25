from __future__ import annotations

from abc import ABCMeta, abstractmethod
from dataclasses import dataclass, field
from typing import Annotated, Any

from ..utils.enums import Unit
from ..utils.time import Time
from .interface import Interface


class IPointingHelioprojective(Interface, metaclass=ABCMeta):
    """The module can move to Mu/Psi coordinates, usually combined with :class:`~pyobs.interfaces.ITelescope`."""

    __module__ = "pyobs.interfaces"

    @dataclass
    class State:
        theta_x: Annotated[float, Unit.DEGREES]
        theta_y: Annotated[float, Unit.DEGREES]
        time: Time = field(default_factory=Time.now)

    @abstractmethod
    async def move_helioprojective(
        self, theta_x: Annotated[float, Unit.DEGREES], theta_y: Annotated[float, Unit.DEGREES], **kwargs: Any
    ) -> None:
        """Moves on given coordinates.

        Args:
            theta_x: The theta_x coordinate.
            theta_y: The theta_y coordinate.

        Raises:
            MoveError: If device could not be moved.
        """
        ...


__all__ = ["IPointingHelioprojective"]
