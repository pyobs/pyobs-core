import asyncio
import logging
from functools import partial
from typing import Union, List, Optional, Any, Dict
import numpy as np
import astropy.units as u

from pyobs.mixins.pipeline import PipelineMixin
from pyobs.object import Object
from pyobs.utils.archive import Archive
from pyobs.utils.enums import ImageType
from pyobs.images import Image, ImageProcessor
from pyobs.utils.time import Time

log = logging.getLogger(__name__)


class Pipeline(Object, PipelineMixin):
    """Pipeline based on the astropy package ccdproc."""

    def __init__(self, steps: List[Union[Dict[str, Any], ImageProcessor]], **kwargs: Any):
        """Pipeline for science images.

        Args:
            steps: List of pipeline steps to perform.
        """
        Object.__init__(self, **kwargs)
        PipelineMixin.__init__(self, steps)

    @staticmethod
    def _combine_calib_images(
        images: List[Image], bias: Optional[Image] = None, normalize: bool = False, method: str = "average"
    ) -> Image:
        """Combine a list of given images.

        Args:
            images: List of images to combine.
            bias: If given, subtract from images before combining them.
            normalize: If True, images are normalized to median of 1 before and after combining them.
            method: Method for combining images.
        """
        import ccdproc

        # get CCDData objects
        data = [image.to_ccddata() for image in images]

        # subtract bias?
        if bias is not None:
            bias_data = bias.to_ccddata()
            data = [ccdproc.subtract_bias(d, bias_data) for d in data]

        # normalize?
        if normalize:
            data = [d.divide(np.median(d.data), handle_meta="first_found") for d in data]

        # combine image
        combined = ccdproc.combine(
            data,
            method=method,
            sigma_clip=True,
            sigma_clip_low_thresh=5,
            sigma_clip_high_thresh=5,
            mem_limit=350e6,
            unit="adu",
            combine_uncertainty_function=np.ma.std,
        )

        # normalize?
        if normalize:
            combined = combined.divide(np.median(combined.data), handle_meta="first_found")

        # to Image and copy header
        image = Image.from_ccddata(combined)

        # add history
        for i, src in enumerate(images, 1):
            basename = src.header["FNAME"].replace(".fits.fz", "").replace(".fits", "")
            image.header["L1AVG%03d" % i] = (basename, "Image used for average")
        image.header["RLEVEL"] = (1, "Reduction level")

        # finished
        return image

    async def _combine_calib_images_async(self, images: List[Image], **kwargs: Any) -> Image:
        return await asyncio.get_running_loop().run_in_executor(
            None, partial(self._combine_calib_images, images, **kwargs)
        )

    async def create_master_bias(self, images: List[Image]) -> Image:
        """Create master bias frame.

        Args:
            images: List of raw bias frames.

        Returns:
            Master bias frame.
        """
        return await self._combine_calib_images_async(images)

    async def create_master_dark(self, images: List[Image], bias: Image) -> Image:
        """Create master dark frame.

        Args:
            images: List of raw dark frames.
            bias: Bias frame to subtract from images.

        Returns:
            Master dark frame.
        """
        return await self._combine_calib_images_async(images, bias=bias)

    async def create_master_flat(self, images: List[Image], bias: Image) -> Image:
        """Create master flat frame.

        Args:
            images: List of raw flat frames.
            bias: Bias frame to subtract from images.

        Returns:
            Master flat frame.
        """
        return await self._combine_calib_images_async(images, bias=bias, normalize=True, method="median")

    async def calibrate(self, image: Image) -> Image:
        """Calibrate a single science frame.

        Args:
            image: Image to calibrate.

        Returns:
            Calibrated image.
        """

        # copy image
        calibrated = image.copy()

        # run pipeline
        return await self.run_pipeline(calibrated)

    @staticmethod
    async def find_master(
        archive: Archive,
        image_type: ImageType,
        time: Time,
        instrument: str,
        binning: str,
        filter_name: Optional[str] = None,
        max_days: float = 30.0,
    ) -> Optional[Image]:
        """Find and download master calibration frame.

        Args:
            archive: Image archive.
            image_type: Image type.
            time: Time to search at.
            instrument: Instrument to use.
            binning: Used binning.
            filter_name: Used filter.
            max_days: Maximum number of days from DATE-OBS to find frames.

        Returns:
            FrameInfo for master calibration frame or None.
        """

        # find reduced frames from +- N days
        log.info(
            "Searching for %s %s master calibration frames%s from instrument %s.",
            binning,
            image_type.value,
            "" if filter_name is None else " in " + filter_name,
            instrument,
        )
        infos = await archive.list_frames(
            start=time - max_days * u.day,
            end=time + max_days * u.day,
            instrument=instrument,
            image_type=image_type,
            binning=binning,
            filter_name=filter_name,
            rlevel=1,
        )

        # found none?
        if len(infos) == 0:
            log.warning("Could not find any matching %s calibration frames.", image_type.value)
            return None

        # sort by diff to time and take first
        s = sorted(infos, key=lambda i: abs((i.dateobs - time).sec))
        info = s[0]
        log.info("Found %s frame %s.", image_type.name, info.filename)

        # download it
        data = await archive.download_frames([info])
        return data[0]


__all__ = ["Pipeline"]
