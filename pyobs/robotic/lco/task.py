from threading import Event
import logging

from pyobs.comm import Comm
from pyobs.interfaces import ITelescope, ICamera, IFilters, ICameraBinning, ICameraWindow
from pyobs.robotic.task import Task
from pyobs.utils.threads import Future
from pyobs.utils.time import Time


log = logging.getLogger(__name__)


class LcoTask(Task):
    def __init__(self, task: dict, comm: Comm, telescope: str, camera: str, filters: str, *args, **kwargs):
        Task.__init__(self, *args, **kwargs)

        # store stuff
        self.task = task
        self.comm = comm
        self.telescope = telescope
        self.camera = camera
        self.filters = filters

    @property
    def id(self) -> str:
        return self.task['request']['id']

    def name(self) -> str:
        return self.task['name']

    def window(self) -> (Time, Time):
        return self.task['start'], self.task['end']

    def run(self, abort_event: Event):
        """Run a task

        Args:
            abort_event: Event to be triggered to abort task.
        """
        from pyobs.robotic.lco import LcoScheduler

        # get request
        req = self.task['request']
        log.info('Running task %d: %s...', self.id, self.task['name'])

        # get proxies
        telescope: ITelescope = self.comm.proxy(self.telescope, ITelescope)
        camera: ICamera = self.comm.proxy(self.camera, ICamera)
        filters: IFilters = self.comm.proxy(self.filters, IFilters)

        try:
            # loop configurations
            for config in req['configurations']:
                # run config
                status = self._run_config(abort_event, config, telescope, camera, filters)

                # send status
                if isinstance(self.scheduler, LcoScheduler):
                    self.scheduler.send_update(config['configuration_status'], status)

            # finished task
            self.task['state'] = 'COMPLETED'

        except InterruptedError:
            log.warning('Task execution was interrupted.')
            self.task['state'] = 'ABORTED'
            raise

    def _run_config(self, abort_event, config, telescope, camera,  filters) -> dict:
        # at least we tried...
        config_status = {'state': 'ATTEMPTED'}

        try:
            # check first
            self._check_abort(abort_event)

            # got a target?
            target = config['target']
            track = None
            if target['ra'] is not None and target['dec'] is not None:
                log.info('Moving to target %s...', target['name'])
                track = telescope.track_radec(target['ra'], target['dec'])

            # loop instrument configs
            for ic in config['instrument_configs']:
                self._check_abort(abort_event)

                # set filter
                set_filter = None
                if 'optical_elements' in ic and 'filter' in ic['optical_elements']:
                    log.info('Setting filter to %s...', ic['optical_elements']['filter'])
                    set_filter = filters.set_filter(ic['optical_elements']['filter'])

                # wait for tracking and filter
                Future.wait_all([track, set_filter])

                # set binning and window
                self._check_abort(abort_event)
                if isinstance(camera, ICameraBinning):
                    log.info('Set binning to %dx%d...', ic['bin_x'], ic['bin_x'])
                    camera.set_binning(ic['bin_x'], ic['bin_x']).wait()
                if isinstance(camera, ICameraWindow):
                    full_frame = camera.get_full_frame().wait()
                    camera.set_window(*full_frame).wait()

                # decide on image type
                image_type = ICamera.ImageType.OBJECT
                if config['type'] == 'BIAS':
                    image_type = ICamera.ImageType.BIAS
                elif config['type'] == 'DARK':
                    image_type = ICamera.ImageType.DARK

                # loop images
                for exp in range(ic['exposure_count']):
                    self._check_abort(abort_event)
                    log.info('Exposing %s image %d/%d for %.2fs...',
                             config['type'], exp + 1, ic['exposure_count'], ic['exposure_time'])
                    camera.expose(int(ic['exposure_time'] * 1000), image_type).wait()

            # finished config
            config_status['state'] = 'COMPLETED'

        except InterruptedError:
            log.warning('Task execution was interrupted.')
            config_status['state'] = 'ATTEMPTED'

        except Exception:
            log.exception('Something went wrong.')
            config_status['state'] = 'FAILED'

        finally:
            # stop telescope and abort exposure
            telescope.stop_motion().wait()

        # finished
        return config_status

    def is_finished(self) -> bool:
        """Whether task is finished."""
        return self.task['state'] != 'PENDING'

    def get_fits_headers(self) -> dict:
        return {}


__all__ = ['LcoTask']
