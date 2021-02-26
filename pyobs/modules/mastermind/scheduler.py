import copy
import json
import logging
from multiprocessing import Process
from typing import Union, List
from astroplan import AtNightConstraint, Transitioner, SequentialScheduler, Schedule, TimeConstraint, ObservingBlock, \
    PriorityScheduler
from astropy.time import TimeDelta
import astropy.units as u

from pyobs.events.taskfinished import TaskFinishedEvent
from pyobs.events.taskstarted import TaskStartedEvent
from pyobs.events import GoodWeatherEvent
from pyobs.utils.time import Time
from pyobs.interfaces import IStoppable, IRunnable
from pyobs import Module, get_object
from pyobs.robotic import TaskArchive


log = logging.getLogger(__name__)


class Scheduler(Module, IStoppable, IRunnable):
    """Scheduler."""

    def __init__(self, tasks: Union[dict, TaskArchive], schedule_range: int = 24, safety_time: int = 60,
                 twilight: str = 'astronomical', *args, **kwargs):
        """Initialize a new scheduler.

        Args:
            scheduler: Scheduler to use
            schedule_range: Number of hours to schedule into the future
            safety_time: If no ETA for next task to start exists (from current task, weather became good, etc), use
                         this time in seconds to make sure that we don't schedule for a time when the scheduler is
                         still running
            twilight: astronomical or nautical
        """
        Module.__init__(self, *args, **kwargs)

        # get scheduler
        self._task_archive = get_object(tasks, TaskArchive)

        # store
        self._schedule_range = schedule_range
        self._safety_time = safety_time
        self._twilight = twilight
        self._running = True
        self._initial_update_done = False
        self._need_update = False

        # time to start next schedule from
        self._schedule_start = None

        # ID of currently running task
        self._current_task_id = None

        # blocks
        self._blocks: List[ObservingBlock] = []
        self._scheduled_blocks: List[ObservingBlock] = []

        # update thread
        self._add_thread_func(self._schedule_thread, True)
        self._add_thread_func(self._update_thread, True)

    def open(self):
        """Open module."""
        Module.open(self)

        # subscribe to events
        if self.comm:
            self.comm.register_event(TaskStartedEvent, self._on_task_started)
            self.comm.register_event(TaskFinishedEvent, self._on_task_finished)
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
                self._initial_update_done = True

            # sleep a little
            self.closing.wait(5)

    def _schedule_thread(self):
        # run forever
        while not self.closing.is_set():
            # need update?
            if self._need_update and self._initial_update_done:
                # reset need for update
                self._need_update = False

                # run scheduler in separate process and wait for it
                p = Process(target=self._schedule)
                p.start()
                p.join()

            # sleep a little
            self.closing.wait(1)

    def _schedule(self):
        """Actually do the scheduling, usually run in a separate process."""

        # only global constraint is the night
        if self._twilight == 'astronomical':
            constraints = [AtNightConstraint.twilight_astronomical()]
        elif self._twilight == 'nautical':
            constraints = [AtNightConstraint.twilight_nautical()]
        else:
            raise ValueError('Unknown twilight type.')

        # we don't need any transitions
        transitioner = Transitioner()

        # create scheduler
        #scheduler = SequentialScheduler(constraints, self.observer, transitioner=transitioner)
        scheduler = PriorityScheduler(constraints, self.observer, transitioner=transitioner)

        # get start time for scheduler
        start = self._schedule_start
        now_plus_safety = Time.now() + self._safety_time * u.second
        if start is None or start < now_plus_safety:
            # if no ETA exists or is in the past, use safety time
            start = now_plus_safety
        end = start + TimeDelta(self._schedule_range * u.hour)

        # make shallow copies of all blocks and loop them
        copied_blocks = [copy.copy(block) for block in self._blocks]
        for block in copied_blocks:
            # astroplan's PriorityScheduler expects lower priorities to be more important, so calculate
            # inverse of our priorities to match that requirement
            block.priority = 1. / block.priority

            # it also doesn't match the requested observing windows exactly, so we make them a little smaller.
            for constraint in block.constraints:
                if isinstance(constraint, TimeConstraint):
                    constraint.min += 15 * u.second
                    constraint.max -= 15 * u.second

        # remove currently running block and filter by start time
        blocks = []
        for b in filter(lambda b: b.configuration['request']['id'] != self._current_task_id, blocks):
            time_constraint_found = False
            # loop all constraints
            for c in b.constraints:
                if isinstance(c, TimeConstraint):
                    # we found a time constraint
                    time_constraint_found = True

                    # does the window start before the end of the scheduling range?
                    if c.min < end:
                        # yes, store block and break loop
                        blocks.append(b)
                        break
            else:
                # loop has finished without breaking
                # if no time constraint has been found, we still take the block
                if time_constraint_found is False:
                    blocks.append(b)

        # if need new update, skip here
        if self._need_update:
            log.info('Not running scheduler, since update was requested.')
            return

        # log it
        log.info('Calculating schedule for %d schedulable block(s) starting at %s...', len(blocks), start)

        # run scheduler
        time_range = Schedule(start, end)
        schedule = scheduler(blocks, time_range)

        # if need new update, skip here
        if self._need_update:
            log.info('Not using scheduler results, since update was requested.')
            return

        # update
        self._task_archive.update_schedule(schedule.scheduled_blocks, start)
        if len(schedule.scheduled_blocks) > 0:
            log.info('Finished calculating schedule for %d block(s):', len(schedule.scheduled_blocks))
            for i, block in enumerate(schedule.scheduled_blocks, 1):
                log.info('  #%d: %s to %s (%.1f)',
                         block.configuration['request']['id'], block.start_time.isot, block.end_time.isot,
                         block.priority)
        else:
            log.info('Finished calculating schedule for 0 blocks.')

    def run(self, *args, **kwargs):
        """Trigger a re-schedule."""
        self._need_update = True

    def _on_task_started(self, event: TaskStartedEvent, sender: str, *args, **kwargs):
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
        self._current_task_id = event.id

    def _on_task_finished(self, event: TaskFinishedEvent, sender: str, *args, **kwargs):
        """Reset current task, when it has finished.

        Args:
            event: The task finished event.
            sender: Who sent it.
        """
        self._current_task_id = None

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
