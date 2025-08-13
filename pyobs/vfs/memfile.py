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
        BufferedFile.__init__(self)

        # store
        self.filename = name
        self.mode = mode
        self._pos = 0
        self._open = True

        # clear cache on write?
        if "w" in self.mode:
            self._clear_buffer(self.filename)

    async def read(self, n: int = -1) -> str | bytes:
        """Read number of bytes from stream.

        Args:
            n: Number of bytes to read, -1  reads until end of data.

        Returns:
            Data read from stream.
        """

        # check size
        if n == -1:
            data = self._buffer(self.filename)
            self._pos = len(data) - 1
        else:
            # extract data to read
            data = self._buffer(self.filename)[self._pos : self._pos + n]
            self._pos += n

        # return data
        return data

    async def write(self, buf: str | bytes) -> None:
        """Write data into the stream.

        Args:
            buf: Bytes of data to write.
        """
        self._append_to_buffer(self.filename, buf)

    async def close(self) -> None:
        """Close stream."""

        # clear buffer
        self._clear_buffer(self.filename)

        # set flag
        self._open = False

    @property
    def closed(self) -> bool:
        """Whether stream is closed."""
        return not self._open


__all__ = ["MemoryFile"]
