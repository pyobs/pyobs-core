from typing import List, Tuple, Optional

import numpy as np
from astropy.stats import sigma_clipped_stats
from astropy.table import QTable
from photutils.aperture import CircularAperture, CircularAnnulus, ApertureMask, aperture_photometry

from pyobs.images import Image
from pyobs.images.processors.photometry._photometry_calculator import _PhotometryCalculator


class _PhotUtilAperturePhotometry(_PhotometryCalculator):

    def __init__(self):
        self._image: Optional[Image] = None
        self._positions: Optional[List[Tuple[float, float]]] = None

    def set_data(self, image: Image):
        self._image = image.copy()
        self._positions = [(x - 1, y - 1) for x, y in image.catalog.iterrows("x", "y")]

    @property
    def catalog(self):
        return self._image.catalog

    def __call__(self, diameter: int):
        radius = self._calc_aperture_radius_in_px(diameter)
        if radius < 1:
            return

        aperture = CircularAperture(self._positions, r=radius)
        aperture_flux, aperture_error = self._calc_aperture_flux(aperture)

        median_background = self._calc_median_backgrounds(radius)
        aperture_background = self._calc_integrated_background(median_background, aperture)

        corrected_aperture = self._background_correct_aperture_flux(aperture_flux, aperture_background)

        self._update_catalog(diameter, corrected_aperture, aperture_error, median_background)

    def _calc_aperture_radius_in_px(self, diameter: int):
        radius = diameter / 2.0
        return radius / self._image.pixel_scale

    def _calc_median_backgrounds(self, radius: float) -> np.ndarray[float]:
        annulus_aperture = CircularAnnulus(self._positions, r_in=2 * radius, r_out=3 * radius)
        annulus_masks = annulus_aperture.to_mask(method="center")

        bkg_median = [
            self._calc_median_background(mask)
            for mask in annulus_masks
        ]

        return np.array(bkg_median)

    def _calc_median_background(self, mask: ApertureMask) -> float:
        annulus_data = mask.multiply(self._image.data)
        annulus_data_1d = annulus_data[mask.data > 0]
        _, sigma_clipped_median, _ = sigma_clipped_stats(annulus_data_1d)
        return sigma_clipped_median

    @staticmethod
    def _calc_integrated_background(median_background: np.ndarray[float], aperture: CircularAperture) -> np.ndarray[float]:
        return median_background * aperture.area

    def _calc_aperture_flux(self, aperture: CircularAperture) -> Tuple[
        np.ndarray[float], Optional[np.ndarray[float]]]:

        phot: QTable = aperture_photometry(self._image.data, aperture, mask=self._image.safe_mask,
                                           error=self._image.safe_uncertainty)

        aperture_flux = phot["aperture_sum"]
        aperture_error = phot["aperture_sum_err"] if "aperture_sum_err" in phot.keys() else None

        return aperture_flux, aperture_error

    @staticmethod
    def _background_correct_aperture_flux(aperture_flux: np.ndarray[float], aperture_background: np.ndarray[float]) -> \
            np.ndarray[float]:
        return aperture_flux - aperture_background

    def _update_catalog(self, diameter: int, corrected_aperture_flux: np.ndarray[float],
                        aperture_error: Optional[np.ndarray[float]], median_background: np.ndarray[float]):

        self._image.catalog["fluxaper%d" % diameter] = corrected_aperture_flux
        if aperture_error is not None:
            self._image.catalog["fluxerr%d" % diameter] = aperture_error
        self._image.catalog["bkgaper%d" % diameter] = median_background
