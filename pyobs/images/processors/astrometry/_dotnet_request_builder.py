from typing import Optional

import pandas as pd
from astropy.io.fits import Header

from pyobs.images import Image
import pyobs.utils.exceptions as exc
from pyobs.images.processors.astrometry._dotnet_request import _DotNetRequest


class _DotNetRequestBuilder:
    def __init__(self, source_count: int, radius: float):
        self._source_count = source_count
        self._radius = radius

        self._request_data = {}
        self._catalog = pd.DataFrame()
        self._header: Optional[Header] = None

    def _filter_catalog(self):
        self._catalog = self._catalog.dropna(how="any")
        self._catalog = self._catalog[self._catalog["peak"] < 60000]

    def _validate_catalog(self):
        if self._catalog is None or len(self._catalog) < 3:
            raise exc.ImageError("Not enough sources for astrometry.")

    def _select_brightest_stars(self):
        self._catalog = self._catalog.sort_values("flux", ascending=False)
        self._catalog = self._catalog[: self._source_count]

    def _validate_header(self):
        if "CDELT1" not in self._header:
            raise exc.ImageError("No CDELT1 found in header.")

    def _build_request_data(self):
        scale = abs(self._header["CDELT1"]) * 3600
        self._request_data = {
            "ra": self._header["TEL-RA"],
            "dec": self._header["TEL-DEC"],
            "scale_low": scale * 0.9,
            "scale_high": scale * 1.1,
            "radius": self._radius,
            "crpix-x": self._header["CRPIX1"],
            "crpix-y": self._header["CRPIX1"],
            "nx": self._header["NAXIS1"],
            "ny": self._header["NAXIS2"],
            "x": self._catalog["x"].tolist(),
            "y": self._catalog["y"].tolist(),
            "flux": self._catalog["flux"].tolist(),
        }

    def __call__(self, image: Image) -> _DotNetRequest:
        # set catalog and header
        if image.catalog is None:
            raise exc.ImageError("No catalog found in image.")
        self._catalog = image.catalog[["x", "y", "flux", "peak"]].to_pandas()
        self._header = image.header

        # select stars
        self._filter_catalog()
        self._validate_catalog()
        self._select_brightest_stars()

        # validate header and build request
        self._validate_header()
        self._build_request_data()
        return _DotNetRequest(self._request_data)
