import logging
from typing import cast

import PIL.Image
import numpy as np
from astropy.wcs import WCS

from pyobs.images import Image


log = logging.getLogger(__name__)


class PillowHelper:
    @staticmethod
    def from_image(image: Image) -> PIL.Image.Image:
        data = image.data
        if image.is_color:
            data = np.moveaxis(data, 0, -1)
        return PIL.Image.fromarray(data)

    @staticmethod
    def to_image(image: Image, im: PIL.Image.Image) -> Image:
        out = image.copy()
        out.data = np.array(im)
        if image.is_color:
            out.data = np.moveaxis(out.data, 2, 0)
        return out

    @staticmethod
    def value(image: Image, value: float | int | str) -> float | int:
        if isinstance(value, str):
            return image.header[value]  # type: ignore
        return value

    @staticmethod
    def position(image: Image, x: float | str, y: float | str, wcs: bool) -> tuple[float, float]:
        x = PillowHelper.value(image, x)
        y = PillowHelper.value(image, y)

        if wcs:
            w = WCS(image.header)
            return cast(tuple[float, float], w.all_world2pix(x, y, 1))
        else:
            return x, y

    @staticmethod
    def color(
        color: float | int | tuple[float | int, float | int, float | int] | None,
    ) -> float | int | tuple[float | int, float | int, float | int] | None:
        return tuple(color) if isinstance(color, list) else color


__all__ = ["PillowHelper"]
