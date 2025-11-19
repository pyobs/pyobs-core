import abc
from typing import Any
from astropy.coordinates import SkyCoord

from .gridnode import GridNode


class Grid(GridNode, metaclass=abc.ABCMeta):
    """Abstract base class for grids."""

    def __init__(self, points: list[tuple[float, float] | SkyCoord], **kwargs: Any):
        GridNode.__init__(self, **kwargs)
        self._points = points

    def _get_next(self) -> tuple[float, float] | SkyCoord:
        """Returns the points of a new grid."""
        if len(self._points) == 0:
            raise StopIteration
        return self._points.pop(0)

    def __len__(self) -> int:
        return len(self._points)

    def append_last(self) -> None:
        if self._last is not None:
            self._points.append(self._last)

    def log_last(self) -> None:
        self.log(self._last)
