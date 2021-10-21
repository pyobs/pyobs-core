import logging
import threading
import time
import numpy as np
from typing import Union, Type

from pyobs.interfaces.proxies import IBinningProxy, IWindowProxy, IExposureTimeProxy, IRoofProxy, IAutoGuidingProxy, \
    ITelescopeProxy, IAcquisitionProxy, ICameraProxy, IFiltersProxy, IImageTypeProxy
from pyobs.robotic.scripts import Script
from pyobs.utils.enums import ImageType
from pyobs.utils.logger import DuplicateFilter
from pyobs.utils.threads import Future


log = logging.getLogger(__name__)

# logger for logging name of task
cannot_run_logger = logging.getLogger(__name__ + ':cannot_run')
cannot_run_logger.addFilter(DuplicateFilter())


class LcoDefaultScript(Script):
    """Default script for LCO configs."""

    def __init__(self, camera: Union[str, ICameraProxy], roof: Union[str, IRoofProxy] = None,
                 telescope: Union[str, ITelescopeProxy] = None, filters: Union[str, IFiltersProxy] = None,
                 autoguider: Union[str, IAutoGuidingProxy] = None, acquisition: Union[str, IAcquisitionProxy] = None,
                 *args, ** kwargs):
        """Initialize a new LCO default script.

        Args:
            roof: Roof to use
            telescope: Telescope to use
            camera: Camera to use
            filters: Filter wheel to use
            autoguider: Autoguider to use
            acquisition: Acquisition to use
        """
        Script.__init__(self, *args, **kwargs)

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

    def _get_proxies(self) -> (IRoofProxy, ITelescopeProxy, ICameraProxy, IFiltersProxy,
                               IAutoGuidingProxy, IAcquisitionProxy):
        """Get proxies for running the task

        Returns:
            Proxies for roof, telescope, camera and filter wheel

        Raises:
            ValueError: If could not get proxies for all modules
        """
        roof: IRoofProxy = self._get_proxy(self.roof, IRoofProxy)
        telescope: ITelescopeProxy = self._get_proxy(self.telescope, ITelescopeProxy)
        camera: ICameraProxy = self._get_proxy(self.camera, ICameraProxy)
        filters: IFiltersProxy = self._get_proxy(self.filters, IFiltersProxy)
        autoguider: IAutoGuidingProxy = self._get_proxy(self.autoguider, IAutoGuidingProxy)
        acquisition: IAcquisitionProxy = self._get_proxy(self.acquisition, IAcquisitionProxy)
        return roof, telescope, camera, filters, autoguider, acquisition

    def can_run(self) -> bool:
        """Whether this config can currently run.

        Returns:
            True, if script can run now
        """

        # get proxies
        roof, telescope, camera, filters, autoguider, acquisition = self._get_proxies()

        # need camera
        if camera is None:
            cannot_run_logger.info('Cannot run task, no camera found.')
            return False

        # for OBJECT exposure we need more
        if self.image_type == ImageType.OBJECT:
            # we need an open roof and a working telescope
            if roof is None or not roof.is_ready().wait():
                cannot_run_logger.warning('Cannot run task, no roof found or roof not ready.')
                return False
            if telescope is None or not telescope.is_ready().wait():
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

    def run(self, abort_event: threading.Event):
        """Run script.

        Args:
            abort_event: Event to abort run.

        Raises:
            InterruptedError: If interrupted
        """

        # get proxies
        roof, telescope, camera, filters, autoguider, acquisition = self._get_proxies()

        # got a target?
        target = self.configuration['target']
        track = None
        if self.image_type == ImageType.OBJECT:
            log.info('Moving to target %s...', target['name'])
            track = telescope.move_radec(target['ra'], target['dec'])

        # acquisition?
        if 'acquisition_config' in self.configuration and 'mode' in self.configuration['acquisition_config'] and \
                self.configuration['acquisition_config']['mode'] == 'ON':
            # wait for track
            track.wait()

            # do acquisition
            log.info('Performing acquisition...')
            acquisition.acquire_target().wait()

        # guiding?
        if 'guiding_config' in self.configuration and 'mode' in self.configuration['guiding_config'] and \
                self.configuration['guiding_config']['mode'] == 'ON':
            log.info('Starting auto-guiding...')
            autoguider.start().wait()

        # total (exposure) time done in this config
        self.exptime_done = 0

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
                self._check_abort(abort_event)

                # get readout mode
                for readout_mode in instrument['modes']['readout']['modes']:
                    if readout_mode['code'] == ic['mode']:
                        break
                else:
                    # could not find readout mode
                    raise ValueError('Could not find readout mode %s.' % ic['mode'])
                log.info('Using readout mode "%s"...' % readout_mode['name'])

                # set filter
                set_filter = None
                if 'optical_elements' in ic and 'filter' in ic['optical_elements']:
                    log.info('Setting filter to %s...', ic['optical_elements']['filter'])
                    set_filter = filters.set_filter(ic['optical_elements']['filter'])

                # wait for tracking and filter
                Future.wait_all([track, set_filter])

                # set binning and window
                if isinstance(camera, IBinningProxy):
                    bin_x = readout_mode['validation_schema']['bin_x']['default']
                    bin_y = readout_mode['validation_schema']['bin_y']['default']
                    log.info('Set binning to %dx%d...', bin_x, bin_y)
                    camera.set_binning(bin_x, bin_y).wait()
                if isinstance(camera, IWindowProxy):
                    full_frame = camera.get_full_frame().wait()
                    camera.set_window(*full_frame).wait()

                # loop images
                for exp in range(ic['exposure_count']):
                    self._check_abort(abort_event)

                    # do exposures
                    if isinstance(camera, IExposureTimeProxy):
                        log.info('Exposing %s image %d/%d for %.2fs...',
                                 self.configuration['type'], exp + 1, ic['exposure_count'], ic['exposure_time'])
                        camera.set_exposure_time(ic['exposure_time']).wait()
                    else:
                        log.info('Exposing %s image %d/%d...',
                                 self.configuration['type'], exp + 1, ic['exposure_count'])
                    if isinstance(camera, IImageTypeProxy):
                        camera.set_image_type(self.image_type).wait()
                    camera.expose().wait()
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
                self.configuration['guiding_config']['mode'] == 'ON':
            log.info('Stopping auto-guiding...')
            autoguider.stop().wait()

        # finally, stop telescope
        if not abort_event.is_set():
            if self.image_type == ImageType.OBJECT:
                log.info('Stopping telescope...')
                telescope.stop_motion().wait()

    def get_fits_headers(self, namespaces: list = None) -> dict:
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
