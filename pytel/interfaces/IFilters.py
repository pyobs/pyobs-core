from .interface import *


class IFilters(Interface):
    def list_filters(self, *args, **kwargs) -> list:
        """returns a list of all filters"""
        raise NotImplementedError

    def set_filter(self, filter_name: str, *args, **kwargs) -> bool:
        """sets current filter"""
        raise NotImplementedError

    def get_filter(self, *args, **kwargs) -> str:
        """returns current filter"""
        raise NotImplementedError


__all__ = ['IFilters']
