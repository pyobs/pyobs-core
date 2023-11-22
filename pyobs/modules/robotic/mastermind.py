import asyncio
import logging
from typing import Union, List, Dict, Tuple, Any, Optional, cast
import astropy.units as u

from pyobs.modules import Module
from pyobs.events.taskfinished import TaskFinishedEvent
from pyobs.events.taskstarted import TaskStartedEvent
from pyobs.interfaces import IFitsHeaderBefore, IAutonomous
from pyobs.robotic.task import Task
from pyobs.utils.time import Time
from pyobs.robotic import TaskRunner, TaskSchedule

log = logging.getLogger(__name__)


class Mastermind(Module, IAutonomous, IFitsHeaderBefore):
    """Mastermind for a full robotic mode."""

    __module__ = "pyobs.modules.robotic"

    def __init__(
        self,
        schedule: Union[TaskSchedule, Dict[str, Any]],
        runner: Union[TaskRunner, Dict[str, Any]],
        allowed_late_start: int = 300,
        allowed_overrun: int = 300,
        **kwargs: Any,
    ):
        """Initialize a new auto focus system.

        Args:
            schedule: Object that can return schedule.
            allowed_late_start: Allowed seconds to start late.
            allowed_overrun: Allowed time for a task to exceed it's window in seconds
        """
        Module.__init__(self, **kwargs)

        # store
        self._allowed_late_start = allowed_late_start
        self._allowed_overrun = allowed_overrun
        self._running = False

        # add thread func
        self.add_background_task(self._run_thread, True)

        # get schedule and runner
        self._task_schedule = self.add_child_object(schedule, TaskSchedule)
        self._task_runner = self.add_child_object(runner, TaskRunner)

        # observation name and exposure number
        self._task = None
        self._obs = None
        self._exp = None

    async def open(self) -> None:
        """Open module."""
        await Module.open(self)

        # subscribe to events
        if self.comm:
            await self.comm.register_event(TaskStartedEvent)
            await self.comm.register_event(TaskFinishedEvent)

        # start
        self._running = True

    async def start(self, **kwargs: Any) -> None:
        """Starts a service."""
        log.info("Starting robotic system...")
        self._running = True

    async def stop(self, **kwargs: Any) -> None:
        """Stops a service."""
        log.info("Stopping robotic system...")
        self._running = False

    async def is_running(self, **kwargs: Any) -> bool:
        """Whether a service is running."""
        return self._running

    async def _run_thread(self) -> None:
        # wait a little
        await asyncio.sleep(1)

        # flags
        first_late_start_warning = True

        # run until closed
        while True:
            # not running?
            if not self._running:
                # sleep a little and continue
                await asyncio.sleep(1)
                continue

            # get now
            now = Time.now()

            # find task that we want to run now
            task: Optional[Task] = await self._task_schedule.get_task(now)
            if task is None or not await self._task_runner.can_run(task):
                # no task found
                await asyncio.sleep(10)
                continue

            # starting too late?
            if not task.can_start_late:
                late_start = now - task.start
                if late_start > self._allowed_late_start * u.second:
                    # only warn once
                    if first_late_start_warning:
                        log.warning(
                            "Time since start of window (%.1f) too long (>%.1f), skipping task...",
                            late_start.to_value("second"),
                            self._allowed_late_start,
                        )
                    first_late_start_warning = False

                    # sleep a little and skip
                    await asyncio.sleep(10)
                    continue

            # reset warning
            first_late_start_warning = True

            # task is definitely not None here
            self._task = cast(Task, task)

            # ETA
            eta = now + self._task.duration * u.second

            # send event
            await self.comm.send_event(TaskStartedEvent(name=self._task.name, id=self._task.id, eta=eta))

            # run task in thread
            log.info("Running task %s...", self._task.name)
            try:
                await self._task_runner.run_task(self._task, task_schedule=self._task_schedule)
            except:
                # something went wrong
                log.warning("Task %s failed.", self._task.name)
                self._task = None
                continue

            # send event
            await self.comm.send_event(TaskFinishedEvent(name=self._task.name, id=self._task.id))

            # finish
            log.info("Finished task %s.", self._task.name)
            self._task = None

    async def get_fits_header_before(
        self, namespaces: Optional[List[str]] = None, **kwargs: Any
    ) -> Dict[str, Tuple[Any, str]]:
        """Returns FITS header for the current status of this module.

        Args:
            namespaces: If given, only return FITS headers for the given namespaces.

        Returns:
            Dictionary containing FITS headers.
        """

        # inside an observation?
        if self._task is not None:
            hdr = self._task.get_fits_headers()
            hdr["TASK"] = self._task.name, "Name of task"
            hdr["REQNUM"] = str(self._task.id), "Unique ID of task"
            return hdr
        else:
            return {}


__all__ = ["Mastermind"]
