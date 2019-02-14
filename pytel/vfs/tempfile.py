import os
from io import FileIO
from tempfile import NamedTemporaryFile
import logging

from .vfs import VFSFile


log = logging.getLogger(__name__)


class TempFile(VFSFile, FileIO):
    """A temporary file."""

    def __init__(self, name: str = None, mode: str = 'r', prefix: str = None, suffix: str = None,
                 root: str = '/tmp/pytel/', mkdir: bool = True, *args, **kwargs):
        """Open/create a temp file.

        Args:
            name: Name of file.
            mode: Open mode.
            prefix: Prefix for automatic filename creation in write mode.
            suffix: Suffix for automatic filename creation in write mode.
            root: Temp directory.
            mkdir: Whether to automatically create directories.
        """
        # no root given?
        if root is None:
            raise ValueError('No root directory given.')

        # create root?
        if not os.path.exists(root):
            os.makedirs(root)

        # no filename?
        if name is None:
            # cannot read from non-existing filename
            if 'r' in mode:
                raise ValueError('No filename given to read from.')

            # create new temp file name
            with NamedTemporaryFile(mode=mode, prefix=prefix, suffix=suffix, dir=root) as tmp:
                name = os.path.basename(tmp.name)

        # filename is not allowed to start with a / or contain ..
        if name.startswith('/') or '..' in name:
            raise ValueError('Only files within root directory are allowed.')

        # build filename
        self.filename = name
        full_name = os.path.join(root, name)

        # need to create directory?
        path = os.path.dirname(full_name)
        if not os.path.exists(path):
            if mkdir:
                os.makedirs(path)
            else:
                raise ValueError('Cannot write into sub-directory with disabled mkdir option.')

        # init FileIO
        FileIO.__init__(self, full_name, mode)

    def close(self):
        """Close file."""

        # close file
        FileIO.close(self)

        # remove file
        if 'w' in self.mode:
            os.remove(self.name)
