import asyncio
import logging
from typing import Union, Tuple, Type, Optional, Any
from astropy.coordinates import SkyCoord
import astropy.units as u

from pyobs.comm.exceptions import RemoteException
from pyobs.modules import Module
from pyobs.interfaces import IPointingAltAz, IPointingRaDec, IReady


log = logging.getLogger(__name__)


async def get_coords(obj: Union[IPointingAltAz, IPointingRaDec], mode: Type[Union[IPointingAltAz, IPointingRaDec]]) \
        -> Tuple[float, float]:
    """Gets coordinates from object

    Args:
        obj: Object to fetch coordinates from.
        mode: IAltAz or IRaDec.

    Returns:
        Return from method call.
    """

    if mode == IPointingAltAz and isinstance(obj, IPointingAltAz):
        return await obj.get_altaz()
    elif mode == IPointingRaDec and isinstance(obj, IPointingRaDec):
        return await obj.get_radec()
    else:
        raise ValueError('Unknown mode.')


def build_skycoord(coord: Tuple[float, float], mode: Type[Union[IPointingAltAz, IPointingRaDec]]) -> SkyCoord:
    """Build SkyCoord from x/y tuple in given mode.

    Args:
        coord: x/y tuple with coordinates in degrees.
        mode: IAltAz or IRaDec.

    Returns:
        SkyCoord with coordinates.
    """

    if mode == IPointingAltAz:
        return SkyCoord(alt=coord[0] * u.deg, az=coord[1] * u.deg, frame='altaz')
    else:
        return SkyCoord(ra=coord[0] * u.deg, dec=coord[1] * u.deg, frame='icrs')


class FollowMixin:
    """Mixin for a device that should follow the motion of another."""
    __module__ = 'pyobs.mixins'

    def __init__(self, device: Optional[str], mode: Type[Union[IPointingAltAz, IPointingRaDec]],
                 interval: float = 10, tolerance: float = 1, only_follow_when_ready: bool = True,
                 *args: Any, **kwargs: Any):
        """Initializes the mixin.

        Args:
            device: Name of device to follow
            interval: Interval in seconds between position checks.
            tolerance: Tolerance in degrees between both devices to trigger new movement.
            mode: Set to "altaz" to follow Alt/Az coordinates or "radec" to follow RA/Dec.
            only_follow_when_ready: Only follow if is_ready() is True.
        """

        # store
        self.__follow_device = device
        self.__follow_interval = interval
        self.__follow_tolerance = tolerance
        self.__follow_mode = mode
        self.__follow_only_when_ready = only_follow_when_ready

        # store self for later
        this = self

        # add thread function only, if device is given
        if self.__follow_device is not None:
            if not isinstance(self, Module):
                raise ValueError('This is not a module.')
            self.add_background_task(this.__update_follow)

        # check
        if not isinstance(self, self.__follow_mode):
            raise ValueError('This module is not of given mode %s.' % mode)

    @property
    def is_following(self) -> bool:
        """Returns True, if we're following another device."""
        return self.__follow_device is not None

    async def __update_follow(self) -> None:
        """Update function."""

        # store self for later
        this = self
        if not isinstance(self, Module):
            raise ValueError('Not a module.')
        module = self

        # wait a little
        await asyncio.sleep(10)

        # run until closing
        connected = True
        while not module.closing.is_set():
            # not ready?
            if isinstance(self, IReady):
                if not await self.is_ready() and this.__follow_only_when_ready:
                    await asyncio.sleep(this.__follow_interval)
                    continue

            # get other device
            try:
                device = await module.proxy(this.__follow_device, this.__follow_mode)
            except ValueError:
                # cannot follow, wait a little longer
                log.warning('Cannot follow module, since it is of wrong type.')
                await asyncio.sleep(this.__follow_interval * 10)
                continue

            # get coordinates from other and from myself
            try:
                my_coords = build_skycoord(await get_coords(module, this.__follow_mode), this.__follow_mode)
                xy_coords = await get_coords(device, this.__follow_mode)
                if xy_coords is None:
                    continue
                other_coords = build_skycoord(xy_coords, this.__follow_mode)
                connected = True
            except (ValueError, RemoteException):
                if connected:
                    log.warning('Could not fetch coordinates.')
                connected = False
                await asyncio.sleep(this.__follow_interval * 10.)
                continue

            # is separation larger than tolerance?
            if my_coords.separation(other_coords).degree > this.__follow_tolerance:
                # move to other
                if this.__follow_mode == IPointingAltAz and isinstance(self, IPointingAltAz):
                    asyncio.create_task(self.move_altaz(*xy_coords))
                elif this.__follow_mode == IPointingRaDec and isinstance(self, IPointingRaDec):
                    asyncio.create_task(self.move_radec(*xy_coords))
                else:
                    raise ValueError('invalid follow mode.')

            # sleep a little
            await asyncio.sleep(this.__follow_interval)


__all__ = ['FollowMixin']
