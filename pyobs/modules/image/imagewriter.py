import logging
import asyncio
from typing import Union, List, Any, Optional

from pyobs.modules import Module
from pyobs.events import NewImageEvent
from pyobs.utils.fits import format_filename

log = logging.getLogger(__name__)


class ImageWriter(Module):
    """Writes new images to disk."""
    __module__ = 'pyobs.modules.image'

    def __init__(self, filename: str = '/archive/{FNAME}', sources: Optional[Union[str, List[str]]] = None,
                 **kwargs: Any):
        """Creates a new image writer.

        Args:
            filename: Pattern for filename to store images at.
            sources: List of sources (e.g. cameras) to process images from or None for all.
        """
        Module.__init__(self, **kwargs)

        # add thread func
        self.add_background_task(self._worker, True)

        # variables
        self._filename = filename
        self._sources = [sources] if isinstance(sources, str) else sources
        self._queue = asyncio.Queue()

    async def open(self) -> None:
        """Open image writer."""
        await Module.open(self)

        # subscribe to channel with new images
        if self.comm is not None:
            log.info('Subscribing to new image events...')
            await self.comm.register_event(NewImageEvent, self.process_new_image_event)

    def process_new_image_event(self, event: NewImageEvent, sender: str) -> bool:
        """Puts a new images in the DB with the given ID.

        Args:
            event:  New image event
            sender: Who sent the event?

        Returns:
            Success
        """

        # filter by source
        if self._sources is not None and sender not in self._sources:
            return False

        # queue file
        log.info('Received new image event from %s.', sender)
        self._queue.put_nowait(event.filename)
        return True

    async def _worker(self) -> None:
        """Worker thread."""

        # run forever
        while not self.closing.is_set():
            # get next filename
            filename = await self._queue.get()

            try:
                # download image
                log.info('Downloading file %s...', filename)
                img = self.vfs.read_image(filename)
            except FileNotFoundError:
                log.error('Could not download image.')
                continue

            # output filename
            try:
                output = format_filename(img.header, self._filename)
            except KeyError as e:
                log.error('Could not format filename: %s', e)
                continue

            try:
                # open output
                log.info('Storing image as %s...',  output)
                self.vfs.write_image(output, img)
            except Exception:
                log.error('Could not store image.')


__all__ = ['ImageWriter']
