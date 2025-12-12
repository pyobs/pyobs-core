from typing import Any

from pyobs.object import Object
from .gridnode import GridNode


class GridPipeline(GridNode):
    """A pipeline that composes a grid and a sequence of filters.

    The pipeline expects a list of steps where the first element constructs a
    GridNode (e.g., a Grid) and subsequent elements construct GridNode filters
    that wrap the previous step. Each step can be either:
      - An instance of GridNode, or
      - A dict specification understood by Object.get_object() to construct a GridNode.

    The pipeline itself is a GridNode that delegates iteration and other methods
    to the constructed chain.
    """

    def __init__(self, steps: list[GridNode | dict[str, Any]], **kwargs: Any):
        """Build a GridPipeline from a list of steps.

        Args:
            steps: A non-empty list where steps[0] yields a GridNode, and subsequent
                elements are GridNode filter specifications. Dict entries are passed
                to get_object() for construction.
            **kwargs: Additional keyword arguments forwarded to Object.__init__().

        Notes:
            If steps is empty, the pipeline is constructed in an "empty" state and
            iteration will immediately raise StopIteration.
        """
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
        """Return the next point from the pipeline.

        Returns:
            The next point produced by the final stage in the pipeline.

        Raises:
            StopIteration: If the pipeline is empty or exhausted.
        """
        if self._grid_pipeline is None:
            raise StopIteration
        return next(self._grid_pipeline)

    def __len__(self) -> int:
        """Return the number of points remaining in the pipeline.

        Returns:
            The length reported by the final stage, or 0 if empty.
        """
        return len(self._grid_pipeline) if self._grid_pipeline is not None else 0

    def append_last(self) -> None:
        """Append the last yielded point back to the pipeline's final stage."""
        if self._grid_pipeline is not None:
            self._grid_pipeline.append_last()

    def log_last(self) -> None:
        """Log the last yielded point via the pipeline's final stage."""
        if self._grid_pipeline is not None:
            self._grid_pipeline.log_last()
