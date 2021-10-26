from __future__ import annotations

from astropy.time import Time
from typing import Union, Optional, TYPE_CHECKING, Dict, Any

from pyobs.object import create_object, Object
if TYPE_CHECKING:
    from pyobs.utils.simulation.telescope import SimTelescope
    from pyobs.utils.simulation.camera import SimCamera


class SimWorld(Object):
    """A simulated world."""
    __module__ = 'pyobs.utils.simulation'

    def __init__(self, time: Optional[Union[Time, str]] = None,
                 telescope: Optional[Union['SimTelescope', Dict[str, Any]]] = None,
                 camera: Optional[Union['SimCamera', Dict[str, Any]]] = None,
                 **kwargs: Any):
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
        Object.__init__(self, **kwargs)

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

    def open(self) -> None:
        """Open module."""
        Object.open(self)

        # open telescope
        if hasattr(self.telescope, 'open'):
            self.telescope.open()

        # open camera
        if hasattr(self.telescope, 'open'):
            self.camera.open()

    def close(self) -> None:
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
        if self.observer is None:
            raise ValueError('No observer given.')
        return float(self.observer.sun_altaz(self.time).alt.degree)


__all__ = ['SimWorld']
