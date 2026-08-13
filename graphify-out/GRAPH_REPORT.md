# Graph Report - pyobs-core  (2026-08-12)

## Corpus Check
- 768 files · ~398,706 words
- Verdict: corpus is large enough that graph structure adds value.

## Summary
- 8682 nodes · 21045 edges · 424 communities (383 shown, 41 thin omitted)
- Extraction: 93% EXTRACTED · 7% INFERRED · 0% AMBIGUOUS · INFERRED: 1400 edges (avg confidence: 0.55)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `262db6fe`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- LcoScript
- imaging.py
- Time
- RunningState
- Interface
- Module
- Image
- DynamicTarget
- BaseCamera
- ImageProcessor
- TaskData
- test_basetelescope.py
- test_localcomm_state.py
- XmppComm
- AstrometryDotNet
- FilenameFormatter
- TimeDelta
- _SepAperturePhotometry
- DummyRoof
- mixins/test_fitsheader.py
- Event
- PipelineMixin
- test_backend_archives.py
- test_flatfielder.py
- LocalComm
- tests/test_events.py
- test_csvpicker_scheduler.py
- LcoTask
- test_mastermind.py
- WindowingWidget
- Interfaces (pyobs.interfaces) API doc
- test_control.py
- test_presence.py
- LogScript
- test_lco_http.py
- enums.py
- Future
- VirtualFileSystem
- CoolingState
- IPointingAltAz.py
- test_astroplanscheduler.py
- reset_network
- NextImage
- Comm
- test_transitimaging.py
- robotic/test_scheduler.py
- StandAlone
- utils/exceptions.py
- ._run_configurations
- test_stellarexptime.py
- StarExpTimeEstimator
- RPC
- WindowCapabilities
- test_shellcommand.py
- Calibration
- Any
- Publisher
- .__init__
- Unit
- Proxy
- FitsHeaderOffsets
- test_basevideo.py
- SkyFlatsBasePointing
- test_yaml_archives.py
- FlatFielder
- IExposure
- Telegram
- XmppConfig
- OffsetResult
- Offsets
- .now
- PyObsError
- test_proxy.py
- XEP_0009
- SiderealTarget
- PyobsDaemon
- MockWeather
- test_config.py
- ImageType
- test_autoguiding.py
- Weather
- FileSystemObservationArchive
- SkyOffsets
- weather.py
- Object
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
- SolarElevationConstraint
- LocalArchive
- Plan: Systematic ejabberd throughput/latency benchmarking
- _PhotUtilAperturePhotometry
- Mixins (pyobs.mixins) API doc
- Script base class
- test_background_task.py
- Test Commlogging (comm)
- TaskFailedEvent
- test_dummyradectelescope.py
- ImagingScript
- test_acquisition.py
- BufferedFile
- VFSFile
- LocalFile
- test_version_mismatch.py
- CLAUDE.md (repo guide)
- SFTPFile
- FocusModel
- OffsetsAltAzEvent
- ImageSourceFilter
- test_darkbias.py
- Portal
- GridNode
- Plan: pyobs-pipeline
- Test Localcomm (local)
- SepSourceDetection
- test_schedulewriter.py
- DummyMode
- test_dummymode.py
- _ResponseImageWriter
- test_autofocus.py
- Grid
- test_kiosk.py
- pyobs.py
- Robotic recipe (doc)
- is_valid_jid
- test_lcoscript.py
- OnSkyDistance
- DummyRaDecTelescope
- Scheduler
- datetime
- .__init__
- Observation
- tests/xmpp/docker-compose.yml (ejabberd integration test container)
- `OBSNUM`: per-night observation counter in FITS headers
- 3rd party packages (doc)
- _DaoBackgroundRemover
- SSHFile
- create_rst.py
- GuidingStatistics
- SoftBin
- AddMask
- Archive
- RandomizeGrid
- comm/test_events.py
- .__init__
- LogEvent
- test_transit_mastermind.py
- ExpTimeEval
- Stellarium
- Overview (doc)
- calibration.py
- GuidingStatisticsPixelOffset
- .get_meta
- .close
- test_grab_sequence.py
- binding.py
- NewSpectrumEvent
- .get_config_value
- CLI
- HttpFileCache
- .set_gain
- ExpTime
- Steering: astropy IERS auto-download blocks event loop
- Test Basecamera (camera)
- test_imagewatcher.py
- .abort
- Merit
- ejabberd shaper throttling bug (xmpp_socket.erl re-arm) & fix
- WeatherStatus
- FileSystemTaskArchive
- Work Plan
- Plan: `pyobs-gui` TelescopeWidget layout — width floor investigation & design notes
- .__init__
- GridPipeline
- .set_tracking_rate
- ._set_optimal_focus
- What's New in pyobs 2.0 (doc)
- TaskStartedEvent
- LcoTaskArchive
- CatalogCircularMask
- .set_exposure_time
- ImageWatcher
- object.py
- .set_offsets_altaz
- show_module_info.py
- integration/conftest.py
- .set_cooling
- robotic
- Scheduler module
- BaseModel (pyobs.utils.serialization)
- Decision
- Smooth
- Scheduler
- DataCacheEntry
- Plan: Widget plugin mechanism + `pyside6-deploy` packaging for `pyobs-gui`
- Plan: Split archive prefetch from CPU-bound merit evaluation, to unblock a `ProcessPoolExecutor`
- test_httpfilecache.py
- Image (pyobs.images.processors.image) API doc
- Offsets (pyobs.images.processors.offsets) API doc
- Constraint
- .set_offsets_radec
- .add_fits_headers
- .set_binning
- flatfield/test_scheduler.py
- ImageWriter
- .move_altaz
- .move_heliocentric_polar
- test_imagewriter.py
- .move_heliographic_stonyhurst
- FileList
- .move_helioprojective
- TempFile
- pyobs 2.0 Wire Protocol, State, and Access Control design doc
- .move_radec
- Findings: driver/gui correctness review, all 8 repos (reviewed 2026-08-11)
- test_xmpp_rpc.py
- CHANGELOG.rst
- Use a self-hosted Keycloak alongside odin, as two parallel auth backends
- Image class
- PyobsArchive
- BrightestStarGuiding
- .set_config
- Module.startup() lifecycle helper
- .night_obs
- Plan: Stop scheduler constraint/merit evaluation from blocking the event loop
- .__init__
- ._filter_data
- SMBFile
- pyobs-gui as a standalone binary (umbrella design)
- Plan: Enforce state publishing for stateful interfaces
- Plan: `pyobs-gui` login window
- test_safe_send.py
- test_pyobsd.py
- Two-phase Object lifecycle; rationale: __init__ must not touch hardware/external services (only store params, create children, register background tasks); open() is where side effects happen, so objects can be constructed cheaply/safely before being started
- Simulation recipe (doc)
- .__init__
- test_dummyvideo.py
- ImageFormat
- Decision
- .track_body
- .track_orbital_elements
- wait_for
- GuidingStatisticsSkyOffset
- robotic
- Archive (image archive base)
- .flat_field
- ._get_client
- ConfigStatus
- BaseVideo
- .add_pointing_measurement
- ._get_next
- Shared authentication across pyobs web projects via Keycloak
- Plan: `pyobs-gui` navbar keyboard shortcuts
- .run_script
- .sync_target
- Image.trim
- conftest.py
- Misc (pyobs.images.processors.misc) API doc
- PolymorphicBaseModel
- wait_for
- .retrieve_class_on_deserialization
- test_comm_interface_resolution.py
- Any
- ObservationList
- .set_rotation
- Target
- GoodWeatherEvent
- Implementation
- Plan: Interactive login/settings dialog for `pyobs-gui`, deferring `Application`'s module construction
- pyobs.modules.utils (doc)
- Plan: Add baseline tests to core-tier repos, then enable grouped Dependabot auto-merge
- Plan: CORS + token auth for `HttpFileCache`
- FluentLogger
- .__call__
- Plan: `pyobs-gui` IAutoGuiding widget
- .grab_sequence
- .set_focus
- Investigation: pyobs-gui receives every LogEvent twice (SAAO/monet production)
- .init
- GraticuleSphericalGrid
- Plan: `pyobs-gui` IAutoFocus widget
- .set_window
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
- .get_permitted_methods
- .__call__
- Implemented
- Plan: `pyobs-gui` IAcquisition widget
- ModuleLocation dataclass (nested in ModuleCapabilities)
- check_pyobs_releases.sh
- check_ejabberd_notify.py
- .get_interfaces
- MockBaseDome
- pyobs.modules.weather (doc)
- Photometry (pyobs.images.processors.photometry) API doc
- .append_last
- .__iter__
- .log_last
- Pipeline
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
1. `Time` - 583 edges
2. `Image` - 444 edges
3. `Task` - 227 edges
4. `Interface` - 186 edges
5. `Module` - 182 edges
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

## Communities (424 total, 41 thin omitted)

### Community 0 - "LcoScript"
Cohesion: 0.09
Nodes (16): LcoAutoFocusScript, Auto focus script for LCO configs., Whether this config can currently run. Returns: True, if the script can run now, Run script. Raises: InterruptedError: If interrupted, # TODO: unfortunately this never happens, since the LCO portal forces…, LcoDefaultScript, Returns FITS header for the current status of this module. Args: namespaces: If…, Default script for LCO configs. (+8 more)

### Community 1 - "imaging.py"
Cohesion: 0.05
Nodes (42): GuidingState, IAutoGuiding, The module can perform auto-guiding., ExposureTimeState, IExposureTime, The camera supports exposure times, to be used together with…, calc_expose_timeout(), Calculates timeout for grabe_image(). (+34 more)

### Community 2 - "Time"
Cohesion: 0.03
Nodes (79): Constraint, ndarray, SkyCoord, Returns a boolean mask of candidates passing this constraint. Default…, MoonIlluminationConstraint, Moon illumination constraint., TimeConstraint, DataProvider (+71 more)

### Community 3 - "RunningState"
Cohesion: 0.03
Nodes (82): F, IAbortable, Any, Abort current actions., The module has an abortable action., AcquisitionAttempt, AcquisitionResult, AcquisitionState (+74 more)

### Community 4 - "Interface"
Cohesion: 0.03
Nodes (105): ABC, Binning, BinningCapabilities, BinningState, IBinning, The camera supports binning, to be used together with…, ICalibrate, Any (+97 more)

### Community 5 - "Module"
Cohesion: 0.02
Nodes (86): AbstractEventLoop, ConfigCapabilities, IConfig, The module allows access to some of its configuration options., A module in *pyobs* is the smalles executable unit. The base class for all…, Module, MultiModule, Any (+78 more)

### Community 6 - "Image"
Cohesion: 0.03
Nodes (87): ImageHDU, Image, Any, CCDData, floating, HDUList, Header, NDArray (+79 more)

### Community 7 - "DynamicTarget"
Cohesion: 0.05
Nodes (54): DynamicTarget, SkyCoord, Target, Pick the best available target given current conditions. For static targets…, HeliocentricPolarTarget, SkyCoord, Target, HelioprojectiveTarget (+46 more)

### Community 8 - "BaseCamera"
Cohesion: 0.04
Nodes (51): ExposureState, Helper methods for all modules that need FITS headers for an image., SpectrumFitsHeaderMixin, BaseCamera, calc_expose_timeout(), ExposureInfo, Any, Header (+43 more)

### Community 9 - "ImageProcessor"
Cohesion: 0.04
Nodes (49): Some info about :class:`pyobs.images.Image`., ImageProcessor, The error handling mode for this step., Processes an image. Args: image: Image to process. Returns: Processed image., Resets state of image processor, AddFitsHeaders, Keyword, Any (+41 more)

### Community 10 - "TaskData"
Cohesion: 0.04
Nodes (26): Whether this config can currently run. Returns: True if script can run now., Run script. Raises: InterruptedError: If interrupted, Estimate duration of the sky flats. The actual schedule depends on sky…, Whether this config can currently run. Returns: True if script can run now., Returns FITS header for the current status of this module. Args: namespaces: If…, Estimate duration of the script for the current case., Returns FITS header for the current status of this module. Args: namespaces: If…, Estimate duration of the branch that would be run for the current condition. (+18 more)

### Community 11 - "test_basetelescope.py"
Cohesion: 0.12
Nodes (27): OrbitalElements, _orbital_plane_to_ecliptic_cartesian(), _perifocal_to_radec(), _propagate_elements(), Rotates a perifocal-plane position into heliocentric ecliptic coordinates, then…, Rotates a perifocal-plane position (AU) into heliocentric ecliptic Cartesian…, Two-body Kepler propagation of orbital elements to (ra, dec) in degrees, ICRS.…, Starts tracking a body defined by orbital elements. Args: elements: Orbital… (+19 more)

### Community 12 - "test_localcomm_state.py"
Cohesion: 0.09
Nodes (28): asyncio, fixture, Tests for LocalComm state, capabilities, and presence., set_presence stores and get_client_state retrieves., Default presence is READY with no error string., subscribe_presence fires callback immediately with the current presence state., subscribe_presence callback is called whenever presence changes., Reset LocalNetwork singleton before each test. (+20 more)

### Community 13 - "XmppComm"
Cohesion: 0.04
Nodes (40): Any, Store published capabilities for inclusion in disco#info responses., Return this client's own published capabilities., Fetch and deserialize capabilities for a remote module's interface. Retries…, Send XMPP presence stanza reflecting the module lifecycle state. ModuleState…, See Comm.mark_ready(). Remembers readiness on self (survives client recreation…, Subscribe to a pubsub node, retrying until the node exists. Runs as a…, Create a new XMPP Comm module. Either a fill JID needs to be provided, or a set… (+32 more)

### Community 14 - "AstrometryDotNet"
Cohesion: 0.04
Nodes (38): Astrometry processors doc, AstrometryDotNet (astrometry processor), Astrometry, Finds astrometric solution to a given image. Args: image: Image to analyse.…, Base class for astrometry processors, AstrometryDotNet, Any, Init new astronomy.net processor. Args: url: URL to service. source_count:… (+30 more)

### Community 15 - "FilenameFormatter"
Cohesion: 0.04
Nodes (53): Format filename with given formatter., Any, Save an image to the virtual file system and optionally broadcast a…, Init an image processor that broadcasts an image Args: filename: Filename to…, Initialize processor., Broadcast image. Args: image: Image to broadcast. Returns: Original image., Save, Any (+45 more)

### Community 16 - "TimeDelta"
Cohesion: 0.07
Nodes (75): ConstantMerit, Merit function that returns a constant value., model_validator, Self, Merit function that uses time windows., TimeWindow, TimeWindowMerit, OnDemandScheduler (+67 more)

### Community 17 - "_SepAperturePhotometry"
Cohesion: 0.05
Nodes (34): AperturePhotometry, Any, Base class for aperture photometry processors -- not meant to be used directly,…, Do aperture photometry on given image. Args: image: Image to do aperture…, _PhotometryCalculator, Table, Abstract class for photometry calculators., Photometry (+26 more)

### Community 18 - "DummyRoof"
Cohesion: 0.06
Nodes (41): pyobs.modules.roof (doc), BaseDome, BaseRoof, DummyRoof, WeatherState, DummyRoof, Any, Get the percentage the roof is open. (+33 more)

### Community 19 - "mixins/test_fitsheader.py"
Cohesion: 0.09
Nodes (54): Any, Initialise the mixin. Args: fits_namespaces: List of namespaces for FITS…, Initialise the mixin. Args: fits_namespaces: List of namespaces for FITS…, Request FITS headers from other modules. Returns: Futures from all modules., Add requested FITS headers to header of given image. Args: image: Image with…, FitsModule, make_image(), make_module() (+46 more)

### Community 20 - "Event"
Cohesion: 0.05
Nodes (44): Event, Base class for all events., DataType, TypedDict, DataType, TypedDict, DataType, TypedDict (+36 more)

### Community 21 - "PipelineMixin"
Cohesion: 0.06
Nodes (41): ImageProcessor on_error kwarg / per-step error handling, Handle an ImageError raised by this step, when on_error == "error". Override…, PipelineMixin, Any, Mixin for a module that needs to implement an image pipeline., Initializes the mixin. Args: steps: Pipeline steps to run on images. archive:…, Resets all previous state of the involved image processors., Run the pipeline on the given image. Each step is run, and an ImageError it… (+33 more)

### Community 22 - "test_backend_archives.py"
Cohesion: 0.06
Nodes (71): BackendTaskArchive, Any, ClientSession, Returns the task with the given ID. Returns: Task with given ID., Task archive based on pyobs-robotic-backend., Creates a new task archive. Args: url: URL of pyobs-robotic-backend. token:…, Opens the backend task archive., Closes the backend observation archive. (+63 more)

### Community 23 - "test_flatfielder.py"
Cohesion: 0.08
Nodes (60): make_flatfielder(), make_observer(), make_twilight_observer(), asyncio, parametrize, Regression test for #481: median == bias_level used to raise ZeroDivisionError., Observer stub returning a constant solar altitude for every sun_altaz() call., Observer stub distinguishing the first (now) vs second (+10min) sun_altaz()… (+52 more)

### Community 24 - "LocalComm"
Cohesion: 0.06
Nodes (31): LocalComm, Any, Store capabilities locally., Return this client's own published capabilities., Fetch capabilities from a remote module., Store presence state and dispatch to all subscribers., Return presence state of a connected module., Returns list of currently connected clients. (+23 more)

### Community 25 - "tests/test_events.py"
Cohesion: 0.04
Nodes (61): Comm API doc (pyobs.comm), Events API doc (pyobs.events), BadWeatherEvent, Event to be sent on bad weather., Create Event from a dictionary. Args: obj_dict: JSON string for event. Returns:…, ExposureStatusChangedEvent, Event to be sent, when the exposure status of a device changes., FilterChangedEvent (+53 more)

### Community 26 - "test_csvpicker_scheduler.py"
Cohesion: 0.25
Nodes (20): make_dynamic_task(), make_vfs(), asyncio, integration, Path, CsvPicker filters out targets that fail the airmass constraint., OnDemandScheduler resolves DynamicTarget via CsvPicker to a SiderealTarget., Scheduler produces no observations when all CSV targets are invisible. (+12 more)

### Community 27 - "LcoTask"
Cohesion: 0.08
Nodes (30): Any, LcoRequest, LcoSchedulableRequest, LcoTask, Any, Target, Returns observation_type of this task. Returns: observation_type of this task., Whether this task is allowed to start later than the user-set time, e.g., for… (+22 more)

### Community 28 - "test_mastermind.py"
Cohesion: 0.07
Nodes (45): Mastermind, Any, Returns FITS header for the current status of this module. Args: namespaces: If…, Mastermind for a full robotic mode., Compute and persist the next per-night observation number. Returns: Compound…, MemoryObservationArchive, Returns filtered observations. Args: task: If given, only return observations…, In-memory observation archive for testing and simple deployments. (+37 more)

### Community 29 - "WindowingWidget"
Cohesion: 0.05
Nodes (14): BinningWidget, DataDisplayWidget, PrimaryHDU, Slot, Select path for auto-saving., ExposeWidget, Slot, ExposureTimeWidget (+6 more)

### Community 30 - "Interfaces (pyobs.interfaces) API doc"
Cohesion: 0.04
Nodes (53): Interfaces (pyobs.interfaces) API doc, IAbortable, IAcquisition, IAutoFocus, IAutoGuiding, IAutonomous, IBinning, ICalibrate (+45 more)

### Community 31 - "test_control.py"
Cohesion: 0.12
Nodes (47): CasesRunner, Script for distinguishing cases., ConditionalRunner, Script for running an if condition., ParallelRunner, Script for running other scripts in parallel., Script for running a sequence of other scripts., SequentialRunner (+39 more)

### Community 32 - "test_presence.py"
Cohesion: 0.05
Nodes (52): Announce this module to already-connected peers, mirroring XmppComm's presence-…, ModuleOpenedEvent, Event to be sent when a module has opened., ModuleLocation, _FakeProxyContext, make_xmpp_comm(), asyncio, Tests for Phase 2.5 Presence and Capabilities implementation. (+44 more)

### Community 33 - "LogScript"
Cohesion: 0.26
Nodes (12): DebugTriggerScript, Script for a debug trigger., LogScript, Script for logging something., asyncio, Expression has access to 'now' as a datetime., test_debug_trigger_can_run(), test_debug_trigger_sets_triggered() (+4 more)

### Community 34 - "test_lco_http.py"
Cohesion: 0.09
Nodes (43): Camera, CameraType, ConfigurationType, Enclosure, Instrument, InstrumentType, Mode, ModeType (+35 more)

### Community 35 - "enums.py"
Cohesion: 0.02
Nodes (130): IDome, The module controls a dome, i.e. a :class:`~pyobs.interfaces.IRoof` with a…, FiltersCapabilities, FilterState, IFilters, Any, The module can change filters in a device., Set the current filter. Args: filter_name: Name of filter to set. Raises:… (+122 more)

### Community 36 - "Future"
Cohesion: 0.08
Nodes (36): Wait until all devices are in one of the given motion states. Args: abort:…, Run script. Raises: InterruptedError: If interrupted, acquire_lock(), event_wait(), Future, Any, Lock, Sets a new timeout for the method call. Cancels any existing timeout handle and… (+28 more)

### Community 37 - "VirtualFileSystem"
Cohesion: 0.08
Nodes (23): Any, DataFrame, HDUList, Convenience function for writing an Image to a FITS file. Args: filename: Name…, Convenience function for writing an Image to a FITS file. Args: filename: Name…, Convenience function for writing bytes to a file. Args: filename: Name of file…, Convenience function for reading a CSV file into a DataFrame. Args: filename:…, Convenience function for writing a CSV file from a DataFrame. Args: filename:… (+15 more)

### Community 38 - "CoolingState"
Cohesion: 0.09
Nodes (29): _dataclass_to_xml(), _event_schema_to_xml(), _interface_schema_to_xml(), _parse_scalar(), Any, Element, Shared XML serializer for pyobs 2.0 (urn:pyobs:rpc:1). Both the state pub/sub…, Deserialize an XML element (produced by ``value_to_xml``) to a Python value.… (+21 more)

### Community 39 - "IPointingAltAz.py"
Cohesion: 0.06
Nodes (40): AltAzState, IPointingAltAz, The module can move to Alt/Az coordinates, usually combined with…, IPointingRaDec, RaDecState, The module can move to RA/Dec coordinates, usually combined with…, build_skycoord(), FollowMixin (+32 more)

### Community 40 - "test_astroplanscheduler.py"
Cohesion: 0.09
Nodes (38): AstroplanScheduler, Any, ObservingBlock, Actually do the scheduling, usually run in a separate process., Scheduler based on astroplan., Initialize a new scheduler. Args: twilight: astronomical or nautical, Queue, _EmptyPicker (+30 more)

### Community 41 - "reset_network"
Cohesion: 0.67
Nodes (3): fixture, Reset LocalNetwork singleton before each test., reset_network()

### Community 42 - "NextImage"
Cohesion: 0.15
Nodes (12): LastImage, NextImage, Any, NamedTuple, NDArray, Create a JPEG ge from a numpy array and return as bytes. Args: data: Numpy…, Create FITS and JPEG images from data., Create an Image object from numpy array. Args: data: Numpy array to convert to… (+4 more)

### Community 43 - "Comm"
Cohesion: 0.04
Nodes (36): Comm responsibility: Discovery (clients_with_interface), Comm responsibility: Events (broadcast typed events), Comm, Any, ProxyType, setter, Returns object directly if it is of given type. Otherwise get proxy of client…, Backend hook, called when a proxy exists but doesn't implement obj_type.… (+28 more)

### Community 44 - "test_transitimaging.py"
Cohesion: 0.08
Nodes (34): EarthLocation, model_validator, Self, SkyCoord, Merit function for observing transits., Returns the time of the next mid-transit., Returns the time until which observations should run: mid-transit + duration/2…, TransitMerit (+26 more)

### Community 45 - "robotic/test_scheduler.py"
Cohesion: 0.10
Nodes (45): Any, Event to be sent when a task has finished., Initializes a new task finished event. Args: name: Name of task that just…, TaskFinishedEvent, Scheduler, DummyTask, make_async_gen(), make_obs() (+37 more)

### Community 46 - "StandAlone"
Cohesion: 0.09
Nodes (40): pyobs.modules.test (doc), StandAlone, Quickstart (doc), pyobs-core (pip package), Test modules. TODO: write doc, Any, Example module that only logs the given message forever in the given interval., Creates a new StandAlone object. Args: message: Message to log in the given… (+32 more)

### Community 47 - "utils/exceptions.py"
Cohesion: 0.07
Nodes (34): PipelineCamera, Any, A virtual camera based on an image pipeline., Creates a new pipeline cammera., Grabs an image and returns reference. Args: broadcast: Broadcast existence of…, Declare that the given PyobsError types (and their subclasses) fire often…, AbortedError, AcquisitionError (+26 more)

### Community 48 - "._run_configurations"
Cohesion: 0.50
Nodes (3): Any, Target, Loop instrument configurations until the transit window ends.

### Community 49 - "test_stellarexptime.py"
Cohesion: 0.09
Nodes (37): ExposureTimeProvider, Determine and return the exposure time in seconds. Returns: Exposure time in…, Abstract base class for providers that determine camera exposure time., ndarray, Find the brightest star near the image centre by fitting a 2D Gaussian. Args:…, Determines exposure time by finding a star near the image centre and adjusting…, Determine the optimal exposure time. Returns: Optimal exposure time in seconds., StellarExposureTimeProvider (+29 more)

### Community 50 - "StarExpTimeEstimator"
Cohesion: 0.07
Nodes (28): Additional Modules index (docs), Image processors index (docs), Calibration processors doc, Exposure Time estimators doc, ExpTimeEstimator (exptime processor base), StarExpTimeEstimator (exptime processor), ExpTimeEstimator, Any (+20 more)

### Community 51 - "RPC"
Cohesion: 0.08
Nodes (23): fault_to_xml(), params_to_xml(), Any, ClientXMPP, Element, Exception, Parse <fault> and return (exception_qualified_name, message)., RPC wrapper around XEP-0009 using pyobs 2.0 payload encoding (urn:pyobs:rpc:1). (+15 more)

### Community 52 - "WindowCapabilities"
Cohesion: 0.08
Nodes (41): ModuleCapabilities, WindowCapabilities, make_module(), Minimal module stub satisfying what XmppComm needs on connect. IModule must be…, get_capabilities_from_disco(), Integration tests for Phase 2.5 Presence and Discovery. Requires a live…, LOCAL state must arrive as away presence., Module.set_state() must automatically push presence — no explicit call. (+33 more)

### Community 53 - "test_shellcommand.py"
Cohesion: 0.10
Nodes (29): ParserState, Any, Enum, ShellCommand, ShellCommandResponse, asyncio, test_command_number_increments(), test_execute_invalid_param() (+21 more)

### Community 54 - "Calibration"
Cohesion: 0.10
Nodes (18): Calibration, Calibrate an image. Args: image: Image to calibrate. Returns: Calibrated image., Calibrate an image using master bias, dark, and flat frames fetched from an…, Find master calibration frame for given parameters using a cache. Args:…, _CCDDataCalibrator, CCDData, ConcreteArchive, mock_image() (+10 more)

### Community 55 - "Any"
Cohesion: 0.11
Nodes (16): ObjectClass, create_object(), get_object(), get_safe_object(), Any, ProxyType, Calls get_object in a safe way and returns None, if an exceptions thrown. Args:…, Create object from dict config. Args: config: Config to create object from… (+8 more)

### Community 56 - "Publisher"
Cohesion: 0.21
Nodes (10): CsvPublisher, LogPublisher, MultiPublisher, Any, Forwards a message to multiple publishers., Initialize new multi publisher. Args: publishers: Publishers to forward…, Publish the given results. Args: **kwargs: Results to publish., Publisher (+2 more)

### Community 57 - ".__init__"
Cohesion: 0.06
Nodes (31): Annotation processors doc, Any, Init new image processor. Args: on_error: How the pipeline should handle an…, Circle, Any, Init a new circle processor. Args: x: Center x coordinate. y: Center y…, Draw a circle on an image, optionally interpreting the center in WCS…, Draws a circle on the image. Args: image: Image to draw on. Returns: Output… (+23 more)

### Community 58 - "Unit"
Cohesion: 0.10
Nodes (28): Enumerator for canonical physical units used on the wire. Attributes: DEGREES:…, The equivalent astropy.units unit, for code that needs to build a Quantity., Unit, _extract_unit(), _interface_unit_hints(), Any, Return Unit annotations from the abstract interface declaration for method_name., Convert annotated float parameters to astropy Quantities before the method… (+20 more)

### Community 59 - "Proxy"
Cohesion: 0.06
Nodes (33): Comm responsibility: Method calls (via Proxy), The Comm object is responsible for all communication between modules (see…, Proxy, _ProxyContext, Any, ProxyType, Signature, Execute a method on the remote client. Args: method: Name of method to call.… (+25 more)

### Community 60 - "FitsHeaderOffsets"
Cohesion: 0.19
Nodes (10): GenericOffset, FitsHeaderOffsets, Any, Compute a 2D offset from FITS header coordinates and store it in image…, Initializes new fits header offsets., Processes an image and sets x/y pixel offset to reference in offset attribute.…, asyncio, test_attribute_validation() (+2 more)

### Community 61 - "test_basevideo.py"
Cohesion: 0.16
Nodes (34): ImageRequest, make_basevideo(), make_request(), asyncio, test_activate_camera_from_inactive_calls_hook(), test_activate_camera_when_already_active_skips_hook(), test_active_update_deactivates_after_sleep_timeout(), test_active_update_skips_deactivate_when_recently_active() (+26 more)

### Community 62 - "SkyFlatsBasePointing"
Cohesion: 0.14
Nodes (12): Move telescope. Args: telescope: Telescope to use., Base class for flat pointings., SkyFlatsBasePointing, model_validator, Self, Static flat pointing., Move telescope. Args: telescope: Telescope to use., SkyFlatsStaticPointing (+4 more)

### Community 63 - "test_yaml_archives.py"
Cohesion: 0.24
Nodes (28): make_obs(), make_obs_archive(), make_task(), make_task_archive(), asyncio, Verify observations are actually written to disk in valid YAML., test_add_and_load_observations(), test_add_empty_list_is_noop() (+20 more)

### Community 64 - "FlatFielder"
Cohesion: 0.09
Nodes (21): ICamera, The module controls a camera., Initialize a new flat fielder. Args: telescope: Name of ITelescope. camera:…, FlatFielder, Enum, Calls next step in state machine. Args: telescope: Telescope to use. camera:…, Returns True, if functions are based on filters., Do a quick initial check. Returns: False, if flat-field time for this filter is… (+13 more)

### Community 65 - "IExposure"
Cohesion: 0.06
Nodes (34): Comm._get_client, ADR-0001: Check Interface.state by own declaration, not inheritance, Composite interfaces inheriting stateful bases (ICamera, IDome, ITelescope, ...), Interface.capabilities (ClassVar), Interface.has_own_state(), Interface.state (ClassVar), XmppComm disco#info feature registration, ADR-0006: Proxy.wait_for_state() returns None on timeout (+26 more)

### Community 66 - "Telegram"
Cohesion: 0.16
Nodes (11): CallbackContext, Save storage file. Args: context: Telegram context., Store new user in auth database. Args: context: Telegram context. user_id: ID…, Handle click on buttons. Args: update: Message to process. context: Telegram…, Handle input of params when in EXEC_PARAMS state. Args: update: Message to…, Handle input of params when in EXEC_PARAMS state. Args: update: Message to…, Args: context: Telegram context. chat_id: Telegram chat ID. call_id: ID of…, Handle normal text messages, e.g. for login or method parameters. Args: update:… (+3 more)

### Community 67 - "XmppConfig"
Cohesion: 0.12
Nodes (29): Open the connection to the XMPP server. Returns: Whether opening was successful., env_config(), main(), make_comm(), maybe_register(), open_publisher(), Any, Build an unopened XmppComm for ``<user>@<domain>``. (+21 more)

### Community 68 - "OffsetResult"
Cohesion: 0.09
Nodes (25): ITelescope, The module controls a telescope., Any, Initializes a new base pointing. Args: telescope: Telescope to use. pipeline:…, ApplyAltAzOffsets, Any, EarthLocation, Apply offsets from a given image to a given telescope. (+17 more)

### Community 69 - "Offsets"
Cohesion: 0.07
Nodes (27): PixelOffsets, AstrometryOffsets, CorrelationMaxCloseToBorderError, Any, Exception, SkyCoord, Compute pixel offsets from WCS by comparing image reference coordinates to…, Initializes new astrometry offsets. MUST run after an astrometry processor. (+19 more)

### Community 70 - ".now"
Cohesion: 0.13
Nodes (21): Observer, ObservationArchiveEvolution, date, Observer, Populates the task cache and the one real night (anchored to `start`) up front.…, Freezes observation cache. After this: a task-id miss raises RuntimeError; a…, Returns list of observations for the given task. Args: date: Date of night to…, Add or replace a task. Updates last_changed timestamp. (+13 more)

### Community 71 - "PyObsError"
Cohesion: 0.07
Nodes (31): ADR-0003: Restrict Proxy access to async with, has_proxy() / safe_proxy, Proxy, _ProxyContext.__await__ (removed), specs/design/pyobs_2_0_wire_protocol.md, acl: config block (allow/deny), ADR-0004: Enforce access control on the callee, not the caller, Module.execute() (+23 more)

### Community 72 - "test_proxy.py"
Cohesion: 0.12
Nodes (33): _cooling_state(), make_proxy(), asyncio, Methods from both interfaces are callable., A CoolingState timestamped `age_seconds` in the past., Callers that don't pass max_age see no behavior change, however old the cached…, A future interface whose State dataclass has no `time` field fails loudly at…, Create a Proxy with a mock comm. (+25 more)

### Community 73 - "XEP_0009"
Cohesion: 0.07
Nodes (13): BasePlugin, Expose method to public., Expose method to public., Expose method to public., Small fix for the original XEP_0009 plugin., Route RPC-level errors (e.g. forbidden, item-not-found) through the same…, XEP_0009, A plugin for SleekXMPP, adding a timeout to RPC calls. (+5 more)

### Community 74 - "SiderealTarget"
Cohesion: 0.06
Nodes (46): AirmassConstraint, ndarray, SkyCoord, MoonSeparationConstraint, ndarray, SkyCoord, Moon separation constraint., model_validator (+38 more)

### Community 75 - "PyobsDaemon"
Cohesion: 0.14
Nodes (10): Any, PyobsDaemon, Return the bare module name from a config or PID file path., Strip a leading underscore, which marks a module as disabled. PID and log files…, Return sorted module names from *.yaml files, excluding *.shared.yaml., Read and return the PID from the module's PID file, or None., Return the live PID for a module, or None. Cleans up stale PID files., Return uptime (seconds) and rss_mb for a running PID. No CPU -- that needs a… (+2 more)

### Community 76 - "MockWeather"
Cohesion: 0.14
Nodes (21): MockWeather, Any, Return value for given sensor. Args: station: Name of weather station to get…, Returns FITS header for the current status of this module. Args: namespaces: If…, A mock weather station for testing and simulations., Creates a new mock weather station. Args: good: Initial weather-good state.…, Set the simulated weather-good state, for use in tests and simulations. Fires a…, asyncio (+13 more)

### Community 77 - "test_config.py"
Cohesion: 0.10
Nodes (31): include_parts(), pre_process_yaml(), Any, Replaces blocks of the form {include <source.yaml> <key>} in the loaded config…, Include nested contents from another YAML file. Args: include: dictionary based…, Finds anchors ('&') in the included file. Args: filename: name of the file with…, Replaces aliases ('<<: *...') in the main file by the anchor in the included…, reload_anchors() (+23 more)

### Community 78 - "ImageType"
Cohesion: 0.12
Nodes (15): ProgressEvent, Any, Set the image type. Args: image_type: New image type., ImageType, Enumerator specifying the image type. Attributes: BIAS: Bias/zero exposure.…, Find and download master calibration frame. Args: archive: Image archive.…, MasterCalibCreated, A master calibration frame (BIAS/DARK/SKYFLAT) was created and stored/uploaded. (+7 more)

### Community 79 - "test_autoguiding.py"
Cohesion: 0.20
Nodes (32): make_guiding(), make_image(), asyncio, _state_for(), test_auto_guiding_sleeps_when_disabled(), test_auto_guiding_takes_and_processes_image_when_enabled(), test_get_fits_header_after_includes_statistics(), test_get_fits_header_before_reports_closed_loop() (+24 more)

### Community 80 - "Weather"
Cohesion: 0.15
Nodes (24): Builds the current per-sensor readings from the last raw status, for state…, Connection to pyobs-weather., Weather, asyncio, test_active_flag_defaults_true_and_tracks_stop(), test_calc_system_init_eta(), test_get_fits_header_before(), test_get_fits_header_before_invalid() (+16 more)

### Community 81 - "FileSystemObservationArchive"
Cohesion: 0.08
Nodes (17): Any, FileSystemObservationArchive, Any, date, Clear schedule after given start time. Args: start_time: Start time to clear…, Fetch schedule from portal. Returns: Dictionary with tasks. Raises: Timeout: If…, Returns the active scheduled task at the given time. Args: time: Time to return…, Returns the currently running observation. Args: task_archive: Task archive to… (+9 more)

### Community 82 - "SkyOffsets"
Cohesion: 0.13
Nodes (18): BaseCoordinateFrame, Angle, SkyCoord, Returns separatation between both coordinates, either in their own or a given…, Calculates spherical offset from first coordinate to second. Args: frame:…, Args: frame: Coordinate frame to use, or None to use coordinates' own frames.…, SkyOffsets, Any (+10 more)

### Community 83 - "weather.py"
Cohesion: 0.08
Nodes (19): IAutonomous, The module does some autonomous actions, mainly used for warnings to users., IStartStop, Any, The module can be started and stopped., IWeather, The module acts as a weather station., WeatherSensorReading (+11 more)

### Community 84 - "Object"
Cohesion: 0.12
Nodes (23): PydanticBaseModel, Object, Base class for all objects in *pyobs*., Whether object has been opened., Can be overloaded to quit program., ConfigurationStatus, ConfigurationSummary, LcoAcquisitionConfig (+15 more)

### Community 85 - "Ring"
Cohesion: 0.14
Nodes (9): integer, Any, floating, NDArray, Estimate pixel guiding offsets from asymmetry of spilled light around a fiber…, Init an image processor that adds the calculated offset. Args: fibers:…, Processes an image and sets x/y pixel offset to reference in offset attribute.…, Ring (+1 more)

### Community 86 - "DummySolarTelescope"
Cohesion: 0.13
Nodes (19): DummySolarTelescope, Any, Moves to and continuously tracks a Heliocentric Polar (mu, psi) coordinate., Moves to and continuously tracks a Heliographic Stonyhurst (lon, lat)…, Moves to and continuously tracks a Helioprojective (theta_x, theta_y)…, Background task: while a solar-relative target is active, keeps the simulated…, A dummy telescope dedicated to solar pointing (Heliocentric Polar/Heliographic…, Converts Heliocentric Polar (mu, psi) to (ra, dec) in degrees, ICRS. Mirrors… (+11 more)

### Community 87 - "xmppcomm.py"
Cohesion: 0.07
Nodes (26): Any, Disconnect only, instead of slixmpp's default reconnect-in-place. xep_0199's…, Called when the server sends a <stream:error/>, e.g. when this connection gets…, Whether this client was (or is being) kicked because another session connected…, Human-readable reason text sent alongside the conflict stream error, if any., Wait for client to connect. Returns: Success or not., XMPP client for pyobs., Session start event. Args: event: The event sent at session start. (+18 more)

### Community 88 - "test_exception_logging.py"
Cohesion: 0.11
Nodes (31): PresenceCallback, Register a presence callback and deliver the current state immediately., Callback for flat-field class to call with statistics., FocusError, ForbiddenError, The call itself didn't reach/return -- a transport failure, not a domain…, Raised when a caller is not permitted to invoke a method under the target…, RemoteError (+23 more)

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
Cohesion: 0.12
Nodes (23): Any, get_class_from_string(), Get class from a given string. Args: class_name: Name of class as string.…, _build_params_model(), CallModuleScript, _get_valid_param_names(), model_validator, Script for calling a method on a module. (+15 more)

### Community 93 - "ProjectedOffsets"
Cohesion: 0.14
Nodes (20): ProjectedOffsets, Any, floating, NDArray, Processes an image and sets x/y pixel offset to reference in offset attribute.…, Project image along x and y axes and return results. Args: image: Image to…, Compute pixel offsets for guiding by correlating 1D projections of the current…, Initializes a new auto guiding system. (+12 more)

### Community 94 - "test_pyobs_archive.py"
Cohesion: 0.20
Nodes (23): PyobsArchiveFrameInfo, Frame info for pyobs archive., make_archive(), make_frame_dict(), MockResponse, Any, asyncio, test_download_frames_returns_images() (+15 more)

### Community 95 - "HttpFile"
Cohesion: 0.11
Nodes (18): ArchiveFile, Wraps a file in an archive. To be used in combination with pyobs-archive., Creates a new archive file. Args: name: Name of file. mode: Open mode (r/w).…, If in write mode, actually send the file to the archive., HttpFile, Any, Read number of bytes from stream. Args: n: Number of bytes to read. Read until…, Write data into the stream. Args: s: Bytes of data to write. (+10 more)

### Community 96 - ".__init__"
Cohesion: 0.40
Nodes (3): Any, Any, Initialize a new scheduler. Args: twilight: astronomical or nautical

### Community 97 - "application.py"
Cohesion: 0.09
Nodes (18): _disable_iers_auto_download(), GuiApplication, InfluxLogConfig, Any, TypedDict, Derived Application class that uses a Qt GUI. Allows for graceful shutdown in…, Create a new GUI application., Initializes a pyobs application. Exactly one of `config`/`module_factory` must… (+10 more)

### Community 98 - "FocusSeries"
Cohesion: 0.05
Nodes (39): fit_hyperbola(), Fit a hyperbola Args: x_arr: X data y_arr: Y data y_err: Y errors Returns:…, FocusSeries, Analyse given image. Args: image: Image to analyse focus_value: Value to fit…, Returns a list of data points., Fit focus from analysed images Returns: Tuple of new focus and its error, Base class for focus series helper classes., PhotometryFocusSeries (+31 more)

### Community 99 - "_SourceCatalog"
Cohesion: 0.09
Nodes (16): Any, floating, NDArray, PySepStatsCalculator, Any, DataFrame, floating, NDArray (+8 more)

### Community 100 - "make_proxy_cm"
Cohesion: 0.21
Nodes (27): make_proxy_cm(), Wrap value in a MagicMock standing in for the async context manager returned by…, make_flatfield(), asyncio, Find the state object set_state() was called with for the given interface., _ready_telescope(), _state_for(), test_abort_sets_event() (+19 more)

### Community 101 - "WeatherSensors"
Cohesion: 0.11
Nodes (18): Any, Return value for given sensor. Args: station: Name of weather station to get…, Set a simulated sensor's value, for use in tests and simulations. Args: sensor:…, Any, ClientSession, WeatherApi, Return value for given sensor. Args: station: Name of weather station to get…, The weather station's API response was malformed or incomplete (missing an… (+10 more)

### Community 102 - "ScriptRunner"
Cohesion: 0.14
Nodes (15): calc_run_timeout(), Any, Calculates timeout for run()., Module for running a script., Initialize a new script runner. Args: script: Config for script to run., Run script. Raises: ScriptError: If the script failed (e.g. a proxy/network…, Abort current actions., ScriptRunner (+7 more)

### Community 103 - "ResolvableErrorLogger"
Cohesion: 0.17
Nodes (9): Any, Creates a new LCO scheduler. Args: url: URL to portal site: Site filter for…, Any, Logger, Logging for resolvable errors. Args: logger: Logger to use. error_level: Log…, Log an error message., ResolvableErrorLogger, create_logger() (+1 more)

### Community 104 - "test_coordinates.py"
Cohesion: 0.15
Nodes (25): offset_altaz_to_radec(), offset_radec_to_altaz(), EarthLocation, SkyCoord, make_altaz(), make_radec(), SkyCoord, Zero offset returns (0, 0). (+17 more)

### Community 105 - "get_registered_interface"
Cohesion: 0.12
Nodes (22): get_registered_interface(), Look up a registered interface class by name, or None if unknown., All currently-registered interface classes, keyed by name., registered_interfaces(), Tests for the import-time interface registry in pyobs/interfaces/interface.py.…, Re-importing the same interface module twice resolves to the same class object…, Two genuinely different classes claiming the same name must raise TypeError…, Mutating the returned dict must not affect the live registry. (+14 more)

### Community 106 - "SolarElevationConstraint"
Cohesion: 0.17
Nodes (27): AtNightConstraint, Solar elevation constraint., SolarElevationConstraint, constraint(), data(), observer(), asyncio, fixture (+19 more)

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
Cohesion: 0.17
Nodes (19): BackgroundTask, Any, make_task(), asyncio, Too many fast failures calls parent.quit() when restart=True., Too many fast failures with restart=False just stops without calling quit., Failures spread over time don't trigger the rapid-failure quit., test_cancelled_error_exits_cleanly() (+11 more)

### Community 113 - "Test Commlogging (comm)"
Cohesion: 0.12
Nodes (20): Send an event to all connected modules. Args: event: Event to send.…, CommLoggingHandler, Any, A logging handler that sends all messages through a Comm module., Create a new logging handler. Args: comm: Comm module to use., Send a new log entry to the comm module. Args: rec: Log record to send., comm(), handler() (+12 more)

### Community 114 - "TaskFailedEvent"
Cohesion: 0.06
Nodes (19): Any, JSON representation of event., String representation of event., Generic from_dict method for derived classes that don't need their own., Any, Any, Any, Any (+11 more)

### Community 115 - "test_dummyradectelescope.py"
Cohesion: 0.24
Nodes (21): TrackingRateCapabilities, make_dummyradectelescope(), asyncio, test_move_altaz_clears_tracked_body(), test_move_altaz_resets_tracking_mode_to_off(), test_move_radec_clears_tracked_body(), test_move_radec_resets_tracking_mode_to_sidereal(), test_move_task_applies_tracking_rate_to_position() (+13 more)

### Community 116 - "ImagingScript"
Cohesion: 0.15
Nodes (9): ImagingScript, Any, Target, Run script. Raises: InterruptedError: If interrupted, Returns FITS header for the current status of this module. Args: namespaces: If…, Estimate the duration of this script in seconds., Return the exposure time, computing it dynamically if needed., Default script for imaging configs. (+1 more)

### Community 117 - "test_acquisition.py"
Cohesion: 0.28
Nodes (28): make_acquisition(), make_camera(), make_image(), make_telescope(), asyncio, offsets_frame: 'radec', 'altaz', or None (telescope supports neither offsets…, _state_for(), test_abort_sets_event() (+20 more)

### Community 118 - "BufferedFile"
Cohesion: 0.10
Nodes (11): BufferedFile, Base class for all byffered VFS file classes., MemoryFile, Any, A file stored in memory., Open/create a file in memory. Args: name: Name of file. mode: Open mode., Read number of bytes from stream. Args: n: Number of bytes to read, -1 reads…, Write data into the stream. Args: buf: Bytes of data to write. (+3 more)

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
Cohesion: 0.11
Nodes (28): OptimalFocusState, FocusModel, FocusTimeoutError, MissingSensorError, Returns the optimal focus. Args: filter_name: If given, use this filter name…, The weather station returned an invalid/missing reading -- plausibly transient,…, Retrieve all required values for the model. Returns: Dictionary containing all…, Timed out waiting for a temperature reading from another module -- plausibly… (+20 more)

### Community 125 - "OffsetsAltAzEvent"
Cohesion: 0.11
Nodes (14): DataTypeAltAz, DataTypeRaDec, OffsetsAltAzEvent, OffsetsEvent, OffsetsRaDecEvent, Any, TypedDict, Event to be sent when an RA/Dec offset is to be moved. (+6 more)

### Community 126 - "ImageSourceFilter"
Cohesion: 0.12
Nodes (17): ImageSourceFilter, Any, floating, NDArray, Table, Filters the source table after pysep detection has run Args:…, Filter a source catalog by border distance, quality metrics, and brightness,…, Convert from FITS to numpy conventions for pixel coordinates. (+9 more)

### Community 127 - "test_darkbias.py"
Cohesion: 0.20
Nodes (20): DarkBiasScript, Script for running darks or biases., Whether this config can currently run. Returns: True if script can run now., Run script. Raises: InterruptedError: If interrupted, Estimate duration of the dark/bias series., make_camera(), make_script(), asyncio (+12 more)

### Community 128 - "Portal"
Cohesion: 0.12
Nodes (11): Portal, Any, Do a GET request on the portal. Args: url: URL to request. Returns: Response…, Clear schedule after given start time. Args: start: Start time to clear…, Submit observations. Args: observations: List of observations to submit., Send report to LCO portal Args: status_id: id of config status status: Status…, Delay re-attempt to send report to LCO portal Args: status_id: id of config…, Fetch schedule from portal. Args: start_before: Task must start before this… (+3 more)

### Community 129 - "GridNode"
Cohesion: 0.16
Nodes (19): AvoidMoon, ConvertGridFrame, ConvertGridToSkyCoord, FromList, GridFilterValue, Convert (x, y) degree tuples to SkyCoord objects. Wraps a tuple-producing grid…, Transform SkyCoord points to a different frame., Remove points too close to the moon. If the next point in the underlying grid… (+11 more)

### Community 130 - "Plan: pyobs-pipeline"
Cohesion: 0.08
Nodes (24): Celery task, Consequences, Django models, Implementation checklist, Log viewing, Open questions, Pages, Pipeline builder (+16 more)

### Community 131 - "Test Localcomm (local)"
Cohesion: 0.18
Nodes (22): make_comm(), asyncio, fixture, Sender also receives its own events., Reset LocalNetwork singleton between tests., #677: a late-joining module must announce itself via ModuleOpenedEvent once…, get_interfaces returns [] when the remote client has no module., reset_network() (+14 more)

### Community 132 - "SepSourceDetection"
Cohesion: 0.16
Nodes (17): Background, Any, floating, NDArray, Initializes a wrapper for SEP. See its documentation for details. Highly…, Find stars in given image and append catalog. Args: image: Image to find stars…, Remove background from image in data. Args: data: Data to remove background…, Detect astronomical sources using SEP (Source Extractor for Python). This… (+9 more)

### Community 133 - "test_schedulewriter.py"
Cohesion: 0.19
Nodes (18): InstrumentLocation, ConfigDB, make_portal(), Shared helpers for LCO tests., Create Portal bypassing Object.__init__ and aiohttp session., make_configdb(), make_lco_observation(), make_writer() (+10 more)

### Community 134 - "DummyMode"
Cohesion: 0.08
Nodes (20): IMode, ModeCapabilities, ModeState, Any, The module can change modes in a device., Set the current mode. Args: mode: Name of mode to set. group: Name of the group…, DummyMode, Any (+12 more)

### Community 135 - "test_dummymode.py"
Cohesion: 0.32
Nodes (13): _event_of_type(), make_dummymode(), asyncio, Find the most recent state object set_state() was called with for the given…, Find the send_event() call with an event of the given type., _state_for(), test_init_default_modes(), test_init_park_stop_motion_are_noops() (+5 more)

### Community 136 - "_ResponseImageWriter"
Cohesion: 0.24
Nodes (4): Any, WCS, astrometry.net gives a CD matrix, so we have to delete the PC matrix and the…, _ResponseImageWriter

### Community 137 - "test_autofocus.py"
Cohesion: 0.23
Nodes (20): AutoFocusScript, Script for running autofocus series., isinstance_class(), Shared test-double helpers used across multiple test modules., Build a fresh class purely for isinstance() checks against a MagicMock.…, make_autofocus(), make_script(), make_task() (+12 more)

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

### Community 142 - "is_valid_jid"
Cohesion: 0.21
Nodes (6): is_valid_jid(), Whether jid is a valid user@domain or user@domain/resource JID -- exactly what…, JID parsing/validation in XmppComm.__init__ and the reusable is_valid_jid()…, The actual production bug this was found from: a JID ending in "/" with nothing…, re.match alone doesn't anchor the end -- confirms the pattern is anchored so…, TestIsValidJid

### Community 143 - "test_lcoscript.py"
Cohesion: 0.17
Nodes (18): FakeScript, make_lco_script(), make_request(), Any, asyncio, Minimal script used to verify LcoScript's dispatch., can_run() resolves and delegates to the script named in…, run() delegates to the named script and copies its exptime_done back. (+10 more)

### Community 144 - "OnSkyDistance"
Cohesion: 0.13
Nodes (16): OnSkyDistance, Angle, BrightestStarOffsets, Angle, Any, Table, Processes an image and sets x/y pixel offset to reference in offset attribute.…, Compute pixel offsets from the image center to the brightest star and store… (+8 more)

### Community 145 - "DummyRaDecTelescope"
Cohesion: 0.09
Nodes (23): AltAzOffsetState, IOffsetsAltAz, The module supports Alt/Az offsets, usually combined with…, IOffsetsRaDec, RaDecOffsetState, The module supports RA/Dec offsets, usually combined with…, DummyAltAzTelescope, Any (+15 more)

### Community 146 - "Scheduler"
Cohesion: 0.15
Nodes (7): Any, Compares two lists of tasks and returns two lists, containing those that are…, Trigger a re-schedule., Re-schedule when task has started and we can predict its end. Args: event: The…, Reset current task, when it has finished or failed. Args: event: The task…, Re-schedule on incoming good weather event. Args: event: The good weather…, Scheduler

### Community 147 - "datetime"
Cohesion: 0.06
Nodes (50): datetime, GuidingStatisticsUptime, Any, Runs an async callable to completion on a dedicated worker thread, off the…, run_cpu_bound(), RollingTimeAverage, ConfigFieldSchema, ConfigSchema (+42 more)

### Community 148 - ".__init__"
Cohesion: 0.11
Nodes (12): PydanticModel, PrivateAttrMixin, EarthLocation, Observer, Location of the observer, derived from :attr:`observer` (there is no separately…, Validate a pydantic model with additional fields., .. note:: Objects must always be opened and closed using…, Any (+4 more)

### Community 149 - "Observation"
Cohesion: 0.04
Nodes (41): Observation, Any, Fetch a task from the task archive., Updates observation. Args: observation: Observation to update., AcquisitionConfig, Configuration, GuidingConfig, InstrumentConfig (+33 more)

### Community 151 - "`OBSNUM`: per-night observation counter in FITS headers"
Cohesion: 0.22
Nodes (8): Migration, `OBSNUM`: per-night observation counter in FITS headers, Problem, Proposed design, Still open (not resolved by this doc), When is `obsnum` assigned: scheduled, or observed?, Where the pieces actually are, Why this determines the design, not just where to put a function

### Community 152 - "3rd party packages (doc)"
Cohesion: 0.11
Nodes (20): 3rd party packages (doc), Astroplan, Astropy, Astroquery, Cython, LMFIT, matplotlib, NumPy (+12 more)

### Community 153 - "_DaoBackgroundRemover"
Cohesion: 0.05
Nodes (40): Source Detection processors doc, DaophotSourceDetection (detection processor), SepSourceDetection (detection processor), _DaoBackgroundRemover, Any, floating, NDArray, DaophotSourceDetection (+32 more)

### Community 154 - "SSHFile"
Cohesion: 0.12
Nodes (12): Any, VFS wrapper for a file that can be accessed over a SFTP connection., Write data into the stream. Args: b: Bytes of data to write., If in write mode, actually send the file to the SSH server., Returns content of given path. Args: path: Path to list. kwargs: Parameters for…, Open/create a file over a SSH connection. Args: name: Name of file. mode: Open…, For read access, download the file into a local buffer. Raises:…, Read number of bytes from stream. Args: n: Number of bytes to read. Read until… (+4 more)

### Community 155 - "create_rst.py"
Cohesion: 0.33
Nodes (18): create_image_processors_rst(), create_modules_rst(), create_rst_overview(), create_utils_rst(), find_classes_in_modules(), find_python_modules(), find_submodules(), Any (+10 more)

### Community 156 - "GuidingStatistics"
Cohesion: 0.17
Nodes (8): IN, OUT, GuidingStatistics, Any, Calculates statistics for guiding., Inits a stat measurement session for a client. Args: client: name/id of the…, Add statistics to given header. Args: client: id/name of the client header:…, Adds data to all client measurement sessions. Args: input_data: Image witch…

### Community 157 - "SoftBin"
Cohesion: 0.16
Nodes (11): Any, floating, NDArray, Bin a 2D image by averaging non-overlapping blocks, updating relevant FITS…, Init a new software binning pipeline step. Args: binning: Binning to apply to…, Bin an image. Args: image: Image to bin. Returns: Binned image., SoftBin, asyncio (+3 more)

### Community 158 - "AddMask"
Cohesion: 0.21
Nodes (13): AddMask, Any, floating, NDArray, Add mask to image. Args: image: Image to add mask to. Returns: Image with mask, Attach a precomputed mask to an image based on instrument and binning. This…, Init an image processor that adds a mask to an image. Args: masks: Dictionary…, asyncio (+5 more)

### Community 159 - "Archive"
Cohesion: 0.15
Nodes (10): Archive, FrameInfo, Any, Base class for frame infos., Base class for image archives., TypedDict, PyobsArchiveFrameInfoDict, _FlakyCalibArchive (+2 more)

### Community 160 - "RandomizeGrid"
Cohesion: 0.12
Nodes (11): SkyCoord, RandomizeGrid, Return the next point that satisfies all constraints. Iterates underlying…, Convert the next tuple to a SkyCoord. Expects a tuple (x_deg, y_deg) from the…, Transform the next SkyCoord to the target frame. Returns: A SkyCoord…, Randomize iteration order by rotating the underlying sequence. For each…, Yield a point after rotating the underlying grid a random number of times.…, Yield a point after rotating the underlying grid a random number of times.… (+3 more)

### Community 161 - "comm/test_events.py"
Cohesion: 0.18
Nodes (15): asyncio, Tests for Comm.register_event / unregister_event. Covers…, Two independent subscribers for the same event: one tearing down must not un-…, A module that both sends an event (handler-less register_event()) and…, unregister must mirror the exact same derived-events expansion register_event…, Two independent subscribers (e.g. two widget instances for the same event type)…, Once the last handler for an event is unregistered, the event must no longer be…, test_unregister_event_drops_subscribed_role_when_last_handler_removed() (+7 more)

### Community 162 - ".__init__"
Cohesion: 0.29
Nodes (5): Any, Pipeline, ProgressCallback, Pre-pass: list (not download) OBJECT frames for every instrument/binning/filter…, Creates a Reduction object for reducing a given observation period. Args:…

### Community 163 - "LogEvent"
Cohesion: 0.15
Nodes (7): LogEvent, Any, Event for log entries., Enum, TelegramUserState, test_log_event_properties(), test_log_event_roundtrip()

### Community 164 - "test_transit_mastermind.py"
Cohesion: 0.21
Nodes (20): Configuration, InstrumentConfig, make_transit_merit(), make_transit_observation(), make_transit_task(), asyncio, integration, Mastermind picks up a transit observation and runs it to completion. (+12 more)

### Community 165 - "ExpTimeEval"
Cohesion: 0.11
Nodes (15): ExpTimeEval, Any, Observer, Return list of binnings., Return list of filters., Estimate exposure time for given filter Args: solalt: Solar altitude. binning:…, Initialize object with the given time. Args: time: Start time for all further…, Estimates exposure time for a given filter and binning at a given time offset… (+7 more)

### Community 166 - "Stellarium"
Cohesion: 0.14
Nodes (8): BaseTransport, Any, Exception, Send coordinates to clients., A stellarium telescope., Initialize a new stellarium telescope proxy. Args: telescope: Name of telescope…, Stellarium, StellariumProtocol

### Community 167 - "Overview (doc)"
Cohesion: 0.18
Nodes (17): Overview (doc), Access control (ACL), Comm, Events, Interface, Module (base class), Object (base class), Location / astroplan.Observer (+9 more)

### Community 168 - "calibration.py"
Cohesion: 0.16
Nodes (9): _CalibrationCache, Any, Init a new image calibration pipeline step. Args: archive: Archive to fetch…, mock_image(), fixture, test_add_to_cache(), test_add_to_cache_size(), test_find_cache_entry_emtpy() (+1 more)

### Community 169 - "GuidingStatisticsPixelOffset"
Cohesion: 0.25
Nodes (7): GuidingStatisticsPixelOffset, Calculates RMS of data. Args: data: Data to calculate RMS for. Returns: Tuple…, mock_meta_image(), fixture, test_build_header_to_few_values(), test_end_to_end(), test_get_session_data()

### Community 170 - ".get_meta"
Cohesion: 0.40
Nodes (3): MetaClass, Returns meta information, assuming that it is stored under the class of the…, Calls get_meta in a safe way and returns default value in case of an exception.

### Community 171 - ".close"
Cohesion: 0.12
Nodes (5): Matrix, Any, Drain the message queue and send messages one at a time. Sending sequentially…, Process a new log entry. Args: entry: The log event. sender: Name of sender., Initialize a new bot. Args: server: Server to connect to. user_id: ID of user…

### Community 172 - "test_grab_sequence.py"
Cohesion: 0.29
Nodes (16): make_camera(), asyncio, Tests for BaseCamera.grab_sequence()/abort_sequence(), the IDataSequence…, grab_sequence() must not block for the whole sequence -- see design doc: a…, test_abort_clears_running_sequence(), test_abort_cuts_delay_short(), test_abort_sequence_cuts_delay_short(), test_abort_sequence_lets_current_grab_finish_but_stops_the_rest() (+8 more)

### Community 173 - "binding.py"
Cohesion: 0.23
Nodes (8): fault2xml(), py2xml(), Any, Element, rpcbase64, rpctime, xml2fault(), xml2py()

### Community 174 - "NewSpectrumEvent"
Cohesion: 0.14
Nodes (11): NewSpectrumEvent, Any, Event to be sent on a new image., Initializes new NewSpectrumEvent. Args: filename: Name of new image file., HDUList, Store spectrum at given destination. Can be overwritten by derived classes to…, Actually do the exposure, should be implemented by derived classes. Args:…, Wrapper for a single exposure. Args: broadcast: Whether or not the new image… (+3 more)

### Community 175 - ".get_config_value"
Cohesion: 0.40
Nodes (4): Any, ConfigValue, Returns current value of config item with given name. Args: name: Name of…, Sets value of config item with given name. Args: name: Name of config item.…

### Community 176 - "CLI"
Cohesion: 0.16
Nodes (9): CLI, Initializes a new instance of the CLI class., Overwrite this to set CLI parameters with argparse., Overwrite this to actually run the CLI., Load config from config file, Load config from environment variables., main(), PyobsDaemonCLI (+1 more)

### Community 177 - "HttpFileCache"
Cohesion: 0.09
Nodes (16): HttpFileCache, Any, Response, Handles OPTIONS access to /{filename} for CORS preflight requests. Args:…, Handles GET access to /{filename} and returns image. Args: request: Request to…, Handles PUSH access to /, stores image and returns filename. Args: request:…, A file cache based on a HTTP server., Initializes file cache. Args: port: Port for HTTP server. cache_size: Size of… (+8 more)

### Community 178 - ".set_gain"
Cohesion: 0.40
Nodes (3): Any, Set the camera gain. Args: gain: New camera gain. Raises: ValueError: If gain…, Set the camera offset. Args: offset: New camera offset. Raises: ValueError: If…

### Community 179 - "ExpTime"
Cohesion: 0.14
Nodes (6): AltAzOffsets, ExpTime, RaDecOffsets, test_alt_az_offsets(), test_exp_time(), test_radecoffsets()

### Community 180 - "Steering: astropy IERS auto-download blocks event loop"
Cohesion: 0.32
Nodes (8): BaseTelescope._celestial / _update_celestial_headers, Steering: astropy IERS auto-download blocks event loop, iers_offline config flag (stopgap fix), Steering: Blocking vendor SDK calls must never run directly on the event loop, _run_blocking() pattern (pyobs_aravis.araviscamera.AravisCamera), _wait_for_frame() tight-poll wrapper pattern, Steering: OnDemandScheduler.evolve() uncached sunset lookup stalls event loop, ObservationArchiveEvolution.evolve() Time.night_obs() bug (fixed via memoization)

### Community 181 - "Test Basecamera (camera)"
Cohesion: 0.18
Nodes (15): asyncio, parametrize, DummyCamera's _expose() must raise AbortedError, not some guessed builtin, when…, Test basic open/close of BaseCamera., #547: BaseCamera must abort on BadWeatherEvent., #547: a BadWeatherEvent must actually trigger abort() -- exposure + any running…, #672: a BadWeatherEvent must not interrupt a dark/bias sequence -- the shutter…, Test the methods for remaining exposure time and progress. (+7 more)

### Community 182 - "test_imagewatcher.py"
Cohesion: 0.33
Nodes (15): make_fits_bytes(), make_read_write_ctx(), make_watcher(), asyncio, On write failure the file is re-queued and remove is NOT called., test_add_file_queues_filename(), test_add_file_respects_pattern(), test_add_file_skips_non_matching_pattern() (+7 more)

### Community 183 - ".abort"
Cohesion: 0.40
Nodes (3): Any, Abort current actions., Sets the currently active fiber. Must be in fiber_names capability. Args:…

### Community 184 - "Merit"
Cohesion: 0.15
Nodes (15): AfterTimeMerit, BeforeTimeMerit, ConstantMerit, DataProvider, FollowMerit, IntervalMerit, ObservationArchiveEvolution wraps ObservationArchive with per-run caching (avoid repeated HTTP requests) and lookahead simulation (evolve() records tentative future assignments so IntervalMerit/PerNightMerit see them and avoid double-scheduling within one run), Merit (+7 more)

### Community 185 - "ejabberd shaper throttling bug (xmpp_socket.erl re-arm) & fix"
Cohesion: 0.21
Nodes (12): XMPP/ejabberd diagnostics recipe (doc), benchmark_state_throughput.py, check_ejabberd_notify.py, delete_pubsub_nodes.py, list_pubsub_nodes.py, Comparing shaper configs (rationale), show_module_info.py, scripts/xmpp/install-ejabberd.sh (+4 more)

### Community 186 - "WeatherStatus"
Cohesion: 0.14
Nodes (9): Any, Returns FITS header for the current status of this module. Args: namespaces: If…, Initialize a new pyobs-weather connector. Args: url: URL to weather station…, Any, setter, WeatherStatus, test_status_set(), test_status_set_non_good() (+1 more)

### Community 187 - "FileSystemTaskArchive"
Cohesion: 0.15
Nodes (9): FileSystemTaskArchive, Any, Task archive based on files., Creates a new filesystem-based task archive. Args: extension: Extension of…, Returns time when last time any blocks changed., Returns list of projects. Returns: List of projects., Returns list of schedulable tasks. Returns: List of schedulable tasks, Returns the task with the given ID. Returns: Task with given ID. (+1 more)

### Community 188 - "Work Plan"
Cohesion: 0.12
Nodes (16): Dropped items, Phase 0 — Foundations, Phase 1.5 — RPC payload encoding 2.0, Phase 1 — Walking skeleton: prove State end-to-end on one interface, Phase 2.5 — Discovery and Presence, Phase 2 — Audit and design pass (no implementation yet), Phase 3 — Bulk rollout, Phase 4 — Other backends and Presence (+8 more)

### Community 189 - "Plan: `pyobs-gui` TelescopeWidget layout — width floor investigation & design notes"
Cohesion: 0.12
Nodes (16): 1. Make the stacked widget size to the current page, not the widest one, 2. Adopt a width convention for future coordinate-type pages, 3. `QFormLayout::setRowWrapPolicy()` on the individual form pages, 4. Resize-driven reparenting for the four-groupbox row, Capability-driven visibility is handled by toggling pre-built sections on/off, Coordinate-type selection is already a combobox, not tabs, Each coordinate-type page has a fixed, hand-built field set, Filter, Focus, and the offsets rows are structurally duplicated (+8 more)

### Community 191 - "GridPipeline"
Cohesion: 0.14
Nodes (9): GridPipeline, Any, Build a GridPipeline from a list of steps. Args: steps: A non-empty list where…, Return the next point from the pipeline. Returns: The next point produced by…, Return the number of points remaining in the pipeline. Returns: The length…, Append the last yielded point back to the pipeline's final stage., Log the last yielded point via the pipeline's final stage., A pipeline that composes a grid and a sequence of filters. The pipeline expects… (+1 more)

### Community 192 - ".set_tracking_rate"
Cohesion: 0.50
Nodes (3): ARCSEC_PER_SEC, Any, Sets an absolute tracking rate on the sky, in arcsec/sec. Args: ra_rate: Rate…

### Community 193 - "._set_optimal_focus"
Cohesion: 0.16
Nodes (9): Any, DataFrame, floating, NDArray, Initialize a focus model. Args: focuser: Name of focuser. weather: Name of…, Sets optimal focus. Args: filter_name: Name of filter to use. Raises:…, Sets optimal focus. Raises: WeatherDataError: If the weather station returned…, Fit method for model Args: x: Paramaters to evaluate. data: Full data set.… (+1 more)

### Community 194 - "What's New in pyobs 2.0 (doc)"
Cohesion: 0.15
Nodes (14): What's New in pyobs 2.0 (doc), ACL feature (2.0), Capabilities and versioned discovery, Exception handling redesign, External-package interfaces, ICamera/ISpectrograph no longer imply IExposure, IDataSequence, InvocationError / SevereError retired (+6 more)

### Community 195 - "TaskStartedEvent"
Cohesion: 0.16
Nodes (9): Any, Event to be sent when a task has started., Initializes a new task started event. Args: name: Name of task that just…, TaskStartedEvent, test_task_started_invalid_name(), test_task_started_missing_id(), test_task_started_no_eta(), test_task_started_properties() (+1 more)

### Community 196 - "LcoTaskArchive"
Cohesion: 0.15
Nodes (9): LcoTaskArchive, Any, Returns a list of schedulable tasks and projects Returns: List of schedulable…, Scheduler for using the LCO portal, Creates a new LCO scheduler. Args: url: URL to portal token: Authorization…, Returns time when last time any tasks changed., Returns list of projects from the LCO portal., Returns list of schedulable tasks. Returns: List of schedulable tasks (+1 more)

### Community 197 - "CatalogCircularMask"
Cohesion: 0.18
Nodes (9): CatalogCircularMask, Any, NDArray, Table, Init an image processor that masks out everything except for a central circle.…, Remove everything outside the given radius from the image. Args: image: Image…, Filter a source catalog by keeping only entries inside a central circle (or…, asyncio (+1 more)

### Community 198 - ".set_exposure_time"
Cohesion: 0.50
Nodes (3): Any, SECONDS, Set the exposure time in seconds. Args: exposure_time: Exposure time in…

### Community 199 - "ImageWatcher"
Cohesion: 0.15
Nodes (9): CurrentFile, ImageWatcher, Any, Add a file to the file queue. Args: filename (str): Local filename of new file., Can be overwritten by derived classes to do extra processing on files. All…, Can be overwritten by derived classes to do clean up after successful copying.…, Watch for new files and write them to all given destinations. Watches a path…, Create a new image watcher. Args: watchpath: Path to watch. destinations:… (+1 more)

### Community 200 - "object.py"
Cohesion: 0.04
Nodes (48): Modules for robotic mode. TODO: write doc, Initialize a new auto focus system. Args: schedule: Object that can return…, # TODO: add abort (see old robotic/scheduler.py), Initialize a new scheduler. Args: scheduler: Scheduler to use. tasks: Task…, :class:`~pyobs.object.Object` is the base for almost all classes in *pyobs*. It…, ObservationState, StrEnum, Abstract base class for tasks scheduler. (+40 more)

### Community 201 - ".set_offsets_altaz"
Cohesion: 0.50
Nodes (3): Any, DEGREES, Move an Alt/Az offset. Args: dalt: Altitude offset in degrees. daz: Azimuth…

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

### Community 210 - "Scheduler"
Cohesion: 0.09
Nodes (18): Run script. Raises: InterruptedError: If interrupted, ArchiveSkyflatPriorities, Calculate flat priorities from an archive., Base class for sky flat priorities., SkyflatPriorities, ConstSkyflatPriorities, Constant flat priorities., Observer (+10 more)

### Community 211 - "DataCacheEntry"
Cohesion: 0.19
Nodes (8): DataCacheEntry, Any, A single entry in the data cache., Create a new entry for the data cache Args: name: Name of item data: Data for…, Update time for this item., Update usage time and return data for entry., Returns data from entry in cache. Args: name: Name of data. Returns: Data from…, Set new entry in the cache. Args: name: Name for data to store. data: Date of…

### Community 212 - "Plan: Widget plugin mechanism + `pyside6-deploy` packaging for `pyobs-gui`"
Cohesion: 0.13
Nodes (14): Consequences, Considered options, Considered options, Deciding which widget to use, without user-side config, Decision, Decision outcome, Implementation checklist, Non-goals (+6 more)

### Community 213 - "Plan: Split archive prefetch from CPU-bound merit evaluation, to unblock a `ProcessPoolExecutor`"
Cohesion: 0.13
Nodes (14): 1. `ObservationArchiveEvolution` — add prefetch + freeze (`observationarchiveevolution.py`), 2. Call prefetch + freeze — `ondemandscheduler.py`, `schedule()`, 3. Confirm zero cache misses before touching the executor, 4. Only after step 3 is clean: swap the executor (`_executor.py`), Consequences, Considered options, Decision, Existing coverage (+6 more)

### Community 214 - "test_httpfilecache.py"
Cohesion: 0.52
Nodes (11): make_cache(), make_request(), asyncio, test_download_response_has_cors_header(), test_download_with_token_configured_accepts_correct_token(), test_download_with_token_configured_rejects_missing_header(), test_download_with_token_configured_rejects_wrong_token(), test_download_without_token_configured_is_unauthenticated() (+3 more)

### Community 215 - "Image (pyobs.images.processors.image) API doc"
Cohesion: 0.18
Nodes (11): AddFitsHeaders, Image (pyobs.images.processors.image) API doc, Download, Flip, Grayscale, HttpServer, Normalize, Save (+3 more)

### Community 216 - "Offsets (pyobs.images.processors.offsets) API doc"
Cohesion: 0.33
Nodes (11): AstrometryOffsets, BrightestStarGuiding, BrightestStarOffsets, Offsets (pyobs.images.processors.offsets) API doc, DummyOffsets, DummySkyOffsets, FitsHeaderOffsets, Offsets (+3 more)

### Community 217 - "Constraint"
Cohesion: 0.20
Nodes (11): AirmassConstraint, AstroplanScheduler, Constraint, Constraints answer a binary may-it-run question (any False excludes the task); Merits answer a continuous how-desirable question (values multiplied together with priority, highest score wins); rationale: clean separation lets scheduling policy be expressed in YAML without code, and a Merit returning 0.0 can double as a soft constraint, MoonIlluminationConstraint, MoonSeparationConstraint, OnDemandScheduler, OnDemandScheduler: greedy, evaluates constraints/merits per time step, robust to interruption, supports merits+global constraints+lookahead. AstroplanScheduler: full-night planning via astroplan PriorityScheduler in a separate process (avoids blocking event loop), only SiderealTarget, only per-task constraints, no merits; rationale: choose based on whether a committed nightly plan or rolling on-demand decisions is needed (+3 more)

### Community 218 - ".set_offsets_radec"
Cohesion: 0.50
Nodes (3): Any, DEGREES, Move an RA/Dec offset. Args: dra: RA offset in degrees. ddec: Dec offset in…

### Community 219 - ".add_fits_headers"
Cohesion: 0.24
Nodes (6): PrimaryHDU, Add requested FITS headers to header of given image. Args: image: Image with…, Add FITS header keywords to the given FITS header. Args: image: Image with…, Add FRAMENUM keyword to header Args: image: Image with header to add to., Format filename according to given pattern and store in header of image. Args:…, Add FITS header keywords to the given FITS header. Args: image: Image with…

### Community 221 - "flatfield/test_scheduler.py"
Cohesion: 0.14
Nodes (18): FlatFieldScheduler, Any, Abort current actions., Run the flat-field scheduler., Initialize a new flat field scheduler. Args: flatfield: Flat field module to…, Perform flat-fielding Raises: DeviceBusyError: If a flat-fielding run is…, Iterate over scheduler items, A single item in the flat scheduler (+10 more)

### Community 222 - "ImageWriter"
Cohesion: 0.10
Nodes (11): ImageWriter, Any, Writes new images to disk., Creates a new image writer. Args: filename: Pattern for filename to store…, Puts a new images in the DB with the given ID. Args: event: New image event…, Modules for image operations. TODO: write doc, Any, Measures seeing on reduced images with a catalog. (+3 more)

### Community 223 - ".move_altaz"
Cohesion: 0.50
Nodes (3): Any, DEGREES, Moves to given coordinates. Args: alt: Alt in deg to move to. az: Az in deg to…

### Community 224 - ".move_heliocentric_polar"
Cohesion: 0.50
Nodes (3): Any, DEGREES, Moves on given coordinates. Args: mu: Cosine of the angular distance from Sun…

### Community 225 - "test_imagewriter.py"
Cohesion: 0.47
Nodes (11): make_image_event(), make_writer(), asyncio, test_process_event_accepts_all_when_no_filter(), test_process_event_accepts_listed_source(), test_process_event_filters_by_source(), test_process_event_queues_filename(), test_process_event_rejects_wrong_type() (+3 more)

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

### Community 231 - ".move_radec"
Cohesion: 0.50
Nodes (3): Any, DEGREES, Starts tracking on given coordinates. Args: ra: RA in deg to track. dec: Dec in…

### Community 232 - "Findings: driver/gui correctness review, all 8 repos (reviewed 2026-08-11)"
Cohesion: 0.13
Nodes (14): Context, Findings: driver/gui correctness review, all 8 repos (reviewed 2026-08-11), Plan: Driver/GUI split for all camera modules + qhyccd correctness review, pyobs-aravis, pyobs-asi, pyobs-fli (driver split only — gui.py not built yet), pyobs-flipro, pyobs-qhyccd (+6 more)

### Community 233 - "test_xmpp_rpc.py"
Cohesion: 0.19
Nodes (14): Integration tests for the pyobs 2.0 RPC payload encoding (urn:pyobs:rpc:1).…, set_binning(int, int) -> None: multiple int params, void return., Calling a method that raises on the remote side propagates the exception., set_cooling(bool, float) then verify via state: full encode/decode cycle., set_cooling(bool, float) -> None: void return with bool + float params., set_gain(float) -> None and verify via IGain state: float param, state readback., set_gain(float) then verify via IGain state: float param round-trip., test_rpc_bool_float_roundtrip() (+6 more)

### Community 234 - "CHANGELOG.rst"
Cohesion: 0.22
Nodes (9): ejabberd shaper/xmpp_socket.erl reactivation bug (iag50srv capability-fetch timeouts), XmppComm disco#info role attribute (send/subscribe split), OnDemandScheduler CPU-bound work offloaded to ThreadPoolExecutor, Vfs.write_image()/write_fits() moved to asyncio.to_thread(), run_cpu_bound (scheduler/_executor.py), Vfs.write_fits (pyobs/vfs/vfs.py), Vfs.write_image (pyobs/vfs/vfs.py), specs/plans/event-role-advertising.md (+1 more)

### Community 235 - "Use a self-hosted Keycloak alongside odin, as two parallel auth backends"
Cohesion: 0.33
Nodes (5): Consequences, Considered Options, Context and Problem Statement, Decision Outcome, Use a self-hosted Keycloak alongside odin, as two parallel auth backends

### Community 236 - "Image class"
Cohesion: 0.20
Nodes (10): meta.AltAzOffsets, meta.ExpTime, Image class, Image.meta dict; rationale: keyed by class to avoid collisions between pipeline stages, kept out of FITS since it's runtime-only data, meta.OnSkyDistance, meta.PixelOffsets, meta.RaDecOffsets, meta.SkyOffsets (+2 more)

### Community 237 - "PyobsArchive"
Cohesion: 0.27
Nodes (5): Any, PyobsArchive, Connector class to running pyobs-archive instance., test_build_query_empty_when_nothing_given(), test_build_query_includes_all_given_params()

### Community 238 - "BrightestStarGuiding"
Cohesion: 0.19
Nodes (7): BrightestStarGuiding, Any, SkyCoord, Table, Initializes a new auto guiding system., Processes an image and sets x/y pixel offset to reference in offset attribute.…, Compute guiding offsets by tracking the brightest star relative to an initial…

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

### Community 244 - "._filter_data"
Cohesion: 0.24
Nodes (3): Any, DataFrame, Update files in root directory.

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

### Community 253 - ".__init__"
Cohesion: 0.40
Nodes (4): Any, Pipeline, ProgressCallback, Args: archive: Archive to fetch raw and calibration frames from. pipeline:…

### Community 254 - "test_dummyvideo.py"
Cohesion: 0.47
Nodes (9): make_dummyvideo(), asyncio, test_frame_task_sets_image_when_active(), test_frame_task_skips_image_when_inactive(), test_init_custom_fps_and_image_size(), test_init_defaults(), test_open_publishes_exposure_time_state(), test_set_exposure_time_updates_fps_and_publishes_state() (+1 more)

### Community 255 - "ImageFormat"
Cohesion: 0.21
Nodes (6): Any, Set the camera image format. Args: fmt: New image format. Raises: ValueError:…, ImageFormat, StrEnum, Enumerator for image formats. Attributes: INT8: 8 bit integer (i.e. byte).…, ImageFormatWidget

### Community 256 - "Decision"
Cohesion: 0.17
Nodes (11): 1. `ImageProcessor` — new methods and kwarg, 2. `PipelineMixin.run_pipeline()` — wrap each step, 3. `AstrometryDotNet` — migrate to handle_error, 4. Deprecation notes, 5. Tests, Consequences, Considered options, Decision (+3 more)

### Community 259 - "wait_for"
Cohesion: 0.17
Nodes (12): DummyCamera.open() must publish IWindow.Capabilities with the SimCamera full…, DummyCamera.open() must publish IModule.Capabilities with version and label., get_capabilities() must return None for an interface DummyCamera doesn't…, Poll *condition* until truthy or *timeout* seconds elapse., DummyCamera's _cooling_thread publishes CoolingState every second. An observer…, After calling set_cooling via RPC, the published CoolingState must reflect the…, test_dummy_camera_cooling_state_reflects_set_cooling(), test_dummy_camera_no_capabilities_for_unconfigured_interface() (+4 more)

### Community 260 - "GuidingStatisticsSkyOffset"
Cohesion: 0.25
Nodes (7): GuidingStatisticsSkyOffset, Calculates RMS of data. Args: data: Data to calculate RMS for. Returns: Tuple…, mock_meta_image(), fixture, test_build_header_to_few_values(), test_end_to_end(), test_get_session_data()

### Community 261 - "robotic"
Cohesion: 0.43
Nodes (8): acquisition, fibercamera, fts, guiding, robotic, solar telescope, suncamera, weather

### Community 262 - "Archive (image archive base)"
Cohesion: 0.32
Nodes (8): Archive (image archive base), LocalArchive, PyobsArchive, ArchiveSkyflatPriorities, Archive, Image archives (pyobs.robotic.utils.archive) API doc, LocalArchive, PyobsArchive

### Community 263 - ".flat_field"
Cohesion: 0.50
Nodes (3): Any, SECONDS, Do a series of flat fields. Args: count: Number of images to take Returns:…

### Community 264 - "._get_client"
Cohesion: 0.11
Nodes (10): PresenceCallback, Get a proxy to the given client. Args: client: Name of client. Returns: Proxy…, Fetch capabilities for a single interface and push them into the given proxy…, Called when a client disconnects. Args: event: Disconnect event. sender: Name…, Returns list of interfaces for given client. Args: client: Name of client.…, Subscribe to state updates for a given module and interface. Delivers the…, Unsubscribe from state updates. Args: module: Name of remote module. interface:…, Subscribe to presence updates for a given module. Delivers the current value… (+2 more)

### Community 265 - "ConfigStatus"
Cohesion: 0.25
Nodes (6): ConfigStatus, Run a config Args: script: Script to run Returns: Configuration status to send…, Status of a single configuration., Initializes a new Status with an ATTEMPTED., Finish this status with the given values and the current time. Args: state:…, Convert status to JSON for sending to portal.

### Community 266 - "BaseVideo"
Cohesion: 0.06
Nodes (22): BaseVideo, Response, Whether the server is started., Handles access to / and returns HTML page. Args: request: Request to respond…, Handles GET access to /ping for testing connectivity. Args: request: Request to…, Handles access to /video.mjpg and returns the video. Args: request: Request to…, Handles access to /* and returns a specified image. Args: request: Request to…, Whether camera is currently active. (+14 more)

### Community 268 - "._get_next"
Cohesion: 0.33
Nodes (4): SkyCoord, Log a point if logging is enabled. For SkyCoord instances, logs RA/Dec in…, Return the next point in the sequence. Implementors must return either a (x, y)…, Return the next point, storing it as the last yielded value. Returns: A point…

### Community 269 - "Shared authentication across pyobs web projects via Keycloak"
Cohesion: 0.22
Nodes (8): Decision: Keycloak as the single issuer; observation-portal becomes a brokered upstream, not a second integration, Decision: realm layout and user mapping, Non-issue: upstream OIDC brokering (including observation-portal), Note: observation-portal's own token validation shortcut (context, not adopted), Problem, Proposed change: `pyobs-auth` package, Scope, Shared authentication across pyobs web projects via Keycloak

### Community 270 - "Plan: `pyobs-gui` navbar keyboard shortcuts"
Cohesion: 0.18
Nodes (10): Binding is by page name, not by widget or list-item instance, File changes, Key scheme, Motivation, Plan: `pyobs-gui` navbar keyboard shortcuts, Shortcut wiring, State, Verification (once implemented) (+2 more)

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

### Community 277 - "wait_for"
Cohesion: 0.18
Nodes (11): A caller granted "*" access under "allow" can still call normally., A caller not present in the "allow" map is denied by default., A caller on the "deny" list gets exc.RemoteError with a forbidden message, not…, Naming an interface under "allow" permits all of its methods, but nothing…, A module not on the "deny" list is unaffected., test_acl_allow_denies_unlisted_caller(), test_acl_allow_interface_name_sugar(), test_acl_allow_permits_listed_method() (+3 more)

### Community 278 - ".retrieve_class_on_deserialization"
Cohesion: 0.24
Nodes (7): model_serializer, Any, model_validator, Self, Get the correct class for this model and run model_validate on that class with…, ValidationInfo, ValidatorFunctionWrapHandler

### Community 279 - "test_comm_interface_resolution.py"
Cohesion: 0.29
Nodes (8): Converts a list of interface names to interface classes. Args: interfaces: list…, LogCaptureFixture, Tests for Comm._interface_names_to_classes -- the base-Comm chokepoint that…, An interface defined entirely outside pyobs.interfaces resolves the same way…, test_resolves_external_interface(), test_resolves_known_and_skips_unknown_in_same_list(), test_resolves_known_core_interfaces(), test_skips_unknown_name()

### Community 280 - "Any"
Cohesion: 0.22
Nodes (8): Any, Is user authorized? Args: context: Telegram context. user_id: ID of user.…, Handle /start command. Args: update: Message to process. context: Telegram…, Handle /exec command. Args: update: Message to process. context: Telegram…, Initialize a new bot. Args: token: The telegram API token. password: Password…, Handle /modules command that shows list of modules. Args: update: Message to…, Handle /loglevel command that sets the log level Args: update: Message to…, Update

### Community 281 - "ObservationList"
Cohesion: 0.05
Nodes (75): ObservationList, Add the list of scheduled tasks to the schedule. Args: tasks: Scheduled tasks., LcoScheduleWriter, Scheduler for using the LCO portal, Add the list of scheduled tasks to the schedule. Args: tasks: Scheduled tasks., Clear schedule after given start time. Args: start_time: Start time to clear…, Create observations from schedule. Args: scheduled_tasks: List of scheduled…, MemoryTaskArchive (+67 more)

### Community 282 - ".set_rotation"
Cohesion: 0.50
Nodes (3): Any, DEGREES, Sets the rotation angle to the given value in degrees. Raises: MoveError: If…

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

### Community 290 - "FluentLogger"
Cohesion: 0.25
Nodes (5): FluentLogger, Any, Log to fluentd server., Initialize a new logger. Args: hostname: Hostname of server. port: Port of…, Process a new log entry. Args: event: The log event. sender: Name of sender.

### Community 291 - ".__call__"
Cohesion: 0.29
Nodes (5): Any, DataFrame, Initialize new CSV publisher. Args: filename: Name of file to log in., Publish the given results. Args: **kwargs: Results to publish., Return data that has so far been published.

### Community 292 - "Plan: `pyobs-gui` IAutoGuiding widget"
Cohesion: 0.25
Nodes (7): Known bug in the shipped widget (to fix alongside this change), Plan: `pyobs-gui` IAutoGuiding widget, Problem: pixel offsets aren't physical, and the per-image correction is discarded, Proposed pyobs-core change, Resolved from the original open questions, Shipped (pyobs-core, `develop`), Widget design (pyobs-gui)

### Community 293 - ".grab_sequence"
Cohesion: 0.33
Nodes (4): Any, SECONDS, Start a sequence of `count` grabs. Returns immediately; progress is available…, Stop the sequence after the current grab. The grab currently in progress, if…

### Community 294 - ".set_focus"
Cohesion: 0.40
Nodes (4): Any, MM, Sets new focus. Args: focus: New focus value in mm. Raises:…, Sets focus offset. Args: offset: New focus offset in mm. Raises: ValueError: If…

### Community 295 - "Investigation: pyobs-gui receives every LogEvent twice (SAAO/monet production)"
Cohesion: 0.25
Nodes (7): Access used, Artifacts from this session, Investigation: pyobs-gui receives every LogEvent twice (SAAO/monet production), Next steps, Problem, What's confirmed, What's ruled out

### Community 296 - ".init"
Cohesion: 0.29
Nodes (4): Any, Initialize device. Raises: InitError: If device could not be initialized., Park device. Raises: ParkError: If device could not be parked., Stop the motion. Args: device: Name of device to stop, or None for all.

### Community 297 - "GraticuleSphericalGrid"
Cohesion: 0.33
Nodes (6): GraticuleSphericalGrid, Grid with approximately equidistributed points on a sphere. Uses a graticule-…, Reinsert one point back into the grid., test_graticulesphericalgrid(), test_regularsphericalgrid(), test_regularsphericalgrid_append_last()

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

### Community 312 - ".get_permitted_methods"
Cohesion: 0.40
Nodes (3): Any, Reset error of module, if any., Returns names of all methods the calling module is allowed to invoke on this…

### Community 313 - ".__call__"
Cohesion: 0.40
Nodes (3): Any, Initialize new log publisher. Args: level: Level to log on., Publish the given results. Args: **kwargs: Results to publish.

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

### Community 321 - "pyobs.modules.weather (doc)"
Cohesion: 1.00
Nodes (3): pyobs.modules.weather (doc), MockWeather, Weather (module)

### Community 322 - "Photometry (pyobs.images.processors.photometry) API doc"
Cohesion: 0.83
Nodes (4): Photometry (pyobs.images.processors.photometry) API doc, Photometry, PhotUtilsPhotometry, SepPhotometry

### Community 338 - "Pipeline"
Cohesion: 0.18
Nodes (19): Pipeline, Any, Create master bias frame. Args: images: List of raw bias frames. Returns:…, Create master dark frame. Args: images: List of raw dark frames. bias: Bias…, Create master flat frame. Args: images: List of raw flat frames. bias: Bias…, Calibrate a single science frame. Args: image: Image to calibrate. Returns:…, Pipeline based on the astropy package ccdproc., Pipeline for science images. Args: steps: List of pipeline steps to perform.… (+11 more)

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
- **548 isolated node(s):** `Goal`, `Architecture`, `File Map (representative, not exhaustive — see commit diffs for the full ~74-file list)`, `Tasks`, `Goal` (+543 more)
  These have ≤1 connection - possible missing edges or undocumented components.
- **41 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **What is the exact relationship between `Configuration utilities (pyobs.utils.config) API doc` and `Coordinate utilities (pyobs.utils.coordinates) API doc`?**
  _Edge tagged AMBIGUOUS (relation: conceptually_related_to) - confidence is low._
- **What is the exact relationship between `PyObsError` and `ScriptRunner.run()`?**
  _Edge tagged AMBIGUOUS (relation: conceptually_related_to) - confidence is low._
- **What is the exact relationship between `FocusError` and `FocusModel.set_optimal_focus`?**
  _Edge tagged AMBIGUOUS (relation: conceptually_related_to) - confidence is low._
- **Why does `Time` connect `Time` to `LcoScript`, `imaging.py`, `RunningState`, `Interface`, `DynamicTarget`, `BaseCamera`, `ImageProcessor`, `TaskData`, `test_basetelescope.py`, `FilenameFormatter`, `TimeDelta`, `Event`, `test_backend_archives.py`, `test_flatfielder.py`, `tests/test_events.py`, `LcoTask`, `test_mastermind.py`, `test_control.py`, `test_lco_http.py`, `enums.py`, `CoolingState`, `IPointingAltAz.py`, `test_astroplanscheduler.py`, `test_transitimaging.py`, `robotic/test_scheduler.py`, `Calibration`, `Proxy`, `SkyFlatsBasePointing`, `test_yaml_archives.py`, `FlatFielder`, `OffsetResult`, `Offsets`, `.now`, `test_proxy.py`, `SiderealTarget`, `ImageType`, `Weather`, `FileSystemObservationArchive`, `weather.py`, `Object`, `DummySolarTelescope`, `DummyCamera`, `test_pyobs_archive.py`, `application.py`, `WeatherSensors`, `test_coordinates.py`, `SolarElevationConstraint`, `LocalArchive`, `Test Commlogging (comm)`, `ImagingScript`, `FocusModel`, `test_darkbias.py`, `Portal`, `GridNode`, `test_schedulewriter.py`, `DummyMode`, `test_autofocus.py`, `Grid`, `pyobs.py`, `DummyRaDecTelescope`, `Scheduler`, `Observation`, `Archive`, `RandomizeGrid`, `test_transit_mastermind.py`, `ExpTimeEval`, `calibration.py`, `FileSystemTaskArchive`, `TaskStartedEvent`, `LcoTaskArchive`, `object.py`, `Scheduler`, `.add_fits_headers`, `flatfield/test_scheduler.py`, `ImageWriter`, `PyobsArchive`, `BrightestStarGuiding`, `.night_obs`, `._filter_data`, `ConfigStatus`, `ObservationList`, `GoodWeatherEvent`, `FluentLogger`, `Pipeline`?**
  _High betweenness centrality (0.272) - this node is a cross-community bridge._
- **Why does `Image` connect `Image` to `imaging.py`, `SepSourceDetection`, `Interface`, `GuidingStatisticsSkyOffset`, `_ResponseImageWriter`, `ImageProcessor`, `BaseCamera`, `AstrometryDotNet`, `FilenameFormatter`, `OnSkyDistance`, `_SepAperturePhotometry`, `mixins/test_fitsheader.py`, `PipelineMixin`, `test_flatfielder.py`, `_DaoBackgroundRemover`, `GuidingStatistics`, `SoftBin`, `AddMask`, `Archive`, `enums.py`, `VirtualFileSystem`, `calibration.py`, `GuidingStatisticsPixelOffset`, `.get_meta`, `NextImage`, `utils/exceptions.py`, `StarExpTimeEstimator`, `Calibration`, `.__init__`, `FitsHeaderOffsets`, `test_basevideo.py`, `OffsetResult`, `CatalogCircularMask`, `Offsets`, `ImageType`, `test_autoguiding.py`, `Smooth`, `Pipeline`, `Ring`, `DummyCamera`, `.add_fits_headers`, `ProjectedOffsets`, `test_pyobs_archive.py`, `FocusSeries`, `_SourceCatalog`, `LocalArchive`, `_PhotUtilAperturePhotometry`, `BrightestStarGuiding`, `PyobsArchive`, `._filter_data`, `test_acquisition.py`, `VFSFile`, `ImageSourceFilter`?**
  _High betweenness centrality (0.160) - this node is a cross-community bridge._
- **Why does `Module` connect `Module` to `imaging.py`, `Time`, `RunningState`, `Interface`, `DummyMode`, `test_dummymode.py`, `._get_client`, `BaseCamera`, `BaseVideo`, `test_kiosk.py`, `pyobs.py`, `XmppComm`, `Scheduler`, `mixins/test_fitsheader.py`, `PipelineMixin`, `test_mastermind.py`, `test_presence.py`, `FluentLogger`, `enums.py`, `LogEvent`, `CoolingState`, `IPointingAltAz.py`, `Stellarium`, `Comm`, `.close`, `robotic/test_scheduler.py`, `StandAlone`, `utils/exceptions.py`, `HttpFileCache`, `RPC`, `WindowCapabilities`, `Proxy`, `test_basevideo.py`, `Telegram`, `ImageWatcher`, `object.py`, `MockWeather`, `test_autoguiding.py`, `Weather`, `weather.py`, `Object`, `xmppcomm.py`, `test_exception_logging.py`, `Application`, `flatfield/test_scheduler.py`, `ImageWriter`, `application.py`, `make_proxy_cm`, `ScriptRunner`, `test_acquisition.py`, `FocusModel`?**
  _High betweenness centrality (0.089) - this node is a cross-community bridge._
- **Are the 167 inferred relationships involving `Time` (e.g. with `PyobsCLI` and `Proxy`) actually correct?**
  _`Time` has 167 INFERRED edges - model-reasoned connections that need verification._