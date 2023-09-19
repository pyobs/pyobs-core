from __future__ import annotations
import asyncio
import logging
import math
import time
from asyncio import Server
from struct import unpack, pack
from typing import Any, Optional, List

from pyobs.interfaces import IPointingRaDec
from pyobs.modules import Module

log = logging.getLogger(__name__)

MAX_INT = 2147483648


class StellariumProtocol(asyncio.Protocol):
    def __init__(self, server: Stellarium):
        self.server = server

    def connection_made(self, transport):
        log.info("Client connected.")
        self.transport = transport
        self.server.register_client(self)

    def connection_lost(self, exc: Exception | None) -> None:
        log.info("Client disconnected.")
        self.server.unregister_client(self)

    def data_received(self, data):
        # unpack data
        request = unpack("<BBBBQIi", data)

        # calculate RA/Dec
        ra_int, dec_int = request[5], request[6]
        ra = ra_int / MAX_INT * 180
        dec = dec_int / MAX_INT * 180

        # move
        log.info(f"Received command to move telescope to RA={ra}, Dec={dec}.")
        asyncio.create_task(self.server.move_telescope(ra, dec))

    def send(self, ra, dec, status):
        # to integer
        ra_int = math.floor(0.5 + ra * MAX_INT / 180.0)
        dec_int = math.floor(0.5 + dec * MAX_INT / 180.0)

        # build data and send it
        data = pack("<BBBBQIii", 24, 0, 0, 0, int(time.time() * 1000000), ra_int, dec_int, 0)
        self.transport.write(data)


class Stellarium(Module):
    """A stellarium telescope."""

    __module__ = "pyobs.modules.utils"

    def __init__(self, telescope: str, host: str = "localhost", port: int = 10001, **kwargs: Any):
        """Initialize a new stellarium telescope proxy.

        Args:
            telescope: Name of telescope module.
            port: Port to be accessed by Stellarium.

        """
        Module.__init__(self, **kwargs)

        # store
        self._telescope = telescope
        self._host = host
        self._port = port
        self._clients: List[StellariumProtocol] = []

        # server
        self._server: Optional[Server] = None

        # background task
        self.add_background_task(self._send_task)

    async def open(self) -> None:
        """Open module."""
        await Module.open(self)

        loop = asyncio.get_running_loop()
        self._server = await loop.create_server(lambda: StellariumProtocol(self), self._host, self._port)
        await self._server.start_serving()

    async def close(self) -> None:
        """Close module."""
        await Module.close(self)
        self._server.close()
        await self._server.wait_closed()

    def register_client(self, client: StellariumProtocol):
        self._clients.append(client)

    def unregister_client(self, client: StellariumProtocol):
        self._clients.remove(client)

    async def move_telescope(self, ra, dec):
        try:
            telescope = await self.proxy(self._telescope, IPointingRaDec)
            await telescope.move_radec(ra, dec)
        except ValueError:
            return

    async def _send_task(self):
        """Send coordinates to clients."""

        while True:
            # get telescope
            try:
                telescope = await self.proxy(self._telescope, IPointingRaDec)
            except ValueError:
                await asyncio.sleep(10)
                continue

            # get RA/Dec
            ra, dec = await telescope.get_radec()

            # send to all clients
            for client in self._clients:
                client.send(ra, dec, 0)

            # sleep a second
            await asyncio.sleep(1.0)


__all__ = ["Stellarium"]
