Overview
========

After installing pyobs, you have the new command ``pyobs``, which creates and
starts pyobs modules from the command line based on a configuration file, written
in YAML.

A simple configuration file (``standalone.yaml``) might look like this::

    class: pyobs.modules.test.StandAlone
    message: Hello world
    interval: 10

Every block always defines a ``class`` together with its parameters. When *pyobs* loads this file, it
instantiates the given class and passes the remaining keys as keyword arguments to its constructor.

In this example, the module is of type :class:`~pyobs.modules.test.StandAlone`, which logs a message
repeatedly at a given interval. Its implementation looks like this::

    import asyncio
    import logging
    from typing import Any
    from pyobs.modules import Module

    log = logging.getLogger(__name__)


    class StandAlone(Module):
        """Example module that only logs the given message forever in the given interval."""

        def __init__(self, message: str = "Hello world", interval: int = 10, **kwargs: Any):
            Module.__init__(self, **kwargs)
            self._message = message
            self._interval = interval
            self.add_background_task(self._message_func)

        async def _message_func(self) -> None:
            while True:
                log.info(self._message)
                await asyncio.sleep(self._interval)

The constructor calls :meth:`Module.__init__ <pyobs.modules.Module.__init__>` (forwarding ``**kwargs`` so
that ``comm``, ``vfs``, and other shared parameters are handled automatically) and registers a background
task using :meth:`~pyobs.object.Object.add_background_task`. Background tasks are async coroutines that
run concurrently while the module is open. The task here loops indefinitely, logging the message and
then sleeping.

If the configuration file is saved as ``standalone.yaml``, start it with::

    pyobs standalone.yaml

The program shuts down gracefully when it receives an interrupt (``Ctrl+c``).

For a deeper look at how :class:`~pyobs.object.Object` and :class:`~pyobs.modules.Module` work, see
:doc:`api/object` and :doc:`api/module`.


Modules
-------

A Module defines a single process in *pyobs*, as defined in :class:`~pyobs.modules.Module`. Modules can work
completely independently of each other, but usually they communicate with and call methods on other modules.
The functionality that a module exports for remote calling is defined by its interfaces — classes derived from
:class:`~pyobs.interfaces.Interface`. See :doc:`api/interfaces` for the full list.


Location of observatory
-----------------------

Many modules need to know where the telescope is located and what the local time is. This is configured
at the top level of any module configuration file::

    timezone: Africa/Johannesburg
    location:
      longitude: 20.810808
      latitude: -32.375823
      elevation: 1798.

From these values, *pyobs* automatically builds an :class:`~astroplan.Observer` object, which is available
inside any module via the :attr:`~pyobs.object.Object.observer` property. The location itself is accessible
via :attr:`~pyobs.object.Object.location`, and the timezone via :attr:`~pyobs.object.Object.timezone`::

    async def open(self) -> None:
        await Module.open(self)
        print(self.observer.location)


Communication between modules
-----------------------------

For a module to communicate with others, it needs a :class:`~pyobs.comm.Comm` object, defined in the
configuration like this::

    comm:
      class: pyobs.comm.xmpp.XmppComm
      jid: some_module@my.domain.com

Once configured, other modules on the network can be reached via a proxy::

    telescope = await self.proxy("telescope", ITelescope)
    await telescope.move_radec(ra=83.8, dec=-5.4)

More details about this can be found in the :doc:`api/comm` section.


Virtual File System
-------------------

In a *pyobs* system, modules are typically distributed across several computers. To make file exchange
straightforward, *pyobs* has a built-in virtual file system (VFS) that maps logical file paths to real
locations transparently.

A typical VFS setup in a module configuration file looks like this::

    vfs:
      class: pyobs.vfs.VirtualFileSystem
      roots:
        cache:
          class: pyobs.vfs.LocalFile
          root: /path/to/data

This maps every filename beginning with ``cache`` to the path ``/path/to/data`` on the local file system.
Opening ``/cache/test.txt`` for writing via ``vfs.open_file('/cache/test.txt', 'w')`` actually writes to
``/path/to/data/test.txt``.

The same path on a different machine can be mapped over SSH::

    vfs:
      class: pyobs.vfs.VirtualFileSystem
      roots:
        cache:
          class: pyobs.vfs.SSHFile
          hostname: othercomputer
          username: xxx
          password: xxx
          root: /path/to/data

Both machines use the same ``vfs.open_file('/cache/test.txt', ...)`` call — the VFS handles the transport
transparently. See :doc:`api/vfs` for more information.


Events
------

In addition to calling each other's methods, *pyobs* modules can send and receive events asynchronously.
See :doc:`api/events` for details.