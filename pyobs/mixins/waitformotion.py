import logging
import time
from threading import Event
from typing import Union, List

from pyobs import PyObsModule
from pyobs.interfaces import IMotion

log = logging.getLogger(__name__)


class WaitForMotionMixin:
    """Mixin for a device that should wait for the motion status of another device."""
    def __init__(self, wait_for_devices: List[str] = None, wait_for_states: List[str] = None,
                 wait_for_timeout: float = None, *args, **kwargs):
        """Initializes the mixin.

        Args:
            wait_for_devices: One or more devices to wait for.
            wait_for_states: List of states to wait for.
            wait_for_timeout: Wait timeout in seconds.
        """

        # store
        self.__wait_for_devices = wait_for_devices if wait_for_devices is not None else []
        self.__wait_for_states = [IMotion.Status(s) for s in wait_for_states] if wait_for_states is not None else []
        self.__wait_for_timeout = wait_for_timeout

    def _wait_for_motion(self, abort: Event):
        """Wait until all devices are in one of the given motion states.

        Args:
            event: Abort event.

        Raises:
            TimeoutError if wait timed out.
        """

        # I'm a module!
        self: Union[WaitForMotionMixin, PyObsModule]

        # get all proxies
        proxies = [self.proxy(device) for device in self.__wait_for_devices]

        # all need to be derived from IMotion
        if not all([isinstance(p, IMotion) for p in proxies]):
            raise ValueError('Not all given devices are derived from IMotion!')

        # run until timeout
        start = time.time()
        while not abort.is_set():
            # timeout?
            if time.time() > start + self.__wait_for_timeout:
                raise TimeoutError

            # get all states and compare them
            states = [p.get_motion_status().wait() for p in proxies]

            # in a good state?
            good = [s in self.__wait_for_states for s in states]

            # if all good, we're finished waiting
            if all(good):
                break


__all__ = ['WaitForMotionMixin']