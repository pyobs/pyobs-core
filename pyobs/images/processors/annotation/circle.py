import logging
from typing import Any

from pyobs.images.processor import ImageProcessor
from pyobs.images import Image
from ._pillow import PillowHelper

log = logging.getLogger(__name__)


class Circle(ImageProcessor):
    """
    Draw a circle on an image, optionally interpreting the center in WCS coordinates.

    This asynchronous processor uses Pillow to render a circle on a
    :class:`pyobs.images.Image`. The center coordinates ``(x, y)`` and the ``radius``
    can be provided as numbers or strings that are resolved by
    :class:`pyobs.utils.image.PillowHelper`. If ``wcs=True``, the center coordinates
    are interpreted in world coordinates (e.g., sky coordinates) and converted to
    pixel coordinates using the image’s WCS, if available.

    :param float | str x: X coordinate of the circle center. May be a numeric pixel position
                          or a string that PillowHelper can resolve (e.g., a symbolic/relative
                          specification). If ``wcs=True``, interpreted as a world-coordinate value.
    :param float | str y: Y coordinate of the circle center. Same rules as for ``x``.
    :param float radius: Circle radius. Resolved via PillowHelper to a pixel value.
    :param float | int | tuple[float | int, float | int, float | int] | None fill:
        Fill color for the circle interior. Can be a single-channel value (grayscale)
        or a 3-tuple (RGB). If ``None``, the interior is not filled. Default: ``None``.
    :param float | int | tuple[float | int, float | int, float | int] | None outline:
        Outline color for the circle boundary. Same type rules as ``fill``. If ``None``,
        no outline is drawn. Default: ``None``.
    :param int width: Outline line width in pixels. Default: ``1``.
    :param bool wcs: If ``True``, interpret ``x`` and ``y`` as world coordinates and convert
                     to pixel coordinates using the image’s WCS. Default: ``False``.
    :param kwargs: Additional keyword arguments forwarded to
                   :class:`pyobs.images.processor.ImageProcessor`.

    Behavior
    --------
    - Converts the input image to a Pillow image using :class:`pyobs.utils.image.PillowHelper`.
    - Resolves ``x``, ``y`` via ``PillowHelper.position(image, x, y, wcs)`` and ``radius`` via
      ``PillowHelper.value(image, radius)``.
    - Converts ``fill`` and ``outline`` to Pillow-compatible color values via
      ``PillowHelper.color(...)``.
    - Draws the circle using ``PIL.ImageDraw.Draw.circle([x, y], radius, fill=..., outline=..., width=...)``.
    - Converts the result back to a :class:`pyobs.images.Image` with
      ``PillowHelper.to_image(image, im)``.
    - If both ``fill`` and ``outline`` are ``None``, the rendered output will be unchanged.

    Input/Output
    ------------
    - Input: :class:`pyobs.images.Image`
    - Output: :class:`pyobs.images.Image` (copied) with the circle drawn onto the pixel data.

    Configuration (YAML)
    --------------------
    Draw a red outlined circle:

    .. code-block:: yaml

       class: pyobs.images.processors.misc.Circle
       x: 100
       y: 150
       radius: 50
       outline: [255, 0, 0]
       width: 3

    Fill a green circle with no outline:

    .. code-block:: yaml

       class: pyobs.images.processors.misc.Circle
       x: 200
       y: 300
       radius: 30
       fill: [0, 255, 0]
       outline: null

    Use WCS for the center (requires valid WCS in the image header):

    .. code-block:: yaml

       class: pyobs.images.processors.misc.Circle
       x: "10:00:00"     # example world-coordinate string resolvable by PillowHelper
       y: "+20:00:00"
       radius: 20
       wcs: true
       outline: [255, 255, 0]

    Notes
    -----
    - Coordinate and value resolution depend on PillowHelper; supported string formats
      and semantics are defined there. If a value cannot be resolved, an exception may be raised.
    - When ``wcs=True``, only ``x`` and ``y`` are interpreted in world coordinates; ``radius`` is
      resolved to a pixel value (no angular conversion is applied).
    - Color values typically use 0–255 per channel for 8-bit images; PillowHelper handles
      mapping for different dtypes/layouts.
    - This processor is asynchronous; call it within an event loop (using ``await``).
    """

    __module__ = "pyobs.images.processors.annotation"

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
        """Init a new circle processor.

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
        """Draws a circle on the image.

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
        draw.circle([x, y], radius, fill=fill, outline=outline, width=self._width)  # type: ignore

        return PillowHelper.to_image(image, im)


__all__ = ["Circle"]
