from __future__ import annotations
import abc
import random
from typing import Any
from astropy.coordinates import SkyCoord
import astropy.units as u
from astropy.time import Time

from .gridnode import GridNode
from .grid import Grid


class GridFilter(GridNode, metaclass=abc.ABCMeta):
    def __init__(self, grid: GridNode, **kwargs: Any):
        GridNode.__init__(self, **kwargs)
        self._grid = grid

    def _get_next(self) -> tuple[float, float] | SkyCoord:
        """Returns the points of a new grid."""
        return next(self._grid)

    def __len__(self) -> int:
        return len(self._grid)

    def append_last(self) -> None:
        self._grid.append_last()

    def log_last(self) -> None:
        self._grid.log_last()
        self.log(self._last)


class GridFilterValue(GridFilter):
    def __init__(
        self,
        grid: Grid | GridFilter,
        x_gt: int | None = None,
        x_gte: int | None = None,
        x_lt: int | None = None,
        x_lte: int | None = None,
        y_gt: int | None = None,
        y_gte: int | None = None,
        y_lt: int | None = None,
        y_lte: int | None = None,
        **kwargs: object,
    ):
        GridFilter.__init__(self, grid, **kwargs)
        self._x_gt = x_gt
        self._x_gte = x_gte
        self._x_lt = x_lt
        self._x_lte = x_lte
        self._y_gt = y_gt
        self._y_gte = y_gte
        self._y_lt = y_lt
        self._y_lte = y_lte

    def _get_next(self) -> tuple[float, float] | SkyCoord:
        """Returns the points of a new grid."""

        while True:
            # what do we have?
            point = next(self._grid)
            if isinstance(point, tuple):
                x, y = point[0], point[1]
            elif isinstance(point, SkyCoord) and hasattr(point, "ra") and hasattr(point, "dec"):
                x, y = point.ra.degree, point.dec.degree
            elif isinstance(point, SkyCoord) and hasattr(point, "az") and hasattr(point, "alt"):
                x, y = point.az.degree, point.alt.degree
            else:
                raise TypeError("Unknown point type.")

            if self._x_gt is not None and x <= self._x_gt:
                continue
            if self._x_gte is not None and x < self._x_gte:
                continue
            if self._x_lt is not None and x >= self._x_lt:
                continue
            if self._x_lte is not None and x > self._x_lte:
                continue
            if self._y_gt is not None and y <= self._y_gt:
                continue
            if self._y_gte is not None and y < self._y_gte:
                continue
            if self._y_lt is not None and y >= self._y_lt:
                continue
            if self._y_lte is not None and y > self._y_lte:
                continue

            return point


class ConvertGridToSkyCoord(GridFilter):
    def __init__(self, grid: Grid | GridFilter, frame: str = "altaz", **kwargs: object):
        GridFilter.__init__(self, grid, **kwargs)
        self._frame = frame

    def _get_next(self) -> tuple[float, float] | SkyCoord:
        """Returns the points of a new grid."""

        point = next(self._grid)
        if not isinstance(point, tuple) or len(point) != 2:
            raise TypeError(f"Expected a tuple with 2 elements, got {type(point)}")

        # to SkyCoord
        return SkyCoord(
            point[0] * u.deg, point[1] * u.deg, frame=self._frame, location=self.location, obstime=Time.now()
        )


class ConvertGridFrame(GridFilter):
    def __init__(self, grid: Grid | GridFilter, frame: str = "altaz", **kwargs: object):
        GridFilter.__init__(self, grid, **kwargs)
        self._frame = frame

    def _get_next(self) -> tuple[float, float] | SkyCoord:
        """Returns the points of a new grid."""

        point = next(self._grid)
        if not isinstance(point, SkyCoord):
            raise TypeError("Expected a SkyCoord.")
        return point.transform_to(frame=self._frame)


class RandomizeGrid(GridFilter):
    def __init__(self, grid: Grid | GridFilter, iterations: int = 50, **kwargs: object):
        GridFilter.__init__(self, grid, **kwargs)
        self._iterations = iterations

    def _get_next(self) -> tuple[float, float] | SkyCoord:
        for i in range(random.randrange(self._iterations)):
            next(self._grid)
            self._grid.append_last()
        return next(self._grid)


__all__ = ["GridFilterValue", "ConvertGridFrame", "ConvertGridToSkyCoord", "RandomizeGrid"]
