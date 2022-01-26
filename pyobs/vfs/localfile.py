import asyncio
import fnmatch
import os
from pathlib import PurePosixPath
from typing import Any, Optional, Iterator, BinaryIO, IO, AnyStr, cast, List

from .file import VFSFile


class LocalFile(VFSFile):
    """Wraps a local file with the virtual file system."""

    __module__ = "pyobs.vfs"

    def __init__(self, name: str, mode: str = "r", root: Optional[str] = None, mkdir: bool = True, **kwargs: Any):
        """Open a local file.

        Args:
            name: Name of file.
            mode: Open mode.
            root: Root to prefix name with for absolute path in filesystem.
            mkdir: Whether or not to create non-existing paths automatically.
        """

        # no root given?
        if root is None:
            raise ValueError("No root directory given.")

        # filename is not allowed to start with a / or contain ..
        if name.startswith("/") or ".." in name:
            raise ValueError("Only files within root directory are allowed.")

        # build filename
        self.filename = name
        full_path = os.path.join(root, name)

        # need to create directory?
        path = os.path.dirname(full_path)
        if not os.path.exists(path):
            if mkdir:
                os.makedirs(path)
            else:
                raise ValueError("Cannot write into sub-directory with disabled mkdir option.")

        # file object
        self.fd: IO[Any] = open(full_path, mode)

    async def close(self) -> None:
        if self.fd:
            self.fd.close()

    async def read(self, n: int = -1) -> AnyStr:
        if self.fd is None:
            raise OSError
        return cast(AnyStr, self.fd.read(n))

    async def write(self, s: AnyStr) -> None:
        if self.fd is None:
            raise OSError
        self.fd.write(s)

    @staticmethod
    async def find(path: str, pattern: str, **kwargs: Any) -> List[str]:
        """Find files by pattern matching.

        Args:
            path: Path to search in.
            pattern: Pattern to search for.

        Returns:
            List of found files.
        """

        # get root from kwargs
        if "root" not in kwargs:
            raise ValueError("No root directory given.")
        root = kwargs["root"]

        # build full path
        full_path = os.path.join(root, path)

        # loop directories
        files = []
        for cur, dirnames, filenames in os.walk(full_path):
            for filename in fnmatch.filter(filenames, pattern):
                files += [os.path.relpath(os.path.join(cur, filename), root)]
        return files

    @staticmethod
    async def remove(path: str, *args: Any, **kwargs: Any) -> bool:
        """Remove file at given path.

        Args:
            path: Path of file to delete.

        Returns:
            Success or not.
        """

        # get root from kwargs
        root = kwargs["root"]

        # build full path and remove
        full_path = os.path.join(root, path)
        try:
            os.remove(full_path)
            return True
        except (FileNotFoundError, IsADirectoryError):
            return False

    @classmethod
    async def exists(cls, path: str, root: str = "", *args: Any, **kwargs: Any) -> bool:
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


__all__ = ["LocalFile"]
