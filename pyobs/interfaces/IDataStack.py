from __future__ import annotations

from abc import ABCMeta, abstractmethod
from dataclasses import dataclass, field
from typing import Any

from ..utils.time import Time
from .IAbortable import IAbortable


@dataclass
class DataStackState:
    count_total: int  # 0 when idle / no stack running
    count_left: int
    time: Time = field(default_factory=Time.now)


class IDataStack(IAbortable, metaclass=ABCMeta):
    """The module can grab a stack of consecutive frames (images, ...) into one product."""

    __module__ = "pyobs.interfaces"

    state = DataStackState

    @abstractmethod
    async def grab_stack(self, count: int, broadcast: bool = True, **kwargs: Any) -> str:
        """Grab `count` consecutive frames into one product and return its name.

        Without a pipeline selected (IDataPipeline), the product is a 3D cube of all frames.
        With one, the pipeline runs on the cube (e.g. to combine it) and only its result is
        stored.

        Blocks until the product is stored. Progress is available via DataStackState.

        Args:
            count: Number of frames.
            broadcast: Broadcast existence of the product.

        Returns:
            Name of the stored product.

        Raises:
            InvalidArgumentError: If count < 1, or the stack would exceed the module's memory cap.
            DeviceBusyError: If the device is exposing, or running a sequence or another stack.
            AbortedError: If the stack was aborted.
            GrabImageError: If a frame could not be grabbed, frames don't match, or the
                pipeline failed.
        """
        ...


__all__ = ["IDataStack", "DataStackState"]
