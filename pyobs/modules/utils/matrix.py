import asyncio
import logging
from asyncio import Task
from typing import Any

from pyobs.modules import Module
from pyobs.events import LogEvent, Event

log = logging.getLogger(__name__)


class Matrix(Module):
    """A matrix bot."""

    __module__ = "pyobs.modules.utils"

    def __init__(
        self,
        server: str,
        user_id: str,
        password: str,
        room_id: str,
        name: str = "Bot",
        log_level: str = "WARNING",
        **kwargs: Any,
    ):
        """Initialize a new bot.

        Args:
            server: Server to connect to.
            user_id: ID of user to connect as.
            password: Password for user.
            room_id: Room ID to send messages to.
            name: Name of bot.
            log_level: Log level to use.
        """
        Module.__init__(self, **kwargs)

        from nio import AsyncClient  # type: ignore

        self.client = AsyncClient(server, user_id)
        self._password = password
        self._room_id = room_id
        self._name = name
        self._log_level = log_level
        self._sync: Task[Any] | None = None

        # get log levels
        self._log_levels = {
            logging.getLevelName(x): x for x in range(1, 101) if not logging.getLevelName(x).startswith("Level")
        }

        # disable INFO logging for nio
        logging.getLogger("nio").setLevel(logging.WARNING)

    async def open(self) -> None:
        """Open module."""
        await Module.open(self)

        # self.client.add_event_callback(message_callback, RoomMessageText)
        await self.client.login(self._password)

        # listen to log events
        await self.comm.register_event(LogEvent, self._process_log_entry)

        # do initial sync
        await self.client.sync()
        await self.client.set_displayname(self._name)

        # join invited room if it is the given room id
        for room_id, room in self.client.invited_rooms.items():
            if room_id == self._room_id:
                await self.client.join(room_id)

        # start sync loop
        self._sync = asyncio.create_task(self.client.sync_forever(30000, loop_sleep_time=30000))

        await self.client.room_send(
            room_id=self._room_id,
            message_type="m.room.message",
            content={"msgtype": "m.text", "body": "Hello world!"},
        )

    async def close(self) -> None:
        """Close module."""
        await Module.close(self)

        # stop matrix client
        self.client.stop_sync_forever()
        await self.client.close()

    async def _process_log_entry(self, entry: Event, sender: str) -> bool:
        """Process a new log entry.

        Args:
            entry: The log event.
            sender: Name of sender.
        """
        if not isinstance(entry, LogEvent):
            return False

        # don't log my own messages
        if sender == self.comm.name:
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
