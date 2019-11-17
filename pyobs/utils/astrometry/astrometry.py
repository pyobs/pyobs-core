from pyobs.utils.images import Image


class Astrometry:
    def __init__(self, *args, **kwargs):
        pass

    def __call__(self, image: Image):
        raise NotImplementedError


__all__ = ['Astrometry']
