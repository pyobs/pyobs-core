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
        self.source_count = source_count
        self.radius = radius
        self.timeout = timeout
        self.exceptions = exceptions

    @staticmethod
    def _get_catalog(image: Image) -> pd.DataFrame:
        if image.catalog is None:
            raise exc.ImageError("No catalog found in image.")

        return image.catalog[["x", "y", "flux", "peak"]].to_pandas()

    @staticmethod
    def _filter_catalog(catalogue: pd.DataFrame) -> pd.DataFrame:
        res_catalogue = catalogue.dropna(how="any")
        res_catalogue = res_catalogue[res_catalogue["peak"] < 60000]

        return res_catalogue

    @staticmethod
    def _validate_catalogue(catalogue: pd.DataFrame):
        if catalogue is None or len(catalogue) < 3:
            raise exc.ImageError("Not enough sources for astrometry.")

    def _select_brightest_stars(self, catalogue: pd.DataFrame) -> pd.DataFrame:
        catalogue = catalogue.sort_values("flux", ascending=False)
        catalogue = catalogue[: self.source_count]

        return catalogue

    @staticmethod
    def _validate_header(header: Header):
        if "CDELT1" not in header:
            raise exc.ImageError("No CDELT1 found in header.")

    def _build_request_data(self, image: Image, catalogue: pd.DataFrame):
        scale = abs(image.header["CDELT1"]) * 3600
        data = {
            "ra": image.header["TEL-RA"],
            "dec": image.header["TEL-DEC"],
            "scale_low": scale * 0.9,
            "scale_high": scale * 1.1,
            "radius": self.radius,
            "nx": image.header["NAXIS1"],
            "ny": image.header["NAXIS2"],
            "x": catalogue["x"].tolist(),
            "y": catalogue["y"].tolist(),
            "flux": catalogue["flux"].tolist(),
        }

        return data

    @staticmethod
    def _log_catalogue_data(image: Image, data: Dict[str, Any]):
        ra_dec = SkyCoord(ra=data["ra"] * u.deg, dec=data["dec"] * u.deg, frame="icrs")
        cx, cy = image.header["CRPIX1"], image.header["CRPIX2"]
        log.info(
            "Found original RA=%s (%.4f), Dec=%s (%.4f) at pixel %.2f,%.2f.",
            ra_dec.ra.to_string(sep=":", unit=u.hour, pad=True),
            data["ra"],
            ra_dec.dec.to_string(sep=":", unit=u.deg, pad=True),
            data["dec"],
            cx,
            cy,
        )

    async def _send_request(self, data: Dict[str, Any]) -> (Dict[str, any], int):
        async with aiohttp.ClientSession() as session:
            async with session.post(self.url, json=data, timeout=self.timeout) as response:
                status_code = response.status
                json = await response.json()

        return json, status_code

    @staticmethod
    def _generate_request_error_msg(json: Dict[str, Any]) -> str:
        if "error" not in json:
            return "Could not connect to astrometry service."

        if json["error"] == "Could not find WCS file.":
            return "Could not determine WCS."

        return f"Received error from astrometry service: {json['error']}"

    def _handle_request_error(self, json: Dict[str, Any]):
        error_msg = self._generate_request_error_msg(json)
        raise exc.ImageError(error_msg)

    @staticmethod
    def _copy_response_into_header(header: Header, json: Dict[str, Any]):
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
            header[keyword] = json[keyword]

    @staticmethod
    def _delete_old_wcs_data(header: Header):
        """
        astrometry.net gives a CD matrix, so we have to delete the PC matrix and the CDELT* parameters
        """
        for keyword in ["PC1_1", "PC1_2", "PC2_1", "PC2_2", "CDELT1", "CDELT2"]:
            del header[keyword]

    @staticmethod
    def _add_plate_solution_to_catalogue(catalogue: pd.DataFrame, image_wcs: WCS):
        ras, decs = image_wcs.all_pix2world(catalogue["x"], catalogue["y"], 1)

        catalogue["ra"] = ras
        catalogue["dec"] = decs

    @staticmethod
    def _log_request_result(image: Image, image_wcs: WCS, data: Dict[str, Any]):

        cx, cy = image.header["CRPIX1"], image.header["CRPIX2"]
        final_ra, final_dec = image_wcs.all_pix2world(cx, cy, 0)
        ra_dec = SkyCoord(ra=final_ra * u.deg, dec=final_dec * u.deg, frame="icrs")

        # log it
        log.info(
            "Found final RA=%s (%.4f), Dec=%s (%.4f) at pixel %.2f,%.2f.",
            ra_dec.ra.to_string(sep=":", unit=u.hour, pad=True),
            data["ra"],
            ra_dec.dec.to_string(sep=":", unit=u.deg, pad=True),
            data["dec"],
            cx,
            cy,
        )

    async def _process(self, image: Image) -> Image:
        img = image.copy()

        catalogue = self._get_catalog(image)
        filtered_catalogue = self._filter_catalog(catalogue)

        self._validate_catalogue(filtered_catalogue)

        reduced_catalogue = self._select_brightest_stars(filtered_catalogue)

        self._validate_header(img.header)

        data = self._build_request_data(img, reduced_catalogue)

        self._log_catalogue_data(image, data)

        json, status_code = await self._send_request(data)

        # success?
        if status_code != 200 or "error" in json:
            self._handle_request_error(json)

        self._copy_response_into_header(img.header, json)
        self._delete_old_wcs_data(img.header)

        image_wcs = WCS(img.header)
        self._add_plate_solution_to_catalogue(img.catalog, image_wcs)
        self._log_request_result(image, image_wcs, data)

        # huge success
        img.header["WCSERR"] = 0
        return img

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
