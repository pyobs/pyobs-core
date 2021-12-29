import logging
import time
from asyncio import Event
from typing import Union, List, Any, Optional

from pyobs.interfaces import IMotion
from pyobs.modules import Module
from pyobs.utils.enums import MotionStatus
from pyobs.utils.parallel import event_wait

log = logging.getLogger(__name__)


class WaitForMotionMixin:
    """Mixin for a device that should wait for the motion status of another device."""
    __module__ = 'pyobs.mixins'

    def __init__(self, wait_for_modules: Optional[List[str]] = None,
                 wait_for_states: Optional[List[Union[MotionStatus, str]]] = None,
                 wait_for_timeout: float = 0, **kwargs: Any):
        """Initializes the mixin.

        Args:
            wait_for_modules: One or more modules to wait for.
            wait_for_states: List of states to wait for.
            wait_for_timeout: Wait timeout in seconds.
        """

        # store
        self.__wait_for_modules = wait_for_modules if wait_for_modules is not None else []
        self.__wait_for_states = [s if isinstance(s, MotionStatus) else MotionStatus(s)
                                  for s in wait_for_states] if wait_for_states is not None else []
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
            raise ValueError('This is not a module.')

        # get all proxies
        proxies = [await self.proxy(device) for device in this.__wait_for_modules]

        # all need to be derived from IMotion
        if not all([isinstance(p, IMotion) for p in proxies]):
            raise ValueError('Not all given devices are derived from IMotion!')

        # run until timeout
        start = time.time()
        log.info('Waiting for motion of other modules...')
        while not abort.is_set():
            # timeout?
            if time.time() > start + this.__wait_for_timeout:
                raise TimeoutError

            # get all states and compare them
            states = [await p.get_motion_status() for p in proxies]

            # in a good state?
            good = [s in this.__wait_for_states for s in states]

            # if all good, we're finished waiting
            if all(good):
                log.info('All other modules have finished moving.')
                break

            # sleep a little
            await event_wait(abort, 1)


__all__ = ['WaitForMotionMixin']
