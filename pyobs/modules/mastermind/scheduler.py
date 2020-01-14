import functools
import json
import logging
import threading
import typing
from astroplan import AtNightConstraint, Transitioner, SequentialScheduler, Schedule
from astropy.time import TimeDelta
import astropy.units as u

from pyobs.utils.time import Time
from pyobs.interfaces import IStoppable, IRunnable
from pyobs import PyObsModule, get_object
from pyobs.robotic import TaskArchive


log = logging.getLogger(__name__)


class Scheduler(PyObsModule, IStoppable, IRunnable):
    """Scheduler."""

    def __init__(self, tasks: typing.Union[dict, TaskArchive], interval: int = 300, *args, **kwargs):
        """Initialize a new scheduler.

        Args:
            scheduler: Scheduler to use
            interval: Interval between scheduler updates
        """
        PyObsModule.__init__(self, *args, **kwargs)

        # get scheduler
        self._task_archive: TaskArchive = get_object(tasks, TaskArchive)

        # store
        self._interval = interval
        self._running = True
        self._need_update = False

        # blocks
        self._blocks = []
        self._scheduled_blocks = []

        # update thread
        self._add_thread_func(self._schedule_thread, True)
        self._add_thread_func(self._update_thread, True)

    def start(self, *args, **kwargs):
        """Start scheduler."""
        self._running = True

    def stop(self, *args, **kwargs):
        """Stop scheduler."""
        self._running = False

    def is_running(self, *args, **kwargs) -> bool:
        """Whether scheduler is running."""
        return self._running

    def _update_thread(self):
        # wait a little
        self.closing.wait(1)

        # run forever
        while not self.closing.is_set():
            # not running?
            if self._running is False:
                self.closing.wait(10)
                continue

            # get schedulable blocks and sort them
            blocks = sorted(self._task_archive.get_schedulable_blocks(),
                            key=lambda x: json.dumps(x.configuration, sort_keys=True))

            # did it change?
            # we compare the blocks' configurations, so they need to be unique
            equal = functools.reduce(lambda i, j: i and j,
                                     map(lambda m, k: m.configuration == k.configuration, blocks, self._blocks),
                                     True)
            if len(blocks) != len(self._blocks) or not equal:
                # store blocks and update schedule
                self._blocks = blocks
                self._need_update = True

            # sleep a little
            self.closing.wait(1)

    def _schedule_thread(self):
        # wait a little
        self.closing.wait(10)

        # only constraint is the night
        constraints = [AtNightConstraint.twilight_astronomical()]

        # we don't need any transitions
        transitioner = Transitioner()

        # run forever
        while not self.closing.is_set():
            # need update?
            if self._need_update:
                # reset need for update
                log.info('Calculating schedule for %d schedulable block(s)...', len(self._blocks))
                self._need_update = False

                # init scheduler and schedule
                scheduler = SequentialScheduler(constraints, self.observer, transitioner=transitioner)
                time_range = Schedule(Time.now(), Time.now() + TimeDelta(1 * u.day))
                schedule = scheduler(self._blocks, time_range)

                # update
                self._task_archive.update_schedule(schedule.scheduled_blocks)
                log.info('Finished calculating schedule for %d block(s).', len(schedule.scheduled_blocks))

            # sleep a little
            self.closing.wait(1)

    def run(self, *args, **kwargs):
        """Trigger a re-schedule."""
        self._need_update = True


__all__ = ['Scheduler']
