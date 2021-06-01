from threading import Event
import logging
from typing import Union, Dict, Tuple

from pyobs.object import get_object
from pyobs.robotic.scripts import Script
from pyobs.robotic.task import Task
from pyobs.utils.logger import DuplicateFilter
from pyobs.utils.time import Time

log = logging.getLogger(__name__)

# logger for logging name of task
task_name_logger = logging.getLogger(__name__ + ':task_name')
task_name_logger.addFilter(DuplicateFilter())


class ConfigStatus:
    """Status of a single configuration."""

    def __init__(self, state='ATTEMPTED', reason=''):
        """Initializes a new Status with an ATTEMPTED."""
        self.start = Time.now()
        self.end = None
        self.state = state
        self.reason = reason
        self.time_completed = 0

    def finish(self, state=None, reason=None, time_completed: int = 0) -> 'ConfigStatus':
        """Finish this status with the given values and the current time.

        Args:
            state: State of configuration
            reason: Reason for that state
            time_completed: Completed time [s]
        """
        if state is not None:
            self.state = state
        if reason is not None:
            self.reason = reason
        self.time_completed = time_completed
        self.end = Time.now()
        return self

    def to_json(self):
        """Convert status to JSON for sending to portal."""
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
    """A task from the LCO portal."""

    def __init__(self, config: dict, scripts: Dict[str, Script], *args, **kwargs):
        """Init LCO task (called request there).

        Args:
            config: Configuration for task
            scripts: External scripts to run
        """
        Task.__init__(self, *args, **kwargs)

        # store stuff
        self.config = config
        self.scripts = scripts
        self.cur_script = None

    @property
    def id(self) -> str:
        """ID of task."""
        return self.config['request']['id']

    @property
    def name(self) -> str:
        """Returns name of task."""
        return self.config['name']

    @property
    def duration(self) -> float:
        """Returns estimated duration of task in seconds."""
        return self.config['request']['duration']

    def __eq__(self, other: 'LcoTask'):
        """Compares to tasks."""
        return self.config == other.config

    @property
    def start(self) -> Time:
        """Start time for task"""
        return self.config['start']

    @property
    def end(self) -> Time:
        """End time for task"""
        return self.config['end']

    @property
    def observation_type(self) -> str:
        """Returns observation_type of this task.

        Returns:
            observation_type of this task.
        """
        return self.config['observation_type']

    @property
    def can_start_late(self) -> bool:
        """Whether this tasks is allowed to start later than the user-set time, e.g. for flatfields.

        Returns:
            True, if task can start late.
        """
        return self.observation_type == 'DIRECT'

    def _get_config_script(self, config: dict) -> Script:
        """Get config script for given configuration.

        Args:
            config: Config to create runner for.

        Returns:
            Script for running config

        Raises:
            ValueError: If could not create runner.
        """

        # what do we run?
        config_type = config['type']
        if config_type not in self.scripts:
            raise ValueError('No script found for configuration type "%s".' % config_type)

        # create script handler
        return get_object(self.scripts[config_type],
                          configuration=config, task_archive=self.task_archive, comm=self.comm, observer=self.observer)

    def can_run(self) -> bool:
        """Checks, whether this task could run now.

        Returns:
            True, if task can run now.
        """

        # get logger for task name and log
        task_name_logger.info(f'Checking whether task {self.name} can run...')

        # loop configurations
        req = self.config['request']
        for config in req['configurations']:
            # get config runner
            runner = self._get_config_script(config)

            # if any runner can run, we proceed
            try:
                if runner.can_run():
                    return True
            except Exception:
                log.exception('Error on evaluating whether task can run.')
                return False

        # no config found that could run
        return False

    def run(self, abort_event: Event):
        """Run a task

        Args:
            abort_event: Event to be triggered to abort task.
        """
        from pyobs.robotic.lco import LcoTaskArchive

        # get request
        req = self.config['request']

        # loop configurations
        for config in req['configurations']:
            # aborted?
            if abort_event.is_set():
                break

            # send an ATTEMPTED status
            if isinstance(self.task_archive, LcoTaskArchive):
                status = ConfigStatus()
                self.config['state'] = 'ATTEMPTED'
                self.task_archive.send_update(config['configuration_status'], status.finish().to_json())

            # get config runner
            script = self._get_config_script(config)

            # can run?
            if not script.can_run():
                log.warning('Cannot run config.')
                continue

            # run config
            log.info('Running config...')
            self.cur_script = script
            status = self._run_script(abort_event, script)
            self.cur_script = None

            # send status
            if status is not None and isinstance(self.task_archive, LcoTaskArchive):
                self.config['state'] = status.state
                self.task_archive.send_update(config['configuration_status'], status.to_json())

        # finished task
        log.info('Finished task.')

    def _run_script(self, abort_event, script: Script) -> Union[ConfigStatus, None]:
        """Run a config

        Args:
            abort_event: Event for signaling abort
            script: Script to run

        Returns:
            Configuration status to send to portal
        """

        # at least we tried...
        config_status = ConfigStatus()

        try:
            # check first
            self._check_abort(abort_event)

            # run it
            log.info('Running task %d: %s...', self.id, self.config['name'])
            script.run(abort_event)

            # finished config
            config_status.finish(state='COMPLETED', time_completed=script.exptime_done)

        except InterruptedError:
            log.warning('Task execution was interrupted.')
            config_status.finish(state='FAILED', reason='Task execution was interrupted.',
                                 time_completed=script.exptime_done)

        except Exception:
            log.exception('Something went wrong.')
            config_status.finish(state='FAILED', reason='Something went wrong', time_completed=script.exptime_done)

        # finished
        return config_status

    def is_finished(self) -> bool:
        """Whether task is finished."""
        return self.config['state'] != 'PENDING'

    def get_fits_headers(self, namespaces: list = None) -> dict:
        """Returns FITS header for the current status of this module.

        Args:
            namespaces: If given, only return FITS headers for the given namespaces.

        Returns:
            Dictionary containing FITS headers.
        """

        # get header from script
        hdr = self.cur_script.get_fits_headers(namespaces) if self.cur_script is not None else {}

        # return it
        return hdr


__all__ = ['LcoTask']
