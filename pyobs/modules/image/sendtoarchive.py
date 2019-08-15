import glob
import logging
import os
from queue import Queue
import pyinotify
import requests

from pyobs import PyObsModule, get_object


log = logging.getLogger(__name__)


class ArchiveClient:
    def __call__(self, filename: str) -> bool:
        raise NotImplementedError


class PyObsArchiveClient(ArchiveClient):
    def __init__(self, url: str, token: str, *args, **kwargs):
        # store url
        self._url = url
        if not self._url.endswith('/'):
            self._url += '/'

        # http stuff
        self._headers = {
            'Authorization': 'Token ' + token
        }
        self._session = requests.session()

        # do some initial GET request for getting the csrftoken
        self._session.get(self._url, headers=self._headers)

    def __call__(self, filename: str) -> bool:
        # define list of files and url
        files = {'image': open(filename, 'rb')}
        url = self._url +  'frames/create/'

        # post it
        r = self._session.post(url,
                               data={'csrfmiddlewaretoken': self._session.cookies['csrftoken']},
                               files=files, headers=self._headers)

        # success, if status code is 200
        if r.status_code == 200:
            return True
        else:
            log.error('Received status code %d.', r.status_code)
            return False


class SendToArchive(PyObsModule):
    """Watch for new images and add them to one or more archives."""

    def __init__(self, watchpath: str = None, archives: dict = None, *args, **kwargs):
        """Create a new image watcher.

        Args:
            watchpath: Path to watch.
            archives: Config for a client to the archive.
        """
        PyObsModule.__init__(self, *args, **kwargs)

        # add thread func
        self._add_thread_func(self._worker, True)

        # variables
        self._watchpath = watchpath
        self._notifier = None
        self._queue = Queue()

        # create archives
        if not archives:
            raise ValueError('No archives given.')
        self._archives = {name: get_object(a, ArchiveClient) for name, a in archives.items()}

    def open(self):
        """Open module."""
        PyObsModule.open(self)

        # start watching directory
        if self._watchpath:
            log.info('Start watching directory %s for changes...', self._watchpath)
            wm = pyinotify.WatchManager()
            wm.add_watch(self._watchpath, pyinotify.IN_CLOSE_WRITE)
            self._notifier = pyinotify.ThreadedNotifier(wm, default_proc_fun=EventHandler(self)) #, name='observer')
            self._notifier.start()

    def close(self):
        """Close image watcher."""
        PyObsModule.close(self)

        # stop watching
        if self._notifier:
            log.info('Stop watching directory...')
            self._notifier.stop()

    def add_image(self, filename: str):
        """Add an image to the image database.

        Args:
            filename (str): Local filename of new image.
        """

        # log file
        log.info('Adding new image %s...', filename)
        self._queue.put(filename)

    def _clear_queue(self):
        """Clear the queue with new files."""

        # clear queue
        with self._queue.mutex:
            self._queue.queue.clear()

    def _worker(self):
        """Worker thread."""

        # first, add all files from directory to queue
        self._clear_queue()
        for filename in sorted(glob.glob(os.path.join(self._watchpath, '*'))):
            self.add_image(filename)

        # run forever
        while not self.closing.is_set():
            # get next filename
            if self._queue.empty():
                self.closing.wait(1)
                continue
            filename = self._queue.get()
            log.info('Working on file %s...', filename)

            # better safe than sorry
            try:
                # loop archive and upload
                success = True
                for name, archive in self._archives.items():
                    log.info('Sending file to archive %s...', name)
                    if not archive(filename):
                        log.error('Could not upload image, skipping for now...')
                        success = False
                        break

                # no success_
                if not success:
                    continue

                # close and delete files
                log.info('Removing file from watch directory...')
                os.remove(filename)

            except:
                log.exception('Something went wrong.')


class EventHandler(pyinotify.ProcessEvent):
    """Event handler for file watcher."""

    def __init__(self, main, *args, **kwargs):
        """Create event handler."""
        pyinotify.ProcessEvent.__init__(self, *args, **kwargs)
        self.main = main

    def process_IN_CLOSE_WRITE(self, event):
        """React to IN_CLOSE_WRITE events."""
        self.main.add_image(event.pathname)


__all__ = ['SendToArchive']
