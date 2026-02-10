import logging
from typing import Any, cast
import astropy.units as u

from pyobs.robotic.observation import ObservationList
from pyobs.utils.time import Time
from ._portal import Portal
from .configdb import ConfigDB
from .task import LcoTask
from ...object import Object

log = logging.getLogger(__name__)


class LcoScheduleWriter(Object):
    """Scheduler for using the LCO portal"""

    def __init__(
        self,
        portal: Portal,
        configdb: ConfigDB,
        site: str,
        enclosure: str,
        telescope: str,
        period: float,
        **kwargs: Any,
    ):
        """Creates a new LCO scheduler.

        Args:
            portal: Portal to use.
            configdb: ConfigDB to use.
            site: Site filter for fetching requests
            enclosure: Enclosure for new schedules.
            telescope: Telescope for new schedules.
            instrument: Instrument for new schedules.
            period: Period to schedule in hours
        """
        Object.__init__(self, **kwargs)

        # portal
        self._portal = portal
        self._configdb = configdb

        # store stuff
        self._site = site
        self._enclosure = enclosure
        self._telescope = telescope
        self._period = period

    async def add_schedule(self, tasks: ObservationList) -> None:
        """Add the list of scheduled tasks to the schedule.

        Args:
            tasks: Scheduled tasks.
        """
        observations = self._create_observations(tasks)
        await self._portal.submit_observations(observations)

    async def clear_schedule(self, start_time: Time) -> None:
        """Clear schedule after given start time.

        Args:
            start_time: Start time to clear from.
        """
        await self._portal.clear_schedule(start_time, start_time + self._period * u.hour)

    def _create_observations(self, scheduled_tasks: ObservationList) -> list[dict[str, Any]]:
        """Create observations from schedule.

        Args:
            scheduled_tasks: List of scheduled tasks

        Returns:
            List with observations.
        """

        # loop tasks
        observations = []
        for scheduled_task in scheduled_tasks:
            # get request
            request = cast(LcoTask, scheduled_task.task).config["request"]

            # create observation
            obs = {
                "site": self._site,
                "enclosure": self._enclosure,
                "telescope": self._telescope,
                "start": scheduled_task.start.isot,
                "end": scheduled_task.end.isot,
                "request": request["id"],
                "configuration_statuses": [],
            }

            # add configuration statuses
            for config in request["configurations"]:
                # get instrument
                instruments = self._configdb.get_instrument_by_type(
                    config["instrument_type"], site=self._site, enclosure=self._enclosure, telescope=self._telescope
                )
                if len(instruments) == 0:
                    log.warning(f"Instrument type {config['instrument_type']} not found. Skipping configuration.")
                    continue
                if len(instruments) > 1:
                    log.warning(f"More than one instrument of type {config['instrument_type']} found. Using first one.")
                instrument = instruments[0].instrument

                # add configuration status
                obs["configuration_statuses"].append(
                    {
                        "configuration": config["id"],
                        "instrument_name": instrument.code,
                        "guide_camera_name": instrument.autoguider_camera.code,
                    }
                )

            # add it
            observations.append(obs)

        # return list
        return observations


__all__ = ["LcoScheduleWriter"]
