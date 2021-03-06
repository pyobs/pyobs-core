import json
import time
import uuid


class Event(object):
    local = False

    def __init__(self):
        self.uuid = str(uuid.uuid4())
        self.timestamp = time.time()
        self.data = None

    def to_json(self):
        """JSON representation of event."""
        return {
            'type': self.__class__.__name__,
            'timestamp': self.timestamp,
            'uuid': self.uuid,
            'data': self.data
        }

    def __str__(self):
        """String representation of event."""
        return json.dumps(self.to_json())


class EventFactory(object):
    packages = [__package__]

    @staticmethod
    def from_dict(obj_dict: dict) -> Event:
        """Create Event from a dictionary.
        
        Args:
            obj_dict: JSON string for event.

        Returns:
            Event object containing event.
        """

        # create class
        cls = None
        for p in EventFactory.packages:
            # import package
            parts = p.split('.')
            pkg = __import__(parts[0])
            for comp in parts[1:]:
                pkg = getattr(pkg, comp)

            # does it have the given type as class?
            if hasattr(pkg, obj_dict['type']):
                cls = getattr(pkg, obj_dict['type'])
                break

        # not found?
        if cls is None:
            return None

        # instantiate object and set data
        obj = cls()
        obj.data = obj_dict['data']
        obj.uuid = obj_dict['uuid']
        obj.timestamp = obj_dict['timestamp'] if 'timestamp' in obj_dict else 0
        return obj


__all__ = ['Event', 'EventFactory']
