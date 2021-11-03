from typing import List, Dict, Tuple, Any, Optional

from .interface import Interface


class IFitsHeaderBefore(Interface):
    """The module provides some additional header entries for FITS headers."""
    __module__ = 'pyobs.interfaces'

    def get_fits_header_before(self, namespaces: Optional[List[str]] = None, **kwargs: Any) -> Dict[str, Tuple[Any, str]]:
        """Returns FITS header for the current status of this module.

        Args:
            namespaces: If given, only return FITS headers for the given namespaces.

        Returns:
            Dictionary containing FITS headers.
        """
        raise NotImplementedError


__all__ = ['IFitsHeaderBefore']
