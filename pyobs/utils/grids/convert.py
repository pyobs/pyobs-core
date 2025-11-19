from astropy.coordinates import SkyCoord
import astropy.units as u
import logging

from .filters import GridFilter
from .grid import Grid
from ..time import Time

log = logging.getLogger(__name__)


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


__all__ = ["ConvertGridToSkyCoord", "ConvertGridFrame"]
