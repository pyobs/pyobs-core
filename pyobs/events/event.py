from __future__ import annotations

import json
import logging
import time
import uuid
from typing import Any

log = logging.getLogger(__name__)


class Event:
    """Base class for all events."""

    __module__ = "pyobs.events"
    local = False

    def __init__(self, **kwargs: Any):
        self.uuid = str(uuid.uuid4())
        self.timestamp = time.time()
        self.data: Any = {}

    def to_json(self) -> dict[str, Any]:
        """JSON representation of event."""
        return {"type": self.__class__.__name__, "timestamp": self.timestamp, "uuid": self.uuid, "data": self.data}

    def __str__(self) -> str:
        """String representation of event."""
        return json.dumps(self.to_json())

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> Event:
        """Generic from_dict method for derived classes that don't need their own."""
        return cls(**d)


class EventFactory:
    packages = [__package__]

    @staticmethod
    def from_dict(obj_dict: dict[str, Any]) -> Event | None:
        """Create Event from a dictionary.

        Args:
            obj_dict: JSON string for event.

        Returns:
            Event object containing event.
        """

        # create class
        cls: Event | None = None
        for p in EventFactory.packages:
            # import package
            parts = p.split(".")
            pkg = __import__(parts[0])
            for comp in parts[1:]:
                pkg = getattr(pkg, comp)

            # does it have the given type as class?
            if hasattr(pkg, obj_dict["type"]):
                cls = getattr(pkg, obj_dict["type"])
                break

        # not found?
        if cls is None:
            return None

        # instantiate object and set data
        try:
            kwargs = obj_dict["data"] if "data" in obj_dict and obj_dict["data"] is not None else {}
            if not isinstance(kwargs, dict):
                raise ValueError(f'Invalid event structure for event {str(cls)}: "{str(kwargs)}".')
            obj: Event = cls.from_dict(kwargs)
            obj.uuid = obj_dict["uuid"]
            obj.timestamp = obj_dict["timestamp"] if "timestamp" in obj_dict else 0
            return obj

        except ValueError as e:
            log.warning("Could not create event %s: %s", obj_dict["type"], e)
            return None


__all__ = ["Event", "EventFactory"]
