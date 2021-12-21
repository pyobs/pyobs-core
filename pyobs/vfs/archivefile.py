import os
from typing import Optional
import logging
import aiohttp

from .httpfile import HttpFile


log = logging.getLogger(__name__)


class ArchiveFile(HttpFile):
    """Wraps a file in an archive. To be used in combination with pyobs-archive."""
    __module__ = 'pyobs.vfs'

    def __init__(self, name: str, url: str, mode: str = 'w', token: Optional[str] = None):
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
        self._headers = {'Authorization': 'Token ' + token} if token is not None else {}

    async def _upload(self) -> None:
        """If in write mode, actually send the file to the archive."""

        # open session
        async with aiohttp.ClientSession() as session:
            # do some initial GET request for getting the csrftoken
            async with session.get(self._url, headers=self._headers) as response:
                token = response.cookies['csrftoken']

            # define list of files and url
            url = self._url + 'frames/create/'
            data = aiohttp.FormData()
            data.add_field('csrfmiddlewaretoken', token)
            data.add_field('file', self._buffer, filename=os.path.basename(self.filename))

            # send data and return image ID
            async with session.post(url, auth=self._auth, data=data, timeout=10, headers=self._headers) as response:
                # success, if status code is 200
                if response.status != 200:
                    raise ValueError('Cannot write file, received status_code %d.' % response.status)

                # check json
                json = await response.json()
                if 'created' not in json or json['created'] == 0:
                    if 'errors' in json:
                        raise ValueError('Could not create file in archive: ' + str(json['errors']))
                    else:
                        raise ValueError('Could not create file in archive.')


__all__ = ['ArchiveFile']
