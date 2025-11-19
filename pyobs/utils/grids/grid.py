import abc
from typing import Any
from astropy.coordinates import SkyCoord
import numpy as np

from .gridnode import GridNode


class Grid(GridNode, metaclass=abc.ABCMeta):
    """Abstract base class for grids."""

    def __init__(self, points: list[tuple[float, float] | SkyCoord], **kwargs: Any):
        GridNode.__init__(self, **kwargs)
        self._points = points

    def _get_next(self) -> tuple[float, float] | SkyCoord:
        """Returns the points of a new grid."""
        if len(self._points) == 0:
            raise StopIteration
        return self._points.pop(0)

    def __len__(self) -> int:
        return len(self._points)

    def append_last(self) -> None:
        if self._last is not None:
            self._points.append(self._last)

    def log_last(self) -> None:
        self.log(self._last)


class RegularSphericalGrid(Grid):
    def __init__(self, n_lon: int, n_lat: int, **kwargs: Any):
        """Creates a grid with points at the intersections of longitudinal and latitudinal lines.

        Params:
            n_lon: Number of longitudinal points.
            n_lat: Number of latitudinal points.

        Returns:
            Lat/lon grid.
        """
        points: list[tuple[float, float]] = []
        for lon in np.linspace(0.0, 360.0 - 360.0 / n_lon, n_lon):
            for lat in np.linspace(-90.0, 90.0, n_lat):
                points.append((float(lon), float(lat)))
        Grid.__init__(self, points=points, **kwargs)


class GraticuleSphericalGrid(Grid):
    def __init__(self, n: int, **kwargs: Any):
        """Creates equidistributed points on the surface of a sphere

        See https://www.cmu.edu/biolphys/deserno/pdf/sphere_equi.pdf

        Params:
            n:  Number of points

        Returns:
            Lat/lon grid.
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
