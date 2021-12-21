import os
from tempfile import NamedTemporaryFile
import logging
from typing import Optional, Any, AnyStr, cast

from .localfile import VFSFile


log = logging.getLogger(__name__)


class TempFile(VFSFile):
    """A temporary file."""
    __module__ = 'pyobs.vfs'

    def __init__(self, name: Optional[str] = None, mode: str = 'r', prefix: Optional[str] = None,
                 suffix: Optional[str] = None, root: str = '/tmp/pyobs/', mkdir: bool = True, **kwargs: Any):
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
        self.full_name = os.path.join(root, name)

        # need to create directory?
        path = os.path.dirname(self.full_name)
        if not os.path.exists(path):
            if mkdir:
                os.makedirs(path)
            else:
                raise ValueError('Cannot write into sub-directory with disabled mkdir option.')

        # init fd
        self.mode = mode
        self.fd = open(self.full_name, mode)

    async def close(self) -> None:
        """Close file."""

        # close file
        if self.fd:
            self.fd.close()

        # remove file
        if 'w' in self.mode:
            os.remove(self.full_name)

    async def read(self, n: int = -1) -> AnyStr:
        if self.fd is None:
            raise OSError
        return cast(AnyStr, self.fd.read(n))

    async def write(self, s: AnyStr) -> None:
        if self.fd is None:
            raise OSError
        self.fd.write(s)


__all__ = ['TempFile']
