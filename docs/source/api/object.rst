Objects (pyobs.object)
----------------------

.. automodule:: pyobs.object

The :class:`~pyobs.object.Object` class is the base for almost everything in *pyobs*. Understanding it is the key
to understanding how the framework is configured and how objects are created from YAML files.


The ``class:`` key and YAML instantiation
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Every *pyobs* object can be described in a YAML configuration block by specifying its fully qualified class name
under the ``class:`` key, followed by any constructor parameters::

    class: pyobs.modules.camera.DummyCamera
    exposure_time: 2.0
    vfs:
      class: pyobs.vfs.VirtualFileSystem
      roots:
        cache:
          class: pyobs.vfs.LocalFile
          root: /data

When *pyobs* encounters such a block, it strips the ``class:`` key and passes the remaining keys as keyword
arguments to the constructor. This means constructor parameters map directly to YAML keys, and nested objects
(like ``vfs`` above) are instantiated recursively in the same way.

The functions :func:`~pyobs.object.create_object` and :func:`~pyobs.object.get_object` implement this
mechanism. You will typically use :func:`~pyobs.object.get_object` or
:meth:`~pyobs.object.Object.add_child_object` inside your own classes rather than calling
:func:`~pyobs.object.create_object` directly.


Lifecycle: ``__init__``, ``open()``, and ``close()``
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Every :class:`~pyobs.object.Object` follows a strict two-phase lifecycle:

1. **Construction** (``__init__``): Store parameters, create child objects via
   :meth:`~pyobs.object.Object.add_child_object`, and register background tasks via
   :meth:`~pyobs.object.Object.add_background_task`. Do **not** connect to hardware or external services here.

2. **Opening** (``open()``): Connect to hardware, subscribe to events, and start background tasks. This is
   where side effects should happen.

Always pair ``open()`` with a corresponding ``close()``, which stops background tasks and closes all child objects.

.. important::

    :meth:`~pyobs.object.Object.add_background_task` and :meth:`~pyobs.object.Object.add_child_object` **must**
    be called in ``__init__``, before ``open()`` is called.


Runtime context: ``comm``, ``vfs``, ``observer``, ``location``, ``timezone``
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

:class:`~pyobs.object.Object` provides several shared runtime resources as properties:

- :attr:`~pyobs.object.Object.comm` — the :class:`~pyobs.comm.Comm` object for communicating with other modules.
- :attr:`~pyobs.object.Object.vfs` — the :class:`~pyobs.vfs.VirtualFileSystem` for file access.
- :attr:`~pyobs.object.Object.observer` — an :class:`astroplan.Observer` built from the configured location and timezone.
- :attr:`~pyobs.object.Object.location` — the observatory's :class:`~astropy.coordinates.EarthLocation`.
- :attr:`~pyobs.object.Object.timezone` — the local timezone as a :class:`datetime.tzinfo`.

These are automatically propagated to child objects created via :meth:`~pyobs.object.Object.add_child_object`.
They can be configured in the YAML block (see :doc:`/overview` for examples) or inherited from a parent object.


Background tasks
^^^^^^^^^^^^^^^^

Background tasks are async coroutines that run concurrently alongside the main module. Register them in
``__init__`` using :meth:`~pyobs.object.Object.add_background_task`::

    class MyObject(Object):
        def __init__(self, interval: int = 10, **kwargs):
            Object.__init__(self, **kwargs)
            self._interval = interval
            self.add_background_task(self._run)

        async def _run(self) -> None:
            while True:
                log.info("Running...")
                await asyncio.sleep(self._interval)

By default, background tasks are restarted automatically if they raise an unhandled exception. Pass
``restart=False`` to disable this. Pass ``autostart=False`` to prevent the task from starting when
``open()`` is called (you can then start it manually).


Child objects
^^^^^^^^^^^^^

:meth:`~pyobs.object.Object.add_child_object` creates a child object from a config dict or existing instance,
automatically copies the runtime context (``comm``, ``vfs``, ``observer``, etc.) into it, and registers it
for automatic ``open()``/``close()`` calls::

    class MyObject(Object):
        def __init__(self, camera: dict | ICamera, **kwargs):
            Object.__init__(self, **kwargs)
            self._camera = self.add_child_object(camera, ICamera)

When ``MyObject.open()`` is called, it will also call ``self._camera.open()`` automatically. The same applies
to ``close()``.


API reference
^^^^^^^^^^^^^

.. autoclass:: pyobs.object.Object
  :members:

.. autofunction:: pyobs.object.get_object

.. autofunction:: pyobs.object.get_safe_object

.. autofunction:: pyobs.object.create_object

.. autofunction:: pyobs.object.get_class_from_string