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
    """Add data to the FITS header."""

    __module__ = "pyobs.images.processors.misc"

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
