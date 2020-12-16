import logging
import threading

from pyobs.events import NewImageEvent
from pyobs.utils.images import Image
from .base import BaseGuiding


log = logging.getLogger(__name__)


class ScienceFrameAutoGuiding(BaseGuiding):
    """An auto-guiding system based on comparing collapsed images along the x&y axes with a reference image."""

    def __init__(self, *args, **kwargs):
        """Initializes a new science frame auto guiding system."""
        BaseGuiding.__init__(self, *args, **kwargs)

        # add thread func
        self._add_thread_func(self._auto_guiding, True)

        # variables
        self._next_image: Image = None
        self._lock = threading.Lock()

    def open(self):
        """Open module."""
        BaseGuiding.open(self)

        # subscribe to channel with new images
        log.info('Subscribing to new image events...')
        self.comm.register_event(NewImageEvent, self.add_image)

    def set_exposure_time(self, exposure_time: float, *args, **kwargs):
        """Set the exposure time for the auto-guider.

        Args:
            exposure_time: Exposure time in secs.
        """
        raise NotImplementedError

    def add_image(self, event: NewImageEvent, sender: str, *args, **kwargs):
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
        image = self.vfs.read_image(event.filename)

        # we only accept OBJECT images
        if image.header['IMAGETYP'] != 'object':
            return

        # store filename as next image to process
        with self._lock:
            # do we have a filename in here already?
            if self._next_image:
                log.warning('Last image still being processed by auto-guiding, skipping new one.')
                return

            # store it
            self._next_image = image

    def _auto_guiding(self):
        """the thread function for processing the images"""

        # run until closed
        while not self.closing.is_set():
            # get next image to process
            with self._lock:
                image = self._next_image

            # got one?
            if image is not None:
                # process it
                self._process_image(image)

                # image finished
                with self._lock:
                    self._next_image = None

            # wait for next image
            self.closing.wait(0.1)


__all__ = ['ScienceFrameAutoGuiding']
