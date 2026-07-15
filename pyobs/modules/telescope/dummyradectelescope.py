from __future__ import annotations

import logging
import random
from typing import Any

import astropy.units as u
import numpy as np
from astropy.coordinates import SkyCoord

from pyobs.events import OffsetsRaDecEvent
from pyobs.interfaces import IOffsetsRaDec, IPointingBody, IPointingOrbitalElements, RaDecOffsetState
from pyobs.modules.telescope._dummytelescopebase import _DummyTelescopeBase

log = logging.getLogger(__name__)


class DummyRaDecTelescope(_DummyTelescopeBase, IOffsetsRaDec, IPointingBody, IPointingOrbitalElements):
    """A dummy equatorial-mount telescope for testing, offering RA/Dec offsets."""

    __module__ = "pyobs.modules.telescope"

    def __init__(self, offsets: tuple[float, float] | None = None, **kwargs: Any):
        """Creates a new dummy RA/Dec telescope.

        Args:
            offsets: Initial RA/Dec offsets in degrees.
        """
        _DummyTelescopeBase.__init__(self, **kwargs)
        self._offsets = (0.0, 0.0) if offsets is None else tuple(offsets)

    @property
    def real_pos(self) -> SkyCoord:
        """Current position including offsets and drift."""
        dra = (self._offsets[0] * u.deg + self._drift[0] * u.arcsec) / np.cos(np.radians(self._position.dec.degree))
        ddec = self._offsets[1] * u.deg + self._drift[1] * u.arcsec
        return SkyCoord(ra=self._position.ra + dra, dec=self._position.dec + ddec, frame="icrs")

    async def open(self) -> None:
        """Open module."""
        await _DummyTelescopeBase.open(self)
        if self._comm:
            await self.comm.register_event(OffsetsRaDecEvent)
        await self.comm.set_state(IOffsetsRaDec, RaDecOffsetState(ra=self._offsets[0], dec=self._offsets[1]))

    async def set_offsets_radec(self, dra: float, ddec: float, **kwargs: Any) -> None:
        """Move an RA/Dec offset."""
        log.info("Moving offset dra=%.5f, ddec=%.5f", dra, ddec)
        await self.comm.send_event(OffsetsRaDecEvent(ra=dra, dec=ddec))
        acc = self._move_accuracy / 3600.0
        self._offsets = (random.gauss(dra, acc), random.gauss(ddec, acc))
        await self.comm.set_state(IOffsetsRaDec, RaDecOffsetState(ra=dra, dec=ddec))


__all__ = ["DummyRaDecTelescope"]
