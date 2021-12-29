import logging
import asyncio
from typing import Any

from pyobs.events import NewImageEvent, Event
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

    async def open(self) -> None:
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

    async def add_image(self, event: Event, sender: str, **kwargs: Any) -> bool:
        """Processes an image asynchronously, returns immediately.

        Args:
            event: Event for new image.
            sender: Name of sender.
        """

        # did it come from correct camera and are we enabled?
        if sender != self._camera or not self._enabled or not isinstance(event, NewImageEvent):
            return False
        log.info('Received new image.')

        # download image
        image = await self.vfs.read_image(event.filename)

        # we only accept OBJECT images
        if image.header['IMAGETYP'] != 'object':
            return False

        # do we have a filename in here already?
        if not self._next_image.empty():
            log.warning('Last image still being processed by auto-guiding, skipping new one.')
            return False

        # store it
        await self._next_image.put(image)
        return True

    async def _auto_guiding(self) -> None:
        """the thread function for processing the images"""

        # run until closed
        while True:
            # get next image to process
            image = await self._next_image.get()

            # process it
            await self._process_image(image)

            # wait for next image
            await asyncio.sleep(1)


__all__ = ['ScienceFrameAutoGuiding']
