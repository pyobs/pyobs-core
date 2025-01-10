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
        self,
        fibre_position,
        inner_radius,
        outer_radius,
        max_relative_sigma=0.1,
        relative_shift=None,
        section_angular_width=36,
        section_angular_shift=18,
        **kwargs: Any
    ):
        """Init an image processor that adds the calculated offset.

        Args:
            fibre_position: pixel position of the fibre centre
            inner_radius: inner pixel radius of the considered ring
            outer_radius: outer pixel radius of the considered ring
            max_relative_sigma: upper limit for fraction of standard deviation and median in order determine if ring is uniform
            relative_shift: fraction of inner radius, that will be used as pixel offset
            delta_angle: angle of the sections of the ring, that are used to find the offset direction
        """
        Offsets.__init__(self, **kwargs)

        self._fibre_position = fibre_position
        self._inner_radius = inner_radius
        self._outer_radius = outer_radius
        self._max_relative_sigma = max_relative_sigma
        self._relative_shift = relative_shift
        self._section_angular_width = section_angular_width
        self._section_angular_shift = section_angular_shift

    async def __call__(self, image: Image) -> Image:
        """Processes an image and sets x/y pixel offset to reference in offset attribute.

        Args:
            image: Image to process.

        Returns:
            Original image.

        Raises:
            ValueError: If offset could not be found.
        """
        image.data = image.data - np.mean(image.data.ravel())
        await self._apply_ring_mask(image)
        await self.plot_masked_image(image.data, self.ring)
        if await self._ring_is_uniform():
            print("Ring is uniform, No offset")
            pixel_offset = (0, 0)
        else:
            pixel_offset = await self._get_offset()
        print(pixel_offset)
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
        self.ring = np.where(ring == 0, np.nan, ring)

    async def plot_masked_image(self, full_image, masked_image, sigma_clim=5):
        vmin, vmax = (np.nanmean(full_image.ravel()) - sigma_clim * np.nanstd(full_image.ravel()),
                      np.nanmean(full_image.ravel()) + sigma_clim * np.nanstd(full_image.ravel()))
        full_image_plot = np.where(full_image == np.nan, 0, full_image)
        masked_image_plot = np.where(masked_image == np.nan, 0, masked_image)
        fig = plt.figure(frameon=False)
        im1 = plt.imshow(full_image_plot, cmap="gray", alpha=1)
        im1.set_clim(vmin, vmax)
        im2 = plt.imshow(masked_image_plot, cmap="viridis", alpha=0.7)
        im2.set_clim(vmin, vmax)
        plt.show()

    async def _ring_is_uniform(self):
        return np.nanstd(self.ring.data) < np.nanmedian(self.ring.data) * self._max_relative_sigma

    async def _get_brightest_point(self):
        index = np.nanargmax(self.ring)
        return np.unravel_index(index, self.ring.shape)

    async def _get_section_angles(self):
        return np.arange(0, 360, self._section_angular_shift)

    async def _apply_section_mask(self, min_angle, max_angle):
        ny, nx = self.ring.shape
        x, y = np.arange(0, nx), np.arange(0, ny)
        x_coordinates, y_coordinates = np.meshgrid(x, y)
        section_mask = ((min_angle < await self._get_angle_from_position(x_coordinates, y_coordinates)) &
                        (max_angle > await self._get_angle_from_position(x_coordinates, y_coordinates)))
        section = self.ring.copy()
        section *= section_mask
        section = np.where(section == 0, np.nan, section)
        return section

    async def _get_sections(self):
        section_list = []
        for section_start in await self._get_section_angles():
            section = await self._apply_section_mask(section_start, section_start + self._section_angular_width)
            section_list.append(section)
            #print(section_start, section_start + self._section_angular_width)
            #await self.plot_masked_image(self.ring, section)
        return section_list

    async def _get_brightest_section_index(self):
        section_mean_counts = [np.nanmean(section.ravel()) for section in await self._get_sections()]
        plt.figure()
        plt.plot(await self._get_section_angles() + + self._section_angular_width / 2, section_mean_counts)
        plt.show()
        self._brightest_section_index = np.argmax(section_mean_counts)
        await self.plot_masked_image(self.ring, (await self._get_sections())[self._brightest_section_index], sigma_clim=1)
        return self._brightest_section_index

    async def _get_brightest_section_angle(self):
        section_angles = await self._get_section_angles()
        return section_angles[await self._get_brightest_section_index()] + self._section_angular_width / 2

    async def _get_opposite_section_index(self, index_section):
        number_of_sections = len(await self._get_section_angles())
        if index_section < number_of_sections / 2:
            return int(index_section + number_of_sections / 2)
        else:
            return int(index_section - number_of_sections / 2)

    async def _get_opposite_section_counts_ratio(self, index_section):
        index_opposite_section = await self._get_opposite_section_index(index_section)
        section_list = await self._get_sections()
        return np.nanmean(section_list[index_section]) / np.nanmean(section_list[index_opposite_section])

    async def _get_angle_from_position(self, x_coordinate, y_coordinate):
        x_fibre, y_fibre = self._fibre_position
        delta_x, delta_y = x_coordinate - x_fibre, y_coordinate - y_fibre
        angle = np.arctan2(delta_y, delta_x) * 180 / np.pi + 90
        angle =  np.where(angle < 0, angle + 360, angle)
        return np.where(angle > 360, angle - 360, angle)

    async def _get_brightest_direction(self, method="brightest_section"):
        if method == "brightest_point":
            y_brightest_point, x_brightest_point = await self._get_brightest_point()
            print("Brightest Point at: ", y_brightest_point, x_brightest_point)
            return await self._get_angle_from_position(x_brightest_point, y_brightest_point)
        if method == "brightest_section":
            return await self._get_brightest_section_angle()

    async def _calculate_relative_shift(self):
        if self._relative_shift is None:
            #TODO find suitable weighting (equal sections -> no shift, unequal sections -> shift should approach 1 asymptotically)
            section_ratio = await self._get_opposite_section_counts_ratio(self._brightest_section_index)
            self._relative_shift = min(1, section_ratio-1)

    async def _get_offset(self):
        angle_direction = await self._get_brightest_direction()
        print("Brightest Angle:", angle_direction)
        await self._calculate_relative_shift()
        total_offset = self._relative_shift * self._inner_radius
        x_offset = total_offset * np.sin(angle_direction / 180 * np.pi)
        y_offset = total_offset * np.cos(angle_direction / 180 * np.pi)
        return x_offset, y_offset

__all__ = ["SpilledLightGuiding"]
