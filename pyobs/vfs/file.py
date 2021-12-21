from abc import ABCMeta, abstractmethod
from typing import Any, AnyStr


class VFSFile(metaclass=ABCMeta):
    """Base class for all VFS file classes."""
    __module__ = 'pyobs.vfs'

    @abstractmethod
    async def close(self) -> None:
        ...

    @abstractmethod
    async def read(self, n: int = -1) -> AnyStr:
        ...

    @abstractmethod
    async def write(self, s: AnyStr) -> None:
        ...

    async def __aenter__(self) -> 'VFSFile':
        return self

    async def __aexit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        await self.close()


__all__ = ['VFSFile']
