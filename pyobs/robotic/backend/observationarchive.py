from __future__ import annotations
import asyncio
import datetime
from typing import Any, Literal
from urllib.parse import urljoin
import aiohttp
import logging

from pyobs.utils.time import Time
from .. import ObservationArchive, TaskArchive
from .. import Task
from ..observation import ObservationList, Observation

log = logging.getLogger(__name__)


class BackendObservationArchive(ObservationArchive):
    """Observation archive based on pyobs-robotic-backend."""

    def __init__(
        self,
        url: str,
        token: str,
        mode: Literal["day", "night"] = "night",
        **kwargs: Any,
    ):
        ObservationArchive.__init__(self, **kwargs)
        self._url = url
        self._token = token
        self._mode = mode
        self._session: aiohttp.ClientSession | None = None
        self._last_update: Time | None = None
        self._observations = ObservationList()

        self.add_background_task(self._check_for_changes)

    async def open(self) -> None:
        """Opens the backend observation archive."""
        await ObservationArchive.open(self)
        self._session = aiohttp.ClientSession(headers={"Authorization": f"Token {self._token}"})

    async def _check_for_changes(self) -> None:
        """Update schedule in background."""

        while True:
            last_update = await self.last_update_time()
            if self._last_update is None or self._last_update < last_update:
                self._observations = await self._get_schedule()
                if len(self._observations) == 0:
                    log.info("Downloaded new schedule.")
                else:
                    obs = self._observations[0]
                    log.info(f"Downloaded new schedule. Next observation is task {obs.task} at {obs.start}.")
                self._last_update = last_update

            await asyncio.sleep(5)

    async def last_update_time(self) -> Time:
        """Fetches last schedule update time."""
        async with self._session.get(urljoin(self._url, "/api/last_observation_update/")) as response:
            if response.status != 200:
                raise RuntimeError("Invalid response from backend: " + await response.text())
            res = await response.json()
            return Time(res["last_observation_update"])

    async def _get_schedule(self) -> ObservationList:
        """Fetch schedule from portal.

        Returns:
            Dictionary with tasks.

        Raises:
            Timeout: If request timed out.
            ValueError: If something goes wrong.
        """
        async with self._session.get(
            urljoin(self._url, "/api/observations/"), params={"start": Time.now().isot, "state": "pending,in_progress"}
        ) as response:
            if response.status != 200:
                raise RuntimeError("Invalid response from backend: " + await response.text())
            observations = await response.json()
            return ObservationList([self.pyobs_model_validate(Observation, obs) for obs in observations])

    async def add_schedule(self, tasks: ObservationList) -> None:
        """Add the list of scheduled tasks to the schedule.

        Args:
            tasks: Scheduled tasks.
        """
        async with self._session.post(
            urljoin(self._url, "/api/observations/"), json=tasks.model_dump(use_task_id=True)
        ) as response:
            if response.status != 201:
                raise RuntimeError("Invalid response from backend: " + await response.text())

    async def clear_schedule(self, start_time: Time) -> None:
        """Clear schedule after given start time.

        Args:
            start_time: Start time to clear from.
        """
        async with self._session.get(
            urljoin(self._url, "/api/cancel_observations/"), params={"after": start_time.isot}
        ) as response:
            if response.status != 200:
                raise RuntimeError("Invalid response from backend: " + await response.text())

    async def get_schedule(self) -> ObservationList:
        """Fetch schedule from portal.

        Returns:
            Dictionary with tasks.

        Raises:
            Timeout: If request timed out.
            ValueError: If something goes wrong.
        """
        return self._observations

    async def get_next_observation(self, time: Time, task_archive: TaskArchive | None = None) -> Observation | None:
        """Returns the active scheduled task at the given time.

        Args:
            time: Time to return task for.
            task_archive: Task archive to get task from.

        Returns:
            Scheduled task at the given time.
        """
        for obs in self._observations:
            if obs.state == "pending" and obs.start < time < obs.end:
                if task_archive is not None:
                    await obs.fetch_task(task_archive)
                return obs
        else:
            return None

    async def get_current_observation(self, task_archive: TaskArchive | None = None) -> Observation | None:
        """Returns the currently running observation.

        Args:
            task_archive: Task archive to get task from.

        Returns:
            Currently running observation.
        """
        for obs in self._observations:
            if obs.state == "in_progress":
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
        async with self._session.put(
            urljoin(self._url, f"/api/observations/{observation.id}/"), json=observation.model_dump(use_task_id=True)
        ) as response:
            if response.status != 200:
                raise RuntimeError("Invalid response from backend: " + await response.text())

    async def observations_for_task(self, task: Task) -> ObservationList:
        """Returns list of observations for the given task.

        Args:
            task: Task to get observations for.

        Returns:
            List of observations for the given task.
        """
        async with self._session.get(urljoin(self._url, f"/api/tasks/{task.id}/observations/")) as response:
            if response.status != 200:
                raise RuntimeError("Invalid response from backend: " + await response.text())
            observations = await response.json()
            return ObservationList([self.pyobs_model_validate(Observation, obs) for obs in observations])

    async def observations_for_night(self, date: datetime.date) -> ObservationList:
        """Returns list of observations for the given task.

        Args:
            date: Date of night to get observations for.

        Returns:
            List of observations for the given task.
        """
        start = datetime.datetime.combine(date, datetime.time(0, 0, 0))
        end = datetime.datetime.combine(date, datetime.time(23, 59, 59))
        async with self._session.get(
            urljoin(self._url, "/api/observations/"), params={"start": start.isoformat(), "end": end.isoformat()}
        ) as response:
            if response.status != 200:
                raise RuntimeError("Invalid response from backend: " + await response.text())
            observations = await response.json()
            return ObservationList([self.pyobs_model_validate(Observation, obs) for obs in observations])


__all__ = ["BackendObservationArchive"]
