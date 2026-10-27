from __future__ import annotations

from typing import Any, TypedDict

from pyobs.events.event import Event


class DataType(TypedDict):
    filename: str


class FileWrittenEvent(Event):
    """Event to be sent after a file has been written to its destination.

    The filename is a VFS path, not a local path, so a receiver needs the same VFS root to open the file.
    """

    __module__ = "pyobs.events"

    def __init__(self, filename: str, **kwargs: Any):
        """Initializes new FileWrittenEvent.

        Args:
            filename: VFS name of the written file.
        """
        Event.__init__(self)
        self.data: DataType = {"filename": filename}

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> Event:
        # get filename
        if "filename" not in d or not isinstance(d["filename"], str):
            raise ValueError("Invalid type for filename.")
        filename: str = d["filename"]

        # return object
        return FileWrittenEvent(filename)

    @property
    def filename(self) -> str:
        return self.data["filename"]


__all__ = ["FileWrittenEvent"]
