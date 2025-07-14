from copy import copy
from typing import Dict, Any, Optional

from astropy.wcs import WCS

from pyobs.images import Image
import pyobs.utils.exceptions as exc


class _ResponseImageWriter:
    def __init__(self, response_data: Dict[str, Any], image: Image):
        self._response_data = response_data
        self._image = copy(image)

        self._image_wcs: Optional[WCS] = None

    @property
    def response_data(self) -> Dict[str, Any]:
        return self._response_data

    @property
    def image(self) -> Image:
        return self._image

    @property
    def image_wcs(self) -> WCS:
        return self._image_wcs

    def _write_response_into_header(self) -> None:
        header_keywords_to_update = [
            "CTYPE1",
            "CTYPE2",
            "CRPIX1",
            "CRPIX2",
            "CRVAL1",
            "CRVAL2",
            "CD1_1",
            "CD1_2",
            "CD2_1",
            "CD2_2",
        ]

        for keyword in header_keywords_to_update:
            self._image.header[keyword] = self._response_data[keyword]

    def _delete_old_wcs_data(self) -> None:
        """
        astrometry.net gives a CD matrix, so we have to delete the PC matrix and the CDELT* parameters
        """
        for keyword in ["PC1_1", "PC1_2", "PC2_1", "PC2_2", "CDELT1", "CDELT2"]:
            del self._image.header[keyword]

    def _generate_image_wcs(self) -> None:
        self._image_wcs = WCS(self._image.header)

    def _add_plate_solution_to_catalog(self) -> None:
        if self._image_wcs is None:
            raise exc.ImageError("No WCS found.")
        ras, decs = self._image_wcs.all_pix2world(self._image.catalog["x"], self._image.catalog["y"], 1)

        self._image.catalog["ra"] = ras
        self._image.catalog["dec"] = decs

    def _add_wcs_err_success(self) -> None:
        self._image.header["WCSERR"] = 0

    def __call__(self, *args: Any, **kwargs: Any) -> Image:
        self._write_response_into_header()
        self._delete_old_wcs_data()
        self._generate_image_wcs()
        self._add_plate_solution_to_catalog()
        self._add_wcs_err_success()

        return self._image
