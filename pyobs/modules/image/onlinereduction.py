import asyncio
import logging
import os
from typing import List, Union, Type, Any, Dict, Optional
from astropy.time import Time

from pyobs.images import Image
from pyobs.modules import Module
from pyobs.object import get_object
from pyobs.events import NewImageEvent
from pyobs.utils.archive import Archive
from pyobs.utils.cache import DataCache
from pyobs.utils.enums import ImageType
from pyobs.utils.pipeline import Pipeline

log = logging.getLogger(__name__)


class OnlineReduction(Module):
    """Calibrates images online during the night."""
    __module__ = 'pyobs.modules.image'

    def __init__(self, pipeline: Union[Dict[str, Any], Pipeline], archive: Union[dict, Archive],
                 sources: Union[str, Optional[List[str]]] = None, cache_size: int = 20, **kwargs: Any):
        """Creates a new image writer.

        Args:
            pipeline: Pipeline to use for reduction.
            archive: Used for retrieving calibration files. If None, no calibration is done.
            sources: List of sources (e.g. cameras) to process images from or None for all.
            cache_size: Size of cache for calibration files.
        """
        Module.__init__(self, **kwargs)

        # stuff
        self._sources = [sources] if isinstance(sources, str) else sources
        self._queue = asyncio.Queue()
        self._archive = None if archive is None else get_object(archive, Archive)
        self._pipeline = get_object(pipeline, Pipeline)
        self._cache = DataCache(size=cache_size)

        # add thread func
        self.add_background_task(self._worker, True)

    async def open(self) -> None:
        """Open image writer."""
        await Module.open(self)

        # subscribe to channel with new images
        log.info('Subscribing to new image events...')
        await self.comm.register_event(NewImageEvent, self.process_new_image_event)

    def process_new_image_event(self, event: NewImageEvent, sender: str) -> bool:
        """Puts a new images in the DB with the given ID.

        Args:
            event:  New image event
            sender: Who sent the event?

        Returns:
            Success
        """

        # filter by source
        if self._sources is not None and sender not in self._sources:
            return False

        # only process OBJECT frames
        if event.image_type != ImageType.OBJECT:
            return False

        # put into queue
        log.info('Received new image event from %s.', sender)
        self._queue.put_nowait(event.filename)
        return True

    async def _worker(self) -> None:
        """Worker thread."""

        # run forever
        while not self.closing.is_set():
            # get next filename
            filename = self._queue.get()

            try:
                # download image
                log.info('Downloading file %s...', filename)
                image = await self.vfs.read_image(filename)
            except FileNotFoundError:
                log.error('Could not download image.')
                continue

            # only use master calibration frames, if an archive is given
            bias, dark, flat = None, None, None
            if self._archive is not None:
                # get instrument, binning and filter from image
                try:
                    instrument = image.header['INSTRUME']
                    binning = '%dx%d' % (image.header['XBINNING'], image.header['YBINNING'])
                    filter_name = image.header['FILTER'] if 'FILTER' in image.header else None
                    date_obs = Time(image.header['DATE-OBS'])
                except KeyError:
                    log.warning('Missing header keywords.')
                    continue

                # get master calibration frames
                bias = self._get_master_calibration(Image, date_obs, instrument, binning)
                dark = self._get_master_calibration(Image, date_obs, instrument, binning)
                flat = self._get_master_calibration(Image, date_obs, instrument, binning, filter_name)

                # anything missing?
                if bias is None or dark is None or flat is None:
                    log.warning('Could not find BIAS/DARK/FLAT, skipping frame...')
                    continue

            # calibrate
            calibrated = self._pipeline.calibrate(image, bias, dark, flat)

            # upload file
            outfile = os.path.join(os.path.dirname(filename), calibrated.header['FNAME'])
            try:
                log.info('Uploading image to file server...')
                await self.vfs.write_image(outfile, calibrated)
            except FileNotFoundError:
                raise ValueError('Could not upload image.')

            # broadcast image path
            if self.comm:
                log.info('Broadcasting image ID...')
                await self.comm.send_event(NewImageEvent(outfile, ImageType.OBJECT, raw=filename))
            log.info('Finished image.')

    def _get_master_calibration(self, image_class: Type[Image], time: Time, instrument: str, binning: str,
                                filter_name: Optional[str] = None) -> Optional[Union[Image]]:
        """Find master calibration frame for given parameters using a cache.

        Args:
            image_class: Image class.
            instrument: Instrument name.
            binning: Binning.
            filter_name: Name of filter.

        Returns:
            Image or None
        """

        # get frame info for best master frame
        frame = image_class.find_master(self._archive, time, instrument, binning, filter_name)
        if frame is None:
            return None

        # is frame in cache already?
        if frame.filename in self._cache:
            return self._cache[frame.filename]

        # download, store and return it
        log.info('Downlading frame %s...', frame.filename)
        self._cache[frame.filename] = self._archive.download_frames([frame])[0]
        return self._cache[frame.filename]


__all__ = ['OnlineReduction']
