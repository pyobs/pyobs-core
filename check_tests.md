# Tests accessing private (underscore-prefixed) variables

Snapshot after the comm/observer/location/timezone/vfs constructor-routing pass (see "Resolved this session" below). Split into two buckets.

## Resolved this session

18 test files were changed to pass `comm`/`observer`/`location`/`timezone`/`vfs` into the constructor (`Object.__init__` params for `Object` subclasses, or `Model.model_validate(data, context={...})` for the pydantic-based `Picker`/`Target`/`Task`/`Script` classes) instead of poking the private attribute after construction:

`test_presence.py`, `test_save.py`, `test_basetelescope.py`, `test_mockweather.py`, `test_weather.py`, `test_csvpicker_scheduler.py`, `test_dynamic_target.py`, `test_dynamictarget.py`, `test_dynamictarget_scheduler.py`, `test_xmpp_presence.py`, `test_autofocus.py`, `test_callmodule.py`, `test_control.py`, `test_darkbias.py`, `test_transitimaging.py`, `test_transit_mastermind.py` (script bits only), `test_imagewatcher.py`, `test_imagewriter.py`, `test_task.py` (helper was dead code, removed).

Full suite verified: `pytest tests/` (858 passed, 2 skipped) and, against a local ejabberd, `pytest tests/integration -m "integration or xmpp"` (72 passed).

**Left unresolved, deliberately, within that same scope:**

- `tests/comm/test_presence.py:39` -- `module._comm = None`. `Object.__init__`'s `comm=None` means "use a default `DummyComm()`", not "leave it unset", so this exact state can't be produced via the constructor.
- 8 files using a `Class.__new__(Class)` + all-`None` null-test-double pattern for logic-only tests (listed under Bucket A below, still tagged `[comm/observer/location/timezone/vfs -- exception]`) -- `Object.__init__` raises `ValueError` for `timezone=None`, so there's no constructor call that reproduces the state these tests deliberately want.

**Update (later session):** `tests/integration/conftest.py`'s `make_xmpp_comm` fixture -- originally flagged above as "fixable in principle, not attempted" -- has since been fixed. See `TODO.md`. `make_unopened_comm(user)` now builds comm before the module exists, and `make_module(interfaces, comm, ...)` wires itself to it internally, instead of `make_xmpp_comm` retrofitting `module._comm = comm` onto an already-built module. Only 14 of the ~44 `make_xmpp_comm` call sites (`test_xmpp_presence.py`, `test_xmpp_state.py`) actually needed the change. The one line still poking `module._comm` in that file (`connect()`, L32) is unrelated dead code -- a LocalComm helper with zero callers anywhere in the suite, not part of the XMPP fixture.

**Never in scope this session:** every other private attribute in Bucket A (`_state`, `_label`, `_own_comm`, `_config_caps`, `_acl_allow`, `_queue`, `_active`, etc.), and all of Bucket B (state-assertion reads). Both remain exactly as before.

## Resolved in the Bucket B review (follow-up session)

All 171 distinct test functions flagged in Bucket B (grouped by function, not raw line -- the 314-line count below is per-line) were reviewed individually, same depth as the check_mocks.md Bucket 5 pass. Outcomes:

- **~155 fine, no change** -- the private attribute has no reasonable public equivalent (internal algorithm state in a decomposed pipeline already unit-tested step-by-step elsewhere, e.g. `ProjectedOffsets`/`_DotNetRequestBuilder`/`StarExpTimeEstimator`; pure internal bookkeeping like `BackgroundTask._task`, `Comm._interface_features`, `LcoScheduleReader._scheduled_tasks`; or a private attribute used only to build an expected-value baseline for a real mock/behavior assertion, e.g. `astrometry._request_builder._source_count`).
- **~16 strengthened** to use a public accessor that already existed but wasn't being used: `Task.target` property (6 call sites across `test_csvpicker_scheduler.py`, `test_dynamic_target.py`, `test_dynamictarget_scheduler.py` -- only safe for success-case assertions, since the property falls back to `static_target` rather than `None` on failure), `DummyRoof.get_percent_open()` (6x in `test_dummyroof.py`), `Weather`/`MockWeather.is_running()` (4x), `AutoFocusSeries.is_running()`, `MockWeather.get_sensor_value()`, `MemoryTaskArchive.get_task()`/`.last_changed()` (3x in `test_memory_archives.py`), `_CalibrationCache.get_from_cache()` (2x), `LocalNetwork.get_client()`/`.get_client_names()`, `XmppComm.get_interfaces()`/`.clients`, `RollingTimeAverage.average()`.
- **2 real bugs found and fixed**, both matching the `stellarexptime.py` collection-bug pattern from the mock-audit session:
  - `tests/modules/test/standalone.py` -> `test_standalone.py`: missing the `test_` prefix, so pytest's default collection glob silently skipped the whole file -- **29 ACL tests never ran in CI.** All 29 passed once collected (no hidden bugs this time, unlike `stellarexptime.py`).
  - `tests/utils/grids/test_filters.py::test_fromlistfilter`: patched `astropy.time.Time.now`, but `pyobs.utils.time.Time` (what the code under test actually imports and calls) overrides `now()` itself as a separate classmethod, so the patch never took effect -- the test silently ran against the real wall-clock time instead of the frozen date, and only broke when the date actually rolled over mid-session. Fixed to patch `pyobs.utils.time.Time.now`.

Verified: `pytest tests/` (896 passed, 2 skipped -- 29 more than the prior session's 867, from `test_standalone.py` now being collected).

## Resolved in the Bucket A remainder review (follow-up session)

The rest of Bucket A (everything other than `comm`/`observer`/`location`/`timezone`/`vfs`, already handled above) was reviewed function-by-function, same depth as the Bucket B pass: 174 write lines across 94 functions in 33 files. Outcomes:

- **Vast majority fine, no change** -- either the null-test-double `Class.__new__(Class)` pattern continuing to set its own fields (same exception as the comm/observer/location/timezone/vfs case -- `test_mastermind.py`/`test_scheduler_mastermind.py`'s `make_obs_archive`/`make_mastermind`, `lco/helpers.py`'s `make_task_archive`/`make_observation_archive`, `test_schedulewriter.py`/`test_yaml_archives.py`'s factories), a test-double subclass's own `__init__`/methods setting its own state (`TransitQuickRunner.__init__`, `MockPhotometryCalculator`, `_weather_mock`), or private state with no public equivalent that's necessary to isolate the method under test from the rest of the pipeline (`StarExpTimeEstimator._image`, `_DotNetRequestBuilder._catalog`, `ProjectedOffsets._ref_image`, `TransitImagingScript._transit_merit` in both `test_transit_mastermind.py` and `test_transitimaging.py`, `LcoTaskArchive._tasks`/`_last_changed`/`_projects` in `test_lco_http.py` -- all only ever populated by a private network-polling method with no constructor/setter path).
- **8 strengthened** to use a public accessor/constructor param that already existed but wasn't being used: `MemoryTaskArchive.add_task()` (2x in `test_memory_archives.py`, replacing direct `_tasks` dict writes), `Mastermind.stop()` (3x across `test_mastermind.py`/`test_scheduler_mastermind.py`, replacing `mm._running = False` teardown pokes -- `_comm` is a real `DummyComm()` in these null-doubles, so the async call is safe), `make_mastermind`'s new `task_archive=` param (`test_dynamic_target.py`, replacing a `mm._task_archive = ...` poke after the factory call), `AddMask`'s already-existing `masks` constructor param (`test_addmask.py`, replacing `AddMask({}); adder._masks = masks`), `_CalibrationCache.add_to_cache()` (2x in `test_calibration_cache.py`, replacing direct `_cache` deque writes), `Weather.stop()`/`MockWeather.stop()` (3x, replacing `_active = False` pokes in `is_running`/`set_good` tests).
- **1 real bug found and fixed**: `tests/modules/weather/test_weather.py::test_start` poked `weather._is_good = False`, but the real attribute is `weather._weather.is_good` (a property on a nested `WeatherStatus` object) -- `_is_good` doesn't exist on `Weather` at all, so the line silently created an unused instance attribute and had zero effect. The test passed anyway only because `WeatherStatus` already defaults `is_good` to `False`. Removed the dead line.
- **4 redundant pokes removed**: `test_focusmodel.py`'s `fm._enabled = True` (already the constructor default) and three `weather._active = True` pokes in `test_weather.py` (`test_update_good_weather`, `test_update_bad_weather`, `test_update_publishes_state` -- `_active` already defaults to `True`).

Verified: `pytest tests/ -m "not integration and not xmpp"` (896 passed, 2 skipped) and, against a local ejabberd, `pytest tests/ -m "integration or xmpp"`.

## Bucket A -- Setup pokes (writes): tests assign directly to a private attribute

253 lines across 34 files (conftest.py's count changed after the `make_xmpp_comm` fix -- see above). Pattern: `obj._attr = value` used to inject a test double or seed state post-construction, instead of going through the constructor / a public API.

### tests/comm/local/test_istructuredconfig.py (4)

- L24: `self._config = DummyConfig()`
- L27: `self._config = dataclasses.replace(self._config, **config)`
- L34: `LocalNetwork._instance = None`
- L36: `LocalNetwork._instance = None`

### tests/comm/local/test_localcomm.py (2)

- L16: `LocalNetwork._instance = None`
- L18: `LocalNetwork._instance = None`

### tests/comm/local/test_localcomm_state.py (2)

- L16: `LocalNetwork._instance = None`
- L18: `LocalNetwork._instance = None`

### tests/comm/local/test_localnetwork.py (2)

- L8: `LocalNetwork._instance = None`
- L10: `LocalNetwork._instance = None`

### tests/comm/test_presence.py (36)

- L37: `module._state = ModuleState.READY`
- L38: `module._error_string = ""`
- L39: `module._comm = None`  _[comm/observer/location/timezone/vfs -- exception: see above]_
- L52: `module._error_string = "existing error"`
- L67: `module._state = ModuleState.ERROR`
- L68: `module._error_string = "previous error"`
- L90: `module._label = "Test Camera"`
- L91: `module._child_objects = []`
- L92: `module._own_comm = False  # skip comm.open()`
- L93: `module._config_caps = {}  # no config caps for stub`
- L119: `module._label = None`
- L120: `module._child_objects = []`
- L121: `module._own_comm = False`
- L122: `module._config_caps = {}`
- L149: `module._label = "Test Camera"`
- L150: `module._child_objects = []`
- L151: `module._own_comm = False`
- L152: `module._config_caps = {}`
- L177: `self._proxy = proxy`
- L305: `comm._client_states = {}`
- L306: `comm._online_clients = []`
- L307: `comm._interface_cache = {}`
- L351: `comm._jid = "gui@localhost/pyobs"`
- L352: `comm._interface_cache = {}`
- L353: `comm._client_states = {}`
- L354: `comm._online_clients = []`
- L355: `comm._presence_callbacks = {}`
- L356: `comm._event_handlers = {}`
- L386: `comm._jid = "gui@localhost/pyobs"`
- L387: `comm._interface_cache = {}`
- L388: `comm._client_states = {}`
- L389: `comm._online_clients = []`
- L390: `comm._presence_callbacks = {"camera": [MagicMock(side_effect=RuntimeError("Signal source has been deleted"))]}`
- L391: `comm._event_handlers = {ModuleOpenedEvent: [handler]}`
- L451: `comm._client_states = {}`
- L452: `comm._online_clients = []`

### tests/comm/test_version_mismatch.py (4)

- L31: `comm._domain = "localhost"`
- L32: `comm._resource = "pyobs"`
- L33: `comm._interface_features = {}`
- L34: `comm._warned_version_mismatches = set()`

### tests/images/processors/astrometry/test_dotnet.py (1)

- L142: `self._text = text`

### tests/images/processors/astrometry/test_dotnet_request.py (3)

- L9: `request._response_data = {}`
- L12: `request._response_data = {"error": "Could not find WCS file."}`
- L15: `request._response_data = {"error": "Test"}`

### tests/images/processors/astrometry/test_dotnet_request_builder.py (1)

- L11: `request_builder._catalog = pandas_catalog`

### tests/images/processors/exptime/test_star.py (2)

- L44: `estimator._image = mock_image`
- L55: `estimator._image = mock_image`

### tests/images/processors/misc/test_addmask.py (1)

- L49: `adder._masks = masks`

### tests/images/processors/misc/test_calibration_cache.py (2)

- L29: `cache._cache = deque([((image_type, image_instrument, image_binning, image_filter), cached_image)], 5)`
- L56: `cache._cache = deque([((image_type, image_instrument, image_binning, image_filter), other_image)], 1)`

### tests/images/processors/offsets/test_projected.py (3)

- L16: `offsets._ref_image = np.zeros((2, 2))`
- L107: `offsets._ref_image = (np.ones(10) * 10, np.ones(10) * 10)`
- L122: `offsets._ref_image = (np.ones(10) * 10, np.ones(10) * 10)`

### tests/images/processors/photometry/test_aperture_photometry.py (2)

- L15: `self._catalog = None`
- L22: `self._catalog = image.catalog.copy()`

### tests/integration/conftest.py (5) -- updated after the `make_xmpp_comm` fix, see above

- L21: `LocalNetwork._instance = None`
- L23: `LocalNetwork._instance = None`
- L32: `module._comm = comm`  _[dead code -- `connect()` has no callers anywhere in the suite, unrelated to the XMPP fixture]_
- L118: `m._label = label`  _[fine -- `make_module()` is a test-double factory setting its own state, same pattern as `DummyStructuredConfigModule.__init__`]_
- L121: `m._comm = comm`  _[fine -- same as above; comm is now passed in as a parameter rather than retrofitted from outside]_

### tests/integration/test_dynamic_target.py (1)

- L176: `mm._task_archive = task_archive`

### tests/integration/test_mastermind.py (32)

- L26: `obj._comm = None`  _[comm/observer/location/timezone/vfs -- exception: null test double]_
- L27: `obj._observer = None`  _[comm/observer/location/timezone/vfs -- exception: null test double]_
- L28: `obj._vfs = None`  _[comm/observer/location/timezone/vfs -- exception: null test double]_
- L29: `obj._timezone = None`  _[comm/observer/location/timezone/vfs -- exception: null test double]_
- L30: `obj._location = None`  _[comm/observer/location/timezone/vfs -- exception: null test double]_
- L48: `obj._comm = None`  _[comm/observer/location/timezone/vfs -- exception: null test double]_
- L49: `obj._observer = None`  _[comm/observer/location/timezone/vfs -- exception: null test double]_
- L50: `obj._vfs = None`  _[comm/observer/location/timezone/vfs -- exception: null test double]_
- L51: `obj._timezone = None`  _[comm/observer/location/timezone/vfs -- exception: null test double]_
- L52: `obj._location = None`  _[comm/observer/location/timezone/vfs -- exception: null test double]_
- L74: `archive._comm = None`  _[comm/observer/location/timezone/vfs -- exception: null test double]_
- L75: `archive._observer = None`  _[comm/observer/location/timezone/vfs -- exception: null test double]_
- L76: `archive._vfs = None`  _[comm/observer/location/timezone/vfs -- exception: null test double]_
- L77: `archive._timezone = None`  _[comm/observer/location/timezone/vfs -- exception: null test double]_
- L78: `archive._location = None`  _[comm/observer/location/timezone/vfs -- exception: null test double]_
- L79: `archive._observations = ObservationList()`
- L89: `mm._comm = DummyComm()`  _[comm/observer/location/timezone/vfs -- exception: null test double]_
- L90: `mm._observer = None`  _[comm/observer/location/timezone/vfs -- exception: null test double]_
- L91: `mm._vfs = None`  _[comm/observer/location/timezone/vfs -- exception: null test double]_
- L92: `mm._timezone = None`  _[comm/observer/location/timezone/vfs -- exception: null test double]_
- L93: `mm._location = None`  _[comm/observer/location/timezone/vfs -- exception: null test double]_
- L94: `mm._allowed_late_start = 300`
- L95: `mm._allowed_overrun = 300`
- L96: `mm._after_task_sleep = 0`
- L97: `mm._running = True`
- L98: `mm._task = None`
- L99: `mm._task_archive = None`
- L100: `mm._last_cant_run_reason = {}`
- L101: `mm._observation_archive = obs_archive`
- L102: `mm._task_runner = runner`
- L148: `mm._running = False`
- L226: `mm._running = False`

### tests/integration/test_scheduler_mastermind.py (7)

- L28: `archive._comm = None`  _[comm/observer/location/timezone/vfs -- exception: null test double]_
- L29: `archive._observer = None`  _[comm/observer/location/timezone/vfs -- exception: null test double]_
- L30: `archive._vfs = None`  _[comm/observer/location/timezone/vfs -- exception: null test double]_
- L31: `archive._timezone = None`  _[comm/observer/location/timezone/vfs -- exception: null test double]_
- L32: `archive._location = None`  _[comm/observer/location/timezone/vfs -- exception: null test double]_
- L33: `archive._observations = ObservationList()`
- L208: `mm._running = False`

### tests/integration/test_transit_mastermind.py (10)

- L76: `self._comm = None`  _[comm/observer/location/timezone/vfs -- exception: null test double]_
- L77: `self._observer = None`  _[comm/observer/location/timezone/vfs -- exception: null test double]_
- L78: `self._vfs = None`  _[comm/observer/location/timezone/vfs -- exception: null test double]_
- L79: `self._timezone = None`  _[comm/observer/location/timezone/vfs -- exception: null test double]_
- L80: `self._location = None`  _[comm/observer/location/timezone/vfs -- exception: null test double]_
- L83: `self._end_time = end_time`
- L168: `script._transit_merit = merit`
- L176: `script._run_configuration = mock_run_configuration`
- L212: `script._transit_merit = merit`
- L220: `script._run_configuration = mock_run_configuration`

### tests/integration/test_xmpp_presence.py (1)

- L36: `m._label = label`

### tests/modules/focus/test_focusmodel.py (1)

- L61: `fm._enabled = True`

### tests/modules/roof/test_dummyroof.py (1)

- L43: `roof._open_percentage = 100`

### tests/modules/weather/test_mockweather.py (4)

- L42: `weather._active = False`
- L43: `weather._good = False`
- L66: `weather._active = False`
- L112: `weather._active = False`

### tests/modules/weather/test_weather.py (7)

- L36: `weather._active = False`
- L37: `weather._is_good = False`
- L57: `weather._active = False`
- L170: `weather._active = True`
- L186: `weather._active = True`
- L209: `weather._active = True`
- L233: `weather._active = False`

### tests/modules/weather/test_weather_api.py (1)

- L11: `self._json = json`

### tests/robotic/scripts/test_transitimaging.py (7)

- L84: `script._transit_merit = merit`
- L93: `script._run_configuration = mock_run_configuration`
- L117: `script._transit_merit = merit`
- L128: `script._run_configuration = mock_run_configuration`
- L139: `script._transit_merit = None`
- L155: `script._transit_merit = merit`
- L163: `script._run_configuration = mock_run_configuration`

### tests/robotic/storage/backend/test_backend_archives.py (33)

- L35: `archive._comm = None`  _[comm/observer/location/timezone/vfs -- exception: null test double]_
- L36: `archive._observer = None`  _[comm/observer/location/timezone/vfs -- exception: null test double]_
- L37: `archive._vfs = None`  _[comm/observer/location/timezone/vfs -- exception: null test double]_
- L38: `archive._timezone = None`  _[comm/observer/location/timezone/vfs -- exception: null test double]_
- L39: `archive._location = None`  _[comm/observer/location/timezone/vfs -- exception: null test double]_
- L40: `archive._url = "http://localhost:8000"`
- L41: `archive._token = "testtoken"`
- L43: `archive._last_update = None`
- L44: `archive._projects = []`
- L45: `archive._tasks = []`
- L46: `archive._on_tasks_changed = None`
- L52: `archive._comm = None`  _[comm/observer/location/timezone/vfs -- exception: null test double]_
- L53: `archive._observer = None`  _[comm/observer/location/timezone/vfs -- exception: null test double]_
- L54: `archive._vfs = None`  _[comm/observer/location/timezone/vfs -- exception: null test double]_
- L55: `archive._timezone = None`  _[comm/observer/location/timezone/vfs -- exception: null test double]_
- L56: `archive._location = None`  _[comm/observer/location/timezone/vfs -- exception: null test double]_
- L57: `archive._url = "http://localhost:8000"`
- L58: `archive._token = "testtoken"`
- L60: `archive._last_update = None`
- L61: `archive._observations = ObservationList()`
- L77: `archive._last_update = T0`
- L84: `archive._projects = [Project(code="test", name="Test", priority=1.0)]`
- L93: `archive._tasks = [make_task(1), make_task(2)]`
- L102: `archive._tasks = [task]`
- L110: `archive._tasks = []`
- L156: `archive._observations = ObservationList([obs])`
- L166: `archive._observations = ObservationList([obs])`
- L175: `archive._observations = ObservationList([obs])`
- L187: `archive._observations = ObservationList([obs])`
- L198: `archive._observations = ObservationList([obs])`
- L209: `archive._observations = ObservationList([obs])`
- L224: `archive._observations = ObservationList([obs])`
- L234: `archive._observations = ObservationList([obs])`

### tests/robotic/storage/filesystem/test_yaml_archives.py (16)

- L33: `archive._comm = None`  _[comm/observer/location/timezone/vfs -- exception: null test double]_
- L34: `archive._vfs = None`  _[comm/observer/location/timezone/vfs -- exception: null test double]_
- L35: `archive._timezone = None`  _[comm/observer/location/timezone/vfs -- exception: null test double]_
- L36: `archive._location = None`  _[comm/observer/location/timezone/vfs -- exception: null test double]_
- L37: `archive._observer = SAAO`  _[comm/observer/location/timezone/vfs -- exception: null test double]_
- L38: `archive._path = str(tmp_path)`
- L39: `archive._extension = "yaml"`
- L40: `archive._mode = mode`
- L41: `archive._lock = FileLock(os.path.join(str(tmp_path), ".lock"))`
- L263: `archive._comm = None`  _[comm/observer/location/timezone/vfs -- exception: null test double]_
- L264: `archive._observer = None`  _[comm/observer/location/timezone/vfs -- exception: null test double]_
- L265: `archive._timezone = None`  _[comm/observer/location/timezone/vfs -- exception: null test double]_
- L266: `archive._location = None`  _[comm/observer/location/timezone/vfs -- exception: null test double]_
- L267: `archive._path = str(tmp_path)`
- L268: `archive._extension = "yaml"`
- L282: `archive._vfs = vfs`  _[comm/observer/location/timezone/vfs -- exception: null test double]_

### tests/robotic/storage/lco/helpers.py (25)

- L16: `p._comm = None`  _[comm/observer/location/timezone/vfs -- exception: null test double]_
- L17: `p._observer = None`  _[comm/observer/location/timezone/vfs -- exception: null test double]_
- L18: `p._vfs = None`  _[comm/observer/location/timezone/vfs -- exception: null test double]_
- L19: `p._timezone = None`  _[comm/observer/location/timezone/vfs -- exception: null test double]_
- L20: `p._location = None`  _[comm/observer/location/timezone/vfs -- exception: null test double]_
- L25: `p._site = "goe"`
- L26: `p._enclosure = "roof"`
- L27: `p._telescope = "0m5a"`
- L38: `archive._comm = None`  _[comm/observer/location/timezone/vfs -- exception: null test double]_
- L39: `archive._observer = None`  _[comm/observer/location/timezone/vfs -- exception: null test double]_
- L40: `archive._vfs = None`  _[comm/observer/location/timezone/vfs -- exception: null test double]_
- L41: `archive._timezone = None`  _[comm/observer/location/timezone/vfs -- exception: null test double]_
- L42: `archive._location = None`  _[comm/observer/location/timezone/vfs -- exception: null test double]_
- L43: `archive._portal = make_portal()`
- L44: `archive._instrument_type = [instrument_type]`
- L45: `archive._last_changed = None`
- L46: `archive._tasks = []`
- L47: `archive._projects = []`
- L48: `archive._on_tasks_changed = None`
- L55: `archive._comm = None`  _[comm/observer/location/timezone/vfs -- exception: null test double]_
- L56: `archive._observer = None`  _[comm/observer/location/timezone/vfs -- exception: null test double]_
- L57: `archive._vfs = None`  _[comm/observer/location/timezone/vfs -- exception: null test double]_
- L58: `archive._timezone = None`  _[comm/observer/location/timezone/vfs -- exception: null test double]_
- L59: `archive._location = None`  _[comm/observer/location/timezone/vfs -- exception: null test double]_
- L60: `archive._portal = make_portal()`

### tests/robotic/storage/lco/test_lco_http.py (5)

- L35: `archive._tasks = [task]`
- L74: `archive._last_changed = Time("2026-05-27T08:18:50Z")`
- L93: `archive._projects = [`
- L108: `archive._tasks = [task]`
- L118: `archive._tasks = []`

### tests/robotic/storage/lco/test_schedulereader.py (18)

- L23: `reader._comm = None`  _[comm/observer/location/timezone/vfs -- exception: null test double]_
- L24: `reader._observer = None`  _[comm/observer/location/timezone/vfs -- exception: null test double]_
- L25: `reader._vfs = None`  _[comm/observer/location/timezone/vfs -- exception: null test double]_
- L26: `reader._timezone = None`  _[comm/observer/location/timezone/vfs -- exception: null test double]_
- L27: `reader._location = None`  _[comm/observer/location/timezone/vfs -- exception: null test double]_
- L28: `reader._portal = portal or make_portal()`
- L29: `reader._site = "goe"`
- L30: `reader._telescope = "0m5a"`
- L31: `reader._last_schedule_time = None`
- L32: `reader._update_lock = asyncio.Lock()`
- L33: `reader._auto_updates = auto_updates`
- L34: `reader._last_scheduled = None`
- L35: `reader._scheduled_tasks = ObservationList()`
- L70: `reader._scheduled_tasks = ObservationList([obs])`
- L88: `reader._scheduled_tasks = ObservationList([obs])`
- L105: `reader._scheduled_tasks = ObservationList([obs])`
- L120: `reader._scheduled_tasks = ObservationList([obs])`
- L129: `reader._scheduled_tasks = ObservationList()`

### tests/robotic/storage/lco/test_schedulewriter.py (11)

- L31: `writer._comm = None`  _[comm/observer/location/timezone/vfs -- exception: null test double]_
- L32: `writer._observer = None`  _[comm/observer/location/timezone/vfs -- exception: null test double]_
- L33: `writer._vfs = None`  _[comm/observer/location/timezone/vfs -- exception: null test double]_
- L34: `writer._timezone = None`  _[comm/observer/location/timezone/vfs -- exception: null test double]_
- L35: `writer._location = None`  _[comm/observer/location/timezone/vfs -- exception: null test double]_
- L36: `writer._portal = portal or make_portal()`
- L37: `writer._configdb = configdb or make_configdb()`
- L38: `writer._site = "goe"`
- L39: `writer._enclosure = "roof"`
- L40: `writer._telescope = "0m5a"`
- L41: `writer._period = 24.0`

### tests/robotic/storage/memory/test_memory_archives.py (2)

- L299: `task_archive._tasks = {"42": task}`
- L313: `task_archive._tasks = {"1": task}`

### tests/utils/grids/test_filters.py (1)

- L72: `grid4._data = SkyCoord(data["RA_ICRS"], data["DE_ICRS"], unit="deg", frame="icrs")`

## Bucket B -- State reads: tests read/assert on a private attribute

314 lines across 54 files. Not addressed this session. Pattern: `assert obj._attr == ...` or using `obj._attr` as part of an assertion or internal test logic -- this asserts on implementation state rather than externally observable behavior (return values, public getters, events fired, side effects on collaborators). These are the better candidates for rewriting the test around behavior, and/or extracting the covered logic into a smaller unit with its own public surface.

### tests/comm/local/test_istructuredconfig.py (2)

- L27: `self._config = dataclasses.replace(self._config, **config)`
- L28: `await self.comm.set_state(IStructuredConfig, ConfigAppliedState(config=dataclasses.asdict(self._config)))`

### tests/comm/local/test_localnetwork.py (2)

- L22: `assert "test" in net._clients`
- L23: `assert net._clients["test"] is client`

### tests/comm/test_presence.py (5)

- L180: `return self._proxy`
- L322: `comm._client_states["camera@localhost/pyobs"] = (ModuleState.READY, "")`
- L332: `comm._client_states["telescope@localhost/pyobs"] = (ModuleState.ERROR, "mount stalled")`
- L363: `future = comm._interface_cache["camera@localhost/pyobs"]`
- L398: `assert "camera@localhost/pyobs" in comm._online_clients`

### tests/comm/test_version_mismatch.py (5)

- L107: `assert comm._interface_features["camera@localhost/pyobs"] == features`
- L117: `comm._interface_features["camera@localhost/pyobs"] = []`
- L130: `comm._interface_features["camera@localhost/pyobs"] = ["urn:pyobs:interface:FakeInterface:2"]`
- L142: `comm._interface_features["camera@localhost/pyobs"] = ["urn:pyobs:interface:FakeInterface:0"]`
- L152: `comm._interface_features["camera@localhost/pyobs"] = ["urn:pyobs:interface:FakeInterface:2"]`

### tests/images/processors/astrometry/test_dotnet.py (6)

- L18: `assert astrometry._request_builder._source_count == 50`
- L19: `assert astrometry._request_builder._radius == 3.0`
- L33: `assert astrometry._request_builder._source_count == source_count`
- L34: `assert astrometry._request_builder._radius == radius`
- L146: `return self._text`
- L149: `return json.loads(self._text)`

### tests/images/processors/astrometry/test_dotnet_request_builder.py (2)

- L14: `assert True not in request_builder._catalog.isna()`
- L15: `assert len(request_builder._catalog[request_builder._catalog["peak"] >= 6000]) == 0`

### tests/images/processors/detection/test_daophot.py (6)

- L12: `assert detector._background_remover._sigma_clip.sigma == 3.0`
- L13: `assert detector._background_remover._box_size == (50, 50)`
- L14: `assert detector._background_remover._filter_size == (3, 3)`
- L28: `assert detector._background_remover._sigma_clip.sigma == bkg_sigma`
- L29: `assert detector._background_remover._box_size == bkg_box_size`
- L30: `assert detector._background_remover._filter_size == bkg_filter_size`

### tests/images/processors/exptime/test_star.py (1)

- L58: `result_table = estimator._image.catalog`

### tests/images/processors/misc/test_addmask.py (2)

- L16: `np.testing.assert_array_equal(adder._masks["camera"]["1x1"], mask)`
- L28: `np.testing.assert_array_equal(adder._masks["camera"]["1x1"], mask)`

### tests/images/processors/misc/test_calibration.py (7)

- L43: `assert calibration._calib_cache is not None`
- L44: `mocker.patch.object(calibration._calib_cache, "get_from_cache", return_value=cached_image)`
- L58: `assert calibration._calib_cache is not None`
- L59: `mocker.patch.object(calibration._calib_cache, "get_from_cache", side_effect=ValueError())`
- L83: `assert calibration._calib_cache is not None`
- L84: `mocker.patch.object(calibration._calib_cache, "add_to_cache")`
- L87: `calibration._calib_cache.add_to_cache.assert_called_once_with(calib_image, image_type)`

### tests/images/processors/misc/test_calibration_cache.py (2)

- L45: `assert cache._cache[0] == ((image_type, image_instrument, image_binning, image_filter), mock_image)`
- L59: `assert cache._cache[0] == ((image_type, image_instrument, image_binning, image_filter), mock_image)`

### tests/images/processors/misc/test_createfilename.py (1)

- L32: `pyobs.images.Image.format_filename.assert_called_once_with(create_filename._formatter)`

### tests/images/processors/misc/test_removebackground.py (6)

- L16: `assert remover._background_remover._sigma_clip.sigma == sigma`
- L17: `assert remover._background_remover._box_size == box_size`
- L18: `assert remover._background_remover._filter_size == filter_size`
- L23: `assert remover._background_remover._sigma_clip.sigma == 3.0`
- L24: `assert remover._background_remover._box_size == (50, 50)`
- L25: `assert remover._background_remover._filter_size == (3, 3)`

### tests/images/processors/misc/test_save.py (5)

- L21: `mocker.patch.object(save._comm, "register_event")`
- L24: `save._comm.register_event.assert_called_once_with(NewImageEvent)`
- L34: `mocker.patch.object(save._comm, "send_event")`
- L35: `mocker.patch.object(save._vfs, "write_image")`
- L39: `save._vfs.write_image.assert_called_once_with("image.fits", image)`

### tests/images/processors/offsets/test_projected.py (3)

- L21: `assert offsets._ref_image is None`
- L99: `np.testing.assert_array_equal(offsets._ref_image[0], np.ones(10) * 10)`
- L100: `np.testing.assert_array_equal(offsets._ref_image[1], np.ones(10) * 10)`

### tests/images/processors/photometry/test_aperture_photometry.py (2)

- L19: `return self._catalog`
- L25: `self._catalog[f"call{diameter}"] = 1`

### tests/images/processors/photometry/test_photutil.py (1)

- L7: `assert isinstance(photometry._calculator, _PhotUtilAperturePhotometry)`

### tests/images/processors/photometry/test_pysep.py (1)

- L7: `assert isinstance(photometry._calculator, _SepAperturePhotometry)`

### tests/images/processors/test_removebackground.py (4)

- L14: `assert remover._sigma_clip.sigma == sigma`
- L15: `assert remover._box_size == box_size`
- L16: `assert remover._filter_size == filter_size`
- L38: `assert kwargs["bkg_estimator"] == remover._bkg_estimator`

### tests/integration/conftest.py (1)

- L143: `if comm._connected:`

### tests/integration/test_astroplanscheduler.py (3)

- L175: `assert not scheduler._abort.is_set()`
- L177: `assert scheduler._abort.is_set()`
- L185: `assert scheduler._abort.is_set()`

### tests/integration/test_csvpicker_scheduler.py (5)

- L84: `result = task._resolved_target`
- L101: `result = task._resolved_target`
- L118: `result = task._resolved_target`
- L143: `assert isinstance(observations[0].task._resolved_target, SiderealTarget)`
- L144: `assert observations[0].task._resolved_target.name in ["Betelgeuse", "Rigel", "Sirius"]`

### tests/integration/test_dynamic_target.py (4)

- L85: `assert task._resolved_target is not None`
- L86: `assert isinstance(task._resolved_target, SiderealTarget)`
- L198: `first_target = task._resolved_target`
- L202: `second_target = task._resolved_target`

### tests/integration/test_mastermind.py (3)

- L201: `original_send = mm._comm.send_event`
- L207: `mm._comm.send_event = tracking_send`
- L233: `assert mm._task is None`

### tests/integration/test_scheduler_mastermind.py (1)

- L215: `assert mm._task is None`

### tests/integration/test_xmpp_presence.py (3)

- L225: `camera_jid = next(jid for jid in observer_comm._online_clients if jid.startswith("camera@"))`
- L253: `camera_jid = next(jid for jid in observer_comm._online_clients if jid.startswith("camera@"))`
- L278: `camera_jid = next(jid for jid in observer_comm._online_clients if jid.startswith("camera@"))`

### tests/integration/test_xmpp_state.py (1)

- L170: `assert "camera" not in observer_comm._state_subscriptions`

### tests/modules/focus/test_focusmodel.py (7)

- L28: `weather.get_sensor_value.assert_awaited_once_with(fm._temp_station, fm._temp_sensor)`
- L44: `fm._comm.set_state = AsyncMock()`
- L49: `fm._comm.set_state.assert_awaited_once()`
- L50: `interface, state = fm._comm.set_state.await_args[0]`
- L60: `fm._comm.set_state = AsyncMock()`
- L71: `fm._comm.set_state.assert_awaited_once()`
- L72: `interface, state = fm._comm.set_state.await_args[0]`

### tests/modules/focus/test_focusseries.py (5)

- L19: `series._comm.set_state = AsyncMock()`
- L24: `assert series._comm.set_state.await_count == 2`
- L25: `interface, state = series._comm.set_state.await_args_list[0][0]`
- L30: `interface, state = series._comm.set_state.await_args_list[1][0]`
- L55: `assert series._running is False`

### tests/modules/image/test_imagewatcher.py (19)

- L58: `assert not watcher._queue.empty()`
- L59: `filename, _ = watcher._queue.get_nowait()`
- L68: `_, ready_at = watcher._queue.get_nowait()`
- L77: `assert not watcher._queue.empty()`
- L84: `assert watcher._queue.empty()`
- L99: `watcher._vfs.open_file = MagicMock(side_effect=open_side_effect)`
- L100: `watcher._vfs.remove = AsyncMock(return_value=True)`
- L102: `watcher._queue.put_nowait(("/watch/test.fits", 0.0))`
- L124: `watcher._vfs.open_file = MagicMock(side_effect=open_side_effect)`
- L125: `watcher._vfs.remove = AsyncMock(return_value=True)`
- L127: `watcher._queue.put_nowait(("/watch/test.fits", 0.0))`
- L136: `watcher._vfs.remove.assert_called_once_with("/watch/test.fits")`
- L148: `watcher._vfs.open_file = MagicMock(side_effect=open_side_effect)`
- L149: `watcher._vfs.remove = AsyncMock(return_value=True)`
- L151: `watcher._queue.put_nowait(("/watch/img.fits", 0.0))`
- L181: `watcher._vfs.open_file = MagicMock(side_effect=open_side_effect)`
- L182: `watcher._vfs.remove = AsyncMock(return_value=True)`
- L184: `watcher._queue.put_nowait(("/watch/test.fits", 0.0))`
- L195: `watcher._vfs.remove.assert_not_called()`

### tests/modules/image/test_imagewriter.py (18)

- L37: `assert writer._queue.get_nowait() == "/tmp/img.fits"`
- L47: `assert writer._queue.empty()`
- L55: `assert writer._queue.empty()`
- L64: `assert not writer._queue.empty()`
- L82: `writer._vfs.read_image = AsyncMock(return_value=img)`
- L83: `writer._vfs.write_image = AsyncMock()`
- L85: `writer._queue.put_nowait("/tmp/test.fits")`
- L95: `writer._vfs.read_image.assert_called_once_with("/tmp/test.fits")`
- L96: `writer._vfs.write_image.assert_called_once()`
- L97: `assert writer._vfs.write_image.call_args[0][0] == "/archive/test.fits"`
- L105: `writer._vfs.read_image = AsyncMock(side_effect=FileNotFoundError)`
- L106: `writer._queue.put_nowait("/tmp/missing.fits")`
- L118: `writer._vfs.write_image = AsyncMock()`
- L119: `writer._vfs.write_image.assert_not_called()`
- L127: `writer._vfs.read_image = AsyncMock(return_value=img)`
- L128: `writer._vfs.write_image = AsyncMock()`
- L129: `writer._queue.put_nowait("/tmp/test.fits")`
- L139: `writer._vfs.write_image.assert_not_called()`

### tests/modules/roof/test_dummyroof.py (14)

- L15: `roof._comm.register_event = AsyncMock()`
- L21: `assert roof._comm.register_event.call_args_list[0][0][0] == RoofOpenedEvent`
- L22: `assert roof._comm.register_event.call_args_list[1][0][0] == RoofClosingEvent`
- L31: `roof._comm.send_event = AsyncMock()`
- L46: `roof._comm.send_event = AsyncMock()`
- L59: `await roof._move_roof(roof._ROOF_OPEN_PERCENTAGE)`
- L61: `assert roof._open_percentage == 100`
- L70: `await roof._move_roof(roof._ROOF_CLOSED_PERCENTAGE)`
- L72: `assert roof._open_percentage == 0`
- L81: `roof._abort_motion.set()`
- L82: `await roof._move_roof(roof._ROOF_OPEN_PERCENTAGE)`
- L84: `assert roof._open_percentage == 0`
- L93: `await roof._move_roof(roof._ROOF_OPEN_PERCENTAGE)`
- L95: `assert roof._open_percentage == 100`

### tests/modules/test/standalone.py (23)

- L12: `assert module._message == "Hello world"`
- L13: `assert module._interval == 10`
- L31: `assert any(task._func == module._message_func for task, _ in module._background_tasks)`
- L44: `assert module._acl_allow is None`
- L45: `assert module._acl_deny is None`
- L46: `assert module._acl_mode == "enforce"`
- L51: `assert module._acl_allow == {"scheduler": ["expose", "abort"]}`
- L52: `assert module._acl_deny is None`
- L53: `assert module._acl_mode == "enforce"`
- L58: `assert module._acl_allow is None`
- L59: `assert module._acl_deny == ["legacy_gui"]`
- L64: `assert module._acl_mode == "log"`
- L79: `interface_methods = set(module._interface_methods["IConfig"])`
- L80: `assert interface_methods == set(module._acl_allow["scheduler"])`
- L81: `assert "get_config_value" in module._acl_allow["scheduler"]`
- L82: `assert "set_config_value" in module._acl_allow["scheduler"]`
- L84: `assert "reset_error" not in module._acl_allow["scheduler"]`
- L89: `assert "get_config_value" in module._acl_allow["scheduler"]`
- L90: `assert "reset_error" in module._acl_allow["scheduler"]`
- L95: `assert module._acl_allow["scheduler"].count("get_config_value") == 1`
- L100: `assert module._acl_allow["mastermind"] == "*"`
- L105: `assert module._acl_allow["scheduler"] == ["some_unknown_method"]`
- L124: `assert set(methods) == set(module._interface_methods["IConfig"])`

### tests/modules/test_module_interfaces.py (1)

- L60: `assert "custom_method" in m._interface_methods["IModuleTestWithMethod"]`

### tests/modules/weather/test_mockweather.py (32)

- L15: `weather._comm.register_event = AsyncMock()`
- L16: `weather._comm.set_state = AsyncMock()`
- L22: `weather._comm.register_event.assert_called()`
- L23: `assert weather._comm.register_event.await_args_list[0][0][0] == BadWeatherEvent`
- L24: `assert weather._comm.register_event.await_args_list[1][0][0] == GoodWeatherEvent`
- L26: `assert weather._comm.set_state.await_count == 2`
- L27: `interface, state = weather._comm.set_state.await_args_list[0][0]`
- L31: `interface, state = weather._comm.set_state.await_args_list[1][0]`
- L39: `weather._comm.send_event = AsyncMock()`
- L40: `weather._comm.set_state = AsyncMock()`
- L47: `assert weather._active is True`
- L48: `assert isinstance(weather._comm.send_event.await_args[0][0], BadWeatherEvent)`
- L54: `weather._comm.set_state = AsyncMock()`
- L58: `assert weather._active is False`
- L73: `weather._comm.send_event = AsyncMock()`
- L74: `weather._comm.set_state = AsyncMock()`
- L78: `weather._comm.send_event.assert_not_called()`
- L79: `weather._comm.set_state.assert_not_called()`
- L85: `weather._comm.send_event = AsyncMock()`
- L86: `weather._comm.set_state = AsyncMock()`
- L90: `assert weather._good is False`
- L91: `assert isinstance(weather._comm.send_event.await_args[0][0], BadWeatherEvent)`
- L93: `_, state = weather._comm.set_state.await_args_list[0][0]`
- L100: `weather._comm.send_event = AsyncMock()`
- L101: `weather._comm.set_state = AsyncMock()`
- L105: `assert weather._good is True`
- L106: `assert isinstance(weather._comm.send_event.await_args[0][0], GoodWeatherEvent)`
- L113: `weather._comm.send_event = AsyncMock()`
- L114: `weather._comm.set_state = AsyncMock()`
- L118: `weather._comm.send_event.assert_not_called()`
- L119: `_, state = weather._comm.set_state.await_args_list[0][0]`
- L126: `assert weather._sensors[WeatherSensors.TEMPERATURE] == 42.0`

### tests/modules/weather/test_weather.py (33)

- L19: `weather._comm.register_event = AsyncMock()`
- L25: `weather._comm.register_event.assert_called()`
- L27: `assert weather._comm.register_event.await_args_list[0][0][0] == BadWeatherEvent`
- L28: `assert weather._comm.register_event.await_args_list[1][0][0] == GoodWeatherEvent`
- L34: `weather._comm.send_event = AsyncMock()`
- L41: `assert weather._active is True`
- L42: `assert isinstance(weather._comm.send_event.await_args[0][0], BadWeatherEvent)`
- L49: `assert weather._active is False`
- L65: `weather._api.get_sensor_value = AsyncMock(side_effect=ValueError)`
- L70: `weather._api.get_sensor_value.assert_called_once_with("test", WeatherSensors.RAIN)`
- L77: `weather._api.get_sensor_value = AsyncMock(return_value={})`
- L86: `weather._api.get_sensor_value = AsyncMock(return_value={"time": "2026-07-02T08:36:42", "value": 2})`
- L108: `weather._weather.status["sensors"] = {"rain": {"value": 1}}`
- L142: `weather._api.get_current_status = AsyncMock(side_effect=ValueError("Could not connect to weather station."))`
- L147: `assert weather._weather.is_good is False`
- L150: `weather._api.get_current_status.assert_called_once_with()`
- L157: `weather._api.get_current_status = AsyncMock(return_value={})`
- L162: `assert weather._weather.is_good is False`
- L169: `weather._comm.send_event = AsyncMock()`
- L172: `weather._api.get_current_status = AsyncMock(return_value={"good": True})`
- L178: `assert isinstance(weather._comm.send_event.await_args[0][0], GoodWeatherEvent)`
- L184: `weather._weather.is_good = True`
- L185: `weather._comm.send_event = AsyncMock()`
- L188: `weather._api.get_current_status = AsyncMock(return_value={"good": False})`
- L194: `assert isinstance(weather._comm.send_event.await_args[0][0], BadWeatherEvent)`
- L208: `weather._comm.set_state = AsyncMock()`
- L211: `weather._api.get_current_status = AsyncMock(`
- L217: `weather._comm.set_state.assert_awaited_once()`
- L218: `interface, state = weather._comm.set_state.await_args[0]`
- L232: `weather._comm.set_state = AsyncMock()`
- L235: `weather._api.get_current_status = AsyncMock(return_value={"good": False})`
- L239: `_, state = weather._comm.set_state.await_args[0]`
- L245: `weather._weather.status = {`

### tests/modules/weather/test_weather_api.py (1)

- L15: `return self._json`

### tests/robotic/scheduler/merits/test_transit.py (2)

- L87: `phase_mid = 1.0 - merit._duration / 2.0`
- L96: `in_window = 1.0 - merit._duration / 2.0 - merit._ingress <= phi <= 1.0 - merit._duration / 2.0 - merit._over`

### tests/robotic/scheduler/targets/test_dynamictarget.py (1)

- L71: `assert target._target is not None`

### tests/robotic/scheduler/test_dynamictarget_scheduler.py (6)

- L73: `assert task._resolved_target is not None`
- L74: `assert isinstance(task._resolved_target, SiderealTarget)`
- L124: `first_target = task._resolved_target`
- L127: `second_target = task._resolved_target`
- L153: `assert task._resolved_target is not None`
- L154: `assert task._resolved_target.name == "Betelgeuse"`

### tests/robotic/scripts/test_autofocus.py (9)

- L74: `script._comm.has_proxy = AsyncMock(return_value=True)`
- L75: `script._comm.safe_proxy = MagicMock(return_value=make_proxy_cm(telescope))`
- L82: `script._comm.has_proxy = AsyncMock(return_value=False)`
- L90: `script._comm.has_proxy = AsyncMock(return_value=True)`
- L91: `script._comm.safe_proxy = MagicMock(return_value=make_proxy_cm(telescope))`
- L119: `script._comm.proxy = MagicMock(side_effect=[make_proxy_cm(telescope), make_proxy_cm(autofocus)])`
- L121: `script._comm.safe_proxy = MagicMock(return_value=make_proxy_cm(telescope))`
- L140: `script._comm.proxy = MagicMock(side_effect=[make_proxy_cm(telescope), make_proxy_cm(autofocus)])`
- L141: `script._comm.safe_proxy = MagicMock(return_value=make_proxy_cm(telescope))`

### tests/robotic/scripts/test_callmodule.py (7)

- L104: `script._comm.has_proxy = AsyncMock(return_value=True)`
- L110: `script._comm.has_proxy = AsyncMock(return_value=False)`
- L116: `script._comm.has_proxy = AsyncMock(return_value=True)`
- L118: `assert script._comm.has_proxy.call_args[0][1] is IExposureTime`
- L128: `script._comm.proxy = MagicMock(return_value=make_proxy_cm(proxy))`
- L138: `script._comm.proxy = MagicMock(return_value=make_proxy_cm(proxy))`
- L141: `assert script._comm.proxy.call_args[0][1] is IExposureTime`

### tests/robotic/scripts/test_darkbias.py (4)

- L90: `script._comm.safe_proxy = MagicMock(side_effect=safe_proxy_se)`
- L91: `script._comm.proxy = MagicMock(return_value=make_proxy_cm(camera))`
- L100: `script._comm.has_proxy = AsyncMock(return_value=True)`
- L107: `script._comm.has_proxy = AsyncMock(return_value=False)`

### tests/robotic/storage/lco/test_lco_http.py (9)

- L48: `mocker.patch.object(archive._portal, "schedulable_requests", AsyncMock(return_value=[sr]))`
- L49: `mocker.patch.object(archive._portal, "proposals", AsyncMock(return_value=[{"id": "test", "tac_priority": 1.0}]))`
- L63: `mocker.patch.object(archive._portal, "schedulable_requests", AsyncMock(return_value=[sr]))`
- L64: `mocker.patch.object(archive._portal, "proposals", AsyncMock(return_value=[{"id": "test", "tac_priority": 1.0}]))`
- L133: `mocker.patch.object(archive._portal, "observations", AsyncMock(return_value=obs_list))`
- L158: `mocker.patch.object(archive._portal, "observations", AsyncMock(return_value=obs_list))`
- L171: `archive._portal, "update_configuration_status", AsyncMock(return_value=CONFIG_STATUS_RESPONSE)`
- L181: `archive._portal.update_configuration_status = AsyncMock()`
- L184: `archive._portal.update_configuration_status.assert_not_called()`

### tests/robotic/storage/lco/test_schedulereader.py (9)

- L37: `reader._update_error_log.resolve = MagicMock()`
- L38: `reader._update_error_log.error = MagicMock()`
- L146: `mocker.patch.object(reader._portal, "download_schedule", AsyncMock(return_value=[obs]))`
- L155: `mocker.patch.object(reader._portal, "download_schedule", AsyncMock(return_value=[]))`
- L174: `assert len(reader._scheduled_tasks) == 1`
- L180: `assert reader._last_schedule_time is None`
- L185: `assert reader._last_schedule_time is not None`
- L194: `await reader._update_lock.acquire()  # hold the lock`
- L206: `reader._update_lock.release()`

### tests/robotic/storage/lco/test_schedulewriter.py (1)

- L170: `assert abs((args[1] - T0).to(u.hour).value - writer._period) < 0.001`

### tests/robotic/storage/memory/test_memory_archives.py (5)

- L335: `assert "1" in task_archive._tasks`
- L336: `assert task_archive._last_changed is not None`
- L344: `assert task_archive._tasks["1"].name == "replaced"`
- L351: `assert "1" not in task_archive._tasks`
- L352: `assert task_archive._last_changed is not None`

### tests/robotic/test_task.py (1)

- L222: `assert task._resolved_target is None`

### tests/robotic/utils/exptime/stellarexptime.py (3)

- L81: `provider._vfs.read_image = AsyncMock(`
- L97: `provider._comm.proxy = AsyncMock(side_effect=proxy_side_effect)`
- L215: `provider._comm.proxy = AsyncMock(side_effect=proxy_side_effect)`

### tests/test_background_task.py (5)

- L32: `assert task._task is not None`
- L48: `assert task._task.cancelled() or task._task.done()`
- L105: `assert task._task.done()`
- L135: `assert task._task.done()`
- L197: `assert task._task.done()`

### tests/test_object.py (3)

- L13: `assert task._func == test_function`
- L14: `assert task._restart is False`
- L16: `assert obj._background_tasks[0] == (task, False)`

### tests/utils/grids/test_filters.py (4)

- L81: `assert data_points[0] == grid4._data[7]`
- L82: `assert data_points[1] == grid4._data[15]`
- L83: `assert data_points[2] == grid4._data[10]`
- L84: `assert data_points[3] == grid4._data[18]`

### tests/utils/test_average.py (4)

- L49: `t1 = avg._start_time`
- L51: `t2 = avg._start_time`
- L91: `assert len(avg._values) == 1`
- L92: `assert avg._values[0][1] == 1.0`

### tests/utils/test_exceptions.py (4)

- L18: `assert len(exc._local_exceptions) == 0`
- L26: `assert len(exc._handlers) == 1`
- L30: `assert len(exc._local_exceptions) == 0`
- L31: `assert len(exc._handlers) == 0`
