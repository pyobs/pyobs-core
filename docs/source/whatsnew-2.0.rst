What's New in pyobs 2.0
########################

.. note::
   pyobs 2.0 is still under development (currently |release|). This page is a living
   summary of what has changed since the 1.x series and will be updated as new changes
   land on ``develop``, until the final 2.0 release.

Summary
=======

pyobs 2.0 is primarily a redesign of the communication layer. The RPC / interface-discovery
/ events architecture from 1.x is kept, but the wire protocol is made explicit and extended
with a fourth concept, **state**: modules continuously publish "what is true right now"
(a camera's cooling temperature, a telescope's tracking status, ...) over XMPP PubSub,
instead of clients polling for it via RPC. Interface discovery (XEP-0030) is extended into
a full, versioned, language-neutral schema for commands, state, events and fixed
capabilities, so that non-Python clients (e.g. ``pyobs-web-client``) can be generated
against it directly instead of reverse-engineering the Python interfaces.

Almost none of this is optional or opt-in — it touches the wire protocol, the ``Proxy``
API, and roughly half of the interfaces in :mod:`pyobs.interfaces`. Read the
`Breaking changes`_ section carefully before upgrading any module outside of
``pyobs-core`` (custom hardware drivers, GUIs, scripts).

Breaking changes
=================

Minimum Python version
-----------------------

pyobs now requires **Python 3.11 or newer**.

.. _proxy-async-with-only:

``Proxy`` is now ``async with``-only
--------------------------------------

The long-lived-reference pattern is gone. ``await self.proxy(...)`` no longer returns a
usable proxy object; ``self.proxy(name, IInterface)`` is now an async context manager and
must be used as such:

.. code-block:: python

   # 1.x
   camera = await self.proxy("camera", ICamera)
   await camera.expose(10)

   # 2.0
   async with self.proxy("camera", ICamera) as camera:
       await camera.expose(10)

``self.safe_proxy(...)`` (the version that swallows connection errors and logs instead of
raising) works the same way. The ``cache_proxies`` option is gone along with the pattern it
enabled. Use ``await self.has_proxy(name, IInterface)`` (a plain coroutine returning
``bool``, *not* a context manager) where you only need an existence/type check rather than
an actual call.

Two shapes that come up in real migrations:

**Resolving several proxies in a loop.** ``async with`` cannot appear inside a
comprehension (``[async with p as x for p in proxies]`` is a ``SyntaxError``), and a list of
already-resolved ``Proxy`` objects held across time is exactly the pattern being closed
off. Resolve a list of *names*, not proxies, and wrap each use in its own ``async with``:

.. code-block:: python

   async def _status(client: str) -> MotionStatus:
       async with self.proxy(client, IMotion) as p:
           return await p.get_motion_status()

   # sequential -- behavior-preserving translation of the old comprehension
   states = [await _status(client) for client in clients]

   # concurrent, if actually wanted (a genuine behavior change, not required by the migration)
   states = await asyncio.gather(*(_status(client) for client in clients))

**A proxy that's only sometimes needed, used later in the same method.** Don't just wrap
the resolution line in a no-op ``async with ...: pass`` block — nothing stops the name from
being referenced later even though its context has already exited, so this *looks* fine and
is silently broken. Use ``contextlib.AsyncExitStack`` when a proxy needs to stay valid for
the rest of the method body:

.. code-block:: python

   from contextlib import AsyncExitStack

   async def do_exposure(self) -> None:
       async with AsyncExitStack() as stack:
           filters: IFilters | None = None
           if self._filter_wheel is not None:
               filters = await stack.enter_async_context(self.safe_proxy(self._filter_wheel, IFilters))

           # ... rest of the method, however long, filters stays valid here ...
           if filters is not None:
               await filters.set_filter("R")

Modules and configuration
---------------------------

* ``Module``'s constructor no longer takes a ``name`` parameter. A module's name always
  tracks its ``comm`` object's own identity (the XMPP JID's user part, or the ``LocalComm``
  name) rather than an independently configurable string — remove any top-level ``name:``
  key from module YAML configs; use ``label:`` for a purely cosmetic display name instead.
* ``IModule.get_state()`` and ``IModule.get_error_string()`` are removed. A module's
  online/ready/error status is available via XMPP presence and
  ``Comm.get_client_state(module) -> tuple[ModuleState, str] | None`` instead of an RPC
  round trip.
* A module now shuts down gracefully instead of endlessly reconnecting when it is kicked
  from the XMPP server due to a JID conflict (a duplicate login, or an admin-issued kick,
  both surface as the same stream-error condition).

Removed and renamed interfaces / RPC methods
----------------------------------------------

``ILatLon`` (and its ``LatLonCapabilities``) is removed from :mod:`pyobs.interfaces`
entirely.

Renamed classes: ``SubClassBaseModel`` → ``PolymorphicBaseModel``, ``MeritScheduler`` →
``OnDemandScheduler``. ``Object`` is no longer a base class of ``BaseModel``.

A large fraction of the ``get_*``/``is_*`` RPC methods across :mod:`pyobs.interfaces` are
removed, replaced by one of: subscribing to the interface's new ``state``, reading a
fixed ``capabilities`` value from discovery (no RPC round trip needed), or — for exactly
two cases — XMPP presence. If you have custom modules that *implement* one of the affected
interfaces, you need to call ``self.comm.set_state(...)`` (see `Live state`_ below) instead
of answering the old getter; if you have code that *calls* one of these methods on a proxy,
switch to ``await proxy.get_state(IInterface)`` (or ``wait_for_state``) or
``proxy.get_capabilities(IInterface)``.

.. list-table::
   :header-rows: 1
   :widths: 22 30 48

   * - Interface
     - Removed method(s)
     - Replacement
   * - ``ICooling``
     - ``get_cooling``
     - ``state = CoolingState(enabled, setpoint, power, temperature, time)``
   * - ``ITemperatures``
     - ``get_temperatures``
     - ``state = TemperaturesState(readings: list[SensorReading])``
   * - ``IBinning``
     - ``get_binning``
     - ``state = BinningState``; fixed options via ``capabilities = BinningCapabilities``
   * - ``IWindow``
     - ``get_window``, ``get_full_frame``
     - ``get_window`` → ``state = WindowState``; ``get_full_frame`` → ``capabilities = WindowCapabilities``
   * - ``IExposureTime``
     - ``get_exposure_time``, ``get_exposure_time_left``
     - ``state = ExposureTimeState``
   * - ``IGain``
     - ``get_gain``, ``get_offset``
     - ``state = GainState``
   * - ``IFilters``
     - ``get_filter``
     - ``state = FilterState``; available filters via ``capabilities = FiltersCapabilities``
   * - ``IImageFormat``
     - ``get_image_format``
     - ``state = ImageFormatState``; available formats via ``capabilities = ImageFormatCapabilities``
   * - ``IImageType``
     - ``get_image_type``
     - ``state = ImageTypeState``
   * - ``IExposure``
     - ``get_exposure_status``, ``get_exposure_progress``
     - ``state = ExposureState(status, progress, time)``
   * - ``IMode``
     - ``get_mode``
     - ``state = ModeState``; available modes via ``capabilities = ModeCapabilities``
   * - ``IMotion``
     - ``get_motion_status``
     - ``state = MotionState(devices: list[DeviceMotionStatus])``
   * - ``IPointingRaDec``
     - ``get_radec``
     - ``state = RaDecState``
   * - ``IPointingAltAz``
     - ``get_altaz``
     - ``state = AltAzState``
   * - ``IPointingHeliocentricPolar``
     - ``get_heliocentric_polar``
     - ``state = HeliocentricPolarState``
   * - ``IPointingHelioprojective``
     - ``get_helioprojective``
     - ``state = HelioprojectiveState``
   * - ``IRotation``
     - ``get_rotation``
     - ``state = RotationState``
   * - ``IOffsetsRaDec``
     - ``get_offsets_radec``
     - ``state = RaDecOffsetState``
   * - ``IOffsetsAltAz``
     - ``get_offsets_altaz``
     - ``state = AltAzOffsetState``
   * - ``IFocuser``
     - ``get_focus``, ``get_focus_offset``
     - ``state = FocuserState``
   * - ``IFocusModel``
     - ``get_optimal_focus``
     - ``state = OptimalFocusState`` (re-exported from :mod:`pyobs.interfaces`)
   * - ``IWeather``
     - ``get_weather_status``, ``is_weather_good``, ``get_current_weather``
     - ``state = WeatherState(good, readings: list[WeatherSensorReading], time)``. ``get_sensor_value(station, sensor)`` **stays RPC** (it's a live per-station call), but now returns a ``WeatherSensorReading`` instead of ``tuple[str, float]``.
   * - ``IMultiFiber``
     - ``get_fiber``, ``get_pixel_position``, ``get_radius``
     - ``state = MultiFiberState``; ``get_fiber_count`` → ``capabilities = MultiFiberCapabilities``
   * - ``IReady``
     - ``is_ready``
     - ``state = ReadyState``
   * - ``IRunning``
     - ``is_running``
     - ``state = RunningState``
   * - ``IModule``
     - ``get_label``, ``get_version``
     - ``capabilities = ModuleCapabilities(label, version)``
   * - ``IConfig``
     - ``get_config_caps``
     - ``capabilities = ConfigCapabilities``. ``get_config_value``/``set_config_value`` stay RPC (config keys are genuinely dynamic).
   * - ``IVideo``
     - ``get_video``
     - ``capabilities = VideoCapabilities``

``IAutoFocus`` and ``IAcquisition`` also moved from tuple/``dict[str, Any]`` returns to
structured results, on top of gaining live state:

* ``IAutoFocus.auto_focus()`` now returns ``AutoFocusResult(focus, focus_err)`` instead of a
  bare tuple; the old ``auto_focus_status() -> dict[str, Any]`` RPC method is removed
  entirely, replaced by ``state = AutoFocusState`` (which includes a growing
  ``points: list[AutoFocusPoint]`` log of the current run).
* ``IAcquisition.acquire_target()`` now returns a typed ``AcquisitionResult`` (``time``,
  ``ra``/``dec``, ``alt``/``az``, and an optional applied offset) instead of
  ``dict[str, Any]``, and ``state = AcquisitionState`` tracks a growing log of
  ``attempts: list[AcquisitionAttempt]`` for the current run plus the last ``result``.
* ``IAutoGuiding`` gained ``state = GuidingState`` (``loop_closed``, and the last applied
  offset).
* ``IFitsHeaderBefore``/``IFitsHeaderAfter`` keep their RPC-based
  ``get_fits_header_*(namespaces)`` methods, but the return type is now
  ``dict[str, FitsHeaderEntry]`` (a named ``value``/``comment`` pair) instead of
  ``dict[str, tuple[Any, str]]``.

Across the board, **19 of 19** originally tuple-returning interface methods have been
converted to named dataclasses, except ``IFlatField.flat_field() -> tuple[int, float]``,
which stays a tuple deliberately (it's a genuine one-off RPC action result, not a
State/Capability candidate).

``ICamera``/``ISpectrograph`` no longer imply ``IExposure``
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

``ICamera`` and ``ISpectrograph`` used to inherit ``IExposure`` (the table above), forcing every
implementer to carry exposure-progress state even when it doesn't apply -- ``PipelineCamera``
published a single, never-updated ``ExposureState`` purely to satisfy the type, despite having no
in-progress exposure to report. Both interfaces are now plain ``IData`` identity interfaces;
``BaseCamera``/``BaseSpectrograph`` declare ``IExposure`` explicitly alongside them instead of
inheriting it implicitly, and ``PipelineCamera`` drops it entirely. If you have a module that
subclasses ``ICamera``/``ISpectrograph`` directly (not via ``BaseCamera``/``BaseSpectrograph``)
and actually wants exposure-progress semantics, add ``IExposure`` to its own bases explicitly and
publish ``ExposureState`` via ``self.comm.set_state(...)``.

Deployment / infrastructure
------------------------------

If you run your own ejabberd server (rather than only using ``LocalComm`` for testing),
**state publication requires ``mod_pubsub`` to be configured with different node defaults
than ejabberd ships with**. Add this to ``ejabberd.yml``:

.. code-block:: yaml

   mod_pubsub:
     default_node_config:
       deliver_notifications: true
       deliver_payloads: true
       persist_items: true
       max_items: 1
       send_last_published_item: on_sub_and_presence
       notify_retract: false

Without this, ejabberd's own defaults don't reliably enable notification delivery for the
state PubSub nodes pyobs auto-creates on first publish, and new subscribers won't
immediately receive the last known value.

New features
============

Live state
----------

Modules publish live state over XMPP PubSub for every interface they implement that
declares one (see the table above for the full list — ``ICooling``, ``IWeather``,
``IAutoFocus``, ``IAutoGuiding``, ``IAcquisition``, and about a dozen more), instead of
clients polling via RPC. A module publishes state with:

.. code-block:: python

   await self.comm.set_state(ICooling, CoolingState(enabled=True, setpoint=-20.0, power=87.3, temperature=-19.8))

On a ``Proxy``, read it with:

.. code-block:: python

   async with self.proxy("camera", ICooling) as camera:
       state = camera.get_state(ICooling)          # last known value, or None if never subscribed/published
       state = await camera.wait_for_state(ICooling)  # wait for the next update

State is cached per-connection and delivered immediately on subscribe (ejabberd's
"last published item" semantics), so a client always has a value right after resolving a
proxy without a separate fetch. State has no history: it is "what is true right now," kept
strictly distinct from events, which remain immutable, timestamped facts about things that
happened.

Some interfaces need a variable, hardware-dependent set of fields rather than a fixed
schema — a telescope's temperature sensors vary in name and count by installation. These
use **extensible, typed collections** instead of one field per sensor:
``ITemperatures.state = TemperaturesState(readings: list[SensorReading])``, where each
``SensorReading`` is a self-describing ``(name, value)`` pair. The same pattern is used for
``IWeather.state.readings`` and ``IMotion.state.devices``.

Capabilities and versioned discovery
---------------------------------------

Service discovery (disco#info) now publishes a full, versioned schema for a module's
interfaces, state, and events: ``urn:pyobs:interface:ICamera:2``,
``urn:pyobs:state:ICooling:1``, ``urn:pyobs:event:NewImageEvent:1``. Fixed-for-lifetime
values that used to require an RPC round trip (a camera's full-frame size, a module's
label/version, the list of available filters) are now published inline as
``capabilities`` alongside the interface schema — see the removed-methods table above for
which interfaces gained one.

Both ``Interface.version`` and ``Event.version`` (each defaulting to ``1``) are part of
the wire contract now: a mismatched version between two ends of a connection excludes
that interface from a resolved proxy instead of silently misbehaving on a request/response
shape it no longer matches, which gives pyobs a mixed-version-fleet diagnostic for free —
useful when rolling out a 2.0 module gradually alongside older ones.

This also effectively turns pyobs's Python interfaces into a language-neutral IDL: a
non-Python client (``pyobs-web-client``, or any future binding) can generate its
commands/state/event schema directly from one disco#info query, instead of maintaining a
separate interface-extraction step against the Python source.

External-package interfaces
------------------------------

Interfaces no longer have to live in :mod:`pyobs.interfaces`. Any package can define its
own by subclassing :class:`~pyobs.interfaces.Interface` — it's picked up automatically at
import time and resolves correctly over the wire, exactly like a core interface:

.. code-block:: python

   # pyobs_mypackage/interfaces.py
   from pyobs.interfaces import Interface

   class ISiderostatAlignment(Interface):
       async def start_alignment_sequence(self) -> None: ...

   # a module implementing it
   class Siderostat(Module, ISiderostatAlignment):
       async def start_alignment_sequence(self) -> None:
           ...

   # a consumer, resolved the same way as any core interface
   async with self.proxy("siderostat", ISiderostatAlignment) as proxy:
       await proxy.start_alignment_sequence()

There's no separate registration step beyond the import: a module implementing the
interface, and any code building a typed proxy for it, already have to import it — the same
implicit requirement core interfaces already impose. Two interfaces defined independently
that happen to share a class name raise ``TypeError`` immediately at import time, naming
both offending classes, rather than silently resolving to whichever one happened to be
imported last.

Units
-----

Interface parameters, return values, and state fields that carry a physical quantity are
now annotated with a canonical unit via ``typing.Annotated`` and the new
``pyobs.utils.enums.Unit`` enum, e.g. ``Annotated[float, Unit.CELSIUS]``. The
annotation is the single source of truth for both the Python signature and the generated
wire schema (``unit="celsius"`` in disco#info) — nothing to keep in sync by hand. Existing
conventions are unchanged (degrees for angles, Celsius for temperature, seconds for
duration, percent, hPa, km/h) — this only makes them explicit on the wire for non-Python
clients.

Non-sidereal tracking
----------------------

Telescopes can now track anything beyond sidereal: the Moon, planets, the Sun, or a body
defined by orbital elements (asteroids, comets, NEOs). Two new interfaces express this at
the hardware-capability level, mirroring the ASCOM ``ITelescope`` split between discrete
tracking rates and an arbitrary rate offset:

* ``ITrackingMode`` — discrete, firmware-native rates (``sidereal``/``solar``/``lunar``/``off``),
  for drivers whose hardware actually has them.
* ``ITrackingRate`` — an arbitrary continuous RA/Dec rate offset
  (``Annotated[float, Unit.ARCSEC_PER_SEC]``, absolute on the sky), for anything without a
  native mode. Always applied on top of ``TrackingMode.SIDEREAL``, never ``OFF`` — the
  physical decomposition of a tracked body's motion is "sidereal plus a small correction,"
  not an unrelated absolute rate.

Two more interfaces are the actual pointing-layer entry points on top of those:

.. code-block:: python

   async with self.proxy("telescope", IPointingBody) as telescope:
       await telescope.track_body("moon")  # or "mars", "jupiter", an asteroid designation, ...

``IPointingOrbitalElements.track_orbital_elements(elements)`` is the equivalent for a body
given as classical orbital elements directly (asteroid/comet/NEO) rather than resolved by
name — the manual-input path for a freshly-posted NEOCP object, for instance, with no
automatic scraping layer in between.

``BaseTelescope`` implements the ephemeris/propagation math once, centrally, rather than
per-driver: named bodies resolve via ``astropy.coordinates.get_body`` with a JPL Horizons
fallback, and orbital elements propagate via a hand-rolled two-body Kepler/Barker solver — no
new third-party dependency (the obvious one, ``poliastro``, can't actually be installed
alongside this project's Python/astropy version requirements). A background task keeps
refreshing rate and position for whatever's being tracked, preferring a driver's native
``TrackingMode`` for Sun/Moon when available and falling back to ``ITrackingRate`` otherwise,
clamped against a driver's own ``TrackingRateCapabilities.min_update_interval`` if it
publishes one (read back via the new ``Comm.get_own_capabilities``, mirroring the existing
``get_own_state``).

``move_radec``/``move_altaz`` gained a documented side effect: they now reset tracking mode
to ``SIDEREAL``/``OFF`` respectively and stop any active body/orbital-element tracking, so a
mount left in a stale lunar/custom-rate mode from a previous target doesn't silently keep
applying it to an unrelated slew. ``DummyRaDecTelescope`` and ``DummyAltAzTelescope`` implement
all four new interfaces (``ITrackingMode``, ``ITrackingRate``, ``IPointingBody``,
``IPointingOrbitalElements``), so there's a real module to exercise a GUI or client against
without hardware.

Counted data sequences
-------------------------

Taking a sequence of N grabs (images, spectra, ...) no longer requires a client-side loop of
individual ``grab_data()`` calls. The new ``IDataSequence`` interface, implemented by
``BaseCamera``, adds a server-side counted sequence:

.. code-block:: python

   async with self.proxy("camera", IDataSequence) as camera:
       await camera.grab_sequence(10, delay=5)  # returns immediately, sequence runs in the background
       state = camera.get_state(IDataSequence)  # DataSequenceState(count_total, count_left, time)

       await camera.abort_sequence()  # graceful: lets the current grab finish, stops the rest
       # vs. the existing IAbortable.abort(), which now also clears a running sequence's count

``grab_sequence()`` is deliberately fire-and-forget rather than blocking for the whole
sequence: a blocking call's RPC timeout would have to scale with the caller-supplied count,
weakening it as a stall-detection sanity check the larger the count gets. Progress is instead
observed via the pushed ``DataSequenceState``, consistent with how the rest of live state
works. The optional ``delay`` (seconds between the end of one grab and the start of the next,
default ``0``) is skipped after the last grab and cut short immediately by either
``abort_sequence()`` or ``abort()`` instead of idling out the full wait. Dithering/offsets
between grabs remain out of scope -- that's a pointing-layer concern, not this interface's.

Access control (ACLs)
----------------------

Modules can restrict which callers may invoke which of their RPC methods via an ``acl:``
block next to their ``comm:`` config:

.. code-block:: yaml

   class: pyobs.modules.camera.MyCamera
   comm:
     class: pyobs.comm.xmpp.XmppComm
     jid: camera@example.com/pyobs

   acl:
     allow:
       scheduler: [expose, abort]   # scheduler may call only these two methods here
       mastermind: "*"              # mastermind may call anything
       # anyone else -> denied

A module with no ``acl:`` block is fully open, exactly like 1.x. ``allow`` is
least-privilege: the moment it's present, every caller not listed is denied, and an entry's
value may be a list of method names, ``"*"`` for unrestricted access, or the name of an
interface as shorthand for all of that interface's own methods. ``deny`` is the opposite
shape — coarse and whole-caller, for quarantining one or a few known-bad/untrusted callers
while leaving the module open to everyone else, including modules added to the fleet later:

.. code-block:: yaml

   acl:
     deny: [legacy_gui]   # everyone else keeps full access; legacy_gui is blocked entirely

``allow`` and ``deny`` are mutually exclusive on one module. A denied call raises
``exc.ForbiddenError`` (a ``RemoteError``), which maps to the XMPP IQ-level ``forbidden``
condition on the wire. Setting ``mode: log`` (default is ``mode: enforce``) runs the same
allow/deny decision but only logs what *would* have been denied and lets the call through —
useful for validating a new policy against real traffic before it can block a legitimate
caller:

.. code-block:: yaml

   acl:
     mode: log   # "enforce" (default) | "log"
     allow:
       scheduler: [expose, abort]

Any module can call ``IModule.get_permitted_methods()`` on another to ask, up front, which
methods it is currently allowed to call — exempt from ACL enforcement itself, so a denied
caller can still ask what it's denied from doing. Useful for UIs (``pyobs-gui``,
``pyobs-web-client``) that want to grey out or hide actions an operator can't use, instead
of only finding out via a ``ForbiddenError`` on an actual click. ACL scope is RPC only:
discovery, presence, and state subscriptions are unaffected by ``acl:`` blocks.

Other notable changes
----------------------

* A global ``pyobs.yaml`` config file is looked up (including under
  ``/opt/pyobs/storage/``) in addition to a module's own config file.
* ``pyobs`` and ``pyobsd`` support a ``--syslog`` flag.
* Fixed an XMPP reconnect storm after an ejabberd outage, and a module reconnect that could
  be silently dropped by a stale presence callback.

Upgrading
=========

If you maintain modules outside of ``pyobs-core`` (custom hardware drivers, scripts, or a
GUI/client), check for, in roughly descending order of how likely they are to affect you:

#. Any remaining ``await self.proxy(...)`` call sites — convert to
   ``async with self.proxy(...) as x:`` (see :ref:`proxy-async-with-only` above).
#. A top-level ``name:`` key in module YAML configs — remove it (use ``label:`` instead).
#. Any interface you *implement* that gained a ``state`` (see the table in
   `Removed and renamed interfaces / RPC methods`_) — publish it via
   ``self.comm.set_state(...)`` when the underlying value changes, rather than only
   answering the (now-removed) RPC getter.
#. Any interface you *call through a proxy* whose getter was removed — switch to
   ``get_state``/``wait_for_state`` or ``get_capabilities``.
#. If you run your own ejabberd server, apply the ``mod_pubsub`` config change above.
