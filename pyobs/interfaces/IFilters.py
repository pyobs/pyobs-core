from typing import List, Any

from .IMotion import IMotion


class IFilters(IMotion):
    """The module can change filters in a device."""
    __module__ = 'pyobs.interfaces'

    def list_filters(self, **kwargs: Any) -> List[str]:
        """List available filters.

        Returns:
            List of available filters.
        """
        raise NotImplementedError

    def set_filter(self, filter_name: str, **kwargs: Any) -> None:
        """Set the current filter.

        Args:
            filter_name: Name of filter to set.

        Raises:
            ValueError: If binning could not be set.
        """
        raise NotImplementedError

    def get_filter(self, **kwargs: Any) -> str:
        """Get currently set filter.

        Returns:
            Name of currently set filter.
        """
        raise NotImplementedError


__all__ = ['IFilters']
