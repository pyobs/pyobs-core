from copy import copy
from typing import Any, Union, Dict

from astropy.coordinates import SkyCoord

from pyobs.images import Image
from pyobs.images.meta import SkyOffsets
from pyobs.images.processors.offsets import Offsets
from pyobs.object import get_object


class DummySkyOffsets(Offsets):
    def __init__(self, coord0: Union[SkyCoord, Dict[str, Any]], coord1: Union[SkyCoord, Dict[str, Any]], **kwargs: Any) -> None:
        super().__init__(**kwargs)
        sky_coord0 = get_object(coord0, SkyCoord)
        sky_coord1 = get_object(coord1, SkyCoord)
        self._offset = SkyOffsets(sky_coord0, sky_coord1)

    async def __call__(self, image: Image) -> Image:
        image.set_meta(copy(self._offset))
        return image


__all__ = ["DummySkyOffsets"]
