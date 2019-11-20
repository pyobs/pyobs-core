from threading import Event
import logging
from typing import Union

from pyobs.comm import Comm
from pyobs.interfaces import ITelescope, ICamera, IFilters, ICameraBinning, ICameraWindow, IRoof, IMotion
from pyobs.robotic.lco.configs import LcoDefaultConfig, LcoSkyFlatsConfig
from pyobs.robotic.task import Task
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
        log.info('Getting proxies for modules...')
        roof: IRoof = self.comm.proxy(self.roof, IRoof)
        telescope: ITelescope = self.comm.proxy(self.telescope, ITelescope)
        camera: ICamera = self.comm.proxy(self.camera, ICamera)
        filters: IFilters = self.comm.proxy(self.filters, IFilters)

        try:
            # loop configurations
            for config in req['configurations']:
                # run config
                log.info('Running config...')
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
                    cfg_runner = LcoSkyFlatsConfig(config, roof, telescope, camera, filters)
                else:
                    # unknown script
                    raise ValueError('Invalid script task type.')

            else:
                # seems to be a default task
                log.info('Creating default configuration...')
                cfg_runner = LcoDefaultConfig(config, roof, telescope, camera, filters)

            # can we run it?
            if not cfg_runner.can_run():
                return None

            # run it
            log.info('Running task %d: %s...', self.id, self.task['name'])
            exp_time_done += cfg_runner(abort_event)

            # finished config
            config_status['state'] = 'COMPLETED'
            config_status['summary']['state'] = 'COMPLETED'

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

    def is_finished(self) -> bool:
        """Whether task is finished."""
        return self.task['state'] != 'PENDING'

    def get_fits_headers(self) -> dict:
        return {}


__all__ = ['LcoTask']
