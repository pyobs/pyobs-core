from pyobs.utils.images import Image


class Photometry:
    def __call__(self, image: Image):
        raise NotImplementedError


__all__ = ['Photometry']
