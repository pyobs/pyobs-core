v2.0.0.dev18 (unreleased)
*************************
* Fixed ``UnclassifiedError.original_type`` silently not surviving the wire: ``Module.execute()``
  wraps a non-domain exception (``IndexError``, a vendor SDK exception, ...) as
  ``UnclassifiedError`` before ``rpc.py`` ever sees it, but ``fault_to_xml`` was serializing the
  wrapper's own class name instead of the original type it was tagged with -- since
  ``UnclassifiedError`` itself is a registered type, the caller reconstructed a fresh one with
  ``original_type`` never set, making a remote ``IndexError`` and a remote ``ValueError``
  indistinguishable. Now serializes the original type name instead, so the caller's own registry
  lookup runs against it and correctly repopulates ``original_type`` on the (still-unresolvable)
  ``UnclassifiedError`` it falls back to. Also fixed in the same pass: every exception crossing the
  wire had its message doubled (``"<ClassName> <ClassName> message"``) once displayed, because the
  message field serialized ``str(exception)`` (already ``"<ClassName> message"``) instead of the
  raw message, which reconstruction then fed back in as the new instance's own message before
  formatting it again.
* Docstring sweep across every interface flagged by the exception-handling audit (16 of 27
  documented interfaces had at least one mismatch) -- ``Raises:`` clauses now match what's
  actually raised: ``IFocuser``/``IPointingRaDec``/``IPointingAltAz``/``IPointingBody``/
  ``IPointingOrbitalElements``/the Heliocentric*/Helioprojective family gain
  ``NotSupportedError``/``MissingObserverError``/``AltitudeLimitError``/``BodyResolutionError``/
  ``InvalidOrbitalElementsError`` (or a note that they propagate from the underlying RA/Dec move);
  ``IAutoFocus``/``IAcquisition`` now document the types their own ``@raises`` already declared
  instead of a stale ``ValueError``; ``IData``/``IDataSequence`` document ``DeviceBusyError``;
  ``IFocusModel`` documents its three new leaf types; ``IExposureTime``/``IFlatField``/``IWeather``
  gain the clauses their implementations already needed. ``FlatField.set_filter``'s docstring
  copy-paste bug ("If binning could not be set" on a filter setter) is fixed. The handful of
  interfaces with zero concrete implementers anywhere in this repo (``ICalibrate``, ``ISyncTarget``,
  ``IMultiFiber.set_fiber``, ``IPointingSeries``, ``IRotation``, ``IScriptRunner.run_script``) gain
  a plausible ``Raises:`` clause so a future implementer has a contract to follow instead of
  guessing -- the same guess that produced several of the mismatches this sweep fixes. Documentation
  only, no behavior changes. Note: several interface methods still document plain ``ValueError``
  for bad-argument validation (as opposed to domain operation failures) -- deliberately not
  promoted to typed exceptions in this sweep; see ``DESIGN_exception_handling.md``'s "Still open"
  section for the tradeoff.
* Documented the ``AbortedError`` contract on every ``abort_event``-taking hook in
  ``pyobs-core`` (``BaseCamera``/``BaseSpectrograph._expose()``, ``BaseTelescope._move_radec``/
  ``_move_altaz``) -- nothing had ever told driver authors which type to use for "this was
  cancelled, not a real failure," so two of pyobs-core's own in-tree implementations
  (``DummyCamera``, ``DummySpectrograph``) had each independently guessed a different wrong type
  (``InterruptedError``, ``ValueError``) for the exact same condition. Both now raise
  ``exc.AbortedError``, as does ``_DummyTelescopeBase.set_focus``'s equivalent abort check. (Two
  more instances of the same guessed-wrong-type pattern, in ``pyobs-sbig``/``pyobs-fli``, are a
  companion fix in those repos, not something this PR can reach.)
* Documented the domain/transport split in ``pyobs/utils/exceptions.py`` as a deliberate axis:
  ``RemoteError`` and its subtree (``RemoteTimeoutError``, ``ForbiddenError``) mean "the call
  itself didn't reach/return," which doesn't benefit from the same fine-grained-per-reason
  treatment domain exceptions get -- documentation only, no behavior change.
* First sweep of concrete exception-typing gaps (goal 5: specific types over generic ones/bare
  builtins). New cross-cutting types in ``pyobs.utils.exceptions``: ``DeviceBusyError`` ("this
  device can't service this request right now, back off and retry") and ``NotSupportedError``
  ("this module doesn't implement this optional capability at all"). ``CameraException``
  (``BaseCamera``) and ``AcquireLockFailed`` (``LockWithAbort``, a plain ``Exception`` that leaked
  out of ``move_radec``/``move_altaz``/``set_focus``/``stop_motion``/roof ``init``/``park``
  unconverted) are retired -- both meant the same thing, "device busy," now unified as
  ``DeviceBusyError``. The telescope/roof ``init()``/``park()`` boundary specifically translates a
  lock-acquisition failure (or any other failure) into ``InitError``/``ParkError`` instead, per
  ``IMotion``'s own documented contract, following ``BaseCamera.__expose()``'s existing
  catch-and-translate pattern. Capability-check ``NotImplementedError`` sites (an alt/az-only
  telescope's ``move_radec``, ``ScienceFrameAutoGuiding.set_exposure_time``, a dummy telescope's
  ``set_focus_offset``) now raise ``NotSupportedError`` instead. ``BaseTelescope`` gained
  ``MissingObserverError``/``AltitudeLimitError``/``BodyResolutionError``/
  ``InvalidOrbitalElementsError`` (all ``MotionError``) for its previously-bare ``ValueError``
  sites. ``FocusModel`` gained ``WeatherDataError``/``FocusTimeoutError``/``MissingSensorError``
  (all ``FocusError``). New ``ScriptError`` (``pyobs.robotic.scripts``) wraps whatever a script's
  ``run()`` raises that isn't already a domain exception, following the same pattern;
  ``AutoFocusScript.can_run()`` now checks for a target itself instead of only discovering its
  absence after ``run()`` has already started. ``BaseVideo``/``BaseSpectrograph.grab_data()``'s
  "no image" ``ValueError`` sites now raise ``GrabImageError``, matching ``BaseCamera``. All new
  leaf types live next to the code that raises them (``basetelescope.py``, ``focusmodel.py``,
  ``pyobs.robotic.scripts``), not bolted onto ``exceptions.py``, now that the registry from the
  previous step lets a domain exception survive the wire regardless of which module defines it.
  Fifth step of the exception-handling rollout in ``DESIGN_exception_handling.md`` (tracks #446);
  remaining items in that sweep (``ScriptRunner``'s per-script leaves if ever wanted, driver-repo
  ``AbortedError``/``NotImplementedError`` fixes) are out of scope for a ``pyobs-core`` PR alone.
* RPC calls over XMPP now carry a correlation id end to end: the origin-side log line for a
  domain exception (``Module.execute()``'s catch block) includes ``(call_id=...)``, and the same
  id is attached to the exception the caller receives as ``exception.call_id`` -- reusing
  XEP-0009's existing per-call ``iq["id"]`` rather than adding new plumbing. Lets an operator
  debugging a caller-side ``FocusError`` jump straight to the matching detailed log on the module
  that actually raised it, instead of neither side's log line pointing at the other. Purely
  additive, no migration required; not set for ``LocalComm``/``MultiModule`` calls, which are
  already in the same log stream as the caller. Fourth step of the exception-handling rollout in
  ``DESIGN_exception_handling.md`` (tracks #446).
* Constructing a ``PyobsError`` is now side-effect-free, ordinary Python. ``raise
  exc.FocusError(...)`` always raises a ``FocusError`` -- it no longer risks silently coming back
  as a ``SevereError`` instead, which could happen because the old severity-escalation metaclass
  intercepted *construction*, not raising or catching. ``SevereError`` is retired entirely: nothing
  in this repo or any sibling project ever caught it specifically, its only real consumer was
  ``register_exception``'s ``callback`` (already used everywhere; production code never actually
  set ``throw=True``), which already does the meaningful part itself (``set_state(ModuleState.ERROR)``).
  ``register_exception``/``handle_exception`` move from module-level free functions with
  process-global state to ``Module._register_exception()``/an internal ``_record_exception()``,
  called from ``Module.execute()``'s catch block (the same chokepoint that already classifies and
  logs) -- fixing a real cross-instance bug as a byproduct, where two ``Module`` instances in the
  same process (e.g. under ``MultiModule``, or two instances watching the same remote module) used
  to share one counter. Ten in-tree call sites plus one in ``pyobs-alpaca`` need the mechanical
  ``exc.register_exception(...)`` -> ``self._register_exception(...)`` rename (the ``throw``
  parameter is gone with the substitution it existed for). Also: any non-``PyobsError`` exception
  escaping a module's method body is now wrapped as ``UnclassifiedError`` right in ``execute()``,
  not only on the XMPP fault path, so ``LocalComm``/``MultiModule`` get the same safety net as XMPP;
  ``RPC._on_jabber_rpc_method_call`` no longer logs domain exceptions itself since ``execute()``
  already did (it still logs failures that never reach ``execute()``, like malformed RPC
  parameters). Third step of the exception-handling rollout in ``DESIGN_exception_handling.md``
  (tracks #446).
* A remote domain exception now arrives at the caller as its real type, catchable directly (e.g.
  ``except exc.FocusError:`` around a proxy call actually fires now) -- previously every remote
  failure, transport or domain, arrived wrapped in ``InvocationError`` (now retired entirely), so a
  caller could only catch the broad wrapper and manually unwrap ``.exception``. Exception classes
  are now resolved via a registry (``PyobsError.resolve()``, populated automatically via
  ``__init_subclass__``) instead of a ``getattr`` lookup restricted to ``pyobs.utils.exceptions``,
  so a domain exception can now live anywhere (a driver package, a ``pyobs-core`` submodule) and
  still survive the wire, keyed by fully-qualified name rather than bare class name. An exception
  that can't be resolved (a raw builtin, a vendor SDK exception, or a domain type whose defining
  module was never imported in this process) arrives as the new ``UnclassifiedError`` instead of
  silently degrading to a generic ``RemoteError`` with only the message surviving -- the original
  type's qualified name is preserved as ``UnclassifiedError.original_type``. ``UnclassifiedError``
  joins ``ModuleError``/``SevereError`` as unsuppressible and always-loud.
  ``PyObsError`` is renamed to ``PyobsError`` (naming consistency with ``PyobsArchive``,
  ``PyobsCLI``, etc.) and its constructor is now ``PyobsError(message=None, **context)``, storing
  every keyword generically as an attribute -- ``RemoteError``/``RemoteTimeoutError``/
  ``ForbiddenError`` no longer have their own constructors, so direct construction now takes
  ``module=``/``sender=``/``method=`` as keywords instead of fixed positional arguments. Breaking
  change for any external code constructing these directly, catching ``exc.PyObsError``/
  ``exc.InvocationError`` by name, or relying on a remote failure always arriving as some
  ``RemoteError`` subclass (``pyobs-gui``'s ``base.py``/``mainwindow.py`` reference ``PyObsError``
  by name and need the rename applied). Second step of the exception-handling rollout in
  ``DESIGN_exception_handling.md`` (tracks #446).
* Every RPC-exposed method raising a domain ``PyobsError`` now logs a quiet INFO line locally by
  default, without a traceback -- previously this only happened for methods explicitly decorated
  with ``@raises(...)`` (used on exactly two methods), and every other domain exception logged at
  ERROR with a full traceback despite the caller already receiving the same error. ``@raises`` no
  longer controls log level (documentation value only, for now); ``Module`` gained
  ``_disable_exception_logging(*exception_types)`` for a module to opt a high-frequency exception
  type out of even the quiet line entirely, since the caller already has it.
  ``ModuleError``/``SevereError`` are exempt from both the quiet default and the opt-out -- they
  always log loudly, since both mean "this needs a human's attention at the source," not "an
  anticipated domain failure." Part of the first step of the exception-handling rollout in
  ``DESIGN_exception_handling.md`` (tracks #446).
* ``ICamera``/``ISpectrograph`` no longer inherit ``IExposure`` -- they're now pure ``IData``
  identity interfaces ("this module produces images/spectra"), not "...and has an exposure
  clock." ``BaseCamera`` and ``BaseSpectrograph`` (which push real ``ExposureState``) now declare
  ``IExposure`` explicitly instead of getting it for free; ``PipelineCamera`` drops ``IExposure``
  entirely instead of publishing a fabricated, never-updated ``ExposureState`` for a pipeline run
  that has no exposure to report progress on. Breaking change for any external module that
  subclasses ``ICamera``/``ISpectrograph`` directly (not via ``BaseCamera``/``BaseSpectrograph``)
  and relied on inheriting ``IExposure`` implicitly -- it needs to add ``IExposure`` to its own
  bases now if it actually wants to publish exposure state (e.g. ``pyobs_iagvt``'s ``SunCamera``,
  tracked separately, not fixed here). ``pyobs-gui``'s ``CameraWidget`` needs no change: its
  exposure-progress panel was already conditional on ``has_proxy(..., IExposure)``. See
  ``DESIGN_ICamera_IExposure.md``.
* Added ``IDataSequence`` (``grab_sequence()``/``abort_sequence()``, pushed ``DataSequenceState``)
  for taking a counted sequence of grabs in one call instead of driving a client-side loop of
  ``grab_data()`` calls. Implemented by ``BaseCamera``. ``grab_sequence()`` returns immediately and
  runs the sequence in the background; ``abort_sequence()`` stops after the current grab finishes,
  while the existing ``abort()`` now also cancels the rest of a running sequence. ``grab_sequence()``
  also takes an optional ``delay`` (seconds between grabs, default ``0``), skipped after the last
  grab and cut short by either abort path.
* Removed ``pyobs.modules.utils.AutonomousWarning`` (played warning sounds while an ``IAutonomous``
  module was running). Found while writing tests for it: ``started_sound``/``stopped_sound`` were
  stored but never read anywhere, and ``_check_autonomous()``'s sound selection looked inverted (it
  logged "Robotic systems started" but played ``stop_sound``, apparently copy-pasted from
  ``_check_trigger()``'s toggle logic without adjusting the polarity) -- breaking change for anyone
  using it, no replacement provided.
* ``Object.location`` is now derived from ``Object.observer`` instead of being stored and propagated to
  child objects independently, removing a source of location/observer divergence. The ``location``
  constructor argument is unchanged, but only affects the default ``observer`` built from it.
* Fixed ``DummyTelescope.set_focus_offset`` (now ``DummyRaDecTelescope``/``DummyAltAzTelescope``/
  ``DummySolarTelescope``, see below) silently logging an error instead of raising, which made
  remote callers see a false success; its M1/M2 temperatures now drift like ``DummyCamera``'s sensors
  instead of staying static after startup.
* Split ``DummyTelescope`` into ``DummyRaDecTelescope`` (+``IOffsetsRaDec``), ``DummyAltAzTelescope``
  (+``IOffsetsAltAz``), and ``DummySolarTelescope`` (+``IPointingHeliocentricPolar``,
  ``IPointingHeliographicStonyhurst``, ``IPointingHelioprojective`` -- always tracks the Sun via a
  dedicated background task, no compatibility alias for the old class name). See
  ``dummy-telescope-split-design.md``.
* Renamed ``IPointingHGS`` to ``IPointingHeliocentricPolar`` and its fields from ``lon``/``lat`` to
  ``mu``/``psi``, matching the existing ``HeliocentricPolarTarget`` -- the old fields actually
  represented Heliographic Stonyhurst coordinates, a different frame; breaking change for any
  external driver implementing it (e.g. ``pyobs_iagvt``, tracked separately).
* Reintroduced the old ``IPointingHGS`` lon/lat contract as ``IPointingHeliographicStonyhurst``, now
  a separate interface from ``IPointingHeliocentricPolar`` instead of a repurposing of it -- drivers
  needing Heliographic Stonyhurst tracking (e.g. ``pyobs_iagvt``'s ``SolarTelescope``) should
  implement this one instead.
* ``pyobsd`` now defaults to sending module logs to the systemd journal (``--syslog`` is on by
  default; pass ``--no-syslog`` to disable it).
* Added ``pyobsd logs [module] [journalctl arguments...]``, a thin passthrough to ``journalctl``
  filtered to the module's journal fields.
* Added ``Image.trim()``, unifying three previously-independent implementations of TRIMSEC parsing
  (inline in ``ProjectedOffsets``, ``fitssec()``, and ``Pipeline.trim_ccddata()``) into one method
  that also keeps ``mask``/``uncertainty`` aligned with ``data``. Shifts ``CRPIX1``/``CRPIX2`` to
  account for the new origin -- a correctness fix, since none of the three prior implementations
  did this, silently leaving a stale WCS reference pixel after trimming. Raises ``ValueError`` if
  a catalog is already attached, since its pixel coordinates would otherwise silently go stale
  against the trimmed frame -- run source detection after trimming, not before. Removed
  ``Pipeline.trim_ccddata()``; its two call sites now trim the ``Image`` before converting to
  ``CCDData`` instead of after -- breaking change for any external code calling it directly.
  ``fitssec()``'s parser is now shared (``pyobs.utils.fits.parse_section_bounds``) and raises a
  well-defined ``ValueError`` for a malformed section keyword instead of an arbitrary
  ``IndexError``/``ValueError``. See ``DESIGN_Image_trim.md``.

v2.0.0.dev17 (2026-07-11)
*************************
* Added a ``/ping`` health-check endpoint to ``HttpFileCache`` and ``BaseVideo``, for verifying HTTP
  connectivity without touching the file/image cache.

v2.0.0.dev16 (2026-07-10)
*************************
* Added ``IStructuredConfig``, letting a module push/apply its whole config dataclass as a unit
  (schema auto-derived via ``dataclass_to_schema``), complementing ``IConfig``'s per-field get/set.
* Added ``pydantic_to_schema``, the Pydantic-model counterpart to ``dataclass_to_schema``, for module
  configs (e.g. pyobs-iagvt's ``FTSConfig``) that need Pydantic's own validation.
* Renamed ``HeliocentricPolar`` to ``HeliocentricPolarTarget`` for naming consistency.
* Replaced ``HelioprojectiveRadialTarget`` with ``HelioprojectiveTarget``, using the Helioprojective
  frame's Tx/Ty (arcsec) directly instead of a radial (psi/delta) representation.

v2.0.0.dev15 (2026-07-10)
*************************
* Fixed ``HttpFileCache`` rejecting uploads with "413 Request Entity Too Large" because
  ``client_max_size`` was never passed through to configure the upload limit.

v2.0.0.dev14 (2026-07-09)
*************************
* Fixed ``Scheduler``, ``Trigger``, ``Kiosk``, ``PointingSeries``, ``Weather``, ``MockWeather``, and
  ``Mastermind`` never publishing their advertised ``IRunning`` state, leaving subscribers retrying
  indefinitely.
* The LCO schedule backend now logs the next observation after a schedule update, matching
  ``BackendObservationArchive``.

v2.0.0.dev13 (2026-07-09)
*************************
* Internal fixes only: resolved the remaining pyrefly type-check errors blocking CI.

v2.0.0.dev12 (2026-07-09)
*************************
* Added ``HelioprojectiveRadialTarget`` for solar coordinate scheduling.
* Added ``MockWeather``, a deterministic in-memory ``IWeather`` implementation for tests and
  simulations.
* ``IAcquisition``/``IAutoGuiding`` now publish live state (``AcquisitionState``/``AcquisitionAttempt``,
  ``GuidingState``); fleshed out their dummy modules to match.
* ``AcquisitionResult``/``AcquisitionAttempt`` now use a single ``offset_frame`` (RA_DEC/ALT_AZ) plus
  ``offset_lon``/``offset_lat`` instead of four separate ``off_ra``/``off_dec``/``off_alt``/``off_az``
  fields, and attempts track the 2D offset per iteration.
* ``ApplyOffsets`` (and its RA/Dec and Alt/Az subclasses) now return an ``OffsetResult`` with the
  actually-applied correction instead of a bare ``bool``.
* ``IMode.set_mode`` now takes a group name instead of a positional index.
* Added ``IRunning`` support to ``IAutoFocus``/``DummyAutoFocus``.
* Implemented script dispatch for the ``SCRIPT`` config type (``LcoScript``), selecting a nested
  script via ``extra_params.script_name``.
* Fixed context (``comm``/``observer``/``vfs``) not being propagated to ``Portal``,
  ``LcoScheduleReader``/``LcoScheduleWriter``, and ``LcoTask`` when constructed directly, which broke
  proxy lookups.
* Fixed a missing ``request`` field causing LCO script validation to fail.
* Fixed ``BaseVideo`` never publishing ``IImageType`` state (unlike ``BaseCamera``).
* Made the ``telegram`` import lazy in the ``Telegram`` module, so it's no longer a hard dependency
  for unrelated modules in ``pyobs.modules.utils``.
* Added a "What's New in pyobs 2.0" docs page tracking user-facing changes for the 2.0 release.

v2.0.0.dev11 (2026-07-05)
*************************
* Implemented access control (ACLs) for module RPC calls, via an ``acl:`` config block next to
  ``comm:`` (``allow``/``deny`` policy, ``enforce``/``log`` mode, ``IModule.get_permitted_methods()``).
* Completed the ``Unit`` annotation rollout across all applicable interface signatures.
* Interface and event schemas, including versioning, are now fully published via service discovery
  (disco#info), enabling a mixed-version-fleet diagnostic.
* ``IAcquisition.acquire_target()`` now returns a typed ``AcquisitionResult`` instead of
  ``dict[str, Any]``.
* ``Module``'s constructor no longer takes a ``name`` parameter; a module's name always tracks its
  ``comm`` object's own identity (XMPP JID / ``LocalComm`` name) instead.
* Added ``--syslog`` to ``pyobsd``, forwarding it to the ``pyobs`` processes it launches.
* A module now shuts down gracefully instead of endlessly reconnecting when kicked from XMPP due to
  a JID conflict.
* Fixed an XMPP reconnect storm after an ejabberd outage, and a module reconnect that could be
  silently dropped by a stale presence callback.
* Fixed ``DummyTelescope.park()`` not stopping an in-progress slew.
* Fixed a crash when a cooling setpoint or config name is ``None``.
* Fixed CRITICAL log lines being journaled with the wrong priority under ``--syslog``.
* Hardened RPC parameter parsing (``xml_to_params``) against malformed input.
* Fixed phantom XMPP state subscriptions for composite interfaces.
* A global ``pyobs.yaml`` config file (including under ``/opt/pyobs/storage/``) is now looked up in
  addition to a module's own config file.

v2.0.0.dev10 (2026-07-02)
*************************
* Interface features are now version-tagged in service discovery, giving a diagnostic for
  mixed-version fleets.
* ``IAutoFocus.auto_focus()`` now returns ``AutoFocusResult`` instead of a tuple; added live
  ``AutoFocusState``; removed the old ``auto_focus_status()``.
* Added ``OptimalFocusState`` for structured focus-model state tracking.
* ``IWeather`` migrated to structured live state; dropped ``station`` from sensor readings.
* ``IFitsHeaderBefore``/``IFitsHeaderAfter`` now return ``dict[str, FitsHeaderEntry]`` instead of
  ``dict[str, tuple[Any, str]]``.
* Removed the old XML-RPC cast pipeline (``pyobs.utils.types``).

v2.0.0.dev9 (2026-07-01)
************************
* Linked all ``pyobs-*`` module docs, now hosted on docs.pyobs.org.

v2.0.0.dev8 (2026-07-01)
************************
* Documented optional extras and CLI tools in the README.

v2.0.0.dev7 (2026-07-01)
************************
* Minor internal fixes (Dependabot configuration, import scoping in ``DummyCamera``).

v2.0.0.dev6 (2026-06-30)
************************
* Renamed the ``state``/``capabilities`` proxy accessor methods to ``get_state``/``get_capabilities``
  for clarity; both are now also available directly on ``Interface``.
* Added IERS offline mode support via the ``PYOBS_IERS_OFFLINE`` environment variable.
* The ``pyobs`` service now loads environment variables from ``/etc/default/pyobs``.
* Added ``astropy-iers-data`` as a direct dependency.

v2.0.0.dev5 (2026-06-30)
************************
* Refactored ``capabilities`` handling for consistency across interfaces.

v2.0.0.dev4 (2026-06-29)
************************
* Interface ``State`` classes are now module-level dataclasses rather than nested classes.

v2.0.0.dev3 (2026-06-29)
************************
* Removed ``pyobs.utils.simulation`` (``SimWorld``/``SimTelescope``/``SimCamera``) with no
  replacement.
* Added ``DummyVideo`` for simulated video streaming.
* ``IMode`` now uses ``capabilities``/``state`` dataclasses instead of separate mode-group methods.
* Added an optional ``sender`` attribute to ``LogEvent``.

v2.0.0.dev2 (2026-06-29)
************************
* Rolled out live state to (almost) all state-bearing interfaces; removed the corresponding
  ``get_*``/``is_*`` RPC methods project-wide in favor of subscribing to state.
* Added a shared XML serializer for both RPC and state payloads
  (``pyobs.comm.xmpp.serializer``); rewrote the XMPP RPC layer on top of it.
* Added ``Proxy.wait_for_state`` (returns cached state immediately, or waits for the first update).
* Added ``capabilities`` — fixed-for-lifetime values published via service discovery, alongside the
  new ``state`` mechanism.
* A module's online/ready/error status is now tracked via XMPP presence rather than RPC; removed
  ``IModule.get_state()``/``get_error_string()``.
* ``LocalComm`` gained state, capabilities, and presence support to match ``XmppComm``.
* Removed ``ILatLon`` and the never-implemented ``DbusComm`` backend.

v2.0.0.dev1 (2026-06-22)
************************
* Added ``version`` (default ``1``) to ``Interface`` and ``Event``.
* ``Proxy`` is now obtained via ``async with self.proxy(...) as x:`` only; the long-lived
  ``await self.proxy(...)`` pattern and the ``cache_proxies`` option are removed. Added
  ``has_proxy``/``safe_proxy``.
* Added ``Unit`` annotations for physical quantities on interface signatures.
* Added the first live **state** implementation over XMPP PubSub, piloted on ``ICooling``.

v1.53.0 (2026-06-19)
********************
* Replaced the threading-based XMPP client internals with asyncio throughout.
* Added ``--syslog`` to log to the systemd journal, for both ``pyobs`` and ``pyobsd``.
* ``pyobsd`` now names each module's log file after its config file (e.g. ``camera.yaml`` →
  ``camera.log``) instead of a fixed name, and takes its default module name from the config file.
* Added ``ObservationState.WINDOW_EXPIRED``.
* Added ``HelioprojectiveRadialTarget``.
* The scheduler now guarantees a minimum scheduling window length and excludes the currently-running
  task from "is there a better task" checks.
* Made XMPP message sending more robust: queues messages, skips repeated ones, and checks whether
  the user is actually logged in.
* Fixed object-ownership tracking so an ``ObservationArchive`` is only registered as a child once.
* Various performance improvements (lazy imports to reduce memory consumption, a fast path for
  transit-window calculation).

v1.52.0 (2026-06-13)
********************
* Added ``TransitImagingScript`` for imaging around a target's transit.
* ``estimate_duration`` now takes ``task``/``time`` parameters and can compute full-transit
  durations.
* Added ``ExposureTimeProvider`` (and ``StellarExposureTimeProvider``) for dynamic per-exposure
  timing in ``ImagingScript``.
* Rewrote ``pyobsd`` to no longer depend on ``start-stop-daemon``; prints subprocess stdout/stderr
  if a module fails to start.
* Added a GitHub Actions integration-test run triggered on release.
* Removed the tornado-based logger handling in favor of slixmpp's own logging.
* The scheduler now only fetches pending and in-progress observations rather than everything.

v1.51.0 (2026-06-09)
********************
* ``Script.can_run`` can now report a reason via ``cant_run_reason``, surfaced by the mastermind
  when skipping a task.

v1.50.0 (2026-06-09)
********************
* Moved the robotic storage backends (filesystem, HTTP backend, LCO) into their own
  ``pyobs.robotic.storage`` subpackage.
* Added an in-memory ``TaskArchive``/``ObservationArchive`` implementation, useful for testing.
* Added ``Comm.has_module``.
* ``Time`` is now imported from ``pyobs.utils.time`` instead of ``astropy.time`` throughout.
* Added ``Constraint.filter_skycoord`` for faster constraint filtering.
* Fixed a proxy deduplication bug.

v1.49.0 (2026-06-08)
********************
* Added a ``time`` parameter to ``ObservationArchive.get_schedule`` and ``get_current_observation``
  across all backends (filesystem, HTTP backend, LCO).
* Log timestamps are now formatted as ISO 8601.

v1.48.0 (2026-06-07)
********************
* Switched linting from flake8 to ruff and fixed the resulting warnings project-wide.
* Replaced broad ``except Exception`` catches with narrower exception handling in several places.
* Changed log calls to use lazy (``%``-style) argument evaluation throughout.
* Renamed ``ensure_feature`` to ``create_task``.

v1.47.0 (2025-06-07)
*********************
* Set minimum Python version to 3.11.
* Replaced old-style type hints (``Optional``, ``Union``, ``List``, etc.) with modern Python 3.11+ syntax throughout.
* Replaced deprecated ``asyncio.ensure_future`` with ``asyncio.create_task``.
* Replaced deprecated ``asyncio.get_event_loop`` with ``asyncio.get_running_loop``.
* Replaced ``str, Enum`` with ``StrEnum`` throughout.
* Replaced ``asyncio.gather`` with ``asyncio.TaskGroup`` where applicable.
* Added ruff linting to CI and pre-commit.

v1.46.0 (2025-05-27)
*********************
* Added ``DynamicTarget`` class for runtime target selection via a pluggable ``Picker`` interface.
* Added ``CsvPicker`` for selecting targets from a CSV catalogue, with constraint-aware filtering.
* ``OnDemandScheduler`` now resolves dynamic targets before evaluating constraints and merits.
* Added ``direction`` parameter to ``SolarElevationConstraint`` for filtering on rising or setting sun.
* Resolved target is now stored on ``Observation`` and restored by the mastermind via ``fetch_task``.
* Target resolution result is cached per scheduling run.
* Added ``set_resolved_target`` and ``estimate_duration`` to ``Task``.
* ``LcoTaskRunner`` now correctly injects script before ``run_task``.
* Added missing abstract method implementations to ``LcoTaskArchive`` and ``LcoObservationArchive``.
* Fixed inverted ``PENDING`` filter in ``LcoTaskArchive.get_schedulable_tasks``.
* Fixed ``LcoConfiguration.state`` default to ``"PENDING"``.
* Portal now creates aiohttp session in ``open()`` instead of ``__init__()``.
* Portal now managed via ``add_child_object`` for correct lifecycle.
* Fixed ``SolarElevationConstraint`` direction logic using ``observer.midnight``.
* Added ``AstroplanScheduler`` tests; fixed empty block list causing subprocess hang.
* Fixed ``LcoRequest.location`` field name conflict with ``BaseModel.location``.
* Added ``ImagingScript`` for standard science exposures with acquisition and guiding support.
* Comprehensive test suite additions for LCO classes, scheduler, and scripts.

v1.45.0 (2025-05-14)
*********************
* Added unified ``get_observations`` interface to ``ObservationArchive`` with state and time filters.
* ``IntervalMerit`` and ``PerNightMerit`` now push filters directly to ``get_observations``.
* Added ``ObservationArchiveEvolution.get_observations`` method.
* Added ``min_safety_time`` parameter to ``Mastermind``.
* Added ``active`` field to ``Task``.
* Fixed telescope not stopping after auto focus.

v1.44.0 (2025-04-24)
*********************
* Renamed ``SubClassBaseModel`` to ``PolymorphicBaseModel``.
* Renamed ``MeritScheduler`` to ``OnDemandScheduler``.
* Moved ``utils.archive`` and ``utils.skyflats`` into ``robotic.utils`` as pydantic models.
* Moved ``serialization.py`` from ``robotic.utils`` to ``utils``.
* Converted ``SkyFlatsBasePointing``, ``SkyflatPriorities``, ``Archive``, and ``PyobsArchive`` to ``PolymorphicBaseModel``.
* Removed ``Object`` from ``Script`` base classes.
* Context injection now propagates to all child pydantic models.
* HTTP requests now use pagination; all list responses wrapped in ``{"results": [...]}`` format.
* Added ``create_script`` method to ``Task``.
* Added ``http_request_with_retries`` with tenacity-based retry logic.
* ``BaseModel`` no longer inherits from ``Object``.
* Added ``trigger_on_every_update`` parameter to ``Scheduler`` module.
* Added Observation priority field.
* Major documentation overhaul for the robotic subsystem.

v1.43.0 (2025-04-20)
*********************
* Added ``http_request_with_retries`` utility.
* Backend archives now use ``http_request_with_retries`` instead of direct HTTP calls.
* Added ``ignore_cert_errors`` parameter to backend archives.
* Added filesystem-based backend for robotic scheduling (``YamlTaskArchive``, ``YamlObservationArchive``).
* Fixed ``inject_class_on_serialization`` for pydantic models.

v1.42.0 (2025-03-08)
*********************
* Backend archives migrated from ``requests`` to ``aiohttp``.
* Observation fetching moved to a background task.
* Task changes now driven by ``on_tasks_changed`` callback.
* Refactored robotic subsystem to support pluggable backends.

v1.41.0 (2025-02-20)
*********************
* Added optional Qt widget dependencies for GUI support.
* Added general-purpose Qt widgets.

v1.40.0 (2025-02-10)
*********************
* XMPP communication now connects with TLS using slixmpp 1.4.1.
* Fixed PyPy compatibility issues.
* Added ``AvoidMoon`` constraint.
* Added ``FromList`` grid filter.
* ``PerNightMerit`` now uses last sunrise for night boundary.
* Auto focus now uses actual measured focus position.

v1.39.0 (2024-12-10)
*********************
* Major scheduler refactoring: introduced pluggable scheduler architecture.
* Added ``OnDemandScheduler`` (merit-based greedy scheduler) with ``DataProvider`` context.
* Added ``ABORTED``, ``IN_PROGRESS``, and ``FAILED`` observation states.
* Added ``ConfigurationSummary`` to LCO integration.

v1.38.0 (2024-11-05)
*********************
* Added config file support via ``--config`` flag.
* Added InfluxDB logging handler.
* Added ``CommLoggingHandler`` guard against duplicate logger registration.
* Added ``--verbose`` CLI switch.

v1.37.0 (2024-10-20)
*********************
* Added InfluxDB logging handler (``InfluxLoggingHandler``).

v1.36.0 (2024-10-05)
*********************
* Improved exception handling in background tasks; ``BackgroundTask`` now receives parent reference.
* Unknown remote exceptions now wrapped in ``RemoteError``.
* Added SSL check option for XMPP.
* Fixed: don't reconnect after intentional XMPP disconnect.
* Added example systemd service file.

v1.35.0 (2024-09-01)
*********************
* Added ``--verbose`` switch to CLI.
* Added ``CALIBRATING`` motion status.
* Refactored shell command handling into dedicated classes.

v1.34.0 (2024-08-20)
*********************
* Refactored shell command and response into dedicated ``ShellCommand`` classes.

v1.33.0 (2024-08-05)
*********************
* Added new grid creation for pointing series.
* Configurable wait times in pointing module.

v1.32.0 (2024-07-20)
*********************
* Moved exceptions to a dedicated module.
* Added ``AcquisitionError`` for failed acquisitions.
* Changed ``GeneralError`` to ``FocusError`` for focus-related errors.
* Added 60s timeout to autoguider stop method.
* LCO integration: use ConfigDB to fetch instrument; support multiple configurations.

v1.31.0 (2024-05-25)
*********************
* Added documentation for image processors.
* Registered ``pyobs`` exceptions now logged as ``INFO`` without stack trace.
* Added ``overwrite`` parameter to image writing.
* Added Matrix chat client module.

v1.30.0 (2024-05-01)
*********************
* Added Matrix chat client module.
* Fixed context propagation for non-dict objects.
* Added reset method to ``BrightestStarGuiding``.
* Added ``oneshot`` parameter to ``ScriptRunner``.
* Added logging when a script cannot run.

v1.29.0 (2024-03-15)
*********************
* Added ``PipelineCamera`` for running image pipeline on camera images.
* Added ``Flip`` image processor.
* Added TypeScript interface export.
* Added ``HttpServer`` to serve images via HTTP.
* Added ``SolarHelioprojective`` image processor.
* Added ``Pipeline`` module.

v1.28.0 (2024-02-20)
*********************
* Added offset parameter to ``IGain``.
* Reduced httpx logging verbosity.

v1.27.0 (2024-02-01)
*********************
* ``FilenameFormatter`` now supports formatting with FITS headers via ``GetFitsHeaders``.

v1.26.0 (2024-01-15)
*********************
* Added comprehensive typing throughout using ``TypedDict`` and ``npt.NDArray``.
* Improved ``get_object`` overloads.

v1.25.0 (2024-01-01)
*********************
* Migrated build system to ``uv``.
* Pointing module updated to use new grid classes.

v1.24.0 (2023-12-30)
*********************
* Added new spherical grid classes (``RegularSphericalGrid``, filters, pipeline) with tests.

v1.23.0 (2023-12-29)
*********************
* Improved spilled light guiding sigmoid function for more accurate relative offset calculation.
* Added weather station workaround.

v1.22.0 (2023-12-29)
*********************
* Added ``auto_focus`` integration to relevant modules.

v1.21.0 (2023-12-28)
*********************
* Added ``init_offset_to_zero`` functionality.
* Spilled light guiding: added binning correction, image trimming, and improved calculations.

v1.20.0 (2023-12-28)
*********************
* VFS not created if none is configured.
* Added pixel offset image processor for simplified acquisition workflow.
* ``get_object`` no longer overwrites existing parameters.

v1.19.0 (2023-12-28)
*********************
* Added spilled light guiding processor.
* Added ``IMultiFiber`` interface.

v1.18.0 (2023-12-28)
*********************
* ``ITelescope`` no longer directly implements ``IPointingRaDec``/``IPointingAltAz``; ``BaseTelescope`` handles dispatch.
* Added bright star guiding.
* Restore initial focus if focus series fails.

v1.17.0 (2023-12-28)
*********************
* Added ``DummyMode`` module and ``ModeChangedEvent``.
* Added ``ResolvableErrorLogger`` utility.
* Reactivated publisher module.
* Added XMPP auto-reconnect on connection loss.

v1.16.0 (2023-12-28)
*********************
* New ``pyobsd`` daemon with improved module management and config testing.
* Added several default scripts.
* Added group support for module configuration.

v1.15.0 (2023-12-28)
*********************
* Added group support for module configuration.

v1.14.0 (2023-12-28)
*********************
* Stop telescope after autofocus completes.
* Updated to Python 3.12; replaced deprecated ``datetime.utcnow()``.
* Warn when no RA/Dec given for pointing.

v1.13.0 (2023-12-28)
*********************
* Added acquisition support for bright central star.
* Added derotator offset handling.
* Added ``BackgroundTask`` class to simplify background task management in ``Object``.
* Added unit tests for ``BackgroundTask`` and ``Object``.

v1.12.0 (2023-12-28)
*******************
* Added `list` command for `pyobsd`, which outputs all configurations.
* Added bash auto-complete script `pyobsd`.
* Added timeouts (to be defined in the config) for `ScriptRunner` modules.


v1.11.0 (2023-12-25)
*******************
* Acquisition and AutoFocus both got a `broadcast` option to disable broadcast of images.
* AutoFocus got a `final_image` parameter to take a final image at optimal focus.


v1.10.0 (2023-12-24)
*******************
* Added CallModule script.
* Changed ScriptRunner module so that it can run a script multiple times.

v1.9.0 (2023-12-23)
*******************
* Added getters and safe getters for Image class.

v1.3.0 (2023-02-04)
*******************
* Adopted LCO default task to new LCO portal.

v1.2.0 (2022-10-06)
*******************
* Added AltAzOffsets and RaDecOffsets and (partly) implemented them in the ApplyOffsets classes.

v1.1.0 (2022-09-20)
*******************
* Changed signature of `pyobs.robotic.TaskSchedule.get_schedule` to have no parameters.

v1.0.0 (2022-09-13)
*******************

v0.22.0 (2022-08-25)
********************
* Removed comm.sleexxmpp implementation.
* Renamed comm.slixmpp to comm.xmpp.

v0.21.0 (2022-08-25)
********************
* Some pipeline stuff.
* Added DbusComm for communicating via Dbus.
* Cleaned up parameter casting for communication.

v0.20.0 (2022-06-22)
********************
* Some fixes with asyncio and the GUI.
* Handle JID conflicts in XMPP.

v0.19.0 (2022-05-17)
********************
* Getter/setter methods in Module must be async.
* get_task() in TaskScheduler is now async.
* Lots of bug fixes.

v0.18.0 (2022-03-13)
********************
* New IGain interface.

v0.17.0 (2022-02-14)
********************
* Restructuring robotic system.

v0.16.0 (2022-01-14)
********************
* Added new exceptions.
* Use those new exceptions to keep track of errors over time and raise SevereErrors.
* Add new state to module, so that a severe error can put a module into an error state.
* Added get_state() and get_error_string() methods to modules.

v0.15.0 (2021-12-29)
********************
* Added Comm implementation for SliXMPP (which should now be default) and moved old comm.xmpp to comm.sleekcmpp.
* Using asyncio throughout the project, all method and event handlers are async now, as well as open/close methods.
* Got rid of multi-threading as best as possible.
* VFS now also uses asyncio.

v0.14.2
*******
* Fixed a bug with Poetry

v0.14.1
*******
* Added possibility to use class hierarchy for events, i.e. subscribe to a class and receive all derived events.
* Change to Poetry as build system

v0.14 (2021-11-03)
******************
* Guiding modules accept a pipeline now, so more image processors than just Offsets can run.
* Renamed ICameraBinning, ICameraExposureTime and ICameraWindow and removed the "Camera" part.
* Added meta attribute (temporary storage, not I/O persistent) to Image.
* Extracted IImageGrabber from ICamera and renamed expose() to grab_image().
* Added new IVideo interface and a corresponding BaseVideo module.
* Raising exception, if XmppComm cannot connect to server, allowing for graceful exit.
* On shutdown, wait for hanging threads, and kill them after 30 seconds.
* Multi-processing for the pipeline, using ccdproc now.
* New interface IPointingSeries, giving access to methods at the telescope that support pointing series.
* Send logs in thread.
* Added concept of image processors that take an Image as parameter and return it after some processing.
* Added new NStarOffsets image processor (T. Masur).
* Improved scheduler.
* Added pipelines that take a list of image processors (see Pipeline mixin).
* Re-organized all get_object methods.
* Improved type hints throughout the code.
* Renamed all coordinated interfaces (IRaDec, etc) to IPointing*, i.e. IPointingRaDec.
* Renamed all offset interfaces to IOffsets*, i.e. IOffsetsRaDec.
* Renamed IFitsHeaderProvider to IFitsHeaderBefore and also renamed its only method.
* Added IFitsHeaderAfter to fetch FITS headers after an exposure as well.
* Moved functionality from Module to Object.
* New meta data system for images.
* Renamed IStoppable to IStartStop.
* Added new proxy interfaces in interfaces.proxies. All proxies now derive from these interfaces instead of the 
  original ones.
* And a lot more cleanup and re-organization.


v0.13 (2021-04-30)
******************
* Added a Telegram bot module.
* Added a module for a Kiosk mode, in which pictures are published on a webpage.
* Added new IImageFormats interface for cameras that support multiple ones (e.g. grayscale and color).
* Moved more enums into utils.enums, like WeatherSensors and MotionStatus.
* Added list_binnings() to IBinning interface and (temporary) default implementation in BaseCamera.
* Restructured image processors into pyobs.image.processors.
* Split photometry into separate SourceDetection and Photometry interfaces, added DaophotSourceDetection, and 
  PhotUtilsPhotometry.
* Sending events non-blocking, which might solve some problems with disappeared XMPP clients.
* Added lots of documentation, which included setting `__module__` for many classes.


v0.12 (2021-01-01)
******************
* Changed PyObsModule to Module.
* Removed possibility for network configs.
* Added MultiModule, which allows for multiple modules in one process.
* Flat scheduler: add options for readout times.
* New OnlineReduction module for reduction during the night.
* Fixed bug that sometimes appears in the interface caching for Comm.
* LcoTaskArchive: added MoonSeparationConstraint, fixed AirmassConstraint.
* Optimized Scheduler by only scheduling blocks that actually have a window in the given range.
* Added module Seeing that extracts FWHMs from the catalogs in reduced images and calculated a median seeing.
* Introduced concept of Publishers, which can be used to publish data to log, CSV, and hopefully later, database, 
  web, etc.
* Created new Object class that handles most of what Module did before so that Module only adds module specific stuff.
* Added some convenience methods for reading/writing files to VFS.
* Added new IConfig interface which is implemented in every module and allows remote access to config parameters 
  (if getter/setters are implemented).
* Removed count parameter from ICamera.expose().
* Removed exposure_time parameter from ICamera.expose() and introduced IExposureTime interface.
* Removed image_type parameter from ICamera.expose() and introduced IImageType.
* Moved ImageType enumerator from ICamera to utils.enums.


v0.11 (2020-10-18)
******************
* Major changes to robotic system based on LCO portal.
* Setting filter/window/binning in acquisition.
* Added WaitForMotion and Follow mixins.
* Added support for flats that don't directly scale with binning.
* New module for acoustic warning when autonomous modules are running.
* Improved SepPhotometry by calculating columns used also by LCO.
* New interface for Lat/Lon telescopes, e.g. solar telescopes.


v0.10 (2020-05-05)
******************
* Re-factored acquisition modules and added one based on astrometry.
* Added combine_binnings parameter to FlatFielder, which triggers, whether to use one function for all binnings or not
* Added get_current_weather() to IWeather
* New FlatFieldPointing module that can move telescope to a flatfield pointing
* Changed requirements in setup.py and put packages that are only required by a server module into [full]
* Removed HTTP proxy classes
* Some new mixins


v0.9 (2020-03-06)
*****************
* working on robotic system based on LCO portal


v0.8 (2019-11-17)
*****************
* Added module for bright star acquisition.
* Added and changed some FITS header keywords.
* Added module for flat-fielding.
* Changed some interfaces.
* Added basic pipeline.
* Started with code that will be used for a full robotic mode.
* Re-organized auto-guiding modules.
* and many more...