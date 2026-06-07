"""
Modules for roofs.
TODO: write doc
"""

__title__ = "Roofs"

from .basedome import BaseDome
from .baseroof import BaseRoof
from .dummyroof import DummyRoof

__all__ = ["BaseRoof", "DummyRoof", "BaseDome"]
