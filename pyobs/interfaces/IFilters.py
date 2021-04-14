from typing import List

from .IMotion import IMotion


class IFilters(IMotion):
    __module__ = 'pyobs.interfaces'

    def list_filters(self, *args, **kwargs) -> List[str]:
        """List available filters.

        Returns:
            List of available filters.
        """
        raise NotImplementedError

    def set_filter(self, filter_name: str, *args, **kwargs):
        """Set the current filter.

        Args:
            filter_name: Name of filter to set.

        Raises:
            ValueError: If binning could not be set.
        """
        raise NotImplementedError

    def get_filter(self, *args, **kwargs) -> str:
        """Get currently set filter.

        Returns:
            Name of currently set filter.
        """
        raise NotImplementedError


__all__ = ['IFilters']
