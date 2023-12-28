from typing import Any

from .offsets import Offsets
from pyobs.images import Image
from pyobs.object import get_class_from_string


class DummyOffsets(Offsets):
    def __init__(self, offset_class: str, offset: float = 1.0, **kwargs: Any) -> None:
        super().__init__(**kwargs)

        self._offset = offset
        self._offset_class = get_class_from_string(offset_class)

    async def __call__(self, image: Image) -> Image:
        image.set_meta(self._offset_class(self._offset, self._offset))
        return image


__all__ = ["DummyOffsets"]
