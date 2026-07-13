# Mock usage in tests

370 `Mock`/`MagicMock`/`AsyncMock` instantiations and 130 `patch(...)`/`mocker.patch(...)` calls across 57 files. Categorized into five buckets by what the mock is actually standing in for and whether the test verifies real behavior or just mock interactions.

## Resolved this session

**Bucket 3 swaps (5 of 18):** `MagicMock(spec=Comm)` -> real `DummyComm()` in `tests/integration/test_transit_mastermind.py` (2 spots), `tests/modules/image/test_imagewatcher.py`, `tests/modules/image/test_imagewriter.py`, `tests/robotic/scripts/test_transitimaging.py` (2 spots). The other 13 stayed as mocks per the table below (genuinely need call-tracking or a specific `.name`).

**Bucket 4 consolidations (all 4):**
- `make_proxy_cm` and `isinstance_class` (renamed from `_isinstance_class`) extracted to new `tests/helpers.py`, imported by the 5 + 2 files that used to define them locally.
- `make_camera_comm` moved into `tests/integration/conftest.py` as a `@pytest.fixture` (was a plain function requiring an explicit `xmpp_config` argument at each call site; as a fixture it's just requested by name, and the 16 call sites across 3 files dropped their `xmpp_config` parameter too since nothing else in those tests needed it directly).
- `make_module` consolidated to the superset version (from `test_xmpp_presence.py`) in `tests/integration/conftest.py`; `test_xmpp_state.py` now imports it instead of keeping its own subset copy.

**`test_stellarexptime.py` bug fix:** the file was named `stellarexptime.py` (missing the `test_` prefix), so pytest's default collection glob silently skipped it entirely -- its 4 failing tests never ran in CI. Renamed it into collection and fixed what was actually broken: `provider._comm.proxy` was an `AsyncMock`, but `Comm.proxy()` is a sync method returning an async context manager, so `async with self.comm.proxy(...) as camera:` was awaiting a coroutine instead of entering a context manager. Fixed by wiring `.proxy` as a `MagicMock` returning `make_proxy_cm(...)` (the shared helper from `tests/helpers.py`). That unmasked two more latent bugs: the proxy-routing `side_effect` matched on `ICamera`, but production code requests `IData` for `grab_data` -- the camera mock was never actually reached, silently falling through to the window mock instead; and `mock_exptime`/`mock_window` were configured with methods (`get_exposure_time`, `get_window`) that production code never calls -- it calls `camera.get_state(IExposureTime/IWindow)`, which needs a sync `MagicMock` returning an `ExposureTimeState`/`WindowState` (the mocks were also plain `AsyncMock()`s, so any unconfigured method returned a coroutine instead of a real value). Also fixed `test_call_converges_in_one_iteration`, which never called `await provider()` at all before asserting on call counts. All 9 tests pass now.

Verified: `pytest tests/` (867 passed, 2 skipped -- 9 more than before, from `test_stellarexptime.py` now being collected) and, against a local ejabberd, `pytest tests/integration -m "integration or xmpp"` (72 passed).

**Bucket 5 reviewed (all 49 functions):** went through every flagged function individually. Breakdown:

- **8 false positives** -- the "0 real assertions" heuristic had three blind spots it didn't account for: `pytest.raises(..., match=...)` (verifies via regex, no `assert` statement needed), assert-like function *calls* rather than `assert` statements (`np.testing.assert_array_equal(...)`), and `await asyncio.wait_for(event.wait(), timeout=...)` (fails via timeout if the awaited condition never happens). Affected: `test_version_mismatch.py:168`, `test_weather.py:62`, `test_removebackground.py:29`, `test_image.py:81`, `test_image.py:96`, `test_background_task.py:201`.
- **~35 genuinely fine** -- thin delegation/orchestration code (event dispatch, proxy calls, guard clauses) where the mock interaction *is* the entire observable behavior; there's no other state to check because the collaborator is fully mocked out. No changes.
- **4 real bugs found and fixed:**
  - `test_save.py::test_call` -- constructed `Save(comm=Comm())` without `broadcast=True`, so `send_event` was never actually called; the original author's verification was commented out with `# todo: fix`. Fixed the constructor call and enabled the assertions.
  - `test_image.py::test_write_catalog_value` / `test_write_catalog_non_value` -- patched `astropy.io.fits.convenience.table_to_hdu`, but `pyobs/images/image.py` imports `table_to_hdu` by name, so that patch never touched the reference actually called; the assertion was marked `# FIXME: does not work for some reason` (in the "not called" test, the wrong-path mock trivially reported "not called" regardless of real behavior). Fixed to patch `pyobs.images.image.table_to_hdu` instead, and simplified away a second `HDUList.writeto` patch that was only working by accident (real `table_to_hdu` output routing through `_ValidHDU.writeto`'s internal `HDUList` wrapping).
  - `test_imagewriter.py::test_worker_skips_on_file_not_found` -- reassigned `write_image` to a brand-new `AsyncMock` *after* the worker had already run, then asserted the fresh mock was never called -- trivially true regardless of what actually happened. Fixed to wire the mock before running the worker and moved `caplog.at_level(...)` to actually wrap the run.
- **4 tests strengthened** with a real assertion alongside the existing mock check, where production code does something checkable that wasn't being verified:
  - `test_presence.py` (3 functions) -- `set_state()` also mutates `module._state`/`module._error_string`, previously unverified.
  - `test_dummyroof.py::test_init` / `test_park` -- `_move_roof()` runs unmocked and really moves `_open_percentage`; `test_park` also never checked what `_comm.send_event` was called with.
  - `test_mockweather.py::test_set_good_no_change` -- added a check that `_good` is actually unchanged.
  - `test_schedulewriter.py::test_add_schedule_calls_portal` -- `assert_called_once()` alone didn't check that `submit_observations` received the converted observations.

## Bucket 1 -- External-boundary mocks: keep, no action needed

Mocks/patches substituting something genuinely external, non-deterministic, or slow, where no pyobs class could stand in instead:

- `pyobs.utils.time.Time.now` / `Time.now` (~26 call sites) -- pins time for deterministic tests.
- `asyncio.sleep` (10) -- skips real waits.
- Network I/O: `aiohttp.ClientSession.get/post`, `http_request_with_retries` (~13) -- avoids real HTTP calls to LCO/weather APIs.
- Astropy/FITS/ccdproc internals: `SkyCoord.transform_to`, `astropy.io.fits.*`, `ccdproc.ccd_process`, `Pipeline.find_master/trim_ccddata` (~10) -- avoids heavy/real astronomy computation in unit tests.
- `pyobs.background_task.BackgroundTask.start`, `pyobs.object.Object.open` / `Module.open` (~5) -- skip real lifecycle/threading in tests that target one method.

No changes suggested here.

## Bucket 2 -- Internal collaborator-method patches: mostly fine, same pattern as check_tests.md

`mocker.patch.object(obj, "_method")` / `ClassName._method = Mock(...)`-style patches on a *private method of the class under test itself*, to isolate the method actually being tested (e.g. `offsets._process`, `ProjectedOffsets._subtract_sky`, `reader._download_schedule`, `calibration._calib_cache.get_from_cache`, `api._send`). This is a standard unit-isolation technique and was explicitly out of scope for check_tests.md ("calling private methods"). Flagging only because it's the same class of internals-reaching -- worth a look if a single class accumulates many of these (a sign its public seams are too coarse), but not a per-line action item.

## Bucket 3 -- `Comm` / `VirtualFileSystem` stand-ins: case-by-case verdict

18 instances of `MagicMock(spec=Comm)` / `MagicMock(spec=VirtualFileSystem)` (mostly introduced in the constructor-routing pass). Verdict is per-instance: **keep** if the test configures or asserts on specific comm/vfs methods (that needs a mock); **replaceable** if the object is never touched beyond satisfying `isinstance()` / presence (a real `DummyComm()`/`VirtualFileSystem()` would do, with no `spec=` bookkeeping needed).

| File | Line(s) | Function | Verdict | Why |
|---|---|---|---|---|
| `tests/comm/test_presence.py` | 22, 47, 62 | `test_set_state_*` | **keep** | configures and asserts `comm.set_presence.assert_called_once_with(...)` -- the mock IS the test. |
| `tests/comm/test_presence.py` | 85, 114, 144 | `test_open_publishes_*` | **keep** | configures and asserts `comm.set_capabilities.call_args_list` -- same reason. |
| `tests/comm/test_presence.py` | 196, 225, 252 | `test_on_module_opened_*` | **keep** | needs `comm.name` set to a specific string to differentiate sender in `_on_module_opened`; `DummyComm.name` is a hardcoded read-only property ("module"), and `LocalComm(name)` would drag in the global `LocalNetwork` singleton (reset-fixture ceremony) for no benefit here. |
| `tests/integration/test_transit_mastermind.py` | 164, 208 | `test_transit_script_*` | **replaced** ✅ | now `comm=DummyComm()`. |
| `tests/modules/image/test_imagewatcher.py` | 24 | `make_watcher` | **replaced** ✅ | now `comm=DummyComm()`. |
| `tests/modules/image/test_imagewatcher.py` | 25 | `make_watcher` | **keep** | `watcher._vfs.open_file` / `.remove` are configured per-test with specific side effects. |
| `tests/modules/image/test_imagewriter.py` | 19 | `make_writer` | **replaced** ✅ | now `comm=DummyComm()`. |
| `tests/modules/image/test_imagewriter.py` | 20 | `make_writer` | **keep** | `writer._vfs.read_image` is configured per-test with specific return values/side effects. |
| `tests/robotic/scripts/test_transitimaging.py` | 29, 152 | `make_script / test_run_configurations_uses_modulo_repeats` | **replaced** ✅ | now `comm=DummyComm()`. |
| `tests/robotic/utils/exptime/test_stellarexptime.py` | 48 | `make_provider` | **keep** | `provider._comm.proxy` is reconfigured per-test via `attach_proxies()` with a side_effect resolving fake device proxies. |

5 of 18 were cheap swaps to a real `DummyComm()` (done -- see above). The rest need mock call-tracking and stayed as-is.

## Bucket 4 -- Duplicated mock/fake builder helpers: consolidation candidates

Several test files independently defined their own near-identical helper for building the same kind of fake, instead of sharing one. All four found were consolidated:

- **`make_proxy_cm(value)`** ✅ -- was byte-for-byte identical in 5 files (`test_autofocus.py`, `test_callmodule.py`, `test_control.py`, `test_darkbias.py`, `test_shellcommand.py`). Now lives in `tests/helpers.py`, imported by all 5.
- **`_isinstance_class(name, interfaces)`** ✅ (+ its module-level `_mock_class_counter`) -- was identical in `test_autofocus.py` and `test_darkbias.py`. Now `isinstance_class` in `tests/helpers.py` (dropped the leading underscore since it's a public shared helper now).
- **`make_camera_comm(xmpp_config)`** ✅ -- was identical in 3 files (`test_xmpp_acl.py`, `test_xmpp_dummy_camera.py`, `test_xmpp_rpc.py`). Now a `@pytest.fixture` in `tests/integration/conftest.py`; the 16 call sites across those 3 files request it by name instead of calling `make_camera_comm(xmpp_config)`, and dropped the now-unused `xmpp_config` parameter.
- **`make_module(interfaces, ...)`** ✅ -- was near-duplicated in `test_xmpp_state.py` and `test_xmpp_presence.py`. Now the superset version (with `label`/`get_label`/`get_version`) lives in `tests/integration/conftest.py`; both files import it.

**Not** flagged as consolidation candidates: `make_camera`/`make_telescope`/`make_camera_mocks` in `test_darkbias.py`/`test_autofocus.py`/`test_stellarexptime.py`. These look superficially similar (all build a fake device `MagicMock`) but each mocks a different, purpose-specific interface surface for its own script under test -- merging them would mean one over-parameterized "FakeDevice" builder covering every interface combination any script happens to need, which is more abstraction than the modest duplication saves.

## Bucket 5 -- Testing mock behavior only (reviewed -- see "Resolved this session" above)

Test functions where **every** assertion is about a mock's call history (`.assert_called*`, `.call_args`, etc.) and none assert on real return values, object state, or side effects, per the original heuristic scan. All 49 were reviewed individually; outcomes (false positive / fine / bug fixed / strengthened) are summarized above. Kept here for reference:

- `tests/comm/dummy/test_dummycomm.py:56` `test_send_event_dispatches_to_module` -- fine
- `tests/comm/local/test_localcomm.py:122` `test_send_event_dispatches_to_all_clients` -- fine
- `tests/comm/local/test_localcomm.py:137` `test_send_event_dispatches_to_sender_too` -- fine
- `tests/comm/test_presence.py:20,45,60` `test_set_state_*` -- strengthened
- `tests/comm/test_version_mismatch.py:168` `test_resolve_proxy_appends_diagnostic_hint` -- false positive
- `tests/images/processors/misc/test_removebackground.py:29` `test_call_const_background` -- false positive
- `tests/images/processors/misc/test_save.py:10,18` `test_init`, `test_open` -- fine
- `tests/images/processors/misc/test_save.py:28` `test_call` -- bug fixed
- `tests/images/test_image.py:81,96` `test_from_bytes`, `test_from_file` -- false positive
- `tests/images/test_image.py:292,304` `test_write_catalog_value`, `test_write_catalog_non_value` -- bug fixed
- `tests/modules/image/test_imagewatcher.py:116` `test_worker_deletes_file_after_success` -- fine
- `tests/modules/image/test_imagewriter.py:78` `test_worker_downloads_and_stores_image` -- fine
- `tests/modules/image/test_imagewriter.py:101` `test_worker_skips_on_file_not_found` -- bug fixed
- `tests/modules/image/test_imagewriter.py:123` `test_worker_skips_on_bad_filename_format` -- fine
- `tests/modules/roof/test_baseroof.py:23` `test_open` -- fine
- `tests/modules/roof/test_dummyroof.py:12` `test_open` -- fine
- `tests/modules/roof/test_dummyroof.py:26,39` `test_init`, `test_park` -- strengthened
- `tests/modules/roof/test_dummyroof.py:99` `test_stop_motion` -- fine
- `tests/modules/weather/test_mockweather.py:71` `test_set_good_no_change` -- strengthened
- `tests/modules/weather/test_weather.py:17,116,128` `test_open`, `test_loop_valid`, `test_loop_invalid` -- fine
- `tests/modules/weather/test_weather.py:62` `test_get_sensor_value_invalid_request` -- false positive
- `tests/modules/weather/test_weather_api.py:44,52` `test_get_current_status`, `test_get_sensor_value` -- fine
- `tests/robotic/scripts/test_autofocus.py:113,133` `test_run_moves_telescope_and_focuses`, `test_run_stops_telescope_in_finally` -- fine
- `tests/robotic/scripts/test_callmodule.py:115,125,135` -- fine
- `tests/robotic/scripts/test_control.py:356` `test_selector_run_sets_mode` -- fine
- `tests/robotic/storage/lco/test_lco_http.py:168,179,188,204` -- fine
- `tests/robotic/storage/lco/test_schedulereader.py:126,189` -- fine
- `tests/robotic/storage/lco/test_schedulewriter.py:149` `test_add_schedule_calls_portal` -- strengthened
- `tests/robotic/utils/exptime/test_stellarexptime.py:192` `test_call_restores_settings_on_exception` -- fine (fixed in the earlier collection-bug pass)
- `tests/test_background_task.py:201` `test_slow_failures_reset_counter` -- false positive
- `tests/test_object.py:19,31,43` -- fine

## Full inventory

Every `Mock`/`MagicMock`/`AsyncMock` instantiation and `patch(...)` call, grouped by file, for reference.

### tests/comm/dummy/test_dummycomm.py (1)

- L57 [test_send_event_dispatches_to_module]: `handler = AsyncMock(return_value=True)`

### tests/comm/local/test_localcomm.py (7)

- L59 [test_get_interfaces_with_module]: `module = MagicMock()`
- L73 [test_supports_interface_true]: `module = MagicMock()`
- L83 [test_supports_interface_false]: `module = MagicMock()`
- L98 [test_execute_calls_remote_module]: `module = MagicMock()`
- L99 [test_execute_calls_remote_module]: `module.execute = AsyncMock(return_value=30.0)`
- L126 [test_send_event_dispatches_to_all_clients]: `handler = AsyncMock(return_value=True)`
- L141 [test_send_event_dispatches_to_sender_too]: `handler = AsyncMock(return_value=True)`

### tests/comm/test_commlogging.py (2)

- L14 [comm]: `c = MagicMock()`
- L15 [comm]: `c.log_message = MagicMock()`

### tests/comm/test_presence.py (40)

- L22 [test_set_state_calls_set_presence] spec=Comm: `comm = MagicMock(spec=Comm)`
- L24 [test_set_state_calls_set_presence]: `comm.set_presence = AsyncMock()`
- L47 [test_set_state_passes_current_error_string] spec=Comm: `comm = MagicMock(spec=Comm)`
- L49 [test_set_state_passes_current_error_string]: `comm.set_presence = AsyncMock()`
- L62 [test_set_state_ready_clears_error] spec=Comm: `comm = MagicMock(spec=Comm)`
- L64 [test_set_state_ready_clears_error]: `comm.set_presence = AsyncMock()`
- L85 [test_open_publishes_imodule_capabilities] spec=Comm: `comm = MagicMock(spec=Comm)`
- L87 [test_open_publishes_imodule_capabilities]: `comm.set_capabilities = AsyncMock()`
- L95 [test_open_publishes_imodule_capabilities] patch(`'pyobs.object.Object.open'`): `with patch("pyobs.object.Object.open", new_callable=AsyncMock):`
- L96 [test_open_publishes_imodule_capabilities]: `module.get_version = AsyncMock(return_value="2.0.0")`
- L97 [test_open_publishes_imodule_capabilities]: `module.get_label = AsyncMock(return_value="Test Camera")`
- L114 [test_open_publishes_empty_label_when_none] spec=Comm: `comm = MagicMock(spec=Comm)`
- L116 [test_open_publishes_empty_label_when_none]: `comm.set_capabilities = AsyncMock()`
- L124 [test_open_publishes_empty_label_when_none] patch(`'pyobs.object.Object.open'`): `with patch("pyobs.object.Object.open", new_callable=AsyncMock):`
- L125 [test_open_publishes_empty_label_when_none]: `module.get_version = AsyncMock(return_value="2.0.0")`
- L126 [test_open_publishes_empty_label_when_none]: `module.get_label = AsyncMock(return_value="")`
- L144 [test_open_publishes_location_when_configured] spec=Comm: `comm = MagicMock(spec=Comm)`
- L146 [test_open_publishes_location_when_configured]: `comm.set_capabilities = AsyncMock()`
- L154 [test_open_publishes_location_when_configured] patch(`'pyobs.object.Object.open'`): `with patch("pyobs.object.Object.open", new_callable=AsyncMock):`
- L155 [test_open_publishes_location_when_configured]: `module.get_version = AsyncMock(return_value="2.0.0")`
- L156 [test_open_publishes_location_when_configured]: `module.get_label = AsyncMock(return_value="Test Camera")`
- L196 [test_on_module_opened_warns_on_location_mismatch] spec=Comm: `comm = MagicMock(spec=Comm)`
- L205 [test_on_module_opened_warns_on_location_mismatch]: `fake_proxy = MagicMock()`
- L206 [test_on_module_opened_warns_on_location_mismatch]: `fake_proxy.get_capabilities = MagicMock(return_value=remote_caps)`
- L207 [test_on_module_opened_warns_on_location_mismatch]: `module.proxy = MagicMock(return_value=_FakeProxyContext(fake_proxy))`
- L225 [test_on_module_opened_no_warning_when_locations_match] spec=Comm: `comm = MagicMock(spec=Comm)`
- L234 [test_on_module_opened_no_warning_when_locations_match]: `fake_proxy = MagicMock()`
- L235 [test_on_module_opened_no_warning_when_locations_match]: `fake_proxy.get_capabilities = MagicMock(return_value=remote_caps)`
- L236 [test_on_module_opened_no_warning_when_locations_match]: `module.proxy = MagicMock(return_value=_FakeProxyContext(fake_proxy))`
- L252 [test_on_module_opened_no_warning_when_no_local_location] spec=Comm: `comm = MagicMock(spec=Comm)`
- L261 [test_on_module_opened_no_warning_when_no_local_location]: `fake_proxy = MagicMock()`
- L262 [test_on_module_opened_no_warning_when_no_local_location]: `fake_proxy.get_capabilities = MagicMock(return_value=remote_caps)`
- L263 [test_on_module_opened_no_warning_when_no_local_location]: `module.proxy = MagicMock(return_value=_FakeProxyContext(fake_proxy))`
- L279 [test_comm_get_client_state_delegates]: `comm._get_client_state = MagicMock(return_value=(ModuleState.READY, ""))`
- L357 [test_got_online_resolves_future_when_no_interfaces_found]: `comm._get_interfaces = AsyncMock(return_value=[])`
- L359 [test_got_online_resolves_future_when_no_interfaces_found]: `msg = {"from": MagicMock(full="camera@localhost/pyobs", username="camera"), "show": "", "status": ""}`
- L390 [test_got_online_completes_despite_broken_presence_callback]: `comm._presence_callbacks = {"camera": [MagicMock(side_effect=RuntimeError("Signal source has been deleted"))]}`
- L392 [test_got_online_completes_despite_broken_presence_callback]: `comm._get_interfaces = AsyncMock(return_value=["IModule"])`
- L394 [test_got_online_completes_despite_broken_presence_callback]: `msg = {"from": MagicMock(full="camera@localhost/pyobs", username="camera"), "show": "", "status": ""}`
- L426 [test_comm_get_capabilities_delegates]: `comm._get_capabilities = AsyncMock(return_value=WindowCapabilities())`

### tests/comm/test_proxy.py (2)

- L14 [make_proxy]: `comm = MagicMock()`
- L17 [make_proxy]: `comm.execute = AsyncMock(return_value=return_value)`

### tests/comm/test_version_mismatch.py (9)

- L30 [make_xmpp_comm]: `comm._xmpp = MagicMock()`
- L47 [test_get_interfaces_keeps_matching_version]: `comm._safe_send = AsyncMock(return_value={"features": features})`
- L59 [test_get_interfaces_drops_mismatched_version]: `comm._safe_send = AsyncMock(return_value={"features": features})`
- L71 [test_get_interfaces_drops_unknown_name]: `comm._safe_send = AsyncMock(return_value={"features": features})`
- L90 [test_get_interfaces_resolves_external_interface]: `comm._safe_send = AsyncMock(return_value={"features": features})`
- L103 [test_get_interfaces_caches_raw_features_regardless_of_match]: `comm._safe_send = AsyncMock(return_value={"features": features})`
- L170 [test_resolve_proxy_appends_diagnostic_hint]: `comm._get_client = AsyncMock(return_value=object())`
- L171 [test_resolve_proxy_appends_diagnostic_hint]: `comm._diagnose_missing_interface = MagicMock(return_value="Remote implements it at v2, upgrade this client.")`
- L184 [test_resolve_proxy_keeps_generic_message_when_no_hint]: `comm._get_client = AsyncMock(return_value=object())`

### tests/images/meta/test_skyoffsets.py (4)

- L46 [test_to_frame_w_value] patch(`'astropy.coordinates.SkyCoord.transform_to'`): `mocker.patch("astropy.coordinates.SkyCoord.transform_to", return_value=0)`
- L65 [test_separation] patch.object(`meta.'_to_frame'`): `mocker.patch.object(meta, "_to_frame", return_value=(coord0, coord1))`
- L81 [test_spherical_offsets] patch.object(`meta.'_to_frame'`): `mocker.patch.object(meta, "_to_frame", return_value=(coord0, coord1))`
- L82 [test_spherical_offsets] patch(`'astropy.coordinates.SkyCoord.spherical_offsets_to'`): `mocker.patch("astropy.coordinates.SkyCoord.spherical_offsets_to", return_value=(0, 1))`

### tests/images/processors/astrometry/test_dotnet.py (3)

- L167 [test_call_post_error_n_exception] patch(`'aiohttp.ClientSession.post'`): `mock = mocker.patch("aiohttp.ClientSession.post", return_value=resp)`
- L201 [test_call_post_error_w_exception] patch(`'aiohttp.ClientSession.post'`): `mocker.patch("aiohttp.ClientSession.post", return_value=resp)`
- L236 [test_call_success] patch(`'aiohttp.ClientSession.post'`): `mocker.patch("aiohttp.ClientSession.post", return_value=resp)`

### tests/images/processors/exptime/test_exptime.py (4)

- L17 [test_call] patch.object(`estimator.'_calc_exp_time'`): `mocker.patch.object(estimator, "_calc_exp_time", return_value=1.0)`
- L18 [test_call] patch.object(`estimator.'_set_exp_time'`): `mocker.patch.object(estimator, "_set_exp_time", return_value=image)`
- L28 [test_set_exp_time_lower] patch.object(`image.'set_meta'`): `mocker.patch.object(image, "set_meta")`
- L40 [test_set_exp_time_upper] patch.object(`image.'set_meta'`): `mocker.patch.object(image, "set_meta")`

### tests/images/processors/misc/test_addmask.py (1)

- L23 [test_init_str] patch(`'astropy.io.fits.getdata'`): `mocker.patch("astropy.io.fits.getdata", return_value=mask)`

### tests/images/processors/misc/test_calibration.py (11)

- L44 [test_find_master_in_cache] patch.object(`calibration._calib_cache.'get_from_cache'`): `mocker.patch.object(calibration._calib_cache, "get_from_cache", return_value=cached_image)`
- L52 [test_find_master_not_in_archive] patch(`'pyobs.utils.pipeline.Pipeline.find_master'`): `mocker.patch("pyobs.utils.pipeline.Pipeline.find_master", return_value=None)`
- L59 [test_find_master_not_in_archive] patch.object(`calibration._calib_cache.'get_from_cache'`): `mocker.patch.object(calibration._calib_cache, "get_from_cache", side_effect=ValueError())`
- L78 [test_find_master_in_archive] patch(`'pyobs.utils.pipeline.Pipeline.find_master'`): `mocker.patch("pyobs.utils.pipeline.Pipeline.find_master", return_value=calib_image)`
- L84 [test_find_master_in_archive] patch.object(`calibration._calib_cache.'add_to_cache'`): `mocker.patch.object(calibration._calib_cache, "add_to_cache")`
- L99 [test_call_valid] patch(`'pyobs.utils.pipeline.Pipeline.trim_ccddata'`): `mocker.patch("pyobs.utils.pipeline.Pipeline.trim_ccddata", return_value=mock_image)`
- L100 [test_call_valid] patch(`'ccdproc.ccd_process'`): `mocker.patch("ccdproc.ccd_process", return_value=calib_image)`
- L101 [test_call_valid] patch(`'pyobs.images.Image.from_ccddata'`): `mocker.patch("pyobs.images.Image.from_ccddata", return_value=calib_image)`
- L102 [test_call_valid] patch(`'pyobs.images.Image.to_ccddata'`): `mocker.patch("pyobs.images.Image.to_ccddata", return_value=calib_image)`
- L106 [test_call_valid] patch.object(`calibration.'_find_master'`): `mocker.patch.object(calibration, "_find_master", return_value=mock_image)`
- L126 [test_call_calibration_not_found] patch.object(`calibration.'_get_calibrations_masters'`): `mocker.patch.object(calibration, "_get_calibrations_masters", side_effect=ValueError("Test"))`

### tests/images/processors/misc/test_createfilename.py (1)

- L26 [test_call] patch(`'pyobs.images.Image.format_filename'`): `mocker.patch("pyobs.images.Image.format_filename")`

### tests/images/processors/misc/test_removebackground.py (1)

- L37 [test_call_const_background]: `remover._background_remover = Mock(return_value=output_image)`

### tests/images/processors/misc/test_save.py (5)

- L11 [test_init] patch(`'pyobs.utils.fits.FilenameFormatter.__init__'`): `mocker.patch("pyobs.utils.fits.FilenameFormatter.__init__", return_value=None)`
- L21 [test_open] patch.object(`save._comm.'register_event'`): `mocker.patch.object(save._comm, "register_event")`
- L31 [test_call] patch.object(`image.'format_filename'`): `mocker.patch.object(image, "format_filename", return_value="image.fits")`
- L34 [test_call] patch.object(`save._comm.'send_event'`): `mocker.patch.object(save._comm, "send_event")`
- L35 [test_call] patch.object(`save._vfs.'write_image'`): `mocker.patch.object(save._vfs, "write_image")`

### tests/images/processors/misc/test_smooth.py (1)

- L49 [test_call] patch(`'scipy.ndimage.gaussian_filter'`): `mocker.patch("scipy.ndimage.gaussian_filter", return_value=1)`

### tests/images/processors/offsets/test_projected.py (8)

- L29 [test_gaussian_fit] patch(`'pyobs.images.processors.offsets.ProjectedOffsets._gaussian'`): `mocker.patch("pyobs.images.processors.offsets.ProjectedOffsets._gaussian", return_value=np.ones((4, 1)))`
- L55 [test_process_axis_collapse]: `ProjectedOffsets._subtract_sky = Mock(return_value=np.ones(10))`
- L79 [test_process_valid_timsec]: `ProjectedOffsets._subtract_sky = Mock(return_value=np.ones(10))`
- L93 [test_call_ref] patch.object(`offsets.'_process'`): `mocker.patch.object(offsets, "_process", return_value=(np.ones(10) * 10, np.ones(10) * 10))`
- L108 [test_call_no_corr] patch.object(`offsets.'_process'`): `mocker.patch.object(offsets, "_process", return_value=(np.ones(10) * 10, np.ones(10) * 10))`
- L109 [test_call_no_corr] patch.object(`offsets.'_calc_1d_offset'`): `mocker.patch.object(offsets, "_calc_1d_offset", return_value=None)`
- L124 [test_call] patch.object(`offsets.'_process'`): `mocker.patch.object(offsets, "_process", return_value=(np.ones(10) * 10, np.ones(10) * 10))`
- L125 [test_call] patch.object(`offsets.'_calc_1d_offset'`): `mocker.patch.object(offsets, "_calc_1d_offset", return_value=10)`

### tests/images/test_image.py (8)

- L85 [test_from_bytes] patch(`'pyobs.images.Image._from_hdu_list'`): `mocker.patch("pyobs.images.Image._from_hdu_list", return_value=Image(mock_image))`
- L100 [test_from_file] patch(`'pyobs.images.Image._from_hdu_list'`): `mocker.patch("pyobs.images.Image._from_hdu_list", return_value=Image(mock_image))`
- L101 [test_from_file] patch(`'astropy.io.fits.open'`): `mocker.patch("astropy.io.fits.open", return_value=hdul)`
- L203 [test__deepcopy__] patch(`'pyobs.images.Image.copy'`): `mocker.patch("pyobs.images.Image.copy", return_value=image)`
- L293 [test_write_catalog_value] patch(`'astropy.io.fits.convenience.table_to_hdu'`): `mocker.patch("astropy.io.fits.convenience.table_to_hdu")`
- L294 [test_write_catalog_value] patch(`'astropy.io.fits.HDUList.writeto'`): `mocker.patch("astropy.io.fits.HDUList.writeto")`
- L305 [test_write_catalog_non_value] patch(`'astropy.io.fits.convenience.table_to_hdu'`): `mocker.patch("astropy.io.fits.convenience.table_to_hdu")`
- L306 [test_write_catalog_non_value] patch(`'astropy.io.fits.HDUList.writeto'`): `mocker.patch("astropy.io.fits.HDUList.writeto")`

### tests/integration/test_csvpicker_scheduler.py (7)

- L82 [test_csvpicker_picks_visible_target] patch(`'pyobs.utils.time.Time.now'`): `with patch("pyobs.utils.time.Time.now", return_value=NIGHT):`
- L99 [test_csvpicker_returns_none_for_invisible_targets] patch(`'pyobs.utils.time.Time.now'`): `with patch("pyobs.utils.time.Time.now", return_value=NIGHT):`
- L116 [test_csvpicker_respects_airmass_constraint] patch(`'pyobs.utils.time.Time.now'`): `with patch("pyobs.utils.time.Time.now", return_value=NIGHT):`
- L137 [test_scheduler_resolves_csv_dynamic_target] patch(`'pyobs.utils.time.Time.now'`): `with patch("pyobs.utils.time.Time.now", return_value=NIGHT):`
- L157 [test_scheduler_skips_csv_task_with_no_visible_target] patch(`'pyobs.utils.time.Time.now'`): `with patch("pyobs.utils.time.Time.now", return_value=NIGHT):`
- L175 [test_resolved_target_preserved_in_observation] patch(`'pyobs.utils.time.Time.now'`): `with patch("pyobs.utils.time.Time.now", return_value=NIGHT):`
- L198 [test_csv_scheduler_to_mastermind_completes_task] patch(`'pyobs.utils.time.Time.now'`): `with patch("pyobs.utils.time.Time.now", return_value=NIGHT):`

### tests/integration/test_dynamic_target.py (2)

- L46 [make_mock_vfs]: `vfs = MagicMock()`
- L48 [make_mock_vfs]: `vfs.read_csv = AsyncMock(return_value=df)`

### tests/integration/test_mastermind.py (2)

- L140 [run_until_state] patch(`'pyobs.utils.time.Time.now'`): `with patch("pyobs.utils.time.Time.now", return_value=now):`
- L223 [test_mastermind_skips_when_no_observation] patch(`'pyobs.utils.time.Time.now'`): `with patch("pyobs.utils.time.Time.now", return_value=NIGHT):`

### tests/integration/test_scheduler_mastermind.py (8)

- L67 [test_scheduler_produces_observation_for_visible_target] patch(`'pyobs.utils.time.Time.now'`): `with patch("pyobs.utils.time.Time.now", return_value=NIGHT):`
- L88 [test_scheduler_skips_target_failing_airmass] patch(`'pyobs.utils.time.Time.now'`): `with patch("pyobs.utils.time.Time.now", return_value=NIGHT):`
- L101 [test_scheduler_fills_window_with_multiple_tasks] patch(`'pyobs.utils.time.Time.now'`): `with patch("pyobs.utils.time.Time.now", return_value=NIGHT):`
- L114 [test_scheduler_respects_task_duration] patch(`'pyobs.utils.time.Time.now'`): `with patch("pyobs.utils.time.Time.now", return_value=NIGHT):`
- L132 [test_scheduler_to_mastermind_completes_task] patch(`'pyobs.utils.time.Time.now'`): `with patch("pyobs.utils.time.Time.now", return_value=NIGHT):`
- L154 [test_scheduler_to_mastermind_failed_task] patch(`'pyobs.utils.time.Time.now'`): `with patch("pyobs.utils.time.Time.now", return_value=NIGHT):`
- L182 [test_memory_task_archive_feeds_scheduler] patch(`'pyobs.utils.time.Time.now'`): `with patch("pyobs.utils.time.Time.now", return_value=NIGHT):`
- L205 [test_scheduler_ignores_future_observation] patch(`'pyobs.utils.time.Time.now'`): `with patch("pyobs.utils.time.Time.now", return_value=NIGHT):`

### tests/integration/test_transit_mastermind.py (11)

- L61 [make_transit_observation] patch(`'pyobs.utils.time.Time.now'`): `with patch("pyobs.utils.time.Time.now", return_value=NIGHT):`
- L99 [test_transit_merit_end_time_after_night] patch(`'pyobs.utils.time.Time.now'`): `with patch("pyobs.utils.time.Time.now", return_value=NIGHT):`
- L110 [test_transit_merit_end_time_offset] patch(`'pyobs.utils.time.Time.now'`): `with patch("pyobs.utils.time.Time.now", return_value=NIGHT):`
- L164 [test_transit_script_runs_until_end_time] spec=Comm: `{"camera": "camera", "configuration": config}, context={"comm": MagicMock(spec=Comm)}`
- L180 [test_transit_script_runs_until_end_time] patch(`'pyobs.utils.time.Time.now'`): `with patch("pyobs.utils.time.Time.now", return_value=NIGHT):`
- L190 [test_transit_script_runs_until_end_time] patch(`'pyobs.robotic.scripts.imaging.transitimaging.Time.now'`): `with patch("pyobs.robotic.scripts.imaging.transitimaging.Time.now", side_effect=advancing_now):`
- L191 [test_transit_script_runs_until_end_time] patch.object(`TransitMerit.'end_time'`): `with patch.object(TransitMerit, "end_time", return_value=fixed_end):`
- L208 [test_transit_script_does_not_run_after_end_time] spec=Comm: `{"camera": "camera", "configuration": config}, context={"comm": MagicMock(spec=Comm)}`
- L222 [test_transit_script_does_not_run_after_end_time] patch(`'pyobs.utils.time.Time.now'`): `with patch("pyobs.utils.time.Time.now", return_value=NIGHT):`
- L228 [test_transit_script_does_not_run_after_end_time] patch(`'pyobs.robotic.scripts.imaging.transitimaging.Time.now'`): `with patch(`
- L231 [test_transit_script_does_not_run_after_end_time] patch.object(`TransitMerit.'end_time'`): `with patch.object(TransitMerit, "end_time", return_value=past_end):`

### tests/integration/test_xmpp_presence.py (3)

- L33 [make_module]: `m = MagicMock()`
- L37 [make_module]: `m.get_label = AsyncMock(return_value=label)`
- L38 [make_module]: `m.get_version = AsyncMock(return_value="2.0.0.dev1")`

### tests/integration/test_xmpp_state.py (1)

- L47 [make_module]: `m = MagicMock()`

### tests/modules/focus/test_focusmodel.py (8)

- L13 [_weather_mock] spec=IWeather: `weather = MagicMock(spec=IWeather)`
- L14 [_weather_mock]: `weather.get_sensor_value = AsyncMock(`
- L44 [test_open_publishes_optimal_focus_state]: `fm._comm.set_state = AsyncMock()`
- L45 [test_open_publishes_optimal_focus_state]: `mocker.patch.object(Module, "open", AsyncMock())`
- L45 [test_open_publishes_optimal_focus_state] patch.object(`Module.'open'`): `mocker.patch.object(Module, "open", AsyncMock())`
- L60 [test_update_publishes_state_every_iteration]: `fm._comm.set_state = AsyncMock()`
- L66 [test_update_publishes_state_every_iteration]: `mocker.patch("asyncio.sleep", AsyncMock(side_effect=[None, asyncio.CancelledError()]))`
- L66 [test_update_publishes_state_every_iteration] patch(`'asyncio.sleep'`): `mocker.patch("asyncio.sleep", AsyncMock(side_effect=[None, asyncio.CancelledError()]))`

### tests/modules/focus/test_focusseries.py (6)

- L13 [_series] spec=FocusSeries: `return AutoFocusSeries(focuser="focuser", camera="camera", series=MagicMock(spec=FocusSeries))`
- L19 [test_open_publishes_initial_state]: `series._comm.set_state = AsyncMock()`
- L20 [test_open_publishes_initial_state]: `mocker.patch.object(Module, "open", AsyncMock())`
- L20 [test_open_publishes_initial_state] patch.object(`Module.'open'`): `mocker.patch.object(Module, "open", AsyncMock())`
- L39 [test_auto_focus_wraps_tuple_result_in_autofocusresult]: `series._auto_focus = AsyncMock(return_value=(12.3, 0.05))`
- L50 [test_auto_focus_resets_running_flag_on_error]: `series._auto_focus = AsyncMock(side_effect=ValueError("boom"))`

### tests/modules/image/test_imagewatcher.py (28)

- L24 [make_watcher] spec=Comm: `comm=MagicMock(spec=Comm),`
- L25 [make_watcher] spec=VirtualFileSystem: `vfs=MagicMock(spec=VirtualFileSystem),`
- L40 [make_read_write_ctx]: `read_ctx = MagicMock()`
- L41 [make_read_write_ctx]: `read_ctx.__aenter__ = AsyncMock(return_value=MagicMock(read=AsyncMock(return_value=data)))`
- L41 [make_read_write_ctx]: `read_ctx.__aenter__ = AsyncMock(return_value=MagicMock(read=AsyncMock(return_value=data)))`
- L41 [make_read_write_ctx]: `read_ctx.__aenter__ = AsyncMock(return_value=MagicMock(read=AsyncMock(return_value=data)))`
- L42 [make_read_write_ctx]: `read_ctx.__aexit__ = AsyncMock(return_value=False)`
- L44 [make_read_write_ctx]: `write_ctx = MagicMock()`
- L45 [make_read_write_ctx]: `write_ctx.__aenter__ = AsyncMock(return_value=MagicMock(write=AsyncMock()))`
- L45 [make_read_write_ctx]: `write_ctx.__aenter__ = AsyncMock(return_value=MagicMock(write=AsyncMock()))`
- L45 [make_read_write_ctx]: `write_ctx.__aenter__ = AsyncMock(return_value=MagicMock(write=AsyncMock()))`
- L46 [make_read_write_ctx]: `write_ctx.__aexit__ = AsyncMock(return_value=False)`
- L99 [test_worker_copies_file_to_destination]: `watcher._vfs.open_file = MagicMock(side_effect=open_side_effect)`
- L100 [test_worker_copies_file_to_destination]: `watcher._vfs.remove = AsyncMock(return_value=True)`
- L124 [test_worker_deletes_file_after_success]: `watcher._vfs.open_file = MagicMock(side_effect=open_side_effect)`
- L125 [test_worker_deletes_file_after_success]: `watcher._vfs.remove = AsyncMock(return_value=True)`
- L148 [test_worker_formats_fits_filename]: `watcher._vfs.open_file = MagicMock(side_effect=open_side_effect)`
- L149 [test_worker_formats_fits_filename]: `watcher._vfs.remove = AsyncMock(return_value=True)`
- L170 [test_worker_requeues_on_write_failure]: `read_ctx = MagicMock()`
- L171 [test_worker_requeues_on_write_failure]: `read_ctx.__aenter__ = AsyncMock(return_value=MagicMock(read=AsyncMock(return_value=data)))`
- L171 [test_worker_requeues_on_write_failure]: `read_ctx.__aenter__ = AsyncMock(return_value=MagicMock(read=AsyncMock(return_value=data)))`
- L171 [test_worker_requeues_on_write_failure]: `read_ctx.__aenter__ = AsyncMock(return_value=MagicMock(read=AsyncMock(return_value=data)))`
- L172 [test_worker_requeues_on_write_failure]: `read_ctx.__aexit__ = AsyncMock(return_value=False)`
- L174 [test_worker_requeues_on_write_failure]: `write_ctx = MagicMock()`
- L175 [test_worker_requeues_on_write_failure]: `write_ctx.__aenter__ = AsyncMock(side_effect=OSError("write failed"))`
- L176 [test_worker_requeues_on_write_failure]: `write_ctx.__aexit__ = AsyncMock(return_value=False)`
- L181 [test_worker_requeues_on_write_failure]: `watcher._vfs.open_file = MagicMock(side_effect=open_side_effect)`
- L182 [test_worker_requeues_on_write_failure]: `watcher._vfs.remove = AsyncMock(return_value=True)`

### tests/modules/image/test_imagewriter.py (10)

- L19 [make_writer] spec=Comm: `comm=MagicMock(spec=Comm),`
- L20 [make_writer] spec=VirtualFileSystem: `vfs=MagicMock(spec=VirtualFileSystem),`
- L80 [test_worker_downloads_and_stores_image]: `img = MagicMock()`
- L82 [test_worker_downloads_and_stores_image]: `writer._vfs.read_image = AsyncMock(return_value=img)`
- L83 [test_worker_downloads_and_stores_image]: `writer._vfs.write_image = AsyncMock()`
- L105 [test_worker_skips_on_file_not_found]: `writer._vfs.read_image = AsyncMock(side_effect=FileNotFoundError)`
- L118 [test_worker_skips_on_file_not_found]: `writer._vfs.write_image = AsyncMock()`
- L125 [test_worker_skips_on_bad_filename_format]: `img = MagicMock()`
- L127 [test_worker_skips_on_bad_filename_format]: `writer._vfs.read_image = AsyncMock(return_value=img)`
- L128 [test_worker_skips_on_bad_filename_format]: `writer._vfs.write_image = AsyncMock()`

### tests/modules/roof/test_basedome.py (1)

- L32 [test_get_fits_header_before] patch(`'pyobs.modules.roof.BaseRoof.get_fits_header_before'`): `mocker.patch(`

### tests/modules/roof/test_baseroof.py (7)

- L24 [test_open] patch(`'pyobs.mixins.WeatherAwareMixin.open'`): `mocker.patch("pyobs.mixins.WeatherAwareMixin.open")`
- L25 [test_open] patch(`'pyobs.mixins.MotionStatusMixin.open'`): `mocker.patch("pyobs.mixins.MotionStatusMixin.open")`
- L26 [test_open] patch(`'pyobs.modules.Module.open'`): `mocker.patch("pyobs.modules.Module.open")`
- L40 [test_get_fits_header_before_open]: `telescope.motion_status = MagicMock(return_value=MotionStatus.POSITIONED)`
- L51 [test_get_fits_header_before_closed]: `telescope.motion_status = MagicMock(return_value=MotionStatus.PARKED)`
- L60 [test_ready]: `telescope.motion_status = MagicMock(return_value=MotionStatus.TRACKING)`
- L66 [test_not_ready]: `telescope.motion_status = MagicMock(return_value=MotionStatus.PARKING)`

### tests/modules/roof/test_dummyroof.py (13)

- L13 [test_open] patch(`'pyobs.modules.roof.BaseRoof.open'`): `mocker.patch("pyobs.modules.roof.BaseRoof.open")`
- L15 [test_open]: `roof._comm.register_event = AsyncMock()`
- L27 [test_init] patch(`'asyncio.sleep'`): `mocker.patch("asyncio.sleep")`
- L30 [test_init]: `roof._change_motion_status = AsyncMock()`
- L31 [test_init]: `roof._comm.send_event = AsyncMock()`
- L40 [test_park] patch(`'asyncio.sleep'`): `mocker.patch("asyncio.sleep")`
- L45 [test_park]: `roof._change_motion_status = AsyncMock()`
- L46 [test_park]: `roof._comm.send_event = AsyncMock()`
- L55 [test_move_roof_open] patch(`'asyncio.sleep'`): `mocker.patch("asyncio.sleep")`
- L66 [test_move_roof_closed] patch(`'asyncio.sleep'`): `mocker.patch("asyncio.sleep")`
- L77 [test_move_roof_abort] patch(`'asyncio.sleep'`): `mocker.patch("asyncio.sleep")`
- L89 [test_move_roof_percentage] patch(`'asyncio.sleep'`): `mocker.patch("asyncio.sleep")`
- L101 [test_stop_motion]: `roof._change_motion_status = AsyncMock()`

### tests/modules/test/standalone.py (1)

- L18 [test_loop] patch(`'asyncio.sleep'`): `mocker.patch("asyncio.sleep", return_value=None)`

### tests/modules/weather/test_mockweather.py (14)

- L15 [test_open]: `weather._comm.register_event = AsyncMock()`
- L16 [test_open]: `weather._comm.set_state = AsyncMock()`
- L18 [test_open]: `Module.open = AsyncMock()`
- L39 [test_start]: `weather._comm.send_event = AsyncMock()`
- L40 [test_start]: `weather._comm.set_state = AsyncMock()`
- L54 [test_stop]: `weather._comm.set_state = AsyncMock()`
- L73 [test_set_good_no_change]: `weather._comm.send_event = AsyncMock()`
- L74 [test_set_good_no_change]: `weather._comm.set_state = AsyncMock()`
- L85 [test_set_good_becomes_bad]: `weather._comm.send_event = AsyncMock()`
- L86 [test_set_good_becomes_bad]: `weather._comm.set_state = AsyncMock()`
- L100 [test_set_good_becomes_good]: `weather._comm.send_event = AsyncMock()`
- L101 [test_set_good_becomes_good]: `weather._comm.set_state = AsyncMock()`
- L113 [test_set_good_inactive_no_event]: `weather._comm.send_event = AsyncMock()`
- L114 [test_set_good_inactive_no_event]: `weather._comm.set_state = AsyncMock()`

### tests/modules/weather/test_weather.py (21)

- L19 [test_open]: `weather._comm.register_event = AsyncMock()`
- L21 [test_open]: `Module.open = AsyncMock()`
- L34 [test_start]: `weather._comm.send_event = AsyncMock()`
- L65 [test_get_sensor_value_invalid_request]: `weather._api.get_sensor_value = AsyncMock(side_effect=ValueError)`
- L77 [test_get_sensor_value_invalid_response]: `weather._api.get_sensor_value = AsyncMock(return_value={})`
- L86 [test_get_sensor_value]: `weather._api.get_sensor_value = AsyncMock(return_value={"time": "2026-07-02T08:36:42", "value": 2})`
- L118 [test_loop_valid]: `weather._update = AsyncMock()`
- L120 [test_loop_valid] patch(`'asyncio.sleep'`): `mocker.patch("asyncio.sleep")`
- L130 [test_loop_invalid]: `weather._update = AsyncMock(side_effect=ValueError)`
- L132 [test_loop_invalid] patch(`'asyncio.sleep'`): `mocker.patch("asyncio.sleep")`
- L142 [test_update_invalid_url]: `weather._api.get_current_status = AsyncMock(side_effect=ValueError("Could not connect to weather station."))`
- L157 [test_update_invalid_response]: `weather._api.get_current_status = AsyncMock(return_value={})`
- L169 [test_update_good_weather]: `weather._comm.send_event = AsyncMock()`
- L172 [test_update_good_weather]: `weather._api.get_current_status = AsyncMock(return_value={"good": True})`
- L185 [test_update_bad_weather]: `weather._comm.send_event = AsyncMock()`
- L188 [test_update_bad_weather]: `weather._api.get_current_status = AsyncMock(return_value={"good": False})`
- L199 [test_calc_system_init_eta]: `pyobs.utils.time.Time.now = Mock(return_value=Time("2010-01-01T00:00:00", format="isot", scale="utc"))`
- L208 [test_update_publishes_state]: `weather._comm.set_state = AsyncMock()`
- L211 [test_update_publishes_state]: `weather._api.get_current_status = AsyncMock(`
- L232 [test_update_publishes_good_when_inactive]: `weather._comm.set_state = AsyncMock()`
- L235 [test_update_publishes_good_when_inactive]: `weather._api.get_current_status = AsyncMock(return_value={"good": False})`

### tests/modules/weather/test_weather_api.py (4)

- L29 [test_send_valid] patch(`'aiohttp.ClientSession.get'`): `mocker.patch("aiohttp.ClientSession.get", return_value=MockResponse(json, 200))`
- L37 [test_send_invalid] patch(`'aiohttp.ClientSession.get'`): `mocker.patch("aiohttp.ClientSession.get", return_value=MockResponse({}, 404))`
- L46 [test_get_current_status] patch.object(`api.'_send'`): `mocker.patch.object(api, "_send")`
- L54 [test_get_sensor_value] patch.object(`api.'_send'`): `mocker.patch.object(api, "_send")`

### tests/robotic/scheduler/targets/test_dynamictarget.py (3)

- L47 [mock_vfs]: `vfs = MagicMock()`
- L49 [mock_vfs]: `vfs.read_csv = AsyncMock(return_value=df)`
- L193 [test_csv_picker_ra_unit_hour]: `mock_vfs.read_csv = AsyncMock(return_value=df)`

### tests/robotic/scheduler/test_dynamictarget_scheduler.py (2)

- L37 [mock_vfs]: `vfs = MagicMock()`
- L39 [mock_vfs]: `vfs.read_csv = AsyncMock(return_value=df)`

### tests/robotic/scripts/test_autofocus.py (21)

- L27 [make_script]: `return AutoFocusScript.model_validate(kwargs, context={"comm": MagicMock()})`
- L31 [make_task]: `task = MagicMock()`
- L44 [make_telescope] spec=interfaces: `tel = MagicMock(spec=interfaces)`
- L45 [make_telescope]: `tel.get_state = MagicMock(return_value=ReadyState(ready=ready))`
- L46 [make_telescope]: `tel.move_radec = AsyncMock()`
- L47 [make_telescope]: `tel.stop_motion = AsyncMock()`
- L55 [make_autofocus] spec=[IAutoFocus]: `af = MagicMock(spec=[IAutoFocus])`
- L56 [make_autofocus]: `af.auto_focus = AsyncMock()`
- L61 [make_proxy_cm]: `cm = MagicMock()`
- L62 [make_proxy_cm]: `cm.__aenter__ = AsyncMock(return_value=value)`
- L63 [make_proxy_cm]: `cm.__aexit__ = AsyncMock(return_value=None)`
- L74 [test_can_run_true_when_ready]: `script._comm.has_proxy = AsyncMock(return_value=True)`
- L75 [test_can_run_true_when_ready]: `script._comm.safe_proxy = MagicMock(return_value=make_proxy_cm(telescope))`
- L82 [test_can_run_false_when_autofocus_unavailable]: `script._comm.has_proxy = AsyncMock(return_value=False)`
- L90 [test_can_run_false_when_telescope_not_ready]: `script._comm.has_proxy = AsyncMock(return_value=True)`
- L91 [test_can_run_false_when_telescope_not_ready]: `script._comm.safe_proxy = MagicMock(return_value=make_proxy_cm(telescope))`
- L119 [test_run_moves_telescope_and_focuses]: `script._comm.proxy = MagicMock(side_effect=[make_proxy_cm(telescope), make_proxy_cm(autofocus)])`
- L121 [test_run_moves_telescope_and_focuses]: `script._comm.safe_proxy = MagicMock(return_value=make_proxy_cm(telescope))`
- L138 [test_run_stops_telescope_in_finally]: `autofocus.auto_focus = AsyncMock(side_effect=RuntimeError("focus failed"))`
- L140 [test_run_stops_telescope_in_finally]: `script._comm.proxy = MagicMock(side_effect=[make_proxy_cm(telescope), make_proxy_cm(autofocus)])`
- L141 [test_run_stops_telescope_in_finally]: `script._comm.safe_proxy = MagicMock(return_value=make_proxy_cm(telescope))`

### tests/robotic/scripts/test_callmodule.py (13)

- L21 [script]: `context={"comm": MagicMock()},`
- L26 [make_proxy_cm]: `cm = MagicMock()`
- L27 [make_proxy_cm]: `cm.__aenter__ = AsyncMock(return_value=value)`
- L28 [make_proxy_cm]: `cm.__aexit__ = AsyncMock(return_value=None)`
- L104 [test_can_run_true_when_module_available]: `script._comm.has_proxy = AsyncMock(return_value=True)`
- L110 [test_can_run_false_when_module_unavailable]: `script._comm.has_proxy = AsyncMock(return_value=False)`
- L116 [test_can_run_uses_interface_for_proxy]: `script._comm.has_proxy = AsyncMock(return_value=True)`
- L126 [test_run_calls_method_with_named_params]: `proxy = MagicMock()`
- L127 [test_run_calls_method_with_named_params]: `proxy.execute = AsyncMock()`
- L128 [test_run_calls_method_with_named_params]: `script._comm.proxy = MagicMock(return_value=make_proxy_cm(proxy))`
- L136 [test_run_uses_interface_for_proxy]: `proxy = MagicMock()`
- L137 [test_run_uses_interface_for_proxy]: `proxy.execute = AsyncMock()`
- L138 [test_run_uses_interface_for_proxy]: `script._comm.proxy = MagicMock(return_value=make_proxy_cm(proxy))`

### tests/robotic/scripts/test_control.py (22)

- L310 [make_proxy_cm]: `cm = MagicMock()`
- L311 [make_proxy_cm]: `cm.__aenter__ = AsyncMock(return_value=value)`
- L312 [make_proxy_cm]: `cm.__aexit__ = AsyncMock(return_value=None)`
- L318 [test_selector_can_run_when_parked]: `selector = MagicMock()`
- L319 [test_selector_can_run_when_parked]: `selector.wait_for_state = AsyncMock(return_value=MotionState(status=MotionStatus.PARKED))`
- L321 [test_selector_can_run_when_parked]: `comm = MagicMock()`
- L322 [test_selector_can_run_when_parked]: `comm.has_proxy = AsyncMock(return_value=True)`
- L323 [test_selector_can_run_when_parked]: `comm.proxy = MagicMock(return_value=make_proxy_cm(selector))`
- L331 [test_selector_can_run_when_positioned]: `selector = MagicMock()`
- L332 [test_selector_can_run_when_positioned]: `selector.wait_for_state = AsyncMock(return_value=MotionState(status=MotionStatus.POSITIONED))`
- L334 [test_selector_can_run_when_positioned]: `comm = MagicMock()`
- L335 [test_selector_can_run_when_positioned]: `comm.has_proxy = AsyncMock(return_value=True)`
- L336 [test_selector_can_run_when_positioned]: `comm.proxy = MagicMock(return_value=make_proxy_cm(selector))`
- L344 [test_selector_cannot_run_when_moving]: `selector = MagicMock()`
- L345 [test_selector_cannot_run_when_moving]: `selector.wait_for_state = AsyncMock(return_value=MotionState(status=MotionStatus.SLEWING))`
- L347 [test_selector_cannot_run_when_moving]: `comm = MagicMock()`
- L348 [test_selector_cannot_run_when_moving]: `comm.has_proxy = AsyncMock(return_value=True)`
- L349 [test_selector_cannot_run_when_moving]: `comm.proxy = MagicMock(return_value=make_proxy_cm(selector))`
- L357 [test_selector_run_sets_mode]: `selector = MagicMock()`
- L358 [test_selector_run_sets_mode]: `selector.set_mode = AsyncMock()`
- L360 [test_selector_run_sets_mode]: `comm = MagicMock()`
- L361 [test_selector_run_sets_mode]: `comm.proxy = MagicMock(return_value=make_proxy_cm(selector))`

### tests/robotic/scripts/test_darkbias.py (15)

- L26 [make_script]: `return DarkBiasScript.model_validate({"camera": "camera", **kwargs}, context={"comm": MagicMock()})`
- L47 [make_camera] spec=interfaces: `camera = MagicMock(spec=interfaces)`
- L48 [make_camera]: `camera.set_binning = AsyncMock()`
- L49 [make_camera]: `camera.get_capabilities = MagicMock(`
- L52 [make_camera]: `camera.set_window = AsyncMock()`
- L53 [make_camera]: `camera.set_exposure_time = AsyncMock()`
- L54 [make_camera]: `camera.set_image_type = AsyncMock()`
- L55 [make_camera]: `camera.grab_data = AsyncMock()`
- L63 [make_proxy_cm]: `cm = MagicMock()`
- L64 [make_proxy_cm]: `cm.__aenter__ = AsyncMock(return_value=value)`
- L65 [make_proxy_cm]: `cm.__aexit__ = AsyncMock(return_value=None)`
- L90 [setup_run_comm]: `script._comm.safe_proxy = MagicMock(side_effect=safe_proxy_se)`
- L91 [setup_run_comm]: `script._comm.proxy = MagicMock(return_value=make_proxy_cm(camera))`
- L100 [test_can_run_true_when_camera_available]: `script._comm.has_proxy = AsyncMock(return_value=True)`
- L107 [test_can_run_false_when_camera_unavailable]: `script._comm.has_proxy = AsyncMock(return_value=False)`

### tests/robotic/scripts/test_transitimaging.py (13)

- L29 [make_script] spec=Comm: `{"camera": "camera", "configuration": config}, context={"comm": MagicMock(spec=Comm)}`
- L50 [make_task_data]: `data = MagicMock()`
- L62 [test_can_run_false_without_transit_merit]: `with patch.object(script.__class__.__bases__[0], "can_run", AsyncMock(return_value=True)):`
- L62 [test_can_run_false_without_transit_merit] patch.object(`script.__class__.__bases__[0].'can_run'`): `with patch.object(script.__class__.__bases__[0], "can_run", AsyncMock(return_value=True)):`
- L105 [test_run_configurations_loops_until_end_time] patch.object(`TransitMerit.'end_time'`): `with patch.object(TransitMerit, "end_time", return_value=fixed_end_time):`
- L106 [test_run_configurations_loops_until_end_time] patch(`'pyobs.robotic.scripts.imaging.transitimaging.Time.now'`): `with patch("pyobs.robotic.scripts.imaging.transitimaging.Time.now", side_effect=controlled_now):`
- L130 [test_run_configurations_stops_immediately_if_past_end_time] patch.object(`TransitMerit.'end_time'`): `with patch.object(TransitMerit, "end_time", return_value=past_end_time):`
- L152 [test_run_configurations_uses_modulo_repeats] spec=Comm: `{"camera": "camera", "configuration": config}, context={"comm": MagicMock(spec=Comm)}`
- L177 [test_run_configurations_uses_modulo_repeats] patch(`'pyobs.robotic.scripts.imaging.transitimaging.Time.now'`): `with patch("pyobs.robotic.scripts.imaging.transitimaging.Time.now", side_effect=advancing_now):`
- L178 [test_run_configurations_uses_modulo_repeats] patch.object(`TransitMerit.'end_time'`): `with patch.object(TransitMerit, "end_time", return_value=fixed_end_time):`
- L194 [test_estimate_duration_no_data_returns_full_window]: `data = MagicMock()`
- L216 [test_estimate_duration_with_time_never_returns_zero_outside_window]: `data = MagicMock()`
- L235 [test_estimate_duration_with_time_decreases_through_window]: `data = MagicMock()`

### tests/robotic/storage/backend/test_backend_archives.py (21)

- L42 [make_task_archive]: `archive._aiohttp_session = MagicMock()`
- L59 [make_obs_archive]: `archive._aiohttp_session = MagicMock()`
- L117 [test_task_last_update_time] patch(`'pyobs.robotic.storage.backend.taskarchive.http_request_with_retries'`): `mocker.patch(`
- L119 [test_task_last_update_time]: `AsyncMock(return_value={"last_task_update": "2025-11-03T23:00:00.000"}),`
- L128 [test_task_get_projects_from_backend] patch(`'pyobs.robotic.storage.backend.taskarchive.http_request_with_retries'`): `mocker.patch(`
- L130 [test_task_get_projects_from_backend]: `AsyncMock(return_value={"results": [{"code": "test", "name": "Test", "priority": 1.0}]}),`
- L140 [test_task_get_tasks_from_backend] patch(`'pyobs.robotic.storage.backend.taskarchive.http_request_with_retries'`): `mocker.patch(`
- L142 [test_task_get_tasks_from_backend]: `AsyncMock(return_value={"results": [{"id": 1, "name": "t1", "duration": 300}]}),`
- L211 [test_obs_get_next_calls_fetch_task]: `task_archive = MagicMock()`
- L212 [test_obs_get_next_calls_fetch_task]: `mock_fetch = mocker.patch.object(Observation, "fetch_task", AsyncMock())`
- L212 [test_obs_get_next_calls_fetch_task] patch.object(`Observation.'fetch_task'`): `mock_fetch = mocker.patch.object(Observation, "fetch_task", AsyncMock())`
- L241 [test_obs_add_observations] patch(`'pyobs.robotic.storage.backend.observationarchive.http_request_with_retries'`): `mock_request = mocker.patch(`
- L243 [test_obs_add_observations]: `AsyncMock(return_value={}),`
- L256 [test_obs_clear_schedule] patch(`'pyobs.robotic.storage.backend.observationarchive.http_request_with_retries'`): `mock_request = mocker.patch(`
- L258 [test_obs_clear_schedule]: `AsyncMock(return_value={}),`
- L269 [test_obs_update_observation] patch(`'pyobs.robotic.storage.backend.observationarchive.http_request_with_retries'`): `mock_request = mocker.patch(`
- L271 [test_obs_update_observation]: `AsyncMock(return_value={}),`
- L287 [test_obs_get_observations_builds_params] patch(`'pyobs.robotic.storage.backend.observationarchive.http_request_with_retries'`): `mock_request = mocker.patch(`
- L289 [test_obs_get_observations_builds_params]: `AsyncMock(return_value={"results": []}),`
- L308 [test_obs_last_update_time] patch(`'pyobs.robotic.storage.backend.observationarchive.http_request_with_retries'`): `mocker.patch(`
- L310 [test_obs_last_update_time]: `AsyncMock(return_value={"last_observation_update": "2025-11-03T23:00:00.000"}),`

### tests/robotic/storage/filesystem/test_yaml_archives.py (1)

- L270 [make_task_archive]: `vfs = MagicMock()`

### tests/robotic/storage/lco/helpers.py (1)

- L31 [make_portal]: `p._session = MagicMock()`

### tests/robotic/storage/lco/test_lco_http.py (19)

- L48 [test_task_archive_filters_by_instrument]: `mocker.patch.object(archive._portal, "schedulable_requests", AsyncMock(return_value=[sr]))`
- L48 [test_task_archive_filters_by_instrument] patch.object(`archive._portal.'schedulable_requests'`): `mocker.patch.object(archive._portal, "schedulable_requests", AsyncMock(return_value=[sr]))`
- L49 [test_task_archive_filters_by_instrument]: `mocker.patch.object(archive._portal, "proposals", AsyncMock(return_value=[{"id": "test", "tac_priority": 1.0}]))`
- L49 [test_task_archive_filters_by_instrument] patch.object(`archive._portal.'proposals'`): `mocker.patch.object(archive._portal, "proposals", AsyncMock(return_value=[{"id": "test", "tac_priority": 1.0}]))`
- L63 [test_task_archive_excludes_non_pending_requests]: `mocker.patch.object(archive._portal, "schedulable_requests", AsyncMock(return_value=[sr]))`
- L63 [test_task_archive_excludes_non_pending_requests] patch.object(`archive._portal.'schedulable_requests'`): `mocker.patch.object(archive._portal, "schedulable_requests", AsyncMock(return_value=[sr]))`
- L64 [test_task_archive_excludes_non_pending_requests]: `mocker.patch.object(archive._portal, "proposals", AsyncMock(return_value=[{"id": "test", "tac_priority": 1.0}]))`
- L64 [test_task_archive_excludes_non_pending_requests] patch.object(`archive._portal.'proposals'`): `mocker.patch.object(archive._portal, "proposals", AsyncMock(return_value=[{"id": "test", "tac_priority": 1.0}]))`
- L133 [test_observation_archive_get_observations]: `mocker.patch.object(archive._portal, "observations", AsyncMock(return_value=obs_list))`
- L133 [test_observation_archive_get_observations] patch.object(`archive._portal.'observations'`): `mocker.patch.object(archive._portal, "observations", AsyncMock(return_value=obs_list))`
- L158 [test_observation_archive_get_observations_state_filter]: `mocker.patch.object(archive._portal, "observations", AsyncMock(return_value=obs_list))`
- L158 [test_observation_archive_get_observations_state_filter] patch.object(`archive._portal.'observations'`): `mocker.patch.object(archive._portal, "observations", AsyncMock(return_value=obs_list))`
- L170 [test_observation_archive_send_update] patch.object(`archive._portal.'update_configuration_status'`): `patch_mock = mocker.patch.object(`
- L171 [test_observation_archive_send_update]: `archive._portal, "update_configuration_status", AsyncMock(return_value=CONFIG_STATUS_RESPONSE)`
- L181 [test_observation_archive_send_update_skips_none]: `archive._portal.update_configuration_status = AsyncMock()`
- L196 [test_observation_archive_update_observation]: `send_mock = mocker.patch.object(archive, "send_update", AsyncMock())`
- L196 [test_observation_archive_update_observation] patch.object(`archive.'send_update'`): `send_mock = mocker.patch.object(archive, "send_update", AsyncMock())`
- L212 [test_observation_archive_update_observation_skips_non_lco]: `send_mock = mocker.patch.object(archive, "send_update", AsyncMock())`
- L212 [test_observation_archive_update_observation_skips_non_lco] patch.object(`archive.'send_update'`): `send_mock = mocker.patch.object(archive, "send_update", AsyncMock())`

### tests/robotic/storage/lco/test_portal.py (1)

- L15 [test_schedulable_requests] patch.object(`portal.'_get'`): `mocker.patch.object(portal, "_get", return_value=request_config)`

### tests/robotic/storage/lco/test_schedulereader.py (26)

- L36 [make_reader]: `reader._update_error_log = MagicMock()`
- L37 [make_reader]: `reader._update_error_log.resolve = MagicMock()`
- L38 [make_reader]: `reader._update_error_log.error = MagicMock()`
- L50 [make_observation]: `MagicMock(start=start, end=end, request=MagicMock(id=obs_data["request"]["id"], configurations=[])),`
- L50 [make_observation]: `MagicMock(start=start, end=end, request=MagicMock(id=obs_data["request"]["id"], configurations=[])),`
- L69 [test_get_schedule_returns_cached_tasks]: `obs = Observation(task=MagicMock(id=1, name="t"), start=T0, end=T1)`
- L81 [test_get_task_returns_active_observation]: `reader._update_schedule_now = AsyncMock()`
- L83 [test_get_task_returns_active_observation]: `obs = MagicMock()`
- L98 [test_get_task_returns_none_before_window]: `reader._update_schedule_now = AsyncMock()`
- L100 [test_get_task_returns_none_before_window]: `obs = MagicMock()`
- L113 [test_get_task_skips_finished_tasks]: `reader._update_schedule_now = AsyncMock()`
- L115 [test_get_task_skips_finished_tasks]: `obs = MagicMock()`
- L128 [test_get_task_calls_update_schedule_now]: `reader._update_schedule_now = AsyncMock()`
- L146 [test_download_schedule_returns_observations]: `mocker.patch.object(reader._portal, "download_schedule", AsyncMock(return_value=[obs]))`
- L146 [test_download_schedule_returns_observations] patch.object(`reader._portal.'download_schedule'`): `mocker.patch.object(reader._portal, "download_schedule", AsyncMock(return_value=[obs]))`
- L155 [test_download_schedule_empty_portal_response]: `mocker.patch.object(reader._portal, "download_schedule", AsyncMock(return_value=[]))`
- L155 [test_download_schedule_empty_portal_response] patch.object(`reader._portal.'download_schedule'`): `mocker.patch.object(reader._portal, "download_schedule", AsyncMock(return_value=[]))`
- L167 [test_update_schedule_now_updates_cache]: `obs = MagicMock()`
- L171 [test_update_schedule_now_updates_cache]: `mocker.patch.object(reader, "_download_schedule", AsyncMock(return_value=ObservationList([obs])))`
- L171 [test_update_schedule_now_updates_cache] patch.object(`reader.'_download_schedule'`): `mocker.patch.object(reader, "_download_schedule", AsyncMock(return_value=ObservationList([obs])))`
- L182 [test_update_schedule_now_sets_last_schedule_time]: `mocker.patch.object(reader, "_download_schedule", AsyncMock(return_value=ObservationList([MagicMock()])))`
- L182 [test_update_schedule_now_sets_last_schedule_time]: `mocker.patch.object(reader, "_download_schedule", AsyncMock(return_value=ObservationList([MagicMock()])))`
- L182 [test_update_schedule_now_sets_last_schedule_time] patch.object(`reader.'_download_schedule'`): `mocker.patch.object(reader, "_download_schedule", AsyncMock(return_value=ObservationList([MagicMock()])))`
- L196 [test_update_schedule_now_respects_lock]: `download_mock = mocker.patch.object(reader, "_download_schedule", AsyncMock(return_value=ObservationList()))`
- L196 [test_update_schedule_now_respects_lock] patch.object(`reader.'_download_schedule'`): `download_mock = mocker.patch.object(reader, "_download_schedule", AsyncMock(return_value=ObservationList()))`
- L202 [test_update_schedule_now_respects_lock] patch(`'pyobs.robotic.storage.lco._schedulereader.acquire_lock'`): `with patch("pyobs.robotic.storage.lco._schedulereader.acquire_lock", fast_acquire):`

### tests/robotic/storage/lco/test_schedulewriter.py (9)

- L21 [make_configdb] spec=ConfigDB: `configdb = MagicMock(spec=ConfigDB)`
- L22 [make_configdb]: `instrument = MagicMock()`
- L53 [make_lco_observation] spec=LcoTask: `task = MagicMock(spec=LcoTask)`
- L97 [test_create_observations_skips_unknown_instrument_type] spec=ConfigDB: `configdb = MagicMock(spec=ConfigDB)`
- L112 [test_create_observations_warns_on_multiple_instruments] spec=ConfigDB: `configdb = MagicMock(spec=ConfigDB)`
- L113 [test_create_observations_warns_on_multiple_instruments]: `inst1 = MagicMock()`
- L116 [test_create_observations_warns_on_multiple_instruments]: `inst2 = MagicMock()`
- L151 [test_add_schedule_calls_portal]: `portal.submit_observations = AsyncMock()`
- L162 [test_clear_schedule_calls_portal]: `portal.clear_schedule = AsyncMock()`

### tests/robotic/test_task.py (2)

- L151 [test_fetch_task_restores_resolved_target]: `mock_archive = AsyncMock()`
- L152 [test_fetch_task_restores_resolved_target]: `mock_archive.get_task = AsyncMock(return_value=task)`

### tests/robotic/utils/exptime/test_stellarexptime.py (20)

- L39 [make_image]: `img = MagicMock()`
- L48 [make_provider] spec=Comm: `defaults, context={"comm": MagicMock(spec=Comm), "vfs": MagicMock()}`
- L48 [make_provider]: `defaults, context={"comm": MagicMock(spec=Comm), "vfs": MagicMock()}`
- L56 [make_camera_mocks]: `mock_camera = AsyncMock()`
- L57 [make_camera_mocks]: `mock_camera.grab_data = AsyncMock(side_effect=["bias.fits", "sci.fits"])`
- L59 [make_camera_mocks]: `mock_exptime = AsyncMock()`
- L60 [make_camera_mocks]: `mock_exptime.get_exposure_time = AsyncMock(return_value=orig_exptime)`
- L62 [make_camera_mocks]: `mock_imagetype = AsyncMock()`
- L64 [make_camera_mocks]: `mock_window = AsyncMock()`
- L65 [make_camera_mocks]: `mock_window.get_window = AsyncMock(return_value=(0, 0, SHAPE[1], SHAPE[0]))`
- L81 [attach_proxies]: `provider._vfs.read_image = AsyncMock(`
- L97 [attach_proxies]: `provider._comm.proxy = AsyncMock(side_effect=proxy_side_effect)`
- L198 [test_call_restores_settings_on_exception]: `mock_camera = AsyncMock()`
- L199 [test_call_restores_settings_on_exception]: `mock_camera.grab_data = AsyncMock(side_effect=RuntimeError("camera error"))`
- L200 [test_call_restores_settings_on_exception]: `mock_exptime = AsyncMock()`
- L201 [test_call_restores_settings_on_exception]: `mock_exptime.get_exposure_time = AsyncMock(return_value=10.0)`
- L202 [test_call_restores_settings_on_exception]: `mock_imagetype = AsyncMock()`
- L203 [test_call_restores_settings_on_exception]: `mock_window = AsyncMock()`
- L204 [test_call_restores_settings_on_exception]: `mock_window.get_window = AsyncMock(return_value=(0, 0, 512, 512))`
- L215 [test_call_restores_settings_on_exception]: `provider._comm.proxy = AsyncMock(side_effect=proxy_side_effect)`

### tests/test_background_task.py (5)

- L13 [make_task]: `parent = MagicMock()`
- L14 [make_task]: `parent.quit = MagicMock()`
- L171 [test_rapid_failures_trigger_quit]: `parent = MagicMock()`
- L189 [test_rapid_failures_no_restart_just_quits]: `parent = MagicMock()`
- L214 [test_slow_failures_reset_counter]: `parent = MagicMock()`

### tests/test_object.py (7)

- L9 [test_add_background_task]: `test_function = AsyncMock()`
- L20 [test_perform_background_task_autostart] patch(`'pyobs.background_task.BackgroundTask.start'`): `mocker.patch("pyobs.background_task.BackgroundTask.start")`
- L23 [test_perform_background_task_autostart]: `test_function = AsyncMock()`
- L32 [test_perform_background_task_no_autostart] patch(`'pyobs.background_task.BackgroundTask.start'`): `mocker.patch("pyobs.background_task.BackgroundTask.start")`
- L35 [test_perform_background_task_no_autostart]: `test_function = AsyncMock()`
- L44 [test_stop_background_task] patch(`'pyobs.background_task.BackgroundTask.stop'`): `mocker.patch("pyobs.background_task.BackgroundTask.stop")`
- L47 [test_stop_background_task]: `test_function = AsyncMock()`

### tests/utils/grids/test_filters.py (1)

- L53 [test_fromlistfilter] patch(`'astropy.time.Time.now'`): `mocker.patch("astropy.time.Time.now", return_value=time)`

### tests/utils/test_http.py (12)

- L13 [make_response]: `response = MagicMock()`
- L15 [make_response]: `response.json = AsyncMock(return_value=json_data or {})`
- L16 [make_response]: `response.text = AsyncMock(return_value=text)`
- L17 [make_response]: `response.__aenter__ = AsyncMock(return_value=response)`
- L18 [make_response]: `response.__aexit__ = AsyncMock(return_value=False)`
- L23 [make_session]: `session = MagicMock()`
- L24 [make_session]: `session.request = MagicMock(return_value=response)`
- L91 [test_client_error_raises_on_wrapped]: `bad_response = MagicMock()`
- L92 [test_client_error_raises_on_wrapped]: `bad_response.__aenter__ = AsyncMock(side_effect=aiohttp.ClientError("connection failed"))`
- L93 [test_client_error_raises_on_wrapped]: `bad_response.__aexit__ = AsyncMock(return_value=False)`
- L95 [test_client_error_raises_on_wrapped]: `session = MagicMock()`
- L96 [test_client_error_raises_on_wrapped]: `session.request = MagicMock(return_value=bad_response)`

### tests/utils/test_shellcommand.py (21)

- L98 [make_proxy_cm]: `cm = MagicMock()`
- L99 [make_proxy_cm]: `cm.__aenter__ = AsyncMock(return_value=value)`
- L100 [make_proxy_cm]: `cm.__aexit__ = AsyncMock(return_value=None)`
- L106 [test_execute_success]: `proxy = MagicMock()`
- L107 [test_execute_success]: `proxy.execute = AsyncMock(return_value=None)`
- L108 [test_execute_success]: `comm = MagicMock()`
- L109 [test_execute_success]: `comm.safe_proxy = MagicMock(return_value=make_proxy_cm(proxy))`
- L120 [test_execute_with_return_value]: `proxy = MagicMock()`
- L121 [test_execute_with_return_value]: `proxy.execute = AsyncMock(return_value=30.0)`
- L122 [test_execute_with_return_value]: `comm = MagicMock()`
- L123 [test_execute_with_return_value]: `comm.safe_proxy = MagicMock(return_value=make_proxy_cm(proxy))`
- L134 [test_execute_module_not_found]: `comm = MagicMock()`
- L135 [test_execute_module_not_found]: `comm.safe_proxy = MagicMock(return_value=make_proxy_cm(None))`
- L146 [test_execute_invalid_param]: `proxy = MagicMock()`
- L147 [test_execute_invalid_param]: `proxy.execute = AsyncMock(side_effect=ValueError("bad param"))`
- L148 [test_execute_invalid_param]: `comm = MagicMock()`
- L149 [test_execute_invalid_param]: `comm.safe_proxy = MagicMock(return_value=make_proxy_cm(proxy))`
- L160 [test_execute_remote_error]: `proxy = MagicMock()`
- L161 [test_execute_remote_error]: `proxy.execute = AsyncMock(side_effect=exc.RemoteError("something failed"))`
- L162 [test_execute_remote_error]: `comm = MagicMock()`
- L163 [test_execute_remote_error]: `comm.safe_proxy = MagicMock(return_value=make_proxy_cm(proxy))`

### tests/vfs/test_httpfile.py (10)

- L9 [_make_response]: `resp = MagicMock()`
- L11 [_make_response]: `resp.read = AsyncMock(return_value=body)`
- L12 [_make_response]: `resp.__aenter__ = AsyncMock(return_value=resp)`
- L13 [_make_response]: `resp.__aexit__ = AsyncMock(return_value=False)`
- L18 [_make_session]: `session = MagicMock()`
- L19 [_make_session]: `session.post = MagicMock(return_value=post_resp)`
- L20 [_make_session]: `session.get = MagicMock(return_value=get_resp)`
- L21 [_make_session]: `session.__aenter__ = AsyncMock(return_value=session)`
- L22 [_make_session]: `session.__aexit__ = AsyncMock(return_value=False)`
- L36 [test_upload_download] patch(`'aiohttp.ClientSession'`): `with patch("aiohttp.ClientSession", return_value=session):`
