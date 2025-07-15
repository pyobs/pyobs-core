from __future__ import annotations
import fnmatch
from abc import ABCMeta, abstractmethod
from typing import Any, AnyStr, List, Generic


class VFSFile(Generic[AnyStr], metaclass=ABCMeta):
    """Base class for all VFS file classes."""

    __module__ = "pyobs.vfs"

    @abstractmethod
    async def close(self) -> None: ...

    @abstractmethod
    async def read(self, n: int = -1) -> AnyStr: ...

    @abstractmethod
    async def write(self, s: AnyStr) -> None: ...

    async def __aenter__(self) -> VFSFile:
        return self

    async def __aexit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        await self.close()

    @staticmethod
    async def listdir(path: str, **kwargs: Any) -> List[str]:
        """Returns content of given path.

        Args:
            path: Path to list.
            kwargs: Parameters for specific file implementation (same as __init__).

        Returns:
            List of files in path.
        """
        raise NotImplementedError()

    @classmethod
    async def find(cls, path: str, pattern: str, **kwargs: Any) -> List[str]:
        """Find files by pattern matching.

        Args:
            path: Path to search in.
            pattern: Pattern to search for.

        Returns:
            List of found files.
        """

        # list files in dir
        files = await cls.listdir(path, **kwargs)

        # filter by pattern
        return list(filter(lambda f: fnmatch.fnmatch(f, pattern), files))

    @staticmethod
    async def remove(path: str, *args: Any, **kwargs: Any) -> bool:
        """Remove file at given path.

        Args:
            path: Path of file to delete.

        Returns:
            Success or not.
        """
        raise NotImplementedError()

    @classmethod
    async def exists(cls, path: str, *args: Any, **kwargs: Any) -> bool:
        """Checks, whether a given path or file exists.

        Args:
            path: Path to check.

        Returns:
            Whether it exists or not
        """
        raise NotImplementedError()


__all__ = ["VFSFile"]
