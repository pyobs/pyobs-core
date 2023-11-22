import logging
from typing import Dict, Any

from astropy.coordinates import SkyCoord
import astropy.units as u
from astropy.wcs import WCS

from pyobs.images import Image


class _RequestLogger:
    def __init__(self, logger: logging.Logger, image: Image, request_data: Dict[str, Any]):
        self._logger = logger
        self._image = image
        self._request_data = request_data

    def log_request_data(self):
        ra_dec = SkyCoord(ra=self._request_data["ra"] * u.deg, dec=self._request_data["dec"] * u.deg, frame="icrs")
        center_x, center_y = self._image.header["CRPIX1"], self._image.header["CRPIX2"]

        self._logger.info(
            "Found original RA=%s (%.4f), Dec=%s (%.4f) at pixel %.2f,%.2f.",
            ra_dec.ra.to_string(sep=":", unit=u.hour, pad=True),
            self._request_data["ra"],
            ra_dec.dec.to_string(sep=":", unit=u.deg, pad=True),
            self._request_data["dec"],
            center_x,
            center_y,
        )

    def log_request_result(self, image_wcs: WCS):
        center_x, center_y = self._image.header["CRPIX1"], self._image.header["CRPIX2"]
        final_ra, final_dec = image_wcs.all_pix2world(center_x, center_y, 0)
        final_ra_dec = SkyCoord(ra=final_ra * u.deg, dec=final_dec * u.deg, frame="icrs")

        self._logger.info(
            "Found final RA=%s (%.4f), Dec=%s (%.4f) at pixel %.2f,%.2f.",
            final_ra_dec.ra.to_string(sep=":", unit=u.hour, pad=True),
            self._request_data["ra"],
            final_ra_dec.dec.to_string(sep=":", unit=u.deg, pad=True),
            self._request_data["dec"],
            center_x,
            center_y,
        )