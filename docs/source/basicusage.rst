Basic Usage
===========

After installing pytel, you have the new command ``pytel``, which creates and
starts pytel modules from the command line based on a configuration file, written
in YAML.

A simple configuration file (``/opt/pytel/config/standalone.yaml``) might look like this::

    class: pytel.Application

    module:
      class: pytel.modules.test.StandAlone
      message: Hello world
      interval: 10

Basically you always define a ``class`` for a block together with its properties.

In this example, an object is created from the class :class:`pytel.Application`, which usually
should always be the top-level class in a pytel configuration. Among other parameters, this
class accepts a ``module`` parameter, in which we can define another object, that defines
the logic of the program.

The module itself is of type :class:`pytel.modules.test.StandAlone`, which is a trivial implementation
of a module that does nothing more than logging a given message continuously in a given interval::

    class StandAlone(PytelModule):
        def __init__(self, *args, **kwargs):
            PytelModule.__init__(self, thread_funcs=self.thread_func, *args, **kwargs)

        @classmethod
        def default_config(cls):
            cfg = super(StandAlone, cls).default_config()
            cfg['message'] = 'Hello world'
            cfg['interval'] = 10
            return cfg

        def open(self) -> bool:
            return PytelModule.open(self)

        def close(self):
            PytelModule.close(self)

        def thread_func(self):
            while not self.closing.is_set():
                log.info(self.config['message'])
                self.closing.wait(self.config['interval'])

The constructor just calls the constructor of :class:`pytel.PytelModule`, adding the ``thread_funcs``
parameter, that takes a method that is run in an extra thread. In this case, it is the method
thread_func(), that does some logging in a loop that runs until the
program quits.

The class method default_config() defines the default configuration for the module, and open() and close()
are called when the module is opened and closed, respectively.

If the configuration file is saved as ``standalone.yaml``, one can easily start it via the ``pytel`` command::

    pytel standalone.yaml

The program quits gracefully when it receives an interrupt, so you can stop it by simply pressing ``Ctrl+c``.

Environment
-----------

There is some functionality that is required in many modules, including those concerning the environment,
especially the location of the telescope and the local time. For this, the :class:`pytel.Application` class
has support for an additional module of type :class:`pytel.modules.environment.Environment`, which can be
defined in the application's configuration like this::

    environment:
      class: pytel.modules.environment.Environment
      timezone: utc
      location:
        longitude: 20.810808
        latitude: -32.375823
        elevation: 1798.

Now an object of this type is automatically pushed into the module and can be accessed via the ``environment``
property, e.g.::

    def open(self) -> bool:
        print(self.environment.location)
        return PytelModule.open(self)


Comm
----

In case the module is supposed to communicate with others, we need another module of type
:class:`pytel.comm.Comm`, which can be defined in the application's configuration like this::

    comm:
      class: pytel.comm.xmpp.XmppComm
      jid: some_module@my.domain.com

More details about this can be found in the :doc:`comm` section.
