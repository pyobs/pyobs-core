import logging
from typing import Union, Dict, Tuple, Optional, List, Any

from pyobs.object import get_object
from pyobs.robotic.scripts import Script
from pyobs.robotic.task import Task
from pyobs.utils.logger import DuplicateFilter
from pyobs.utils.time import Time
from pyobs.robotic import TaskRunner, TaskSchedule, TaskArchive

log = logging.getLogger(__name__)

# logger for logging name of task
task_name_logger = logging.getLogger(__name__ + ":task_name")
task_name_logger.addFilter(DuplicateFilter())


class ConfigStatus:
    """Status of a single configuration."""

    def __init__(self, state: str = "ATTEMPTED", reason: str = ""):
        """Initializes a new Status with an ATTEMPTED."""
        self.start: Time = Time.now()
        self.end: Optional[Time] = None
        self.state: str = state
        self.reason: str = reason
        self.time_completed: float = 0.0

    def finish(
        self, state: Optional[str] = None, reason: Optional[str] = None, time_completed: float = 0.0
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

    def to_json(self) -> Dict[str, Any]:
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

    def __init__(self, config: Dict[str, Any], scripts: Dict[str, Script], **kwargs: Any):
        """Init LCO task (called request there).

        Args:
            config: Configuration for task
            scripts: External scripts to run
        """
        Task.__init__(self, **kwargs)

        # store stuff
        self.config = config
        self.scripts = scripts
        self.cur_script: Optional[Script] = None

    @property
    def id(self) -> Any:
        """ID of task."""
        if "request" in self.config and "id" in self.config["request"]:
            return self.config["request"]["id"]
        else:
            raise ValueError("No id found in request.")

    @property
    def name(self) -> str:
        """Returns name of task."""
        if "name" in self.config and isinstance(self.config["name"], str):
            return self.config["name"]
        else:
            raise ValueError("No name found in request group.")

    @property
    def duration(self) -> float:
        """Returns estimated duration of task in seconds."""
        if (
            "request" in self.config
            and "duration" in self.config["request"]
            and isinstance(self.config["request"]["duration"], int)
        ):
            return float(self.config["request"]["duration"])
        else:
            raise ValueError("No duration found in request.")

    def __eq__(self, other: object) -> bool:
        """Compares to tasks."""
        if isinstance(other, LcoTask):
            return self.config == other.config
        else:
            return False

    @property
    def start(self) -> Time:
        """Start time for task"""
        if "start" in self.config and isinstance(self.config["start"], Time):
            return self.config["start"]
        else:
            raise ValueError("No start time found in request group.")

    @property
    def end(self) -> Time:
        """End time for task"""
        if "end" in self.config and isinstance(self.config["end"], Time):
            return self.config["end"]
        else:
            raise ValueError("No end time found in request group.")

    @property
    def observation_type(self) -> str:
        """Returns observation_type of this task.

        Returns:
            observation_type of this task.
        """
        if "observation_type" in self.config:
            return self.config["observation_type"]
        else:
            raise ValueError("No observation_type found in request group.")

    @property
    def can_start_late(self) -> bool:
        """Whether this tasks is allowed to start later than the user-set time, e.g. for flatfields.

        Returns:
            True, if task can start late.
        """
        return self.observation_type == "DIRECT"

    def _get_config_script(self, config: Dict[str, Any]) -> Script:
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
        if config_type not in self.scripts:
            raise ValueError('No script found for configuration type "%s".' % config_type)

        # create script handler
        return get_object(
            self.scripts[config_type],
            Script,
            configuration=config,
            comm=self.comm,
            observer=self.observer,
        )

    async def can_run(self) -> bool:
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
            runner = self._get_config_script(config)

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
        task_schedule: Optional[TaskSchedule] = None,
        task_archive: Optional[TaskArchive] = None,
    ) -> None:
        """Run a task"""
        from pyobs.robotic.lco import LcoTaskSchedule

        # get request
        req = self.config["request"]

        # loop configurations
        status: Optional[ConfigStatus]
        for config in req["configurations"]:
            # send an ATTEMPTED status
            if isinstance(self.schedule, LcoTaskSchedule):
                status = ConfigStatus()
                self.config["state"] = "ATTEMPTED"
                await self.schedule.send_update(config["configuration_status"], status.finish().to_json())

            # get config runner
            script = self._get_config_script(config)

            # can run?
            if not await script.can_run():
                log.warning("Cannot run config.")
                continue

            # run config
            log.info("Running config...")
            self.cur_script = script
            status = await self._run_script(
                script, task_runner=task_runner, task_schedule=task_schedule, task_archive=task_archive
            )
            self.cur_script = None

            # send status
            if status is not None and isinstance(self.schedule, LcoTaskSchedule):
                self.config["state"] = status.state
                await self.schedule.send_update(config["configuration_status"], status.to_json())

        # finished task
        log.info("Finished task.")

    async def _run_script(
        self,
        script: Script,
        task_runner: TaskRunner,
        task_schedule: Optional[TaskSchedule] = None,
        task_archive: Optional[TaskArchive] = None,
    ) -> Union[ConfigStatus, None]:
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
            await script.run(task_runner=task_runner, task_schedule=task_schedule, task_archive=task_archive)

            # finished config
            config_status.finish(state="COMPLETED", time_completed=script.exptime_done)

        except InterruptedError:
            log.warning("Task execution was interrupted.")
            config_status.finish(
                state="FAILED", reason="Task execution was interrupted.", time_completed=script.exptime_done
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

    def get_fits_headers(self, namespaces: Optional[List[str]] = None) -> Dict[str, Tuple[Any, str]]:
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
