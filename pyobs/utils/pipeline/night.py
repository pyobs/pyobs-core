import logging
import os.path
from multiprocessing import Pool
from typing import Union, Type, Dict, Tuple, Optional, List

from pyobs.object import get_object
from pyobs.utils.time import Time
from pyobs.utils.fits import FilenameFormatter
from pyobs.images import Image
from pyobs.utils.archive import Archive
from pyobs.utils.enums import ImageType
from .pipeline import Pipeline

log = logging.getLogger(__name__)


class Night:
    def __init__(self, archive: Union[dict, Archive], pipeline: Union[dict, Pipeline], worker_procs: int = 4,
                 filenames_calib: str = '{SITEID}{TELID}-{INSTRUME}-{DAY-OBS|date:}-'
                                        '{IMAGETYP}-{XBINNING}x{YBINNING}{FILTER|filter}.fits',
                 min_flats: int = 10, store_local: str = None, create_calibs: bool = True, calib_science: bool = True,
                 *args, **kwargs):
        """Creates a Night object for reducing a given night.

        Args:
            archive: Archive to fetch images from and write results to.
            pipeline: Science pipeline.
            worker_procs: Number of worker processes.
            filenames_calib: Filename pattern for master calibration files.
            min_flats: Minimum number of raw frames to create flat field.
            store_local: If True, files are stored in given local directory instead of uploaded to archive.
            create_calibs: If False, no calibration files are created for night.
            calib_science: If False, no science frames are calibrated.
        """

        # get archive and science pipeline
        self._archive = get_object(archive, Archive)
        self._pipeline = get_object(pipeline, Pipeline, archive=archive)

        # stuff
        self._worker_processes = worker_procs
        self._min_flats = min_flats
        self._store_local = store_local
        self._create_calibs = create_calibs
        self._calib_science = calib_science

        # cache for master calibration frames
        self._master_frames: Dict[Tuple[ImageType, str, str, Optional[str]], Image] = {}

        # default filename patterns
        self._fmt_calib = FilenameFormatter(filenames_calib)

    def _find_master(self, night: str, image_type: ImageType, instrument: str, binning: str,
                     filter_name: str = None, max_days: float = 30.) -> Optional[Image]:
        """Find master calibration frame for given parameters using a cache.

        Args:
            image_type: image type.
            instrument: Instrument name.
            binning: Binning.
            filter_name: Name of filter.
            max_days: Maximum number of days from DATE-OBS to find frames.

        Returns:
            Image or None
        """

        # is in cache?
        if (image_type, instrument, binning, filter_name) in self._master_frames:
            return self._master_frames[image_type, instrument, binning, filter_name]

        # try to download one
        midnight = Time(night + ' 23:59:59')
        image = self._pipeline.find_master(self._archive, image_type, midnight, instrument, binning, filter_name,
                                           max_days=max_days)
        if image is not None:
            # store and return it
            self._master_frames[image_type, instrument, binning, filter_name] = image
            return image
        else:
            # still nothing
            return None

    def _create_master_calib(self, night: str, instrument: str, image_type: ImageType, binning: str,
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
        if len(images) < 3:
            log.warning('Too few (%d) frames found, skipping...', len(infos))

        # create master
        if image_type == ImageType.BIAS:
            # BIAS are easy, just combine
            calib = self._pipeline.create_master_bias(images)

            # store in cache
            self._master_frames[ImageType.BIAS, instrument, binning, None] = calib

        elif image_type == ImageType.DARK:
            # for DARKs, we first need a BIAS
            bias = self._find_master(night, ImageType.BIAS, instrument, binning, None)
            if bias is None:
                log.error('Could not find BIAS frame, skipping...')
                return

            # combine
            calib = self._pipeline.create_master_dark(images, bias=bias)

            # store in cache
            self._master_frames[ImageType.DARK, instrument, binning, None] = calib

        elif image_type == ImageType.SKYFLAT:
            # got enough frames?
            if len(images) < self._min_flats:
                log.warning('Not enough flat fields found for combining.')
                return

            # for SKYFLATs, we first need a BIAS
            bias = self._find_master(night, ImageType.BIAS, instrument, binning, None)
            if bias is None:
                log.error('Could not find BIAS frame, skipping...')
                return

            # combine
            calib = self._pipeline.create_master_flat(images, bias=bias)

            # store in cache
            self._master_frames[ImageType.SKYFLAT, instrument, binning, filter_name] = calib

        else:
            raise ValueError('Invalid image type')

        # filename
        calib.format_filename(self._fmt_calib)

        # save/upload
        if self._store_local:
            path = os.path.join(self._store_local, calib.header['FNAME'])
            log.info('Storing master calibration frame as %s...', path)
            calib.writeto(path, overwrite=True)
        else:
            log.info('Uploading master calibration frame as %s...', calib.header['FNAME'])
            self._archive.upload_frames([calib])

        # finished
        return calib

    def _calib_data(self, night: str, instrument: str, binning: str, filter_name: str):
        # get all frames
        infos = self._archive.list_frames(night=night, instrument=instrument,
                                          image_type=ImageType.OBJECT, binning=binning, filter_name=filter_name,
                                          rlevel=0)
        total = len(infos)
        if total == 0:
            return
        log.info('Calibrating %d OBJECT frames...', total)

        # run all science frames
        for i, info in enumerate(infos, 1):
            # temporary fix
            if 'e01' in info.filename:
                continue
            log.info('(%d/%d) Calibrating file %s...', i, total, info.filename)

            try:
                # download frame
                image = self._archive.download_frames([info])[0]

                # calibrate
                calibrated = self._pipeline.calibrate(image)

                # save/upload
                if self._store_local:
                    path = os.path.join(self._store_local, calibrated.header['FNAME'])
                    log.info('(%d/%d) Storing calibrated images as %s...', i, total, path)
                    calibrated.writeto(path, overwrite=True)
                else:
                    log.info('(%d/%d) Uploading calibrated images as %s...', i, total, calibrated.header['FNAME'])
                    self._archive.upload_frames([calibrated])

            except Exception:
                log.exception('(%d/%d) Error processing image %s.', i, total, info.filename)

    def __call__(self, site: str, night: str):
        """Reduces all data im this night."""

        # get options
        log.info('Retrieving configurations for site %s at night %s...', site, night)
        options = self._archive.list_options(night=night, site=site)
        log.info('Got data for %d instruments, %d binnings, and %d filters.',
                 len(options['instruments']), len(options['binnings']), len(options['filters']))

        # loop instruments
        for instrument in options['instruments']:
            log.info('Reducing data for instrument %s...', instrument)

            # loop binnings
            for binning in options['binnings']:
                # create bias and dark
                if self._create_calibs:
                    self._create_master_calib(night, instrument, ImageType.BIAS, binning)
                    self._create_master_calib(night, instrument, ImageType.DARK, binning)

                # loop filters
                for filter_name in options['filters']:
                    # create flat
                    if self._create_calibs:
                        self._create_master_calib(night, instrument, ImageType.SKYFLAT, binning, filter_name)

                    if filter_name != 'Green':
                        continue

                    # calibrate science data
                    if self._calib_science:
                        self._calib_data(night, instrument, binning, filter_name)


__all__ = ['Night']
