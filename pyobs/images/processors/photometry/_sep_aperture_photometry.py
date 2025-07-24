from typing import List, Optional, Any, cast
import numpy as np
import numpy.typing as npt
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

        self._data: npt.NDArray[np.floating[Any]] | None = None
        self._average_background: npt.NDArray[np.floating[Any]] | None = None

    def set_data(self, image: Image) -> None:
        self._image = image.copy()
        self._pos_x, self._pos_y = self._image.catalog["x"], self._image.catalog["y"]
        self._gain = image.header["DET-GAIN"] if "DET-GAIN" in image.header else None

    @property
    def catalog(self) -> Table | None:
        return None if self._image is None else self._image.catalog

    def _update_background_header(self) -> None:
        if self._image is not None:
            self._image.catalog["background"] = self._average_background

    def __call__(self, diameter: int) -> None:
        import sep

        if self._is_background_calculated():
            self._calc_background()
            self._update_background_header()

        radius = self._calc_aperture_radius_in_px(diameter)
        flux, fluxerr, _ = sep.sum_circle(
            self._data,
            self._pos_x,
            self._pos_y,
            radius,
            mask=None if self._image is None else self._image.safe_mask,
            err=None if self._image is None else self._image.safe_uncertainty,
            gain=self._gain,
        )
        self._update_flux_header(diameter, flux, fluxerr)

    def _is_background_calculated(self) -> bool:
        return self._data is None

    def _calc_background(self) -> None:
        if self._image is None:
            raise RuntimeError("No image set.")
        self._data, bkg = SepSourceDetection.remove_background(self._image.data, self._image.safe_mask)
        self._average_background = self._calc_average_background(bkg.back())

    def _calc_average_background(self, background: npt.NDArray[np.floating[Any]]) -> npt.NDArray[np.floating[Any]]:
        """
        since SEP sums up whole pixels, we need to do the same on an image of ones for the background_area
        """
        if self._image is None:
            raise RuntimeError("No image set.")
        background_flux = self._sum_ellipse(background, self._image, self._pos_x, self._pos_y)
        background_area = self._sum_ellipse(np.ones(shape=background.shape), self._image, self._pos_x, self._pos_y)

        median_background = np.divide(background_flux, background_area, where=background_area != 0)
        return cast(npt.NDArray[np.floating[Any]], median_background)

    @staticmethod
    def _sum_ellipse(
        data: npt.NDArray[np.floating[Any]],
        image: Image,
        x: list[float] | None,
        y: list[float] | None,
    ) -> npt.NDArray[np.floating[Any]]:
        import sep

        sum, _, _ = sep.sum_ellipse(
            data,
            x,
            y,
            image.catalog["a"],
            image.catalog["b"],
            theta=np.pi / 2.0,
            r=2.5 * image.catalog["kronrad"],
            subpix=1,
        )
        return cast(npt.NDArray[np.floating[Any]], sum)

    def _calc_aperture_radius_in_px(self, diameter: int) -> float:
        if self._image is None or self._image.pixel_scale is None:
            raise RuntimeError("Image and its pixel scale must be set before calculating aperture radius")
        radius: float = diameter / 2.0
        return radius / self._image.pixel_scale

    def _update_flux_header(
        self,
        diameter: int,
        flux: npt.NDArray[np.floating[Any]],
        fluxerr: npt.NDArray[np.floating[Any]],
    ) -> None:
        if self._image is None:
            raise RuntimeError("No image set.")
        self._image.catalog[f"fluxaper{diameter}"] = flux
        self._image.catalog[f"fluxerr{diameter}"] = fluxerr
