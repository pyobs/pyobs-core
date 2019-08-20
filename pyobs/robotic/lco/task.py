from threading import Event
from astropy.time import TimeDelta
import astropy.units as u

from pyobs.robotic.task import Task
from pyobs.utils.time import Time


class LcoTask(Task):
    def __init__(self, *args, **kwargs):
        self._finished = False

    def name(self) -> str:
        return 'test'

    def window(self) -> (Time, Time):
        now = Time.now()
        return now - TimeDelta(5 * u.minute), now + TimeDelta(5 * u.minute)

    def run(self, abort_event: Event):
        print("running task")
        self._finished = True

    def is_finished(self) -> bool:
        """Whether task is finished."""
        return self._finished

    def get_fits_headers(self) -> dict:
        return {}


__all__ = ['LcoTask']
