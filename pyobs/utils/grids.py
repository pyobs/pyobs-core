from typing import List, Tuple
import matplotlib.pyplot as plt
import numpy as np


class SphericalGrid:
    """Methods for creating points on a spherical lon/lat grid (e.g. Az/Alt or RA/Dec."""

    @staticmethod
    def lonlat(n_lon: int, n_lat: int) -> List[Tuple[float, float]]:
        """Creates a grid with points at the intersections of longitudinal and latitudinal lines.

        Params:
            n_lon: Number of longitudinal points.
            n_lat: Number of latitudinal points.

        Returns:
            Lat/lon grid.
        """
        grid = []
        for lon in np.linspace(0, 360. - 360. / n_lon, n_lon):
            for lat in np.linspace(-90, 90, n_lat):
                grid.append((lon, lat))
        return grid

    @staticmethod
    def equidistributed(n: int) -> List[Tuple[float, float]]:
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
        grid = []

        # conversion radians -> degrees
        r2d = 180. / np.pi

        # loop latitudinal
        for m in range(0, m_phi):
            lat = np.pi * (m + 0.5) / m_phi
            m_varphi = round(2 * np.pi * np.sin(lat) / d_varphi)

            # loop longitudinal
            for n in range(0, m_varphi):
                lon = 2 * np.pi * n / m_varphi

                # append to grid
                grid.append((lon * r2d, lat * r2d - 90.))

        # finished
        return grid

    @staticmethod
    def convert_to_cartesian(grid: List[Tuple[float, float]], radius: float = 1.) -> List[Tuple[float, float, float]]:
        """Convert a grid to cartesian coordinates.

        Params:
            grid: Grid to convert.
            radius: Radius of sphere.

        Returns:
            List of x/y/z points.
        """

        # conversion radians -> degrees
        r2d = 180. / np.pi

        # calculate x/y/z coordinates, assuming r=1
        return [(radius * np.cos(lat / r2d) * np.cos(lon / r2d),
                 radius * np.cos(lat / r2d) * np.sin(lon / r2d),
                 radius * np.sin(lat / r2d)) for lon, lat in grid]

    @staticmethod
    def plot_cartesian(grid: List[Tuple[float, float, float]]) -> None:
        """Plot cartesian grid.

        Params:
            grid: Cartesian grid to plot.
        """
        fig = plt.figure()
        ax = fig.add_subplot(projection='3d')
        x, y, z = list(zip(*grid))
        ax.scatter(x, z, y)
