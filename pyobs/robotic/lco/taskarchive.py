import threading
import urllib.parse
import logging
from typing import Union
import requests
from astroplan import TimeConstraint, AirmassConstraint, ObservingBlock, FixedTarget
from astropy.coordinates import SkyCoord
from astropy.time import TimeDelta
import astropy.units as u

from pyobs.object import get_object
from pyobs.robotic.task import Task
from pyobs.utils.time import Time
from ..taskarchive import TaskArchive
from .task import LcoTask


log = logging.getLogger(__name__)


class LcoTaskArchive(TaskArchive):
    """Scheduler for using the LCO portal"""

    def __init__(self, url: str, site: str, token: str, telescope: str = None, camera: str = None, filters: str = None,
                 roof: str = None, update: bool = True, scripts: dict = None, portal_enclosure: str = None,
                 portal_telescope: str = None, portal_instrument: str = None, portal_instrument_type: str = None,
                 period: int = 24, *args, **kwargs):
        """Creates a new LCO scheduler.

        Args:
            url: URL to portal
            site: Site filter for fetching requests
            token: Authorization token for portal
            telescope: Telescope to use
            camera: Camera to use
            filters: Filter wheel to use
            roof: Roof to use
            update: Whether to update scheduler in background
            scripts: External scripts
            portal_enclosure: Enclosure for new schedules.
            portal_telescope: Telescope for new schedules.
            portal_instrument: Instrument for new schedules.
            portal_instrument_type: Instrument type to schedule.
            period: Period to schedule in hours
        """
        TaskArchive.__init__(self, *args, **kwargs)

        # store stuff
        self._url = url
        self._site = site
        self._portal_enclosure = portal_enclosure
        self._portal_telescope = portal_telescope
        self._portal_instrument = portal_instrument
        self._portal_instrument_type = portal_instrument_type
        self._period = TimeDelta(period * u.hour)
        self.telescope = telescope
        self.camera = camera
        self.filters = filters
        self.roof = roof
        self.instruments = None
        self._update = update

        # create script handlers
        if scripts is None:
            scripts = {}
        self.scripts = {k: get_object(v, comm=self.comm, observer=self.observer) for k, v in scripts.items()}

        # header
        self._token = token
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

        # start update thread
        if self._update:
            self._update_thread = threading.Thread(target=self._update_schedule)
            self._update_thread.start()

        # get stuff from portal
        self._init_from_portal()

    def close(self):
        """Close scheduler."""
        if self._update_thread is not None and self._update_thread.is_alive():
            self._closing.set()
            self._update_thread.join()

    def _init_from_portal(self):
        """Initialize scheduler from portal."""

        # get instruments
        url = urllib.parse.urljoin(self._url, '/api/instruments/')
        res = requests.get(url, headers=self._header)
        if res.status_code != 200:
            raise RuntimeError('Invalid response from portal.')

        # store instruments
        self.instruments = {k.lower(): v for k, v in res.json().items()}

    def _update_schedule(self):
        """Update thread."""
        while not self._closing.is_set():
            # do actual update
            try:
                self._update_now()
            except:
                log.exception('An exception occurred.')

            # sleep a little
            self._closing.wait(10)

    def _update_now(self):
        """Update list of requests."""

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
                                         telescope=self.telescope, filters=self.filters, camera=self.camera,
                                         roof=self.roof, scripts=self.scripts)
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
        task.run(abort_event)

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

    def last_changed(self) -> Time:
        """Returns time when last time any blocks changed."""
        r = requests.get(self._url + '/api/last_changed/', headers=self._header)
        if r.status_code != 200:
            raise ValueError('Could not fetch list of schedulable requests.')
        return r.json()['last_change_time']

    def get_schedulable_blocks(self) -> list:
        """Returns list of schedulable blocks.

        Returns:
            List of schedulable blocks
        """

        # get requests
        r = requests.get(self._url + '/api/requestgroups/schedulable_requests/', headers=self._header)
        if r.status_code != 200:
            raise ValueError('Could not fetch list of schedulable requests.')
        schedulable = r.json()

        # loop all request groups
        blocks = []
        for group in schedulable:
            # loop all requests in group
            for req in group['requests']:

                # duration
                duration = req['duration'] * u.second

                # time constraints
                time_constraints = [TimeConstraint(Time(wnd['start']), Time(wnd['end'])) for wnd in req['windows']]

                # loop configs
                for cfg in req['configurations']:
                    # get instrument and check, whether we schedule it
                    instrument = cfg['instrument_type']
                    if instrument.lower() != self._portal_instrument_type.lower():
                        continue

                    # target
                    t = cfg['target']
                    target = SkyCoord(t['ra'] * u.deg, t['dec'] * u.deg, frame=t['type'].lower())

                    # priority
                    priority = cfg['priority']

                    # constraints
                    c = cfg['constraints']
                    constraints = [AirmassConstraint(max=c['max_airmass'])]

                    # create block
                    block = ObservingBlock(FixedTarget(target, name=req["id"]), duration, priority,
                                           constraints=[*constraints, *time_constraints],
                                           configuration={'request': req})
                    blocks.append(block)

        # return blocks
        return blocks

    def update_schedule(self, blocks: list):
        """Update the list of scheduled blocks.

        Args:
            blocks: Scheduled blocks.
        """

        # create observations
        observations = self._create_observations(blocks)

        # cancel schedule
        self._cancel_schedule(Time.now())

        # send new schedule
        self._submit_observations(observations)

    def _cancel_schedule(self, now: Time):
        """Cancel future schedule."""

        # define parameters
        params = {
            'site': self._site,
            'enclosure': self._portal_enclosure,
            'telescope': self._portal_telescope,
            'start': now.isot,
            'end': (now + self._period).isot
        }

        # cancel schedule
        r = requests.post(self._url + '/api/observations/cancel/', json=params,
                          headers={'Authorization': 'Token ' + self._token,
                                   'Content-Type': 'application/json; charset=utf8'})
        if r.status_code != 200:
            raise ValueError('Could not cancel schedule.')

    def _create_observations(self, blocks: list) -> list:
        """Create observations from schedule.

        Args:
            blocks: List of scheduled blocks

        Returns:
            List with observations.
        """

        # loop blocks
        observations = []
        for block in blocks:
            # get request
            request = block.configuration['request']

            # add observation
            observations.append({
                'site': self._site,
                'enclosure': self._portal_enclosure,
                'telescope': self._portal_telescope,
                'start': block.start_time.isot,
                'end': block.end_time.isot,
                'request': request['id'],
                'configuration_statuses': [{
                    'configuration': request['configurations'][0]['id'],
                    'instrument_name': self._portal_instrument,
                    'guide_camera_name': self._portal_instrument
                }]
            })

        # return list
        return observations

    def _submit_observations(self, observations: list):
        """Submit observations.

        Args:
            observations: List of observations to submit.
        """

        # nothing?
        if len(observations) == 0:
            return

        # submit obervations
        r = requests.post(self._url + '/api/observations/', json=observations,
                          headers={'Authorization': 'Token ' + self._token,
                                   'Content-Type': 'application/json; charset=utf8'})
        if r.status_code != 201:
            raise ValueError('Could not submit observations.')


__all__ = ['LcoTaskArchive']
