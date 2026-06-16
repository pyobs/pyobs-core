import asyncio
import logging
from asyncio import Queue, Task
from typing import Any

from pyobs.events import Event, LogEvent
from pyobs.modules import Module

log = logging.getLogger(__name__)

# Maximum number of messages to buffer before dropping new ones.
# Keeps RAM bounded during log bursts.
_QUEUE_MAX = 50

# Minimum delay between room_send calls to avoid rate limiting (in seconds).
_SEND_INTERVAL = 0.5


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

        self._server = server
        self._user_id = user_id
        self._password = password
        self._room_id = room_id
        self._name = name
        self._log_level = log_level
        self.client: Any = None
        self._sync: Task[Any] | None = None
        self._queue: Queue[str] = Queue(maxsize=_QUEUE_MAX)

        # get log levels
        self._log_levels = {
            logging.getLevelName(x): x for x in range(1, 101) if not logging.getLevelName(x).startswith("Level")
        }

        # disable INFO logging for nio
        logging.getLogger("nio").setLevel(logging.WARNING)

        # register send loop as background task; started automatically on open()
        self.add_background_task(self._send_loop, restart=False)

    async def open(self) -> None:
        """Open module."""
        from nio import AsyncClient, LoginResponse  # type: ignore

        await Module.open(self)

        # create client here, inside the running event loop
        self.client = AsyncClient(self._server, self._user_id)

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
        if self.client is not None:
            self.client.stop_sync_forever()
            await self.client.close()

    async def _send_loop(self) -> None:
        """Drain the message queue and send messages one at a time.

        Sending sequentially with a small delay between messages avoids
        rate limiting (HTTP 429) and keeps memory usage bounded.
        """
        while True:
            message = await self._queue.get()
            try:
                await self.client.room_send(
                    room_id=self._room_id,
                    message_type="m.room.message",
                    content={"msgtype": "m.text", "body": message},
                )
            except Exception:
                log.exception("Failed to send Matrix message.")
            finally:
                self._queue.task_done()

            # brief pause to stay under the server's rate limit
            await asyncio.sleep(_SEND_INTERVAL)

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

        # client not yet connected
        if self.client is None:
            return False

        # build log message
        message = f"({entry.level}) {sender}: {entry.message}"

        # drop message if queue is full to prevent memory runaway during bursts
        if self._queue.full():
            log.warning("Matrix message queue full, dropping message.")
            return False

        await self._queue.put(message)
        return True


__all__ = ["Matrix"]
