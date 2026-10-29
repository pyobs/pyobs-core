from __future__ import annotations

from typing import Any

from pyobs.events.event import Event
from pyobs.events.newdata import DataType, NewDataEvent


class NewSpectrumEvent(NewDataEvent):
    """Event to be sent on a new spectrum."""

    __module__ = "pyobs.events"

    def __init__(self, filename: str, **kwargs: Any):
        """Initializes new NewSpectrumEvent.

        Args:
            filename: Name of new spectrum file.
        """
        NewDataEvent.__init__(self, filename)
        self.data: DataType = {"filename": filename}

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> Event:
        # get filename
        if "filename" not in d or not isinstance(d["filename"], str):
            raise ValueError("Invalid type for filename.")
        filename: str = d["filename"]

        # return object
        return cls(filename)


__all__ = ["NewSpectrumEvent"]
