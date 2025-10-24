from typing import Any
from urllib.parse import urljoin

import aiohttp


class ConfigDB:
    def __init__(self, url: str):
        self.url = url
        self.config: dict[str, Any] = {}

    async def _download_config(self) -> None:
        """Download the config from a URL."""
        async with aiohttp.ClientSession() as session:
            async with session.get(urljoin(self.url, "sites")) as response:
                if response.status == 200:
                    self.config = await response.json()


__all__ = ["ConfigDB"]
