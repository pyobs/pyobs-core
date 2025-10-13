from typing import Any

from .offsets import Offsets
from pyobs.images import Image
from pyobs.object import get_class_from_string


class DummyOffsets(Offsets):
    """
    Attach a dummy offset metadata entry using a class resolved from its name, for testing or simple workflows.

    This asynchronous processor resolves an offset class from a string and instantiates
    it with the same offset value for both components, then attaches the instance to
    the image metadata via ``image.set_meta(...)``. Typical use cases include testing
    pipelines that consume offsets (e.g., PixelOffsets, AltAzOffsets) without running
    a full measurement procedure. Pixel data and FITS headers are not modified.

    :param str offset_class: The name of the offset class to instantiate. Must be
                             resolvable by ``get_class_from_string`` and refer to a
                             class whose constructor accepts two numeric positional
                             arguments (e.g., ``dx, dy``). Examples include
                             ``pyobs.images.processors.offsets.PixelOffsets`` or
                             ``pyobs.images.processors.offsets.AltAzOffsets``.
    :param float offset: The numeric value to use for both components of the offset
                         (e.g., dx = dy = offset). Units depend on the chosen class
                         (pixels for PixelOffsets, arcseconds for AltAzOffsets).
                         Default: ``1.0``.
    :param kwargs: Additional keyword arguments forwarded to
                   :class:`pyobs.images.processors.offsets.Offsets`.

    Behavior
    --------
    - Resolves ``offset_class`` to a class object using
      :func:`pyobs.utils.classes.get_class_from_string`.
    - Instantiates the class with ``(offset, offset)`` and attaches the resulting
      object to the image via ``image.set_meta(...)``.
    - Returns the same image object; pixel data and FITS headers remain unchanged.

    Input/Output
    ------------
    - Input: :class:`pyobs.images.Image`.
    - Output: :class:`pyobs.images.Image` with a metadata entry set to the instantiated
      offset object.

    Configuration (YAML)
    --------------------
    Set dummy pixel offsets of +1 pixel on both axes:

    .. code-block:: yaml

       class: pyobs.images.processors.offsets.DummyOffsets
       offset_class: "pyobs.images.processors.offsets.PixelOffsets"
       offset: 1.0

    Set dummy Alt/Az offsets of +2.5 arcseconds on both axes:

    .. code-block:: yaml

       class: pyobs.images.processors.offsets.DummyOffsets
       offset_class: "pyobs.images.processors.offsets.AltAzOffsets"
       offset: 2.5

    Notes
    -----
    - The meaning and units of ``offset`` depend on the chosen class. Ensure
      consistency with downstream modules that consume the metadata.
    - This processor is intended for testing or simple workflows; for measured offsets,
      use dedicated processors that compute offsets from catalogs, WCS, or other data.
    """

    def __init__(self, offset_class: str, offset: float = 1.0, **kwargs: Any) -> None:
        super().__init__(**kwargs)

        self._offset = offset
        self._offset_class = get_class_from_string(offset_class)

    async def __call__(self, image: Image) -> Image:
        image.set_meta(self._offset_class(self._offset, self._offset))
        return image


__all__ = ["DummyOffsets"]
