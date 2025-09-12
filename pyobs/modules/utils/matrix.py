import asyncio
import logging
from asyncio import Task
from typing import Any
from nio import AsyncClient, MatrixRoom, RoomMessageText, InviteEvent

from pyobs.modules import Module
from pyobs.events import LogEvent, Event

log = logging.getLogger(__name__)


class MatrixClient(AsyncClient):
    def __init__(
        self,
        homeserver,
        user="",
        device_id="",
        config=None,
        ssl=None,
        proxy=None,
    ):
        super().__init__(
            homeserver,
            user=user,
            device_id=device_id,
            config=config,
            ssl=ssl,
            proxy=proxy,
        )

        # auto-join room invites
        self.add_event_callback(self.cb_autojoin_room, InviteEvent)

        # print all the messages we receive
        self.add_event_callback(self.cb_print_messages, RoomMessageText)

    def cb_autojoin_room(self, room: MatrixRoom, event: InviteEvent):
        """Callback to automatically joins a Matrix room on invite.

        Arguments:
            room {MatrixRoom} -- Provided by nio
            event {InviteEvent} -- Provided by nio
        """
        self.join(room.room_id)
        room = self.rooms["ROOM_ID"]
        print(f"Room {room.name} is encrypted: {room.encrypted}")

    async def cb_print_messages(self, room: MatrixRoom, event: RoomMessageText):
        """Callback to print all received messages to stdout.

        Arguments:
            room {MatrixRoom} -- Provided by nio
            event {RoomMessageText} -- Provided by nio
        """
        if event.decrypted:
            encrypted_symbol = "🛡 "
        else:
            encrypted_symbol = "⚠️ "
        print(f"{room.display_name} |{encrypted_symbol}| {room.user_name(event.sender)}: {event.body}")


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
        from nio import LoginResponse

        await Module.open(self)

        # log in
        resp = await self.client.login(self._password)
        if isinstance(resp, LoginResponse):
            log.info("Login to Matrix server successful.")
        else:
            raise RuntimeError(f"Failed to log in: {resp}")

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
