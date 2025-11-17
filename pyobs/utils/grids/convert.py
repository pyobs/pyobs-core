from astropy.coordinates import SkyCoord
import astropy.units as u

from .filters import GridFilter
from .grid import Grid


class ConvertGridToSkyCoord(GridFilter):
    def __init__(self, grid: Grid | GridFilter, frame: str = "altaz", **kwargs: object):
        GridFilter.__init__(self, grid, **kwargs)
        self._frame = frame

    def __next__(self) -> tuple[float, float] | SkyCoord:
        """Returns the points of a new grid."""

        for point in self._grid:
            # not a tuple of two floats?
            if not isinstance(point, tuple) or len(point) != 2:
                raise TypeError(f"Expected a tuple with 2 elements, got {type(point)}")

            # to SkyCoord
            return SkyCoord(point[0] * u.deg, point[1] * u.deg, frame=self._frame)

        raise StopIteration()


__all__ = ["ConvertGridToSkyCoord"]
