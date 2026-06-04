import io
import logging
import urllib.parse
from typing import Any, TypedDict, cast

import aiohttp
from pydantic import PrivateAttr

from pyobs.images import Image
from pyobs.utils.enums import ImageType
from pyobs.utils.time import Time

from .archive import Archive, FrameInfo

log = logging.getLogger(__name__)


class PyobsArchiveFrameInfoDict(TypedDict):
    id: int
    basename: str
    DATE_OBS: str
    FILTER: str
    binning: str
    url: str


class PyobsArchiveFrameInfo(FrameInfo):
    """Frame info for pyobs archive."""

    def __init__(self, info: PyobsArchiveFrameInfoDict):
        FrameInfo.__init__(self)
        self.info = info
        self.id = self.info["id"]
        self.filename = self.info["basename"]
        self.dateobs = Time(self.info["DATE_OBS"])
        self.filter_name = self.info["FILTER"]
        self.binning = int(self.info["binning"][0])
        self.url = self.info["url"]


class PyobsArchive(Archive):
    """Connector class to running pyobs-archive instance."""

    __module__ = "pyobs.utils.archive"

    url: str
    token: str
    proxies: dict[str, str] | None = None

    _headers: dict[str, str] = PrivateAttr()
    _timeout: aiohttp.ClientTimeout = PrivateAttr()

    model_config = {"arbitrary_types_allowed": True}

    def model_post_init(self, __context: Any) -> None:
        self._headers = {"Authorization": "Token " + self.token}
        self._timeout = aiohttp.ClientTimeout(total=30)

    async def list_options(
        self,
        start: Time | None = None,
        end: Time | None = None,
        night: str | None = None,
        site: str | None = None,
        telescope: str | None = None,
        instrument: str | None = None,
        image_type: ImageType | None = None,
        binning: str | None = None,
        filter_name: str | None = None,
        rlevel: int | None = None,
    ) -> dict[str, list[Any]]:
        url = urllib.parse.urljoin(self.url, "frames/aggregate/")
        params = self._build_query(
            start, end, night, site, telescope, instrument, image_type, binning, filter_name, rlevel
        )
        async with aiohttp.ClientSession() as session:
            async with session.get(url, params=params, headers=self._headers, timeout=self._timeout) as response:
                if response.status != 200:
                    raise ValueError(f"Could not query frames: {str(await response.text())}")
                return cast(dict[str, list[Any]], await response.json())

    async def list_frames(
        self,
        start: Time | None = None,
        end: Time | None = None,
        night: str | None = None,
        site: str | None = None,
        telescope: str | None = None,
        instrument: str | None = None,
        image_type: ImageType | None = None,
        binning: str | None = None,
        filter_name: str | None = None,
        rlevel: int | None = None,
    ) -> list[FrameInfo]:
        url = urllib.parse.urljoin(self.url, "frames/")
        params = self._build_query(
            start, end, night, site, telescope, instrument, image_type, binning, filter_name, rlevel
        )
        frames: list[FrameInfo] = []
        params["offset"] = 0
        params["limit"] = 1000
        async with aiohttp.ClientSession() as session:
            while True:
                async with session.get(url, params=params, headers=self._headers, timeout=self._timeout) as response:
                    if response.status != 200:
                        raise ValueError("Could not query frames")
                    res = await response.json()
                    new_frames = [PyobsArchiveFrameInfo(frame) for frame in res["results"]]
                    frames.extend(new_frames)
                    if len(frames) >= res["count"]:
                        return frames
                    params["offset"] += len(new_frames)

    @staticmethod
    def _build_query(
        start: Time | None = None,
        end: Time | None = None,
        night: str | None = None,
        site: str | None = None,
        telescope: str | None = None,
        instrument: str | None = None,
        image_type: ImageType | None = None,
        binning: str | None = None,
        filter_name: str | None = None,
        rlevel: int | None = None,
    ) -> dict[str, Any]:
        params: dict[str, Any] = {}
        if start is not None:
            params["start"] = start.isot
        if end is not None:
            params["end"] = end.isot
        if night is not None:
            params["night"] = night
        if site is not None:
            params["SITE"] = site
        if telescope is not None:
            params["TELESCOPE"] = telescope
        if instrument is not None:
            params["INSTRUMENT"] = instrument
        if image_type is not None:
            params["IMAGETYPE"] = image_type.value
        if binning is not None:
            params["binning"] = binning
        if filter_name is not None:
            params["FILTER"] = filter_name
        if rlevel is not None:
            params["RLEVEL"] = rlevel
        return params

    async def download_frames(self, infos: list[FrameInfo]) -> list[Image]:
        images = []
        for info in infos:
            if not isinstance(info, PyobsArchiveFrameInfo):
                log.warning("Incorrect type for frame info.")
                continue
            url = urllib.parse.urljoin(self.url, info.url)
            async with aiohttp.ClientSession() as session:
                async with session.get(url, headers=self._headers, timeout=self._timeout) as response:
                    if response.status != 200:
                        log.exception("Error downloading file %s.", info.filename)
                    try:
                        image = Image.from_bytes(await response.read())
                        images.append(image)
                    except OSError:
                        log.exception("Error downloading file %s.", info.filename)
        return images

    async def download_headers(self, infos: list[PyobsArchiveFrameInfo]) -> list[dict[str, Any]]:
        headers = []
        for info in infos:
            url = urllib.parse.urljoin(self.url, info.url).replace("download", "headers")
            async with aiohttp.ClientSession() as session:
                async with session.get(url, headers=self._headers, timeout=self._timeout) as response:
                    if response.status != 200:
                        log.error("Could not fetch headers for %s.", info.filename)
                    try:
                        results = (await response.json())["results"]
                        headers.append(dict((d["key"], d["value"]) for d in results))
                    except KeyError:
                        log.error("Could not fetch headers for %s.", info.filename)
                        headers.append({})
        return headers

    async def upload_frames(self, images: list[Image]) -> None:
        url = urllib.parse.urljoin(self.url, "frames/create/")
        async with aiohttp.ClientSession() as session:
            data = aiohttp.FormData()
            async with session.get(self.url, headers=self._headers) as response:
                token = response.cookies["csrftoken"].value
                data.add_field("csrfmiddlewaretoken", token)
            for i, img in enumerate(images, 1):
                filename = img.header["FNAME"]
                with io.BytesIO() as bio:
                    img.writeto(bio)
                    data.add_field(f"file{i}", bio.getvalue(), filename=filename)
            async with session.post(url, data=data, timeout=self._timeout, headers=self._headers) as response:
                if response.status != 200:
                    raise ValueError(f"Cannot write file, received status_code {response.status}.")
                json = await response.json()
                if "created" not in json or json["created"] == 0:
                    if "errors" in json:
                        raise ValueError("Could not create file in archive: " + str(json["errors"]))
                    else:
                        raise ValueError("Could not create file in archive.")


__all__ = ["PyobsArchiveFrameInfo", "PyobsArchive"]
