import glob
import logging
import os
from queue import Queue
import pyinotify
from astropy.io import fits

from pyobs import PyObsModule, get_object
from pyobs.interfaces import IImageDB
from pyobs.utils.fits import format_filename

log = logging.getLogger(__name__)


class NewImageWatcher(PyObsModule):
    """Watch for new images and add them to an ImageDB."""

    def __init__(self, watchpath: str = None, imagedb: str = 'imagedb', copy: list = None,
                 *args, **kwargs):
        """Create a new image watcher.

        Args:
            watchpath: Path to watch.
            imagedb: The ImageDB to use.
            copy: If given, copy the file to the given location(s).
        """
        PyObsModule.__init__(self, thread_funcs=self._worker, *args, **kwargs)

        # variables
        self._watchpath = watchpath
        self._imagedb = get_object(imagedb)
        self._copy_to = [] if copy is None else copy
        self._observer = None
        self._queue = Queue()

        # make a list of copy targets
        if isinstance(self._copy_to, str):
            self._copy_to = [self._copy_to]

    def open(self):
        """Open module."""
        PyObsModule.open(self)

        # start watching directory
        if self._watchpath:
            log.info('Start watching directory %s for changes...', self._watchpath)
            wm = pyinotify.WatchManager()
            wm.add_watch(self._watchpath, pyinotify.IN_CLOSE_WRITE)
            self._observer = pyinotify.ThreadedNotifier(wm, default_proc_fun=EventHandler(self)) #, name='observer')
            self._observer.start()

    def close(self):
        """Close image watcher."""
        PyObsModule.close(self)

        # stop watching
        if self._observer:
            log.info('Stop watching directory...')
            self._observer.stop()

    def add_image(self, filename: str):
        """Add an image to the image database.

        Args:
            filename (str): Local filename of new image.
        """

        # log file
        log.info('Adding new image %s...', filename)
        self._queue.put(filename)

    def _clear_queue(self):
        """Clear the queue with new files."""

        # clear queue
        with self._queue.mutex:
            self._queue.queue.clear()

    def _worker(self):
        """Worker thread."""

        # first, add all files from directory to queue
        self._clear_queue()
        for filename in sorted(glob.glob(os.path.join(self._watchpath, '*'))):
            self.add_image(filename)

        # run forever
        while not self.closing.is_set():
            # get next filename
            if self._queue.empty():
                self.closing.wait(1)
                continue
            filename = self._queue.get()
            log.info('Working on file %s...', filename)

            # better safe than sorry
            try:
                # get imagedb
                log.info('Getting proxy for imagedb...')
                imagedb = self.comm[self._imagedb]
                if not isinstance(imagedb, IImageDB):
                    log.error('Given imagedb is not of type IImageDB, aborting.')
                    self.closing.wait(10)
                    continue

                # open file
                log.info('Opening file...')
                fits_file = fits.open(filename)

                # call before_add hook
                if not self.before_add(filename, fits_file):
                    log.warning('Could not prepare FITS file.')
                    continue

                # copy
                if not self._copy(filename, fits_file):
                    log.warning('Could not copy file to at least one target.')
                    continue

                # send image to imagedb
                log.info('Sending file to image database...')
                archive_filename = imagedb.add_image(filename)

                # check result
                if archive_filename is not None:
                    log.info('Added image as %s.', archive_filename)
                else:
                    log.info('Failed to add image.')
                    continue

                # call after_add hook
                self.after_add(filename, archive_filename)

                # close and delete files
                log.info('Removing file from watch directory...')
                os.remove(filename)

            except:
                log.exception('Something went wrong.')

    def before_add(self, filename: str, fits_file) -> bool:
        """Hook for derived classed that is called directly before sending the file to the ImageDB.

        If False is returned, the file will not be added to the database.

        Args:
            filename: Name of file to add.
            fits_file: Opened FITS file.

        Returns:
            Whether or not to continue with this file.
        """
        return True

    def after_add(self, filename: str, archive: str):
        """Hook for derived classed that is called directly after sending the file to the ImageDB.

        Args:
            filename: Name of file to add.
            archive: Name of file in the archive.
        """
        pass

    def _copy(self, filename: str, fits_file) -> bool:
        """Copy given file to given storage.

        Args:
            filename: Filename of file to copy.
            fits_file: Opened FITS file.

        Returns:
            (bool) Success
        """

        # loop copy targets
        for target in self._copy_to:
            # format filename
            filename = format_filename(fits_file[0].header, target, filename=filename, environment=self.environment)
            print("formated %s to %s" % (target, filename))

            # open and write output file
            log.info('Copying file to %s...', filename)
            try:
                with self.open_file(filename, 'wb') as out:
                    fits_file.writeto(out)
                log.info('Copied successfully.')
            except:
                log.error('Error while copying file.')
                return False

        # success
        return True


class EventHandler(pyinotify.ProcessEvent):
    """Event handler for file watcher."""

    def __init__(self, main, *args, **kwargs):
        """Create event handler."""
        pyinotify.ProcessEvent.__init__(self, *args, **kwargs)
        self.main = main

    def process_IN_CLOSE_WRITE(self, event):
        """React to IN_CLOSE_WRITE events."""
        self.main.add_image(event.pathname)


__all__ = ['NewImageWatcher']
