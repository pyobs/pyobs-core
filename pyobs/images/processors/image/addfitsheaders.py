import importlib
import logging
import re
from dataclasses import dataclass
from typing import Any

from pyobs.images.processor import ImageProcessor
from pyobs.images import Image


log = logging.getLogger(__name__)


@dataclass
class Keyword:
    key: str
    value: Any
    comment: str = ""
    overwrite: bool = True


class AddFitsHeaders(ImageProcessor):
    """
    Add or update FITS header keywords on an image.

    This processor inserts user-defined FITS header cards into a pyobs
    :class:`pyobs.images.Image`. It is typically used to attach observatory,
    instrument, or processing metadata (e.g., OBSERVAT, TELESCOP, FILTER)
    to images so they can be archived or analyzed with standard FITS-aware tools.

    :param dict|list headers:
        Header definitions to add. Can be provided as:

            - A mapping of ``KEY`` -> ``VALUE`` for simple additions.
            - A list of dictionaries for per-key options, each with:

              - ``key`` (str): FITS keyword name.
              - ``value`` (any): The value to set for the keyword.
              - ``comment`` (str, optional): A comment string to attach to the card.
              - ``overwrite`` (bool, optional): Override existing value for this key.
                If not given, the global ``overwrite`` setting applies.

    :param bool overwrite:
        Whether to overwrite existing keywords when they already exist in the header.
        Default: ``True``.

    Behavior
    --------
    - For each specified header card, the processor will add the keyword and value
      to the image's FITS header. If the keyword is already present:

      - If ``overwrite`` is ``True`` (globally or per-card), its value/comment
        will be replaced.
      - If ``overwrite`` is ``False``, the existing card will be left unchanged.

    - The output image’s data array is not modified.
    - FITS keyword names should follow FITS conventions (typically up to 8 ASCII
      characters, uppercase) to ensure compatibility with FITS tools.

    Input/Output
    ------------
    - Input: :class:`pyobs.images.Image`
    - Output: :class:`pyobs.images.Image` with updated FITS headers.

    Configuration (YAML)
    --------------------
    Simple mapping:

    .. code-block:: yaml

       class: pyobs.images.processors.image.addfitsheaders.AddFitsHeaders
       headers:
         OBSERVAT: "Example Observatory"
         TELESCOP: "1.2m RC"
         INSTRUME: "CCD Camera"
       overwrite: true

    Per-key options:

    .. code-block:: yaml

       class: pyobs.images.processors.image.addfitsheaders.AddFitsHeaders
       headers:
         - key: OBSERVER
           value: "Jane Doe"
           comment: "Observer name"
         - key: FILTER
           value: "R"
           comment: "Photometric filter"
           overwrite: false
       overwrite: true

    Examples
    --------
    - Add observatory and instrument metadata:

      .. code-block:: yaml

         class: pyobs.images.processors.image.addfitsheaders.AddFitsHeaders
         headers:
           OBSERVAT: "Example Observatory"
           INSTRUME: "CCD Camera"

    - Preserve existing FILTER value while updating other cards:

      .. code-block:: yaml

         class: pyobs.images.processors.image.addfitsheaders.AddFitsHeaders
         headers:
           - key: FILTER
             value: "R"
             overwrite: false
           - key: TELESCOP
             value: "1.2m RC"
         overwrite: true

    Notes
    -----
    - Be cautious when modifying orientation- or calibration-sensitive keywords
      (e.g., WCS-related keys); downstream tools may rely on their original values.
    - Values will be written as provided; ensure types are appropriate for FITS
      (strings, integers, floats, booleans, or FITS-compliant date strings).
    """

    __module__ = "pyobs.images.processors.image"

    def __init__(self, headers: dict[str, int | float | str] | list[Keyword], overwrite: bool = True, **kwargs: Any):
        """Init a new FITS header processor.

        Args:
            headers: Dictionary of FITS headers.
        """
        ImageProcessor.__init__(self, **kwargs)

        # store
        self._headers = headers
        self._overwrite = overwrite

    async def __call__(self, image: Image) -> Image:
        """Add data to the FITS header.

        Args:
            image: Image to add data to.

        Returns:
            New image.
        """
        # modules to import
        modules = ["astropy", "sunpy", "sunpy.coordinates"]
        imports = {}
        for m in modules:
            try:
                imports[m] = importlib.import_module(m)
            except ModuleNotFoundError:
                pass

        # loop all headers
        if isinstance(self._headers, list):
            for hdr in self._headers:
                self._set_header(image, imports, hdr.key, hdr.value, hdr.comment, hdr.overwrite and self._overwrite)
        elif isinstance(self._headers, dict):
            for key, value in self._headers.items():
                self._set_header(image, imports, key, value, None, self._overwrite)
        return image

    @staticmethod
    def _set_header(
        image: Image,
        imports: dict[Any, Any],
        key: str,
        value: Any,
        comment: str | None = None,
        overwrite: bool = True,
    ) -> None:
        if not overwrite and key in image.header:
            return

        if isinstance(value, str):
            substitutes = re.findall(r"{.*?}", value)
            for sub in substitutes:
                py = sub[1:-1]
                res = eval(py, imports)
                value = value.replace(sub, str(res))

                try:
                    value = int(value)
                except ValueError:
                    try:
                        value = float(value)
                    except ValueError:
                        pass
            image.header[key] = (value, comment)
        else:
            image.header[key] = (value, comment)


__all__ = ["AddFitsHeaders"]
