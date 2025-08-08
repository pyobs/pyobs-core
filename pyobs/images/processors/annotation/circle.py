import logging
from typing import Any

from pyobs.images.processor import ImageProcessor
from pyobs.images import Image
from ._pillow import PillowHelper

log = logging.getLogger(__name__)


class Circle(ImageProcessor):
    """Draw a circle."""

    __module__ = "pyobs.images.processors.misc"

    def __init__(
        self,
        x: float | str,
        y: float | str,
        radius: float,
        fill: float | int | tuple[float | int, float | int, float | int] | None = None,
        outline: float | int | tuple[float | int, float | int, float | int] | None = None,
        width: int = 1,
        wcs: bool = False,
        **kwargs: Any,
    ):
        """Init a new grayscale processor.

        Args:
            x: Center x coordinate.
            y: Center y coordinate.
            radius: Radius.
            fill: Fill color.
            outline: Outline color.
            width: Width of line.
            wcs: Use WCS.
        """
        ImageProcessor.__init__(self, **kwargs)

        # store
        self._x = x
        self._y = y
        self._radius = radius
        self._fill = fill
        self._outline = outline
        self._width = width
        self._wcs = wcs

    async def __call__(self, image: Image) -> Image:
        """Drawn an ellipse on the image.

        Args:
            image: Image to draw on.

        Returns:
            Output image.
        """
        import PIL.ImageDraw

        im = PillowHelper.from_image(image)

        x, y = PillowHelper.position(image, self._x, self._y, self._wcs)
        radius = PillowHelper.value(image, self._radius)
        fill = PillowHelper.color(self._fill)
        outline = PillowHelper.color(self._outline)

        draw = PIL.ImageDraw.Draw(im)
        draw.circle([x, y], radius, fill=fill, outline=outline, width=self._width)

        return PillowHelper.to_image(image, im)


__all__ = ["Circle"]
