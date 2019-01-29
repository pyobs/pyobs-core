import io
import logging
import os
import tarfile

from pytel import Application
from pytel.object import get_object

log = logging.getLogger(__name__)


class TarFile:
    def __init__(self, name=None, mode='rb', source: str = None, *args, **kwargs):
        # get app
        self.app = Application.instance()

        # mode?
        if mode != 'rb':
            raise ValueError('Modes other than rb are not supported.')

        # get list of files to zip
        source = get_object(source)
        self._files = source(name)

        # init stream
        self._out_stream = io.BytesIO()
        self._buffer = b''

        # write to the BytesIO with no compression
        self._tarfile = tarfile.TarFile.open(fileobj=self._out_stream, mode='w')

    def _flush(self):
        """Flush out stream into buffer"""

        # flush out stream
        self._buffer += self._out_stream.getvalue()

        # reset out stream
        self._out_stream.seek(0)
        self._out_stream.truncate(0)

    def _add_file(self, filename):
        """Add file to tarfile.

        Args:
            filename (str): Name of file to add
        """
        with self.app.vfs.open_file(filename, 'rb') as fin:
            # load file into a BytesIO
            with io.BytesIO(fin.read()) as bio:
                # create tar info
                info = tarfile.TarInfo(name=os.path.basename(filename))
                info.size = len(bio.getbuffer())

                # add file
                self._tarfile.addfile(info, fileobj=bio)

    def read(self, size=-1) -> bytes:
        # not enough bytes in the buffer?
        while len(self._files) > 0 and (size == -1 or len(self._buffer) < size):
            # get next file and add it
            filename = self._files.pop()
            self._add_file(filename)

            # flush stream
            self._flush()

        # get data to return
        if size == -1 or size >= len(self._buffer):
            # return everything
            data = self._buffer
            self._buffer = b''

        else:
            # return parts
            data = self._buffer[:size]
            self._buffer = self._buffer[size:]

        # finished
        return data

    def close(self):
        self._tarfile.close()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()


__all__ = ['TarFile']
