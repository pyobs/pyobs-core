Overview
========

After installing pyobs, you have the new command ``pyobs``, which creates and
starts pyobs modules from the command line based on a configuration file, written
in YAML.

A simple configuration file (``standalone.yaml``) might look like this::

    class: pyobs.modules.test.StandAlone
    message: Hello world
    interval: 10

Basically you always define a ``class`` for a block together with its properties.

In this example, the module is of type :class:`~pyobs.modules.test.StandAlone`, which is a trivial implementation
of a module that does nothing more than logging a given message continuously in a given interval::

    class StandAlone(Module):
        """Example module that only logs the given message forever in the given interval."""

        def __init__(self, message: str = 'Hello world', interval: int = 10, *args, **kwargs):
            """Creates a new StandAlone object.

            Args:
                message: Message to log in the given interval.
                interval: Interval between messages.
            """
            Module.__init__(self, *args, **kwargs)

            # add thread func
            self._add_thread_func(self._message_func, True)

            # store
            self._message = message
            self._interval = interval

        def _message_func(self):
            """Thread function for async processing."""
            # loop until closing
            while not self.closing.is_set():
                # log message
                log.info(self._message)

                # sleep a little
                self.closing.wait(self._interval)

The constructor just calls the constructor of :class:`~pyobs.modules.Module` and calls a method
:meth:`~pyobs.object.Object.add_background_task`, which takes a method that is run in an extra thread. In this case,
it is the method ``thread_func()``, that does some logging in a loop until the program quits.

The class method default_config() defines the default configuration for the module, and open() and close()
are called when the module is opened and closed, respectively.

If the configuration file is saved as ``standalone.yaml``, one can easily start it via the ``pyobs`` command::

    pyobs standalone.yaml

The program quits gracefully when it receives an interrupt, so you can stop it by simply pressing ``Ctrl+c``.


Modules
-------

A Module defines a single process in *pyobs*, as defined in :class:`~pyobs.modules.Module`. Modules can work
completely independent of each other, but usually they want to communicate and call methods on other modules.
The functionality that a module exports for remote calling is defined by its base classe, specifically classes
derived from :class:`~pyobs.interfaces.Interface`.


Location of observatory
-----------------------

There is some functionality that is required in many modules, including those concerning the environment,
especially the location of the telescope and the local time. For this, there is support for an additional object
of type :class:`~pyobs.environment.Environment`, which can be defined in the application's configuration
at top-level like this::

    timezone: Africa/Johannesburg
    location:
      longitude: 20.810808
      latitude: -32.375823
      elevation: 1798.

Now an object of this type is automatically pushed into the module and can be accessed via the ``environment``
property, e.g.::

    def open(self):
        Module.open(self)
        print(self.environment.location)


Communication between modules
-----------------------------

In case the module is supposed to communicate with others, we need another module of type
:class:`~pyobs.comm.Comm`, which can be defined in the application's configuration like this::

    comm:
      class: pyobs.comm.xmpp.XmppComm
      jid: some_module@my.domain.com

More details about this can be found in the :doc:`api/comm` section.


Virtual File System
-------------------

At the telescope the *pyobs* system usually contains multiple modules that are distributed over several computers. In
order to make file exchange es easy as possible, *pyobs* has a built-in virtual file system (VFS) that dynamically maps
file paths to real locations.

A typical VFS setup in a module configuration file looks like this::

    vfs:
      class: pyobs.vfs.VirtualFileSystem
      roots:
        cache:
          class: pyobs.vfs.LocalFile
          root: /path/to/data

This simple case uses a :class:`~pyobs.vfs.LocalFile` to map every filename beginning with ``cache`` (see the key in the
``roots`` dictionary) to the path ``/path/to/data`` in the local file system. So opening a file via
``vfs.open_file('/cache/test.txt', 'w')`` actually opens the file in ``/path/to/data/test.txt`` for writing.

The magic begins when running another module on another computer with this configuration::

    vfs:
      class: pyobs.vfs.VirtualFileSystem
      roots:
        cache:
          class: pyobs.vfs.SSHFile
          hostname: othercomputer
          username: xxx
          password: xxx
          root: /path/to/data

Now on that machine you can read the same file, using the same command ``vfs.open_file('/cache/test.txt', 'r')``,
via a SSH connection, by specifying :class:`~pyobs.vfs.SSHFile` as the class for the given root.

See :doc:`api/vfs` for more information about the VFS.


Events
------

In addition to calling each other's method, *pyobs* modules can also send and receive events. See more about this
in :doc:`api/events`.