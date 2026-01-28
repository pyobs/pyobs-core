import datetime
import logging
from typing import Any, Literal

from pyobs.robotic.observation import Observation, ObservationList, ObservationState
from pyobs.utils.time import Time
from pyobs.robotic.observationarchive import ObservationArchive
from ._schedulereader import LcoScheduleReader
from ._schedulewriter import LcoScheduleWriter
from ._portal import Portal
from .configdb import ConfigDB
from .. import Task

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
        ObservationArchive.__init__(self, **kwargs)

        # portal
        self._portal = Portal(url, token, site, enclosure, telescope)
        self._configdb = ConfigDB(configdb)

        # reader/writer
        self._schedule_reader = self.add_child_object(LcoScheduleReader(self._portal, site, telescope))
        self._schedule_writer = self.add_child_object(
            LcoScheduleWriter(self._portal, self._configdb, site, enclosure, telescope, period)
        )

    async def get_schedule(self) -> ObservationList:
        """Fetch schedule from portal.

        Returns:
            Dictionary with tasks.

        Raises:
            Timeout: If request timed out.
            ValueError: If something goes wrong.
        """
        return await self._schedule_reader.get_schedule()

    async def get_task(self, time: Time) -> Observation | None:
        """Returns the active scheduled task at the given time.

        Args:
            time: Time to return task for.

        Returns:
            Scheduled task at the given time.
        """
        return await self._schedule_reader.get_task(time)

    async def send_update(self, status_id: int, status: dict[str, Any]) -> None:
        """Send report to LCO portal

        Args:
            status_id: id of config status
            status: Status dictionary
        """
        await self._portal.update_configuration_status(status_id, status)
        # await self._schedule_reader.update_now()

    async def add_schedule(self, tasks: ObservationList) -> None:
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

    async def observations_for_task(self, task: Task) -> ObservationList:
        """Returns list of observations for the given task.

        Args:
            task: Task to get observations for.

        Returns:
            List of observations for the given task.
        """

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
        return observations

    async def observations_for_night(self, date: datetime.date) -> ObservationList:
        """Returns list of observations for the given task.

        Args:
            date: Date of night to get observations for.

        Returns:
            List of observations for the given task.
        """
        return ObservationList()


__all__ = ["LcoObservationArchive"]
