from __future__ import annotations

import threading
import numpy as np
from astropy.coordinates import SkyCoord
import astropy.units as u
from typing import Tuple, List, Optional, Any, TYPE_CHECKING
import random

from pyobs.object import Object
from pyobs.utils.enums import MotionStatus
if TYPE_CHECKING:
    from pyobs.utils.simulation import SimWorld


class SimTelescope(Object):
    """A simulated telescope on an equitorial mount."""
    __module__ = 'pyobs.utils.simulation'

    def __init__(self, world: 'SimWorld', position: Optional[Tuple[float, float]] = None,
                 offsets: Optional[Tuple[float, float]] = None, pointing_offset: Optional[Tuple[float, float]] = None,
                 move_accuracy: float = 2., speed: float = 20., focus: float = 50, filters: Optional[List[str]] = None,
                 filter: str = 'clear', drift: Optional[Tuple[float, float]] = None, focal_length: float = 5000.,
                 **kwargs: Any):
        """Initializes new telescope.

        Args:
            world: World object.
            position: RA/Dec tuple with position of telescope in degrees.
            offsets: RA/Dec offsets of telescope in arcsecs.
            pointing_offset: Pointing offset in RA/Dec in arcsecs.
            move_accuracy: Accuracy of movements in RA/Dec, i.e. random error after any movement [arcsec].
            speed: Speed of telescope in deg/sec.
            focus: Telescope focus.
            filters: List of filters.
            filter: Current filter.
            drift: RA/Dec drift of telescope in arcsec/sec.
            focal_length: Focal length of telescope in mm.
        """
        Object.__init__(self, **kwargs)

        # store
        self.world = world
        self.status = MotionStatus.IDLE
        self.status_callback = None

        # init
        self._position = SkyCoord(0. * u.deg, 0. * u.deg, frame='icrs') if position is None else \
            SkyCoord(position[0] * u.deg, position[1] * u.deg, frame='icrs')
        self._offsets = (0., 0.) if offsets is None else offsets
        self.pointing_offset = (20., 2.) if pointing_offset is None else pointing_offset
        self.move_accuracy = (1, 1) if move_accuracy is None else move_accuracy
        self.speed = speed     # telescope speed in deg/sec
        self.focus = focus
        self.filters = ['clear', 'B', 'V', 'R'] if filters is None else filters
        self.filter = filter
        self.drift = (0., 0.) if drift is None else drift     # arcsec/sec in RA/Dec
        self.focal_length = focal_length

        # private stuff
        self._drift = (0., 0.)
        self._dest_coords = None

        # locks
        self._pos_lock = threading.RLock()

        # threads
        self.add_thread_func(self._move_thread)

    @property
    def position(self) -> SkyCoord:
        return self._position

    @property
    def offsets(self) -> Tuple[float, float]:
        return self._offsets

    def _change_motion_status(self, status: MotionStatus) -> None:
        """Change the current motion status.

        Args:
            status: New motion status
        """

        # call callback
        if self.status_callback is not None and status != self.status:
            self.status_callback(status)

        # set it
        self.status = status

    @property
    def real_pos(self) -> SkyCoord:
        # calculate offsets
        dra = (self._offsets[0] * u.deg + self._drift[0] * u.arcsec) / np.cos(np.radians(self._position.dec.degree))
        ddec = self._offsets[1] * u.deg + self._drift[1] * u.arcsec

        # return position
        with self._pos_lock:
            return SkyCoord(ra=self._position.ra + dra,
                            dec=self._position.dec + ddec,
                            frame='icrs')

    def move_ra_dec(self, coords: SkyCoord) -> None:
        """Move telescope to given RA/Dec position.

        Args:
            coords: Destination coordinates.
        """

        # change status
        self._change_motion_status(MotionStatus.SLEWING)

        # calculate random RA/Dec offsets
        acc = self.move_accuracy / 3600.
        ra = random.gauss(coords.ra.degree, acc / np.cos(np.radians(coords.dec.degree))) * u.deg
        dec = random.gauss(coords.dec.degree, acc) * u.deg

        # set coordinates
        self._dest_coords = SkyCoord(ra=ra, dec=dec, frame='icrs')

    def set_offsets(self, dra: float, ddec: float) -> None:
        """Move RA/Dec offsets.

        Args:
            dra: RA offset [deg]
            ddec: Dec offset [deg]
        """

        # calculate random RA/Dec offsets
        acc = self.move_accuracy / 3600.
        ra, dec = random.gauss(dra, acc), random.gauss(ddec, acc)

        # set offsets
        self._offsets = (ra, dec)

    def _move_thread(self) -> None:
        """Move the telescope over time."""

        # run until closed
        while not self.closing.is_set():

            # do we have destination coordinates?
            if self._dest_coords is not None:
                # calculate moving vector
                vra = (self._dest_coords.ra.degree - self._position.ra.degree) * \
                      np.cos(np.radians(self._position.dec.degree))
                vdec = self._dest_coords.dec.degree - self._position.dec.degree

                # get direction
                length = np.sqrt(vra**2 + vdec**2)

                # do we reach target?
                if length < self.speed:
                    # set it
                    with self._pos_lock:
                        # set position and reset destination
                        self._change_motion_status(MotionStatus.TRACKING)
                        self._position = self._dest_coords
                        self._dest_coords = None

                        # set some random drift around the pointing error
                        self._drift = (random.gauss(self.pointing_offset[0], self.pointing_offset[0] / 10.),
                                       random.gauss(self.pointing_offset[1], self.pointing_offset[1] / 10.))

                else:
                    # norm vector and get movement
                    dra = vra / length * self.speed / np.cos(np.radians(self._position.dec.degree)) * u.deg
                    ddec = vdec / length * self.speed * u.deg

                    # apply it
                    with self._pos_lock:
                        self._change_motion_status(MotionStatus.SLEWING)
                        self._position = SkyCoord(ra=self._position.ra + dra,
                                                  dec=self._position.dec + ddec,
                                                  frame='icrs')

            else:
                # no movement, just drift
                # calculate constant drift
                drift_ra = random.gauss(self.drift[0], self.drift[0] / 10.)
                drift_dec = random.gauss(self.drift[1], self.drift[1] / 10.)

                # and apply it
                with self._pos_lock:
                    self._drift = (self._drift[0] + drift_ra, self._drift[1] + drift_dec)

            # sleep a second
            self.closing.wait(1)


__all__ = ['SimTelescope']
