from threading import Event
import logging

from pyobs.interfaces import ITelescope, ICamera, IFilters, ICameraBinning, ICameraWindow
from pyobs.robotic.task import Task
from pyobs.utils.threads import Future
from pyobs.utils.time import Time


log = logging.getLogger(__name__)


class LcoTask(Task):
    def __init__(self, task: dict, telescope: str, camera: str, filters: str, *args, **kwargs):
        Task.__init__(self, *args, **kwargs)
        self._task = task

    def id(self) -> str:
        return self._task['request']['id']

    def window(self) -> (Time, Time):
        return self._task['start'], self._task['end']

    def run(self, abort_event: Event):
        # get request
        req = self._task['request']
        log.info('Running task %d: %s...', self.id, req['name'])

        # get proxies
        comm = self.scheduler.comm
        telescope: ITelescope = comm.proxy(self.scheduler.telescope, ITelescope)
        camera: ICamera = comm.proxy(self.scheduler.camera, ICamera)
        filters: IFilters = comm.proxy(self.scheduler.filters, IFilters)

        # loop configurations
        for config in req['configurations']:
            # got a target?
            target = config['target']
            track = None
            if target['ra'] is not None and target['dec'] is not None:
                log.info('Moving to target %s...', target['name'])
                track = telescope.track_radec(target['ra'], target['dec'])

            # get instrument config
            ic = config['instrument_configs']

            # set filter
            set_filter = None
            if 'optical_elements' in ic and 'filter' in ic['optical_elements']:
                log.info('Setting filter to %s...', ic['optical_elements']['filter'])
                set_filter = filters.set_filter(ic['optical_elements']['filter'])

            # wait for tracking and filter
            Future.wait_all([track, set_filter])

            # set binning and window
            if isinstance(camera, ICameraBinning):
                log.info('Set binning to %dx%d...', ic['bin_x'], ic['bin_x'])
                camera.set_binning(ic['bin_x'], ic['bin_x']).wait()
            if isinstance(camera, ICameraWindow):
                full_frame = camera.get_full_frame().wait()
                camera.set_window(**full_frame).wait()

            # decide on image type
            image_type = ICamera.ImageType.OBJECT
            if config['type'] == 'BIAS':
                image_type = ICamera.ImageType.BIAS
            elif config['type'] == 'DARK':
                image_type = ICamera.ImageType.DARK

            # loop images
            for exp in range(ic['exposure_count']):
                log.info('Exposing image %d/%d for %.2fs...', exp + 1, ic['exposure_count'], ic['exposure_time'])
                camera.expose(ic['exposure_time'], image_type).wait()

    def is_finished(self) -> bool:
        """Whether task is finished."""
        return self._task['state'] != 'PENDING'

    def get_fits_headers(self) -> dict:
        return {}


__all__ = ['LcoTask']
