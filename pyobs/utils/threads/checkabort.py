import threading
from typing import Optional

from astropy.time import Time


def check_abort(abort_event: threading.Event, end: Optional[Time] = None) -> None:
    """Throws an exception, if abort_event is set or window has passed

    Args:
        abort_event: Event to check
        end: End of observing window for task

    Raises:
        InterruptedError: if task should be aborted
    """

    # check abort event
    if abort_event.is_set():
        raise InterruptedError

    # check time
    if end is not None and end < Time.now():
        raise InterruptedError
