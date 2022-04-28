import io
from typing import List, Dict, Any, Optional, cast
import aiohttp
import urllib.parse
import logging

from pyobs.utils.time import Time
from pyobs.images import Image
from pyobs.utils.archive import Archive, FrameInfo
from pyobs.utils.enums import ImageType

log = logging.getLogger(__name__)


class PyobsArchiveFrameInfo(FrameInfo):
    """Frame info for pyobs archive."""

    def __init__(self, info: Dict[str, str]):
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

    def __init__(self, url: str, token: str, proxies: Optional[Dict[str, str]] = None, **kwargs: Any):
        self._url = url
        self._headers = {"Authorization": "Token " + token}
        self._proxies = proxies

    async def list_options(
        self,
        start: Optional[Time] = None,
        end: Optional[Time] = None,
        night: Optional[str] = None,
        site: Optional[str] = None,
        telescope: Optional[str] = None,
        instrument: Optional[str] = None,
        image_type: Optional[ImageType] = None,
        binning: Optional[str] = None,
        filter_name: Optional[str] = None,
        rlevel: Optional[int] = None,
    ) -> Dict[str, List[Any]]:
        # build URL
        url = urllib.parse.urljoin(self._url, "frames/aggregate/")

        # and params
        params = self._build_query(
            start, end, night, site, telescope, instrument, image_type, binning, filter_name, rlevel
        )

        # do request
        async with aiohttp.ClientSession() as session:
            async with session.get(url, params=params, headers=self._headers, timeout=10) as response:
                if response.status != 200:
                    raise ValueError("Could not query frames: %s" % str(await response.text()))

                # create frames and return them
                return await response.json()

    async def list_frames(
        self,
        start: Optional[Time] = None,
        end: Optional[Time] = None,
        night: Optional[str] = None,
        site: Optional[str] = None,
        telescope: Optional[str] = None,
        instrument: Optional[str] = None,
        image_type: Optional[ImageType] = None,
        binning: Optional[str] = None,
        filter_name: Optional[str] = None,
        rlevel: Optional[int] = None,
    ) -> List[FrameInfo]:
        # build URL
        url = urllib.parse.urljoin(self._url, "frames/")

        # and params
        params = self._build_query(
            start, end, night, site, telescope, instrument, image_type, binning, filter_name, rlevel
        )

        # init list
        frames = []

        # set offset and limit
        params["offset"] = 0
        params["limit"] = 1000

        # open session
        async with aiohttp.ClientSession() as session:
            # loop until we got all
            while True:
                # do request
                async with session.get(url, params=params, headers=self._headers, timeout=10) as response:
                    if response.status != 200:
                        raise ValueError("Could not query frames")

                    # create frames and return them
                    res = await response.json()

                    # create frames
                    new_frames = [PyobsArchiveFrameInfo(frame) for frame in res["results"]]
                    frames.extend(new_frames)

                    # got all?
                    if len(frames) >= res["count"]:
                        return cast(List[FrameInfo], frames)

                    # get next chunk
                    params["offset"] += len(new_frames)

    @staticmethod
    def _build_query(
        start: Optional[Time] = None,
        end: Optional[Time] = None,
        night: Optional[str] = None,
        site: Optional[str] = None,
        telescope: Optional[str] = None,
        instrument: Optional[str] = None,
        image_type: Optional[ImageType] = None,
        binning: Optional[str] = None,
        filter_name: Optional[str] = None,
        rlevel: Optional[int] = None,
    ) -> Dict[str, Any]:
        # build params
        params: Dict[str, Any] = {}
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

    async def download_frames(self, infos: List[FrameInfo]) -> List[Image]:
        # loop infos
        images = []
        for info in infos:
            # make sure it's the correct FrameInfo
            if not isinstance(info, PyobsArchiveFrameInfo):
                log.warning("Incorrect type for frame info.")
                continue

            # download
            url = urllib.parse.urljoin(self._url, info.url)
            async with aiohttp.ClientSession() as session:
                async with session.get(url, headers=self._headers, timeout=60) as response:
                    if response.status != 200:
                        log.exception("Error downloading file %s.", info.filename)

                    # create image
                    try:
                        image = Image.from_bytes(await response.read())
                        images.append(image)
                    except OSError:
                        log.exception("Error downloading file %s.", info.filename)

        # return all
        return images

    async def download_headers(self, infos: List[PyobsArchiveFrameInfo]) -> List[Dict[str, Any]]:
        # loop infos
        headers = []
        for info in infos:
            # download
            url = urllib.parse.urljoin(self._url, info.url).replace("download", "headers")
            async with aiohttp.ClientSession() as session:
                async with session.get(url, headers=self._headers, timeout=60) as response:
                    if response.status != 200:
                        log.error("Could not fetch headers for %s.", info.filename)

                    try:
                        results = (await response.json())["results"]
                        headers.append(dict((d["key"], d["value"]) for d in results))
                    except KeyError:
                        log.error("Could not fetch headers for %s.", info.filename)
                        headers.append({})

        # return all
        return headers

    async def upload_frames(self, images: List[Image]) -> None:
        # build URL
        url = urllib.parse.urljoin(self._url, "frames/create/")

        # do some initial GET request for getting the csrftoken
        async with aiohttp.ClientSession() as session:
            # do some initial GET request for getting the csrftoken
            data = aiohttp.FormData()
            async with session.get(self._url, headers=self._headers) as response:
                token = response.cookies["csrftoken"].value
                data.add_field("csrfmiddlewaretoken", token)

            for i, img in enumerate(images, 1):
                # get filename
                filename = img.header["FNAME"]

                # write HDU to BytesIO
                with io.BytesIO() as bio:
                    # write it
                    img.writeto(bio)
                    data.add_field(f"file{i}", bio.getvalue(), filename=filename)

            # post it
            async with session.post(url, data=data, timeout=30, headers=self._headers) as response:
                # success, if status code is 200
                if response.status != 200:
                    raise ValueError("Cannot write file, received status_code %d." % response.status)

                # check json
                json = await response.json()
                if "created" not in json or json["created"] == 0:
                    if "errors" in json:
                        raise ValueError("Could not create file in archive: " + str(json["errors"]))
                    else:
                        raise ValueError("Could not create file in archive.")


__all__ = ["PyobsArchiveFrameInfo", "PyobsArchive"]
