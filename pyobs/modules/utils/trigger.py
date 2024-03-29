import logging
from typing import Any, List, Dict

from pyobs.events import Event
from pyobs.modules import Module
from pyobs.interfaces import IAutonomous
from pyobs.object import get_class_from_string

log = logging.getLogger(__name__)


class Trigger(Module, IAutonomous):
    """A module that can call another module's methods when a specific event occurs."""

    __module__ = "pyobs.modules.utils"

    def __init__(self, triggers: List[Dict[str, Any]], **kwargs: Any):
        """Initialize a new trigger module.

        Args:
            triggers: List of dictionaries defining the trigger. Must contain fields for event, module and method,
                      may contain a sender.

        """
        Module.__init__(self, **kwargs)

        # store
        self._running = False

        # store triggers and convert event strings to actual classes
        self._triggers = triggers
        for trigger in self._triggers:
            # get class and store it
            kls = get_class_from_string(trigger["event"])
            trigger["event"] = kls

    async def open(self) -> None:
        """Open module."""
        await Module.open(self)

        # get a list of all events
        events = list(set([t["event"] for t in self._triggers]))

        # start
        self._running = True

        # register them
        for event in events:
            await self.comm.register_event(event, self._handle_event)

    async def start(self, **kwargs: Any) -> None:
        """Starts a service."""
        self._running = True

    async def stop(self, **kwargs: Any) -> None:
        """Stops a service."""
        self._running = False

    async def is_running(self, **kwargs: Any) -> bool:
        """Whether a service is running."""
        return self._running

    async def _handle_event(self, event: Event, sender: str) -> bool:
        """Handle an incoming event.

        Args:
            event: The received event
            sender: Name of sender
        """

        # not running?
        if not self._running:
            return False

        # loop all triggers
        for trigger in self._triggers:
            # does it handle the event?
            if trigger["event"] == event.__class__:
                log.info(
                    "Received a %s event and calling %s.%s now.", str(type(event)), trigger["module"], trigger["method"]
                )

                # get proxy
                try:
                    proxy = await self.comm.proxy(trigger["module"])

                    # call it
                    await proxy.execute(trigger["method"])

                except ValueError:
                    log.exception("Could not execute command on proxy %s.", trigger["module"])
                    continue

                except Exception as e:
                    log.error("Error on calling %s.%s: %s", trigger["module"], trigger["method"], e)
                    continue

        return True


__all__ = ["Trigger"]
