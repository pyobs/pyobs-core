from copy import copy
from typing import Optional

import numpy as np
import pandas as pd
from astropy.table import Table

from pyobs.images import Image


class PySepCatalog:
    def __init__(self, sources: pd.DataFrame):
        self._sources = sources

    @classmethod
    def from_array(cls, sources: np.ndarray):
        source_dataframe = pd.DataFrame(sources)
        return cls(source_dataframe)

    def filter_detection_flag(self):
        self._sources = self._sources[self._sources["flag"] < 8]

    def calc_ellipticity(self):
        self._sources["ellipticity"] = 1.0 - (self._sources["b"] / self._sources["a"])

    def calc_fwhm(self):
        fwhm = 2.0 * (np.log(2) * (self._sources["a"] ** 2.0 + self._sources["b"] ** 2.0)) ** 0.5
        self._sources["fwhm"] = fwhm

    def clip_rotation_angle(self):
        self._sources["theta"] = self._sources["theta"].clip(lower=np.pi / 2, upper=np.pi / 2)

    def calc_kron_radius(self, data: np.ndarray):
        import sep

        kronrad, krflag = sep.kron_radius(
            data,
            self._sources["x"],
            self._sources["y"],
            self._sources["a"],
            self._sources["b"],
            self._sources["theta"],
            6.0,
        )
        self._sources["flag"] |= krflag
        self._sources["kronrad"] = kronrad

    def calc_flux(self, data: np.ndarray, mask: np.ndarray, gain: Optional[float]):
        import sep

        flux, _, flag = sep.sum_ellipse(
            data,
            self._sources["x"],
            self._sources["y"],
            self._sources["a"],
            self._sources["b"],
            self._sources["theta"],
            2.5 * self._sources["kronrad"],
            subpix=5,
            mask=mask,
            gain=gain,
        )

        self._sources["flag"] |= flag
        self._sources["flux"] = flux

    def calc_flux_radii(self, data: np.ndarray):
        import sep

        flux_radii, flag = sep.flux_radius(
            data,
            self._sources["x"],
            self._sources["y"],
            6.0 * self._sources["a"],
            [0.25, 0.5, 0.75],
            normflux=self._sources["flux"],
            subpix=5,
        )

        self._sources["flag"] |= flag
        self._sources["fluxrad25"] = flux_radii[:, 0]
        self._sources["fluxrad50"] = flux_radii[:, 1]
        self._sources["fluxrad75"] = flux_radii[:, 2]

    def calc_winpos(self, data: np.ndarray):
        import sep

        sig = 2.0 / 2.35 * self._sources["fluxrad50"]
        xwin, ywin, flag = sep.winpos(data, self._sources["x"], self._sources["y"], sig)

        self._sources["flag"] |= flag
        self._sources["xwin"] = xwin
        self._sources["ywin"] = ywin

    def rotation_angle_to_degree(self):
        self._sources["theta"] = np.degrees(self._sources["theta"])

    def apply_fits_origin_convention(self):
        self._sources["x"] += 1
        self._sources["y"] += 1

    def save_to_image(self, image: Image):
        cat = self._sources[
            [
                "x",
                "y",
                "peak",
                "flux",
                "fwhm",
                "a",
                "b",
                "theta",
                "ellipticity",
                "tnpix",
                "kronrad",
                "fluxrad25",
                "fluxrad50",
                "fluxrad75",
                "xwin",
                "ywin",
            ]
        ]

        output_image = copy(image)
        output_image.catalog = Table.from_pandas(cat)
        return output_image
