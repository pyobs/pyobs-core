# Graph Report - pyobs-core  (2026-08-20)

## Corpus Check
- 798 files · ~439,936 words
- Verdict: corpus is large enough that graph structure adds value.

## Summary
- 9046 nodes · 21726 edges · 449 communities (412 shown, 37 thin omitted)
- Extraction: 93% EXTRACTED · 7% INFERRED · 0% AMBIGUOUS · INFERRED: 1439 edges (avg confidence: 0.55)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `e8b532ff`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- FlatField
- LcoTaskArchive
- Task
- Module
- benchmark_state_throughput.py
- OffsetResult
- Image
- test_mastermind.py
- test_presence.py
- ImageProcessor
- XmppComm
- Interface
- DummyCamera
- utils/test_http.py
- utils/exceptions.py
- VirtualFileSystem
- BackendTaskArchive
- Unit
- DummyRoof
- mixins/test_fitsheader.py
- Event
- PipelineMixin
- AstrometryDotNet
- test_flatfielder.py
- LocalComm
- tests/test_events.py
- test_lco_http.py
- DummySolarTelescope
- DummyRaDecTelescope
- WindowingWidget
- Interfaces (pyobs.interfaces) API doc
- test_control.py
- SolarElevationConstraint
- dummycamera.py
- WeatherSensors
- .set_exposure_time
- Future
- test_localcomm_state.py
- xmppcomm.py
- test_follow.py
- LcoTask
- SkyOffsets
- test_xmpp_event_subscriptions.py
- Comm
- test_transitimaging.py
- robotic/test_scheduler.py
- StandAlone
- HttpFileCache
- _SepAperturePhotometry
- test_stellarexptime.py
- RuntimeError
- RPC
- WindowCapabilities
- test_shellcommand.py
- Calibration
- object.py
- Publisher
- test_startup_gating.py
- test_autoguiding.py
- Proxy
- FilenameFormatter
- test_basevideo.py
- test_yaml_archives.py
- test_schedulewriter.py
- FlatFielder
- IExposure
- Telegram
- DynamicTarget
- TimeDelta
- Offsets
- .now
- PyObsError
- test_proxy.py
- XEP_0009
- Scheduler
- PyobsDaemon
- test_acquisition.py
- test_config.py
- TaskData
- TaskRunner
- Weather
- IWindow
- test_csvpicker_scheduler.py
- integration/conftest.py
- test_pipeline_on_error.py
- Ring
- loaded_pyobs_packages
- XmppClient
- test_exception_logging.py
- _DaoBackgroundRemover
- Application
- DummyComm
- CallModuleScript
- ProjectedOffsets
- test_pyobs_archive.py
- HttpFile
- Archive
- application.py
- FocusSeries
- _SourceCatalog
- make_proxy_cm
- NewSpectrumEvent
- Any
- lco/task.py
- test_coordinates.py
- get_registered_interface
- Portal
- LocalArchive
- Plan: Systematic ejabberd throughput/latency benchmarking
- _PhotUtilAperturePhotometry
- Mixins (pyobs.mixins) API doc
- Script base class
- ImageWatcher
- CommLoggingHandler
- ._expose
- test_dummyradectelescope.py
- ImagingScript
- comm/test_events.py
- MemoryFile
- VFSFile
- LocalFile
- test_version_mismatch.py
- CLAUDE.md (repo guide)
- PillowHelper
- FocusModel
- DataCache
- ImageSourceFilter
- test_darkbias.py
- Script
- Time
- Plan: pyobs-pipeline
- Test Localcomm (local)
- sourcedetection.py
- MotionStatusChangedEvent
- MoveAltAzEvent
- test_dummymode.py
- MockWeather
- SiderealTarget
- Grid
- test_kiosk.py
- pyobs.py
- Robotic recipe (doc)
- Scheduler
- GuidingStatisticsPixelOffset
- test_config_schema.py
- Pipeline
- NewImageEvent
- RollingTimeAverage
- GuidingStatistics
- LogEvent
- tests/xmpp/docker-compose.yml (ejabberd integration test container)
- `OBSNUM`: per-night observation counter in FITS headers
- 3rd party packages (doc)
- test_basetelescope.py
- SSHFile
- create_rst.py
- test_lcoscript.py
- SoftBin
- AddMask
- pyobs/modules/utils/__init__.py
- SkyCoord
- robotic/task.py
- BaseTelescope
- SepSourceDetection
- Design
- ExpTimeEval
- storage/taskarchive.py
- Overview (doc)
- LogScript
- test_imagewatcher.py
- fit_hyperbola
- FitsHeaderOffsets
- test_grab_sequence.py
- binding.py
- ProjectionFocusSeries
- .get_config_value
- test_xmppcomm_event_payload.py
- test_transit_mastermind.py
- test_dummyvideo.py
- test_scheduler_mastermind.py
- Steering: astropy IERS auto-download blocks event loop
- Kiosk
- .get_object
- .set_focus
- Merit
- ejabberd shaper throttling bug (xmpp_socket.erl re-arm) & fix
- ImageType
- Plan: Make the pydantic config layer reject unknown keys (`extra="forbid"`)
- Work Plan
- Plan: `pyobs-gui` TelescopeWidget layout — width floor investigation & design notes
- PointingSeries
- GridNode
- Plan: Make mixin `__init__` composition cooperative, then enforce unrecognized kwargs at `Object.__init__`
- flatfield/test_scheduler.py
- What's New in pyobs 2.0 (doc)
- .__init__
- test_schedulereader.py
- CatalogCircularMask
- Plan: `pyobs-gui` IAutoFocus widget
- AperturePhotometry
- test_backend_archives.py
- test_basecamera.py
- show_module_info.py
- RunningState
- DaophotSourceDetection
- robotic
- Scheduler module
- BaseModel (pyobs.utils.serialization)
- Decision
- Stellarium
- weather.py
- BaseVideo
- Plan: Widget plugin mechanism + `pyside6-deploy` packaging for `pyobs-gui`
- Plan: Split archive prefetch from CPU-bound merit evaluation, to unblock a `ProcessPoolExecutor`
- .image_handler
- Image (pyobs.images.processors.image) API doc
- Offsets (pyobs.images.processors.offsets) API doc
- Constraint
- Smooth
- http_request_paginated
- test_autofocus.py
- SkyflatPriorities
- test_xmpp_rpc.py
- Plan: `IDataSequence` — server-side counted data sequences (reconstructed)
- TaskStartedEvent
- is_valid_jid
- .move_heliographic_stonyhurst
- FileList
- .move_helioprojective
- .phase_for_jd
- pyobs 2.0 Wire Protocol, State, and Access Control design doc
- Plan: Log the loaded pyobs-* package versions at module startup
- Findings: driver/gui correctness review, all 8 repos (reviewed 2026-08-11)
- Plan: Unify TRIMSEC handling into `Image.trim()` (reconstructed)
- CHANGELOG.rst
- Use a self-hosted Keycloak alongside odin, as two parallel auth backends
- Image class
- PySepStatsCalculator
- Implementation
- .set_rotation
- Module.startup() lifecycle helper
- Object
- Plan: Stop scheduler constraint/merit evaluation from blocking the event loop
- .__init__
- watch_log_events_no_interest.py
- SkyFlatsBasePointing
- pyobs-gui as a standalone binary (umbrella design)
- Plan: Enforce state publishing for stateful interfaces
- Plan: `pyobs-gui` login window
- test_safe_send.py
- test_exceptions.py
- Two-phase Object lifecycle; rationale: __init__ must not touch hardware/external services (only store params, create children, register background tasks); open() is where side effects happen, so objects can be constructed cheaply/safely before being started
- Simulation recipe (doc)
- test_httpfilecache.py
- test_imagewriter.py
- _ResponseImageWriter
- Decision
- _PhotometryCalculator
- TaskFinishedEvent
- TempFile
- PrimaryHDU
- robotic
- Archive (image archive base)
- ._move_radec
- ._get_client
- GuidingStatisticsSkyOffset
- SFTPFile
- test_xmpp_acl.py
- ._get_next
- Discussion: LogEvent double-delivery fix — should we drop add_interest()?
- Plan: `pyobs-gui` navbar keyboard shortcuts
- filters.py
- .__call__
- Image.trim
- conftest.py
- Misc (pyobs.images.processors.misc) API doc
- PolymorphicBaseModel
- Plan: Stop gating backend-archive refreshes on the `last_*_update` marker
- time.py
- InfluxHandler
- FollowMixin
- ObservationList
- .move_heliocentric_polar
- wait_for
- test_astroplanscheduler.py
- Implementation
- Plan: Interactive login/settings dialog for `pyobs-gui`, deferring `Application`'s module construction
- pyobs.modules.utils (doc)
- Plan: Add baseline tests to core-tier repos, then enable grouped Dependabot auto-merge
- Plan: CORS + token auth for `HttpFileCache`
- ._residuals
- Photometry
- Plan: `pyobs-gui` IAutoGuiding widget
- ImageFormat
- DummyMode
- Investigation: pyobs-gui receives every LogEvent twice (SAAO/monet production)
- WeatherStatus
- PyobsArchive
- .init
- BufferedFile
- ADR-0008: _safe_send keeps bounded retry unlike capability/subscribe fetches
- Module._watch_event_loop_lag
- Plan: Surface unrecognized kwargs in `Object.__init__` instead of silently discarding them
- pyobs.modules.image (doc)
- .__init__
- _baseguiding.py
- datetime
- Plan: Bound the FITS-header fetch so a dead peer can't stall the frame
- plans/index.md
- ScriptRunner
- test_camerasettings.py
- CasesRunner
- Plan: `pyobs-auth` + Keycloak integration
- Fleet open items: open issues and plans across the pyobs fleet
- SMBFile
- .grab_sequence
- ModuleLocation dataclass (nested in ModuleCapabilities)
- check_pyobs_releases.sh
- check_ejabberd_notify.py
- test_dummysolartelescope.py
- ._main
- RaDecOffsets
- Photometry (pyobs.images.processors.photometry) API doc
- .__init__
- .__init__
- Target
- test_comm_interface_resolution.py
- .night_obs
- _FakeProxyContext
- .__init__
- .sun_altaz
- _ProxyContext
- Plan: Module observer-location capabilities (reconstructed)
- Plan: Advertise event send/subscribe role in disco#info
- IFocusModel
- .__init__
- .night
- Implemented
- make_observer
- .clients_with_interface
- .flat_field
- test_istructuredconfig.py
- transitimaging.py
- pyobs.modules.weather (doc)
- ._set_presence
- IPointingAltAz
- .move_radec
- test_pointing.py
- ._active_update
- _DummyTelescopeBase
- .set_cooling
- README.md
- Install-ejabberd (xmpp)
- XmppComm._disconnected
- Autocompletion ()
- .__init__
- pyobs.modules.pointing (doc)
- check_changelog.sh
- delete_pubsub_nodes.py
- ejabberd 10x Shaper Benchmark Config
- list_pubsub_nodes.py
- ADR-0005: IConfig stays a stringly-keyed fallback
- Exception handling across the RPC boundary (design doc)
- Steering: Fleet tooling consistency baseline
- mock_header
- docs/requirements.txt
- Modules (pyobs.images.processors.modules) API doc
- WCS (pyobs.images.processors.wcs) API doc
- Changelog (doc)
- License (doc)
- pyobs/images/processors/__init__.py
- Steering: Finding a module's logs under pyobsd
- filecache/test_http.py
- test_cases.py
- test_debugtrigger.py
- Institut für Astrophysik Göttingen (IAG) logo, used as documentation branding image
- MONET Telescopes Logo
- pyobs Project Logo
- pyobs Logo
- ROTSE Namibia logo
- gregory camera
- Object.comm property / proxy pattern
- OnDemandScheduler
- Scheduling (pyobs.robotic.scheduler) API doc
- Project
- pyobs-core

## God Nodes (most connected - your core abstractions)
1. `Time` - 583 edges
2. `Image` - 447 edges
3. `Task` - 230 edges
4. `Interface` - 186 edges
5. `Module` - 182 edges
6. `ObservationList` - 169 edges
7. `DataProvider` - 168 edges
8. `Event` - 156 edges
9. `ImageType` - 117 edges
10. `Comm` - 114 edges

## Surprising Connections (you probably didn't know these)
- `Comm` --references--> `Comm responsibility: Method calls (via Proxy)`  [EXTRACTED]
  pyobs/comm/comm.py → docs/source/api/comm.rst
- `Comm API doc (pyobs.comm)` --references--> `Comm`  [EXTRACTED]
  docs/source/api/comm.rst → pyobs/comm/comm.py
- `Comm` --references--> `Comm responsibility: Discovery (clients_with_interface)`  [EXTRACTED]
  pyobs/comm/comm.py → docs/source/api/comm.rst
- `Comm` --references--> `Comm responsibility: Events (broadcast typed events)`  [EXTRACTED]
  pyobs/comm/comm.py → docs/source/api/comm.rst
- `Comm API doc (pyobs.comm)` --references--> `DummyComm`  [EXTRACTED]
  docs/source/api/comm.rst → pyobs/comm/dummy/dummycomm.py

## Import Cycles
- 3-file cycle: `pyobs/robotic/scheduler/merits/__init__.py -> pyobs/robotic/scheduler/merits/interval.py -> pyobs/robotic/scheduler/merits/merit.py -> pyobs/robotic/scheduler/merits/__init__.py`
- 3-file cycle: `pyobs/robotic/scheduler/merits/__init__.py -> pyobs/robotic/scheduler/merits/pernight.py -> pyobs/robotic/scheduler/merits/merit.py -> pyobs/robotic/scheduler/merits/__init__.py`
- 3-file cycle: `pyobs/robotic/scheduler/merits/__init__.py -> pyobs/robotic/scheduler/merits/beforetime.py -> pyobs/robotic/scheduler/merits/merit.py -> pyobs/robotic/scheduler/merits/__init__.py`
- 3-file cycle: `pyobs/robotic/scheduler/merits/__init__.py -> pyobs/robotic/scheduler/merits/constant.py -> pyobs/robotic/scheduler/merits/merit.py -> pyobs/robotic/scheduler/merits/__init__.py`
- 3-file cycle: `pyobs/robotic/scheduler/merits/__init__.py -> pyobs/robotic/scheduler/merits/aftertime.py -> pyobs/robotic/scheduler/merits/merit.py -> pyobs/robotic/scheduler/merits/__init__.py`
- 3-file cycle: `pyobs/robotic/scheduler/merits/__init__.py -> pyobs/robotic/scheduler/merits/follow.py -> pyobs/robotic/scheduler/merits/merit.py -> pyobs/robotic/scheduler/merits/__init__.py`
- 3-file cycle: `pyobs/robotic/scheduler/merits/__init__.py -> pyobs/robotic/scheduler/merits/random.py -> pyobs/robotic/scheduler/merits/merit.py -> pyobs/robotic/scheduler/merits/__init__.py`
- 3-file cycle: `pyobs/robotic/scheduler/merits/__init__.py -> pyobs/robotic/scheduler/merits/timewindow.py -> pyobs/robotic/scheduler/merits/merit.py -> pyobs/robotic/scheduler/merits/__init__.py`
- 3-file cycle: `pyobs/robotic/scheduler/merits/__init__.py -> pyobs/robotic/scheduler/merits/transit.py -> pyobs/robotic/scheduler/merits/merit.py -> pyobs/robotic/scheduler/merits/__init__.py`
- 3-file cycle: `pyobs/robotic/observation.py -> pyobs/robotic/task.py -> pyobs/robotic/storage/observationarchive.py -> pyobs/robotic/observation.py`

## Hyperedges (group relationships)
- **GitHub Actions CI workflows all standardized on uv + Python 3.13** — github_workflows_pypi, github_workflows_pyrefly, github_workflows_pytest, github_workflows_pytest_integration, github_workflows_ruff [EXTRACTED 1.00]
- **Comm implementations (XmppComm, LocalComm, DummyComm) fulfilling the Comm interface** — pyobs_comm_comm_comm, pyobs_comm_xmpp_xmppcomm_xmppcomm, pyobs_comm_local_localcomm_localcomm, pyobs_comm_dummy_dummycomm_dummycomm [EXTRACTED 1.00]
- **Cluster of late-July 2026 fixes moving CPU-bound/blocking work off the asyncio event loop** — changelog_scheduler_event_loop_blocking, changelog_vfs_write_image_threading, pyobs_robotic_scheduler__executor_run_cpu_bound, pyobs_vfs_vfs_vfs_write_image [INFERRED 0.85]
- **Robotic scheduling pipeline: TaskArchive -> Scheduler -> ObservationArchive -> Mastermind -> Script** — docs_source_api_robotic_index_taskarchive, docs_source_api_robotic_index_scheduler_module, docs_source_api_robotic_index_observationarchive, docs_source_api_robotic_index_mastermind_module, docs_source_api_robotic_index_script [EXTRACTED 1.00]
- **Scheduler evaluation pattern: DataProvider supplies context to Constraint and Merit each time slot** — docs_source_api_robotic_scheduling_dataprovider, docs_source_api_robotic_scheduling_constraint, docs_source_api_robotic_scheduling_merit, docs_source_api_robotic_scheduling_observationarchiveevolution [EXTRACTED 0.90]
- **Runtime context injection: PrivateAttrMixin properties (comm/vfs/observer/location/timezone) shared by Object and BaseModel subclasses** — docs_source_api_robotic_serialization_privateattrmixin, docs_source_api_object_object, docs_source_api_robotic_serialization_basemodel, docs_source_api_robotic_scripts_script [EXTRACTED 0.90]
- **Ejabberd shaper throughput diagnostics** — docs_source_whatsnew_2_0_shaper_rationale, docs_source_recipes_xmpp_diagnostics_benchmark_state_throughput_py, scripts_xmpp_ejabberd_fast_shaper [INFERRED 0.85]
- **Minimal robotic observation system** — docs_source_modules_pyobs_modules_robotic_scheduler, docs_source_modules_pyobs_modules_robotic_mastermind, docs_source_recipes_robotic_script [INFERRED 0.80]
- **Simulated telescope/camera/GUI setup** — docs_source_recipes_simulation_dummycamera, docs_source_modules_pyobs_modules_telescope_dummyradectelescope, docs_source_recipes_simulation_pyobs_gui [INFERRED 0.80]
- **Three XmppComm retry loops sharing jittered backoff, differing in retry budget** — specs_adrs_0008_xmppcomm_safe_send, specs_adrs_0008_xmppcomm_get_capabilities, specs_adrs_0008_xmppcomm_subscribe_with_retry [EXTRACTED 1.00]
- **Three independent pieces required for a standalone pyobs-gui binary** — specs_design_gui_standalone_binary_gui_interactive_login_plan, specs_design_gui_standalone_binary_gui_login_window_plan, specs_design_gui_standalone_binary_gui_widget_plugins_packaging_plan [EXTRACTED 1.00]
- **Interface registry purity-filter regression involving BaseCamera/DummyCamera** — specs_design_external_interfaces_registry_interface_registry, specs_design_external_interfaces_registry_basecamera_dummycamera_bug, specs_design_external_interfaces_registry_dummycamera_module [INFERRED 0.75]
- **Event-loop-blocking diagnosis family (astropy IERS, vendor SDK calls, scheduler CPU-bound)** — specs_steering_astropy_iers_event_loop_stalls_doc, specs_steering_blocking_sdk_calls_must_not_run_on_the_event_loop_doc, specs_steering_scheduler_cpu_bound_merit_evaluation_stalls_event_loop_doc [INFERRED 0.85]

## Communities (449 total, 37 thin omitted)

### Community 0 - "FlatField"
Cohesion: 0.10
Nodes (17): IFilters, Any, The module can change filters in a device., Set the current filter. Args: filter_name: Name of filter to set. Raises:…, Any, Initializes the mixin. Args: filters: Filter wheel module. filter: Filter to…, FlatField, Any (+9 more)

### Community 1 - "LcoTaskArchive"
Cohesion: 0.09
Nodes (16): LcoTaskArchive, Any, Returns a list of schedulable tasks and projects Returns: List of schedulable…, Scheduler for using the LCO portal, Creates a new LCO scheduler. Args: url: URL to portal token: Authorization…, Returns time when last time any tasks changed., Returns list of projects from the LCO portal., Returns list of schedulable tasks. Returns: List of schedulable tasks (+8 more)

### Community 2 - "Task"
Cohesion: 0.03
Nodes (79): Constraint, Any, ndarray, SkyCoord, Returns a boolean mask of candidates passing this constraint. Default…, MoonIlluminationConstraint, Moon illumination constraint., MoonSeparationConstraint (+71 more)

### Community 3 - "Module"
Cohesion: 0.03
Nodes (60): AbstractEventLoop, The Comm object is responsible for all communication between modules (see…, Modules for performing flatfields. TODO: write doc, FlatFieldPointing, Module for pointing a telescope., Move telescope to pointing., Module, MultiModule (+52 more)

### Community 4 - "benchmark_state_throughput.py"
Cohesion: 0.13
Nodes (32): attach_module(), env_config(), main(), make_comm(), maybe_register(), open_publisher(), Any, Benchmark pyobs's XMPP state-push (XEP-0060) and RPC (XEP-0009)… (+24 more)

### Community 5 - "OffsetResult"
Cohesion: 0.12
Nodes (20): ITelescope, The module controls a telescope., Any, Initializes a new base pointing. Args: telescope: Telescope to use. pipeline:…, ApplyAltAzOffsets, EarthLocation, Apply offsets from a given image to a given telescope., Take the pixel offsets stored in the meta data of the image and apply them to… (+12 more)

### Community 6 - "Image"
Cohesion: 0.03
Nodes (76): MetaClass, Image, CCDData, Create Image from a bytes array containing a FITS file. Args: data: Bytes array…, Create image from FITS file. Args: filename: Name of file to load image from.…, A container class for astronomical image data and associated metadata. This…, Create image from astropy.CCDData. Args: data: CCDData to create image from.…, Load Image from HDU list. Args: data: HDU list. Returns: Image. (+68 more)

### Community 7 - "test_mastermind.py"
Cohesion: 0.09
Nodes (49): Mastermind, Any, Returns FITS header for the current status of this module. Args: namespaces: If…, Mastermind for a full robotic mode., make_dynamic_task(), make_mock_vfs(), asyncio, integration (+41 more)

### Community 8 - "test_presence.py"
Cohesion: 0.05
Nodes (51): ModuleOpenedEvent, Event to be sent when a module has opened., ModuleLocation, _FakeProxyContext, make_xmpp_comm(), asyncio, Tests for Phase 2.5 Presence and Capabilities implementation., Module.open() passes empty string for label when _label is None. (+43 more)

### Community 9 - "ImageProcessor"
Cohesion: 0.03
Nodes (71): Some info about :class:`pyobs.images.Image`., ImageProcessor, Any, Init new image processor. Args: on_error: How the pipeline should handle an…, The error handling mode for this step., Processes an image. Args: image: Image to process. Returns: Processed image., Resets state of image processor, Any (+63 more)

### Community 10 - "XmppComm"
Cohesion: 0.03
Nodes (47): Any, Handles an event. Args: msg: Received XMPP message. node: pubsub node id the…, Safely send an XMPP message. Args: method: Method to call. *args: Parameters…, A Comm class using XMPP. This Comm class uses an XMPP server (e.g. `ejabberd…, Fetch the current item for *node* and dispatch it to *callback*. Called when a…, Store published capabilities for inclusion in disco#info responses., Return this client's own published capabilities., Fetch and deserialize capabilities for a remote module's interface. Retries… (+39 more)

### Community 11 - "Interface"
Cohesion: 0.03
Nodes (112): ABC, IAbortable, Any, Abort current actions., The module has an abortable action., IAutonomous, The module does some autonomous actions, mainly used for warnings to users., Binning (+104 more)

### Community 12 - "DummyCamera"
Cohesion: 0.13
Nodes (8): DummyCamera, Any, Header, NDArray, Table, Update cached telescope position from IPointingRaDec state., Returns current solar altitude in degrees, or -18 if no observer., A dummy camera for testing.

### Community 13 - "utils/test_http.py"
Cohesion: 0.16
Nodes (29): MonkeyPatch, make_response(), make_session(), asyncio, Test __wrapped__ directly (bypasses tenacity decorator)., Error message contains the HTTP status code, not the response body., Create a mock aiohttp response., params etc. are baked into the "next" URL by the server -- passing them again… (+21 more)

### Community 14 - "utils/exceptions.py"
Cohesion: 0.05
Nodes (41): PipelineCamera, Any, A virtual camera based on an image pipeline., Creates a new pipeline cammera., Grabs an image and returns reference. Args: broadcast: Broadcast existence of…, Exception, Declare that the given PyobsError types (and their subclasses) fire often…, Watch for repeated occurrences of exc_type -- optionally scoped to a specific… (+33 more)

### Community 15 - "VirtualFileSystem"
Cohesion: 0.08
Nodes (23): Any, DataFrame, HDUList, Convenience function for writing an Image to a FITS file. Args: filename: Name…, Convenience function for writing an Image to a FITS file. Args: filename: Name…, Convenience function for writing bytes to a file. Args: filename: Name of file…, Convenience function for reading a CSV file into a DataFrame. Args: filename:…, Convenience function for writing a CSV file from a DataFrame. Args: filename:… (+15 more)

### Community 16 - "BackendTaskArchive"
Cohesion: 0.09
Nodes (15): BackendTaskArchive, Any, ClientSession, Fetch tasks from backend., Returns time when last time any tasks changed (as observed by this archive).…, Returns list of projects. Returns: List of projects., Returns list of schedulable tasks. Returns: List of schedulable tasks, Returns the task with the given ID. Returns: Task with given ID. (+7 more)

### Community 17 - "Unit"
Cohesion: 0.10
Nodes (28): Enumerator for canonical physical units used on the wire. Attributes: DEGREES:…, The equivalent astropy.units unit, for code that needs to build a Quantity., Unit, _extract_unit(), _interface_unit_hints(), Any, Return Unit annotations from the abstract interface declaration for method_name., Convert annotated float parameters to astropy Quantities before the method… (+20 more)

### Community 18 - "DummyRoof"
Cohesion: 0.05
Nodes (48): pyobs.modules.roof (doc), BaseDome, BaseRoof, DummyRoof, WeatherState, DummyRoof, Any, Get the percentage the roof is open. (+40 more)

### Community 19 - "mixins/test_fitsheader.py"
Cohesion: 0.13
Nodes (48): make_image(), make_module(), asyncio, A peer raising a non-RemoteError -- e.g. a malformed IFitsHeaderBefore/After…, test_add_fits_headers_adds_frame_number_when_enabled(), test_add_fits_headers_sets_day_obs_as_calendar_day_when_night_obs_disabled(), test_add_fits_headers_sets_extname_and_static_headers(), test_add_fits_headers_sets_location_headers() (+40 more)

### Community 20 - "Event"
Cohesion: 0.06
Nodes (43): Event, Base class for all events., DataType, TypedDict, DataType, TypedDict, DataType, TypedDict (+35 more)

### Community 21 - "PipelineMixin"
Cohesion: 0.08
Nodes (23): PipelineMixin, Any, Mixin for a module that needs to implement an image pipeline., Initializes the mixin. Args: steps: Pipeline steps to run on images. archive:…, Whether the given class declares an `archive` parameter anywhere in its…, Resets all previous state of the involved image processors., Pipeline, Any (+15 more)

### Community 22 - "AstrometryDotNet"
Cohesion: 0.04
Nodes (41): ImageProcessor on_error kwarg / per-step error handling, Astrometry processors doc, AstrometryDotNet (astrometry processor), Astrometry, Finds astrometric solution to a given image. Args: image: Image to analyse.…, Base class for astrometry processors, AstrometryDotNet, Any (+33 more)

### Community 23 - "test_flatfielder.py"
Cohesion: 0.08
Nodes (60): make_flatfielder(), make_observer(), make_twilight_observer(), asyncio, parametrize, Regression test for #481: median == bias_level used to raise ZeroDivisionError., Observer stub returning a constant solar altitude for every sun_altaz() call., Observer stub distinguishing the first (now) vs second (+10min) sun_altaz()… (+52 more)

### Community 24 - "LocalComm"
Cohesion: 0.07
Nodes (24): LocalComm, Any, Store capabilities locally., Return this client's own published capabilities., Fetch capabilities from a remote module., Store presence state and dispatch to all subscribers., Return presence state of a connected module., Announce this module to already-connected peers, mirroring XmppComm's presence-… (+16 more)

### Community 25 - "tests/test_events.py"
Cohesion: 0.05
Nodes (56): Comm API doc (pyobs.comm), Events API doc (pyobs.events), BadWeatherEvent, Event to be sent on bad weather., Create Event from a dictionary. Args: obj_dict: JSON string for event. Returns:…, ExposureStatusChangedEvent, Any, Event to be sent, when the exposure status of a device changes. (+48 more)

### Community 26 - "test_lco_http.py"
Cohesion: 0.09
Nodes (44): Camera, CameraType, ConfigurationType, Enclosure, Instrument, InstrumentType, Mode, ModeType (+36 more)

### Community 27 - "DummySolarTelescope"
Cohesion: 0.17
Nodes (10): DummySolarTelescope, Any, Moves to and continuously tracks a Heliocentric Polar (mu, psi) coordinate., Moves to and continuously tracks a Heliographic Stonyhurst (lon, lat)…, Moves to and continuously tracks a Helioprojective (theta_x, theta_y)…, Background task: while a solar-relative target is active, keeps the simulated…, A dummy telescope dedicated to solar pointing (Heliocentric Polar/Heliographic…, Converts Heliocentric Polar (mu, psi) to (ra, dec) in degrees, ICRS. Mirrors… (+2 more)

### Community 28 - "DummyRaDecTelescope"
Cohesion: 0.07
Nodes (29): AltAzOffsetState, IOffsetsAltAz, Any, DEGREES, The module supports Alt/Az offsets, usually combined with…, Move an Alt/Az offset. Args: dalt: Altitude offset in degrees. daz: Azimuth…, IOffsetsRaDec, Any (+21 more)

### Community 29 - "WindowingWidget"
Cohesion: 0.05
Nodes (14): BinningWidget, DataDisplayWidget, PrimaryHDU, Slot, Select path for auto-saving., ExposeWidget, Slot, ExposureTimeWidget (+6 more)

### Community 30 - "Interfaces (pyobs.interfaces) API doc"
Cohesion: 0.04
Nodes (53): Interfaces (pyobs.interfaces) API doc, IAbortable, IAcquisition, IAutoFocus, IAutoGuiding, IAutonomous, IBinning, ICalibrate (+45 more)

### Community 31 - "test_control.py"
Cohesion: 0.13
Nodes (42): ParallelRunner, Script for running other scripts in parallel., Script for running a sequence of other scripts., SequentialRunner, AlwaysRunScript, NeverRunScript, Any, asyncio (+34 more)

### Community 32 - "SolarElevationConstraint"
Cohesion: 0.15
Nodes (29): AtNightConstraint, Solar elevation constraint., SolarElevationConstraint, constraint(), data(), observer(), asyncio, fixture (+21 more)

### Community 33 - "dummycamera.py"
Cohesion: 0.03
Nodes (62): DataSequenceState, ExposureState, IExposure, The module controls a camera., ImageTypeState, FitsHeaderMixin, ImageFitsHeaderMixin, Any (+54 more)

### Community 34 - "WeatherSensors"
Cohesion: 0.13
Nodes (15): Any, Return value for given sensor. Args: station: Name of weather station to get…, Set a simulated sensor's value, for use in tests and simulations. Args: sensor:…, Any, ClientSession, WeatherApi, Enumerator for sensors of a weather station. Attributes: TIME: Time of…, WeatherSensors (+7 more)

### Community 35 - ".set_exposure_time"
Cohesion: 0.50
Nodes (3): Any, SECONDS, Set the exposure time in seconds. Args: exposure_time: Exposure time in…

### Community 36 - "Future"
Cohesion: 0.08
Nodes (36): Wait until all devices are in one of the given motion states. Args: abort:…, Run script. Raises: InterruptedError: If interrupted, acquire_lock(), event_wait(), Future, Any, Lock, Sets a new timeout for the method call. Cancels any existing timeout handle and… (+28 more)

### Community 37 - "test_localcomm_state.py"
Cohesion: 0.09
Nodes (28): asyncio, fixture, Tests for LocalComm state, capabilities, and presence., set_presence stores and get_client_state retrieves., Default presence is READY with no error string., subscribe_presence fires callback immediately with the current presence state., subscribe_presence callback is called whenever presence changes., Reset LocalNetwork singleton before each test. (+20 more)

### Community 38 - "xmppcomm.py"
Cohesion: 0.05
Nodes (59): Serialize a return value to…, return_to_xml(), _dataclass_to_xml(), _event_schema_to_xml(), _interface_schema_to_xml(), _parse_scalar(), Any, Element (+51 more)

### Community 39 - "test_follow.py"
Cohesion: 0.24
Nodes (17): AltAzState, get_coords(), Gets coordinates from object Args: obj: Object to fetch coordinates from. mode:…, _FollowingDevice, asyncio, Tests for FollowMixin's use of max_age when reading a followed device's…, A None from get_coords() (stale or never-published) must hit the existing…, Whether from "never published" or max_age making a stale value look absent,… (+9 more)

### Community 40 - "LcoTask"
Cohesion: 0.07
Nodes (33): LcoRequest, LcoSchedulableRequest, ConfigStatus, LcoTask, Any, Target, Returns observation_type of this task. Returns: observation_type of this task., Whether this task is allowed to start later than the user-set time, e.g., for… (+25 more)

### Community 41 - "SkyOffsets"
Cohesion: 0.13
Nodes (18): BaseCoordinateFrame, Angle, SkyCoord, Returns separatation between both coordinates, either in their own or a given…, Calculates spherical offset from first coordinate to second. Args: frame:…, Args: frame: Coordinate frame to use, or None to use coordinates' own frames.…, SkyOffsets, Any (+10 more)

### Community 42 - "test_xmpp_event_subscriptions.py"
Cohesion: 0.12
Nodes (23): _named_module(), Integration tests for explicit pubsub event subscriptions. Covers…, Registering a handler after a peer is already online must still result in a…, After the last handler for an event class is removed, no further events must…, Registering a handler for a local event (e.g.…, Local events must be unaffected by moving regular events onto the shared pubsub…, After a subscriber restarts (new session, same bare JID), it must resume…, Minimal module stub with a *real* name matching the comm's own JID user --… (+15 more)

### Community 43 - "Comm"
Cohesion: 0.04
Nodes (33): Comm responsibility: Discovery (clients_with_interface), Comm responsibility: Events (broadcast typed events), Comm, Any, ProxyType, setter, Returns object directly if it is of given type. Otherwise get proxy of client…, Backend hook, called when a proxy exists but doesn't implement obj_type.… (+25 more)

### Community 44 - "test_transitimaging.py"
Cohesion: 0.10
Nodes (29): model_validator, Self, Merit function for observing transits., Returns the time of the next mid-transit., Returns the time until which observations should run: mid-transit + duration/2…, TransitMerit, Configuration, Regression test for the bug that motivated extra="forbid" on the imaging config… (+21 more)

### Community 45 - "robotic/test_scheduler.py"
Cohesion: 0.11
Nodes (47): _class_accepts_param(), Whether the class configured in `config` (a dict with a "class" key, or an…, Scheduler, DummyTask, make_async_gen(), make_obs(), make_scheduler(), asyncio (+39 more)

### Community 46 - "StandAlone"
Cohesion: 0.10
Nodes (38): pyobs.modules.test (doc), StandAlone, Quickstart (doc), pyobs-core (pip package), Test modules. TODO: write doc, Example module that only logs the given message forever in the given interval., Thread function for async processing., StandAlone (+30 more)

### Community 47 - "HttpFileCache"
Cohesion: 0.15
Nodes (9): HttpFileCache, Response, Handles OPTIONS access to /{filename} for CORS preflight requests. Args:…, Handles GET access to /{filename} and returns image. Args: request: Request to…, Handles PUSH access to /, stores image and returns filename. Args: request:…, A file cache based on a HTTP server., Whether the server is started., Raises HTTPUnauthorized if a token is configured and the request doesn't carry… (+1 more)

### Community 48 - "_SepAperturePhotometry"
Cohesion: 0.15
Nodes (11): Any, floating, NDArray, Table, since SEP sums up whole pixels, we need to do the same on an image of ones for…, _SepAperturePhotometry, asyncio, fixture (+3 more)

### Community 49 - "test_stellarexptime.py"
Cohesion: 0.11
Nodes (34): ndarray, Find the brightest star near the image centre by fitting a 2D Gaussian. Args:…, Determines exposure time by finding a star near the image centre and adjusting…, Determine the optimal exposure time. Returns: Optimal exposure time in seconds., StellarExposureTimeProvider, attach_proxies(), make_camera_mocks(), make_image() (+26 more)

### Community 50 - "RuntimeError"
Cohesion: 0.06
Nodes (30): Exposure Time estimators doc, ExpTimeEstimator (exptime processor base), StarExpTimeEstimator (exptime processor), ExpTime, ExpTimeEstimator, Any, Estimate exposure time., Init new exposure time estimator. (+22 more)

### Community 51 - "RPC"
Cohesion: 0.09
Nodes (21): fault_to_xml(), params_to_xml(), Any, ClientXMPP, Element, Exception, Parse <fault> and return (exception_qualified_name, message)., RPC wrapper around XEP-0009 using pyobs 2.0 payload encoding (urn:pyobs:rpc:1). (+13 more)

### Community 52 - "WindowCapabilities"
Cohesion: 0.14
Nodes (27): ModuleCapabilities, WindowCapabilities, make_module(), Minimal module stub satisfying what XmppComm needs on connect. IModule must be…, get_capabilities_from_disco(), Integration tests for Phase 2.5 Presence and Discovery. Requires a live…, LOCAL state must arrive as away presence., Module.set_state() must automatically push presence — no explicit call. (+19 more)

### Community 53 - "test_shellcommand.py"
Cohesion: 0.10
Nodes (29): ParserState, Any, Enum, ShellCommand, ShellCommandResponse, asyncio, test_command_number_increments(), test_execute_invalid_param() (+21 more)

### Community 54 - "Calibration"
Cohesion: 0.10
Nodes (18): Calibration, Calibrate an image. Args: image: Image to calibrate. Returns: Calibrated image., Calibrate an image using master bias, dark, and flat frames fetched from an…, Find master calibration frame for given parameters using a cache. Args:…, _CCDDataCalibrator, CCDData, ConcreteArchive, mock_image() (+10 more)

### Community 55 - "object.py"
Cohesion: 0.14
Nodes (21): BackgroundTask, Any, :class:`~pyobs.object.Object` is the base for almost all classes in *pyobs*. It…, Add a new function that should be run in the background. MUST be called in…, make_task(), asyncio, Too many fast failures calls parent.quit() when restart=True., Too many fast failures with restart=False just stops without calling quit. (+13 more)

### Community 56 - "Publisher"
Cohesion: 0.11
Nodes (18): CsvPublisher, Any, DataFrame, Initialize new CSV publisher. Args: filename: Name of file to log in., Publish the given results. Args: **kwargs: Results to publish., Return data that has so far been published., LogPublisher, Any (+10 more)

### Community 57 - "test_startup_gating.py"
Cohesion: 0.12
Nodes (20): _AbortableModule, Any, asyncio, parametrize, Tests for the ModuleState.STARTING guard in Module.execute() and the…, Minimal test module with one guarded (non-whitelisted) RPC method., Module implementing IStartStop, whose abstract `start(**kwargs)` RPC method has…, A freshly constructed module hasn't been started yet. (+12 more)

### Community 58 - "test_autoguiding.py"
Cohesion: 0.20
Nodes (32): make_guiding(), make_image(), asyncio, _state_for(), test_auto_guiding_sleeps_when_disabled(), test_auto_guiding_takes_and_processes_image_when_enabled(), test_get_fits_header_after_includes_statistics(), test_get_fits_header_before_reports_closed_loop() (+24 more)

### Community 59 - "Proxy"
Cohesion: 0.08
Nodes (20): Comm responsibility: Method calls (via Proxy), Proxy, Any, Signature, Execute a method on the remote client. Args: method: Name of method to call.…, Create local methods for the remote client., Function wrapper for remote calls. Args: method: Name of method to wrap.…, Called by Comm whenever a new state arrives. Not intended to be called directly… (+12 more)

### Community 60 - "FilenameFormatter"
Cohesion: 0.05
Nodes (51): Format filename with given formatter., Any, Save an image to the virtual file system and optionally broadcast a…, Init an image processor that broadcasts an image Args: filename: Filename to…, Initialize processor., Broadcast image. Args: image: Image to broadcast. Returns: Original image., Save, CreateFilename (+43 more)

### Community 61 - "test_basevideo.py"
Cohesion: 0.13
Nodes (43): make_basevideo(), make_request(), asyncio, BaseVideo must forward fits_header_timeout to ImageFitsHeaderMixin, not swallow…, _route_paths(), test_activate_camera_from_inactive_calls_hook(), test_activate_camera_when_already_active_skips_hook(), test_active_update_deactivates_after_sleep_timeout() (+35 more)

### Community 62 - "test_yaml_archives.py"
Cohesion: 0.24
Nodes (28): make_obs(), make_obs_archive(), make_task(), make_task_archive(), asyncio, Verify observations are actually written to disk in valid YAML., test_add_and_load_observations(), test_add_empty_list_is_noop() (+20 more)

### Community 63 - "test_schedulewriter.py"
Cohesion: 0.12
Nodes (24): InstrumentLocation, ConfigDB, LcoScheduleWriter, Any, Scheduler for using the LCO portal, Creates a new LCO scheduler. Args: portal: Portal to use. configdb: ConfigDB to…, Add the list of scheduled tasks to the schedule. Args: tasks: Scheduled tasks., Clear schedule after given start time. Args: start_time: Start time to clear… (+16 more)

### Community 64 - "FlatFielder"
Cohesion: 0.08
Nodes (23): ICamera, The module controls a camera., ExposureInfo, NamedTuple, Info about a running exposure., FlatFielder, Enum, Calls next step in state machine. Args: telescope: Telescope to use. camera:… (+15 more)

### Community 65 - "IExposure"
Cohesion: 0.06
Nodes (34): Comm._get_client, ADR-0001: Check Interface.state by own declaration, not inheritance, Composite interfaces inheriting stateful bases (ICamera, IDome, ITelescope, ...), Interface.capabilities (ClassVar), Interface.has_own_state(), Interface.state (ClassVar), XmppComm disco#info feature registration, ADR-0006: Proxy.wait_for_state() returns None on timeout (+26 more)

### Community 66 - "Telegram"
Cohesion: 0.13
Nodes (19): CallbackContext, Any, Save storage file. Args: context: Telegram context., Is user authorized? Args: context: Telegram context. user_id: ID of user.…, Store new user in auth database. Args: context: Telegram context. user_id: ID…, Handle /start command. Args: update: Message to process. context: Telegram…, Handle /exec command. Args: update: Message to process. context: Telegram…, Handle click on buttons. Args: update: Message to process. context: Telegram… (+11 more)

### Community 67 - "DynamicTarget"
Cohesion: 0.05
Nodes (54): DynamicTarget, SkyCoord, Target, Pick the best available target given current conditions. For static targets…, HeliocentricPolarTarget, SkyCoord, Target, HelioprojectiveTarget (+46 more)

### Community 68 - "TimeDelta"
Cohesion: 0.09
Nodes (44): ConstantMerit, Merit function that returns a constant value., model_validator, Self, Merit function that uses time windows., TimeWindow, TimeWindowMerit, OnDemandScheduler (+36 more)

### Community 69 - "Offsets"
Cohesion: 0.04
Nodes (53): AltAzOffsets, OnSkyDistance, Angle, PixelOffsets, AstrometryOffsets, CorrelationMaxCloseToBorderError, Any, Exception (+45 more)

### Community 70 - ".now"
Cohesion: 0.11
Nodes (26): Observer, TaskSuccess, ObservationArchiveEvolution, date, Observer, Populates the task cache and the one real night (anchored to `start`) up front.…, Freezes observation cache. After this: a task-id miss raises RuntimeError; a…, Returns list of observations for the given task. Args: date: Date of night to… (+18 more)

### Community 71 - "PyObsError"
Cohesion: 0.07
Nodes (31): ADR-0003: Restrict Proxy access to async with, has_proxy() / safe_proxy, Proxy, _ProxyContext.__await__ (removed), specs/design/pyobs_2_0_wire_protocol.md, acl: config block (allow/deny), ADR-0004: Enforce access control on the callee, not the caller, Module.execute() (+23 more)

### Community 72 - "test_proxy.py"
Cohesion: 0.12
Nodes (33): _cooling_state(), make_proxy(), asyncio, Methods from both interfaces are callable., A CoolingState timestamped `age_seconds` in the past., Callers that don't pass max_age see no behavior change, however old the cached…, A future interface whose State dataclass has no `time` field fails loudly at…, Create a Proxy with a mock comm. (+25 more)

### Community 73 - "XEP_0009"
Cohesion: 0.07
Nodes (13): BasePlugin, Expose method to public., Expose method to public., Expose method to public., Small fix for the original XEP_0009 plugin., Route RPC-level errors (e.g. forbidden, item-not-found) through the same…, XEP_0009, A plugin for SleekXMPP, adding a timeout to RPC calls. (+5 more)

### Community 74 - "Scheduler"
Cohesion: 0.11
Nodes (14): Iterator for scheduler items, Iterate over scheduler items, Return schedule item., Find a possible slot for a given filter/binning in the given schedule Args:…, A single item in the flat scheduler, Checks, whether a new scheduler item would overlap an existing item Args:…, Initializes a new scheduler item Args: start: Start time in seconds end: End…, Nice string representation for item (+6 more)

### Community 75 - "PyobsDaemon"
Cohesion: 0.06
Nodes (28): CLI, Initializes a new instance of the CLI class., Overwrite this to set CLI parameters with argparse., Overwrite this to actually run the CLI., Load config from config file, Load config from environment variables., main(), Any (+20 more)

### Community 76 - "test_acquisition.py"
Cohesion: 0.28
Nodes (28): make_acquisition(), make_camera(), make_image(), make_telescope(), asyncio, offsets_frame: 'radec', 'altaz', or None (telescope supports neither offsets…, _state_for(), test_abort_sets_event() (+20 more)

### Community 77 - "test_config.py"
Cohesion: 0.07
Nodes (43): include_parts(), pre_process_yaml(), Any, Replaces blocks of the form {include <source.yaml> <key>} in the loaded config…, Finds anchors ('&') in the included file. Args: filename: name of the file with…, Replaces aliases ('<<: *...') in the main file by the anchor in the included…, Include nested contents from another YAML file. Args: include: dictionary based…, Finds keys that hold an anchor ('&') at the top level (no leading whitespace)… (+35 more)

### Community 78 - "TaskData"
Cohesion: 0.04
Nodes (23): Whether this config can currently run. Returns: True if script can run now., Run script. Raises: InterruptedError: If interrupted, Estimate duration of the dark/bias series., Whether this config can currently run. Returns: True if script can run now., Run script. Raises: InterruptedError: If interrupted, Estimate duration of slewing to the flat-field pointing., Estimate duration of the sky flats. The actual schedule depends on sky…, Whether this config can currently run. Returns: True if script can run now. (+15 more)

### Community 79 - "TaskRunner"
Cohesion: 0.23
Nodes (7): Any, Target, Creates a new LCO scheduler. Args: scripts: External scripts, Checks, whether this task could run now. Args: task: Task to run target:…, Returns reason why task cannot run, or None if it can., Run a task. Args: task: Task to run target: Resolved target for this specific…, TaskRunner

### Community 80 - "Weather"
Cohesion: 0.12
Nodes (27): Any, Return value for given sensor. Args: station: Name of weather station to get…, Returns FITS header for the current status of this module. Args: namespaces: If…, Connection to pyobs-weather., Initialize a new pyobs-weather connector. Args: url: URL to weather station…, Weather, asyncio, test_active_flag_defaults_true_and_tracks_stop() (+19 more)

### Community 81 - "IWindow"
Cohesion: 0.29
Nodes (5): IWindow, Any, The camera supports windows, to be used together with…, Set the camera window. Args: left: X offset of window. top: Y offset of window.…, Do camera settings for given camera.

### Community 82 - "test_csvpicker_scheduler.py"
Cohesion: 0.11
Nodes (30): Any, Runs an async callable to completion on a dedicated worker thread, off the…, run_cpu_bound(), Abstract base class for tasks scheduler., TaskScheduler, _T, make_dynamic_task(), make_vfs() (+22 more)

### Community 83 - "integration/conftest.py"
Cohesion: 0.23
Nodes (13): connect(), make_camera_comm(), make_unopened_comm(), make_xmpp_comm(), fixture, Fixtures shared across all integration tests., Factory fixture: ``await make_xmpp_comm(user)`` returns an open XmppComm for…, Connect a module to LocalComm and return the comm. (+5 more)

### Community 84 - "test_pipeline_on_error.py"
Cohesion: 0.15
Nodes (17): Handle an ImageError raised by this step, when on_error == "error". Override…, ImageError, _NonImageErrorStep, Any, asyncio, _RaisingStep, Marks the image with a header entry, so tests can tell whether a step ran., _TagStep (+9 more)

### Community 85 - "Ring"
Cohesion: 0.14
Nodes (9): integer, Any, floating, NDArray, Estimate pixel guiding offsets from asymmetry of spilled light around a fiber…, Init an image processor that adds the calculated offset. Args: fibers:…, Processes an image and sets x/y pixel offset to reference in offset attribute.…, Ring (+1 more)

### Community 86 - "loaded_pyobs_packages"
Cohesion: 0.40
Nodes (9): loaded_pyobs_packages(), Return the version of every loaded ``pyobs``-prefixed distribution. Builds the…, _fake_modules(), test_defaults_to_sys_modules(), test_excludes_non_pyobs_distributions(), test_excludes_not_loaded_top_level_names(), test_returns_loaded_pyobs_distributions(), test_skips_package_not_found() (+1 more)

### Community 87 - "XmppClient"
Cohesion: 0.08
Nodes (20): Any, Disconnect only, instead of slixmpp's default reconnect-in-place. xep_0199's…, Called when the server sends a <stream:error/>, e.g. when this connection gets…, Whether this client was (or is being) kicked because another session connected…, Human-readable reason text sent alongside the conflict stream error, if any., Wait for client to connect. Returns: Success or not., XMPP client for pyobs., Session start event. Args: event: The event sent at session start. (+12 more)

### Community 88 - "test_exception_logging.py"
Cohesion: 0.17
Nodes (24): PresenceCallback, Register a presence callback and deliver the current state immediately., Callback for flat-field class to call with statistics., FocusError, _AbortableModule, Any, asyncio, Exception (+16 more)

### Community 89 - "_DaoBackgroundRemover"
Cohesion: 0.12
Nodes (16): _DaoBackgroundRemover, Any, floating, NDArray, Any, Estimate and subtract the background from an image using a DAOPhot-style…, Init an image processor that removes background from image. Args: sigma: Sigma…, Remove background from image. Args: image: Image to remove background from.… (+8 more)

### Community 90 - "Application"
Cohesion: 0.15
Nodes (23): Application, React to signals and quit the module., Class for initializing and shutting down a pyobs process., make_bare_application(), Any, asyncio, Tests for Application's module_factory path (see specs/plans/gui-interactive-…, Config path: _module is already set in __init__, so _main() must not touch the… (+15 more)

### Community 91 - "DummyComm"
Cohesion: 0.09
Nodes (20): Creates a comm module., DummyComm, Any, A dummy implementation of the Comm interface., Creates a new dummy comm. Args: name: Name to report for this comm. Defaults to…, Always return zero clients., No interfaces implemented., Interfaces are never supported. (+12 more)

### Community 92 - "CallModuleScript"
Cohesion: 0.20
Nodes (17): CallModuleScript, Script for calling a method on a module., asyncio, fixture, script(), test_can_run_false_when_module_unavailable(), test_can_run_true_when_module_available(), test_can_run_uses_interface_for_proxy() (+9 more)

### Community 93 - "ProjectedOffsets"
Cohesion: 0.14
Nodes (20): ProjectedOffsets, Any, floating, NDArray, Processes an image and sets x/y pixel offset to reference in offset attribute.…, Project image along x and y axes and return results. Args: image: Image to…, Compute pixel offsets for guiding by correlating 1D projections of the current…, Initializes a new auto guiding system. (+12 more)

### Community 94 - "test_pyobs_archive.py"
Cohesion: 0.19
Nodes (25): PyobsArchiveFrameInfo, Frame info for pyobs archive., make_archive(), make_frame_dict(), MockResponse, Any, asyncio, test_download_frames_returns_images() (+17 more)

### Community 95 - "HttpFile"
Cohesion: 0.10
Nodes (18): ArchiveFile, Wraps a file in an archive. To be used in combination with pyobs-archive., Creates a new archive file. Args: name: Name of file. mode: Open mode (r/w).…, If in write mode, actually send the file to the archive., HttpFile, Any, Read number of bytes from stream. Args: n: Number of bytes to read. Read until…, Write data into the stream. Args: s: Bytes of data to write. (+10 more)

### Community 96 - "Archive"
Cohesion: 0.11
Nodes (15): Any, Init a new image calibration pipeline step. Args: archive: Archive to fetch…, Archive, FrameInfo, Base class for frame infos., Base class for image archives., TypedDict, PyobsArchiveFrameInfoDict (+7 more)

### Community 97 - "application.py"
Cohesion: 0.13
Nodes (14): _disable_iers_auto_download(), GuiApplication, InfluxLogConfig, Any, TypedDict, Initializes a pyobs application. Exactly one of `config`/`module_factory` must…, Derived Application class that uses a Qt GUI. Allows for graceful shutdown in…, Create a new GUI application. (+6 more)

### Community 98 - "FocusSeries"
Cohesion: 0.14
Nodes (11): AutoFocusPoint, FocusSeries, Analyse given image. Args: image: Image to analyse focus_value: Value to fit…, Returns a list of data points., Fit focus from analysed images Returns: Tuple of new focus and its error, Base class for focus series helper classes., PhotometryFocusSeries, Focus series based on source detection. (+3 more)

### Community 99 - "_SourceCatalog"
Cohesion: 0.13
Nodes (12): Any, DataFrame, floating, NDArray, Table, _SourceCatalog, test_filter_detection_flag(), test_filter_detection_flag_default() (+4 more)

### Community 100 - "make_proxy_cm"
Cohesion: 0.21
Nodes (27): make_proxy_cm(), Wrap value in a MagicMock standing in for the async context manager returned by…, make_flatfield(), asyncio, Find the state object set_state() was called with for the given interface., _ready_telescope(), _state_for(), test_abort_sets_event() (+19 more)

### Community 101 - "NewSpectrumEvent"
Cohesion: 0.14
Nodes (11): NewSpectrumEvent, Any, Event to be sent on a new image., Initializes new NewSpectrumEvent. Args: filename: Name of new image file., HDUList, Store spectrum at given destination. Can be overwritten by derived classes to…, Actually do the exposure, should be implemented by derived classes. Args:…, Wrapper for a single exposure. Args: broadcast: Whether or not the new image… (+3 more)

### Community 102 - "Any"
Cohesion: 0.10
Nodes (16): ImageHDU, Any, floating, HDUList, Header, NDArray, setter, Table (+8 more)

### Community 103 - "lco/task.py"
Cohesion: 0.06
Nodes (28): IAcquisition, Any, The module can acquire a target, usually by accessing a telescope and a camera., Acquire target at given coordinates. If no RA/Dec are given, start from current…, Any, Creates a new LCO scheduler. Args: url: URL to portal site: Site filter for…, LcoAutoFocusScript, Auto focus script for LCO configs. (+20 more)

### Community 104 - "test_coordinates.py"
Cohesion: 0.15
Nodes (25): offset_altaz_to_radec(), offset_radec_to_altaz(), EarthLocation, SkyCoord, make_altaz(), make_radec(), SkyCoord, Zero offset returns (0, 0). (+17 more)

### Community 105 - "get_registered_interface"
Cohesion: 0.12
Nodes (22): get_registered_interface(), Look up a registered interface class by name, or None if unknown., All currently-registered interface classes, keyed by name., registered_interfaces(), Tests for the import-time interface registry in pyobs/interfaces/interface.py.…, Re-importing the same interface module twice resolves to the same class object…, Two genuinely different classes claiming the same name must raise TypeError…, Mutating the returned dict must not affect the live registry. (+14 more)

### Community 106 - "Portal"
Cohesion: 0.13
Nodes (12): Portal, Any, Do a GET request on the portal. Args: url: URL to request. Returns: Response…, Submit observations. Args: observations: List of observations to submit., Send report to LCO portal Args: status_id: id of config status status: Status…, Delay re-attempt to send report to LCO portal Args: status_id: id of config…, Fetch schedule from portal. Args: start_before: Task must start before this…, Any (+4 more)

### Community 107 - "LocalArchive"
Cohesion: 0.32
Nodes (26): LocalArchive, Connector class to a local image archive., make_frame_headers(), asyncio, Path, test_download_frames_loads_real_files(), test_download_frames_skips_frames_without_filename(), test_download_headers_returns_header_dicts() (+18 more)

### Community 108 - "Plan: Systematic ejabberd throughput/latency benchmarking"
Cohesion: 0.07
Nodes (28): Blockers found while getting the environment working (2026-07-27), Conclusion on the O(N²) finding: real bug, not a pyobs design problem, Deeper dig: isolating the real mechanism (2026-07-27, same day), Environment, Fifth investigation session (2026-07-28, same day) — found the specific mechanism: an un-re-armed passive socket, First real results (2026-07-27), Fourth live run (2026-07-28, same day) — found the actual mechanism: stuck per-connection Recv-Q on ejabberd's side, Full incident timeline and what's been ruled out (2026-07-27) (+20 more)

### Community 109 - "_PhotUtilAperturePhotometry"
Cohesion: 0.17
Nodes (10): _PhotUtilAperturePhotometry, Table, PhotUtilsPhotometry, Any, Perform photometry using PhotUtils., test_init(), asyncio, test_call_const() (+2 more)

### Community 110 - "Mixins (pyobs.mixins) API doc"
Cohesion: 0.09
Nodes (25): Images (pyobs.images) API doc, ImageProcessor base class, Object base class, Pipeline module (pyobs.modules.image.Pipeline), API index (toctree), ICamera, IStartStop, CameraSettingsMixin (+17 more)

### Community 111 - "Script base class"
Cohesion: 0.09
Nodes (25): IMode, TaskData, AutoFocusScript, CallModuleScript, CasesRunner, ConditionalRunner, ConstSkyflatPriorities, DarkBiasScript (+17 more)

### Community 112 - "ImageWatcher"
Cohesion: 0.19
Nodes (7): CurrentFile, ImageWatcher, Add a file to the file queue. Args: filename (str): Local filename of new file., Can be overwritten by derived classes to do extra processing on files. All…, Can be overwritten by derived classes to do clean up after successful copying.…, Watch for new files and write them to all given destinations. Watches a path…, test_constructor_raises_without_destinations()

### Community 113 - "CommLoggingHandler"
Cohesion: 0.12
Nodes (20): Send an event to all connected modules. Args: event: Event to send.…, CommLoggingHandler, Any, A logging handler that sends all messages through a Comm module., Create a new logging handler. Args: comm: Comm module to use., Send a new log entry to the comm module. Args: rec: Log record to send., comm(), handler() (+12 more)

### Community 115 - "test_dummyradectelescope.py"
Cohesion: 0.24
Nodes (21): TrackingRateCapabilities, make_dummyradectelescope(), asyncio, test_move_altaz_clears_tracked_body(), test_move_altaz_resets_tracking_mode_to_off(), test_move_radec_clears_tracked_body(), test_move_radec_resets_tracking_mode_to_sidereal(), test_move_task_applies_tracking_rate_to_position() (+13 more)

### Community 116 - "ImagingScript"
Cohesion: 0.15
Nodes (9): ImagingScript, Any, Target, Whether this config can currently run. Returns: True, if the script can run now, Run script. Raises: InterruptedError: If interrupted, Returns FITS header for the current status of this module. Args: namespaces: If…, Estimate the duration of this script in seconds., Return the exposure time, computing it dynamically if needed. (+1 more)

### Community 117 - "comm/test_events.py"
Cohesion: 0.18
Nodes (15): asyncio, Tests for Comm.register_event / unregister_event. Covers…, Two independent subscribers for the same event: one tearing down must not un-…, A module that both sends an event (handler-less register_event()) and…, unregister must mirror the exact same derived-events expansion register_event…, Two independent subscribers (e.g. two widget instances for the same event type)…, Once the last handler for an event is unregistered, the event must no longer be…, test_unregister_event_drops_subscribed_role_when_last_handler_removed() (+7 more)

### Community 118 - "MemoryFile"
Cohesion: 0.14
Nodes (9): MemoryFile, Any, A file stored in memory., Open/create a file in memory. Args: name: Name of file. mode: Open mode., Read number of bytes from stream. Args: n: Number of bytes to read, -1 reads…, Write data into the stream. Args: buf: Bytes of data to write., Whether stream is closed., asyncio (+1 more)

### Community 119 - "VFSFile"
Cohesion: 0.12
Nodes (10): Any, Returns content of given path. Args: path: Path to list. kwargs: Parameters for…, Find files by pattern matching. Args: path: Path to search in. pattern: Pattern…, Remove file at given path. Args: path: Path of file to delete. Returns: Success…, Base class for all VFS file classes., Checks, whether a given path or file exists. Args: path: Path to check.…, VFSFile, __getattr__() (+2 more)

### Community 120 - "LocalFile"
Cohesion: 0.13
Nodes (15): LocalFile, Any, Find files by pattern matching. Args: path: Path to search in. pattern: Pattern…, Wraps a local file with the virtual file system., Remove file at given path. Args: path: Path of file to delete. Returns: Success…, Checks, whether a given path or file exists. Args: path: Path to check. root:…, Open a local file. Args: name: Name of file. mode: Open mode. root: Root to…, Returns local path of given path. Args: path: Path to list. kwargs: Parameters… (+7 more)

### Community 121 - "test_version_mismatch.py"
Cohesion: 0.13
Nodes (24): FakeInterface, make_xmpp_comm(), asyncio, LogCaptureFixture, Tests for the mixed-version-fleet diagnostic on interface resolution. Covers…, The raw feature list is cached even for names that get filtered out --…, Base Comm._diagnose_missing_interface returns None -- e.g. LocalComm, which…, Sanity check that ICooling/IModule (used above as real interfaces) still have… (+16 more)

### Community 122 - "CLAUDE.md (repo guide)"
Cohesion: 0.10
Nodes (23): check_coverage.md (coverage gap survey), Coverage Category A: needs live external service/credentials, Coverage Category B: GUI widgets needing a display, Coverage Category C: CLI/app bootstrap, Coverage Category D: dev/test-support tooling, Coverage Category E: real gaps, no external-service/GUI excuse, Cross-repo docs convention (Repos: line + specs/README.md pointer), graphify usage rules for this repo (+15 more)

### Community 123 - "PillowHelper"
Cohesion: 0.15
Nodes (14): Additional Modules index (docs), Image processors index (docs), Annotation processors doc, Calibration processors doc, Circle, Draw a circle on an image, optionally interpreting the center in WCS…, Draws a circle on the image. Args: image: Image to draw on. Returns: Output…, Crosshair (+6 more)

### Community 124 - "FocusModel"
Cohesion: 0.09
Nodes (33): OptimalFocusState, FocusModel, FocusTimeoutError, MissingSensorError, Any, Initialize a focus model. Args: focuser: Name of focuser. weather: Name of…, Returns the optimal focus. Args: filter_name: If given, use this filter name…, The weather station returned an invalid/missing reading -- plausibly transient,… (+25 more)

### Community 125 - "DataCache"
Cohesion: 0.10
Nodes (15): ImageRequest, DataCache, DataCacheEntry, Any, A single entry in the data cache., Delete entry in cache. Args: name: Name of entry to delete., Create a new entry for the data cache Args: name: Name of item data: Data for…, Update time for this item. (+7 more)

### Community 126 - "ImageSourceFilter"
Cohesion: 0.12
Nodes (17): ImageSourceFilter, Any, floating, NDArray, Table, Filters the source table after pysep detection has run Args:…, Filter a source catalog by border distance, quality metrics, and brightness,…, Convert from FITS to numpy conventions for pixel coordinates. (+9 more)

### Community 127 - "test_darkbias.py"
Cohesion: 0.33
Nodes (17): DarkBiasScript, Script for running darks or biases., make_camera(), make_script(), asyncio, Create a mock camera supporting all or some interfaces., Wire up comm mocks for a DarkBiasScript.run call. safe_proxy is used for…, setup_run_comm() (+9 more)

### Community 128 - "Script"
Cohesion: 0.11
Nodes (15): IMode, Any, The module can change modes in a device., Set the current mode. Args: mode: Name of mode to set. group: Name of the group…, ConditionalRunner, Script for running an if condition., Returns FITS header for the current status of this module. Args: namespaces: If…, Estimate duration of the branch that would be run for the current condition. (+7 more)

### Community 129 - "Time"
Cohesion: 0.03
Nodes (84): Modules for robotic mode. TODO: write doc, Initialize a new auto focus system. Args: schedule: Object that can return…, # TODO: add abort (see old robotic/scheduler.py), Observation, ObservationState, StrEnum, Fetch a task from the task archive., Returns the time of the last sunrise. (+76 more)

### Community 130 - "Plan: pyobs-pipeline"
Cohesion: 0.08
Nodes (24): Celery task, Consequences, Django models, Implementation checklist, Log viewing, Open questions, Pages, Pipeline builder (+16 more)

### Community 131 - "Test Localcomm (local)"
Cohesion: 0.18
Nodes (22): make_comm(), asyncio, fixture, Sender also receives its own events., Reset LocalNetwork singleton between tests., #677: a late-joining module must announce itself via ModuleOpenedEvent once…, get_interfaces returns [] when the remote client has no module., reset_network() (+14 more)

### Community 132 - "sourcedetection.py"
Cohesion: 0.13
Nodes (13): Source Detection processors doc, DaophotSourceDetection (detection processor), SepSourceDetection (detection processor), Any, Detect a disk on image. Args: image: Image to use. Returns: Image with new FITS…, Detect a roughly circular bright disk by thresholding and distance transform.…, Init a new simple disk processor. Args: threshold: Threshold to determine if a…, SimpleDisk (+5 more)

### Community 133 - "MotionStatusChangedEvent"
Cohesion: 0.07
Nodes (17): Any, JSON representation of event., String representation of event., Generic from_dict method for derived classes that don't need their own., Any, Any, Any, Initializes a new good weather event. Args: eta: Predicted ETA for when the… (+9 more)

### Community 134 - "MoveAltAzEvent"
Cohesion: 0.11
Nodes (14): DataTypeAltAz, DataTypeRaDec, MoveAltAzEvent, MoveEvent, MoveRaDecEvent, Any, TypedDict, Event to be sent when moving to RA/Dec. (+6 more)

### Community 135 - "test_dummymode.py"
Cohesion: 0.32
Nodes (13): _event_of_type(), make_dummymode(), asyncio, Find the most recent state object set_state() was called with for the given…, Find the send_event() call with an event of the given type., _state_for(), test_init_default_modes(), test_init_park_stop_motion_are_noops() (+5 more)

### Community 136 - "MockWeather"
Cohesion: 0.12
Nodes (23): WeatherSensorReading, MockWeather, Any, Return value for given sensor. Args: station: Name of weather station to get…, Returns FITS header for the current status of this module. Args: namespaces: If…, A mock weather station for testing and simulations., Creates a new mock weather station. Args: good: Initial weather-good state.…, Set the simulated weather-good state, for use in tests and simulations. Fires a… (+15 more)

### Community 137 - "SiderealTarget"
Cohesion: 0.08
Nodes (32): AirmassConstraint, ndarray, SkyCoord, model_validator, Self, SkyCoord, Target, SiderealTarget (+24 more)

### Community 138 - "Grid"
Cohesion: 0.09
Nodes (21): AvoidMoon, GridFilter, Any, RandomizeGrid, Initialize the conversion filter. Args: grid: Upstream grid or filter that…, Abstract base class for grid filters that wrap another GridNode. A GridFilter…, Initialize the frame conversion filter. Args: grid: Upstream grid or filter…, Randomize iteration order by rotating the underlying sequence. For each… (+13 more)

### Community 139 - "test_kiosk.py"
Cohesion: 0.24
Nodes (21): _cancel_after(), _make_image(), make_kiosk(), asyncio, Side effect that raises CancelledError starting from the n-th call., test_camera_thread_captures_and_adjusts_exposure_time(), test_camera_thread_clips_exposure_time_to_minimum(), test_camera_thread_continues_on_file_not_found() (+13 more)

### Community 140 - "pyobs.py"
Cohesion: 0.13
Nodes (11): main(), Any, PyobsCLI, Start process as a daemon. Args: pid_file: Name of PID file., Class for initializing and running pyobs CLI., main(), Any, PyobsWinCLI (+3 more)

### Community 141 - "Robotic recipe (doc)"
Cohesion: 0.17
Nodes (21): pyobs.modules.robotic (doc), Mastermind (module), PointingSeries, Scheduler (module), ScriptRunner, Robotic recipe (doc), AirmassConstraint, BackendObservationArchive (+13 more)

### Community 142 - "Scheduler"
Cohesion: 0.14
Nodes (8): Any, Compares two lists of tasks and returns two lists, containing those that are…, Trigger a re-schedule., Re-schedule when task has started and we can predict its end. Args: event: The…, Reset current task, when it has finished or failed. Args: event: The task…, Re-schedule on incoming good weather event. Args: event: The good weather…, Initialize a new scheduler. Args: scheduler: Scheduler to use. tasks: Task…, Scheduler

### Community 143 - "GuidingStatisticsPixelOffset"
Cohesion: 0.25
Nodes (7): GuidingStatisticsPixelOffset, Calculates RMS of data. Args: data: Data to calculate RMS for. Returns: Tuple…, mock_meta_image(), fixture, test_build_header_to_few_values(), test_end_to_end(), test_get_session_data()

### Community 144 - "test_config_schema.py"
Cohesion: 0.20
Nodes (22): ConfigFieldSchema, ConfigSchema, dataclass_to_schema(), _field_schema(), Any, _pydantic_field_schema(), pydantic_to_schema(), Recursively derive a ConfigSchema from a dataclass type. Handles: plain scalars… (+14 more)

### Community 145 - "Pipeline"
Cohesion: 0.10
Nodes (29): ProgressEvent, Pipeline, Any, Create master bias frame. Args: images: List of raw bias frames. Returns:…, Create master dark frame. Args: images: List of raw dark frames. bias: Bias…, Create master flat frame. Args: images: List of raw flat frames. bias: Bias…, Calibrate a single science frame. Args: image: Image to calibrate. Returns:…, Pipeline based on the astropy package ccdproc. (+21 more)

### Community 146 - "NewImageEvent"
Cohesion: 0.09
Nodes (14): NewImageEvent, Any, Event to be sent on a new image., Initializes new NewImageEvent. Args: filename: Name of new image file.…, Actually do the exposure, should be implemented by derived classes. Args:…, Method that is always called at the very beginning of __expose and can be used…, Wrapper for a single exposure. Args: exposure_time: The requested exposure time…, Add FITS headers in derived classes. Args: image: Image to write FITS headers… (+6 more)

### Community 147 - "RollingTimeAverage"
Cohesion: 0.15
Nodes (16): RollingTimeAverage, Values older than interval are excluded from average., With min_interval, returns None if no values are older than min_interval., With min_interval, returns average if there are values older than min_interval., Only values within the rolling interval are included., add() cleans up values older than interval., test_add_evicts_expired_values(), test_average_clears_old_values() (+8 more)

### Community 148 - "GuidingStatistics"
Cohesion: 0.16
Nodes (8): IN, OUT, GuidingStatistics, Any, Calculates statistics for guiding., Inits a stat measurement session for a client. Args: client: name/id of the…, Add statistics to given header. Args: client: id/name of the client header:…, Adds data to all client measurement sessions. Args: input_data: Image witch…

### Community 149 - "LogEvent"
Cohesion: 0.09
Nodes (17): Send a log message to other clients. Args: entry (LogEvent): Log event to send., _event_role(), Space-separated role(s) ("send", "subscribe", or both) for an event class, for…, LogEvent, Any, Event for log entries., main(), Same double-delivery trigger test as trigger_duplicate.py, but against iagvtsrv… (+9 more)

### Community 151 - "`OBSNUM`: per-night observation counter in FITS headers"
Cohesion: 0.06
Nodes (28): 1. Event-driven frame delivery, not polling, 2. Backpressure: latest-frame-wins, not a queue, 3. Wire format (new — nothing in pyobs streams raw binary today), 4. Capability advertisement: `mjpeg`/`raw`, both `str | None`, on by default, 5. Activate/deactivate wiring, Alternatives considered, `BaseVideo`: raw-frame streaming endpoint, alongside the existing MJPEG live view, Constraint: one module, one job (+20 more)

### Community 152 - "3rd party packages (doc)"
Cohesion: 0.11
Nodes (20): 3rd party packages (doc), Astroplan, Astropy, Astroquery, Cython, LMFIT, matplotlib, NumPy (+12 more)

### Community 153 - "test_basetelescope.py"
Cohesion: 0.10
Nodes (31): OrbitalElements, Any, Starts tracking a body defined by orbital elements. Args: elements: Orbital…, InvalidOrbitalElementsError, _orbital_plane_to_ecliptic_cartesian(), _perifocal_to_radec(), _propagate_elements(), Rotates a perifocal-plane position into heliocentric ecliptic coordinates, then… (+23 more)

### Community 154 - "SSHFile"
Cohesion: 0.12
Nodes (12): Any, VFS wrapper for a file that can be accessed over a SFTP connection., Write data into the stream. Args: b: Bytes of data to write., If in write mode, actually send the file to the SSH server., Returns content of given path. Args: path: Path to list. kwargs: Parameters for…, Open/create a file over a SSH connection. Args: name: Name of file. mode: Open…, For read access, download the file into a local buffer. Raises:…, Read number of bytes from stream. Args: n: Number of bytes to read. Read until… (+4 more)

### Community 155 - "create_rst.py"
Cohesion: 0.33
Nodes (18): create_image_processors_rst(), create_modules_rst(), create_rst_overview(), create_utils_rst(), find_classes_in_modules(), find_python_modules(), find_submodules(), Any (+10 more)

### Community 156 - "test_lcoscript.py"
Cohesion: 0.17
Nodes (18): FakeScript, make_lco_script(), make_request(), Any, asyncio, Minimal script used to verify LcoScript's dispatch., can_run() resolves and delegates to the script named in…, run() delegates to the named script and copies its exptime_done back. (+10 more)

### Community 157 - "SoftBin"
Cohesion: 0.16
Nodes (11): Any, floating, NDArray, Bin a 2D image by averaging non-overlapping blocks, updating relevant FITS…, Init a new software binning pipeline step. Args: binning: Binning to apply to…, Bin an image. Args: image: Image to bin. Returns: Binned image., SoftBin, asyncio (+3 more)

### Community 158 - "AddMask"
Cohesion: 0.21
Nodes (13): AddMask, Any, floating, NDArray, Add mask to image. Args: image: Image to add mask to. Returns: Image with mask, Attach a precomputed mask to an image based on instrument and binning. This…, Init an image processor that adds a mask to an image. Args: masks: Dictionary…, asyncio (+5 more)

### Community 159 - "pyobs/modules/utils/__init__.py"
Cohesion: 0.12
Nodes (9): FluentLogger, Log to fluentd server., Process a new log entry. Args: event: The log event. sender: Name of sender., Utilities TODO: write doc, Matrix, Drain the message queue and send messages one at a time. Sending sequentially…, Process a new log entry. Args: entry: The log event. sender: Name of sender., Enum (+1 more)

### Community 160 - "SkyCoord"
Cohesion: 0.13
Nodes (9): SkyCoord, Return the next point that satisfies all constraints. Iterates underlying…, Convert the next tuple to a SkyCoord. Expects a tuple (x_deg, y_deg) from the…, Transform the next SkyCoord to the target frame. Returns: A SkyCoord…, Yield a point after rotating the underlying grid a random number of times.…, Yield a point after rotating the underlying grid a random number of times.…, Yield the point from the CSV closest to the next grid point. Returns: A point…, Fetch the next point from the underlying grid. Returns: The next point from the… (+1 more)

### Community 161 - "robotic/task.py"
Cohesion: 0.07
Nodes (23): model_serializer, get_class_from_string(), PrivateAttrMixin, EarthLocation, Observer, Get class from a given string. Args: class_name: Name of class as string.…, Location of the observer, derived from :attr:`observer` (there is no separately…, .. note:: Objects must always be opened and closed using… (+15 more)

### Community 162 - "BaseTelescope"
Cohesion: 0.10
Nodes (15): BaseTelescope, _ra_rate_on_sky(), On-sky RA rate in arcsec/sec, i.e. d(RA)/dt * cos(dec) -- matches JPL Horizons'…, Base class for telescopes., Current RA/Dec position in degrees, or None if unknown. Override in subclasses., Actually applies an absolute tracking rate to hardware. Must be implemented by…, Public entry point for external/manual callers. Enforces the SIDEREAL…, Resolves a body name to (ra, dec, ra_rate, dec_rate) -- degrees and arcsec/sec… (+7 more)

### Community 163 - "SepSourceDetection"
Cohesion: 0.16
Nodes (17): Background, Any, floating, NDArray, Initializes a wrapper for SEP. See its documentation for details. Highly…, Find stars in given image and append catalog. Args: image: Image to find stars…, Remove background from image in data. Args: data: Data to remove background…, Detect astronomical sources using SEP (Source Extractor for Python). This… (+9 more)

### Community 164 - "Design"
Cohesion: 0.15
Nodes (12): `comm.py` changes, Design, Node naming, Plan: Explicit pubsub subscriptions for event delivery, Post-merge fixes (review, 2026-08-16), Problem, Publishing (`send_event`, `xmppcomm.py:763`), Removed / unchanged (+4 more)

### Community 165 - "ExpTimeEval"
Cohesion: 0.11
Nodes (15): ExpTimeEval, Any, Observer, Return list of binnings., Return list of filters., Estimate exposure time for given filter Args: solalt: Solar altitude. binning:…, Initialize object with the given time. Args: time: Start time for all further…, Estimates exposure time for a given filter and binning at a given time offset… (+7 more)

### Community 166 - "storage/taskarchive.py"
Cohesion: 0.10
Nodes (12): Creates a new task archive. Args: url: URL of pyobs-robotic-backend. token:…, FileSystemTaskArchive, Any, Task archive based on files., Creates a new filesystem-based task archive. Args: extension: Extension of…, Returns time when last time any blocks changed., Returns list of projects. Returns: List of projects., Returns list of schedulable tasks. Returns: List of schedulable tasks (+4 more)

### Community 167 - "Overview (doc)"
Cohesion: 0.18
Nodes (17): Overview (doc), Access control (ACL), Comm, Events, Interface, Module (base class), Object (base class), Location / astroplan.Observer (+9 more)

### Community 168 - "LogScript"
Cohesion: 0.18
Nodes (12): DebugTriggerScript, Script for a debug trigger., LogScript, Script for logging something., asyncio, Expression has access to 'now' as a datetime., test_debug_trigger_can_run(), test_debug_trigger_sets_triggered() (+4 more)

### Community 169 - "test_imagewatcher.py"
Cohesion: 0.33
Nodes (15): make_fits_bytes(), make_read_write_ctx(), make_watcher(), asyncio, On write failure the file is re-queued and remove is NOT called., test_add_file_queues_filename(), test_add_file_respects_pattern(), test_add_file_skips_non_matching_pattern() (+7 more)

### Community 170 - "fit_hyperbola"
Cohesion: 0.17
Nodes (16): fit_hyperbola(), Fit a hyperbola Args: x_arr: X data y_arr: Y data y_err: Y errors Returns:…, Fit focus from analysed images Returns: Tuple of new focus and its error, make_hyperbola(), ndarray, Generate clean hyperbola data: b * sqrt((x-c)^2/a^2 + 1)., fit_hyperbola recovers the minimum position of a clean hyperbola., fit_hyperbola returns (minimum, variance). (+8 more)

### Community 171 - "FitsHeaderOffsets"
Cohesion: 0.19
Nodes (10): GenericOffset, FitsHeaderOffsets, Any, Compute a 2D offset from FITS header coordinates and store it in image…, Initializes new fits header offsets., Processes an image and sets x/y pixel offset to reference in offset attribute.…, asyncio, test_attribute_validation() (+2 more)

### Community 172 - "test_grab_sequence.py"
Cohesion: 0.29
Nodes (16): make_camera(), asyncio, Tests for BaseCamera.grab_sequence()/abort_sequence(), the IDataSequence…, grab_sequence() must not block for the whole sequence -- see design doc: a…, test_abort_clears_running_sequence(), test_abort_cuts_delay_short(), test_abort_sequence_cuts_delay_short(), test_abort_sequence_lets_current_grab_finish_but_stops_the_rest() (+8 more)

### Community 173 - "binding.py"
Cohesion: 0.23
Nodes (8): fault2xml(), py2xml(), Any, Element, rpcbase64, rpctime, xml2fault(), xml2py()

### Community 174 - "ProjectionFocusSeries"
Cohesion: 0.16
Nodes (11): ProjectionFocusSeries, Any, floating, NDArray, Returns a list of data points., Fit focus from analysed images Returns: Tuple of new focus and its error, Creates a sine window function of the same size as some 1-D array "arr".…, Removes global slopes and fills up bad rows (ybad) or columns (xbad). (+3 more)

### Community 175 - ".get_config_value"
Cohesion: 0.40
Nodes (4): Any, ConfigValue, Returns current value of config item with given name. Args: name: Name of…, Sets value of config item with given name. Args: name: Name of config item.…

### Community 176 - "test_xmppcomm_event_payload.py"
Cohesion: 0.16
Nodes (22): _log_task_exception(), Retrieve and log a background task's exception, if it failed. Results of…, _event_msg(), _EventMsg, _log_event_json(), _make_comm(), asyncio, XmppComm._handle_event must tolerate pubsub notifications without a payload.… (+14 more)

### Community 177 - "test_transit_mastermind.py"
Cohesion: 0.22
Nodes (19): InstrumentConfig, make_transit_merit(), make_transit_observation(), make_transit_task(), asyncio, integration, Mastermind picks up a transit observation and runs it to completion., Mastermind marks transit observation FAILED when runner raises. (+11 more)

### Community 178 - "test_dummyvideo.py"
Cohesion: 0.17
Nodes (15): DummyVideo, Any, A dummy video module for testing — streams simulated noise frames., Creates a new dummy video module. Args: fps: Frames per second to simulate.…, Set the exposure time (frame interval). Args: exposure_time: Exposure time in…, Background task that generates simulated frames., make_dummyvideo(), asyncio (+7 more)

### Community 179 - "test_scheduler_mastermind.py"
Cohesion: 0.21
Nodes (22): make_obs_archive(), make_task(), asyncio, integration, Scheduled observation end - start matches task duration., Full pipeline: scheduler creates observation, mastermind runs it to completion., Full pipeline: mastermind marks observation FAILED when runner raises., MemoryTaskArchive provides tasks to the scheduler correctly. (+14 more)

### Community 180 - "Steering: astropy IERS auto-download blocks event loop"
Cohesion: 0.32
Nodes (8): BaseTelescope._celestial / _update_celestial_headers, Steering: astropy IERS auto-download blocks event loop, iers_offline config flag (stopgap fix), Steering: Blocking vendor SDK calls must never run directly on the event loop, _run_blocking() pattern (pyobs_aravis.araviscamera.AravisCamera), _wait_for_frame() tight-poll wrapper pattern, Steering: OnDemandScheduler.evolve() uncached sunset lookup stalls event loop, ObservationArchiveEvolution.evolve() Time.night_obs() bug (fixed via memoization)

### Community 181 - "Kiosk"
Cohesion: 0.11
Nodes (8): Kiosk, Any, Response, Thread for taking images., A kiosk mode for a pyobs camera that takes images and published them via HTTP., Initializes file cache. Args: camera: Camera to use for kiosk mode. port: Port…, Handles access to /* and returns a specified image. Args: request: Request to…, Whether the server is started.

### Community 182 - ".get_object"
Cohesion: 0.10
Nodes (20): ObjectClass, PydanticModel, create_object(), get_object(), get_safe_object(), Any, ProxyType, Calls get_object in a safe way and returns None, if an exceptions thrown. Args:… (+12 more)

### Community 183 - ".set_focus"
Cohesion: 0.40
Nodes (4): Any, MM, Sets new focus. Args: focus: New focus value in mm. Raises:…, Sets focus offset. Args: offset: New focus offset in mm. Raises: ValueError: If…

### Community 184 - "Merit"
Cohesion: 0.15
Nodes (15): AfterTimeMerit, BeforeTimeMerit, ConstantMerit, DataProvider, FollowMerit, IntervalMerit, ObservationArchiveEvolution wraps ObservationArchive with per-run caching (avoid repeated HTTP requests) and lookahead simulation (evolve() records tentative future assignments so IntervalMerit/PerNightMerit see them and avoid double-scheduling within one run), Merit (+7 more)

### Community 185 - "ejabberd shaper throttling bug (xmpp_socket.erl re-arm) & fix"
Cohesion: 0.21
Nodes (12): XMPP/ejabberd diagnostics recipe (doc), benchmark_state_throughput.py, check_ejabberd_notify.py, delete_pubsub_nodes.py, list_pubsub_nodes.py, Comparing shaper configs (rationale), show_module_info.py, scripts/xmpp/install-ejabberd.sh (+4 more)

### Community 186 - "ImageType"
Cohesion: 0.09
Nodes (17): _CalibrationCache, Any, Set the image type. Args: image_type: New image type., Any, Any, DataFrame, Update files in root directory., ImageType (+9 more)

### Community 187 - "Plan: Make the pydantic config layer reject unknown keys (`extra="forbid"`)"
Cohesion: 0.18
Nodes (10): Decision, Gap: the imaging config models are not covered by this change, Implementation checklist, Latent bug this surfaced (separate from the above), Merged, Plan: Make the pydantic config layer reject unknown keys (`extra="forbid"`), PR review follow-up (github.com/pyobs/pyobs-core/pull/762, thusser), Problem (+2 more)

### Community 188 - "Work Plan"
Cohesion: 0.12
Nodes (16): Dropped items, Phase 0 — Foundations, Phase 1.5 — RPC payload encoding 2.0, Phase 1 — Walking skeleton: prove State end-to-end on one interface, Phase 2.5 — Discovery and Presence, Phase 2 — Audit and design pass (no implementation yet), Phase 3 — Bulk rollout, Phase 4 — Other backends and Presence (+8 more)

### Community 189 - "Plan: `pyobs-gui` TelescopeWidget layout — width floor investigation & design notes"
Cohesion: 0.12
Nodes (16): 1. Make the stacked widget size to the current page, not the widest one, 2. Adopt a width convention for future coordinate-type pages, 3. `QFormLayout::setRowWrapPolicy()` on the individual form pages, 4. Resize-driven reparenting for the four-groupbox row, Capability-driven visibility is handled by toggling pre-built sections on/off, Coordinate-type selection is already a combobox, not tabs, Each coordinate-type page has a fixed, hand-built field set, Filter, Focus, and the offsets rows are structurally duplicated (+8 more)

### Community 190 - "PointingSeries"
Cohesion: 0.20
Nodes (6): PointingSeries, Any, SkyCoord, Module for running pointing series., Initialize a new pointing series. Args: grid: Grid to use for pointing series.…, Run a pointing series.

### Community 191 - "GridNode"
Cohesion: 0.09
Nodes (15): GridNode, Log the last yielded point, if any. Implementations typically delegate to…, Abstract base class for grid nodes. A GridNode implements the Python iterator…, Return iterator self. Returns: The GridNode itself as an iterator., Return the number of points remaining. Returns: Number of points remaining to…, Append the last yielded point back to the underlying sequence. This can be used…, GridPipeline, Any (+7 more)

### Community 192 - "Plan: Make mixin `__init__` composition cooperative, then enforce unrecognized kwargs at `Object.__init__`"
Cohesion: 0.11
Nodes (18): Approach, Critical finding (2026-08-18): PR #776's blast radius isn't scoped by rollout order, Decision, Implementation checklist, Non-goals, Plan: Make mixin `__init__` composition cooperative, then enforce unrecognized kwargs at `Object.__init__`, Problem, Rollout order (proposed, safest first — confirm before starting, not confirmed operational (+10 more)

### Community 193 - "flatfield/test_scheduler.py"
Cohesion: 0.47
Nodes (9): FlatFieldScheduler, Run the flat-field scheduler., make_scheduler_module(), asyncio, setup_flatfield_proxy(), test_abort_sets_event(), test_run_aborts_current_flat_field_when_requested(), test_run_raises_when_already_running() (+1 more)

### Community 194 - "What's New in pyobs 2.0 (doc)"
Cohesion: 0.15
Nodes (14): What's New in pyobs 2.0 (doc), ACL feature (2.0), Capabilities and versioned discovery, Exception handling redesign, External-package interfaces, ICamera/ISpectrograph no longer imply IExposure, IDataSequence, InvocationError / SevereError retired (+6 more)

### Community 196 - "test_schedulereader.py"
Cohesion: 0.15
Nodes (21): LcoScheduleReader, Update list of requests. Args: force: Force update., Fetch schedule from portal. Returns: Dictionary with tasks. Raises: Timeout: If…, Fetch schedule from portal. Args: start_before: Task must start before this…, Returns the active scheduled task at the given time. Args: time: Time to return…, Scheduler for using the LCO portal, make_observation(), make_reader() (+13 more)

### Community 197 - "CatalogCircularMask"
Cohesion: 0.18
Nodes (9): CatalogCircularMask, Any, NDArray, Table, Init an image processor that masks out everything except for a central circle.…, Remove everything outside the given radius from the image. Args: image: Image…, Filter a source catalog by keeping only entries inside a central circle (or…, asyncio (+1 more)

### Community 198 - "Plan: `pyobs-gui` IAutoFocus widget"
Cohesion: 0.29
Nodes (6): Current state (pyobs-core, `develop`), Gap, Open questions, Plan: `pyobs-gui` IAutoFocus widget, Proposed pyobs-core change, Widget design (pyobs-gui)

### Community 199 - "AperturePhotometry"
Cohesion: 0.18
Nodes (12): AperturePhotometry, Base class for aperture photometry processors -- not meant to be used directly,…, Do aperture photometry on given image. Args: image: Image to do aperture…, MockPhotometryCalculator, asyncio, QTable, AperturePhotometry.__init__ is abstract -- concrete calculators…, test_call_invalid_catalog() (+4 more)

### Community 200 - "test_backend_archives.py"
Cohesion: 0.10
Nodes (54): make_obs(), make_obs_archive(), make_task(), make_task_archive(), asyncio, Projects with the backend `public` flag ingest without a strict-model…, time parameter is unused — backend returns cached observations., Backend uses strictly exclusive boundaries (start < time < end). (+46 more)

### Community 201 - "test_basecamera.py"
Cohesion: 0.16
Nodes (17): asyncio, parametrize, DummyCamera's _expose() must raise AbortedError, not some guessed builtin, when…, BaseCamera must forward fits_header_timeout to ImageFitsHeaderMixin, not…, Test basic open/close of BaseCamera., #547: BaseCamera must abort on BadWeatherEvent., #547: a BadWeatherEvent must actually trigger abort() -- exposure + any running…, #672: a BadWeatherEvent must not interrupt a dark/bias sequence -- the shutter… (+9 more)

### Community 202 - "show_module_info.py"
Cohesion: 0.25
Nodes (13): h1(), h2(), inspect_module(), _interface_from_feature(), kv(), main(), _module_state_from_show(), ok() (+5 more)

### Community 203 - "RunningState"
Cohesion: 0.05
Nodes (59): F, AcquisitionAttempt, AcquisitionResult, AcquisitionState, AutoFocusResult, AutoFocusState, IAutoFocus, Any (+51 more)

### Community 204 - "DaophotSourceDetection"
Cohesion: 0.17
Nodes (13): DaophotSourceDetection, Any, floating, NDArray, Table, Initializes a wrapper for photutils. See its documentation for details. Args:…, Find stars in given image and append catalog. Args: image: Image to find stars…, Detect astronomical point sources using a DAOPhot-style algorithm via… (+5 more)

### Community 205 - "robotic"
Cohesion: 0.32
Nodes (13): acquisition, autofocus, dome, flatfield, focuser, imagewriter, robotic, sbig6303e (+5 more)

### Community 206 - "Scheduler module"
Cohesion: 0.17
Nodes (13): Constraint (binary gate), Mastermind module, Merit (continuous ranking), Module layer (pyobs.modules.robotic: Scheduler, Mastermind — full Module subclasses with comm/background tasks) vs robotic layer (pyobs.robotic: Task, Script, Constraint, Merit, archives — Object subclasses or pydantic models, nested config, not modules); rationale: separates long-running orchestration processes from pure data/logic objects, Observation (scheduled task instance), ObservationArchive, Scheduler module, Script (observing logic) (+5 more)

### Community 207 - "BaseModel (pyobs.utils.serialization)"
Cohesion: 0.15
Nodes (13): Task (unit of work), TaskArchive, BackendTaskArchive, LcoTaskArchive, Observation, ObservationState, Task (pydantic model), TaskArchive (+5 more)

### Community 208 - "Decision"
Cohesion: 0.12
Nodes (15): 1. Separate input and output on `Night`, unified as a single `output` parameter, 2. Implement `LocalArchive.upload_frames`, 3. Rename `Night` → `Reduction`, 4. Fix the remaining `Reduction` bugs found alongside, 5. Remove `Reduction.__init__`'s dead `**kwargs: Any`, Blocking: `Night` can't have a different input and output archive, Bug: `LocalArchive.upload_frames` silently discards data, Decision (+7 more)

### Community 209 - "Stellarium"
Cohesion: 0.17
Nodes (6): BaseTransport, Exception, Send coordinates to clients., A stellarium telescope., Stellarium, StellariumProtocol

### Community 210 - "weather.py"
Cohesion: 0.16
Nodes (9): IStartStop, Any, The module can be started and stopped., IWeather, The module acts as a weather station., Any, Weather modules. TODO: write doc, The weather station's API response was malformed or incomplete (missing an… (+1 more)

### Community 211 - "BaseVideo"
Cohesion: 0.07
Nodes (29): IExposureTime, The camera supports exposure times, to be used together with…, BaseVideo, calc_expose_timeout(), LastImage, NextImage, Any, NamedTuple (+21 more)

### Community 212 - "Plan: Widget plugin mechanism + `pyside6-deploy` packaging for `pyobs-gui`"
Cohesion: 0.14
Nodes (14): Consequences, Considered options, Considered options, Deciding which widget to use, without user-side config, Decision, Decision outcome, Implementation checklist, Non-goals (+6 more)

### Community 213 - "Plan: Split archive prefetch from CPU-bound merit evaluation, to unblock a `ProcessPoolExecutor`"
Cohesion: 0.12
Nodes (16): 1. `ObservationArchiveEvolution` — add prefetch + freeze (`observationarchiveevolution.py`), 2. Call prefetch + freeze — `ondemandscheduler.py`, `schedule()`, 3. Confirm zero cache misses before touching the executor, 4. Only after step 3 is clean: swap the executor (`_executor.py`), Consequences, Considered options, Decision, Existing coverage (+8 more)

### Community 214 - ".image_handler"
Cohesion: 0.29
Nodes (4): Response, Handles access to / and returns HTML page. Args: request: Request to respond…, Handles GET access to /ping for testing connectivity. Args: request: Request to…, Handles access to /* and returns a specified image. Args: request: Request to…

### Community 215 - "Image (pyobs.images.processors.image) API doc"
Cohesion: 0.18
Nodes (11): AddFitsHeaders, Image (pyobs.images.processors.image) API doc, Download, Flip, Grayscale, HttpServer, Normalize, Save (+3 more)

### Community 216 - "Offsets (pyobs.images.processors.offsets) API doc"
Cohesion: 0.33
Nodes (11): AstrometryOffsets, BrightestStarGuiding, BrightestStarOffsets, Offsets (pyobs.images.processors.offsets) API doc, DummyOffsets, DummySkyOffsets, FitsHeaderOffsets, Offsets (+3 more)

### Community 217 - "Constraint"
Cohesion: 0.20
Nodes (11): AirmassConstraint, AstroplanScheduler, Constraint, Constraints answer a binary may-it-run question (any False excludes the task); Merits answer a continuous how-desirable question (values multiplied together with priority, highest score wins); rationale: clean separation lets scheduling policy be expressed in YAML without code, and a Merit returning 0.0 can double as a soft constraint, MoonIlluminationConstraint, MoonSeparationConstraint, OnDemandScheduler, OnDemandScheduler: greedy, evaluates constraints/merits per time step, robust to interruption, supports merits+global constraints+lookahead. AstroplanScheduler: full-night planning via astroplan PriorityScheduler in a separate process (avoids blocking event loop), only SiderealTarget, only per-task constraints, no merits; rationale: choose based on whether a committed nightly plan or rolling on-demand decisions is needed (+3 more)

### Community 218 - "Smooth"
Cohesion: 0.22
Nodes (10): Any, Init a new smoothing pipeline step. Args: sigma: Standard deviation for…, Smooth an image. Args: image: Image to smooth. Returns: Smoothed image., Gaussian smoothing of image data using SciPy’s ndimage.gaussian_filter. This…, Smooth, asyncio, test_call(), test_call_no_image_data() (+2 more)

### Community 219 - "http_request_paginated"
Cohesion: 0.20
Nodes (10): Fetches last schedule update time., Clear schedule after given start time. Args: start_time: Start time to clear…, http_request_paginated(), http_request_with_retries(), InvalidResponseError, Any, ClientSession, Raised when the server returns an unexpected HTTP status. Carries the status… (+2 more)

### Community 220 - "test_autofocus.py"
Cohesion: 0.23
Nodes (20): AutoFocusScript, Script for running autofocus series., isinstance_class(), Shared test-double helpers used across multiple test modules., Build a fresh class purely for isinstance() checks against a MagicMock.…, make_autofocus(), make_script(), make_task() (+12 more)

### Community 221 - "SkyflatPriorities"
Cohesion: 0.30
Nodes (6): ArchiveSkyflatPriorities, Calculate flat priorities from an archive., Base class for sky flat priorities., SkyflatPriorities, ConstSkyflatPriorities, Constant flat priorities.

### Community 222 - "test_xmpp_rpc.py"
Cohesion: 0.19
Nodes (14): Integration tests for the pyobs 2.0 RPC payload encoding (urn:pyobs:rpc:1).…, set_binning(int, int) -> None: multiple int params, void return., Calling a method that raises on the remote side propagates the exception., set_cooling(bool, float) then verify via state: full encode/decode cycle., set_cooling(bool, float) -> None: void return with bool + float params., set_gain(float) -> None and verify via IGain state: float param, state readback., set_gain(float) then verify via IGain state: float param round-trip., test_rpc_bool_float_roundtrip() (+6 more)

### Community 223 - "Plan: `IDataSequence` — server-side counted data sequences (reconstructed)"
Cohesion: 0.33
Nodes (5): Architecture, File Map, Goal, Plan: `IDataSequence` — server-side counted data sequences (reconstructed), Tasks

### Community 224 - "TaskStartedEvent"
Cohesion: 0.16
Nodes (9): Any, Event to be sent when a task has started., Initializes a new task started event. Args: name: Name of task that just…, TaskStartedEvent, test_task_started_invalid_name(), test_task_started_missing_id(), test_task_started_no_eta(), test_task_started_properties() (+1 more)

### Community 225 - "is_valid_jid"
Cohesion: 0.21
Nodes (6): is_valid_jid(), Whether jid is a valid user@domain or user@domain/resource JID -- exactly what…, JID parsing/validation in XmppComm.__init__ and the reusable is_valid_jid()…, The actual production bug this was found from: a JID ending in "/" with nothing…, re.match alone doesn't anchor the end -- confirms the pattern is anchored so…, TestIsValidJid

### Community 226 - ".move_heliographic_stonyhurst"
Cohesion: 0.50
Nodes (3): Any, DEGREES, Moves on given coordinates. Args: lon: Longitude in deg to track. lat: Latitude…

### Community 227 - "FileList"
Cohesion: 0.27
Nodes (5): FileList, Base class for file lists., Any, File list for testing., TestingFileList

### Community 228 - ".move_helioprojective"
Cohesion: 0.50
Nodes (3): Any, DEGREES, Moves on given coordinates. Args: theta_x: The theta_x coordinate. theta_y: The…

### Community 230 - "pyobs 2.0 Wire Protocol, State, and Access Control design doc"
Cohesion: 0.09
Nodes (22): pyobs/utils/config_schema.py: dataclass_to_schema, ICooling interface (reference pattern), slixmpp O(N^2) IQ handler dispatch bug (cross-referenced), IStructuredConfig design doc, IStructuredConfig interface, Rationale: IStructuredConfig coexists with IConfig (per-field vs bulk dataclass config), pyobs 2.0 Wire Protocol, State, and Access Control design doc, Access Control (ACLs): allow/deny, mode: enforce|log (+14 more)

### Community 231 - "Plan: Log the loaded pyobs-* package versions at module startup"
Cohesion: 0.20
Nodes (9): Decision, Design, Helper, Implementation checklist, Log point, Open questions, Out of scope (follow-ups), Plan: Log the loaded pyobs-* package versions at module startup (+1 more)

### Community 232 - "Findings: driver/gui correctness review, all 8 repos (reviewed 2026-08-11)"
Cohesion: 0.13
Nodes (14): Context, Findings: driver/gui correctness review, all 8 repos (reviewed 2026-08-11), Plan: Driver/GUI split for all camera modules + qhyccd correctness review, pyobs-aravis, pyobs-asi, pyobs-fli (driver split only — gui.py built 2026-08-18 via PR #85), pyobs-flipro, pyobs-qhyccd (+6 more)

### Community 233 - "Plan: Unify TRIMSEC handling into `Image.trim()` (reconstructed)"
Cohesion: 0.33
Nodes (5): Architecture, File Map, Goal, Plan: Unify TRIMSEC handling into `Image.trim()` (reconstructed), Tasks

### Community 234 - "CHANGELOG.rst"
Cohesion: 0.22
Nodes (9): ejabberd shaper/xmpp_socket.erl reactivation bug (iag50srv capability-fetch timeouts), XmppComm disco#info role attribute (send/subscribe split), OnDemandScheduler CPU-bound work offloaded to ThreadPoolExecutor, Vfs.write_image()/write_fits() moved to asyncio.to_thread(), run_cpu_bound (scheduler/_executor.py), Vfs.write_fits (pyobs/vfs/vfs.py), Vfs.write_image (pyobs/vfs/vfs.py), specs/plans/event-role-advertising.md (+1 more)

### Community 235 - "Use a self-hosted Keycloak alongside odin, as two parallel auth backends"
Cohesion: 0.10
Nodes (17): Consequences, Considered Options, Context and Problem Statement, Decision Outcome, Use a self-hosted Keycloak alongside odin, as two parallel auth backends, Consequences, Considered Options, Context and Problem Statement (+9 more)

### Community 236 - "Image class"
Cohesion: 0.20
Nodes (10): meta.AltAzOffsets, meta.ExpTime, Image class, Image.meta dict; rationale: keyed by class to avoid collisions between pipeline stages, kept out of FITS since it's runtime-only data, meta.OnSkyDistance, meta.PixelOffsets, meta.RaDecOffsets, meta.SkyOffsets (+2 more)

### Community 237 - "PySepStatsCalculator"
Cohesion: 0.26
Nodes (4): Any, floating, NDArray, PySepStatsCalculator

### Community 238 - "Implementation"
Cohesion: 0.14
Nodes (13): 1. Frame.PROJECT — `pyobs_archive/api/models.py`, 2. Backend connection (project/user knowledge), 3. Access layer — `pyobs_archive/api/permissions.py`, 4. Endpoint filtering — `pyobs_archive/api/views.py`, 5. Frontend — `pyobs_archive/frontend`, 6. Backend dependency — tracked in pyobs/pyobs-robotic-backend#79, Consequences, Implementation (+5 more)

### Community 239 - ".set_rotation"
Cohesion: 0.50
Nodes (3): Any, DEGREES, Sets the rotation angle to the given value in degrees. Raises: MoveError: If…

### Community 240 - "Module.startup() lifecycle helper"
Cohesion: 0.50
Nodes (4): Module.startup() lifecycle helper, ModuleState.STARTING, Rationale: delay send_presence() until READY to avoid capability-publish race, Gating RPC commands until module startup completes

### Community 241 - "Object"
Cohesion: 0.07
Nodes (36): PydanticBaseModel, Object, Base class for all objects in *pyobs*., Whether object has been opened., Can be overloaded to quit program., AcquisitionConfig, GuidingConfig, ConfigurationStatus (+28 more)

### Community 242 - "Plan: Stop scheduler constraint/merit evaluation from blocking the event loop"
Cohesion: 0.14
Nodes (13): 1. Dedicated executor — new file `pyobs/robotic/scheduler/_executor.py`, 2. Offload the three call sites — `pyobs/robotic/scheduler/ondemandscheduler.py`, 3. Cache target-independent astropy results — `pyobs/robotic/scheduler/dataprovider.py`, 4. `AstroplanScheduler` — no change, Consequences, Considered options, Decision, Existing coverage (regression net, no changes needed) (+5 more)

### Community 243 - ".__init__"
Cohesion: 0.18
Nodes (8): Any, SkyCoord, Create an approximately equidistributed spherical grid. Args: n: Target number…, Initialize a Grid with a list of points. Args: points: Initial list of points…, Return the next point and remove it from the internal list. Returns: The next…, Create a regular lon/lat grid. Args: n_lon: Number of longitudinal divisions.…, Any, Initialize a GridNode. Args: log: If True, enable informational logging for…

### Community 244 - "watch_log_events_no_interest.py"
Cohesion: 0.50
Nodes (4): main(), make_client(), ClientXMPP, Like watch_log_events_raw.py, but deliberately never declares XEP-0163…

### Community 245 - "SkyFlatsBasePointing"
Cohesion: 0.18
Nodes (8): Any, Initialize a new flat fielder. Args: functions: Function f(h) for each filter…, Base class for flat pointings., SkyFlatsBasePointing, model_validator, Self, Static flat pointing., SkyFlatsStaticPointing

### Community 246 - "pyobs-gui as a standalone binary (umbrella design)"
Cohesion: 0.27
Nodes (10): ADR-0010: pyobs-gui stays on QtWidgets, not QML, gui-telescopewidget-layout.md, pyobs-gui (PySide6/QtWidgets app), pyobs-web-client (Vue 3 + TypeScript), QML (declarative UI framework), pyobs.application.Application, pyobs-gui as a standalone binary (umbrella design), specs/plans/gui-interactive-login.md (+2 more)

### Community 247 - "Plan: Enforce state publishing for stateful interfaces"
Cohesion: 0.15
Nodes (12): 1. `Comm` — track published state, 2026-07-27 addendum: two more instances of the same bug found in production, plus a severity change, 2. `Module.startup()` — warn on missing state, 3. `Weather` — publish a placeholder synchronously in `open()`, 4. Test — parametrized check for all concrete modules, 5. `DummyComm` — no changes needed, Consequences, Considered options (+4 more)

### Community 248 - "Plan: `pyobs-gui` login window"
Cohesion: 0.15
Nodes (12): Account metadata storage, Connect flow, Design, Goals, Implementation checklist, Model: `pyobs-polaris`'s `LoginWindow.qml`, Non-goals, Non-goals for `module_factory`'s contract (+4 more)

### Community 249 - "test_safe_send.py"
Cohesion: 0.38
Nodes (9): make_xmpp_comm(), asyncio, Tests for XmppComm._safe_send's retry/timeout handling. Covers…, Create a minimal XmppComm instance for testing, without a live connection., A method that never returns (e.g. slixmpp's own IQ timeout not firing) must…, test_safe_send_enforces_own_timeout_when_method_hangs(), test_safe_send_retries_and_raises_on_iq_timeout(), test_safe_send_returns_result_on_success() (+1 more)

### Community 250 - "test_exceptions.py"
Cohesion: 0.29
Nodes (4): ForbiddenError, Raised when a caller is not permitted to invoke a method under the target…, test_forbidden_error(), test_log_only_logs_once()

### Community 251 - "Two-phase Object lifecycle; rationale: __init__ must not touch hardware/external services (only store params, create children, register background tasks); open() is where side effects happen, so objects can be constructed cheaply/safely before being started"
Cohesion: 0.22
Nodes (8): Object.add_child_object(), create_object(), get_object(), Two-phase Object lifecycle; rationale: __init__ must not touch hardware/external services (only store params, create children, register background tasks); open() is where side effects happen, so objects can be constructed cheaply/safely before being started, class: key YAML instantiation; rationale: strips class key, passes remaining keys as kwargs, recursing into nested blocks, so any pyobs object graph is fully describable in YAML, Configuration utilities (pyobs.utils.config) API doc, pre_process_yaml(), Coordinate utilities (pyobs.utils.coordinates) API doc

### Community 252 - "Simulation recipe (doc)"
Cohesion: 0.42
Nodes (9): pyobs.modules.telescope (doc), BaseTelescope, DummyAltAzTelescope, DummyRaDecTelescope, DummySolarTelescope, Simulation recipe (doc), DummyCamera, pyobs_gui.GUI (+1 more)

### Community 253 - "test_httpfilecache.py"
Cohesion: 0.52
Nodes (11): make_cache(), make_request(), asyncio, test_download_response_has_cors_header(), test_download_with_token_configured_accepts_correct_token(), test_download_with_token_configured_rejects_missing_header(), test_download_with_token_configured_rejects_wrong_token(), test_download_without_token_configured_is_unauthenticated() (+3 more)

### Community 254 - "test_imagewriter.py"
Cohesion: 0.12
Nodes (20): ImageWriter, Writes new images to disk., Puts a new images in the DB with the given ID. Args: event: New image event…, Modules for image operations. TODO: write doc, Any, Measures seeing on reduced images with a catalog., Creates a new seeing estimator. Args: sources: List of sources (e.g. cameras)…, Puts a new images in the DB with the given ID. Args: event: New image event… (+12 more)

### Community 255 - "_ResponseImageWriter"
Cohesion: 0.24
Nodes (4): Any, WCS, astrometry.net gives a CD matrix, so we have to delete the PC matrix and the…, _ResponseImageWriter

### Community 256 - "Decision"
Cohesion: 0.17
Nodes (11): 1. `ImageProcessor` — new methods and kwarg, 2. `PipelineMixin.run_pipeline()` — wrap each step, 3. `AstrometryDotNet` — migrate to handle_error, 4. Deprecation notes, 5. Tests, Consequences, Considered options, Decision (+3 more)

### Community 257 - "_PhotometryCalculator"
Cohesion: 0.19
Nodes (4): Any, _PhotometryCalculator, Table, Abstract class for photometry calculators.

### Community 258 - "TaskFinishedEvent"
Cohesion: 0.10
Nodes (13): Any, Event to be sent when a task has failed., Initializes a new task failed event. Args: name: Name of task that just…, TaskFailedEvent, Any, Event to be sent when a task has finished., Initializes a new task finished event. Args: name: Name of task that just…, TaskFinishedEvent (+5 more)

### Community 259 - "TempFile"
Cohesion: 0.24
Nodes (6): Any, Open/create a temp file. Args: name: Name of file. mode: Open mode. prefix:…, TempFile, asyncio, test_name(), test_write_file()

### Community 260 - "PrimaryHDU"
Cohesion: 0.21
Nodes (7): PrimaryHDU, Add the cheap, local FITS headers to the given image (no I/O, no comm). This is…, Add requested FITS headers to header of given image. Args: image: Image with…, Add FITS header keywords to the given FITS header. Args: image: Image with…, Add FRAMENUM keyword to header Args: image: Image with header to add to., Format filename according to given pattern and store in header of image. Args:…, Add FITS header keywords to the given FITS header. Args: image: Image with…

### Community 261 - "robotic"
Cohesion: 0.43
Nodes (8): acquisition, fibercamera, fts, guiding, robotic, solar telescope, suncamera, weather

### Community 262 - "Archive (image archive base)"
Cohesion: 0.32
Nodes (8): Archive (image archive base), LocalArchive, PyobsArchive, ArchiveSkyflatPriorities, Archive, Image archives (pyobs.robotic.utils.archive) API doc, LocalArchive, PyobsArchive

### Community 263 - "._move_radec"
Cohesion: 0.17
Nodes (8): Any, Initialize a new base telescope. Args: fits_headers: Additional FITS headers to…, Actually starts tracking on given coordinates. Must be implemented by derived…, Starts tracking on given coordinates. Args: ra: RA in deg to track. dec: Dec in…, Actually moves to given coordinates. Must be implemented by derived classes.…, Moves to given coordinates. Args: alt: Alt in deg to move to. az: Az in deg to…, Thread for continuously calculating positions and distances to celestial…, Calculate positions and distances to celestial objects like moon and sun.

### Community 264 - "._get_client"
Cohesion: 0.11
Nodes (10): PresenceCallback, Get a proxy to the given client. Args: client: Name of client. Returns: Proxy…, Fetch capabilities for a single interface and push them into the given proxy…, Called when a client disconnects. Args: event: Disconnect event. sender: Name…, Returns list of interfaces for given client. Args: client: Name of client.…, Subscribe to state updates for a given module and interface. Delivers the…, Unsubscribe from state updates. Args: module: Name of remote module. interface:…, Subscribe to presence updates for a given module. Delivers the current value… (+2 more)

### Community 265 - "GuidingStatisticsSkyOffset"
Cohesion: 0.25
Nodes (7): GuidingStatisticsSkyOffset, Calculates RMS of data. Args: data: Data to calculate RMS for. Returns: Tuple…, mock_meta_image(), fixture, test_build_header_to_few_values(), test_end_to_end(), test_get_session_data()

### Community 266 - "SFTPFile"
Cohesion: 0.22
Nodes (5): Any, VFS wrapper for a file that can be accessed over a SFTP connection., Open/create a file over a SSH connection. Args: name: Name of file. mode: Open…, Returns content of given path. Args: path: Path to list. kwargs: Parameters for…, SFTPFile

### Community 267 - "test_xmpp_acl.py"
Cohesion: 0.22
Nodes (12): Integration tests for Phase 8 Access Control (ACLs) over real XMPP. Verifies…, A caller granted "*" access under "allow" can still call normally., A caller not present in the "allow" map is denied by default., A caller on the "deny" list gets exc.RemoteError with a forbidden message, not…, Naming an interface under "allow" permits all of its methods, but nothing…, A module not on the "deny" list is unaffected., test_acl_allow_denies_unlisted_caller(), test_acl_allow_interface_name_sugar() (+4 more)

### Community 268 - "._get_next"
Cohesion: 0.33
Nodes (4): SkyCoord, Log a point if logging is enabled. For SkyCoord instances, logs RA/Dec in…, Return the next point in the sequence. Implementors must return either a (x, y)…, Return the next point, storing it as the last yielded value. Returns: A point…

### Community 269 - "Discussion: LogEvent double-delivery fix — should we drop add_interest()?"
Cohesion: 0.20
Nodes (9): Can roster and pubsub delivery be split?, Consequence: are all events sent to all clients?, Did we ever need add_interest()?, Discussion: LogEvent double-delivery fix — should we drop add_interest()?, How could real interest-based filtering be achieved?, Monitoring / rollback plan, Proposed fix (from the investigation, point 15), Was shared roster a bad idea? (+1 more)

### Community 270 - "Plan: `pyobs-gui` navbar keyboard shortcuts"
Cohesion: 0.18
Nodes (10): Binding is by page name, not by widget or list-item instance, File changes, Key scheme, Motivation, Plan: `pyobs-gui` navbar keyboard shortcuts, Shortcut wiring, State, Verification (once implemented) (+2 more)

### Community 271 - "filters.py"
Cohesion: 0.15
Nodes (20): ConvertGridFrame, ConvertGridToSkyCoord, FromList, GridFilterValue, Convert (x, y) degree tuples to SkyCoord objects. Wraps a tuple-producing grid…, Transform SkyCoord points to a different frame., Select closest point from a list. Only select points if they are closer than a…, Filter points by numeric constraints on x and y. Accepts points as: - (x, y)… (+12 more)

### Community 272 - ".__call__"
Cohesion: 0.38
Nodes (5): ApertureMask, CircularAperture, Any, floating, NDArray

### Community 273 - "Image.trim"
Cohesion: 0.25
Nodes (5): _CCDDataCalibrator, Image.trim(): unify three TRIMSEC implementations, Image, Image.trim(), Issue #342 (unify TRIMSEC implementations)

### Community 274 - "conftest.py"
Cohesion: 0.38
Nodes (6): download_IERS(), Any, fixture, pytest_addoption(), pytest_collection_modifyitems(), pytest_configure()

### Community 275 - "Misc (pyobs.images.processors.misc) API doc"
Cohesion: 0.29
Nodes (7): AddMask, CatalogCircularMask, CircularMask, CreateFilename, Misc (pyobs.images.processors.misc) API doc, ImageSourceFilter, RemoveBackground

### Community 276 - "PolymorphicBaseModel"
Cohesion: 0.29
Nodes (7): CsvPicker, DynamicTarget, HelioprojectiveTarget, Picker, SiderealTarget, Target, PolymorphicBaseModel

### Community 277 - "Plan: Stop gating backend-archive refreshes on the `last_*_update` marker"
Cohesion: 0.20
Nodes (9): `BackendObservationArchive`, `BackendTaskArchive`, Consequences, Design, Out of scope (pyobs-robotic-backend), Plan: Stop gating backend-archive refreshes on the `last_*_update` marker, Problem, Rollout (+1 more)

### Community 278 - "time.py"
Cohesion: 0.04
Nodes (76): IDome, The module controls a dome, i.e. a :class:`~pyobs.interfaces.IRoof` with a…, FiltersCapabilities, FilterState, FitsHeaderEntry, IFitsHeaderBefore, Any, The module provides some additional header entries for FITS headers before some… (+68 more)

### Community 279 - "InfluxHandler"
Cohesion: 0.24
Nodes (4): InfluxHandler, Any, LogRecord, WriteOptions

### Community 280 - "FollowMixin"
Cohesion: 0.18
Nodes (8): build_skycoord(), FollowMixin, Any, SkyCoord, Returns True, if we're following another device., Build SkyCoord from x/y tuple in given mode. Args: coord: x/y tuple with…, Mixin for a device that should follow the motion of another., Initializes the mixin. Args: device: Name of device to follow interval:…

### Community 281 - "ObservationList"
Cohesion: 0.06
Nodes (58): ObservationList, Any, Add the list of scheduled tasks to the schedule. Args: tasks: Scheduled tasks., date, Add the list of scheduled tasks to the schedule. Args: tasks: Scheduled tasks., Returns a list of observations for the given task. Args: date: Date of night to…, Add observations to the archive. Args: observations: Observations to add., MemoryTaskArchive (+50 more)

### Community 282 - ".move_heliocentric_polar"
Cohesion: 0.50
Nodes (3): Any, DEGREES, Moves on given coordinates. Args: mu: Cosine of the angular distance from Sun…

### Community 283 - "wait_for"
Cohesion: 0.17
Nodes (12): DummyCamera.open() must publish IWindow.Capabilities with the SimCamera full…, DummyCamera.open() must publish IModule.Capabilities with version and label., get_capabilities() must return None for an interface DummyCamera doesn't…, Poll *condition* until truthy or *timeout* seconds elapse., DummyCamera's _cooling_thread publishes CoolingState every second. An observer…, After calling set_cooling via RPC, the published CoolingState must reflect the…, test_dummy_camera_cooling_state_reflects_set_cooling(), test_dummy_camera_no_capabilities_for_unconfigured_interface() (+4 more)

### Community 284 - "test_astroplanscheduler.py"
Cohesion: 0.08
Nodes (40): Any, Initialize a new bot. Args: server: Server to connect to. user_id: ID of user…, AstroplanScheduler, Any, ObservingBlock, Actually do the scheduling, usually run in a separate process., Scheduler based on astroplan., Initialize a new scheduler. Args: twilight: astronomical or nautical (+32 more)

### Community 285 - "Implementation"
Cohesion: 0.20
Nodes (9): 1. `Proxy` — the actual freshness check, 2. `Interface.get_state()` / `Interface.wait_for_state()` — matching stub signatures, 3. Fix the concrete unsafe consumer: `WeatherAwareMixin`, 4. Follow-up consumers: `FollowMixin` and `FocusModel`, Consequences, Decision, Implementation, Plan: `max_age` parameter for `get_state()` / `wait_for_state()` (+1 more)

### Community 286 - "Plan: Interactive login/settings dialog for `pyobs-gui`, deferring `Application`'s module construction"
Cohesion: 0.20
Nodes (9): Design, Goals, Implementation checklist, Non-goals, Non-goals for the factory's contract, Open questions, Plan: Interactive login/settings dialog for `pyobs-gui`, deferring `Application`'s module construction, Problem (+1 more)

### Community 287 - "pyobs.modules.utils (doc)"
Cohesion: 0.33
Nodes (6): pyobs.modules.utils (doc), FluentLogger, Kiosk, Matrix, Telegram, Trigger

### Community 288 - "Plan: Add baseline tests to core-tier repos, then enable grouped Dependabot auto-merge"
Cohesion: 0.20
Nodes (9): Baseline test pattern (define once, apply to every repo), Explicitly out of scope, Phase 1 — Group A (5-6 repos), Phase 2 — Group B (3 repos), Phase 3 — Group C (4 repos), Plan: Add baseline tests to core-tier repos, then enable grouped Dependabot auto-merge, Resolved scope questions, Scope correction: drop pyobs-andor and pyobs-tui, add pyobs-qhyccd (+1 more)

### Community 289 - "Plan: CORS + token auth for `HttpFileCache`"
Cohesion: 0.22
Nodes (8): 1. `HttpFileCache` — token check + CORS + preflight, 2. `HttpFile` — send the token instead of Basic auth, 3. Tests, Consequences, Decision, Implementation, Plan: CORS + token auth for `HttpFileCache`, Problem

### Community 290 - "._residuals"
Cohesion: 0.53
Nodes (4): DataFrame, floating, NDArray, Fit method for model Args: x: Paramaters to evaluate. data: Full data set.…

### Community 291 - "Photometry"
Cohesion: 0.20
Nodes (7): Photometry, Do aperture photometry on given image. Args: image: Image to do aperture…, Base class for photometry processors., Any, Perform photometry using SEP., SepPhotometry, test_init()

### Community 292 - "Plan: `pyobs-gui` IAutoGuiding widget"
Cohesion: 0.25
Nodes (7): Known bug in the shipped widget (to fix alongside this change), Plan: `pyobs-gui` IAutoGuiding widget, Problem: pixel offsets aren't physical, and the per-image correction is discarded, Proposed pyobs-core change, Resolved from the original open questions, Shipped (pyobs-core, `develop`), Widget design (pyobs-gui)

### Community 293 - "ImageFormat"
Cohesion: 0.24
Nodes (5): Any, Set the camera image format. Args: fmt: New image format. Raises: ValueError:…, ImageFormat, Enumerator for image formats. Attributes: INT8: 8 bit integer (i.e. byte).…, ImageFormatWidget

### Community 294 - "DummyMode"
Cohesion: 0.27
Nodes (6): ModeState, DummyMode, Any, A dummy module for mode switching., Initialize a new dummy module., Set the current mode. Args: mode: Name of mode to set. group: Name of the group…

### Community 295 - "Investigation: pyobs-gui receives every LogEvent twice (SAAO/monet production)"
Cohesion: 0.25
Nodes (7): Access used, Artifacts from this session, Investigation: pyobs-gui receives every LogEvent twice (SAAO/monet production), Next steps, Problem, What's confirmed, What's ruled out

### Community 296 - "WeatherStatus"
Cohesion: 0.27
Nodes (6): Any, setter, WeatherStatus, test_status_set(), test_status_set_non_good(), test_status_set_none_good()

### Community 297 - "PyobsArchive"
Cohesion: 0.27
Nodes (5): Any, PyobsArchive, Connector class to running pyobs-archive instance., test_build_query_empty_when_nothing_given(), test_build_query_includes_all_given_params()

### Community 298 - ".init"
Cohesion: 0.29
Nodes (4): Any, Initialize device. Raises: InitError: If device could not be initialized., Park device. Raises: ParkError: If device could not be parked., Stop the motion. Args: device: Name of device to stop, or None for all.

### Community 300 - "ADR-0008: _safe_send keeps bounded retry unlike capability/subscribe fetches"
Cohesion: 0.40
Nodes (5): ADR-0008: _safe_send keeps bounded retry unlike capability/subscribe fetches, #664/#666 slow-shaper hang incident, XmppComm._get_capabilities(), XmppComm._retry_delay() (jittered capped backoff), XmppComm._safe_send()

### Community 301 - "Module._watch_event_loop_lag"
Cohesion: 0.33
Nodes (5): BrotDome._update_status, ADR-0009: Event-loop lag watchdog lives on Module, FocusModel._update, pyobs-iag50 capability-fetch timeout incident, Module._watch_event_loop_lag

### Community 302 - "Plan: Surface unrecognized kwargs in `Object.__init__` instead of silently discarding them"
Cohesion: 0.17
Nodes (11): Decision, Fleet-wide cleanup pass (2026-08-18), Implementation checklist, Investigation findings (2026-08-15), Non-goals (for now — this is a stub, scope may change once investigated), Open questions, Plan: Surface unrecognized kwargs in `Object.__init__` instead of silently discarding them, Problem (+3 more)

### Community 303 - "pyobs.modules.image (doc)"
Cohesion: 0.40
Nodes (5): pyobs.modules.image (doc), ImageWatcher, ImageWriter, Pipeline (image module), Seeing

### Community 304 - ".__init__"
Cohesion: 0.40
Nodes (4): Any, Pipeline, ProgressCallback, Creates a Reduction object for reducing a given observation period. Args:…

### Community 305 - "_baseguiding.py"
Cohesion: 0.05
Nodes (34): GuidingState, IAutoGuiding, The module can perform auto-guiding., ExposureTimeState, AutoGuiding, Any, An auto-guiding system., Initializes a new auto guiding system. Args: exposure_time: Initial exposure… (+26 more)

### Community 306 - "datetime"
Cohesion: 0.42
Nodes (4): datetime, GuidingStatisticsUptime, test_calc_uptime_percentage(), test_end_to_end()

### Community 307 - "Plan: Bound the FITS-header fetch so a dead peer can't stall the frame"
Cohesion: 0.29
Nodes (6): Design, Plan: Bound the FITS-header fetch so a dead peer can't stall the frame, Post-merge fixes (review, 2026-08-16), Problem, Rollout, Testing

### Community 308 - "plans/index.md"
Cohesion: 0.06
Nodes (23): Architecture, File Map (representative, not exhaustive — see commit diffs for the full ~74-file list), Goal, Plan: Exception handling across the RPC boundary (reconstructed), Tasks, Architecture, File Map, Goal (+15 more)

### Community 309 - "ScriptRunner"
Cohesion: 0.14
Nodes (15): calc_run_timeout(), Any, Calculates timeout for run()., Module for running a script., Initialize a new script runner. Args: script: Config for script to run., Run script. Raises: ScriptError: If the script failed (e.g. a proxy/network…, Abort current actions., ScriptRunner (+7 more)

### Community 310 - "test_camerasettings.py"
Cohesion: 0.36
Nodes (9): make_camera_proxy(), make_module(), asyncio, Minimal concrete module for exercising CameraSettingsMixin in isolation., Capabilities for a Proxy are fetched in the background (see…, SettingsModule, test_raises_when_capabilities_never_arrive(), test_sets_binning_before_window() (+1 more)

### Community 311 - "CasesRunner"
Cohesion: 0.29
Nodes (5): CasesRunner, Script for distinguishing cases., Returns FITS header for the current status of this module. Args: namespaces: If…, Estimate duration of the script for the current case., test_cases_get_fits_headers()

### Community 312 - "Plan: `pyobs-auth` + Keycloak integration"
Cohesion: 0.29
Nodes (6): 0. observation-portal (Keycloak admin config + small observation-portal config change), 1. `pyobs-auth` package (new repo) — done, released, 2. pyobs-archive — cutover, not dual-path — landed, 3. pyobs-robotic-backend — done, 4. Not in this plan, Plan: `pyobs-auth` + Keycloak integration

### Community 313 - "Fleet open items: open issues and plans across the pyobs fleet"
Cohesion: 0.29
Nodes (7): Design docs still *proposed*, Fleet open items: open issues and plans across the pyobs fleet, Open decisions, Open issues (8, checked 2026-08-20), Open plans, pyobs-core `specs/plans/`, Sibling repos

### Community 314 - "SMBFile"
Cohesion: 0.22
Nodes (5): Any, Returns content of given path. Args: path: Path to list. kwargs: Parameters for…, VFS wrapper for a file that can be accessed over a SMB connection. Requires…, Open/create a file over a SSH connection. Args: name: Name of file. mode: Open…, SMBFile

### Community 315 - ".grab_sequence"
Cohesion: 0.33
Nodes (4): Any, SECONDS, Start a sequence of `count` grabs. Returns immediately; progress is available…, Stop the sequence after the current grab. The grab currently in progress, if…

### Community 316 - "ModuleLocation dataclass (nested in ModuleCapabilities)"
Cohesion: 0.50
Nodes (4): Location-mismatch warning via _on_module_opened, Rationale: location as one-shot capability, not pubsub state, ModuleLocation dataclass (nested in ModuleCapabilities), Module observer-location capabilities design doc

### Community 317 - "check_pyobs_releases.sh"
Cohesion: 0.70
Nodes (4): check_repo(), main(), print_header(), check_pyobs_releases.sh script

### Community 318 - "check_ejabberd_notify.py"
Cohesion: 0.60
Nodes (4): connect(), main(), make_client(), Minimal ejabberd notification test — no pyobs code involved.

### Community 319 - "test_dummysolartelescope.py"
Cohesion: 0.49
Nodes (9): make_dummysolartelescope(), asyncio, test_does_not_implement_body_or_orbital_element_tracking(), test_move_heliocentric_polar_slews_tracks_solar_and_publishes_state(), test_move_heliographic_stonyhurst_slews_tracks_solar_and_publishes_state(), test_move_helioprojective_slews_tracks_solar_and_publishes_state(), test_plain_move_altaz_clears_solar_target(), test_plain_move_radec_clears_solar_target_and_resets_to_sidereal() (+1 more)

### Community 320 - "._main"
Cohesion: 0.40
Nodes (3): Actually run the application., Force astropy's IERS-A table and leap-second table to be loaded/downloaded now,…, _warm_iers_cache()

### Community 322 - "Photometry (pyobs.images.processors.photometry) API doc"
Cohesion: 0.83
Nodes (4): Photometry (pyobs.images.processors.photometry) API doc, Photometry, PhotUtilsPhotometry, SepPhotometry

### Community 323 - ".__init__"
Cohesion: 0.09
Nodes (14): Any, Create a new image watcher. Args: watchpath: Path to watch. destinations:…, Any, Creates a new image writer. Args: filename: Pattern for filename to store…, Args: label: Label for module. If None, name is used. own_comm: If True, module…, List interfaces and methods of this module., Any, Creates a new StandAlone object. Args: message: Message to log in the given… (+6 more)

### Community 324 - ".__init__"
Cohesion: 0.25
Nodes (5): Any, Initializes a new ApplyAltAzOffsets. Args: min_offset: Min offset in arcsec to…, Any, Any, Initializes a new ApplyRaDecOffsets. Args: min_offset: Min offset in arcsec to…

### Community 325 - "Target"
Cohesion: 0.29
Nodes (4): Target, Set the resolved target if not already set, e.g. when restoring from an…, The resolved target, or the static target if not dynamic., Target for this specific run: the observation's own record if known, otherwise…

### Community 326 - "test_comm_interface_resolution.py"
Cohesion: 0.29
Nodes (8): Converts a list of interface names to interface classes. Args: interfaces: list…, LogCaptureFixture, Tests for Comm._interface_names_to_classes -- the base-Comm chokepoint that…, An interface defined entirely outside pyobs.interfaces resolves the same way…, test_resolves_external_interface(), test_resolves_known_and_skips_unknown_in_same_list(), test_resolves_known_core_interfaces(), test_skips_unknown_name()

### Community 327 - ".night_obs"
Cohesion: 0.50
Nodes (3): date, Observer, Returns the night for this time, i.e. the date of the start of the current…

### Community 328 - "_FakeProxyContext"
Cohesion: 0.25
Nodes (3): _FakeProxyContext, Any, Minimal async context manager standing in for Object.proxy()'s _ProxyContext.

### Community 329 - ".__init__"
Cohesion: 0.33
Nodes (4): Any, Abort current actions., Initialize a new flat field scheduler. Args: flatfield: Flat field module to…, Perform flat-fielding Raises: DeviceBusyError: If a flat-fielding run is…

### Community 330 - ".sun_altaz"
Cohesion: 0.29
Nodes (4): SkyCoord, Returns the Sun's coordinates at the given time., Returns the Sun's AltAz coordinates at the given time, as seen by the observer., Returns the Moon's coordinates at the given time.

### Community 331 - "_ProxyContext"
Cohesion: 0.40
Nodes (3): _ProxyContext, ProxyType, Returned by Comm.proxy() / Object.proxy() / Comm.safe_proxy(). Must be used as:…

### Community 332 - "Plan: Module observer-location capabilities (reconstructed)"
Cohesion: 0.33
Nodes (5): Architecture, File Map, Goal, Plan: Module observer-location capabilities (reconstructed), Tasks

### Community 333 - "Plan: Advertise event send/subscribe role in disco#info"
Cohesion: 0.33
Nodes (5): Architecture, File Map, Plan: Advertise event send/subscribe role in disco#info, Problem, Tasks

### Community 334 - "IFocusModel"
Cohesion: 0.40
Nodes (4): IFocusModel, Any, The module provides a model for the telescope focus, e.g. based on temperatures., Sets optimal focus. Raises: WeatherDataError: If the weather station returned…

### Community 335 - ".__init__"
Cohesion: 0.40
Nodes (3): Any, Initialize a new flat field pointing. Args: telescope: Telescope to point…, Abort current actions.

### Community 336 - ".night"
Cohesion: 0.40
Nodes (3): date, Returns the time of the last sunset., Returns the time of the last sunset.

### Community 337 - "Implemented"
Cohesion: 0.40
Nodes (4): Implemented, Option A: reactive-only (already shipped, zero work), Option B: proactive greying-out — effort estimate (~half a day, 3-5 hours), Plan: `pyobs-gui` ACL-aware widget gating

### Community 338 - "make_observer"
Cohesion: 0.50
Nodes (5): make_observer(), date, EarthLocation, test_add_fits_headers_sets_day_obs_from_night_obs(), test_add_fits_headers_sets_lst_when_observer_present()

### Community 340 - ".flat_field"
Cohesion: 0.50
Nodes (3): Any, SECONDS, Do a series of flat fields. Args: count: Number of images to take Returns:…

### Community 341 - "test_istructuredconfig.py"
Cohesion: 0.13
Nodes (18): ConfigAppliedState, IStructuredConfig, Any, ConfigValue, The module accepts a whole structured (possibly nested) config object in one…, Apply a full structured config to this module. Args: config: Nested dict…, DummyConfig, DummyStructuredConfigModule (+10 more)

### Community 342 - "transitimaging.py"
Cohesion: 0.21
Nodes (6): Imaging script that runs until the end of a transit window. Requires a…, Whether this script can currently run. In addition to ImagingScript checks,…, Returns the TransitMerit from the task, or None., Run script. Raises: InterruptedError: If interrupted. ValueError: If no…, Estimate duration of the transit observation. Args: data: Task data containing…, TransitImagingScript

### Community 343 - "pyobs.modules.weather (doc)"
Cohesion: 1.00
Nodes (3): pyobs.modules.weather (doc), MockWeather, Weather (module)

### Community 345 - "IPointingAltAz"
Cohesion: 0.20
Nodes (7): IPointingAltAz, Any, DEGREES, The module can move to Alt/Az coordinates, usually combined with…, Moves to given coordinates. Args: alt: Alt in deg to move to. az: Az in deg to…, Move telescope. Args: telescope: Telescope to use., Move telescope. Args: telescope: Telescope to use.

### Community 346 - ".move_radec"
Cohesion: 0.50
Nodes (3): Any, DEGREES, Starts tracking on given coordinates. Args: ra: RA in deg to track. dec: Dec in…

### Community 347 - "test_pointing.py"
Cohesion: 0.70
Nodes (4): make_pointing_module(), asyncio, test_abort_is_noop(), test_run_points_telescope()

### Community 349 - "_DummyTelescopeBase"
Cohesion: 0.06
Nodes (27): ARCSEC_PER_SEC, ICooling, The module can control the cooling of a device., ITemperatures, The module can return temperatures measured on some device., SensorReading, TemperaturesState, ITrackingRate (+19 more)

### Community 350 - ".set_cooling"
Cohesion: 0.50
Nodes (3): CELSIUS, Any, Enables/disables cooling and sets setpoint. Args: enabled: Enable or disable…

### Community 351 - "README.md"
Cohesion: 0.50
Nodes (3): pyobs CLI (foreground module runner), pyobsd CLI (background daemon manager), pyobsw CLI (Windows equivalent of pyobs)

### Community 352 - "Install-ejabberd (xmpp)"
Cohesion: 0.83
Nodes (3): restore_perms(), install-ejabberd.sh script, yq_is_correct_variant()

### Community 353 - "XmppComm._disconnected"
Cohesion: 0.50
Nodes (3): ADR-0002: XMPP stream-error conflict quits instead of reconnecting, XMPP stream-error condition 'conflict' (RFC 6120 §4.9.3), XmppComm._disconnected()

### Community 356 - "pyobs.modules.pointing (doc)"
Cohesion: 1.00
Nodes (3): pyobs.modules.pointing (doc), Acquisition (pointing module), BaseGuiding

### Community 369 - "ejabberd 10x Shaper Benchmark Config"
Cohesion: 0.67
Nodes (3): ejabberd 10x Shaper Benchmark Config, ejabberd.yml (production default shaper), Throughput benchmark: shaper comparison

### Community 371 - "ADR-0005: IConfig stays a stringly-keyed fallback"
Cohesion: 0.67
Nodes (3): ADR-0005: IConfig stays a stringly-keyed fallback, IConfig, specs/design/istructuredconfig.md

### Community 372 - "Exception handling across the RPC boundary (design doc)"
Cohesion: 0.67
Nodes (3): Exception handling across the RPC boundary (design doc), Issue #446 (redundant local exception logging), PyObsError exception hierarchy

## Ambiguous Edges - Review These
- `Configuration utilities (pyobs.utils.config) API doc` → `Coordinate utilities (pyobs.utils.coordinates) API doc`  [AMBIGUOUS]
  docs/source/api/utils/coordinates.rst · relation: conceptually_related_to
- `PyObsError` → `ScriptRunner.run()`  [AMBIGUOUS]
  specs/design/exception_handling.md · relation: conceptually_related_to
- `FocusError` → `FocusModel.set_optimal_focus`  [AMBIGUOUS]
  specs/design/exception_handling.md · relation: conceptually_related_to

## Knowledge Gaps
- **655 isolated node(s):** `autocompletion.bash script`, `OpticalElement`, `OpticalElementGroup`, `Mode`, `ModeType` (+650 more)
  These have ≤1 connection - possible missing edges or undocumented components.
- **37 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **What is the exact relationship between `Configuration utilities (pyobs.utils.config) API doc` and `Coordinate utilities (pyobs.utils.coordinates) API doc`?**
  _Edge tagged AMBIGUOUS (relation: conceptually_related_to) - confidence is low._
- **What is the exact relationship between `PyObsError` and `ScriptRunner.run()`?**
  _Edge tagged AMBIGUOUS (relation: conceptually_related_to) - confidence is low._
- **What is the exact relationship between `FocusError` and `FocusModel.set_optimal_focus`?**
  _Edge tagged AMBIGUOUS (relation: conceptually_related_to) - confidence is low._
- **Why does `Time` connect `Time` to `LcoTaskArchive`, `Task`, `Module`, `OffsetResult`, `test_mastermind.py`, `ImageProcessor`, `Interface`, `DummyCamera`, `BackendTaskArchive`, `Event`, `test_flatfielder.py`, `tests/test_events.py`, `test_lco_http.py`, `DummySolarTelescope`, `DummyRaDecTelescope`, `test_control.py`, `SolarElevationConstraint`, `dummycamera.py`, `xmppcomm.py`, `LcoTask`, `test_transitimaging.py`, `robotic/test_scheduler.py`, `RuntimeError`, `Calibration`, `Proxy`, `FilenameFormatter`, `test_yaml_archives.py`, `test_schedulewriter.py`, `FlatFielder`, `DynamicTarget`, `TimeDelta`, `Offsets`, `.now`, `test_proxy.py`, `Scheduler`, `TaskData`, `Weather`, `test_csvpicker_scheduler.py`, `test_pyobs_archive.py`, `Archive`, `lco/task.py`, `test_coordinates.py`, `Portal`, `LocalArchive`, `CommLoggingHandler`, `ImagingScript`, `FocusModel`, `test_darkbias.py`, `Script`, `MotionStatusChangedEvent`, `SiderealTarget`, `Grid`, `pyobs.py`, `Scheduler`, `Pipeline`, `test_basetelescope.py`, `pyobs/modules/utils/__init__.py`, `robotic/task.py`, `BaseTelescope`, `ExpTimeEval`, `storage/taskarchive.py`, `test_transit_mastermind.py`, `test_scheduler_mastermind.py`, `ImageType`, `flatfield/test_scheduler.py`, `test_schedulereader.py`, `test_backend_archives.py`, `RunningState`, `weather.py`, `http_request_paginated`, `test_autofocus.py`, `SkyflatPriorities`, `TaskStartedEvent`, `.phase_for_jd`, `Object`, `SkyFlatsBasePointing`, `test_imagewriter.py`, `PrimaryHDU`, `filters.py`, `time.py`, `InfluxHandler`, `ObservationList`, `test_astroplanscheduler.py`, `PyobsArchive`, `_baseguiding.py`, `CasesRunner`, `.night_obs`, `.sun_altaz`, `_ProxyContext`, `.night`, `transitimaging.py`, `_DummyTelescopeBase`?**
  _High betweenness centrality (0.253) - this node is a cross-community bridge._
- **Why does `Image` connect `Image` to `_PhotometryCalculator`, `sourcedetection.py`, `PrimaryHDU`, `OffsetResult`, `ImageProcessor`, `GuidingStatisticsSkyOffset`, `DummyCamera`, `utils/exceptions.py`, `GuidingStatisticsPixelOffset`, `VirtualFileSystem`, `Pipeline`, `NewImageEvent`, `mixins/test_fitsheader.py`, `GuidingStatistics`, `PipelineMixin`, `AstrometryDotNet`, `time.py`, `test_flatfielder.py`, `SoftBin`, `AddMask`, `dummycamera.py`, `SepSourceDetection`, `Photometry`, `PyobsArchive`, `FitsHeaderOffsets`, `ProjectionFocusSeries`, `_SepAperturePhotometry`, `_baseguiding.py`, `RuntimeError`, `Calibration`, `ImageType`, `test_autoguiding.py`, `FilenameFormatter`, `test_basevideo.py`, `CatalogCircularMask`, `Offsets`, `AperturePhotometry`, `DaophotSourceDetection`, `test_acquisition.py`, `BaseVideo`, `test_pipeline_on_error.py`, `Ring`, `_DaoBackgroundRemover`, `Smooth`, `ProjectedOffsets`, `test_pyobs_archive.py`, `Archive`, `FocusSeries`, `_SourceCatalog`, `Any`, `LocalArchive`, `_PhotUtilAperturePhotometry`, `VFSFile`, `PillowHelper`, `ImageSourceFilter`, `_ResponseImageWriter`?**
  _High betweenness centrality (0.140) - this node is a cross-community bridge._
- **Why does `Module` connect `Module` to `FlatField`, `Time`, `test_mastermind.py`, `._get_client`, `MockWeather`, `XmppComm`, `Interface`, `pyobs.py`, `test_presence.py`, `utils/exceptions.py`, `Scheduler`, `test_dummymode.py`, `test_kiosk.py`, `mixins/test_fitsheader.py`, `PipelineMixin`, `time.py`, `pyobs/modules/utils/__init__.py`, `dummycamera.py`, `BaseTelescope`, `xmppcomm.py`, `DummyMode`, `test_follow.py`, `Comm`, `robotic/test_scheduler.py`, `StandAlone`, `HttpFileCache`, `_baseguiding.py`, `RPC`, `WindowCapabilities`, `Kiosk`, `ScriptRunner`, `test_camerasettings.py`, `test_startup_gating.py`, `test_autoguiding.py`, `test_basevideo.py`, `PointingSeries`, `GridNode`, `flatfield/test_scheduler.py`, `Telegram`, `.__init__`, `RunningState`, `test_acquisition.py`, `Weather`, `IWindow`, `Stellarium`, `BaseVideo`, `weather.py`, `test_exception_logging.py`, `Application`, `application.py`, `make_proxy_cm`, `ImageWatcher`, `Object`, `FocusModel`, `DataCache`, `test_imagewriter.py`?**
  _High betweenness centrality (0.083) - this node is a cross-community bridge._
- **Are the 167 inferred relationships involving `Time` (e.g. with `PyobsCLI` and `Proxy`) actually correct?**
  _`Time` has 167 INFERRED edges - model-reasoned connections that need verification._