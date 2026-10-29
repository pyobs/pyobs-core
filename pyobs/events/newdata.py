from __future__ import annotations

from typing import Any, TypedDict

from pyobs.events.event import Event


class DataType(TypedDict):
    filename: str


class NewDataEvent(Event):
    """Event to be sent on new data, e.g. a file that is neither an image nor a spectrum.

    ``filename`` is a VFS path. :class:`NewImageEvent` and :class:`NewSpectrumEvent` derive from this class, so a
    handler registered for ``NewDataEvent`` also receives those; use ``type(event) is NewDataEvent`` to select only
    generic data.
    Registering ``NewDataEvent`` without a handler declares only this class as sent, not the derived events.
    """

    __module__ = "pyobs.events"

    def __init__(self, filename: str, **kwargs: Any):
        """Initializes new NewDataEvent.

        Args:
            filename: Name of new data file.
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
        return cls(filename)

    @property
    def filename(self) -> str:
        return self.data["filename"]


__all__ = ["NewDataEvent"]
