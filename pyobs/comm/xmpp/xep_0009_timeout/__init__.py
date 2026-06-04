from slixmpp.plugins.base import register_plugin

from . import stanza
from .rpc import XEP_0009_timeout
from .stanza import MethodTimeout

register_plugin(XEP_0009_timeout)

__all__ = ["stanza", "XEP_0009_timeout", "MethodTimeout"]
