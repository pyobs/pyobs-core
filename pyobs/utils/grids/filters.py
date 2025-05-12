from typing import Tuple, Union, Optional

from .grid import Grid


class GridFilter:
    def __init__(self, grid: Union[Grid, "GridFilter"], **kwargs):
        self._grid = grid

    def __iter__(self):
        return self

    def __next__(self) -> Tuple[float, float]:
        """Returns the points of a new grid."""
        return next(self._grid)

    def __len__(self) -> int:
        return len(self._grid)

    def append_last(self):
        self._grid.append_last()


class GridFilterValue(GridFilter):
    def __init__(
        self,
        x_gt: Optional[int] = None,
        x_gte: Optional[int] = None,
        x_lt: Optional[int] = None,
        x_lte: Optional[int] = None,
        y_gt: Optional[int] = None,
        y_gte: Optional[int] = None,
        y_lt: Optional[int] = None,
        y_lte: Optional[int] = None,
        **kwargs,
    ):
        GridFilter.__init__(self, **kwargs)
        self._x_gt = x_gt
        self._x_gte = x_gte
        self._x_lt = x_lt
        self._x_lte = x_lte
        self._y_gt = y_gt
        self._y_gte = y_gte
        self._y_lt = y_lt
        self._y_lte = y_lte

    def __next__(self) -> Tuple[float, float]:
        """Returns the points of a new grid."""

        while True:
            point = next(self._grid)
            if self._x_gt is not None and point[0] <= self._x_gt:
                continue
            if self._x_gte is not None and point[0] < self._x_gte:
                continue
            if self._x_lt is not None and point[0] >= self._x_lt:
                continue
            if self._x_lte is not None and point[0] > self._x_lte:
                continue
            if self._y_gt is not None and point[0] <= self._y_gt:
                continue
            if self._y_gte is not None and point[0] < self._y_gte:
                continue
            if self._y_lt is not None and point[0] >= self._y_lt:
                continue
            if self._y_lte is not None and point[0] > self._y_lte:
                continue
            return point
