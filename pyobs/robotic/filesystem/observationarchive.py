from __future__ import annotations
import datetime
import os
from typing import Any, Literal
import abc

from pyobs.utils.time import Time
from .. import ObservationArchive
from .. import Task
from ..observation import ObservationList, Observation
from ...vfs import VirtualFileSystem


class FileSystemObservationArchive(ObservationArchive, metaclass=abc.ABCMeta):
    def __init__(self, path: str, extension: str, mode: Literal["day", "night"], **kwargs: Any):
        ObservationArchive.__init__(self, **kwargs)
        self._path = path
        self._extension = extension
        self._mode = mode

    def _get_filename(self, time: Time) -> str:
        """Returns the filename associated with the given time. If mode==night, the last sunrise is used,
        otherwise the last sunset.

        Args:
            time: Time to get filename for.

        Returns:
            Filename for schedule file.
        """
        if self.observer is None:
            raise ValueError("Observer is not set.")
        day = (
            self.observer.sun_rise_time(time, "previous")
            if self._mode == "night"
            else self.observer.sun_set_time(time, "previous")
        )
        return f"{day.isot[:10]}.{self._extension}"

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
        time = observations[0].start
        schedule = await self._load_observations(time)
        schedule += observations
        await self._save_observations(time, schedule)

    async def clear_schedule(self, start_time: Time) -> None:
        """Clear schedule after given start time.

        Args:
            start_time: Start time to clear from.
        """
        schedule = await self._load_observations(start_time)
        cleared = ObservationList([obs for obs in schedule if obs.end <= start_time])
        await self._save_observations(start_time, cleared)

    async def get_schedule(self) -> ObservationList:
        """Fetch schedule from portal.

        Returns:
            Dictionary with tasks.

        Raises:
            Timeout: If request timed out.
            ValueError: If something goes wrong.
        """
        return await self._load_observations(Time.now())

    async def get_task(self, time: Time) -> Observation | None:
        """Returns the active scheduled task at the given time.

        Args:
            time: Time to return task for.

        Returns:
            Scheduled task at the given time.
        """
        ...

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
    def __init__(self, path: str, **kwargs: Any):
        FileSystemObservationArchive.__init__(self, path, "yaml", **kwargs)

    @classmethod
    async def _load_observations_from_file(cls, path: str, vfs: VirtualFileSystem) -> ObservationList:
        observations = await vfs.read_yaml(path)
        return ObservationList([Observation.from_dict(obs) for obs in observations])

    @classmethod
    async def _save_observations_to_file(cls, path: str, observations: ObservationList, vfs: VirtualFileSystem) -> None:
        data = [Observation.to_dict(obs) for obs in observations]
        await vfs.write_yaml(path, data)


__all__ = ["FileSystemObservationArchive", "YamlObservationArchive"]
