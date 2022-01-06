import glob
import logging
import os
import asyncio
from typing import Any, Optional, List
from astropy.io import fits

from pyobs.modules import Module
from pyobs.utils.fits import format_filename

log = logging.getLogger(__name__)


class ImageWatcher(Module):
    """Watch for new images and write them to all given destinations.

    Watches a path for new images and stores them in all given destinations. Only if all operations were successful,
    the file is deleted.
    """

    __module__ = "pyobs.modules.image"

    def __init__(self, watchpath: Optional[str] = None, destinations: Optional[List[str]] = None, **kwargs: Any):
        """Create a new image watcher.

        Args:
            watchpath: Path to watch.
            destinations: Filename patterns for destinations.
        """
        Module.__init__(self, **kwargs)

        # test import
        import pyinotify

        # add thread func
        self.add_background_task(self._worker)

        # variables
        self._watchpath = watchpath
        self._notifier = None
        self._queue = asyncio.Queue[str]()

        # filename patterns
        if not destinations:
            raise ValueError("No filename patterns given for the destinations.")
        self._destinations = destinations

    async def open(self) -> None:
        """Open module."""
        await Module.open(self)
        import pyinotify

        class EventHandler(pyinotify.ProcessEvent):
            """Event handler for file watcher."""

            def __init__(self, main, *args: Any, **kwargs: Any) -> None:
                """Create event handler."""
                pyinotify.ProcessEvent.__init__(self, *args, **kwargs)
                self.main = main

            def process_IN_CLOSE_WRITE(self, event: Any) -> None:
                """React to IN_CLOSE_WRITE events."""
                self.main.add_image(event.pathname)

        # start watching directory
        if self._watchpath:
            log.info("Start watching directory %s for changes...", self._watchpath)
            wm = pyinotify.WatchManager()
            wm.add_watch(self._watchpath, pyinotify.IN_CLOSE_WRITE)
            self._notifier = pyinotify.ThreadedNotifier(wm, default_proc_fun=EventHandler(self))  # , name='observer')
            self._notifier.start()

    async def close(self) -> None:
        """Close image watcher."""
        await Module.close(self)

        # stop watching
        if self._notifier:
            log.info("Stop watching directory...")
            self._notifier.stop()

    def add_image(self, filename: str) -> None:
        """Add an image to the image database.

        Args:
            filename (str): Local filename of new image.
        """

        # log file
        log.info("Adding new image %s...", filename)
        self._queue.put_nowait(filename)

    async def _clear_queue(self) -> None:
        """Clear the queue with new files."""

        # clear queue
        while not self._queue.empty():
            await self._queue.get()

    async def _worker(self) -> None:
        """Worker thread."""

        # first, add all files from directory to queue
        await self._clear_queue()
        for filename in sorted(glob.glob(os.path.join(self._watchpath, "*"))):
            self.add_image(filename)

        # run forever
        while True:
            # get next filename
            filename = await self._queue.get()
            log.info("Working on file %s...", filename)

            # better safe than sorry
            try:
                # open file
                fits_file = fits.open(filename)

                # loop archive and upload
                success = True
                for pattern in self._destinations:

                    # create filename
                    out_filename = format_filename(fits_file["SCI"].header, pattern)
                    if out_filename is None:
                        raise ValueError("Could not create name for file.")

                    # store it
                    log.info("Storing file as %s...", out_filename)
                    try:
                        await self.vfs.write_fits(out_filename, fits_file)
                    except:
                        log.exception("Error while copying file, skipping for now.")
                        success = False

                # no success_
                if not success:
                    continue

                # close and delete files
                log.info("Removing file from watch directory...")
                os.remove(filename)

            except:
                log.exception("Something went wrong.")


__all__ = ["ImageWatcher"]
