from typing import List, Optional, Any

import numpy as np
from astropy.table import Table

from pyobs.images import Image
from pyobs.images.processors.detection import SepSourceDetection
from pyobs.images.processors.photometry._photometry_calculator import _PhotometryCalculator


class _SepAperturePhotometry(_PhotometryCalculator):
    def __init__(self) -> None:
        self._image: Optional[Image] = None
        self._pos_x: Optional[List[float]] = None
        self._pos_y: Optional[List[float]] = None

        self._gain: Optional[float] = None

        self._data: Optional[np.ndarray[int, Any]] = None
        self._average_background: Optional[np.ndarray[int, float]] = None

    def set_data(self, image: Image) -> None:
        self._image = image.copy()
        self._pos_x, self._pos_y = self._image.catalog["x"], self._image.catalog["y"]
        self._gain = image.header["DET-GAIN"] if "DET-GAIN" in image.header else None

    @property
    def catalog(self) -> Table:
        return self._image.catalog

    def _update_background_header(self) -> None:
        self._image.catalog[f"background"] = self._average_background

    def __call__(self, diameter: int) -> None:
        import sep

        if self._is_background_calculated():
            self._calc_background()
            self._update_background_header()

        radius = self._calc_aperture_radius_in_px(diameter)
        flux, fluxerr, _ = sep.sum_circle(
            self._data, self._pos_x, self._pos_y, radius, mask=self._image.safe_mask, err=self._image.safe_uncertainty, gain=self._gain
        )
        self._update_flux_header(diameter, flux, fluxerr)

    def _is_background_calculated(self) -> None:
        return self._data is None

    def _calc_background(self) -> None:
        self._data, bkg = SepSourceDetection.remove_background(self._image.data, self._image.safe_mask)
        self._average_background = self._calc_average_background(bkg.back())

    def _calc_average_background(self, background: np.ndarray) -> \
    np.ndarray[float]:
        """
        since SEP sums up whole pixels, we need to do the same on an image of ones for the background_area
        """
        background_flux = self._sum_ellipse(background, self._image, self._pos_x, self._pos_y)
        background_area = self._sum_ellipse(np.ones(shape=background.shape), self._image, self._pos_x, self._pos_y)

        median_background = np.divide(background_flux, background_area, where=background_area != 0)
        return median_background

    @staticmethod
    def _sum_ellipse(data: np.ndarray[float], image: Image, x: np.ndarray[float], y: np.ndarray[float]) -> np.ndarray[float]:
        import sep
        sum, _, _ = sep.sum_ellipse(
            data, x, y,
            image.catalog["a"],
            image.catalog["b"],
            theta=np.pi / 2.0,
            r=2.5 * image.catalog["kronrad"],
            subpix=1
        )
        return sum

    def _calc_aperture_radius_in_px(self, diameter: int) -> float:
        radius = diameter / 2.0
        return radius / self._image.pixel_scale

    def _update_flux_header(self, diameter: int, flux: np.ndarray, fluxerr: np.ndarray[float]) -> None:
        self._image.catalog[f"fluxaper{diameter}"] = flux
        self._image.catalog[f"fluxerr{diameter}"] = fluxerr