import io
import logging


log = logging.getLogger(__name__)


class MemoryFile(io.RawIOBase):

    """Global buffer."""
    _buffer = {}

    def __init__(self, name, mode='r', *args, **kwargs):
        # init
        io.RawIOBase.__init__(self)

        # store
        self._filename = name
        self._mode = mode
        self._pos = 0
        self._open = True

        # overwrite?
        if 'w' in mode:
            MemoryFile._buffer[name] = b''

    def readable(self):
        return 'r' in self._mode

    def read(self, size=-1):
        # check size
        if size == -1:
            data = MemoryFile._buffer[self._filename]
            self._pos = len(self) - 1
        else:
            # extract data to read
            data = MemoryFile._buffer[self._filename][self._pos:self._pos + size]
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
        return len(MemoryFile._buffer[self._filename])

    def writable(self):
        return 'w' in self._mode

    def write(self, b):
        MemoryFile._buffer[self._filename] += b

    def close(self):
        # set flag
        self._open = False

        # close RawIOBase
        io.RawIOBase.close(self)

    @property
    def closed(self):
        return not self._open


__all__ = ['MemoryFile']
