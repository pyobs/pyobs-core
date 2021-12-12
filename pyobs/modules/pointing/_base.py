from typing import Union, List, Dict, Any
import logging

from pyobs.interfaces import ITelescope, ICamera
from pyobs.mixins.pipeline import PipelineMixin
from pyobs.object import get_object
from pyobs.utils.offsets import ApplyOffsets
from pyobs.modules import Module
from pyobs.images import ImageProcessor

log = logging.getLogger(__name__)


class BasePointing(Module, PipelineMixin):
    """Base class for guiding and acquisition modules."""
    __module__ = 'pyobs.modules.pointing'

    def __init__(self, camera: Union[str, ICamera], telescope: Union[str, ITelescope],
                 pipeline: List[Union[Dict[str, Any], ImageProcessor]], apply: Union[Dict[str, Any], ApplyOffsets],
                 **kwargs: Any):
        """Initializes a new base pointing.

        Args:
            telescope: Telescope to use.
            pipeline: Pipeline steps to run on new image. MUST include a step calculating offsets!
            apply: Object that handles applying offsets to telescope.
            log_file: Name of file to write log to.
            log_absolute: Log absolute offsets instead of relative ones to last one.
        """
        Module.__init__(self, **kwargs)
        PipelineMixin.__init__(self, pipeline)

        # store
        self._camera = camera
        self._telescope = telescope

        # apply offsets
        self._apply = get_object(apply, ApplyOffsets)

    async def open(self) -> None:
        """Open module."""
        await Module.open(self)

        # check telescope
        try:
            await self.proxy(self._telescope, ITelescope)
        except ValueError:
            log.warning('Given telescope does not exist or is not of correct type at the moment.')

        # check camera
        try:
            await self.proxy(self._camera, ICamera)
        except ValueError:
            log.warning('Given camera does not exist or is not of correct type at the moment.')


__all__ = ['BasePointing']
