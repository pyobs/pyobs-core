import logging
import os
import shutil
from queue import Queue

from pyobs import PyObsModule
from pyobs.events import NewImageEvent

log = logging.getLogger(__name__)


class NewImageWriter(PyObsModule):
    """Writes new images to disk."""

    def __init__(self, new_images_channel: str = 'new_images', root: str = None, *args, **kwargs):
        """Creates a new image writer.

        Args:
            new_images_channel: Name of new images channel.
            root: VFS root to write files to.
        """
        PyObsModule.__init__(self, thread_funcs=self._worker, *args, **kwargs)

        # variables
        self._new_images_channel = new_images_channel
        self._root = root
        self._queue = Queue()

    def open(self):
        """Open image writer."""
        PyObsModule.open(self)

        # subscribe to channel with new images
        if self._new_images_channel:
            log.info('Subscribing to new image events...')
            self.comm.register_event(NewImageEvent, self.process_new_image_event)

    def process_new_image_event(self, event: NewImageEvent, sender: str, *args, **kwargs):
        """Puts a new images in the DB with the given ID.

        Args:
            event:  New image event
            sender: Who sent the event?

        Returns:
            Success
        """
        log.info('Received new image event from %s.', sender)
        self._queue.put(event.filename)

    def _worker(self):
        """Worker thread."""

        # run forever
        while not self.closing.is_set():
            # get next filename
            if self._queue.empty():
                self.closing.wait(1)
                continue
            filename = self._queue.get()
            log.info('Working on file %s...', filename)

            # download image
            try:
                # output filename
                output = os.path.join(self._root, os.path.basename(filename))

                # open input/output
                log.info('Downloading image from %s and storing it as %s...', filename, output)
                with self.open_file(output, 'wb') as fout:
                    with self.open_file(filename, 'rb') as fin:
                        shutil.copyfileobj(fin, fout)

            except FileNotFoundError:
                log.error('Could not download image.')
                return None


__all__ = ['NewImageWriter']
