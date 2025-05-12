import abc
from typing import List, Tuple, Optional


class Grid(metaclass=abc.ABCMeta):
    """Abstract base class for grids."""

    def __init__(self, **kwargs):
        self._points: List[Tuple[float, float]] = []
        self._last: Optional[Tuple[float, float]] = None

    def __iter__(self):
        return self

    def __next__(self) -> Tuple[float, float]:
        """Returns the points of a new grid."""
        if len(self._points) > 0:
            self._last = self._points.pop(0)
            yield self._last
        else:
            raise StopIteration

    def __len__(self) -> int:
        return len(self._points)

    def append_last(self):
        self._points.append(self._last)
