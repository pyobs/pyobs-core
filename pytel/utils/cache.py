import time
from collections import namedtuple


class DataCache(object):
    """Data cache for proxy server."""

    """Type for cache entries."""
    Entry = namedtuple('Entry', 'time name data')

    def __init__(self, size: int = 20):
        """Init cache.

        Args:
            size: Cache size.
        """
        self._entries = []
        self._size = size

    def __setitem__(self, name: str, data: bytearray):
        """Set new item in the cache.

        Args:
            name: Name for data to store.
            data: Date of file.
        """

        # append
        self._entries.append(DataCache.Entry(time.time(), name, data))

        # too many entries?
        if len(self._entries) > self._size:
            # sort by time diff
            now = time.time()
            self._entries.sort(key=lambda e: now - e.time)

            # pick first
            self._entries = self._entries[:self._size]

    def __getitem__(self, name: str) -> bytearray:
        """Retrieve data from the cache.

        Args:
            name: Name for data to retrieve.

        Returns:
            The requested data.

        Raises:
            IndexError: If data does not exist.
        """

        # loop entries in cache and return data if found.
        for e in self._entries:
            if e.name == name:
                return e.data

        # nothing found, so raise exception
        raise IndexError

    def __contains__(self, name):
        """Whether cache contains data of given name.

        Args:
            name: Name of data to check.

        Returns:
            Whether it exists.
        """

        # loop entries and return True, if name was found
        for e in self._entries:
            if e.name == name:
                return True

        # name not found, return False
        return False


__all__ = ['DataCache']
