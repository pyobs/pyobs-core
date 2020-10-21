from __future__ import annotations
from collections import OrderedDict
from astropy.coordinates import SkyCoord
import astropy.units as u
from astropy.time import Time
from typing import Union
from photutils.datasets import make_gaussian_prf_sources_image, make_random_models_table
from photutils.datasets import make_noise_image

from pyobs.object import create_object


class SimTelescope:
    """A simulated telescope on an equitorial mount."""
    def __init__(self, world: SimWorld, *args, **kwargs):
        self.world = world
        self.position = SkyCoord(0. * u.deg, 0. * u.deg, frame='icrs')
        self.offsets = (0., 0.)
        self.focus = 52.
        self.filters = ['clear', 'B', 'V', 'R']
        self.filter = 'clear'


class SimCamera:
    """A simulated camera."""
    def __init__(self, world: SimWorld, *args, **kwargs):
        self.world = world
        self.full_frame = (0, 0, 512, 512)
        self.window = tuple(self.full_frame)
        self.binning = (1, 1)

    def get_image(self, exp_time: float, open_shutter: bool):
        """Simulate an image.

        Args:
            exp_time: Exposure time in ms.
            open_shutter: Whether the shutter is opened.

        Returns:
            numpy array with image.
        """

        # get shape for image
        shape = (int(self.window[3]), int(self.window[2]))

        # create image with Gaussian noise for BIAS
        image = make_noise_image(shape, distribution='gaussian', mean=1000., stddev=10.)

        # add DARK
        if exp_time > 0:
            image += make_noise_image(shape, distribution='gaussian', mean=exp_time / 100., stddev=10.)

        # add stars
        if open_shutter:
            # create random table with sources
            n_sources = 50
            param_ranges = [('amplitude', [1000, 20000]),
                            ('x_0', [0, self.window[3]]),
                            ('y_0', [0, self.window[2]]),
                            ('sigma', [2. / self.binning[0], 2.2 / self.binning[0]])]
            param_ranges = OrderedDict(param_ranges)
            sources = make_random_models_table(n_sources, param_ranges, seed=0)

            # add image
            image += make_gaussian_prf_sources_image(shape, sources)

        # return it
        return image


class SimWorld:
    """A simulated world."""

    def __init__(self, time: Union[Time, str] = None,
                 telescope: Union[SimTelescope, dict] = None, camera: Union[SimCamera, dict] = None,
                 *args, **kwargs):
        """Initializes a new simulated world.

        Args:
            time: Time at start of simulation.
            telescope: Telescope to use.
            camera: Camera to use.
            *args:
            **kwargs:
        """

        time = '2020-08-10 20:12:00'
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
            self.camera = telescope
        elif isinstance(camera, dict):
            self.camera = create_object(camera, world=self)
        else:
            raise ValueError('Invalid camera.')

    @property
    def time(self):
        """Returns current time in simulation."""
        return Time.now() + self.time_offset


__all__ = ['SimTelescope', 'SimCamera', 'SimWorld']
