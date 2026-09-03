import asyncio
import fnmatch
import os
from pathlib import PurePosixPath
from typing import IO, Any

from .file import VFSFile


def _open_sync(full_path: str, mode: str, mkdir: bool) -> IO[Any]:
    """Open a local file, creating parent directories first if needed.

    Runs on an executor thread off the event loop. Raises ``ValueError`` when ``mkdir`` is
    disabled and the parent directory does not exist.
    """
    path = os.path.dirname(full_path)
    if not os.path.exists(path):
        if mkdir:
            # exist_ok: this runs on an executor thread, so concurrent opens into the same new
            # sibling directory can race between the exists() check and makedirs() here.
            os.makedirs(path, exist_ok=True)
        else:
            raise ValueError("Cannot write into sub-directory with disabled mkdir option.")
    return open(full_path, mode)


def _find_sync(full_path: str, pattern: str) -> list[str]:
    """Walk ``full_path`` and return the paths of files matching ``pattern``, relative to it."""
    files = []
    for cur, dirnames, filenames in os.walk(full_path):
        for filename in fnmatch.filter(filenames, pattern):
            files += [os.path.relpath(os.path.join(cur, filename), full_path)]
    return files


def _remove_sync(full_path: str) -> bool:
    """Remove the file at ``full_path``; return False if it does not exist or is a directory."""
    try:
        os.remove(full_path)
        return True
    except (FileNotFoundError, IsADirectoryError):
        return False


def _rmdir_sync(full_path: str) -> bool:
    """Remove the directory at ``full_path`` if it exists and is empty; return False otherwise
    (including if it's not a directory at all) rather than raising."""
    try:
        os.rmdir(full_path)
        return True
    except OSError:
        # covers: doesn't exist, not a directory, or not empty (errno differs by platform)
        return False


class LocalFile(VFSFile):
    """Wraps a local file with the virtual file system.

    All potentially blocking I/O (open/read/write/close/remove/find/exists) runs on the default
    executor, keeping the event loop responsive even on slow (e.g. network-mounted) paths.
    """

    __module__ = "pyobs.vfs"

    def __init__(self, name: str, mode: str = "r", root: str | None = None, mkdir: bool = True, **kwargs: Any):
        """Create a new local file.

        Only validates the path here; the file itself is opened in ``__aenter__`` off the event
        loop, so construction stays cheap and never blocks.

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
        self._full_path = os.path.join(root, name)
        self._mode = mode
        self._mkdir = mkdir
        self.fd: IO[Any] | None = None

    async def __aenter__(self) -> "LocalFile":
        """Open the file on an executor thread, keeping the event loop responsive."""
        loop = asyncio.get_running_loop()
        self.fd = await loop.run_in_executor(None, _open_sync, self._full_path, self._mode, self._mkdir)
        return self

    async def close(self) -> None:
        if self.fd:
            loop = asyncio.get_running_loop()
            await loop.run_in_executor(None, self.fd.close)

    async def read(self, n: int = -1) -> str | bytes:
        if self.fd is None:
            raise OSError("LocalFile is not open; use 'async with' to open it before reading.")
        loop = asyncio.get_running_loop()
        buf = await loop.run_in_executor(None, self.fd.read, n)
        if not isinstance(buf, str) and not isinstance(buf, bytes):
            raise OSError
        return buf

    async def write(self, s: str | bytes) -> None:
        if self.fd is None:
            raise OSError("LocalFile is not open; use 'async with' to open it before writing.")
        loop = asyncio.get_running_loop()
        await loop.run_in_executor(None, self.fd.write, s)

    @staticmethod
    async def local_path(path: str, **kwargs: Any) -> str:
        """Returns local path of given path.

        Args:
            path: Path to list.
            kwargs: Parameters for specific file implementation (same as __init__).

        Returns:
            Local path.
        """

        # get settings
        root = kwargs["root"]

        # return path
        return os.path.join(root, path)

    @staticmethod
    async def listdir(path: str, **kwargs: Any) -> list[str]:
        """Returns content of given path.

        Args:
            path: Path to list.
            kwargs: Parameters for specific file implementation (same as __init__).

        Returns:
            List of files in path.
        """

        # get settings
        root = kwargs["root"]

        # get path and return list
        full_path = PurePosixPath(root) / path
        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(None, os.listdir, str(full_path))

    @staticmethod
    async def find(path: str, pattern: str, **kwargs: Any) -> list[str]:
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

        # walk directories off the event loop
        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(None, _find_sync, full_path, pattern)

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

        # build full path and remove off the event loop
        full_path = os.path.join(root, path)
        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(None, _remove_sync, full_path)

    @staticmethod
    async def rmdir(path: str, *args: Any, **kwargs: Any) -> bool:
        """Remove the directory at given path, if it's empty.

        Args:
            path: Path of directory to remove.

        Returns:
            Success or not (including if the directory doesn't exist, isn't a directory, or
            isn't empty -- none of those raise, they just return False).
        """

        # get root from kwargs
        root = kwargs["root"]

        # build full path and remove off the event loop
        full_path = os.path.join(root, path)
        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(None, _rmdir_sync, full_path)

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

        # check off the event loop
        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(None, os.path.exists, full_path)


__all__ = ["LocalFile"]
