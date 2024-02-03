import logging
from typing import Tuple, List, Union, Dict, Any, Optional
import numpy as np
from photutils.psf import EPSFStar
from scipy import signal
from astropy.nddata import NDData
from astropy.table import Table
import photutils

from pyobs.images import Image, ImageProcessor
from pyobs.images.processors.offsets.nstar._box_generator import _BoxGenerator
from pyobs.mixins.pipeline import PipelineMixin
from pyobs.images.meta import PixelOffsets
from pyobs.images.processors.offsets.nstar._gaussian_fitter import GaussianFitter
from pyobs.images.processors.offsets.offsets import Offsets

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
        """Initializes an offset calculator.

        Args:
            num_stars: maximum number of stars to use to calculate offset from boxes around them
            max_offset: the maximal expected offset in arc seconds. Determines the size of boxes
                around stars.
            min_pixels: minimum required number of pixels for a source to be used for offset calculation.
            min_sources: Minimum required number of sources in image.
            pipeline: Pipeline to be used for first image in series.
        """
        Offsets.__init__(self, **kwargs)
        PipelineMixin.__init__(self, pipeline)

        # store
        self.max_offset = max_offset
        self._box_generator = _BoxGenerator(num_stars=num_stars, min_pixels=min_pixels, min_sources=min_sources)
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
            log.info("Initialising NStar offsets with new image...")
            star_box_size = max(5, self._get_box_size(self.max_offset, image.pixel_scale))
            log.info(f"Choosing box size of {star_box_size} pixels.")

            # initialize reference image information
            try:
                processed_image = await self.run_pipeline(image)
                self.ref_boxes = self._box_generator(processed_image, star_box_size)

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

    def _calculate_offsets(self, image: Image) -> Tuple[Optional[float], Optional[float]]:
        """Calculate offsets of given image to ref image for every star.

        Args:
            image: Image to calculate offset for.

        Returns:
            Offset in x and y dimension.
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
            log.info(f"All {len(self.ref_boxes)} fits on boxed star correlations failed.")
            return None, None
        offsets_np = np.array(offsets)
        return float(np.mean(offsets_np[:, 0])), float(np.mean(offsets_np[:, 1]))


__all__ = ["NStarOffsets"]
