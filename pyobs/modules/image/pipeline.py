import asyncio
import logging
from typing import Any

from pyobs.images import ImageProcessor, Image
from pyobs.mixins.pipeline import PipelineMixin
from pyobs.modules import Module
from pyobs.events import NewImageEvent, Event

log = logging.getLogger(__name__)


class Pipeline(Module, PipelineMixin):
    """Runs an image pipeline."""

    __module__ = "pyobs.modules.image"

    def __init__(
        self,
        pipeline: list[dict[str, Any] | ImageProcessor],
        sources: str | list[str] | None = None,
        interval: int | None = None,
        **kwargs: Any,
    ):
        """Creates a new HTTP publisher for images.

        Args:
            pipeline: Pipeline to run on images.
            sources: List of sources to process images from.
            interval: Interval in seconds for automatic run of pipeline.
        """
        Module.__init__(self, **kwargs)
        PipelineMixin.__init__(self, pipeline)

        # only allow one option!
        if (sources is not None and interval is not None) or (sources is None and interval is None):
            raise ValueError("Either source(s) or interval must be provided, not both.")

        # stuff
        self._sources = [sources] if isinstance(sources, str) else sources
        self._interval = interval

        # background task
        self.add_background_task(self._interval_processing)

    async def open(self) -> None:
        """Open module."""

        # interval?
        if self._interval is not None:
            log.info("Starting interval for image processing...")

        await Module.open(self)

        # subscribe to channel with new images
        if self._sources is not None:
            log.info("Subscribing to new image events...")
            await self.comm.register_event(NewImageEvent, self.process_new_image_event)

    async def _interval_processing(self) -> None:
        while True:
            try:
                if self._interval is not None:
                    image = Image()
                    await self.run_pipeline(image)
            except:
                log.exception("Error in pipeline:")
            await asyncio.sleep(1 if self._interval is None else self._interval)

    async def process_new_image_event(self, event: Event, sender: str) -> bool:
        """Runs a new image through the pipeline.

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

        # put into queue
        log.info("Received new image event from %s.", sender)

        # download image
        try:
            log.info("Downloading file %s...", event.filename)
            image = await self.vfs.read_image(event.filename)

        except FileNotFoundError:
            log.error("Could not download image.")
            return False

        # run it in pipeline
        await self.run_pipeline(image)
        return True


__all__ = ["Pipeline"]
