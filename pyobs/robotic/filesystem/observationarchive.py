from __future__ import annotations
import datetime
import os
from typing import Any, Literal
import abc
import yaml
from filelock import FileLock

from pyobs.utils.time import Time
from .. import ObservationArchive, TaskArchive
from .. import Task
from ..observation import ObservationList, Observation, ObservationState


class FileSystemObservationArchive(ObservationArchive, metaclass=abc.ABCMeta):
    def __init__(
        self,
        extension: str,
        path: str = "/opt/pyobs/robotic/observations/",
        mode: Literal["day", "night"] = "night",
        **kwargs: Any,
    ):
        ObservationArchive.__init__(self, **kwargs)
        self._path = path
        self._extension = extension
        self._mode = mode
        self._lock = FileLock(os.path.join(path, ".lock"))

    def _get_filename(self, time: Time | datetime.date) -> str:
        """Returns the filename associated with the given time. If mode==night, the last sunrise is used,
        otherwise the last sunset.

        Args:
            time: Time to get filename for.

        Returns:
            Filename for schedule file.
        """
        if isinstance(time, Time):
            if self.observer is None:
                raise ValueError("Observer is not set.")
            day = (
                self.observer.sun_rise_time(time, "previous")
                if self._mode == "night"
                else self.observer.sun_set_time(time, "previous")
            )
            return f"{day.isot[:10]}.{self._extension}"
        elif isinstance(time, datetime.date):
            return time.isoformat() + self._extension
        else:
            raise ValueError(f"Unknown time type: {type(time)}")

    async def _load_observations(self, time: Time) -> ObservationList:
        """Loads observations from file for given time.

        Args:
            time: Time defines the night/day to load observations for.

        Returns:
            List of observations.
        """

        filename = self._get_filename(time)
        full_path = os.path.join(self._path, filename)
        try:
            return await self._load_observations_from_file(full_path, self.vfs)
        except FileNotFoundError:
            return ObservationList()

    async def _save_observations(self, time: Time, observations: ObservationList) -> None:
        """Saves observations to file.

        Args:
            time: Time defines the night/day to save observations for.
            observations: List of observations to save.
        """

        filename = self._get_filename(time)
        full_path = os.path.join(self._path, filename)
        await self._save_observations_to_file(full_path, observations, self.vfs)

    @classmethod
    @abc.abstractmethod
    async def _load_observations_from_file(cls, path: str, vfs: VirtualFileSystem) -> ObservationList: ...

    @classmethod
    @abc.abstractmethod
    async def _save_observations_to_file(
        cls, path: str, observations: ObservationList, vfs: VirtualFileSystem
    ) -> None: ...

    async def add_schedule(self, observations: ObservationList) -> None:
        """Add the list of scheduled tasks to the schedule.

        Args:
            observations: Scheduled tasks.
        """
        if len(observations) == 0:
            return
        with self._lock:
            time = observations[0].start
            schedule = await self._load_observations(time)
            schedule += observations
            await self._save_observations(time, schedule)

    async def clear_schedule(self, start_time: Time) -> None:
        """Clear schedule after given start time.

        Args:
            start_time: Start time to clear from.
        """
        with self._lock:
            schedule = await self._load_observations(start_time)
            cleared = ObservationList(
                [obs for obs in schedule if obs.end <= start_time or obs.state != ObservationState.PENDING]
            )
            await self._save_observations(start_time, cleared)

    async def get_schedule(self) -> ObservationList:
        """Fetch schedule from portal.

        Returns:
            Dictionary with tasks.

        Raises:
            Timeout: If request timed out.
            ValueError: If something goes wrong.
        """
        with self._lock:
            return await self._load_observations(Time.now())

    async def get_task(self, time: Time, task_archive: TaskArchive | None = None) -> Observation | None:
        """Returns the active scheduled task at the given time.

        Args:
            time: Time to return task for.
            task_archive: Task archive to get task from.

        Returns:
            Scheduled task at the given time.
        """

        # get schedule
        with self._lock:
            schedule = await self._load_observations(time)

        # loop all tasks
        for obs in schedule:
            # load task
            if task_archive is not None:
                await obs.fetch_task(task_archive)

            # no task?
            if obs.task is None:
                raise ValueError("Task could not be loaded.")

            # running now?
            if obs.start <= time < obs.end and obs.state == ObservationState.PENDING:
                return obs

        # nothing found
        return None

    async def update_observation_state(self, observation: Observation, state: ObservationState) -> None:
        """Updates observation state to given status.
        Args:
            observation: Observation to update.
            state: Observation state.
        """

        with self._lock:
            observation.state = state
            observations = await self._load_observations(observation.start)
            for i in range(len(observations)):
                if observations[i].id == observation.id:
                    observations[i] = observation
                    break
            else:
                observations.append(observation)
            await self._save_observations(observation.start, observations)

    async def observations_for_task(self, task: Task) -> ObservationList:
        """Returns list of observations for the given task.

        Args:
            task: Task to get observations for.

        Returns:
            List of observations for the given task.
        """
        return ObservationList()

    async def observations_for_night(self, date: datetime.date) -> ObservationList:
        """Returns list of observations for the given task.

        Args:
            date: Date of night to get observations for.

        Returns:
            List of observations for the given task.
        """
        return ObservationList()


class YamlObservationArchive(FileSystemObservationArchive):
    def __init__(self, **kwargs: Any):
        FileSystemObservationArchive.__init__(self, "yaml", **kwargs)

    @classmethod
    async def _load_observations_from_file(cls, path: str) -> ObservationList:
        with open(path, "r") as f:
            observations = yaml.safe_load(f)
            return ObservationList([Observation.model_validate(obs) for obs in observations])

    @classmethod
    async def _save_observations_to_file(cls, path: str, observations: ObservationList) -> None:
        data = [obs.model_dump(mode="json", exclude_defaults=True) for obs in observations]
        with open(path, "w") as f:
            yaml.safe_dump(data, f)


__all__ = ["FileSystemObservationArchive", "YamlObservationArchive"]
