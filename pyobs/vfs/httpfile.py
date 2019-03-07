import io
from urllib.parse import urljoin
import logging
import requests

from .vfs import VFSFile


log = logging.getLogger(__name__)


class HttpFile(VFSFile, io.RawIOBase):
    """Wraps a file on a HTTP server that can be accessed via GET/POST.
    Especially useful in combination with :class:`pyobs.modules.filecache,http.HttpFileCacheServer`."""

    def __init__(self, name: str, mode: str = 'r', download: str = None, upload: str = None, *args, **kwargs):
        """Creates a new HTTP file.

        Args:
            name: Name of file.
            mode: Open mode (r/w).
            download: Base URL for downloading files. If None, no read access possible.
            upload: Base URL for uploading files. If None, no write access possible.
        """

        # init
        io.RawIOBase.__init__(self)

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

        # load file
        if self.readable():
            self._download()

    def _download(self):
        """For read access, download the file into a local buffer.

        Raises:
            FileNotFoundError: If file could not be found.
        """

        try:
            # define URL
            url = urljoin(self._download_path, self._filename)

            # do request
            r = requests.get(url, stream=True)

        except requests.exceptions.ConnectionError:
            log.error('Could not connect to filecache.')
            raise FileNotFoundError

        # check response
        if r.status_code == 200:
            # get data and return it
            self._buffer = r.content
        else:
            log.error('Could not download file from filecache.')
            raise FileNotFoundError

    def readable(self):
        """File is readable if it was opened in 'r' mode."""
        return 'r' in self._mode

    def read(self, size: int = -1):
        """Read number of bytes from stream.

        Args:
            size: Number of bytes to read. Read until end, if -1.

        Returns:
            Read bytes.
        """

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

    def seekable(self):
        """Stream is seekable."""
        return True

    def seek(self, offset: int, whence=io.SEEK_SET):
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

    def tell(self):
        """Give current position on stream."""
        return self._pos

    def __len__(self):
        """Length of stream buffer."""
        return len(self._buffer)

    def writable(self):
        """File is writable if it was opened in 'w' mode."""
        return 'w' in self._mode

    def write(self, b: bytearray):
        """Write data into the stream.

        Args:
            b: Bytes of data to write.
        """
        self._buffer += b

    def close(self):
        """Close stream."""

        # write it?
        if self.writable() and self._open:
            self._upload()

        # set flag
        self._open = False

        # close RawIOBase
        io.RawIOBase.close(self)

    def _upload(self):
        """If in write mode, actually send the file to the HTTP server."""

        # filename given?
        headers = {}
        if self._filename is not None:
            headers['content-disposition'] = 'attachment; filename="%s"' % self._filename

        # send data and return image ID
        try:
            r = requests.post(self._upload_path, data=self._buffer, headers=headers)
            if r.status_code != 200:
                log.error('Could not upload file to filecache.')
                raise FileNotFoundError

        except requests.exceptions.ConnectionError:
            log.error('Could not connect to filecache.')
            raise FileNotFoundError

        except Exception:
            log.exception('Something has gone wrong.')
            raise FileNotFoundError

    @property
    def closed(self):
        """Whether the stream is closed."""
        return not self._open


__all__ = ['HttpFile']
