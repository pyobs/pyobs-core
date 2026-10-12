from __future__ import annotations

import json
import logging
import time
import uuid
from typing import Any

log = logging.getLogger(__name__)

_REGISTRY: dict[str, type[Event]] = {}


class Event:
    """Base class for all events.

    Every subclass is registered by its class name (the wire type and the pubsub node id only carry the
    name), no matter where it is defined, so that plugins can define their own events. Two different classes
    with the same name are rejected.
    """

    __module__ = "pyobs.events"
    local: bool = False
    version: int = 1

    def __init_subclass__(cls, **kwargs: Any) -> None:
        super().__init_subclass__(**kwargs)

        existing = _REGISTRY.get(cls.__name__)
        if existing is not None and (existing.__module__, existing.__qualname__) != (cls.__module__, cls.__qualname__):
            raise TypeError(
                f"Event name '{cls.__name__}' is already registered by "
                f"{existing.__module__}.{existing.__qualname__}; "
                f"choose a distinct name for {cls.__module__}.{cls.__qualname__}."
            )
        # same module and name: a reload or a redefinition, replace the old class
        _REGISTRY[cls.__name__] = cls

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


_REGISTRY["Event"] = Event


def get_registered_event(name: str) -> type[Event] | None:
    """Return the event class registered under the given class name, or None."""
    return _REGISTRY.get(name)


def registered_events() -> dict[str, type[Event]]:
    """Return a copy of all registered event classes by name, in registration order."""
    return dict(_REGISTRY)


class EventFactory:
    @staticmethod
    def from_dict(obj_dict: dict[str, Any]) -> Event | None:
        """Create Event from a dictionary.

        Args:
            obj_dict: JSON string for event.

        Returns:
            Event object containing event.
        """

        # find class, it has to be imported (and therefore registered) in this process
        cls = get_registered_event(obj_dict["type"])
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


__all__ = ["Event", "EventFactory", "get_registered_event", "registered_events"]
