"""
Using interface, a :class:`~pyobs.modules.Module` signals another one, what functionality it provides for remote
procedure calls. The base class for all interfaces in *pyobs* is:

.. autoclass:: pyobs.interfaces.Interface
   :members:

Modules need to implement the required interfaces. For instance, if a module operates a camera, it probably should
implement :class:`~pyobs.interfaces.ICamera`.

List of interfaces
******************
"""
__title__ = 'Interfaces'

from .IAbortable import IAbortable
from .IAcquisition import IAcquisition
from .IAltAz import IAltAz
from .ILatLon import ILatLon
from .IAltAzOffsets import IAltAzOffsets
from .IAutoFocus import IAutoFocus
from .IAutoGuiding import IAutoGuiding
from .IAutonomous import IAutonomous
from .ICalibrate import ICalibrate
from .ICamera import ICamera
from .ICameraBinning import ICameraBinning
from .ICameraExposureTime import ICameraExposureTime
from .ICameraWindow import ICameraWindow
from .IConfig import IConfig
from .ICooling import ICooling
from .ICoordinatesQuery import ICoordinatesQuery
from .IDome import IDome
from .IFilters import IFilters
from .IFitsHeaderProvider import IFitsHeaderProvider
from .IFlatField import IFlatField
from .IFocusModel import IFocusModel
from .IFocuser import IFocuser
from .IImageFormat import IImageFormat
from .IImageType import IImageType
from .IModule import IModule
from .IMotion import IMotion
from .IPipeline import IPipeline
from .IRaDec import IRaDec
from .IRaDecOffsets import IRaDecOffsets
from .IReady import IReady
from .IRoof import IRoof
from .IRotation import IRotation
from .IRunnable import IRunnable
from .IScriptRunner import IScriptRunner
from .IStoppable import IStoppable
from .ISyncTarget import ISyncTarget
from .ITelescope import ITelescope
from .ITemperatures import ITemperatures
from .IWeather import IWeather
from .interface import *
