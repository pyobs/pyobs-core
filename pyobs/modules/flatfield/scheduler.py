import asyncio
import logging
from typing import Any

from pyobs.interfaces import IBinning, IFilters, IFlatField, IRunnable
from pyobs.modules import Module, timeout
from pyobs.object import get_object
from pyobs.robotic.utils.skyflats.priorities.base import SkyflatPriorities
from pyobs.robotic.utils.skyflats.scheduler import Scheduler
from pyobs.utils.parallel import event_wait
from pyobs.utils.time import Time

log = logging.getLogger(__name__)


class FlatFieldScheduler(Module, IRunnable):
    """Run the flat-field scheduler."""

    __module__ = "pyobs.modules.flatfield"

    def __init__(
        self,
        flatfield: str | IFlatField,
        functions: str | dict[str, str | dict[str, str]],
        priorities: dict[str, Any] | SkyflatPriorities,
        min_exptime: float = 0.5,
        max_exptime: float = 5,
        timespan: float = 7200,
        filter_change: float = 30,
        count: int = 20,
        **kwargs: Any,
    ):
        """Initialize a new flat field scheduler.

        Args:
            flatfield: Flat field module to use
            functions: Dict with flat functions
            priorities: Class handling priorities
            min_exptime: Minimum exposure time [s]
            max_exptime: Maximum exposure time [s]
            timespan: Time to scheduler after start [s]
            filter_change: Time required for filter change [s]
            count: Number of flats to take per filter/binning
        """
        Module.__init__(self, **kwargs)

        # store
        self._flatfield = flatfield
        self._count = count
        self._running = False

        # abort
        self._abort = asyncio.Event()

        # priorities
        prio = get_object(priorities, SkyflatPriorities)

        # create scheduler
        self._scheduler = Scheduler(
            functions,
            prio,
            self._observer,
            min_exptime=min_exptime,
            max_exptime=max_exptime,
            timespan=timespan,
            filter_change=filter_change,
            count=count,
        )

    async def open(self) -> None:
        """Open module"""
        await Module.open(self)

        # check flat field
        if not await self.has_proxy(self._flatfield, IFlatField):
            log.warning("Flatfield module does not exist or is not of correct type at the moment.")

    @timeout(7200)
    async def run(self, **kwargs: Any) -> None:
        """Perform flat-fielding"""

        # check
        if self._running:
            raise ValueError("Already running.")
        self._running = True

        try:
            # start
            log.info("Performing flat fielding...")
            self._abort = asyncio.Event()

            # do schedule
            log.info("Scheduling flats...")
            await self._scheduler(Time.now())

            # do flat fields
            for item in self._scheduler:
                # aborted?
                if self._abort.is_set():
                    log.info("Scheduler aborted.")
                    break

                # start
                log.info("Taking %d flats in %s %dx%d...", self._count, item.filter_name, item.binning, item.binning)
                async with self.proxy(self._flatfield, IFilters) as proxy:
                    await proxy.set_filter(item.filter_name)
                async with self.proxy(self._flatfield, IBinning) as proxy:
                    await proxy.set_binning(*item.binning)
                async with self.proxy(self._flatfield, IFlatField) as proxy:
                    future = asyncio.create_task(proxy.flat_field(self._count))

                # wait for it
                while not future.done():
                    # aborted?
                    if self._abort.is_set():
                        log.info("Aborting current flat field...")
                        async with self.proxy(self._flatfield, IFlatField) as proxy:
                            await proxy.abort()

                    # sleep a little
                    await event_wait(self._abort, 1)

                # finished
                log.info("Finished.")

        finally:
            self._running = False

    @timeout(20)
    async def abort(self, **kwargs: Any) -> None:
        """Abort current actions."""
        self._abort.set()


__all__ = ["FlatFieldScheduler"]
