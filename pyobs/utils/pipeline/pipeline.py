import logging
from typing import Union
import astropy.units as u

from pyobs.images import BiasImage, DarkImage, FlatImage, Image
from pyobs.utils.archive import FrameInfo
from pyobs.utils.enums import ImageType
from pyobs.utils.time import Time

log = logging.getLogger(__name__)


class Pipeline:
    def calibrate(self, image: Image, bias: BiasImage = None, dark: DarkImage = None, flat: FlatImage = None) -> Image:
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

    @staticmethod
    def find_master(image_type: ImageType , archive: 'Archive', time: Time, instrument: str,
                    binning: str, filter_name: str = None, max_days: float = 30.) -> Union[None, FrameInfo]:
        """Find and download master calibration frame.

        Args:
            image_type: Image type.
            archive: Archive to use for downloading frames.
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

        # found any?
        if len(infos) == 0:
            log.warning('Could not find any matching %s calibration frames.', image_type.value)
            return None
        else:
            # sort by diff to time and take first
            s = sorted(infos, key=lambda i: abs((i.dateobs - time).sec))
            info = s[0]
            log.info('Found %s frame %s.', image_type.name, info.filename)

            # return FrameInfo
            return info


__all__ = ['Pipeline']
