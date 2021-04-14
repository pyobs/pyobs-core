from enum import Enum


class ExposureStatus(Enum):
    """Enumerator for camera status."""
    IDLE = 'idle'
    EXPOSING = 'exposing'
    READOUT = 'readout'
    ERROR = 'error'


class ImageType(Enum):
    """Enumerator specifying the image type."""
    BIAS = 'bias'
    DARK = 'dark'
    OBJECT = 'object'
    SKYFLAT = 'skyflat'
    FOCUS = 'focus'
    ACQUISITION = 'acquisition'


class ImageFormat(Enum):
    """Enumerator for image formats."""
    INT8 = 'int8'
    INT16 = 'int16'
    FLOAT32 = 'float32'
    FLOAT64 = 'float64'
    RGB24 = 'rgb24'


__all__ = ['ExposureStatus', 'ImageType', 'ImageFormat']
