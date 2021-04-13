import logging
import threading
from typing import Union, Tuple, Type
from astropy.coordinates import SkyCoord
import astropy.units as u
from pyobs.comm import RemoteException

from pyobs.modules import Module
from pyobs.interfaces import IAltAz, IRaDec, IReady

log = logging.getLogger(__name__)


def get_coord(obj: Union[IAltAz, IRaDec], mode: Type[Union[IAltAz, IRaDec]]) -> Tuple[float, float]:
    """Gets coordinates from object

    Args:
        obj: Object to fetch coordinates from.
        mode: IAltAz or IRaDec.

    Returns:
        Return from method call.
    """

    if mode == IAltAz and isinstance(obj, IAltAz):
        return obj.get_altaz()
    elif mode == IRaDec and isinstance(obj, IRaDec):
        return obj.get_radec()
    else:
        raise ValueError('Unknown mode.')


def build_skycoord(coord: Tuple[float, float], mode: Type[Union[IAltAz, IRaDec]]) -> SkyCoord:
    """Build SkyCoord from x/y tuple in given mode.

    Args:
        coord: x/y tuple with coordinates in degrees.
        mode: IAltAz or IRaDec.

    Returns:
        SkyCoord with coordinates.
    """

    if mode == IAltAz:
        return SkyCoord(alt=coord[0] * u.deg, az=coord[1] * u.deg, frame='altaz')
    else:
        return SkyCoord(ra=coord[0] * u.deg, dec=coord[1] * u.deg, frame='icrs')


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
        self.__follow_device = device
        self.__follow_interval = interval
        self.__follow_tolerance = tolerance
        self.__follow_mode = mode

        # check
        if not isinstance(self, self.__follow_mode):
            raise ValueError('This module is not of given mode %s.' % mode)

        # add thread function only, if device is given
        if self.__follow_device is not None:
            if not isinstance(self, Module):
                raise ValueError('This is not a module.')
            self._add_thread_func(self.__update_follow)

    @property
    def is_following(self) -> bool:
        """Returns True, if we're following another device."""
        return self.__follow_device is not None

    def __update_follow(self):
        """Update function."""

        # I'm a module!
        self: Union[Module, FollowMixin]

        # wait a little
        self.closing.wait(10)

        # run until closing
        connected = None
        while not self.closing.is_set():
            # not ready?
            if isinstance(self, IReady):
                if not self.is_ready():
                    self.closing.wait(self.__follow_interval)
                    continue

            # get other device
            try:
                device = self.proxy(self.__follow_device, self.__follow_mode)
            except ValueError:
                # cannot follow, wait a little longer
                log.warning('Cannot follow module, since it is of wrong type.')
                self.closing.wait(self.__follow_interval * 10)
                continue

            # get coordinates from other and from myself
            try:
                my_coords = build_skycoord(get_coord(self, self.__follow_mode), self.__follow_mode)
                x, y = get_coord(device, self.__follow_mode).wait()
                other_coords = build_skycoord((x, y), self.__follow_mode)
                connected = True
            except (ValueError, RemoteException):
                if not connected:
                    log.error('Could not fetch coordinates.')
                connected = False
                self.closing.wait(self.__follow_interval * 10.)
                continue

            # is separation larger than tolerance?
            if my_coords.separation(other_coords).degree > self.__follow_tolerance:
                # move to other
                if self.__follow_mode == IAltAz:
                    self: IAltAz
                    threading.Thread(target=self.move_altaz, args=(x, y)).start()
                else:
                    self: IRaDec
                    threading.Thread(target=self.move_radec, args=(x, y)).start()

            # sleep a little
            self.closing.wait(self.__follow_interval)


__all__ = ['FollowMixin']
