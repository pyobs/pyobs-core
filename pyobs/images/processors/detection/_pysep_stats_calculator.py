import asyncio
from copy import copy
from functools import partial
from typing import Optional, Any
import numpy as np
import numpy.typing as npt

from pyobs.images.processors.detection._source_catalog import _SourceCatalog


class PySepStatsCalculator:
    def __init__(
        self,
        catalog: _SourceCatalog,
        data: npt.NDArray[np.floating[Any]],
        mask: npt.NDArray[np.floating[Any]],
        gain: float | None,
    ):
        self._catalog = copy(catalog)
        self._data = data
        self._mask = mask
        self._gain = gain

    async def __call__(self, *args: Any, **kwargs: Any) -> _SourceCatalog:
        self._calc_ellipticity()
        self._calc_fwhm()
        self._calc_kron_radius()

        loop = asyncio.get_running_loop()
        await loop.run_in_executor(None, partial(self._calc_flux))

        self._calc_flux_radii()
        self._calc_winpos()

        return self._catalog

    def _calc_ellipticity(self) -> None:
        self._catalog.sources["ellipticity"] = 1.0 - (self._catalog.sources["b"] / self._catalog.sources["a"])

    def _calc_fwhm(self) -> None:
        fwhm = 2.0 * (np.log(2) * (self._catalog.sources["a"] ** 2.0 + self._catalog.sources["b"] ** 2.0)) ** 0.5
        self._catalog.sources["fwhm"] = fwhm

    def _calc_kron_radius(self) -> None:
        import sep

        kronrad, krflag = sep.kron_radius(
            self._data,
            self._catalog.sources["x"],
            self._catalog.sources["y"],
            self._catalog.sources["a"],
            self._catalog.sources["b"],
            self._catalog.sources["theta"],
            6.0,
        )
        self._catalog.sources["flag"] |= krflag
        self._catalog.sources["kronrad"] = kronrad

    def _calc_flux(self) -> None:
        import sep

        flux, _, flag = sep.sum_ellipse(
            self._data,
            self._catalog.sources["x"],
            self._catalog.sources["y"],
            self._catalog.sources["a"],
            self._catalog.sources["b"],
            self._catalog.sources["theta"],
            2.5 * self._catalog.sources["kronrad"],
            subpix=5,
            mask=self._mask,
            gain=self._gain,
        )

        self._catalog.sources["flag"] |= flag
        self._catalog.sources["flux"] = flux

    def _calc_flux_radii(self) -> None:
        import sep

        flux_radii, flag = sep.flux_radius(
            self._data,
            self._catalog.sources["x"],
            self._catalog.sources["y"],
            6.0 * self._catalog.sources["a"],
            [0.25, 0.5, 0.75],
            normflux=self._catalog.sources["flux"],
            subpix=5,
        )

        self._catalog.sources["flag"] |= flag
        self._catalog.sources["fluxrad25"] = flux_radii[:, 0]
        self._catalog.sources["fluxrad50"] = flux_radii[:, 1]
        self._catalog.sources["fluxrad75"] = flux_radii[:, 2]

    def _calc_winpos(self) -> None:
        import sep

        sig = 2.0 / 2.35 * self._catalog.sources["fluxrad50"]
        xwin, ywin, flag = sep.winpos(self._data, self._catalog.sources["x"], self._catalog.sources["y"], sig)

        self._catalog.sources["flag"] |= flag
        self._catalog.sources["xwin"] = xwin
        self._catalog.sources["ywin"] = ywin
