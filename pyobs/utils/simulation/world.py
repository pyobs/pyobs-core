from collections import OrderedDict

from astropy.coordinates import SkyCoord
import astropy.units as u
from typing import Union
import numpy as np

from astropy.table import Table
from photutils.datasets import make_gaussian_prf_sources_image, make_random_models_table
from photutils.datasets import make_noise_image

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
