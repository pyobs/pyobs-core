from typing import Any

from pyobs.object import Object
from .gridnode import GridNode


class GridPipeline(GridNode):
    """A pipeline for a grid and filters. Accepts a Grid as first element in the input list plus 0-N filters"""

    def __init__(self, steps: list[GridNode | dict[str, Any]], **kwargs: Any):
        Object.__init__(self, **kwargs)

        # variables
        self._grid_pipeline: GridNode | None = None

        # we need one element
        if len(steps) == 0:
            return

        # create grid
        self._grid_pipeline = self.get_object(steps[0], GridNode)

        # create steps
        for step in steps[1:]:
            self._grid_pipeline = self.get_object(step, GridNode, grid=self._grid_pipeline)

    def _get_next(self) -> tuple[float, float]:
        """Returns the points of a new grid."""
        if self._grid_pipeline is None:
            raise StopIteration
        return next(self._grid_pipeline)

    def __len__(self) -> int:
        return len(self._grid_pipeline) if self._grid_pipeline is not None else 0

    def append_last(self) -> None:
        if self._grid_pipeline is not None:
            self._grid_pipeline.append_last()

    def log_last(self) -> None:
        if self._grid_pipeline is not None:
            self._grid_pipeline.log_last()
