from threading import Event
import logging
from typing import Union

from pyobs.comm import Comm
from pyobs.interfaces import ITelescope, ICamera, IFilters, ICameraBinning, ICameraWindow, IRoof, IMotion
from pyobs.robotic.lco.configs import LcoDefaultConfig, LcoSkyFlatsConfig
from pyobs.robotic.task import Task
from pyobs.utils.time import Time

log = logging.getLogger(__name__)


class ConfigStatus:
    def __init__(self):
        self.start = Time.now()
        self.end = None
        self.state = 'ATTEMPTED'
        self.reason = ''
        self.time_completed = 0

    def finish(self, state=None, reason=None, time_completed: int = 0):
        if state is not None:
            self.state = state
        if reason is not None:
            self.reason = reason
        self.time_completed = time_completed
        self.end = Time.now()

    def to_json(self):
        return {
            'state': self.state,
            'summary': {
                'state': self.state,
                'reason': self.reason,
                'start': self.start.isot,
                'end': self.end.isot,
                'time_completed': self.time_completed
            }
        }


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
        try:
            roof: IRoof = self.comm.proxy(self.roof, IRoof)
            telescope: ITelescope = self.comm.proxy(self.telescope, ITelescope)
            camera: ICamera = self.comm.proxy(self.camera, ICamera)
            filters: IFilters = self.comm.proxy(self.filters, IFilters)

        except ValueError:
            # fail all configs
            log.error('Could not get proxies.')
            for config in req['configurations']:
                # create failed status for config
                status = ConfigStatus()
                status.finish(state='FAILED', reason='System failure.')

                # send status
                if isinstance(self.scheduler, LcoScheduler):
                    self.scheduler.send_update(config['configuration_status'], status.to_json())

            # finish
            return

        # loop configurations
        for config in req['configurations']:
            # aborted?
            if abort_event.is_set():
                return

            # run config
            log.info('Running config...')
            status = self._run_config(abort_event, config, roof, telescope, camera, filters)

            # send status
            if status is not None and isinstance(self.scheduler, LcoScheduler):
                self.scheduler.send_update(config['configuration_status'], status.to_json())

    def _run_config(self, abort_event, config, roof, telescope, camera, filters) -> Union[ConfigStatus, None]:
        # at least we tried...
        config_status = ConfigStatus()

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
                log.warning('Cannot run config.')
                return None

            # run it
            log.info('Running task %d: %s...', self.id, self.task['name'])
            exp_time_done += cfg_runner(abort_event)

            # finished config
            config_status.finish(state='COMPLETED', time_completed=exp_time_done)

        except InterruptedError:
            log.warning('Task execution was interrupted.')
            config_status.finish(state='ATTEMPTED', reason='Task execution was interrupted.',
                                 time_completed=exp_time_done)

        except Exception:
            log.exception('Something went wrong.')
            config_status.finish(state='FAILED', reason='Something went wrong', time_completed=exp_time_done)

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
