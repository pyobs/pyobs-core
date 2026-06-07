"""
Modules for performing auto-guiding.
TODO: write doc
"""

__title__ = "Auto-guiding"

from ._baseguiding import BaseGuiding
from .acquisition import Acquisition
from .autoguiding import AutoGuiding
from .dummyacquisition import DummyAcquisition
from .dummyguiding import DummyAutoGuiding
from .scienceframeguiding import ScienceFrameAutoGuiding

__all__ = [
    "BaseGuiding",
    "AutoGuiding",
    "ScienceFrameAutoGuiding",
    "Acquisition",
    "DummyAcquisition",
    "DummyAutoGuiding",
]
