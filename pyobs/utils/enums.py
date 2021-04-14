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


class MotionStatus(Enum):
    """Enumerator for moving device status:
        - PARKED means that the device needs to be initialized or positioned or
          moved (depending upon the device; some devices don't need a formal
          initialization); presumedly, this is the safe "off" state.
        - INITIALIZING means that the device is transitioning from a PARKED state
          to an active state but is not yet fully operable.
        - unPARKED is either IDLE (operating but in no particular state) or
          POSITIONED (operating in a well-defined state)
        - SLEWING means that the device is moving to some targeted state (e.g.
          to POSITIONED or TRACKING) but has not yet arrived at that state
        - TRACKING means that the device is moving as commanded
    """
    ABORTING = 'aborting'
    ERROR = 'error'
    IDLE = 'idle'
    INITIALIZING = 'initializing'
    PARKING = 'parking'
    PARKED = 'parked'
    POSITIONED = 'positioned'
    SLEWING = 'slewing'
    TRACKING = 'tracking'
    UNKNOWN = 'unknown'


__all__ = ['ExposureStatus', 'ImageType', 'ImageFormat', 'MotionStatus']
