import logging
from typing import Union, Tuple, Type

from astropy.coordinates import SkyCoord

from pyobs import PyObsModule
from pyobs.interfaces import IAltAz, IRaDec

log = logging.getLogger(__name__)


def get_coord(obj: Union[IAltAz, IRaDec], mode: Type[Union[IAltAz, IRaDec]]) -> (float, float):
    """Gets coordinates from object

    Args:
        obj: Object to fetch coordinates from.
        mode: IAltAz or IRaDec.

    Returns:
        Return from method call.
    """

    if mode == IAltAz:
        return obj.get_altaz()
    else:
        return obj.get_radec()


def build_skycoord(coord: Tuple[float, float], mode: Type[Union[IAltAz, IRaDec]]) -> SkyCoord:
    """Build SkyCoord from x/y tuple in given mode.

    Args:
        coord: x/y tuple with coordinates in degrees.
        mode: IAltAz or IRaDec.

    Returns:
        SkyCoord with coordinates.
    """

    if mode == IAltAz:
        return SkyCoord(alt=coord[0], az=coord[1], frame='altaz')
    else:
        return SkyCoord(ra=coord[0], dec=coord[1], frame='icrs')


class FollowMixin:
    """Mixin for a device that should follow the motion of another."""
    def __init__(self, device: str, interval: float, tolerance: float, mode: Type[Union[IAltAz, IRaDec]],
                 *args, **kwargs):
        """Initializes the mixin.

        Args:
            device: Name of device to follow
            interval: Interval in seconds between position checks.
            tolerance: Tolerance in degrees between both devices to trigger new movement.
            mode: Set to "altaz" to follow Alt/Az coordinates or "radec" to follow RA/Dec.

        """

        # store
        self._device = device
        self._interval = interval
        self._tolerance = tolerance
        self._mode = mode

        # check
        if not isinstance(self, self._mode):
            raise ValueError('This module is not of given mode %s.' % mode)

        # add thread function only, if device is given
        if self._device is not None:
            self: Union[PyObsModule, FollowMixin]
            self._add_thread_func(self.__update_follow)

    def __update_follow(self):
        """Update function."""

        # I'm a module!
        self: Union[PyObsModule, FollowMixin]

        # run until closing
        while not self.closing.is_set():
            # get other device
            try:
                device = self.proxy(self._device, self._mode)
            except ValueError:
                # cannot follow, wait a little longer
                log.error('Cannot follow device, since it is of wrong type.')
                self.closing.wait(self._interval * 10)
                continue

            # get coordinates from other and from myself
            my_coords = build_skycoord(get_coord(self, self._mode), self._mode)
            x, y = get_coord(device, self._mode).wait()
            other_coords = build_skycoord((x, y), self._mode)

            # is separation larger than tolerance?
            if my_coords.separation(other_coords).degree > self._tolerance:
                # move to other
                if self._mode == IAltAz:
                    self: IAltAz
                    self.move_altaz(x, y)
                else:
                    self: IRaDec
                    self.move_radec(x, y)

            # sleep a little
            self.closing.wait(self._interval)


__all__ = ['FollowMixin']
