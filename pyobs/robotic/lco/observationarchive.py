import datetime
import logging
from typing import Any, Literal

from pyobs.robotic.observation import Observation, ObservationList, ObservationState
from pyobs.robotic.observationarchive import ObservationArchive
from pyobs.utils.time import Time

from .. import Task, TaskArchive
from ._portal import Portal
from .configdb import ConfigDB

log = logging.getLogger(__name__)


STATE_MAP = {
    "CANCELED": ObservationState.CANCELED,
    "COMPLETED": ObservationState.COMPLETED,
    "PENDING": ObservationState.PENDING,
    "ABORTED": ObservationState.ABORTED,
    "IN_PROGRESS": ObservationState.IN_PROGRESS,
    "FAILED": ObservationState.FAILED,
}


class LcoObservationArchive(ObservationArchive):
    """Scheduler for using the LCO portal"""

    def __init__(
        self,
        url: str,
        configdb: str,
        site: str,
        token: str,
        enclosure: str,
        telescope: str,
        period: int = 24,
        mode: Literal["read", "write", "readwrite"] = "readwrite",
        **kwargs: Any,
    ):
        """Creates a new LCO scheduler.

        Args:
            url: URL to portal
            configdb: URL to configdb
            site: Site filter for fetching requests
            token: Authorization token for portal
            enclosure: Enclosure for new schedules.
            telescope: Telescope for new schedules.
            instrument: Instrument for new schedules.
            period: Period to schedule in hours
        """
        from ._schedulereader import LcoScheduleReader
        from ._schedulewriter import LcoScheduleWriter

        ObservationArchive.__init__(self, **kwargs)

        # portal
        self._portal = self.add_child_object(Portal(url, token, site, enclosure, telescope))
        self._configdb = ConfigDB(configdb)

        # reader/writer
        self._schedule_reader = self.add_child_object(LcoScheduleReader(self._portal, site, telescope))
        self._schedule_writer = self.add_child_object(
            LcoScheduleWriter(self._portal, self._configdb, site, enclosure, telescope, period)
        )

    async def get_schedule(self, time: Time | None = None) -> ObservationList:
        """Fetch schedule from the portal.

        Returns:
            Dictionary with tasks.

        Raises:
            Timeout: If request timed out.
            ValueError: If something goes wrong.
        """
        return await self._schedule_reader.get_schedule()

    async def get_current_observation(
        self, task_archive: TaskArchive | None = None, time: Time | None = None
    ) -> Observation | None:
        """Returns the currently running observation."""
        return await self._schedule_reader.get_task(time or Time.now())

    async def update_observation(self, observation: Observation) -> None:
        """Updates observation state in the portal."""
        if not isinstance(observation.task, Task) or observation.task.id is None:
            return
        from .task import ConfigStatus, LcoTask

        if not isinstance(observation.task, LcoTask):
            return
        for config in observation.task.request.configurations:
            status = ConfigStatus(state=observation.state)
            status.finish(state=observation.state)
            await self.send_update(config.configuration_status, status.to_json())

    async def get_next_observation(self, time: Time, task_archive: TaskArchive | None = None) -> Observation | None:
        """Returns the active scheduled task at the given time.

        Args:
            time: Time to return an observation for.

        Returns:
            Scheduled task at the given time.
        """
        return await self._schedule_reader.get_task(time)

    async def send_update(self, status_id: int | None, status: dict[str, Any]) -> None:
        """Send a report to the LCO portal

        Args:
            status_id: id of config status
            status: Status dictionary
        """
        if status_id is None:
            return
        await self._portal.update_configuration_status(status_id, status)
        # await self._schedule_reader.update_now()

    async def add_observations(self, tasks: ObservationList) -> None:
        """Add the list of scheduled tasks to the schedule.

        Args:
            tasks: Scheduled tasks.
        """
        await self._schedule_writer.add_schedule(tasks)

    async def clear_schedule(self, start_time: Time) -> None:
        """Clear schedule after given start time.

        Args:
            start_time: Start time to clear from.
        """
        await self._schedule_writer.clear_schedule(start_time)

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

        The LCO portal requires a request id, so a task is mandatory for this archive.

        Args:
            task: Task to get observations for (required for the LCO archive).
            state: If given, only return observations in this state.
            start_before: If given, only return observations that start before this time.
            start_after: If given, only return observations that start after this time.
            end_before: If given, only return observations that end before this time.
            end_after: If given, only return observations that end after this time.

        Returns:
            List of matching observations.
        """

        from .task import LcoTask

        if not isinstance(task, LcoTask) or task.id is None or not isinstance(task.id, int):
            raise ValueError("Task is not a LCO task.")

        portal_observations = await self._portal.observations(task.id)
        observations = ObservationList()
        for obs in portal_observations:
            observations.append(
                Observation(
                    id=obs.id,
                    task=task,
                    start=obs.start,
                    end=obs.end,
                    state=STATE_MAP[obs.state],
                )
            )
        return observations.filter(
            state=state,
            start_before=start_before,
            start_after=start_after,
            end_before=end_before,
            end_after=end_after,
        )

    async def observations_for_night(self, date: datetime.date) -> ObservationList:
        """Returns a list of observations for the given task.

        Args:
            date: Date of night to get observations for.

        Returns:
            List of observations for the given task.
        """
        return ObservationList()


__all__ = ["LcoObservationArchive"]
