import io
import logging
from typing import Any

from .bufferedfile import BufferedFile


log = logging.getLogger(__name__)


class MemoryFile(BufferedFile):
    """A file stored in memory."""

    __module__ = "pyobs.vfs"

    def __init__(self, name: str, mode: str = "r", **kwargs: Any):
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

    async def read(self, n: int = -1) -> str | bytes:
        """Read number of bytes from stream.

        Args:
            n: Number of bytes to read, -1  reads until end of data.

        Returns:
            Data read from stream.
        """

        # check size
        if n == -1:
            data = self._buffer(self._filename)
            self._pos = len(data) - 1
        else:
            # extract data to read
            data = self._buffer(self._filename)[self._pos : self._pos + n]
            self._pos += n

        # return data
        return data

    async def write(self, buf: str | bytes) -> None:
        """Write data into the stream.

        Args:
            buf: Bytes of data to write.
        """
        self._append_to_buffer(self._filename, buf)

    async def close(self) -> None:
        """Close stream."""

        # set flag
        self._open = False

    @property
    def closed(self) -> bool:
        """Whether stream is closed."""
        return not self._open


__all__ = ["MemoryFile"]
