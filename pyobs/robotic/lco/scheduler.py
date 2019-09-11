import threading
import urllib.parse
import logging
import requests
from astropy.time import TimeDelta
import astropy.units as u

from pyobs.robotic.task import Task
from pyobs.utils.time import Time
from ..scheduler import Scheduler
from .task import LcoTask


log = logging.getLogger(__name__)


class LcoScheduler(Scheduler):
    def __init__(self, url: str, site: str, token: str, telescope: str, camera: str, filters: str,
                 *args, **kwargs):
        Scheduler.__init__(self, *args, **kwargs)

        # store stuff
        self._url = url
        self._site = site
        self.telescope = telescope
        self.camera = camera
        self.filters = filters

        # header
        self._header = {
            'Authorization': 'Token ' + token
        }

        # update thread
        self._update_lock = threading.RLock()
        self._update_thread = None
        self._closing = threading.Event()

        # task list
        self._tasks = {}

    def open(self):
        """Open scheduler."""
        self._update_thread = threading.Thread(target=self._update)
        self._update_thread.start()

    def close(self):
        """Close scheduler."""
        if self._update_thread is not None and self._update_thread.is_alive():
            self._closing.set()
            self._update_thread.join()

    def _update(self):
        """Update thread."""
        while not self._closing.is_set():
            # get url and params
            url = urllib.parse.urljoin(self._url, '/api/observations/')
            now = Time.now()
            params = {
                'site': self._site,
                'end_after': now.isot,
                'start_before': (now + TimeDelta(24 * u.hour)).isot,
                'state': 'PENDING'
            }

            # do request
            r = requests.get(url, params=params, headers=self._header)

            # success?
            if r.status_code == 200:
                # get schedule
                schedules = r.json()['results']

                # update
                with self._update_lock:
                    # create tasks
                    for sched in schedules:
                        # parse start and end
                        sched['start'] = Time(sched['start'])
                        sched['end'] = Time(sched['end'])

                        # does task exist?
                        if sched['request']['id'] not in self._tasks:
                            task = self._create_task(LcoTask, sched,
                                                     telescope=self.telescope, filters=self.filters, camera=self.camera)
                            self._tasks[sched['request']['id']] = task

                    # clean up old tasks
                    to_delete = [k for k, v in self._tasks.items() if v.window()[1] < now]
                    for d in to_delete:
                        del self._tasks[d]

            else:
                log.warning('Could not fetch schedule.')

            # sleep a little
            self._closing.wait(10)

    def get_task(self, time: Time) -> Task:
        """Returns the active task at the given time.

        Args:
            time: Time to return task for.

        Returns:
            Task at the given time.
        """

        # loop all tasks
        with self._update_lock:
            for task in self._tasks.values():
                # get start and end
                start, end = task.window()

                # running now?
                if start <= time < end:
                    return task

        # nothing found
        return None


__all__ = ['LcoScheduler']
