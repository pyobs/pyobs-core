from __future__ import annotations
import logging
from typing import Any, TYPE_CHECKING, cast

from pyobs.object import get_object
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
from pyobs.robotic.task import Task
from pyobs.utils.logger import DuplicateFilter
from pyobs.utils.time import Time
import pyobs.utils.exceptions as exc

if TYPE_CHECKING:
    from pyobs.robotic import TaskRunner, ObservationArchive, TaskArchive

log = logging.getLogger(__name__)

# logger for logging name of task
task_name_logger = logging.getLogger(__name__ + ":task_name")
task_name_logger.addFilter(DuplicateFilter())


class ConfigStatus:
    """Status of a single configuration."""

    def __init__(self, state: str = "ATTEMPTED", reason: str = ""):
        """Initializes a new Status with an ATTEMPTED."""
        self.start: Time = Time.now()
        self.end: Time | None = None
        self.state: str = state
        self.reason: str = reason
        self.time_completed: float = 0.0

    def finish(
        self, state: str | None = None, reason: str | None = None, time_completed: float = 0.0
    ) -> "ConfigStatus":
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


class LcoTask(Task):
    """A task from the LCO portal."""

    def __init__(self, **kwargs: Any):
        """Init LCO task (called request there).

        Args:
            config: Configuration for task
        """
        Task.__init__(self, **kwargs)

        # store stuff
        self.cur_script: Script | None = None

    @staticmethod
    def from_lco_request(config: dict[str, Any]) -> LcoTask:
        request = config["request"]
        return LcoTask(
            id=request["id"],
            name=request["id"],
            duration=float(request["duration"]),
            constraints=LcoTask._create_constraints(request),
            merits=LcoTask._create_merits(request),
            target=LcoTask._create_target(request),
            config=config,
        )

    @staticmethod
    def _create_constraints(req: dict[str, Any]) -> list[Constraint]:
        # get constraints
        constraints: list[Constraint] = []

        # time constraints?
        if "windows" in req:
            constraints.extend([TimeConstraint(Time(wnd["start"]), Time(wnd["end"])) for wnd in req["windows"]])

        # take first config
        cfg = req["configurations"][0]

        # constraints
        if "constraints" in cfg:
            c = cfg["constraints"]
            if "max_airmass" in c and c["max_airmass"] is not None:
                constraints.append(AirmassConstraint(c["max_airmass"]))
            if "min_lunar_distance" in c and c["min_lunar_distance"] is not None:
                constraints.append(MoonSeparationConstraint(c["min_lunar_distance"]))
            if "max_lunar_phase" in c and c["max_lunar_phase"] is not None:
                constraints.append(MoonIlluminationConstraint(c["max_lunar_phase"]))
                # if max lunar phase <= 0.4 (which would be DARK), we also enforce the sun to be <-18 degrees
                if c["max_lunar_phase"] <= 0.4:
                    constraints.append(SolarElevationConstraint(-18.0))

        return constraints

    @staticmethod
    def _create_merits(req: dict[str, Any]) -> list[Merit]:
        # take merits from first config
        cfg = req["configurations"][0]
        merits: list[Merit] = []
        if "merits" in cfg:
            for merit in cfg["merits"]:
                config = {"class": merit["type"]}
                if "params" in merit:
                    config.update(**merit["params"])
                merits.append(Merit.model_validate(config, by_alias=True))
        return merits

    @staticmethod
    def _create_target(req: dict[str, Any]) -> Target | None:
        # target
        target = req["configurations"][0]["target"]
        if "ra" in target and "dec" in target:
            return SiderealTarget(name=target["name"], ra=target["ra"], dec=target["dec"])
        else:
            log.warning("Unsupported coordinate type.")
            return None

    def __eq__(self, other: object) -> bool:
        """Compares to tasks."""
        if isinstance(other, LcoTask):
            return self.config == other.config
        else:
            return False

    @property
    def observation_type(self) -> str:
        """Returns observation_type of this task.

        Returns:
            observation_type of this task.
        """
        if "observation_type" in self.config:
            return cast(str, self.config["observation_type"])
        else:
            raise ValueError("No observation_type found in request group.")

    @property
    def can_start_late(self) -> bool:
        """Whether this tasks is allowed to start later than the user-set time, e.g. for flatfields.

        Returns:
            True, if task can start late.
        """
        return self.observation_type == "DIRECT"

    def _get_config_script(self, config: dict[str, Any], scripts: dict[str, Script] | None = None) -> Script:
        """Get config script for given configuration.

        Args:
            config: Config to create runner for.

        Returns:
            Script for running config

        Raises:
            ValueError: If could not create runner.
        """

        # what do we run?
        config_type = config["type"]
        if scripts is None or config_type not in scripts:
            raise ValueError('No script found for configuration type "%s".' % config_type)

        # create script handler
        return get_object(
            scripts[config_type],
            Script,
            configuration=config,
            comm=self.comm,
            observer=self.observer,
        )

    async def can_run(self, scripts: dict[str, Script] | None = None) -> bool:
        """Checks, whether this task could run now.

        Returns:
            True, if task can run now.
        """

        # get logger for task name and log
        task_name_logger.info(f"Checking whether task {self.name} can run...")

        # loop configurations
        req = self.config["request"]
        for config in req["configurations"]:
            # get config runner
            runner = self._get_config_script(config, scripts)

            # if any runner can run, we proceed
            try:
                if await runner.can_run():
                    return True
            except Exception:
                log.exception("Error on evaluating whether task can run.")
                return False

        # no config found that could run
        return False

    async def run(
        self,
        task_runner: TaskRunner,
        observation_archive: ObservationArchive | None = None,
        task_archive: TaskArchive | None = None,
        scripts: dict[str, Script] | None = None,
    ) -> None:
        """Run a task"""
        from pyobs.robotic.lco import LcoObservationArchive

        # get request
        req = self.config["request"]

        # loop configurations
        status: ConfigStatus | None
        for config in req["configurations"]:
            # send an ATTEMPTED status
            if isinstance(observation_archive, LcoObservationArchive):
                status = ConfigStatus()
                self.config["state"] = "ATTEMPTED"
                await observation_archive.send_update(config["configuration_status"], status.finish().to_json())

            # get config runner
            script = self._get_config_script(config, scripts)

            # can run?
            if not await script.can_run():
                log.warning("Cannot run config.")
                continue

            # run config
            log.info("Running config...")
            self.cur_script = script
            status = await self._run_script(
                script, task_runner=task_runner, observation_archive=observation_archive, task_archive=task_archive
            )
            self.cur_script = None

            # send status
            if status is not None and isinstance(observation_archive, LcoObservationArchive):
                self.config["state"] = status.state
                await observation_archive.send_update(config["configuration_status"], status.to_json())

        # finished task
        log.info("Finished task.")

    async def _run_script(
        self,
        script: Script,
        task_runner: TaskRunner,
        observation_archive: ObservationArchive | None = None,
        task_archive: TaskArchive | None = None,
    ) -> ConfigStatus | None:
        """Run a config

        Args:
            script: Script to run

        Returns:
            Configuration status to send to portal
        """

        # at least we tried...
        config_status = ConfigStatus()

        try:
            # run it
            log.info("Running task %d: %s...", self.id, self.config["name"])
            await script.run(
                task_runner=task_runner, observation_archive=observation_archive, task_archive=task_archive
            )

            # finished config
            config_status.finish(state="COMPLETED", time_completed=script.exptime_done)

        except InterruptedError:
            log.warning("Task execution was interrupted.")
            config_status.finish(
                state="FAILED", reason="Task execution was interrupted.", time_completed=script.exptime_done
            )

        except exc.InvocationError as e:
            if isinstance(e.exception, exc.AbortedError):
                log.warning(f"Task execution was aborted: {e.exception}")
                config_status.finish(
                    state="FAILED", reason="Task execution was aborted.", time_completed=script.exptime_done
                )
            else:
                log.warning(f"Error during task execution: {e.exception}")
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
        if "config" in self.config and isinstance(self.config["state"], str):
            return self.config["state"] != "PENDING"
        else:
            return False

    def get_fits_headers(self, namespaces: list[str] | None = None) -> dict[str, tuple[Any, str]]:
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


__all__ = ["LcoTask"]
