import logging
from typing import Union, Dict, Any

from pyobs.interfaces import IRunnable
from pyobs.interfaces.proxies import ITelescopeProxy
from pyobs.modules import Module
from pyobs.object import get_object
from pyobs.modules import timeout
from pyobs.utils.skyflats.pointing.base import SkyFlatsBasePointing

log = logging.getLogger(__name__)


class FlatFieldPointing(Module, IRunnable):
    """Module for pointing a telescope."""
    __module__ = 'pyobs.modules.flatfield'

    def __init__(self, telescope: Union[str, ITelescopeProxy],
                 pointing: Union[Dict[str, Any], SkyFlatsBasePointing], **kwargs: Any):
        """Initialize a new flat field pointing.

        Args:
            telescope: Telescope to point
            pointing: Pointing for calculating coordinates.
        """
        Module.__init__(self, **kwargs)

        # store telescope and pointing
        self._telescope = telescope
        self._pointing = pointing

    @timeout(60)
    def run(self, **kwargs: Any):
        """Move telescope to pointing."""

        # get telescope
        log.info('Getting proxy for telescope...')
        telescope: ITelescopeProxy = self.proxy(self._telescope, ITelescopeProxy)

        # pointing
        pointing = get_object(self._pointing, SkyFlatsBasePointing, observer=self.observer)

        # point
        pointing(telescope).wait()
        log.info('Finished pointing telescope.')

    def abort(self, **kwargs: Any):
        """Abort current actions."""
        pass


__all__ = ['FlatFieldPointing']
