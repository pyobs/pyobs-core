import asyncio
from urllib.parse import urljoin
import logging
from typing import List, Dict, Optional, Any, cast
import aiohttp as aiohttp
from astroplan import ObservingBlock
from astropy.time import TimeDelta
import astropy.units as u

from pyobs.robotic.task import Task
from pyobs.utils.time import Time
from pyobs.robotic.taskschedule import TaskSchedule
from .portal import Portal
from .task import LcoTask

log = logging.getLogger(__name__)


class LcoTaskSchedule(TaskSchedule):
    """Scheduler for using the LCO portal"""

    def __init__(
        self,
        url: str,
        site: str,
        token: str,
        enclosure: Optional[str] = None,
        telescope: Optional[str] = None,
        instrument: Optional[str] = None,
        period: int = 24,
        scripts: Optional[Dict[str, Any]] = None,
        **kwargs: Any,
    ):
        """Creates a new LCO scheduler.

        Args:
            url: URL to portal
            site: Site filter for fetching requests
            token: Authorization token for portal
            portal_enclosure: Enclosure for new schedules.
            portal_telescope: Telescope for new schedules.
            portal_instrument: Instrument for new schedules.
            period: Period to schedule in hours
            scripts: External scripts
        """
        TaskSchedule.__init__(self, **kwargs)

        # portal
        self._portal = Portal(url, token)

        # store stuff
        self._url = url
        self._site = site
        self._enclosure = enclosure
        self._telescope = telescope
        self._instrument = instrument
        self._period = TimeDelta(period * u.hour)
        self.instruments: Dict[str, Any] = {}
        self._last_schedule_time: Optional[Time] = None
        self._scripts = scripts

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
        await TaskSchedule.open(self)

        # get stuff from portal
        await self._init_from_portal()

        # start update thread
        asyncio.create_task(self._update_schedule())

    async def _init_from_portal(self) -> None:
        """Initialize scheduler from portal."""

        # get instruments
        # don't catch exception, we want to fail, if something goes wrong here
        data = await self._portal.instruments()

        # and store
        self.instruments = {k.lower(): v for k, v in data.items()}

    async def last_scheduled(self) -> Optional[Time]:
        """Returns time of last scheduler run."""

        # try to update time
        try:
            # get data
            self._last_scheduled = await self._portal.last_scheduled()

        finally:
            # even in case of errors, return last time
            return self._last_scheduled

    async def _update_schedule(self) -> None:
        """Update thread."""
        while True:
            # do actual update
            try:
                await self.update_now()
            except:
                log.exception("An exception occurred.")

            # sleep a little
            await asyncio.sleep(10)

    async def update_now(self, force: bool = False) -> None:
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
            tasks = await self.get_schedule(
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

    async def get_schedule(self, start_before: Time, end_after: Time, include_running: bool = True) -> Dict[str, Task]:
        """Fetch schedule from portal.

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
                    task = self._create_task(LcoTask, config=sched, scripts=self._scripts)
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
            "enclosure": self._enclosure,
            "telescope": self._telescope,
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
                    "enclosure": self._enclosure,
                    "telescope": self._telescope,
                    "start": block.start_time.isot,
                    "end": block.end_time.isot,
                    "request": request["id"],
                    "configuration_statuses": [
                        {
                            "configuration": request["configurations"][0]["id"],
                            "instrument_name": self._instrument,
                            "guide_camera_name": self._instrument,
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

        # submit observations
        async with aiohttp.ClientSession() as session:
            async with session.post(url, json=observations, headers=headers, timeout=10) as response:
                if response.status != 200:
                    log.error("Could not submit observations: %s", await response.text())
                data = await response.json()

        # log
        log.info("%d observations created.", data["num_created"])

        # errors?
        if "errors" in data and len(data["errors"]) > 0:
            for err in data["errors"].values():
                log.warning("Error from portal: " + str(err["non_field_errors"]))


__all__ = ["LcoTaskSchedule"]
