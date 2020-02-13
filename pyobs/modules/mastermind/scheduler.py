import functools
import json
import logging
import threading
import typing
from astroplan import AtNightConstraint, Transitioner, SequentialScheduler, Schedule
from astropy.time import TimeDelta
import astropy.units as u
from pyobs.events.taskstarted import TaskStartedEvent

from pyobs.events import GoodWeatherEvent

from pyobs.utils.time import Time
from pyobs.interfaces import IStoppable, IRunnable
from pyobs import PyObsModule, get_object
from pyobs.robotic import TaskArchive


log = logging.getLogger(__name__)


class Scheduler(PyObsModule, IStoppable, IRunnable):
    """Scheduler."""

    def __init__(self, tasks: typing.Union[dict, TaskArchive], schedule_range: int = 24, safety_time: int = 60,
                 *args, **kwargs):
        """Initialize a new scheduler.

        Args:
            scheduler: Scheduler to use
            schedule_range: Number of hours to schedule into the future
            safety_time: If no ETA for next task to start exists (from current task, weather became good, etc), use
                         this time in seconds to make sure that we don't schedule for a time when the scheduler is
                         still running
        """
        PyObsModule.__init__(self, *args, **kwargs)

        # get scheduler
        self._task_archive: TaskArchive = get_object(tasks, TaskArchive)

        # store
        self._schedule_range = schedule_range
        self._safety_time = safety_time
        self._running = True
        self._need_update = False

        # time to start next schedule from
        self._schedule_start = None

        # blocks
        self._blocks = []
        self._scheduled_blocks = []

        # update thread
        self._add_thread_func(self._schedule_thread, True)
        self._add_thread_func(self._update_thread, True)

    def open(self):
        """Open module."""
        PyObsModule.open(self)

        # subscribe to events
        if self.comm:
            self.comm.register_event(TaskStartedEvent, self._on_task_started)
            self.comm.register_event(GoodWeatherEvent, self._on_good_weather)

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
        # time of last change in blocks
        last_change = None

        # run forever
        while not self.closing.is_set():
            # not running?
            if self._running is False:
                self.closing.wait(1)
                continue

            # got new time of last change?
            t = self._task_archive.last_changed()
            if last_change is None or last_change < t:
                # get schedulable blocks and sort them
                log.info('Found update in schedulable block, downloading them...')
                self._blocks = sorted(self._task_archive.get_schedulable_blocks(),
                                      key=lambda x: json.dumps(x.configuration, sort_keys=True))
                log.info('Downloaded %d schedulable block(s).', len(self._blocks))

                # schedule update
                log.info('Triggering scheduler run...')
                self._need_update = True

                # remember now
                last_change = Time.now()

            # sleep a little
            self.closing.wait(5)

    def _schedule_thread(self):
        # only constraint is the night
        constraints = [AtNightConstraint.twilight_astronomical()]

        # we don't need any transitions
        transitioner = Transitioner()

        # run forever
        while not self.closing.is_set():
            # need update?
            if self._need_update:
                # reset need for update
                self._need_update = False

                # get start time for scheduler
                start = self._schedule_start
                now_plus_safety = Time.now() + self._safety_time * u.second
                if start is None or start < now_plus_safety:
                    # if no ETA exists or is in the past, use safety time
                    start = now_plus_safety

                # log it
                log.info('Calculating schedule for %d schedulable block(s) starting at %s...', len(self._blocks), start)

                # init scheduler and schedule
                scheduler = SequentialScheduler(constraints, self.observer, transitioner=transitioner)
                time_range = Schedule(start, start + TimeDelta(self._schedule_range * u.hour))
                schedule = scheduler(self._blocks, time_range)

                # update
                self._task_archive.update_schedule(schedule.scheduled_blocks)
                log.info('Finished calculating schedule for %d block(s).', len(schedule.scheduled_blocks))

            # sleep a little
            self.closing.wait(1)

    def run(self, *args, **kwargs):
        """Trigger a re-schedule."""
        self._need_update = True

    def _on_task_started(self, event: GoodWeatherEvent, sender: str, *args, **kwargs):
        """Re-schedule when task has started and we can predict its end.

        Args:
            event: The task started event.
            sender: Who sent it.
        """

        # get ETA in minutes
        eta = (event.eta - Time.now()).sec / 60
        log.info('Received task started event with ETA of %.0f minutes, triggering new scheduler run...', eta)

        # set it
        self._need_update = True
        self._schedule_start = event.eta

    def _on_good_weather(self, event: GoodWeatherEvent, sender: str, *args, **kwargs):
        """Re-schedule on incoming good weather event.

        Args:
            event: The good weather event.
            sender: Who sent it.
        """

        # get ETA in minutes
        eta = (event.eta - Time.now()).sec / 60
        log.info('Received good weather event with ETA of %.0f minutes, triggering new scheduler run...', eta)

        # set it
        self._need_update = True
        self._schedule_start = event.eta


__all__ = ['Scheduler']
