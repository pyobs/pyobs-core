import time
from collections import namedtuple
from threading import Lock
from typing import Any, Dict


class DataCacheEntry:
    """A single entry in the data cache."""

    def __init__(self, name: str, data: Any = None):
        """Create a new entry for the data cache

        Args:
            name: Name of item
            data: Data for this item or None.
        """
        self.name = name
        self._data = data
        self.time = time.time()

    def update(self) -> None:
        """Update time for this item."""
        self.time = time.time()

    @property
    def data(self) -> Any:
        """Update usage time and return data for entry."""

        # update time
        self.update()

        # return data
        return self._data


class DataCache(object):
    """Data cache for proxy server."""

    """Type for cache entries."""
    Entry = namedtuple("Entry", "time name data")

    def __init__(self, size: int = 20):
        """Init cache.

        Args:
            size: Cache size.
        """
        self._lock = Lock()
        self._cache: Dict[str, DataCacheEntry] = {}
        self._size = size

    def __contains__(self, name: str) -> bool:
        """Checks, whether entry is in cache.

        Args:
            name: Name of entry.

        Returns:
            Whether it exists in cache.
        """
        with self._lock:
            return name in self._cache

    def __getitem__(self, name: str) -> Any:
        """Returns data from entry in cache.

        Args:
            name: Name of data.

        Returns:
            Data from entry in cache.

        Raises:
            IndexError: If entry does not exists.
        """

        # return data or raise IndexError
        with self._lock:
            return self._cache[name].data

    def __setitem__(self, name: str, data: Any) -> None:
        """Set new entry in the cache.

        Args:
            name: Name for data to store.
            data: Date of file.
        """

        # lock cache
        with self._lock:
            # does it exist already?
            if name in self._cache:
                # delete it
                del self._cache[name]

            # create new entry
            self._cache[name] = DataCacheEntry(name, data)

            # check size
            if len(self._cache) > self._size:
                # sort cache values by update time
                cache = sorted(self._cache.values(), key=lambda x: x.time, reverse=True)

                # delete all elements except for the latest N
                for c in cache[self._size :]:
                    del self._cache[c.name]

    def __delitem__(self, name: str) -> None:
        """Delete entry in cache.

        Args:
            name: Name of entry to delete.
        """
        del self._cache[name]


__all__ = ["DataCache"]
