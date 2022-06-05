import fnmatch
import glob
import logging
import os
import asyncio
from dataclasses import dataclass
from pathlib import PurePosixPath
from typing import Any, Optional, List, Tuple, AnyStr
from astropy.io import fits

from pyobs.modules import Module
from pyobs.utils.fits import format_filename

log = logging.getLogger(__name__)


@dataclass
class CurrentFile:
    filename: str
    data: AnyStr
    out_filename: Optional[str] = None
    hdu_list: Optional[fits.HDUList] = None


class ImageWatcher(Module):
    """Watch for new files and write them to all given destinations.

    Watches a path for new files and stores them in all given destinations. Only if all operations were successful,
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
        pattern: str = "*",
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
        self._pattern = pattern
        self.current_file: Optional[CurrentFile] = None

        # filename patterns
        if not destinations:
            raise ValueError("No filename patterns given for the destinations.")
        self._destinations = destinations

    async def _watch_inotify(self) -> None:
        from asyncinotify import Inotify, Mask  # type: ignore

        # get local directory
        local = await self.vfs.local_path(self._watchpath)

        # Context manager to close the inotify handle after use
        with Inotify() as inotify:
            # add watch on local directory
            inotify.add_watch(local, Mask.CLOSE_WRITE)

            # iterate events forever
            async for event in inotify:
                # get filename by replacing local with watchpath
                filename = str(event.path).replace(local, self._watchpath)

                # add file
                self.add_file(filename)

    async def _watch_poll(self) -> None:
        # init list
        files = set(await self.vfs.listdir(self._watchpath))

        # run forever
        path = PurePosixPath(self._watchpath)
        while True:
            # get new list
            new_files = await self.vfs.listdir(self._watchpath)

            # find all new files and add them
            for f in new_files:
                if f not in files:
                    print(str(path / f))
                    self.add_file(str(path / f))

            # store new list
            files = set(new_files)

    async def open(self) -> None:
        """Open image watcher."""
        await Module.open(self)

        # add all files from directory to queue
        for filename in await self.vfs.listdir(self._watchpath):
            self.add_file(os.path.join(self._watchpath, filename))

    async def close(self) -> None:
        """Close image watcher."""
        await Module.close(self)

        # stop watching
        if self._notifier:
            log.info("Stop watching directory...")
            self._notifier.stop()

    def add_file(self, filename: str) -> None:
        """Add a file to the file queue.

        Args:
            filename (str): Local filename of new file.
        """

        # check pattern
        if not fnmatch.fnmatch(filename, self._pattern):
            return

        # log and add file
        log.info("Adding new file %s...", filename)
        self._queue.put_nowait((filename, asyncio.create_task(asyncio.sleep(self._wait_time))))

    async def _worker(self) -> None:
        """Worker thread."""

        # run forever
        while True:
            # get next filename
            filename, future = await self._queue.get()

            # waiting for future, which is the wait time for new files
            await future
            log.info("Working on file %s...", filename)

            # better safe than sorry
            try:
                # get file data
                async with self.vfs.open_file(filename, "rb") as fd:
                    data = await fd.read()

                # try to load as fits file
                try:
                    fits_file = fits.HDUList.fromstring(data)
                except:
                    fits_file = None

                # fill current file
                self.current_file = CurrentFile(filename=filename, data=data, hdu_list=fits_file)

                # loop archive and upload
                success = True
                for pattern in self._destinations:
                    # if it contains {placeholders}, we assume it's a FITS file and format filename
                    if "{" in pattern and "}" in pattern and fits_file is not None:
                        # format filename
                        out_filename = format_filename(fits_file["SCI"].header, pattern)
                        if out_filename is None:
                            raise ValueError("Could not create name for file.")

                    else:
                        # no formatting, so just add filename to destination
                        out_filename = os.path.join(pattern, os.path.basename(filename))

                    # store it
                    log.info("Storing file as %s...", out_filename)
                    self.current_file.out_filename = out_filename
                    try:
                        async with self.vfs.open_file(out_filename, "wb") as fd:
                            await fd.write(data)
                    except:
                        log.warning("Error while copying file, skipping for now.")
                        success = False
                        break

                    # do extra processing
                    if not await self.process_extra(filename):
                        success = False
                        break

                # no success?
                if not success:
                    continue

                # close and delete files
                log.info("Removing file from watch directory...")
                if not await self.vfs.remove(filename):
                    log.warning("Could not delete %s.", filename)

                # cleanup extra
                await self.cleanup_extra(filename)

            except:
                log.exception("Something went wrong.")

    async def process_extra(self, filename: str) -> bool:
        """Can be overwritten by derived classes to do extra processing on files.
        All information are stored in self.current_file and can be checked against the given filename.

        Args:
            filename: Input name of original file.

        Returns:
            Whether processing was successful
        """
        return True

    async def cleanup_extra(self, filename: str) -> None:
        """Can be overwritten by derived classes to do clean up after successful copying.
        All information are stored in self.current_file and can be checked against the given filename.

        Args:
            filename: Input name of original file.
        """
        ...


__all__ = ["ImageWatcher"]
