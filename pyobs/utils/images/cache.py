import time
from threading import Lock
from typing import Dict

from pyobs.utils.images import Image


class ImageCacheItem:
    """A single item in the image cache."""

    def __init__(self, name: str, image: Image = None):
        """Create a new item for the image cache

        Args:
            name: Name of item
            image: Image for this item or None.
        """
        self.name = name
        self._image = image
        self.time = time.time()

    def update(self):
        """Update time for this item."""
        self.time = time.time()

    @property
    def image(self) -> Image:
        """Update usage time and return image for item."""

        # update time
        self.update()

        # return image
        return self._image


class ImageCache:
    """Cache for images."""

    def __init__(self, size: int = 20):
        """Initializes new image cache.

        Args:
            size: Maximum size of cache.
        """
        self._lock = Lock()
        self._size = size
        self._cache: Dict[str, ImageCacheItem] = {}

    def __contains__(self, item: str) -> bool:
        """Checks, whether item is in cache.

        Args:
            item: Name of image.

        Returns:
            Whether it exists in cache.
        """
        with self._lock:
            return item in self._cache

    def __getitem__(self, item: str):
        """Returns item from cache.

        Args:
            item: Name of image.

        Returns:
            Item from cache.

        Raises:
            IndexError if item does not exists.
        """

        # return image from cache item or raise IndexError, if it doesn't exist
        with self._lock:
            return self._cache[item].image

    def __setitem__(self, item: str, image: Image):
        """Puts an image into the cache.

        Args:
            item: Name of new cache item.
            image: New image.
        """

        # lock cache
        with self._lock:
            # does it exist already?
            if item in self._cache:
                # delete it
                del self._cache[item]

            # create new entry
            self._cache[item] = ImageCacheItem(item, image)

            # check size
            if len(self._cache) > self._size:
                # sort cache values by update time
                cache = sorted(self._cache.values(), key=lambda c: c.time, reverse=True)

                # delete all elements except for the latest N
                for c in cache[self._size:]:
                    del self._cache[c.name]

    def __delitem__(self, item: str):
        """Delete item from cache.

        Args:
            item: Name of item to delete
        """
        with self._lock:
            del self._cache[item]


__all__ = ['ImageCache']
