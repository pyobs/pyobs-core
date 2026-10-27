from __future__ import annotations

import asyncio
import logging
from typing import Any

from pyobs.events import Event, FileWrittenEvent, NewImageEvent
from pyobs.modules import Module
from pyobs.utils.fits import format_filename

log = logging.getLogger(__name__)


class ImageWriter(Module):
    """Writes new images to disk.

    After an image has been written, a :class:`~pyobs.events.FileWrittenEvent` with the output filename is sent.
    """

    __module__ = "pyobs.modules.image"

    def __init__(self, filename: str = "/archive/{FNAME}", sources: str | list[str] | None = None, **kwargs: Any):
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
        self._queue = asyncio.Queue[str]()

    async def open(self) -> None:
        """Open image writer."""
        await Module.open(self)

        # subscribe to channel with new images
        if self._comm is not None:
            log.info("Subscribing to new image events...")
            await self.comm.register_event(NewImageEvent, self.process_new_image_event)
            await self.comm.register_event(FileWrittenEvent)

    async def process_new_image_event(self, event: Event, sender: str) -> bool:
        """Puts a new images in the DB with the given ID.

        Args:
            event:  New image event
            sender: Who sent the event?

        Returns:
            Success
        """
        if not isinstance(event, NewImageEvent):
            return False

        # filter by source
        if self._sources is not None and sender not in self._sources:
            return False

        # queue file
        log.info("Received new image event from %s.", sender)
        self._queue.put_nowait(event.filename)
        return True

    async def _worker(self) -> None:
        """Worker thread."""

        # run forever
        while True:
            # get next filename
            filename = await self._queue.get()

            try:
                # download image
                log.info("Downloading file %s...", filename)
                img = await self.vfs.read_image(filename)
            except FileNotFoundError:
                log.error("Could not download image.")
                continue

            # output filename
            try:
                output = format_filename(img.header, self._filename)
            except KeyError as e:
                log.error("Could not format filename: %s", e)
                continue

            try:
                # open output
                log.info("Storing image as %s...", output)
                await self.vfs.write_image(output, img)
            except Exception:
                log.error("Could not store image.")
            else:
                await self._send_file_written(output)

    async def _send_file_written(self, filename: str) -> None:
        """Send a FileWrittenEvent. A failure is only logged, the file has been written anyway.

        Args:
            filename: Name of the written file.
        """
        if self._comm is None:
            return
        try:
            await self.comm.send_event(FileWrittenEvent(filename))
        except Exception as e:
            log.warning("Could not send FileWrittenEvent for %s: %s", filename, e)


__all__ = ["ImageWriter"]
