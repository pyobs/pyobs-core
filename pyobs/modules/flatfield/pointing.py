import logging
import typing

from pyobs.interfaces import ITelescope, IRunnable
from pyobs import PyObsModule, get_object
from pyobs.utils.skyflats.pointing.base import SkyFlatsBasePointing

log = logging.getLogger(__name__)


class FlatFieldPointing(PyObsModule, IRunnable):
    """Module for pointing a telescope."""

    def __init__(self, telescope: typing.Union[str, ITelescope], pointing: typing.Union[dict, SkyFlatsBasePointing],
                 *args, **kwargs):
        """Initialize a new flat field pointing.

        Args:
            telescope: Telescope to point
            pointing: Pointing for calculating coordinates.
        """
        PyObsModule.__init__(self, *args, **kwargs)

        # store telescope
        self._telescope = telescope

        # pointing
        self._pointing = get_object(pointing, SkyFlatsBasePointing, observer=self.observer)

    def run(self, *args, **kwargs):
        """Move telescope to pointing."""

        # get telescope
        log.info('Getting proxy for telescope...')
        telescope: ITelescope = self.proxy(self._telescope, ITelescope)

        # point
        self._pointing(telescope).wait()
        log.info('Finished pointing telescope.')

    def abort(self, *args, **kwargs):
        """Abort current actions."""
        pass


__all__ = ['FlatFieldPointing']
