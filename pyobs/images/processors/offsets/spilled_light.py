import logging
from typing import Any, cast, overload
import numpy as np
import numpy.typing as npt

from pyobs.images import Image
from pyobs.images.meta import PixelOffsets
from pyobs.interfaces import IMultiFiber
from .offsets import Offsets

log = logging.getLogger(__name__)


class Ring:
    def __init__(
        self,
        full_image_data: npt.NDArray[np.floating[Any]],
        fibre_position: tuple[float, float],
        inner_radius: float,
        outer_radius: float,
        max_relative_sigma: float = 0.1,
        section_angular_width: float = 36,
        section_angular_shift: float = 18,
        **kwargs: Any,
    ):
        self._full_image_data = full_image_data
        self._fibre_position = fibre_position
        self._inner_radius = inner_radius
        self._outer_radius = outer_radius
        self._max_relative_sigma = max_relative_sigma
        self._section_angular_width = section_angular_width
        self._section_angular_shift = section_angular_shift
        self._apply_ring_mask()
        self._load_sections()
        self.brightest_section_index = 0
        self._calculate_brightest_section_index()

    def _apply_ring_mask(self) -> None:
        ny, nx = self._full_image_data.shape
        x, y = np.arange(0, nx), np.arange(0, ny)
        x_coordinates, y_coordinates = np.meshgrid(x, y)
        fibre_x, fibre_y = self._fibre_position
        inner_mask = (x_coordinates - fibre_x) ** 2 + (y_coordinates - fibre_y) ** 2 >= self._inner_radius**2
        outer_mask = (x_coordinates - fibre_x) ** 2 + (y_coordinates - fibre_y) ** 2 <= self._outer_radius**2
        ring = self._full_image_data.copy()
        ring *= inner_mask * outer_mask
        self.data = np.where(ring == 0, np.nan, ring)

    def is_uniform(self) -> bool:
        return bool(np.nanstd(self.data) < float(np.nanmedian(self.data)) * self._max_relative_sigma)

    @overload
    def get_angle_from_position(self, x_coordinate: float, y_coordinate: float) -> float: ...

    @overload
    def get_angle_from_position(
        self, x_coordinate: npt.NDArray[np.floating[Any]], y_coordinate: npt.NDArray[np.floating[Any]]
    ) -> npt.NDArray[np.floating[Any]]: ...

    def get_angle_from_position(
        self, x_coordinate: float | npt.NDArray[np.floating[Any]], y_coordinate: float | npt.NDArray[np.floating[Any]]
    ) -> float | npt.NDArray[np.floating[Any]]:
        x_fibre, y_fibre = self._fibre_position
        delta_x, delta_y = x_coordinate - x_fibre, y_coordinate - y_fibre
        angle = np.arctan2(delta_y, delta_x) * 180 / np.pi + 90
        angle = np.where(angle < 0, angle + 360, angle)
        return np.where(angle > 360, angle - 360, angle)

    def get_brightest_point(self) -> tuple[int, int]:
        index_brightest_point = np.nanargmax(self.data)
        return cast(tuple[int, int], np.unravel_index(index_brightest_point, self.data.shape))

    def _get_section_angles(self) -> npt.NDArray[np.float32]:
        return np.arange(0, 360, self._section_angular_shift, dtype=float)

    def _apply_section_mask(self, min_angle: float, max_angle: float) -> npt.NDArray[np.floating[Any]]:
        ny, nx = self.data.shape
        x, y = np.arange(0, nx), np.arange(0, ny)
        x_coordinates, y_coordinates = np.meshgrid(x, y)
        section_mask = (min_angle < self.get_angle_from_position(x_coordinates, y_coordinates)) & (
            max_angle > self.get_angle_from_position(x_coordinates, y_coordinates)
        )
        section = self.data.copy()
        section *= section_mask
        section = np.where(section == 0, np.nan, section)
        return section

    def _load_sections(self) -> None:
        section_list = []
        for section_start in self._get_section_angles():
            section = self._apply_section_mask(float(section_start), float(section_start) + self._section_angular_width)
            section_list.append(section)
        self.sections = section_list

    def _calculate_brightest_section_index(self) -> None:
        section_mean_counts = [np.nanmean(section.ravel()) for section in self.sections]
        self.brightest_section_index = int(np.argmax(section_mean_counts))

    def get_brightest_section_angle(self) -> float:
        section_angles = self._get_section_angles()
        return float(section_angles[self.brightest_section_index] + self._section_angular_width / 2)

    def _get_opposite_section_index(self, index_section: int) -> int:
        number_of_sections = len(self._get_section_angles())
        if index_section < number_of_sections / 2:
            return int(index_section + number_of_sections / 2)
        else:
            return int(index_section - number_of_sections / 2)

    def get_opposite_section_normalized_counts_ratio(self, index_section: int) -> float:
        index_opposite_section = self._get_opposite_section_index(index_section)
        counts_section = np.nanmean(self.sections[index_section])
        counts_opposite_section = np.nanmean(self.sections[index_opposite_section])
        return float((counts_section - counts_opposite_section) / counts_section)


class SpilledLightGuiding(Offsets):
    """Calculates offsets from the light in a ring around a fibre."""

    __module__ = "pyobs.images.processors.offsets"

    def __init__(
        self,
        fibers: str,
        radius_ratio: float = 2,
        max_relative_sigma: float = 0.1,
        section_angular_width: float = 36,
        section_angular_shift: float = 18,
        **kwargs: Any,
    ):
        """Init an image processor that adds the calculated offset.

        Args:
            fibers: IMultiFiber module that contains information about the currently selected fiber
            radius_ratio: ratio between inner radius (radius of the fiber) and outer radius of the ring around the fiber
            max_relative_sigma: upper limit for fraction of standard deviation and median in order determine if ring is uniform
            relative_shift: fraction of inner radius, that will be used as pixel offset
            delta_angle: angle of the sections of the ring, that are used to find the offset direction
        """
        Offsets.__init__(self, **kwargs)

        self._fibers = fibers
        self._fibre_position: Any[tuple[float, float], None] = None
        self._inner_radius: Any[float, None] = None
        self._radius_ratio = radius_ratio
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
        await self._load_fibre_information()
        await self._correct_for_binning(binning=image.header["DET-BIN1"])
        image.data = image.data - np.mean(image.data.ravel())
        trimmed_image_data = await self._get_trimmed_image(image.data)
        log.info(
            f"Creating Ring at x={self._fibre_position[0]}, y={self._fibre_position[1]} with radius {self._inner_radius}."
        )
        await self._correct_fibre_position_for_trimming()
        self.ring = Ring(
            full_image_data=trimmed_image_data,
            fibre_position=self._fibre_position,
            inner_radius=self._inner_radius,
            outer_radius=self._inner_radius * self._radius_ratio,
            max_relative_sigma=self._max_relative_sigma,
            section_angular_width=self._section_angular_width,
            section_angular_shift=self._section_angular_shift,
        )
        if self.ring.is_uniform():
            log.info("Ring is uniform, no offset applied.")
            pixel_offset = (0.0, 0.0)
        else:
            pixel_offset = await self._get_offset()
        image.set_meta(PixelOffsets(*pixel_offset))
        return image

    async def _load_fibre_information(self) -> None:
        fibers = await self.comm.proxy(self._fibers, IMultiFiber)
        self._fibre_position = await fibers.get_pixel_position()
        self._inner_radius = await fibers.get_radius()

    async def _correct_for_binning(self, binning: int) -> None:
        self._fibre_position = (self._fibre_position[0] / binning, self._fibre_position[1] / binning)
        self._inner_radius /= binning

    async def _get_trimmed_image(self, image_data: npt.NDArray[np.floating[Any]]) -> npt.NDArray[np.floating[Any]]:
        xmin, xmax, ymin, ymax = await self._get_trim_limits()
        return image_data[xmin:xmax, ymin:ymax]

    async def _correct_fibre_position_for_trimming(self) -> None:
        xmin, xmax, ymin, ymax = await self._get_trim_limits()
        self._fibre_position = (self._fibre_position[1] - xmin, self._fibre_position[0] - ymin)

    async def _get_trim_limits(self) -> tuple[int, int, int, int]:
        xmin = self._fibre_position[1] - self._radius_ratio * self._inner_radius
        xmax = self._fibre_position[1] + self._radius_ratio * self._inner_radius
        ymin = self._fibre_position[0] - self._radius_ratio * self._inner_radius
        ymax = self._fibre_position[0] + self._radius_ratio * self._inner_radius
        return int(xmin), int(xmax), int(ymin), int(ymax)

    async def _calculate_relative_shift(self) -> None:
        section_ratio = self.ring.get_opposite_section_normalized_counts_ratio(self.ring.brightest_section_index)
        log.info("Ratio between brightest and the opposite section: %s", section_ratio)
        relative_shift = 1 / (1 + np.exp(-(section_ratio - 0.8) * 5))
        log.info("Corresponding relative offset: %s", relative_shift)
        self._relative_shift = min(1, relative_shift)

    async def _get_brightest_direction(self, method: str = "brightest_section") -> float:
        if method == "brightest_point":
            y_brightest_point, x_brightest_point = self.ring.get_brightest_point()
            return self.ring.get_angle_from_position(x_brightest_point, y_brightest_point)
        elif method == "brightest_section":
            return self.ring.get_brightest_section_angle()
        else:
            raise ValueError(f"Unknown method {method}")

    async def _get_offset(self) -> tuple[float, float]:
        angle_direction = await self._get_brightest_direction()
        log.info("Angle of the brightest section: %s deg", angle_direction)
        await self._calculate_relative_shift()
        total_offset = self._relative_shift * self._inner_radius
        x_offset = total_offset * np.sin(angle_direction / 180 * np.pi)
        y_offset = -total_offset * np.cos(angle_direction / 180 * np.pi)
        return x_offset, y_offset


__all__ = ["SpilledLightGuiding"]
