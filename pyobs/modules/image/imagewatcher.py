import asyncio
import fnmatch
import logging
import os
import time
import warnings
from dataclasses import dataclass
from pathlib import Path, PurePosixPath
from typing import Any

from astropy.io import fits

from pyobs.modules import Module
from pyobs.utils.fits import format_filename

log = logging.getLogger(__name__)


@dataclass
class CurrentFile:
    filename: str
    data: bytes | str
    out_filename: str | None = None
    hdu_list: fits.HDUList | None = None


class ImageWatcher(Module):
    """Watch for new files and write them to all given destinations.

    Watches a path for new files and stores them in all given destinations. Only if all operations were successful,
    the file is deleted.

    New files are not processed immediately, but only after a wait time (``wait_time``) has passed since they were
    detected. This is mainly to make sure the file is fully written before it is read: while the inotify watcher
    only reports files after they have been closed for writing (``CLOSE_WRITE``), the polling watcher and the
    initial scan in ``open()`` can see a file while its write is still in progress. The same wait time is also
    used to delay re-processing of files whose destination copy failed (see ``_worker``).
    """

    __module__ = "pyobs.modules.image"

    def __init__(
        self,
        watchpath: str,
        destinations: list[str] | None = None,
        poll: bool = False,
        poll_interval: int = 5,
        wait_time: int = 10,
        pattern: str = "*",
        flatten: bool = True,
        **kwargs: Any,
    ):
        """Create a new image watcher.

        Args:
            watchpath: Path to watch.
            destinations: Filename patterns for destinations.
            poll: If True, watchpath is polled instead of watched by inotify.
            poll_interval: Interval for polling in seconds, if poll is True.
            wait_time: Time in seconds between adding a file to the list and processing it. Gives a file that is
                still being written time to finish (relevant for poll mode and the initial scan) and spaces out
                re-queued files after failed destination copies.
            pattern: Only watch/process files matching this fnmatch pattern; also applied recursively, i.e. it
                is matched against the full path, so a pattern like "*.fits" matches files in subdirectories too.
            flatten: For a non-templated destination (one without ``{placeholder}``s), whether to collapse the
                file's path to just its basename under that destination (the historical behavior, default) or to
                preserve its path relative to ``watchpath`` under the destination instead. Files found via
                recursive watching or polling only keep their subdirectory structure at the destination when this
                is False.
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
        self._notifier: Any | None = None
        self._queue = asyncio.Queue[tuple[str, float]]()
        self._poll = poll
        self._poll_interval = poll_interval
        self._wait_time = wait_time
        self._pattern = pattern
        self._flatten = flatten
        self.current_file: CurrentFile | None = None

        # filename patterns
        if not destinations:
            raise ValueError("No filename patterns given for the destinations.")
        self._destinations = destinations

    async def _watch_inotify(self) -> None:
        from asyncinotify import Mask, RecursiveWatcher

        # get local directory
        local = await self.vfs.local_path(self._watchpath)

        # recursively watch the local directory: watches are added for subdirectories as they're
        # created or moved in, and removed as they're moved out (deletion needs no explicit
        # removal -- the kernel invalidates the watch on its own, see the plan doc for details)
        watcher = RecursiveWatcher(Path(local), Mask.CLOSE_WRITE)
        async for event in watcher.watch_recursive():
            if event.path is None:
                continue

            # get filename by replacing local with watchpath
            filename = str(event.path).replace(local, self._watchpath)

            # add file
            await self.add_file(filename)

    async def _watch_poll(self) -> None:
        # init list (recursive, so subdirectories are picked up too)
        files = set(await self.vfs.find(self._watchpath, self._pattern))

        # run forever
        while True:
            await asyncio.sleep(self._poll_interval)

            # get new list
            new_files = set(await self.vfs.find(self._watchpath, self._pattern))

            # find all new files and add them
            for f in new_files - files:
                await self.add_file(os.path.join(self._watchpath, f))

            # store new list
            files = new_files

    async def open(self) -> None:
        """Open image watcher."""
        await Module.open(self)

        # add all files from directory to queue (recursive, so subdirectories are picked up too)
        for filename in await self.vfs.find(self._watchpath, self._pattern):
            await self.add_file(os.path.join(self._watchpath, filename))

    async def close(self) -> None:
        """Close image watcher."""
        await Module.close(self)

        # stop watching
        if self._notifier:
            log.info("Stop watching directory...")
            self._notifier.stop()

    async def add_file(self, filename: str) -> None:
        """Add a file to the file queue.

        Args:
            filename (str): Local filename of new file.
        """

        # check pattern
        if not fnmatch.fnmatch(filename, self._pattern):
            return

        # log and add file
        log.info("Adding new file %s...", filename)
        self._queue.put_nowait((filename, time.time() + self._wait_time))

    async def _worker(self) -> None:
        """Worker thread."""

        # run forever
        while True:
            # get next filename and wait some time
            filename, ready_at = await self._queue.get()
            wait = ready_at - time.time()
            if wait > 0:
                await asyncio.sleep(wait)
            log.info("Working on file %s...", filename)

            # better safe than sorry
            try:
                # get file data
                async with self.vfs.open_file(filename, "rb") as fd:
                    data = await fd.read()

                # try to load as fits file; data may well not be a FITS file at all
                try:
                    with warnings.catch_warnings():
                        warnings.simplefilter("ignore", fits.verify.VerifyWarning)
                        fits_file = await asyncio.to_thread(fits.HDUList.fromstring, data)
                except Exception:
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

                    elif self._flatten:
                        # no formatting, so just add filename to destination
                        out_filename = os.path.join(pattern, os.path.basename(filename))

                    else:
                        # preserve the file's path relative to watchpath under the destination
                        rel = PurePosixPath(filename).relative_to(self._watchpath)
                        out_filename = str(PurePosixPath(pattern) / rel)

                    # store it
                    log.info("Storing file as %s...", out_filename)
                    self.current_file.out_filename = out_filename
                    try:
                        async with self.vfs.open_file(out_filename, "wb") as fd:
                            await fd.write(data)
                    except Exception as e:
                        log.warning("Error while copying file, skipping for now: %s", e)
                        success = False
                        break

                    # do extra processing
                    if not await self.process_extra(filename):
                        success = False
                        break

                # no success?
                if not success:
                    # re-queue file and skip file for now
                    self._queue.put_nowait((filename, time.time() + self._wait_time))
                    continue

                # close and delete files
                log.info("Removing file from watch directory...")
                if not await self.vfs.remove(filename):
                    log.warning("Could not delete %s.", filename)

                # cleanup extra
                await self.cleanup_extra(filename)

            except Exception:
                log.exception("Something went wrong.")

    async def process_extra(self, filename: str) -> bool:
        """Can be overwritten by derived classes to do extra processing on files.
        All information are stored in self.current_file and can be checked against the given filename.

        Note:
            This hook runs on the module's event loop and must not block: no CPU-heavy or
            synchronous I/O here. Offload such work to a thread, e.g. with ``asyncio.to_thread``.

        Args:
            filename: Input name of original file.

        Returns:
            Whether processing was successful
        """
        return True

    async def cleanup_extra(self, filename: str) -> None:
        """Can be overwritten by derived classes to do clean up after successful copying.
        All information are stored in self.current_file and can be checked against the given filename.

        Note:
            This hook runs on the module's event loop and must not block: no CPU-heavy or
            synchronous I/O here. Offload such work to a thread, e.g. with ``asyncio.to_thread``.

        Args:
            filename: Input name of original file.
        """
        ...


__all__ = ["ImageWatcher"]
