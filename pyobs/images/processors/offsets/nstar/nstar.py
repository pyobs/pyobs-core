import logging
from typing import Tuple, List, Union, Dict, Any, Optional

import numpy as np
from photutils.psf import EPSFStar
from scipy import signal

from pyobs.images import Image, ImageProcessor
from pyobs.images.meta import PixelOffsets
from pyobs.images.processors.offsets.nstar._box_generator import _BoxGenerator
from pyobs.images.processors.offsets.nstar._gaussian_fitter import GaussianFitter
from pyobs.images.processors.offsets.offsets import Offsets
from pyobs.mixins.pipeline import PipelineMixin

log = logging.getLogger(__name__)


class CorrelationMaxCloseToBorderError(Exception):
    pass


class NStarOffsets(Offsets, PipelineMixin):
    """An offset-calculation method based on comparing 2D images of the surroundings of a variable number of stars."""

    def __init__(
            self,
            max_pixel_offset: float = 5.0,
            min_sources: int = 1,
            pipeline: Optional[List[Union[Dict[str, Any], ImageProcessor]]] = None,
            **kwargs: Any,
    ):
        """Initializes an offset calculator.

        Args:
            num_stars: maximum number of stars to use to calculate offset from boxes around them
            max_pixel_offset: the maximal expected pixel offset. Determines the size of boxes around stars.
            min_pixels: minimum required number of pixels for a source to be used for offset calculation.
            min_sources: Minimum required number of sources in image.
            pipeline: Pipeline to be used for first image in series.
        """
        Offsets.__init__(self, **kwargs)
        PipelineMixin.__init__(self, pipeline)

        # store
        self._box_size = max_pixel_offset
        self._box_generator = _BoxGenerator(max_pixel_offset, min_sources=min_sources)
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

        output_image = image.copy()

        if self._boxes_initialized():
            log.info("Initialising NStar offsets with new image...")
            try:
                await self._init_boxes(output_image)
                output_image.set_meta(PixelOffsets(0.0, 0.0))
            except ValueError as e:
                log.warning(f"Could not initialize reference image info due to exception '{e}'. Resetting...")
                await self.reset()
                if PixelOffsets in output_image.meta:
                    del output_image.meta[PixelOffsets]

        else:
            log.info("Perform auto-guiding on new image...")
            offsets = self._calculate_offsets(output_image)
            if offsets[0] is not None and offsets[1] is not None:
                output_image.set_meta(PixelOffsets(offsets[0], offsets[1]))

        return output_image

    def _boxes_initialized(self) -> bool:
        return len(self.ref_boxes) == 0

    async def _init_boxes(self, image: Image) -> None:
        processed_image = await self.run_pipeline(image)
        self.ref_boxes = self._box_generator(processed_image)

    def _calculate_offsets(self, image: Image) -> Tuple[Optional[float], Optional[float]]:
        """Calculate offsets of given image to ref image for every star.

        Args:
            image: Image to calculate offset for.

        Returns:
            Offset in x and y dimension.
        """

        if (image_data := image.safe_data) is None:
            return None, None

        offsets = np.fromiter(
            filter(
                lambda x: x is not None,
                map(lambda x: NStarOffsets._calculate_star_offset(x, image_data), self.ref_boxes)
            ),
            np.dtype((float, 2))
        )

        if len(offsets) == 0:
            log.info(f"All {len(self.ref_boxes)} fits on boxed star correlations failed.")
            return None, None

        return float(np.mean(offsets[:, 0])), float(np.mean(offsets[:, 1]))

    @staticmethod
    def _calculate_star_offset(box: EPSFStar, image: np.ndarray) -> Optional[Tuple[float, float]]:
        current_boxed_image = image[box.slices]

        corr = signal.correlate2d(current_boxed_image, box.data, mode="same", boundary="wrap")

        try:
            return GaussianFitter.offsets_from_corr(corr)
        except Exception as e:
            log.info(f"Exception '{e}' caught. Ignoring this star.")
            return None


__all__ = ["NStarOffsets"]
