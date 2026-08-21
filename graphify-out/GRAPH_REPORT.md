# Graph Report - pyobs-core  (2026-08-21)

## Corpus Check
- 810 files · ~454,313 words
- Verdict: corpus is large enough that graph structure adds value.

## Summary
- 9131 nodes · 21624 edges · 444 communities (389 shown, 55 thin omitted)
- Extraction: 93% EXTRACTED · 7% INFERRED · 0% AMBIGUOUS · INFERRED: 1414 edges (avg confidence: 0.55)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `640c1ce8`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- utils/exceptions.py
- .__init__
- Time
- Module
- benchmark_state_throughput.py
- BaseVideo
- Image
- Observation
- focusmodel.py
- ImageProcessor
- Any
- Interface
- xmpp/rpc.py
- RuntimeError
- robotic/task.py
- VirtualFileSystem
- BackendObservationArchive
- test_units.py
- DummyRoof
- mixins/test_fitsheader.py
- Event
- BaseGuiding
- AstrometryDotNet
- test_flatfielder.py
- LocalComm
- tests/test_events.py
- test_lco_http.py
- DummySolarTelescope
- FitsHeaderEntry
- WindowingWidget
- Interfaces (pyobs.interfaces) API doc
- test_control.py
- test_weatheraware.py
- BaseCamera
- SolarElevationConstraint
- .set_exposure_time
- Future
- SiderealTarget
- CoolingState
- IPointingAltAz.py
- _DotNetRequest
- SkyOffsets
- test_xmpp_event_subscriptions.py
- Proxy
- mixins/fitsheader.py
- robotic/test_scheduler.py
- StandAlone
- HttpFileCache
- _PhotometryCalculator
- test_stellarexptime.py
- ExpTimeEstimator
- test_dynamictarget.py
- test_xmpp_presence.py
- test_shellcommand.py
- Calibration
- test_csvpicker_scheduler.py
- Publisher
- .__call__
- test_autoguiding.py
- ImageType
- FilenameFormatter
- test_basevideo.py
- test_yaml_archives.py
- Portal
- FlatFielder
- IExposure
- Telegram
- test_astroplanscheduler.py
- TimeDelta
- Offsets
- .now
- PyObsError
- test_proxy.py
- XEP_0009
- LogEvent
- PyobsDaemon
- test_acquisition.py
- test_config.py
- TaskData
- xmppcomm.py
- Weather
- ImagingScript
- test_transit_mastermind.py
- DummyCamera
- PipelineMixin
- Ring
- loaded_pyobs_packages
- make_obs_archive
- test_exception_logging.py
- test_config_schema.py
- Application
- DummyComm
- get_class_from_string
- ProjectedOffsets
- test_pyobs_archive.py
- HttpFile
- FrameInfo
- application.py
- FocusSeries
- _DaoBackgroundRemover
- make_proxy_cm
- TaskStartedEvent
- .get_object
- test_lcoscript.py
- test_coordinates.py
- get_registered_interface
- DummyMode
- LocalArchive
- Plan: Systematic ejabberd throughput/latency benchmarking
- _PhotUtilAperturePhotometry
- Mixins (pyobs.mixins) API doc
- Script base class
- ImageWatcher
- Comm
- CommLoggingHandler
- test_dummyradectelescope.py
- SkyFlatsBasePointing
- modules/image/__init__.py
- MemoryFile
- VFSFile
- LocalFile
- test_version_mismatch.py
- CLAUDE.md (repo guide)
- ._record_exception
- FocusModel
- SFTPFile
- ImageSourceFilter
- test_darkbias.py
- WeatherSensors
- TempFile
- Plan: pyobs-pipeline
- Test Localcomm (local)
- comm.py
- .__init__
- flatfield/test_scheduler.py
- test_dummymode.py
- MockWeather
- SkyflatPriorities
- Grid
- test_kiosk.py
- pyobs.py
- Robotic recipe (doc)
- BufferedFile
- GuidingStatistics
- RollingTimeAverage
- TaskFailedEvent
- WeatherApi
- BackendTaskArchive
- .can_run
- ._set_optimal_focus
- tests/xmpp/docker-compose.yml (ejabberd integration test container)
- `OBSNUM`: per-night observation counter in FITS headers
- 3rd party packages (doc)
- test_basetelescope.py
- SSHFile
- create_rst.py
- LcoScript
- SoftBin
- AddMask
- DataCache
- RandomizeGrid
- .retrieve_class_on_deserialization
- MockBaseDome
- _SourceCatalog
- Design
- ExpTimeEval
- Plan: Stop ImageWatcher per-file processing from blocking the event loop
- Plan: `IDataSequence` — server-side counted data sequences (reconstructed)
- wait_for
- ResolvableErrorLogger
- .__init__
- ._get_client
- test_grab_sequence.py
- binding.py
- Event
- wait_for
- test_xmppcomm_event_payload.py
- test_httpfilecache.py
- test_dummyvideo.py
- MotionStatusChangedEvent
- Steering: astropy IERS auto-download blocks event loop
- .move_radec
- CLI
- .set_focus
- Merit
- ejabberd shaper throttling bug (xmpp_socket.erl re-arm) & fix
- test_xmpp_acl.py
- Plan: Make the pydantic config layer reject unknown keys (`extra="forbid"`)
- Work Plan
- Plan: `pyobs-gui` TelescopeWidget layout — width floor investigation & design notes
- .__init__
- GridPipeline
- Plan: Make mixin `__init__` composition cooperative, then enforce unrecognized kwargs at `Object.__init__`
- test_comm_interface_resolution.py
- What's New in pyobs 2.0 (doc)
- test_imagewriter.py
- localcomm.py
- .__init__
- .get_fits_headers
- comm/test_events.py
- asyncio
- test_basecamera.py
- show_module_info.py
- RunningState
- FitsHeaderMixin
- robotic
- Scheduler module
- BaseModel (pyobs.utils.serialization)
- Decision
- Stellarium
- .__init__
- Plan: Widget plugin mechanism + `pyside6-deploy` packaging for `pyobs-gui`
- Plan: Split archive prefetch from CPU-bound merit evaluation, to unblock a `ProcessPoolExecutor`
- .image_handler
- Image (pyobs.images.processors.image) API doc
- Offsets (pyobs.images.processors.offsets) API doc
- Constraint
- Smooth
- Scheduler
- test_autofocus.py
- Archive
- LogScript
- test_imagewatcher.py
- XEP_0009_timeout
- is_valid_jid
- .move_heliographic_stonyhurst
- FileList
- .move_helioprojective
- pyobs 2.0 Wire Protocol, State, and Access Control design doc
- Plan: Log the loaded pyobs-* package versions at module startup
- Findings: driver/gui correctness review, all 8 repos (reviewed 2026-08-11)
- GridNode
- CHANGELOG.rst
- Use a self-hosted Keycloak alongside odin, as two parallel auth backends
- Image class
- ._expose
- Implementation
- IMotion
- Module.startup() lifecycle helper
- Object
- Plan: Stop scheduler constraint/merit evaluation from blocking the event loop
- .__init__
- watch_log_events_no_interest.py
- pyobs-gui as a standalone binary (umbrella design)
- Plan: Enforce state publishing for stateful interfaces
- Plan: `pyobs-gui` login window
- test_safe_send.py
- test_exceptions.py
- Two-phase Object lifecycle; rationale: __init__ must not touch hardware/external services (only store params, create children, register background tasks); open() is where side effects happen, so objects can be constructed cheaply/safely before being started
- Simulation recipe (doc)
- IOffsetsAltAz.py
- XmppComm
- Decision
- .can_run
- enums.py
- robotic
- Archive (image archive base)
- Scheduler
- integration/conftest.py
- CasesRunner
- RemoveBackground
- test_camerasettings.py
- ._get_next
- Discussion: LogEvent double-delivery fix — should we drop add_interest()?
- Plan: `pyobs-gui` navbar keyboard shortcuts
- Enum
- test_baseroof.py
- Image.trim
- conftest.py
- Misc (pyobs.images.processors.misc) API doc
- PolymorphicBaseModel
- Plan: Stop gating backend-archive refreshes on the `last_*_update` marker
- GuidingStatisticsPixelOffset
- GuidingStatisticsSkyOffset
- ObservationList
- .move_heliocentric_polar
- WeatherStatus
- run_cpu_bound
- Implementation
- Plan: Interactive login/settings dialog for `pyobs-gui`, deferring `Application`'s module construction
- pyobs.modules.utils (doc)
- Plan: Add baseline tests to core-tier repos, then enable grouped Dependabot auto-merge
- Plan: CORS + token auth for `HttpFileCache`
- Plan: raw-frame streaming endpoint in `BaseVideo`
- Plan: `pyobs-gui` IAutoGuiding widget
- ExposureStatus
- SchedulerItem
- Investigation: pyobs-gui receives every LogEvent twice (SAAO/monet production)
- Plan: Module observer-location capabilities (reconstructed)
- ._subscribe_presence
- datetime
- ADR-0008: _safe_send keeps bounded retry unlike capability/subscribe fetches
- Module._watch_event_loop_lag
- Plan: Surface unrecognized kwargs in `Object.__init__` instead of silently discarding them
- pyobs.modules.image (doc)
- ._filter_data
- test_pyobsd.py
- ._change_exposure_status
- Plan: Bound the FITS-header fetch so a dead peer can't stall the frame
- plans/index.md
- ScriptRunner
- SMBFile
- .__call__
- .set_tracking_rate
- Fleet open items: open issues and plans across the pyobs fleet
- Any
- .get_interfaces
- ModuleLocation dataclass (nested in ModuleCapabilities)
- check_pyobs_releases.sh
- check_ejabberd_notify.py
- GraticuleSphericalGrid
- Photometry (pyobs.images.processors.photometry) API doc
- Plan: `pyobs-gui` IAutoFocus widget
- .get_meta
- .resolve
- .night_obs
- .get_config_value
- IAbortable
- .grab_data
- Plan: Exception handling across the RPC boundary (reconstructed)
- Plan: Decouple `ICamera`/`IExposure` (reconstructed)
- Plan: Advertise event send/subscribe role in disco#info
- Target
- asyncio
- .set_offsets_altaz
- .set_config
- .flat_field
- .get_interfaces
- .set_offsets_radec
- .track_orbital_elements
- Script
- pyobs.modules.weather (doc)
- .append_last
- .__iter__
- .set_cooling
- README.md
- Install-ejabberd (xmpp)
- XmppComm._disconnected
- Autocompletion ()
- .log_last
- pyobs.modules.pointing (doc)
- Any
- Header
- NamedTuple
- SkyCoord
- Target
- asyncio
- fixture
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
- BackendObservationArchive
- BackendTaskArchive
- Observation
- ObservationState

## God Nodes (most connected - your core abstractions)
1. `Time` - 545 edges
2. `Image` - 441 edges
3. `Task` - 214 edges
4. `Interface` - 186 edges
5. `Module` - 177 edges
6. `DataProvider` - 155 edges
7. `ObservationList` - 152 edges
8. `Event` - 149 edges
9. `Comm` - 114 edges
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

## Communities (444 total, 55 thin omitted)

### Community 0 - "utils/exceptions.py"
Cohesion: 0.09
Nodes (27): Declare that the given PyobsError types (and their subclasses) fire often…, AbortedError, AcquisitionError, DeviceBusyError, GeneralError, InitError, InvalidArgumentError, ModuleError (+19 more)

### Community 1 - ".__init__"
Cohesion: 0.04
Nodes (34): Any, Init new image processor. Args: on_error: How the pipeline should handle an…, Any, Init a new circle processor. Args: x: Center x coordinate. y: Center y…, Any, Init a new crosshair processor. Args: x: Center x coordinate. y: Center y…, Any, Init a new grayscale processor. Args: x: Center x coordinate. y: Center y… (+26 more)

### Community 2 - "Time"
Cohesion: 0.03
Nodes (102): PolymorphicBaseModel, AirmassConstraint, ndarray, SkyCoord, Constraint, ndarray, SkyCoord, Returns a boolean mask of candidates passing this constraint. Default… (+94 more)

### Community 3 - "Module"
Cohesion: 0.02
Nodes (148): AbstractEventLoop, ConfigCapabilities, IModule, ModuleCapabilities, ModuleLocation, Any, The module is actually a module. Implemented by all modules., Reset error of module, if any. (+140 more)

### Community 4 - "benchmark_state_throughput.py"
Cohesion: 0.06
Nodes (52): BinningState, IBinning, Any, The camera supports binning, to be used together with…, Set the camera binning. Args: x: X binning. y: Y binning. Raises: ValueError:…, FilterState, FlatField, Any (+44 more)

### Community 5 - "BaseVideo"
Cohesion: 0.07
Nodes (27): BaseVideo, LastImage, NextImage, Any, NamedTuple, NDArray, Whether the server is started., Handles access to /video.mjpg and returns the video. Args: request: Request to… (+19 more)

### Community 6 - "Image"
Cohesion: 0.03
Nodes (92): ImageHDU, Image, Any, CCDData, floating, HDUList, Header, NDArray (+84 more)

### Community 7 - "Observation"
Cohesion: 0.03
Nodes (97): Modules for robotic mode. TODO: write doc, Mastermind, Any, Returns FITS header for the current status of this module. Args: namespaces: If…, Mastermind for a full robotic mode., Initialize a new auto focus system. Args: schedule: Object that can return…, Initialize a new scheduler. Args: scheduler: Scheduler to use. tasks: Task…, Observation (+89 more)

### Community 8 - "focusmodel.py"
Cohesion: 0.09
Nodes (23): IData, Any, Grabs an image and returns reference. Args: broadcast: Broadcast existence of…, The module can grab and return an image from whatever device., IFilters, Any, The module can change filters in a device., Set the current filter. Args: filter_name: Name of filter to set. Raises:… (+15 more)

### Community 9 - "ImageProcessor"
Cohesion: 0.03
Nodes (60): Annotation processors doc, Some info about :class:`pyobs.images.Image`., ImageProcessor, The error handling mode for this step., Processes an image. Args: image: Image to process. Returns: Processed image., Resets state of image processor, Circle, Draw a circle on an image, optionally interpreting the center in WCS… (+52 more)

### Community 10 - "Any"
Cohesion: 0.07
Nodes (16): Any, Safely send an XMPP message. Args: method: Method to call. *args: Parameters…, Fetch the current item for *node* and dispatch it to *callback*. Called when a…, Store published capabilities for inclusion in disco#info responses., Return this client's own published capabilities., Fetch and deserialize capabilities for a remote module's interface. Retries…, Subscribe to a pubsub node, retrying until the node exists. Runs as a…, Create a new XMPP Comm module. Either a fill JID needs to be provided, or a set… (+8 more)

### Community 11 - "Interface"
Cohesion: 0.03
Nodes (118): ABC, Binning, BinningCapabilities, ICalibrate, Any, Calibrate the device. Raises: GeneralError: If calibration failed., The module can calibrate a device., IConfig (+110 more)

### Community 12 - "xmpp/rpc.py"
Cohesion: 0.09
Nodes (25): fault_to_xml(), params_to_xml(), Any, ClientXMPP, Element, Exception, Parse <fault> and return (exception_qualified_name, message)., RPC wrapper around XEP-0009 using pyobs 2.0 payload encoding (urn:pyobs:rpc:1). (+17 more)

### Community 13 - "RuntimeError"
Cohesion: 0.05
Nodes (54): MonkeyPatch, Any, Init new exposure time estimator., Any, Create new exp time estimator from single star. Args: edge: Fraction of image…, Process an image and calculates the new exposure time Args: image: Image to…, Estimate a new exposure time from the brightest unsaturated star in the image.…, StarExpTimeEstimator (+46 more)

### Community 14 - "robotic/task.py"
Cohesion: 0.05
Nodes (27): BaseModel, # TODO: add abort (see old robotic/scheduler.py), Abstract base class for tasks scheduler., TaskScheduler, FileSystemTaskArchive, Any, Task archive based on files., Creates a new filesystem-based task archive. Args: extension: Extension of… (+19 more)

### Community 15 - "VirtualFileSystem"
Cohesion: 0.08
Nodes (24): Any, DataFrame, HDUList, Convenience function for writing an Image to a FITS file. Args: filename: Name…, Convenience function that wraps around open_file() to read an Image. Args:…, Convenience function for writing an Image to a FITS file. Args: filename: Name…, Convenience function for writing bytes to a file. Args: filename: Name of file…, Convenience function for reading a CSV file into a DataFrame. Args: filename:… (+16 more)

### Community 16 - "BackendObservationArchive"
Cohesion: 0.07
Nodes (24): ObservationArchive, BackendObservationArchive, Any, ClientSession, Observation, ObservationState, Task, TaskArchive (+16 more)

### Community 17 - "test_units.py"
Cohesion: 0.10
Nodes (24): _extract_unit(), _interface_unit_hints(), Any, Return Unit annotations from the abstract interface declaration for method_name., Convert annotated float parameters to astropy Quantities before the method…, with_units(), Focuser, IFocus (+16 more)

### Community 18 - "DummyRoof"
Cohesion: 0.14
Nodes (17): DummyRoof, Any, Get the percentage the roof is open., Stop the motion. Args: device: Name of device to stop, or None for all. Raises:…, A dummy camera for testing., Creates a new dummy root., Open the roof. Raises: InitError: If the roof could not be initialized (e.g.…, Close the roof. Raises: ParkError: If the roof could not be parked (e.g.… (+9 more)

### Community 19 - "mixins/test_fitsheader.py"
Cohesion: 0.10
Nodes (55): FitsModule, make_image(), make_module(), make_observer(), asyncio, date, EarthLocation, A peer raising a non-RemoteError -- e.g. a malformed IFitsHeaderBefore/After… (+47 more)

### Community 20 - "Event"
Cohesion: 0.05
Nodes (52): Event, Base class for all events., DataType, TypedDict, DataType, TypedDict, DataType, TypedDict (+44 more)

### Community 21 - "BaseGuiding"
Cohesion: 0.07
Nodes (21): GuidingState, AutoGuiding, Any, An auto-guiding system., Initializes a new auto guiding system. Args: exposure_time: Initial exposure…, Set the exposure time in seconds. Args: exposure_time: Exposure time in…, Starts/resets auto-guiding., BaseGuiding (+13 more)

### Community 22 - "AstrometryDotNet"
Cohesion: 0.04
Nodes (38): Astrometry processors doc, AstrometryDotNet (astrometry processor), Astrometry, Finds astrometric solution to a given image. Args: image: Image to analyse.…, Base class for astrometry processors, AstrometryDotNet, Any, Init new astronomy.net processor. Args: url: URL to service. source_count:… (+30 more)

### Community 23 - "test_flatfielder.py"
Cohesion: 0.08
Nodes (60): make_flatfielder(), make_observer(), make_twilight_observer(), asyncio, parametrize, Regression test for #481: median == bias_level used to raise ZeroDivisionError., Observer stub returning a constant solar altitude for every sun_altaz() call., Observer stub distinguishing the first (now) vs second (+10min) sun_altaz()… (+52 more)

### Community 24 - "LocalComm"
Cohesion: 0.07
Nodes (23): LocalComm, Any, Store capabilities locally., Return this client's own published capabilities., Fetch capabilities from a remote module., Store presence state and dispatch to all subscribers., Return presence state of a connected module., Announce this module to already-connected peers, mirroring XmppComm's presence-… (+15 more)

### Community 25 - "tests/test_events.py"
Cohesion: 0.04
Nodes (63): Comm API doc (pyobs.comm), Events API doc (pyobs.events), BadWeatherEvent, Event to be sent on bad weather., Create Event from a dictionary. Args: obj_dict: JSON string for event. Returns:…, FilterChangedEvent, Event to be sent when a filter has been changed., FocusFoundEvent (+55 more)

### Community 26 - "test_lco_http.py"
Cohesion: 0.09
Nodes (43): Camera, CameraType, ConfigurationType, Enclosure, Instrument, InstrumentType, Mode, ModeType (+35 more)

### Community 27 - "DummySolarTelescope"
Cohesion: 0.13
Nodes (19): DummySolarTelescope, Any, Moves to and continuously tracks a Heliocentric Polar (mu, psi) coordinate., Moves to and continuously tracks a Heliographic Stonyhurst (lon, lat)…, Moves to and continuously tracks a Helioprojective (theta_x, theta_y)…, Background task: while a solar-relative target is active, keeps the simulated…, A dummy telescope dedicated to solar pointing (Heliocentric Polar/Heliographic…, Converts Heliocentric Polar (mu, psi) to (ra, dec) in degrees, ICRS. Mirrors… (+11 more)

### Community 28 - "FitsHeaderEntry"
Cohesion: 0.02
Nodes (96): IDome, The module controls a dome, i.e. a :class:`~pyobs.interfaces.IRoof` with a…, Any, Returns FITS header for the current status of this module. Args: namespaces: If…, FitsHeaderEntry, IFitsHeaderBefore, Any, The module provides some additional header entries for FITS headers before some… (+88 more)

### Community 29 - "WindowingWidget"
Cohesion: 0.05
Nodes (14): BinningWidget, DataDisplayWidget, PrimaryHDU, Slot, Select path for auto-saving., ExposeWidget, Slot, ExposureTimeWidget (+6 more)

### Community 30 - "Interfaces (pyobs.interfaces) API doc"
Cohesion: 0.04
Nodes (53): Interfaces (pyobs.interfaces) API doc, IAbortable, IAcquisition, IAutoFocus, IAutoGuiding, IAutonomous, IBinning, ICalibrate (+45 more)

### Community 31 - "test_control.py"
Cohesion: 0.13
Nodes (43): ParallelRunner, Script for running other scripts in parallel., Script for running a sequence of other scripts., SequentialRunner, AlwaysRunScript, NeverRunScript, Any, asyncio (+35 more)

### Community 32 - "test_weatheraware.py"
Cohesion: 0.15
Nodes (19): pyobs.modules.roof (doc), BaseDome, BaseRoof, DummyRoof, WeatherState, ParkError, _FakeProxyContext, asyncio (+11 more)

### Community 33 - "BaseCamera"
Cohesion: 0.08
Nodes (23): Any, Header, IDataSequence, IExposure, IExposureTime, IImageType, ImageFitsHeaderMixin, ImageType (+15 more)

### Community 34 - "SolarElevationConstraint"
Cohesion: 0.15
Nodes (29): AtNightConstraint, Solar elevation constraint., SolarElevationConstraint, constraint(), data(), observer(), asyncio, fixture (+21 more)

### Community 35 - ".set_exposure_time"
Cohesion: 0.50
Nodes (3): Any, SECONDS, Set the exposure time in seconds. Args: exposure_time: Exposure time in…

### Community 36 - "Future"
Cohesion: 0.08
Nodes (36): Wait until all devices are in one of the given motion states. Args: abort:…, Run script. Raises: InterruptedError: If interrupted, acquire_lock(), event_wait(), Future, Any, Lock, Sets a new timeout for the method call. Cancels any existing timeout handle and… (+28 more)

### Community 37 - "SiderealTarget"
Cohesion: 0.07
Nodes (29): HeliocentricPolarTarget, SkyCoord, Target, HelioprojectiveTarget, SkyCoord, Target, model_validator, Self (+21 more)

### Community 38 - "CoolingState"
Cohesion: 0.09
Nodes (32): _dataclass_to_xml(), _event_schema_to_xml(), _interface_schema_to_xml(), _parse_scalar(), Any, Element, Shared XML serializer for pyobs 2.0 (urn:pyobs:rpc:1). Both the state pub/sub…, Serialize a dataclass to ``<{namespace}state>`` with plain field children. Each… (+24 more)

### Community 39 - "IPointingAltAz.py"
Cohesion: 0.05
Nodes (47): AltAzState, IPointingAltAz, Any, DEGREES, The module can move to Alt/Az coordinates, usually combined with…, Moves to given coordinates. Args: alt: Alt in deg to move to. az: Az in deg to…, IPointingRaDec, The module can move to RA/Dec coordinates, usually combined with… (+39 more)

### Community 40 - "_DotNetRequest"
Cohesion: 0.22
Nodes (4): _DotNetRequest, Any, asyncio, test_generate_request_error_msg()

### Community 41 - "SkyOffsets"
Cohesion: 0.15
Nodes (16): BaseCoordinateFrame, Angle, SkyCoord, Returns separatation between both coordinates, either in their own or a given…, Calculates spherical offset from first coordinate to second. Args: frame:…, Args: frame: Coordinate frame to use, or None to use coordinates' own frames.…, SkyOffsets, Tests that SkyCoord.transform_to is correctly used (+8 more)

### Community 42 - "test_xmpp_event_subscriptions.py"
Cohesion: 0.11
Nodes (24): _log_event(), _named_module(), Integration tests for explicit pubsub event subscriptions. Covers…, Registering a handler after a peer is already online must still result in a…, After the last handler for an event class is removed, no further events must…, Registering a handler for a local event (e.g.…, Local events must be unaffected by moving regular events onto the shared pubsub…, After a subscriber restarts (new session, same bare JID), it must resume… (+16 more)

### Community 43 - "Proxy"
Cohesion: 0.08
Nodes (20): Comm responsibility: Method calls (via Proxy), Proxy, Any, Signature, Execute a method on the remote client. Args: method: Name of method to call.…, Create local methods for the remote client., Function wrapper for remote calls. Args: method: Name of method to wrap.…, Called by Comm whenever a new state arrives. Not intended to be called directly… (+12 more)

### Community 44 - "mixins/fitsheader.py"
Cohesion: 0.08
Nodes (16): IWeather, ImageFitsHeaderMixin, Helper methods for all modules that need FITS headers for an image., FitsNamespaceMixin, Any, Mixin for IFitsHeaderProvider modules that filters FITS headers by namespace., Filter FITS header keywords by given namespaces. If no namespaces are given,…, Add FITS header keywords from namespace to list of valid keywords Args: name:… (+8 more)

### Community 45 - "robotic/test_scheduler.py"
Cohesion: 0.08
Nodes (53): Any, Event to be sent when a task has finished., Initializes a new task finished event. Args: name: Name of task that just…, TaskFinishedEvent, _class_accepts_param(), Whether the class configured in `config` (a dict with a "class" key, or an…, Scheduler, DummyTask (+45 more)

### Community 46 - "StandAlone"
Cohesion: 0.09
Nodes (40): pyobs.modules.test (doc), StandAlone, Quickstart (doc), pyobs-core (pip package), Test modules. TODO: write doc, Any, Example module that only logs the given message forever in the given interval., Creates a new StandAlone object. Args: message: Message to log in the given… (+32 more)

### Community 47 - "HttpFileCache"
Cohesion: 0.17
Nodes (9): HttpFileCache, Response, Handles OPTIONS access to /{filename} for CORS preflight requests. Args:…, Handles GET access to /{filename} and returns image. Args: request: Request to…, Handles PUSH access to /, stores image and returns filename. Args: request:…, A file cache based on a HTTP server., Whether the server is started., Raises HTTPUnauthorized if a token is configured and the request doesn't carry… (+1 more)

### Community 48 - "_PhotometryCalculator"
Cohesion: 0.08
Nodes (24): AperturePhotometry, Any, Base class for aperture photometry processors -- not meant to be used directly,…, Do aperture photometry on given image. Args: image: Image to do aperture…, _PhotometryCalculator, Table, Abstract class for photometry calculators., Perform photometry using SEP. (+16 more)

### Community 49 - "test_stellarexptime.py"
Cohesion: 0.11
Nodes (34): ndarray, Find the brightest star near the image centre by fitting a 2D Gaussian. Args:…, Determines exposure time by finding a star near the image centre and adjusting…, Determine the optimal exposure time. Returns: Optimal exposure time in seconds., StellarExposureTimeProvider, attach_proxies(), make_camera_mocks(), make_image() (+26 more)

### Community 50 - "ExpTimeEstimator"
Cohesion: 0.16
Nodes (13): Additional Modules index (docs), Image processors index (docs), Calibration processors doc, Exposure Time estimators doc, ExpTimeEstimator (exptime processor base), StarExpTimeEstimator (exptime processor), ExpTimeEstimator, Estimate exposure time. (+5 more)

### Community 51 - "test_dynamictarget.py"
Cohesion: 0.15
Nodes (27): Constraint, fixture, SkyCoord, data(), make_task(), mock_vfs(), observer(), DataProvider (+19 more)

### Community 52 - "test_xmpp_presence.py"
Cohesion: 0.08
Nodes (39): make_module(), Minimal module stub satisfying what XmppComm needs on connect. IModule must be…, get_capabilities_from_disco(), Integration tests for Phase 2.5 Presence and Discovery. Requires a live…, LOCAL state must arrive as away presence., Module.set_state() must automatically push presence — no explicit call., subscribe_presence fires immediately with current state and again on each…, disco#info must contain IModule.Capabilities with version and label. (+31 more)

### Community 53 - "test_shellcommand.py"
Cohesion: 0.10
Nodes (29): ParserState, Any, Enum, ShellCommand, ShellCommandResponse, asyncio, test_command_number_increments(), test_execute_invalid_param() (+21 more)

### Community 54 - "Calibration"
Cohesion: 0.09
Nodes (20): Calibration, Any, Init a new image calibration pipeline step. Args: archive: Archive to fetch…, Calibrate an image. Args: image: Image to calibrate. Returns: Calibrated image., Calibrate an image using master bias, dark, and flat frames fetched from an…, Find master calibration frame for given parameters using a cache. Args:…, _CCDDataCalibrator, CCDData (+12 more)

### Community 55 - "test_csvpicker_scheduler.py"
Cohesion: 0.25
Nodes (20): make_dynamic_task(), make_vfs(), asyncio, integration, Path, CsvPicker filters out targets that fail the airmass constraint., OnDemandScheduler resolves DynamicTarget via CsvPicker to a SiderealTarget., Scheduler produces no observations when all CSV targets are invisible. (+12 more)

### Community 56 - "Publisher"
Cohesion: 0.15
Nodes (12): LogPublisher, Any, Initialize new log publisher. Args: level: Level to log on., Publish the given results. Args: **kwargs: Results to publish., MultiPublisher, Any, Forwards a message to multiple publishers., Initialize new multi publisher. Args: publishers: Publishers to forward… (+4 more)

### Community 57 - ".__call__"
Cohesion: 0.21
Nodes (9): ICamera, IFilters, ITelescope, Calls next step in state machine. Args: telescope: Telescope to use. camera:…, Initialize whole system., Take bias image to determine bias level. Returns: Median bias level., Take flat-fields but don't store them., Set camera window. Args: testing: Whether we're in testing mode or not. (+1 more)

### Community 58 - "test_autoguiding.py"
Cohesion: 0.20
Nodes (32): make_guiding(), make_image(), asyncio, _state_for(), test_auto_guiding_sleeps_when_disabled(), test_auto_guiding_takes_and_processes_image_when_enabled(), test_get_fits_header_after_includes_statistics(), test_get_fits_header_before_reports_closed_loop() (+24 more)

### Community 59 - "ImageType"
Cohesion: 0.12
Nodes (14): _CalibrationCache, Broadcast image. Args: image: Image to broadcast. Returns: Original image., Any, Set the image type. Args: image_type: New image type., Any, ImageType, Enumerator specifying the image type. Attributes: BIAS: Bias/zero exposure.…, Find master calibration frame for given parameters using a cache. Args:… (+6 more)

### Community 60 - "FilenameFormatter"
Cohesion: 0.05
Nodes (50): Format filename with given formatter., Any, Save an image to the virtual file system and optionally broadcast a…, Init an image processor that broadcasts an image Args: filename: Filename to…, Initialize processor., Save, CreateFilename, Any (+42 more)

### Community 61 - "test_basevideo.py"
Cohesion: 0.13
Nodes (44): make_basevideo(), make_request(), asyncio, BaseVideo must forward fits_header_timeout to ImageFitsHeaderMixin, not swallow…, _route_paths(), test_activate_camera_from_inactive_calls_hook(), test_activate_camera_when_already_active_skips_hook(), test_active_update_deactivates_after_sleep_timeout() (+36 more)

### Community 62 - "test_yaml_archives.py"
Cohesion: 0.24
Nodes (28): make_obs(), make_obs_archive(), make_task(), make_task_archive(), asyncio, Verify observations are actually written to disk in valid YAML., test_add_and_load_observations(), test_add_empty_list_is_noop() (+20 more)

### Community 63 - "Portal"
Cohesion: 0.05
Nodes (47): InstrumentLocation, EarthLocation, Observer, Location of the observer, derived from :attr:`observer` (there is no separately…, .. note:: Objects must always be opened and closed using…, Any, Initialize a new scheduler. Args: twilight: astronomical or nautical, ConfigDB (+39 more)

### Community 64 - "FlatFielder"
Cohesion: 0.09
Nodes (16): Enum, Object, FlatFielder, Any, Returns True, if functions are based on filters., Do a quick initial check. Returns: False, if flat-field time for this filter is…, Wait for flat-field time., Evaluate function for given filter at given time. Args: time: Time to evaluate… (+8 more)

### Community 65 - "IExposure"
Cohesion: 0.06
Nodes (34): Comm._get_client, ADR-0001: Check Interface.state by own declaration, not inheritance, Composite interfaces inheriting stateful bases (ICamera, IDome, ITelescope, ...), Interface.capabilities (ClassVar), Interface.has_own_state(), Interface.state (ClassVar), XmppComm disco#info feature registration, ADR-0006: Proxy.wait_for_state() returns None on timeout (+26 more)

### Community 66 - "Telegram"
Cohesion: 0.13
Nodes (19): CallbackContext, Any, Save storage file. Args: context: Telegram context., Is user authorized? Args: context: Telegram context. user_id: ID of user.…, Store new user in auth database. Args: context: Telegram context. user_id: ID…, Handle /start command. Args: update: Message to process. context: Telegram…, Handle /exec command. Args: update: Message to process. context: Telegram…, Handle click on buttons. Args: update: Message to process. context: Telegram… (+11 more)

### Community 67 - "test_astroplanscheduler.py"
Cohesion: 0.07
Nodes (51): AstroplanScheduler, Any, ObservingBlock, Actually do the scheduling, usually run in a separate process., Scheduler based on astroplan., Initialize a new scheduler. Args: twilight: astronomical or nautical, DynamicTarget, Picker (+43 more)

### Community 68 - "TimeDelta"
Cohesion: 0.07
Nodes (77): ConstantMerit, Merit function that returns a constant value., model_validator, Self, Merit function that uses time windows., TimeWindow, TimeWindowMerit, OnDemandScheduler (+69 more)

### Community 69 - "Offsets"
Cohesion: 0.03
Nodes (64): AltAzOffsets, GenericOffset, OnSkyDistance, Angle, PixelOffsets, RaDecOffsets, AstrometryOffsets, CorrelationMaxCloseToBorderError (+56 more)

### Community 70 - ".now"
Cohesion: 0.07
Nodes (33): Compute and persist the next per-night observation number. Returns: Compound…, Observer, ObservationArchiveEvolution, date, Observer, Populates the task cache and the one real night (anchored to `start`) up front.…, Freezes observation cache. After this: a task-id miss raises RuntimeError; a…, Returns list of observations for the given task. Args: date: Date of night to… (+25 more)

### Community 71 - "PyObsError"
Cohesion: 0.07
Nodes (31): ADR-0003: Restrict Proxy access to async with, has_proxy() / safe_proxy, Proxy, _ProxyContext.__await__ (removed), specs/design/pyobs_2_0_wire_protocol.md, acl: config block (allow/deny), ADR-0004: Enforce access control on the callee, not the caller, Module.execute() (+23 more)

### Community 72 - "test_proxy.py"
Cohesion: 0.12
Nodes (33): _cooling_state(), make_proxy(), asyncio, Methods from both interfaces are callable., A CoolingState timestamped `age_seconds` in the past., Callers that don't pass max_age see no behavior change, however old the cached…, A future interface whose State dataclass has no `time` field fails loudly at…, Create a Proxy with a mock comm. (+25 more)

### Community 73 - "XEP_0009"
Cohesion: 0.12
Nodes (7): Expose method to public., Expose method to public., Expose method to public., Small fix for the original XEP_0009 plugin., Route RPC-level errors (e.g. forbidden, item-not-found) through the same…, XEP_0009, XEP_0009_original

### Community 74 - "LogEvent"
Cohesion: 0.13
Nodes (9): LogEvent, Any, Event for log entries., Enum, TelegramUserState, main(), Trigger one controlled LogEvent publish on production while debug logging is…, test_log_event_properties() (+1 more)

### Community 75 - "PyobsDaemon"
Cohesion: 0.14
Nodes (10): Any, PyobsDaemon, Return the bare module name from a config or PID file path., Strip a leading underscore, which marks a module as disabled. PID and log files…, Return sorted module names from *.yaml files, excluding *.shared.yaml., Read and return the PID from the module's PID file, or None., Return the live PID for a module, or None. Cleans up stale PID files., Return uptime (seconds) and rss_mb for a running PID. No CPU -- that needs a… (+2 more)

### Community 76 - "test_acquisition.py"
Cohesion: 0.13
Nodes (39): ExpTime, EarthLocation, Take the pixel offsets stored in the meta data of the image and apply them to…, OffsetResult, EarthLocation, SkyCoord, Take the pixel offsets stored in the meta data of the image and apply them to…, Return RA/Dec of central pixel and of central pixel plus offsets. Args: image:… (+31 more)

### Community 77 - "test_config.py"
Cohesion: 0.07
Nodes (43): include_parts(), pre_process_yaml(), Any, Replaces blocks of the form {include <source.yaml> <key>} in the loaded config…, Finds anchors ('&') in the included file. Args: filename: name of the file with…, Replaces aliases ('<<: *...') in the main file by the anchor in the included…, Include nested contents from another YAML file. Args: include: dictionary based…, Finds keys that hold an anchor ('&') at the top level (no leading whitespace)… (+35 more)

### Community 78 - "TaskData"
Cohesion: 0.05
Nodes (17): Whether this config can currently run. Returns: True if script can run now., Run script. Raises: InterruptedError: If interrupted, Estimate duration of the dark/bias series., Whether this config can currently run. Returns: True if script can run now., Run script. Raises: InterruptedError: If interrupted, Estimate duration of slewing to the flat-field pointing., Estimate duration of the sky flats. The actual schedule depends on sky…, Whether this config can currently run. Returns: True if script can run now. (+9 more)

### Community 79 - "xmppcomm.py"
Cohesion: 0.07
Nodes (25): Any, Disconnect only, instead of slixmpp's default reconnect-in-place. xep_0199's…, Called when the server sends a <stream:error/>, e.g. when this connection gets…, Whether this client was (or is being) kicked because another session connected…, Human-readable reason text sent alongside the conflict stream error, if any., Wait for client to connect. Returns: Success or not., XMPP client for pyobs., Session start event. Args: event: The event sent at session start. (+17 more)

### Community 80 - "Weather"
Cohesion: 0.11
Nodes (27): Any, Builds the current per-sensor readings from the last raw status, for state…, Returns FITS header for the current status of this module. Args: namespaces: If…, Connection to pyobs-weather., Initialize a new pyobs-weather connector. Args: url: URL to weather station…, Weather, asyncio, test_active_flag_defaults_true_and_tracks_stop() (+19 more)

### Community 81 - "ImagingScript"
Cohesion: 0.15
Nodes (9): ImagingScript, Any, Target, Whether this config can currently run. Returns: True, if the script can run now, Run script. Raises: InterruptedError: If interrupted, Returns FITS header for the current status of this module. Args: namespaces: If…, Estimate the duration of this script in seconds., Return the exposure time, computing it dynamically if needed. (+1 more)

### Community 82 - "test_transit_mastermind.py"
Cohesion: 0.06
Nodes (53): EarthLocation, model_validator, Self, SkyCoord, Merit function for observing transits., Returns the time of the next mid-transit., Returns the time until which observations should run: mid-transit + duration/2…, TransitMerit (+45 more)

### Community 83 - "DummyCamera"
Cohesion: 0.12
Nodes (9): DummyCamera, Any, Header, NDArray, Table, Update cached telescope position from IPointingRaDec state., Returns current solar altitude in degrees, or -18 if no observer., A dummy camera for testing. (+1 more)

### Community 84 - "PipelineMixin"
Cohesion: 0.06
Nodes (40): Handle an ImageError raised by this step, when on_error == "error". Override…, PipelineMixin, Any, Mixin for a module that needs to implement an image pipeline., Initializes the mixin. Args: steps: Pipeline steps to run on images. archive:…, Whether the given class declares an `archive` parameter anywhere in its…, Resets all previous state of the involved image processors., Run the pipeline on the given image. Each step is run, and an ImageError it… (+32 more)

### Community 85 - "Ring"
Cohesion: 0.14
Nodes (9): integer, Any, floating, NDArray, Estimate pixel guiding offsets from asymmetry of spilled light around a fiber…, Init an image processor that adds the calculated offset. Args: fibers:…, Processes an image and sets x/y pixel offset to reference in offset attribute.…, Ring (+1 more)

### Community 86 - "loaded_pyobs_packages"
Cohesion: 0.40
Nodes (9): loaded_pyobs_packages(), Return the version of every loaded ``pyobs``-prefixed distribution. Builds the…, _fake_modules(), test_defaults_to_sys_modules(), test_excludes_non_pyobs_distributions(), test_excludes_not_loaded_top_level_names(), test_returns_loaded_pyobs_distributions(), test_skips_package_not_found() (+1 more)

### Community 87 - "make_obs_archive"
Cohesion: 0.18
Nodes (26): ObservationList, make_obs(), make_obs_archive(), make_task(), Observation, ObservationState, Task, Time (+18 more)

### Community 88 - "test_exception_logging.py"
Cohesion: 0.27
Nodes (20): Callback for flat-field class to call with statistics., FocusError, _AbortableModule, asyncio, Minimal test module whose abort() raises whatever exception it's given. Starts…, test_call_id_is_attached_to_the_exception_and_included_in_the_log_line(), test_call_id_omitted_from_log_line_when_not_given(), test_disable_exception_logging_covers_subclasses() (+12 more)

### Community 89 - "test_config_schema.py"
Cohesion: 0.20
Nodes (22): ConfigFieldSchema, ConfigSchema, dataclass_to_schema(), _field_schema(), Any, _pydantic_field_schema(), pydantic_to_schema(), Recursively derive a ConfigSchema from a dataclass type. Handles: plain scalars… (+14 more)

### Community 90 - "Application"
Cohesion: 0.13
Nodes (24): Application, React to signals and quit the module., Actually run the application., Class for initializing and shutting down a pyobs process., make_bare_application(), Any, asyncio, Tests for Application's module_factory path (see specs/plans/gui-interactive-… (+16 more)

### Community 91 - "DummyComm"
Cohesion: 0.09
Nodes (20): Creates a comm module., DummyComm, Any, A dummy implementation of the Comm interface., Creates a new dummy comm. Args: name: Name to report for this comm. Defaults to…, Always return zero clients., No interfaces implemented., Interfaces are never supported. (+12 more)

### Community 92 - "get_class_from_string"
Cohesion: 0.12
Nodes (23): Any, get_class_from_string(), Get class from a given string. Args: class_name: Name of class as string.…, _build_params_model(), CallModuleScript, _get_valid_param_names(), model_validator, Script for calling a method on a module. (+15 more)

### Community 93 - "ProjectedOffsets"
Cohesion: 0.14
Nodes (20): ProjectedOffsets, Any, floating, NDArray, Processes an image and sets x/y pixel offset to reference in offset attribute.…, Project image along x and y axes and return results. Args: image: Image to…, Compute pixel offsets for guiding by correlating 1D projections of the current…, Initializes a new auto guiding system. (+12 more)

### Community 94 - "test_pyobs_archive.py"
Cohesion: 0.19
Nodes (25): PyobsArchiveFrameInfo, Frame info for pyobs archive., make_archive(), make_frame_dict(), MockResponse, Any, asyncio, test_download_frames_returns_images() (+17 more)

### Community 95 - "HttpFile"
Cohesion: 0.10
Nodes (18): ArchiveFile, Wraps a file in an archive. To be used in combination with pyobs-archive., Creates a new archive file. Args: name: Name of file. mode: Open mode (r/w).…, If in write mode, actually send the file to the archive., HttpFile, Any, Read number of bytes from stream. Args: n: Number of bytes to read. Read until…, Write data into the stream. Args: s: Bytes of data to write. (+10 more)

### Community 96 - "FrameInfo"
Cohesion: 0.11
Nodes (12): FrameInfo, Base class for frame infos., Any, TypedDict, PyobsArchive, PyobsArchiveFrameInfoDict, Connector class to running pyobs-archive instance., test_build_query_empty_when_nothing_given() (+4 more)

### Community 97 - "application.py"
Cohesion: 0.09
Nodes (20): _disable_iers_auto_download(), GuiApplication, InfluxLogConfig, Any, TypedDict, Initializes a pyobs application. Exactly one of `config`/`module_factory` must…, Derived Application class that uses a Qt GUI. Allows for graceful shutdown in…, Create a new GUI application. (+12 more)

### Community 98 - "FocusSeries"
Cohesion: 0.06
Nodes (38): AutoFocusPoint, fit_hyperbola(), Fit a hyperbola Args: x_arr: X data y_arr: Y data y_err: Y errors Returns:…, FocusSeries, Analyse given image. Args: image: Image to analyse focus_value: Value to fit…, Returns a list of data points., Fit focus from analysed images Returns: Tuple of new focus and its error, Base class for focus series helper classes. (+30 more)

### Community 99 - "_DaoBackgroundRemover"
Cohesion: 0.06
Nodes (33): Source Detection processors doc, DaophotSourceDetection (detection processor), SepSourceDetection (detection processor), _DaoBackgroundRemover, Any, floating, NDArray, DaophotSourceDetection (+25 more)

### Community 100 - "make_proxy_cm"
Cohesion: 0.21
Nodes (27): make_proxy_cm(), Wrap value in a MagicMock standing in for the async context manager returned by…, make_flatfield(), asyncio, Find the state object set_state() was called with for the given interface., _ready_telescope(), _state_for(), test_abort_sets_event() (+19 more)

### Community 101 - "TaskStartedEvent"
Cohesion: 0.16
Nodes (9): Any, Event to be sent when a task has started., Initializes a new task started event. Args: name: Name of task that just…, TaskStartedEvent, test_task_started_invalid_name(), test_task_started_missing_id(), test_task_started_no_eta(), test_task_started_properties() (+1 more)

### Community 102 - ".get_object"
Cohesion: 0.05
Nodes (44): ObjectClass, PydanticModel, BackgroundTask, Any, create_object(), get_object(), get_safe_object(), Any (+36 more)

### Community 103 - "test_lcoscript.py"
Cohesion: 0.17
Nodes (18): FakeScript, make_lco_script(), make_request(), Any, asyncio, Minimal script used to verify LcoScript's dispatch., can_run() resolves and delegates to the script named in…, run() delegates to the named script and copies its exptime_done back. (+10 more)

### Community 104 - "test_coordinates.py"
Cohesion: 0.15
Nodes (25): offset_altaz_to_radec(), offset_radec_to_altaz(), EarthLocation, SkyCoord, make_altaz(), make_radec(), SkyCoord, Zero offset returns (0, 0). (+17 more)

### Community 105 - "get_registered_interface"
Cohesion: 0.12
Nodes (20): get_registered_interface(), Look up a registered interface class by name, or None if unknown., Tests for the import-time interface registry in pyobs/interfaces/interface.py.…, Re-importing the same interface module twice resolves to the same class object…, Two genuinely different classes claiming the same name must raise TypeError…, Mutating the returned dict must not affect the live registry., An interface composing other interfaces (like ICamera(IData, IExposure))…, A class mixing in a non-Interface base (like BaseCamera(Module, ICamera, ...))… (+12 more)

### Community 106 - "DummyMode"
Cohesion: 0.04
Nodes (31): ICamera, The module controls a camera., IMode, ModeCapabilities, ModeState, Any, The module can change modes in a device., Set the current mode. Args: mode: Name of mode to set. group: Name of the group… (+23 more)

### Community 107 - "LocalArchive"
Cohesion: 0.32
Nodes (26): LocalArchive, Connector class to a local image archive., make_frame_headers(), asyncio, Path, test_download_frames_loads_real_files(), test_download_frames_skips_frames_without_filename(), test_download_headers_returns_header_dicts() (+18 more)

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

### Community 112 - "ImageWatcher"
Cohesion: 0.14
Nodes (9): Module, CurrentFile, ImageWatcher, Add a file to the file queue. Args: filename (str): Local filename of new file., Can be overwritten by derived classes to do extra processing on files. All…, Can be overwritten by derived classes to do clean up after successful copying.…, Watch for new files and write them to all given destinations. Watches a path…, Create a new image watcher. Args: watchpath: Path to watch. destinations:… (+1 more)

### Community 113 - "Comm"
Cohesion: 0.04
Nodes (36): Comm responsibility: Discovery (clients_with_interface), Comm responsibility: Events (broadcast typed events), Comm, Any, ProxyType, setter, Returns object directly if it is of given type. Otherwise get proxy of client…, Backend hook, called when a proxy exists but doesn't implement obj_type.… (+28 more)

### Community 114 - "CommLoggingHandler"
Cohesion: 0.12
Nodes (20): Send an event to all connected modules. Args: event: Event to send.…, CommLoggingHandler, Any, A logging handler that sends all messages through a Comm module., Create a new logging handler. Args: comm: Comm module to use., Send a new log entry to the comm module. Args: rec: Log record to send., comm(), handler() (+12 more)

### Community 115 - "test_dummyradectelescope.py"
Cohesion: 0.24
Nodes (21): TrackingRateCapabilities, make_dummyradectelescope(), asyncio, test_move_altaz_clears_tracked_body(), test_move_altaz_resets_tracking_mode_to_off(), test_move_radec_clears_tracked_body(), test_move_radec_resets_tracking_mode_to_sidereal(), test_move_task_applies_tracking_rate_to_position() (+13 more)

### Community 116 - "SkyFlatsBasePointing"
Cohesion: 0.14
Nodes (12): Move telescope. Args: telescope: Telescope to use., Base class for flat pointings., SkyFlatsBasePointing, model_validator, Self, Static flat pointing., Move telescope. Args: telescope: Telescope to use., SkyFlatsStaticPointing (+4 more)

### Community 117 - "modules/image/__init__.py"
Cohesion: 0.18
Nodes (6): Modules for image operations. TODO: write doc, Any, Measures seeing on reduced images with a catalog., Creates a new seeing estimator. Args: sources: List of sources (e.g. cameras)…, Puts a new images in the DB with the given ID. Args: event: New image event…, Seeing

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

### Community 123 - "._record_exception"
Cohesion: 0.18
Nodes (7): Exception, Records exception for severity tracking (see _register_exception) and fires any…, Whether exception should count as an instance of exc_type for severity-handler…, Checks all handlers against all recorded exceptions and returns those whose…, ExceptionHandler, LoggedException, NamedTuple

### Community 124 - "FocusModel"
Cohesion: 0.14
Nodes (20): FocusModel, Returns the optimal focus. Args: filter_name: If given, use this filter name…, Receive FocusFoundEvent. Args: event: The event itself sender: The name of the…, Calculate new focus model from saved entries., A focus model that is automatically applied to an IFocuser. If, e.g., the model…, _FakeProxyContext, asyncio, weather is a string name that no proxy exists for yet (e.g. the weather module… (+12 more)

### Community 125 - "SFTPFile"
Cohesion: 0.22
Nodes (5): Any, VFS wrapper for a file that can be accessed over a SFTP connection., Open/create a file over a SSH connection. Args: name: Name of file. mode: Open…, Returns content of given path. Args: path: Path to list. kwargs: Parameters for…, SFTPFile

### Community 126 - "ImageSourceFilter"
Cohesion: 0.12
Nodes (17): ImageSourceFilter, Any, floating, NDArray, Table, Filters the source table after pysep detection has run Args:…, Filter a source catalog by border distance, quality metrics, and brightness,…, Convert from FITS to numpy conventions for pixel coordinates. (+9 more)

### Community 127 - "test_darkbias.py"
Cohesion: 0.33
Nodes (17): DarkBiasScript, Script for running darks or biases., make_camera(), make_script(), asyncio, Create a mock camera supporting all or some interfaces., Wire up comm mocks for a DarkBiasScript.run call. safe_proxy is used for…, setup_run_comm() (+9 more)

### Community 128 - "WeatherSensors"
Cohesion: 0.16
Nodes (13): IWeather, Any, The module acts as a weather station., Return value for given sensor. Args: station: Name of weather station to get…, WeatherSensorReading, Weather modules. TODO: write doc, Return value for given sensor. Args: station: Name of weather station to get…, Set a simulated sensor's value, for use in tests and simulations. Args: sensor:… (+5 more)

### Community 129 - "TempFile"
Cohesion: 0.24
Nodes (6): Any, Open/create a temp file. Args: name: Name of file. mode: Open mode. prefix:…, TempFile, asyncio, test_name(), test_write_file()

### Community 130 - "Plan: pyobs-pipeline"
Cohesion: 0.08
Nodes (24): Celery task, Consequences, Django models, Implementation checklist, Log viewing, Open questions, Pages, Pipeline builder (+16 more)

### Community 131 - "Test Localcomm (local)"
Cohesion: 0.18
Nodes (22): make_comm(), asyncio, fixture, Sender also receives its own events., Reset LocalNetwork singleton between tests., #677: a late-joining module must announce itself via ModuleOpenedEvent once…, get_interfaces returns [] when the remote client has no module., reset_network() (+14 more)

### Community 132 - "comm.py"
Cohesion: 0.27
Nodes (4): The Comm object is responsible for all communication between modules (see…, _ProxyContext, ProxyType, Returned by Comm.proxy() / Object.proxy() / Comm.safe_proxy(). Must be used as:…

### Community 133 - ".__init__"
Cohesion: 0.06
Nodes (20): Any, JSON representation of event., String representation of event., Generic from_dict method for derived classes that don't need their own., Any, Any, Any, Initializes a new good weather event. Args: eta: Predicted ETA for when the… (+12 more)

### Community 134 - "flatfield/test_scheduler.py"
Cohesion: 0.47
Nodes (9): FlatFieldScheduler, Run the flat-field scheduler., make_scheduler_module(), asyncio, setup_flatfield_proxy(), test_abort_sets_event(), test_run_aborts_current_flat_field_when_requested(), test_run_raises_when_already_running() (+1 more)

### Community 135 - "test_dummymode.py"
Cohesion: 0.32
Nodes (13): _event_of_type(), make_dummymode(), asyncio, Find the most recent state object set_state() was called with for the given…, Find the send_event() call with an event of the given type., _state_for(), test_init_default_modes(), test_init_park_stop_motion_are_noops() (+5 more)

### Community 136 - "MockWeather"
Cohesion: 0.15
Nodes (20): MockWeather, Any, Returns FITS header for the current status of this module. Args: namespaces: If…, A mock weather station for testing and simulations., Creates a new mock weather station. Args: good: Initial weather-good state.…, Set the simulated weather-good state, for use in tests and simulations. Fires a…, asyncio, test_active_flag_defaults_true_and_tracks_stop() (+12 more)

### Community 137 - "SkyflatPriorities"
Cohesion: 0.30
Nodes (6): ArchiveSkyflatPriorities, Calculate flat priorities from an archive., Base class for sky flat priorities., SkyflatPriorities, ConstSkyflatPriorities, Constant flat priorities.

### Community 138 - "Grid"
Cohesion: 0.10
Nodes (17): GridFilter, Any, Initialize the conversion filter. Args: grid: Upstream grid or filter that…, Abstract base class for grid filters that wrap another GridNode. A GridFilter…, Initialize the frame conversion filter. Args: grid: Upstream grid or filter…, Initialize the randomizer. Args: grid: Upstream grid or filter. iterations:…, Initialize a filter with an underlying grid. Args: grid: The upstream GridNode…, Initialize the moon avoider. Args: grid: Upstream grid or filter.… (+9 more)

### Community 139 - "test_kiosk.py"
Cohesion: 0.24
Nodes (21): _cancel_after(), _make_image(), make_kiosk(), asyncio, Side effect that raises CancelledError starting from the n-th call., test_camera_thread_captures_and_adjusts_exposure_time(), test_camera_thread_clips_exposure_time_to_minimum(), test_camera_thread_continues_on_file_not_found() (+13 more)

### Community 140 - "pyobs.py"
Cohesion: 0.13
Nodes (11): main(), Any, PyobsCLI, Start process as a daemon. Args: pid_file: Name of PID file., Class for initializing and running pyobs CLI., main(), Any, PyobsWinCLI (+3 more)

### Community 141 - "Robotic recipe (doc)"
Cohesion: 0.17
Nodes (21): pyobs.modules.robotic (doc), Mastermind (module), PointingSeries, Scheduler (module), ScriptRunner, Robotic recipe (doc), AirmassConstraint, BackendObservationArchive (+13 more)

### Community 143 - "GuidingStatistics"
Cohesion: 0.16
Nodes (8): IN, OUT, GuidingStatistics, Any, Calculates statistics for guiding., Inits a stat measurement session for a client. Args: client: name/id of the…, Add statistics to given header. Args: client: id/name of the client header:…, Adds data to all client measurement sessions. Args: input_data: Image witch…

### Community 144 - "RollingTimeAverage"
Cohesion: 0.15
Nodes (16): RollingTimeAverage, Values older than interval are excluded from average., With min_interval, returns None if no values are older than min_interval., With min_interval, returns average if there are values older than min_interval., Only values within the rolling interval are included., add() cleans up values older than interval., test_add_evicts_expired_values(), test_average_clears_old_values() (+8 more)

### Community 145 - "TaskFailedEvent"
Cohesion: 0.25
Nodes (6): Any, Event to be sent when a task has failed., Initializes a new task failed event. Args: name: Name of task that just…, TaskFailedEvent, test_task_failed_properties(), test_task_failed_roundtrip()

### Community 146 - "WeatherApi"
Cohesion: 0.19
Nodes (10): Any, ClientSession, WeatherApi, MockResponse, Any, asyncio, test_get_current_status(), test_get_sensor_value() (+2 more)

### Community 147 - "BackendTaskArchive"
Cohesion: 0.07
Nodes (21): Project, BackendTaskArchive, Any, ClientSession, Task, TaskArchive, Time, Fetches last schedule update time. (+13 more)

### Community 148 - ".can_run"
Cohesion: 0.47
Nodes (3): Target, Checks, whether this task could run now. Args: task: Task to run target:…, Run a task. Args: task: Task to run target: Resolved target for this specific…

### Community 149 - "._set_optimal_focus"
Cohesion: 0.13
Nodes (11): Any, DataFrame, floating, NDArray, Initialize a focus model. Args: focuser: Name of focuser. weather: Name of…, Sets optimal focus. Args: filter_name: Name of filter to use. Raises:…, Sets optimal focus. Raises: WeatherDataError: If the weather station returned…, Fit method for model Args: x: Paramaters to evaluate. data: Full data set.… (+3 more)

### Community 151 - "`OBSNUM`: per-night observation counter in FITS headers"
Cohesion: 0.06
Nodes (28): 1. Event-driven frame delivery, not polling, 2. Backpressure: latest-frame-wins, not a queue, 3. Wire format (new — nothing in pyobs streams raw binary today), 4. Capability advertisement: `mjpeg`/`raw`, both `str | None`, on by default, 5. Activate/deactivate wiring, Alternatives considered, `BaseVideo`: raw-frame streaming endpoint, alongside the existing MJPEG live view, Constraint: one module, one job (+20 more)

### Community 152 - "3rd party packages (doc)"
Cohesion: 0.11
Nodes (20): 3rd party packages (doc), Astroplan, Astropy, Astroquery, Cython, LMFIT, matplotlib, NumPy (+12 more)

### Community 153 - "test_basetelescope.py"
Cohesion: 0.12
Nodes (29): OrbitalElements, InvalidOrbitalElementsError, _orbital_plane_to_ecliptic_cartesian(), _perifocal_to_radec(), _propagate_elements(), Rotates a perifocal-plane position into heliocentric ecliptic coordinates, then…, Rotates a perifocal-plane position (AU) into heliocentric ecliptic Cartesian…, Two-body Kepler propagation of orbital elements to (ra, dec) in degrees, ICRS.… (+21 more)

### Community 154 - "SSHFile"
Cohesion: 0.12
Nodes (12): Any, VFS wrapper for a file that can be accessed over a SFTP connection., Write data into the stream. Args: b: Bytes of data to write., If in write mode, actually send the file to the SSH server., Returns content of given path. Args: path: Path to list. kwargs: Parameters for…, Open/create a file over a SSH connection. Args: name: Name of file. mode: Open…, For read access, download the file into a local buffer. Raises:…, Read number of bytes from stream. Args: n: Number of bytes to read. Read until… (+4 more)

### Community 155 - "create_rst.py"
Cohesion: 0.33
Nodes (18): create_image_processors_rst(), create_modules_rst(), create_rst_overview(), create_utils_rst(), find_classes_in_modules(), find_python_modules(), find_submodules(), Any (+10 more)

### Community 156 - "LcoScript"
Cohesion: 0.09
Nodes (15): LcoAutoFocusScript, Auto focus script for LCO configs., Whether this config can currently run. Returns: True, if the script can run now, Run script. Raises: InterruptedError: If interrupted, LcoDefaultScript, Returns FITS header for the current status of this module. Args: namespaces: If…, Default script for LCO configs., Whether this config can currently run. Returns: True, if the script can run now (+7 more)

### Community 157 - "SoftBin"
Cohesion: 0.16
Nodes (11): Any, floating, NDArray, Bin a 2D image by averaging non-overlapping blocks, updating relevant FITS…, Init a new software binning pipeline step. Args: binning: Binning to apply to…, Bin an image. Args: image: Image to bin. Returns: Binned image., SoftBin, asyncio (+3 more)

### Community 158 - "AddMask"
Cohesion: 0.21
Nodes (13): AddMask, Any, floating, NDArray, Add mask to image. Args: image: Image to add mask to. Returns: Image with mask, Attach a precomputed mask to an image based on instrument and binning. This…, Init an image processor that adds a mask to an image. Args: masks: Dictionary…, asyncio (+5 more)

### Community 159 - "DataCache"
Cohesion: 0.09
Nodes (16): ImageRequest, Any, Initializes file cache. Args: port: Port for HTTP server. cache_size: Size of…, DataCache, DataCacheEntry, Any, A single entry in the data cache., Delete entry in cache. Args: name: Name of entry to delete. (+8 more)

### Community 160 - "RandomizeGrid"
Cohesion: 0.12
Nodes (11): SkyCoord, RandomizeGrid, Return the next point that satisfies all constraints. Iterates underlying…, Convert the next tuple to a SkyCoord. Expects a tuple (x_deg, y_deg) from the…, Transform the next SkyCoord to the target frame. Returns: A SkyCoord…, Randomize iteration order by rotating the underlying sequence. For each…, Yield a point after rotating the underlying grid a random number of times.…, Yield a point after rotating the underlying grid a random number of times.… (+3 more)

### Community 161 - ".retrieve_class_on_deserialization"
Cohesion: 0.24
Nodes (7): model_serializer, Any, model_validator, Self, Get the correct class for this model and run model_validate on that class with…, ValidationInfo, ValidatorFunctionWrapHandler

### Community 163 - "_SourceCatalog"
Cohesion: 0.06
Nodes (33): Background, Any, floating, NDArray, Initializes a wrapper for SEP. See its documentation for details. Highly…, Find stars in given image and append catalog. Args: image: Image to find stars…, Remove background from image in data. Args: data: Data to remove background…, Detect astronomical sources using SEP (Source Extractor for Python). This… (+25 more)

### Community 164 - "Design"
Cohesion: 0.15
Nodes (12): `comm.py` changes, Design, Node naming, Plan: Explicit pubsub subscriptions for event delivery, Post-merge fixes (review, 2026-08-16), Problem, Publishing (`send_event`, `xmppcomm.py:763`), Removed / unchanged (+4 more)

### Community 165 - "ExpTimeEval"
Cohesion: 0.11
Nodes (15): ExpTimeEval, Any, Observer, Return list of binnings., Return list of filters., Estimate exposure time for given filter Args: solalt: Solar altitude. binning:…, Initialize object with the given time. Args: time: Start time for all further…, Estimates exposure time for a given filter and binning at a given time offset… (+7 more)

### Community 166 - "Plan: Stop ImageWatcher per-file processing from blocking the event loop"
Cohesion: 0.15
Nodes (13): 1. Offload the FITS parse — `pyobs/modules/image/imagewatcher.py`, 2. Make `LocalFile` I/O non-blocking — `pyobs/vfs/localfile.py`, 3. (step 0, diagnostic) Confirm the culprit and measure before/after, Consequences, Considered options, Decision, Existing coverage (regression net, must keep passing), Goal (+5 more)

### Community 167 - "Plan: `IDataSequence` — server-side counted data sequences (reconstructed)"
Cohesion: 0.33
Nodes (5): Architecture, File Map, Goal, Plan: `IDataSequence` — server-side counted data sequences (reconstructed), Tasks

### Community 168 - "wait_for"
Cohesion: 0.15
Nodes (13): set_binning(int, int) -> None: multiple int params, void return., Calling a method that raises on the remote side propagates the exception., set_cooling(bool, float) then verify via state: full encode/decode cycle., set_cooling(bool, float) -> None: void return with bool + float params., set_gain(float) -> None and verify via IGain state: float param, state readback., set_gain(float) then verify via IGain state: float param round-trip., test_rpc_bool_float_roundtrip(), test_rpc_exception_fault() (+5 more)

### Community 169 - "ResolvableErrorLogger"
Cohesion: 0.23
Nodes (7): Any, Logger, Logging for resolvable errors. Args: logger: Logger to use. error_level: Log…, Log an error message., ResolvableErrorLogger, create_logger(), test_logger()

### Community 170 - ".__init__"
Cohesion: 0.33
Nodes (4): Any, Abort current actions., Initialize a new flat field scheduler. Args: flatfield: Flat field module to…, Perform flat-fielding Raises: DeviceBusyError: If a flat-fielding run is…

### Community 171 - "._get_client"
Cohesion: 0.11
Nodes (10): PresenceCallback, Get a proxy to the given client. Args: client: Name of client. Returns: Proxy…, Fetch capabilities for a single interface and push them into the given proxy…, Called when a client disconnects. Args: event: Disconnect event. sender: Name…, Returns list of interfaces for given client. Args: client: Name of client.…, Subscribe to state updates for a given module and interface. Delivers the…, Unsubscribe from state updates. Args: module: Name of remote module. interface:…, Subscribe to presence updates for a given module. Delivers the current value… (+2 more)

### Community 172 - "test_grab_sequence.py"
Cohesion: 0.29
Nodes (16): make_camera(), asyncio, Tests for BaseCamera.grab_sequence()/abort_sequence(), the IDataSequence…, grab_sequence() must not block for the whole sequence -- see design doc: a…, test_abort_clears_running_sequence(), test_abort_cuts_delay_short(), test_abort_sequence_cuts_delay_short(), test_abort_sequence_lets_current_grab_finish_but_stops_the_rest() (+8 more)

### Community 173 - "binding.py"
Cohesion: 0.23
Nodes (8): fault2xml(), py2xml(), Any, Element, rpcbase64, rpctime, xml2fault(), xml2py()

### Community 174 - "Event"
Cohesion: 0.40
Nodes (3): Event, Change status of weather. Args: event: The good weather event. sender: Who sent…, Creates a new BaseCamera. Args: fits_headers: Additional FITS headers. centre:…

### Community 175 - "wait_for"
Cohesion: 0.17
Nodes (12): DummyCamera.open() must publish IWindow.Capabilities with the SimCamera full…, DummyCamera.open() must publish IModule.Capabilities with version and label., get_capabilities() must return None for an interface DummyCamera doesn't…, Poll *condition* until truthy or *timeout* seconds elapse., DummyCamera's _cooling_thread publishes CoolingState every second. An observer…, After calling set_cooling via RPC, the published CoolingState must reflect the…, test_dummy_camera_cooling_state_reflects_set_cooling(), test_dummy_camera_no_capabilities_for_unconfigured_interface() (+4 more)

### Community 176 - "test_xmppcomm_event_payload.py"
Cohesion: 0.14
Nodes (23): _log_task_exception(), Retrieve and log a background task's exception, if it failed. Results of…, Send an event to other clients. Args: event (Event): Event to send, _event_msg(), _EventMsg, _log_event_json(), _make_comm(), asyncio (+15 more)

### Community 177 - "test_httpfilecache.py"
Cohesion: 0.52
Nodes (11): make_cache(), make_request(), asyncio, test_download_response_has_cors_header(), test_download_with_token_configured_accepts_correct_token(), test_download_with_token_configured_rejects_missing_header(), test_download_with_token_configured_rejects_wrong_token(), test_download_without_token_configured_is_unauthenticated() (+3 more)

### Community 178 - "test_dummyvideo.py"
Cohesion: 0.17
Nodes (15): DummyVideo, Any, A dummy video module for testing — streams simulated noise frames., Creates a new dummy video module. Args: fps: Frames per second to simulate.…, Set the exposure time (frame interval). Args: exposure_time: Exposure time in…, Background task that generates simulated frames., make_dummyvideo(), asyncio (+7 more)

### Community 179 - "MotionStatusChangedEvent"
Cohesion: 0.20
Nodes (7): MotionStatusChangedEvent, Any, Event to be sent when the motion status of a device has changed., test_motion_status_invalid_status(), test_motion_status_no_interfaces(), test_motion_status_properties(), test_motion_status_roundtrip()

### Community 180 - "Steering: astropy IERS auto-download blocks event loop"
Cohesion: 0.32
Nodes (8): BaseTelescope._celestial / _update_celestial_headers, Steering: astropy IERS auto-download blocks event loop, iers_offline config flag (stopgap fix), Steering: Blocking vendor SDK calls must never run directly on the event loop, _run_blocking() pattern (pyobs_aravis.araviscamera.AravisCamera), _wait_for_frame() tight-poll wrapper pattern, Steering: OnDemandScheduler.evolve() uncached sunset lookup stalls event loop, ObservationArchiveEvolution.evolve() Time.night_obs() bug (fixed via memoization)

### Community 181 - ".move_radec"
Cohesion: 0.50
Nodes (3): Any, DEGREES, Starts tracking on given coordinates. Args: ra: RA in deg to track. dec: Dec in…

### Community 182 - "CLI"
Cohesion: 0.16
Nodes (9): CLI, Initializes a new instance of the CLI class., Overwrite this to set CLI parameters with argparse., Overwrite this to actually run the CLI., Load config from config file, Load config from environment variables., main(), PyobsDaemonCLI (+1 more)

### Community 183 - ".set_focus"
Cohesion: 0.40
Nodes (4): Any, MM, Sets new focus. Args: focus: New focus value in mm. Raises:…, Sets focus offset. Args: offset: New focus offset in mm. Raises: ValueError: If…

### Community 184 - "Merit"
Cohesion: 0.15
Nodes (15): AfterTimeMerit, BeforeTimeMerit, ConstantMerit, DataProvider, FollowMerit, IntervalMerit, ObservationArchiveEvolution wraps ObservationArchive with per-run caching (avoid repeated HTTP requests) and lookahead simulation (evolve() records tentative future assignments so IntervalMerit/PerNightMerit see them and avoid double-scheduling within one run), Merit (+7 more)

### Community 185 - "ejabberd shaper throttling bug (xmpp_socket.erl re-arm) & fix"
Cohesion: 0.21
Nodes (12): XMPP/ejabberd diagnostics recipe (doc), benchmark_state_throughput.py, check_ejabberd_notify.py, delete_pubsub_nodes.py, list_pubsub_nodes.py, Comparing shaper configs (rationale), show_module_info.py, scripts/xmpp/install-ejabberd.sh (+4 more)

### Community 186 - "test_xmpp_acl.py"
Cohesion: 0.22
Nodes (12): Integration tests for Phase 8 Access Control (ACLs) over real XMPP. Verifies…, A caller granted "*" access under "allow" can still call normally., A caller not present in the "allow" map is denied by default., A caller on the "deny" list gets exc.RemoteError with a forbidden message, not…, Naming an interface under "allow" permits all of its methods, but nothing…, A module not on the "deny" list is unaffected., test_acl_allow_denies_unlisted_caller(), test_acl_allow_interface_name_sugar() (+4 more)

### Community 187 - "Plan: Make the pydantic config layer reject unknown keys (`extra="forbid"`)"
Cohesion: 0.18
Nodes (10): Decision, Gap: the imaging config models are not covered by this change, Implementation checklist, Latent bug this surfaced (separate from the above), Merged, Plan: Make the pydantic config layer reject unknown keys (`extra="forbid"`), PR review follow-up (github.com/pyobs/pyobs-core/pull/762, thusser), Problem (+2 more)

### Community 188 - "Work Plan"
Cohesion: 0.12
Nodes (16): Dropped items, Phase 0 — Foundations, Phase 1.5 — RPC payload encoding 2.0, Phase 1 — Walking skeleton: prove State end-to-end on one interface, Phase 2.5 — Discovery and Presence, Phase 2 — Audit and design pass (no implementation yet), Phase 3 — Bulk rollout, Phase 4 — Other backends and Presence (+8 more)

### Community 189 - "Plan: `pyobs-gui` TelescopeWidget layout — width floor investigation & design notes"
Cohesion: 0.12
Nodes (16): 1. Make the stacked widget size to the current page, not the widest one, 2. Adopt a width convention for future coordinate-type pages, 3. `QFormLayout::setRowWrapPolicy()` on the individual form pages, 4. Resize-driven reparenting for the four-groupbox row, Capability-driven visibility is handled by toggling pre-built sections on/off, Coordinate-type selection is already a combobox, not tabs, Each coordinate-type page has a fixed, hand-built field set, Filter, Focus, and the offsets rows are structurally duplicated (+8 more)

### Community 191 - "GridPipeline"
Cohesion: 0.14
Nodes (9): GridPipeline, Any, Build a GridPipeline from a list of steps. Args: steps: A non-empty list where…, Return the next point from the pipeline. Returns: The next point produced by…, Return the number of points remaining in the pipeline. Returns: The length…, Append the last yielded point back to the pipeline's final stage., Log the last yielded point via the pipeline's final stage., A pipeline that composes a grid and a sequence of filters. The pipeline expects… (+1 more)

### Community 192 - "Plan: Make mixin `__init__` composition cooperative, then enforce unrecognized kwargs at `Object.__init__`"
Cohesion: 0.11
Nodes (18): Approach, Critical finding (2026-08-18): PR #776's blast radius isn't scoped by rollout order, Decision, Implementation checklist, Non-goals, Plan: Make mixin `__init__` composition cooperative, then enforce unrecognized kwargs at `Object.__init__`, Problem, Rollout order (proposed, safest first — confirm before starting, not confirmed operational (+10 more)

### Community 193 - "test_comm_interface_resolution.py"
Cohesion: 0.29
Nodes (8): Converts a list of interface names to interface classes. Args: interfaces: list…, LogCaptureFixture, Tests for Comm._interface_names_to_classes -- the base-Comm chokepoint that…, An interface defined entirely outside pyobs.interfaces resolves the same way…, test_resolves_external_interface(), test_resolves_known_and_skips_unknown_in_same_list(), test_resolves_known_core_interfaces(), test_skips_unknown_name()

### Community 194 - "What's New in pyobs 2.0 (doc)"
Cohesion: 0.12
Nodes (26): Overview (doc), Access control (ACL), Comm, Events, Interface, Module (base class), Object (base class), Location / astroplan.Observer (+18 more)

### Community 195 - "test_imagewriter.py"
Cohesion: 0.20
Nodes (16): ImageWriter, Any, Writes new images to disk., Creates a new image writer. Args: filename: Pattern for filename to store…, Puts a new images in the DB with the given ID. Args: event: New image event…, make_image_event(), make_writer(), asyncio (+8 more)

### Community 196 - "localcomm.py"
Cohesion: 0.16
Nodes (13): ConfigAppliedState, DummyConfig, DummyStructuredConfigModule, Any, asyncio, fixture, Tests for IStructuredConfig capabilities/state round-tripping through LocalComm., Reset LocalNetwork singleton before each test. (+5 more)

### Community 199 - "comm/test_events.py"
Cohesion: 0.18
Nodes (15): asyncio, Tests for Comm.register_event / unregister_event. Covers…, Two independent subscribers for the same event: one tearing down must not un-…, A module that both sends an event (handler-less register_event()) and…, unregister must mirror the exact same derived-events expansion register_event…, Two independent subscribers (e.g. two widget instances for the same event type)…, Once the last handler for an event is unregistered, the event must no longer be…, test_unregister_event_drops_subscribed_role_when_last_handler_removed() (+7 more)

### Community 200 - "asyncio"
Cohesion: 0.09
Nodes (44): asyncio, make_task_archive(), Projects with the backend `public` flag ingest without a strict-model…, Tasks with the backend `updated_at` field (pyobs-robotic-backend#84) ingest…, `_update()` itself does not consult the marker -- the gate lives in `_poll()`,…, Idempotent poll: identical content must not fire on_tasks_changed or bump…, Same task identity but changed content (e.g. active=False in the backend) must…, Change detection must compare model fields, not pydantic __eq__: runtime… (+36 more)

### Community 201 - "test_basecamera.py"
Cohesion: 0.16
Nodes (17): asyncio, parametrize, DummyCamera's _expose() must raise AbortedError, not some guessed builtin, when…, BaseCamera must forward fits_header_timeout to ImageFitsHeaderMixin, not…, Test basic open/close of BaseCamera., #547: BaseCamera must abort on BadWeatherEvent., #547: a BadWeatherEvent must actually trigger abort() -- exposure + any running…, #672: a BadWeatherEvent must not interrupt a dark/bias sequence -- the shutter… (+9 more)

### Community 202 - "show_module_info.py"
Cohesion: 0.25
Nodes (13): h1(), h2(), inspect_module(), _interface_from_feature(), kv(), main(), _module_state_from_show(), ok() (+5 more)

### Community 203 - "RunningState"
Cohesion: 0.04
Nodes (65): F, AcquisitionAttempt, AcquisitionResult, AcquisitionState, Any, Acquire target at given coordinates. If no RA/Dec are given, start from current…, AutoFocusResult, AutoFocusState (+57 more)

### Community 204 - "FitsHeaderMixin"
Cohesion: 0.11
Nodes (16): FitsHeaderMixin, Any, PrimaryHDU, Add requested FITS headers to header of given image. Args: image: Image with…, Add the cheap, local FITS headers to the given image (no I/O, no comm). This is…, Add requested FITS headers to header of given image. Args: image: Image with…, Add FITS header keywords to the given FITS header. Args: image: Image with…, Helper methods for all modules that implement IImageGrabber. (+8 more)

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
Cohesion: 0.14
Nodes (8): BaseTransport, Any, Exception, Send coordinates to clients., A stellarium telescope., Initialize a new stellarium telescope proxy. Args: telescope: Name of telescope…, Stellarium, StellariumProtocol

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

### Community 219 - "Scheduler"
Cohesion: 0.15
Nodes (7): Any, Compares two lists of tasks and returns two lists, containing those that are…, Trigger a re-schedule., Re-schedule when task has started and we can predict its end. Args: event: The…, Reset current task, when it has finished or failed. Args: event: The task…, Re-schedule on incoming good weather event. Args: event: The good weather…, Scheduler

### Community 220 - "test_autofocus.py"
Cohesion: 0.23
Nodes (20): AutoFocusScript, Script for running autofocus series., isinstance_class(), Shared test-double helpers used across multiple test modules., Build a fresh class purely for isinstance() checks against a MagicMock.…, make_autofocus(), make_script(), make_task() (+12 more)

### Community 221 - "Archive"
Cohesion: 0.08
Nodes (36): ProgressEvent, Archive, Base class for image archives., Pipeline, Any, Create master bias frame. Args: images: List of raw bias frames. Returns:…, Create master dark frame. Args: images: List of raw dark frames. bias: Bias…, Create master flat frame. Args: images: List of raw flat frames. bias: Bias… (+28 more)

### Community 222 - "LogScript"
Cohesion: 0.26
Nodes (12): DebugTriggerScript, Script for a debug trigger., LogScript, Script for logging something., asyncio, Expression has access to 'now' as a datetime., test_debug_trigger_can_run(), test_debug_trigger_sets_triggered() (+4 more)

### Community 223 - "test_imagewatcher.py"
Cohesion: 0.33
Nodes (15): make_fits_bytes(), make_read_write_ctx(), make_watcher(), asyncio, On write failure the file is re-queued and remove is NOT called., test_add_file_queues_filename(), test_add_file_respects_pattern(), test_add_file_skips_non_matching_pattern() (+7 more)

### Community 224 - "XEP_0009_timeout"
Cohesion: 0.17
Nodes (6): BasePlugin, A plugin for SleekXMPP, adding a timeout to RPC calls., XEP_0009_timeout, SleekXMPP: The Sleek XMPP Library Copyright (C) 2011 Nathanael C. Fritz, Dann…, MethodTimeout, ElementBase

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

### Community 233 - "GridNode"
Cohesion: 0.16
Nodes (19): AvoidMoon, ConvertGridFrame, ConvertGridToSkyCoord, FromList, GridFilterValue, Convert (x, y) degree tuples to SkyCoord objects. Wraps a tuple-producing grid…, Transform SkyCoord points to a different frame., Remove points too close to the moon. If the next point in the underlying grid… (+11 more)

### Community 234 - "CHANGELOG.rst"
Cohesion: 0.18
Nodes (11): ejabberd shaper/xmpp_socket.erl reactivation bug (iag50srv capability-fetch timeouts), XmppComm disco#info role attribute (send/subscribe split), ImageProcessor on_error kwarg / per-step error handling, OnDemandScheduler CPU-bound work offloaded to ThreadPoolExecutor, Vfs.write_image()/write_fits() moved to asyncio.to_thread(), run_cpu_bound (scheduler/_executor.py), Vfs.write_fits (pyobs/vfs/vfs.py), Vfs.write_image (pyobs/vfs/vfs.py) (+3 more)

### Community 235 - "Use a self-hosted Keycloak alongside odin, as two parallel auth backends"
Cohesion: 0.10
Nodes (17): Consequences, Considered Options, Context and Problem Statement, Decision Outcome, Use a self-hosted Keycloak alongside odin, as two parallel auth backends, Consequences, Considered Options, Context and Problem Statement (+9 more)

### Community 236 - "Image class"
Cohesion: 0.20
Nodes (10): meta.AltAzOffsets, meta.ExpTime, Image class, Image.meta dict; rationale: keyed by class to avoid collisions between pipeline stages, kept out of FITS since it's runtime-only data, meta.OnSkyDistance, meta.PixelOffsets, meta.RaDecOffsets, meta.SkyOffsets (+2 more)

### Community 237 - "._expose"
Cohesion: 0.13
Nodes (12): Image, NamedTuple, ExposureInfo, Actually do the exposure, should be implemented by derived classes. Args:…, Method that is always called at the very beginning of __expose and can be used…, Wrapper for a single exposure. Args: exposure_time: The requested exposure time…, Info about a running exposure., Add FITS headers in derived classes. Args: image: Image to write FITS headers… (+4 more)

### Community 238 - "Implementation"
Cohesion: 0.15
Nodes (13): 1. Frame.PROJECT — `pyobs_archive/api/models.py`, 2. Backend connection (project/user knowledge), 3. Access layer — `pyobs_archive/api/permissions.py`, 4. Endpoint filtering — `pyobs_archive/api/views.py`, 5. Frontend — `pyobs_archive/frontend`, 6. Backend dependency — tracked in pyobs/pyobs-robotic-backend#79, Consequences, Implementation (+5 more)

### Community 239 - "IMotion"
Cohesion: 0.15
Nodes (12): IMotion, Any, The module controls a device that can move., Initialize device. Raises: InitError: If device could not be initialized., Park device. Raises: ParkError: If device could not be parked., Stop the motion. Args: device: Name of device to stop, or None for all., IRotation, Any (+4 more)

### Community 240 - "Module.startup() lifecycle helper"
Cohesion: 0.50
Nodes (4): Module.startup() lifecycle helper, ModuleState.STARTING, Rationale: delay send_presence() until READY to avoid capability-publish race, Gating RPC commands until module startup completes

### Community 241 - "Object"
Cohesion: 0.03
Nodes (78): PydanticBaseModel, Object, PrivateAttrMixin, :class:`~pyobs.object.Object` is the base for almost all classes in *pyobs*. It…, Base class for all objects in *pyobs*., Whether object has been opened., Can be overloaded to quit program., Any (+70 more)

### Community 242 - "Plan: Stop scheduler constraint/merit evaluation from blocking the event loop"
Cohesion: 0.14
Nodes (13): 1. Dedicated executor — new file `pyobs/robotic/scheduler/_executor.py`, 2. Offload the three call sites — `pyobs/robotic/scheduler/ondemandscheduler.py`, 3. Cache target-independent astropy results — `pyobs/robotic/scheduler/dataprovider.py`, 4. `AstroplanScheduler` — no change, Consequences, Considered options, Decision, Existing coverage (regression net, no changes needed) (+5 more)

### Community 243 - ".__init__"
Cohesion: 0.18
Nodes (8): Any, SkyCoord, Create an approximately equidistributed spherical grid. Args: n: Target number…, Initialize a Grid with a list of points. Args: points: Initial list of points…, Return the next point and remove it from the internal list. Returns: The next…, Create a regular lon/lat grid. Args: n_lon: Number of longitudinal divisions.…, Any, Initialize a GridNode. Args: log: If True, enable informational logging for…

### Community 244 - "watch_log_events_no_interest.py"
Cohesion: 0.50
Nodes (4): main(), make_client(), ClientXMPP, Like watch_log_events_raw.py, but deliberately never declares XEP-0163…

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
Cohesion: 0.23
Nodes (14): pyobs.modules.telescope (doc), BaseTelescope, DummyAltAzTelescope, DummyRaDecTelescope, DummySolarTelescope, Jupyter recipe (doc), ICamera, ITelescope (+6 more)

### Community 253 - "IOffsetsAltAz.py"
Cohesion: 0.19
Nodes (12): AltAzOffsetState, IOffsetsAltAz, The module supports Alt/Az offsets, usually combined with…, DummyAltAzTelescope, Any, A dummy alt/az-offset telescope for testing, offering Alt/Az offsets., Creates a new dummy Alt/Az telescope. Args: offsets: Initial Alt/Az offsets in…, Move an Alt/Az offset. (+4 more)

### Community 254 - "XmppComm"
Cohesion: 0.04
Nodes (32): Handles an event. Args: msg: Received XMPP message. node: pubsub node id the…, A Comm class using XMPP. This Comm class uses an XMPP server (e.g. `ejabberd…, Send XMPP presence stanza reflecting the module lifecycle state. ModuleState…, See Comm.mark_ready(). Remembers readiness on self (survives client recreation…, Called, when the module connected to this Comm changes. Args: module: The…, Open the connection to the XMPP server. Returns: Whether opening was successful., Sleep a little and reconnect, Reset connection after disconnect. (+24 more)

### Community 256 - "Decision"
Cohesion: 0.17
Nodes (11): 1. `ImageProcessor` — new methods and kwarg, 2. `PipelineMixin.run_pipeline()` — wrap each step, 3. `AstrometryDotNet` — migrate to handle_error, 4. Deprecation notes, 5. Tests, Consequences, Considered options, Decision (+3 more)

### Community 257 - ".can_run"
Cohesion: 0.17
Nodes (6): DataProvider, Time, Resolve dynamic target. Returns False if no valid target found., Checks whether this task could run now. Returns: True, if the task can run now., Returns reason why task cannot run, or None if it can., Script

### Community 260 - "enums.py"
Cohesion: 0.04
Nodes (56): IAcquisition, The module can acquire a target, usually by accessing a telescope and a camera., IAutoGuiding, The module can perform auto-guiding., ExposureTimeState, IExposureTime, The camera supports exposure times, to be used together with…, ImageTypeState (+48 more)

### Community 261 - "robotic"
Cohesion: 0.43
Nodes (8): acquisition, fibercamera, fts, guiding, robotic, solar telescope, suncamera, weather

### Community 262 - "Archive (image archive base)"
Cohesion: 0.32
Nodes (8): Archive (image archive base), LocalArchive, PyobsArchive, ArchiveSkyflatPriorities, Archive, Image archives (pyobs.robotic.utils.archive) API doc, LocalArchive, PyobsArchive

### Community 263 - "Scheduler"
Cohesion: 0.16
Nodes (8): Run script. Raises: InterruptedError: If interrupted, Observer, Iterator for scheduler items, Scheduler for taking flat fields, Initializes a new scheduler for taking flat fields Args: functions: Flat field…, Scheduler, asyncio, test_scheduler()

### Community 264 - "integration/conftest.py"
Cohesion: 0.23
Nodes (13): connect(), make_camera_comm(), make_unopened_comm(), make_xmpp_comm(), fixture, Fixtures shared across all integration tests., Factory fixture: ``await make_xmpp_comm(user)`` returns an open XmppComm for…, Connect a module to LocalComm and return the comm. (+5 more)

### Community 265 - "CasesRunner"
Cohesion: 0.33
Nodes (4): CasesRunner, Script for distinguishing cases., Returns FITS header for the current status of this module. Args: namespaces: If…, Estimate duration of the script for the current case.

### Community 266 - "RemoveBackground"
Cohesion: 0.21
Nodes (9): Any, Estimate and subtract the background from an image using a DAOPhot-style…, Init an image processor that removes background from image. Args: sigma: Sigma…, Remove background from image. Args: image: Image to remove background from.…, RemoveBackground, asyncio, test_call_const_background(), test_init() (+1 more)

### Community 267 - "test_camerasettings.py"
Cohesion: 0.57
Nodes (7): make_camera_proxy(), make_module(), asyncio, Capabilities for a Proxy are fetched in the background (see…, test_raises_when_capabilities_never_arrive(), test_sets_binning_before_window(), test_sets_window_to_full_frame_once_capabilities_arrive_late()

### Community 268 - "._get_next"
Cohesion: 0.33
Nodes (4): SkyCoord, Log a point if logging is enabled. For SkyCoord instances, logs RA/Dec in…, Return the next point in the sequence. Implementors must return either a (x, y)…, Return the next point, storing it as the last yielded value. Returns: A point…

### Community 269 - "Discussion: LogEvent double-delivery fix — should we drop add_interest()?"
Cohesion: 0.20
Nodes (9): Can roster and pubsub delivery be split?, Consequence: are all events sent to all clients?, Did we ever need add_interest()?, Discussion: LogEvent double-delivery fix — should we drop add_interest()?, How could real interest-based filtering be achieved?, Monitoring / rollback plan, Proposed fix (from the investigation, point 15), Was shared roster a bad idea? (+1 more)

### Community 270 - "Plan: `pyobs-gui` navbar keyboard shortcuts"
Cohesion: 0.18
Nodes (10): Binding is by page name, not by widget or list-item instance, File changes, Key scheme, Motivation, Plan: `pyobs-gui` navbar keyboard shortcuts, Shortcut wiring, State, Verification (once implemented) (+2 more)

### Community 272 - "test_baseroof.py"
Cohesion: 0.30
Nodes (8): MockBaseRoof, Any, asyncio, test_get_fits_header_before_closed(), test_get_fits_header_before_open(), test_not_ready(), test_open(), test_ready()

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

### Community 279 - "GuidingStatisticsPixelOffset"
Cohesion: 0.25
Nodes (7): GuidingStatisticsPixelOffset, Calculates RMS of data. Args: data: Data to calculate RMS for. Returns: Tuple…, mock_meta_image(), fixture, test_build_header_to_few_values(), test_end_to_end(), test_get_session_data()

### Community 280 - "GuidingStatisticsSkyOffset"
Cohesion: 0.25
Nodes (7): GuidingStatisticsSkyOffset, Calculates RMS of data. Args: data: Data to calculate RMS for. Returns: Tuple…, mock_meta_image(), fixture, test_build_header_to_few_values(), test_end_to_end(), test_get_session_data()

### Community 281 - "ObservationList"
Cohesion: 0.04
Nodes (82): ObservationList, Any, date, Add the list of scheduled tasks to the schedule. Args: tasks: Scheduled tasks., Returns a list of observations for the given task. Args: date: Date of night to…, Fetch schedule from the portal. Returns: Dictionary with tasks. Raises:…, LcoScheduleReader, Update list of requests. Args: force: Force update. (+74 more)

### Community 282 - ".move_heliocentric_polar"
Cohesion: 0.50
Nodes (3): Any, DEGREES, Moves on given coordinates. Args: mu: Cosine of the angular distance from Sun…

### Community 283 - "WeatherStatus"
Cohesion: 0.27
Nodes (6): Any, setter, WeatherStatus, test_status_set(), test_status_set_non_good(), test_status_set_none_good()

### Community 284 - "run_cpu_bound"
Cohesion: 0.29
Nodes (8): Any, Runs an async callable to completion on a dedicated worker thread, off the…, run_cpu_bound(), _T, asyncio, test_run_cpu_bound_propagates_exception(), test_run_cpu_bound_returns_value(), test_run_cpu_bound_runs_on_different_thread()

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

### Community 290 - "Plan: raw-frame streaming endpoint in `BaseVideo`"
Cohesion: 0.29
Nodes (6): Context, Explicitly out of scope for this plan, Plan: raw-frame streaming endpoint in `BaseVideo`, Post-merge fixes (review, 2026-08-16), Testing, Todo

### Community 292 - "Plan: `pyobs-gui` IAutoGuiding widget"
Cohesion: 0.25
Nodes (7): Known bug in the shipped widget (to fix alongside this change), Plan: `pyobs-gui` IAutoGuiding widget, Problem: pixel offsets aren't physical, and the per-image correction is discarded, Proposed pyobs-core change, Resolved from the original open questions, Shipped (pyobs-core, `develop`), Widget design (pyobs-gui)

### Community 293 - "ExposureStatus"
Cohesion: 0.06
Nodes (34): ExposureStatusChangedEvent, Any, Event to be sent, when the exposure status of a device changes., ExposureState, BaseSpectrograph, ExposureInfo, Any, HDUList (+26 more)

### Community 294 - "SchedulerItem"
Cohesion: 0.13
Nodes (9): Iterate over scheduler items, Return schedule item., Find a possible slot for a given filter/binning in the given schedule Args:…, A single item in the flat scheduler, Checks, whether a new scheduler item would overlap an existing item Args:…, Initializes a new scheduler item Args: start: Start time in seconds end: End…, Nice string representation for item, Calculate schedule starting at given time Args: time: Time to start schedule at (+1 more)

### Community 295 - "Investigation: pyobs-gui receives every LogEvent twice (SAAO/monet production)"
Cohesion: 0.25
Nodes (7): Access used, Artifacts from this session, Investigation: pyobs-gui receives every LogEvent twice (SAAO/monet production), Next steps, Problem, What's confirmed, What's ruled out

### Community 297 - "Plan: Module observer-location capabilities (reconstructed)"
Cohesion: 0.33
Nodes (5): Architecture, File Map, Goal, Plan: Module observer-location capabilities (reconstructed), Tasks

### Community 299 - "datetime"
Cohesion: 0.42
Nodes (4): datetime, GuidingStatisticsUptime, test_calc_uptime_percentage(), test_end_to_end()

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

### Community 304 - "._filter_data"
Cohesion: 0.24
Nodes (3): Any, DataFrame, Update files in root directory.

### Community 305 - "test_pyobsd.py"
Cohesion: 0.29
Nodes (9): make_daemon(), Any, parametrize, Tests for PyobsDaemon._start_service()'s command construction -- in particular,…, file_log defaults to False -- --log-file is opt-in, not unconditional., test_start_service_creates_log_path_only_when_file_log_enabled(), test_start_service_creates_log_path_when_file_log_enabled(), test_start_service_default_is_no_file_log() (+1 more)

### Community 306 - "._change_exposure_status"
Cohesion: 0.25
Nodes (5): ExposureStatus, Change exposure status and send event, Args: status: New exposure status., Returns the remaining exposure time on the current exposure in seconds., Returns the progress of the current exposure in percent. Returns: Progress of…, Background task: re-publish IExposure state while exposing.…

### Community 307 - "Plan: Bound the FITS-header fetch so a dead peer can't stall the frame"
Cohesion: 0.29
Nodes (6): Design, Plan: Bound the FITS-header fetch so a dead peer can't stall the frame, Post-merge fixes (review, 2026-08-16), Problem, Rollout, Testing

### Community 308 - "plans/index.md"
Cohesion: 0.07
Nodes (22): Architecture, File Map, Goal, Plan: Unify TRIMSEC handling into `Image.trim()` (reconstructed), Tasks, Implemented, Option A: reactive-only (already shipped, zero work), Option B: proactive greying-out — effort estimate (~half a day, 3-5 hours) (+14 more)

### Community 309 - "ScriptRunner"
Cohesion: 0.14
Nodes (15): calc_run_timeout(), Any, Calculates timeout for run()., Module for running a script., Initialize a new script runner. Args: script: Config for script to run., Run script. Raises: ScriptError: If the script failed (e.g. a proxy/network…, Abort current actions., ScriptRunner (+7 more)

### Community 310 - "SMBFile"
Cohesion: 0.22
Nodes (5): Any, Returns content of given path. Args: path: Path to list. kwargs: Parameters for…, VFS wrapper for a file that can be accessed over a SMB connection. Requires…, Open/create a file over a SSH connection. Args: name: Name of file. mode: Open…, SMBFile

### Community 311 - ".__call__"
Cohesion: 0.29
Nodes (5): Any, DataFrame, Initialize new CSV publisher. Args: filename: Name of file to log in., Publish the given results. Args: **kwargs: Results to publish., Return data that has so far been published.

### Community 312 - ".set_tracking_rate"
Cohesion: 0.50
Nodes (3): ARCSEC_PER_SEC, Any, Sets an absolute tracking rate on the sky, in arcsec/sec. Args: ra_rate: Rate…

### Community 313 - "Fleet open items: open issues and plans across the pyobs fleet"
Cohesion: 0.29
Nodes (7): Design docs still *proposed*, Fleet open items: open issues and plans across the pyobs fleet, Open decisions, Open issues (7, checked 2026-08-21), Open plans, pyobs-core `specs/plans/`, Sibling repos

### Community 315 - ".get_interfaces"
Cohesion: 0.29
Nodes (4): Returns list of interfaces for given client. Args: client: Name of client.…, Return list of interfaces for the given JID. Args: jid: JID to get interfaces…, Extract (event class name, version) pairs a peer's disco#info marks role="send"…, Checks, whether the given client supports the given interface. Args: client:…

### Community 316 - "ModuleLocation dataclass (nested in ModuleCapabilities)"
Cohesion: 0.50
Nodes (4): Location-mismatch warning via _on_module_opened, Rationale: location as one-shot capability, not pubsub state, ModuleLocation dataclass (nested in ModuleCapabilities), Module observer-location capabilities design doc

### Community 317 - "check_pyobs_releases.sh"
Cohesion: 0.70
Nodes (4): check_repo(), main(), print_header(), check_pyobs_releases.sh script

### Community 318 - "check_ejabberd_notify.py"
Cohesion: 0.60
Nodes (4): connect(), main(), make_client(), Minimal ejabberd notification test — no pyobs code involved.

### Community 321 - "GraticuleSphericalGrid"
Cohesion: 0.33
Nodes (6): GraticuleSphericalGrid, Grid with approximately equidistributed points on a sphere. Uses a graticule-…, Reinsert one point back into the grid., test_graticulesphericalgrid(), test_regularsphericalgrid(), test_regularsphericalgrid_append_last()

### Community 322 - "Photometry (pyobs.images.processors.photometry) API doc"
Cohesion: 0.83
Nodes (4): Photometry (pyobs.images.processors.photometry) API doc, Photometry, PhotUtilsPhotometry, SepPhotometry

### Community 323 - "Plan: `pyobs-gui` IAutoFocus widget"
Cohesion: 0.29
Nodes (6): Current state (pyobs-core, `develop`), Gap, Open questions, Plan: `pyobs-gui` IAutoFocus widget, Proposed pyobs-core change, Widget design (pyobs-gui)

### Community 324 - ".get_meta"
Cohesion: 0.40
Nodes (3): MetaClass, Returns meta information, assuming that it is stored under the class of the…, Calls get_meta in a safe way and returns default value in case of an exception.

### Community 325 - ".resolve"
Cohesion: 0.18
Nodes (7): DataProvider, Task, Pick the best available target given current conditions. For static targets…, Set the resolved target if not already set, e.g. when restoring from an…, The resolved target, or the static target if not dynamic., Target for this specific run: the observation's own record if known, otherwise…, Target

### Community 327 - ".night_obs"
Cohesion: 0.50
Nodes (3): date, Observer, Returns the night for this time, i.e. the date of the start of the current…

### Community 328 - ".get_config_value"
Cohesion: 0.40
Nodes (4): Any, ConfigValue, Returns current value of config item with given name. Args: name: Name of…, Sets value of config item with given name. Args: name: Name of config item.…

### Community 329 - "IAbortable"
Cohesion: 0.06
Nodes (37): IAbortable, Any, Abort current actions., The module has an abortable action., DataSequenceState, IDataSequence, Any, SECONDS (+29 more)

### Community 330 - ".grab_data"
Cohesion: 0.33
Nodes (4): Any, Creates a new pipeline cammera., Grabs an image and returns reference. Args: broadcast: Broadcast existence of…, GrabImageError

### Community 331 - "Plan: Exception handling across the RPC boundary (reconstructed)"
Cohesion: 0.33
Nodes (5): Architecture, File Map (representative, not exhaustive — see commit diffs for the full ~74-file list), Goal, Plan: Exception handling across the RPC boundary (reconstructed), Tasks

### Community 332 - "Plan: Decouple `ICamera`/`IExposure` (reconstructed)"
Cohesion: 0.33
Nodes (5): Architecture, File Map, Goal, Plan: Decouple `ICamera`/`IExposure` (reconstructed), Tasks

### Community 333 - "Plan: Advertise event send/subscribe role in disco#info"
Cohesion: 0.33
Nodes (5): Architecture, File Map, Plan: Advertise event send/subscribe role in disco#info, Problem, Tasks

### Community 337 - ".set_offsets_altaz"
Cohesion: 0.50
Nodes (3): Any, DEGREES, Move an Alt/Az offset. Args: dalt: Altitude offset in degrees. daz: Azimuth…

### Community 338 - ".set_config"
Cohesion: 0.50
Nodes (3): Any, ConfigValue, Apply a full structured config to this module. Args: config: Nested dict…

### Community 340 - ".flat_field"
Cohesion: 0.50
Nodes (3): Any, SECONDS, Do a series of flat fields. Args: count: Number of images to take Returns:…

### Community 342 - ".set_offsets_radec"
Cohesion: 0.50
Nodes (3): Any, DEGREES, Move an RA/Dec offset. Args: dra: RA offset in degrees. ddec: Dec offset in…

### Community 346 - "Script"
Cohesion: 0.10
Nodes (13): ConditionalRunner, Script for running an if condition., Returns FITS header for the current status of this module. Args: namespaces: If…, Estimate duration of the branch that would be run for the current condition., _run_script(), Script for running Mode Selection., Whether this config can currently run. Returns: True if script can run now., Estimate duration of the mode change. (+5 more)

### Community 347 - "pyobs.modules.weather (doc)"
Cohesion: 1.00
Nodes (3): pyobs.modules.weather (doc), MockWeather, Weather (module)

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
- **665 isolated node(s):** `Open issues (7, checked 2026-08-21)`, `pyobs-core `specs/plans/``, `Design docs still *proposed*`, `Sibling repos`, `Open decisions` (+660 more)
  These have ≤1 connection - possible missing edges or undocumented components.
- **55 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **What is the exact relationship between `Configuration utilities (pyobs.utils.config) API doc` and `Coordinate utilities (pyobs.utils.coordinates) API doc`?**
  _Edge tagged AMBIGUOUS (relation: conceptually_related_to) - confidence is low._
- **What is the exact relationship between `PyObsError` and `ScriptRunner.run()`?**
  _Edge tagged AMBIGUOUS (relation: conceptually_related_to) - confidence is low._
- **What is the exact relationship between `FocusError` and `FocusModel.set_optimal_focus`?**
  _Edge tagged AMBIGUOUS (relation: conceptually_related_to) - confidence is low._
- **Why does `Time` connect `Time` to `.__init__`, `Observation`, `focusmodel.py`, `Interface`, `robotic/task.py`, `Event`, `BaseGuiding`, `test_flatfielder.py`, `tests/test_events.py`, `test_lco_http.py`, `DummySolarTelescope`, `FitsHeaderEntry`, `test_control.py`, `SolarElevationConstraint`, `SiderealTarget`, `CoolingState`, `IPointingAltAz.py`, `Proxy`, `mixins/fitsheader.py`, `robotic/test_scheduler.py`, `Calibration`, `ImageType`, `FilenameFormatter`, `test_yaml_archives.py`, `Portal`, `test_astroplanscheduler.py`, `TimeDelta`, `Offsets`, `.now`, `test_proxy.py`, `test_acquisition.py`, `TaskData`, `Weather`, `ImagingScript`, `test_transit_mastermind.py`, `DummyCamera`, `test_pyobs_archive.py`, `FrameInfo`, `application.py`, `TaskStartedEvent`, `test_coordinates.py`, `DummyMode`, `LocalArchive`, `CommLoggingHandler`, `SkyFlatsBasePointing`, `modules/image/__init__.py`, `FocusModel`, `test_darkbias.py`, `WeatherSensors`, `comm.py`, `.__init__`, `flatfield/test_scheduler.py`, `SkyflatPriorities`, `Grid`, `pyobs.py`, `test_basetelescope.py`, `LcoScript`, `RandomizeGrid`, `ExpTimeEval`, `RunningState`, `FitsHeaderMixin`, `Scheduler`, `test_autofocus.py`, `Archive`, `GridNode`, `IMotion`, `Object`, `IOffsetsAltAz.py`, `enums.py`, `Scheduler`, `CasesRunner`, `ObservationList`, `SchedulerItem`, `._filter_data`, `.night_obs`, `IAbortable`, `Script`?**
  _High betweenness centrality (0.243) - this node is a cross-community bridge._
- **Why does `Image` connect `Image` to `.__init__`, `enums.py`, `BaseVideo`, `ImageProcessor`, `RemoveBackground`, `Interface`, `RuntimeError`, `GuidingStatistics`, `VirtualFileSystem`, `mixins/test_fitsheader.py`, `BaseGuiding`, `AstrometryDotNet`, `GuidingStatisticsPixelOffset`, `GuidingStatisticsSkyOffset`, `test_flatfielder.py`, `SoftBin`, `AddMask`, `_SourceCatalog`, `_DotNetRequest`, `mixins/fitsheader.py`, `_PhotometryCalculator`, `._filter_data`, `ExpTimeEstimator`, `Calibration`, `test_autoguiding.py`, `ImageType`, `FilenameFormatter`, `test_basevideo.py`, `.get_meta`, `Offsets`, `.grab_data`, `FitsHeaderMixin`, `test_acquisition.py`, `DummyCamera`, `PipelineMixin`, `Ring`, `Smooth`, `ProjectedOffsets`, `Archive`, `test_pyobs_archive.py`, `FrameInfo`, `FocusSeries`, `_DaoBackgroundRemover`, `LocalArchive`, `_PhotUtilAperturePhotometry`, `._expose`, `VFSFile`, `ImageSourceFilter`?**
  _High betweenness centrality (0.145) - this node is a cross-community bridge._
- **Why does `Module` connect `Module` to `utils/exceptions.py`, `WeatherSensors`, `comm.py`, `enums.py`, `BaseVideo`, `benchmark_state_throughput.py`, `focusmodel.py`, `flatfield/test_scheduler.py`, `Observation`, `Interface`, `xmpp/rpc.py`, `pyobs.py`, `robotic/task.py`, `MockWeather`, `test_camerasettings.py`, `test_kiosk.py`, `mixins/test_fitsheader.py`, `BaseGuiding`, `FitsHeaderEntry`, `DataCache`, `ExposureStatus`, `IPointingAltAz.py`, `test_dummymode.py`, `._get_client`, `mixins/fitsheader.py`, `robotic/test_scheduler.py`, `StandAlone`, `HttpFileCache`, `test_xmpp_presence.py`, `ScriptRunner`, `test_autoguiding.py`, `test_basevideo.py`, `Telegram`, `test_imagewriter.py`, `IAbortable`, `LogEvent`, `RunningState`, `test_acquisition.py`, `xmppcomm.py`, `Weather`, `Stellarium`, `PipelineMixin`, `test_exception_logging.py`, `Application`, `Scheduler`, `application.py`, `make_proxy_cm`, `DummyMode`, `Comm`, `Object`, `modules/image/__init__.py`, `._record_exception`, `FocusModel`, `XmppComm`?**
  _High betweenness centrality (0.077) - this node is a cross-community bridge._
- **Are the 158 inferred relationships involving `Time` (e.g. with `PyobsCLI` and `Proxy`) actually correct?**
  _`Time` has 158 INFERRED edges - model-reasoned connections that need verification._