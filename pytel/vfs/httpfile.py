import io
from urllib.parse import urljoin
import logging
import requests


log = logging.getLogger(__name__)


class HttpFile(io.RawIOBase):
    def __init__(self, name, mode='r', download: str = None, upload: str = None, *args, **kwargs):
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
        return 'r' in self._mode

    def read(self, size=-1):
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
        return True

    def seek(self, offset, whence=io.SEEK_SET):
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
        return self._pos

    def __len__(self):
        return len(self._buffer)

    def writable(self):
        return 'w' in self._mode

    def write(self, b):
        self._buffer += b

    def close(self):
        # write it?
        if self.writable() and self._open:
            self._upload()

        # set flag
        self._open = False

        # close RawIOBase
        io.RawIOBase.close(self)

    def _upload(self):
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
        return not self._open


__all__ = ['HttpFile']
