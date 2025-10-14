from copy import copy
from typing import Any, Union, Dict

from astropy.coordinates import SkyCoord

from pyobs.images import Image
from pyobs.images.meta import SkyOffsets
from pyobs.images.processors.offsets import Offsets
from pyobs.object import get_object


class DummySkyOffsets(Offsets):
    """
    Attach a precomputed sky-coordinate offset to image metadata for testing or simple workflows.

    This processor constructs a :class:`SkyOffsets` object from two sky
    coordinates and attaches a copy of it to the image metadata via ``image.set_meta``.
    Coordinates can be provided directly as :class:`astropy.coordinates.SkyCoord`
    instances or as configuration dictionaries that are instantiated via
    :func:`pyobs.utils.classes.get_object`. Pixel data and FITS headers are not
    modified.

    :param SkyCoord | dict coord0: The reference sky position. Either a SkyCoord
                                   instance or a configuration dictionary that
                                   resolves to one via ``get_object``.
    :param SkyCoord | dict coord1: The target sky position. Either a SkyCoord
                                   instance or a configuration dictionary that
                                   resolves to one via ``get_object``.
    :param kwargs: Additional keyword arguments forwarded to
                   :class:`pyobs.images.processors.offsets.Offsets`.

    Behavior
    --------
    - Resolves ``coord0`` and ``coord1`` to :class:`SkyCoord` objects using
      :func:`get_object` if dictionaries are provided.
    - Constructs a :class:`SkyOffsets` instance representing the offset from
      ``coord0`` to ``coord1``.
    - Attaches a shallow copy of this SkyOffsets object to the image metadata with
      ``image.set_meta(...)``.
    - Returns the same image object; pixel data and header entries are unchanged.

    Input/Output
    ------------
    - Input: :class:`pyobs.images.Image`.
    - Output: :class:`pyobs.images.Image` with a ``SkyOffsets`` metadata entry set.

    Configuration (YAML)
    --------------------
    Provide coordinates as configuration dicts:

    .. code-block:: yaml

       class: pyobs.images.processors.offsets.DummySkyOffsets
       coord0:
         class: astropy.coordinates.SkyCoord
         ra: "10h00m00s"
         dec: "+20d00m00s"
         frame: icrs
       coord1:
         class: astropy.coordinates.SkyCoord
         ra: "10h00m30s"
         dec: "+20d00m00s"
         frame: icrs

    Notes
    -----
    - Frames and units of the provided SkyCoord objects determine the semantics of
      the SkyOffsets. Ensure both coordinates use compatible frames (e.g., ICRS).
    - This processor does not consult the image WCS or header; it simply stores the
      provided offset object in metadata.
    - A copy of the SkyOffsets is stored to avoid shared state across images.
    """

    __module__ = "pyobs.images.processors.offsets"

    def __init__(
        self, coord0: Union[SkyCoord, Dict[str, Any]], coord1: Union[SkyCoord, Dict[str, Any]], **kwargs: Any
    ) -> None:
        super().__init__(**kwargs)
        sky_coord0 = get_object(coord0, SkyCoord)
        sky_coord1 = get_object(coord1, SkyCoord)
        self._offset = SkyOffsets(sky_coord0, sky_coord1)

    async def __call__(self, image: Image) -> Image:
        image.set_meta(copy(self._offset))
        return image


__all__ = ["DummySkyOffsets"]
