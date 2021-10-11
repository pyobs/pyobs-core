import logging

from pyobs.events import NewImageEvent
from pyobs.images.processor import ImageProcessor
from pyobs.images import Image


log = logging.getLogger(__name__)


class Broadcast(ImageProcessor):
    """Broadcast image."""
    __module__ = 'pyobs.images.processors.misc'

    def __init__(self, copy: bool = True, filename: str = '/cache/{FNAME}', *args, **kwargs):
        """Init an image processor that broadcasts an image

        Args:
            copy: If True, copy image to given filename before broadcasting.
            filename: New filename, only used if copy=True.
        """
        ImageProcessor.__init__(self, *args, **kwargs)

        # store
        self._copy = copy
        self._filename = filename

    def open(self):
        """Initialize processor."""
        ImageProcessor.open(self)

        # register event
        if self.comm is not None:
            self.comm.register_event(NewImageEvent)

    def __call__(self, image: Image) -> Image:
        """Broadcast image.

        Args:
            image: Image to broadcast.

        Returns:
            Original image.
        """
        pass


__all__ = ['Broadcast']

