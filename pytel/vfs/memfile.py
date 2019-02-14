import io
import logging


log = logging.getLogger(__name__)


class MemoryFile(io.RawIOBase):
    """A file stored in memory."""

    """Global buffer."""
    _buffer = {}

    def __init__(self, name: str, mode: str = 'r', *args, **kwargs):
        """Open/create a file in memory.

        Args:
            name: Name of file.
            mode: Open mode.
        """

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
        """Stream is readable if it was opened in 'r' mode."""
        return 'r' in self._mode

    def read(self, size=-1):
        """Read number of bytes from stream.

        Args:
            size: Number of bytes to read, -1  reads until end of data.

        Returns:
            Data read from stream.
        """

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
        """Length of buffer."""
        return len(MemoryFile._buffer[self._filename])

    def writable(self):
        """Stream is readable if it was opened in 'w' mode."""
        return 'w' in self._mode

    def write(self, b):
        """Write data into the stream.

        Args:
            b: Bytes of data to write.
        """
        MemoryFile._buffer[self._filename] += b

    def close(self):
        """Close stream."""

        # set flag
        self._open = False

        # close RawIOBase
        io.RawIOBase.close(self)

    @property
    def closed(self):
        """Whether stream is closed."""
        return not self._open


__all__ = ['MemoryFile']
