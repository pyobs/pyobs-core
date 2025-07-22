from typing import Any, cast
from typing_extensions import Self

from pyobs.object import get_object
from pyobs.utils.grids.filters import GridFilter
from pyobs.utils.grids.grid import Grid


class GridPipeline:
    """A pipeline for a grid and filters. Accepts a Grid as first element in the input list plus 0-N filters"""

    def __init__(self, steps: list[Grid | GridFilter | dict[str, Any]]):
        # variables
        self._grid_pipeline: Grid | GridFilter | None = None

        # we need one element
        if len(steps) == 0:
            return

        # create grid
        self._grid_pipeline = cast(Grid, get_object(steps[0], Grid))

        # create steps
        for step in steps[1:]:
            self._grid_pipeline = cast(GridFilter, get_object(step, GridFilter, grid=self._grid_pipeline))

    def __iter__(self) -> Self:
        return self

    def __next__(self) -> tuple[float, float]:
        """Returns the points of a new grid."""
        if self._grid_pipeline is None:
            raise StopIteration
        return next(self._grid_pipeline)

    def __len__(self) -> int:
        return len(self._grid_pipeline) if self._grid_pipeline is not None else 0

    def append_last(self) -> None:
        if self._grid_pipeline is not None:
            self._grid_pipeline.append_last()
