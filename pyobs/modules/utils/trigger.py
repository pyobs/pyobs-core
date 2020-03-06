import logging

from pyobs.events import Event
from pyobs import PyObsModule
from pyobs.object import get_class_from_string

log = logging.getLogger(__name__)


class Trigger(PyObsModule):
    """A module that can call another module's methods when a specific event occurs."""

    def __init__(self, triggers: list, *args, **kwargs):
        """Initialize a new trigger module.

        Args:
            triggers: List of dictionaries defining the trigger. Must contain fields for event, module and method,
                      may contain a sender.

        """
        PyObsModule.__init__(self, *args, **kwargs)

        # store triggers and convert event strings to actual classes
        self._triggers = triggers
        for trigger in self._triggers:
            # get class and store it
            kls = get_class_from_string(trigger['event'])
            trigger['event'] = kls

    def open(self):
        """Open module."""
        PyObsModule.open(self)

        # get a list of all events
        events = list(set([t['event'] for t in self._triggers]))

        # register them
        for event in events:
            self.comm.register_event(event, self._handle_event)

    def _handle_event(self, event: Event, sender: str):
        """Handle an incoming event.

        Args:
            event: The received event
            sender: Name of sender
        """

        # loop all triggers
        for trigger in self._triggers:
            # does it handle the event?
            if trigger['event'] == event.__class__:
                log.info('Received a %s event and calling %s.%s now.',
                         str(type(event)), trigger['module'], trigger['method'])

                # get proxy
                try:
                    proxy = self.comm[trigger['module']]
                except KeyError:
                    log.error('Could not get proxy for %s.', trigger['module'])
                    continue

                # call it
                try:
                    proxy.execute(trigger['method'])
                except Exception as e:
                    log.error('Error on calling %s.%s: %s', trigger['module'], trigger['method'], e)
                    continue


__all__ = ['Trigger']
