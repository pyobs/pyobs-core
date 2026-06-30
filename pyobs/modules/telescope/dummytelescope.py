from __future__ import annotations

import asyncio
import logging
import random
from typing import Any

import astropy.units as u
import numpy as np
from astropy.coordinates import SkyCoord

from pyobs.events import FilterChangedEvent, OffsetsRaDecEvent
from pyobs.interfaces import (
    FiltersCapabilities,
    FilterState,
    FocuserState,
    IFilters,
    IFitsHeaderBefore,
    IFocuser,
    IOffsetsRaDec,
    IPointingAltAz,
    IPointingRaDec,
    IReady,
    ITemperatures,
    RaDecOffsetState,
    RaDecState,
    ReadyState,
    SensorReading,
    TemperaturesState,
)
from pyobs.mixins.fitsnamespace import FitsNamespaceMixin
from pyobs.modules import timeout
from pyobs.modules.telescope.basetelescope import BaseTelescope
from pyobs.utils.enums import MotionStatus
from pyobs.utils.threads import LockWithAbort
from pyobs.utils.time import Time

log = logging.getLogger(__name__)


class DummyTelescope(
    BaseTelescope,
    IPointingRaDec,
    IPointingAltAz,
    IOffsetsRaDec,
    IFocuser,
    IFilters,
    IFitsHeaderBefore,
    ITemperatures,
    FitsNamespaceMixin,
):
    """A dummy telescope for testing."""

    __module__ = "pyobs.modules.telescope"

    def __init__(
        self,
        position: tuple[float, float] | None = None,
        offsets: tuple[float, float] | None = None,
        pointing_offset: tuple[float, float] | None = None,
        move_accuracy: float = 2.0,
        speed: float = 20.0,
        focus: float = 50.0,
        filters: list[str] | None = None,
        filter_name: str = "clear",
        drift: tuple[float, float] | None = None,
        focal_length: float = 5000.0,
        wait_secs: float = 1.0,
        **kwargs: Any,
    ):
        """Creates a new dummy telescope.

        Args:
            position: Initial RA/Dec position in degrees.
            offsets: Initial RA/Dec offsets in degrees.
            pointing_offset: Pointing offset in RA/Dec in arcsecs.
            move_accuracy: Accuracy of movements in arcsec (random error after any movement).
            speed: Speed of telescope in deg/sec.
            focus: Initial focus value.
            filters: List of available filters.
            filter_name: Initial filter name.
            drift: RA/Dec drift in arcsec/sec.
            focal_length: Focal length in mm.
            wait_secs: Wait time between slew checks in seconds.
        """
        BaseTelescope.__init__(self, **kwargs, motion_status_interfaces=["ITelescope", "IFocuser", "IFilters"])
        FitsNamespaceMixin.__init__(self, **kwargs)

        # telescope state
        self._position = (
            SkyCoord(0.0 * u.deg, 0.0 * u.deg, frame="icrs")
            if position is None
            else SkyCoord(position[0] * u.deg, position[1] * u.deg, frame="icrs")
        )
        self._offsets = (0.0, 0.0) if offsets is None else tuple(offsets)
        self._pointing_offset = (20.0, 2.0) if pointing_offset is None else tuple(pointing_offset)
        self._move_accuracy = move_accuracy
        self._speed = speed
        self._focus = focus
        self._filters = ["clear", "B", "V", "R"] if filters is None else filters
        self._filter_name = filter_name
        self._drift_rate = (0.0, 0.0) if drift is None else tuple(drift)
        self._focal_length = focal_length
        self._wait_secs = wait_secs

        # internal slewing state
        self._dest_coords: SkyCoord | None = None
        self._drift = (0.0, 0.0)
        self._sim_status = MotionStatus.IDLE

        # locks
        self._lock_focus = asyncio.Lock()
        self._abort_focus = asyncio.Event()

        # background slewing task
        self.add_background_task(self._move_task)

    @property
    def focal_length(self) -> float:
        return self._focal_length

    @property
    def real_pos(self) -> SkyCoord:
        """Current position including offsets and drift."""
        dra = (self._offsets[0] * u.deg + self._drift[0] * u.arcsec) / np.cos(np.radians(self._position.dec.degree))
        ddec = self._offsets[1] * u.deg + self._drift[1] * u.arcsec
        return SkyCoord(ra=self._position.ra + dra, dec=self._position.dec + ddec, frame="icrs")

    @property
    def _position_radec(self) -> tuple[float, float] | None:
        return float(self._position.ra.degree), float(self._position.dec.degree)

    async def _sim_change_status(self, status: MotionStatus) -> None:
        if status != self._sim_status:
            self._sim_status = status
            await self._change_motion_status(status)

    async def _move_task(self) -> None:
        """Background task that simulates telescope motion."""
        while True:
            if self._dest_coords is not None:
                vra = (self._dest_coords.ra.degree - self._position.ra.degree) * np.cos(
                    np.radians(self._position.dec.degree)
                )
                vdec = self._dest_coords.dec.degree - self._position.dec.degree
                length = np.sqrt(vra**2 + vdec**2)

                if length < self._speed:
                    await self._sim_change_status(MotionStatus.TRACKING)
                    self._position = self._dest_coords
                    self._dest_coords = None
                    self._drift = (
                        random.gauss(self._pointing_offset[0], self._pointing_offset[0] / 10.0),
                        random.gauss(self._pointing_offset[1], self._pointing_offset[1] / 10.0),
                    )
                    # publish updated position
                    await self.comm.set_state(
                        IPointingRaDec,
                        RaDecState(
                            ra=float(self._position.ra.degree),
                            dec=float(self._position.dec.degree),
                        ),
                    )
                else:
                    dra = vra / length * self._speed / np.cos(np.radians(self._position.dec.degree)) * u.deg
                    ddec = vdec / length * self._speed * u.deg
                    await self._sim_change_status(MotionStatus.SLEWING)
                    self._position = SkyCoord(ra=self._position.ra + dra, dec=self._position.dec + ddec, frame="icrs")
            else:
                drift_ra = random.gauss(self._drift_rate[0], max(self._drift_rate[0] / 10.0, 1e-9))
                drift_dec = random.gauss(self._drift_rate[1], max(self._drift_rate[1] / 10.0, 1e-9))
                self._drift = (self._drift[0] + drift_ra, self._drift[1] + drift_dec)

            await asyncio.sleep(1)

    async def open(self) -> None:
        """Open module."""
        await BaseTelescope.open(self)

        if self._comm:
            await self.comm.register_event(FilterChangedEvent)
            await self.comm.register_event(OffsetsRaDecEvent)

        await self._change_motion_status(MotionStatus.IDLE)

        # publish initial states and capabilities
        await self.comm.set_capabilities(IFilters, FiltersCapabilities(filters=self._filters))
        await self.comm.set_state(IFocuser, FocuserState(focus=self._focus, focus_offset=0.0))
        await self.comm.set_state(IFilters, FilterState(filter=self._filter_name))
        await self.comm.set_state(
            ITemperatures,
            TemperaturesState(
                readings=[
                    SensorReading(name="M1", value=10.0),
                    SensorReading(name="M2", value=12.0),
                ]
            ),
        )
        await self.comm.set_state(IReady, ReadyState(ready=True))
        await self.comm.set_state(
            IPointingRaDec,
            RaDecState(
                ra=float(self._position.ra.degree),
                dec=float(self._position.dec.degree),
            ),
        )
        await self.comm.set_state(IOffsetsRaDec, RaDecOffsetState(ra=self._offsets[0], dec=self._offsets[1]))

    async def _move_radec(self, ra: float, dec: float, abort_event: asyncio.Event) -> None:
        acc = self._move_accuracy / 3600.0
        ra_dest = random.gauss(ra, acc / np.cos(np.radians(self._position.dec.degree)))
        dec_dest = random.gauss(dec, acc)
        self._dest_coords = SkyCoord(ra=ra_dest * u.deg, dec=dec_dest * u.deg, frame="icrs")
        await self._sim_change_status(MotionStatus.SLEWING)

        while self._sim_status == MotionStatus.SLEWING and not abort_event.is_set():
            await asyncio.sleep(self._wait_secs)

    async def _move_altaz(self, alt: float, az: float, abort_event: asyncio.Event) -> None:
        coords = SkyCoord(
            alt=alt * u.degree, az=az * u.degree, obstime=Time.now(), location=self._location, frame="altaz"
        )
        icrs = coords.icrs
        await self._move_radec(icrs.ra.degree, icrs.dec.degree, abort_event)

    @timeout(60)
    async def set_focus(self, focus: float, **kwargs: Any) -> None:
        """Sets new focus."""
        if focus < 0 or focus > 100:
            raise ValueError("Invalid focus value.")

        async with LockWithAbort(self._lock_focus, self._abort_focus):
            log.info("Setting focus to %.2f...", focus)
            await self._change_motion_status(MotionStatus.SLEWING, interface="IFocuser")
            ifoc = self._focus * 1.0
            dfoc = (focus - ifoc) / 300.0
            for i in range(300):
                if self._abort_focus.is_set():
                    raise InterruptedError("Setting focus was interrupted.")
                self._focus = ifoc + i * dfoc
                await asyncio.sleep(0.01)
            await self._change_motion_status(MotionStatus.POSITIONED, interface="IFocuser")
            self._focus = focus
            await self.comm.set_state(IFocuser, FocuserState(focus=focus, focus_offset=0.0))

    async def set_filter(self, filter_name: str, **kwargs: Any) -> None:
        """Set the current filter."""
        if filter_name not in self._filters:
            raise ValueError("Invalid filter name.")

        if filter_name != self._filter_name:
            logging.info("Setting filter to %s", filter_name)
            await self._change_motion_status(MotionStatus.SLEWING, interface="IFilters")
            try:
                await asyncio.wait_for(asyncio.shield(self._closing.wait()), timeout=3.0)
                return
            except TimeoutError:
                pass
            await self._change_motion_status(MotionStatus.POSITIONED, interface="IFilters")
            self._filter_name = filter_name
            await self.comm.send_event(FilterChangedEvent(filter_name))
            await self.comm.set_state(IFilters, FilterState(filter=filter_name))
            logging.info("New filter set.")

    @timeout(60)
    async def init(self, **kwargs: Any) -> None:
        """Initialize telescope."""
        log.info("Initializing telescope...")
        await self._change_motion_status(MotionStatus.INITIALIZING)
        try:
            await asyncio.wait_for(asyncio.shield(self._closing.wait()), timeout=5.0)
            return
        except TimeoutError:
            pass
        await self._change_motion_status(MotionStatus.IDLE)
        log.info("Telescope initialized.")

    @timeout(60)
    async def park(self, **kwargs: Any) -> None:
        """Park telescope."""
        log.info("Parking telescope...")
        await self._change_motion_status(MotionStatus.PARKING)
        try:
            await asyncio.wait_for(asyncio.shield(self._closing.wait()), timeout=5.0)
            return
        except TimeoutError:
            pass
        await self._change_motion_status(MotionStatus.PARKED)
        log.info("Telescope parked.")

    async def set_offsets_radec(self, dra: float, ddec: float, **kwargs: Any) -> None:
        """Move an RA/Dec offset."""
        log.info("Moving offset dra=%.5f, ddec=%.5f", dra, ddec)
        await self.comm.send_event(OffsetsRaDecEvent(ra=dra, dec=ddec))
        acc = self._move_accuracy / 3600.0
        self._offsets = (random.gauss(dra, acc), random.gauss(ddec, acc))
        await self.comm.set_state(IOffsetsRaDec, RaDecOffsetState(ra=dra, dec=ddec))

    async def get_fits_header_before(
        self, namespaces: list[str] | None = None, **kwargs: Any
    ) -> dict[str, tuple[Any, str]]:
        hdr = await BaseTelescope.get_fits_header_before(self)
        hdr["TEL-FOCU"] = (self._focus, "Focus position [mm]")
        return self._filter_fits_namespace(hdr, namespaces=namespaces, **kwargs)

    async def stop_motion(self, device: str | None = None, **kwargs: Any) -> None:
        pass

    async def set_focus_offset(self, offset: float, **kwargs: Any) -> None:
        log.error("Not implemented")


__all__ = ["DummyTelescope"]
