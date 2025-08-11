import asyncio
import logging
from asyncio import Task
from typing import Any

from pyobs.images.processor import ImageProcessor
from pyobs.images import Image
from pyobs.interfaces import IFitsHeaderBefore

log = logging.getLogger(__name__)


class GetFitsHeaders(ImageProcessor):
    """Retrieves FITS headers from another module (or more)."""

    __module__ = "pyobs.images.processors.modules"

    def __init__(self, sender: str | list[str], namespace: str | None = None, **kwargs: Any):
        """Init a fits header processor.

        Args:
            sender: Sender(s) to fetch FITS headers from.
            namespace: FITS namespace.
        """
        ImageProcessor.__init__(self, **kwargs)

        self._senders = [sender] if isinstance(sender, str) else sender
        self._namespace = namespace

    async def __call__(self, image: Image) -> Image:
        """Retrieve FITS headers from another module (or more).

        Args:
            image: Image to add headers to.

        Returns:
            Image with headers added.
        """

        # loop all modules
        requests: list[Task[Any]] = []
        for sender in self._senders:
            # get proxy
            proxy = await self.proxy(sender, IFitsHeaderBefore)

            # request headers
            requests.append(asyncio.create_task(proxy.get_fits_header_before(self._namespace)))

        # copy image
        out = image.copy()

        # await all requests
        for request in requests:
            hdr = await request
            for key, value in hdr.items():
                if isinstance(value, list) and not isinstance(value, str):
                    # convert list to tuple
                    out.header[key] = tuple(value)
                else:
                    out.header[key] = value
        return out


__all__ = ["GetFitsHeaders"]
