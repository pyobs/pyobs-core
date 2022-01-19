from abc import ABCMeta, abstractmethod
from typing import Any, AnyStr, List


class VFSFile(metaclass=ABCMeta):
    """Base class for all VFS file classes."""

    __module__ = "pyobs.vfs"

    @abstractmethod
    async def close(self) -> None:
        ...

    @abstractmethod
    async def read(self, n: int = -1) -> AnyStr:
        ...

    @abstractmethod
    async def write(self, s: AnyStr) -> None:
        ...

    async def __aenter__(self) -> "VFSFile":
        return self

    async def __aexit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        await self.close()

    @staticmethod
    def find(path: str, pattern: str, **kwargs: Any) -> List[str]:
        """Find files by pattern matching.

        Args:
            path: Path to search in.
            pattern: Pattern to search for.
            kwargs: Parameters for specific file implementation (same as __init__).

        Returns:
            List of found files.
        """
        raise NotImplementedError()


__all__ = ["VFSFile"]
