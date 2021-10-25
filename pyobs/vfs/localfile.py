import fnmatch
from io import FileIO
import os
from typing import Any, Optional, Iterator

from .vfs import VFSFile


class LocalFile(VFSFile, FileIO):  # type: ignore
    """Wraps a local file with the virtual file system."""
    __module__ = 'pyobs.vfs'

    def __init__(self, name: str, mode: str = 'r', root: Optional[str] = None, mkdir: bool = True, **kwargs: Any):
        """Open a local file.

        Args:
            name: Name of file.
            mode: Open mode.
            root: Root to prefix name with for absolute path in filesystem.
            mkdir: Whether or not to create non-existing paths automatically.
        """

        # no root given?
        if root is None:
            raise ValueError('No root directory given.')

        # filename is not allowed to start with a / or contain ..
        if name.startswith('/') or '..' in name:
            raise ValueError('Only files within root directory are allowed.')

        # build filename
        self.filename = name
        full_path = os.path.join(root, name)

        # need to create directory?
        path = os.path.dirname(full_path)
        if not os.path.exists(path):
            if mkdir:
                os.makedirs(path)
            else:
                raise ValueError('Cannot write into sub-directory with disabled mkdir option.')

        # init FileIO
        FileIO.__init__(self, full_path, mode)

    @staticmethod
    def find(path: str, pattern: str, root: str = '', *args: Any, **kwargs: Any) -> Iterator[str]:
        """Find files by pattern matching.

        Args:
            path: Path to search in.
            pattern: Pattern to search for.
            root: VFS root.

        Returns:
            List of found files.
        """

        # build full path
        full_path = os.path.join(root, path)

        # loop directories
        for cur, dirnames, filenames in os.walk(full_path):
            for filename in fnmatch.filter(filenames, pattern):
                yield os.path.relpath(os.path.join(cur, filename), root)

    @staticmethod
    def exists(path: str, root: str = '', *args: Any, **kwargs: Any) -> bool:
        """Checks, whether a given path or file exists.

        Args:
            path: Path to check.
            root: VFS root.

        Returns:
            Whether it exists or not
        """

        # build full path
        full_path = os.path.join(root, path)

        # check
        return os.path.exists(full_path)


__all__ = ['LocalFile']
