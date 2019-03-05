import threading
from enum import Enum

from pytel.interfaces import ITelescope
from pytel import PytelModule
from pytel.modules import timeout
from pytel.utils.threads import LockWithAbort


class BaseTelescope(PytelModule, ITelescope):
    """Base class for telescopes."""

    class Status(Enum):
        """Telescope status values."""
        PARKED = 'parked'
        INITPARK = 'initpark'
        IDLE = 'idle'
        SLEWING = 'slewing'
        TRACKING = 'tracking'
        ERROR = 'error'

    def __init__(self, *args, **kwargs):
        """Initialize a new base telescope."""
        PytelModule.__init__(self, *args, **kwargs)

        # some multi-threading stuff
        self._lock_moving = threading.Lock()
        self._abort_move = threading.Event()

    def status(self, *args, **kwargs) -> dict:
        """Returns current status.

        Returns:
            dict: A dictionary with status values.
        """
        return {}

    def init(self, *args, **kwargs):
        """Initialize telescope.

        Raises:
            ValueError: If telescope could not be initialized.
        """
        raise NotImplementedError

    def park(self, *args, **kwargs):
        """Park telescope.

        Raises:
            ValueError: If telescope could not be parked.
        """
        raise NotImplementedError

    def reset_offset(self, *args, **kwargs):
        """Reset Alt/Az offset.

        Raises:
            ValueError: If offset could not be reset.
        """
        raise NotImplementedError

    def _track(self, ra: float, dec: float, abort_event: threading.Event):
        """Actually starts tracking on given coordinates. Must be implemented by derived classes.

        Args:
            ra: RA in deg to track.
            dec: Dec in deg to track.
            abort_event: Event that gets triggered when movement should be aborted.

        Raises:
            Exception: On any error.
        """

        raise NotImplementedError

    @timeout(60000)
    def track(self, ra: float, dec: float, *args, **kwargs):
        """Starts tracking on given coordinates.

        Args:
            ra: RA in deg to track.
            dec: Dec in deg to track.

        Raises:
            ValueError: If telescope could not track.
        """

        # acquire lock
        with LockWithAbort(self._lock_moving, self._abort_move):
            # track telescope
            return self._track(ra, dec, abort_event=self._abort_move)

    def offset(self, dalt: float, daz: float, *args, **kwargs):
        """Move an Alt/Az offset, which will be reset on next call of track.

        Args:
            dalt: Altitude offset in degrees.
            daz: Azimuth offset in degrees.

        Raises:
            ValueError: If offset could not be set.
        """
        raise NotImplementedError

    def _move(self, alt: float, az: float, abort_event: threading.Event):
        """Actually moves to given coordinates. Must be implemented by derived classes.

        Args:
            alt: Alt in deg to move to.
            az: Az in deg to move to.
            abort_event: Event that gets triggered when movement should be aborted.

        Raises:
            Exception: On error.
        """
        raise NotImplementedError

    def move(self, alt: float, az: float, *args, **kwargs):
        """Moves to given coordinates.

        Args:
            alt: Alt in deg to move to.
            az: Az in deg to move to.

        Raises:
            Exception: On error.
        """

        # acquire lock
        with LockWithAbort(self._lock_moving, self._abort_move):
            # move telescope
            return self._move(alt, az, abort_event=self._abort_move)


__all__ = ['BaseTelescope']
