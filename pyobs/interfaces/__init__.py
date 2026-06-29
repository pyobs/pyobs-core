"""
Using interface, a :class:`~pyobs.modules.Module` signals another one, what functionality it provides for remote
procedure calls. The base class for all interfaces in *pyobs* is:

.. autoclass:: pyobs.interfaces.Interface
   :members:

Modules need to implement the required interfaces. For instance, if a module operates a camera, it probably should
implement :class:`~pyobs.interfaces.ICamera`.
"""

__title__ = "Interfaces"

from .IAbortable import IAbortable
from .IAcquisition import IAcquisition
from .IAutoFocus import IAutoFocus
from .IAutoGuiding import IAutoGuiding
from .IAutonomous import IAutonomous
from .IBinning import BinningState, IBinning
from .ICalibrate import ICalibrate
from .ICamera import ICamera
from .IConfig import IConfig
from .ICooling import CoolingState, ICooling
from .IData import IData
from .IDome import IDome
from .IExposure import ExposureState, IExposure
from .IExposureTime import ExposureTimeState, IExposureTime
from .IFilters import FilterState, IFilters
from .IFitsHeaderAfter import IFitsHeaderAfter
from .IFitsHeaderBefore import IFitsHeaderBefore
from .IFlatField import IFlatField
from .IFocuser import FocuserState, IFocuser
from .IFocusModel import IFocusModel
from .IGain import GainState, IGain
from .IImageFormat import IImageFormat, ImageFormatState
from .IImageType import IImageType, ImageTypeState
from .IMode import IMode, ModeState
from .IModule import IModule
from .IMotion import DeviceMotionStatus, IMotion, MotionState
from .IMultiFiber import IMultiFiber, MultiFiberState
from .interface import Interface
from .IOffsetsAltAz import AltAzOffsetState, IOffsetsAltAz
from .IOffsetsRaDec import IOffsetsRaDec, RaDecOffsetState
from .IPointingAltAz import AltAzState, IPointingAltAz
from .IPointingHelioprojective import HelioprojectiveState, IPointingHelioprojective
from .IPointingHGS import HGSState, IPointingHGS
from .IPointingRaDec import IPointingRaDec, RaDecState
from .IPointingSeries import IPointingSeries
from .IReady import IReady, ReadyState
from .IRoof import IRoof
from .IRotation import IRotation, RotationState
from .IRunnable import IRunnable
from .IRunning import IRunning, RunningState
from .IScriptRunner import IScriptRunner
from .ISpectrograph import ISpectrograph
from .IStartStop import IStartStop
from .ISyncTarget import ISyncTarget
from .ITelescope import ITelescope
from .ITemperatures import ITemperatures, SensorReading, TemperaturesState
from .IVideo import IVideo
from .IWeather import IWeather
from .IWindow import IWindow, WindowState

__all__ = [
    "IAbortable",
    "IAcquisition",
    "ILatLon",
    "IAutoFocus",
    "IAutoGuiding",
    "IAutonomous",
    "IBinning",
    "BinningState",
    "ICalibrate",
    "ICamera",
    "IConfig",
    "ICooling",
    "CoolingState",
    "IDome",
    "IExposure",
    "ExposureState",
    "IExposureTime",
    "ExposureTimeState",
    "IFilters",
    "FilterState",
    "IFitsHeaderAfter",
    "IFitsHeaderBefore",
    "IFlatField",
    "IFocusModel",
    "IFocuser",
    "FocuserState",
    "IGain",
    "GainState",
    "IImageFormat",
    "ImageFormatState",
    "IData",
    "IImageType",
    "ImageTypeState",
    "IMode",
    "ModeState",
    "IModule",
    "IMotion",
    "DeviceMotionStatus",
    "MotionState",
    "IMultiFiber",
    "MultiFiberState",
    "IPointingAltAz",
    "AltAzState",
    "IPointingHelioprojective",
    "HelioprojectiveState",
    "IPointingHGS",
    "HGSState",
    "IPointingRaDec",
    "RaDecState",
    "IPointingSeries",
    "IReady",
    "ReadyState",
    "IRoof",
    "IRotation",
    "RotationState",
    "IRunnable",
    "IRunning",
    "RunningState",
    "IScriptRunner",
    "IStartStop",
    "ISyncTarget",
    "ITelescope",
    "ITemperatures",
    "SensorReading",
    "TemperaturesState",
    "IOffsetsAltAz",
    "AltAzOffsetState",
    "IOffsetsRaDec",
    "RaDecOffsetState",
    "ISpectrograph",
    "IVideo",
    "IWeather",
    "IWindow",
    "WindowState",
    "Interface",
]
