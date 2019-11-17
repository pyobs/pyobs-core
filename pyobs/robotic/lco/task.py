from threading import Event
import logging
from typing import Union

from pyobs.comm import Comm
from pyobs.interfaces import ITelescope, ICamera, IFilters, ICameraBinning, ICameraWindow, IRoof, IMotion
from pyobs.robotic.task import Task
from pyobs.utils.threads import Future
from pyobs.utils.time import Time

log = logging.getLogger(__name__)


class CannotRunTask(Exception):
    pass


class LcoTask(Task):
    def __init__(self, task: dict, comm: Comm, telescope: str, camera: str, filters: str, roof: str,
                 *args, **kwargs):
        Task.__init__(self, *args, **kwargs)

        # store stuff
        self.task = task
        self.comm = comm
        self.telescope = telescope
        self.camera = camera
        self.filters = filters
        self.roof = roof

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

        # get proxies
        roof: IRoof = self.comm.proxy(self.roof, IRoof)
        telescope: ITelescope = self.comm.proxy(self.telescope, ITelescope)
        camera: ICamera = self.comm.proxy(self.camera, ICamera)
        filters: IFilters = self.comm.proxy(self.filters, IFilters)

        try:
            # loop configurations
            for config in req['configurations']:
                # run config
                status = self._run_config(abort_event, config, roof, telescope, camera, filters)

                # send status
                if status is not None and isinstance(self.scheduler, LcoScheduler):
                    self.scheduler.send_update(config['configuration_status'], status)

            # finished task
            self.task['state'] = 'COMPLETED'

        except InterruptedError:
            log.warning('Task execution was interrupted.')
            self.task['state'] = 'ABORTED'
            raise

    def _run_config(self, abort_event, config, roof, telescope, camera, filters) -> Union[dict, None]:
        # at least we tried...
        config_status = {'state': 'ATTEMPTED', 'summary': {'start': Time.now().isot}}

        # total exposure time
        exp_time_done = 0

        try:
            # check first
            self._check_abort(abort_event)

            # what do we run?
            if 'extra_params' in config and 'script_name' in config['extra_params']:
                # let's run some script, so get its name
                script_name = config['extra_params']['script_name']

                # which one is it?
                if script_name == 'skyflats':
                    exp_time_done += self._run_skyflats_config(abort_event, config, roof, telescope, camera, filters)
                else:
                    # unknown script
                    raise ValueError('Invalid script task type.')

            else:
                # seems to be a default task
                exp_time_done += self._run_default_config(abort_event, config, roof, telescope, camera, filters)

            # finished config
            config_status['state'] = 'COMPLETED'
            config_status['summary']['state'] = 'COMPLETED'

        except CannotRunTask:
            return None

        except InterruptedError:
            log.warning('Task execution was interrupted.')
            config_status['state'] = 'ATTEMPTED'
            config_status['summary']['state'] = 'ATTEMPTED'
            config_status['summary']['reason'] = 'Task execution was interrupted'

        except Exception:
            log.exception('Something went wrong.')
            config_status['state'] = 'FAILED'
            config_status['summary']['state'] = 'FAILED'
            config_status['summary']['reason'] = 'Something went wrong'

        # stop telescope and abort exposure
        telescope.stop_motion().wait()

        # finish filling config status
        config_status['summary']['end'] = Time.now().isot
        config_status['summary']['time_completed'] = exp_time_done

        # finished
        return config_status

    def _run_default_config(self, abort_event, config, roof, telescope, camera, filters) -> float:
        # get image type
        image_type = ICamera.ImageType.OBJECT
        if config['type'] == 'BIAS':
            image_type = ICamera.ImageType.BIAS
        elif config['type'] == 'DARK':
            image_type = ICamera.ImageType.DARK

        # we need an open roof and a working telescope for OBJECT exposures
        if image_type == ICamera.ImageType.OBJECT:
            if roof.get_motion_status().wait() not in [IMotion.Status.POSITIONED, IMotion.Status.TRACKING] or \
                    telescope.get_motion_status().wait() != IMotion.Status.IDLE:
                raise CannotRunTask

        # log
        log.info('Running default task %d: %s...', self.id, self.task['name'])

        # got a target?
        target = config['target']
        track = None
        if target['ra'] is not None and target['dec'] is not None:
            log.info('Moving to target %s...', target['name'])
            track = telescope.track_radec(target['ra'], target['dec'])

        # total exposure time in this config
        exp_time_done = 0

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

            # loop images
            for exp in range(ic['exposure_count']):
                self._check_abort(abort_event)
                log.info('Exposing %s image %d/%d for %.2fs...',
                         config['type'], exp + 1, ic['exposure_count'], ic['exposure_time'])
                camera.expose(int(ic['exposure_time'] * 1000), image_type).wait()
                exp_time_done += ic['exposure_time']

        # finally, return total exposure time
        return exp_time_done

    def _run_skyflats_config(self, abort_event, config, roof, telescope, camera, filters) -> float:
        # we need an open roof and a working telescope
        if roof.get_motion_status().wait() not in [IMotion.Status.POSITIONED, IMotion.Status.TRACKING] or \
                telescope.get_motion_status().wait() != IMotion.Status.IDLE:
            raise CannotRunTask

        # log
        log.info('Running skyflats task %d: %s...', self.id, self.task['name'])
        return 0.

    def is_finished(self) -> bool:
        """Whether task is finished."""
        return self.task['state'] != 'PENDING'

    def get_fits_headers(self) -> dict:
        return {}


__all__ = ['LcoTask']
