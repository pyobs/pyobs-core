import asyncio
import logging
from typing import Any

import astropy.units as u

from pyobs.events import TaskFailedEvent, TaskFinishedEvent, TaskStartedEvent
from pyobs.interfaces import FitsHeaderEntry, IAutonomous, IFitsHeaderBefore, IRobotic, IRunning
from pyobs.interfaces.IRobotic import RoboticState, RoboticTask
from pyobs.interfaces.IRunning import RunningState
from pyobs.modules import Module
from pyobs.robotic import (
    Observation,
    ObservationArchive,
    ObservationState,
    Task,
    TaskArchive,
    TaskRunner,
)
from pyobs.robotic.scheduler.targets import Target
from pyobs.utils import exceptions as exc
from pyobs.utils.time import Time

log = logging.getLogger(__name__)


class Mastermind(Module, IAutonomous, IRobotic, IFitsHeaderBefore):
    """Mastermind for a full robotic mode."""

    __module__ = "pyobs.modules.robotic"

    def __init__(
        self,
        schedule: ObservationArchive | dict[str, Any],
        runner: TaskRunner | dict[str, Any],
        tasks: TaskArchive | dict[str, Any] | None = None,
        allowed_late_start: int = 300,
        allowed_overrun: int = 300,
        after_task_sleep: int = 0,
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
        self._after_task_sleep = after_task_sleep
        self._cant_run_reason: str | None = None
        self._next_observation: Observation | None = None

        # add thread func
        self.add_background_task(self._run_thread, True)

        # get schedule and runner
        self._task_archive = self.add_child_object(tasks, TaskArchive) if tasks is not None else None
        self._observation_archive = self.add_child_object(schedule, ObservationArchive)
        self._task_runner = self.add_child_object(runner, TaskRunner, observation_archive=self._observation_archive)

        # observation name and exposure number
        self._task: Task | None = None
        self._task_target: Target | None = None
        self._obsnum: str | None = None
        self._task_start: Time | None = None
        self._task_eta: Time | None = None

        # per-night observation counter
        self._obsnum_cache = f"/pyobs/modules/{self.name}/obsnum.yaml"

    async def _next_obsnum(self) -> str:
        """Compute and persist the next per-night observation number.

        Returns:
            Compound "<night>-<counter>" string, e.g. "20260810-001".
        """
        night = Time.now().night_obs(self._observer) if self._observer is not None else Time.now().datetime.date()
        night_str = night.strftime("%Y%m%d")

        # load cache, bump counter, reset on night change
        counter = 1
        try:
            cache = await self.vfs.read_yaml(self._obsnum_cache)
            if cache is not None and cache.get("night") == night_str:
                counter = cache["obsnum"] + 1
        except (FileNotFoundError, ValueError, IndexError):
            # IndexError: some VFS backends (e.g. MemoryFile) raise this for a missing file
            # instead of FileNotFoundError
            pass

        # write it back
        try:
            await self.vfs.write_yaml(self._obsnum_cache, {"night": night_str, "obsnum": counter})
        except (FileNotFoundError, ValueError):
            log.warning("Could not write obsnum cache file.")

        return f"{night_str}-{counter:03d}"

    async def open(self) -> None:
        """Open module."""
        await Module.open(self)

        # subscribe to events
        if self._comm:
            await self.comm.register_event(TaskStartedEvent)
            await self.comm.register_event(TaskFinishedEvent)

        # start
        self._running = True
        await self.comm.set_state(IRunning, RunningState(running=self._running))
        await self._publish_robotic_state()

    async def start(self, **kwargs: Any) -> None:
        """Starts a service."""
        log.info("Starting robotic system...")
        self._running = True
        await self.comm.set_state(IRunning, RunningState(running=self._running))
        await self._publish_robotic_state()

    async def stop(self, **kwargs: Any) -> None:
        """Stops a service."""
        log.info("Stopping robotic system...")
        self._running = False
        await self.comm.set_state(IRunning, RunningState(running=self._running))
        await self._publish_robotic_state()

    async def _publish_robotic_state(self) -> None:
        """Publish IRobotic state: current task (from self._task/...), and self._next_observation
        / self._cant_run_reason as last updated by _run_thread."""
        current = None
        if self._task is not None:
            current = RoboticTask(
                id=self._task.id,
                name=self._task.name,
                target=self._task_target.name if self._task_target is not None else None,
                start=self._task_start,
                end=self._task_eta,
                obsnum=self._obsnum,
                state=ObservationState.IN_PROGRESS.value,
                priority=self._task.priority,
            )
        next_task = RoboticTask.from_observation(self._next_observation) if self._next_observation else None
        await self.comm.set_state(
            IRobotic, RoboticState(current=current, next=next_task, cant_run_reason=self._cant_run_reason)
        )

    async def _run_thread(self) -> None:
        # wait a little
        await asyncio.sleep(5)

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
            observation: Observation | None = await self._observation_archive.get_next_observation(
                now, self._task_archive
            )
            if observation is None:
                # nothing scheduled at all -- publish once when this changes, not every loop
                if self._next_observation is not None or self._cant_run_reason is not None:
                    self._next_observation = None
                    self._cant_run_reason = None
                    await self._publish_robotic_state()
                await asyncio.sleep(10)
                continue

            if not await self._task_runner.can_run(observation.task, observation.target):
                reason = self._task_runner.cant_run_reason(observation.task)
                # publish (and log) only when the next task or its reason actually changed --
                # avoids spamming a state update every 10s while stuck on the same block
                changed = (
                    reason != self._cant_run_reason
                    or self._next_observation is None
                    or self._next_observation.task.id != observation.task.id
                )
                if changed:
                    if reason is not None:
                        log.info("Task %s cannot run: %s", observation.task.name, reason)
                    self._cant_run_reason = reason
                    self._next_observation = observation
                    await self._publish_robotic_state()
                await asyncio.sleep(10)
                continue

            # task can run — clear stored reason
            self._cant_run_reason = None
            self._next_observation = None

            # starting too late?
            if not observation.task.can_start_late:
                late_start = now - observation.start
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
            self._task = observation.task
            self._task_target = observation.target
            self._obsnum = await self._next_obsnum()

            # ETA
            now = Time.now()
            eta = now + self._task.duration * u.second
            self._task_start = now
            self._task_eta = eta

            # send event and change state
            await self.comm.send_event(
                TaskStartedEvent(name=self._task.name, id=self._task.id, eta=eta, obsnum=self._obsnum)
            )
            observation.state = ObservationState.IN_PROGRESS
            observation.start = now
            observation.end = eta
            observation.obsnum = self._obsnum
            await self._observation_archive.update_observation(observation)
            await self._publish_robotic_state()

            # run task in thread
            log.info("Running task %s...", self._task.name)
            try:
                await self._task_runner.run_task(self._task, self._task_target)
            except Exception as e:
                # a PyobsError is an expected/domain failure (e.g. acquisition out of tolerance) --
                # quiet INFO line, no traceback. Anything else is unexpected and needs a full
                # traceback to debug. e.log() also skips re-logging if some deeper layer (e.g. the
                # module's own execute()) already logged this same exception.
                if isinstance(e, exc.PyobsError):
                    e.log(log, "INFO", f"Task {self._task.name} failed: {e}")
                else:
                    log.exception("Task %s failed.", self._task.name)
                observation.end = Time.now()
                observation.state = ObservationState.FAILED
                await self._observation_archive.update_observation(observation)
                await self.comm.send_event(TaskFailedEvent(name=self._task.name, id=self._task.id, obsnum=self._obsnum))
                self._task = None
                self._task_target = None
                self._obsnum = None
                self._task_start = None
                self._task_eta = None
                await self._publish_robotic_state()
                continue

            # send event and change state
            await self.comm.send_event(TaskFinishedEvent(name=self._task.name, id=self._task.id, obsnum=self._obsnum))
            observation.end = Time.now()
            observation.state = ObservationState.COMPLETED
            await self._observation_archive.update_observation(observation)

            # finish
            log.info("Finished task %s.", self._task.name)
            self._task = None
            self._task_target = None
            self._obsnum = None
            self._task_start = None
            self._task_eta = None
            await self._publish_robotic_state()

            # sleep?
            await asyncio.sleep(self._after_task_sleep)

    async def get_fits_header_before(
        self, namespaces: list[str] | None = None, **kwargs: Any
    ) -> dict[str, FitsHeaderEntry]:
        """Returns FITS header for the current status of this module.

        Args:
            namespaces: If given, only return FITS headers for the given namespaces.

        Returns:
            Dictionary containing FITS headers.
        """

        # inside an observation?
        if self._task is not None:
            hdr = self._task.get_fits_headers()
            hdr["TASK"] = FitsHeaderEntry(self._task.name, "Name of task")
            hdr["REQNUM"] = FitsHeaderEntry(str(self._task.id), "Unique ID of task")
            if self._task.project:
                hdr["PROJECT"] = FitsHeaderEntry(self._task.project, "Project code")
            if self._obsnum is not None:
                hdr["OBSNUM"] = FitsHeaderEntry(self._obsnum, "Observation number (night-obsnum)")
            return hdr
        else:
            return {}


__all__ = ["Mastermind"]
