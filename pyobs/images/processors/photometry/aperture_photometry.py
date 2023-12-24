import asyncio
import logging

from pyobs.images import Image
from pyobs.images.processors.photometry import Photometry
from pyobs.images.processors.photometry._photometry_calculator import _PhotometryCalculator

log = logging.getLogger(__name__)


class AperturePhotometry(Photometry):
    APERTURE_RADII = range(1, 9)

    def __init__(self, calculator: _PhotometryCalculator, **kwargs):
        self._calculator = calculator
        super().__init__(**kwargs)

    async def __call__(self, image: Image) -> Image:
        """Do aperture photometry on given image.

                Args:
                    image: Image to do aperture photometry on.

                Returns:
                    Image with attached catalog.
                """

        if image.data is None:
            log.warning("No data found in image.")
            return image

        if image.pixel_scale is None:
            log.warning("No pixel scale provided by image.")
            return image

        if image.catalog is None:
            log.warning("No catalog found in image.")
            return image

        self._calculator.set_data(image)

        loop = asyncio.get_running_loop()
        await loop.run_in_executor(None, self._photometry)

        output_image = image.copy()
        output_image.catalog = self._calculator.catalog
        return output_image

    def _photometry(self) -> None:
        for diameter in self.APERTURE_RADII:
            self._calculator(diameter)
