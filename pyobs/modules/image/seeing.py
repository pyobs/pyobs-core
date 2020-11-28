import logging
import numpy as np
from typing import List, Union
from astropy.wcs import WCS
from astropy.wcs.utils import proj_plane_pixel_scales

from pyobs import Module
from pyobs.events import NewImageEvent
from pyobs.utils.publisher import Publisher
from pyobs.utils.time import Time

log = logging.getLogger(__name__)


class Seeing(Module):
    """Measures seeing on reduced images with a catalog."""

    def __init__(self, sources: Union[str, List[str]] = None, publishers: List[Union[Publisher, dict]] = None,
                 max_ellipticity: float = 0.2, *args, **kwargs):
        """Creates a new seeing estimator.

        Args:
            sources: List of sources (e.g. cameras) to process images from or None for all.
            max_ellipticity: Maximum ellipticity for sources to consider.
        """
        Module.__init__(self, *args, **kwargs)

        # stuff
        self._sources = [sources] if isinstance(sources, str) else sources
        self._publishers = [] if publishers is None else [self._add_child_object(p) for p in publishers]
        self._max_ellipticity = max_ellipticity

    def open(self):
        """Open module."""
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

        # put into queue
        log.info('Received new image event from %s.', sender)

        # download image
        try:

            log.info('Downloading file %s...', event.filename)
            image = self.vfs.download_image(event.filename)
        except FileNotFoundError:
            log.error('Could not download image.')
            return

        # get catalog
        cat = image.catalog
        if cat is None:
            # no catalog found in file
            return

        # filter by ellipticity
        cat = cat[cat['ellipticity'] < self._max_ellipticity]

        # get WCS and pixel size
        wcs = WCS(image.header)
        pix_size = abs(proj_plane_pixel_scales(wcs)[0] * 3600.)

        # calculate seeing
        seeing = np.mean(cat['fwhm']) * pix_size
        log.info('Found seeing of %.2f".', seeing)

        # log it
        for publisher in self._publishers:
            publisher(time=Time.now().isot, seeing=seeing)


__all__ = ['Seeing']
