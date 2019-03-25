import logging
import os
import shutil
from queue import Queue

from pyobs import PyObsModule
from pyobs.events import NewImageEvent
from pyobs.utils.fits import format_filename

log = logging.getLogger(__name__)


class NewImageWriter(PyObsModule):
    """Writes new images to disk."""

    def __init__(self, new_images_channel: str = 'new_images', root: str = None, filenames: str = None,
                 *args, **kwargs):
        """Creates a new image writer.

        Args:
            new_images_channel: Name of new images channel.
            root: VFS root to write files to.
            filenames: If not None, create new filename from this pattern.
        """
        PyObsModule.__init__(self, thread_funcs=self._worker, *args, **kwargs)

        # variables
        self._new_images_channel = new_images_channel
        self._filenames = filenames
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

            try:
                # download image
                log.info('Downloading file %s...', filename)
                hdu = self.vfs.download_fits_image(filename)
            except FileNotFoundError:
                log.error('Could not download image.')
                continue

            # output filename
            output = filename
            if self._filenames:
                try:
                    output = format_filename(hdu, self._filenames, self.environment, filename)
                except KeyError as e:
                    log.error('Could not format filename: %s', e)
                    continue

            # add path to output filename
            output = os.path.join(self._root, os.path.basename(output))

            try:
                # open output
                log.info('Storing image as %s...',  output)
                with self.open_file(output, 'wb') as fout:
                    hdu.writeto(fout)
            except Exception:
                log.error('Could not store image.')


__all__ = ['NewImageWriter']
