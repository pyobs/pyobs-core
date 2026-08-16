# Graph Report - pyobs-core  (2026-08-16)

## Corpus Check
- 790 files · ~415,132 words
- Verdict: corpus is large enough that graph structure adds value.

## Summary
- 8817 nodes · 21195 edges · 458 communities (402 shown, 56 thin omitted)
- Extraction: 93% EXTRACTED · 7% INFERRED · 0% AMBIGUOUS · INFERRED: 1391 edges (avg confidence: 0.55)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `516cc99f`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- BaseTelescope
- BaseGuiding
- Time
- Module
- Interface
- test_presence.py
- Image
- .to_astropy
- PyobsError
- ImageProcessor
- Any
- BaseCamera
- WeatherSensors
- XmppComm
- _ResponseImageWriter
- .__init__
- TimeDelta
- test_schedulereader.py
- DummyRoof
- mixins/test_fitsheader.py
- Event
- PipelineMixin
- AstrometryDotNet
- test_flatfielder.py
- LocalComm
- tests/test_events.py
- test_lco_http.py
- FlatFieldPointing
- SiderealTarget
- WindowingWidget
- Interfaces (pyobs.interfaces) API doc
- test_control.py
- test_basetelescope.py
- Any
- Portal
- utils/exceptions.py
- test_parallel.py
- _AbortableModule
- _dataclass_to_xml
- IPointingAltAz.py
- ObservationList
- OffsetsAltAzEvent
- _SourceCatalog
- Any
- test_transitimaging.py
- robotic/test_scheduler.py
- StandAlone
- .__call__
- test_schedulewriter.py
- test_stellarexptime.py
- StarExpTimeEstimator
- RPC
- WindowCapabilities
- test_shellcommand.py
- Calibration
- .get_object
- Publisher
- _SepAperturePhotometry
- Any
- Proxy
- FilenameFormatter
- test_basevideo.py
- test_yaml_archives.py
- Project
- FlatFielder
- IExposure
- Telegram
- benchmark_state_throughput.py
- SolarElevationConstraint
- Offsets
- .now
- PyObsError
- test_proxy.py
- XEP_0009
- VirtualFileSystem
- PyobsDaemon
- MockWeather
- test_config.py
- test_dummyvideo.py
- test_acquisition.py
- Weather
- CoolingState
- ProjectionFocusSeries
- .set_focus
- AperturePhotometry
- Ring
- application.py
- XmppClient
- test_exception_logging.py
- DaophotSourceDetection
- Application
- DummyComm
- CallModuleScript
- ProjectedOffsets
- test_pyobs_archive.py
- HttpFile
- Object
- InfluxHandler
- FocusSeries
- SepSourceDetection
- make_proxy_cm
- test_autoguiding.py
- timeout
- ResolvableErrorLogger
- test_coordinates.py
- get_registered_interface
- What You Must Do When Invoked
- LocalArchive
- Plan: Systematic ejabberd throughput/latency benchmarking
- _PhotUtilAperturePhotometry
- Mixins (pyobs.mixins) API doc
- Script base class
- test_background_task.py
- Test Commlogging (comm)
- test_imagewriter.py
- test_dummyradectelescope.py
- ImagingScript
- HttpFileCache
- MemoryFile
- VFSFile
- LocalFile
- test_version_mismatch.py
- CLAUDE.md (repo guide)
- SFTPFile
- FocusModel
- ._expose
- ImageSourceFilter
- test_darkbias.py
- TaskData
- Archive
- Plan: pyobs-pipeline
- Test Localcomm (local)
- ImageWatcher
- .__init__
- test_camerasettings.py
- test_dummymode.py
- SkyFlatsBasePointing
- test_autofocus.py
- Grid
- test_kiosk.py
- pyobs.py
- Robotic recipe (doc)
- is_valid_jid
- test_basecamera.py
- test_config_schema.py
- ImageType
- Scheduler
- RollingTimeAverage
- SkyOffsets
- LogScript
- tests/xmpp/docker-compose.yml (ejabberd integration test container)
- `OBSNUM`: per-night observation counter in FITS headers
- 3rd party packages (doc)
- sourcedetection.py
- SSHFile
- create_rst.py
- Any
- SoftBin
- AddMask
- FrameInfo
- SkyCoord
- comm/test_events.py
- NewSpectrumEvent
- LogEvent
- ._filter_data
- ExpTimeEval
- Stellarium
- Overview (doc)
- TaskStartedEvent
- fits.py
- .can_run
- Scheduler
- test_grab_sequence.py
- binding.py
- test_comm_interface_resolution.py
- .get_config_value
- CLI
- get_class_from_string
- graphify reference: extra exports and benchmark
- test_aperture_photometry.py
- Steering: astropy IERS auto-download blocks event loop
- acquisition.py
- format_filename
- ._disconnected
- Merit
- ejabberd shaper throttling bug (xmpp_socket.erl re-arm) & fix
- configdb.py
- Plan: Make the pydantic config layer reject unknown keys (`extra="forbid"`)
- Work Plan
- Plan: `pyobs-gui` TelescopeWidget layout — width floor investigation & design notes
- PointingSeries
- GridNode
- .set_tracking_rate
- ._set_optimal_focus
- What's New in pyobs 2.0 (doc)
- New scenario: reconnect-storm (2026-07-27, production incident follow-up)
- SkyflatPriorities
- CatalogCircularMask
- .get_permitted_methods
- test_imagewatcher.py
- test_backend_archives.py
- .__call__
- show_module_info.py
- integration/conftest.py
- .set_cooling
- robotic
- Scheduler module
- BaseModel (pyobs.utils.serialization)
- Decision
- Smooth
- _DaoBackgroundRemover
- DataCache
- Plan: Widget plugin mechanism + `pyside6-deploy` packaging for `pyobs-gui`
- Plan: Split archive prefetch from CPU-bound merit evaluation, to unblock a `ProcessPoolExecutor`
- PySepStatsCalculator
- Image (pyobs.images.processors.image) API doc
- Offsets (pyobs.images.processors.offsets) API doc
- Constraint
- test_httpfilecache.py
- test_module_state_publishing.py
- WeatherStatus
- graphify reference: query, path, explain
- ._record_exception
- BufferedFile
- .retrieve_class_on_deserialization
- .__init__
- .move_heliographic_stonyhurst
- FileList
- .move_helioprojective
- .move_altaz
- pyobs 2.0 Wire Protocol, State, and Access Control design doc
- Plan: Log the loaded pyobs-* package versions at module startup
- Findings: driver/gui correctness review, all 8 repos (reviewed 2026-08-11)
- Plan: Unify TRIMSEC handling into `Image.trim()` (reconstructed)
- CHANGELOG.rst
- Use a self-hosted Keycloak alongside odin, as two parallel auth backends
- Image class
- Plan: Module observer-location capabilities (reconstructed)
- Plan: Advertise event send/subscribe role in disco#info
- reset_network
- Module.startup() lifecycle helper
- CreateFilename
- Plan: Stop scheduler constraint/merit evaluation from blocking the event loop
- .__init__
- watch_log_events_no_interest.py
- Implemented
- pyobs-gui as a standalone binary (umbrella design)
- Plan: Enforce state publishing for stateful interfaces
- Plan: `pyobs-gui` login window
- test_safe_send.py
- test_pyobsd.py
- Two-phase Object lifecycle; rationale: __init__ must not touch hardware/external services (only store params, create children, register background tasks); open() is where side effects happen, so objects can be constructed cheaply/safely before being started
- Simulation recipe (doc)
- Future
- PhotometryFocusSeries
- graphify reference: add a URL and watch a folder
- Decision
- graphify reference: commit hook and native CLAUDE.md integration
- graphify reference: incremental update and cluster-only
- .__call__
- TempFile
- robotic
- Archive (image archive base)
- ._register_exception
- Comm
- _PhotometryCalculator
- BaseVideo
- SMBFile
- ._get_next
- .__init__
- Plan: `pyobs-gui` navbar keyboard shortcuts
- filters.py
- DummyCamera
- Image.trim
- conftest.py
- Misc (pyobs.images.processors.misc) API doc
- PolymorphicBaseModel
- .get_sensor_value
- RemoteError
- .get_interfaces
- .flat_field
- test_memory_archives.py
- .move_heliocentric_polar
- MockBaseDome
- GoodWeatherEvent
- Implementation
- Plan: Interactive login/settings dialog for `pyobs-gui`, deferring `Application`'s module construction
- pyobs.modules.utils (doc)
- Plan: Add baseline tests to core-tier repos, then enable grouped Dependabot auto-merge
- Plan: CORS + token auth for `HttpFileCache`
- TaskFinishedEvent
- .grab_sequence
- Plan: `pyobs-gui` IAutoGuiding widget
- IStructuredConfig
- graphify reference: GitHub clone and cross-repo merge
- Investigation: pyobs-gui receives every LogEvent twice (SAAO/monet production)
- ._expose
- .night_obs
- graphify reference: transcribe video and audio
- MotionStatusChangedEvent
- ADR-0008: _safe_send keeps bounded retry unlike capability/subscribe fetches
- Module._watch_event_loop_lag
- Plan: Surface unrecognized kwargs in `Object.__init__` instead of silently discarding them
- pyobs.modules.image (doc)
- Plan: `pyobs-auth` + Keycloak integration
- Plan: Exception handling across the RPC boundary (reconstructed)
- Plan: Decouple `ICamera`/`IExposure` (reconstructed)
- GuidingStatisticsPixelOffset
- plans/index.md
- test_scriptrunner.py
- ModuleNameFilter
- CLAUDE.md
- Target
- extraction-spec.md
- flatfield/test_scheduler.py
- ModuleLocation dataclass (nested in ModuleCapabilities)
- check_pyobs_releases.sh
- check_ejabberd_notify.py
- .__init__
- Kiosk
- test_dummyaltaztelescope.py
- Photometry (pyobs.images.processors.photometry) API doc
- GuiApplication
- _event_role
- Any
- _dummytelescopebase.py
- .__init__
- steering/index.md
- ConfigDB
- .__init__
- .__init__
- ModuleGui
- .__init__
- .set_exposure_time
- .set_offsets_altaz
- .set_gain
- .abort
- .set_rotation
- .__init__
- pyobs.modules.weather (doc)
- ._subscribe_presence
- .__init__
- .__init__
- .__init__
- .abort
- .calibrate
- .grab_data
- .set_optimal_focus
- .set_mode
- .track_body
- README.md
- Install-ejabberd (xmpp)
- XmppComm._disconnected
- Autocompletion ()
- .track_orbital_elements
- pyobs.modules.pointing (doc)
- .add_pointing_measurement
- .run
- .run_script
- .sync_target
- .set_window
- .__init__
- reset_network
- Any
- TypedDict
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
2. `Image` - 444 edges
3. `Task` - 227 edges
4. `Interface` - 186 edges
5. `Module` - 180 edges
6. `ObservationList` - 168 edges
7. `DataProvider` - 168 edges
8. `Event` - 152 edges
9. `ImageType` - 117 edges
10. `Comm` - 113 edges

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

## Communities (458 total, 56 thin omitted)

### Community 0 - "BaseTelescope"
Cohesion: 0.04
Nodes (49): Any, StrEnum, Discrete, hardware-native tracking rate., Switches to the given tracking mode. Args: mode: Tracking mode to switch to.…, TrackingMode, BaseTelescope, Any, _ra_rate_on_sky() (+41 more)

### Community 1 - "BaseGuiding"
Cohesion: 0.07
Nodes (23): ExposureTimeState, AutoGuiding, Any, An auto-guiding system., Initializes a new auto guiding system. Args: exposure_time: Initial exposure…, Set the exposure time in seconds. Args: exposure_time: Exposure time in…, Starts/resets auto-guiding., BaseGuiding (+15 more)

### Community 2 - "Time"
Cohesion: 0.03
Nodes (99): ndarray, SkyCoord, Constraint, ndarray, SkyCoord, Returns a boolean mask of candidates passing this constraint. Default…, MoonIlluminationConstraint, Moon illumination constraint. (+91 more)

### Community 3 - "Module"
Cohesion: 0.04
Nodes (67): AbstractEventLoop, AutoFocusResult, AutoFocusState, IAutoFocus, Any, SECONDS, The module can perform an autofocus., Perform an autofocus series. This method performs an autofocus series with… (+59 more)

### Community 4 - "Interface"
Cohesion: 0.03
Nodes (119): ABC, The Comm object is responsible for all communication between modules (see…, _event_schema_to_xml(), _interface_schema_to_xml(), Element, Shared XML serializer for pyobs 2.0 (urn:pyobs:rpc:1). Both the state pub/sub…, Map a Python type hint to a (wire_type_string, unit_string|None) pair., Build the <{ns}interface> disco#info schema element for one Interface subclass. (+111 more)

### Community 5 - "test_presence.py"
Cohesion: 0.05
Nodes (52): Announce this module to already-connected peers, mirroring XmppComm's presence-…, ModuleOpenedEvent, Event to be sent when a module has opened., ModuleLocation, _FakeProxyContext, make_xmpp_comm(), asyncio, Tests for Phase 2.5 Presence and Capabilities implementation. (+44 more)

### Community 6 - "Image"
Cohesion: 0.03
Nodes (77): MetaClass, Image, CCDData, Create Image from a bytes array containing a FITS file. Args: data: Bytes array…, Create image from FITS file. Args: filename: Name of file to load image from.…, Create image from astropy.CCDData. Args: data: CCDData to create image from.…, Load Image from HDU list. Args: data: HDU list. Returns: Image., A container class for astronomical image data and associated metadata. This… (+69 more)

### Community 8 - "PyobsError"
Cohesion: 0.08
Nodes (20): Declare that the given PyobsError types (and their subclasses) fire often…, AbortedError, AcquisitionError, DeviceBusyError, GeneralError, InvalidArgumentError, ModuleError, ModuleStartingError (+12 more)

### Community 9 - "ImageProcessor"
Cohesion: 0.04
Nodes (53): Annotation processors doc, Some info about :class:`pyobs.images.Image`., ImageProcessor, The error handling mode for this step., Processes an image. Args: image: Image to process. Returns: Processed image., Resets state of image processor, Circle, Draw a circle on an image, optionally interpreting the center in WCS… (+45 more)

### Community 10 - "Any"
Cohesion: 0.07
Nodes (16): Any, Store published capabilities for inclusion in disco#info responses., Return this client's own published capabilities., Fetch and deserialize capabilities for a remote module's interface. Retries…, Subscribe to a pubsub node, retrying until the node exists. Runs as a…, Create a new XMPP Comm module. Either a fill JID needs to be provided, or a set…, Authentication failed. Args: event: XMPP event., Capped exponential backoff with full jitter. Used for retry loops that can end… (+8 more)

### Community 11 - "BaseCamera"
Cohesion: 0.06
Nodes (36): ExposureState, BaseCamera, calc_expose_timeout(), Any, Header, Set the exposure time in seconds. Args: exposure_time: Exposure time in…, Set the image type. Args: image_type: New image type., Change exposure status and send event, Args: status: New exposure status. (+28 more)

### Community 12 - "WeatherSensors"
Cohesion: 0.13
Nodes (15): Any, Return value for given sensor. Args: station: Name of weather station to get…, Set a simulated sensor's value, for use in tests and simulations. Args: sensor:…, Any, ClientSession, WeatherApi, Enumerator for sensors of a weather station. Attributes: TIME: Time of…, WeatherSensors (+7 more)

### Community 13 - "XmppComm"
Cohesion: 0.06
Nodes (23): Send XMPP presence stanza reflecting the module lifecycle state. ModuleState…, See Comm.mark_ready(). Remembers readiness on self (survives client recreation…, Called, when the module connected to this Comm changes. Args: module: The…, Open the connection to the XMPP server. Returns: Whether opening was successful., Builds full JID from a given username. Args: name: Username to build JID for.…, Returns list of interfaces for given client. Args: client: Name of client.…, Return list of interfaces for the given JID. Args: jid: JID to get interfaces…, Checks the disco#info features already cached for client for a version of… (+15 more)

### Community 14 - "_ResponseImageWriter"
Cohesion: 0.11
Nodes (10): Any, Logger, WCS, _RequestLogger, Any, WCS, astrometry.net gives a CD matrix, so we have to delete the PC matrix and the…, _ResponseImageWriter (+2 more)

### Community 15 - ".__init__"
Cohesion: 0.09
Nodes (14): Any, Create a new image watcher. Args: watchpath: Path to watch. destinations:…, Any, Creates a new image writer. Args: filename: Pattern for filename to store…, Args: label: Label for module. If None, name is used. own_comm: If True, module…, Any, Creates a new StandAlone object. Args: message: Message to log in the given…, Any (+6 more)

### Community 16 - "TimeDelta"
Cohesion: 0.04
Nodes (105): AstroplanScheduler, Any, ObservingBlock, Actually do the scheduling, usually run in a separate process., Scheduler based on astroplan., AirmassConstraint, ConstantMerit, Merit function that returns a constant value. (+97 more)

### Community 17 - "test_schedulereader.py"
Cohesion: 0.15
Nodes (21): LcoScheduleReader, Update list of requests. Args: force: Force update., Fetch schedule from portal. Returns: Dictionary with tasks. Raises: Timeout: If…, Fetch schedule from portal. Args: start_before: Task must start before this…, Returns the active scheduled task at the given time. Args: time: Time to return…, Scheduler for using the LCO portal, make_observation(), make_reader() (+13 more)

### Community 18 - "DummyRoof"
Cohesion: 0.06
Nodes (41): pyobs.modules.roof (doc), BaseDome, BaseRoof, DummyRoof, WeatherState, DummyRoof, Any, Get the percentage the roof is open. (+33 more)

### Community 19 - "mixins/test_fitsheader.py"
Cohesion: 0.06
Nodes (66): FitsHeaderMixin, ImageFitsHeaderMixin, Any, PrimaryHDU, Add requested FITS headers to header of given image. Args: image: Image with…, Add FITS header keywords to the given FITS header. Args: image: Image with…, Add FRAMENUM keyword to header Args: image: Image with header to add to., Helper methods for all modules that implement IImageGrabber. (+58 more)

### Community 20 - "Event"
Cohesion: 0.05
Nodes (42): Event, Base class for all events., DataType, TypedDict, DataType, TypedDict, DataType, TypedDict (+34 more)

### Community 21 - "PipelineMixin"
Cohesion: 0.05
Nodes (44): Handle an ImageError raised by this step, when on_error == "error". Override…, PipelineMixin, Any, Mixin for a module that needs to implement an image pipeline., Initializes the mixin. Args: steps: Pipeline steps to run on images. archive:…, Resets all previous state of the involved image processors., PipelineCamera, Any (+36 more)

### Community 22 - "AstrometryDotNet"
Cohesion: 0.06
Nodes (27): AstrometryDotNet, Any, Init new astronomy.net processor. Args: url: URL to service. source_count:…, Deprecated, use on_error instead., Find astrometric solution on given image. Writes WCSERR=1 into FITS header on…, Perform astrometric solving using an astrometry.net-compatible service. This…, _DotNetRequestBuilder, _DotNetRequest (+19 more)

### Community 23 - "test_flatfielder.py"
Cohesion: 0.08
Nodes (60): make_flatfielder(), make_observer(), make_twilight_observer(), asyncio, parametrize, Regression test for #481: median == bias_level used to raise ZeroDivisionError., Observer stub returning a constant solar altitude for every sun_altaz() call., Observer stub distinguishing the first (now) vs second (+10min) sun_altaz()… (+52 more)

### Community 24 - "LocalComm"
Cohesion: 0.06
Nodes (49): LocalComm, Store presence state and dispatch to all subscribers., Return presence state of a connected module., Returns list of currently connected clients., Send an event to other clients., LocalNetwork, ConfigAppliedState, DummyConfig (+41 more)

### Community 25 - "tests/test_events.py"
Cohesion: 0.04
Nodes (58): Comm API doc (pyobs.comm), Events API doc (pyobs.events), BadWeatherEvent, Event to be sent on bad weather., EventFactory, Create Event from a dictionary. Args: obj_dict: JSON string for event. Returns:…, ExposureStatusChangedEvent, Any (+50 more)

### Community 26 - "test_lco_http.py"
Cohesion: 0.13
Nodes (30): make_observation_archive(), make_task_archive(), Create LcoTaskArchive without background tasks or Object.__init__., Create LcoObservationArchive without background tasks or Object.__init__., make_lco_task(), asyncio, get_task returns task when found in cache., get_task returns None when task not in cache. (+22 more)

### Community 27 - "FlatFieldPointing"
Cohesion: 0.20
Nodes (10): Modules for performing flatfields. TODO: write doc, FlatFieldPointing, Any, Module for pointing a telescope., Initialize a new flat field pointing. Args: telescope: Telescope to point…, Abort current actions., make_pointing_module(), asyncio (+2 more)

### Community 28 - "SiderealTarget"
Cohesion: 0.08
Nodes (30): model_validator, Self, SkyCoord, Target, SiderealTarget, make_merit(), asyncio, transit_time should be jd0 + n*period for integer n closest to now. (+22 more)

### Community 29 - "WindowingWidget"
Cohesion: 0.05
Nodes (14): BinningWidget, DataDisplayWidget, PrimaryHDU, Slot, Select path for auto-saving., ExposeWidget, Slot, ExposureTimeWidget (+6 more)

### Community 30 - "Interfaces (pyobs.interfaces) API doc"
Cohesion: 0.04
Nodes (53): Interfaces (pyobs.interfaces) API doc, IAbortable, IAcquisition, IAutoFocus, IAutoGuiding, IAutonomous, IBinning, ICalibrate (+45 more)

### Community 31 - "test_control.py"
Cohesion: 0.08
Nodes (53): CasesRunner, Script for distinguishing cases., Returns FITS header for the current status of this module. Args: namespaces: If…, ConditionalRunner, Script for running an if condition., Returns FITS header for the current status of this module. Args: namespaces: If…, ParallelRunner, Script for running other scripts in parallel. (+45 more)

### Community 32 - "test_basetelescope.py"
Cohesion: 0.13
Nodes (26): OrbitalElements, _orbital_plane_to_ecliptic_cartesian(), _perifocal_to_radec(), _propagate_elements(), Rotates a perifocal-plane position into heliocentric ecliptic coordinates, then…, Rotates a perifocal-plane position (AU) into heliocentric ecliptic Cartesian…, Two-body Kepler propagation of orbital elements to (ra, dec) in degrees, ICRS.…, Solves M = E - e*sin(E) for the eccentric anomaly E, via Newton-Raphson. Args:… (+18 more)

### Community 33 - "Any"
Cohesion: 0.07
Nodes (16): Any, ConfigValue, Signature, Returns name of module., Parse the optional "acl" config block into _acl_allow/_acl_deny/_acl_mode.…, Expand any interface names (e.g. "ICamera") in an "allow" entry list into that…, Whether the acl policy denies `sender` calling `method`, ignoring `mode`…, Returns a dictionary with config caps. (+8 more)

### Community 34 - "Portal"
Cohesion: 0.13
Nodes (11): Portal, Any, Do a GET request on the portal. Args: url: URL to request. Returns: Response…, Clear schedule after given start time. Args: start: Start time to clear…, Submit observations. Args: observations: List of observations to submit., Send report to LCO portal Args: status_id: id of config status status: Status…, Delay re-attempt to send report to LCO portal Args: status_id: id of config…, Fetch schedule from portal. Args: start_before: Task must start before this… (+3 more)

### Community 35 - "utils/exceptions.py"
Cohesion: 0.03
Nodes (83): IDome, The module controls a dome, i.e. a :class:`~pyobs.interfaces.IRoof` with a…, Any, Returns FITS header for the current status of this module. Args: namespaces: If…, FitsHeaderEntry, IFitsHeaderBefore, Any, The module provides some additional header entries for FITS headers before some… (+75 more)

### Community 36 - "test_parallel.py"
Cohesion: 0.10
Nodes (31): Wait until all devices are in one of the given motion states. Args: abort:…, acquire_lock(), event_wait(), Lock, asyncio, _on_timeout sets TimeoutError on the future., _on_timeout is a no-op if future is already resolved., wait_all awaits all futures and returns their results. (+23 more)

### Community 37 - "_AbortableModule"
Cohesion: 0.11
Nodes (19): _AbortableModule, Any, asyncio, parametrize, Minimal test module with one guarded (non-whitelisted) RPC method., Module implementing IStartStop, whose abstract `start(**kwargs)` RPC method has…, A freshly constructed module hasn't been started yet., A regular RPC method must be rejected while the module is still STARTING. (+11 more)

### Community 38 - "_dataclass_to_xml"
Cohesion: 0.11
Nodes (18): _dataclass_to_xml(), _parse_scalar(), Any, Deserialize an XML element (produced by ``value_to_xml``) to a Python value.…, Serialize a dataclass to ``<{namespace}state>`` with plain field children. Each…, Deserialize a ``<{ns}state>`` element to a dataclass instance. Handles both…, Parse a raw text value to the given type (legacy state format fallback)., Serialize a Python value to an XML element using the pyobs vocabulary. The… (+10 more)

### Community 39 - "IPointingAltAz.py"
Cohesion: 0.07
Nodes (37): AltAzState, IPointingAltAz, The module can move to Alt/Az coordinates, usually combined with…, IPointingRaDec, Any, DEGREES, RaDecState, The module can move to RA/Dec coordinates, usually combined with… (+29 more)

### Community 40 - "ObservationList"
Cohesion: 0.02
Nodes (147): Mastermind, Any, Returns FITS header for the current status of this module. Args: namespaces: If…, Mastermind for a full robotic mode., Initialize a new auto focus system. Args: schedule: Object that can return…, Observation, ObservationList, ObservationState (+139 more)

### Community 41 - "OffsetsAltAzEvent"
Cohesion: 0.12
Nodes (13): DataTypeAltAz, DataTypeRaDec, OffsetsAltAzEvent, OffsetsEvent, OffsetsRaDecEvent, Any, TypedDict, Event to be sent when an RA/Dec offset is to be moved. (+5 more)

### Community 42 - "_SourceCatalog"
Cohesion: 0.13
Nodes (12): Any, DataFrame, floating, NDArray, Table, _SourceCatalog, test_filter_detection_flag(), test_filter_detection_flag_default() (+4 more)

### Community 43 - "Any"
Cohesion: 0.07
Nodes (18): Any, ProxyType, Returns object directly if it is of given type. Otherwise get proxy of client…, Backend hook, called when a proxy exists but doesn't implement obj_type.…, Calls proxy() in a safe way and returns None instead of raising an exception., Returns a context manager; use as `async with self.proxy(...) as x:`., Same as proxy(), but yields None inside the block instead of raising., True if a proxy of the given type can currently be resolved. Doesn't keep a… (+10 more)

### Community 44 - "test_transitimaging.py"
Cohesion: 0.07
Nodes (38): EarthLocation, model_validator, Self, SkyCoord, Merit function for observing transits., Returns the time of the next mid-transit., Returns the time until which observations should run: mid-transit + duration/2…, TransitMerit (+30 more)

### Community 45 - "robotic/test_scheduler.py"
Cohesion: 0.13
Nodes (39): Scheduler, DummyTask, make_async_gen(), make_obs(), make_scheduler(), asyncio, Regression test: _on_task_finished is registered for both TaskFinishedEvent and…, _state_for() (+31 more)

### Community 46 - "StandAlone"
Cohesion: 0.10
Nodes (38): pyobs.modules.test (doc), StandAlone, Quickstart (doc), pyobs-core (pip package), Test modules. TODO: write doc, Example module that only logs the given message forever in the given interval., Thread function for async processing., StandAlone (+30 more)

### Community 47 - ".__call__"
Cohesion: 0.33
Nodes (4): EarthLocation, SkyCoord, Take the pixel offsets stored in the meta data of the image and apply them to…, Return RA/Dec of central pixel and of central pixel plus offsets. Args: image:…

### Community 48 - "test_schedulewriter.py"
Cohesion: 0.25
Nodes (16): make_portal(), Shared helpers for LCO tests., Create Portal bypassing Object.__init__ and aiohttp session., make_configdb(), make_lco_observation(), make_writer(), asyncio, test_add_schedule_calls_portal() (+8 more)

### Community 49 - "test_stellarexptime.py"
Cohesion: 0.08
Nodes (38): WindowState, ExposureTimeProvider, Determine and return the exposure time in seconds. Returns: Exposure time in…, Abstract base class for providers that determine camera exposure time., ndarray, Find the brightest star near the image centre by fitting a 2D Gaussian. Args:…, Determines exposure time by finding a star near the image centre and adjusting…, Determine the optimal exposure time. Returns: Optimal exposure time in seconds. (+30 more)

### Community 50 - "StarExpTimeEstimator"
Cohesion: 0.07
Nodes (27): Exposure Time estimators doc, ExpTimeEstimator (exptime processor base), StarExpTimeEstimator (exptime processor), ExpTime, ExpTimeEstimator, Any, Estimate exposure time., Init new exposure time estimator. (+19 more)

### Community 51 - "RPC"
Cohesion: 0.08
Nodes (22): fault_to_xml(), params_to_xml(), Any, ClientXMPP, Element, Exception, Parse <fault> and return (exception_qualified_name, message)., RPC wrapper around XEP-0009 using pyobs 2.0 payload encoding (urn:pyobs:rpc:1). (+14 more)

### Community 52 - "WindowCapabilities"
Cohesion: 0.12
Nodes (28): ModuleCapabilities, WindowCapabilities, Returns label of module., make_module(), Minimal module stub satisfying what XmppComm needs on connect. IModule must be…, get_capabilities_from_disco(), Integration tests for Phase 2.5 Presence and Discovery. Requires a live…, LOCAL state must arrive as away presence. (+20 more)

### Community 53 - "test_shellcommand.py"
Cohesion: 0.10
Nodes (29): ParserState, Any, Enum, ShellCommand, ShellCommandResponse, asyncio, test_command_number_increments(), test_execute_invalid_param() (+21 more)

### Community 54 - "Calibration"
Cohesion: 0.08
Nodes (26): ImageProcessor on_error kwarg / per-step error handling, Additional Modules index (docs), Image processors index (docs), Astrometry processors doc, AstrometryDotNet (astrometry processor), Calibration processors doc, Calibration, Calibrate an image. Args: image: Image to calibrate. Returns: Calibrated image. (+18 more)

### Community 55 - ".get_object"
Cohesion: 0.09
Nodes (20): ObjectClass, PydanticModel, Move telescope to pointing., create_object(), get_object(), get_safe_object(), Any, ProxyType (+12 more)

### Community 56 - "Publisher"
Cohesion: 0.10
Nodes (17): Any, Measures seeing on reduced images with a catalog., Creates a new seeing estimator. Args: sources: List of sources (e.g. cameras)…, Puts a new images in the DB with the given ID. Args: event: New image event…, Seeing, LogPublisher, Any, Initialize new log publisher. Args: level: Level to log on. (+9 more)

### Community 57 - "_SepAperturePhotometry"
Cohesion: 0.15
Nodes (11): Any, floating, NDArray, Table, since SEP sums up whole pixels, we need to do the same on an image of ones for…, _SepAperturePhotometry, asyncio, fixture (+3 more)

### Community 58 - "Any"
Cohesion: 0.11
Nodes (13): ImageHDU, Any, floating, HDUList, Header, NDArray, setter, Table (+5 more)

### Community 59 - "Proxy"
Cohesion: 0.07
Nodes (23): Comm responsibility: Method calls (via Proxy), Proxy, _ProxyContext, Any, ProxyType, Signature, Execute a method on the remote client. Args: method: Name of method to call.…, Create local methods for the remote client. (+15 more)

### Community 60 - "FilenameFormatter"
Cohesion: 0.14
Nodes (13): Format filename with given formatter., FilenameFormatter, Header, Returns value for given key. Args: hdr: fits.Header to take value from. key:…, Formats a filename given a format template and a FITS header. Args: hdr: FITS…, Format a given placeholder. Args: placeholder: Placeholder to format. hdr: FITS…, Sets a given string to lowercase. Args: hdr: FITS header to take values from.…, Formats time using the given delimiter. Args: hdr: FITS header to take values… (+5 more)

### Community 61 - "test_basevideo.py"
Cohesion: 0.16
Nodes (34): ImageRequest, make_basevideo(), make_request(), asyncio, test_activate_camera_from_inactive_calls_hook(), test_activate_camera_when_already_active_skips_hook(), test_active_update_deactivates_after_sleep_timeout(), test_active_update_skips_deactivate_when_recently_active() (+26 more)

### Community 62 - "test_yaml_archives.py"
Cohesion: 0.10
Nodes (41): Any, DataFrame, HDUList, Convenience function for writing an Image to a FITS file. Args: filename: Name…, Convenience function for writing an Image to a FITS file. Args: filename: Name…, Convenience function for writing bytes to a file. Args: filename: Name of file…, Convenience function for reading a CSV file into a DataFrame. Args: filename:…, Convenience function for writing a CSV file from a DataFrame. Args: filename:… (+33 more)

### Community 63 - "Project"
Cohesion: 0.07
Nodes (16): # TODO: add abort (see old robotic/scheduler.py), Abstract base class for tasks scheduler., TaskScheduler, FileSystemTaskArchive, Any, Task archive based on files., Creates a new filesystem-based task archive. Args: extension: Extension of…, Returns time when last time any blocks changed. (+8 more)

### Community 64 - "FlatFielder"
Cohesion: 0.06
Nodes (32): ICamera, The module controls a camera., IFilters, Any, The module can change filters in a device., Set the current filter. Args: filter_name: Name of filter to set. Raises:…, ITelescope, The module controls a telescope. (+24 more)

### Community 65 - "IExposure"
Cohesion: 0.06
Nodes (34): Comm._get_client, ADR-0001: Check Interface.state by own declaration, not inheritance, Composite interfaces inheriting stateful bases (ICamera, IDome, ITelescope, ...), Interface.capabilities (ClassVar), Interface.has_own_state(), Interface.state (ClassVar), XmppComm disco#info feature registration, ADR-0006: Proxy.wait_for_state() returns None on timeout (+26 more)

### Community 66 - "Telegram"
Cohesion: 0.14
Nodes (18): CallbackContext, Any, Save storage file. Args: context: Telegram context., Is user authorized? Args: context: Telegram context. user_id: ID of user.…, Store new user in auth database. Args: context: Telegram context. user_id: ID…, Handle /start command. Args: update: Message to process. context: Telegram…, Handle /exec command. Args: update: Message to process. context: Telegram…, Handle click on buttons. Args: update: Message to process. context: Telegram… (+10 more)

### Community 67 - "benchmark_state_throughput.py"
Cohesion: 0.06
Nodes (53): BinningState, IBinning, Any, The camera supports binning, to be used together with…, Set the camera binning. Args: x: X binning. y: Y binning. Raises: ValueError:…, FlatField, Any, Enum (+45 more)

### Community 68 - "SolarElevationConstraint"
Cohesion: 0.17
Nodes (27): AtNightConstraint, Solar elevation constraint., SolarElevationConstraint, constraint(), data(), observer(), asyncio, fixture (+19 more)

### Community 69 - "Offsets"
Cohesion: 0.03
Nodes (64): AltAzOffsets, GenericOffset, OnSkyDistance, Angle, PixelOffsets, RaDecOffsets, AstrometryOffsets, CorrelationMaxCloseToBorderError (+56 more)

### Community 70 - ".now"
Cohesion: 0.08
Nodes (28): Observer, ObservationArchiveEvolution, date, Observer, Populates the task cache and the one real night (anchored to `start`) up front.…, Freezes observation cache. After this: a task-id miss raises RuntimeError; a…, Returns list of observations for the given task. Args: date: Date of night to…, SkyCoord (+20 more)

### Community 71 - "PyObsError"
Cohesion: 0.07
Nodes (31): ADR-0003: Restrict Proxy access to async with, has_proxy() / safe_proxy, Proxy, _ProxyContext.__await__ (removed), specs/design/pyobs_2_0_wire_protocol.md, acl: config block (allow/deny), ADR-0004: Enforce access control on the callee, not the caller, Module.execute() (+23 more)

### Community 72 - "test_proxy.py"
Cohesion: 0.12
Nodes (33): _cooling_state(), make_proxy(), asyncio, Methods from both interfaces are callable., A CoolingState timestamped `age_seconds` in the past., Callers that don't pass max_age see no behavior change, however old the cached…, A future interface whose State dataclass has no `time` field fails loudly at…, Create a Proxy with a mock comm. (+25 more)

### Community 73 - "XEP_0009"
Cohesion: 0.07
Nodes (13): BasePlugin, Expose method to public., Expose method to public., Expose method to public., Small fix for the original XEP_0009 plugin., Route RPC-level errors (e.g. forbidden, item-not-found) through the same…, XEP_0009, A plugin for SleekXMPP, adding a timeout to RPC calls. (+5 more)

### Community 74 - "VirtualFileSystem"
Cohesion: 0.05
Nodes (52): PrivateAttrMixin, DynamicTarget, SkyCoord, Target, Pick the best available target given current conditions. For static targets…, HeliocentricPolarTarget, Target, HelioprojectiveTarget (+44 more)

### Community 75 - "PyobsDaemon"
Cohesion: 0.14
Nodes (10): Any, PyobsDaemon, Return the bare module name from a config or PID file path., Strip a leading underscore, which marks a module as disabled. PID and log files…, Return sorted module names from *.yaml files, excluding *.shared.yaml., Read and return the PID from the module's PID file, or None., Return the live PID for a module, or None. Cleans up stale PID files., Return uptime (seconds) and rss_mb for a running PID. No CPU -- that needs a… (+2 more)

### Community 76 - "MockWeather"
Cohesion: 0.14
Nodes (22): WeatherSensorReading, MockWeather, Any, Return value for given sensor. Args: station: Name of weather station to get…, Returns FITS header for the current status of this module. Args: namespaces: If…, A mock weather station for testing and simulations., Creates a new mock weather station. Args: good: Initial weather-good state.…, Set the simulated weather-good state, for use in tests and simulations. Fires a… (+14 more)

### Community 77 - "test_config.py"
Cohesion: 0.10
Nodes (31): include_parts(), pre_process_yaml(), Any, Replaces blocks of the form {include <source.yaml> <key>} in the loaded config…, Include nested contents from another YAML file. Args: include: dictionary based…, Finds anchors ('&') in the included file. Args: filename: name of the file with…, Replaces aliases ('<<: *...') in the main file by the anchor in the included…, reload_anchors() (+23 more)

### Community 78 - "test_dummyvideo.py"
Cohesion: 0.17
Nodes (15): DummyVideo, Any, A dummy video module for testing — streams simulated noise frames., Creates a new dummy video module. Args: fps: Frames per second to simulate.…, Set the exposure time (frame interval). Args: exposure_time: Exposure time in…, Background task that generates simulated frames., make_dummyvideo(), asyncio (+7 more)

### Community 79 - "test_acquisition.py"
Cohesion: 0.20
Nodes (33): EarthLocation, Take the pixel offsets stored in the meta data of the image and apply them to…, OffsetResult, EarthLocation, Take the pixel offsets stored in the meta data of the image and apply them to…, make_acquisition(), make_camera(), make_image() (+25 more)

### Community 80 - "Weather"
Cohesion: 0.15
Nodes (24): Builds the current per-sensor readings from the last raw status, for state…, Connection to pyobs-weather., Weather, asyncio, test_active_flag_defaults_true_and_tracks_stop(), test_calc_system_init_eta(), test_get_fits_header_before(), test_get_fits_header_before_invalid() (+16 more)

### Community 81 - "CoolingState"
Cohesion: 0.18
Nodes (18): ModuleClosedEvent, Event to be sent when a module has closed., CoolingState, Integration tests for the XEP-0060 state pub/sub path. Requires a live ejabberd…, proxy.get_state(ICooling) must return the latest value without an RPC round-…, When the remote module disconnects, _client_disconnected must call…, After disconnect and reconnect, the next proxy() call must produce a fresh…, Poll *condition* until truthy or *timeout* seconds elapse. (+10 more)

### Community 82 - "ProjectionFocusSeries"
Cohesion: 0.16
Nodes (11): ProjectionFocusSeries, Any, floating, NDArray, Returns a list of data points., Fit focus from analysed images Returns: Tuple of new focus and its error, Creates a sine window function of the same size as some 1-D array "arr".…, Removes global slopes and fills up bad rows (ybad) or columns (xbad). (+3 more)

### Community 83 - ".set_focus"
Cohesion: 0.40
Nodes (4): Any, MM, Sets new focus. Args: focus: New focus value in mm. Raises:…, Sets focus offset. Args: offset: New focus offset in mm. Raises: ValueError: If…

### Community 84 - "AperturePhotometry"
Cohesion: 0.12
Nodes (11): AperturePhotometry, Any, Base class for aperture photometry processors -- not meant to be used directly,…, Do aperture photometry on given image. Args: image: Image to do aperture…, Photometry, Do aperture photometry on given image. Args: image: Image to do aperture…, Base class for photometry processors., Any (+3 more)

### Community 85 - "Ring"
Cohesion: 0.14
Nodes (9): integer, Any, floating, NDArray, Estimate pixel guiding offsets from asymmetry of spilled light around a fiber…, Init an image processor that adds the calculated offset. Args: fibers:…, Processes an image and sets x/y pixel offset to reference in offset attribute.…, Ring (+1 more)

### Community 86 - "application.py"
Cohesion: 0.22
Nodes (12): Actually run the application., Force astropy's IERS-A table and leap-second table to be loaded/downloaded now,…, _warm_iers_cache(), loaded_pyobs_packages(), Return the version of every loaded ``pyobs``-prefixed distribution. Builds the…, _fake_modules(), test_defaults_to_sys_modules(), test_excludes_non_pyobs_distributions() (+4 more)

### Community 87 - "XmppClient"
Cohesion: 0.08
Nodes (19): Any, Disconnect only, instead of slixmpp's default reconnect-in-place. xep_0199's…, Called when the server sends a <stream:error/>, e.g. when this connection gets…, Whether this client was (or is being) kicked because another session connected…, Human-readable reason text sent alongside the conflict stream error, if any., Wait for client to connect. Returns: Success or not., XMPP client for pyobs., Session start event. Args: event: The event sent at session start. (+11 more)

### Community 88 - "test_exception_logging.py"
Cohesion: 0.27
Nodes (20): Callback for flat-field class to call with statistics., FocusError, _AbortableModule, asyncio, Minimal test module whose abort() raises whatever exception it's given. Starts…, test_call_id_is_attached_to_the_exception_and_included_in_the_log_line(), test_call_id_omitted_from_log_line_when_not_given(), test_disable_exception_logging_covers_subclasses() (+12 more)

### Community 89 - "DaophotSourceDetection"
Cohesion: 0.17
Nodes (13): DaophotSourceDetection, Any, floating, NDArray, Table, Initializes a wrapper for photutils. See its documentation for details. Args:…, Find stars in given image and append catalog. Args: image: Image to find stars…, Detect astronomical point sources using a DAOPhot-style algorithm via… (+5 more)

### Community 90 - "Application"
Cohesion: 0.15
Nodes (23): Application, React to signals and quit the module., Class for initializing and shutting down a pyobs process., make_bare_application(), Any, asyncio, Tests for Application's module_factory path (see specs/plans/gui-interactive-…, Config path: _module is already set in __init__, so _main() must not touch the… (+15 more)

### Community 91 - "DummyComm"
Cohesion: 0.13
Nodes (16): DummyComm, A dummy implementation of the Comm interface., Always return zero clients., No interfaces implemented., Interfaces are never supported., Send an event to other clients. Args: event (Event): Event to send, comm(), asyncio (+8 more)

### Community 92 - "CallModuleScript"
Cohesion: 0.20
Nodes (17): CallModuleScript, Script for calling a method on a module., asyncio, fixture, script(), test_can_run_false_when_module_unavailable(), test_can_run_true_when_module_available(), test_can_run_uses_interface_for_proxy() (+9 more)

### Community 93 - "ProjectedOffsets"
Cohesion: 0.14
Nodes (20): ProjectedOffsets, Any, floating, NDArray, Processes an image and sets x/y pixel offset to reference in offset attribute.…, Project image along x and y axes and return results. Args: image: Image to…, Compute pixel offsets for guiding by correlating 1D projections of the current…, Initializes a new auto guiding system. (+12 more)

### Community 94 - "test_pyobs_archive.py"
Cohesion: 0.20
Nodes (23): PyobsArchiveFrameInfo, Frame info for pyobs archive., make_archive(), make_frame_dict(), MockResponse, Any, asyncio, test_download_frames_returns_images() (+15 more)

### Community 95 - "HttpFile"
Cohesion: 0.10
Nodes (18): ArchiveFile, Wraps a file in an archive. To be used in combination with pyobs-archive., Creates a new archive file. Args: name: Name of file. mode: Open mode (r/w).…, If in write mode, actually send the file to the archive., HttpFile, Any, Read number of bytes from stream. Args: n: Number of bytes to read. Read until…, Write data into the stream. Args: s: Bytes of data to write. (+10 more)

### Community 96 - "Object"
Cohesion: 0.03
Nodes (96): PydanticBaseModel, Object, :class:`~pyobs.object.Object` is the base for almost all classes in *pyobs*. It…, Base class for all objects in *pyobs*., Whether object has been opened., Can be overloaded to quit program., Any, AcquisitionConfig (+88 more)

### Community 97 - "InfluxHandler"
Cohesion: 0.28
Nodes (4): InfluxHandler, Any, LogRecord, WriteOptions

### Community 98 - "FocusSeries"
Cohesion: 0.11
Nodes (22): AutoFocusPoint, fit_hyperbola(), Fit a hyperbola Args: x_arr: X data y_arr: Y data y_err: Y errors Returns:…, FocusSeries, Analyse given image. Args: image: Image to analyse focus_value: Value to fit…, Returns a list of data points., Fit focus from analysed images Returns: Tuple of new focus and its error, Base class for focus series helper classes. (+14 more)

### Community 99 - "SepSourceDetection"
Cohesion: 0.16
Nodes (17): Background, Any, floating, NDArray, Initializes a wrapper for SEP. See its documentation for details. Highly…, Find stars in given image and append catalog. Args: image: Image to find stars…, Remove background from image in data. Args: data: Data to remove background…, Detect astronomical sources using SEP (Source Extractor for Python). This… (+9 more)

### Community 100 - "make_proxy_cm"
Cohesion: 0.21
Nodes (27): make_proxy_cm(), Wrap value in a MagicMock standing in for the async context manager returned by…, make_flatfield(), asyncio, Find the state object set_state() was called with for the given interface., _ready_telescope(), _state_for(), test_abort_sets_event() (+19 more)

### Community 101 - "test_autoguiding.py"
Cohesion: 0.20
Nodes (32): make_guiding(), make_image(), asyncio, _state_for(), test_auto_guiding_sleeps_when_disabled(), test_auto_guiding_takes_and_processes_image_when_enabled(), test_get_fits_header_after_includes_statistics(), test_get_fits_header_before_reports_closed_loop() (+24 more)

### Community 102 - "timeout"
Cohesion: 0.07
Nodes (25): F, ConfigCapabilities, A module in *pyobs* is the smalles executable unit. The base class for all…, MultiModule, raises(), Wait until all sub-module tasks have finished., Cancel sub-module tasks and close shared objects., Quit all sub-modules. (+17 more)

### Community 103 - "ResolvableErrorLogger"
Cohesion: 0.17
Nodes (9): Any, Creates a new LCO scheduler. Args: url: URL to portal site: Site filter for…, Any, Logger, Logging for resolvable errors. Args: logger: Logger to use. error_level: Log…, Log an error message., ResolvableErrorLogger, create_logger() (+1 more)

### Community 104 - "test_coordinates.py"
Cohesion: 0.15
Nodes (25): offset_altaz_to_radec(), offset_radec_to_altaz(), EarthLocation, SkyCoord, make_altaz(), make_radec(), SkyCoord, Zero offset returns (0, 0). (+17 more)

### Community 105 - "get_registered_interface"
Cohesion: 0.10
Nodes (23): get_registered_interface(), Look up a registered interface class by name, or None if unknown., All currently-registered interface classes, keyed by name., registered_interfaces(), List interfaces and methods of this module., Tests for the import-time interface registry in pyobs/interfaces/interface.py.…, Re-importing the same interface module twice resolves to the same class object…, Two genuinely different classes claiming the same name must raise TypeError… (+15 more)

### Community 106 - "What You Must Do When Invoked"
Cohesion: 0.08
Nodes (24): For /graphify add and --watch, For /graphify query, For the commit hook and native CLAUDE.md integration, For --update and --cluster-only, /graphify, Honesty Rules, Interpreter guard for subcommands, Part A - Structural extraction for code files (+16 more)

### Community 107 - "LocalArchive"
Cohesion: 0.33
Nodes (25): LocalArchive, Connector class to a local image archive., make_frame_headers(), asyncio, Path, test_download_frames_loads_real_files(), test_download_frames_skips_frames_without_filename(), test_download_headers_returns_header_dicts() (+17 more)

### Community 108 - "Plan: Systematic ejabberd throughput/latency benchmarking"
Cohesion: 0.11
Nodes (17): Blockers found while getting the environment working (2026-07-27), Conclusion on the O(N²) finding: real bug, not a pyobs design problem, Deeper dig: isolating the real mechanism (2026-07-27, same day), Environment, First real results (2026-07-27), Goals — questions this benchmark should answer, Harness location, Measurement approach (+9 more)

### Community 109 - "_PhotUtilAperturePhotometry"
Cohesion: 0.17
Nodes (10): _PhotUtilAperturePhotometry, Table, PhotUtilsPhotometry, Any, Perform photometry using PhotUtils., test_init(), asyncio, test_call_const() (+2 more)

### Community 110 - "Mixins (pyobs.mixins) API doc"
Cohesion: 0.09
Nodes (25): Images (pyobs.images) API doc, ImageProcessor base class, Object base class, Pipeline module (pyobs.modules.image.Pipeline), API index (toctree), ICamera, IStartStop, CameraSettingsMixin (+17 more)

### Community 111 - "Script base class"
Cohesion: 0.09
Nodes (25): IMode, TaskData, AutoFocusScript, CallModuleScript, CasesRunner, ConditionalRunner, ConstSkyflatPriorities, DarkBiasScript (+17 more)

### Community 112 - "test_background_task.py"
Cohesion: 0.17
Nodes (19): BackgroundTask, Any, make_task(), asyncio, Too many fast failures calls parent.quit() when restart=True., Too many fast failures with restart=False just stops without calling quit., Failures spread over time don't trigger the rapid-failure quit., test_cancelled_error_exits_cleanly() (+11 more)

### Community 113 - "Test Commlogging (comm)"
Cohesion: 0.12
Nodes (20): Send an event to all connected modules. Args: event: Event to send.…, CommLoggingHandler, Any, A logging handler that sends all messages through a Comm module., Create a new logging handler. Args: comm: Comm module to use., Send a new log entry to the comm module. Args: rec: Log record to send., comm(), handler() (+12 more)

### Community 114 - "test_imagewriter.py"
Cohesion: 0.47
Nodes (11): make_image_event(), make_writer(), asyncio, test_process_event_accepts_all_when_no_filter(), test_process_event_accepts_listed_source(), test_process_event_filters_by_source(), test_process_event_queues_filename(), test_process_event_rejects_wrong_type() (+3 more)

### Community 115 - "test_dummyradectelescope.py"
Cohesion: 0.24
Nodes (21): TrackingRateCapabilities, make_dummyradectelescope(), asyncio, test_move_altaz_clears_tracked_body(), test_move_altaz_resets_tracking_mode_to_off(), test_move_radec_clears_tracked_body(), test_move_radec_resets_tracking_mode_to_sidereal(), test_move_task_applies_tracking_rate_to_position() (+13 more)

### Community 116 - "ImagingScript"
Cohesion: 0.17
Nodes (9): ImagingScript, InstrumentConfig, Any, Target, Run script. Raises: InterruptedError: If interrupted, Returns FITS header for the current status of this module. Args: namespaces: If…, Return the exposure time, computing it dynamically if needed., Default script for imaging configs. (+1 more)

### Community 117 - "HttpFileCache"
Cohesion: 0.15
Nodes (9): HttpFileCache, Response, Handles OPTIONS access to /{filename} for CORS preflight requests. Args:…, Handles GET access to /{filename} and returns image. Args: request: Request to…, Handles PUSH access to /, stores image and returns filename. Args: request:…, A file cache based on a HTTP server., Whether the server is started., Raises HTTPUnauthorized if a token is configured and the request doesn't carry… (+1 more)

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
Cohesion: 0.13
Nodes (24): OptimalFocusState, FocusModel, MissingSensorError, The weather station returned an invalid/missing reading -- plausibly transient,…, Receive FocusFoundEvent. Args: event: The event itself sender: The name of the…, The configured sensor name isn't in the responding module's temperature data --…, Calculate new focus model from saved entries., A focus model that is automatically applied to an IFocuser. If, e.g., the model… (+16 more)

### Community 125 - "._expose"
Cohesion: 0.22
Nodes (5): Actually do the exposure, should be implemented by derived classes. Args:…, Method that is always called at the very beginning of __expose and can be used…, Wrapper for a single exposure. Args: exposure_time: The requested exposure time…, Add FITS headers in derived classes. Args: image: Image to write FITS headers…, If the telescope has a meridian flip (MERIDIAN keyword in header), flip the…

### Community 126 - "ImageSourceFilter"
Cohesion: 0.12
Nodes (17): ImageSourceFilter, Any, floating, NDArray, Table, Filters the source table after pysep detection has run Args:…, Filter a source catalog by border distance, quality metrics, and brightness,…, Convert from FITS to numpy conventions for pixel coordinates. (+9 more)

### Community 127 - "test_darkbias.py"
Cohesion: 0.23
Nodes (19): DarkBiasScript, Script for running darks or biases., Whether this config can currently run. Returns: True if script can run now., Run script. Raises: InterruptedError: If interrupted, make_camera(), make_script(), asyncio, Create a mock camera supporting all or some interfaces. (+11 more)

### Community 128 - "TaskData"
Cohesion: 0.03
Nodes (64): datetime, Estimate duration of the dark/bias series., PointingScript, Script for pointing the telescope for flats., Whether this config can currently run. Returns: True if script can run now., Run script. Raises: InterruptedError: If interrupted, Estimate duration of slewing to the flat-field pointing., # TODO: get a better estimate for slewing (+56 more)

### Community 129 - "Archive"
Cohesion: 0.10
Nodes (31): ProgressEvent, Archive, Base class for image archives., Pipeline, Any, Create master bias frame. Args: images: List of raw bias frames. Returns:…, Create master dark frame. Args: images: List of raw dark frames. bias: Bias…, Create master flat frame. Args: images: List of raw flat frames. bias: Bias… (+23 more)

### Community 130 - "Plan: pyobs-pipeline"
Cohesion: 0.08
Nodes (24): Celery task, Consequences, Django models, Implementation checklist, Log viewing, Open questions, Pages, Pipeline builder (+16 more)

### Community 131 - "Test Localcomm (local)"
Cohesion: 0.18
Nodes (22): make_comm(), asyncio, fixture, Sender also receives its own events., Reset LocalNetwork singleton between tests., #677: a late-joining module must announce itself via ModuleOpenedEvent once…, get_interfaces returns [] when the remote client has no module., reset_network() (+14 more)

### Community 132 - "ImageWatcher"
Cohesion: 0.17
Nodes (8): CurrentFile, ImageWatcher, Add a file to the file queue. Args: filename (str): Local filename of new file., Can be overwritten by derived classes to do extra processing on files. All…, Can be overwritten by derived classes to do clean up after successful copying.…, Watch for new files and write them to all given destinations. Watches a path…, Modules for image operations. TODO: write doc, test_constructor_raises_without_destinations()

### Community 133 - ".__init__"
Cohesion: 0.15
Nodes (8): EarthLocation, Observer, Location of the observer, derived from :attr:`observer` (there is no separately…, .. note:: Objects must always be opened and closed using…, Initialize a new scheduler. Args: twilight: astronomical or nautical, Any, Initialize a new flat fielder. Args: functions: Function f(h) for each filter…, tzinfo

### Community 134 - "test_camerasettings.py"
Cohesion: 0.42
Nodes (9): make_camera_proxy(), make_module(), asyncio, Minimal concrete module for exercising CameraSettingsMixin in isolation., Capabilities for a Proxy are fetched in the background (see…, SettingsModule, test_raises_when_capabilities_never_arrive(), test_sets_binning_before_window() (+1 more)

### Community 135 - "test_dummymode.py"
Cohesion: 0.32
Nodes (13): _event_of_type(), make_dummymode(), asyncio, Find the most recent state object set_state() was called with for the given…, Find the send_event() call with an event of the given type., _state_for(), test_init_default_modes(), test_init_park_stop_motion_are_noops() (+5 more)

### Community 136 - "SkyFlatsBasePointing"
Cohesion: 0.17
Nodes (8): Move telescope. Args: telescope: Telescope to use., Base class for flat pointings., SkyFlatsBasePointing, model_validator, Self, Static flat pointing., Move telescope. Args: telescope: Telescope to use., SkyFlatsStaticPointing

### Community 137 - "test_autofocus.py"
Cohesion: 0.27
Nodes (18): isinstance_class(), Shared test-double helpers used across multiple test modules., Build a fresh class purely for isinstance() checks against a MagicMock.…, make_autofocus(), make_script(), make_task(), make_telescope(), asyncio (+10 more)

### Community 138 - "Grid"
Cohesion: 0.09
Nodes (21): AvoidMoon, GridFilter, Any, RandomizeGrid, Initialize the conversion filter. Args: grid: Upstream grid or filter that…, Abstract base class for grid filters that wrap another GridNode. A GridFilter…, Initialize the frame conversion filter. Args: grid: Upstream grid or filter…, Randomize iteration order by rotating the underlying sequence. For each… (+13 more)

### Community 139 - "test_kiosk.py"
Cohesion: 0.24
Nodes (21): _cancel_after(), _make_image(), make_kiosk(), asyncio, Side effect that raises CancelledError starting from the n-th call., test_camera_thread_captures_and_adjusts_exposure_time(), test_camera_thread_clips_exposure_time_to_minimum(), test_camera_thread_continues_on_file_not_found() (+13 more)

### Community 140 - "pyobs.py"
Cohesion: 0.15
Nodes (8): main(), Any, PyobsCLI, Start process as a daemon. Args: pid_file: Name of PID file., Class for initializing and running pyobs CLI., Returns pyobs version of module., React to other modules connecting., version()

### Community 141 - "Robotic recipe (doc)"
Cohesion: 0.17
Nodes (21): pyobs.modules.robotic (doc), Mastermind (module), PointingSeries, Scheduler (module), ScriptRunner, Robotic recipe (doc), AirmassConstraint, BackendObservationArchive (+13 more)

### Community 142 - "is_valid_jid"
Cohesion: 0.21
Nodes (6): is_valid_jid(), Whether jid is a valid user@domain or user@domain/resource JID -- exactly what…, JID parsing/validation in XmppComm.__init__ and the reusable is_valid_jid()…, The actual production bug this was found from: a JID ending in "/" with nothing…, re.match alone doesn't anchor the end -- confirms the pattern is anchored so…, TestIsValidJid

### Community 143 - "test_basecamera.py"
Cohesion: 0.18
Nodes (15): asyncio, parametrize, DummyCamera's _expose() must raise AbortedError, not some guessed builtin, when…, Test basic open/close of BaseCamera., #547: BaseCamera must abort on BadWeatherEvent., #547: a BadWeatherEvent must actually trigger abort() -- exposure + any running…, #672: a BadWeatherEvent must not interrupt a dark/bias sequence -- the shutter…, Test the methods for remaining exposure time and progress. (+7 more)

### Community 144 - "test_config_schema.py"
Cohesion: 0.20
Nodes (22): ConfigFieldSchema, ConfigSchema, dataclass_to_schema(), _field_schema(), Any, _pydantic_field_schema(), pydantic_to_schema(), Recursively derive a ConfigSchema from a dataclass type. Handles: plain scalars… (+14 more)

### Community 145 - "ImageType"
Cohesion: 0.09
Nodes (19): _CalibrationCache, Any, Init a new image calibration pipeline step. Args: archive: Archive to fetch…, Any, Set the image type. Args: image_type: New image type., LcoDefaultScript, Returns FITS header for the current status of this module. Args: namespaces: If…, Default script for LCO configs. (+11 more)

### Community 146 - "Scheduler"
Cohesion: 0.14
Nodes (8): Any, Compares two lists of tasks and returns two lists, containing those that are…, Trigger a re-schedule., Re-schedule when task has started and we can predict its end. Args: event: The…, Reset current task, when it has finished or failed. Args: event: The task…, Re-schedule on incoming good weather event. Args: event: The good weather…, Initialize a new scheduler. Args: scheduler: Scheduler to use. tasks: Task…, Scheduler

### Community 147 - "RollingTimeAverage"
Cohesion: 0.10
Nodes (24): Any, Runs an async callable to completion on a dedicated worker thread, off the…, run_cpu_bound(), RollingTimeAverage, _T, asyncio, test_run_cpu_bound_propagates_exception(), test_run_cpu_bound_returns_value() (+16 more)

### Community 148 - "SkyOffsets"
Cohesion: 0.05
Nodes (36): BaseCoordinateFrame, IN, OUT, Angle, SkyCoord, Returns separatation between both coordinates, either in their own or a given…, Calculates spherical offset from first coordinate to second. Args: frame:…, Args: frame: Coordinate frame to use, or None to use coordinates' own frames.… (+28 more)

### Community 149 - "LogScript"
Cohesion: 0.20
Nodes (12): DebugTriggerScript, Script for a debug trigger., LogScript, Script for logging something., asyncio, Expression has access to 'now' as a datetime., test_debug_trigger_can_run(), test_debug_trigger_sets_triggered() (+4 more)

### Community 151 - "`OBSNUM`: per-night observation counter in FITS headers"
Cohesion: 0.06
Nodes (28): 1. Event-driven frame delivery, not polling, 2. Backpressure: latest-frame-wins, not a queue, 3. Wire format (new — nothing in pyobs streams raw binary today), 4. Capability advertisement: `mjpeg`/`raw`, both `str | None`, on by default, 5. Activate/deactivate wiring, Alternatives considered, `BaseVideo`: raw-frame streaming endpoint, alongside the existing MJPEG live view, Constraint: one module, one job (+20 more)

### Community 152 - "3rd party packages (doc)"
Cohesion: 0.11
Nodes (20): 3rd party packages (doc), Astroplan, Astropy, Astroquery, Cython, LMFIT, matplotlib, NumPy (+12 more)

### Community 153 - "sourcedetection.py"
Cohesion: 0.16
Nodes (11): Source Detection processors doc, DaophotSourceDetection (detection processor), SepSourceDetection (detection processor), Any, Detect a disk on image. Args: image: Image to use. Returns: Image with new FITS…, Detect a roughly circular bright disk by thresholding and distance transform.…, Init a new simple disk processor. Args: threshold: Threshold to determine if a…, SimpleDisk (+3 more)

### Community 154 - "SSHFile"
Cohesion: 0.12
Nodes (12): Any, VFS wrapper for a file that can be accessed over a SFTP connection., Write data into the stream. Args: b: Bytes of data to write., If in write mode, actually send the file to the SSH server., Returns content of given path. Args: path: Path to list. kwargs: Parameters for…, Open/create a file over a SSH connection. Args: name: Name of file. mode: Open…, For read access, download the file into a local buffer. Raises:…, Read number of bytes from stream. Args: n: Number of bytes to read. Read until… (+4 more)

### Community 155 - "create_rst.py"
Cohesion: 0.33
Nodes (18): create_image_processors_rst(), create_modules_rst(), create_rst_overview(), create_utils_rst(), find_classes_in_modules(), find_python_modules(), find_submodules(), Any (+10 more)

### Community 156 - "Any"
Cohesion: 0.12
Nodes (7): Any, Store capabilities locally., Return this client's own published capabilities., Fetch capabilities from a remote module., Execute a given method on a remote client., Publish state locally and dispatch to subscribers., Subscribe to state updates from a remote module.

### Community 157 - "SoftBin"
Cohesion: 0.16
Nodes (11): Any, floating, NDArray, Bin a 2D image by averaging non-overlapping blocks, updating relevant FITS…, Init a new software binning pipeline step. Args: binning: Binning to apply to…, Bin an image. Args: image: Image to bin. Returns: Binned image., SoftBin, asyncio (+3 more)

### Community 158 - "AddMask"
Cohesion: 0.21
Nodes (13): AddMask, Any, floating, NDArray, Add mask to image. Args: image: Image to add mask to. Returns: Image with mask, Attach a precomputed mask to an image based on instrument and binning. This…, Init an image processor that adds a mask to an image. Args: masks: Dictionary…, asyncio (+5 more)

### Community 159 - "FrameInfo"
Cohesion: 0.11
Nodes (12): FrameInfo, Base class for frame infos., Any, TypedDict, PyobsArchive, PyobsArchiveFrameInfoDict, Connector class to running pyobs-archive instance., test_build_query_empty_when_nothing_given() (+4 more)

### Community 160 - "SkyCoord"
Cohesion: 0.13
Nodes (9): SkyCoord, Return the next point that satisfies all constraints. Iterates underlying…, Convert the next tuple to a SkyCoord. Expects a tuple (x_deg, y_deg) from the…, Transform the next SkyCoord to the target frame. Returns: A SkyCoord…, Yield a point after rotating the underlying grid a random number of times.…, Yield a point after rotating the underlying grid a random number of times.…, Yield the point from the CSV closest to the next grid point. Returns: A point…, Fetch the next point from the underlying grid. Returns: The next point from the… (+1 more)

### Community 161 - "comm/test_events.py"
Cohesion: 0.18
Nodes (15): asyncio, Tests for Comm.register_event / unregister_event. Covers…, Two independent subscribers for the same event: one tearing down must not un-…, A module that both sends an event (handler-less register_event()) and…, unregister must mirror the exact same derived-events expansion register_event…, Two independent subscribers (e.g. two widget instances for the same event type)…, Once the last handler for an event is unregistered, the event must no longer be…, test_unregister_event_drops_subscribed_role_when_last_handler_removed() (+7 more)

### Community 162 - "NewSpectrumEvent"
Cohesion: 0.14
Nodes (11): NewSpectrumEvent, Any, Event to be sent on a new image., Initializes new NewSpectrumEvent. Args: filename: Name of new image file., HDUList, Store spectrum at given destination. Can be overwritten by derived classes to…, Actually do the exposure, should be implemented by derived classes. Args:…, Wrapper for a single exposure. Args: broadcast: Whether or not the new image… (+3 more)

### Community 163 - "LogEvent"
Cohesion: 0.08
Nodes (15): LogEvent, Event for log entries., FluentLogger, Any, Log to fluentd server., Initialize a new logger. Args: hostname: Hostname of server. port: Port of…, Process a new log entry. Args: event: The log event. sender: Name of sender., Utilities TODO: write doc (+7 more)

### Community 164 - "._filter_data"
Cohesion: 0.24
Nodes (3): Any, DataFrame, Update files in root directory.

### Community 165 - "ExpTimeEval"
Cohesion: 0.11
Nodes (15): ExpTimeEval, Any, Observer, Return list of binnings., Return list of filters., Estimate exposure time for given filter Args: solalt: Solar altitude. binning:…, Initialize object with the given time. Args: time: Start time for all further…, Estimates exposure time for a given filter and binning at a given time offset… (+7 more)

### Community 166 - "Stellarium"
Cohesion: 0.14
Nodes (8): BaseTransport, Any, Exception, Send coordinates to clients., A stellarium telescope., Initialize a new stellarium telescope proxy. Args: telescope: Name of telescope…, Stellarium, StellariumProtocol

### Community 167 - "Overview (doc)"
Cohesion: 0.18
Nodes (17): Overview (doc), Access control (ACL), Comm, Events, Interface, Module (base class), Object (base class), Location / astroplan.Observer (+9 more)

### Community 168 - "TaskStartedEvent"
Cohesion: 0.16
Nodes (9): Any, Event to be sent when a task has started., Initializes a new task started event. Args: name: Name of task that just…, TaskStartedEvent, test_task_started_invalid_name(), test_task_started_missing_id(), test_task_started_no_eta(), test_task_started_properties() (+1 more)

### Community 169 - "fits.py"
Cohesion: 0.22
Nodes (12): fitssec(), parse_section_bounds(), Any, NDArray, Parse a FITS section keyword (e.g. TRIMSEC) into 0-based, half-open slice…, Trim an image to TRIMSEC or BIASSEC. Args: hdu: HDU to take data from. keyword:…, DummyHdu, test_fitssec_no_keyword() (+4 more)

### Community 170 - ".can_run"
Cohesion: 0.16
Nodes (9): Any, Target, Creates a new LCO task runner. Args: scripts: External scripts, Run a task. Args: task: Task to run target: Resolved target for this specific…, Checks whether this task could run now. Args: task: Task to run target:…, Get config script for given configuration. Args: request: LCO request. Returns:…, Target, Checks, whether this task could run now. Args: task: Task to run target:… (+1 more)

### Community 171 - "Scheduler"
Cohesion: 0.11
Nodes (14): Iterator for scheduler items, Iterate over scheduler items, Return schedule item., Find a possible slot for a given filter/binning in the given schedule Args:…, A single item in the flat scheduler, Checks, whether a new scheduler item would overlap an existing item Args:…, Initializes a new scheduler item Args: start: Start time in seconds end: End…, Nice string representation for item (+6 more)

### Community 172 - "test_grab_sequence.py"
Cohesion: 0.29
Nodes (16): make_camera(), asyncio, Tests for BaseCamera.grab_sequence()/abort_sequence(), the IDataSequence…, grab_sequence() must not block for the whole sequence -- see design doc: a…, test_abort_clears_running_sequence(), test_abort_cuts_delay_short(), test_abort_sequence_cuts_delay_short(), test_abort_sequence_lets_current_grab_finish_but_stops_the_rest() (+8 more)

### Community 173 - "binding.py"
Cohesion: 0.23
Nodes (8): fault2xml(), py2xml(), Any, Element, rpcbase64, rpctime, xml2fault(), xml2py()

### Community 174 - "test_comm_interface_resolution.py"
Cohesion: 0.29
Nodes (8): Converts a list of interface names to interface classes. Args: interfaces: list…, LogCaptureFixture, Tests for Comm._interface_names_to_classes -- the base-Comm chokepoint that…, An interface defined entirely outside pyobs.interfaces resolves the same way…, test_resolves_external_interface(), test_resolves_known_and_skips_unknown_in_same_list(), test_resolves_known_core_interfaces(), test_skips_unknown_name()

### Community 175 - ".get_config_value"
Cohesion: 0.40
Nodes (4): Any, ConfigValue, Returns current value of config item with given name. Args: name: Name of…, Sets value of config item with given name. Args: name: Name of config item.…

### Community 176 - "CLI"
Cohesion: 0.16
Nodes (9): CLI, Initializes a new instance of the CLI class., Overwrite this to set CLI parameters with argparse., Overwrite this to actually run the CLI., Load config from config file, Load config from environment variables., main(), PyobsDaemonCLI (+1 more)

### Community 177 - "get_class_from_string"
Cohesion: 0.20
Nodes (6): Any, get_class_from_string(), Get class from a given string. Args: class_name: Name of class as string.…, _build_params_model(), _get_valid_param_names(), model_validator

### Community 178 - "graphify reference: extra exports and benchmark"
Cohesion: 0.22
Nodes (8): graphify reference: extra exports and benchmark, Step 6b - Wiki (only if --wiki flag), Step 7 - Neo4j export (only if --neo4j or --neo4j-push flag), Step 7a - FalkorDB export (only if --falkordb or --falkordb-push flag), Step 7b - SVG export (only if --svg flag), Step 7c - GraphML export (only if --graphml flag), Step 7d - MCP server (only if --mcp flag), Step 8 - Token reduction benchmark (only if total_words > 5000)

### Community 179 - "test_aperture_photometry.py"
Cohesion: 0.26
Nodes (9): MockPhotometryCalculator, asyncio, QTable, AperturePhotometry.__init__ is abstract -- concrete calculators…, test_call_invalid_catalog(), test_call_invalid_data(), test_call_invalid_pixelscale(), test_call_valid() (+1 more)

### Community 180 - "Steering: astropy IERS auto-download blocks event loop"
Cohesion: 0.32
Nodes (8): BaseTelescope._celestial / _update_celestial_headers, Steering: astropy IERS auto-download blocks event loop, iers_offline config flag (stopgap fix), Steering: Blocking vendor SDK calls must never run directly on the event loop, _run_blocking() pattern (pyobs_aravis.araviscamera.AravisCamera), _wait_for_frame() tight-poll wrapper pattern, Steering: OnDemandScheduler.evolve() uncached sunset lookup stalls event loop, ObservationArchiveEvolution.evolve() Time.night_obs() bug (fixed via memoization)

### Community 181 - "acquisition.py"
Cohesion: 0.05
Nodes (46): AcquisitionAttempt, AcquisitionResult, AcquisitionState, IAcquisition, Any, The module can acquire a target, usually by accessing a telescope and a camera., Acquire target at given coordinates. If no RA/Dec are given, start from current…, CameraSettingsMixin (+38 more)

### Community 182 - "format_filename"
Cohesion: 0.19
Nodes (10): ImageWriter, Writes new images to disk., Puts a new images in the DB with the given ID. Args: event: New image event…, format_filename(), Formats a filename given a format template and a FITS header. Args: hdr: FITS…, test_date_obs(), test_default(), test_filter() (+2 more)

### Community 183 - "._disconnected"
Cohesion: 0.14
Nodes (7): Sleep a little and reconnect, Reset connection after disconnect., If a new client connects, add it to list. Args: msg: XMPP message., Call every presence callback registered for a module, isolating failures. A…, Handle presence changes from already-connected modules., If a new client disconnects, remove it from list. Args: msg: XMPP message., If a new client disconnects, remove it from list. Args: jid: JID that got…

### Community 184 - "Merit"
Cohesion: 0.15
Nodes (15): AfterTimeMerit, BeforeTimeMerit, ConstantMerit, DataProvider, FollowMerit, IntervalMerit, ObservationArchiveEvolution wraps ObservationArchive with per-run caching (avoid repeated HTTP requests) and lookahead simulation (evolve() records tentative future assignments so IntervalMerit/PerNightMerit see them and avoid double-scheduling within one run), Merit (+7 more)

### Community 185 - "ejabberd shaper throttling bug (xmpp_socket.erl re-arm) & fix"
Cohesion: 0.21
Nodes (12): XMPP/ejabberd diagnostics recipe (doc), benchmark_state_throughput.py, check_ejabberd_notify.py, delete_pubsub_nodes.py, list_pubsub_nodes.py, Comparing shaper configs (rationale), show_module_info.py, scripts/xmpp/install-ejabberd.sh (+4 more)

### Community 186 - "configdb.py"
Cohesion: 0.21
Nodes (13): Camera, CameraType, ConfigurationType, Enclosure, Instrument, InstrumentType, Mode, ModeType (+5 more)

### Community 187 - "Plan: Make the pydantic config layer reject unknown keys (`extra="forbid"`)"
Cohesion: 0.25
Nodes (7): Decision, Implementation checklist, Latent bug this surfaced (separate from the above), Open questions, Plan: Make the pydantic config layer reject unknown keys (`extra="forbid"`), Problem, What breaks, and how to fix each

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

### Community 192 - ".set_tracking_rate"
Cohesion: 0.50
Nodes (3): ARCSEC_PER_SEC, Any, Sets an absolute tracking rate on the sky, in arcsec/sec. Args: ra_rate: Rate…

### Community 193 - "._set_optimal_focus"
Cohesion: 0.12
Nodes (13): FocusTimeoutError, Any, DataFrame, floating, NDArray, Initialize a focus model. Args: focuser: Name of focuser. weather: Name of…, Returns the optimal focus. Args: filter_name: If given, use this filter name…, Retrieve all required values for the model. Returns: Dictionary containing all… (+5 more)

### Community 194 - "What's New in pyobs 2.0 (doc)"
Cohesion: 0.15
Nodes (14): What's New in pyobs 2.0 (doc), ACL feature (2.0), Capabilities and versioned discovery, Exception handling redesign, External-package interfaces, ICamera/ISpectrograph no longer imply IExposure, IDataSequence, InvocationError / SevereError retired (+6 more)

### Community 195 - "New scenario: reconnect-storm (2026-07-27, production incident follow-up)"
Cohesion: 0.18
Nodes (11): Fifth investigation session (2026-07-28, same day) — found the specific mechanism: an un-re-armed passive socket, Fourth live run (2026-07-28, same day) — found the actual mechanism: stuck per-connection Recv-Q on ejabberd's side, Full incident timeline and what's been ruled out (2026-07-27), New scenario: reconnect-storm (2026-07-27, production incident follow-up), Reproduced live with real modules on iag50srv (2026-07-28) — root cause still open, but the incident is real and reproducible, Runbook executed against iag50srv itself (2026-07-28), Runbook for tomorrow: run `late-joiner` and `reconnect-storm` against both `iag50srv` and monet-south, Second live run (2026-07-28, same day) — likely root cause found: `mod_client_state` (CSI, XEP-0352) (+3 more)

### Community 196 - "SkyflatPriorities"
Cohesion: 0.27
Nodes (6): ArchiveSkyflatPriorities, Calculate flat priorities from an archive., Base class for sky flat priorities., SkyflatPriorities, ConstSkyflatPriorities, Constant flat priorities.

### Community 197 - "CatalogCircularMask"
Cohesion: 0.18
Nodes (9): CatalogCircularMask, Any, NDArray, Table, Init an image processor that masks out everything except for a central circle.…, Remove everything outside the given radius from the image. Args: image: Image…, Filter a source catalog by keeping only entries inside a central circle (or…, asyncio (+1 more)

### Community 198 - ".get_permitted_methods"
Cohesion: 0.40
Nodes (3): Any, Reset error of module, if any., Returns names of all methods the calling module is allowed to invoke on this…

### Community 199 - "test_imagewatcher.py"
Cohesion: 0.33
Nodes (15): make_fits_bytes(), make_read_write_ctx(), make_watcher(), asyncio, On write failure the file is re-queued and remove is NOT called., test_add_file_queues_filename(), test_add_file_respects_pattern(), test_add_file_skips_non_matching_pattern() (+7 more)

### Community 200 - "test_backend_archives.py"
Cohesion: 0.06
Nodes (71): BackendTaskArchive, Any, ClientSession, Returns the task with the given ID. Returns: Task with given ID., Task archive based on pyobs-robotic-backend., Creates a new task archive. Args: url: URL of pyobs-robotic-backend. token:…, Opens the backend task archive., Closes the backend observation archive. (+63 more)

### Community 201 - ".__call__"
Cohesion: 0.38
Nodes (5): ApertureMask, CircularAperture, Any, floating, NDArray

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

### Community 210 - "_DaoBackgroundRemover"
Cohesion: 0.12
Nodes (16): _DaoBackgroundRemover, Any, floating, NDArray, Any, Estimate and subtract the background from an image using a DAOPhot-style…, Init an image processor that removes background from image. Args: sigma: Sigma…, Remove background from image. Args: image: Image to remove background from.… (+8 more)

### Community 211 - "DataCache"
Cohesion: 0.10
Nodes (14): Creates a new BaseWebcam. On the receiving end, a VFS root with a HTTPFile must…, DataCache, DataCacheEntry, Any, A single entry in the data cache., Delete entry in cache. Args: name: Name of entry to delete., Create a new entry for the data cache Args: name: Name of item data: Data for…, Update time for this item. (+6 more)

### Community 212 - "Plan: Widget plugin mechanism + `pyside6-deploy` packaging for `pyobs-gui`"
Cohesion: 0.13
Nodes (14): Consequences, Considered options, Considered options, Deciding which widget to use, without user-side config, Decision, Decision outcome, Implementation checklist, Non-goals (+6 more)

### Community 213 - "Plan: Split archive prefetch from CPU-bound merit evaluation, to unblock a `ProcessPoolExecutor`"
Cohesion: 0.12
Nodes (16): 1. `ObservationArchiveEvolution` — add prefetch + freeze (`observationarchiveevolution.py`), 2. Call prefetch + freeze — `ondemandscheduler.py`, `schedule()`, 3. Confirm zero cache misses before touching the executor, 4. Only after step 3 is clean: swap the executor (`_executor.py`), Consequences, Considered options, Decision, Existing coverage (+8 more)

### Community 214 - "PySepStatsCalculator"
Cohesion: 0.26
Nodes (4): Any, floating, NDArray, PySepStatsCalculator

### Community 215 - "Image (pyobs.images.processors.image) API doc"
Cohesion: 0.18
Nodes (11): AddFitsHeaders, Image (pyobs.images.processors.image) API doc, Download, Flip, Grayscale, HttpServer, Normalize, Save (+3 more)

### Community 216 - "Offsets (pyobs.images.processors.offsets) API doc"
Cohesion: 0.33
Nodes (11): AstrometryOffsets, BrightestStarGuiding, BrightestStarOffsets, Offsets (pyobs.images.processors.offsets) API doc, DummyOffsets, DummySkyOffsets, FitsHeaderOffsets, Offsets (+3 more)

### Community 217 - "Constraint"
Cohesion: 0.20
Nodes (11): AirmassConstraint, AstroplanScheduler, Constraint, Constraints answer a binary may-it-run question (any False excludes the task); Merits answer a continuous how-desirable question (values multiplied together with priority, highest score wins); rationale: clean separation lets scheduling policy be expressed in YAML without code, and a Merit returning 0.0 can double as a soft constraint, MoonIlluminationConstraint, MoonSeparationConstraint, OnDemandScheduler, OnDemandScheduler: greedy, evaluates constraints/merits per time step, robust to interruption, supports merits+global constraints+lookahead. AstroplanScheduler: full-night planning via astroplan PriorityScheduler in a separate process (avoids blocking event loop), only SiderealTarget, only per-task constraints, no merits; rationale: choose based on whether a committed nightly plan or rolling on-demand decisions is needed (+3 more)

### Community 218 - "test_httpfilecache.py"
Cohesion: 0.52
Nodes (11): make_cache(), make_request(), asyncio, test_download_response_has_cors_header(), test_download_with_token_configured_accepts_correct_token(), test_download_with_token_configured_rejects_missing_header(), test_download_with_token_configured_rejects_wrong_token(), test_download_without_token_configured_is_unauthenticated() (+3 more)

### Community 219 - "test_module_state_publishing.py"
Cohesion: 0.33
Nodes (6): _discover_concrete_modules(), asyncio, parametrize, Parametrized check: every concrete Module publishes state for each stateful…, All concrete (non-abstract, non-internal) pyobs.modules.Module subclasses.…, test_module_publishes_all_stateful_interfaces()

### Community 220 - "WeatherStatus"
Cohesion: 0.27
Nodes (6): Any, setter, WeatherStatus, test_status_set(), test_status_set_non_good(), test_status_set_none_good()

### Community 221 - "graphify reference: query, path, explain"
Cohesion: 0.33
Nodes (5): For /graphify explain, For /graphify path, graphify reference: query, path, explain, Step 0 — Constrained query expansion (REQUIRED before traversal), Step 1 — Traversal

### Community 222 - "._record_exception"
Cohesion: 0.25
Nodes (4): Exception, Records exception for severity tracking (see _register_exception) and fires any…, Whether exception should count as an instance of exc_type for severity-handler…, Execute a local method safely with type conversion All incoming variables in…

### Community 224 - ".retrieve_class_on_deserialization"
Cohesion: 0.24
Nodes (7): model_serializer, Any, model_validator, Self, Get the correct class for this model and run model_validate on that class with…, ValidationInfo, ValidatorFunctionWrapHandler

### Community 225 - ".__init__"
Cohesion: 0.04
Nodes (32): Any, Init new image processor. Args: on_error: How the pipeline should handle an…, Any, Init a new circle processor. Args: x: Center x coordinate. y: Center y…, Any, Init a new crosshair processor. Args: x: Center x coordinate. y: Center y…, Any, Init a new grayscale processor. Args: x: Center x coordinate. y: Center y… (+24 more)

### Community 226 - ".move_heliographic_stonyhurst"
Cohesion: 0.50
Nodes (3): Any, DEGREES, Moves on given coordinates. Args: lon: Longitude in deg to track. lat: Latitude…

### Community 227 - "FileList"
Cohesion: 0.27
Nodes (5): FileList, Base class for file lists., Any, File list for testing., TestingFileList

### Community 228 - ".move_helioprojective"
Cohesion: 0.50
Nodes (3): Any, DEGREES, Moves on given coordinates. Args: theta_x: The theta_x coordinate. theta_y: The…

### Community 229 - ".move_altaz"
Cohesion: 0.50
Nodes (3): Any, DEGREES, Moves to given coordinates. Args: alt: Alt in deg to move to. az: Az in deg to…

### Community 230 - "pyobs 2.0 Wire Protocol, State, and Access Control design doc"
Cohesion: 0.09
Nodes (22): pyobs/utils/config_schema.py: dataclass_to_schema, ICooling interface (reference pattern), slixmpp O(N^2) IQ handler dispatch bug (cross-referenced), IStructuredConfig design doc, IStructuredConfig interface, Rationale: IStructuredConfig coexists with IConfig (per-field vs bulk dataclass config), pyobs 2.0 Wire Protocol, State, and Access Control design doc, Access Control (ACLs): allow/deny, mode: enforce|log (+14 more)

### Community 231 - "Plan: Log the loaded pyobs-* package versions at module startup"
Cohesion: 0.20
Nodes (9): Decision, Design, Helper, Implementation checklist, Log point, Open questions, Out of scope (follow-ups), Plan: Log the loaded pyobs-* package versions at module startup (+1 more)

### Community 232 - "Findings: driver/gui correctness review, all 8 repos (reviewed 2026-08-11)"
Cohesion: 0.13
Nodes (14): Context, Findings: driver/gui correctness review, all 8 repos (reviewed 2026-08-11), Plan: Driver/GUI split for all camera modules + qhyccd correctness review, pyobs-aravis, pyobs-asi, pyobs-fli (driver split only — gui.py not built yet), pyobs-flipro, pyobs-qhyccd (+6 more)

### Community 233 - "Plan: Unify TRIMSEC handling into `Image.trim()` (reconstructed)"
Cohesion: 0.33
Nodes (5): Architecture, File Map, Goal, Plan: Unify TRIMSEC handling into `Image.trim()` (reconstructed), Tasks

### Community 234 - "CHANGELOG.rst"
Cohesion: 0.22
Nodes (9): ejabberd shaper/xmpp_socket.erl reactivation bug (iag50srv capability-fetch timeouts), XmppComm disco#info role attribute (send/subscribe split), OnDemandScheduler CPU-bound work offloaded to ThreadPoolExecutor, Vfs.write_image()/write_fits() moved to asyncio.to_thread(), run_cpu_bound (scheduler/_executor.py), Vfs.write_fits (pyobs/vfs/vfs.py), Vfs.write_image (pyobs/vfs/vfs.py), specs/plans/event-role-advertising.md (+1 more)

### Community 235 - "Use a self-hosted Keycloak alongside odin, as two parallel auth backends"
Cohesion: 0.25
Nodes (6): Consequences, Considered Options, Context and Problem Statement, Decision Outcome, Use a self-hosted Keycloak alongside odin, as two parallel auth backends, ADRs

### Community 236 - "Image class"
Cohesion: 0.20
Nodes (10): meta.AltAzOffsets, meta.ExpTime, Image class, Image.meta dict; rationale: keyed by class to avoid collisions between pipeline stages, kept out of FITS since it's runtime-only data, meta.OnSkyDistance, meta.PixelOffsets, meta.RaDecOffsets, meta.SkyOffsets (+2 more)

### Community 237 - "Plan: Module observer-location capabilities (reconstructed)"
Cohesion: 0.33
Nodes (5): Architecture, File Map, Goal, Plan: Module observer-location capabilities (reconstructed), Tasks

### Community 238 - "Plan: Advertise event send/subscribe role in disco#info"
Cohesion: 0.33
Nodes (5): Architecture, File Map, Plan: Advertise event send/subscribe role in disco#info, Problem, Tasks

### Community 239 - "reset_network"
Cohesion: 0.67
Nodes (3): fixture, Reset LocalNetwork singleton before each test., reset_network()

### Community 240 - "Module.startup() lifecycle helper"
Cohesion: 0.50
Nodes (4): Module.startup() lifecycle helper, ModuleState.STARTING, Rationale: delay send_presence() until READY to avoid capability-publish race, Gating RPC commands until module startup completes

### Community 241 - "CreateFilename"
Cohesion: 0.21
Nodes (9): CreateFilename, Any, Add filename to image. Args: image: Image to add filename to. Returns: Image…, Format and set a filename for the image using a pattern, storing it in the…, Init an image processor that adds a filename to an image. Args: pattern:…, asyncio, test_call(), test_init_default() (+1 more)

### Community 242 - "Plan: Stop scheduler constraint/merit evaluation from blocking the event loop"
Cohesion: 0.14
Nodes (13): 1. Dedicated executor — new file `pyobs/robotic/scheduler/_executor.py`, 2. Offload the three call sites — `pyobs/robotic/scheduler/ondemandscheduler.py`, 3. Cache target-independent astropy results — `pyobs/robotic/scheduler/dataprovider.py`, 4. `AstroplanScheduler` — no change, Consequences, Considered options, Decision, Existing coverage (regression net, no changes needed) (+5 more)

### Community 243 - ".__init__"
Cohesion: 0.18
Nodes (8): Any, SkyCoord, Create an approximately equidistributed spherical grid. Args: n: Target number…, Initialize a Grid with a list of points. Args: points: Initial list of points…, Return the next point and remove it from the internal list. Returns: The next…, Create a regular lon/lat grid. Args: n_lon: Number of longitudinal divisions.…, Any, Initialize a GridNode. Args: log: If True, enable informational logging for…

### Community 244 - "watch_log_events_no_interest.py"
Cohesion: 0.50
Nodes (4): main(), make_client(), ClientXMPP, Like watch_log_events_raw.py, but deliberately never declares XEP-0163…

### Community 245 - "Implemented"
Cohesion: 0.40
Nodes (4): Implemented, Option A: reactive-only (already shipped, zero work), Option B: proactive greying-out — effort estimate (~half a day, 3-5 hours), Plan: `pyobs-gui` ACL-aware widget gating

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

### Community 253 - "Future"
Cohesion: 0.21
Nodes (5): Run script. Raises: InterruptedError: If interrupted, Future, Any, Sets a new timeout for the method call. Cancels any existing timeout handle and…, Returns async timeout.

### Community 254 - "PhotometryFocusSeries"
Cohesion: 0.17
Nodes (7): PhotometryFocusSeries, Any, Focus series based on source detection., Initialize a new projection focus series. Args: source_detection: Photometry to…, Analyse given image. Args: image: Image to analyse focus_value: Value to fit…, Returns a list of data points., Fit focus from analysed images Returns: Tuple of new focus and its error

### Community 255 - "graphify reference: add a URL and watch a folder"
Cohesion: 0.50
Nodes (3): For /graphify add, For --watch, graphify reference: add a URL and watch a folder

### Community 256 - "Decision"
Cohesion: 0.17
Nodes (11): 1. `ImageProcessor` — new methods and kwarg, 2. `PipelineMixin.run_pipeline()` — wrap each step, 3. `AstrometryDotNet` — migrate to handle_error, 4. Deprecation notes, 5. Tests, Consequences, Considered options, Decision (+3 more)

### Community 257 - "graphify reference: commit hook and native CLAUDE.md integration"
Cohesion: 0.50
Nodes (3): For git commit hook, For native CLAUDE.md integration, graphify reference: commit hook and native CLAUDE.md integration

### Community 258 - "graphify reference: incremental update and cluster-only"
Cohesion: 0.50
Nodes (3): For --cluster-only, For --update (incremental re-extraction), graphify reference: incremental update and cluster-only

### Community 259 - ".__call__"
Cohesion: 0.29
Nodes (5): Any, DataFrame, Initialize new CSV publisher. Args: filename: Name of file to log in., Publish the given results. Args: **kwargs: Results to publish., Return data that has so far been published.

### Community 260 - "TempFile"
Cohesion: 0.24
Nodes (6): Any, Open/create a temp file. Args: name: Name of file. mode: Open mode. prefix:…, TempFile, asyncio, test_name(), test_write_file()

### Community 261 - "robotic"
Cohesion: 0.43
Nodes (8): acquisition, fibercamera, fts, guiding, robotic, solar telescope, suncamera, weather

### Community 262 - "Archive (image archive base)"
Cohesion: 0.32
Nodes (8): Archive (image archive base), LocalArchive, PyobsArchive, ArchiveSkyflatPriorities, Archive, Image archives (pyobs.robotic.utils.archive) API doc, LocalArchive, PyobsArchive

### Community 263 - "._register_exception"
Cohesion: 0.29
Nodes (5): Watch for repeated occurrences of exc_type -- optionally scoped to a specific…, Checks all handlers against all recorded exceptions and returns those whose…, ExceptionHandler, LoggedException, NamedTuple

### Community 264 - "Comm"
Cohesion: 0.04
Nodes (34): Comm responsibility: Discovery (clients_with_interface), Comm responsibility: Events (broadcast typed events), Comm, PresenceCallback, setter, Get a proxy to the given client. Args: client: Name of client. Returns: Proxy…, Fetch capabilities for a single interface and push them into the given proxy…, Called when a client disconnects. Args: event: Disconnect event. sender: Name… (+26 more)

### Community 265 - "_PhotometryCalculator"
Cohesion: 0.29
Nodes (3): _PhotometryCalculator, Table, Abstract class for photometry calculators.

### Community 266 - "BaseVideo"
Cohesion: 0.06
Nodes (27): BaseVideo, LastImage, NextImage, Any, NamedTuple, NDArray, Response, Whether the server is started. (+19 more)

### Community 267 - "SMBFile"
Cohesion: 0.22
Nodes (5): Any, Returns content of given path. Args: path: Path to list. kwargs: Parameters for…, VFS wrapper for a file that can be accessed over a SMB connection. Requires…, Open/create a file over a SSH connection. Args: name: Name of file. mode: Open…, SMBFile

### Community 268 - "._get_next"
Cohesion: 0.33
Nodes (4): SkyCoord, Log a point if logging is enabled. For SkyCoord instances, logs RA/Dec in…, Return the next point in the sequence. Implementors must return either a (x, y)…, Return the next point, storing it as the last yielded value. Returns: A point…

### Community 270 - "Plan: `pyobs-gui` navbar keyboard shortcuts"
Cohesion: 0.18
Nodes (10): Binding is by page name, not by widget or list-item instance, File changes, Key scheme, Motivation, Plan: `pyobs-gui` navbar keyboard shortcuts, Shortcut wiring, State, Verification (once implemented) (+2 more)

### Community 271 - "filters.py"
Cohesion: 0.15
Nodes (20): ConvertGridFrame, ConvertGridToSkyCoord, FromList, GridFilterValue, Convert (x, y) degree tuples to SkyCoord objects. Wraps a tuple-producing grid…, Transform SkyCoord points to a different frame., Select closest point from a list. Only select points if they are closer than a…, Filter points by numeric constraints on x and y. Accepts points as: - (x, y)… (+12 more)

### Community 272 - "DummyCamera"
Cohesion: 0.04
Nodes (60): Binning, BinningCapabilities, GainState, IImageFormat, ImageFormatCapabilities, ImageFormatState, Any, The module supports different image formats (e.g. INT16, FLOAT32), mainly used… (+52 more)

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

### Community 277 - ".get_sensor_value"
Cohesion: 0.22
Nodes (4): Any, Return value for given sensor. Args: station: Name of weather station to get…, Returns FITS header for the current status of this module. Args: namespaces: If…, Initialize a new pyobs-weather connector. Args: url: URL to weather station…

### Community 278 - "RemoteError"
Cohesion: 0.20
Nodes (7): ForbiddenError, The call itself didn't reach/return -- a transport failure, not a domain…, Raised when a caller is not permitted to invoke a method under the target…, RemoteError, RemoteTimeoutError, test_forbidden_error(), test_log_only_logs_once()

### Community 280 - ".flat_field"
Cohesion: 0.50
Nodes (3): Any, SECONDS, Do a series of flat fields. Args: count: Number of images to take Returns:…

### Community 281 - "test_memory_archives.py"
Cohesion: 0.08
Nodes (51): MemoryTaskArchive, Any, In-memory task archive for testing and simple deployments., Returns time when tasks last changed., Returns list of projects., Returns list of all tasks., Returns task with given ID, or None if not found., make_obs() (+43 more)

### Community 282 - ".move_heliocentric_polar"
Cohesion: 0.50
Nodes (3): Any, DEGREES, Moves on given coordinates. Args: mu: Cosine of the angular distance from Sun…

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

### Community 291 - ".grab_sequence"
Cohesion: 0.33
Nodes (4): Any, SECONDS, Start a sequence of `count` grabs. Returns immediately; progress is available…, Stop the sequence after the current grab. The grab currently in progress, if…

### Community 292 - "Plan: `pyobs-gui` IAutoGuiding widget"
Cohesion: 0.25
Nodes (7): Known bug in the shipped widget (to fix alongside this change), Plan: `pyobs-gui` IAutoGuiding widget, Problem: pixel offsets aren't physical, and the per-image correction is discarded, Proposed pyobs-core change, Resolved from the original open questions, Shipped (pyobs-core, `develop`), Widget design (pyobs-gui)

### Community 293 - "IStructuredConfig"
Cohesion: 0.33
Nodes (5): IStructuredConfig, Any, ConfigValue, The module accepts a whole structured (possibly nested) config object in one…, Apply a full structured config to this module. Args: config: Nested dict…

### Community 295 - "Investigation: pyobs-gui receives every LogEvent twice (SAAO/monet production)"
Cohesion: 0.25
Nodes (7): Access used, Artifacts from this session, Investigation: pyobs-gui receives every LogEvent twice (SAAO/monet production), Next steps, Problem, What's confirmed, What's ruled out

### Community 297 - ".night_obs"
Cohesion: 0.50
Nodes (3): date, Observer, Returns the night for this time, i.e. the date of the start of the current…

### Community 299 - "MotionStatusChangedEvent"
Cohesion: 0.06
Nodes (19): Any, JSON representation of event., String representation of event., Generic from_dict method for derived classes that don't need their own., Any, Any, Any, Any (+11 more)

### Community 300 - "ADR-0008: _safe_send keeps bounded retry unlike capability/subscribe fetches"
Cohesion: 0.40
Nodes (5): ADR-0008: _safe_send keeps bounded retry unlike capability/subscribe fetches, #664/#666 slow-shaper hang incident, XmppComm._get_capabilities(), XmppComm._retry_delay() (jittered capped backoff), XmppComm._safe_send()

### Community 301 - "Module._watch_event_loop_lag"
Cohesion: 0.33
Nodes (5): BrotDome._update_status, ADR-0009: Event-loop lag watchdog lives on Module, FocusModel._update, pyobs-iag50 capability-fetch timeout incident, Module._watch_event_loop_lag

### Community 302 - "Plan: Surface unrecognized kwargs in `Object.__init__` instead of silently discarding them"
Cohesion: 0.22
Nodes (8): Decision, Implementation checklist, Investigation findings (2026-08-15), Non-goals (for now — this is a stub, scope may change once investigated), Open questions, Plan: Surface unrecognized kwargs in `Object.__init__` instead of silently discarding them, Problem, Why not fixed already / why it's not trivial

### Community 303 - "pyobs.modules.image (doc)"
Cohesion: 0.40
Nodes (5): pyobs.modules.image (doc), ImageWatcher, ImageWriter, Pipeline (image module), Seeing

### Community 304 - "Plan: `pyobs-auth` + Keycloak integration"
Cohesion: 0.29
Nodes (6): 0. observation-portal (Keycloak admin config + small observation-portal config change), 1. `pyobs-auth` package (new repo) — done, released, 2. pyobs-archive — cutover, not dual-path — not landed, 3. pyobs-robotic-backend — done, 4. Not in this plan, Plan: `pyobs-auth` + Keycloak integration

### Community 305 - "Plan: Exception handling across the RPC boundary (reconstructed)"
Cohesion: 0.33
Nodes (5): Architecture, File Map (representative, not exhaustive — see commit diffs for the full ~74-file list), Goal, Plan: Exception handling across the RPC boundary (reconstructed), Tasks

### Community 306 - "Plan: Decouple `ICamera`/`IExposure` (reconstructed)"
Cohesion: 0.33
Nodes (5): Architecture, File Map, Goal, Plan: Decouple `ICamera`/`IExposure` (reconstructed), Tasks

### Community 307 - "GuidingStatisticsPixelOffset"
Cohesion: 0.25
Nodes (7): GuidingStatisticsPixelOffset, Calculates RMS of data. Args: data: Data to calculate RMS for. Returns: Tuple…, mock_meta_image(), fixture, test_build_header_to_few_values(), test_end_to_end(), test_get_session_data()

### Community 308 - "plans/index.md"
Cohesion: 0.07
Nodes (22): Architecture, File Map, Goal, Plan: `IDataSequence` — server-side counted data sequences (reconstructed), Tasks, Plan: `pyobs-gui` IAcquisition widget, Resolved from the original open questions, Shipped (pyobs-core, `develop`) (+14 more)

### Community 309 - "test_scriptrunner.py"
Cohesion: 0.29
Nodes (7): A script failed while running -- e.g. a proxy/network failure reaching a module…, ScriptError, make_runner(), asyncio, _RaisingScript, test_run_lets_domain_exception_through_unwrapped(), test_run_wraps_untyped_exception_as_script_error()

### Community 310 - "ModuleNameFilter"
Cohesion: 0.20
Nodes (5): Background thread for handling the logging., Send an event to other clients. Args: event (Event): Event to send, ModuleNameFilter, LogRecord, Logging filter that stamps the current module name onto every LogRecord.…

### Community 313 - "Target"
Cohesion: 0.29
Nodes (4): Target, Set the resolved target if not already set, e.g. when restoring from an…, The resolved target, or the static target if not dynamic., Target for this specific run: the observation's own record if known, otherwise…

### Community 315 - "flatfield/test_scheduler.py"
Cohesion: 0.47
Nodes (9): FlatFieldScheduler, Run the flat-field scheduler., make_scheduler_module(), asyncio, setup_flatfield_proxy(), test_abort_sets_event(), test_run_aborts_current_flat_field_when_requested(), test_run_raises_when_already_running() (+1 more)

### Community 316 - "ModuleLocation dataclass (nested in ModuleCapabilities)"
Cohesion: 0.50
Nodes (4): Location-mismatch warning via _on_module_opened, Rationale: location as one-shot capability, not pubsub state, ModuleLocation dataclass (nested in ModuleCapabilities), Module observer-location capabilities design doc

### Community 317 - "check_pyobs_releases.sh"
Cohesion: 0.70
Nodes (4): check_repo(), main(), print_header(), check_pyobs_releases.sh script

### Community 318 - "check_ejabberd_notify.py"
Cohesion: 0.60
Nodes (4): connect(), main(), make_client(), Minimal ejabberd notification test — no pyobs code involved.

### Community 319 - ".__init__"
Cohesion: 0.25
Nodes (7): Any, Module, _disable_iers_auto_download(), InfluxLogConfig, Initializes a pyobs application. Exactly one of `config`/`module_factory` must…, Create a new GUI application., TypedDict

### Community 320 - "Kiosk"
Cohesion: 0.15
Nodes (8): Kiosk, Any, Response, Thread for taking images., A kiosk mode for a pyobs camera that takes images and published them via HTTP., Initializes file cache. Args: camera: Camera to use for kiosk mode. port: Port…, Handles access to /* and returns a specified image. Args: request: Request to…, Whether the server is started.

### Community 321 - "test_dummyaltaztelescope.py"
Cohesion: 0.70
Nodes (4): make_dummyaltaztelescope(), asyncio, test_open_registers_offsets_altaz_event_and_publishes_initial_state(), test_set_offsets_altaz_sends_event_and_updates_state()

### Community 322 - "Photometry (pyobs.images.processors.photometry) API doc"
Cohesion: 0.83
Nodes (4): Photometry (pyobs.images.processors.photometry) API doc, Photometry, PhotUtilsPhotometry, SepPhotometry

### Community 323 - "GuiApplication"
Cohesion: 0.31
Nodes (6): GuiApplication, Derived Application class that uses a Qt GUI. Allows for graceful shutdown in…, main(), Any, PyobsWinCLI, Class for initializing and running pyobs CLI.

### Community 324 - "_event_role"
Cohesion: 0.39
Nodes (7): _event_role(), Space-separated role(s) ("send", "subscribe", or both) for an event class, for…, Tests for XmppComm's disco#info event role tagging. See specs/plans/event-role-…, test_event_role_ignores_unrelated_events(), test_event_role_send_and_subscribe(), test_event_role_send_only(), test_event_role_subscribe_only()

### Community 325 - "Any"
Cohesion: 0.25
Nodes (4): Any, Return the last received state for the given interface, or None., Return the capabilities for the given interface, or None., Return state immediately if available, otherwise wait for the first update.

### Community 326 - "_dummytelescopebase.py"
Cohesion: 0.04
Nodes (52): FiltersCapabilities, FilterState, FocuserState, IFocuser, The module is a focusing device., AltAzOffsetState, IOffsetsRaDec, Any (+44 more)

### Community 327 - ".__init__"
Cohesion: 0.25
Nodes (5): Any, Aborts the current exposure. Raises: ValueError: If exposure could not be…, Creates a new BaseCamera. Args: fits_headers: Additional FITS headers. flip:…, Any, Creates a new dummy cammera. Args: readout_time: Readout time in seconds. sim:…

### Community 329 - "ConfigDB"
Cohesion: 0.33
Nodes (3): InstrumentLocation, ConfigDB, Creates a new LCO scheduler. Args: portal: Portal to use. configdb: ConfigDB to…

### Community 330 - ".__init__"
Cohesion: 0.29
Nodes (4): Creates a comm module., Any, Creates a new dummy comm. Args: name: Name to report for this comm. Defaults to…, Execute a given method on a remote client. Args: client (str): ID of client.…

### Community 331 - ".__init__"
Cohesion: 0.33
Nodes (4): Any, Abort current actions., Initialize a new flat field scheduler. Args: flatfield: Flat field module to…, Perform flat-fielding Raises: DeviceBusyError: If a flat-fielding run is…

### Community 332 - "ModuleGui"
Cohesion: 0.33
Nodes (3): ModuleGui, Any, LogRecord

### Community 333 - ".__init__"
Cohesion: 0.29
Nodes (5): Any, Pipeline, ProgressCallback, Pre-pass: list (not download) OBJECT frames for every instrument/binning/filter…, Creates a Reduction object for reducing a given observation period. Args:…

### Community 334 - ".set_exposure_time"
Cohesion: 0.50
Nodes (3): Any, SECONDS, Set the exposure time in seconds. Args: exposure_time: Exposure time in…

### Community 335 - ".set_offsets_altaz"
Cohesion: 0.50
Nodes (3): Any, DEGREES, Move an Alt/Az offset. Args: dalt: Altitude offset in degrees. daz: Azimuth…

### Community 336 - ".set_gain"
Cohesion: 0.40
Nodes (3): Any, Set the camera gain. Args: gain: New camera gain. Raises: ValueError: If gain…, Set the camera offset. Args: offset: New camera offset. Raises: ValueError: If…

### Community 337 - ".abort"
Cohesion: 0.40
Nodes (3): Any, Abort current actions., Sets the currently active fiber. Must be in fiber_names capability. Args:…

### Community 338 - ".set_rotation"
Cohesion: 0.50
Nodes (3): Any, DEGREES, Sets the rotation angle to the given value in degrees. Raises: MoveError: If…

### Community 339 - ".__init__"
Cohesion: 0.40
Nodes (3): Any, Abort current actions., Create a new dummy auto-focus. Args: wait_time: Time to wait between focus…

### Community 340 - "pyobs.modules.weather (doc)"
Cohesion: 1.00
Nodes (3): pyobs.modules.weather (doc), MockWeather, Weather (module)

### Community 342 - ".__init__"
Cohesion: 0.40
Nodes (3): Any, Any, Initialize a new scheduler. Args: twilight: astronomical or nautical

### Community 343 - ".__init__"
Cohesion: 0.40
Nodes (4): Any, Pipeline, ProgressCallback, Args: archive: Archive to fetch raw and calibration frames from. pipeline:…

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

### Community 363 - "reset_network"
Cohesion: 0.67
Nodes (3): fixture, Reset LocalNetwork singleton before each test., reset_network()

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
- **620 isolated node(s):** `Problem`, `Decision`, `Helper`, `Log point`, `Out of scope (follow-ups)` (+615 more)
  These have ≤1 connection - possible missing edges or undocumented components.
- **56 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **What is the exact relationship between `Configuration utilities (pyobs.utils.config) API doc` and `Coordinate utilities (pyobs.utils.coordinates) API doc`?**
  _Edge tagged AMBIGUOUS (relation: conceptually_related_to) - confidence is low._
- **What is the exact relationship between `PyObsError` and `ScriptRunner.run()`?**
  _Edge tagged AMBIGUOUS (relation: conceptually_related_to) - confidence is low._
- **What is the exact relationship between `FocusError` and `FocusModel.set_optimal_focus`?**
  _Edge tagged AMBIGUOUS (relation: conceptually_related_to) - confidence is low._
- **Why does `Time` connect `Time` to `BaseTelescope`, `BaseGuiding`, `TaskData`, `Module`, `Interface`, `Archive`, `SkyFlatsBasePointing`, `ImageProcessor`, `Grid`, `pyobs.py`, `filters.py`, `DummyCamera`, `ImageType`, `Scheduler`, `mixins/test_fitsheader.py`, `Event`, `.get_sensor_value`, `TimeDelta`, `test_schedulereader.py`, `test_flatfielder.py`, `test_memory_archives.py`, `test_lco_http.py`, `tests/test_events.py`, `GoodWeatherEvent`, `SiderealTarget`, `test_control.py`, `test_basetelescope.py`, `FrameInfo`, `Portal`, `utils/exceptions.py`, `LogEvent`, `._filter_data`, `ExpTimeEval`, `IPointingAltAz.py`, `TaskStartedEvent`, `ObservationList`, `fits.py`, `Scheduler`, `test_transitimaging.py`, `.night_obs`, `robotic/test_scheduler.py`, `test_schedulewriter.py`, `acquisition.py`, `Calibration`, `Publisher`, `flatfield/test_scheduler.py`, `Proxy`, `FilenameFormatter`, `test_yaml_archives.py`, `Project`, `FlatFielder`, `._set_optimal_focus`, `SolarElevationConstraint`, `Offsets`, `.now`, `_dummytelescopebase.py`, `test_backend_archives.py`, `SkyflatPriorities`, `VirtualFileSystem`, `test_proxy.py`, `test_acquisition.py`, `Weather`, `test_pyobs_archive.py`, `Object`, `InfluxHandler`, `test_coordinates.py`, `LocalArchive`, `Test Commlogging (comm)`, `ImagingScript`, `FocusModel`, `test_darkbias.py`?**
  _High betweenness centrality (0.267) - this node is a cross-community bridge._
- **Why does `Image` connect `Image` to `BaseGuiding`, `Archive`, `Interface`, `Comm`, `ImageProcessor`, `_PhotometryCalculator`, `BaseVideo`, `_ResponseImageWriter`, `DummyCamera`, `ImageType`, `mixins/test_fitsheader.py`, `Event`, `PipelineMixin`, `AstrometryDotNet`, `SkyOffsets`, `test_flatfielder.py`, `sourcedetection.py`, `SoftBin`, `AddMask`, `FrameInfo`, `utils/exceptions.py`, `._filter_data`, `fits.py`, `_SourceCatalog`, `.__call__`, `StarExpTimeEstimator`, `GuidingStatisticsPixelOffset`, `test_aperture_photometry.py`, `acquisition.py`, `Calibration`, `_SepAperturePhotometry`, `Any`, `FilenameFormatter`, `test_basevideo.py`, `test_yaml_archives.py`, `CatalogCircularMask`, `Offsets`, `test_acquisition.py`, `Smooth`, `_DaoBackgroundRemover`, `ProjectionFocusSeries`, `AperturePhotometry`, `Ring`, `VFSFile`, `DaophotSourceDetection`, `ProjectedOffsets`, `test_pyobs_archive.py`, `.__init__`, `FocusSeries`, `SepSourceDetection`, `test_autoguiding.py`, `LocalArchive`, `_PhotUtilAperturePhotometry`, `CreateFilename`, `PhotometryFocusSeries`, `._expose`, `ImageSourceFilter`?**
  _High betweenness centrality (0.140) - this node is a cross-community bridge._
- **Why does `Module` connect `Module` to `BaseTelescope`, `Time`, `Interface`, `ImageWatcher`, `test_presence.py`, `._register_exception`, `Comm`, `PyobsError`, `BaseVideo`, `BaseCamera`, `pyobs.py`, `XmppComm`, `test_camerasettings.py`, `.__init__`, `test_dummymode.py`, `test_kiosk.py`, `Scheduler`, `mixins/test_fitsheader.py`, `PipelineMixin`, `FlatFieldPointing`, `Any`, `utils/exceptions.py`, `LogEvent`, `_AbortableModule`, `Stellarium`, `IPointingAltAz.py`, `ObservationList`, `robotic/test_scheduler.py`, `StandAlone`, `RPC`, `WindowCapabilities`, `acquisition.py`, `format_filename`, `.close`, `Publisher`, `flatfield/test_scheduler.py`, `test_basevideo.py`, `PointingSeries`, `GridNode`, `FlatFielder`, `Project`, `Kiosk`, `benchmark_state_throughput.py`, `Telegram`, `MockWeather`, `test_acquisition.py`, `Weather`, `DataCache`, `test_exception_logging.py`, `Application`, `test_module_state_publishing.py`, `._record_exception`, `Object`, `make_proxy_cm`, `test_autoguiding.py`, `timeout`, `get_registered_interface`, `HttpFileCache`, `FocusModel`?**
  _High betweenness centrality (0.082) - this node is a cross-community bridge._
- **Are the 167 inferred relationships involving `Time` (e.g. with `PyobsCLI` and `Proxy`) actually correct?**
  _`Time` has 167 INFERRED edges - model-reasoned connections that need verification._