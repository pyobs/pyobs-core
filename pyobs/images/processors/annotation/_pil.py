import logging
import PIL.Image
import numpy as np
from astropy.wcs import WCS

from pyobs.images import Image


log = logging.getLogger(__name__)


def from_image(image: Image) -> PIL.Image.Image:
    data = image.data
    if image.is_color:
        data = np.moveaxis(data, 0, -1)
    return PIL.Image.fromarray(data)


def to_image(image: Image, im: PIL.Image.Image) -> Image:
    out = image.copy()
    out.data = np.array(im)
    if image.is_color:
        out.data = np.moveaxis(out.data, 2, 0)
    return out


def position(image: Image, x: float, y: float, wcs: bool) -> tuple[float, float]:
    if wcs:
        w = WCS(image.header)
        return w.all_world2pix(x, y, 1)
    else:
        return x, y


__all__ = ["from_image", "to_image"]
