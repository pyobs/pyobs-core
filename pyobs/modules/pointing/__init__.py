"""
Modules for performing auto-guiding.
TODO: write doc
"""
__title__ = 'Auto-guiding'

from ._baseguiding import BaseGuiding
from .autoguiding import AutoGuiding
from .scienceframeguiding import ScienceFrameAutoGuiding
from .acquisition import Acquisition
from .dummyacquisition import DummyAcquisition
from .dummyguiding import DummyAutoGuiding
