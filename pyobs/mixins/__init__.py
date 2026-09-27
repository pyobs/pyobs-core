"""
Mixins are classes that can be inherited from to automatically add some functionality to a module.
"""

__title__ = "Mixins"

from .camerasettings import CameraSettingsMixin
from .datapipeline import DataPipelineMixin
from .datasequence import DataSequenceMixin
from .fitsheader import (
    FilterHeaderMixin,
    FitsHeaderMixin,
    FocuserHeaderMixin,
    ImageFitsHeaderMixin,
    SpectrumFitsHeaderMixin,
)
from .fitsnamespace import FitsNamespaceMixin
from .follow import FollowMixin
from .motionstatus import MotionStatusMixin
from .waitformotion import WaitForMotionMixin
from .weatheraware import WeatherAwareMixin

__all__ = [
    "FitsHeaderMixin",
    "FitsNamespaceMixin",
    "FollowMixin",
    "MotionStatusMixin",
    "WaitForMotionMixin",
    "WeatherAwareMixin",
    "CameraSettingsMixin",
    "DataPipelineMixin",
    "DataSequenceMixin",
    "ImageFitsHeaderMixin",
    "SpectrumFitsHeaderMixin",
    "FilterHeaderMixin",
    "FocuserHeaderMixin",
]
