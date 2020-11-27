import logging
import os
from queue import Queue
from typing import List, Union, Type

from astropy.time import Time

from pyobs import Module, get_object
from pyobs.events import NewImageEvent
from pyobs.interfaces import ICamera
from pyobs.utils.archive import Archive
from pyobs.utils.images import ImageCache, CalibrationImage, BiasImage, DarkImage, FlatImage
from pyobs.utils.pipeline import Pipeline

log = logging.getLogger(__name__)


class OnlineReduction(Module):
    """Calibrates images online during the night."""

    def __init__(self, archive: Union[dict, Archive], pipeline: Union[dict, Pipeline],
                 sources: Union[str, List[str]] = None, cache_size: int = 20, *args, **kwargs):
        """Creates a new image writer.

        Args:
        """
        Module.__init__(self, *args, **kwargs)

        # stuff
        self._sources = [sources] if isinstance(sources, str) else sources
        self._queue = Queue()
        self._archive: Archive = get_object(archive, Archive)
        self._pipeline = get_object(pipeline, Pipeline)
        self._cache = ImageCache(size=cache_size)

        # add thread func
        self._add_thread_func(self._worker, True)

    def open(self):
        """Open image writer."""
        Module.open(self)

        # subscribe to channel with new images
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

        # filter by source
        if self._sources is not None and sender not in self._sources:
            return

        # only process OBJECT frames
        if event.image_type != ICamera.ImageType.OBJECT:
            return

        # put into queue
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
                image = self.vfs.download_image(filename)
            except FileNotFoundError:
                log.error('Could not download image.')
                continue

            # get instrument, binning and filter from image
            try:
                instrument = image.header['INSTRUME']
                binning = '%dx%d' % (image.header['XBINNING'], image.header['YBINNING'])
                filter_name = image.header['FILTER'] if 'FILTER' in image.header else None
                date_obs = Time(image.header['DATE-OBS'])
            except KeyError:
                log.error('Missing header keywords.')
                continue

            # get master calibration frames
            bias = self._get_master_calibration(BiasImage, date_obs, instrument, binning)
            dark = self._get_master_calibration(DarkImage, date_obs, instrument, binning)
            flat = self._get_master_calibration(FlatImage, date_obs, instrument, binning, filter_name)

            # anything missing?
            if bias is None or dark is None or flat is None:
                log.error('Could not find BIAS/DARK/FLAT, skipping frame...')
                continue

            # calibrate
            calibrated = self._pipeline.calibrate(image, bias, dark, flat)

            # upload file
            outfile = os.path.join(os.path.dirname(filename), calibrated.header['FNAME'])
            try:
                with self.open_file(outfile, 'wb') as cache:
                    log.info('Uploading image to file server...')
                    calibrated.writeto(cache)
            except FileNotFoundError:
                raise ValueError('Could not upload image.')

            # broadcast image path
            if self.comm:
                log.info('Broadcasting image ID...')
                self.comm.send_event(NewImageEvent(outfile, ICamera.ImageType.OBJECT, raw=filename))
            log.info('Finished image.')

    def _get_master_calibration(self, image_class: Type[CalibrationImage], time: Time, instrument: str, binning: str,
                                filter_name: str = None) -> Union[CalibrationImage, None]:
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
