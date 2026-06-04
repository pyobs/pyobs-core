from __future__ import annotations
import asyncio
from typing import Any, Literal
from urllib.parse import urljoin
import aiohttp
import logging

from pyobs.utils.time import Time
from .. import ObservationArchive, TaskArchive
from .. import Task
from ..observation import ObservationList, Observation, ObservationState
from ...utils.http import http_request_with_retries

log = logging.getLogger(__name__)


class BackendObservationArchive(ObservationArchive):
    """Observation archive based on pyobs-robotic-backend."""

    def __init__(
        self,
        url: str,
        token: str,
        mode: Literal["day", "night"] = "night",
        auto_update: bool = True,
        **kwargs: Any,
    ):
        ObservationArchive.__init__(self, **kwargs)
        self._url = url
        self._token = token
        self._mode = mode
        self._aiohttp_session: aiohttp.ClientSession | None = None
        self._last_update: Time | None = None
        self._observations = ObservationList()

        if auto_update:
            self.add_background_task(self._check_for_changes)

    async def open(self) -> None:
        """Opens the backend observation archive."""
        await ObservationArchive.open(self)
        self._aiohttp_session = aiohttp.ClientSession(headers={"Authorization": f"Token {self._token}"})

    async def close(self) -> None:
        """Closes the backend observation archive."""
        await ObservationArchive.close(self)
        if self._aiohttp_session is not None:
            await self._aiohttp_session.close()
            self._aiohttp_session = None

    @property
    def _session(self) -> aiohttp.ClientSession:
        if self._aiohttp_session is None:
            raise ValueError("No session available.")
        return self._aiohttp_session

    async def _check_for_changes(self) -> None:
        """Update schedule in background."""

        while True:
            try:
                last_update = await self.last_update_time()
                if self._last_update is None or self._last_update < last_update:
                    self._observations = await self._get_schedule()
                    if len(self._observations) == 0:
                        log.info("Downloaded new schedule.")
                    else:
                        obs = self._observations[0]
                        log.info("Downloaded new schedule. Next observation is task %s at %s.", obs.task, obs.start)
                    self._last_update = last_update
            except Exception as e:
                log.error("Failed to update observations from backend: %s", e)
            await asyncio.sleep(5)

    async def last_update_time(self) -> Time:
        """Fetches last schedule update time."""
        res = await http_request_with_retries(self._session, urljoin(self._url, "/api/last_observation_update/"))
        return Time(res["last_observation_update"])

    async def _get_schedule(self) -> ObservationList:
        """Fetch schedule from portal.

        Returns:
            Dictionary with tasks.

        Raises:
            Timeout: If request timed out.
            ValueError: If something goes wrong.
        """
        return await self.get_observations(end_after=Time.now())

    async def add_observations(self, tasks: ObservationList) -> None:
        """Add the list of scheduled tasks to the schedule.

        Args:
            tasks: Scheduled tasks.
        """
        await http_request_with_retries(
            self._session,
            urljoin(self._url, "/api/observations/"),
            method="post",
            expected_status=201,
            json=tasks.model_dump(use_task_id=True),
        )

    async def clear_schedule(self, start_time: Time) -> None:
        """Clear schedule after given start time.

        Args:
            start_time: Start time to clear from.
        """
        await http_request_with_retries(
            self._session, urljoin(self._url, "/api/cancel_observations/"), params={"after": start_time.isot}
        )

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

        await http_request_with_retries(
            self._session,
            urljoin(self._url, f"/api/observations/{observation.id}/"),
            method="put",
            expected_status=200,
            json=observation.model_dump(use_task_id=True),
        )

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

        url = urljoin(self._url, "/api/observations/")
        params = {}
        if task is not None:
            params["task"] = task.id
        if state is not None:
            params["state"] = state.value
        if start_before is not None:
            params["start_before"] = start_before.isot
        if start_after is not None:
            params["start_after"] = start_after.isot
        if end_before is not None:
            params["end_before"] = end_before.isot
        if end_after is not None:
            params["end_after"] = end_after.isot
        observations = await http_request_with_retries(self._session, url, params=params)
        return ObservationList([self.pyobs_model_validate(Observation, obs) for obs in observations["results"]])


__all__ = ["BackendObservationArchive"]
