import asyncio
import logging
import os
from asyncio import Task
from typing import Any

import yaml
from nio import (
    AsyncClient,
    MatrixRoom,
    InviteEvent,
    AsyncClientConfig,
    LoginResponse,
    RoomMessageText,
)  # type: ignore
from nio.store import DefaultStore

from pyobs.modules import Module
from pyobs.events import LogEvent, Event

log = logging.getLogger(__name__)


class MatrixClient(AsyncClient):  # type: ignore
    def __init__(
        self,
        homeserver: str,
        user: str = "",
        device_id: str | None = "",
        store_path: str | None = "",
        config: AsyncClientConfig | None = None,
        ssl: bool | None = None,
        proxy: str | None = None,
    ):
        super().__init__(
            homeserver,
            user=user,
            device_id=device_id,
            store_path=store_path,
            config=config,
            ssl=ssl,
            proxy=proxy,
        )

        # auto-join room invites
        self.add_event_callback(self.cb_autojoin_room, InviteEvent)

        # print all the messages we receive
        self.add_event_callback(self.cb_print_messages, RoomMessageText)

    async def cb_autojoin_room(self, room: MatrixRoom, event: InviteEvent) -> None:
        """Callback to automatically joins a Matrix room on invite.

        Args:
            room: Room to join.
            event: Invite event.
        """
        await self.join(room.room_id)

    async def cb_print_messages(self, room: MatrixRoom, event: RoomMessageText) -> None:
        """Callback to print all received messages to stdout.

        Arguments:
            room {MatrixRoom} -- Provided by nio
            event {RoomMessageText} -- Provided by nio
        """

        # ignore messages from myself
        if event.sender == self.user_id:
            return

        if event.decrypted:
            encrypted_symbol = "🛡 "
        else:
            encrypted_symbol = "⚠️ "
        msg = f"{room.display_name} |{encrypted_symbol}| {room.user_name(event.sender)}: {event.body}"
        try:
            await self.room_send(
                room_id="!atijqBDCwcekDQTQTU:uni-goettingen.de",
                message_type="m.room.message",
                content={"msgtype": "m.text", "body": msg},
            )
        except:
            log.exception("Failed to send message to room.")

    def trust_devices(self, user_id: str, device_list: str | None = None) -> None:
        """Trusts the devices of a user.

        If no device_list is provided, all of the users devices are trusted. If
        one is provided, only the devices with IDs in that list are trusted.

        Arguments:
            user_id {str} -- the user ID whose devices should be trusted.

        Keyword Arguments:
            device_list {Optional[str]} -- The full list of device IDs to trust
                from that user (default: {None})
        """

        print(f"{user_id}'s device store: {self.device_store[user_id]}")

        # The device store contains a dictionary of device IDs and known
        # OlmDevices for all users that share a room with us, including us.

        # We can only run this after a first sync. We have to populate our
        # device store and that requires syncing with the server.
        for device_id, olm_device in self.device_store[user_id].items():
            if device_list and device_id not in device_list:
                # a list of trusted devices was provided, but this ID is not in
                # that list. That's an issue.
                print(f"Not trusting {device_id} as it's not in {user_id}'s pre-approved list.")
                continue

            if user_id == self.user_id and device_id == self.device_id:
                # We cannot explicitly trust the device @alice is using
                continue

            self.verify_device(olm_device)
            print(f"Trusting {device_id} from user {user_id}")


class Matrix(Module):
    """A matrix bot."""

    __module__ = "pyobs.modules.utils"

    def __init__(
        self,
        server: str,
        user: str,
        password: str,
        room_id: str,
        store_path: str,
        name: str = "Bot",
        log_level: str = "WARNING",
        **kwargs: Any,
    ):
        """Initialize a new bot.

        Args:
            server: Server to connect to.
            user: ID of user to connect as.
            password: Password for user.
            room_id: Room ID to send messages to.
            store_path: Path to store files, NO vfs path!
            name: Name of bot.
            log_level: Log level to use.
        """
        Module.__init__(self, **kwargs)

        self._password = password
        self._room_id = room_id
        self._name = name
        self._log_level = log_level
        self._store_path = store_path
        self._sync: Task[Any] | None = None

        # if the store location doesn't exist, we'll make it
        if store_path and not os.path.isdir(store_path):
            os.mkdir(store_path)

        # matrix client
        config = AsyncClientConfig(store_sync_tokens=True, store=DefaultStore)
        self.client = MatrixClient(server, user, store_path=store_path, config=config, ssl=False)

        # get log levels
        self._log_levels = {
            logging.getLevelName(x): x for x in range(1, 101) if not logging.getLevelName(x).startswith("Level")
        }

        # disable INFO logging for nio
        logging.getLogger("nio").setLevel(logging.WARNING)

    async def open(self) -> None:
        """Open module."""
        await Module.open(self)

        # log in
        await self.login()

        # do initial sync and set name
        await self.client.sync()
        await self.after_first_sync()
        await self.client.set_displayname(self._name)

        # start sync loop
        self._sync = asyncio.create_task(self.client.sync_forever(30000))

        # listen to log events
        await self.comm.register_event(LogEvent, self._process_log_entry)

        # await self.client.room_send(
        #    room_id="!atijqBDCwcekDQTQTU:uni-goettingen.de",
        #    message_type="m.room.message",
        #    content={"msgtype": "m.text", "body": "Hello world!"},
        # )

    async def close(self) -> None:
        """Close module."""
        await Module.close(self)

        # stop matrix client
        self.client.stop_sync_forever()
        await self.client.close()

    async def after_first_sync(self) -> None:
        self.client.trust_devices("@thusser:uni-goettingen.de")
        self.client.trust_devices("@u20380:bot.academiccloud.de")

    async def login(self) -> None:
        """Log in either using the global variables or (if possible) using the
        session details file."""

        session_file = os.path.join(self._store_path, "session.yaml")

        # restore the previous session if we can
        if os.path.exists(session_file) and os.path.isfile(session_file):
            with open(session_file, "r") as sf:
                config = yaml.load(sf, Loader=yaml.SafeLoader)
                self.client.access_token = config["access_token"]
                self.client.user_id = config["user_id"]
                self.client.device_id = config["device_id"]
                self.client.load_store()
                log.info(f"Logging in using stored credentials: {self.client.user_id} on {self.client.device_id}")

        # we didn't restore a previous session, so we'll log in with a password
        if not self.client.user_id or not self.client.access_token or not self.client.device_id:
            # this calls the login method defined in AsyncClient from nio
            resp = await self.client.login(self._password)

            if isinstance(resp, LoginResponse):
                log.info("Logged in using a password, saving details...")
                with open(session_file, "w") as sf:
                    yaml.dump(
                        {
                            "access_token": self.client.access_token,
                            "device_id": self.client.device_id,
                            "user_id": self.client.user_id,
                        },
                        sf,
                    )
            else:
                raise RuntimeError(f"Failed to log in: {resp}")

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
