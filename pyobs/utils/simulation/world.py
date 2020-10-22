from __future__ import annotations
from collections import OrderedDict
import numpy as np
from astropy.coordinates import SkyCoord
import astropy.units as u
from astropy.time import Time
from typing import Union
from photutils.datasets import make_gaussian_prf_sources_image, make_random_models_table
from photutils.datasets import make_noise_image

from pyobs import Module
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

            # add stars and stuff
            if open_shutter:
                # get solar altitude
                sun_alt = self.world.sun_alt

                # get mean flatfield counts
                flat_counts = 30000 / np.exp(-1.28 * (4.209 + sun_alt)) * exp_time / 1000.

                # create flat
                image += make_noise_image(shape, distribution='gaussian', mean=flat_counts, stddev=flat_counts / 10.)

                # create random table with sources
                n_sources = 50
                param_ranges = [('amplitude', [1000, 20000]),
                                ('x_0', [0, self.window[3]]),
                                ('y_0', [0, self.window[2]]),
                                ('sigma', [2. / self.binning[0], 2.2 / self.binning[0]])]
                param_ranges = OrderedDict(param_ranges)
                sources = make_random_models_table(n_sources, param_ranges, seed=0)

                # create image
                image += make_gaussian_prf_sources_image(shape, sources)

        # saturate
        image[image > 65535] = 65535

        # return it
        return image


class SimWorld(Module):
    """A simulated world."""

    def __init__(self, time: Union[Time, str] = None,
                 telescope: Union[SimTelescope, dict] = None, camera: Union[SimCamera, dict] = None,
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
        Module.__init__(self, *args, **kwargs)

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
    def time(self) -> Time:
        """Returns current time in simulation."""
        return Time.now() + self.time_offset

    @property
    def sun_alt(self) -> float:
        """Returns current solar altitude."""
        return float(self.observer.sun_altaz(self.time).alt.degree)




__all__ = ['SimTelescope', 'SimCamera', 'SimWorld']
