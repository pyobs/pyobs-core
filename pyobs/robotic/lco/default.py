import logging
import time
import numpy as np
from typing import Union, Optional, Any, Tuple, cast, Dict, List

from pyobs.interfaces import IBinning, IWindow, IExposureTime, IRoof, IAutoGuiding, \
    ITelescope, IAcquisition, ICamera, IFilters, IImageType
from pyobs.robotic.scripts import Script
from pyobs.utils.enums import ImageType
from pyobs.utils.logger import DuplicateFilter
from pyobs.utils.parallel import Future


log = logging.getLogger(__name__)

# logger for logging name of task
cannot_run_logger = logging.getLogger(__name__ + ':cannot_run')
cannot_run_logger.addFilter(DuplicateFilter())


class LcoDefaultScript(Script):
    """Default script for LCO configs."""

    def __init__(self, camera: Union[str, ICamera], roof: Optional[Union[str, IRoof]] = None,
                 telescope: Optional[Union[str, ITelescope]] = None,
                 filters: Optional[Union[str, IFilters]] = None,
                 autoguider: Optional[Union[str, IAutoGuiding]] = None,
                 acquisition: Optional[Union[str, IAcquisition]] = None, **kwargs: Any):
        """Initialize a new LCO default script.

        Args:
            roof: Roof to use
            telescope: Telescope to use
            camera: Camera to use
            filters: Filter wheel to use
            autoguider: Autoguider to use
            acquisition: Acquisition to use
        """
        Script.__init__(self, **kwargs)

        # store
        self.roof = roof
        self.telescope = telescope
        self.camera = camera
        self.filters = filters
        self.autoguider = autoguider
        self.acquisition = acquisition

        # get image type
        self.image_type = ImageType.OBJECT
        if self.configuration['type'] == 'BIAS':
            self.image_type = ImageType.BIAS
        elif self.configuration['type'] == 'DARK':
            self.image_type = ImageType.DARK

    async def _get_proxies(self) -> Tuple[Optional[IRoof], Optional[ITelescope], Optional[ICamera],
                                          Optional[IFilters], Optional[IAutoGuiding], Optional[IAcquisition]]:
        """Get proxies for running the task

        Returns:
            Proxies for roof, telescope, camera and filter wheel

        Raises:
            ValueError: If could not get proxies for all modules
        """
        roof = await self.comm.safe_proxy(self.roof, IRoof)
        telescope = await self.comm.safe_proxy(self.telescope, ITelescope)
        camera = await self.comm.safe_proxy(self.camera, ICamera)
        filters = await self.comm.safe_proxy(self.filters, IFilters)
        autoguider = await self.comm.safe_proxy(self.autoguider, IAutoGuiding)
        acquisition = await self.comm.safe_proxy(self.acquisition, IAcquisition)
        return roof, telescope, camera, filters, autoguider, acquisition

    async def can_run(self) -> bool:
        """Whether this config can currently run.

        Returns:
            True, if script can run now
        """

        # get proxies
        roof, telescope, camera, filters, autoguider, acquisition = await self._get_proxies()

        # need camera
        if camera is None:
            cannot_run_logger.info('Cannot run task, no camera found.')
            return False

        # for OBJECT exposure we need more
        if self.image_type == ImageType.OBJECT:
            # we need an open roof and a working telescope
            if roof is None or not await roof.is_ready():
                cannot_run_logger.warning('Cannot run task, no roof found or roof not ready.')
                return False
            if telescope is None or not await telescope.is_ready():
                cannot_run_logger.warning('Cannot run task, no telescope found or telescope not ready.')
                return False

            # we probably need filters and autoguider/acquisition
            if filters is None:
                cannot_run_logger.warning('Cannot run task, No filter module found.')
                return False

            # acquisition?
            if 'acquisition_config' in self.configuration and 'mode' in self.configuration['acquisition_config'] and \
                    self.configuration['acquisition_config']['mode'] == 'ON' and acquisition is None:
                cannot_run_logger.warning('Cannot run task, no acquisition found.')
                return False

            # guiding?
            if 'guiding_config' in self.configuration and 'mode' in self.configuration['guiding_config'] and \
                    self.configuration['guiding_config']['mode'] == 'ON' and autoguider is None:
                cannot_run_logger.warning('Cannot run task, no auto guider found.')
                return False

        # seems alright
        return True

    async def run(self) -> None:
        """Run script.

        Raises:
            InterruptedError: If interrupted
        """

        # get proxies
        roof, telescope, camera, filters, autoguider, acquisition = await self._get_proxies()

        # got a target?
        target = self.configuration['target']
        track = Future[None](empty=True)
        if self.image_type == ImageType.OBJECT:
            if telescope is None:
                raise ValueError('No telescope given.')
            log.info('Moving to target %s...', target['name'])
            track = await telescope.move_radec(target['ra'], target['dec'])

        # acquisition?
        if 'acquisition_config' in self.configuration and 'mode' in self.configuration['acquisition_config'] and \
                self.configuration['acquisition_config']['mode'] == 'ON':
            # wait for track
            await track

            # do acquisition
            if acquisition is None:
                raise ValueError('No acquisition given.')
            log.info('Performing acquisition...')
            await acquisition.acquire_target()

        # guiding?
        if 'guiding_config' in self.configuration and 'mode' in self.configuration['guiding_config'] and \
                self.configuration['guiding_config']['mode'] == 'ON':
            if autoguider is None:
                raise ValueError('No autoguider given.')
            log.info('Starting auto-guiding...')
            await autoguider.start()

        # total (exposure) time done in this config
        self.exptime_done = 0.

        # task archive must be LCO
        from pyobs.robotic.lco import LcoTaskArchive
        if not isinstance(self.task_archive, LcoTaskArchive):
            raise ValueError('Task archive is not for LCO observation portal.')

        # get instrument info
        instrument_type = self.configuration['instrument_type'].lower()
        instrument = self.task_archive.instruments[instrument_type]

        # setting repeat duration depending on config type
        repeat_duration = None
        if self.configuration['type'] == 'REPEAT_EXPOSE':
            if 'repeat_duration' in self.configuration:
                repeat_duration = self.configuration['repeat_duration']
                log.info('Repeating all instrument configurations for %d seconds.', repeat_duration)
            else:
                log.error('Type is REPEAT_EXPOSE, but no repeat_duration was set.')

        # config iterations
        config_finished = False
        ic_durations = []
        while not config_finished:
            # ic start time
            ic_start_time = time.time()

            # loop instrument configs
            for ic in self.configuration['instrument_configs']:
                # get readout mode
                for readout_mode in instrument['modes']['readout']['modes']:
                    if readout_mode['code'] == ic['mode']:
                        break
                else:
                    # could not find readout mode
                    raise ValueError('Could not find readout mode %s.' % ic['mode'])
                log.info('Using readout mode "%s"...' % readout_mode['name'])

                # set filter
                set_filter = Future[None](empty=True)
                if 'optical_elements' in ic and 'filter' in ic['optical_elements'] and filters is not None:
                    log.info('Setting filter to %s...', ic['optical_elements']['filter'])
                    set_filter = await filters.set_filter(ic['optical_elements']['filter'])

                # wait for tracking and filter
                await Future.wait_all([track, set_filter])

                # set binning and window
                if isinstance(camera, IBinning):
                    bin_x = readout_mode['validation_schema']['bin_x']['default']
                    bin_y = readout_mode['validation_schema']['bin_y']['default']
                    log.info('Set binning to %dx%d...', bin_x, bin_y)
                    await camera.set_binning(bin_x, bin_y)
                if isinstance(camera, IWindow):
                    full_frame = await camera.get_full_frame()
                    await camera.set_window(*full_frame)

                # loop images
                for exp in range(ic['exposure_count']):
                    # do exposures
                    if isinstance(camera, IExposureTime):
                        log.info('Exposing %s image %d/%d for %.2fs...',
                                 self.configuration['type'], exp + 1, ic['exposure_count'], ic['exposure_time'])
                        await camera.set_exposure_time(ic['exposure_time'])
                    else:
                        log.info('Exposing %s image %d/%d...',
                                 self.configuration['type'], exp + 1, ic['exposure_count'])
                    if isinstance(camera, IImageType):
                        await camera.set_image_type(self.image_type)
                    await cast(ICamera, camera).grab_image()
                    self.exptime_done += ic['exposure_time']

            # store duration for all ICs
            ic_durations.append(time.time() - ic_start_time)

            # need repeat?
            if repeat_duration is None:
                # if there is no repeat duration, we're finished
                config_finished = True

            else:
                # get average IC duration
                avg_ic_duration = np.mean(ic_durations)

                # can we do another one, i.e. is done time plus average time larger than repeat_duration?
                if sum(ic_durations) + avg_ic_duration > repeat_duration:
                    # doesn't seem so
                    config_finished = True

        # stop auto guiding
        if 'guiding_config' in self.configuration and 'mode' in self.configuration['guiding_config'] and \
                self.configuration['guiding_config']['mode'] == 'ON' and autoguider is not None:
            log.info('Stopping auto-guiding...')
            await autoguider.stop()

        # finally, stop telescope
        if self.image_type == ImageType.OBJECT:
            log.info('Stopping telescope...')
            await cast(ITelescope, telescope).stop_motion()

    def get_fits_headers(self, namespaces: Optional[List[str]] = None) -> Dict[str, Any]:
        """Returns FITS header for the current status of this module.

        Args:
            namespaces: If given, only return FITS headers for the given namespaces.

        Returns:
            Dictionary containing FITS headers.
        """

        # init header
        hdr = {}

        # which image type?
        if self.image_type == ImageType.OBJECT:
            # add object name
            hdr['OBJECT'] = self.configuration['target']['name'], 'Name of target'

        # return
        return hdr


__all__ = ['LcoDefaultScript']
