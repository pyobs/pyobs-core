"""
A module in *pyobs* is the smalles executable unit. The base class for all modules is
:class:`~pyobs.modules.Module`, so all modules should derive from this class and, usually, implement
one or more :class:`~pyobs.interfaces.Interface` s.

Modules are usually not created directly in code, but via a configuration file, which is a YAML file that directly
maps to the constructor of the module plus an additional entry ``class`` containing the full reference to the class
of the module to instantiate.

Take, for instance, the :class:`~pyobs.modules.test.StandAlone` class, which has two parameters in its
constructor: ``message`` and ``interval``. So a valid configuration file would look like this::

    class: pyobs.modules.test.Standalone
    message: Test
    interval: 5

Note that both parameters have default values, so both could be omitted from the configuration. So, this would also
work::

    class: pyobs.modules.test.Standalone
    message: Test

In this case, interval would have to its default value of 10.

.. note::
    Remember that the ``*args`` and ``**kwargs`` are always forwarded to the super class(es), so the constructor of
    a module *always* also provides the parameters from :class:`~pyobs.object.Object` and
    :class:`~pyobs.modules.Module`.

Quite often, a parameter will accept both an object of a given type and a dict. If this is the case, the dict must
be another class definition with a ``class`` keyword, referring to a class of the given type. See, for example, the
``comm`` parameter of :class:`~pyobs.modules.Module`: it takes both a dict and a :class:`pyobs.comm.Comm`.
So in a configuration file, we can always specify a Comm object like this::

    comm:
        class: pyobs.comm.sleekxmpp.XmppComm
        jid: someone@example.com
        password: secret

An object of type :class:`~pyobs.comm.sleekxmpp.XmppComm` (which is a class derived from
:class:`~pyobs.comm.Comm`) will automatically be created.

With a Comm object, proxies to other modules can easily be created (see :mod:`~pyobs.comm` for details)::

    camera: ICamera = self.comm['camera']
    camera.expose()

Sometimes, multiple modules have to run in a single process, so that they can access a common resource. For this case
a :class:`~pyobs.modules.MultiModule` can contain multiple module descriptions.
"""

from .module import Module, MultiModule, timeout, raises

__all__ = ["Module", "MultiModule", "timeout", "raises"]
