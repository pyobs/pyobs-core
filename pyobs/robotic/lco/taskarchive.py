import threading
from urllib.parse import urljoin
import logging
from typing import Union, List, Dict
import requests
from astroplan import TimeConstraint, AirmassConstraint, ObservingBlock, FixedTarget, MoonSeparationConstraint
from astropy.coordinates import SkyCoord
from astropy.time import TimeDelta
import astropy.units as u
from requests import Timeout

from pyobs.object import get_object
from pyobs.robotic.task import Task
from pyobs.utils.time import Time
from ..taskarchive import TaskArchive
from .task import LcoTask

log = logging.getLogger(__name__)


class LcoTaskArchive(TaskArchive):
    """Scheduler for using the LCO portal"""

    def __init__(self, url: str, site: str, token: str, telescope: str = None, camera: str = None, filters: str = None,
                 roof: str = None, autoguider: str = None, update: bool = True, scripts: dict = None,
                 portal_enclosure: str = None, portal_telescope: str = None, portal_instrument: str = None,
                 portal_instrument_type: str = None, period: int = 24, proxies: List[str] = None,
                 *args, **kwargs):
        """Creates a new LCO scheduler.

        Args:
            url: URL to portal
            site: Site filter for fetching requests
            token: Authorization token for portal
            telescope: Telescope to use
            camera: Camera to use
            filters: Filter wheel to use
            roof: Roof to use
            autoguider: Autoguider to use
            update: Whether to update scheduler in background
            scripts: External scripts
            portal_enclosure: Enclosure for new schedules.
            portal_telescope: Telescope for new schedules.
            portal_instrument: Instrument for new schedules.
            portal_instrument_type: Instrument type to schedule.
            period: Period to schedule in hours
            proxies: Proxies for requests.
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
        self.autoguider = autoguider
        self.instruments = None
        self._update = update
        self._last_schedule_time = None
        self._last_schedule_lock = threading.RLock()
        self.scripts = scripts
        self._proxies = {} if proxies is None else proxies

        # buffers in case of errors
        self._last_scheduled = None
        self._last_changed = None

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

        # get stuff from portal
        self._init_from_portal()

        # start update thread
        if self._update:
            self._update_thread = threading.Thread(target=self._update_schedule)
            self._update_thread.start()

    def close(self):
        """Close scheduler."""
        if self._update_thread is not None and self._update_thread.is_alive():
            self._closing.set()
            self._update_thread.join()

    def _init_from_portal(self):
        """Initialize scheduler from portal."""

        # get instruments
        url = urljoin(self._url, '/api/instruments/')
        res = requests.get(url, headers=self._header, proxies=self._proxies)
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

    def _update_now(self, force: bool = False):
        """Update list of requests.

        Args:
            force: Force update.
        """

        # only want to do this once at a time
        with self._last_schedule_lock:
            # remember now
            now = Time.now()

            # get time of last scheduler run and check, whether we need an update, which is not the case, if
            # - we updated before
            # - AND last update was after last schedule update
            # - AND last update is less then 1 min ago
            # - AND force is set to False
            last_scheduled = self.last_scheduled()
            if self._last_schedule_time is not None and \
                    (last_scheduled is None or self._last_schedule_time >= last_scheduled) and \
                    self._last_schedule_time > now - TimeDelta(1. * u.minute) and \
                    force is False:
                # need no update
                return

            # need update!
            try:
                tasks = self.fetch_tasks(end_after=now, start_before=now + TimeDelta(24 * u.hour), state='PENDING')
            except Timeout:
                log.error('Request timed out')
                self._closing.wait(60)
                return
            except ValueError:
                log.warning('Could not fetch schedule.')
                return

            # any changes?
            if sorted(tasks) != sorted(self._tasks):
                log.info('Task list changed, found %d task(s) to run.', len(tasks))

            # update
            with self._update_lock:
                self._tasks = tasks

            # finished
            self._last_schedule_time = now

    def fetch_tasks(self, end_after: Time, start_before: Time, state: str = 'PENDING') -> Dict[str, Task]:
        """Fetch tasks from portal.

        Args:
            end_after: Task must end after this time.
            start_before: Task must start before this time.
            state: State of tasks.

        Returns:
            Dictionary with tasks.

        Raises:
            Timeout if request timed out.
            ValueError if something goes wrong.
        """

        # get url and params
        url = urljoin(self._url, '/api/observations/')
        params = {
            'site': self._site,
            'end_after': end_after.isot,
            'start_before': start_before.isot,
            'state': state,
            'request_state': state,
            'limit': 1000
        }

        # do request
        r = requests.get(url, params=params, headers=self._header, timeout=10, proxies=self._proxies)

        # success?
        if r.status_code != 200:
            raise ValueError()

        # get schedule
        schedules = r.json()['results']

        # create tasks
        tasks = {}
        for sched in schedules:
            # parse start and end
            sched['start'] = Time(sched['start'])
            sched['end'] = Time(sched['end'])

            # create task
            task = self._create_task(LcoTask, sched, scripts=self.scripts)
            tasks[sched['request']['id']] = task

        # finished
        r.close()
        return tasks

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
        self._update_now(force=True)

        # finish
        return True

    def send_update(self, status_id: int, status: dict):
        """Send report to LCO portal

        Args:
            status_id: id of config status
            status: Status dictionary
        """

        log.info('Sending configuration status update to portal...')
        url = urljoin(self._url, '/api/configurationstatus/%d/' % status_id)

        # do request
        res = None
        try:
            res = requests.patch(url, json=status, headers=self._header, timeout=10, proxies=self._proxies)
            if res.status_code != 200:
                log.error('Could not update configuration status: %s', res.text)
        except Timeout:
            log.error('Request timed out.')
        finally:
            if res is not None:
                res.close()

    def last_changed(self) -> Time:
        """Returns time when last time any blocks changed."""

        # try to update time
        res = None
        try:
            res = requests.get(urljoin(self._url, '/api/last_changed/'), headers=self._header, timeout=10,
                               proxies=self._proxies)
            if res.status_code != 200:
                raise ValueError
            self._last_changed = res.json()['last_change_time']
            return self._last_changed

        except:
            # in case of errors, return last time
            return self._last_changed

        finally:
            if res is not None:
                res.close()

    def last_scheduled(self) -> Time:
        """Returns time of last scheduler run."""

        # try to update time
        res = None
        try:
            res = requests.get(urljoin(self._url, '/api/last_scheduled/'), headers=self._header, timeout=10,
                               proxies=self._proxies)
            if res.status_code != 200:
                raise ValueError
            self._last_scheduled = Time(res.json()['last_schedule_time'])
            return self._last_scheduled

        except:
            # in case of errors, return last time
            return self._last_scheduled

        finally:
            if res is not None:
                res.close()

    def get_schedulable_blocks(self) -> list:
        """Returns list of schedulable blocks.

        Returns:
            List of schedulable blocks
        """

        # get requests
        res = requests.get(urljoin(self._url, '/api/requestgroups/schedulable_requests/'), headers=self._header,
                         proxies=self._proxies)
        if res.status_code != 200:
            raise ValueError('Could not fetch list of schedulable requests.')
        schedulable = res.json()
        res.close()

        # get proposal priorities
        res = requests.get(urljoin(self._url, '/api/proposals/'), headers=self._header, proxies=self._proxies)
        if res.status_code != 200:
            raise ValueError('Could not fetch list of proposals.')
        tac_priorities = {p['id']: p['tac_priority'] for p in res.json()['results']}
        res.close()

        # loop all request groups
        blocks = []
        for group in schedulable:
            # get base priority, which is tac_priority * ipp_value
            proposal = group['proposal']
            if proposal not in tac_priorities:
                log.error('Could not find proposal "%s".', proposal)
                continue
            base_priority = group['ipp_value'] * tac_priorities[proposal]

            # loop all requests in group
            for req in group['requests']:
                # still pending?
                if req['state'] != 'PENDING':
                    continue

                # duration
                duration = req['duration'] * u.second

                # time constraints
                # make them 15s shorter at each end: for whatever reason astroplan's PriorityScheduler doesn't
                # stick exactly to the times...
                time_constraints = [TimeConstraint(Time(wnd['start']) + 15 * u.second,
                                                   Time(wnd['end']) - 15 * u.second) for wnd in req['windows']]

                # loop configs
                for cfg in req['configurations']:
                    # get instrument and check, whether we schedule it
                    instrument = cfg['instrument_type']
                    if instrument.lower() != self._portal_instrument_type.lower():
                        continue

                    # target
                    t = cfg['target']
                    target = SkyCoord(t['ra'] * u.deg, t['dec'] * u.deg, frame=t['type'].lower())

                    # constraints
                    c = cfg['constraints']
                    constraints = [
                        AirmassConstraint(max=c['max_airmass'], boolean_constraint=False),
                        MoonSeparationConstraint(min=c['min_lunar_distance'] * u.deg)
                    ]

                    # priority is base_priority times duration in minutes
                    priority = base_priority * duration.value / 60.

                    # create block
                    block = ObservingBlock(FixedTarget(target, name=req["id"]), duration, priority,
                                           constraints=[*constraints, *time_constraints],
                                           configuration={'request': req})
                    blocks.append(block)

        # return blocks
        return blocks

    def update_schedule(self, blocks: list, start_time: Time):
        """Update the list of scheduled blocks.

        Args:
            blocks: Scheduled blocks.
            start_time: Start time for schedule.
        """

        # create observations
        observations = self._create_observations(blocks)

        # cancel schedule
        self._cancel_schedule(start_time)

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
        res = requests.post(urljoin(self._url, '/api/observations/cancel/'), json=params,
                          headers={'Authorization': 'Token ' + self._token,
                                   'Content-Type': 'application/json; charset=utf8'},
                          proxies=self._proxies)
        res.close()
        if res.status_code != 200:
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
        res = requests.post(urljoin(self._url, '/api/observations/'), json=observations,
                          headers={'Authorization': 'Token ' + self._token,
                                   'Content-Type': 'application/json; charset=utf8'},
                          proxies=self._proxies)
        res.close()
        if res.status_code != 201:
            raise ValueError('Could not submit observations.')


__all__ = ['LcoTaskArchive']
