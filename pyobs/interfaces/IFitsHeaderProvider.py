from typing import List, Dict, Tuple, Any

from .interface import *


class IFitsHeaderProvider(Interface):
    def get_fits_headers(self, namespaces: List[str] = None, *args, **kwargs) -> Dict[str, Tuple[Any, str]]:
        """Returns FITS header for the current status of this module.

        Args:
            namespaces: If given, only return FITS headers for the given namespaces.

        Returns:
            Dictionary containing FITS headers.
        """
        raise NotImplementedError


__all__ = ['IFitsHeaderProvider']
