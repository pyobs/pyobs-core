from pyobs.utils.images import Image


class Astrometry:
    def __call__(self, image: Image):
        raise NotImplementedError


__all__ = ['Astrometry']
