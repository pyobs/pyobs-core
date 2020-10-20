from astropy.coordinates import SkyCoord
import astropy.units as u
from typing import Union

from pyobs.object import create_object


class SimTelescope:
    """A simulated telescope on an equitorial mount."""
    def __init__(self, *args, **kwargs):
        self.position = SkyCoord(0. * u.deg, 0. * u.deg, frame='icrs')
        self.offsets = (0., 0.)
        self.focus = 52.
        self.filter = 'V'


class SimCamera:
    """A simulated camera."""
    def __init__(self, *args, **kwargs):
        pass


class SimWorld:
    """A simulated world."""

    def __init__(self, telescope: Union[SimTelescope, dict] = None, camera: Union[SimCamera, dict] = None,
                 *args, **kwargs):

        # get telescope
        if telescope is None:
            self.telescope = SimTelescope()
        elif isinstance(telescope, SimTelescope):
            self.telescope = telescope
        elif isinstance(telescope, dict):
            self.telescope = create_object(telescope)
        else:
            raise ValueError('Invalid telescope.')

        # get camera
        if camera is None:
            self.camera = SimCamera()
        elif isinstance(camera, SimCamera):
            self.camera = telescope
        elif isinstance(camera, dict):
            self.camera = create_object(camera)
        else:
            raise ValueError('Invalid camera.')


__all__ = ['SimTelescope', 'SimCamera', 'SimWorld']
