import asyncio
import logging
from typing import Any, Dict, List, cast, Tuple, Optional
from urllib.parse import urljoin
from pydantic import BaseModel, Field
from astropydantic import AstroPydanticTime  # type: ignore
import aiohttp

from pyobs.utils.time import Time


log = logging.getLogger(__name__)


class ConfigurationSummary(BaseModel):
    end: str = ""
    events: dict[str, str] = Field(default_factory=dict)
    id: Any = 0
    reason: str = ""
    start: str = ""
    state: str = ""
    time_completed: float = 0.0


class ConfigurationStatus(BaseModel):
    id: int
    configuration: int
    instrument_name: str
    guide_camera_name: str
    state: str
    summary: ConfigurationSummary


class LcoObservation(BaseModel):
    id: int
    request: int
    site: str
    enclosure: str
    telescope: str
    start: AstroPydanticTime
    end: AstroPydanticTime
    priority: int
    state: str
    configuration_statuses: list[ConfigurationStatus]


class Portal:
    def __init__(
        self,
        url: str,
        token: str,
        site: str,
        enclosure: str,
        telescope: str,
    ):
        self.url = url
        self.token = token
        self.headers = {"Authorization": "Token " + self.token}
        self.site = site
        self.enclosure = enclosure
        self.telescope = telescope

    async def _get(self, path: str, timeout: int = 30, params: Optional[Dict[str, Any]] = None) -> Any:
        """Do a GET request on the portal.

        Args:
            url: URL to request.

        Returns:
            Response for request.

        Raises:
            RuntimeError if the call failed.
            TimeoutError if the call timed out.
        """

        async with aiohttp.ClientSession() as session:
            async with session.get(
                urljoin(self.url, path), headers=self.headers, timeout=timeout, params=params
            ) as response:
                if response.status != 200:
                    raise RuntimeError("Invalid response from portal: " + await response.text())
                return await response.json()

    async def last_changed(self) -> Time:
        t = await self._get("/api/last_changed/")
        return Time(t["last_change_time"])

    async def last_scheduled(self) -> Time:
        t = await self._get("/api/last_scheduled/")
        return Time(t["last_schedule_time"])

    async def schedulable_requests(self) -> List[Dict[str, Any]]:
        req = await self._get("/api/requestgroups/schedulable_requests/")
        return cast(List[Dict[str, Any]], req)

    async def proposals(self) -> List[Dict[str, Any]]:
        # init
        proposal_list: List[Dict[str, Any]] = []
        offset, limit = 0, 100

        # get everything!
        while True:
            # get batch of proposals
            proposals_new, count = await self._proposals(offset, limit)

            # empty set?
            if len(proposals_new) == 0:
                raise ValueError("Could not fetch data.")

            # add to list and increase offset
            proposal_list.extend(proposals_new)
            offset += limit

            # finished?
            if len(proposal_list) == count:
                return proposal_list

    async def _proposals(self, offset: int, limit: int) -> Tuple[List[Dict[str, Any]], int]:
        req = await self._get("/api/proposals/", params={"offset": offset, "limit": limit})
        return cast(List[Dict[str, Any]], req["results"]), req["count"]

    async def instruments(self) -> Dict[str, Any]:
        req = await self._get("/api/instruments/")
        return cast(Dict[str, Any], req)

    async def observations(self, request_id: int) -> list[LcoObservation]:
        req = await self._get(f"/api/requests/{request_id}/observations/")
        return [LcoObservation.model_validate(r) for r in req]

    async def clear_schedule(self, start: Time, end: Time) -> None:
        """Clear schedule after given start time.

        Args:
            start: Start time to clear schedule from.
            end: End time to clear schedule to
        """

        # define parameters
        params = {
            "site": self.site,
            "enclosure": self.enclosure,
            "telescope": self.telescope,
            "start": start.isot,
            "end": end.isot,
        }

        # url and headers
        url = urljoin(self.url, "/api/observations/cancel/")
        headers = {"Authorization": "Token " + self.token, "Content-Type": "application/json; charset=utf8"}

        # cancel schedule
        log.info("Deleting all scheduled tasks after %s...", start.isot)
        async with aiohttp.ClientSession() as session:
            async with session.post(url, json=params, headers=headers, timeout=10) as response:
                if response.status != 200:
                    log.error("Could not cancel schedule: %s", await response.text())

    async def submit_observations(self, observations: list[dict[str, Any]]) -> None:
        """Submit observations.

        Args:
            observations: List of observations to submit.
        """

        # nothing?
        if len(observations) == 0:
            return

        # url and headers
        url = urljoin(self.url, "/api/observations/")
        headers = {"Authorization": "Token " + self.token, "Content-Type": "application/json; charset=utf8"}

        # submit observations
        async with aiohttp.ClientSession() as session:
            async with session.post(url, json=observations, headers=headers, timeout=10) as response:
                if response.status != 201:
                    log.error("Could not submit observations: %s", await response.text())
                data = await response.json()

        # log
        log.info("%d observations created.", data["num_created"])

        # errors?
        if "errors" in data and len(data["errors"]) > 0:
            for err in data["errors"].values():
                log.warning(f"Error from portal: {err}")

    async def update_configuration_status(self, status_id: int, status: dict[str, Any]) -> None:
        """Send report to LCO portal

        Args:
            status_id: id of config status
            status: Status dictionary
        """

        log.info("Sending configuration status update to portal...")
        url = urljoin(self.url, f"/api/configurationstatus/{status_id}/")

        # do request
        try:
            async with aiohttp.ClientSession() as session:
                async with session.patch(url, json=status, headers=self.headers, timeout=10) as response:
                    if response.status != 200:
                        log.error("Could not update configuration status: %s", await response.text())

        except asyncio.TimeoutError:
            # schedule re-attempt for sending
            asyncio.create_task(self._update_configuration_status_later(status_id, status))

    async def _update_configuration_status_later(
        self, status_id: int, status: dict[str, Any], delay: int = 300
    ) -> None:
        """Delay re-attempt to send report to LCO portal

        Args:
            status_id: id of config status
            status: Status dictionary
            delay: Delay in seconds
        """

        # sleep
        await asyncio.sleep(delay)

        # re-send
        await self.update_configuration_status(status_id, status)
