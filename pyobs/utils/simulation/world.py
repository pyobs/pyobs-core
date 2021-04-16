from __future__ import annotations

from astropy.time import Time
from typing import Union

from pyobs.object import create_object, Object


class SimWorld(Object):
    """A simulated world."""
    ___module__ = 'pyobs.utils.simulation'

    def __init__(self, time: Union[Time, str] = None,
                 telescope: Union['SimTelescope', dict] = None, camera: Union['SimCamera', dict] = None,
                 *args, **kwargs):
        """Initializes a new simulated world.

        Args:
            time: Time at start of simulation.
            telescope: Telescope to use.
            camera: Camera to use.
            observer: Observer to use.
            *args:
            **kwargs:
        """
        from .camera import SimCamera
        from .telescope import SimTelescope
        Object.__init__(self, *args, **kwargs)

        # get start time
        if time is None:
            time = Time.now()
        elif isinstance(time, str):
            time = Time(time)

        # calculate time offset
        self.time_offset = time - Time.now()

        # get telescope
        if telescope is None:
            self.telescope = SimTelescope(world=self)
        elif isinstance(telescope, SimTelescope):
            self.telescope = telescope
        elif isinstance(telescope, dict):
            self.telescope = create_object(telescope, world=self)
        else:
            raise ValueError('Invalid telescope.')

        # get camera
        if camera is None:
            self.camera = SimCamera(world=self)
        elif isinstance(camera, SimCamera):
            self.camera = camera
        elif isinstance(camera, dict):
            self.camera = create_object(camera, world=self)
        else:
            raise ValueError('Invalid camera.')

    def open(self):
        """Open module."""
        Object.open(self)

        # open telescope
        if hasattr(self.telescope, 'open'):
            self.telescope.open()

        # open camera
        if hasattr(self.telescope, 'open'):
            self.camera.open()

    def close(self):
        """Close module."""
        Object.close(self)

        # close telescope
        if hasattr(self.telescope, 'close'):
            self.telescope.close()

        # close camera
        if hasattr(self.camera, 'close'):
            self.camera.close()

    @property
    def time(self) -> Time:
        """Returns current time in simulation."""
        return Time.now() + self.time_offset

    @property
    def sun_alt(self) -> float:
        """Returns current solar altitude."""
        return float(self.observer.sun_altaz(self.time).alt.degree)


__all__ = ['SimWorld']
