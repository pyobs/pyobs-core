import threading
import urllib.parse
import logging
from typing import Union
import requests
from astroplan import TimeConstraint, AirmassConstraint, ObservingBlock, FixedTarget, AtNightConstraint, Transitioner, \
    SequentialScheduler, Schedule
from astropy.coordinates import SkyCoord
from astropy.table import Table
from astropy.time import TimeDelta
import astropy.units as u

from pyobs.object import get_object
from pyobs.robotic.task import BaseTask
from pyobs.utils.time import Time
from ..scheduler import BaseScheduler
from .task import LcoTask


log = logging.getLogger(__name__)


class LcoScheduler(BaseScheduler):
    """Scheduler for using the LCO portal"""

    def __init__(self, url: str, site: str, token: str, telescope: str, camera: str, filters: str, roof: str,
                 scripts: dict = None, portal_enclosure: str = None, portal_telescope: str = None,
                 portal_instrument: str = None, period: int = 24, *args, **kwargs):
        """Creates a new LCO scheduler.

        Args:
            url: URL to portal
            site: Site filter for fetching requests
            token: Authorization token for portal
            telescope: Telescope to use
            camera: Camera to use
            filters: Filter wheel to use
            roof: Roof to use
            scripts: External scripts
            portal_enclosure: Enclosure for new schedules.
            portal_telescope: Telescope for new schedules.
            portal_instrument: Instrument for new schedules.
            period: Period to schedule in hours
        """
        BaseScheduler.__init__(self, *args, **kwargs)

        # store stuff
        self._url = url
        self._site = site
        self._portal_enclosure = portal_enclosure
        self._portal_telescope = portal_telescope
        self._portal_instrument = portal_instrument
        self._period = TimeDelta(period * u.hour)
        self.telescope = telescope
        self.camera = camera
        self.filters = filters
        self.roof = roof
        self.instruments = None

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
        self._update_thread = threading.Thread(target=self._update)
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
        # get url and params

        # get url
        url = urllib.parse.urljoin(self._url, '/api/instruments/')

        # do request
        res = requests.get(url, headers=self._header)
        if res.status_code != 200:
            raise RuntimeError('Invalid response from portal.')

        # store instruments
        self.instruments = {k.lower(): v for k, v in res.json().items()}

    def _update(self):
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

    def get_task(self, time: Time) -> Union[BaseTask, None]:
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

    def run_task(self, task: BaseTask, abort_event: threading.Event):
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

    def __call__(self):
        """Calculate new schedule."""

        # need some info
        if self._portal_enclosure is None or self._portal_telescope is None or self._portal_instrument is None:
            log.error('No enclosure, telescope, or instrument given.')
            return

        # get now
        now = Time.now()

        # get schedulable requests
        schedulable = self._get_requests()

        # get all observation blocks
        blocks, all_requests = self._get_blocks(schedulable)

        # schedule
        schedule = self._schedule(blocks)
        # print(schedule)

        # create observations
        observations = self._create_observations(schedule, all_requests)

        # cancel schedule
        self._cancel_schedule(now)

        # submit observations
        self._submit_observations(observations)

    def _get_requests(self):
        """Get requests from observe page"""

        # get requests
        r = requests.get(self._url + '/api/requestgroups/schedulable_requests/', headers=self._header)
        if r.status_code != 200:
            raise ValueError('Could not fetch list of schedulable requests.')
        return r.json()

    def _get_blocks(self, schedulable: list) -> (list, dict):
        """Get all blocks from a list of schedulable requests

        Args:
            schedulable: List of schedulable requests.

        Returns:
            Lists of blocks and dict with all requests by ID.
        """

        # loop all request groups
        blocks = []
        all_requests = {}
        for group in schedulable:
            # loop all requests in group
            for req in group['requests']:
                # store request
                all_requests[req['id']] = req

                # duration
                duration = req['duration'] * u.second

                # time constraints
                time_constraints = [TimeConstraint(Time(wnd['start']), Time(wnd['end'])) for wnd in req['windows']]

                # loop configs
                for cfg in req['configurations']:
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
                                           constraints=[*constraints, *time_constraints])
                    blocks.append(block)

        # return it
        return blocks, all_requests

    def _schedule(self, blocks: list) -> Table:
        # only constraint is the night
        constraints = [AtNightConstraint.twilight_civil()]

        # we don't need any transitions
        transitioner = Transitioner()

        # init scheduler and schedule
        scheduler = SequentialScheduler(constraints, self.observer, transitioner=transitioner)
        schedule = Schedule(Time.now(), Time.now() + TimeDelta(1 * u.day))
        scheduler(blocks, schedule)

        # return table
        return schedule.to_table()

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
        r = requests.post(self._url + '/observations/cancel/', json=params,
                          headers={'Authorization': 'Token ' + self._token,
                                   'Content-Type': 'application/json; charset=utf8'})
        if r.status_code != 200:
            raise ValueError('Could not cancel schedule.')

    def _create_observations(self, schedule: Table, all_requests: dict) -> list:
        """Create observations from schedule.

        Args:
            schedule: Schedule to use.
            all_requests: Dict with all requests.

        Returns:
            List with observations.
        """

        # loop results
        observations = []
        for row in schedule:
            # find request
            request = all_requests[row['target']]

            # add observation
            observations.append({
                'site': self._site,
                'enclosure': self._portal_enclosure,
                'telescope': self._portal_telescope,
                'start': row['start time (UTC)'],
                'end': row['end time (UTC)'],
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
        r = requests.post(self._url + '/observations/', json=observations,
                          headers={'Authorization': 'Token ' + self._token,
                                   'Content-Type': 'application/json; charset=utf8'})
        if r.status_code != 201:
            raise ValueError('Could not submit observations.')


__all__ = ['LcoScheduler']
