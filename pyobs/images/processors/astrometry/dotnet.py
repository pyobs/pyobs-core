import logging
from typing import Any, Dict
import aiohttp
import pandas as pd
from astropy.coordinates import SkyCoord
from astropy.io.fits import Header
from astropy.wcs import WCS
import astropy.units as u

from pyobs.images import Image
import pyobs.utils.exceptions as exc
from ._dotnet_request_builder import _DotNetRequestBuilder
from .astrometry import Astrometry

log = logging.getLogger(__name__)


class AstrometryDotNet(Astrometry):
    """Perform astrometry using astrometry.net"""

    __module__ = "pyobs.images.processors.astrometry"

    def __init__(
        self,
        url: str,
        source_count: int = 50,
        radius: float = 3.0,
        timeout: int = 10,
        exceptions: bool = True,
        **kwargs: Any,
    ):
        """Init new astronomy.net processor.

        Args:
            url: URL to service.
            source_count: Number of sources to send.
            radius: Radius to search in.
            timeout: Timeout in seconds for call to astrometry web service.
            exceptions: Whether to raise Exceptions.
        """
        Astrometry.__init__(self, **kwargs)

        # URL to web-service
        self.url = url

        self.timeout = timeout
        self.exceptions = exceptions

        self._request_builder = _DotNetRequestBuilder(source_count, radius)

    @staticmethod
    def _log_catalog_data(image: Image, request_data: Dict[str, Any]):
        ra_dec = SkyCoord(ra=request_data["ra"] * u.deg, dec=request_data["dec"] * u.deg, frame="icrs")
        center_x, center_y = image.header["CRPIX1"], image.header["CRPIX2"]
        log.info(
            "Found original RA=%s (%.4f), Dec=%s (%.4f) at pixel %.2f,%.2f.",
            ra_dec.ra.to_string(sep=":", unit=u.hour, pad=True),
            request_data["ra"],
            ra_dec.dec.to_string(sep=":", unit=u.deg, pad=True),
            request_data["dec"],
            center_x,
            center_y,
        )

    async def _send_request(self, request_data: Dict[str, Any]) -> (Dict[str, any], int):
        async with aiohttp.ClientSession() as session:
            async with session.post(self.url, json=request_data, timeout=self.timeout) as response:
                response_status_code = response.status
                response_data = await response.json()

        return response_data, response_status_code

    @staticmethod
    def _generate_request_error_msg(response_data: Dict[str, Any]) -> str:
        if "error" not in response_data:
            return "Could not connect to astrometry service."

        if response_data["error"] == "Could not find WCS file.":
            return "Could not determine WCS."

        return f"Received error from astrometry service: {response_data['error']}"

    def _handle_request_error(self, response_data: Dict[str, Any]):
        error_msg = self._generate_request_error_msg(response_data)
        raise exc.ImageError(error_msg)

    @staticmethod
    def _copy_response_into_header(header: Header, response_data: Dict[str, Any]):
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
            header[keyword] = response_data[keyword]

    @staticmethod
    def _delete_old_wcs_data(header: Header):
        """
        astrometry.net gives a CD matrix, so we have to delete the PC matrix and the CDELT* parameters
        """
        for keyword in ["PC1_1", "PC1_2", "PC2_1", "PC2_2", "CDELT1", "CDELT2"]:
            del header[keyword]

    @staticmethod
    def _add_plate_solution_to_catalog(catalog: pd.DataFrame, image_wcs: WCS):
        ras, decs = image_wcs.all_pix2world(catalog["x"], catalog["y"], 1)

        catalog["ra"] = ras
        catalog["dec"] = decs

    @staticmethod
    def _log_request_result(image: Image, image_wcs: WCS, response_data: Dict[str, Any]):

        center_x, center_y = image.header["CRPIX1"], image.header["CRPIX2"]
        final_ra, final_dec = image_wcs.all_pix2world(center_x, center_y, 0)
        final_ra_dec = SkyCoord(ra=final_ra * u.deg, dec=final_dec * u.deg, frame="icrs")

        # log it
        log.info(
            "Found final RA=%s (%.4f), Dec=%s (%.4f) at pixel %.2f,%.2f.",
            final_ra_dec.ra.to_string(sep=":", unit=u.hour, pad=True),
            response_data["ra"],
            final_ra_dec.dec.to_string(sep=":", unit=u.deg, pad=True),
            response_data["dec"],
            center_x,
            center_y,
        )

    async def _process(self, image: Image) -> Image:
        result_image = image.copy()

        self._request_builder.add_catalog_from_image(result_image)
        self._request_builder.add_header_from_image(result_image)

        request_data = self._request_builder()

        self._log_catalog_data(image, request_data)

        response_data, response_status_code = await self._send_request(request_data)

        # success?
        if response_status_code != 200 or "error" in response_data:
            self._handle_request_error(response_data)

        self._copy_response_into_header(result_image.header, response_data)
        self._delete_old_wcs_data(result_image.header)

        image_wcs = WCS(result_image.header)
        self._add_plate_solution_to_catalog(result_image.catalog, image_wcs)
        self._log_request_result(result_image, image_wcs, request_data)

        # huge success
        result_image.header["WCSERR"] = 0
        return result_image

    def _handle_error(self, image: Image, error: exc.ImageError):
        if self.exceptions:
            raise error

        image.header["WCSERR"] = 1

        log.warning(error.message)

        return image

    async def __call__(self, image: Image) -> Image:
        """Find astrometric solution on given image.

        Writes WCSERR=1 into FITS header on failure.

        Args:
            image: Image to analyse.
        """

        try:
            return await self._process(image)
        except exc.ImageError as e:
            return self._handle_error(image, e)


__all__ = ["AstrometryDotNet"]
