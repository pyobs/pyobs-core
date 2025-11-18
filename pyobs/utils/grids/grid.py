import abc
from typing import Any

from astropy.coordinates import SkyCoord

from pyobs.object import Object


class Grid(Object, metaclass=abc.ABCMeta):
    """Abstract base class for grids."""

    def __init__(self, points: list[tuple[float, float] | SkyCoord], **kwargs: Any):
        Object.__init__(self, **kwargs)
        self._points = points
        self._last: tuple[float, float] | SkyCoord | None = None

    def __iter__(self) -> "Grid":
        return self

    def __next__(self) -> tuple[float, float]:
        """Returns the points of a new grid."""
        if len(self._points) > 0:
            self._last = self._points.pop(0)
            return self._last
        else:
            raise StopIteration

    def __len__(self) -> int:
        return len(self._points)

    def append_last(self) -> None:
        if self._last is not None:
            self._points.append(self._last)
