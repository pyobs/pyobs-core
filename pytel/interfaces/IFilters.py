from .interface import *


class IFilters(Interface):
    def list_filters(self, *args, **kwargs) -> list:
        """List available filters.

        Returns:
            List of available filters.
        """
        raise NotImplementedError

    def set_filter(self, filter_name: str, *args, **kwargs) -> bool:
        """Set the current filter.

        Args:
            filter_name: Name of filter to set.

        Returns:
            Success or not.
        """
        raise NotImplementedError

    def get_filter(self, *args, **kwargs) -> str:
        """Get currently set filter.

        Returns:
            Name of currently set filter.
        """
        raise NotImplementedError


__all__ = ['IFilters']
