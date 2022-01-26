import glob
import logging
import os
import asyncio
from typing import Any, Optional, List, Tuple
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

    def __init__(
        self,
        watchpath: str,
        destinations: Optional[List[str]] = None,
        poll: bool = False,
        poll_interval: int = 5,
        wait_time: int = 10,
        **kwargs: Any,
    ):
        """Create a new image watcher.

        Args:
            watchpath: Path to watch.
            destinations: Filename patterns for destinations.
            poll: If True, watchpath is polled instead of watched by inotify.
            poll_interval: Interval for polling in seconds, if poll is True.
            wait_time: Time in seconds between adding file to list and processing it.
        """
        Module.__init__(self, **kwargs)

        # add thread func
        self.add_background_task(self._worker)
        if poll:
            self.add_background_task(self._watch_poll)
        else:
            self.add_background_task(self._watch_inotify)

        # variables
        self._watchpath = watchpath
        self._notifier: Optional[Any] = None
        self._queue = asyncio.Queue[Tuple[str, asyncio.Future[None]]]()
        self._poll = poll
        self._poll_interval = poll_interval
        self._wait_time = wait_time

        # filename patterns
        if not destinations:
            raise ValueError("No filename patterns given for the destinations.")
        self._destinations = destinations

    async def _watch_inotify(self) -> None:
        from asyncinotify import Inotify, Mask  # type: ignore

        # Context manager to close the inotify handle after use
        with Inotify() as inotify:
            # add watch
            inotify.add_watch(self._watchpath, Mask.CLOSE_WRITE)

            # iterate events forever
            async for event in inotify:
                self.add_image(str(event.path))

    async def _watch_poll(self) -> None:
        # init list
        files = await self.vfs.listdir(self._watchpath)

        # run forever
        while True:
            # get new list
            new_files = await self.vfs.listdir(self._watchpath)

            # find all new files and add them
            for f in new_files:
                if f not in files:
                    self.add_image(f)

            # store new list
            files = new_files

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
        self._queue.put_nowait((filename, asyncio.create_task(asyncio.sleep(self._wait_time))))

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
            filename, future = await self._queue.get()

            # waiting for future, which is the wait time for new files
            await future
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
