import logging
from typing import Union, Optional, List
import astropy.units as u

from pyobs.images import Image
from pyobs.utils.archive import FrameInfo, Archive
from pyobs.utils.enums import ImageType
from pyobs.utils.time import Time

log = logging.getLogger(__name__)


class Pipeline:
    def create_master_bias(self, images: List[Image]) -> Image:
        """Create master bias frame.

        Args:
            images: List of raw bias frames.

        Returns:
            Master bias frame.
        """
        raise NotImplementedError

    def create_master_dark(self, images: List[Image], bias: Image) -> Image:
        """Create master dark frame.

        Args:
            images: List of raw dark frames.
            bias: Bias frame to subtract from images.

        Returns:
            Master dark frame.
        """
        raise NotImplementedError

    def create_master_flat(self, images: List[Image], bias: Image) -> Image:
        """Create master flat frame.

        Args:
            images: List of raw flat frames.
            bias: Bias frame to subtract from images.

        Returns:
            Master flat frame.
        """
        raise NotImplementedError

    def calibrate(self, image: Image, bias: Image = None, dark: Image = None, flat: Image = None) -> Image:
        """Calibrate a single science frame.

        Args:
            image: Image to calibrate.
            bias: Bias frame to use.
            dark: Dark frame to use.
            flat: Flat frame to use.

        Returns:
            Calibrated image.
        """
        raise NotImplementedError

    def find_master(self, archive: Archive, image_type: ImageType, time: Time, instrument: str,
                    binning: str, filter_name: str = None, max_days: float = 30.) -> Optional[Image]:
        """Find and download master calibration frame.

        Args:
            archive: Image archive.
            image_type: Image type.
            time: Time to search at.
            instrument: Instrument to use.
            binning: Used binning.
            filter_name: Used filter.
            max_days: Maximum number of days from DATE-OBS to find frames.

        Returns:
            FrameInfo for master calibration frame or None.
        """

        # find reduced frames from +- N days
        log.info('Searching for %s %s master calibration frames%s from instrument %s.',
                 binning, image_type.value, '' if filter_name is None else ' in ' + filter_name, instrument)
        infos = archive.list_frames(start=time - max_days * u.day, end=time + max_days * u.day,
                                    instrument=instrument, image_type=image_type, binning=binning,
                                    filter_name=filter_name, rlevel=1)

        # found none?
        if len(infos) == 0:
            log.warning('Could not find any matching %s calibration frames.', image_type.value)
            return None

        # sort by diff to time and take first
        s = sorted(infos, key=lambda i: abs((i.dateobs - time).sec))
        info = s[0]
        log.info('Found %s frame %s.', image_type.name, info.filename)

        # download it
        return archive.download_frames([info])[0]


__all__ = ['Pipeline']
