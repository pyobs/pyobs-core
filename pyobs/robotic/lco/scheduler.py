import threading
import urllib.parse
import logging
from typing import Union

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
            # do actual update
            self._update_now()

            # sleep a little
            self._closing.wait(10)

    def _update_now(self):
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

            # create tasks
            tasks = {}
            for sched in schedules:
                # parse start and end
                sched['start'] = Time(sched['start'])
                sched['end'] = Time(sched['end'])

                # create task
                task = self._create_task(LcoTask, sched,
                                         telescope=self.telescope, filters=self.filters, camera=self.camera)
                tasks[sched['request']['id']] = task

            # update
            with self._update_lock:
                self._tasks = tasks

        else:
            log.warning('Could not fetch schedule.')

    def get_task(self, time: Time) -> Union[Task, None]:
        """Returns the active task at the given time.

        Args:
            time: Time to return task for.

        Returns:
            Task at the given time or None.
        """

        # loop all tasks
        with self._update_lock:
            for task in self._tasks.values():
                # get start and end
                start, end = task.window()

                # running now?
                if start <= time < end and not task.is_finished():
                    return task

        # nothing found
        return None

    def run_task(self, task: Task, abort_event: threading.Event):
        """Run a task.

        Args:
            task: Task to run
            abort_event: Abort event

        Returns:
            Success or not
        """

        # run task
        status = task.run(abort_event)

        # force update tasks
        self._update_now()

        # finish
        return True

    def send_update(self, status_id: int, status: dict):
        """Send report to LCO portal

        Args:
            status_id: id of config status
            status: Status dictionary
        """

        log.info('Sending configuration status update to portal...')
        url = urllib.parse.urljoin(self._url, '/api/configurationstatus/%d/' % status_id)
        r = requests.patch(url, json=status, headers=self._header)
        if r.status_code != 200:
            log.error('Could not update configuration status: %s', r.text)


__all__ = ['LcoScheduler']
