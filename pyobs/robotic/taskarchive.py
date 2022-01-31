from abc import ABCMeta, abstractmethod
from typing import Optional, Any, List
from astroplan import ObservingBlock

from pyobs.utils.time import Time
from pyobs.object import Object


class TaskArchive(Object, metaclass=ABCMeta):
    def __init__(self, **kwargs: Any):
        Object.__init__(self, **kwargs)

    async def open(self) -> None:
        pass

    async def close(self) -> None:
        pass

    @abstractmethod
    async def last_changed(self) -> Optional[Time]:
        """Returns time when last time any blocks changed."""
        ...

    @abstractmethod
    async def get_schedulable_blocks(self) -> List[ObservingBlock]:
        """Returns list of schedulable blocks.

        Returns:
            List of schedulable blocks
        """
        ...


__all__ = ["TaskArchive"]
