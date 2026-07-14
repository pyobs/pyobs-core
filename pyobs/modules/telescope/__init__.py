"""
Modules for telescopes.
TODO: write doc
"""

__title__ = "Telescopes"

from .basetelescope import BaseTelescope
from .dummyaltaztelescope import DummyAltAzTelescope
from .dummyradectelescope import DummyRaDecTelescope
from .dummysolartelescope import DummySolarTelescope

__all__ = ["BaseTelescope", "DummyRaDecTelescope", "DummyAltAzTelescope", "DummySolarTelescope"]
