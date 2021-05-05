"""
TODO: write doc
"""
__title__ = 'Enumerations'

from enum import Enum


class ExposureStatus(Enum):
    """Enumerator for camera status.

    Attributes:
        IDLE: Camera is idle, i.e. ready for work.
        EXPOSING: Camera is currently exposing.
        READOUT: Camera is currently reading out.
        ERROR: Camera is in error state.
    """
    IDLE = 'idle'
    EXPOSING = 'exposing'
    READOUT = 'readout'
    ERROR = 'error'


class ImageType(Enum):
    """Enumerator specifying the image type.

    Attributes:
        BIAS: Bias/zero exposure.
        DARK: Dark exposure.
        OBJECT: Object/science exposure
        SKYFLAT: Flat-field taken on sky.
        FOCUS: Exposure from a focus-series.
        ACQUISITION: Exposure from an acquisition
    """
    BIAS = 'bias'
    DARK = 'dark'
    OBJECT = 'object'
    SKYFLAT = 'skyflat'
    FOCUS = 'focus'
    ACQUISITION = 'acquisition'


class ImageFormat(Enum):
    """Enumerator for image formats.

    Attributes:
        INT8: 8 bit integer (i.e. byte).
        INT16: 16 bit integer (i.e. short).
        FLOAT32: 32 bit float.
        FLOAT64: 64 bit float (i.e. double).
        RGB24: RGB format with 8 bit for each colour.
    """
    INT8 = 'int8'
    INT16 = 'int16'
    FLOAT32 = 'float32'
    FLOAT64 = 'float64'
    RGB24 = 'rgb24'


class MotionStatus(Enum):
    """Enumerator for moving device status.

    Attributes:
        PARKED: The device needs to be initialized or positioned or
            oved (depending upon the device; some devices don't need a formal
            initialization); presumedly, this is the safe "off" state.
        INITIALIZING: The device is transitioning from a PARKED state
            to an active state but is not yet fully operable.
        IDLE: Operating but in no particular state.
        POSITIONED: Operating in a well-defined state, but not moving.
        SLEWING: The device is moving to some targeted state (e.g. to POSITIONED or TRACKING) but has not yet
            arrived at that state.
        TRACKING: The device is moving as commanded.
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


class WeatherSensors(Enum):
    """Enumerator for sensors of a weather station.

    Attributes:
        TIME: Time of measurement.
        TEMPERATURE: Temperature in °C
        HUMIDITY: Relative humidity in %.
        PRESSURE: Pressure in hPa.
        WINDDIR: Wind direction in degrees azimuth.
        WINDSPEED: Wind speed in km/h.
        RAIN: Raining (1) or not (0).
        SKYTEMP: Relative sky temperature in °C.
        DEWPOINT: Dew point in °C.
        PARTICLES: Number of particles per m³.

    """
    TIME = 'time'
    TEMPERATURE = 'temp'
    HUMIDITY = 'humid'
    PRESSURE = 'press'
    WINDDIR = 'winddir'
    WINDSPEED = 'windspeed'
    RAIN = 'rain'
    SKYTEMP = 'skytemp'
    DEWPOINT = 'dewpoint'
    PARTICLES = 'particles'


__all__ = ['ExposureStatus', 'ImageType', 'ImageFormat', 'MotionStatus', 'WeatherSensors']
