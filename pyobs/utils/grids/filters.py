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
    """Abstract base class for grid filters that wrap another GridNode.

    A GridFilter delegates iteration and length to the wrapped grid, and can
    override _get_next() to transform or filter points. It also proxies
    append_last() and log_last() to the underlying grid, while optionally adding
    its own logging.
    """

    def __init__(self, grid: GridNode, **kwargs: Any):
        """Initialize a filter with an underlying grid.

        Args:
            grid: The upstream GridNode to read points from.
            **kwargs: Additional keyword arguments forwarded to GridNode.__init__().
        """
        GridNode.__init__(self, **kwargs)
        self._grid = grid

    def _get_next(self) -> tuple[float, float] | SkyCoord:
        """Fetch the next point from the underlying grid.

        Returns:
            The next point from the underlying grid.

        Raises:
            StopIteration: If the underlying grid is exhausted.
        """
        return next(self._grid)

    def __len__(self) -> int:
        """Return the number of points remaining in the underlying grid.

        Returns:
            Number of remaining points reported by the underlying grid.
        """
        return len(self._grid)

    def append_last(self) -> None:
        """Append the last yielded point back to the underlying grid."""
        self._grid.append_last()

    def log_last(self) -> None:
        """Log the last point via the underlying grid, then log locally if enabled."""
        self._grid.log_last()
        self.log(self._last)


class GridFilterValue(GridFilter):
    """Filter points by numeric constraints on x and y.

    Accepts points as:
      - (x, y) tuples (degrees), or
      - SkyCoord with RA/Dec (x=RA deg, y=Dec deg), or
      - SkyCoord with Alt/Az (x=Az deg, y=Alt deg).

    Each constraint is optional; only provided constraints are applied.
    Points not satisfying all constraints are skipped.
    """

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
        """Initialize the value-based filter.

        Args:
            grid: Upstream grid or filter.
            x_gt: Keep points with x > x_gt (degrees).
            x_gte: Keep points with x >= x_gte (degrees).
            x_lt: Keep points with x < x_lt (degrees).
            x_lte: Keep points with x <= x_lte (degrees).
            y_gt: Keep points with y > y_gt (degrees).
            y_gte: Keep points with y >= y_gte (degrees).
            y_lt: Keep points with y < y_lt (degrees).
            y_lte: Keep points with y <= y_lte (degrees).
            **kwargs: Additional keyword arguments forwarded to GridFilter.__init__().

        Notes:
            Constraints are combined conjunctively (logical AND). If multiple
            constraints on the same axis are provided, they are all applied.
        """
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
        """Return the next point that satisfies all constraints.

        Iterates underlying points until one matches all provided constraints,
        then returns it.

        Returns:
            A point as (x, y) in degrees or a SkyCoord that satisfies the constraints.

        Raises:
            StopIteration: If the underlying grid is exhausted before a match is found.
            TypeError: If a point of unknown type is encountered.
        """
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
    """Convert (x, y) degree tuples to SkyCoord objects.

    Wraps a tuple-producing grid and converts each point to a SkyCoord in the
    requested frame. The current time (Time.now()) is used as obstime. The
    'location' attribute is taken from this object (inherited from Object).
    """

    def __init__(self, grid: Grid | GridFilter, frame: str = "altaz", **kwargs: object):
        """Initialize the conversion filter.

        Args:
            grid: Upstream grid or filter that yields (x, y) tuples in degrees.
            frame: Target frame for the SkyCoord (e.g., 'altaz', 'icrs', 'galactic').
            **kwargs: Additional keyword arguments forwarded to GridFilter.__init__().

        Notes:
            Requires that 'self.location' be defined (e.g., an EarthLocation)
            for frames that need it (such as AltAz).
        """
        GridFilter.__init__(self, grid, **kwargs)
        self._frame = frame

    def _get_next(self) -> tuple[float, float] | SkyCoord:
        """Convert the next tuple to a SkyCoord.

        Expects a tuple (x_deg, y_deg) from the upstream grid and converts it
        to SkyCoord in the requested frame using degrees.

        Returns:
            A SkyCoord corresponding to the input tuple.

        Raises:
            TypeError: If the upstream point is not a 2-element tuple.
            StopIteration: If the upstream grid is exhausted.
        """
        point = next(self._grid)
        if not isinstance(point, tuple) or len(point) != 2:
            raise TypeError(f"Expected a tuple with 2 elements, got {type(point)}")

        # to SkyCoord
        return SkyCoord(
            point[0] * u.deg, point[1] * u.deg, frame=self._frame, location=self.location, obstime=Time.now()
        )


class ConvertGridFrame(GridFilter):
    """Transform SkyCoord points to a different frame."""

    def __init__(self, grid: Grid | GridFilter, frame: str = "altaz", **kwargs: object):
        """Initialize the frame conversion filter.

        Args:
            grid: Upstream grid or filter yielding SkyCoord objects.
            frame: Target frame name passed to SkyCoord.transform_to().
            **kwargs: Additional keyword arguments forwarded to GridFilter.__init__().

        Notes:
            The ability to transform depends on the source and target frames; some
            transformations require obstime/location or other frame attributes.
        """
        GridFilter.__init__(self, grid, **kwargs)
        self._frame = frame

    def _get_next(self) -> tuple[float, float] | SkyCoord:
        """Transform the next SkyCoord to the target frame.

        Returns:
            A SkyCoord transformed to the requested frame.

        Raises:
            TypeError: If the upstream point is not a SkyCoord.
            StopIteration: If the upstream grid is exhausted.
        """
        point = next(self._grid)
        if not isinstance(point, SkyCoord):
            raise TypeError("Expected a SkyCoord.")
        return point.transform_to(frame=self._frame)


class RandomizeGrid(GridFilter):
    """Randomize iteration order by rotating the underlying sequence.

    For each requested point, perform k random "rotations" by taking the next
    underlying point and appending it back (k chosen uniformly from [0, iterations)).
    Then yield the next point.

    This preserves multiset contents while randomizing access order somewhat.
    """

    def __init__(self, grid: Grid | GridFilter, iterations: int = 50, **kwargs: object):
        """Initialize the randomizer.

        Args:
            grid: Upstream grid or filter.
            iterations: Upper bound (exclusive) for the number of rotations per yield.
            **kwargs: Additional keyword arguments forwarded to GridFilter.__init__().

        Raises:
            ValueError: If iterations < 0.
        """
        GridFilter.__init__(self, grid, **kwargs)
        self._iterations = iterations

    def _get_next(self) -> tuple[float, float] | SkyCoord:
        """Yield a point after rotating the underlying grid a random number of times.

        Returns:
            A (possibly randomized) next point from the underlying grid.

        Raises:
            StopIteration: If the underlying grid is exhausted.
        """
        for i in range(random.randrange(self._iterations)):
            next(self._grid)
            self._grid.append_last()
        return next(self._grid)


__all__ = ["GridFilterValue", "ConvertGridFrame", "ConvertGridToSkyCoord", "RandomizeGrid"]
