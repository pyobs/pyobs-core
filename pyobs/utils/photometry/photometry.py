from astropy.table import Table

from pyobs.utils.images import Image


class Photometry:
    def __init__(self, *args, **kwargs):
        pass

    def find_stars(self, image: Image) -> Table:
        """Find stars in given image and append catalog.

        Args:
            image: Image to find stars in.

        Returns:
            Full table with results.
        """
        raise NotImplementedError


__all__ = ['Photometry']
