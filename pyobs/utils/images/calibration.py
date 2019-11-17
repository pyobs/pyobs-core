from typing import List
import numpy as np
from astropy.io import fits
import astropy.units as u
import logging

from pyobs.interfaces import ICamera
from pyobs.utils.time import Time
from .image import Image


log = logging.getLogger(__name__)


class CalibrationImage(Image):
    _master_names = {}
    _master_frames = {}

    @classmethod
    def average(cls, images: List[Image]):
        # collect data
        data = [img.data for img in images]

        # create new image
        img = cls()

        # average
        img.data = np.mean(data, axis=0)

        # header
        img.header = images[0].header.copy()

        # add history
        for i, src in enumerate(images, 1):
            basename = src.header['FNAME'].replace('.fits.fz', '').replace('.fits', '')
            img.header['L1AVG%03d' % i] = (basename, 'Image used for average')
        img.header['RLEVEL'] = (1, 'Reduction level')

        # finished
        return img

    @classmethod
    def find_master(cls, archive: 'Archive', time: Time, instrument: str, binning: str, filter_name: str = None):
        # does it not exist?
        if (cls, instrument, binning, filter_name) not in CalibrationImage._master_names:
            # try to download one
            if not cls._download_calib_frame(archive, time, instrument, binning, filter_name):
                # still nothing...
                return None

        # get calib frame
        filename = CalibrationImage._master_names[cls, instrument, binning, filter_name]
        calib = CalibrationImage._master_frames[filename]

        # return
        return calib

    @classmethod
    def _download_calib_frame(cls, archive: 'Archive', time: Time, instrument: str, binning: str, filter_name: str) \
            -> bool:

        # get image type
        from . import BiasImage, DarkImage, FlatImage
        image_type = {
            BiasImage: ICamera.ImageType.BIAS,
            DarkImage: ICamera.ImageType.DARK,
            FlatImage: ICamera.ImageType.SKYFLAT
        }[cls]

        # find reduced frames from +- 30 days
        fltr = '' if filter_name is None else ' in ' + filter_name
        log.info('Searching for %s %s master calibration frames%s from instrument %s.',
                 binning, image_type.value, fltr, instrument)
        infos = archive.list_frames(start=time - 30 * u.day, end=time + 30 * u.day,
                                    instrument=instrument, image_type=image_type, binning=binning,
                                    filter_name=filter_name, rlevel=1)

        # found any?
        if len(infos) == 0:
            log.error('Found none.')
            return False
        else:
            # sort by diff to time and take first
            s = sorted(infos, key=lambda i: abs((i.dateobs - time).sec))
            info = s[0]
            log.info('Found calibration frame %s.', info.filename)

            # download it
            calib = archive.download_frames([info])[0]

            # set it
            CalibrationImage._master_names[cls, instrument, binning, filter_name] = info.filename
            CalibrationImage._master_frames[info.filename] = calib
            return True


__all__ = ['CalibrationImage']
