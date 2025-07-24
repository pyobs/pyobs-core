import abc
from typing import List, Tuple, Any

import numpy as np

from .grid import Grid


class SphericalGrid(Grid, metaclass=abc.ABCMeta):
    """Abstract base class for spherical grids, coordinates are longitudes and latitudes."""

    pass


class RegularSphericalGrid(SphericalGrid):
    def __init__(self, n_lon: int, n_lat: int, **kwargs: Any):
        """Creates a grid with points at the intersections of longitudinal and latitudinal lines.

        Params:
            n_lon: Number of longitudinal points.
            n_lat: Number of latitudinal points.

        Returns:
            Lat/lon grid.
        """
        points = []
        for lon in np.linspace(0.0, 360.0 - 360.0 / n_lon, n_lon):
            for lat in np.linspace(-90.0, 90.0, n_lat):
                points.append((float(lon), float(lat)))
        SphericalGrid.__init__(self, points=points, **kwargs)


class GraticuleSphericalGrid(SphericalGrid):
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
        points: List[Tuple[float, float]] = []

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

        SphericalGrid.__init__(self, points=points, **kwargs)
