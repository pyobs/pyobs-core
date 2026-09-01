import glob
import logging
from pathlib import Path
from typing import Any

import pandas as pd
from astropy.io import fits
from pydantic import PrivateAttr

from pyobs.images import Image
from pyobs.utils.enums import ImageType
from pyobs.utils.exptime_grouping import exptimes_close
from pyobs.utils.time import Time

from .archive import Archive, FrameInfo

log = logging.getLogger(__name__)


class LocalArchive(Archive):
    """Connector class to a local image archive."""

    root: str

    _root_path: Path = PrivateAttr()
    _data: pd.DataFrame = PrivateAttr(default_factory=pd.DataFrame)

    model_config = {"arbitrary_types_allowed": True}

    def model_post_init(self, __context: Any) -> None:
        self._root_path = Path(self.root)
        self._data = pd.DataFrame()
        self._update_root()

    def _update_root(self) -> None:
        """Update files in root directory."""
        filenames = sorted(glob.glob(str(self._root_path / "*.fits")))
        columns: dict[str, Any] = {
            h: []
            for h in [
                "date-obs",
                "day-obs",
                "binning",
                "filter",
                "image_type",
                "instrument",
                "site",
                "telescope",
                "rlevel",
                "obsnum",
                "exptime",
            ]
        }
        for filename in filenames:
            hdr = fits.getheader(filename)
            columns["date-obs"].append(Time(hdr["DATE-OBS"]) if "DATE-OBS" in hdr else None)
            columns["day-obs"].append(Time(hdr["DAY-OBS"]) if "DAY-OBS" in hdr else None)
            columns["binning"].append(f"{hdr['XBINNING']}x{hdr['YBINNING']}" if "XBINNING" in hdr else None)
            columns["filter"].append(hdr["FILTER"] if "FILTER" in hdr else None)
            columns["image_type"].append(hdr["IMAGETYP"] if "IMAGETYP" in hdr else None)
            columns["instrument"].append(hdr["INSTRUME"] if "INSTRUME" in hdr else None)
            columns["site"].append(hdr["SITEID"] if "SITEID" in hdr else None)
            columns["telescope"].append(hdr["TELID"] if "TELID" in hdr else None)
            columns["rlevel"].append(hdr["RLEVEL"] if "RLEVEL" in hdr else None)
            columns["obsnum"].append(str(hdr["OBSNUM"]) if "OBSNUM" in hdr else None)
            columns["exptime"].append(float(hdr["EXPTIME"]) if "EXPTIME" in hdr else None)
        columns["filename"] = filenames
        self._data = pd.DataFrame(columns)

    def _filter_data(
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
        obsnum: str | None = None,
        exptime: float | None = None,
    ) -> pd.DataFrame:
        data = self._data
        if start is not None:
            data = data[data["date-obs"] > start]
        if end is not None:
            data = data[data["date-obs"] < end]
        if night is not None:
            data = data[data["day-obs"] == night]
        if site is not None:
            data = data[data["site"] == site]
        if telescope is not None:
            data = data[data["telescope"] == telescope]
        if instrument is not None:
            data = data[data["instrument"] == instrument]
        if image_type is not None:
            data = data[data["image_type"] == image_type]
        if binning is not None:
            data = data[data["binning"] == binning]
        if filter_name is not None:
            data = data[data["filter"] == filter_name]
        if rlevel is not None:
            data = data[data["rlevel"] == rlevel]
        if obsnum is not None:
            data = data[data["obsnum"] == obsnum]
        if exptime is not None:
            data = data[data["exptime"].apply(lambda e: e is not None and exptimes_close(e, exptime))]
        return data

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
        obsnum: str | None = None,
        exptime: float | None = None,
    ) -> dict[str, list[Any]]:
        data = self._filter_data(
            start,
            end,
            night,
            site,
            telescope,
            instrument,
            image_type,
            binning,
            filter_name,
            rlevel,
            obsnum=obsnum,
            exptime=exptime,
        )
        return {
            "binnings": list(data["binning"].unique()),
            "filters": list(data["filter"].unique()),
            "imagetypes": list(data["image_type"].unique()),
            "instruments": list(data["instrument"].unique()),
            "sites": list(data["site"].unique()),
            "telescopes": list(data["telescope"].unique()),
            "exptimes": [e for e in data["exptime"].unique() if e is not None],
        }

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
        obsnum: str | None = None,
        exptime: float | None = None,
    ) -> list[FrameInfo]:
        data = self._filter_data(
            start,
            end,
            night,
            site,
            telescope,
            instrument,
            image_type,
            binning,
            filter_name,
            rlevel,
            obsnum=obsnum,
            exptime=exptime,
        )
        infos: list[FrameInfo] = []
        for _, row in data.iterrows():
            info = FrameInfo()
            info.id = row["filename"]
            info.filename = row["filename"]
            info.filter_name = row["filter"]
            info.binning = row["binning"]
            info.dateobs = row["date-obs"]
            info.exptime = row["exptime"]
            infos.append(info)
        return infos

    async def download_frames(self, frames: list[FrameInfo]) -> list[Image]:
        images: list[Image] = []
        for frame in frames:
            if frame.filename is not None:
                images.append(Image.from_file(frame.filename))
        return images

    async def download_headers(self, infos: list[FrameInfo]) -> list[dict[str, Any]]:
        headers = []
        for frame in infos:
            headers.append({k: v for k, v in fits.getheader(frame.filename).items()})
        return headers

    async def upload_frames(self, images: list[Image]) -> None:
        self._root_path.mkdir(parents=True, exist_ok=True)
        for image in images:
            filename = image.header.get("FNAME")
            if not filename:
                raise ValueError("Image has no FNAME header set, cannot determine output filename.")
            image.writeto(str(self._root_path / filename), overwrite=True)
        self._update_root()  # refresh the in-memory index so newly-written frames are queryable


__all__ = ["LocalArchive"]
