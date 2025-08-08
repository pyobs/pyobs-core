import logging
from typing import Any

from pyobs.images.processor import ImageProcessor
from pyobs.images import Image
from ._pil import from_image, to_image

log = logging.getLogger(__name__)


class Circle(ImageProcessor):
    """Draw a circle."""

    __module__ = "pyobs.images.processors.misc"

    def __init__(
        self,
        x: float,
        y: float,
        radius: float,
        fill: float | int | tuple[float | int, float | int, float | int] | None = None,
        outline: float | int | tuple[float | int, float | int, float | int] | None = None,
        width: int = 1,
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
        """
        ImageProcessor.__init__(self, **kwargs)

        # store
        self._x = x
        self._y = y
        self._radius = radius
        self._fill = fill
        self._outline = outline
        self._width = width

    async def __call__(self, image: Image) -> Image:
        """Drawn an ellipse on the image.

        Args:
            image: Image to draw on.

        Returns:
            Output image.
        """
        import PIL.ImageDraw

        im = from_image(image)

        draw = PIL.ImageDraw.Draw(im)
        draw.circle([self._x, self._y], self._radius, fill=self._fill, outline=self._outline, width=self._width)

        return to_image(image, im)


__all__ = ["Circle"]
