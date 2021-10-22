"""
Using interface, a :class:`~pyobs.modules.Module` signals another one, what functionality it provides for remote
procedure calls. The base class for all interfaces in *pyobs* is:

.. autoclass:: pyobs.interfaces.Interface
   :members:

Modules need to implement the required interfaces. For instance, if a module operates a camera, it probably should
implement :class:`~pyobs.interfaces.ICamera`.
"""
__title__ = 'Interfaces'

from .IAbortable import IAbortable
from .IAcquisition import IAcquisition
from .ILatLon import ILatLon
from .IAutoFocus import IAutoFocus
from .IAutoGuiding import IAutoGuiding
from .IAutonomous import IAutonomous
from .IBinning import IBinning
from .ICalibrate import ICalibrate
from .ICamera import ICamera
from .IConfig import IConfig
from .ICooling import ICooling
from .IDome import IDome
from .IExposureTime import IExposureTime
from .IFilters import IFilters
from .IFitsHeaderProvider import IFitsHeaderProvider
from .IFlatField import IFlatField
from .IFocusModel import IFocusModel
from .IFocuser import IFocuser
from .IImageFormat import IImageFormat
from .IImageGrabber import IImageGrabber
from .IImageType import IImageType
from .IModule import IModule
from .IMotion import IMotion
from .IPointingAltAz import IPointingAltAz
from .IPointingHGS import IPointingHGS
from .IPointingRaDec import IPointingRaDec
from .IPointingSeries import IPointingSeries
from .IReady import IReady
from .IRoof import IRoof
from .IRotation import IRotation
from .IRunnable import IRunnable
from .IRunning import IRunning
from .IScriptRunner import IScriptRunner
from .IStartStop import IStartStop
from .ISyncTarget import ISyncTarget
from .ITelescope import ITelescope
from .ITemperatures import ITemperatures
from .IOffsetsAltAz import IOffsetsAltAz
from .IOffsetsRaDec import IOffsetsRaDec
from .IVideo import IVideo
from .IWeather import IWeather
from .IWindow import IWindow
from .interface import Interface
