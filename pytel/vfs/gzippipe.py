import io
import subprocess
import logging
import os
import gzip


log = logging.getLogger(__name__)


class GzipReader(io.RawIOBase):
    def __init__(self, fd, close_fd=True):
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
        return True

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

    def close(self):
        # close fd
        if self._close_fd:
            self._fd.close()


class GzipWriter(io.RawIOBase):
    def __init__(self, fd, close_fd=True):
        io.RawIOBase.__init__(self)

        # init buffer
        self._buffer = b''
        self._fd = fd
        self._close_fd = close_fd

        # does gzip exist?
        self._use_shell = os.path.exists('/bin/gzip')

    def writable(self):
        return True

    def write(self, b):
        self._buffer += b

    def flush(self):
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
        # flush
        self.flush()

        # close fd
        if self._close_fd:
            self._fd.close()

