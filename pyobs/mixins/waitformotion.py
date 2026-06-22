from __future__ import annotations

import logging
import time
from asyncio import Event
from typing import Any

from pyobs.interfaces import IMotion
from pyobs.modules import Module
from pyobs.utils.enums import MotionStatus
from pyobs.utils.parallel import event_wait

log = logging.getLogger(__name__)


class WaitForMotionMixin:
    """Mixin for a device that should wait for the motion status of another device."""

    __module__ = "pyobs.mixins"

    def __init__(
        self,
        wait_for_modules: list[str] | None = None,
        wait_for_states: list[MotionStatus | str] | None = None,
        wait_for_timeout: float = 0,
        **kwargs: Any,
    ):
        """Initializes the mixin.

        Args:
            wait_for_modules: One or more modules to wait for.
            wait_for_states: List of states to wait for.
            wait_for_timeout: Wait timeout in seconds.
        """

        # store
        self.__wait_for_modules = wait_for_modules if wait_for_modules is not None else []
        self.__wait_for_states = (
            [s if isinstance(s, MotionStatus) else MotionStatus(s) for s in wait_for_states]
            if wait_for_states is not None
            else []
        )
        self.__wait_for_timeout = wait_for_timeout

    async def _wait_for_motion(self, abort: Event) -> None:
        """Wait until all devices are in one of the given motion states.

        Args:
            abort: Abort event.

        Raises:
            TimeoutError: If wait timed out.
        """

        # no device?
        if len(self.__wait_for_modules) == 0:
            return

        # check type
        this = self
        if not isinstance(self, Module):
            raise ValueError("This is not a module.")

        # all need to be derived from IMotion
        if not all([self.has_proxy(device, IMotion) for device in this.__wait_for_modules]):
            raise ValueError("Not all given devices are derived from IMotion!")

        # run until timeout
        start = time.time()
        log.info("Waiting for motion of other modules...")
        while not abort.is_set():
            # timeout?
            if time.time() > start + this.__wait_for_timeout:
                raise TimeoutError

            # loop all modules
            for module in this.__wait_for_modules:
                async with self.proxy(module, IMotion) as proxy:
                    state = await proxy.get_motion_status()
                    if state not in this.__wait_for_states:
                        break
            else:
                # if all good, we're finished waiting
                log.info("All other modules have finished moving.")
                break

            # sleep a little
            await event_wait(abort, 1)


__all__ = ["WaitForMotionMixin"]
