import io
import subprocess
import logging
import os
import gzip

from .vfs import VFSFile


log = logging.getLogger(__name__)


class GzipReader(VFSFile, io.RawIOBase):
    """A pipe object that takes a file-like object as input and acts itself like a stream,
    decompressing data on the fly."""
    __module__ = 'pyobs.vfs'

    def __init__(self, fd, close_fd=True):
        """Create a new GZIP reader pipe.

        Args:
            fd: File-like object.
            close_fd: Whether or not to close the file afterwards. If False, caller has to close it by itself.
        """
        io.RawIOBase.__init__(self)

        # init
        self._pos = 0
        self._fd = fd
        self._close_fd = close_fd

        # does gzip exist?
        use_shell = os.path.exists('/bin/gzip')

        # read and compress raw stream
        if use_shell:
            p = subprocess.run(['/bin/gzip', '-d'], stdout=subprocess.PIPE, stderr=subprocess.PIPE, input=fd.read())
            if len(p.stderr) > 1:
                raise RuntimeError('Error from gzip: %s', p.stderr)
            self._buffer = p.stdout
        else:
            self._buffer = gzip.decompress(fd.read())

    def readable(self):
        """Stream is readable."""
        return True

    def seekable(self):
        """Stream is seekable."""
        return True

    def seek(self, offset, whence=io.SEEK_SET):
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

    def read(self, size=-1) -> bytearray:
        """Read number of bytes from stream.

        Args:
            size: Number of bytes to read, -1  reads until end of data.

        Returns:
            Data read from stream.
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

    def close(self):
        """Close stream."""
        if self._close_fd:
            # close fd, if requested
            self._fd.close()


class GzipWriter(VFSFile, io.RawIOBase):
    """A pipe object that takes a file-like object as input and acts itself like a stream,
    compressing data on the fly."""

    def __init__(self, fd, close_fd=True):
        """Create a new GZIP writer pipe.

        Args:
            fd: File-like object.
            close_fd: Whether or not to close the file afterwards. If False, caller has to close it by itself.
        """
        io.RawIOBase.__init__(self)

        # init buffer
        self._buffer = b''
        self._fd = fd
        self._close_fd = close_fd

        # does gzip exist?
        self._use_shell = os.path.exists('/bin/gzip')

    def writable(self):
        """Stream is writable."""
        return True

    def write(self, b: bytearray):
        """Write data into the stream.

        Args:
            b: Bytes of data to write.
        """
        self._buffer += b

    def flush(self):
        """Flush the stream."""

        # write compressed data
        if self._use_shell:
            p = subprocess.run(['/bin/gzip'], stdout=subprocess.PIPE, stderr=subprocess.PIPE, input=self._buffer)
            if len(p.stderr) > 1:
                raise RuntimeError('Error from gzip: %s', p.stderr)
            self._fd.write(p.stdout)
        else:
            self._fd.write(gzip.compress(self._buffer))

        # reset buffer
        self._buffer = b''

    def close(self):
        """Close the stream."""

        # flush
        self.flush()

        # close fd
        if self._close_fd:
            self._fd.close()


__all__ = ['GzipReader', 'GzipWriter']
