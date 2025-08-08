import logging
import PIL.Image
import numpy as np

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


__all__ = ["from_image", "to_image"]
