from __future__ import annotations
from typing import Optional, Dict, Any
from typing_extensions import TypedDict

from pyobs.events.event import Event
from pyobs.utils.enums import ImageType


DataType = TypedDict("DataType", {"filename": str, "image_type": Optional[str], "raw": Optional[str]})


class NewImageEvent(Event):
    """Event to be sent on a new image."""

    __module__ = "pyobs.events"

    def __init__(self, filename: str, image_type: Optional[ImageType] = None, raw: Optional[str] = None, **kwargs: Any):
        """Initializes new NewImageEvent.

        Args:
            filename: Name of new image file.
            image_type: Type of image.
            raw: Only for reduced images, references raw frame.
        """
        Event.__init__(self)
        self.data: DataType = {
            "filename": filename,
            "image_type": image_type.value if image_type is not None else None,
            "raw": raw,
        }

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> Event:
        # get filename
        if "filename" not in d or not isinstance(d["filename"], str):
            raise ValueError("Invalid type for filename.")
        filename: str = d["filename"]

        # get image type
        image_type: Optional[ImageType] = None
        if "image_type" in d and isinstance(d["image_type"], str):
            image_type = ImageType(d["image_type"])

        # get raw
        raw: Optional[str] = None
        if "raw" in d and isinstance(d["raw"], str):
            raw = d["raw"]

        # return object
        return NewImageEvent(filename, image_type, raw)

    @property
    def filename(self) -> str:
        return self.data["filename"]

    @property
    def image_type(self) -> Optional[ImageType]:
        return ImageType(self.data["image_type"]) if "image_type" in self.data else None

    @property
    def raw(self) -> Optional[str]:
        return self.data["raw"]

    @property
    def is_reduced(self) -> bool:
        return self.raw is not None


__all__ = ["NewImageEvent"]
