Communication between modules (pyobs.comm)
------------------------------------------

.. automodule:: pyobs.comm

Modules in a *pyobs* system rarely run in isolation — an autofocus module needs to tell the camera
to take a picture, a guiding module needs to send corrections to the telescope, and so on. All of
this inter-module communication goes through a :class:`~pyobs.comm.Comm` object.

The ``Comm`` layer has three responsibilities:

- **Method calls** — calling a method on a remote module as if it were local, via a :class:`~pyobs.comm.Proxy`
- **Events** — broadcasting typed event objects to all interested modules
- **Discovery** — finding out which modules are online and what interfaces they expose


Configuration
^^^^^^^^^^^^^

A ``Comm`` object is configured at the top level of any module YAML file::

    comm:
      class: pyobs.comm.xmpp.XmppComm
      jid: camera@my.observatory.org

Once configured, it is available inside any :class:`~pyobs.object.Object` or
:class:`~pyobs.modules.Module` via ``self.comm``.


Proxies and remote method calls
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

A :class:`~pyobs.comm.Proxy` is a local stand-in for a remote module. It exposes the same interface
methods as the real module, but executes them remotely over the network. Obtain one with
:meth:`~pyobs.object.Object.proxy` (available on every ``Object`` and ``Module``)::

    from pyobs.interfaces import ITelescope, ICamera

    # get a proxy to the telescope module
    telescope = await self.proxy("telescope", ITelescope)

    # call its methods just like local ones
    await telescope.move_radec(ra=83.8, dec=-5.4)

The second argument is the expected interface. If the named module does not implement that interface,
:meth:`~pyobs.object.Object.proxy` raises a ``ValueError``, which makes type errors visible immediately
rather than at the point of the actual call.

For cases where a module might or might not be present, use
:meth:`~pyobs.comm.Comm.safe_proxy`, which returns ``None`` instead of raising::

    focuser = await self.comm.safe_proxy("focuser", IFocuser)
    if focuser is not None:
        await focuser.set_focus(focus_value)

To find all currently connected modules that implement a given interface::

    cameras = await self.comm.clients_with_interface(ICamera)


Events
^^^^^^

Events are typed objects broadcast to all modules that have registered an interest in them. They are
used for loosely coupled notification — a module that finishes an exposure fires a
:class:`~pyobs.events.NewImageEvent`; any module that wants to react to new images subscribes to it.

**Subscribing** to an event is done in ``open()``::

    from pyobs.events import NewImageEvent, GoodWeatherEvent

    async def open(self) -> None:
        await Module.open(self)
        await self.comm.register_event(NewImageEvent, self._on_new_image)
        await self.comm.register_event(GoodWeatherEvent, self._on_good_weather)

    async def _on_new_image(self, event: NewImageEvent, sender: str) -> bool:
        log.info("New image from %s: %s", sender, event.filename)
        return True

The handler must be an async coroutine that accepts the event object and the sender's name, and returns
a boolean indicating whether the event was handled.

**Sending** an event requires registering the event type first (even without a handler), then sending::

    from pyobs.events import ExposureStatusChangedEvent
    from pyobs.utils.enums import ExposureStatus

    async def open(self) -> None:
        await Module.open(self)
        await self.comm.register_event(ExposureStatusChangedEvent)

    async def _expose(self) -> None:
        await self.comm.send_event(ExposureStatusChangedEvent(ExposureStatus.EXPOSING))

See :doc:`events` for the full list of available event types.


Implementations
^^^^^^^^^^^^^^^

.. list-table::
   :header-rows: 1
   :widths: 30 70

   * - Class
     - Use case
   * - :class:`~pyobs.comm.xmpp.XmppComm`
     - Production use. Requires an XMPP server (e.g. ejabberd). All modules connect to the server and
       communicate via XMPP's RPC and publish-subscribe extensions. This is the standard choice for
       real observatories.
   * - :class:`~pyobs.comm.dbus.DbusComm`
     - Single-machine setups on Linux using D-Bus for inter-process communication. No external server
       required, but modules must run on the same machine.
   * - :class:`~pyobs.comm.local.LocalComm`
     - In-process communication for use in :class:`~pyobs.modules.MultiModule` setups and tests.
       All modules share the same Python process.
   * - :class:`~pyobs.comm.dummy.DummyComm`
     - No-op implementation used when no comm is configured. A module with ``DummyComm`` runs in
       isolation — it cannot call remote methods or receive events.


API reference
^^^^^^^^^^^^^

.. autoclass:: pyobs.comm.Comm
   :members:

.. autoclass:: pyobs.comm.Proxy
   :members:

.. autoclass:: pyobs.comm.xmpp.XmppComm
   :members:
   :show-inheritance:

.. autoclass:: pyobs.comm.dbus.DbusComm
   :members:
   :show-inheritance: