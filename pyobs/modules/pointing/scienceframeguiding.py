import logging
import asyncio
from typing import Any

from pyobs.events import NewImageEvent
from pyobs.images import Image
from ._baseguiding import BaseGuiding
from ...utils.parallel import event_wait

log = logging.getLogger(__name__)


class ScienceFrameAutoGuiding(BaseGuiding):
    """An auto-guiding system based on comparing collapsed images along the x&y axes with a reference image."""
    __module__ = 'pyobs.modules.guiding'

    def __init__(self, **kwargs: Any):
        """Initializes a new science frame auto guiding system."""
        BaseGuiding.__init__(self, **kwargs)

        # add thread func
        self.add_background_task(self._auto_guiding, True)

        # variables
        self._next_image: asyncio.Queue[Image] = asyncio.Queue()

    async def open(self):
        """Open module."""
        await BaseGuiding.open(self)

        # subscribe to channel with new images
        log.info('Subscribing to new image events...')
        await self.comm.register_event(NewImageEvent, self.add_image)

    def set_exposure_time(self, exposure_time: float, **kwargs: Any):
        """Set the exposure time for the auto-guider.

        Args:
            exposure_time: Exposure time in secs.
        """
        raise NotImplementedError

    async def add_image(self, event: NewImageEvent, sender: str, **kwargs: Any):
        """Processes an image asynchronously, returns immediately.

        Args:
            event: Event for new image.
            sender: Name of sender.
        """

        # did it come from correct camera and are we enabled?
        if sender != self._camera or not self._enabled:
            return
        log.info('Received new image.')

        # download image
        image = await self.vfs.read_image(event.filename)

        # we only accept OBJECT images
        if image.header['IMAGETYP'] != 'object':
            return

        # do we have a filename in here already?
        if not self._next_image.empty():
            log.warning('Last image still being processed by auto-guiding, skipping new one.')
            return

        # store it
        await self._next_image.put(image)

    async def _auto_guiding(self):
        """the thread function for processing the images"""

        # run until closed
        while not self.closing.is_set():
            # get next image to process
            image = await self._next_image.get()

            # process it
            await self._process_image(image)

            # wait for next image
            await event_wait(self.closing, 1)


__all__ = ['ScienceFrameAutoGuiding']
