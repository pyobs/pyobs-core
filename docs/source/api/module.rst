Modules (pyobs.modules)
-----------------------

A :class:`~pyobs.modules.Module` is the building block of a *pyobs* system. Each module represents one
component of the observatory — a camera, a telescope, a scheduler, a weather monitor, and so on — and runs
as its own process, configured from a YAML file.

:class:`~pyobs.modules.Module` inherits from :class:`~pyobs.object.Object` and adds the communication layer
that allows modules to call each other's methods across a network.


Writing a minimal module
^^^^^^^^^^^^^^^^^^^^^^^^

A module is a class that inherits from :class:`~pyobs.modules.Module` (plus any interfaces it implements)::

    import asyncio
    import logging
    from typing import Any
    from pyobs.modules import Module

    log = logging.getLogger(__name__)


    class MyModule(Module):
        """A minimal example module."""

        def __init__(self, interval: int = 10, **kwargs: Any):
            Module.__init__(self, **kwargs)
            self._interval = interval
            self.add_background_task(self._run)

        async def open(self) -> None:
            await Module.open(self)
            # connect to hardware or subscribe to events here

        async def _run(self) -> None:
            while True:
                log.info("Running...")
                await asyncio.sleep(self._interval)

The matching YAML configuration::

    class: mypackage.MyModule
    interval: 5

    comm:
      class: pyobs.comm.xmpp.XmppComm
      jid: mymodule@my.domain.com

    timezone: UTC
    location:
      longitude: 10.0
      latitude: 51.0
      elevation: 200.0

    vfs:
      class: pyobs.vfs.VirtualFileSystem
      roots:
        cache:
          class: pyobs.vfs.LocalFile
          root: /data

.. note::

    Always forward ``**kwargs`` to ``Module.__init__``. This is how ``comm``, ``vfs``, ``timezone``, and
    ``location`` are passed down from the YAML configuration.


Startup and ``ModuleState.STARTING``
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

A module starts in :attr:`~pyobs.utils.enums.ModuleState.STARTING` and stays there for the
whole ``open()`` override chain — including everything a subclass's own ``open()`` does
after calling ``await Module.open(self)``, e.g. connecting to hardware. While
``STARTING``, :meth:`~pyobs.modules.Module.execute` rejects any call from another module
except ``get_permitted_methods``/``reset_error``, raising
:class:`~pyobs.utils.exceptions.ModuleStartingError`, and the module stays invisible to
XMPP peer discovery (see :ref:`module-startup-gating`). This matters if your own ``open()``
calls into another module via ``self.proxy(...)`` — that module may itself still be
``STARTING``.

A module doesn't call :meth:`~pyobs.modules.Module.startup` on itself; whatever launches it
(``Application``, the normal ``pyobs``/``pyobsd`` entry point, or
:class:`~pyobs.modules.MultiModule`) calls ``startup()``, which runs ``open()`` and then
transitions the module to
:attr:`~pyobs.utils.enums.ModuleState.READY`. You only need to call ``startup()`` yourself
when opening a module outside of those two (a test, a standalone script) — ``open()`` alone
leaves it in ``STARTING`` indefinitely. It's named ``startup()`` rather than ``start()``
because ``start()`` is already :class:`~pyobs.interfaces.IStartStop`'s abstract RPC method —
a plain ``start()`` here would be silently shadowed by any module implementing that
interface.


Interfaces
^^^^^^^^^^

The functionality a module exposes for remote calls is defined by the interfaces it declares. Interfaces
are abstract base classes (defined in :mod:`pyobs.interfaces`) that specify method signatures. A module
implementing :class:`~pyobs.interfaces.ICamera`, for example, advertises that it can take images::

    from pyobs.interfaces import ICamera
    from pyobs.utils.enums import ImageType

    class MyCamera(Module, ICamera):
        async def grab_data(self, broadcast: bool = True, **kwargs: Any) -> str:
            ...

Other modules can then obtain a proxy to ``MyCamera`` and call ``grab_data`` remotely, without knowing
which machine the camera is running on::

    async with self.proxy("camera", ICamera) as camera:
        filename = await camera.grab_data()

See :doc:`interfaces` for the full list of available interfaces.


Communicating between modules
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Modules communicate via the :attr:`~pyobs.object.Object.comm` property, which provides access to the
:class:`~pyobs.comm.Comm` object. The most common use is obtaining a proxy to another module::

    async def open(self) -> None:
        await Module.open(self)
        async with self.proxy("telescope", ITelescope) as telescope:
            await telescope.move_radec(ra=83.8, dec=-5.4)

Modules can also subscribe to and emit :doc:`events`::

    async def open(self) -> None:
        await Module.open(self)
        await self.comm.register_event(NewImageEvent, self._on_new_image)

    async def _on_new_image(self, event: NewImageEvent, sender: str) -> bool:
        log.info("New image from %s: %s", sender, event.filename)
        return True


The ``@timeout`` decorator
^^^^^^^^^^^^^^^^^^^^^^^^^^^

Methods exposed via an interface should declare an expected timeout, so that the comm layer can raise a
helpful error if a call takes too long. Use the :func:`~pyobs.modules.timeout` decorator::

    from pyobs.modules import timeout

    class MyCamera(Module, ICamera):
        @timeout(30)                   # fixed 30 second timeout
        async def grab_data(self, broadcast: bool = True, **kwargs: Any) -> str:
            ...

        @timeout("exposure_time + 10") # expression using method parameters
        async def expose(self, exposure_time: float, **kwargs: Any) -> str:
            ...

The expression form is evaluated with the method's keyword arguments as variables.


API reference
^^^^^^^^^^^^^

.. autoclass:: pyobs.modules.Module
   :members:
   :show-inheritance:

.. autoclass:: pyobs.modules.MultiModule
   :members:
   :show-inheritance: