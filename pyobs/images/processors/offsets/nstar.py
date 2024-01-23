import logging
from typing import Tuple, List, Union, Dict, Any, Optional
import numpy as np
import pandas as pd
from numpy import ndarray, dtype
from numpy.typing import NDArray
from photutils.psf import EPSFStar
from scipy import signal, optimize
from astropy.nddata import NDData
from astropy.table import Table, Column
import photutils

from pyobs.images import Image, ImageProcessor
from pyobs.mixins.pipeline import PipelineMixin
from pyobs.images.meta import PixelOffsets
from ._gaussian_fitter import GaussianFitter
from .offsets import Offsets

log = logging.getLogger(__name__)


class CorrelationMaxCloseToBorderError(Exception):
    pass


class NStarOffsets(Offsets, PipelineMixin):
    """An offset-calculation method based on comparing 2D images of the surroundings of a variable number of stars."""

    def __init__(
        self,
        num_stars: int = 10,
        max_offset: float = 4.0,
        min_pixels: int = 3,
        min_sources: int = 1,
        pipeline: Optional[List[Union[Dict[str, Any], ImageProcessor]]] = None,
        **kwargs: Any,
    ):
        """Initializes a new auto guiding system.

        Requires pyobs.images.processors.detection.SepSourceDetection and
        pyobs.images.processors.photometry.SepPhotometry to be run on the image beforehand.

        Args:
            num_stars: maximum number of stars to use to calculate offset from boxes around them
            max_offset: the maximal expected offset in arc seconds. Determines the size of boxes
                around stars.
            min_pixels: minimum required number of pixels above threshold for source to be
                used for offset calculation.
            min_sources: Minimum required number of sources in image.
            pipeline: Pipeline to be used for first image in series.
        """
        Offsets.__init__(self, **kwargs)
        PipelineMixin.__init__(self, pipeline)

        # store
        self.num_stars = num_stars
        self.max_offset = max_offset
        self.min_pixels = min_pixels
        self.min_sources = min_sources
        self.ref_boxes: List[EPSFStar] = []

    async def reset(self) -> None:
        """Resets guiding."""
        log.info("Reset auto-guiding.")
        self.ref_boxes = []

    async def __call__(self, image: Image) -> Image:
        """Processes an image and sets x/y pixel offset to reference in offset attribute.

        Args:
            image: Image to process.

        Returns:
            Original image.

        Raises:
            ValueError: If offset could not be found.
        """

        # no reference image?
        if len(self.ref_boxes) == 0:
            log.info("Initialising nstar auto-guiding with new image...")
            star_box_size = max(5, self._get_box_size(self.max_offset, image.pixel_scale))
            log.info(f"Choosing box size of {star_box_size} pixels.")

            # initialize reference image information
            try:
                # get boxes
                self.ref_boxes = await self._boxes_from_ref(image, star_box_size)

                # reset and finish
                image.set_meta(PixelOffsets(0.0, 0.0))
                return image

            except ValueError as e:
                # didn't work
                log.warning(f"Could not initialize reference image info due to exception '{e}'. Resetting...")
                await self.reset()
                if PixelOffsets in image.meta:
                    del image.meta[PixelOffsets]
                self.offset = None, None
                return image

        # process it
        log.info("Perform auto-guiding on new image...")
        offsets = self._calculate_offsets(image)
        if offsets[0] is not None:
            image.set_meta(PixelOffsets(offsets[0], offsets[1]))
        return image

    @staticmethod
    def _get_box_size(max_expected_offset_in_arcsec, pixel_scale) -> int:
        # multiply by 4 to give enough space for fit of correlation around the peak on all sides
        return int(4 * max_expected_offset_in_arcsec / pixel_scale if pixel_scale else 20)

    async def _boxes_from_ref(self, image: Image, star_box_size: int) -> List[EPSFStar]:
        """Calculate the boxes around self.N_stars best sources in the image.

        Args:
             image: Image to process

        Returns:
            2-tuple with
                list of dimensions of boxes in "numpy" order: [0'th axis min, 0'th axis max, 1st axis min, 1st axis max]
                list of images of those boxes

        Raises:
            ValueError if not at least max(self.min_required_sources_in_image, self.N_stars) in filtered list of sources
        """

        # run pipeline on 1st image
        img = await self.run_pipeline(image)

        # do photometry and get catalog
        sources = self._fits2numpy(img.catalog)

        # filter sources
        sources = self.remove_sources_close_to_border(sources, img.data.shape, star_box_size // 2 + 1)
        sources = self.remove_bad_sources(sources)
        self._check_sources_count(sources)
        selected_sources = self._select_brightest_sources(self.num_stars, sources)

        # extract boxes
        return photutils.psf.extract_stars(
            NDData(img.data.astype(float)), selected_sources, size=star_box_size
        ).all_stars

    @staticmethod
    def _fits2numpy(sources: Table) -> Table:
        """Convert from FITS to numpy conventions for pixel coordinates."""
        for k in ["x", "y", "xmin", "xmax", "ymin", "ymax", "xpeak", "ypeak"]:
            if k in sources.keys():
                sources[k] -= 1
        return sources

    @staticmethod
    def remove_sources_close_to_border(sources: Table, image_shape: Tuple[int, int], min_dist: float) -> Table:
        """Remove table rows from sources when source is closer than given distance from border of image.

        Args:
            sources: Input table.
            image_shape: Shape of image.
            min_dist: Minimum distance from border in pixels.

        Returns:
            Filtered table.
        ."""

        width, height = image_shape

        x_dist_from_border = width / 2 - np.abs(sources["y"] - width / 2)
        y_dist_from_border = height / 2 - np.abs(sources["x"] - height / 2)

        min_dist_from_border = np.minimum(x_dist_from_border, y_dist_from_border)
        sources_result = sources[min_dist_from_border > min_dist]

        return sources_result

    def remove_bad_sources(
        self, sources: Table, max_ellipticity: float = 0.4, min_bkg_factor: float = 1.5, saturation: int = 50000
    ) -> Table:
        """Remove bad sources from table.

        Args:
            sources: Input table.
            max_ellipticity: Maximum ellipticity.
            min_bkg_factor: Minimum factor above local background.
            saturation: Saturation level.

        Returns:
            Filtered table.
        """

        # remove saturated sources
        sources = sources[sources["peak"] < saturation]

        # remove small sources
        sources = sources[sources["tnpix"] >= self.min_pixels]

        # remove large sources
        tnpix_median = np.median(sources["tnpix"])
        tnpix_std = np.std(sources["tnpix"])
        sources = sources[sources["tnpix"] <= tnpix_median + 2 * tnpix_std]

        # remove highly elliptic sources
        sources.sort("ellipticity")
        sources = sources[sources["ellipticity"] <= max_ellipticity]

        # remove sources with background <= 0
        sources = sources[sources["background"] > 0]

        # remove sources with low contrast to background
        sources = sources[(sources["peak"] + sources["background"]) / sources["background"] > min_bkg_factor]
        return sources

    @staticmethod
    def _select_brightest_sources(num_stars: int, sources: Table) -> Table:
        """Select N brightest sources from table.

        Args:
            num_stars: Maximum number of stars to select.
            sources: Source table.

        Returns:
            New table containing N brightest sources.
        """

        sources.sort("flux",  reverse=True)

        # extract
        if 0 < num_stars < len(sources):
            sources = sources[:num_stars]
        return sources

    def _check_sources_count(self, sources: Table) -> None:
        """Check if enough sources in table.

        Args:
            sources: astropy table of sources to check.

        Returns:
            None

        Raises:
            ValueError if not at least self.min_sources in sources table

        """

        if len(sources) < self.min_sources:
            raise ValueError(f"Only {len(sources)} source(s) in image, but at least {self.min_sources} required.")

    def _calculate_offsets(self, image: Image) -> Tuple[Optional[float], Optional[float]]:
        """Calculate offsets of given image to ref image for every star.

        Args:
            image: Image to calculate offset for.

        Returns:
            Offset tuple.
        """

        # data?
        if image.safe_data is None:
            return None, None

        # calculate offset for each star
        offsets = []
        for box in self.ref_boxes:
            # get box dimensions
            box_ymin, box_ymax = box.origin[1], box.origin[1] + box.data.shape[0]
            box_xmin, box_xmax = box.origin[0], box.origin[0] + box.data.shape[1]

            # extract box image
            current_boxed_image = image.data[box_ymin:box_ymax, box_xmin:box_xmax].astype(float)

            # correlate
            corr = signal.correlate2d(current_boxed_image, box.data, mode="same", boundary="wrap")

            try:
                offset = GaussianFitter.offsets_from_corr(corr)
                offsets.append(offset)
            except Exception as e:
                log.info(f"Exception '{e}' caught. Ignoring this star.")
                pass

        if len(offsets) == 0:
            log.info(f"All {self.num_stars} fits on boxed star correlations failed.")
            return None, None
        offsets_np = np.array(offsets)
        return float(np.mean(offsets_np[:, 0])), float(np.mean(offsets_np[:, 1]))

__all__ = ["NStarOffsets"]
