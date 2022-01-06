import asyncio
from urllib.parse import urljoin
import logging
from typing import List, Dict, Optional, Any, cast

import aiohttp as aiohttp
from astroplan import (
    TimeConstraint,
    AirmassConstraint,
    ObservingBlock,
    FixedTarget,
    MoonSeparationConstraint,
    MoonIlluminationConstraint,
    AtNightConstraint,
)
from astropy.coordinates import SkyCoord
from astropy.time import TimeDelta
import astropy.units as u

from pyobs.robotic.task import Task
from pyobs.utils.time import Time
from ..taskarchive import TaskArchive
from .task import LcoTask

log = logging.getLogger(__name__)


class LcoTaskArchive(TaskArchive):
    """Scheduler for using the LCO portal"""

    def __init__(
        self,
        url: str,
        site: str,
        token: str,
        telescope: Optional[str] = None,
        camera: Optional[str] = None,
        filters: Optional[str] = None,
        roof: Optional[str] = None,
        autoguider: Optional[str] = None,
        update: bool = True,
        scripts: Optional[Dict[str, Any]] = None,
        portal_enclosure: Optional[str] = None,
        portal_telescope: Optional[str] = None,
        portal_instrument: Optional[str] = None,
        portal_instrument_type: Optional[str] = None,
        period: int = 24,
        proxies: Optional[List[str]] = None,
        **kwargs: Any,
    ):
        """Creates a new LCO scheduler.

        Args:
            url: URL to portal
            site: Site filter for fetching requests
            token: Authorization token for portal
            telescope: Telescope to use
            camera: Camera to use
            filters: Filter wheel to use
            roof: Roof to use
            autoguider: Autoguider to use
            update: Whether to update scheduler in background
            scripts: External scripts
            portal_enclosure: Enclosure for new schedules.
            portal_telescope: Telescope for new schedules.
            portal_instrument: Instrument for new schedules.
            portal_instrument_type: Instrument type to schedule.
            period: Period to schedule in hours
            proxies: Proxies for requests.
        """
        TaskArchive.__init__(self, **kwargs)

        # store stuff
        self._url = url
        self._site = site
        self._portal_enclosure = portal_enclosure
        self._portal_telescope = portal_telescope
        self._portal_instrument = portal_instrument
        self._portal_instrument_type = portal_instrument_type
        self._period = TimeDelta(period * u.hour)
        self.telescope = telescope
        self.camera = camera
        self.filters = filters
        self.roof = roof
        self.autoguider = autoguider
        self.instruments: Dict[str, Any] = {}
        self._update = update
        self._last_schedule_time: Optional[Time] = None
        self.scripts = scripts
        self._proxies = {} if proxies is None else proxies

        # buffers in case of errors
        self._last_scheduled: Optional[Time] = None
        self._last_changed: Optional[Time] = None

        # header
        self._token = token
        self._header = {"Authorization": "Token " + token}

        # task list
        self._tasks: Dict[str, LcoTask] = {}

    async def open(self) -> None:
        """Open scheduler."""

        # get stuff from portal
        await self._init_from_portal()

        # start update thread
        if self._update:
            asyncio.create_task(self._update_schedule())

    async def _portal_get(self, url: str) -> dict:
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
            async with session.get(url, headers=self._header, timeout=10) as response:
                if response.status != 200:
                    raise RuntimeError("Invalid response from portal: " + await response.text())
                return await response.json()

    async def _init_from_portal(self) -> None:
        """Initialize scheduler from portal."""

        # get instruments
        # don't catch exception, we want to fail, if something goes wrong here
        data = await self._portal_get(urljoin(self._url, "/api/instruments/"))

        # and store
        self.instruments = {k.lower(): v for k, v in data.items()}

    async def _update_schedule(self) -> None:
        """Update thread."""
        while True:
            # do actual update
            try:
                await self._update_now()
            except:
                log.exception("An exception occurred.")

            # sleep a little
            await asyncio.sleep(10)

    async def _update_now(self, force: bool = False) -> None:
        """Update list of requests.

        Args:
            force: Force update.
        """

        # remember now
        now = Time.now()

        # get time of last scheduler run and check, whether we need an update, which is not the case, if
        # - we updated before
        # - AND last update was after last schedule update
        # - AND last update is less then 1 min ago
        # - AND force is set to False
        last_scheduled = await self.last_scheduled()
        if (
            self._last_schedule_time is not None
            and (last_scheduled is None or self._last_schedule_time >= last_scheduled)
            and self._last_schedule_time > now - TimeDelta(1.0 * u.minute)
            and force is False
        ):
            # need no update
            return

        # need update!
        try:
            tasks = await self.get_pending_tasks(
                end_after=now, start_before=now + TimeDelta(24 * u.hour), include_running=False
            )
        except TimeoutError:
            log.error("Request timed out")
            await asyncio.sleep(60)
            return
        except RuntimeError:
            log.warning("Could not fetch schedule.")
            return

        # any changes?
        if sorted(tasks) != sorted(self._tasks):
            log.info("Task list changed, found %d task(s) to run.", len(tasks))
            for task_id, task in tasks.items():
                log.info(f"  - {task.start} to {task.end}: {task.name} (#{task_id})")

        # update
        self._tasks = cast(Dict[str, LcoTask], tasks)

        # finished
        self._last_schedule_time = now

    async def get_pending_tasks(
        self, start_before: Time, end_after: Time, include_running: bool = True
    ) -> Dict[str, Task]:
        """Fetch pending tasks from portal.

        Args:
            start_before: Task must start before this time.
            end_after: Task must end after this time.
            include_running: Whether to include a currently running task.

        Returns:
            Dictionary with tasks.

        Raises:
            Timeout: If request timed out.
            RuntimeError: If something goes wrong.
        """

        # define states
        states = ["PENDING"]
        if include_running:
            states += ["IN_PROGRESS"]

        # get url and params
        url = urljoin(self._url, "/api/observations/")
        params = {
            "site": self._site,
            "end_after": end_after.isot,
            "start_before": start_before.isot,
            "state": states,
            "request_state": "PENDING",
            "limit": 1000,
        }

        # do request
        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=self._header, params=params, timeout=10) as response:
                if response.status != 200:
                    raise RuntimeError("Invalid response from portal.")
                data = await response.json()

                # get schedule
                schedules = data["results"]

                # create tasks
                tasks = {}
                for sched in schedules:
                    # parse start and end
                    sched["start"] = Time(sched["start"])
                    sched["end"] = Time(sched["end"])

                    # create task
                    task = self._create_task(LcoTask, config=sched, scripts=self.scripts)
                    tasks[sched["request"]["id"]] = task

                # finished
                return tasks

    def get_task(self, time: Time) -> Optional[LcoTask]:
        """Returns the active task at the given time.

        Args:
            time: Time to return task for.

        Returns:
            Task at the given time or None.
        """

        # loop all tasks
        for task in self._tasks.values():
            # running now?
            if task.start <= time < task.end and not task.is_finished():
                return task

        # nothing found
        return None

    async def run_task(self, task: Task) -> bool:
        """Run a task.

        Args:
            task: Task to run

        Returns:
            Success or not
        """

        # run task
        await task.run()

        # force update tasks
        await self._update_now(force=True)

        # finish
        return True

    async def send_update(self, status_id: int, status: Dict[str, Any]) -> None:
        """Send report to LCO portal

        Args:
            status_id: id of config status
            status: Status dictionary
        """

        log.info("Sending configuration status update to portal...")
        url = urljoin(self._url, "/api/configurationstatus/%d/" % status_id)

        # do request
        try:
            async with aiohttp.ClientSession() as session:
                async with session.patch(url, json=status, headers=self._header, timeout=10) as response:
                    if response.status != 200:
                        log.error("Could not update configuration status: %s", await response.text())

        except TimeoutError:
            log.error("Request timed out.")

    async def last_changed(self) -> Optional[Time]:
        """Returns time when last time any blocks changed."""

        # try to update time
        try:
            # get data
            data = await self._portal_get(urljoin(self._url, "/api/last_changed/"))

            # get last change
            self._last_changed = data["last_change_time"]
            return self._last_changed

        except TimeoutError:
            # in case of errors, return last time
            return self._last_changed

    async def last_scheduled(self) -> Optional[Time]:
        """Returns time of last scheduler run."""

        # try to update time
        try:
            # get data
            data = await self._portal_get(urljoin(self._url, "/api/last_scheduled/"))

            # get last change
            self._last_changed = data["last_schedule_time"]
            return self._last_changed

        except TimeoutError:
            # in case of errors, return last time
            return self._last_scheduled

    async def get_schedulable_blocks(self) -> List[ObservingBlock]:
        """Returns list of schedulable blocks.

        Returns:
            List of schedulable blocks
        """

        # check
        if self._portal_instrument_type is None:
            raise ValueError("No instrument type for portal set.")

        # get data
        schedulable = await self._portal_get(urljoin(self._url, "/api/requestgroups/schedulable_requests/"))

        # get proposal priorities
        data = await self._portal_get(urljoin(self._url, "/api/proposals/"))
        tac_priorities = {p["id"]: p["tac_priority"] for p in data["results"]}

        # loop all request groups
        blocks = []
        for group in schedulable:
            # get base priority, which is tac_priority * ipp_value
            proposal = group["proposal"]
            if proposal not in tac_priorities:
                log.error('Could not find proposal "%s".', proposal)
                continue
            base_priority = group["ipp_value"] * tac_priorities[proposal]

            # loop all requests in group
            for req in group["requests"]:
                # still pending?
                if req["state"] != "PENDING":
                    continue

                # duration
                duration = req["duration"] * u.second

                # time constraints
                time_constraints = [TimeConstraint(Time(wnd["start"]), Time(wnd["end"])) for wnd in req["windows"]]

                # loop configs
                for cfg in req["configurations"]:
                    # get instrument and check, whether we schedule it
                    instrument = cfg["instrument_type"]
                    if instrument.lower() != self._portal_instrument_type.lower():
                        continue

                    # target
                    t = cfg["target"]
                    target = SkyCoord(t["ra"] * u.deg, t["dec"] * u.deg, frame=t["type"].lower())

                    # constraints
                    c = cfg["constraints"]
                    constraints = []
                    if "max_airmass" in c and c["max_airmass"] is not None:
                        constraints.append(AirmassConstraint(max=c["max_airmass"], boolean_constraint=False))
                    if "min_lunar_distance" in c and c["min_lunar_distance"] is not None:
                        constraints.append(MoonSeparationConstraint(min=c["min_lunar_distance"] * u.deg))
                    if "max_lunar_phase" in c and c["max_lunar_phase"] is not None:
                        constraints.append(MoonIlluminationConstraint(max=c["max_lunar_phase"]))
                        # if max lunar phase <= 0.4 (which would be DARK), we also enforce the sun to be <-18 degrees
                        if c["max_lunar_phase"] <= 0.4:
                            constraints.append(AtNightConstraint.twilight_astronomical())

                    # priority is base_priority times duration in minutes
                    # priority = base_priority * duration.value / 60.
                    priority = base_priority

                    # create block
                    block = ObservingBlock(
                        FixedTarget(target, name=req["id"]),
                        duration,
                        priority,
                        constraints=[*constraints, *time_constraints],
                        configuration={"request": req},
                    )
                    blocks.append(block)

        # return blocks
        return blocks

    async def update_schedule(self, blocks: List[ObservingBlock], start_time: Time) -> None:
        """Update the list of scheduled blocks.

        Args:
            blocks: Scheduled blocks.
            start_time: Start time for schedule.
        """

        # create observations
        observations = self._create_observations(blocks)

        # cancel schedule
        await self._cancel_schedule(start_time)

        # send new schedule
        await self._submit_observations(observations)

    async def _cancel_schedule(self, now: Time) -> None:
        """Cancel future schedule."""

        # define parameters
        params = {
            "site": self._site,
            "enclosure": self._portal_enclosure,
            "telescope": self._portal_telescope,
            "start": now.isot,
            "end": (now + self._period).isot,
        }

        # url and headers
        url = urljoin(self._url, "/api/observations/cancel/")
        headers = {"Authorization": "Token " + self._token, "Content-Type": "application/json; charset=utf8"}

        # cancel schedule
        log.info("Deleting all scheduled tasks after %s...", now.isot)
        async with aiohttp.ClientSession() as session:
            async with session.post(url, json=params, headers=headers, timeout=10) as response:
                if response.status != 200:
                    log.error("Could not cancel schedule: %s", await response.text())

    def _create_observations(self, blocks: List[ObservingBlock]) -> List[Dict[str, Any]]:
        """Create observations from schedule.

        Args:
            blocks: List of scheduled blocks

        Returns:
            List with observations.
        """

        # loop blocks
        observations = []
        for block in blocks:
            # get request
            request = block.configuration["request"]

            # add observation
            observations.append(
                {
                    "site": self._site,
                    "enclosure": self._portal_enclosure,
                    "telescope": self._portal_telescope,
                    "start": block.start_time.isot,
                    "end": block.end_time.isot,
                    "request": request["id"],
                    "configuration_statuses": [
                        {
                            "configuration": request["configurations"][0]["id"],
                            "instrument_name": self._portal_instrument,
                            "guide_camera_name": self._portal_instrument,
                        }
                    ],
                }
            )

        # return list
        return observations

    async def _submit_observations(self, observations: List[Dict[str, Any]]) -> None:
        """Submit observations.

        Args:
            observations: List of observations to submit.
        """

        # nothing?
        if len(observations) == 0:
            return

        # url and headers
        url = urljoin(self._url, "/api/observations/")
        headers = {"Authorization": "Token " + self._token, "Content-Type": "application/json; charset=utf8"}

        # submit obervations
        async with aiohttp.ClientSession() as session:
            async with session.post(url, json=observations, headers=headers, timeout=10) as response:
                if response.status != 200:
                    log.error("Could not submit observations: %s", await response.text())
                data = await response.json()

        # log
        log.info("%d observations created.", data["num_created"])

        # errors?
        if "errors" in data:
            for err in data["errors"].values():
                log.warning("Error from portal: %s", err["non_field_errors"])


__all__ = ["LcoTaskArchive"]
