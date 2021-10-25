import io
from typing import Optional, Any
from urllib.parse import urljoin
import logging
import requests

from .vfs import VFSFile
from ..utils.http import requests_retry_session

log = logging.getLogger(__name__)


class HttpFile(VFSFile, io.RawIOBase):
    """Wraps a file on a HTTP server that can be accessed via GET/POST.
    Especially useful in combination with :class:`~pyobs.modules.utils.HttpFileCache`."""
    __module__ = 'pyobs.vfs'

    def __init__(self, name: str, mode: str = 'r', download: Optional[str] = None, upload: Optional[str] = None,
                 username: Optional[str] = None, password: Optional[str] = None, verify_tls: bool = False,
                 **kwargs: Any):
        """Creates a new HTTP file.

        Args:
            name: Name of file.
            mode: Open mode (r/w).
            download: Base URL for downloading files. If None, no read access possible.
            upload: Base URL for uploading files. If None, no write access possible.
            username: Username for accessing the HTTP server.
            password: Password for accessing the HTTP server.
            verify_tls: Whether to verify TLS certificates.
        """

        # init
        io.RawIOBase.__init__(self)
        self._verify_tls = verify_tls

        # auth
        self._auth = None
        if username is not None and password is not None:
            self._auth = (username, password)

        # filename is not allowed to start with a / or contain ..
        if name.startswith('/') or '..' in name:
            raise ValueError('Only files within root directory are allowed.')

        # build filename
        self._filename = name
        self._mode = mode
        self._buffer = b''
        self._pos = 0
        self._open = True

        # URLs given?
        self._download_path = download
        self._upload_path = upload
        if self.readable() and self._download_path is None:
            raise ValueError('No download URL given.')
        if self.writable() and self.readable is None:
            raise ValueError('No upload URL given.')

    @property
    def url(self) -> str:
        """Returns URL of file."""
        if self._download_path is None:
            raise ValueError('No download URL given.')
        return urljoin(self._download_path, self._filename)

    def _download(self) -> None:
        """For read access, download the file into a local buffer.

        Raises:
            FileNotFoundError: If file could not be found.
        """

        try:
            # do request
            r = requests_retry_session().get(self.url, stream=True, auth=self._auth, verify=self._verify_tls, timeout=5)

        except requests.exceptions.ConnectionError:
            log.error('Could not connect to filecache.')
            raise FileNotFoundError

        # check response
        if r.status_code == 200:
            # get data and return it
            self._buffer = r.content
        elif r.status_code == 401:
            log.error('Wrong credentials for downloading file.')
            raise FileNotFoundError
        else:
            log.error('Could not download file from filecache.')
            raise FileNotFoundError

    def readable(self) -> bool:
        """File is readable if it was opened in 'r' mode."""
        return 'r' in self._mode

    def read(self, size: int = -1) -> bytes:
        """Read number of bytes from stream.

        Args:
            size: Number of bytes to read. Read until end, if -1.

        Returns:
            Read bytes.
        """

        # load file
        if len(self._buffer) == 0 and self.readable():
            self._download()

        # check size
        if size == -1:
            data = self._buffer
            self._pos = len(self) - 1
        else:
            # extract data to read
            data = self._buffer[self._pos:self._pos + size]
            self._pos += size

        # return data
        return data

    def seekable(self) -> bool:
        """Stream is seekable."""
        return True

    def seek(self, offset: int, whence: int = io.SEEK_SET) -> int:
        """Seek in stream.

        Args:
            offset: Offset to move.
            whence: Origin of move, i.e. beginning, current position, or end of stream.
        """

        # set offset
        if whence == io.SEEK_SET:
            self._pos = offset
        elif whence == io.SEEK_CUR:
            self._pos += offset
        elif whence == io.SEEK_END:
            self._pos = len(self) - 1 + offset

        # limit
        self._pos = max(0, min(len(self) - 1, self._pos))
        return self._pos

    def tell(self) -> int:
        """Give current position on stream."""
        return self._pos

    def __len__(self) -> int:
        """Length of stream buffer."""
        return len(self._buffer)

    def writable(self) -> bool:
        """File is writable if it was opened in 'w' mode."""
        return 'w' in self._mode

    def write(self, b: bytes) -> None:  # type: ignore
        """Write data into the stream.

        Args:
            b: Bytes of data to write.
        """
        self._buffer += b

    def close(self) -> None:
        """Close stream."""

        # write it?
        if self.writable() and self._open:
            self._upload()

        # set flag
        self._open = False

        # close RawIOBase
        io.RawIOBase.close(self)

    def _upload(self) -> None:
        """If in write mode, actually send the file to the HTTP server."""

        # filename given?
        headers = {}
        if self._filename is not None:
            headers['content-disposition'] = 'attachment; filename="%s"' % self._filename

        # check
        if self._upload_path is None:
            raise ValueError('No upload URL given.')

        # send data and return image ID
        try:
            r = requests_retry_session().post(self._upload_path, data=self._buffer, headers=headers, auth=self._auth,
                                              timeout=5)
            if r.status_code == 401:
                log.error('Wrong credentials for uploading file.')
                raise FileNotFoundError
            elif r.status_code != 200:
                log.error('Could not upload file to filecache.')
                raise FileNotFoundError

        except requests.exceptions.ConnectionError:
            log.error('Could not connect to filecache.')
            raise FileNotFoundError

        except Exception:
            log.exception('Something has gone wrong.')
            raise FileNotFoundError

    @property
    def closed(self) -> bool:
        """Whether the stream is closed."""
        return not self._open


__all__ = ['HttpFile']
