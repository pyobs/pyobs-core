import logging
from typing import Any

from pyobs.images.processor import ImageProcessor
from pyobs.images import Image
from ._pillow import PillowHelper

log = logging.getLogger(__name__)


class Crosshair(ImageProcessor):
    """
    Draw a crosshair (circle plus orthogonal lines) on an image, optionally using WCS coordinates.

    This processor uses Pillow to render a crosshair symbol on a
    :class:`pyobs.images.Image`. The crosshair consists of a circular outline of the given
    ``radius`` centered at ``(x, y)`` and horizontal/vertical lines crossing the center,
    each extending to the circle’s radius. The center coordinates may be specified in pixel
    space or, if ``wcs=True``, interpreted as world coordinates and transformed to pixels
    via the image’s WCS.

    :param float x: X coordinate of the crosshair center. If ``wcs=True``, interpreted as a
                    world-coordinate value and converted to pixel coordinates.
    :param float y: Y coordinate of the crosshair center. Same rules as for ``x``.
    :param float radius: Crosshair radius in pixels. Determines both the circle size and the
                         half-length of the crosshair lines.
    :param float | int | tuple[float | int, float | int, float | int] | None color:
        Color used for the circle outline and the crosshair lines. Can be a single-channel
        value (grayscale) or a 3-tuple (RGB). If ``None``, the library’s default color is used.
        Default: ``None``.
    :param bool wcs: If ``True``, interpret ``x`` and ``y`` as world coordinates and convert
                     them to pixel coordinates using the image’s WCS. Default: ``False``.
    :param kwargs: Additional keyword arguments forwarded to
                   :class:`pyobs.images.processor.ImageProcessor`.

    Behavior
    --------
    - Converts the input to a Pillow image via :class:`pyobs.utils.image.PillowHelper.from_image`.
    - Resolves the center position with ``PillowHelper.position(image, x, y, wcs)`` and the color
      with ``PillowHelper.color(color)``.
    - Draws:
      - A circle centered at ``(x, y)`` with radius ``radius`` and outline ``color``.
      - A horizontal line from ``x - radius`` to ``x + radius`` at ``y``.
      - A vertical line from ``y - radius`` to ``y + radius`` at ``x``.
    - The line width is set to ``int(radius / 10.0)``.
    - Converts the Pillow image back to a :class:`pyobs.images.Image` via
      ``PillowHelper.to_image(image, im)``.

    Input/Output
    ------------
    - Input: :class:`pyobs.images.Image`
    - Output: :class:`pyobs.images.Image` (copied) with the crosshair drawn onto the pixel data.

    Configuration (YAML)
    --------------------
    Pixel coordinates:

    .. code-block:: yaml

       class: pyobs.images.processors.misc.Crosshair
       x: 250
       y: 300
       radius: 40
       color: [255, 255, 0]   # yellow

    WCS coordinates for the center (requires valid WCS in the image):

    .. code-block:: yaml

       class: pyobs.images.processors.misc.Crosshair
       x: 150.1234          # example RA/longitude-like value resolvable by PillowHelper
       y: -20.5678          # example Dec/latitude-like value resolvable by PillowHelper
       radius: 25
       color: [0, 255, 0]
       wcs: true

    Notes
    -----
    - When ``wcs=True``, only ``x`` and ``y`` are interpreted in world coordinates; ``radius``
      is treated as a pixel length.
    - Color representation and supported coordinate/value formats depend on
      :class:`pyobs.utils.image.PillowHelper`.
    - The line width scales with radius and is not independently configurable.
    """

    __module__ = "pyobs.images.processors.annotation"

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

        im = PillowHelper.from_image(image)
        x, y = PillowHelper.position(image, self._x, self._y, self._wcs)
        color = PillowHelper.color(self._color)

        draw = PIL.ImageDraw.Draw(im)
        width = int(self._radius / 10.0)
        draw.circle([x, y], self._radius, outline=color, width=width)  # type: ignore
        draw.line([(x - self._radius, y), (x + self._radius), y], color, width=width)  # type: ignore
        draw.line([(x, y - self._radius), (x, y + self._radius)], color, width=width)  # type: ignore

        return PillowHelper.to_image(image, im)


__all__ = ["Crosshair"]
