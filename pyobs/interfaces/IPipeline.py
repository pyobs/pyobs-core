from pyobs.utils.time import Time
from .interface import *


class IPipeline(Interface):
    def reduce_range(self, start: Time, end: Time, *args, **kwargs):
        """Reduces all data within a given range of time.

        Args:
            start: Start of time range.
            end: End of time range.
        """
        raise NotImplementedError


__all__ = ['IPipeline']
