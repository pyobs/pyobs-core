import datetime
import glob
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
            if self._observer is None:
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

    async def _load_observations(self, time: Time | datetime.date) -> ObservationList:
        """Loads observations from file for given time.

        Args:
            time: Time defines the night/day to load observations for.

        Returns:
            List of observations.
        """

        filename = self._get_filename(time)
        full_path = os.path.join(self._path, filename)
        try:
            return await self._load_observations_from_file(full_path)
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
        await self._save_observations_to_file(full_path, observations)

    @abc.abstractmethod
    async def _load_observations_from_file(self, path: str) -> ObservationList: ...

    @abc.abstractmethod
    async def _save_observations_to_file(self, path: str, observations: ObservationList) -> None: ...

    async def add_observations(self, observations: ObservationList) -> None:
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

    async def get_next_observation(self, time: Time, task_archive: TaskArchive | None = None) -> Observation | None:
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

    async def get_current_observation(self, task_archive: TaskArchive | None = None) -> Observation | None:
        """Returns the currently running observation.

        Args:
            task_archive: Task archive to get task from.

        Returns:
            Currently running observation.
        """

        # get schedule
        with self._lock:
            observations = await self._load_observations(Time.now())

        # find running one
        for obs in observations:
            if obs.state == ObservationState.IN_PROGRESS:
                if task_archive is not None:
                    await obs.fetch_task(task_archive)
                return obs
        else:
            return None

    async def update_observation(self, observation: Observation) -> None:
        """Updates observation.
        Args:
            observation: Observation to update.
        """

        with self._lock:
            observations = await self._load_observations(observation.start)
            for i in range(len(observations)):
                if observations[i].id == observation.id:
                    observations[i] = observation
                    break
            else:
                observations.append(observation)
            await self._save_observations(observation.start, observations)

    async def get_observations(
        self,
        task: Task | None = None,
        state: ObservationState | None = None,
        start_before: Time | None = None,
        start_after: Time | None = None,
        end_before: Time | None = None,
        end_after: Time | None = None,
    ) -> ObservationList:
        """Returns a list of observations matching the given filters.

        Args:
            task: If given, only return observations for this task.
            state: If given, only return observations in this state.
            start_before: If given, only return observations that start before this time.
            start_after: If given, only return observations that start after this time.
            end_before: If given, only return observations that end before this time.
            end_after: If given, only return observations that end after this time.

        Returns:
            List of matching observations.
        """
        observations: list[Observation] = []
        with self._lock:
            for filename in glob.glob(os.path.join(self._path, f"*.{self._extension}")):
                night = await self._load_observations_from_file(filename)
                observations.extend(night)
        return ObservationList(observations).filter(
            state=state,
            task_id=task.id if task is not None else None,
            start_before=start_before,
            start_after=start_after,
            end_before=end_before,
            end_after=end_after,
        )


class YamlObservationArchive(FileSystemObservationArchive):
    def __init__(self, **kwargs: Any):
        FileSystemObservationArchive.__init__(self, "yaml", **kwargs)

    async def _load_observations_from_file(self, path: str) -> ObservationList:
        with open(path, "r") as f:
            observations = yaml.safe_load(f)
            return ObservationList([self.pyobs_model_validate(Observation, obs) for obs in observations])

    async def _save_observations_to_file(self, path: str, observations: ObservationList) -> None:
        data = [obs.model_dump(mode="json", exclude_defaults=True) for obs in observations]
        with open(path, "w") as f:
            yaml.safe_dump(data, f)


__all__ = ["FileSystemObservationArchive", "YamlObservationArchive"]
