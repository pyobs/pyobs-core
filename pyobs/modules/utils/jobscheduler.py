import logging
import threading
import time

from astroplan import Observer
from astropy.time import TimeDelta
import astropy.units as u

from pyobs.comm import Comm
from pyobs.comm.proxy import Proxy
from pyobs import Module
from pyobs.utils.threads import Future
from pyobs.utils.time import Time


log = logging.getLogger(__name__)


class Job:
    def __init__(self, module: str, method: str, params: dict = None):
        self.id = None
        self.comm = None
        self.observer = None
        self.abort = None
        self.module = module
        self.method = method
        self.params = {} if params is None else params
        self.next_run = None

    def __call__(self):
        # before we start, we schedule next run
        self.next_run = self._schedule_next_run()

        # start job in thread
        threading.Thread(target=self._run_job).start()

    def _run_job(self):
        # log start of job
        log.info('Starting job #%d on %s.%s...', self.id, self.module, self.method)
        start = time.time()
        response = None

        try:
            # get proxy
            proxy: Proxy = self.comm[self.module]

            # call method
            future: Future = proxy.execute(self.method, **self.params)

            # wait for it
            while not future.is_done():
                # abort?
                if self.abort.is_set():
                    log.error('Aborted job #%d on %s.%s after %.2fs.', self.id, self.module, self.method)

                # wait for it
                self.abort.wait(0.1)

            # get response
            response = future.wait()

            # log end of job
            duration = time.time() - start
            log.info('Finished job #%d on %s.%s after %.2fs: %s',
                     self.id, self.module, self.method, duration, str(response))

        except:
            log.exception('Failed job #%d on %s.%s.', self.id, self.module, self.method)

    def _schedule_next_run(self) -> Time:
        raise NotImplementedError


class PeriodicJob(Job):
    def __init__(self, seconds: int = None, minutes: int = None, hours: int = None, days: int = None, *args, **kwargs):
        Job.__init__(self, *args, **kwargs)

        # calculate interval
        self.interval = 0
        self.interval += 0 if seconds is None else seconds
        self.interval += 0 if minutes is None else minutes * 60
        self.interval += 0 if hours is None else hours * 3600
        self.interval += 0 if days is None else days * 86400

        # schedule first run
        self.next_run = Time.now()

    def _schedule_next_run(self) -> Time:
        if self.interval:
            return Time.now() + TimeDelta(self.interval * u.second)


class JobScheduler(Module):
    """Job scheduler."""

    def __init__(self, *args, **kwargs):
        """Initialize a new job scheduler."""
        Module.__init__(self, *args, **kwargs)

        # last job ID
        self.last_id = 0

        # jobs
        self.jobs = []

    def open(self):
        """Open module"""
        Module.open(self)

        self.add_job(PeriodicJob(module='camera', method='get_binning', seconds=10))

    def main(self):
        """Main loop for application."""
        while not self.closing.is_set():
            # loop all jobs
            now = Time.now()
            for job in self.jobs:
                # need to run?
                if job.next_run is not None and now > job.next_run:
                    job()

            # sleep a little
            self.closing.wait(1)

    def add_job(self, job: Job):
        self.last_id += 1
        job.id = self.last_id
        job.comm = self.comm
        job.observer = self.observer
        job.abort = self.closing
        self.jobs.append(job)


__all__ = ['JobScheduler']
