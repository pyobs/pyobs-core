import logging
from typing import Any

from pyobs.images.processor import ImageProcessor
from pyobs.images import Image
from ._pillow import PillowHelper

log = logging.getLogger(__name__)


class Text(ImageProcessor):
    """Draw text on an image."""

    __module__ = "pyobs.images.processors.misc"

    def __init__(
        self,
        x: float,
        y: float,
        text: str,
        font: str | None = None,
        font_size: float = 10,
        fill: float | int | tuple[float | int, float | int, float | int] | None = None,
        anchor: str | None = None,
        spacing: int = 4,
        align: str = "left",
        direction: str | None = None,
        wcs: bool = False,
        **kwargs: Any,
    ):
        """Init a new grayscale processor.

        Args:
            x: Center x coordinate.
            y: Center y coordinate.
            text: Text to draw.
            font: Font to use.
            font_size: Text size.
            fill: Fill color.
            anchor: Text anchor alignment.
            spacing: Number of pixels between lines.
            align: Text alignment.
            direction: Text direction.
            wcs: Use WCS.
        """
        import PIL.ImageFont

        ImageProcessor.__init__(self, **kwargs)

        # store
        self._x = x
        self._y = y
        self._text = text
        self._fill = fill
        self._anchor = anchor
        self._spacing = spacing
        self._align = align
        self._direction = direction
        self._wcs = wcs

        # font
        self._font_size = font_size
        self._font = None
        if font is not None:
            self._font = PIL.ImageFont.truetype(font, font_size)

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
        fill = PillowHelper.color(self._fill)
        try:
            text = self._text.format(**image.header)
        except KeyError:
            text = self._text

        draw = PIL.ImageDraw.Draw(im)
        draw.text(
            (x, y),
            text,
            fill=fill,  # type: ignore
            font=self._font,
            anchor=self._anchor,
            spacing=self._spacing,
            align=self._align,
            direction=self._direction,
            font_size=self._font_size,
        )

        return PillowHelper.to_image(image, im)


__all__ = ["Text"]
