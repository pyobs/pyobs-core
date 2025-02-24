import logging
from typing import Any
import matplotlib.pyplot as plt
import numpy as np

from pyobs.images import Image
from pyobs.images.meta import PixelOffsets
from .offsets import Offsets

log = logging.getLogger(__name__)


def plot_masked_image(full_image, masked_image, sigma_clim=3):
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


class Ring:
    def __init__(
        self,
        full_image,
        fibre_position,
        inner_radius,
        outer_radius,
        max_relative_sigma=0.1,
        section_angular_width=36,
        section_angular_shift=18,
        **kwargs: Any
    ):
        self._full_image = full_image
        self._fibre_position = fibre_position
        self._inner_radius = inner_radius
        self._outer_radius = outer_radius
        self._max_relative_sigma = max_relative_sigma
        self._section_angular_width = section_angular_width
        self._section_angular_shift = section_angular_shift
        self._apply_ring_mask()
        self._load_sections()
        self._calculate_brightest_section_index()

    def _apply_ring_mask(self):
        ny, nx = self._full_image.data.shape
        x, y = np.arange(0, nx), np.arange(0, ny)
        x_coordinates, y_coordinates = np.meshgrid(x, y)
        fibre_x, fibre_y = self._fibre_position
        inner_mask = (x_coordinates - fibre_x) ** 2 + (y_coordinates - fibre_y) ** 2 >= self._inner_radius**2
        outer_mask = (x_coordinates - fibre_x) ** 2 + (y_coordinates - fibre_y) ** 2 <= self._outer_radius**2
        ring = self._full_image.data.copy()
        ring *= inner_mask * outer_mask
        self.data = np.where(ring == 0, np.nan, ring)
        plot_masked_image(self._full_image.data, self.data)

    def is_uniform(self):
        return np.nanstd(self.data) < np.nanmedian(self.data) * self._max_relative_sigma

    def get_angle_from_position(self, x_coordinate, y_coordinate):
        x_fibre, y_fibre = self._fibre_position
        delta_x, delta_y = x_coordinate - x_fibre, y_coordinate - y_fibre
        angle = np.arctan2(delta_y, delta_x) * 180 / np.pi + 90
        angle =  np.where(angle < 0, angle + 360, angle)
        return np.where(angle > 360, angle - 360, angle)

    def get_brightest_point(self):
        index = np.nanargmax(self.data)
        return np.unravel_index(index, self.data.shape)

    def _get_section_angles(self):
        return np.arange(0, 360, self._section_angular_shift)

    def _apply_section_mask(self, min_angle, max_angle):
        ny, nx = self.data.shape
        x, y = np.arange(0, nx), np.arange(0, ny)
        x_coordinates, y_coordinates = np.meshgrid(x, y)
        section_mask = ((min_angle < self.get_angle_from_position(x_coordinates, y_coordinates)) &
                        (max_angle > self.get_angle_from_position(x_coordinates, y_coordinates)))
        section = self.data.copy()
        section *= section_mask
        section = np.where(section == 0, np.nan, section)
        return section

    def _load_sections(self):
        section_list = []
        for section_start in self._get_section_angles():
            section = self._apply_section_mask(section_start, section_start + self._section_angular_width)
            section_list.append(section)
        self.sections = section_list

    def _calculate_brightest_section_index(self):
        section_mean_counts = [np.nanmean(section.ravel()) for section in self.sections]
        self.brightest_section_index = np.argmax(section_mean_counts)

    def get_brightest_section_angle(self):
        section_angles = self._get_section_angles()
        return section_angles[self.brightest_section_index] + self._section_angular_width / 2

    def _get_opposite_section_index(self, index_section):
        number_of_sections = len(self._get_section_angles())
        if index_section < number_of_sections / 2:
            return int(index_section + number_of_sections / 2)
        else:
            return int(index_section - number_of_sections / 2)

    def get_opposite_section_counts_ratio(self, index_section):
        index_opposite_section = self._get_opposite_section_index(index_section)
        return np.nanmean(self.sections[index_section]) / np.nanmean(self.sections[index_opposite_section])


class SpilledLightGuiding(Offsets):
    """Calculates offsets from the light in a ring around a fibre."""

    __module__ = "pyobs.images.processors.offsets"

    def __init__(
        self,
        fibre_position,
        inner_radius,
        outer_radius,
        max_relative_sigma=0.1,
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
        self.ring = Ring(image,
                         fibre_position=self._fibre_position,
                         inner_radius=self._inner_radius,
                         outer_radius=self._outer_radius,
                         max_relative_sigma=self._max_relative_sigma,
                         section_angular_width=self._section_angular_width,
                         section_angular_shift=self._section_angular_shift)
        if self.ring.is_uniform():
            print("Ring is uniform, No offset")
            pixel_offset = (0, 0)
        else:
            pixel_offset = await self._get_offset()
        print(pixel_offset)
        image.set_meta(PixelOffsets(*pixel_offset))
        return image

    async def _calculate_relative_shift(self):
        section_ratio = self.ring.get_opposite_section_counts_ratio(self.ring.brightest_section_index)
        log.info("section ratio: ", section_ratio)
        relative_shift = ((section_ratio - 3) / np.sqrt(1 + (section_ratio - 3)**2) + 1) / 2
        log.info("sigmoid: ", relative_shift)
        self._relative_shift = min(1, relative_shift)

    async def _get_brightest_direction(self, method="brightest_section"):
        if method == "brightest_point":
            y_brightest_point, x_brightest_point = self.ring.get_brightest_point()
            return self.ring.get_angle_from_position(x_brightest_point, y_brightest_point)
        if method == "brightest_section":
            return self.ring.get_brightest_section_angle()

    async def _get_offset(self):
        angle_direction = await self._get_brightest_direction()
        log.info("Brightest Angle:", angle_direction, " deg")
        await self._calculate_relative_shift()
        total_offset = self._relative_shift * self._inner_radius
        x_offset = total_offset * np.sin(angle_direction / 180 * np.pi)
        y_offset = -total_offset * np.cos(angle_direction / 180 * np.pi)
        return x_offset, y_offset


__all__ = ["SpilledLightGuiding"]
