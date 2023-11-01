from typing import Dict, Any

import pandas as pd
from astropy.io.fits import Header

from pyobs.images import Image
import pyobs.utils.exceptions as exc


class _DotNetRequestBuilder:
    def __init__(self, source_count: int, radius: float):
        self._source_count = source_count
        self._radius = radius

        self._data = {}
        self._catalog: pd.DataFrame = None
        self._header: Header = None

    def add_catalog_from_image(self, image: Image):
        if image.catalog is None:
            raise exc.ImageError("No catalog found in image.")

        self._catalog = image.catalog[["x", "y", "flux", "peak"]].to_pandas()

    def add_header_from_image(self, image: Image):
        self._header = image.header

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
        self._data = {
            "ra": self._header["TEL-RA"],
            "dec": self._header["TEL-DEC"],
            "scale_low": scale * 0.9,
            "scale_high": scale * 1.1,
            "radius": self._radius,
            "nx": self._header["NAXIS1"],
            "ny": self._header["NAXIS2"],
            "x": self._catalog["x"].tolist(),
            "y": self._catalog["y"].tolist(),
            "flux": self._catalog["flux"].tolist(),
        }

    def __call__(self) -> Dict[str, Any]:
        self._validate_header()

        self._filter_catalog()
        self._validate_catalog()
        self._select_brightest_stars()

        self._build_request_data()

        return self._data
