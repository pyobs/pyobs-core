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
            NotSupportedError: If this device doesn't support body tracking.
            BodyResolutionError: If body name is not resolvable.
            MoveError: If telescope could not be moved. Also propagates whatever the underlying
                RA/Dec move raises (e.g. MissingObserverError, AltitudeLimitError), since tracking
                a body is implemented as resolving it and then moving there.
        """
        ...


__all__ = ["IPointingBody"]
