import asyncio
import asyncio.exceptions
from urllib.parse import urljoin
import logging
from typing import Any, cast, Literal
import aiodns
import aiohttp as aiohttp
from astropy.time import TimeDelta
import astropy.units as u

from pyobs.robotic.observation import Observation, ObservationList
from pyobs.utils.time import Time
from pyobs.robotic.taskschedule import TaskSchedule
from .portal import Portal
from .configdb import ConfigDB
from .task import LcoTask
from ...utils.logger import DuplicateFilter
from ...utils.logging.resolvableerror import ResolvableErrorLogger
from ...utils.parallel import acquire_lock

log = logging.getLogger(__name__)

# logger for logging errors
error_logger = logging.getLogger(__name__ + ":error")
error_logger.addFilter(DuplicateFilter())


class LcoTaskSchedule(TaskSchedule):
    """Scheduler for using the LCO portal"""

    def __init__(
        self,
        url: str,
        configdb: str,
        site: str,
        token: str,
        enclosure: str | None = None,
        telescope: str | None = None,
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
            portal_enclosure: Enclosure for new schedules.
            portal_telescope: Telescope for new schedules.
            portal_instrument: Instrument for new schedules.
            period: Period to schedule in hours
        """
        TaskSchedule.__init__(self, **kwargs)

        # portal
        self._portal = Portal(url, token)
        self._configdb = ConfigDB(configdb)

        # store stuff
        self._url = url
        self._site = site
        self._enclosure = enclosure
        self._telescope = telescope
        self._period = TimeDelta(period * u.hour)
        self.instruments: dict[str, Any] = {}
        self._last_schedule_time: Time | None = None
        self._update_lock = asyncio.Lock()
        self._initialized = asyncio.Event()

        # buffers in case of errors
        self._last_scheduled: Time | None = None
        self._last_changed: Time | None = None

        # header
        self._token = token
        self._header = {"Authorization": "Token " + token}

        # task list
        self._scheduled_tasks = ObservationList()

        # error logging for regular updates
        self._update_error_log = ResolvableErrorLogger(log, error_level=logging.WARNING)

        # background task
        if mode in ["read", "readwrite"]:
            self.add_background_task(self._update_schedule)

    async def open(self) -> None:
        await TaskSchedule.open(self)

        # get stuff from portal and do initial update
        await self._init_from_portal()

    async def _init_from_portal(self) -> None:
        """Initialize scheduler from portal."""

        # get instruments
        # don't catch exception, we want to fail, if something goes wrong here
        data = await self._portal.instruments()

        # and store
        self.instruments = {k.lower(): v for k, v in data.items()}
        self._initialized.set()

    async def last_scheduled(self) -> Time | None:
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
                error_logger.info("Successfully updated schedule.")

            except asyncio.CancelledError:
                return

            except asyncio.TimeoutError:
                # do nothing
                error_logger.warning("Could not retrieve schedule.")

            except:
                log.exception("An exception occurred.")

            # sleep a little
            await asyncio.sleep(10)

    async def update_now(self, force: bool = False) -> None:
        """Update list of requests.

        Args:
            force: Force update.
        """

        # wait for init
        await self._initialized.wait()

        # acquire lock
        if not await acquire_lock(self._update_lock, 20):
            return

        try:
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
                scheduled_tasks = await self._get_schedule(end_after=now, start_before=now + TimeDelta(24 * u.hour))
                self._update_error_log.resolve("Successfully updated schedule.")
            except (TimeoutError, aiodns.error.DNSError):
                self._update_error_log.error("Network error in request for updating schedule.")
                await asyncio.sleep(60)
                return
            except RuntimeError:
                self._update_error_log.error("Could not fetch schedule.")
                return

            # any changes?
            if sorted(scheduled_tasks) != sorted(self._scheduled_tasks):
                log.info("Task list changed, found %d task(s) to run.", len(scheduled_tasks))
                for scheduled_task in sorted(scheduled_tasks, key=lambda x: x.start):
                    log.info(
                        f"  - {scheduled_task.start} to {scheduled_task.end}: {scheduled_task.task.name} (#{scheduled_task.task.id})"
                    )

                # update
                self._scheduled_tasks = scheduled_tasks

                # finished
                self._last_schedule_time = now

        finally:
            # release lock
            self._update_lock.release()

    async def get_schedule(self) -> ObservationList:
        """Fetch schedule from portal.

        Returns:
            Dictionary with tasks.

        Raises:
            Timeout: If request timed out.
            ValueError: If something goes wrong.
        """
        return self._scheduled_tasks

    async def _get_schedule(self, start_before: Time, end_after: Time) -> ObservationList:
        """Fetch schedule from portal.

        Args:
            start_before: Task must start before this time.
            end_after: Task must end after this time.

        Returns:
            List with tasks.

        Raises:
            Timeout: If request timed out.
            RuntimeError: If something goes wrong.
        """

        # define states
        states = ["PENDING", "IN_PROGRESS"]

        # get url and params
        url = urljoin(self._url, "/api/observations/")
        params = {
            "site": self._site,
            "telescope": self._telescope,
            "end_after": end_after.isot,
            "start_before": start_before.isot,
            "state": states,
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
                scheduled_tasks = ObservationList()
                for sched in schedules:
                    # create task
                    task = self._create_task(LcoTask, config=sched)

                    # create scheduled task
                    scheduled_task = Observation(task=task, start=Time(sched["start"]), end=Time(sched["end"]))

                    # add it
                    scheduled_tasks.append(scheduled_task)

                # finished
                return scheduled_tasks

    async def get_task(self, time: Time) -> Observation | None:
        """Returns the active scheduled task at the given time.

        Args:
            time: Time to return task for.

        Returns:
            Scheduled task at the given time.
        """

        # update schedule
        await self.update_now(force=True)

        # loop all tasks
        for scheduled_task in self._scheduled_tasks:
            # running now?
            if scheduled_task.start <= time < scheduled_task.end and not scheduled_task.task.is_finished():
                return scheduled_task

        # nothing found
        return None

    async def send_update(self, status_id: int, status: dict[str, Any]) -> None:
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

        except asyncio.TimeoutError:
            # schedule re-attempt for sending
            asyncio.create_task(self._send_update_later(status_id, status))

        # update
        await self.update_now()

    async def _send_update_later(self, status_id: int, status: dict[str, Any], delay: int = 300) -> None:
        """Delay re-attempt to send report to LCO portal

        Args:
            status_id: id of config status
            status: Status dictionary
            delay: Delay in seconds
        """

        # sleep
        await asyncio.sleep(delay)

        # re-send
        await self.send_update(status_id, status)

    async def add_schedule(self, tasks: ObservationList) -> None:
        """Add the list of scheduled tasks to the schedule.

        Args:
            tasks: Scheduled tasks.
        """

        # create observations
        observations = self._create_observations(tasks)

        # send new schedule
        await self._submit_observations(observations)

    async def clear_schedule(self, start_time: Time) -> None:
        """Clear schedule after given start time.

        Args:
            start_time: Start time to clear from.
        """

        # define parameters
        params = {
            "site": self._site,
            "enclosure": self._enclosure,
            "telescope": self._telescope,
            "start": start_time.isot,
            "end": (start_time + self._period).isot,
        }

        # url and headers
        url = urljoin(self._url, "/api/observations/cancel/")
        headers = {"Authorization": "Token " + self._token, "Content-Type": "application/json; charset=utf8"}

        # cancel schedule
        log.info("Deleting all scheduled tasks after %s...", start_time.isot)
        async with aiohttp.ClientSession() as session:
            async with session.post(url, json=params, headers=headers, timeout=10) as response:
                if response.status != 200:
                    log.error("Could not cancel schedule: %s", await response.text())

    def _create_observations(self, scheduled_tasks: ObservationList) -> list[dict[str, Any]]:
        """Create observations from schedule.

        Args:
            scheduled_tasks: List of scheduled tasks

        Returns:
            List with observations.
        """

        # loop tasks
        # TODO: get site, enclosure, telescope and instrument from obsportal using the instrument type
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

    async def _submit_observations(self, observations: list[dict[str, Any]]) -> None:
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
                if response.status != 201:
                    log.error("Could not submit observations: %s", await response.text())
                data = await response.json()

        # log
        log.info("%d observations created.", data["num_created"])

        # errors?
        if "errors" in data and len(data["errors"]) > 0:
            for err in data["errors"].values():
                log.warning(f"Error from portal: {err}")


__all__ = ["LcoTaskSchedule"]
