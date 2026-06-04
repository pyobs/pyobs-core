from __future__ import annotations

from abc import ABCMeta, abstractmethod
from typing import TYPE_CHECKING, Any

from pyobs.utils.enums import ImageType
from pyobs.utils.serialization import PolymorphicBaseModel
from pyobs.utils.time import Time

if TYPE_CHECKING:
    from pyobs.images import Image


class FrameInfo:
    """Base class for frame infos."""

    def __init__(self) -> None:
        self.id: str | int | None = None
        self.filename: str | None = None
        self.filter_name: str | None = None
        self.binning: int | None = None
        self.dateobs: str | None = None


class Archive(PolymorphicBaseModel, metaclass=ABCMeta):
    """Base class for image archives."""

    __module__ = "pyobs.utils.archive"

    model_config = {"arbitrary_types_allowed": True}

    @abstractmethod
    async def list_options(
        self,
        start: Time | None = None,
        end: Time | None = None,
        night: str | None = None,
        site: str | None = None,
        telescope: str | None = None,
        instrument: str | None = None,
        image_type: ImageType | None = None,
        binning: str | None = None,
        filter_name: str | None = None,
        rlevel: int | None = None,
    ) -> dict[str, list[Any]]: ...

    @abstractmethod
    async def list_frames(
        self,
        start: Time | None = None,
        end: Time | None = None,
        night: str | None = None,
        site: str | None = None,
        telescope: str | None = None,
        instrument: str | None = None,
        image_type: ImageType | None = None,
        binning: str | None = None,
        filter_name: str | None = None,
        rlevel: int | None = None,
    ) -> list[FrameInfo]: ...

    @abstractmethod
    async def download_frames(self, frames: list[FrameInfo]) -> list[Image]: ...

    async def upload_frames(self, frames: list[Image]) -> None:
        raise NotImplementedError


__all__ = ["FrameInfo", "Archive"]
