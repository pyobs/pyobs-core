from __future__ import annotations

from abc import ABCMeta, abstractmethod
from dataclasses import dataclass, field
from typing import Annotated, Any

from ..utils.enums import Unit
from ..utils.time import Time
from .interface import Interface


@dataclass
class HelioprojectiveState:
    theta_x: Annotated[float, Unit.DEGREES]
    theta_y: Annotated[float, Unit.DEGREES]
    time: Time = field(default_factory=Time.now)


class IPointingHelioprojective(Interface, metaclass=ABCMeta):
    """The module can move to Mu/Psi coordinates, usually combined with :class:`~pyobs.interfaces.ITelescope`."""

    __module__ = "pyobs.interfaces"

    state = HelioprojectiveState

    @abstractmethod
    async def move_helioprojective(
        self, theta_x: Annotated[float, Unit.DEGREES], theta_y: Annotated[float, Unit.DEGREES], **kwargs: Any
    ) -> None:
        """Moves on given coordinates.

        Args:
            theta_x: The theta_x coordinate.
            theta_y: The theta_y coordinate.

        Raises:
            MoveError: If device could not be moved. Also propagates whatever the underlying
                RA/Dec move raises (e.g. MissingObserverError, AltitudeLimitError), since this is
                typically implemented as converting to RA/Dec and then moving there.
        """
        ...


__all__ = ["IPointingHelioprojective", "HelioprojectiveState"]
