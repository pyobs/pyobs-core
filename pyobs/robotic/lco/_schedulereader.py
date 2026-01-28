import asyncio
import asyncio.exceptions
import logging
from typing import Any
import aiodns
from astropy.time import TimeDelta
import astropy.units as u

from pyobs.robotic.observation import Observation, ObservationList
from pyobs.utils.time import Time
from ._portal import Portal
from .task import LcoTask
from ...object import Object
from ...utils.logger import DuplicateFilter
from ...utils.logging.resolvableerror import ResolvableErrorLogger
from ...utils.parallel import acquire_lock

log = logging.getLogger(__name__)

# logger for logging errors
error_logger = logging.getLogger(__name__ + ":error")
error_logger.addFilter(DuplicateFilter())


class LcoScheduleReader(Object):
    """Scheduler for using the LCO portal"""

    def __init__(
        self,
        portal: Portal,
        site: str,
        telescope: str,
        auto_updates: bool = True,
        **kwargs: Any,
    ):
        """Creates a new LCO scheduler.

        Args:
            url: URL to portal
            site: Site filter for fetching requests
            token: Authorization token for portal
            telescope: Telescope for new schedules.
            auto_updates: Whether schedule is updated automatically.
        """
        Object.__init__(self, **kwargs)

        # store stuff
        self._portal = portal
        self._site = site
        self._telescope = telescope
        self._last_schedule_time: Time | None = None
        self._update_lock = asyncio.Lock()
        self._auto_updates = auto_updates

        # buffers in case of errors
        self._last_scheduled: Time | None = None

        # task list
        self._scheduled_tasks = ObservationList()

        # error logging for regular updates
        self._update_error_log = ResolvableErrorLogger(log, error_level=logging.WARNING)

        # background task
        if auto_updates:
            self.add_background_task(self._update_schedule)

    async def _update_schedule(self) -> None:
        """Update thread."""

        while True:
            await asyncio.sleep(10)

            # get time of last schedule
            try:
                last_scheduled = await self._portal.last_scheduled()
            except asyncio.CancelledError:
                return
            except:
                continue

            # get time of last scheduler run and check, whether we need an update, which is not the case, if
            # - we updated before
            # - AND last update was after last schedule update
            if self._last_schedule_time is not None and (
                last_scheduled is None or self._last_schedule_time >= last_scheduled
            ):
                continue

            # do actual update
            try:
                await self._update_schedule_now()
                error_logger.info("Successfully updated schedule.")
            except asyncio.CancelledError:
                return
            except asyncio.TimeoutError:
                # do nothing
                error_logger.warning("Could not retrieve schedule.")
            except:
                log.exception("An exception occurred.")

    async def _update_schedule_now(self, force: bool = False) -> None:
        """Update list of requests.

        Args:
            force: Force update.
        """

        # acquire lock
        if not await acquire_lock(self._update_lock, 20):
            return

        try:
            # remember now
            now = Time.now()

            # need update!
            try:
                scheduled_tasks = await self._download_schedule(
                    end_after=now, start_before=now + TimeDelta(24 * u.hour)
                )
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

    async def _download_schedule(self, start_before: Time, end_after: Time) -> ObservationList:
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

        # download schedule
        schedules = await self._portal.download_schedule(start_before, end_after)

        # create tasks
        scheduled_tasks = ObservationList()
        for sched in schedules:
            # create task
            task = LcoTask.from_lco_request(sched)

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
        await self._update_schedule_now()

        # loop all tasks
        for scheduled_task in self._scheduled_tasks:
            # running now?
            if scheduled_task.start <= time < scheduled_task.end and not scheduled_task.task.is_finished():
                return scheduled_task

        # nothing found
        return None


__all__ = ["LcoScheduleReader"]
