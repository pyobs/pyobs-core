from typing import Any, Dict, List, cast, Tuple, Optional
from urllib.parse import urljoin
from pydantic import BaseModel, Field
from astropydantic import AstroPydanticTime  # type: ignore
import aiohttp

from pyobs.utils.time import Time


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
    def __init__(self, url: str, token: str):
        self.url = url
        self.token = token

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

        # build header
        headers = {"Authorization": "Token " + self.token}

        async with aiohttp.ClientSession() as session:
            async with session.get(
                urljoin(self.url, path), headers=headers, timeout=timeout, params=params
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
