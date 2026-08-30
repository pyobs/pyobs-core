from __future__ import annotations

import asyncio
import inspect
import json
import logging
import time
from typing import Any

import astropy.units as u
from astropy.time import TimeDelta

from pyobs.events import (
    Event,
    GoodWeatherEvent,
    TaskFailedEvent,
    TaskFinishedEvent,
    TaskStartedEvent,
)
from pyobs.interfaces import IRoboticScheduler, IRunnable, IRunning
from pyobs.interfaces.IRobotic import RoboticTask
from pyobs.interfaces.IRoboticScheduler import SchedulerState
from pyobs.interfaces.IRunning import RunningState
from pyobs.modules import Module
from pyobs.object import get_class_from_string
from pyobs.robotic import (
    ObservationArchive,
    ObservationList,
    ObservationState,
    Project,
    Task,
    TaskArchive,
)
from pyobs.robotic.scheduler import TaskScheduler
from pyobs.utils.time import Time

log = logging.getLogger(__name__)


def _class_accepts_param(config: dict[str, Any] | Any, param_name: str) -> bool:
    """Whether the class configured in `config` (a dict with a "class" key, or an already-built
    object) declares `param_name` somewhere in its __init__ MRO.

    Used to decide whether a kwarg can be injected into a child object's config -- injecting
    unconditionally relies on the target silently absorbing it if unwanted, which no longer
    happens now that Object.__init__ forwards leftover kwargs on to object.__init__().
    """
    if isinstance(config, dict):
        if "class" not in config:
            return False
        try:
            klass = get_class_from_string(config["class"])
        except Exception:
            return False
    elif isinstance(config, type):
        klass = config
    else:
        klass = type(config)
    for cls in klass.__mro__:
        init = cls.__dict__.get("__init__")
        if init is None:
            continue
        try:
            sig = inspect.signature(init)
        except (TypeError, ValueError):
            continue
        if param_name in sig.parameters:
            return True
    return False


class Scheduler(Module, IRunnable, IRoboticScheduler):
    """Scheduler."""

    __module__ = "pyobs.modules.robotic"

    # hard ceiling on get_schedule()'s limit, regardless of what a client requests
    _MAX_SCHEDULE_LIMIT = 100

    def __init__(
        self,
        scheduler: dict[str, Any] | TaskScheduler,
        tasks: dict[str, Any] | TaskArchive,
        schedule: dict[str, Any] | ObservationArchive,
        trigger_on_task_started: bool = False,
        trigger_on_task_finished: bool = False,
        trigger_on_every_update: bool = False,
        schedule_range: float = 24.0,
        safety_time: float = 300,
        min_safety_time: float = 20,
        **kwargs: Any,
    ):
        """Initialize a new scheduler.

        Args:
            scheduler: Scheduler to use.
            tasks: Task archive to use.
            schedule: Task schedule to use.
            trigger_on_task_started: Whether to trigger a re-calculation of schedule, when task has started.
            trigger_on_task_finishes: Whether to trigger a re-calculation of schedule, when task has finished.
            schedule_range: Number of hours to schedule into the future
            safety_time: If no ETA for next task to start exists (from current task, weather became good, etc), use
                         this time in seconds to make sure that we don't schedule for a time when the scheduler is
                         still running
            min_safety_time: Minimum safety time.
        """
        Module.__init__(self, **kwargs)

        # get scheduler
        self._task_archive = self.add_child_object(tasks, TaskArchive, on_tasks_changed=self._update_schedule)
        # PortalObservationArchive declares auto_update and gates its own polling loop on it --
        # since we already drive updates via on_tasks_changed above, that poller must stay off.
        # Other ObservationArchive implementations (e.g. LcoObservationArchive) don't declare it at
        # all, so it must not be injected unconditionally.
        extra_schedule_kwargs: dict[str, Any] = {}
        if _class_accepts_param(schedule, "auto_update"):
            extra_schedule_kwargs["auto_update"] = False
        self._schedule = self.add_child_object(schedule, ObservationArchive, **extra_schedule_kwargs)
        extra_scheduler_kwargs: dict[str, Any] = {}
        if _class_accepts_param(scheduler, "observation_archive"):
            extra_scheduler_kwargs["observation_archive"] = self._schedule
        self._scheduler = self.add_child_object(scheduler, TaskScheduler, **extra_scheduler_kwargs)

        # store
        self._running = True
        self._initial_update_done = False
        self._need_update = False
        self._trigger_on_task_started = trigger_on_task_started
        self._trigger_on_task_finished = trigger_on_task_finished
        self._trigger_on_every_update = trigger_on_every_update
        self._schedule_range = schedule_range * u.hour
        self._safety_time = safety_time * u.second
        self._min_safety_time = min_safety_time * u.second

        # time to start next schedule from
        self._schedule_start: Time = Time.now()
        self._last_reschedule: Time | None = None

        # ID of currently running task, and current (or last if finished) block
        self._current_task_id = None
        self._last_task_id = None

        # tasks
        self._tasks: list[Task] = []
        self._projects: list[Project] = []

        # update threads
        self.add_background_task(self._schedule_worker)

    async def open(self) -> None:
        """Open module."""
        await Module.open(self)

        # subscribe to events
        if self._comm:
            await self.comm.register_event(TaskStartedEvent, self._on_task_started)
            await self.comm.register_event(TaskFinishedEvent, self._on_task_finished)
            await self.comm.register_event(TaskFailedEvent, self._on_task_finished)
            await self.comm.register_event(GoodWeatherEvent, self._on_good_weather)

        await self.comm.set_state(IRunning, RunningState(running=self._running))
        await self.comm.set_state(IRoboticScheduler, SchedulerState(last_reschedule=self._last_reschedule))

    async def start(self, **kwargs: Any) -> None:
        """Start scheduler."""
        self._running = True
        await self.comm.set_state(IRunning, RunningState(running=self._running))
        await self.comm.set_state(IRoboticScheduler, SchedulerState(last_reschedule=self._last_reschedule))

    async def stop(self, **kwargs: Any) -> None:
        """Stop scheduler."""
        self._running = False
        await self.comm.set_state(IRunning, RunningState(running=self._running))
        await self.comm.set_state(IRoboticScheduler, SchedulerState(last_reschedule=self._last_reschedule))

    async def _update_schedule(self) -> None:
        # get schedulable tasks and sort them
        log.info("Found update in schedulable block, downloading them...")
        tasks = sorted(
            await self._task_archive.get_schedulable_tasks(),
            key=lambda x: json.dumps(x.id, sort_keys=True),
        )
        log.info("Downloaded %d schedulable tasks(s).", len(tasks))

        # download projects
        self._projects = await self._task_archive.get_projects()

        # compare new and old lists
        removed, added = self._compare_task_lists(self._tasks, tasks)

        # schedule update
        self._need_update = True

        # no changes?
        if not self._trigger_on_every_update and len(removed) == 0 and len(added) == 0:
            # no need to re-schedule
            log.info("No change in list of blocks detected.")
            self._need_update = False

        # has only the current block been removed?
        log.info("Removed: %d, added: %d", len(removed), len(added))
        if len(removed) == 1:
            log.info(
                "Found 1 removed block with ID %d. Last task ID was %s, current is %s.",
                removed[0],
                str(self._last_task_id),
                str(self._current_task_id),
            )
        if len(removed) == 1 and len(added) == 0 and removed[0] == self._last_task_id:
            # no need to re-schedule
            log.info("Only one removed block detected, which is the one currently running.")
            self._need_update = False

        # check, if one of the removed blocks was actually in schedule
        if len(removed) > 0 and self._need_update:
            schedule = await self._schedule.get_schedule()
            removed_from_schedule = [s for s in schedule if s.task.id in removed]
            if len(removed_from_schedule) == 0:
                log.info("Found %s tasks, but none of them was scheduled.", len(removed))
                self._need_update = False

        # store blocks
        self._tasks = tasks

        # schedule update
        if self._need_update:
            log.info("Triggering scheduler run...")

        # remember now
        self._initial_update_done = True

    @staticmethod
    def _compare_task_lists(tasks1: list[Task], tasks2: list[Task]) -> tuple[list[Any], list[Any]]:
        """Compares two lists of tasks and returns two lists, containing those that are missing in list 1
        and list 2, respectively.

        Args:
            tasks1: First list of tasks.
            tasks2: Second list of tasks.

        Returns:
            (tuple): Tuple containing:
                unique1:  Blocks that exist in tasks1, but not in tasks2.
                unique2:  Blocks that exist in tasks2, but not in tasks1.
        """

        # get dictionaries with block ids
        ids1 = {t.id: t for t in tasks1}
        ids2 = {t.id: t for t in tasks2}

        # find elements in ids1 that are missing in ids2 and vice versa
        additional1 = list(set(ids1.keys()).difference(ids2.keys()))
        additional2 = list(set(ids2.keys()).difference(ids1.keys()))

        return sorted(additional1), sorted(additional2)  # type: ignore[type-var]

    async def _schedule_worker(self) -> None:
        await asyncio.sleep(5)

        # run forever
        while True:
            # need update?
            if self._need_update and self._initial_update_done:
                # reset need for update
                self._need_update = False

                try:
                    # TODO: add abort (see old robotic/scheduler.py)

                    # start time
                    start_time = time.time()

                    # schedule start must be at least safety_time in the future
                    start = self._schedule_start
                    if start - Time.now() < self._safety_time:
                        start = Time.now() + TimeDelta(self._safety_time)
                    end = start + TimeDelta(self._schedule_range)

                    # do we have an observation running?
                    running_obs = await self._schedule.get_current_observation(self._task_archive)
                    if running_obs is not None and running_obs.end < start:
                        start = Time(running_obs.end)

                    # clear future schedule
                    await self._schedule.clear_schedule(start)

                    # schedule
                    scheduled_tasks = ObservationList()
                    first = True
                    async for scheduled_task in self._scheduler.schedule(self._tasks, self._projects, start, end):
                        # remember for later
                        scheduled_tasks.append(scheduled_task)

                        if self._need_update:
                            log.info("Not using scheduler results, since update was requested.")
                            break

                        # on first task, we have to clear the schedule
                        if first:
                            first = False
                            log.info("Finished calculating next task:")
                            self._log_scheduled_task(ObservationList([scheduled_task]))

                            # set new safety_time as duration + 20%, but at least _min_safety_time
                            self._safety_time = max((time.time() - start_time) * 1.2 * u.second, self._min_safety_time)

                            # submit it
                            await self._schedule.add_observations(ObservationList([scheduled_task]))

                    if self._need_update:
                        log.info("Not using scheduler results, since update was requested.")
                        continue

                    # log it
                    log.info("Finished calculating schedule for %d block(s):", len(scheduled_tasks))
                    self._log_scheduled_task(scheduled_tasks)
                    log.info("Done.")

                    # submit it
                    await self._schedule.add_observations(scheduled_tasks[1:])

                    # clean up
                    del scheduled_tasks

                    # record + publish
                    self._last_reschedule = Time.now()
                    await self.comm.set_state(IRoboticScheduler, SchedulerState(last_reschedule=self._last_reschedule))

                except asyncio.CancelledError:
                    return

                except Exception:
                    log.exception("Something went wrong")

            # sleep a little
            await asyncio.sleep(1)

    def _log_scheduled_task(self, scheduled_tasks: ObservationList) -> None:
        try:
            observer = self._scheduler.observer
        except AttributeError:
            observer = None
        for scheduled_task in scheduled_tasks:
            msg = f"  - {scheduled_task.start.strftime('%H:%M:%S')} to {scheduled_task.end.strftime('%H:%M:%S')}: "
            msg += f"{scheduled_task.task.name} ({scheduled_task.task.id}"
            if scheduled_task.priority is not None:
                msg += f", priority: {scheduled_task.priority}"
            msg += ")"
            if scheduled_task.target is not None and observer is not None:
                start = Time(scheduled_task.start)
                altaz = observer.altaz(start, scheduled_task.target.coordinates(start))
                msg += f" [{scheduled_task.target.name}: alt={altaz.alt.degree:.1f}°, airmass={float(altaz.secz):.2f}]"
            log.info(msg)

    async def run(self, **kwargs: Any) -> None:
        """Trigger a re-schedule."""
        self._need_update = True

    async def get_schedule(self, limit: int = 20, **kwargs: Any) -> list[RoboticTask]:
        """Return the upcoming (pending/in-progress) schedule, most imminent first.

        Args:
            limit: Maximum number of entries to return.

        Returns:
            Up to `limit` scheduled tasks, capped at `_MAX_SCHEDULE_LIMIT` regardless of what's
            requested.

        Raises:
            ValueError: If limit is negative.
        """
        if limit < 0:
            raise ValueError("limit must be >= 0.")
        limit = min(limit, self._MAX_SCHEDULE_LIMIT)

        schedule = await self._schedule.get_schedule()
        pending = sorted(
            (obs for obs in schedule if obs.state in (ObservationState.PENDING, ObservationState.IN_PROGRESS)),
            key=lambda obs: obs.start,
        )
        return [RoboticTask.from_observation(obs) for obs in pending[:limit]]

    async def _on_task_started(self, event: Event, sender: str) -> bool:
        """Re-schedule when task has started and we can predict its end.

        Args:
            event: The task started event.
            sender: Who sent it.
        """
        if not isinstance(event, TaskStartedEvent):
            return False

        # store it
        self._current_task_id = event.id
        self._last_task_id = event.id

        # trigger?
        if self._trigger_on_task_started:
            # get ETA in minutes
            eta = (event.eta - Time.now()).sec / 60 if event.eta is not None else 0.0
            log.info("Received task started event with ETA of %.0f minutes, triggering new scheduler run...", eta)

            # set it
            self._need_update = True
            self._schedule_start = event.eta if event.eta is not None else Time.now()

        return True

    async def _on_task_finished(self, event: Event, sender: str) -> bool:
        """Reset current task, when it has finished or failed.

        Args:
            event: The task finished or failed event.
            sender: Who sent it.
        """
        if not isinstance(event, TaskFinishedEvent | TaskFailedEvent):
            return False

        # reset current task
        self._current_task_id = None

        # trigger?
        if self._trigger_on_task_finished:
            # get ETA in minutes
            log.info("Received task finished event, triggering new scheduler run...")

            # set it
            self._need_update = True
            self._schedule_start = Time.now()

        return True

    async def _on_good_weather(self, event: Event, sender: str) -> bool:
        """Re-schedule on incoming good weather event.

        Args:
            event: The good weather event.
            sender: Who sent it.
        """
        if not isinstance(event, GoodWeatherEvent):
            return False

        # get ETA in minutes
        eta = (event.eta - Time.now()).sec / 60 if event.eta is not None else 0.0
        log.info("Received good weather event with ETA of %.0f minutes, triggering new scheduler run...", eta)

        # set it
        self._need_update = True
        self._schedule_start = event.eta if event.eta is not None else Time.now()
        return True

    async def abort(self, **kwargs: Any) -> None:
        pass


__all__ = ["Scheduler"]
