import logging
from astropy.io import fits
import numpy as np

from pyobs.modules.camera import DummyCamera
from pyobs.utils.time import Time

log = logging.getLogger(__name__)


class FlatFieldTestCamera(DummyCamera):
    """A dummy camera for testing."""

    def __init__(self, bias: float = 1000, noise: float = 10, radius: float = 5000,
                 A: float = -1.32411, B: float = 3.943923, *args, **kwargs):
        """Creates a new test cammera for flat fielding.

        Args:
            bias: Bias level for images.
            noise: Noise level in image.
            radius: Radius in pixel at which the counts drop to zero.
            A, B: Exposure time for 30,000 counts as exp(A*(alt+B)), where alt is the altitude of the sun.
        """
        DummyCamera.__init__(self, *args, **kwargs)

        self.bias = bias
        self.noise = noise
        self.radius = radius
        self.exp_time = lambda alt: np.exp(A * (alt + B))

    def _get_image(self, exp_time: float) -> fits.PrimaryHDU:
        """Actually get (i.e. simulate) the image."""

        # get current time
        time = Time.now()

        # image size
        wnd = self.get_window()
        width, height = int(wnd[2] / self._binning[0]), int(wnd[3] / self._binning[1])

        # sim radial profile, normed to one
        data = np.array([[1. - np.sqrt((x - width / 2)**2 + (y - height / 2)**2) / self.radius
                          for x in range(width)] for y in range(height)])
        data /= np.mean(data)

        # get altitude of sun
        sun = self.observer.sun_altaz(time)

        # calculate exp time required for getting 30,000 counts
        exp_time_30000 = self.exp_time(sun.alt.degree)      # in seconds, while exp_time is in ms!

        # get expected count level
        expected_counts = (30000 - self.bias) / exp_time_30000 * (exp_time / 1000)
        print(expected_counts)

        # and scale
        data *= expected_counts

        # add bias
        data += np.random.normal(self.bias, self.noise, data.shape)

        # return HDU
        return fits.PrimaryHDU(data.astype('uint16'))
        #return fits.PrimaryHDU(data)


__all__ = ['FlatFieldTestCamera']
