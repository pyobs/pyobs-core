v2.5.0
*********************
* Every module implementing ``IFitsHeaderBefore``/``IFitsHeaderAfter`` now writes one
  ``HIERARCH <MODULE> VERSION <PACKAGE>`` card per loaded ``pyobs-*`` package into FITS headers,
  reusing ``loaded_pyobs_packages()`` (added for #759). Closes #739. See
  ``specs/design/package_versions_fits_header.md``.
* Fixes ``Comm.unregister_event()`` not cancelling a handler dispatch that
  ``_send_event_to_module()`` had already scheduled via ``asyncio.create_task()`` before the
  unregister call -- the task ran later regardless, against whatever the handler was bound to
  (observed in pyobs-gui as a ``libshiboken: Internal C++ object already deleted`` error on
  client disconnect). Closes #871.

v2.4.1 (2026-09-03)
*********************
* Fixes ``Time.night_obs()`` flipping to the next night around dawn: it anchored the night
  boundary at "nearest sunset + 12h", which lands close to sunrise near the equinox -- exactly
  when morning calibration scripts run (e.g. ``DarkBiasScript`` queried the following night,
  with no science frames yet, instead of the one that just ended). Anchored at local solar noon
  instead, matching the archive's own night-labeling convention and not drifting with day length.
  Also affects ``Mastermind``'s night resolution and the ``DAY-OBS`` FITS header, which share the
  same call.

v2.4.0 (2026-09-03)
*********************
* **Breaking:** ``TaskScheduler.schedule()`` (both ``OnDemandScheduler`` and
  ``AstroplanScheduler``) gained a new ``instrument_capabilities: InstrumentCapabilities | None
  = None`` parameter, part of pyobs-core#864/#865's plumbing for feeding pyobs-portal instrument
  capability data into script duration estimates (see
  ``specs/plans/2026-09-01-instrument-capability-duration-estimates.md``). Any out-of-tree
  ``TaskScheduler`` subclass overriding ``schedule(tasks, projects, start, end)`` without the new
  keyword argument will raise ``TypeError`` once called by ``pyobs/modules/robotic/scheduler.py``'s
  ``_schedule_worker``, which now always passes it. Add the parameter to your override's signature
  (a default of ``None`` is enough if you don't use it) to stay compatible.
* Added ``InstrumentCapabilities`` (``pyobs/robotic/instruments.py``), mirroring pyobs-portal's
  instrument JSON with module-name-keyed camera/telescope/dome/filter-wheel capability lookups,
  and threaded it through ``TaskData``/``TaskArchive``/``Task.estimate_duration()``.
  ``PortalTaskArchive`` now polls and caches real capability data from ``GET /api/instruments/``
  (re-fetched only when pyobs-portal's ``last_instrument_update`` marker moves in either
  direction; a fetch/parse failure keeps serving the last-good data rather than blocking the
  tasks/projects poll). ``ImagingScript``, ``PointingScript``, ``DarkBiasScript``, and
  ``AutoFocusScript`` now use real portal-declared readout/filter-change/slew numbers where
  available, falling back to the previous flat fudge constants otherwise. See
  ``specs/plans/2026-09-01-instrument-capability-duration-estimates.md``.
* Fixes the ``Scheduler``'s ``get_schedule()``/``get_current_observation()`` permanently
  returning an empty schedule: forcing ``auto_update=False`` on the observation archive also
  silenced the poller that's the only channel by which the scheduler process learns about
  observation-state changes written by other processes (e.g. ``Mastermind`` marking an
  observation ``IN_PROGRESS``/``COMPLETED``). Added ``announce_updates`` to
  ``PortalObservationArchive`` instead, so the poller can stay on without double-logging its own
  writes.
* ``VFS`` gained ``rmdir()`` (``LocalFile``/``VirtualFileSystem``); ``ImageWatcher`` now removes
  now-empty parent directories left behind when it deletes a watched file.
* ``ImageWatcher`` only attempts FITS header parsing for filenames that look like FITS
  (``.fits``/``.fitz``/``.fits.gz``/``.fits.fz``); other watched/copied files no longer produce
  spurious astropy header-parse warnings.

v2.3.0 (2026-09-02)
*********************
* ``ImageWatcher`` gained a ``flatten=True`` (default) constructor option: set ``False`` to keep
  a non-templated destination file's path relative to ``watchpath`` instead of collapsing it to
  just the basename, so a whole nested directory tree can be relocated while preserving its
  structure. Also added recursive watching (inotify mode via asyncinotify's
  ``RecursiveWatcher``, poll mode, and the initial ``open()`` scan), so subdirectories are picked
  up too, not just the watched root. Fixed two pre-existing bugs while rewriting the poll loop:
  ``poll_interval`` was stored but never actually awaited between iterations (a busy-loop), and a
  stray debug ``print()`` was left in the new-file branch. (#860)
* Issue #855: ``PolymorphicBaseModel``'s custom serializer (used by ``Task``/``Script``/
  ``Constraint``/``Merit``/``Target`` and their subclasses) now honors ``exclude``/``include``/
  ``by_alias``/``exclude_none``/``exclude_unset``/``exclude_defaults`` on ``model_dump()``/
  ``model_dump_json()`` instead of silently ignoring them, for flat top-level field specs (the
  only pattern any current caller uses); a nested spec now raises ``NotImplementedError`` instead
  of being silently ignored or partially applied.
* Issue #844: ``Reduction``'s minimum-darks-per-group threshold is now configurable via
  ``min_darks_per_group`` (default 3, unchanged), matching the existing ``min_flats`` option.
* Issue #856: ``PortalTaskArchive._update()`` no longer counts a bare ``updated_at`` bump (e.g. a
  no-op re-save) as a real content change, which previously triggered an avoidable re-download
  and reschedule.
* Issue #851: ``DummyCamera`` gained an optional ``roof`` reference (mirroring the existing
  ``telescope`` reference) and now skips flat-field/star simulation, producing dark frames,
  while its ``DummyRoof`` is parked; fails closed until the roof's state has been received.
* Issue #848: ``Scheduler._update_schedule()`` now also reschedules on a project priority change
  or a same-ID task content change (e.g. priority), not just on task IDs appearing or
  disappearing; also fixes an assignment-order bug where ``self._projects`` was overwritten
  before it could ever be diffed. Follow-up review fixes: preserve the portal task FK when
  canceling (the cancel PUT was silently rejected every time otherwise), guard against a startup
  race between the observation- and task-archive pollers, and stop ``get_current_observation()``
  from self-healing an in-progress observation out from under a running ``Mastermind``.
* Issue #850: ``AltitudeLimitError`` no longer inherits from ``MotionError``, so refusing a
  below-horizon target no longer counts toward motion-fault escalation (3 legitimate rejections
  within 10 minutes used to push the module into ``ERROR`` state, requiring a manual
  ``reset_error()``).
* Issue #845: ``Module._on_module_opened`` and ``FocusSeries._run_focus_series`` now also catch
  the plain ``ValueError`` that ``Comm._resolve_proxy()`` raises (per its documented contract)
  when a proxy can't be resolved, instead of leaking it to the caller.
* Issue #847: ``Scheduler._update_schedule()`` no longer skips rescheduling on portal task
  removal (the observation-archive schedule-cache gate it relied on is permanently empty for
  ``PortalObservationArchive`` by construction). ``PortalObservationArchive`` also self-heals
  observations whose task the portal no longer resolves, canceling them locally and on the
  portal instead of logging-and-skipping forever.
* Issue #849: ``DummyRoof.stop_motion()`` now reports ``PARKED`` rather than ``IDLE`` on a closed
  roof, matching ``init()``/``park()``.

v2.2.0 (2026-09-01)
*********************
* Issue #832: ``Calibration``/``Reduction`` now match dark masters to a science frame's
  ``EXPTIME`` instead of always scaling whatever dark master ``find_master`` happened to return
  (see ADR ``0015-dark-master-strict-exptime-matching-reference-scale-down-only.md``). An exact
  exptime match (within ``dark_exptime_tolerance``, default 1%) is used unscaled; below
  ``dark_min_exptime`` (default 5s) with no exact match, calibration falls back to bias-only; a
  reference master (``dark_scale_exptime``, default 600s) is scaled down to shorter science
  exptimes but never scaled up.

  **Behavior change, upgrade check required:** a site that takes darks at only one exptime and
  previously relied on always-scale-whatever's-nearest now fails calibration (a caught,
  catchable ``ValueError``, logged and returned uncalibrated -- not a crash) for any science
  exptime longer than its one master, or with no reference configured. Set
  ``allow_unmatched_dark_scale=True`` to keep today's behavior, or take darks at more than one
  exptime (``DarkBiasScript``'s ``exptimes``/``match_science_exptimes``, issue #831) so exact
  matches exist. ``Reduction``'s master-calibration-frame filename pattern also gained an
  exposure-time component (``{EXPTIME|exptime}``, shared by BIAS/SKYFLAT too); existing archives
  keep their old-pattern masters under their original filenames.

  A reference master is also no longer scaled up (only down), and a legacy master with no
  ``EXPTIME`` in its header is now used unscaled instead of raising ``KeyError`` on the
  ``allow_unmatched_dark_scale`` fallback path.
* Issue #831: ``DarkBiasScript`` can now take one morning dark series per exposure time actually
  used by the night's science frames, instead of always a single fixed exptime. Adds
  ``science_exptimes_for_night()`` (derives per-instrument/binning exptimes from the night's
  ``OBJECT`` frames; exptimes below ``dark_min_exptime`` are dropped since calibration treats them
  as bias-only) and exposes ``EXPTIME`` on the archive API (``FrameInfo``, ``list_frames``/
  ``list_options``, both ``PyobsArchive`` and ``LocalArchive``) so it can be queried. Enable via
  ``DarkBiasScript``'s new ``exptimes``/``match_science_exptimes`` options.
* Added ``DummyStructuredConfig`` (``pyobs.modules``), implementing ``IStructuredConfig`` with one
  field of every ``ConfigFieldSchema`` type (str, int, a float with a unit, bool, enum, nested
  object) so pyobs-gui's new ``StructuredConfigWidget`` (gui#154) has something to manually verify
  against without pyobs-iagvt's FTS, the only other ``IStructuredConfig`` consumer.
* Fixes issue #830: ``http_request_with_retries`` no longer logs a WARNING on every failed retry
  attempt. Retries now stay quiet for the first 60s a URL has been failing (covering a typical
  short pyobs-portal restart), then warn at most once per minute until the request succeeds again.
  ``PortalTaskArchive``/``PortalObservationArchive``'s poll loops got the same treatment for their
  ``log.error`` calls: the first failure still logs immediately at ERROR, but repeats during the
  same outage are throttled to at most once per minute instead of once per ~20s poll cycle. Both
  reuse a new ``pyobs.utils.http.LogThrottle`` helper.

v2.1.0 (2026-08-31)
********************
* Added ``IRobotic`` (executor) / ``IRoboticScheduler`` (planner) interfaces, wired into
  ``Mastermind`` and ``Scheduler`` respectively (issue #825). ``IRobotic`` pushes ``RoboticState``
  (current task, next-up, ``cant_run_reason``) on every transition; ``IRoboticScheduler`` adds
  ``get_schedule(limit)``, returning pending/in-progress entries only, capped server-side
  regardless of the requested limit. ``TaskStartedEvent``/``TaskFinishedEvent``/``TaskFailedEvent``
  now also carry ``obsnum``. See ``specs/design/irobotic.md``.
* Added ``DummyMastermind``/``DummyScheduler`` (``pyobs.modules.robotic``), simulating a robotic
  schedule so pyobs-gui's new ``RoboticWidget``/``ScheduleWidget`` have real state transitions to
  develop and test against without live hardware.
* ``XmppComm`` now pre-creates a module's own event pubsub nodes at the moment it declares them
  (send-only ``register_event()``), instead of relying on the server's lazy auto-create-on-first-
  publish. Closes the window where a peer connecting before a module's first publish could never
  complete a subscribe (``item-not-found``) and had to fall back to an indefinitely retrying
  background task. State nodes are explicitly out of scope (see
  ``specs/plans/2026-08-28-precreate-pubsub-nodes.md``'s "Why state nodes are excluded" section).
* Fixes issue #824: ``_retry_delay``'s exponential backoff no longer raises ``OverflowError`` at
  high attempt counts (e.g. attempt 1024), and both event/state subscribe-retry background tasks
  now discard their tracked key/handler on an unexpected failure instead of leaving a permanently
  stuck "subscribed" marker behind with nothing actually subscribed and nothing retrying.
* Fixes issue #829: ``DummyCamera`` exposures were broken under the pinned photutils 3.0 --
  ``make_model_image`` looks up source positions by the model's own parameter names (``x_0``/
  ``y_0`` for ``Moffat2D``), not by the sources table's column names (``x_mean``/``y_mean``); now
  passes ``params_map`` to bridge the two.

v2.0.0 (2026-08-26)
*******************

v2.0.0.dev98 (2026-08-25)
=========================
* ``Observation`` gained an ``archive_url`` field (``str | None``, default ``None``), matching the
  computed link pyobs-portal#82 started returning from ``GET /api/observations/`` (a deep link into
  the archive's frontend for terminal observations; always ``None`` for the ``pending``/
  ``in_progress`` states Mastermind schedules on). Without it, the strict ``Observation`` model
  rejected the new key and ``PortalObservationArchive`` failed every download; the validation
  error was swallowed by ``_check_for_changes``'s retry handler, so the marker-gated poll loop
  stalled forever without ever picking up schedule changes. The field is portal-only UI metadata
  that Mastermind tolerates but never consumes.

v2.0.0.dev97 (2026-08-25)
=========================
* No pyobs-core code changes -- version bump only.

v2.0.0.dev96 (2026-08-25)
=========================
* **Breaking:** ``pyobs.robotic.storage.backend`` is renamed to ``pyobs.robotic.storage.portal``,
  and ``BackendTaskArchive``/``BackendObservationArchive`` are renamed to
  ``PortalTaskArchive``/``PortalObservationArchive``, following the ``pyobs-robotic-backend`` ->
  ``pyobs-portal`` rename (see ADR 0013,
  ``specs/adrs/0013-renaming-pyobs-robotic-backend.md``). There is no deprecation shim -- update
  the ``class:`` dotted path in any deployment YAML using the old names before upgrading.

v2.0.0.dev95 (2026-08-25)
=========================
* Added ``Field(description=...)`` to every field across all ``pyobs.robotic.scripts`` ``Script``
  subclasses and their nested config models (e.g. skyflat priorities) -- pyobs-robotic-backend's
  script builder renders each field's JSON-schema description as form help text, and none had one
  (``InstrumentConfig.image_type`` only appeared to, via a leaked ``ImageType`` enum docstring, now
  replaced with an explicit member listing). A new parametrized test guards every ``Script``/config
  field for a description going forward. Fixes #811. (#812)

v2.0.0.dev94 (2026-08-24)
=========================
* Fixed broken ``__module__`` overrides on ``PolymorphicBaseModel`` subclasses
  (``SkyFlatsBasePointing``, ``SkyflatPriorities``, ``Archive`` and its subclasses including
  ``LocalArchive``/``PyobsArchive``): a stale short path left over from an earlier
  ``pyobs.robotic.utils`` reorg made serialization, which keys on ``self.__module__``, produce
  unparseable dumps on reload (``ModuleNotFoundError``). Removed the overrides so ``__module__``
  reflects the real, importable path. Fixes #806.
* ``BaseVideo.raw_handler`` now caches the per-frame ``(meta, frame)`` bytes it builds
  (header assembly, JSON serialization, ``ascontiguousarray``/``tobytes()`` copy), keyed by
  ``_frame_num``. With N simultaneous raw clients (guiding, a recorder, a viewer -- a case
  the raw endpoint (``specs/design/basevideo-raw-frame-streaming.md``) already supports but
  didn't dedupe for), only the first consumer to wake for a given frame does the work; the
  rest reuse the cached result instead of redoing it (#769). Costs nothing with 0 or 1 raw
  clients connected.
* ``Mastermind.get_fits_header_before()`` now emits a ``PROJECT`` FITS keyword from
  ``Task.project``, alongside ``TASK``/``REQNUM``/``OBSNUM`` -- closes the last open item of the
  project-based access-control work for pyobs-archive (pyobs-archive#42; superseded by that repo's
  own more detailed plan, which already shipped the archive-side filtering).
* ``Script`` module-name fields (``pyobs.robotic.scripts``) are now tagged with their required
  ``pyobs.interfaces`` via ``Annotated`` metadata, letting pyobs-robotic-backend introspect
  ``FieldInfo.metadata`` to render interface-filtered module dropdowns instead of hand-maintaining
  a duplicate table (pyobs-robotic-backend#98). Fixes #808. (#809)

v2.0.0.dev93 (2026-08-23)
=========================
* ``ImageWatcher`` no longer blocks the event loop while processing watched files: per-file FITS
  parsing (``astropy.io.fits.HDUList.fromstring``) now runs via ``asyncio.to_thread()``, and all
  blocking ``LocalFile`` I/O (open/read/write/close/remove/find/exists) is routed through the
  default executor, mirroring the existing ``listdir`` pattern -- root cause of the 2026-08-20
  "Event loop stalled" incident on MONET South, where RPC handling, inotify processing, and comm
  keepalive froze for seconds during a slow parse. ``LocalFile``'s ``open()``/``makedirs`` moved
  from ``__init__`` into ``__aenter__`` (still validating the path synchronously at construction
  time), closing a gap for network-mounted watch paths; every VFS consumer inherits the fix, not
  just ``ImageWatcher``. See ``specs/plans/2026-08-20-imagewatcher-event-loop-blocking.md``. (#798)
* ``move_radec``/``move_altaz`` now reject non-finite (NaN/inf) RA/Dec/Alt/Az up front with
  ``InvalidArgumentError``, instead of letting them reach a NaN altitude comparison that was
  silently always ``False`` and then ``Angle.to_string()``, whose numpy 2.x vectorized formatter
  raised a ``RuntimeWarning`` that ``application.py``'s filterwarnings promotes to a hard error --
  killing the RPC handler mid-slew. All ``to_string()`` call sites in the affected module were
  replaced with manual sexagesimal formatting, mirroring pyobs-gui's fix for the same numpy 2.x
  issue. Fixes #802.

v2.0.0.dev92 (2026-08-23)
=========================
* ``BaseVideo`` gained an opt-in ``token`` parameter gating its MJPEG/raw/FITS endpoints behind
  either an ``Authorization: Bearer <token>`` header or an HMAC-signed session cookie issued by a
  new browser ``/login`` page (``/logout`` clears it); ``/ping`` stays open. The cookie is
  stateless (expiry plus HMAC-SHA256 over the expiry, keyed by the token), all comparisons are
  constant-time, and an unauthenticated request is redirected (401 -> 303) to ``/login`` so
  browsers land on the form. ``HttpFile`` gained a public ``headers`` property so consumers (e.g.
  pyobs-gui's ``VideoWidget``) can read the ``Authorization`` header without reaching into a
  private attribute. See ``specs/plans/2026-08-21-basevideo-http-token-auth.md``. (#799)

v2.0.0.dev91 (2026-08-21)
=========================
* Demoted routine retry/shutdown log messages from WARNING to INFO.
* Fixed ``BIASSEC``/``TRIMSEC`` FITS-header computation: the old guard fired (and warned) for any
  window not covering the full visible frame on both axes -- exactly the common case of a subframe
  with no prescan/overscan at all (e.g. guided skyflats) -- while the case it claimed to describe,
  prescan/overscan on *both* axes, slipped through silently and wrote an incomplete one-axis
  ``BIASSEC``. The check is now based on whether the window actually extends beyond the visible
  frame: fully-inside windows log at INFO (nothing to compute), and true both-axis prescan/overscan
  windows warn that only one axis is supported. Header output is unchanged for the common cases.
* ``Application`` now logs module-creation failures (unconsumed config keys, broken ``__init__``
  chains, ...) at ERROR level with the full traceback before re-raising, so they land in the
  configured log file / journald instead of only on stderr -- which is ``/dev/null`` for
  daemonized modules (``--pid-file``, as started by pyobsd / pyobs-web-admin). Such a failure
  previously vanished from all logs: the log simply stopped after the last INFO line and the
  module just showed as stopped.
* Fixed ``BaseVideo``'s index page using a root-absolute ``/video.mjpg`` image URL, which 404s when
  the module is served behind a reverse-proxy path prefix (e.g. ``/pyobs/fibercamera/``) since the
  browser resolves it against the host root instead of the page's own path -- and since that
  request never reaches the module, the camera is never (re)activated. Now relative.

v2.0.0.dev90 (2026-08-20)
=========================
* ``BackendTaskArchive`` and ``BackendObservationArchive`` gate their 5s refresh on the backend's
  ``last_task_update``/``last_observation_update`` marker again. The marker is now a DB-derived
  ``Max(updated_at)`` (pyobs-robotic-backend#84) that is truthful across gunicorn workers, so the
  archives no longer re-download (and re-compare) on every poll -- the per-poll content comparison
  was fragile and misfired whenever runtime code mutated a serialized field (see the
  ``DynamicTarget.resolve()`` fix below), livelocking the scheduler. The content comparison is
  kept as the ``on_tasks_changed`` trigger, so no-op marker bumps never fire a scheduler run.

v2.0.0.dev89 (2026-08-20)
=========================
* ``DynamicTarget.resolve()`` no longer overwrites its declared ``name`` field with the picked
  star's name. That mutation leaked into ``Task.model_dump()`` (which serializes the static
  target), so ``BackendTaskArchive``'s content comparison saw a "change" on every poll while the
  scheduler resolved a dynamic target (e.g. the CSV-picker autofocus task) -- the constant
  ``on_tasks_changed`` kept ``_need_update`` set and every scheduler run aborted itself with
  "Not using scheduler results, since update was requested", so no schedule was ever committed.
  The picked star is still available via the resolved target (``_target``) and lands in the
  scheduled observation; the serialized ``name`` stays ``"(dynamic)"``.

v2.0.0.dev88 (2026-08-20)
=========================
* ``Task`` gained an ``updated_at`` field (``str | None``, default ``None``), matching the field
  pyobs-robotic-backend#84 started returning from ``GET /api/tasks/`` (DB-derived ``updated_at``
  on ``Task``). Without it, the strict ``Task`` model rejected the new key and
  ``BackendTaskArchive`` failed every download, leaving the scheduler and mastermind without a
  task list.

v2.0.0.dev87 (2026-08-20)
=========================
* ``BackendTaskArchive`` and ``BackendObservationArchive`` no longer gate their 5s refresh loop on
  the robotic-backend's ``last_task_update``/``last_observation_update`` marker. That marker is
  computed from a per-process Django ``LocMemCache`` and is unreliable across gunicorn workers, so
  a stale or missing marker pinned the archive's ``_last_update`` and the mastermind kept running
  stale tasks/schedules (edited task parameters, deactivated tasks, newly scheduled observations,
  window-expired observations) forever. Both archives now re-fetch unconditionally on every poll
  and detect real changes by comparing the downloaded content against the cached copy (full model
  dumps, including observation ``state``), firing ``on_tasks_changed`` only when content actually
  changed; ``last_changed()`` now reports the local time a change was last observed. Fixes #789.
  (#790)
* ``PyobsArchive`` and ``LocalArchive`` gained an ``obsnum`` filter on ``list_frames()`` and
  ``list_options()``: ``PyobsArchive`` now emits the ``OBSNUM`` query parameter (exact match on
  ``Frame.OBSNUM``), and ``LocalArchive`` filters its local index on the ``OBSNUM`` FITS header, so
  observations can be matched to their archived frames via ``list_frames(obsnum=...)``. Needed by
  pyobs-robotic-backend#82. (#791)

v2.0.0.dev86 (2026-08-19)
=========================
* Fixed ``FitsHeaderMixin.add_requested_fits_headers()`` letting a misbehaving peer's malformed
  ``IFitsHeaderBefore``/``IFitsHeaderAfter`` response crash the whole exposure: it only caught
  ``exc.RemoteError``, but ``XmppComm.execute()`` only converts ``IqError``/``IqTimeout`` into
  that, so anything else raised while making or deserializing the RPC call escaped uncaught. Now
  catches ``Exception`` broadly (logging the peer and failure type, skipping just that peer), while
  ``CancelledError`` -- a ``BaseException`` -- still propagates, preserving cancellation semantics.
  Fixes #767.
* ``Project`` gained a ``public`` flag (default ``False``), matching the field the robotic backend
  (pyobs-robotic-backend#79) will start returning from ``GET /api/projects/``. Without it, the
  strict ``Project`` model rejected the new key and ``BackendTaskArchive`` silently kept running on
  stale or empty task/project data. Fixes #786.
* Fixed ``XmppComm`` crashing on payload-less pubsub notifications (retract stanzas, node purges,
  and nodes with ``deliver_payloads`` off all arrive without a ``<payload>`` element under
  ``<item>``): ``_handle_event`` raised ``AttributeError`` on ``None.text``, surfacing only as a
  noisy "Task exception was never retrieved" since the dispatching task was never awaited. Now
  guards the payload access and drops payload-less notifications, and the background task gets a
  done-callback so any future exception is retrieved and logged normally.

v2.0.0.dev85 (2026-08-19)
=========================
* ``http_request_paginated()`` now tolerates page drift mid-fetch: DRF's ``page=N`` pagination
  404s with "Invalid page." once ``N`` exceeds the current page count, and on a live-growing
  dataset with non-unique ordering (e.g. ``Observation.Meta.ordering = ["start"]``) a concurrent
  insert can shift page boundaries between fetching a "next" link and following it, crashing the
  whole request. Now stops pagination early with whatever was already fetched -- but only for that
  specific error shape, and never on the first page, so other 404s still raise.

v2.0.0.dev84 (2026-08-19)
=========================
* ``Project`` gained a missing ``users`` field (per-user project visibility), matching the robotic
  backend's ``ProjectSerializer``. With ``extra="forbid"`` enabled (#762), the unmodeled field
  previously raised a validation error instead of being silently dropped.

v2.0.0.dev83 (2026-08-19)
=========================
* The ``TypeError`` raised when a leftover kwarg reaches ``object.__init__()`` unclaimed (end of
  the cooperative ``super().__init__(**kwargs)`` chain added below) is now re-raised with a
  diagnosable message naming the offending class and the actual unconsumed kwargs -- not
  ``Object``'s own pre-consumption view, which could wrongly flag a kwarg a downstream mixin in the
  MRO had already legitimately claimed (e.g. ``motion_status_interfaces``). The precise leftover
  set is read from the deepest frame in the chained exception's traceback, i.e. the cooperative
  call that actually reached ``object.__init__()`` and got rejected. Previously this raised only
  the generic, class-and-kwarg-less ``object.__init__() takes exactly one argument`` message.

v2.0.0.dev82 (2026-08-19)
=========================
* ``Object.__init__`` now forwards leftover kwargs cooperatively via ``super().__init__(**kwargs)``
  instead of silently absorbing them, giving mixins listed after ``Module`` in a subclass's MRO
  (``WeatherAwareMixin``, ``MotionStatusMixin``, ``PipelineMixin``, etc.) a real chance to claim
  their own kwargs -- prerequisite for eventually raising on genuinely unrecognized ones. Converted
  the 14 pyobs-core classes that composed mixins via explicit multi-call fan-out to a single
  cooperative call, reordering base classes in ``BaseRoof``/``BaseTelescope``/``DummyMode`` so
  ``Module`` runs first (every mixin that calls ``add_background_task``/``add_child_object`` or
  reads ``self.comm`` needs ``Object``/``Module`` already set up). ``FitsHeaderMixin``'s cache-path
  attribute is now a lazily-computed property instead of eager at ``__init__`` time, since it can
  now run before ``Module`` has set ``self._device_name``. ``PipelineMixin``'s ``archive``
  default-injection now only applies to step classes that actually declare an ``archive``
  parameter (checked via signature inspection), instead of injecting unconditionally and relying on
  silent-drop -- exactly the behavior this change removes. See
  ``specs/plans/2026-08-18-cooperative-mixin-init.md``.
* Fixed a regression from the change above: unconditionally dropping ``auto_update=False`` from
  ``Scheduler``'s kwarg injection (justified at the time as "never declared, no effect") silently
  re-enabled ``BackendObservationArchive``'s 5-second polling loop, which *does* declare and gate on
  that kwarg -- a poller deliberately disabled when the scheduler moved to event-driven
  ``on_tasks_changed`` updates, live on two fleet configs (MONET South, iagvtsrv). The kwarg-support
  check is now a general ``_class_accepts_param()``, reused for both the ``observation_archive`` and
  ``auto_update`` injections.
* Fixed ``WindowingWidget.value_top`` (``pyobs/utils/gui/camera/windowingwidget.py``) returning the
  Left spinbox's value instead of the Top spinbox's (copy-paste bug) -- windowing offsets set via
  the GUI applied the wrong Y coordinate.

v2.0.0.dev81 (2026-08-18)
=========================
* No pyobs-core code changes -- version bump only.

v2.0.0.dev80 (2026-08-18)
=========================
* ``BaseVideo`` now declares itself a sender of ``NewImageEvent`` via ``comm.register_event()`` in
  ``open()``, matching ``BaseCamera``'s existing registration -- without it, a peer's disco#info-
  driven subscription logic never subscribed (since it skips event types a peer doesn't advertise
  sending), so ``send_event()`` succeeded server-side but nothing ever received it: the GUI's
  video/FITS grab silently never updated, with no errors on either side.

v2.0.0.dev79 (2026-08-18)
=========================
* Fixed a TOCTOU race in ``BaseVideo.activate_camera()``/``deactivate_camera()``: two concurrent
  callers (e.g. an incoming video-stream request racing an RPC like ``set_exposure_time``) could
  both observe ``self._active`` as unset and both proceed to open/close the camera,
  double-connecting to the same GigE device and tripping "Controller privilege required for
  streaming control" on devices that only grant one controller. The check-and-set is now
  serialized with a lock.

v2.0.0.dev78 (2026-08-18)
=========================
* ``BaseVideo`` gained a raw-frame streaming endpoint (``/video.raw``) alongside the existing MJPEG
  stream: a multipart, event-driven feed of a JSON FITS-keyed meta header plus raw little-endian
  frame bytes, with latest-frame-wins backpressure (a slow client drops stale frames instead of
  queuing). ``VideoCapabilities.video`` is renamed to ``mjpeg``, and a new ``raw`` field
  (``str | None``) advertises the raw endpoint's path; ``live_view`` collapses into ``video_path``
  alongside the new ``raw_path``. ``add_fits_headers()`` is split into ``add_local_fits_headers()``
  (no VFS I/O, usable per-frame) plus the persistent ``FRAMENUM`` step. Also fixed
  ``video_handler``'s hardcoded 1 fps interval and lowered the default ``sleep_time`` to 60s. A
  connected-but-idle raw client now keeps the camera awake correctly: ``raw_handler`` bounds its
  wait for a new frame with a timeout and re-touches the activity timestamp even when no frame
  arrives, instead of only doing so when a frame is actually sent. ``DATE-OBS`` is captured at
  acquisition time (in ``_set_image()``) rather than at send time, avoiding drift under frame
  coalescing or scheduling delay. See ``specs/design/2026-08-11-basevideo-raw-frame-streaming.md``.
  (#766, #770)
* Bounded ``add_requested_fits_headers()``'s wait for peer-supplied FITS headers with a single
  ``asyncio.wait()`` deadline (new ``fits_header_timeout`` kwarg on ``FitsHeaderMixin``, default
  15s), instead of awaiting every header future with no timeout at all -- a peer that never answers
  its IQ (e.g. a laptop put to sleep without closing its client) previously stalled frame
  finalization for the full ~120s XMPP IQ timeout. Fixed two bugs found while implementing this:
  ``asyncio.wait()`` raised ``ValueError`` on an empty futures dict (any module with no comm, or no
  peer implementing ``IFitsHeaderBefore``/``IFitsHeaderAfter``), crashing every exposure; and
  ``BaseCamera``/``BaseVideo`` passed an explicit keyword list to
  ``ImageFitsHeaderMixin.__init__`` instead of forwarding ``**kwargs``, silently dropping a
  configured ``fits_header_timeout`` for exactly the modules (e.g. ``fli230``) that motivated this
  fix. Fixes #764. (#765, #768)

v2.0.0.dev77 (2026-08-16)
=========================
* Every module now logs the versions of loaded ``pyobs-*`` packages at startup, alongside the
  existing IERS-cache priming. Guarded with the same try/except as that priming, so broken
  dist-info metadata on any installed package can't abort startup; an editable install won't show
  up in the output (``packages_distributions()`` can't derive its top-level-name mapping without
  ``RECORD`` file entries), which is fine since the only consumer only needs this in production.
  (#759)
* Fixed ``WeatherAwareMixin`` retrying ``park()`` on every 10s bad-weather check while a device was
  already in ``MotionStatus.ERROR``, instead of only once: the error-state guard only suppressed
  the *first* post-error ``park()`` call, then fell through and called it again on every subsequent
  check. Devices whose ``park()`` raises on ``ERROR`` status (``BrotRoof``, ``BrotTelescope``)
  flooded logs with a ``ParkError`` plus "Task exception was never retrieved" every cycle, since the
  call happens via a fire-and-forget background task.

v2.0.0.dev76 (2026-08-15)
=========================
* ``BaseCamera`` now publishes live ``IExposure`` state (``progress``/``exposure_time_left``) once
  a second while ``EXPOSING``, via a new background task; previously it only published on status
  transitions, so both values stayed frozen at 0 for the whole exposure.
  ``exposure_time_left`` is clamped to ``>= 0``.

v2.0.0.dev75 (2026-08-15)
=========================
* ``BaseVideo``'s image-cache write now offloads ``image.to_bytes()`` to a worker thread (matching
  the existing ``create_jpeg()`` pattern), instead of serializing a ~5MB FITS frame directly on the
  event loop -- same class of fix as ``Vfs.write_image()``/``write_fits()`` in dev53, applied to a
  different choke point.

v2.0.0.dev74 (2026-08-15)
=========================
* ``FocusModel``'s coefficient fit (``lmfit.minimize`` plus residual model evaluation) now runs on
  a worker thread instead of directly on the event loop.

v2.0.0.dev71 (2026-08-10)
=========================
* Added ``OBSNUM``: ``Mastermind`` now assigns a compound ``<night>-<counter>`` observation number
  when a task starts running, persisted via a VFS-cached per-night counter and written to both
  ``Observation.obsnum`` and the ``OBSNUM`` FITS header -- lets frames from possibly-multiple
  cameras be tied back to the observation that produced them. See
  ``specs/design/obsnum_fits_header.md``. (#738)

v2.0.0.dev70 (2026-08-10)
=========================
* Added structured progress reporting to ``Reduction`` (a ``progress_callback`` reporting
  master-calib creation and per-frame science calibration results as they happen, with a cumulative
  whole-night frame total computed via a cheap pre-pass), so a caller (e.g. ``pyobs-pipeline``'s web
  UI) can drive a live progress bar instead of only tailing free-text logs. ``Reduction`` is split
  into an abstract ``ReductionBase`` (archive/pipeline plumbing, master-calib cache/lookup, the
  progress-callback mechanism) and the concrete ``Reduction``, giving a future second reduction
  strategy a base to build on.
* ``PipelineMixin`` now propagates a ``Pipeline``'s own ``archive`` into any step that doesn't
  specify its own -- ``Reduction`` already passed ``archive=archive`` into
  ``get_object(pipeline, Pipeline, archive=archive)``, clearly intending it to reach steps like
  ``Calibration``, but ``Pipeline.__init__`` absorbed it into ``Object.__init__(**kwargs)`` and
  dropped it, so every ``Calibration`` step had to redundantly repeat the same archive config
  already set at the ``Reduction``/site level. An explicit per-step ``archive`` still overrides it.
* Fixed ``Calibration`` aborting when a science frame arrived with a catalog already attached (e.g.
  quick-look photometry done at the telescope): it tripped ``Image.trim()``'s stale-catalog guard,
  even though ``to_ccddata()`` never carries a catalog through anyway. The pre-existing catalog is
  now dropped before trimming.
* Made ``AperturePhotometry`` abstract instead of exporting it as if instantiable directly -- it's a
  base class for ``PhotUtilsPhotometry``/``SepPhotometry`` (each supplies its own calculator), and
  its ``__module__`` override advertised a dotted path the package's ``__init__.py`` never actually
  re-exported. Breaking change for any external code instantiating ``AperturePhotometry`` directly
  (subclasses that define their own ``__init__``, as both existing ones already do, are unaffected).
* Removed the generated TypeScript interface exports (``export/typescript/``) -- breaking change for
  any external tooling consuming them.

v2.0.0.dev68 (2026-08-09)
=========================
* Renamed ``pyobs.utils.pipeline.Night`` to ``Reduction`` (fits solar telescopes too, not just
  nighttime ones). Replaced ``store_local`` with a single ``output`` param (local path, dict, or
  ``Archive``), so input and output can be different archives. Implemented
  ``LocalArchive.upload_frames`` (previously a silent no-op), including a ``ValueError`` on a
  missing ``FNAME`` header and a ``_update_root()`` refresh after write; the local output directory
  is now auto-created if missing. Calibration-frame creation failures are now isolated per
  instrument/binning/filter combination instead of aborting the whole run. Fixed a missing
  ``return None`` after the post-download frame-count check. Removed the dead ``worker_procs``
  param and the ``**kwargs`` catch-all on ``Reduction.__init__``, so a typo'd kwarg now raises
  ``TypeError`` instead of being silently swallowed. Breaking change for any external code using
  ``Night``, ``store_local``, or ``worker_procs`` directly.

v2.0.0.dev67 (2026-08-06)
=========================
* Re-landed the ``OnDemandScheduler`` event-loop offload (added in dev53, briefly reverted in
  dev66) unchanged, alongside a prefetch/freeze split for ``ObservationArchiveEvolution``: a new
  ``prefetch()`` fetches every task's observations plus the one real "current" night
  (``night(start)``) up front, then ``freeze()`` makes a subsequent task-id cache miss raise
  ``RuntimeError`` instead of silently falling back to a live archive lookup, while a miss on any
  other (necessarily later, necessarily empty) night seeds an empty result instead of fetching or
  raising. Groundwork for eventually moving that evaluation from a worker thread to a worker
  process (real GIL isolation); the thread-shared live archive connection was the blocker, since a
  process pool can't share it. See ``specs/plans/scheduler-archive-prefetch-for-process-isolation.md``.

v2.0.0.dev66 (2026-08-05)
=========================
* Briefly reverted the ``OnDemandScheduler`` event-loop offload added in dev53 while investigating
  the process-isolation groundwork above; re-landed unchanged in dev67, so only a dev66 build itself
  ran evaluation synchronously on the event loop again.
* ``Mastermind`` now logs a task failing with a domain ``PyobsError`` (e.g. ``AcquisitionError``) at
  INFO instead of ERROR with a full traceback -- these are expected outcomes, not bugs; only a
  genuinely unclassified exception still logs loudly.

v2.0.0.dev65 (2026-08-05)
=========================
* Fixed a scheduler event-loop stall traced live (``py-spy dump``) to the **main** thread, not the
  worker thread the dev53 offload targets: ``ObservationArchiveEvolution.evolve()`` called
  ``Time.now().night_obs()`` directly on the event loop for every scheduled task, redoing an
  uncached astropy sunset computation each time -- a 52-block schedule triggered this dozens of
  times in a few seconds. ``evolve()`` now takes the night as a parameter
  (``data.night(task.start)``, reusing ``DataProvider``'s existing cache) instead of computing it
  from ``Time.now()`` internally. Also a correctness fix: keying off "now" filed a task scheduled
  hours ahead under the wrong night's bucket, which a later ``FollowMerit``/``PerNightMerit`` check
  for that night would then miss. See
  ``specs/steering/scheduler-cpu-bound-merit-evaluation-stalls-event-loop.md``.
* IERS auto-download being disabled (``iers_offline``) now logs at info instead of warning -- it's a
  deliberate config choice, not an anomaly.

v2.0.0.dev64 (2026-08-05)
=========================
* Fixed ``ArchiveFile._upload`` referencing ``self._auth``, which was never set (leftover from
  before auth moved to ``self._headers``/token-based auth) -- any actual write to a
  ``pyobs-archive`` backend crashed with ``AttributeError`` before the request was even sent.

v2.0.0.dev63 (2026-08-05)
=========================
* Downgraded routine no-detection acquisition log lines ("no on-sky distance found", a missed
  sun/star detection) from warning to info -- neither is actionable on its own, since the
  acquisition loop just retries; warning level was noise for something expected to happen
  occasionally.

v2.0.0.dev62 (2026-08-05)
=========================
* ``ImageFitsHeaderMixin``'s missing-WCS-header warnings (``CDELT1``/``2``, ``CRPIX1``/``2``, the
  CD-matrix) now fire once per module lifetime instead of once per frame, for cameras missing the
  relevant config/header fields.
* ``BackendTaskArchive`` now follows pagination when fetching tasks/projects/observations from
  ``pyobs-robotic-backend`` (DRF ``PageNumberPagination``, 100/page) via a new
  ``http_request_paginated()`` that follows the "next" link until exhausted -- previously only the
  first page's results were ever read, so tasks or projects past page 1 were silently invisible
  regardless of how long they'd existed.
* ``Mastermind``'s ``get_next_observation``/``get_current_observation`` now skip and log an
  observation whose task failed to resolve (``Observation.task`` left ``None`` -- e.g. a deleted
  task, or the backend task-cache poll racing the observation-schedule poll) instead of returning
  it, which previously propagated a bare ``None`` into ``task_runner.can_run()`` and crashed
  Mastermind's background thread with an ``AttributeError``.

v2.0.0.dev61 (2026-08-04)
=========================
* Added CORS headers to ``HttpFileCache.download_handler`` (previously blocked browser ``fetch()``
  clients like ``pyobs-web-client`` from cross-origin reads) and an opt-in token param, checked via
  constant-time compare, plus the required ``OPTIONS`` preflight handler -- replacing ``HttpFile``'s
  Basic Auth, which ``HttpFileCache`` was silently ignoring since the server never enforced any auth
  at all. (#725)

v2.0.0.dev60 (2026-08-04)
=========================
* Moved the ``iers_offline`` warning log after handler setup, so it actually reaches a configured
  log handler instead of firing before one exists.

v2.0.0.dev59 (2026-08-04)
=========================
* Added an ``iers_offline`` config option: the existing ``PYOBS_IERS_OFFLINE`` env-var check is now
  also reachable via ``Application.__init__(iers_offline=...)`` and wired through
  ``PyobsCLI.GLOBAL_CONFIG_KEYS``, letting ``/etc/pyobs.yaml`` (or a ``--iers-offline`` flag)
  disable astropy's IERS/leap-second auto-download regardless of how the module process was spawned
  (``pyobsd`` vs. ``pyobs-web-admin``), unlike an env var, which only propagates through whichever
  launcher's own environment it happens to inherit.
* Fixed ``syslog`` being unsettable via ``pyobs.yaml``: it was missing from
  ``PyobsCLI.GLOBAL_CONFIG_KEYS`` even though a ``--syslog`` flag exists, so a ``pyobs:`` section in
  the config file silently had no effect on it.

v2.0.0.dev58 (2026-08-04)
=========================
* ``pyobsd status``'s CPU measurement is now opt-in (``--cpu-interval SECONDS``, sampling all
  modules over one shared sleep) instead of always-on -- previously every "status" call paid a
  blocking 0.1s per running module, and that short a window is too close to ``/proc``'s tick
  granularity to give a meaningful reading anyway. Uptime/RSS still report instantly.

v2.0.0.dev56 (2026-08-04)
=========================
* Also prime the leap-second table when warming astropy's IERS cache at startup (see dev55):
  ``IERS_Auto.open()`` only covers UT1-UTC/polar motion, and the leap-second table is a separate
  auto-download that was still landing inside ``basetelescope.py``'s celestial-header task and
  blocking the loop there even after dev55's fix. Uses ``update_leap_seconds()`` (not the
  lower-level ``LeapSeconds.auto_open()``), which both fetches it and installs it into ``erfa``.
* Exported ``DummyMode`` from ``pyobs.modules.utils``.

v2.0.0.dev55 (2026-08-04)
=========================
* Astropy's IERS cache is now primed once at startup, off the event loop via an executor, before
  module/comm setup -- left implicit, the first UT1-UTC lookup happened inside
  ``basetelescope.py``'s periodic celestial-header task and triggered astropy's ``auto_download``
  synchronously, blocking the event loop for however long the download took at an unpredictable
  point during normal operation.

v2.0.0.dev54 (2026-08-04)
=========================
* ``XmppComm``'s disco#info now tags each advertised ``<event>`` element with a ``role``
  attribute (``"send"``, ``"subscribe"``, or ``"send subscribe"``), derived from splitting
  ``Comm._registered_events`` into ``_events_sent``/``_events_subscribed``. Previously the two
  were merged into one undifferentiated set, so a client with no access to the ``pyobs.events``
  catalog (e.g. ``pyobs-web-client``) couldn't tell which events a module actually publishes vs.
  which it only listens for. ``Comm.unregister_event()`` now also drops an event from
  ``_events_subscribed`` once its last handler is removed, so a torn-down subscription stops
  being advertised (previously it stayed advertised forever). See
  ``specs/plans/event-role-advertising.md``.

v2.0.0.dev53 (2026-08-03)
=========================
* Offloaded ``OnDemandScheduler``'s per-timestep constraint/merit evaluation
  (``find_next_best_task``/``check_for_better_task``/``can_postpone_task``) onto a dedicated
  single-worker ``ThreadPoolExecutor`` (new ``pyobs/robotic/scheduler/_executor.py``'s
  ``run_cpu_bound``), and cache target-independent sun/moon computations in ``DataProvider`` per
  timestep. These constraint/merit ``__call__`` methods are declared ``async`` but never actually
  ``await`` -- they run synchronous astropy/astroplan work directly on the event loop, blocking it
  for multiple seconds at real fleet scale; root cause of a 2026-07-30 "Event loop stalled" warning
  on the scheduler module. Same class of fix as ``Vfs.write_image()``/``write_fits()`` below. See
  ``specs/plans/scheduler-event-loop-blocking.md``. (#712)
* ``ImageProcessor`` gained an ``on_error`` kwarg (``"raise"`` (default) / ``"error"`` / ``"info"``
  / ``"ignore"``) and a ``handle_error(image, error)`` override point, and
  ``PipelineMixin.run_pipeline()`` (``pyobs/mixins/pipeline.py``) now catches each step's
  ``ImageError`` and dispatches per that step's setting, instead of the whole chain aborting on
  the first exception from any step (previous behavior, equivalent to ``on_error="raise"``
  everywhere). Non-``ImageError`` exceptions still always propagate. Lets one step's failure be
  non-fatal while another stays fatal within the same pipeline run -- e.g. a calibration path that
  must have a valid WCS vs. a quick-look pipeline where a missing WCS is fine. Originally proposed
  in #328 as a nested ``ExceptionHandler`` wrapper processor; rejected there for adding config
  nesting for what should be a per-step toggle. ``AstrometryDotNet``'s ``exceptions: bool`` kwarg
  is now deprecated in favor of ``on_error`` (``exceptions=False`` == ``on_error="error"``;
  ``on_error`` takes precedence if both are set) and its former internal try/except was removed --
  its ``on_error``/``handle_error`` dispatch now only happens when it runs as a pipeline step via
  ``run_pipeline()``. Calling it (or any other migrated processor) directly, outside a pipeline,
  always raises on failure regardless of ``on_error``/``exceptions``. See
  ``specs/plans/pipeline-step-error-control.md``.
* ``Vfs.write_image()``/``write_fits()`` (``pyobs/vfs/vfs.py``) now serialize the FITS data
  (``image.writeto()``/``hdulist.writeto()``, including gzip compression for ``.fits.gz``
  targets) via ``asyncio.to_thread()`` instead of directly on the event loop. That serialization
  is CPU-bound and can take multiple seconds for larger frames, and running it inline blocked
  every other coroutine in the module for the duration -- including state-publishing background
  tasks and comm handling -- observed as multi-second event-loop stalls in ``pyobs-iagvt``'s
  ``SunCamera``/``FTS`` right at the ``vfs.write_image()`` call. Callers that were working around
  this themselves (serializing via ``asyncio.to_thread`` and uploading raw bytes with
  ``write_bytes()`` instead) no longer need to.

v2.0.0.dev52 (2026-07-29)
=========================
* Guarded optional WCS/image-type handling against missing capabilities: ``_ResponseImageWriter``
  (astrometry.net response saving) unconditionally deleted ``PC``/``CDELT`` header keywords after a
  solve, raising ``KeyError`` when a header lacked one of them -- now a no-op if the keyword is
  already absent. ``Acquisition``/``AutoFocusSeries`` required ``IImageType`` from the configured
  camera via a hard proxy, unlike ``AutoGuiding``'s identical use case, which already tolerates a
  camera without it via ``safe_proxy`` -- now consistent.

v2.0.0.dev51 (2026-07-28)
=========================
* No pyobs-core code changes -- entirely root-causing and mitigating the ejabberd shaper/
  ``xmpp_socket.erl`` reactivation bug behind the iag50srv capability-fetch timeouts (see
  ``specs/plans/ejabberd-throughput-benchmarking.md``); the shaper fix itself (raising
  ``shaper.normal``/``shaper.fast``) is an ejabberd-side configuration change, applied to iag50
  production and baked into the new ``scripts/xmpp/install-ejabberd.sh`` for future hosts.

v2.0.0.dev50 (2026-07-28)
=========================
* Fixed the XMPP wire serializer silently corrupting two more shapes of value: ``Time``-typed
  fields (e.g. ``WeatherState.time``) had no encode/decode support at all and arrived client-side
  as a plain string; and a field declared ``dict[str, str]``/``str`` could arrive as a stray
  ``bool`` if the isinstance-based encode dispatch won over the field's own declared type (seen as
  ``ModeState.modes`` containing bools instead of strings). Follow-up fixes for a not-yet-restarted
  sender still running the old serializer: ``Time`` decode no longer pins to ``isot`` format (a
  legacy sender's plain ``str(Time)`` fallback used the space-separated ``iso`` format, which the
  strict parse rejected), and boolean/int/double values are now coerced to ``str`` on decode as
  well as encode.

v2.0.0.dev49 (2026-07-28)
=========================
* Fixed ``XmppComm.__init__`` raising a bare, message-less ``ValueError`` on a malformed JID (found
  via a real login-window crash on a saved account with a trailing-slash, no-resource JID). The JID
  regex is now a module-level, properly end-anchored pattern (the previous ``re.match`` wasn't
  end-anchored, so ``user@domain/res/extra`` matched as valid), and the new ``is_valid_jid()`` lets
  a caller taking raw user input (e.g. a login window) validate upfront instead of finding out via
  an exception.
* Fixed ``Application.run()`` crashing on a benign qasync shutdown race, where a Qt-backed event
  loop (``pyobs-gui``) can report itself stopped before the main task/cancellation gather has
  actually finished -- now handled the same way as the existing ``CancelledError`` case.
* ``Application`` can now defer constructing its ``Module`` until the event loop is already
  running, via a new ``module_factory``/``loop_module_class`` alternative to ``config`` -- letting
  the factory ``await`` something like a login dialog's submit signal before the module and its
  comm connection exist at all. Existing config-file callers are unaffected.

v2.0.0.dev48 (2026-07-27)
=========================
* A module declaring a stateful interface but never publishing it (see the state-publishing
  enforcement below) now logs as an ``error``, not a ``warning`` -- it's a standing per-module
  defect that recurs on every startup, not a transient condition.

v2.0.0.dev47 (2026-07-27)
=========================
* Every ``Module`` now runs a background watchdog that detects the event loop itself stalling: it
  times its own wakeups against how long it asked to sleep for, so a synchronous blocking call
  anywhere in the module (or a background task) shows up as a logged stall -- once when it starts,
  once when it clears, with total duration -- instead of only being visible indirectly as peers
  timing out trying to reach that module.

v2.0.0.dev46 (2026-07-27)
=========================
* The capability-fetch retry warning now includes the actual exception that caused the retry,
  instead of just noting that one occurred.

v2.0.0.dev45 (2026-07-27)
=========================
* Fixed ``FocusModel.open()`` skipping its state publish entirely when the weather module wasn't
  reachable yet at startup (a common ordering race), which then always tripped the "declares
  state, but none published" warning; it now falls back to a placeholder ``focus=0.0`` until the
  background update loop replaces it with a real value.

v2.0.0.dev44 (2026-07-27)
=========================
* ``DummyComm`` now takes a real name instead of a hardcoded ``"module"`` placeholder
  (``Application`` fills it in from the config file's stem for comm-less modules), fixing
  indistinguishable ``PYOBS_MODULE`` log tags and a guaranteed false positive against the
  config-stem-mismatch warning.
* Fixed ``Comm``'s log-forwarding failure handler re-queuing its own failure log through the same
  queue it was draining, turning a sustained send outage into an unbounded stream of
  self-generated failure reports.
* ``pyobsd``'s per-module file logging (``--log-file``) is now opt-in (``--file-log``/
  ``--no-file-log``, default off) instead of always passed to every started module regardless of
  the already-default-on journal logging; non-systemd deployments relying on the old always-on
  file logging need to pass ``--file-log`` explicitly.
* Removed ``IRunning.is_running()`` (and its ~12 implementers) now that ``RunningState`` (pushed
  via ``comm.set_state(IRunning, ...)``) already covers the same information -- both existed side
  by side for the same boolean.
* Extended the ``max_age`` freshness check (see below) to ``FollowMixin`` (default 3x its poll
  interval) and ``FocusModel``'s temperature reads (default 2x), so a dead publisher's frozen last
  value is treated as unavailable instead of trusted indefinitely.

v2.0.0.dev43 (2026-07-27)
=========================
* Added an opt-in ``max_age`` freshness check to ``Proxy.get_state()``/``wait_for_state()``: a
  cached state value past its ``max_age`` is now treated the same as not-yet-published
  (``None``/timeout) instead of trusted forever, even if the publisher's update loop has died or a
  stanza was shaper-delayed by minutes. ``WeatherAwareMixin`` passes ``weather_max_age`` (default
  120s) so a dead ``Weather`` update loop degrades to bad-weather within a couple of check cycles.
* ``Comm`` now tracks which interfaces have actually had ``set_state()`` called, and
  ``Module.startup()`` warns when a module implements a stateful interface but never published it
  -- caught ``Weather``/``DummyCamera`` both only ever publishing ``IWeather``/``ITemperatures``
  from a background loop, never synchronously from ``open()``; both now also publish a placeholder
  value from ``open()``.
* Fixed non-TLS XMPP connections failing entirely ("No appropriate login method") against ejabberd
  26.4.0: ``unencrypted_scram`` was already set for ``use_tls=False``, but slixmpp also needs
  ``unencrypted_plain`` set explicitly before it will attempt PLAIN over a plaintext connection.

v2.0.0.dev42 (2026-07-26)
=========================
* Removed racy, non-gating ``has_proxy()`` startup checks in ``open()`` (``FlatField``,
  ``BasePointing``/``Acquisition``, ``AutoFocusSeries``, ``FlatFieldScheduler``) -- one-shot,
  no-retry, 5s presence checks that routinely false-positived under any slow/delayed presence
  propagation without actually gating anything (every real use of the peer already re-resolves a
  fresh proxy and raises its own well-attributed error if genuinely missing).
* ``LocalComm`` now broadcasts ``ModuleOpenedEvent`` on ``mark_ready()``, matching ``XmppComm``'s
  presence-driven behavior -- previously a module joining the local network after a peer had
  already started stayed invisible to that peer's ``ModuleOpenedEvent`` handlers until the peer
  restarted.
* ``BaseCamera`` no longer aborts closed-shutter (``DARK``/``BIAS``) exposures or sequences on bad
  weather, since the shutter being closed already means weather can't affect them.
* Fixed the config-filename/module-name mismatch check (see below) firing a spurious warning
  against a legitimately-deactivated ``_test.yaml``-style config, by stripping the leading
  underscore from the config stem before comparing.

v2.0.0.dev41 (2026-07-26)
=========================
* ``FlatField.open()`` now publishes ``IFilters`` state unconditionally, instead of only once
  ``set_filter()`` had been called via RPC -- previously the pubsub state node never got created
  on a fresh start, leaving subscribers (e.g. GUI widgets) retrying forever.
* The config-filename/module-name mismatch check added below now logs a warning instead of
  raising, so a genuine mismatch no longer prevents a module from starting at all.

v2.0.0.dev40 (2026-07-25)
=========================
* A config file starting with an underscore (e.g. a deactivated ``_test.yaml``) is now logged with
  its leading underscores stripped from the module-name tag, instead of tagging log lines with the
  raw filename stem.

v2.0.0.dev39 (2026-07-24)
=========================
* ``Application`` now refuses to start a non-``MultiModule`` whose config filename doesn't match
  its own comm-derived name, catching a class of drift where background tasks/RPC log lines use
  the real name but everything else falls back to the config file's stem -- silently splitting a
  module's ``PYOBS_MODULE`` log tag in two whenever a config file is renamed independently of its
  ``comm`` configuration.

v2.0.0.dev38 (2026-07-21)
=========================
* Suppressed astropy's ``VerifyWarning`` on FITS header comment truncation in ``Image.writeto()``,
  the single choke point every FITS write funnels through -- expected whenever a header value
  (aggregated from many modules) is long enough to leave no room for its comment within the
  80-char card limit; the value itself is untouched, so the warning had nothing actionable to
  report.

v2.0.0.dev37 (2026-07-21)
=========================
* ``Comm.get_interfaces()`` now waits briefly for a not-yet-discovered client instead of raising
  ``KeyError`` instantly, tolerating a caller's own startup racing slightly ahead of this module's
  peer discovery (which only populates once ``_got_online`` has processed the peer's presence).
  Also fixed a docstring/behavior mismatch: it promised ``IndexError`` on not-found, matching
  ``_get_client``'s existing handling, but actually raised ``KeyError``.

v2.0.0.dev36 (2026-07-21)
=========================
* ``Proxy.wait_for_state()`` now returns ``None`` on timeout instead of letting
  ``asyncio.wait_for``'s ``TimeoutError`` propagate -- every caller (``waitformotion.py``,
  ``weatheraware.py``, ``pyobs-iagvt``'s ``SunCamera``, others) already checked for ``None``
  immediately afterward, so a peer simply not having published yet was turning into an unhandled
  exception for all of them.

v2.0.0.dev35 (2026-07-21)
=========================
* Event handler exceptions are now logged properly (with handler and event context) via
  ``log.error()`` instead of surfacing only as asyncio's generic "Task exception was never
  retrieved" warning at garbage-collection time, since ``_send_event_to_module`` dispatches every
  handler as a fire-and-forget background task with nothing checking the result.

v2.0.0.dev34 (2026-07-21)
=========================
* Added jitter to ``_safe_send``'s retry wait (``send_event``/``_set_state``'s underlying path),
  matching the indefinite-retry jitter added for capability/state-subscribe fetches below --
  without it, many modules' ``_safe_send`` calls retrying around the same moment (e.g. a
  fleet-wide restart) stayed in lockstep instead of spreading out.

v2.0.0.dev33 (2026-07-21)
=========================
* Capability-fetch and state-subscribe retries (``_get_capabilities``/``_subscribe_with_retry``)
  no longer give up permanently after a fixed attempt budget -- they now retry indefinitely with
  capped exponential backoff and full jitter, stopping only when the peer actually goes offline or
  the last subscriber unsubscribes. A fixed budget could be exhausted across many module pairs at
  once by a simultaneous fleet-wide restart, leaving capabilities/state permanently missing until a
  manual restart.

v2.0.0.dev32 (2026-07-21)
=========================
* ``XmppComm``'s XEP-0199 keepalive ping interval/timeout is now configurable, instead of a fixed
  30s default that can be shorter than an ejabberd shaper's IQ reply delay under load -- letting a
  deployment tolerate a known-slow server instead of only a genuinely dead connection.

v2.0.0.dev31 (2026-07-21)
=========================
* Fixed pubsub subscribe retries only catching ``IqError``, not the ``IqTimeout`` that
  ``_safe_send`` also raises once its own internal retries are exhausted -- an uncaught
  ``IqTimeout`` killed the whole 30-attempt subscription retry loop after a single slow response,
  surfacing only as an unretrieved background-task exception instead of the intended "could not
  subscribe" warning, with the subscription then permanently abandoned.

v2.0.0.dev30 (2026-07-21)
=========================
* ``WeatherAwareMixin`` no longer parks on the first weather-check connection hiccup -- a common
  right-after-restart race where XMPP roster/presence for the weather module hasn't settled yet. A
  connection failure now only counts as bad weather after 3 consecutive failed checks.

v2.0.0.dev29 (2026-07-18)
=========================
* Modules no longer accept RPC calls until they've actually finished starting up. Some drivers
  (e.g. camera modules connecting to hardware) take a while inside ``open()``, but were previously
  reachable over XMPP -- and visible to peer discovery -- the instant they connected to the server,
  long before ``open()`` returned. New ``ModuleState.STARTING``, set at construction and cleared by
  the new ``Module.startup()`` once the full ``open()`` override chain (base setup plus every
  subclass's own) has completed; ``Module.execute()`` now rejects any call outside a small
  introspection/recovery whitelist (``get_permitted_methods``, ``reset_error``) with the new
  ``ModuleStartingError`` while a module is still ``STARTING``. ``XmppComm``/``XmppClient`` also
  hold back the initial XMPP presence broadcast until a module reaches ``READY``, closing a race
  where a peer reacting to ``_got_online`` could read capabilities (e.g. hardware-dependent ones
  like ``IWindow``/``IBinning``) that hadn't been published yet -- scoped to comms with an actual
  starting ``Module`` attached, so bare/GUI-style ``XmppComm`` usage announces itself exactly as
  before. ``Application`` and ``MultiModule`` both call ``Module.startup()`` instead of ``open()``
  directly now; any other code that opens a module standalone (a custom script, a test) needs to do
  the same, or call ``set_state(ModuleState.READY)`` itself after ``open()`` -- see
  :ref:`module-startup-gating`.

v2.0.0.dev28 (2026-07-18)
=========================
* New ``InvalidArgumentError`` for bad-argument validation on RPC-exposed methods (unknown filter
  name, invalid focus value, invalid config parameter, out-of-range ``grab_sequence`` count/delay,
  ...) -- previously these stayed as plain ``ValueError``, which works fine locally (``LocalComm``,
  direct calls, tests) but silently degrades to ``UnclassifiedError`` the moment the same call
  crosses XMPP, since ``ValueError`` is a builtin and never in the registry. That inconsistency is
  exactly the kind of bug that only shows up once code moves from a local test to a networked
  deployment. Fixed for ``IConfig.get_config_value``/``get_config_value_options``/
  ``set_config_value``, ``IDataSequence.grab_sequence``, ``ITrackingMode.set_tracking_mode``,
  ``IFocuser.set_focus``, ``IFilters.set_filter``, ``IMode.set_mode``, and
  ``IWeather.get_sensor_value`` (``MockWeather``'s implementation -- the real ``Weather`` class's
  own ``ValueError`` there is about a malformed station response, not a bad argument; see the next
  entry). Also reused the existing ``DeviceBusyError`` for ``FlatField.flat_field``/
  ``FlatFieldScheduler.run``'s "already running" check, which was never actually about a bad
  argument either. Scoped out first (see ``DESIGN_exception_handling.md``) before touching
  anything: real driver repos (e.g. ``pyobs-sbig``) likely have the identical ``ValueError``
  pattern for real hardware and would need the same companion fix, not reachable from this PR.
* New ``WeatherResponseError`` (``pyobs.modules.weather.weather``) for ``Weather.get_sensor_value``
  getting back a station response missing its ``time``/``value`` fields -- a different shape of
  problem from the bad-argument case above (an external dependency being flaky, not a caller
  mistake), same reasoning as ``BodyResolutionError``: plausibly transient, worth retrying, not the
  caller's fault. ``WeatherStatus.status``'s similar-looking ``ValueError`` (``weather_state.py``)
  turned out to be unreachable from any RPC caller at all -- it only fires inside a background
  polling loop that already catches it broadly and just logs a warning -- so it's left untouched.
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

v2.0.0.dev27 (2026-07-16)
=========================
* Fixed ``PhotometryFocusSeries`` systematically underreporting its focus error by a factor of its
  own square root: ``fit_hyperbola`` returns ``(focus, variance)``, not ``(focus, error)``.
* ``curve_fit`` (``pyobs.utils.curvefit.fit_hyperbola``) now passes ``absolute_sigma=True``, so the
  reported variance reflects the actual per-point measurement uncertainty passed in via ``y_err``
  instead of being silently rescaled to force a reduced chi-square of 1; the weighted-mean focus
  calculation now uses inverse variances accordingly.
* Guiding-statistics FITS keys (``GUIDING UPTIME``/``RMS``/``RMS1``/``RMS2``) now get an explicit
  ``HIERARCH`` prefix, avoiding astropy's ``VerifyWarning`` from auto-promoting them (they exceed
  the 8-char keyword limit).

v2.0.0.dev26 (2026-07-16)
=========================
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
* Added an optional ``delay`` parameter (seconds between grabs, default ``0``) to
  ``IDataSequence.grab_sequence()``, for cadence control between grabs without resorting to
  dithering/offsets (a pointing-layer concern out of scope for this interface). Both
  ``abort_sequence()`` and ``abort()`` cut a pending delay short instead of idling out the full
  wait once the sequence has already been told to stop.
* Fixed ``Time.night_obs()`` crashing during polar day/night: it assumed
  ``observer.sun_set_time()`` always returns a valid ``Time``, but astroplan returns a masked
  value when the sun never crosses the horizon in the search window; now falls back to the
  observer's local calendar date.
* Fixed ``Scheduler`` reading the private ``_observer`` attribute instead of the public
  ``observer`` property in its altitude/airmass logging, which broke silently (``AttributeError``
  swallowed by the worker loop) on mocked scheduler instances in tests, aborting scheduling before
  ``add_observations`` was even called.
* Enriched existing scheduler/telescope log lines (per-block schedule summary, altitude-limit
  error) with the computed altitude/azimuth/airmass on each side, so a mismatch between what the
  scheduler validated and what the telescope sees at move time can be diagnosed without new
  per-candidate logging on hot paths.
* Fixed a missing ``OBJECT`` FITS header: ``Task``/``LcoTask``/``LcoScript.get_fits_headers()``
  re-validated a brand-new ``Script`` instance from the stored config instead of reusing the
  instance ``run()`` actually executed, losing any state (like the target name) accumulated during
  the run; the actively-running script instance is now cached and reused for header lookups.
* Fixed ``CameraSettingsMixin`` still calling the synchronous, cache-only ``get_capabilities()``
  after capability fetches became asynchronous background tasks (previous release), which made
  "Could not get full frame size." fail deterministically for every ``IWindow`` camera; now awaits
  ``Proxy.wait_for_capabilities()`` for a ``Proxy`` camera.
* Fixed ``CircularMask`` destroying pixel data by zeroing it directly instead of flagging via
  ``image.mask`` -- it now sets (OR's) ``image.mask`` and leaves the underlying data untouched.

v2.0.0.dev24 (2026-07-15)
=========================
* ``Comm``'s proxy capability fetch (previously a single blocking disco#info query with no retry)
  now runs as a background task retried up to 3 times, mirroring the existing state-pubsub race
  fix, plus a new ``Proxy.wait_for_capabilities()`` for callers that need a guaranteed value; a
  peer that hadn't finished starting up no longer produces a permanent missing-capability warning.

v2.0.0.dev23 (2026-07-15)
=========================
* Added ``IDataSequence`` (``grab_sequence()``/``abort_sequence()``, pushed ``DataSequenceState``)
  for taking a counted sequence of grabs in one call instead of driving a client-side loop of
  ``grab_data()`` calls. Implemented by ``BaseCamera``. ``grab_sequence()`` returns immediately and
  runs the sequence in the background; ``abort_sequence()`` stops after the current grab finishes,
  while the existing ``abort()`` now also cancels the rest of a running sequence. See
  ``DESIGN_IDataSequence.md``.
* Fixed a ``FocusModel`` startup race fetching module temperatures: it used ``get_state()``, which
  only reflects whatever pub/sub state has arrived so far, crashing with a confusing "sensor not
  in data" error if the target module hadn't published ``ITemperatures`` yet; now uses
  ``wait_for_state()``, matching ``waitformotion.py``/``weatheraware.py``.
* ``BaseCamera`` now aborts the current exposure/sequence on ``BadWeatherEvent`` (hard-stopping via
  ``abort()``, clearing any running ``grab_sequence()`` count), matching the existing
  ``FlatField._abort_weather`` pattern -- previously this only worked client-side, via
  ``pyobs-gui``'s own sequence loop. (#547)
* Published previously-missing states for the dummy telescope/spectrograph modules:
  ``_DummyTelescopeBase`` (and its ``DummyAltAzTelescope``/``DummyRaDecTelescope`` subclasses)
  never published ``IPointingAltAz``; ``DummySolarTelescope`` never published its
  Heliocentric/Heliographic/Helioprojective pointing states until a corresponding ``move_*`` call
  had already been made; ``BaseSpectrograph``/``DummySpectrograph`` never published ``IExposure``.
  All three now publish at ``open()`` (and update live), mirroring ``BaseCamera``.
* Published previously-missing initial/``IReady`` states for several modules that formally require
  them via interface inheritance but never published them, leaving subscribers to retry
  indefinitely: ``AutoGuiding``/``ScienceFrameAutoGuiding``'s ``IExposureTime``, ``PipelineCamera``'s
  state entirely (including the ``IExposure`` required by ``ICamera``), ``FlatField``'s
  ``IMotion``, and ``MotionStatusMixin``'s separately-enumerated ``IReady`` (which ``IMotion``
  implies) -- folding ``BaseRoof``'s duplicate ready-derivation and ``DummyMode``'s hardcoded
  publish into the mixin's shared default.
* Added ``Comm.unregister_event()``, the missing inverse of ``register_event()`` -- previously a
  caller torn down while the app keeps running (e.g. a GUI widget discarded on client disconnect)
  could never stop receiving events, keeping it alive and firing on every future matching event.
  (#438)
* Fixed a ``ZeroDivisionError`` in ``FlatFielder._calc_new_exptime`` when a test flat-field's
  median counts equal or fall below the bias level (e.g. sky still very dark); now clamps to the
  max exposure-time increase factor instead. (#481)

v2.0.0.dev21 (2026-07-15)
=========================
* Bounded ``XmppComm._safe_send`` with its own 15s ``asyncio.wait_for()`` timeout, instead of
  relying entirely on slixmpp's internal IQ timeout (default 120s, which could fail to fire even on
  a healthy connection) -- an unbounded hang here could freeze the calling module, including inside
  ``open()``, which blocks the whole event loop. (#664)

v2.0.0.dev20 (2026-07-15)
=========================
* Internal only: fixed the remaining deprecated ``self._xmpp[...]``-style slixmpp plugin-subscript
  access in ``XmppComm``, following up on the earlier migration to ``client.plugin[...]``.

v2.0.0.dev19 (2026-07-15)
=========================
* Reintroduced the old ``IPointingHGS`` lon/lat contract as ``IPointingHeliographicStonyhurst``, now
  a separate interface from ``IPointingHeliocentricPolar`` instead of a repurposing of it -- drivers
  needing Heliographic Stonyhurst tracking (e.g. ``pyobs_iagvt``'s ``SolarTelescope``) should
  implement this one instead.
* Removed ``pyobs.modules.utils.AutonomousWarning`` (played warning sounds while an ``IAutonomous``
  module was running). Found while writing tests for it: ``started_sound``/``stopped_sound`` were
  stored but never read anywhere, and ``_check_autonomous()``'s sound selection looked inverted (it
  logged "Robotic systems started" but played ``stop_sound``, apparently copy-pasted from
  ``_check_trigger()``'s toggle logic without adjusting the polarity) -- breaking change for anyone
  using it, no replacement provided.
* Fixed three ``BaseVideo`` bugs found while reviewing it: a request-list race where
  ``grab_data()`` removed its request from ``_image_requests`` without holding
  ``_image_request_lock``, while ``_set_image()`` iterates/mutates the same list under that lock
  across an ``await`` (could skip another pending request); a fallback-filename bug where
  ``_finish_image()``'s ``"image.fits"`` fallback (used when no filename pattern is configured)
  never reached ``image.header["FNAME"]``, the actual cache key, raising ``KeyError`` instead of
  degrading gracefully; and removed the dead ``_new_image_event`` (set every frame, never waited on
  anywhere -- the real new-image notification is the separate ``NewImageEvent`` comm event).
* Split ``DummyTelescope`` into ``DummyRaDecTelescope`` (+``IOffsetsRaDec``), ``DummyAltAzTelescope``
  (+``IOffsetsAltAz``), and ``DummySolarTelescope`` (+``IPointingHeliocentricPolar``,
  ``IPointingHeliographicStonyhurst``, ``IPointingHelioprojective`` -- always tracks the Sun via a
  dedicated background task, no compatibility alias for the old class name). See
  ``dummy-telescope-split-design.md``.
* Renamed ``IPointingHGS`` to ``IPointingHeliocentricPolar`` and its fields from ``lon``/``lat`` to
  ``mu``/``psi``, matching the existing ``HeliocentricPolarTarget`` -- the old fields actually
  represented Heliographic Stonyhurst coordinates, a different frame; breaking change for any
  external driver implementing it (e.g. ``pyobs_iagvt``, tracked separately).
* ``Object.location`` is now derived from ``Object.observer`` instead of being stored and propagated to
  child objects independently, removing a source of location/observer divergence. The ``location``
  constructor argument is unchanged, but only affects the default ``observer`` built from it.
* Fixed ``Scheduler._on_task_finished`` silently ignoring ``TaskFailedEvent`` (registered as its
  handler alongside ``TaskFinishedEvent``, but its own guard only accepted the latter -- a sibling
  class, not a subclass), so a failed task never cleared ``_current_task_id`` or triggered a
  re-schedule even with ``trigger_on_task_finished`` enabled.
* Implemented non-sidereal tracking: new ``ITrackingMode``/``ITrackingRate`` interfaces (discrete
  vs. continuous tracking modes) and ``IPointingBody``/``IPointingOrbitalElements`` (track a named
  body or a set of orbital elements), plus ``ARCSEC_PER_SEC``/``AU`` units. ``BaseTelescope``
  implements the continuous-tracking background task, propagating a tracked body or orbital
  elements (two-body Kepler solve, hand-rolled rather than via ``poliastro`` -- ~6us/call for the
  propagation itself, dominated by astropy's own frame-transform cost) into a live RA/Dec
  correction, with the refresh interval clamped against the mount's own published
  ``min_update_interval`` (via the new ``Comm.get_own_capabilities()``, mirroring
  ``get_own_state``). ``DummyTelescope`` (see split above) is the reference implementation;
  ``BaseTelescope`` also now publishes ``AltAzState`` for ``IPointingAltAz`` telescopes.
  ``track_body()`` resolves via ``astropy.coordinates.get_body``/JPL Horizons only -- deliberately
  no automatic MPC/NEOCP-by-designation lookup, since MPC has no formal REST API and scraping would
  be riskiest for exactly the fresh-NEOCP-object case the feature exists for; a caller with elements
  in hand uses ``track_orbital_elements()`` directly. See ``tracking-mode-design.md``.
* Fixed two crash paths in ``FitsHeaderMixin``'s header-building: ``_fitsheadermixin_add_framenum()``
  read ``hdr["DAY-OBS"]`` unconditionally, but that key is only set when ``DATE-OBS`` was present,
  crashing with ``KeyError`` instead of the warn-and-skip its own log message implied; and
  ``_fitsheadermixin_add_fits_headers()`` called ``date_obs.night_obs()`` (which needs a real
  ``Observer``) whenever ``night_obs=True`` (the default) even with no observer configured,
  crashing with ``AttributeError`` instead of falling back to the plain calendar day like the
  location handling right above it already does.
* Fixed ``FlatFielder``'s deviation check comparing a fraction against ``target_count`` (a raw
  count-rate) instead of the already-stored ``_allowed_offset_frac``, so the "retry if the flat is
  way off target" check could essentially never trigger.
* Added an import-time registry for ``Interface`` subclasses
  (``pyobs.interfaces.interface.get_registered_interface``/``registered_interfaces``), and switched
  ``Module._get_interfaces_and_methods``, ``XmppComm._get_interfaces``, and
  ``Comm._interface_names_to_classes`` to resolve through it instead of hardcoded lookups against
  the ``pyobs.interfaces`` module namespace -- previously a module implementing an
  externally-defined interface (e.g. a driver package's own) was never discovered, advertised, or
  resolved by name at all.
* Fixed XMPP wire serialization corrupting/mishandling numpy scalar types: ``numpy>=2.0`` changed
  ``np.float64``'s ``repr()`` to ``"np.float64(x)"``, corrupting the ``<double>`` element text and
  aborting reconstruction of the whole enclosing dataclass (e.g. dropping ``IModule``
  ``capabilities.version`` alongside a malformed ``location.longitude``); ``np.integer`` types
  aren't subclasses of ``int`` at all and silently fell through to the ``<string>`` fallback
  instead of ``<int>``. Any ``np.generic`` scalar is now converted to its native Python type before
  serialization.

v2.0.0.dev18 (2026-07-12)
=========================
* Fixed ``DummyTelescope.set_focus_offset`` silently logging an error instead of raising, which made
  remote callers see a false success; its M1/M2 temperatures now drift like ``DummyCamera``'s sensors
  instead of staying static after startup.
* ``pyobsd`` now defaults to sending module logs to the systemd journal (``--syslog`` is on by
  default; pass ``--no-syslog`` to disable it).
* Added ``pyobsd logs [module] [journalctl arguments...]``, a thin passthrough to ``journalctl``
  filtered to the module's journal fields.

v2.0.0.dev17 (2026-07-11)
=========================
* Added a ``/ping`` health-check endpoint to ``HttpFileCache`` and ``BaseVideo``, for verifying HTTP
  connectivity without touching the file/image cache.

v2.0.0.dev16 (2026-07-10)
=========================
* Added ``IStructuredConfig``, letting a module push/apply its whole config dataclass as a unit
  (schema auto-derived via ``dataclass_to_schema``), complementing ``IConfig``'s per-field get/set.
* Added ``pydantic_to_schema``, the Pydantic-model counterpart to ``dataclass_to_schema``, for module
  configs (e.g. pyobs-iagvt's ``FTSConfig``) that need Pydantic's own validation.
* Renamed ``HeliocentricPolar`` to ``HeliocentricPolarTarget`` for naming consistency.
* Replaced ``HelioprojectiveRadialTarget`` with ``HelioprojectiveTarget``, using the Helioprojective
  frame's Tx/Ty (arcsec) directly instead of a radial (psi/delta) representation.

v2.0.0.dev15 (2026-07-10)
=========================
* Fixed ``HttpFileCache`` rejecting uploads with "413 Request Entity Too Large" because
  ``client_max_size`` was never passed through to configure the upload limit.

v2.0.0.dev14 (2026-07-09)
=========================
* Fixed ``Scheduler``, ``Trigger``, ``Kiosk``, ``PointingSeries``, ``Weather``, ``MockWeather``, and
  ``Mastermind`` never publishing their advertised ``IRunning`` state, leaving subscribers retrying
  indefinitely.
* The LCO schedule backend now logs the next observation after a schedule update, matching
  ``BackendObservationArchive``.

v2.0.0.dev13 (2026-07-09)
=========================
* Internal fixes only: resolved the remaining pyrefly type-check errors blocking CI.

v2.0.0.dev12 (2026-07-09)
=========================
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
=========================
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
=========================
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
========================
* Linked all ``pyobs-*`` module docs, now hosted on docs.pyobs.org.

v2.0.0.dev8 (2026-07-01)
========================
* Documented optional extras and CLI tools in the README.

v2.0.0.dev7 (2026-07-01)
========================
* Minor internal fixes (Dependabot configuration, import scoping in ``DummyCamera``).

v2.0.0.dev6 (2026-06-30)
========================
* Renamed the ``state``/``capabilities`` proxy accessor methods to ``get_state``/``get_capabilities``
  for clarity; both are now also available directly on ``Interface``.
* Added IERS offline mode support via the ``PYOBS_IERS_OFFLINE`` environment variable.
* The ``pyobs`` service now loads environment variables from ``/etc/default/pyobs``.
* Added ``astropy-iers-data`` as a direct dependency.

v2.0.0.dev5 (2026-06-30)
========================
* Refactored ``capabilities`` handling for consistency across interfaces.

v2.0.0.dev4 (2026-06-29)
========================
* Interface ``State`` classes are now module-level dataclasses rather than nested classes.

v2.0.0.dev3 (2026-06-29)
========================
* Removed ``pyobs.utils.simulation`` (``SimWorld``/``SimTelescope``/``SimCamera``) with no
  replacement.
* Added ``DummyVideo`` for simulated video streaming.
* ``IMode`` now uses ``capabilities``/``state`` dataclasses instead of separate mode-group methods.
* Added an optional ``sender`` attribute to ``LogEvent``.

v2.0.0.dev2 (2026-06-29)
========================
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
========================
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
********************
* Added `list` command for `pyobsd`, which outputs all configurations.
* Added bash auto-complete script `pyobsd`.
* Added timeouts (to be defined in the config) for `ScriptRunner` modules.


v1.11.0 (2023-12-25)
********************
* Acquisition and AutoFocus both got a `broadcast` option to disable broadcast of images.
* AutoFocus got a `final_image` parameter to take a final image at optimal focus.


v1.10.0 (2023-12-24)
********************
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