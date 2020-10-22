import logging
import typing

from pyobs.interfaces import ITelescope, IRunnable
from pyobs import Module, get_object
from pyobs.modules import timeout
from pyobs.utils.skyflats.pointing.base import SkyFlatsBasePointing

log = logging.getLogger(__name__)


class FlatFieldPointing(Module, IRunnable):
    """Module for pointing a telescope."""

    def __init__(self, telescope: typing.Union[str, ITelescope], pointing: typing.Union[dict, SkyFlatsBasePointing],
                 *args, **kwargs):
        """Initialize a new flat field pointing.

        Args:
            telescope: Telescope to point
            pointing: Pointing for calculating coordinates.
        """
        Module.__init__(self, *args, **kwargs)

        # store telescope and pointing
        self._telescope = telescope
        self._pointing = pointing

    @timeout(60000)
    def run(self, *args, **kwargs):
        """Move telescope to pointing."""

        # get telescope
        log.info('Getting proxy for telescope...')
        telescope: ITelescope = self.proxy(self._telescope, ITelescope)

        # pointing
        pointing = get_object(self._pointing, SkyFlatsBasePointing, observer=self.observer)

        # point
        pointing(telescope).wait()
        log.info('Finished pointing telescope.')

    def abort(self, *args, **kwargs):
        """Abort current actions."""
        pass


__all__ = ['FlatFieldPointing']
