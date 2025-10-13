import logging
from typing import Any, Optional

from pyobs.images.processor import ImageProcessor
from pyobs.images import Image
from pyobs.utils.fits import FilenameFormatter


log = logging.getLogger(__name__)


class CreateFilename(ImageProcessor):
    """
    Format and set a filename for the image using a pattern, storing it in the FNAME header.

    This asynchronous processor uses a :class:`pyobs.utils.filenames.FilenameFormatter`
    to render a filename string from image metadata and writes it into the FITS header
    key ``FNAME`` on a copy of the image. If no pattern is provided, a built-in default
    pattern is used.

    The default pattern is:
    ``{SITEID}{TELID}-{INSTRUME}-{DAY-OBS|date:}-{FRAMENUM|string:04d}-{IMAGETYP|type}01.fits``

    This pattern typically expands to a string like:
    ``XXYY-CAM-20240130-0007-L101.fits``

    :param str | None pattern: A filename pattern understood by
                               :class:`pyobs.utils.filenames.FilenameFormatter`. If
                               ``None``, a default pattern is used. The pattern is a
                               template with placeholders of the form ``{KEY}`` or
                               ``{KEY|filter:params}``, where KEY is usually a FITS
                               header keyword and optional filters control formatting.
                               Common filters include:
                               - ``date:...``: format a date/time value (e.g., from
                                 ``DATE-OBS`` or ``DAY-OBS``) according to formatter
                                 defaults or supplied parameters.
                               - ``string:fmt``: format using a Python-style format
                                 specification (e.g., ``04d`` to zero-pad integers).
                               - ``type``: map image type values to standardized tokens.
                               See the FilenameFormatter documentation for the full set
                               of supported filters and parameters.
    :param kwargs: Additional keyword arguments forwarded to
                   :class:`pyobs.images.processor.ImageProcessor`.

    Behavior
    --------
    - Creates a :class:`FilenameFormatter` from the given pattern during initialization
      (or from the built-in default pattern if none was provided).
    - On call, creates a copy of the input image and invokes
      :meth:`Image.format_filename(formatter)` to compute the filename and store it in
      the FITS header under ``FNAME``.
    - Returns the modified copy; pixel data and other metadata remain unchanged.

    Input/Output
    ------------
    - Input: :class:`pyobs.images.Image` with FITS header fields referenced by the
      chosen pattern (e.g., ``SITEID``, ``TELID``, ``INSTRUME``, ``DAY-OBS`` or
      ``DATE-OBS``, ``FRAMENUM``, ``IMAGETYP``).
    - Output: :class:`pyobs.images.Image` (copied) with the ``FNAME`` header set to
      the formatted filename.

    Configuration (YAML)
    --------------------
    Use the default pattern:

    .. code-block:: yaml

       class: pyobs.images.processors.misc.CreateFilename
       pattern: null

    Custom pattern with zero-padded sequence and date:

    .. code-block:: yaml

       class: pyobs.images.processors.misc.CreateFilename
       pattern: "{SITEID}-{DAY-OBS|date:%Y%m%d}-{FRAMENUM|string:05d}.fits"

    Notes
    -----
    - Ensure the FITS header contains all keywords required by the pattern; otherwise
      the formatter may raise an error or leave fields empty, depending on its behavior.
    - The exact syntax and capabilities of filters (``date``, ``string``, ``type``,
      etc.) are defined by :class:`FilenameFormatter`.
    - This processor is asynchronous; call it within an event loop (using ``await``).
    """

    __module__ = "pyobs.images.processors.misc"

    _DEFAULT_PATTERN = "{SITEID}{TELID}-{INSTRUME}-{DAY-OBS|date:}-{FRAMENUM|string:04d}-{IMAGETYP|type}01.fits"

    def __init__(self, pattern: Optional[str], **kwargs: Any):
        """Init an image processor that adds a filename to an image.

        Args:
            pattern: Filename pattern.
        """
        ImageProcessor.__init__(self, **kwargs)

        if pattern is None:
            pattern = self._DEFAULT_PATTERN

        self._formatter = FilenameFormatter(pattern)

    async def __call__(self, image: Image) -> Image:
        """Add filename to image.

        Args:
            image: Image to add filename to.

        Returns:
            Image with filename in FNAME.
        """

        output_image = image.copy()
        output_image.format_filename(self._formatter)
        return output_image


__all__ = ["CreateFilename"]
