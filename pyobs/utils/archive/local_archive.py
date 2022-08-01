import glob
from pathlib import Path
from typing import List, Dict, Any, Optional
import logging

import pandas as pd
from astropy.io import fits

from pyobs.utils.time import Time
from pyobs.images import Image
from pyobs.utils.archive import Archive, FrameInfo
from pyobs.utils.enums import ImageType

log = logging.getLogger(__name__)


class LocalArchive(Archive):
    """Connector class to a local image archive."""

    __module__ = "pyobs.utils.archive"

    def __init__(self, root: str, **kwargs: Any):
        self._root = Path(root)
        self._data = pd.DataFrame()
        self._update_root()

    def _update_root(self):
        """Update files in root directory."""

        # init lists
        filenames = sorted(glob.glob(str(self._root / "*.fits")))
        columns = {
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
            ]
        }

        # loop files
        for filename in filenames:
            # load header
            hdr = fits.getheader(filename)

            # store it
            columns["date-obs"].append(Time(hdr["DATE-OBS"]) if "DATE-OBS" in hdr else None)
            columns["day-obs"].append(Time(hdr["DAY-OBS"]) if "DAY-OBS" in hdr else None)
            columns["binning"].append(f"{hdr['XBINNING']}x{hdr['YBINNING']}" if "XBINNING" in hdr else None)
            columns["filter"].append(hdr["FILTER"] if "FILTER" in hdr else None)
            columns["image_type"].append(hdr["IMAGETYP"] if "IMAGETYP" in hdr else None)
            columns["instrument"].append(hdr["INSTRUME"] if "INSTRUME" in hdr else None)
            columns["site"].append(hdr["SITEID"] if "SITEID" in hdr else None)
            columns["telescope"].append(hdr["TELID"] if "TELID" in hdr else None)
            columns["rlevel"].append(hdr["RLEVEL"] if "RLEVEL" in hdr else None)

        # init df
        columns["filename"] = filenames
        self._data = pd.DataFrame(columns)

    def _filter_data(
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
    ) -> pd.DataFrame:
        """Filter data"""

        # filter
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
            data = data[data["image_type"] == image_type.value]
        if binning is not None:
            data = data[data["binning"] == binning]
        if filter_name is not None:
            data = data[data["filter"] == filter_name]
        if rlevel is not None:
            data = data[data["rlevel"] == rlevel]
        return data

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
        """Returns a list of options restricted to the given parameters.

        Args:
            start: Start time for restriction.
            end: End time for restriction.
            night: Images in given night.
            site: From given site.
            telescope: From given telescope.
            instrument: From given instrument.
            image_type: With given image type.
            binning: With given binning.
            filter_name: With given filter.
            rlevel: In given reduction level.

        Returns:
            Dictionary with lists of "binnings", "filters", "imagetypes", "instruments", "sites", and "telescopes".
        """

        # filter
        data = self._filter_data(
            start, end, night, site, telescope, instrument, image_type, binning, filter_name, rlevel
        )

        # return results
        return {
            "binnings": data["binning"].unique(),
            "filters": data["filter"].unique(),
            "imagetypes": data["image_type"].unique(),
            "instruments": data["instrument"].unique(),
            "sites": data["site"].unique(),
            "telescopes": data["telescope"].unique(),
        }

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
        """Returns a list of frames restricted to the given parameters.

        Args:
            start: Start time for restriction.
            end: End time for restriction.
            night: Images in given night.
            site: From given site.
            telescope: From given telescope.
            instrument: From given instrument.
            image_type: With given image type.
            binning: With given binning.
            filter_name: With given filter.
            rlevel: In given reduction level.

        Returns:
            List of frames.
        """

        # filter
        data = self._filter_data(
            start, end, night, site, telescope, instrument, image_type, binning, filter_name, rlevel
        )

        # create list of FrameInfos
        infos: List[FrameInfo] = []
        for _, row in data.iterrows():
            info = FrameInfo()
            info.id = row["filename"]
            info.filename = row["filename"]
            info.filter_name = row["filter"]
            info.binning = row["binning"]
            info.dateobs = row["date-obs"]
            infos.append(info)
        return infos

    async def download_frames(self, frames: List[FrameInfo]) -> List[Image]:
        """Download given frames.

        Args:
            frames: List of frames to download.

        Returns:
            List of Image objects.
        """

        # load frames
        images = []
        for frame in frames:
            images.append(Image.from_file(frame.filename))
        return images

    async def download_headers(self, infos: List[FrameInfo]) -> List[Dict[str, Any]]:
        """Download given headers.

        Args:
            infos: List of frames to download.

        Returns:
            List of dicts with headers.
        """

        # load frames
        headers = []
        for frame in infos:
            headers.append({k: v for k, v in fits.getheader(frame.filename).items()})
        return headers

    async def upload_frames(self, images: List[Image]) -> None:
        pass


__all__ = ["LocalArchive"]
