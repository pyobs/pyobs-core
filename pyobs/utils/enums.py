from enum import Enum


class ImageType(Enum):
    """Enumerator specifying the image type."""
    BIAS = 'bias'
    DARK = 'dark'
    OBJECT = 'object'
    SKYFLAT = 'skyflat'
    FOCUS = 'focus'
    ACQUISITION = 'acquisition'


__all__ = ['ImageType']
