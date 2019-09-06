import io
import os
from urllib.parse import urljoin
import logging
import requests

from .httpfile import HttpFile


log = logging.getLogger(__name__)


class ArchiveFile(HttpFile):
    """Wraps a file in an archive. To be used in combination with pyobs-archive."""

    def __init__(self, name: str, mode: str = 'w', url: str = None, token: str = None, *args, **kwargs):
        """Creates a new archive file.

        Args:
            name: Name of file.
            mode: Open mode (r/w).
            url: Archive url url.
            token: Authorization token.
        """

        # init
        HttpFile.__init__(self, name, mode)

        # only allow write access for now
        if mode != 'w':
            raise ValueError('Only write operations allowed.')

        # store
        self._url = url + ('/' if not url.endswith('/') else '')
        self._headers = {
            'Authorization': 'Token ' + token
        }

    def _upload(self):
        """If in write mode, actually send the file to the archive."""

        # create session
        session = requests.session()

        # do some initial GET request for getting the csrftoken
        session.get(self._url, headers=self._headers)

        # define list of files and url
        files = {os.path.basename(self._filename): self._buffer}
        url = self._url + 'api/frames/create/'

        # post it
        r = session.post(url, data={'csrfmiddlewaretoken': session.cookies['csrftoken']},
                         files=files, headers=self._headers)

        # success, if status code is 200
        if r.status_code != 200:
            raise ValueError('Cannot write file, received status_code %d.' % r.status_code)

        # check json
        json = r.json()
        if 'created' not in json or json['created'] == 0:
            if 'errors' in json:
                raise ValueError('Could not create file in archive: ' + str(json['errors']))
            else:
                raise ValueError('Could not create file in archive.')


__all__ = ['ArchiveFile']
