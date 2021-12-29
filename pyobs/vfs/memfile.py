import io
import logging
from typing import Dict, Any, AnyStr

from .file import VFSFile


log = logging.getLogger(__name__)


class MemoryFile(VFSFile):
    """A file stored in memory."""
    __module__ = 'pyobs.vfs'

    """Global buffer."""
    _buffer: Dict[str, AnyStr] = {}

    def __init__(self, name: str, mode: str = 'r', **kwargs: Any):
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
            MemoryFile._buffer[name] = b'' if 'b' in mode else ''

    async def read(self, n: int = -1) -> AnyStr:
        """Read number of bytes from stream.

        Args:
            n: Number of bytes to read, -1  reads until end of data.

        Returns:
            Data read from stream.
        """

        # check size
        if n == -1:
            data = MemoryFile._buffer[self._filename]
            self._pos = len(data) - 1
        else:
            # extract data to read
            data = MemoryFile._buffer[self._filename][self._pos:self._pos + n]
            self._pos += n

        # return data
        return data

    async def write(self, s: AnyStr) -> None:
        """Write data into the stream.

        Args:
            s: Bytes of data to write.
        """
        MemoryFile._buffer[self._filename] += s

    async def close(self) -> None:
        """Close stream."""

        # set flag
        self._open = False

    @property
    def closed(self) -> bool:
        """Whether stream is closed."""
        return not self._open


__all__ = ['MemoryFile']
