import logging
from typing import Tuple, Any, Optional

import matplotlib.colors
import matplotlib.pyplot as plt
import numpy as np
from astropy.coordinates import Angle, AltAz, EarthLocation
from astropy.table import Table, Row
from astropy.wcs import WCS
from pandas._typing import npt
from pyobs.utils.time import Time
import astropy.units as u

from pyobs.images import Image
from pyobs.images.meta import PixelOffsets, OnSkyDistance, AltAzOffsets
from .offsets import Offsets

log = logging.getLogger(__name__)


class SpilledLightGuiding(Offsets):
    """Calculates offsets from the light in a ring around a fibre."""

    __module__ = "pyobs.images.processors.offsets"

    def __init__(
        self, fibre_position, inner_radius, outer_radius, max_relative_sigma=0.1, relative_shift=0.5, **kwargs: Any
    ):
        """Init an image processor that adds the calculated offset.

        Args:
            fibre_position: pixel position of the fibre centre
            inner_radius: inner pixel radius of the considered ring
            outer_radius: outer pixel radius of the considered ring
            max_relative_sigma: upper limit for fraction of standard deviation and median in order determine if ring is uniform
            relative_shift: fraction of inner radius, that will be used as pixel offset
        """
        Offsets.__init__(self, **kwargs)

        self._fibre_position = fibre_position
        self._inner_radius = inner_radius
        self._outer_radius = outer_radius
        self._max_relative_sigma = max_relative_sigma
        self._relative_shift = relative_shift

    async def __call__(self, image: Image) -> Image:
        """Processes an image and sets x/y pixel offset to reference in offset attribute.

        Args:
            image: Image to process.

        Returns:
            Original image.

        Raises:
            ValueError: If offset could not be found.
        """

        ring = await self._apply_ring_mask(image)
        if await self._is_uniform(ring):
            print(np.nanstd(ring), np.nanmedian(ring), np.nanmedian(ring) * self._max_relative_sigma)
            pixel_offset = (0, 0)
        else:
            pixel_offset = await self._get_offset(ring)
        plt.figure()
        plt.imshow(image.data, cmap="gray", norm=matplotlib.colors.LogNorm())
        plt.imshow(ring)
        plt.show()
        image.set_meta(PixelOffsets(*pixel_offset))
        return image

    async def _apply_ring_mask(self, image):
        ny, nx = image.data.shape
        x, y = np.arange(0, nx), np.arange(0, ny)
        x_coordinates, y_coordinates = np.meshgrid(x, y)
        fibre_x, fibre_y = self._fibre_position
        inner_mask = (x_coordinates - fibre_x) ** 2 + (y_coordinates - fibre_y) ** 2 >= self._inner_radius**2
        outer_mask = (x_coordinates - fibre_x) ** 2 + (y_coordinates - fibre_y) ** 2 <= self._outer_radius**2
        ring = image.data.copy()
        ring *= inner_mask * outer_mask
        ring = np.where(ring == 0, np.nan, ring)
        return ring

    async def _is_uniform(self, ring):
        return np.nanstd(ring.data) < np.nanmedian(ring.data) * self._max_relative_sigma

    async def _get_brightest_point(self, ring):
        index = np.nanargmax(ring)
        return np.unravel_index(index, ring.shape)

    async def _get_brightest_direction(self, ring):
        x_fibre, y_fibre = self._fibre_position
        y_brightest_point, x_brightest_point = await self._get_brightest_point(ring)
        print(y_brightest_point, x_brightest_point)
        delta_x, delta_y = x_brightest_point - x_fibre, y_brightest_point - y_fibre
        return np.arctan(delta_x / delta_y)

    async def _get_offset(self, ring):
        angle_direction = await self._get_brightest_direction(ring)
        print(angle_direction * 180 / np.pi)
        total_offset = self._relative_shift * self._inner_radius
        x_offset = total_offset * np.sin(angle_direction)
        y_offset = total_offset * np.cos(angle_direction)
        return x_offset, y_offset


__all__ = ["SpilledLightGuiding"]
