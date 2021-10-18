from typing import Union, List
import logging

from pyobs.mixins.pipeline import PipelineMixin
from pyobs.object import get_object
from pyobs.utils.offsets import ApplyOffsets
from pyobs.interfaces import ITelescope, ICamera
from pyobs.modules import Module
from pyobs.images import ImageProcessor

log = logging.getLogger(__name__)


class BasePointing(Module, PipelineMixin):
    """Base class for guiding and acquisition modules."""
    __module__ = 'pyobs.modules.pointing'

    def __init__(self, camera: Union[str, ICamera], telescope: Union[str, ITelescope],
                 pipeline: List[Union[dict, ImageProcessor]], apply: Union[dict, ApplyOffsets],
                 *args, **kwargs):
        """Initializes a new base pointing.

        Args:
            telescope: Telescope to use.
            pipeline: Pipeline steps to run on new image. MUST include a step calculating offsets!
            apply: Object that handles applying offsets to telescope.
        """
        Module.__init__(self, *args, **kwargs)
        PipelineMixin.__init__(self, pipeline)

        # store
        self._camera = camera
        self._telescope = telescope

        # apply offsets
        self._apply = get_object(apply, ApplyOffsets)

    def open(self):
        """Open module."""
        Module.open(self)

        # check telescope
        try:
            self.proxy(self._telescope, ITelescope)
        except ValueError:
            log.warning('Given telescope does not exist or is not of correct type at the moment.')

        # check camera
        try:
            self.proxy(self._camera, ICamera)
        except ValueError:
            log.warning('Given camera does not exist or is not of correct type at the moment.')


__all__ = ['BasePointing']
