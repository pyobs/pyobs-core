import logging
from typing import Union

from pyobs.interfaces import ICamera
from pyobs.object import get_object
from pyobs.utils.time import Time
from pyobs.utils.fits import FilenameFormatter
from pyobs.utils.images import BiasImage, DarkImage, FlatImage
from pyobs.utils.astrometry import Astrometry
from pyobs.utils.photometry import Photometry
from pyobs.utils.archive import Archive


log = logging.getLogger(__name__)


class Night:
    def __init__(self, archive: Union[dict, Archive], photometry: Union[dict, Photometry],
                 astrometry: Union[dict, Astrometry], worker_procs: int = 4,
                 filenames_calib: str = '{SITEID}{TELID}-{INSTRUME}-{DAY-OBS|date:}-'
                                        '{IMAGETYP}-{XBINNING}x{YBINNING}{FILTER|filter}.fits',
                 filenames: str = '{SITEID}{TELID}-{INSTRUME}-{DAY-OBS|date:}-'
                                  '{FRAMENUM|string:04d}-{IMAGETYP|type}01.fits',
                 *args, **kwargs):

        # get archive, photometry and astrometry
        self._archive = get_object(archive, Archive)
        self._photometry = get_object(photometry, Photometry)
        self._astrometry = get_object(astrometry, Astrometry)

        # stuff
        self._worker_processes = worker_procs

        # cache for master calibration frames
        self._master_names = {}
        self._master_data = {}

        # default filename patterns
        self._fmt_calib = FilenameFormatter(filenames_calib)
        self._fmt_object = FilenameFormatter(filenames)

    def _calib_data_frame(self, info, bias, dark, flat):
        # download frame
        img = self._archive.download_frames([info])[0]

        # calibrate and trim to TRIMSEC
        calibrated = img.calibrate(bias=bias, dark=dark, flat=flat).trim()

        # set (raw) filename
        calibrated.format_filename(self._fmt_object)
        calibrated.header['L1RAW'] = info.filename

        # do photometry and astrometry
        self._photometry(calibrated)
        self._astrometry(calibrated)

        # upload
        self._archive.upload_frames([calibrated])

    def _calib_data(self, night: str, instrument: str, binning: str, filter_name: str):
        # get all frames
        infos = self._archive.list_frames(night=night, instrument=instrument,
                                          image_type=ICamera.ImageType.OBJECT, binning=binning, filter_name=filter_name,
                                          rlevel=0)
        if len(infos) == 0:
            return
        log.info('Calibrating %d OBJECT frames...', len(infos))

        # midnight
        midnight = Time(night + ' 23:59:59')

        # get calibration frames
        bias = BiasImage.find_master(self._archive, midnight, instrument, binning)
        dark = DarkImage.find_master(self._archive, midnight, instrument, binning)
        flat = FlatImage.find_master(self._archive, midnight, instrument, binning, filter_name)

        # anything missing?
        if bias is None or dark is None or flat is None:
            log.error('Could not find BIAS/DARK/FLAT, skipping %d frames...', len(infos))
            return
        log.info('Using BIAS frame: %s', bias.header['FNAME'])
        log.info('Using DARK frame: %s', dark.header['FNAME'])
        log.info('Using SKYFLAT frame: %s', flat.header['FNAME'])

        # run all science frames
        for i, info in enumerate(infos, 1):
            log.info('Calibrating file %d/%d: %s...', i, len(infos), info.filename)
            self._calib_data_frame(info, bias, dark, flat)

    def _create_master_calib(self, night: str, instrument: str, image_type: ICamera.ImageType, binning: str,
                             filter_name: str = None):
        # get frames
        infos = self._archive.list_frames(night=night, image_type=image_type, filter_name=filter_name,
                                          instrument=instrument, binning=binning, rlevel=0)

        # log it
        fltr = '' if filter_name is None else ' in ' + filter_name
        log.info('Found %d %s %s frames%s from instrument %s.',
                 len(infos), binning, image_type.value, fltr, instrument)

        # if too few, we're finished
        if len(infos) < 3:
            if len(infos) > 0:
                log.warning('Too few (%d) frames found, skipping...', len(infos))
            return None

        # download frames
        images = self._archive.download_frames(infos)

        # midnight
        midnight = Time(night + ' 23:59:59')

        # create master
        if image_type == ICamera.ImageType.BIAS:
            # BIAS are easy
            calib = BiasImage.create_master(images)

        elif image_type == ICamera.ImageType.DARK:
            # for DARKs, we first need a BIAS
            bias = BiasImage.find_master(self._archive, midnight, instrument, binning, None)
            if bias is None:
                log.error('Could not find BIAS frame, skipping...')
                return
            calib = DarkImage.create_master(images, bias=bias)

        elif image_type == ICamera.ImageType.SKYFLAT:
            # for DARKs, we first ne a BIAS and a DARK
            bias = BiasImage.find_master(self._archive, midnight, instrument, binning, None)
            dark = DarkImage.find_master(self._archive, midnight, instrument, binning, None)
            if bias is None or dark is None:
                log.error('Could not find BIAS/DARK frame, skipping...')
                return
            calib = FlatImage.create_master(images, bias=bias, dark=dark)

        else:
            raise ValueError('Invalid image type')

        # filename
        calib.format_filename(self._fmt_calib)

        # upload
        log.info('Uploading master calibration frame as %s...', calib.header['FNAME'])
        self._archive.upload_frames([calib])

        # finished
        return calib

    def __call__(self, night: str):
        """Reduces all data within a given range of time.

        Args:
            night: Night to reduce
        """

        # get options
        options = self._archive.list_options(night=night)

        # loop instruments
        for instrument in options['instruments']:
            log.info('Reducing data for instrument %s...', instrument)

            # loop binnings
            for binning in options['binnings']:
                # create bias
                self._create_master_calib(night, instrument, ICamera.ImageType.BIAS, binning)

                # create dark
                self._create_master_calib(night, instrument, ICamera.ImageType.DARK, binning)

                # loop filters
                for filter_name in options['filters']:
                    # create flat
                    self._create_master_calib(night, instrument, ICamera.ImageType.SKYFLAT, binning, filter_name)

                    # calibrate science data
                    self._calib_data(night, instrument, binning, filter_name)


__all__ = ['Night']
