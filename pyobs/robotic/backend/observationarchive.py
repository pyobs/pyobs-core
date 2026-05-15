from __future__ import annotations
import datetime
from typing import Any, Literal
from urllib.parse import urljoin
import requests
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
        self._session = requests.Session()
        self._session.headers["Authorization"] = f"Token {self._token}"

    async def add_schedule(self, tasks: ObservationList) -> None:
        """Add the list of scheduled tasks to the schedule.

        Args:
            tasks: Scheduled tasks.
        """
        self._session.post(urljoin(self._url, "/api/observations/"), json=tasks.model_dump(use_task_id=True))

    async def clear_schedule(self, start_time: Time) -> None:
        """Clear schedule after given start time.

        Args:
            start_time: Start time to clear from.
        """
        self._session.get(urljoin(self._url, "/api/cancel_observations/"), params={"after": start_time.isot})

    async def get_schedule(self) -> ObservationList:
        """Fetch schedule from portal.

        Returns:
            Dictionary with tasks.

        Raises:
            Timeout: If request timed out.
            ValueError: If something goes wrong.
        """
        res = self._session.get(
            urljoin(self._url, "/api/observations/"), params={"start": Time.now().isot, "state": "pending"}
        )
        observations = res.json()
        return ObservationList([self.pyobs_model_validate(Observation, obs) for obs in observations])

    async def get_next_observation(self, time: Time, task_archive: TaskArchive | None = None) -> Observation | None:
        """Returns the active scheduled task at the given time.

        Args:
            time: Time to return task for.
            task_archive: Task archive to get task from.

        Returns:
            Scheduled task at the given time.
        """
        req = self._session.get(
            urljoin(self._url, "/api/observations/"), params={"start": time.isot, "end": time.isot, "state": "pending"}
        )
        observations = req.json()
        if len(observations) > 0:
            if len(observations) > 1:
                log.warning("More than one active scheduled task.")
            obs = self.pyobs_model_validate(Observation, observations[0])
            if task_archive is not None:
                await obs.fetch_task(task_archive)
            return obs
        return None

    async def get_current_observation(self, task_archive: TaskArchive | None = None) -> Observation | None:
        """Returns the currently running observation.

        Args:
            task_archive: Task archive to get task from.

        Returns:
            Currently running observation.
        """
        time = Time.now()
        res = self._session.get(
            urljoin(self._url, "/api/observations/"),
            json={"start": time.isot, "end": time.isot, "state": "in_progress"},
        )
        observations = res.json()
        if len(observations) == 1:
            return self.pyobs_model_validate(Observation, observations[0])
        return None

    async def update_observation(self, observation: Observation) -> None:
        """Updates observation.
        Args:
            observation: Observation to update.
        """
        self._session.put(
            urljoin(self._url, f"/api/observations/{observation.id}/"), json=observation.model_dump(use_task_id=True)
        )

    async def observations_for_task(self, task: Task) -> ObservationList:
        """Returns list of observations for the given task.

        Args:
            task: Task to get observations for.

        Returns:
            List of observations for the given task.
        """
        res = self._session.get(urljoin(self._url, f"/api/tasks/{task.id}/observations/"))
        observations = res.json()
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
        res = self._session.get(
            urljoin(self._url, "/api/observations/"), params={"start": start.isoformat(), "end": end.isoformat()}
        )
        observations = res.json()
        return ObservationList([self.pyobs_model_validate(Observation, obs) for obs in observations])


__all__ = ["BackendObservationArchive"]
