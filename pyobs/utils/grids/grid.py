import abc
from typing import Any
from astropy.coordinates import SkyCoord
import numpy as np

from .gridnode import GridNode


class Grid(GridNode, metaclass=abc.ABCMeta):
    """Abstract base class for grids backed by a mutable list of points.

    This class consumes a list of points (tuples or SkyCoord) in FIFO order.
    It implements iteration, length, and appending the last element back to
    the list, enabling simple queue-like behavior.
    """

    def __init__(self, points: list[tuple[float, float] | SkyCoord], **kwargs: Any):
        """Initialize a Grid with a list of points.

        Args:
            points: Initial list of points to yield. Each element must be either
                a (x, y) tuple in degrees or a SkyCoord.
            **kwargs: Additional keyword arguments forwarded to GridNode.__init__().
        """
        GridNode.__init__(self, **kwargs)
        self._points = points

    def _get_next(self) -> tuple[float, float] | SkyCoord:
        """Return the next point and remove it from the internal list.

        Returns:
            The next point as (x, y) in degrees or a SkyCoord.

        Raises:
            StopIteration: If no points remain.
        """
        if len(self._points) == 0:
            raise StopIteration
        return self._points.pop(0)

    def __len__(self) -> int:
        """Return the number of remaining points.

        Returns:
            Number of points still available in the grid.
        """
        return len(self._points)

    def append_last(self) -> None:
        """Append the last yielded point to the end of the grid."""
        if self._last is not None:
            self._points.append(self._last)

    def log_last(self) -> None:
        """Log the last yielded point, if logging is enabled."""
        self.log(self._last)


class RegularSphericalGrid(Grid):
    """Grid over a sphere using regular longitude/latitude sampling.

    Produces points at intersections of equally spaced longitudes and latitudes:
      - Longitudes: [0, 360) with step 360 / n_lon (360 is excluded)
      - Latitudes: Inclusive linspace from -90 to +90 with n_lat values

    The resulting points are (lon_deg, lat_deg) tuples in degrees.
    """

    def __init__(self, n_lon: int, n_lat: int, **kwargs: Any):
        """Create a regular lon/lat grid.

        Args:
            n_lon: Number of longitudinal divisions. Must be > 0.
            n_lat: Number of latitudinal points. Must be >= 2 to include both poles.
            **kwargs: Additional keyword arguments forwarded to Grid.__init__().

        Raises:
            ValueError: If n_lon <= 0 or n_lat <= 0.

        Notes:
            Longitudes are in [0, 360) and latitudes are in [-90, 90].
        """
        points: list[tuple[float, float]] = []
        for lon in np.linspace(0.0, 360.0 - 360.0 / n_lon, n_lon):
            for lat in np.linspace(-90.0, 90.0, n_lat):
                points.append((float(lon), float(lat)))
        Grid.__init__(self, points=points, **kwargs)


class GraticuleSphericalGrid(Grid):
    """Grid with approximately equidistributed points on a sphere.

    Uses a graticule-like construction for near-uniform sampling over the sphere
    following the approach described by Deserno (2004):
      https://www.cmu.edu/biolphys/deserno/pdf/sphere_equi.pdf

    Produces points as (lon_deg, lat_deg) tuples in degrees.
    """

    def __init__(self, n: int, **kwargs: Any):
        """Create an approximately equidistributed spherical grid.

        Args:
            n: Target number of points on the sphere. Must be > 0.
            **kwargs: Additional keyword arguments forwarded to Grid.__init__().

        Raises:
            ValueError: If n <= 0.

        Notes:
            The actual number of generated points follows the construction and
            may be close to, but not necessarily exactly, n.
        """
        # init
        a = 4 * np.pi / n
        d = np.sqrt(a)
        m_phi = round(np.pi / d)
        d_phi = np.pi / m_phi
        d_varphi = a / d_phi
        points: list[tuple[float, float]] = []

        # conversion radians -> degrees
        r2d = 180.0 / np.pi

        # loop latitudinal
        for m in range(0, m_phi):
            lat = np.pi * (m + 0.5) / m_phi
            m_varphi = round(2 * np.pi * np.sin(lat) / d_varphi)

            # loop longitudinal
            for n in range(0, m_varphi):
                lon = 2 * np.pi * n / m_varphi

                # append to grid
                points.append((lon * r2d, lat * r2d - 90.0))

        Grid.__init__(self, points=points, **kwargs)


__all__ = ["RegularSphericalGrid", "GraticuleSphericalGrid"]
