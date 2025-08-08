import logging
from typing import Any

from pyobs.images.processor import ImageProcessor
from pyobs.images import Image
from ._pil import PILHelper

log = logging.getLogger(__name__)


class Crosshair(ImageProcessor):
    """Draw a crosshair."""

    __module__ = "pyobs.images.processors.misc"

    def __init__(
        self,
        x: float,
        y: float,
        radius: float,
        color: float | int | tuple[float | int, float | int, float | int] | None = None,
        wcs: bool = False,
        **kwargs: Any,
    ):
        """Init a new crosshair processor.

        Args:
            x: Center x coordinate.
            y: Center y coordinate.
            radius: Radius.
            color: Fill color.
            wcs: Use WCS for position.
        """
        ImageProcessor.__init__(self, **kwargs)

        # store
        self._x = x
        self._y = y
        self._radius = radius
        self._color = color
        self._wcs = wcs

    async def __call__(self, image: Image) -> Image:
        """Drawn a crosshair on the image.

        Args:
            image: Image to draw on.

        Returns:
            Output image.
        """
        import PIL.ImageDraw

        im = PILHelper.from_image(image)
        x, y = PILHelper.position(image, self._x, self._y, self._wcs)

        draw = PIL.ImageDraw.Draw(im)
        width = int(self._radius / 10.0)
        draw.circle([x, y], self._radius, outline=self._color, width=width)
        draw.line([(x - self._radius, y), (x + self._radius), y], self._color, width=width)
        draw.line([(x, y - self._radius), (x, y + self._radius)], self._color, width=width)

        return PILHelper.to_image(image, im)


__all__ = ["Crosshair"]
