from __future__ import annotations

from abc import ABCMeta, abstractmethod
from typing import Any

from .interface import Interface


class IPointingBody(Interface, metaclass=ABCMeta):
    """Points at and tracks a named solar-system body."""

    __module__ = "pyobs.interfaces"

    @abstractmethod
    async def track_body(self, body: str, **kwargs: Any) -> None:
        """Starts tracking a named solar-system body.

        Args:
            body: Name resolvable to an ephemeris (e.g. 'moon', 'mars', 'jupiter', or an
                  asteroid/comet designation known to JPL Horizons).

        Raises:
            MoveError: If telescope could not be moved.
            ValueError: If body name is not resolvable.
        """
        ...


__all__ = ["IPointingBody"]
