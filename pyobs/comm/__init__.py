"""
The Comm object is responsible for all communication between modules (see :mod:`pyobs.modules`). The base
class for all implementations is :class:`~pyobs.comm.Comm`.

The user usually only has contact with the Comm object when writing the configuration for an existing module or when
developing a new module that needs to communicate with other modules.

In a configuration file, the Comm object is defined at top-level like this::

    comm:
        class: pyobs.comm.sleekxmpp.XmppComm

Except for a single parameter defined in :class:`~pyobs.comm.Comm`'s constructor, all parameters are defined in
derived classes.

The most convenient way for getting access to other modules' method is by using a :class:`~pyobs.comm.Proxy` object,
which can easily be obtained by using the :meth:`~pyobs.comm.Comm.proxy` method or the ``[]`` operator like this (if
the module named 'camera' implements the :class:`~pyobs.interfaces.ICamera` interface)::

    camera = comm['camera']
    camera.expose().wait()

Note that camera is now not of type :class:`~pyobs.interfaces.ICamera`, but it is a
:class:`~pyobs.interfaces.proxies.ICameraProxy`, which implements exactly the same methods, but with them returning
Futures instead of their return values directly -- thus the call to ``wait()`` at the end.

Each :class:`~pyobs.modules.Module` that was configured with a Comm object (see :mod:`~pyobs.modules`) has
an attribute ``comm`` for easy access.

There is currently one one implementation of the Comm interface:

* :class:`~pyobs.comm.sleekxmpp.XmppComm` uses the XMPP protocol for communication.

.. seealso::

   Module :mod:`~pyobs.modules`
      Description for modules, to which Comm objects are usually assigned.
"""

from .comm import Comm
from .proxy import Proxy
from .exceptions import *


__all__ = ['Comm', 'Proxy']
