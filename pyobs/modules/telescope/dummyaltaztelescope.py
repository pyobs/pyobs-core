from __future__ import annotations

import logging
import random
from typing import Any

from pyobs.events import OffsetsAltAzEvent
from pyobs.interfaces import AltAzOffsetState, IOffsetsAltAz, IPointingBody, IPointingOrbitalElements
from pyobs.modules.telescope._dummytelescopebase import _DummyTelescopeBase

log = logging.getLogger(__name__)


class DummyAltAzTelescope(_DummyTelescopeBase, IOffsetsAltAz, IPointingBody, IPointingOrbitalElements):
    """A dummy alt/az-offset telescope for testing, offering Alt/Az offsets."""

    __module__ = "pyobs.modules.telescope"

    def __init__(self, offsets: tuple[float, float] | None = None, **kwargs: Any):
        """Creates a new dummy Alt/Az telescope.

        Args:
            offsets: Initial Alt/Az offsets in degrees.
        """
        _DummyTelescopeBase.__init__(self, **kwargs)
        self._altaz_offsets = (0.0, 0.0) if offsets is None else tuple(offsets)

    async def open(self) -> None:
        """Open module."""
        await _DummyTelescopeBase.open(self)
        if self._comm:
            await self.comm.register_event(OffsetsAltAzEvent)
        await self.comm.set_state(
            IOffsetsAltAz, AltAzOffsetState(alt=self._altaz_offsets[0], az=self._altaz_offsets[1])
        )

    async def set_offsets_altaz(self, dalt: float, daz: float, **kwargs: Any) -> None:
        """Move an Alt/Az offset."""
        log.info("Moving offset dalt=%.5f, daz=%.5f", dalt, daz)
        await self.comm.send_event(OffsetsAltAzEvent(alt=dalt, az=daz))
        acc = self._move_accuracy / 3600.0
        self._altaz_offsets = (random.gauss(dalt, acc), random.gauss(daz, acc))
        await self.comm.set_state(IOffsetsAltAz, AltAzOffsetState(alt=dalt, az=daz))


__all__ = ["DummyAltAzTelescope"]
