import importlib
import logging
import re
from typing import Any

from pyobs.images.processor import ImageProcessor
from pyobs.images import Image


log = logging.getLogger(__name__)


class AddFitsHeaders(ImageProcessor):
    """Add data to the FITS header."""

    __module__ = "pyobs.images.processors.misc"

    def __init__(self, headers: dict[str, int | float | str], **kwargs: Any):
        """Init a new FITS header processor.

        Args:
            headers: Dictionary of FITS headers.
        """
        ImageProcessor.__init__(self, **kwargs)

        # store
        self._headers = headers

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
        for key, value in self._headers.items():
            if isinstance(value, str):
                susbtitutes = re.findall(r"{.*?}", value)
                for sub in susbtitutes:
                    py = sub[1:-1]
                    res = eval(py, imports)
                    value = value.replace(sub, str(res))  # type: ignore

                    try:
                        value = int(value)
                    except ValueError:
                        try:
                            value = float(value)
                        except ValueError:
                            pass

                image.header[key] = value
            else:
                image.header[key] = value

        return image


__all__ = ["AddFitsHeaders"]
