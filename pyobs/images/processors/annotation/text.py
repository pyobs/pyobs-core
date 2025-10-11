import logging
from typing import Any

from pyobs.images.processor import ImageProcessor
from pyobs.images import Image
from ._pillow import PillowHelper

log = logging.getLogger(__name__)


class Text(ImageProcessor):
    """
    Draw text on an image at a specified position, optionally using WCS coordinates and header-based formatting.

    This asynchronous processor uses Pillow to render text onto a
    :class:`pyobs.images.Image`. The text string may include Python ``str.format``
    placeholders that are filled from the image’s FITS header. The position can be
    given in pixel coordinates or, if ``wcs=True``, interpreted as world coordinates
    and converted to pixels using the image’s WCS, if available.

    :param float x: X coordinate for the text anchor position. If ``wcs=True``, interpreted
                    as a world-coordinate value and converted to pixel coordinates.
    :param float y: Y coordinate for the text anchor position. Same rules as for ``x``.
    :param str text: The text to render. Supports Python format fields referencing
                     header keys, e.g., ``"{OBJECT} {FILTER}"``.
    :param str font: Optional path to a TrueType font file. If provided, the font is loaded
                     via ``PIL.ImageFont.truetype(font, font_size)``. Default: ``None``.
    :param float font_size: Font size in points for the TrueType font; if no font is provided,
                            the size may be applied via Pillow’s ``draw.text`` where supported.
                            Default: ``10``.
    :param float | int | tuple[float | int, float | int, float | int] | None fill:
        Text fill color. Can be a single-channel value (grayscale) or a 3-tuple (RGB).
        If ``None``, Pillow’s default color is used. Default: ``None``.
    :param str anchor: Text anchor alignment (e.g., ``"la"``, ``"mm"``). See Pillow’s documentation
                       for valid values and semantics. Default: ``None``.
    :param int spacing: Number of pixels between lines when ``text`` contains newlines. Default: ``4``.
    :param str align: Multiline text alignment; one of ``"left"``, ``"center"``, ``"right"``.
                      Default: ``"left"``.
    :param str direction: Text direction; e.g., ``"ltr"`` (left-to-right), ``"rtl"`` (right-to-left),
                          or ``"ttb"`` (top-to-bottom), if supported by Pillow. Default: ``None``.
    :param bool wcs: If ``True``, interpret ``x`` and ``y`` as world coordinates and convert
                     to pixel coordinates using the image’s WCS. Default: ``False``.
    :param kwargs: Additional keyword arguments forwarded to
                   :class:`pyobs.images.processor.ImageProcessor`.

    Behavior
    --------
    - Converts the input image to a Pillow image via :class:`pyobs.utils.image.PillowHelper.from_image`.
    - Resolves the position with ``PillowHelper.position(image, x, y, wcs)`` and the fill color with
      ``PillowHelper.color(fill)``.
    - Attempts to format ``text`` using ``self._text.format(**image.header)``; if a placeholder key
      is missing, falls back to the original ``self._text`` without formatting.
    - If ``font`` was provided, loads a TrueType font with the specified ``font_size``; otherwise,
      uses Pillow’s default font. The call to ``draw.text`` includes the configured parameters
      (fill, font, anchor, spacing, align, direction, font_size).
    - Converts the Pillow image back to a :class:`pyobs.images.Image` with
      ``PillowHelper.to_image(image, im)``.

    Input/Output
    ------------
    - Input: :class:`pyobs.images.Image`
    - Output: :class:`pyobs.images.Image` (copied) with the text drawn onto the pixel data.

    Configuration (YAML)
    --------------------
    Draw static text in pixel coordinates:

    .. code-block:: yaml

       class: pyobs.images.processors.misc.Text
       x: 50
       y: 40
       text: "Hello, world!"
       fill: [255, 255, 255]   # white
       align: "left"

    Use FITS header fields in the text:

    .. code-block:: yaml

       class: pyobs.images.processors.misc.Text
       x: 10
       y: 20
       text: "{OBJECT}  {FILTER}  exp={EXPTIME}s"
       fill: [255, 255, 0]     # yellow

    Specify a TrueType font and size:

    .. code-block:: yaml

       class: pyobs.images.processors.misc.Text
       x: 100
       y: 100
       text: "Center"
       font: "/usr/share/fonts/truetype/DejaVuSans.ttf"
       font_size: 14
       anchor: "mm"            # center the text at (x, y)

    Use WCS coordinates for placement (requires valid WCS):

    .. code-block:: yaml

       class: pyobs.images.processors.misc.Text
       x: 150.1234
       y: -20.5678
       text: "{OBJECT}"
       wcs: true
       fill: [0, 255, 0]

    Notes
    -----
    - Header-based formatting uses Python’s ``str.format`` mechanism with ``image.header`` as
      the source of values. Missing keys are ignored and the unformatted text is used.
    - Color representation and supported value formats depend on :class:`pyobs.utils.image.PillowHelper`.
    - The ``anchor`` option controls how the text is positioned relative to ``(x, y)``; refer to
      Pillow’s documentation for the available anchor codes.
    - If no font is provided, Pillow’s default font is used. When a TrueType font is specified,
      ``font_size`` sets the size at loading time; some Pillow versions may also support a
      ``font_size`` parameter to ``draw.text``.
    - This processor is asynchronous; use it within an event loop (``await``).
    """

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
