from __future__ import annotations
import logging
from typing import Any

from pyobs.robotic.lco._portal import LcoSchedulableRequest, LcoRequest, LcoObservation
from pyobs.robotic.scheduler.constraints import (
    TimeConstraint,
    Constraint,
    AirmassConstraint,
    MoonSeparationConstraint,
    MoonIlluminationConstraint,
    SolarElevationConstraint,
)
from pyobs.robotic.scheduler.merits import Merit
from pyobs.robotic.scheduler.targets import Target, SiderealTarget
from pyobs.robotic.scripts import Script
from pyobs.robotic.task import Task, TaskData
from pyobs.utils.logger import DuplicateFilter
from pyobs.utils.time import Time
import pyobs.utils.exceptions as exc

log = logging.getLogger(__name__)

# logger for logging name of the task
task_name_logger = logging.getLogger(__name__ + ":task_name")
task_name_logger.addFilter(DuplicateFilter())


class LcoTask(Task):
    """A task from the LCO portal."""

    request: LcoRequest

    @staticmethod
    def __lco_task(request: LcoRequest, name: str, script: dict[str, Any]) -> LcoTask:
        return LcoTask(
            id=request.id,
            name=name,
            duration=request.duration,
            constraints=LcoTask._create_constraints(request),
            merits=LcoTask._create_merits(request),
            target=LcoTask._create_target(request),
            request=request,
            script=script,
        )

    @staticmethod
    def from_schedulable_request(schedulable_request: LcoSchedulableRequest, script: dict[str, Any]) -> list[LcoTask]:
        tasks: list[LcoTask] = []
        for request in schedulable_request.requests:
            tasks.append(LcoTask.__lco_task(request, schedulable_request.name, script))
        return tasks

    @staticmethod
    def from_observation(observation: LcoObservation, script: dict[str, Any]) -> LcoTask:
        request = observation.request
        if not isinstance(request, LcoRequest):
            raise ValueError("Observation does not contain a fully defined request.")
        return LcoTask.__lco_task(request, str(request.id), script)

    @staticmethod
    def _create_constraints(request: LcoRequest) -> list[Constraint]:
        # get constraints
        constraints: list[Constraint] = []

        # time constraints?
        for window in request.windows:
            constraints.append(TimeConstraint(start=window.start, end=window.end))

        # take first config
        cfg = request.configurations[0]

        # constraints
        c = cfg.constraints
        if c.max_airmass is not None:
            constraints.append(AirmassConstraint(max_airmass=c.max_airmass))
        if c.min_lunar_distance is not None:
            constraints.append(MoonSeparationConstraint(min_distance=c.min_lunar_distance))
        if c.max_lunar_phase is not None:
            constraints.append(MoonIlluminationConstraint(max_phase=c.max_lunar_phase))
            # if max lunar phase <= 0.4 (which would be DARK), we also enforce the sun to be <-18 degrees
            if c.max_lunar_phase <= 0.4:
                constraints.append(SolarElevationConstraint(max_elevation=-18.0))

        return constraints

    @staticmethod
    def _create_merits(request: LcoRequest) -> list[Merit]:
        # take merits from the first config
        cfg = request.configurations[0]
        merits: list[Merit] = []
        for merit in cfg.merits:
            config = {"type": merit.type, **merit.params}
            merits.append(Merit.create(config))
        return merits

    @staticmethod
    def _create_target(request: LcoRequest) -> Target | None:
        # target
        target = request.configurations[0].target
        return SiderealTarget(name=target.name, ra=target.ra, dec=target.dec)

    def __eq__(self, other: object) -> bool:
        """Compares to tasks."""
        if isinstance(other, LcoTask):
            return self.request == other.request
        else:
            return False

    @property
    def observation_type(self) -> str:
        """Returns observation_type of this task.

        Returns:
            observation_type of this task.
        """
        return self.request.configurations[0].type

    @property
    def can_start_late(self) -> bool:
        """Whether this task is allowed to start later than the user-set time, e.g., for flatfields.

        Returns:
            True, if the task can start late.
        """
        return self.observation_type == "DIRECT"

    async def run(self, data: TaskData | None) -> None:
        """Run a task"""
        from .observationarchive import LcoObservationArchive

        if data is None:
            raise ValueError("No TaskData given.")

        # get request
        req = self.request

        # loop configurations
        status: ConfigStatus | None
        for config in req.configurations:
            # send an ATTEMPTED status
            if isinstance(data.observation_archive, LcoObservationArchive):
                status = ConfigStatus()
                config.state = "ATTEMPTED"
                await data.observation_archive.send_update(config.configuration_status, status.finish().to_json())

            # can run?
            script = self.pyobs_model_validate(Script, self.script, by_alias=True)
            if not await script.can_run(data):
                log.warning("Cannot run config.")
                continue

            # run config
            log.info("Running config...")
            status = await self._run_script(data)

            # send status
            if status is not None and isinstance(data.observation_archive, LcoObservationArchive):
                config.state = status.state
                await data.observation_archive.send_update(config.configuration_status, status.to_json())

        # finished task
        log.info("Finished task.")

    async def _run_script(self, data: TaskData) -> ConfigStatus | None:
        """Run a config

        Args:
            script: Script to run

        Returns:
            Configuration status to send to portal
        """

        # at least we tried...
        config_status = ConfigStatus()
        script = self.pyobs_model_validate(Script, self.script, by_alias=True)

        try:
            # run it
            log.info("Running task %d: %s...", self.id, self.name)
            await script.run(data)

            # finished config
            config_status.finish(state="COMPLETED", time_completed=script.exptime_done)

        except InterruptedError:
            log.warning("Task execution was interrupted.")
            config_status.finish(
                state="FAILED", reason="Task execution was interrupted.", time_completed=script.exptime_done
            )

        except exc.InvocationError as e:
            if isinstance(e.exception, exc.AbortedError):
                log.warning("Task execution was aborted: %s", e.exception)
                config_status.finish(
                    state="FAILED", reason="Task execution was aborted.", time_completed=script.exptime_done
                )
            else:
                log.warning("Error during task execution: %s", e.exception)
                config_status.finish(
                    state="FAILED", reason="Error during task execution.", time_completed=script.exptime_done
                )

        except Exception:
            log.exception("Something went wrong.")
            config_status.finish(state="FAILED", reason="Something went wrong", time_completed=script.exptime_done)

        # finished
        return config_status

    def is_finished(self) -> bool:
        """Whether task is finished."""
        return self.request.configurations[0].state != "PENDING"

    def get_fits_headers(self, namespaces: list[str] | None = None) -> dict[str, tuple[Any, str]]:
        """Returns FITS header for the current status of this module.

        Args:
            namespaces: If given, only return FITS headers for the given namespaces.

        Returns:
            Dictionary containing FITS headers.
        """

        # get header from the script

        script = self.pyobs_model_validate(Script, self.script, by_alias=True)
        hdr = script.get_fits_headers(namespaces)

        # return it
        return hdr


class ConfigStatus:
    """Status of a single configuration."""

    def __init__(self, state: str = "ATTEMPTED", reason: str = ""):
        """Initializes a new Status with an ATTEMPTED."""
        self.start: Time = Time.now()
        self.end: Time | None = None
        self.state: str = state
        self.reason: str = reason
        self.time_completed: float = 0.0

    def finish(self, state: str | None = None, reason: str | None = None, time_completed: float = 0.0) -> ConfigStatus:
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

    def to_json(self) -> dict[str, Any]:
        """Convert status to JSON for sending to portal."""
        return {
            "state": self.state,
            "summary": {
                "state": self.state,
                "reason": self.reason,
                "start": self.start.isot,
                "end": "" if self.end is None else self.end.isot,
                "time_completed": self.time_completed,
            },
        }


__all__ = ["LcoTask"]
