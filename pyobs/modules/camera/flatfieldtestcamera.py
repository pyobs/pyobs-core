import logging
from astropy.io import fits

from pyobs.modules.camera import DummyCamera
from pyobs.utils.time import Time

log = logging.getLogger(__name__)


class FlatFieldTestCamera(DummyCamera):
    """A dummy camera for testing."""

    def __init__(self, *args, **kwargs):
        """Creates a new test cammera for flat fielding."""
        DummyCamera.__init__(self, *args, **kwargs)

    def _get_image(self) -> fits.PrimaryHDU:
        """Actually get (i.e. simulate) the image."""

        # get current time
        time = Time.now()

        # get altitude of sun


__all__ = ['FlatFieldTestCamera']
