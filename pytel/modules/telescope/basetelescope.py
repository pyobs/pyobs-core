import threading
from enum import Enum

from pytel.interfaces import ITelescope
from pytel import PytelModule
from pytel.modules import timeout
from pytel.utils.threads import LockWithAbort


class BaseTelescope(PytelModule, ITelescope):
    class Status(Enum):
        PARKED = 'parked'
        INITPARK = 'initpark'
        IDLE = 'idle'
        SLEWING = 'slewing'
        TRACKING = 'tracking'
        ERROR = 'error'

    def __init__(self, *args, **kwargs):
        PytelModule.__init__(self, *args, **kwargs)

        # some multi-threading stuff
        self._lock_moving = threading.Lock()
        self._abort_move = threading.Event()

    def status(self, *args, **kwargs) -> dict:
        return {}

    def park(self, *args, **kwargs) -> bool:
        raise NotImplementedError

    def init(self, *args, **kwargs) -> bool:
        raise NotImplementedError

    def reset_offset(self, *args, **kwargs) -> bool:
        raise NotImplementedError

    def _track(self, ra: float, dec: float, abort_event: threading.Event) -> bool:
        raise NotImplementedError

    @timeout(60000)
    def track(self, ra: float, dec: float, *args, **kwargs) -> bool:
        # acquire lock
        with LockWithAbort(self._lock_moving, self._abort_move):
            # track telescope
            return self._track(ra, dec, abort_event=self._abort_move)

    def offset(self, dalt: float, daz: float, *args, **kwargs) -> bool:
        raise NotImplementedError

    def _move(self, alt: float, az: float, abort_event: threading.Event) -> bool:
        raise NotImplementedError

    def move(self, alt: float, az: float, *args, **kwargs) -> bool:
        # acquire lock
        with LockWithAbort(self._lock_moving, self._abort_move):
            # move telescope
            return self._move(alt, az, abort_event=self._abort_move)


__all__ = ['BaseTelescope']
