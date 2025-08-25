import logging
from typing import Any

from pyobs.modules import Module
from pyobs.events import LogEvent, Event

log = logging.getLogger(__name__)


class Matrix(Module):
    """A matrix bot."""

    __module__ = "pyobs.modules.utils"

    def __init__(
        self, server: str, user_id: str, password: str, room_id: str, log_level: str = "WARNING", **kwargs: Any
    ):
        """Initialize a new bot.

        Args:
            server: Server to connect to.
            user_id: ID of user to connect as.
            password: Password for user.
            room_id: Room ID to send messages to.
            log_level: Log level to use.
        """
        Module.__init__(self, **kwargs)

        from nio import AsyncClient  # type: ignore

        self.client = AsyncClient(server, user_id)
        self._password = password
        self._room_id = room_id
        self._log_level = log_level

        # get log levels
        self._log_levels = {
            logging.getLevelName(x): x for x in range(1, 101) if not logging.getLevelName(x).startswith("Level")
        }

    async def open(self) -> None:
        """Open module."""
        await Module.open(self)

        # self.client.add_event_callback(message_callback, RoomMessageText)
        await self.client.login(self._password)

        # listen to log events
        await self.comm.register_event(LogEvent, self._process_log_entry)

    async def close(self) -> None:
        """Close module."""
        await Module.close(self)

        # stop matrix client
        if self.client is not None:
            await self.client.close()

    async def _process_log_entry(self, entry: Event, sender: str) -> bool:
        """Process a new log entry.

        Args:
            entry: The log event.
            sender: Name of sender.
        """
        if not isinstance(entry, LogEvent):
            return False

        # if log level of message is too small, ignore it
        if self._log_levels[entry.level] < self._log_levels[self._log_level]:
            return False

        # build log message
        message = "(%s) %s: %s" % (entry.level, sender, entry.message)

        # send it
        await self.client.room_send(
            room_id=self._room_id,
            message_type="m.room.message",
            content={"msgtype": "m.text", "body": message},
        )
        return True


__all__ = ["Matrix"]
