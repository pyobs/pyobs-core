import logging
from typing import Union, Dict, Type

from pyobs.interfaces import ICamera
from pyobs.object import get_object
from pyobs.utils.time import Time
from pyobs.utils.fits import FilenameFormatter
from pyobs.utils.images import BiasImage, DarkImage, FlatImage, Image, CalibrationImage
from pyobs.utils.astrometry import Astrometry
from pyobs.utils.photometry import Photometry
from pyobs.utils.archive import Archive


log = logging.getLogger(__name__)


class Night:
    def __init__(self, site: str, night: str,
                 archive: Union[dict, Archive], photometry: Union[dict, Photometry],
                 astrometry: Union[dict, Astrometry], worker_procs: int = 4,
                 filenames_calib: str = '{SITEID}{TELID}-{INSTRUME}-{DAY-OBS|date:}-'
                                        '{IMAGETYP}-{XBINNING}x{YBINNING}{FILTER|filter}.fits',
                 filenames: str = '{SITEID}{TELID}-{INSTRUME}-{DAY-OBS|date:}-'
                                  '{FRAMENUM|string:04d}-{IMAGETYP|type}01.fits',
                 flats_combine: Union[str, Image.CombineMethod] = Image.CombineMethod.MEDIAN, flats_min_raw: int = 10,
                 masks: Dict[str, Union[Image, str]] = None, *args, **kwargs):
        """Creates a Night object for reducing a given night.

        Args:
            site: Telescope site to use.
            night: Night to reduce.
            archive: Archive to fetch images from and write results to.
            photometry: Photometry object.
            astrometry: Astrometry object.
            worker_procs: Number of worker processes.
            filenames_calib: Filename pattern for master calibration files.
            filenames: Filename pattern for reduced science frames.
            flats_combine: Method to combine flats.
            flats_min_raw: Minimum number of raw frames to create flat field.
            masks: Dictionary with masks to use for each binning given as, e.g., 1x1.
            *args:
            **kwargs:
        """

        # get archive, photometry and astrometry
        self._archive = get_object(archive, Archive)
        self._photometry = get_object(photometry, Photometry)
        self._astrometry = get_object(astrometry, Astrometry)

        # stuff
        self._site = site
        self._night = night
        self._worker_processes = worker_procs
        self._flats_combine = Image.CombineMethod(flats_combine) if isinstance(flats_combine, str) else flats_combine
        self._flats_min_raw = flats_min_raw

        # masks
        self._masks = {}
        if masks is not None:
            for binning, mask in masks.items():
                if isinstance(mask, Image):
                    self._masks[binning] = mask
                elif isinstance(mask, str):
                    self._masks[binning] = Image.from_file(mask)
                else:
                    raise ValueError('Unknown mask format.')

        # cache for master calibration frames
        self._master_frames = {}

        # default filename patterns
        self._fmt_calib = FilenameFormatter(filenames_calib)
        self._fmt_object = FilenameFormatter(filenames)

    def _calib_data_frame(self, info, bias, dark, flat):
        # download frame
        img = self._archive.download_frames([info])[0]

        # calibrate and trim to TRIMSEC
        calibrated = img.calibrate(bias=bias, dark=dark, flat=flat).trim()

        # add mask
        binning = '%dx%s' % (img.header['XBINNING'], img.header['YBINNING'])
        if binning in self._masks:
            calibrated.mask = self._masks[binning].copy()
        else:
            log.warning('No mask found for binning of frame.')

        # set (raw) filename
        calibrated.format_filename(self._fmt_object)
        calibrated.header['L1RAW'] = info.filename

        # do photometry and astrometry
        self._photometry.find_stars(calibrated)
        try:
            self._astrometry.find_solution(calibrated)
        except ValueError:
            # error message comes from astrometry
            pass

        # upload
        self._archive.upload_frames([calibrated])

    def _find_master(self, image_class: Type[CalibrationImage], instrument: str, binning: str,
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

        # is in cache?
        if (image_class, instrument, binning, filter_name) in self._master_frames:
            return self._master_frames[image_class, instrument, binning, filter_name]

        # try to download one
        midnight = Time(self._night + ' 23:59:59')
        frame = image_class.find_master(self._archive, midnight, instrument, binning, filter_name)
        if frame is not None:
            # download it
            calib = self._archive.download_frames([frame])[0]

            # store and return it
            self._master_frames[image_class, instrument, binning, filter_name] = calib
            return calib
        else:
            # still nothing
            return None

    def _calib_data(self, instrument: str, binning: str, filter_name: str):
        # get all frames
        infos = self._archive.list_frames(night=self._night, instrument=instrument,
                                          image_type=ICamera.ImageType.OBJECT, binning=binning, filter_name=filter_name,
                                          rlevel=0)
        if len(infos) == 0:
            return
        log.info('Calibrating %d OBJECT frames...', len(infos))

        # get calibration frames
        bias = self._find_master(BiasImage, instrument, binning)
        dark = self._find_master(DarkImage, instrument, binning)
        flat = self._find_master(FlatImage, instrument, binning, filter_name)

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

    def _create_master_calib(self, instrument: str, image_type: ICamera.ImageType, binning: str,
                             filter_name: str = None):
        # get frames
        infos = self._archive.list_frames(night=self._night, image_type=image_type, filter_name=filter_name,
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
        if len(images) < 3:
            log.warning('Too few (%d) frames found, skipping...', len(infos))

        # create master
        if image_type == ICamera.ImageType.BIAS:
            # BIAS are easy, just combine
            calib = BiasImage.create_master(images)

            # store in cache
            self._master_frames[BiasImage, instrument, binning, None] = calib

        elif image_type == ICamera.ImageType.DARK:
            # for DARKs, we first need a BIAS
            bias = self._find_master(BiasImage, instrument, binning, None)
            if bias is None:
                log.error('Could not find BIAS frame, skipping...')
                return

            # combine
            calib = DarkImage.create_master(images, bias=bias)

            # store in cache
            self._master_frames[DarkImage, instrument, binning, None] = calib

        elif image_type == ICamera.ImageType.SKYFLAT:
            # got enough frames?
            if len(images) < self._flats_min_raw:
                log.warning('Not enough flat fields found for combining.')
                return

            # for DARKs, we first ne a BIAS and a DARK
            bias = self._find_master(BiasImage, instrument, binning, None)
            dark = self._find_master(DarkImage, instrument, binning, None)
            if bias is None or dark is None:
                log.error('Could not find BIAS/DARK frame, skipping...')
                return

            # combine
            calib = FlatImage.create_master(images, bias=bias, dark=dark, method=self._flats_combine)

            # store in cache
            self._master_frames[FlatImage, instrument, binning, filter_name] = calib

        else:
            raise ValueError('Invalid image type')

        # filename
        calib.format_filename(self._fmt_calib)

        # upload
        log.info('Uploading master calibration frame as %s...', calib.header['FNAME'])
        self._archive.upload_frames([calib])

        # finished
        return calib

    def __call__(self):
        """Reduces all data im this night."""

        # get options
        log.info('Retrieving configurations for site %s at night %s...', self._site, self._night)
        options = self._archive.list_options(night=self._night, site=self._site)
        log.info('Got data for %d instruments, %d binnings, and %d filters.',
                 len(options['instruments']), len(options['binnings']), len(options['filters']))

        # loop instruments
        for instrument in options['instruments']:
            log.info('Reducing data for instrument %s...', instrument)

            # loop binnings
            for binning in options['binnings']:
                # create bias
                self._create_master_calib(instrument, ICamera.ImageType.BIAS, binning)

                # create dark
                self._create_master_calib(instrument, ICamera.ImageType.DARK, binning)

                # loop filters
                for filter_name in options['filters']:
                    # create flat
                    self._create_master_calib(instrument, ICamera.ImageType.SKYFLAT, binning, filter_name)

                    # calibrate science data
                    self._calib_data(instrument, binning, filter_name)


__all__ = ['Night']
