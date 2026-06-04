"""
TODO: write doc
"""

__title__ = "Events"

from .badweather import BadWeatherEvent
from .event import Event
from .exposurestatuschanged import ExposureStatusChangedEvent
from .filterchanged import FilterChangedEvent
from .focusfound import FocusFoundEvent
from .goodweather import GoodWeatherEvent
from .log import LogEvent
from .modechanged import ModeChangedEvent
from .moduleclosed import ModuleClosedEvent
from .moduleopened import ModuleOpenedEvent
from .motionstatuschanged import MotionStatusChangedEvent
from .move import MoveAltAzEvent, MoveEvent, MoveRaDecEvent
from .newimage import NewImageEvent
from .newspectrum import NewSpectrumEvent
from .offsets import OffsetsAltAzEvent, OffsetsEvent, OffsetsRaDecEvent
from .roofclosing import RoofClosingEvent
from .roofopened import RoofOpenedEvent
from .taskfailed import TaskFailedEvent
from .taskfinished import TaskFinishedEvent
from .taskstarted import TaskStartedEvent
from .testevent import TestEvent

__all__ = [
    "BadWeatherEvent",
    "ExposureStatusChangedEvent",
    "Event",
    "FilterChangedEvent",
    "FocusFoundEvent",
    "GoodWeatherEvent",
    "LogEvent",
    "ModeChangedEvent",
    "ModuleClosedEvent",
    "ModuleOpenedEvent",
    "MotionStatusChangedEvent",
    "MoveEvent",
    "MoveRaDecEvent",
    "MoveAltAzEvent",
    "NewImageEvent",
    "NewSpectrumEvent",
    "RoofClosingEvent",
    "RoofOpenedEvent",
    "TaskStartedEvent",
    "TaskFailedEvent",
    "TaskFinishedEvent",
    "TestEvent",
    "OffsetsEvent",
    "OffsetsRaDecEvent",
    "OffsetsAltAzEvent",
]
