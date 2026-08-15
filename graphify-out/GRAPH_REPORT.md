# Graph Report - pyobs-core  (2026-08-15)

## Corpus Check
- 783 files · ~412,199 words
- Verdict: corpus is large enough that graph structure adds value.

## Summary
- 8707 nodes · 20956 edges · 417 communities (371 shown, 46 thin omitted)
- Extraction: 93% EXTRACTED · 7% INFERRED · 0% AMBIGUOUS · INFERRED: 1364 edges (avg confidence: 0.55)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `0159542f`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- FitsHeaderEntry
- BaseGuiding
- Time
- RunningState
- Interface
- Module
- Image
- test_units.py
- Events API doc (pyobs.events)
- ImageProcessor
- TaskData
- test_yaml_archives.py
- MultiModule
- XmppComm
- AstrometryDotNet
- FilenameFormatter
- TimeDelta
- .__init__
- DummyRoof
- mixins/test_fitsheader.py
- Event
- PipelineMixin
- http_request_with_retries
- test_flatfielder.py
- LocalComm
- tests/test_events.py
- Any
- FlatField
- _clear_vfs_buffer
- WindowingWidget
- Interfaces (pyobs.interfaces) API doc
- test_control.py
- test_presence.py
- _DotNetRequest
- Object
- basetelescope.py
- Future
- test_backend_archives.py
- CoolingState
- IPointingAltAz.py
- AstroplanScheduler
- .can_run
- Any
- Any
- imaging.py
- robotic/test_scheduler.py
- StandAlone
- utils/exceptions.py
- module.py
- test_stellarexptime.py
- StarExpTimeEstimator
- xmpp/rpc.py
- test_xmpp_presence.py
- test_shellcommand.py
- Calibration
- .get_object
- Publisher
- PillowHelper
- test_acquisition.py
- Proxy
- fitssec
- test_basevideo.py
- .register_event
- ScienceFrameAutoGuiding
- FlatFielder
- IExposure
- Telegram
- benchmark_state_throughput.py
- ModuleState
- Offsets
- .now
- PyObsError
- test_proxy.py
- XEP_0009
- SiderealTarget
- PyobsDaemon
- MockWeather
- test_config.py
- .set_image_type
- test_autoguiding.py
- Weather
- MotionStatusChangedEvent
- SkyOffsets
- MotionStatus
- test_xmpp_rpc.py
- Ring
- DummySolarTelescope
- xmppcomm.py
- test_exception_logging.py
- DummyCamera
- Application
- DummyComm
- CallModuleScript
- ProjectedOffsets
- test_pyobs_archive.py
- HttpFile
- .__init__
- application.py
- FocusSeries
- _SourceCatalog
- make_proxy_cm
- WeatherSensors
- ScriptRunner
- ResolvableErrorLogger
- test_coordinates.py
- get_registered_interface
- _DotNetRequestBuilder
- LocalArchive
- Plan: Systematic ejabberd throughput/latency benchmarking
- _PhotUtilAperturePhotometry
- Mixins (pyobs.mixins) API doc
- Script base class
- test_background_task.py
- Test Commlogging (comm)
- .__init__
- test_dummyradectelescope.py
- ImagingScript
- test_localcomm_state.py
- MemoryFile
- VFSFile
- LocalFile
- test_version_mismatch.py
- CLAUDE.md (repo guide)
- SFTPFile
- FocusModel
- _AbortableModule
- ImageSourceFilter
- test_darkbias.py
- BackendTaskArchive
- .__init__
- Plan: pyobs-pipeline
- Test Localcomm (local)
- _SepAperturePhotometry
- ExposureTimeProvider
- Any
- test_dummymode.py
- ._client_disconnected
- test_autofocus.py
- Grid
- test_kiosk.py
- pyobs.py
- Robotic recipe (doc)
- is_valid_jid
- IModule
- test_config_schema.py
- DummyRaDecTelescope
- Scheduler
- RollingTimeAverage
- .__init__
- Kiosk
- tests/xmpp/docker-compose.yml (ejabberd integration test container)
- `OBSNUM`: per-night observation counter in FITS headers
- 3rd party packages (doc)
- _DaoBackgroundRemover
- SSHFile
- create_rst.py
- .__init__
- SoftBin
- AddMask
- ImageType
- SkyCoord
- comm/test_events.py
- WeatherState
- LogEvent
- ._update_root
- ExpTimeEval
- Stellarium
- Overview (doc)
- .__init__
- GuidingStatisticsPixelOffset
- test_module_state_publishing.py
- .abort
- test_grab_sequence.py
- binding.py
- NewSpectrumEvent
- .get_config_value
- CLI
- .get_interfaces
- SkyflatPriorities
- .grab_data
- Steering: astropy IERS auto-download blocks event loop
- test_schedulereader.py
- test_istructuredconfig.py
- .set_filter
- Merit
- ejabberd shaper throttling bug (xmpp_socket.erl re-arm) & fix
- WeatherStatus
- Any
- Work Plan
- Plan: `pyobs-gui` TelescopeWidget layout — width floor investigation & design notes
- PointingSeries
- GridNode
- .set_tracking_rate
- Any
- What's New in pyobs 2.0 (doc)
- TaskStartedEvent
- test_imagewatcher.py
- CatalogCircularMask
- Header
- ImageWatcher
- ObservationList
- test_xmpp_acl.py
- show_module_info.py
- integration/conftest.py
- .set_cooling
- robotic
- Scheduler module
- BaseModel (pyobs.utils.serialization)
- Decision
- Smooth
- flatfield/scheduler.py
- HttpFileCache
- Plan: Widget plugin mechanism + `pyside6-deploy` packaging for `pyobs-gui`
- Plan: Split archive prefetch from CPU-bound merit evaluation, to unblock a `ProcessPoolExecutor`
- Image (pyobs.images.processors.image) API doc
- Offsets (pyobs.images.processors.offsets) API doc
- Constraint
- flatfield/test_scheduler.py
- NewImageEvent
- .move_heliocentric_polar
- .move_heliographic_stonyhurst
- FileList
- .move_helioprojective
- TempFile
- pyobs 2.0 Wire Protocol, State, and Access Control design doc
- Findings: driver/gui correctness review, all 8 repos (reviewed 2026-08-11)
- ImageFormat
- CHANGELOG.rst
- Use a self-hosted Keycloak alongside odin, as two parallel auth backends
- Image class
- NamedTuple
- .set_config
- Module.startup() lifecycle helper
- .night_obs
- Plan: Stop scheduler constraint/merit evaluation from blocking the event loop
- .__init__
- test_basecamera.py
- SMBFile
- pyobs-gui as a standalone binary (umbrella design)
- Plan: Enforce state publishing for stateful interfaces
- Plan: `pyobs-gui` login window
- test_safe_send.py
- test_pyobsd.py
- Two-phase Object lifecycle; rationale: __init__ must not touch hardware/external services (only store params, create children, register background tasks); open() is where side effects happen, so objects can be constructed cheaply/safely before being started
- Simulation recipe (doc)
- ExposureTimeState
- test_baseroof.py
- Decision
- BufferedFile
- XEP_0009_timeout
- robotic
- Archive (image archive base)
- ._get_client
- BaseVideo
- RaDecOffsets
- ._get_next
- Shared authentication across pyobs web projects via Keycloak
- Plan: `pyobs-gui` navbar keyboard shortcuts
- filters.py
- BaseCamera
- Image.trim
- conftest.py
- Misc (pyobs.images.processors.misc) API doc
- PolymorphicBaseModel
- test_memory_archives.py
- wait_for
- Target
- GoodWeatherEvent
- Implementation
- Plan: Interactive login/settings dialog for `pyobs-gui`, deferring `Application`'s module construction
- pyobs.modules.utils (doc)
- Plan: Add baseline tests to core-tier repos, then enable grouped Dependabot auto-merge
- Plan: CORS + token auth for `HttpFileCache`
- TaskFinishedEvent
- Plan: `pyobs-gui` IAutoGuiding widget
- _dummytelescopebase.py
- Investigation: pyobs-gui receives every LogEvent twice (SAAO/monet production)
- OffsetResult
- Plan: `pyobs-gui` IAutoFocus widget
- ADR-0008: _safe_send keeps bounded retry unlike capability/subscribe fetches
- Module._watch_event_loop_lag
- Plan: Surface unrecognized kwargs in `Object.__init__` instead of silently discarding them
- pyobs.modules.image (doc)
- Plan: `pyobs-auth` + Keycloak integration
- Plan: Exception handling across the RPC boundary (reconstructed)
- Plan: Decouple `ICamera`/`IExposure` (reconstructed)
- Plan: `IDataSequence` — server-side counted data sequences (reconstructed)
- Plan: Unify TRIMSEC handling into `Image.trim()` (reconstructed)
- Plan: Module observer-location capabilities (reconstructed)
- Plan: Advertise event send/subscribe role in disco#info
- Plan: raw-frame streaming endpoint in `BaseVideo`
- .set_gain
- Implemented
- Plan: `pyobs-gui` IAcquisition widget
- ModuleLocation dataclass (nested in ModuleCapabilities)
- check_pyobs_releases.sh
- check_ejabberd_notify.py
- _ProxyContext
- MockBaseDome
- test_exceptions.py
- Photometry (pyobs.images.processors.photometry) API doc
- IDataSequence
- IFocuser
- weather.py
- object.py
- DataFrame
- floating
- NDArray
- .__init__
- Comm
- IFlatField
- ._subscribe_presence
- .set_offsets_altaz
- Pipeline
- IRotation
- pyobs.modules.weather (doc)
- Any
- NamedTuple
- NDArray
- Response
- README.md
- Install-ejabberd (xmpp)
- XmppComm._disconnected
- Autocompletion ()
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
1. `Time` - 578 edges
2. `Image` - 437 edges
3. `Task` - 227 edges
4. `Interface` - 186 edges
5. `Module` - 176 edges
6. `ObservationList` - 168 edges
7. `DataProvider` - 168 edges
8. `Event` - 145 edges
9. `Comm` - 113 edges
10. `Object` - 110 edges

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

## Communities (417 total, 46 thin omitted)

### Community 0 - "FitsHeaderEntry"
Cohesion: 0.06
Nodes (27): IDome, The module controls a dome, i.e. a :class:`~pyobs.interfaces.IRoof` with a…, Any, Returns FITS header for the current status of this module. Args: namespaces: If…, FitsHeaderEntry, Any, Returns FITS header for the current status of this module. Args: namespaces: If…, IRoof (+19 more)

### Community 1 - "BaseGuiding"
Cohesion: 0.05
Nodes (31): GuidingState, IAutoGuiding, The module can perform auto-guiding., IExposureTime, Any, SECONDS, The camera supports exposure times, to be used together with…, Set the exposure time in seconds. Args: exposure_time: Exposure time in… (+23 more)

### Community 2 - "Time"
Cohesion: 0.02
Nodes (156): AtNightConstraint, AirmassConstraint, ndarray, SkyCoord, Constraint, ndarray, SkyCoord, Returns a boolean mask of candidates passing this constraint. Default… (+148 more)

### Community 3 - "RunningState"
Cohesion: 0.03
Nodes (77): F, ExpTime, IAbortable, Any, Abort current actions., The module has an abortable action., AcquisitionAttempt, AcquisitionResult (+69 more)

### Community 4 - "Interface"
Cohesion: 0.03
Nodes (99): ABC, IAutonomous, The module does some autonomous actions, mainly used for warnings to users., Binning, BinningCapabilities, BinningState, ICalibrate, Any (+91 more)

### Community 5 - "Module"
Cohesion: 0.05
Nodes (32): AbstractEventLoop, setter, The module that this Comm object is attached to., The module that this Comm object is attached to., Called, when the module connected to this Comm changes. Args: module: The…, Module, Exception, Base class for all pyobs modules. (+24 more)

### Community 6 - "Image"
Cohesion: 0.03
Nodes (90): ImageHDU, MetaClass, Image, Any, CCDData, floating, HDUList, Header (+82 more)

### Community 7 - "test_units.py"
Cohesion: 0.10
Nodes (24): _extract_unit(), _interface_unit_hints(), Any, Return Unit annotations from the abstract interface declaration for method_name., Convert annotated float parameters to astropy Quantities before the method…, with_units(), Focuser, IFocus (+16 more)

### Community 8 - "Events API doc (pyobs.events)"
Cohesion: 0.06
Nodes (33): Comm API doc (pyobs.comm), Events API doc (pyobs.events), ExposureStatusChangedEvent, Any, Event to be sent, when the exposure status of a device changes., ExposureState, BaseSpectrograph, ExposureInfo (+25 more)

### Community 9 - "ImageProcessor"
Cohesion: 0.02
Nodes (80): Some info about :class:`pyobs.images.Image`., ImageProcessor, Any, Init new image processor. Args: on_error: How the pipeline should handle an…, The error handling mode for this step., Processes an image. Args: image: Image to process. Returns: Processed image., Resets state of image processor, Any (+72 more)

### Community 10 - "TaskData"
Cohesion: 0.03
Nodes (67): datetime, Estimate duration of the dark/bias series., PointingScript, Script for pointing the telescope for flats., Whether this config can currently run. Returns: True if script can run now., Run script. Raises: InterruptedError: If interrupted, Estimate duration of slewing to the flat-field pointing., # TODO: get a better estimate for slewing (+59 more)

### Community 11 - "test_yaml_archives.py"
Cohesion: 0.07
Nodes (47): Any, DataFrame, HDUList, Convenience function for writing an Image to a FITS file. Args: filename: Name…, Convenience function for writing an Image to a FITS file. Args: filename: Name…, Convenience function for writing bytes to a file. Args: filename: Name of file…, Convenience function for reading a CSV file into a DataFrame. Args: filename:…, Convenience function for writing a CSV file from a DataFrame. Args: filename:… (+39 more)

### Community 12 - "MultiModule"
Cohesion: 0.09
Nodes (10): A module in *pyobs* is the smalles executable unit. The base class for all…, MultiModule, Wait until all sub-module tasks have finished., Cancel sub-module tasks and close shared objects., Quit all sub-modules., Wrapper for running multiple modules in a single process., Checks, whether this multi-module contains a module of given name., Returns module of given name. (+2 more)

### Community 13 - "XmppComm"
Cohesion: 0.05
Nodes (36): Any, Store published capabilities for inclusion in disco#info responses., Return this client's own published capabilities., Fetch and deserialize capabilities for a remote module's interface. Retries…, Subscribe to a pubsub node, retrying until the node exists. Runs as a…, Create a new XMPP Comm module. Either a fill JID needs to be provided, or a set…, Sleep a little and reconnect, Reset connection after disconnect. (+28 more)

### Community 14 - "AstrometryDotNet"
Cohesion: 0.05
Nodes (37): ImageProcessor on_error kwarg / per-step error handling, Astrometry processors doc, AstrometryDotNet (astrometry processor), Astrometry, Finds astrometric solution to a given image. Args: image: Image to analyse.…, Base class for astrometry processors, AstrometryDotNet, Deprecated, use on_error instead. (+29 more)

### Community 15 - "FilenameFormatter"
Cohesion: 0.07
Nodes (29): Format filename with given formatter., CreateFilename, Any, Add filename to image. Args: image: Image to add filename to. Returns: Image…, Format and set a filename for the image using a pattern, storing it in the…, Init an image processor that adds a filename to an image. Args: pattern:…, FilenameFormatter, format_filename() (+21 more)

### Community 16 - "TimeDelta"
Cohesion: 0.06
Nodes (59): ConstantMerit, Merit function that returns a constant value., model_validator, Self, Merit function that uses time windows., TimeWindow, TimeWindowMerit, OnDemandScheduler (+51 more)

### Community 17 - ".__init__"
Cohesion: 0.08
Nodes (15): Args: label: Label for module. If None, name is used. own_comm: If True, module…, Returns name of module., Parse the optional "acl" config block into _acl_allow/_acl_deny/_acl_mode.…, Expand any interface names (e.g. "ICamera") in an "allow" entry list into that…, List interfaces and methods of this module., Returns a dictionary with config caps., Check for getter and setter Params: name: Name of variable. Returns: Tuple of…, Returns dict of all config capabilities. First value is whether it has a… (+7 more)

### Community 18 - "DummyRoof"
Cohesion: 0.14
Nodes (17): DummyRoof, Any, Get the percentage the roof is open., Stop the motion. Args: device: Name of device to stop, or None for all. Raises:…, A dummy camera for testing., Creates a new dummy root., Open the roof. Raises: InitError: If the roof could not be initialized (e.g.…, Close the roof. Raises: ParkError: If the roof could not be parked (e.g.… (+9 more)

### Community 19 - "mixins/test_fitsheader.py"
Cohesion: 0.06
Nodes (66): FitsHeaderMixin, ImageFitsHeaderMixin, Any, PrimaryHDU, Add requested FITS headers to header of given image. Args: image: Image with…, Add FITS header keywords to the given FITS header. Args: image: Image with…, Add FRAMENUM keyword to header Args: image: Image with header to add to., Helper methods for all modules that implement IImageGrabber. (+58 more)

### Community 20 - "Event"
Cohesion: 0.06
Nodes (47): Event, Base class for all events., DataType, TypedDict, DataType, TypedDict, DataType, TypedDict (+39 more)

### Community 21 - "PipelineMixin"
Cohesion: 0.05
Nodes (48): Handle an ImageError raised by this step, when on_error == "error". Override…, PipelineMixin, Any, Mixin for a module that needs to implement an image pipeline., Initializes the mixin. Args: steps: Pipeline steps to run on images. archive:…, Resets all previous state of the involved image processors., Run the pipeline on the given image. Each step is run, and an ImageError it…, PipelineCamera (+40 more)

### Community 22 - "http_request_with_retries"
Cohesion: 0.18
Nodes (26): http_request_paginated(), http_request_with_retries(), Any, ClientSession, Fetches all pages of a DRF-style paginated list endpoint and returns the…, retry, make_response(), make_session() (+18 more)

### Community 23 - "test_flatfielder.py"
Cohesion: 0.08
Nodes (60): make_flatfielder(), make_observer(), make_twilight_observer(), asyncio, parametrize, Regression test for #481: median == bias_level used to raise ZeroDivisionError., Observer stub returning a constant solar altitude for every sun_altaz() call., Observer stub distinguishing the first (now) vs second (+10min) sun_altaz()… (+52 more)

### Community 24 - "LocalComm"
Cohesion: 0.07
Nodes (22): LocalComm, Any, Store capabilities locally., Return this client's own published capabilities., Fetch capabilities from a remote module., Store presence state and dispatch to all subscribers., Return presence state of a connected module., Announce this module to already-connected peers, mirroring XmppComm's presence-… (+14 more)

### Community 25 - "tests/test_events.py"
Cohesion: 0.05
Nodes (51): BadWeatherEvent, Event to be sent on bad weather., Create Event from a dictionary. Args: obj_dict: JSON string for event. Returns:…, FilterChangedEvent, Event to be sent when a filter has been changed., FocusFoundEvent, Event to be sent when a new best focus has been found, e.g. after a focus…, ModeChangedEvent (+43 more)

### Community 26 - "Any"
Cohesion: 0.10
Nodes (12): Any, ConfigValue, Signature, Watch for repeated occurrences of exc_type -- optionally scoped to a specific…, Whether the acl policy denies `sender` calling `method`, ignoring `mode`…, Execute a local method safely with type conversion All incoming variables in…, Returns current value of config item with given name. Args: name: Name of…, Returns possible values for config item with given name. Args: name: Name of… (+4 more)

### Community 27 - "FlatField"
Cohesion: 0.16
Nodes (10): FlatField, Any, List available binnings. Returns: List of available binnings as (x, y) tuples., Set the camera binning. Args: x: X binning. y: Y binning. Raises: ValueError:…, List available filters. Returns: List of available filters., Set the current filter. Args: filter_name: Name of filter to set., Do a series of flat fields in the given filter. Args: count: Number of images…, Abort current actions. (+2 more)

### Community 28 - "_clear_vfs_buffer"
Cohesion: 0.67
Nodes (3): _clear_vfs_buffer(), fixture, MemoryFile's buffer is a process-wide class dict; every Mastermind instance in…

### Community 29 - "WindowingWidget"
Cohesion: 0.05
Nodes (14): BinningWidget, DataDisplayWidget, PrimaryHDU, Slot, Select path for auto-saving., ExposeWidget, Slot, ExposureTimeWidget (+6 more)

### Community 30 - "Interfaces (pyobs.interfaces) API doc"
Cohesion: 0.04
Nodes (53): Interfaces (pyobs.interfaces) API doc, IAbortable, IAcquisition, IAutoFocus, IAutoGuiding, IAutonomous, IBinning, ICalibrate (+45 more)

### Community 31 - "test_control.py"
Cohesion: 0.08
Nodes (53): CasesRunner, Script for distinguishing cases., Returns FITS header for the current status of this module. Args: namespaces: If…, ConditionalRunner, Script for running an if condition., Returns FITS header for the current status of this module. Args: namespaces: If…, ParallelRunner, Script for running other scripts in parallel. (+45 more)

### Community 32 - "test_presence.py"
Cohesion: 0.05
Nodes (51): ModuleOpenedEvent, Event to be sent when a module has opened., ModuleLocation, _FakeProxyContext, make_xmpp_comm(), asyncio, Tests for Phase 2.5 Presence and Capabilities implementation., Module.open() passes empty string for label when _label is None. (+43 more)

### Community 33 - "_DotNetRequest"
Cohesion: 0.22
Nodes (4): _DotNetRequest, Any, asyncio, test_generate_request_error_msg()

### Community 34 - "Object"
Cohesion: 0.02
Nodes (183): InstrumentLocation, PydanticBaseModel, Object, Base class for all objects in *pyobs*., Whether object has been opened., Can be overloaded to quit program., Any, AcquisitionConfig (+175 more)

### Community 35 - "basetelescope.py"
Cohesion: 0.04
Nodes (65): IFitsHeaderBefore, The module provides some additional header entries for FITS headers before some…, OrbitalElements, Any, Starts tracking a body defined by orbital elements. Args: elements: Orbital…, TrackingRateState, AltitudeLimitError, BaseTelescope (+57 more)

### Community 36 - "Future"
Cohesion: 0.07
Nodes (39): Wait until all devices are in one of the given motion states. Args: abort:…, Any, Target, Loop instrument configurations until the transit window ends., Run script. Raises: InterruptedError: If interrupted, acquire_lock(), event_wait(), Future (+31 more)

### Community 37 - "test_backend_archives.py"
Cohesion: 0.21
Nodes (30): make_obs(), make_obs_archive(), make_task(), make_task_archive(), asyncio, time parameter is unused — backend returns cached observations., Backend uses strictly exclusive boundaries (start < time < end)., fetch_task is called with task_archive when provided. (+22 more)

### Community 38 - "CoolingState"
Cohesion: 0.08
Nodes (33): _dataclass_to_xml(), _event_schema_to_xml(), _interface_schema_to_xml(), _parse_scalar(), Any, Element, Shared XML serializer for pyobs 2.0 (urn:pyobs:rpc:1). Both the state pub/sub…, Deserialize an XML element (produced by ``value_to_xml``) to a Python value.… (+25 more)

### Community 39 - "IPointingAltAz.py"
Cohesion: 0.04
Nodes (58): AltAzState, IPointingAltAz, Any, DEGREES, The module can move to Alt/Az coordinates, usually combined with…, Moves to given coordinates. Args: alt: Alt in deg to move to. az: Az in deg to…, IPointingRaDec, Any (+50 more)

### Community 40 - "AstroplanScheduler"
Cohesion: 0.23
Nodes (9): AstroplanScheduler, Any, ObservingBlock, Actually do the scheduling, usually run in a separate process., Scheduler based on astroplan., Initialize a new scheduler. Args: twilight: astronomical or nautical, Queue, fixture (+1 more)

### Community 41 - ".can_run"
Cohesion: 0.47
Nodes (3): Target, Checks, whether this task could run now. Args: task: Task to run target:…, Run a task. Args: task: Task to run target: Resolved target for this specific…

### Community 42 - "Any"
Cohesion: 0.12
Nodes (15): Any, DataFrame, floating, ImageType, NDArray, Set the image type. Args: image_type: New image type., Create a JPEG ge from a numpy array and return as bytes. Args: data: Numpy…, Create FITS and JPEG images from data. (+7 more)

### Community 43 - "Any"
Cohesion: 0.10
Nodes (14): Any, ProxyType, Returns object directly if it is of given type. Otherwise get proxy of client…, Backend hook, called when a proxy exists but doesn't implement obj_type.…, Calls proxy() in a safe way and returns None instead of raising an exception., Returns a context manager; use as `async with self.proxy(...) as x:`., Same as proxy(), but yields None inside the block instead of raising., True if a proxy of the given type can currently be resolved. Doesn't keep a… (+6 more)

### Community 44 - "imaging.py"
Cohesion: 0.07
Nodes (42): EarthLocation, model_validator, Self, SkyCoord, Merit function for observing transits., Returns the time of the next mid-transit., Returns the time until which observations should run: mid-transit + duration/2…, TransitMerit (+34 more)

### Community 45 - "robotic/test_scheduler.py"
Cohesion: 0.13
Nodes (39): Scheduler, DummyTask, make_async_gen(), make_obs(), make_scheduler(), asyncio, Regression test: _on_task_finished is registered for both TaskFinishedEvent and…, _state_for() (+31 more)

### Community 46 - "StandAlone"
Cohesion: 0.09
Nodes (40): pyobs.modules.test (doc), StandAlone, Quickstart (doc), pyobs-core (pip package), Test modules. TODO: write doc, Any, Example module that only logs the given message forever in the given interval., Creates a new StandAlone object. Args: message: Message to log in the given… (+32 more)

### Community 47 - "utils/exceptions.py"
Cohesion: 0.07
Nodes (33): Grabs an image and returns reference. Args: broadcast: Broadcast existence of…, Declare that the given PyobsError types (and their subclasses) fire often…, AbortedError, AcquisitionError, DeviceBusyError, ExceptionHandler, GeneralError, GrabImageError (+25 more)

### Community 48 - "module.py"
Cohesion: 0.18
Nodes (5): ConfigCapabilities, Returns label of module., Returns pyobs version of module., React to other modules connecting., version()

### Community 49 - "test_stellarexptime.py"
Cohesion: 0.11
Nodes (34): ndarray, Find the brightest star near the image centre by fitting a 2D Gaussian. Args:…, Determines exposure time by finding a star near the image centre and adjusting…, Determine the optimal exposure time. Returns: Optimal exposure time in seconds., StellarExposureTimeProvider, attach_proxies(), make_camera_mocks(), make_image() (+26 more)

### Community 50 - "StarExpTimeEstimator"
Cohesion: 0.07
Nodes (25): Exposure Time estimators doc, ExpTimeEstimator (exptime processor base), StarExpTimeEstimator (exptime processor), ExpTimeEstimator, Any, Estimate exposure time., Init new exposure time estimator., Any (+17 more)

### Community 51 - "xmpp/rpc.py"
Cohesion: 0.09
Nodes (23): fault_to_xml(), params_to_xml(), Any, ClientXMPP, Element, Exception, Parse <fault> and return (exception_qualified_name, message)., RPC wrapper around XEP-0009 using pyobs 2.0 payload encoding (urn:pyobs:rpc:1). (+15 more)

### Community 52 - "test_xmpp_presence.py"
Cohesion: 0.08
Nodes (40): ModuleCapabilities, make_module(), Minimal module stub satisfying what XmppComm needs on connect. IModule must be…, get_capabilities_from_disco(), Integration tests for Phase 2.5 Presence and Discovery. Requires a live…, LOCAL state must arrive as away presence., Module.set_state() must automatically push presence — no explicit call., subscribe_presence fires immediately with current state and again on each… (+32 more)

### Community 53 - "test_shellcommand.py"
Cohesion: 0.10
Nodes (29): ParserState, Any, Enum, ShellCommand, ShellCommandResponse, asyncio, test_command_number_increments(), test_execute_invalid_param() (+21 more)

### Community 54 - "Calibration"
Cohesion: 0.06
Nodes (30): Additional Modules index (docs), Image processors index (docs), Calibration processors doc, _CalibrationCache, Calibration, Any, Init a new image calibration pipeline step. Args: archive: Archive to fetch…, Calibrate an image. Args: image: Image to calibrate. Returns: Calibrated image. (+22 more)

### Community 55 - ".get_object"
Cohesion: 0.11
Nodes (18): ObjectClass, PydanticModel, create_object(), get_object(), get_safe_object(), Any, ProxyType, Calls get_object in a safe way and returns None, if an exceptions thrown. Args:… (+10 more)

### Community 56 - "Publisher"
Cohesion: 0.09
Nodes (20): Any, Creates a new seeing estimator. Args: sources: List of sources (e.g. cameras)…, CsvPublisher, Any, DataFrame, Initialize new CSV publisher. Args: filename: Name of file to log in., Publish the given results. Args: **kwargs: Results to publish., Return data that has so far been published. (+12 more)

### Community 57 - "PillowHelper"
Cohesion: 0.18
Nodes (11): Annotation processors doc, Circle, Draw a circle on an image, optionally interpreting the center in WCS…, Draws a circle on the image. Args: image: Image to draw on. Returns: Output…, Crosshair, Drawn a crosshair on the image. Args: image: Image to draw on. Returns: Output…, Draw a crosshair (circle plus orthogonal lines) on an image, optionally using…, PillowHelper (+3 more)

### Community 58 - "test_acquisition.py"
Cohesion: 0.28
Nodes (28): make_acquisition(), make_camera(), make_image(), make_telescope(), asyncio, offsets_frame: 'radec', 'altaz', or None (telescope supports neither offsets…, _state_for(), test_abort_sets_event() (+20 more)

### Community 59 - "Proxy"
Cohesion: 0.06
Nodes (30): Comm responsibility: Method calls (via Proxy), The Comm object is responsible for all communication between modules (see…, Proxy, Any, Signature, Execute a method on the remote client. Args: method: Name of method to call.…, Create local methods for the remote client., Function wrapper for remote calls. Args: method: Name of method to wrap.… (+22 more)

### Community 60 - "fitssec"
Cohesion: 0.23
Nodes (12): fitssec(), parse_section_bounds(), Any, NDArray, Parse a FITS section keyword (e.g. TRIMSEC) into 0-based, half-open slice…, Trim an image to TRIMSEC or BIASSEC. Args: hdu: HDU to take data from. keyword:…, DummyHdu, test_fitssec_no_keyword() (+4 more)

### Community 61 - "test_basevideo.py"
Cohesion: 0.14
Nodes (38): NamedTuple, ImageRequest, LastImage, NextImage, # TODO: find a better way to convert to uint8, make_basevideo(), make_request(), asyncio (+30 more)

### Community 62 - ".register_event"
Cohesion: 0.17
Nodes (5): Background thread for handling the logging., Send an event to other clients. Args: event (Event): Event to send, Return list of given event itself and all events derived from it. Args: event:…, Register an event type. If a handler is given, we also receive those events,…, Remove a handler previously added via register_event(). Leaves the event type…

### Community 63 - "ScienceFrameAutoGuiding"
Cohesion: 0.20
Nodes (7): Any, An auto-guiding system based on comparing collapsed images along the x&y axes…, Initializes a new science frame auto guiding system., Set the exposure time for the auto-guider. Args: exposure_time: Exposure time…, Processes an image asynchronously, returns immediately. Args: event: Event for…, the thread function for processing the images, ScienceFrameAutoGuiding

### Community 64 - "FlatFielder"
Cohesion: 0.08
Nodes (26): ICamera, The module controls a camera., IFilters, The module can change filters in a device., ITelescope, The module controls a telescope., Initialize a new flat fielder. Args: telescope: Name of ITelescope. camera:…, FlatFielder (+18 more)

### Community 65 - "IExposure"
Cohesion: 0.06
Nodes (34): Comm._get_client, ADR-0001: Check Interface.state by own declaration, not inheritance, Composite interfaces inheriting stateful bases (ICamera, IDome, ITelescope, ...), Interface.capabilities (ClassVar), Interface.has_own_state(), Interface.state (ClassVar), XmppComm disco#info feature registration, ADR-0006: Proxy.wait_for_state() returns None on timeout (+26 more)

### Community 66 - "Telegram"
Cohesion: 0.13
Nodes (19): CallbackContext, Any, Save storage file. Args: context: Telegram context., Is user authorized? Args: context: Telegram context. user_id: ID of user.…, Store new user in auth database. Args: context: Telegram context. user_id: ID…, Handle /start command. Args: update: Message to process. context: Telegram…, Handle /exec command. Args: update: Message to process. context: Telegram…, Handle click on buttons. Args: update: Message to process. context: Telegram… (+11 more)

### Community 67 - "benchmark_state_throughput.py"
Cohesion: 0.13
Nodes (32): Open the connection to the XMPP server. Returns: Whether opening was successful., attach_module(), env_config(), main(), make_comm(), maybe_register(), open_publisher(), Any (+24 more)

### Community 68 - "ModuleState"
Cohesion: 0.20
Nodes (6): Send XMPP presence stanza reflecting the module lifecycle state. ModuleState…, See Comm.mark_ready(). Remembers readiness on self (survives client recreation…, Return cached presence state for a connected module., ModuleState, Enumerator for module states. Attributes: CLOSED: Module is closed. STARTING:…, Timing

### Community 69 - "Offsets"
Cohesion: 0.03
Nodes (62): AltAzOffsets, GenericOffset, OnSkyDistance, Angle, PixelOffsets, AstrometryOffsets, CorrelationMaxCloseToBorderError, Any (+54 more)

### Community 70 - ".now"
Cohesion: 0.07
Nodes (31): Observer, ObservationArchiveEvolution, date, Observer, Populates the task cache and the one real night (anchored to `start`) up front.…, Freezes observation cache. After this: a task-id miss raises RuntimeError; a…, Returns list of observations for the given task. Args: date: Date of night to…, SkyCoord (+23 more)

### Community 71 - "PyObsError"
Cohesion: 0.07
Nodes (31): ADR-0003: Restrict Proxy access to async with, has_proxy() / safe_proxy, Proxy, _ProxyContext.__await__ (removed), specs/design/pyobs_2_0_wire_protocol.md, acl: config block (allow/deny), ADR-0004: Enforce access control on the callee, not the caller, Module.execute() (+23 more)

### Community 72 - "test_proxy.py"
Cohesion: 0.12
Nodes (33): _cooling_state(), make_proxy(), asyncio, Methods from both interfaces are callable., A CoolingState timestamped `age_seconds` in the past., Callers that don't pass max_age see no behavior change, however old the cached…, A future interface whose State dataclass has no `time` field fails loudly at…, Create a Proxy with a mock comm. (+25 more)

### Community 73 - "XEP_0009"
Cohesion: 0.12
Nodes (7): Expose method to public., Expose method to public., Expose method to public., Small fix for the original XEP_0009 plugin., Route RPC-level errors (e.g. forbidden, item-not-found) through the same…, XEP_0009, XEP_0009_original

### Community 74 - "SiderealTarget"
Cohesion: 0.08
Nodes (28): model_validator, Self, SkyCoord, Target, SiderealTarget, make_merit(), asyncio, transit_time should be jd0 + n*period for integer n closest to now. (+20 more)

### Community 75 - "PyobsDaemon"
Cohesion: 0.14
Nodes (10): Any, PyobsDaemon, Return the bare module name from a config or PID file path., Strip a leading underscore, which marks a module as disabled. PID and log files…, Return sorted module names from *.yaml files, excluding *.shared.yaml., Read and return the PID from the module's PID file, or None., Return the live PID for a module, or None. Cleans up stale PID files., Return uptime (seconds) and rss_mb for a running PID. No CPU -- that needs a… (+2 more)

### Community 76 - "MockWeather"
Cohesion: 0.14
Nodes (21): MockWeather, Any, Return value for given sensor. Args: station: Name of weather station to get…, Returns FITS header for the current status of this module. Args: namespaces: If…, A mock weather station for testing and simulations., Creates a new mock weather station. Args: good: Initial weather-good state.…, Set the simulated weather-good state, for use in tests and simulations. Fires a…, asyncio (+13 more)

### Community 77 - "test_config.py"
Cohesion: 0.10
Nodes (31): include_parts(), pre_process_yaml(), Any, Replaces blocks of the form {include <source.yaml> <key>} in the loaded config…, Include nested contents from another YAML file. Args: include: dictionary based…, Finds anchors ('&') in the included file. Args: filename: name of the file with…, Replaces aliases ('<<: *...') in the main file by the anchor in the included…, reload_anchors() (+23 more)

### Community 79 - "test_autoguiding.py"
Cohesion: 0.20
Nodes (32): make_guiding(), make_image(), asyncio, _state_for(), test_auto_guiding_sleeps_when_disabled(), test_auto_guiding_takes_and_processes_image_when_enabled(), test_get_fits_header_after_includes_statistics(), test_get_fits_header_before_reports_closed_loop() (+24 more)

### Community 80 - "Weather"
Cohesion: 0.15
Nodes (24): Builds the current per-sensor readings from the last raw status, for state…, Connection to pyobs-weather., Weather, asyncio, test_active_flag_defaults_true_and_tracks_stop(), test_calc_system_init_eta(), test_get_fits_header_before(), test_get_fits_header_before_invalid() (+16 more)

### Community 81 - "MotionStatusChangedEvent"
Cohesion: 0.20
Nodes (7): MotionStatusChangedEvent, Any, Event to be sent when the motion status of a device has changed., test_motion_status_invalid_status(), test_motion_status_no_interfaces(), test_motion_status_properties(), test_motion_status_roundtrip()

### Community 82 - "SkyOffsets"
Cohesion: 0.05
Nodes (36): BaseCoordinateFrame, IN, OUT, Angle, SkyCoord, Returns separatation between both coordinates, either in their own or a given…, Calculates spherical offset from first coordinate to second. Args: frame:…, Args: frame: Coordinate frame to use, or None to use coordinates' own frames.… (+28 more)

### Community 83 - "MotionStatus"
Cohesion: 0.05
Nodes (45): FilterState, IMode, ModeCapabilities, ModeState, Any, The module can change modes in a device., Set the current mode. Args: mode: Name of mode to set. group: Name of the group…, DeviceMotionStatus (+37 more)

### Community 84 - "test_xmpp_rpc.py"
Cohesion: 0.19
Nodes (14): Integration tests for the pyobs 2.0 RPC payload encoding (urn:pyobs:rpc:1).…, set_binning(int, int) -> None: multiple int params, void return., Calling a method that raises on the remote side propagates the exception., set_cooling(bool, float) then verify via state: full encode/decode cycle., set_cooling(bool, float) -> None: void return with bool + float params., set_gain(float) -> None and verify via IGain state: float param, state readback., set_gain(float) then verify via IGain state: float param round-trip., test_rpc_bool_float_roundtrip() (+6 more)

### Community 85 - "Ring"
Cohesion: 0.14
Nodes (9): integer, Any, floating, NDArray, Estimate pixel guiding offsets from asymmetry of spilled light around a fiber…, Init an image processor that adds the calculated offset. Args: fibers:…, Processes an image and sets x/y pixel offset to reference in offset attribute.…, Ring (+1 more)

### Community 86 - "DummySolarTelescope"
Cohesion: 0.12
Nodes (22): HeliocentricPolarState, HeliographicStonyhurstState, HelioprojectiveState, DummySolarTelescope, Any, Moves to and continuously tracks a Heliocentric Polar (mu, psi) coordinate., Moves to and continuously tracks a Heliographic Stonyhurst (lon, lat)…, Moves to and continuously tracks a Helioprojective (theta_x, theta_y)… (+14 more)

### Community 87 - "xmppcomm.py"
Cohesion: 0.07
Nodes (26): Any, Disconnect only, instead of slixmpp's default reconnect-in-place. xep_0199's…, Called when the server sends a <stream:error/>, e.g. when this connection gets…, Whether this client was (or is being) kicked because another session connected…, Human-readable reason text sent alongside the conflict stream error, if any., Wait for client to connect. Returns: Success or not., XMPP client for pyobs., Session start event. Args: event: The event sent at session start. (+18 more)

### Community 88 - "test_exception_logging.py"
Cohesion: 0.21
Nodes (22): Callback for flat-field class to call with statistics., FocusError, _AbortableModule, Any, asyncio, Exception, Minimal test module whose abort() raises whatever exception it's given. Starts…, test_call_id_is_attached_to_the_exception_and_included_in_the_log_line() (+14 more)

### Community 89 - "DummyCamera"
Cohesion: 0.12
Nodes (9): DummyCamera, Any, Header, NDArray, Table, Update cached telescope position from IPointingRaDec state., Returns current solar altitude in degrees, or -18 if no observer., A dummy camera for testing. (+1 more)

### Community 90 - "Application"
Cohesion: 0.11
Nodes (26): Application, React to signals and quit the module., Actually run the application., Force astropy's IERS-A table and leap-second table to be loaded/downloaded now,…, Class for initializing and shutting down a pyobs process., _warm_iers_cache(), make_bare_application(), Any (+18 more)

### Community 91 - "DummyComm"
Cohesion: 0.09
Nodes (20): Creates a comm module., DummyComm, Any, A dummy implementation of the Comm interface., Creates a new dummy comm. Args: name: Name to report for this comm. Defaults to…, Always return zero clients., No interfaces implemented., Interfaces are never supported. (+12 more)

### Community 92 - "CallModuleScript"
Cohesion: 0.06
Nodes (42): model_serializer, Any, get_class_from_string(), Get class from a given string. Args: class_name: Name of class as string.…, _build_params_model(), CallModuleScript, _get_valid_param_names(), model_validator (+34 more)

### Community 93 - "ProjectedOffsets"
Cohesion: 0.14
Nodes (20): ProjectedOffsets, Any, floating, NDArray, Processes an image and sets x/y pixel offset to reference in offset attribute.…, Project image along x and y axes and return results. Args: image: Image to…, Compute pixel offsets for guiding by correlating 1D projections of the current…, Initializes a new auto guiding system. (+12 more)

### Community 94 - "test_pyobs_archive.py"
Cohesion: 0.20
Nodes (23): PyobsArchiveFrameInfo, Frame info for pyobs archive., make_archive(), make_frame_dict(), MockResponse, Any, asyncio, test_download_frames_returns_images() (+15 more)

### Community 95 - "HttpFile"
Cohesion: 0.10
Nodes (18): ArchiveFile, Wraps a file in an archive. To be used in combination with pyobs-archive., Creates a new archive file. Args: name: Name of file. mode: Open mode (r/w).…, If in write mode, actually send the file to the archive., HttpFile, Any, Read number of bytes from stream. Args: n: Number of bytes to read. Read until…, Write data into the stream. Args: s: Bytes of data to write. (+10 more)

### Community 96 - ".__init__"
Cohesion: 0.40
Nodes (3): Any, Any, Initialize a new scheduler. Args: twilight: astronomical or nautical

### Community 97 - "application.py"
Cohesion: 0.09
Nodes (18): _disable_iers_auto_download(), GuiApplication, InfluxLogConfig, Any, TypedDict, Derived Application class that uses a Qt GUI. Allows for graceful shutdown in…, Create a new GUI application., Initializes a pyobs application. Exactly one of `config`/`module_factory` must… (+10 more)

### Community 98 - "FocusSeries"
Cohesion: 0.06
Nodes (37): AutoFocusPoint, fit_hyperbola(), Fit a hyperbola Args: x_arr: X data y_arr: Y data y_err: Y errors Returns:…, FocusSeries, Analyse given image. Args: image: Image to analyse focus_value: Value to fit…, Returns a list of data points., Fit focus from analysed images Returns: Tuple of new focus and its error, Base class for focus series helper classes. (+29 more)

### Community 99 - "_SourceCatalog"
Cohesion: 0.06
Nodes (33): Background, Any, floating, NDArray, Initializes a wrapper for SEP. See its documentation for details. Highly…, Find stars in given image and append catalog. Args: image: Image to find stars…, Remove background from image in data. Args: data: Data to remove background…, Detect astronomical sources using SEP (Source Extractor for Python). This… (+25 more)

### Community 100 - "make_proxy_cm"
Cohesion: 0.21
Nodes (27): make_proxy_cm(), Wrap value in a MagicMock standing in for the async context manager returned by…, make_flatfield(), asyncio, Find the state object set_state() was called with for the given interface., _ready_telescope(), _state_for(), test_abort_sets_event() (+19 more)

### Community 101 - "WeatherSensors"
Cohesion: 0.16
Nodes (13): Set a simulated sensor's value, for use in tests and simulations. Args: sensor:…, Any, ClientSession, WeatherApi, Enumerator for sensors of a weather station. Attributes: TIME: Time of…, WeatherSensors, MockResponse, Any (+5 more)

### Community 102 - "ScriptRunner"
Cohesion: 0.14
Nodes (15): calc_run_timeout(), Any, Calculates timeout for run()., Module for running a script., Initialize a new script runner. Args: script: Config for script to run., Run script. Raises: ScriptError: If the script failed (e.g. a proxy/network…, Abort current actions., ScriptRunner (+7 more)

### Community 103 - "ResolvableErrorLogger"
Cohesion: 0.23
Nodes (7): Any, Logger, Logging for resolvable errors. Args: logger: Logger to use. error_level: Log…, Log an error message., ResolvableErrorLogger, create_logger(), test_logger()

### Community 104 - "test_coordinates.py"
Cohesion: 0.15
Nodes (25): offset_altaz_to_radec(), offset_radec_to_altaz(), EarthLocation, SkyCoord, make_altaz(), make_radec(), SkyCoord, Zero offset returns (0, 0). (+17 more)

### Community 105 - "get_registered_interface"
Cohesion: 0.08
Nodes (30): Converts a list of interface names to interface classes. Args: interfaces: list…, get_registered_interface(), Look up a registered interface class by name, or None if unknown., All currently-registered interface classes, keyed by name., registered_interfaces(), LogCaptureFixture, Tests for Comm._interface_names_to_classes -- the base-Comm chokepoint that…, An interface defined entirely outside pyobs.interfaces resolves the same way… (+22 more)

### Community 106 - "_DotNetRequestBuilder"
Cohesion: 0.27
Nodes (3): Any, Init new astronomy.net processor. Args: url: URL to service. source_count:…, _DotNetRequestBuilder

### Community 107 - "LocalArchive"
Cohesion: 0.33
Nodes (25): LocalArchive, Connector class to a local image archive., make_frame_headers(), asyncio, Path, test_download_frames_loads_real_files(), test_download_frames_skips_frames_without_filename(), test_download_headers_returns_header_dicts() (+17 more)

### Community 108 - "Plan: Systematic ejabberd throughput/latency benchmarking"
Cohesion: 0.07
Nodes (28): Blockers found while getting the environment working (2026-07-27), Conclusion on the O(N²) finding: real bug, not a pyobs design problem, Deeper dig: isolating the real mechanism (2026-07-27, same day), Environment, Fifth investigation session (2026-07-28, same day) — found the specific mechanism: an un-re-armed passive socket, First real results (2026-07-27), Fourth live run (2026-07-28, same day) — found the actual mechanism: stuck per-connection Recv-Q on ejabberd's side, Full incident timeline and what's been ruled out (2026-07-27) (+20 more)

### Community 109 - "_PhotUtilAperturePhotometry"
Cohesion: 0.13
Nodes (15): ApertureMask, CircularAperture, _PhotUtilAperturePhotometry, Any, floating, NDArray, Table, PhotUtilsPhotometry (+7 more)

### Community 110 - "Mixins (pyobs.mixins) API doc"
Cohesion: 0.09
Nodes (25): Images (pyobs.images) API doc, ImageProcessor base class, Object base class, Pipeline module (pyobs.modules.image.Pipeline), API index (toctree), ICamera, IStartStop, CameraSettingsMixin (+17 more)

### Community 111 - "Script base class"
Cohesion: 0.09
Nodes (25): IMode, TaskData, AutoFocusScript, CallModuleScript, CasesRunner, ConditionalRunner, ConstSkyflatPriorities, DarkBiasScript (+17 more)

### Community 112 - "test_background_task.py"
Cohesion: 0.16
Nodes (20): BackgroundTask, Any, Add a new function that should be run in the background. MUST be called in…, make_task(), asyncio, Too many fast failures calls parent.quit() when restart=True., Too many fast failures with restart=False just stops without calling quit., Failures spread over time don't trigger the rapid-failure quit. (+12 more)

### Community 113 - "Test Commlogging (comm)"
Cohesion: 0.12
Nodes (20): Send an event to all connected modules. Args: event: Event to send.…, CommLoggingHandler, Any, A logging handler that sends all messages through a Comm module., Create a new logging handler. Args: comm: Comm module to use., Send a new log entry to the comm module. Args: rec: Log record to send., comm(), handler() (+12 more)

### Community 114 - ".__init__"
Cohesion: 0.11
Nodes (9): Any, JSON representation of event., String representation of event., Generic from_dict method for derived classes that don't need their own., Any, Any, Any, Any (+1 more)

### Community 115 - "test_dummyradectelescope.py"
Cohesion: 0.24
Nodes (21): TrackingRateCapabilities, make_dummyradectelescope(), asyncio, test_move_altaz_clears_tracked_body(), test_move_altaz_resets_tracking_mode_to_off(), test_move_radec_clears_tracked_body(), test_move_radec_resets_tracking_mode_to_sidereal(), test_move_task_applies_tracking_rate_to_position() (+13 more)

### Community 116 - "ImagingScript"
Cohesion: 0.17
Nodes (8): ImagingScript, Any, Target, Run script. Raises: InterruptedError: If interrupted, Returns FITS header for the current status of this module. Args: namespaces: If…, Return the exposure time, computing it dynamically if needed., Default script for imaging configs., Whether this config can currently run. Returns: True, if the script can run now

### Community 117 - "test_localcomm_state.py"
Cohesion: 0.09
Nodes (28): asyncio, fixture, Tests for LocalComm state, capabilities, and presence., set_presence stores and get_client_state retrieves., Default presence is READY with no error string., subscribe_presence fires callback immediately with the current presence state., subscribe_presence callback is called whenever presence changes., Reset LocalNetwork singleton before each test. (+20 more)

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
Nodes (24): FakeInterface, make_xmpp_comm(), asyncio, LogCaptureFixture, Tests for the mixed-version-fleet diagnostic on interface resolution. Covers…, Base Comm._diagnose_missing_interface returns None -- e.g. LocalComm, which…, Sanity check that ICooling/IModule (used above as real interfaces) still have…, Stand-in for a pyobs Interface class -- only __name__ and .version matter here. (+16 more)

### Community 122 - "CLAUDE.md (repo guide)"
Cohesion: 0.10
Nodes (23): check_coverage.md (coverage gap survey), Coverage Category A: needs live external service/credentials, Coverage Category B: GUI widgets needing a display, Coverage Category C: CLI/app bootstrap, Coverage Category D: dev/test-support tooling, Coverage Category E: real gaps, no external-service/GUI excuse, Cross-repo docs convention (Repos: line + specs/README.md pointer), graphify usage rules for this repo (+15 more)

### Community 123 - "SFTPFile"
Cohesion: 0.22
Nodes (5): Any, VFS wrapper for a file that can be accessed over a SFTP connection., Open/create a file over a SSH connection. Args: name: Name of file. mode: Open…, Returns content of given path. Args: path: Path to list. kwargs: Parameters for…, SFTPFile

### Community 124 - "FocusModel"
Cohesion: 0.10
Nodes (28): IFocusModel, FocusModel, FocusTimeoutError, MissingSensorError, Returns the optimal focus. Args: filter_name: If given, use this filter name…, The weather station returned an invalid/missing reading -- plausibly transient,…, Retrieve all required values for the model. Returns: Dictionary containing all…, Timed out waiting for a temperature reading from another module -- plausibly… (+20 more)

### Community 125 - "_AbortableModule"
Cohesion: 0.11
Nodes (19): _AbortableModule, Any, asyncio, parametrize, Minimal test module with one guarded (non-whitelisted) RPC method., Module implementing IStartStop, whose abstract `start(**kwargs)` RPC method has…, A freshly constructed module hasn't been started yet., A regular RPC method must be rejected while the module is still STARTING. (+11 more)

### Community 126 - "ImageSourceFilter"
Cohesion: 0.12
Nodes (17): ImageSourceFilter, Any, floating, NDArray, Table, Filters the source table after pysep detection has run Args:…, Filter a source catalog by border distance, quality metrics, and brightness,…, Convert from FITS to numpy conventions for pixel coordinates. (+9 more)

### Community 127 - "test_darkbias.py"
Cohesion: 0.18
Nodes (22): DarkBiasScript, Script for running darks or biases., Whether this config can currently run. Returns: True if script can run now., Run script. Raises: InterruptedError: If interrupted, isinstance_class(), Shared test-double helpers used across multiple test modules., Build a fresh class purely for isinstance() checks against a MagicMock.…, make_camera() (+14 more)

### Community 128 - "BackendTaskArchive"
Cohesion: 0.07
Nodes (17): BackendTaskArchive, Any, ClientSession, Returns the task with the given ID. Returns: Task with given ID., Task archive based on pyobs-robotic-backend., Creates a new task archive. Args: url: URL of pyobs-robotic-backend. token:…, Opens the backend task archive., Closes the backend observation archive. (+9 more)

### Community 129 - ".__init__"
Cohesion: 0.20
Nodes (5): Any, Create master bias frame. Args: images: List of raw bias frames. Returns:…, Create master dark frame. Args: images: List of raw dark frames. bias: Bias…, Create master flat frame. Args: images: List of raw flat frames. bias: Bias…, Pipeline for science images. Args: steps: List of pipeline steps to perform.…

### Community 130 - "Plan: pyobs-pipeline"
Cohesion: 0.08
Nodes (24): Celery task, Consequences, Django models, Implementation checklist, Log viewing, Open questions, Pages, Pipeline builder (+16 more)

### Community 131 - "Test Localcomm (local)"
Cohesion: 0.18
Nodes (22): make_comm(), asyncio, fixture, Sender also receives its own events., Reset LocalNetwork singleton between tests., #677: a late-joining module must announce itself via ModuleOpenedEvent once…, get_interfaces returns [] when the remote client has no module., reset_network() (+14 more)

### Community 132 - "_SepAperturePhotometry"
Cohesion: 0.05
Nodes (34): AperturePhotometry, Any, Base class for aperture photometry processors -- not meant to be used directly,…, Do aperture photometry on given image. Args: image: Image to do aperture…, _PhotometryCalculator, Table, Abstract class for photometry calculators., Photometry (+26 more)

### Community 133 - "ExposureTimeProvider"
Cohesion: 0.22
Nodes (5): ExposureTimeProvider, Determine and return the exposure time in seconds. Returns: Exposure time in…, Abstract base class for providers that determine camera exposure time., The equivalent astropy.units unit, for code that needs to build a Quantity., UnitBase

### Community 134 - "Any"
Cohesion: 0.25
Nodes (4): Any, Return the last received state for the given interface, or None., Return the capabilities for the given interface, or None., Return state immediately if available, otherwise wait for the first update.

### Community 135 - "test_dummymode.py"
Cohesion: 0.32
Nodes (13): _event_of_type(), make_dummymode(), asyncio, Find the most recent state object set_state() was called with for the given…, Find the send_event() call with an event of the given type., _state_for(), test_init_default_modes(), test_init_park_stop_motion_are_noops() (+5 more)

### Community 136 - "._client_disconnected"
Cohesion: 0.29
Nodes (4): PresenceCallback, Called when a client disconnects. Args: event: Disconnect event. sender: Name…, Subscribe to presence updates for a given module. Delivers the current value…, Unsubscribe from presence updates. Args: module: Name of remote module.…

### Community 137 - "test_autofocus.py"
Cohesion: 0.38
Nodes (15): make_autofocus(), make_script(), make_task(), make_telescope(), asyncio, Telescope is stopped even if auto_focus raises., test_can_run_false_when_autofocus_unavailable(), test_can_run_false_when_no_data() (+7 more)

### Community 138 - "Grid"
Cohesion: 0.09
Nodes (21): AvoidMoon, GridFilter, Any, RandomizeGrid, Initialize the conversion filter. Args: grid: Upstream grid or filter that…, Abstract base class for grid filters that wrap another GridNode. A GridFilter…, Initialize the frame conversion filter. Args: grid: Upstream grid or filter…, Randomize iteration order by rotating the underlying sequence. For each… (+13 more)

### Community 139 - "test_kiosk.py"
Cohesion: 0.24
Nodes (21): _cancel_after(), _make_image(), make_kiosk(), asyncio, Side effect that raises CancelledError starting from the n-th call., test_camera_thread_captures_and_adjusts_exposure_time(), test_camera_thread_clips_exposure_time_to_minimum(), test_camera_thread_continues_on_file_not_found() (+13 more)

### Community 140 - "pyobs.py"
Cohesion: 0.19
Nodes (9): main(), Any, PyobsCLI, Start process as a daemon. Args: pid_file: Name of PID file., Class for initializing and running pyobs CLI., main(), Any, PyobsWinCLI (+1 more)

### Community 141 - "Robotic recipe (doc)"
Cohesion: 0.17
Nodes (21): pyobs.modules.robotic (doc), Mastermind (module), PointingSeries, Scheduler (module), ScriptRunner, Robotic recipe (doc), AirmassConstraint, BackendObservationArchive (+13 more)

### Community 142 - "is_valid_jid"
Cohesion: 0.21
Nodes (6): is_valid_jid(), Whether jid is a valid user@domain or user@domain/resource JID -- exactly what…, JID parsing/validation in XmppComm.__init__ and the reusable is_valid_jid()…, The actual production bug this was found from: a JID ending in "/" with nothing…, re.match alone doesn't anchor the end -- confirms the pattern is anchored so…, TestIsValidJid

### Community 143 - "IModule"
Cohesion: 0.33
Nodes (5): IModule, Any, The module is actually a module. Implemented by all modules., Reset error of module, if any., Returns names of all methods the calling module is allowed to invoke on this…

### Community 144 - "test_config_schema.py"
Cohesion: 0.20
Nodes (22): ConfigFieldSchema, ConfigSchema, dataclass_to_schema(), _field_schema(), Any, _pydantic_field_schema(), pydantic_to_schema(), Recursively derive a ConfigSchema from a dataclass type. Handles: plain scalars… (+14 more)

### Community 145 - "DummyRaDecTelescope"
Cohesion: 0.07
Nodes (27): AltAzOffsetState, IOffsetsRaDec, Any, DEGREES, RaDecOffsetState, The module supports RA/Dec offsets, usually combined with…, Move an RA/Dec offset. Args: dra: RA offset in degrees. ddec: Dec offset in…, Any (+19 more)

### Community 146 - "Scheduler"
Cohesion: 0.15
Nodes (7): Any, Compares two lists of tasks and returns two lists, containing those that are…, Trigger a re-schedule., Re-schedule when task has started and we can predict its end. Args: event: The…, Reset current task, when it has finished or failed. Args: event: The task…, Re-schedule on incoming good weather event. Args: event: The good weather…, Scheduler

### Community 147 - "RollingTimeAverage"
Cohesion: 0.10
Nodes (24): Any, Runs an async callable to completion on a dedicated worker thread, off the…, run_cpu_bound(), RollingTimeAverage, _T, asyncio, test_run_cpu_bound_propagates_exception(), test_run_cpu_bound_returns_value() (+16 more)

### Community 148 - ".__init__"
Cohesion: 0.12
Nodes (10): EarthLocation, Observer, Location of the observer, derived from :attr:`observer` (there is no separately…, .. note:: Objects must always be opened and closed using…, Observer, Initialize object with the given time. Args: time: Start time for all further…, Initializes a new evaluator. Args: observer: Observer to use. functions: Dict…, Any (+2 more)

### Community 149 - "Kiosk"
Cohesion: 0.16
Nodes (8): Kiosk, Any, Response, Thread for taking images., A kiosk mode for a pyobs camera that takes images and published them via HTTP., Initializes file cache. Args: camera: Camera to use for kiosk mode. port: Port…, Handles access to /* and returns a specified image. Args: request: Request to…, Whether the server is started.

### Community 151 - "`OBSNUM`: per-night observation counter in FITS headers"
Cohesion: 0.22
Nodes (8): Migration, `OBSNUM`: per-night observation counter in FITS headers, Problem, Proposed design, Still open (not resolved by this doc), When is `obsnum` assigned: scheduled, or observed?, Where the pieces actually are, Why this determines the design, not just where to put a function

### Community 152 - "3rd party packages (doc)"
Cohesion: 0.11
Nodes (20): 3rd party packages (doc), Astroplan, Astropy, Astroquery, Cython, LMFIT, matplotlib, NumPy (+12 more)

### Community 153 - "_DaoBackgroundRemover"
Cohesion: 0.05
Nodes (42): Source Detection processors doc, DaophotSourceDetection (detection processor), SepSourceDetection (detection processor), _DaoBackgroundRemover, Any, floating, NDArray, DaophotSourceDetection (+34 more)

### Community 154 - "SSHFile"
Cohesion: 0.12
Nodes (12): Any, VFS wrapper for a file that can be accessed over a SFTP connection., Write data into the stream. Args: b: Bytes of data to write., If in write mode, actually send the file to the SSH server., Returns content of given path. Args: path: Path to list. kwargs: Parameters for…, Open/create a file over a SSH connection. Args: name: Name of file. mode: Open…, For read access, download the file into a local buffer. Raises:…, Read number of bytes from stream. Args: n: Number of bytes to read. Read until… (+4 more)

### Community 155 - "create_rst.py"
Cohesion: 0.33
Nodes (18): create_image_processors_rst(), create_modules_rst(), create_rst_overview(), create_utils_rst(), find_classes_in_modules(), find_python_modules(), find_submodules(), Any (+10 more)

### Community 156 - ".__init__"
Cohesion: 0.33
Nodes (4): Any, Abort current actions., Initialize a new flat field scheduler. Args: flatfield: Flat field module to…, Perform flat-fielding Raises: DeviceBusyError: If a flat-fielding run is…

### Community 157 - "SoftBin"
Cohesion: 0.16
Nodes (11): Any, floating, NDArray, Bin a 2D image by averaging non-overlapping blocks, updating relevant FITS…, Init a new software binning pipeline step. Args: binning: Binning to apply to…, Bin an image. Args: image: Image to bin. Returns: Binned image., SoftBin, asyncio (+3 more)

### Community 158 - "AddMask"
Cohesion: 0.21
Nodes (13): AddMask, Any, floating, NDArray, Add mask to image. Args: image: Image to add mask to. Returns: Image with mask, Attach a precomputed mask to an image based on instrument and binning. This…, Init an image processor that adds a mask to an image. Args: masks: Dictionary…, asyncio (+5 more)

### Community 159 - "ImageType"
Cohesion: 0.09
Nodes (19): Broadcast image. Args: image: Image to broadcast. Returns: Original image., Archive, FrameInfo, Any, Base class for frame infos., Base class for image archives., Any, TypedDict (+11 more)

### Community 160 - "SkyCoord"
Cohesion: 0.13
Nodes (9): SkyCoord, Return the next point that satisfies all constraints. Iterates underlying…, Convert the next tuple to a SkyCoord. Expects a tuple (x_deg, y_deg) from the…, Transform the next SkyCoord to the target frame. Returns: A SkyCoord…, Yield a point after rotating the underlying grid a random number of times.…, Yield a point after rotating the underlying grid a random number of times.…, Yield the point from the CSV closest to the next grid point. Returns: A point…, Fetch the next point from the underlying grid. Returns: The next point from the… (+1 more)

### Community 161 - "comm/test_events.py"
Cohesion: 0.18
Nodes (15): asyncio, Tests for Comm.register_event / unregister_event. Covers…, Two independent subscribers for the same event: one tearing down must not un-…, A module that both sends an event (handler-less register_event()) and…, unregister must mirror the exact same derived-events expansion register_event…, Two independent subscribers (e.g. two widget instances for the same event type)…, Once the last handler for an event is unregistered, the event must no longer be…, test_unregister_event_drops_subscribed_role_when_last_handler_removed() (+7 more)

### Community 162 - "WeatherState"
Cohesion: 0.23
Nodes (12): WeatherState, _FakeProxyContext, asyncio, Tests for WeatherAwareMixin's use of Proxy.wait_for_state's max_age -- see…, Minimal async context manager standing in for Object.proxy()'s _ProxyContext., Runs WeatherAwareMixin's private background-check loop just long enough for one…, None from wait_for_state() -- whether "never published" or "published but stale…, _run_one_weather_check_iteration() (+4 more)

### Community 163 - "LogEvent"
Cohesion: 0.18
Nodes (6): LogEvent, Event for log entries., Enum, TelegramUserState, test_log_event_properties(), test_log_event_roundtrip()

### Community 164 - "._update_root"
Cohesion: 0.33
Nodes (3): Any, DataFrame, Update files in root directory.

### Community 165 - "ExpTimeEval"
Cohesion: 0.14
Nodes (12): ExpTimeEval, Any, Return list of binnings., Return list of filters., Estimate exposure time for given filter Args: solalt: Solar altitude. binning:…, Estimates exposure time for a given filter and binning at a given time offset…, Exposure time evaluator for skyflats., Estimates the duration for a given amount of flats in the given filter and… (+4 more)

### Community 166 - "Stellarium"
Cohesion: 0.18
Nodes (6): BaseTransport, Exception, Send coordinates to clients., A stellarium telescope., Stellarium, StellariumProtocol

### Community 167 - "Overview (doc)"
Cohesion: 0.18
Nodes (17): Overview (doc), Access control (ACL), Comm, Events, Interface, Module (base class), Object (base class), Location / astroplan.Observer (+9 more)

### Community 168 - ".__init__"
Cohesion: 0.29
Nodes (5): Any, Pipeline, ProgressCallback, Pre-pass: list (not download) OBJECT frames for every instrument/binning/filter…, Creates a Reduction object for reducing a given observation period. Args:…

### Community 169 - "GuidingStatisticsPixelOffset"
Cohesion: 0.25
Nodes (7): GuidingStatisticsPixelOffset, Calculates RMS of data. Args: data: Data to calculate RMS for. Returns: Tuple…, mock_meta_image(), fixture, test_build_header_to_few_values(), test_end_to_end(), test_get_session_data()

### Community 170 - "test_module_state_publishing.py"
Cohesion: 0.33
Nodes (6): _discover_concrete_modules(), asyncio, parametrize, Parametrized check: every concrete Module publishes state for each stateful…, All concrete (non-abstract, non-internal) pyobs.modules.Module subclasses.…, test_module_publishes_all_stateful_interfaces()

### Community 171 - ".abort"
Cohesion: 0.40
Nodes (3): Any, Abort current actions., Sets the currently active fiber. Must be in fiber_names capability. Args:…

### Community 172 - "test_grab_sequence.py"
Cohesion: 0.29
Nodes (16): make_camera(), asyncio, Tests for BaseCamera.grab_sequence()/abort_sequence(), the IDataSequence…, grab_sequence() must not block for the whole sequence -- see design doc: a…, test_abort_clears_running_sequence(), test_abort_cuts_delay_short(), test_abort_sequence_cuts_delay_short(), test_abort_sequence_lets_current_grab_finish_but_stops_the_rest() (+8 more)

### Community 173 - "binding.py"
Cohesion: 0.23
Nodes (8): fault2xml(), py2xml(), Any, Element, rpcbase64, rpctime, xml2fault(), xml2py()

### Community 174 - "NewSpectrumEvent"
Cohesion: 0.22
Nodes (7): NewSpectrumEvent, Any, Event to be sent on a new image., Initializes new NewSpectrumEvent. Args: filename: Name of new image file., test_new_spectrum_invalid_filename(), test_new_spectrum_properties(), test_new_spectrum_roundtrip()

### Community 175 - ".get_config_value"
Cohesion: 0.40
Nodes (4): Any, ConfigValue, Returns current value of config item with given name. Args: name: Name of…, Sets value of config item with given name. Args: name: Name of config item.…

### Community 176 - "CLI"
Cohesion: 0.16
Nodes (9): CLI, Initializes a new instance of the CLI class., Overwrite this to set CLI parameters with argparse., Overwrite this to actually run the CLI., Load config from config file, Load config from environment variables., main(), PyobsDaemonCLI (+1 more)

### Community 178 - "SkyflatPriorities"
Cohesion: 0.20
Nodes (8): ArchiveSkyflatPriorities, Calculate flat priorities from an archive., Base class for sky flat priorities., SkyflatPriorities, ConstSkyflatPriorities, Constant flat priorities., Observer, Initializes a new scheduler for taking flat fields Args: functions: Flat field…

### Community 180 - "Steering: astropy IERS auto-download blocks event loop"
Cohesion: 0.32
Nodes (8): BaseTelescope._celestial / _update_celestial_headers, Steering: astropy IERS auto-download blocks event loop, iers_offline config flag (stopgap fix), Steering: Blocking vendor SDK calls must never run directly on the event loop, _run_blocking() pattern (pyobs_aravis.araviscamera.AravisCamera), _wait_for_frame() tight-poll wrapper pattern, Steering: OnDemandScheduler.evolve() uncached sunset lookup stalls event loop, ObservationArchiveEvolution.evolve() Time.night_obs() bug (fixed via memoization)

### Community 181 - "test_schedulereader.py"
Cohesion: 0.31
Nodes (15): make_observation(), make_reader(), asyncio, Does not update if lock cannot be acquired within timeout., test_download_schedule_empty_portal_response(), test_download_schedule_returns_observations(), test_get_schedule_returns_cached_tasks(), test_get_schedule_returns_empty_initially() (+7 more)

### Community 182 - "test_istructuredconfig.py"
Cohesion: 0.18
Nodes (13): ConfigAppliedState, DummyConfig, DummyStructuredConfigModule, Any, asyncio, fixture, Tests for IStructuredConfig capabilities/state round-tripping through LocalComm., Reset LocalNetwork singleton before each test. (+5 more)

### Community 184 - "Merit"
Cohesion: 0.15
Nodes (15): AfterTimeMerit, BeforeTimeMerit, ConstantMerit, DataProvider, FollowMerit, IntervalMerit, ObservationArchiveEvolution wraps ObservationArchive with per-run caching (avoid repeated HTTP requests) and lookahead simulation (evolve() records tentative future assignments so IntervalMerit/PerNightMerit see them and avoid double-scheduling within one run), Merit (+7 more)

### Community 185 - "ejabberd shaper throttling bug (xmpp_socket.erl re-arm) & fix"
Cohesion: 0.21
Nodes (12): XMPP/ejabberd diagnostics recipe (doc), benchmark_state_throughput.py, check_ejabberd_notify.py, delete_pubsub_nodes.py, list_pubsub_nodes.py, Comparing shaper configs (rationale), show_module_info.py, scripts/xmpp/install-ejabberd.sh (+4 more)

### Community 186 - "WeatherStatus"
Cohesion: 0.14
Nodes (9): Any, Returns FITS header for the current status of this module. Args: namespaces: If…, Initialize a new pyobs-weather connector. Args: url: URL to weather station…, Any, setter, WeatherStatus, test_status_set(), test_status_set_non_good() (+1 more)

### Community 188 - "Work Plan"
Cohesion: 0.12
Nodes (16): Dropped items, Phase 0 — Foundations, Phase 1.5 — RPC payload encoding 2.0, Phase 1 — Walking skeleton: prove State end-to-end on one interface, Phase 2.5 — Discovery and Presence, Phase 2 — Audit and design pass (no implementation yet), Phase 3 — Bulk rollout, Phase 4 — Other backends and Presence (+8 more)

### Community 189 - "Plan: `pyobs-gui` TelescopeWidget layout — width floor investigation & design notes"
Cohesion: 0.12
Nodes (16): 1. Make the stacked widget size to the current page, not the widest one, 2. Adopt a width convention for future coordinate-type pages, 3. `QFormLayout::setRowWrapPolicy()` on the individual form pages, 4. Resize-driven reparenting for the four-groupbox row, Capability-driven visibility is handled by toggling pre-built sections on/off, Coordinate-type selection is already a combobox, not tabs, Each coordinate-type page has a fixed, hand-built field set, Filter, Focus, and the offsets rows are structurally duplicated (+8 more)

### Community 190 - "PointingSeries"
Cohesion: 0.17
Nodes (7): Modules for robotic mode. TODO: write doc, PointingSeries, Any, SkyCoord, Module for running pointing series., Initialize a new pointing series. Args: grid: Grid to use for pointing series.…, Run a pointing series.

### Community 191 - "GridNode"
Cohesion: 0.09
Nodes (15): GridNode, Log the last yielded point, if any. Implementations typically delegate to…, Abstract base class for grid nodes. A GridNode implements the Python iterator…, Return iterator self. Returns: The GridNode itself as an iterator., Return the number of points remaining. Returns: Number of points remaining to…, Append the last yielded point back to the underlying sequence. This can be used…, GridPipeline, Any (+7 more)

### Community 192 - ".set_tracking_rate"
Cohesion: 0.50
Nodes (3): ARCSEC_PER_SEC, Any, Sets an absolute tracking rate on the sky, in arcsec/sec. Args: ra_rate: Rate…

### Community 194 - "What's New in pyobs 2.0 (doc)"
Cohesion: 0.15
Nodes (14): What's New in pyobs 2.0 (doc), ACL feature (2.0), Capabilities and versioned discovery, Exception handling redesign, External-package interfaces, ICamera/ISpectrograph no longer imply IExposure, IDataSequence, InvocationError / SevereError retired (+6 more)

### Community 195 - "TaskStartedEvent"
Cohesion: 0.16
Nodes (9): Any, Event to be sent when a task has started., Initializes a new task started event. Args: name: Name of task that just…, TaskStartedEvent, test_task_started_invalid_name(), test_task_started_missing_id(), test_task_started_no_eta(), test_task_started_properties() (+1 more)

### Community 196 - "test_imagewatcher.py"
Cohesion: 0.33
Nodes (15): make_fits_bytes(), make_read_write_ctx(), make_watcher(), asyncio, On write failure the file is re-queued and remove is NOT called., test_add_file_queues_filename(), test_add_file_respects_pattern(), test_add_file_skips_non_matching_pattern() (+7 more)

### Community 197 - "CatalogCircularMask"
Cohesion: 0.18
Nodes (9): CatalogCircularMask, Any, NDArray, Table, Init an image processor that masks out everything except for a central circle.…, Remove everything outside the given radius from the image. Args: image: Image…, Filter a source catalog by keeping only entries inside a central circle (or…, asyncio (+1 more)

### Community 199 - "ImageWatcher"
Cohesion: 0.15
Nodes (9): CurrentFile, ImageWatcher, Any, Add a file to the file queue. Args: filename (str): Local filename of new file., Can be overwritten by derived classes to do extra processing on files. All…, Can be overwritten by derived classes to do clean up after successful copying.…, Watch for new files and write them to all given destinations. Watches a path…, Create a new image watcher. Args: watchpath: Path to watch. destinations:… (+1 more)

### Community 200 - "ObservationList"
Cohesion: 0.02
Nodes (161): Mastermind, Mastermind for a full robotic mode., Initialize a new auto focus system. Args: schedule: Object that can return…, # TODO: add abort (see old robotic/scheduler.py), Initialize a new scheduler. Args: scheduler: Scheduler to use. tasks: Task…, Observation, ObservationList, ObservationState (+153 more)

### Community 201 - "test_xmpp_acl.py"
Cohesion: 0.22
Nodes (12): Integration tests for Phase 8 Access Control (ACLs) over real XMPP. Verifies…, A caller granted "*" access under "allow" can still call normally., A caller not present in the "allow" map is denied by default., A caller on the "deny" list gets exc.RemoteError with a forbidden message, not…, Naming an interface under "allow" permits all of its methods, but nothing…, A module not on the "deny" list is unaffected., test_acl_allow_denies_unlisted_caller(), test_acl_allow_interface_name_sugar() (+4 more)

### Community 202 - "show_module_info.py"
Cohesion: 0.25
Nodes (13): h1(), h2(), inspect_module(), _interface_from_feature(), kv(), main(), _module_state_from_show(), ok() (+5 more)

### Community 203 - "integration/conftest.py"
Cohesion: 0.23
Nodes (13): connect(), make_camera_comm(), make_unopened_comm(), make_xmpp_comm(), fixture, Fixtures shared across all integration tests., Factory fixture: ``await make_xmpp_comm(user)`` returns an open XmppComm for…, Connect a module to LocalComm and return the comm. (+5 more)

### Community 204 - ".set_cooling"
Cohesion: 0.50
Nodes (3): CELSIUS, Any, Enables/disables cooling and sets setpoint. Args: enabled: Enable or disable…

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

### Community 209 - "Smooth"
Cohesion: 0.22
Nodes (10): Any, Init a new smoothing pipeline step. Args: sigma: Standard deviation for…, Smooth an image. Args: image: Image to smooth. Returns: Smoothed image., Gaussian smoothing of image data using SciPy’s ndimage.gaussian_filter. This…, Smooth, asyncio, test_call(), test_call_no_image_data() (+2 more)

### Community 210 - "flatfield/scheduler.py"
Cohesion: 0.14
Nodes (8): Iterator for scheduler items, Iterate over scheduler items, Return schedule item., Find a possible slot for a given filter/binning in the given schedule Args:…, Checks, whether a new scheduler item would overlap an existing item Args:…, Scheduler for taking flat fields, Calculate schedule starting at given time Args: time: Time to start schedule at, Scheduler

### Community 211 - "HttpFileCache"
Cohesion: 0.06
Nodes (35): HttpFileCache, Any, Response, Handles OPTIONS access to /{filename} for CORS preflight requests. Args:…, Handles GET access to /{filename} and returns image. Args: request: Request to…, Handles PUSH access to /, stores image and returns filename. Args: request:…, A file cache based on a HTTP server., Initializes file cache. Args: port: Port for HTTP server. cache_size: Size of… (+27 more)

### Community 212 - "Plan: Widget plugin mechanism + `pyside6-deploy` packaging for `pyobs-gui`"
Cohesion: 0.13
Nodes (14): Consequences, Considered options, Considered options, Deciding which widget to use, without user-side config, Decision, Decision outcome, Implementation checklist, Non-goals (+6 more)

### Community 213 - "Plan: Split archive prefetch from CPU-bound merit evaluation, to unblock a `ProcessPoolExecutor`"
Cohesion: 0.12
Nodes (15): 1. `ObservationArchiveEvolution` — add prefetch + freeze (`observationarchiveevolution.py`), 2. Call prefetch + freeze — `ondemandscheduler.py`, `schedule()`, 3. Confirm zero cache misses before touching the executor, 4. Only after step 3 is clean: swap the executor (`_executor.py`), Consequences, Considered options, Decision, Existing coverage (+7 more)

### Community 215 - "Image (pyobs.images.processors.image) API doc"
Cohesion: 0.18
Nodes (11): AddFitsHeaders, Image (pyobs.images.processors.image) API doc, Download, Flip, Grayscale, HttpServer, Normalize, Save (+3 more)

### Community 216 - "Offsets (pyobs.images.processors.offsets) API doc"
Cohesion: 0.33
Nodes (11): AstrometryOffsets, BrightestStarGuiding, BrightestStarOffsets, Offsets (pyobs.images.processors.offsets) API doc, DummyOffsets, DummySkyOffsets, FitsHeaderOffsets, Offsets (+3 more)

### Community 217 - "Constraint"
Cohesion: 0.20
Nodes (11): AirmassConstraint, AstroplanScheduler, Constraint, Constraints answer a binary may-it-run question (any False excludes the task); Merits answer a continuous how-desirable question (values multiplied together with priority, highest score wins); rationale: clean separation lets scheduling policy be expressed in YAML without code, and a Merit returning 0.0 can double as a soft constraint, MoonIlluminationConstraint, MoonSeparationConstraint, OnDemandScheduler, OnDemandScheduler: greedy, evaluates constraints/merits per time step, robust to interruption, supports merits+global constraints+lookahead. AstroplanScheduler: full-night planning via astroplan PriorityScheduler in a separate process (avoids blocking event loop), only SiderealTarget, only per-task constraints, no merits; rationale: choose based on whether a committed nightly plan or rolling on-demand decisions is needed (+3 more)

### Community 221 - "flatfield/test_scheduler.py"
Cohesion: 0.24
Nodes (13): FlatFieldScheduler, Run the flat-field scheduler., A single item in the flat scheduler, Initializes a new scheduler item Args: start: Start time in seconds end: End…, Nice string representation for item, SchedulerItem, make_scheduler_module(), asyncio (+5 more)

### Community 222 - "NewImageEvent"
Cohesion: 0.07
Nodes (29): NewImageEvent, Any, Event to be sent on a new image., Initializes new NewImageEvent. Args: filename: Name of new image file.…, ImageWriter, Any, Writes new images to disk., Creates a new image writer. Args: filename: Pattern for filename to store… (+21 more)

### Community 224 - ".move_heliocentric_polar"
Cohesion: 0.50
Nodes (3): Any, DEGREES, Moves on given coordinates. Args: mu: Cosine of the angular distance from Sun…

### Community 226 - ".move_heliographic_stonyhurst"
Cohesion: 0.50
Nodes (3): Any, DEGREES, Moves on given coordinates. Args: lon: Longitude in deg to track. lat: Latitude…

### Community 227 - "FileList"
Cohesion: 0.27
Nodes (5): FileList, Base class for file lists., Any, File list for testing., TestingFileList

### Community 228 - ".move_helioprojective"
Cohesion: 0.50
Nodes (3): Any, DEGREES, Moves on given coordinates. Args: theta_x: The theta_x coordinate. theta_y: The…

### Community 229 - "TempFile"
Cohesion: 0.24
Nodes (6): Any, Open/create a temp file. Args: name: Name of file. mode: Open mode. prefix:…, TempFile, asyncio, test_name(), test_write_file()

### Community 230 - "pyobs 2.0 Wire Protocol, State, and Access Control design doc"
Cohesion: 0.09
Nodes (22): pyobs/utils/config_schema.py: dataclass_to_schema, ICooling interface (reference pattern), slixmpp O(N^2) IQ handler dispatch bug (cross-referenced), IStructuredConfig design doc, IStructuredConfig interface, Rationale: IStructuredConfig coexists with IConfig (per-field vs bulk dataclass config), pyobs 2.0 Wire Protocol, State, and Access Control design doc, Access Control (ACLs): allow/deny, mode: enforce|log (+14 more)

### Community 232 - "Findings: driver/gui correctness review, all 8 repos (reviewed 2026-08-11)"
Cohesion: 0.13
Nodes (14): Context, Findings: driver/gui correctness review, all 8 repos (reviewed 2026-08-11), Plan: Driver/GUI split for all camera modules + qhyccd correctness review, pyobs-aravis, pyobs-asi, pyobs-fli (driver split only — gui.py not built yet), pyobs-flipro, pyobs-qhyccd (+6 more)

### Community 233 - "ImageFormat"
Cohesion: 0.24
Nodes (6): Any, Set the camera image format. Args: fmt: New image format. Raises: ValueError:…, ImageFormat, StrEnum, Enumerator for image formats. Attributes: INT8: 8 bit integer (i.e. byte).…, ImageFormatWidget

### Community 234 - "CHANGELOG.rst"
Cohesion: 0.22
Nodes (9): ejabberd shaper/xmpp_socket.erl reactivation bug (iag50srv capability-fetch timeouts), XmppComm disco#info role attribute (send/subscribe split), OnDemandScheduler CPU-bound work offloaded to ThreadPoolExecutor, Vfs.write_image()/write_fits() moved to asyncio.to_thread(), run_cpu_bound (scheduler/_executor.py), Vfs.write_fits (pyobs/vfs/vfs.py), Vfs.write_image (pyobs/vfs/vfs.py), specs/plans/event-role-advertising.md (+1 more)

### Community 235 - "Use a self-hosted Keycloak alongside odin, as two parallel auth backends"
Cohesion: 0.33
Nodes (5): Consequences, Considered Options, Context and Problem Statement, Decision Outcome, Use a self-hosted Keycloak alongside odin, as two parallel auth backends

### Community 236 - "Image class"
Cohesion: 0.20
Nodes (10): meta.AltAzOffsets, meta.ExpTime, Image class, Image.meta dict; rationale: keyed by class to avoid collisions between pipeline stages, kept out of FITS since it's runtime-only data, meta.OnSkyDistance, meta.PixelOffsets, meta.RaDecOffsets, meta.SkyOffsets (+2 more)

### Community 239 - ".set_config"
Cohesion: 0.50
Nodes (3): Any, ConfigValue, Apply a full structured config to this module. Args: config: Nested dict…

### Community 240 - "Module.startup() lifecycle helper"
Cohesion: 0.50
Nodes (4): Module.startup() lifecycle helper, ModuleState.STARTING, Rationale: delay send_presence() until READY to avoid capability-publish race, Gating RPC commands until module startup completes

### Community 241 - ".night_obs"
Cohesion: 0.50
Nodes (3): date, Observer, Returns the night for this time, i.e. the date of the start of the current…

### Community 242 - "Plan: Stop scheduler constraint/merit evaluation from blocking the event loop"
Cohesion: 0.14
Nodes (13): 1. Dedicated executor — new file `pyobs/robotic/scheduler/_executor.py`, 2. Offload the three call sites — `pyobs/robotic/scheduler/ondemandscheduler.py`, 3. Cache target-independent astropy results — `pyobs/robotic/scheduler/dataprovider.py`, 4. `AstroplanScheduler` — no change, Consequences, Considered options, Decision, Existing coverage (regression net, no changes needed) (+5 more)

### Community 243 - ".__init__"
Cohesion: 0.18
Nodes (8): Any, SkyCoord, Create an approximately equidistributed spherical grid. Args: n: Target number…, Initialize a Grid with a list of points. Args: points: Initial list of points…, Return the next point and remove it from the internal list. Returns: The next…, Create a regular lon/lat grid. Args: n_lon: Number of longitudinal divisions.…, Any, Initialize a GridNode. Args: log: If True, enable informational logging for…

### Community 244 - "test_basecamera.py"
Cohesion: 0.18
Nodes (15): asyncio, parametrize, DummyCamera's _expose() must raise AbortedError, not some guessed builtin, when…, Test basic open/close of BaseCamera., #547: BaseCamera must abort on BadWeatherEvent., #547: a BadWeatherEvent must actually trigger abort() -- exposure + any running…, #672: a BadWeatherEvent must not interrupt a dark/bias sequence -- the shutter…, Test the methods for remaining exposure time and progress. (+7 more)

### Community 245 - "SMBFile"
Cohesion: 0.22
Nodes (5): Any, Returns content of given path. Args: path: Path to list. kwargs: Parameters for…, VFS wrapper for a file that can be accessed over a SMB connection. Requires…, Open/create a file over a SSH connection. Args: name: Name of file. mode: Open…, SMBFile

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

### Community 250 - "test_pyobsd.py"
Cohesion: 0.29
Nodes (9): make_daemon(), Any, parametrize, Tests for PyobsDaemon._start_service()'s command construction -- in particular,…, file_log defaults to False -- --log-file is opt-in, not unconditional., test_start_service_creates_log_path_only_when_file_log_enabled(), test_start_service_creates_log_path_when_file_log_enabled(), test_start_service_default_is_no_file_log() (+1 more)

### Community 251 - "Two-phase Object lifecycle; rationale: __init__ must not touch hardware/external services (only store params, create children, register background tasks); open() is where side effects happen, so objects can be constructed cheaply/safely before being started"
Cohesion: 0.22
Nodes (8): Object.add_child_object(), create_object(), get_object(), Two-phase Object lifecycle; rationale: __init__ must not touch hardware/external services (only store params, create children, register background tasks); open() is where side effects happen, so objects can be constructed cheaply/safely before being started, class: key YAML instantiation; rationale: strips class key, passes remaining keys as kwargs, recursing into nested blocks, so any pyobs object graph is fully describable in YAML, Configuration utilities (pyobs.utils.config) API doc, pre_process_yaml(), Coordinate utilities (pyobs.utils.coordinates) API doc

### Community 252 - "Simulation recipe (doc)"
Cohesion: 0.42
Nodes (9): pyobs.modules.telescope (doc), BaseTelescope, DummyAltAzTelescope, DummyRaDecTelescope, DummySolarTelescope, Simulation recipe (doc), DummyCamera, pyobs_gui.GUI (+1 more)

### Community 254 - "ExposureTimeState"
Cohesion: 0.17
Nodes (16): ExposureTimeState, DummyVideo, Any, A dummy video module for testing — streams simulated noise frames., Creates a new dummy video module. Args: fps: Frames per second to simulate.…, Set the exposure time (frame interval). Args: exposure_time: Exposure time in…, Background task that generates simulated frames., make_dummyvideo() (+8 more)

### Community 255 - "test_baseroof.py"
Cohesion: 0.30
Nodes (8): MockBaseRoof, Any, asyncio, test_get_fits_header_before_closed(), test_get_fits_header_before_open(), test_not_ready(), test_open(), test_ready()

### Community 256 - "Decision"
Cohesion: 0.17
Nodes (11): 1. `ImageProcessor` — new methods and kwarg, 2. `PipelineMixin.run_pipeline()` — wrap each step, 3. `AstrometryDotNet` — migrate to handle_error, 4. Deprecation notes, 5. Tests, Consequences, Considered options, Decision (+3 more)

### Community 260 - "XEP_0009_timeout"
Cohesion: 0.17
Nodes (6): BasePlugin, A plugin for SleekXMPP, adding a timeout to RPC calls., XEP_0009_timeout, SleekXMPP: The Sleek XMPP Library Copyright (C) 2011 Nathanael C. Fritz, Dann…, MethodTimeout, ElementBase

### Community 261 - "robotic"
Cohesion: 0.43
Nodes (8): acquisition, fibercamera, fts, guiding, robotic, solar telescope, suncamera, weather

### Community 262 - "Archive (image archive base)"
Cohesion: 0.32
Nodes (8): Archive (image archive base), LocalArchive, PyobsArchive, ArchiveSkyflatPriorities, Archive, Image archives (pyobs.robotic.utils.archive) API doc, LocalArchive, PyobsArchive

### Community 264 - "._get_client"
Cohesion: 0.18
Nodes (6): Get a proxy to the given client. Args: client: Name of client. Returns: Proxy…, Fetch capabilities for a single interface and push them into the given proxy…, Returns list of interfaces for given client. Args: client: Name of client.…, Subscribe to state updates for a given module and interface. Delivers the…, Unsubscribe from state updates. Args: module: Name of remote module. interface:…, StateCallback

### Community 266 - "BaseVideo"
Cohesion: 0.07
Nodes (20): IImageType, ImageFitsHeaderMixin, IVideo, BaseVideo, Whether the server is started., Handles access to / and returns HTML page. Args: request: Request to respond…, Handles GET access to /ping for testing connectivity. Args: request: Request to…, Handles access to /video.mjpg and returns the video. Args: request: Request to… (+12 more)

### Community 268 - "._get_next"
Cohesion: 0.33
Nodes (4): SkyCoord, Log a point if logging is enabled. For SkyCoord instances, logs RA/Dec in…, Return the next point in the sequence. Implementors must return either a (x, y)…, Return the next point, storing it as the last yielded value. Returns: A point…

### Community 269 - "Shared authentication across pyobs web projects via Keycloak"
Cohesion: 0.22
Nodes (8): Decision: Keycloak as the single issuer; observation-portal becomes a brokered upstream, not a second integration, Decision: realm layout and user mapping, Non-issue: upstream OIDC brokering (including observation-portal), Note: observation-portal's own token validation shortcut (context, not adopted), Problem, Proposed change: `pyobs-auth` package, Scope, Shared authentication across pyobs web projects via Keycloak

### Community 270 - "Plan: `pyobs-gui` navbar keyboard shortcuts"
Cohesion: 0.18
Nodes (10): Binding is by page name, not by widget or list-item instance, File changes, Key scheme, Motivation, Plan: `pyobs-gui` navbar keyboard shortcuts, Shortcut wiring, State, Verification (once implemented) (+2 more)

### Community 271 - "filters.py"
Cohesion: 0.15
Nodes (20): ConvertGridFrame, ConvertGridToSkyCoord, FromList, GridFilterValue, Convert (x, y) degree tuples to SkyCoord objects. Wraps a tuple-producing grid…, Transform SkyCoord points to a different frame., Select closest point from a list. Only select points if they are closer than a…, Filter points by numeric constraints on x and y. Accepts points as: - (x, y)… (+12 more)

### Community 272 - "BaseCamera"
Cohesion: 0.04
Nodes (40): Event, ExposureStatus, Header, ICamera, IDataSequence, IExposure, IExposureTime, Image (+32 more)

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

### Community 281 - "test_memory_archives.py"
Cohesion: 0.08
Nodes (51): MemoryTaskArchive, Any, In-memory task archive for testing and simple deployments., Returns time when tasks last changed., Returns list of projects., Returns list of all tasks., Returns task with given ID, or None if not found., make_obs() (+43 more)

### Community 282 - "wait_for"
Cohesion: 0.17
Nodes (12): DummyCamera.open() must publish IWindow.Capabilities with the SimCamera full…, DummyCamera.open() must publish IModule.Capabilities with version and label., get_capabilities() must return None for an interface DummyCamera doesn't…, Poll *condition* until truthy or *timeout* seconds elapse., DummyCamera's _cooling_thread publishes CoolingState every second. An observer…, After calling set_cooling via RPC, the published CoolingState must reflect the…, test_dummy_camera_cooling_state_reflects_set_cooling(), test_dummy_camera_no_capabilities_for_unconfigured_interface() (+4 more)

### Community 283 - "Target"
Cohesion: 0.29
Nodes (4): Target, Set the resolved target if not already set, e.g. when restoring from an…, The resolved target, or the static target if not dynamic., Target for this specific run: the observation's own record if known, otherwise…

### Community 284 - "GoodWeatherEvent"
Cohesion: 0.22
Nodes (7): GoodWeatherEvent, Any, Event to be sent on good weather., Initializes a new good weather event. Args: eta: Predicted ETA for when the…, test_good_weather_no_eta(), test_good_weather_roundtrip(), test_good_weather_with_eta()

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

### Community 290 - "TaskFinishedEvent"
Cohesion: 0.10
Nodes (13): Any, Event to be sent when a task has failed., Initializes a new task failed event. Args: name: Name of task that just…, TaskFailedEvent, Any, Event to be sent when a task has finished., Initializes a new task finished event. Args: name: Name of task that just…, TaskFinishedEvent (+5 more)

### Community 292 - "Plan: `pyobs-gui` IAutoGuiding widget"
Cohesion: 0.25
Nodes (7): Known bug in the shipped widget (to fix alongside this change), Plan: `pyobs-gui` IAutoGuiding widget, Problem: pixel offsets aren't physical, and the per-image correction is discarded, Proposed pyobs-core change, Resolved from the original open questions, Shipped (pyobs-core, `develop`), Widget design (pyobs-gui)

### Community 294 - "_dummytelescopebase.py"
Cohesion: 0.06
Nodes (32): FiltersCapabilities, FocuserState, SensorReading, TemperaturesState, ITrackingMode, Any, StrEnum, Discrete, hardware-native tracking rate. (+24 more)

### Community 295 - "Investigation: pyobs-gui receives every LogEvent twice (SAAO/monet production)"
Cohesion: 0.25
Nodes (7): Access used, Artifacts from this session, Investigation: pyobs-gui receives every LogEvent twice (SAAO/monet production), Next steps, Problem, What's confirmed, What's ruled out

### Community 297 - "OffsetResult"
Cohesion: 0.11
Nodes (20): ApplyAltAzOffsets, Any, EarthLocation, Apply offsets from a given image to a given telescope., Initializes a new ApplyAltAzOffsets. Args: min_offset: Min offset in arcsec to…, Take the pixel offsets stored in the meta data of the image and apply them to…, ApplyOffsets, OffsetResult (+12 more)

### Community 298 - "Plan: `pyobs-gui` IAutoFocus widget"
Cohesion: 0.29
Nodes (6): Current state (pyobs-core, `develop`), Gap, Open questions, Plan: `pyobs-gui` IAutoFocus widget, Proposed pyobs-core change, Widget design (pyobs-gui)

### Community 300 - "ADR-0008: _safe_send keeps bounded retry unlike capability/subscribe fetches"
Cohesion: 0.40
Nodes (5): ADR-0008: _safe_send keeps bounded retry unlike capability/subscribe fetches, #664/#666 slow-shaper hang incident, XmppComm._get_capabilities(), XmppComm._retry_delay() (jittered capped backoff), XmppComm._safe_send()

### Community 301 - "Module._watch_event_loop_lag"
Cohesion: 0.33
Nodes (5): BrotDome._update_status, ADR-0009: Event-loop lag watchdog lives on Module, FocusModel._update, pyobs-iag50 capability-fetch timeout incident, Module._watch_event_loop_lag

### Community 302 - "Plan: Surface unrecognized kwargs in `Object.__init__` instead of silently discarding them"
Cohesion: 0.29
Nodes (6): Implementation checklist, Non-goals (for now — this is a stub, scope may change once investigated), Open questions (this plan needs an investigation pass before it has a Decision section), Plan: Surface unrecognized kwargs in `Object.__init__` instead of silently discarding them, Problem, Why not fixed already / why it's not trivial

### Community 303 - "pyobs.modules.image (doc)"
Cohesion: 0.40
Nodes (5): pyobs.modules.image (doc), ImageWatcher, ImageWriter, Pipeline (image module), Seeing

### Community 304 - "Plan: `pyobs-auth` + Keycloak integration"
Cohesion: 0.29
Nodes (6): 0. observation-portal (Keycloak admin config + small observation-portal config change), 1. `pyobs-auth` package (new repo) — done, released, 2. pyobs-archive — cutover, not dual-path — done, confirmed working end to end, 3. pyobs-robotic-backend, 4. Not in this plan, Plan: `pyobs-auth` + Keycloak integration

### Community 305 - "Plan: Exception handling across the RPC boundary (reconstructed)"
Cohesion: 0.33
Nodes (5): Architecture, File Map (representative, not exhaustive — see commit diffs for the full ~74-file list), Goal, Plan: Exception handling across the RPC boundary (reconstructed), Tasks

### Community 306 - "Plan: Decouple `ICamera`/`IExposure` (reconstructed)"
Cohesion: 0.33
Nodes (5): Architecture, File Map, Goal, Plan: Decouple `ICamera`/`IExposure` (reconstructed), Tasks

### Community 307 - "Plan: `IDataSequence` — server-side counted data sequences (reconstructed)"
Cohesion: 0.33
Nodes (5): Architecture, File Map, Goal, Plan: `IDataSequence` — server-side counted data sequences (reconstructed), Tasks

### Community 308 - "Plan: Unify TRIMSEC handling into `Image.trim()` (reconstructed)"
Cohesion: 0.33
Nodes (5): Architecture, File Map, Goal, Plan: Unify TRIMSEC handling into `Image.trim()` (reconstructed), Tasks

### Community 309 - "Plan: Module observer-location capabilities (reconstructed)"
Cohesion: 0.33
Nodes (5): Architecture, File Map, Goal, Plan: Module observer-location capabilities (reconstructed), Tasks

### Community 310 - "Plan: Advertise event send/subscribe role in disco#info"
Cohesion: 0.33
Nodes (5): Architecture, File Map, Plan: Advertise event send/subscribe role in disco#info, Problem, Tasks

### Community 311 - "Plan: raw-frame streaming endpoint in `BaseVideo`"
Cohesion: 0.33
Nodes (5): Context, Explicitly out of scope for this plan, Plan: raw-frame streaming endpoint in `BaseVideo`, Testing, Todo

### Community 312 - ".set_gain"
Cohesion: 0.40
Nodes (3): Any, Set the camera gain. Args: gain: New camera gain. Raises: ValueError: If gain…, Set the camera offset. Args: offset: New camera offset. Raises: ValueError: If…

### Community 314 - "Implemented"
Cohesion: 0.40
Nodes (4): Implemented, Option A: reactive-only (already shipped, zero work), Option B: proactive greying-out — effort estimate (~half a day, 3-5 hours), Plan: `pyobs-gui` ACL-aware widget gating

### Community 315 - "Plan: `pyobs-gui` IAcquisition widget"
Cohesion: 0.40
Nodes (4): Plan: `pyobs-gui` IAcquisition widget, Resolved from the original open questions, Shipped (pyobs-core, `develop`), Widget design (pyobs-gui) — shipped

### Community 316 - "ModuleLocation dataclass (nested in ModuleCapabilities)"
Cohesion: 0.50
Nodes (4): Location-mismatch warning via _on_module_opened, Rationale: location as one-shot capability, not pubsub state, ModuleLocation dataclass (nested in ModuleCapabilities), Module observer-location capabilities design doc

### Community 317 - "check_pyobs_releases.sh"
Cohesion: 0.70
Nodes (4): check_repo(), main(), print_header(), check_pyobs_releases.sh script

### Community 318 - "check_ejabberd_notify.py"
Cohesion: 0.60
Nodes (4): connect(), main(), make_client(), Minimal ejabberd notification test — no pyobs code involved.

### Community 319 - "_ProxyContext"
Cohesion: 0.40
Nodes (3): _ProxyContext, ProxyType, Returned by Comm.proxy() / Object.proxy() / Comm.safe_proxy(). Must be used as:…

### Community 320 - "MockBaseDome"
Cohesion: 0.21
Nodes (8): pyobs.modules.roof (doc), BaseDome, BaseRoof, DummyRoof, MockBaseDome, Any, asyncio, test_get_fits_header_before()

### Community 321 - "test_exceptions.py"
Cohesion: 0.29
Nodes (4): ForbiddenError, Raised when a caller is not permitted to invoke a method under the target…, test_forbidden_error(), test_log_only_logs_once()

### Community 322 - "Photometry (pyobs.images.processors.photometry) API doc"
Cohesion: 0.83
Nodes (4): Photometry (pyobs.images.processors.photometry) API doc, Photometry, PhotUtilsPhotometry, SepPhotometry

### Community 323 - "IDataSequence"
Cohesion: 0.29
Nodes (6): IDataSequence, Any, SECONDS, The module can grab a counted sequence of data (images, spectra, ...)., Start a sequence of `count` grabs. Returns immediately; progress is available…, Stop the sequence after the current grab. The grab currently in progress, if…

### Community 324 - "IFocuser"
Cohesion: 0.32
Nodes (6): IFocuser, Any, MM, The module is a focusing device., Sets new focus. Args: focus: New focus value in mm. Raises:…, Sets focus offset. Args: offset: New focus offset in mm. Raises: ValueError: If…

### Community 326 - "weather.py"
Cohesion: 0.19
Nodes (9): IWeather, Any, The module acts as a weather station., Return value for given sensor. Args: station: Name of weather station to get…, WeatherSensorReading, Weather modules. TODO: write doc, Return value for given sensor. Args: station: Name of weather station to get…, The weather station's API response was malformed or incomplete (missing an… (+1 more)

### Community 328 - "object.py"
Cohesion: 0.05
Nodes (49): PrivateAttrMixin, :class:`~pyobs.object.Object` is the base for almost all classes in *pyobs*. It…, HeliocentricPolarTarget, Target, HelioprojectiveTarget, SkyCoord, Target, CsvPicker (+41 more)

### Community 333 - ".__init__"
Cohesion: 0.40
Nodes (4): Any, Pipeline, ProgressCallback, Args: archive: Archive to fetch raw and calibration frames from. pipeline:…

### Community 334 - "Comm"
Cohesion: 0.07
Nodes (14): Comm responsibility: Discovery (clients_with_interface), Comm responsibility: Events (broadcast typed events), Comm, Base class for all Comm modules in pyobs., Returns list of currently connected clients. Returns: (list) list of currently…, Returns list of currently connected clients that implement the given interface.…, Checks, whether the given client supports the given interface. Args: client:…, Execute a given method on a remote client. Args: client (str): ID of client.… (+6 more)

### Community 335 - "IFlatField"
Cohesion: 0.33
Nodes (5): IFlatField, Any, SECONDS, The module performs flat-fielding., Do a series of flat fields. Args: count: Number of images to take Returns:…

### Community 337 - ".set_offsets_altaz"
Cohesion: 0.50
Nodes (3): Any, DEGREES, Move an Alt/Az offset. Args: dalt: Altitude offset in degrees. daz: Azimuth…

### Community 338 - "Pipeline"
Cohesion: 0.14
Nodes (24): ProgressEvent, Pipeline, Calibrate a single science frame. Args: image: Image to calibrate. Returns:…, Pipeline based on the astropy package ccdproc., MasterCalibCreated, A master calibration frame (BIAS/DARK/SKYFLAT) was created and stored/uploaded., One science frame finished processing (successfully or not). index/total are…, ScienceFrameProcessed (+16 more)

### Community 340 - "IRotation"
Cohesion: 0.33
Nodes (5): IRotation, Any, DEGREES, The module controls a device that can rotate., Sets the rotation angle to the given value in degrees. Raises: MoveError: If…

### Community 341 - "pyobs.modules.weather (doc)"
Cohesion: 1.00
Nodes (3): pyobs.modules.weather (doc), MockWeather, Weather (module)

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
- **549 isolated node(s):** `pyobs-core`, `Problem`, `What's ruled out`, `What's confirmed`, `Next steps` (+544 more)
  These have ≤1 connection - possible missing edges or undocumented components.
- **46 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **What is the exact relationship between `Configuration utilities (pyobs.utils.config) API doc` and `Coordinate utilities (pyobs.utils.coordinates) API doc`?**
  _Edge tagged AMBIGUOUS (relation: conceptually_related_to) - confidence is low._
- **What is the exact relationship between `PyObsError` and `ScriptRunner.run()`?**
  _Edge tagged AMBIGUOUS (relation: conceptually_related_to) - confidence is low._
- **What is the exact relationship between `FocusError` and `FocusModel.set_optimal_focus`?**
  _Edge tagged AMBIGUOUS (relation: conceptually_related_to) - confidence is low._
- **Why does `Time` connect `Time` to `BackendTaskArchive`, `BaseGuiding`, `RunningState`, `Interface`, `Module`, `ImageProcessor`, `TaskData`, `Grid`, `pyobs.py`, `test_yaml_archives.py`, `FilenameFormatter`, `TimeDelta`, `DummyRaDecTelescope`, `Scheduler`, `mixins/test_fitsheader.py`, `Event`, `.__init__`, `filters.py`, `test_flatfielder.py`, `test_memory_archives.py`, `tests/test_events.py`, `GoodWeatherEvent`, `test_control.py`, `ImageType`, `Object`, `basetelescope.py`, `._update_root`, `ExpTimeEval`, `CoolingState`, `IPointingAltAz.py`, `_dummytelescopebase.py`, `AstroplanScheduler`, `OffsetResult`, `test_backend_archives.py`, `imaging.py`, `robotic/test_scheduler.py`, `SkyflatPriorities`, `test_schedulereader.py`, `Calibration`, `Proxy`, `_ProxyContext`, `FlatFielder`, `TaskStartedEvent`, `Offsets`, `weather.py`, `.now`, `ObservationList`, `object.py`, `SiderealTarget`, `test_proxy.py`, `Weather`, `flatfield/scheduler.py`, `MotionStatus`, `Pipeline`, `DummySolarTelescope`, `DummyCamera`, `flatfield/test_scheduler.py`, `NewImageEvent`, `test_pyobs_archive.py`, `application.py`, `test_coordinates.py`, `LocalArchive`, `.night_obs`, `Test Commlogging (comm)`, `ImagingScript`, `test_darkbias.py`?**
  _High betweenness centrality (0.250) - this node is a cross-community bridge._
- **Why does `Image` connect `Image` to `BaseGuiding`, `.__init__`, `RunningState`, `_SepAperturePhotometry`, `Interface`, `ImageProcessor`, `test_yaml_archives.py`, `AstrometryDotNet`, `FilenameFormatter`, `mixins/test_fitsheader.py`, `PipelineMixin`, `test_flatfielder.py`, `_DaoBackgroundRemover`, `SoftBin`, `AddMask`, `ImageType`, `_DotNetRequest`, `._update_root`, `GuidingStatisticsPixelOffset`, `OffsetResult`, `utils/exceptions.py`, `StarExpTimeEstimator`, `Calibration`, `PillowHelper`, `test_acquisition.py`, `test_basevideo.py`, `CatalogCircularMask`, `Offsets`, `test_autoguiding.py`, `Smooth`, `SkyOffsets`, `Pipeline`, `Ring`, `DummyCamera`, `ProjectedOffsets`, `test_pyobs_archive.py`, `FocusSeries`, `_SourceCatalog`, `_DotNetRequestBuilder`, `LocalArchive`, `_PhotUtilAperturePhotometry`, `VFSFile`, `ImageSourceFilter`?**
  _High betweenness centrality (0.182) - this node is a cross-community bridge._
- **Why does `Module` connect `Module` to `FitsHeaderEntry`, `BaseGuiding`, `RunningState`, `Interface`, `test_dummymode.py`, `._get_client`, `Events API doc (pyobs.events)`, `test_kiosk.py`, `MultiModule`, `IModule`, `.__init__`, `Scheduler`, `mixins/test_fitsheader.py`, `PipelineMixin`, `Kiosk`, `Any`, `FlatField`, `test_presence.py`, `Object`, `basetelescope.py`, `LogEvent`, `Stellarium`, `IPointingAltAz.py`, `test_module_state_publishing.py`, `robotic/test_scheduler.py`, `StandAlone`, `utils/exceptions.py`, `module.py`, `xmpp/rpc.py`, `test_xmpp_presence.py`, `test_acquisition.py`, `Proxy`, `test_basevideo.py`, `PointingSeries`, `GridNode`, `Telegram`, `ModuleState`, `weather.py`, `ImageWatcher`, `ObservationList`, `MockWeather`, `test_autoguiding.py`, `Weather`, `flatfield/scheduler.py`, `MotionStatus`, `HttpFileCache`, `xmppcomm.py`, `test_exception_logging.py`, `Application`, `flatfield/test_scheduler.py`, `NewImageEvent`, `application.py`, `make_proxy_cm`, `ScriptRunner`, `FocusModel`, `_AbortableModule`?**
  _High betweenness centrality (0.077) - this node is a cross-community bridge._
- **Are the 163 inferred relationships involving `Time` (e.g. with `PyobsCLI` and `Proxy`) actually correct?**
  _`Time` has 163 INFERRED edges - model-reasoned connections that need verification._