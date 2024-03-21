import logging
from abc import ABCMeta
from typing import List, Dict, Tuple, Any, Optional

from pyobs.interfaces import IDome
from pyobs.utils import exceptions as exc
from .baseroof import BaseRoof


log = logging.getLogger(__name__)


class BaseDome(IDome, BaseRoof, metaclass=ABCMeta):
    """Base class for domes."""

    __module__ = "pyobs.modules.roof"

    def __init__(self, **kwargs: Any):
        """Initialize a new base dome."""
        BaseRoof.__init__(self, **kwargs)

        exc.register_exception(exc.MotionError, 3, timespan=600, callback=self._default_remote_error_callback)

    async def get_fits_header_before(
        self, namespaces: Optional[List[str]] = None, **kwargs: Any
    ) -> Dict[str, Tuple[Any, str]]:
        """Returns FITS header for the current status of this module.

        Args:
            namespaces: If given, only return FITS headers for the given namespaces.

        Returns:
            Dictionary containing FITS headers.
        """

        hdr = await BaseRoof.get_fits_header_before(self, namespaces, **kwargs)

        _, az = await self.get_altaz()
        hdr["ROOF-AZ"] = (az, "Azimuth of roof slit, deg E of N")
        return hdr


__all__ = ["BaseDome"]
