# Graph Report - pyobs-core  (2026-08-25)

## Corpus Check
- 807 files · ~457,119 words
- Verdict: corpus is large enough that graph structure adds value.

## Summary
- 9266 nodes · 21425 edges · 501 communities (406 shown, 95 thin omitted)
- Extraction: 94% EXTRACTED · 6% INFERRED · 0% AMBIGUOUS · INFERRED: 1291 edges (avg confidence: 0.56)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `b9f946e1`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- ExposureStatus
- .get_fits_header_before
- Time
- Module
- benchmark_state_throughput.py
- BaseTelescope
- Image
- Observation
- asyncio
- ImageProcessor
- XmppComm
- Interface
- xmpp/rpc.py
- utils/test_http.py
- test_mastermind.py
- .open_file
- Any
- .to_astropy
- DummyRoof
- mixins/test_fitsheader.py
- Event
- MotionStatus
- _DummyTelescopeBase
- test_flatfielder.py
- LocalComm
- tests/test_events.py
- test_lco_http.py
- Object
- test_basetelescope.py
- WindowingWidget
- Interfaces (pyobs.interfaces) API doc
- TaskData
- DummySolarTelescope
- BaseCamera
- _AbortableModule
- test_astroplanscheduler.py
- test_parallel.py
- .can_run
- CoolingState
- PointingSeries
- test_presence.py
- SkyOffsets
- test_xmpp_event_subscriptions.py
- Proxy
- .__init__
- robotic/test_scheduler.py
- StandAlone
- IDataSequence
- PyobsError
- test_stellarexptime.py
- SkyFlatsBasePointing
- test_dynamictarget.py
- WindowCapabilities
- test_shellcommand.py
- Calibration
- ImagingScript
- Publisher
- PortalObservationArchive
- test_lcoscript.py
- applyoffsets.py
- FilenameFormatter
- test_basevideo.py
- test_yaml_archives.py
- Any
- FlatFielder
- IExposure
- Telegram
- Any
- Task
- Offsets
- .now
- PyObsError
- test_proxy.py
- XEP_0009
- test_schedulereader.py
- PyobsDaemon
- IPointingAltAz.py
- test_config.py
- test_control.py
- xmppcomm.py
- Weather
- Portal
- test_autoguiding.py
- test_acquisition.py
- PipelineMixin
- Ring
- loaded_pyobs_packages
- DataCache
- test_exception_logging.py
- test_config_schema.py
- Application
- DummyComm
- CallModuleScript
- ProjectedOffsets
- LocalArchive
- HttpFile
- test_transit_mastermind.py
- InfluxHandler
- FocusSeries
- RemoveBackground
- make_proxy_cm
- PortalTaskArchive
- test_background_task.py
- _DaoBackgroundRemover
- test_coordinates.py
- get_registered_interface
- test_xmpp_rpc.py
- PixelOffsets
- Plan: Systematic ejabberd throughput/latency benchmarking
- _SepAperturePhotometry
- Mixins (pyobs.mixins) API doc
- Script base class
- ImageWatcher
- Comm
- LogEvent
- test_dummyradectelescope.py
- dummycamera.py
- test_xmpp_acl.py
- MemoryFile
- VFSFile
- LocalFile
- test_version_mismatch.py
- CLAUDE.md (repo guide)
- SoftBin
- FocusModel
- SFTPFile
- ImageSourceFilter
- test_darkbias.py
- .__init__
- OffsetsAltAzEvent
- Plan: pyobs-pipeline
- Test Localcomm (local)
- integration/conftest.py
- .__init__
- module.py
- test_dummymode.py
- MockWeather
- SchedulerItem
- Grid
- test_kiosk.py
- Plan: pyobs-iag50 pyobs-core 2.x migration
- Robotic recipe (doc)
- ._move_radec
- SiderealTarget
- RollingTimeAverage
- ._create_image
- WeatherApi
- Project
- utils/exceptions.py
- OnSkyDistance
- tests/xmpp/docker-compose.yml (ejabberd integration test container)
- `OBSNUM`: per-night observation counter in FITS headers
- 3rd party packages (doc)
- CatalogCircularMask
- SSHFile
- create_rst.py
- _PhotUtilAperturePhotometry
- XEP_0009_timeout
- AddMask
- Any
- SkyCoord
- .retrieve_class_on_deserialization
- .get_object
- _SourceCatalog
- Design
- ExpTimeEval
- Plan: Stop ImageWatcher per-file processing from blocking the event loop
- BrightestStarOffsets
- ._set_optimal_focus
- test_xmpp_state.py
- HttpFileCache
- ._get_client
- test_grab_sequence.py
- binding.py
- WeatherAwareMixin
- SepSourceDetection
- test_xmppcomm_event_payload.py
- _CalibrationCache
- test_dummyvideo.py
- test_aperture_photometry.py
- Steering: astropy IERS auto-download blocks event loop
- filters.py
- FitsHeaderOffsets
- ._run_configurations
- Merit
- ejabberd shaper throttling bug (xmpp_socket.erl re-arm) & fix
- _ResponseImageWriter
- Plan: Make the pydantic config layer reject unknown keys (`extra="forbid"`)
- Work Plan
- Plan: `pyobs-gui` TelescopeWidget layout — width floor investigation & design notes
- MoveAltAzEvent
- GridNode
- Plan: Make mixin `__init__` composition cooperative, then enforce unrecognized kwargs at `Object.__init__`
- Plan: `pyobs-gui` IAutoGuiding widget
- What's New in pyobs 2.0 (doc)
- NewImageEvent
- test_istructuredconfig.py
- test_imagewatcher.py
- TaskStartedEvent
- comm/test_events.py
- ObservationList
- test_basecamera.py
- show_module_info.py
- .__call__
- SkyflatPriorities
- robotic
- Scheduler module
- BaseModel (pyobs.utils.serialization)
- Decision
- Stellarium
- AstrometryDotNet
- ._get_method
- Plan: Widget plugin mechanism + `pyside6-deploy` packaging for `pyobs-gui`
- Plan: Split archive prefetch from CPU-bound merit evaluation, to unblock a `ProcessPoolExecutor`
- BaseVideo
- Image (pyobs.images.processors.image) API doc
- Offsets (pyobs.images.processors.offsets) API doc
- Constraint
- Smooth
- Scheduler
- test_autofocus.py
- time.py
- DummyAltAzTelescope
- Mastermind
- Kiosk
- is_valid_jid
- .move_heliographic_stonyhurst
- FileList
- .move_helioprojective
- test_transitimaging.py
- pyobs 2.0 Wire Protocol, State, and Access Control design doc
- Plan: Log the loaded pyobs-* package versions at module startup
- Findings: driver/gui correctness review, all 8 repos (reviewed 2026-08-11)
- test_baseroof.py
- CHANGELOG.rst
- Use a self-hosted Keycloak alongside odin, as two parallel auth backends
- Image class
- Scheduler
- Implementation
- .abort
- Module.startup() lifecycle helper
- CreateFilename
- Plan: Stop scheduler constraint/merit evaluation from blocking the event loop
- .__init__
- watch_log_events_no_interest.py
- AperturePhotometry
- pyobs-gui as a standalone binary (umbrella design)
- Plan: Enforce state publishing for stateful interfaces
- Plan: `pyobs-gui` login window
- test_safe_send.py
- WeatherSensors
- Two-phase Object lifecycle; rationale: __init__ must not touch hardware/external services (only store params, create children, register background tasks); open() is where side effects happen, so objects can be constructed cheaply/safely before being started
- Simulation recipe (doc)
- ResolvableErrorLogger
- MockBaseDome
- Save
- Decision
- CasesRunner
- RuntimeError
- flatfield/test_scheduler.py
- RunningState
- robotic
- Archive (image archive base)
- RemoteError
- test_dummysolartelescope.py
- TaskFinishedEvent
- Plan: Rename pyobs-robotic-backend → pyobs-portal
- test_camerasettings.py
- Image processors index (docs)
- Discussion: LogEvent double-delivery fix — should we drop add_interest()?
- Plan: `pyobs-gui` navbar keyboard shortcuts
- Enum
- ._combine_calib_images_async
- Image.trim
- conftest.py
- Misc (pyobs.images.processors.misc) API doc
- PolymorphicBaseModel
- Plan: Stop gating backend-archive refreshes on the `last_*_update` marker
- .__get_script
- FitsHeaderEntry
- DummyMode
- ObservationList
- .move_heliocentric_polar
- WeatherStatus
- BufferedFile
- Implementation
- Plan: Interactive login/settings dialog for `pyobs-gui`, deferring `Application`'s module construction
- pyobs.modules.utils (doc)
- Plan: Add baseline tests to core-tier repos, then enable grouped Dependabot auto-merge
- Plan: CORS + token auth for `HttpFileCache`
- _event_role
- Any
- _PhotometryCalculator
- DummyCamera
- pyobs/modules/utils/__init__.py
- Investigation: pyobs-gui receives every LogEvent twice (SAAO/monet production)
- Overview (doc)
- Plan: Module observer-location capabilities (reconstructed)
- .set_gain
- Plan: One-click IdP login via `kc_idp_hint` (dual login buttons)
- ADR-0008: _safe_send keeps bounded retry unlike capability/subscribe fetches
- Module._watch_event_loop_lag
- Plan: Surface unrecognized kwargs in `Object.__init__` instead of silently discarding them
- pyobs.modules.image (doc)
- NamedTuple
- DataFrame
- NDArray
- TypedDict
- plans/index.md
- Script
- SMBFile
- Response
- .set_tracking_rate
- Open plans
- Any
- model_validator
- ModuleLocation dataclass (nested in ModuleCapabilities)
- check_pyobs_releases.sh
- check_ejabberd_notify.py
- Self
- Plan: Bound the FITS-header fetch so a dead peer can't stall the frame
- .__init__
- Photometry (pyobs.images.processors.photometry) API doc
- Plan: `pyobs-gui` IAutoFocus widget
- .set_focus
- Target
- Any
- ._get_next
- .get_config_value
- FitsNamespaceMixin
- Plan: `IDataSequence` — server-side counted data sequences (reconstructed)
- Plan: Exception handling across the RPC boundary (reconstructed)
- ._create_script
- FlatFieldPointing
- http_request_with_retries
- .__init__
- asyncio
- _ProxyContext
- test_module_state_publishing.py
- IModule
- .set_offsets_altaz
- ._expose
- .__call__
- Plan: raw-frame streaming endpoint in `BaseVideo`
- test_localcomm_state.py
- asyncio
- fixture
- Any
- integration
- ModuleNameFilter
- GuidingStatisticsPixelOffset
- README.md
- Install-ejabberd (xmpp)
- XmppComm._disconnected
- Autocompletion ()
- test_comm_interface_resolution.py
- pyobs.modules.pointing (doc)
- Any
- Header
- NamedTuple
- .open
- SkyCoord
- Target
- .__init__
- fixture
- ._subscribe_presence
- .set_optimal_focus
- check_changelog.sh
- delete_pubsub_nodes.py
- ejabberd 10x Shaper Benchmark Config
- list_pubsub_nodes.py
- ADR-0005: IConfig stays a stringly-keyed fallback
- Exception handling across the RPC boundary (design doc)
- .set_cooling
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
- .__call__
- .add_pointing_measurement
- .__call__
- Plan: Advertise event send/subscribe role in disco#info
- Any
- DummySkyOffsets
- StrEnum
- .calibrate
- asyncio
- Observation
- ModuleGui
- Future
- BackendObservationArchive
- BackendTaskArchive
- ObservationState
- .track_body
- .run_script
- .sync_target
- DataProvider
- PolymorphicBaseModel
- model_validator
- ClientSession
- Observation
- ObservationState
- TypedDict
- asyncio
- Task
- TaskArchive
- Time
- Any
- ClientSession
- Task
- TaskArchive
- Time
- Scheduler
- Script
- Task
- Observation
- ObservationState
- Task
- Time

## God Nodes (most connected - your core abstractions)
1. `Time` - 468 edges
2. `Image` - 428 edges
3. `Task` - 215 edges
4. `Interface` - 186 edges
5. `Module` - 165 edges
6. `DataProvider` - 155 edges
7. `ObservationList` - 145 edges
8. `Event` - 142 edges
9. `TaskData` - 114 edges
10. `Comm` - 112 edges

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

## Communities (501 total, 95 thin omitted)

### Community 0 - "ExposureStatus"
Cohesion: 0.10
Nodes (23): ExposureState, IExposure, The module controls a camera., BaseSpectrograph, ExposureInfo, Any, NamedTuple, Grabs a spectrum and returns reference. Args: broadcast: Broadcast existence of… (+15 more)

### Community 1 - ".get_fits_header_before"
Cohesion: 0.22
Nodes (6): Any, Initialize a new base dome., Returns FITS header for the current status of this module. Args: namespaces: If…, Any, Initialize a new base roof., Returns FITS header for the current status of this module. Args: namespaces: If…

### Community 2 - "Time"
Cohesion: 0.03
Nodes (98): AtNightConstraint, Constraint, ndarray, SkyCoord, Returns a boolean mask of candidates passing this constraint. Default…, MoonIlluminationConstraint, Moon illumination constraint., MoonSeparationConstraint (+90 more)

### Community 3 - "Module"
Cohesion: 0.04
Nodes (43): AbstractEventLoop, setter, The module that this Comm object is attached to., The module that this Comm object is attached to., Called, when the module connected to this Comm changes. Args: module: The…, Module, Any, ConfigValue (+35 more)

### Community 4 - "benchmark_state_throughput.py"
Cohesion: 0.14
Nodes (32): attach_module(), env_config(), main(), make_comm(), maybe_register(), open_publisher(), Any, Benchmark pyobs's XMPP state-push (XEP-0060) and RPC (XEP-0009)… (+24 more)

### Community 5 - "BaseTelescope"
Cohesion: 0.08
Nodes (21): MotionStatusMixin, BaseTelescope, BodyResolutionError, _ra_rate_on_sky(), On-sky RA rate in arcsec/sec, i.e. d(RA)/dt * cos(dec) -- matches JPL Horizons'…, Base class for telescopes., Current RA/Dec position in degrees, or None if unknown. Override in subclasses., Actually applies an absolute tracking rate to hardware. Must be implemented by… (+13 more)

### Community 6 - "Image"
Cohesion: 0.03
Nodes (75): MetaClass, Image, CCDData, Create Image from a bytes array containing a FITS file. Args: data: Bytes array…, Create image from FITS file. Args: filename: Name of file to load image from.…, A container class for astronomical image data and associated metadata. This…, Create image from astropy.CCDData. Args: data: CCDData to create image from.…, Load Image from HDU list. Args: data: HDU list. Returns: Image. (+67 more)

### Community 7 - "Observation"
Cohesion: 0.03
Nodes (74): BaseModel, Observation, ObservationState, FileSystemObservationArchive, Any, date, Clear schedule after given start time. Args: start_time: Start time to clear…, Fetch schedule from portal. Returns: Dictionary with tasks. Raises: Timeout: If… (+66 more)

### Community 8 - "asyncio"
Cohesion: 0.07
Nodes (71): asyncio, PortalObservationArchive, PortalTaskArchive, Task, make_obs(), make_obs_archive(), make_task(), make_task_archive() (+63 more)

### Community 9 - "ImageProcessor"
Cohesion: 0.04
Nodes (47): Annotation processors doc, Some info about :class:`pyobs.images.Image`., ImageProcessor, The error handling mode for this step., Processes an image. Args: image: Image to process. Returns: Processed image., Resets state of image processor, Circle, Draw a circle on an image, optionally interpreting the center in WCS… (+39 more)

### Community 10 - "XmppComm"
Cohesion: 0.03
Nodes (51): Any, Handles an event. Args: msg: Received XMPP message. node: pubsub node id the…, Safely send an XMPP message. Args: method: Method to call. *args: Parameters…, A Comm class using XMPP. This Comm class uses an XMPP server (e.g. `ejabberd…, Fetch the current item for *node* and dispatch it to *callback*. Called when a…, Store published capabilities for inclusion in disco#info responses., Return this client's own published capabilities., Fetch and deserialize capabilities for a remote module's interface. Retries… (+43 more)

### Community 11 - "Interface"
Cohesion: 0.04
Nodes (97): ABC, Shared XML serializer for pyobs 2.0 (urn:pyobs:rpc:1). Both the state pub/sub…, ICalibrate, The module can calibrate a device., IConfig, The module allows access to some of its configuration options., ICooling, The module can control the cooling of a device. (+89 more)

### Community 12 - "xmpp/rpc.py"
Cohesion: 0.09
Nodes (23): fault_to_xml(), params_to_xml(), Any, ClientXMPP, Element, Exception, Parse <fault> and return (exception_qualified_name, message)., RPC wrapper around XEP-0009 using pyobs 2.0 payload encoding (urn:pyobs:rpc:1). (+15 more)

### Community 13 - "utils/test_http.py"
Cohesion: 0.16
Nodes (31): MonkeyPatch, http_request_paginated(), Fetches all pages of a DRF-style paginated list endpoint and returns the…, make_response(), make_session(), asyncio, Test __wrapped__ directly (bypasses tenacity decorator)., Error message contains the HTTP status code, not the response body. (+23 more)

### Community 14 - "test_mastermind.py"
Cohesion: 0.14
Nodes (34): integration, MemoryObservationArchive, Observation, ObservationState, make_mastermind(), make_obs(), make_obs_archive(), Any (+26 more)

### Community 15 - ".open_file"
Cohesion: 0.12
Nodes (13): Any, DataFrame, HDUList, Convenience function for writing an Image to a FITS file. Args: filename: Name…, Convenience function for writing an Image to a FITS file. Args: filename: Name…, Convenience function for writing bytes to a file. Args: filename: Name of file…, Convenience function for reading a CSV file into a DataFrame. Args: filename:…, Convenience function for writing a CSV file from a DataFrame. Args: filename:… (+5 more)

### Community 18 - "DummyRoof"
Cohesion: 0.09
Nodes (32): WeatherState, DummyRoof, Any, Get the percentage the roof is open., Stop the motion. Args: device: Name of device to stop, or None for all. Raises:…, A dummy camera for testing., Creates a new dummy root., Open the roof. Raises: InitError: If the roof could not be initialized (e.g.… (+24 more)

### Community 19 - "mixins/test_fitsheader.py"
Cohesion: 0.06
Nodes (71): FitsHeaderMixin, ImageFitsHeaderMixin, Any, PrimaryHDU, Add requested FITS headers to header of given image. Args: image: Image with…, Add the cheap, local FITS headers to the given image (no I/O, no comm). This is…, Add requested FITS headers to header of given image. Args: image: Image with…, Add FITS header keywords to the given FITS header. Args: image: Image with… (+63 more)

### Community 20 - "Event"
Cohesion: 0.06
Nodes (40): Event, Base class for all events., DataType, TypedDict, DataType, TypedDict, DataType, TypedDict (+32 more)

### Community 21 - "MotionStatus"
Cohesion: 0.05
Nodes (47): IDome, The module controls a dome, i.e. a :class:`~pyobs.interfaces.IRoof` with a…, FilterState, DeviceMotionStatus, IMotion, MotionState, Any, The module controls a device that can move. (+39 more)

### Community 22 - "_DummyTelescopeBase"
Cohesion: 0.08
Nodes (16): IFocuser, The module is a focusing device., _DummyTelescopeBase, Any, Publish the current position as IPointingAltAz state, derived from RA/Dec and…, Background task that simulates telescope motion., Applies a tracking rate to the simulated hardware -- state publishing for…, Sets new focus. Raises: InvalidArgumentError: If given value is invalid.… (+8 more)

### Community 23 - "test_flatfielder.py"
Cohesion: 0.08
Nodes (60): make_flatfielder(), make_observer(), make_twilight_observer(), asyncio, parametrize, Regression test for #481: median == bias_level used to raise ZeroDivisionError., Observer stub returning a constant solar altitude for every sun_altaz() call., Observer stub distinguishing the first (now) vs second (+10min) sun_altaz()… (+52 more)

### Community 24 - "LocalComm"
Cohesion: 0.10
Nodes (17): LocalComm, Store presence state and dispatch to all subscribers., Return presence state of a connected module., Announce this module to already-connected peers, mirroring XmppComm's presence-…, Returns list of currently connected clients., Returns list of interfaces for given client., Checks whether the given client supports the given interface., Send an event to other clients. (+9 more)

### Community 25 - "tests/test_events.py"
Cohesion: 0.05
Nodes (58): Comm API doc (pyobs.comm), Events API doc (pyobs.events), BadWeatherEvent, Event to be sent on bad weather., Create Event from a dictionary. Args: obj_dict: JSON string for event. Returns:…, ExposureStatusChangedEvent, Any, Event to be sent, when the exposure status of a device changes. (+50 more)

### Community 26 - "test_lco_http.py"
Cohesion: 0.09
Nodes (43): Camera, CameraType, ConfigurationType, Enclosure, Instrument, InstrumentType, Mode, ModeType (+35 more)

### Community 27 - "Object"
Cohesion: 0.02
Nodes (119): PydanticBaseModel, create_object(), get_object(), Object, PrivateAttrMixin, EarthLocation, Observer, :class:`~pyobs.object.Object` is the base for almost all classes in *pyobs*. It… (+111 more)

### Community 28 - "test_basetelescope.py"
Cohesion: 0.10
Nodes (30): OrbitalElements, OrbitalElements, Any, Starts tracking a body defined by orbital elements. Args: elements: Orbital…, InvalidOrbitalElementsError, _orbital_plane_to_ecliptic_cartesian(), _propagate_elements(), Solves M = E - e*sin(E) for the eccentric anomaly E, via Newton-Raphson. Args:… (+22 more)

### Community 29 - "WindowingWidget"
Cohesion: 0.05
Nodes (14): BinningWidget, DataDisplayWidget, PrimaryHDU, Slot, Select path for auto-saving., ExposeWidget, Slot, ExposureTimeWidget (+6 more)

### Community 30 - "Interfaces (pyobs.interfaces) API doc"
Cohesion: 0.04
Nodes (53): Interfaces (pyobs.interfaces) API doc, IAbortable, IAcquisition, IAutoFocus, IAutoGuiding, IAutonomous, IBinning, ICalibrate (+45 more)

### Community 31 - "TaskData"
Cohesion: 0.04
Nodes (53): PointingScript, Time, Script for pointing the telescope for flats., Whether this config can currently run. Returns: True if script can run now., Run script. Raises: InterruptedError: If interrupted, Estimate duration of slewing to the flat-field pointing., # TODO: get a better estimate for slewing, Time (+45 more)

### Community 32 - "DummySolarTelescope"
Cohesion: 0.17
Nodes (10): DummySolarTelescope, Any, Moves to and continuously tracks a Heliocentric Polar (mu, psi) coordinate., Moves to and continuously tracks a Heliographic Stonyhurst (lon, lat)…, Moves to and continuously tracks a Helioprojective (theta_x, theta_y)…, Background task: while a solar-relative target is active, keeps the simulated…, A dummy telescope dedicated to solar pointing (Heliocentric Polar/Heliographic…, Converts Heliocentric Polar (mu, psi) to (ra, dec) in degrees, ICRS. Mirrors… (+2 more)

### Community 33 - "BaseCamera"
Cohesion: 0.05
Nodes (38): Any, ExposureStatus, Header, IDataSequence, IExposure, IExposureTime, IImageType, Image (+30 more)

### Community 34 - "_AbortableModule"
Cohesion: 0.11
Nodes (19): _AbortableModule, Any, asyncio, parametrize, Minimal test module with one guarded (non-whitelisted) RPC method., Module implementing IStartStop, whose abstract `start(**kwargs)` RPC method has…, A freshly constructed module hasn't been started yet., A regular RPC method must be rejected while the module is still STARTING. (+11 more)

### Community 35 - "test_astroplanscheduler.py"
Cohesion: 0.07
Nodes (45): AstroplanScheduler, Any, ObservingBlock, Actually do the scheduling, usually run in a separate process., Scheduler based on astroplan., Initialize a new scheduler. Args: twilight: astronomical or nautical, DynamicTarget, DataProvider (+37 more)

### Community 36 - "test_parallel.py"
Cohesion: 0.12
Nodes (27): Wait until all devices are in one of the given motion states. Args: abort:…, acquire_lock(), event_wait(), Lock, asyncio, _on_timeout sets TimeoutError on the future., _on_timeout is a no-op if future is already resolved., Future(empty=True) is already done and returns None. (+19 more)

### Community 37 - ".can_run"
Cohesion: 0.18
Nodes (5): DataProvider, Time, Resolve dynamic target. Returns False if no valid target found., Checks whether this task could run now. Returns: True, if the task can run now., Returns reason why task cannot run, or None if it can.

### Community 38 - "CoolingState"
Cohesion: 0.11
Nodes (26): _dataclass_to_xml(), _parse_scalar(), Any, Element, Deserialize an XML element (produced by ``value_to_xml``) to a Python value.…, Serialize a dataclass to ``<{namespace}state>`` with plain field children. Each…, Deserialize a ``<{ns}state>`` element to a dataclass instance. Handles both…, Parse a raw text value to the given type (legacy state format fallback). (+18 more)

### Community 39 - "PointingSeries"
Cohesion: 0.17
Nodes (7): Modules for robotic mode. TODO: write doc, PointingSeries, Any, SkyCoord, Module for running pointing series., Initialize a new pointing series. Args: grid: Grid to use for pointing series.…, Run a pointing series.

### Community 40 - "test_presence.py"
Cohesion: 0.05
Nodes (51): ModuleOpenedEvent, Event to be sent when a module has opened., ModuleLocation, _FakeProxyContext, make_xmpp_comm(), asyncio, Tests for Phase 2.5 Presence and Capabilities implementation., Module.open() passes empty string for label when _label is None. (+43 more)

### Community 41 - "SkyOffsets"
Cohesion: 0.13
Nodes (18): BaseCoordinateFrame, Angle, SkyCoord, Returns separatation between both coordinates, either in their own or a given…, Calculates spherical offset from first coordinate to second. Args: frame:…, Args: frame: Coordinate frame to use, or None to use coordinates' own frames.…, SkyOffsets, Tests that SkyCoord.transform_to is correctly used (+10 more)

### Community 42 - "test_xmpp_event_subscriptions.py"
Cohesion: 0.12
Nodes (23): _named_module(), Integration tests for explicit pubsub event subscriptions. Covers…, Registering a handler after a peer is already online must still result in a…, After the last handler for an event class is removed, no further events must…, Registering a handler for a local event (e.g.…, Local events must be unaffected by moving regular events onto the shared pubsub…, After a subscriber restarts (new session, same bare JID), it must resume…, Minimal module stub with a *real* name matching the comm's own JID user --… (+15 more)

### Community 43 - "Proxy"
Cohesion: 0.07
Nodes (21): Comm responsibility: Method calls (via Proxy), The Comm object is responsible for all communication between modules (see…, Proxy, Any, Signature, Execute a method on the remote client. Args: method: Name of method to call.…, Create local methods for the remote client., Function wrapper for remote calls. Args: method: Name of method to wrap.… (+13 more)

### Community 44 - ".__init__"
Cohesion: 0.04
Nodes (37): Any, Init new image processor. Args: on_error: How the pipeline should handle an…, Any, Init a new circle processor. Args: x: Center x coordinate. y: Center y…, Any, Init a new crosshair processor. Args: x: Center x coordinate. y: Center y…, Any, Init a new grayscale processor. Args: x: Center x coordinate. y: Center y… (+29 more)

### Community 45 - "robotic/test_scheduler.py"
Cohesion: 0.10
Nodes (47): _class_accepts_param(), Whether the class configured in `config` (a dict with a "class" key, or an…, DummyTask, make_async_gen(), make_obs(), make_scheduler(), asyncio, Observation (+39 more)

### Community 46 - "StandAlone"
Cohesion: 0.09
Nodes (40): pyobs.modules.test (doc), StandAlone, Quickstart (doc), pyobs-core (pip package), Test modules. TODO: write doc, Any, Example module that only logs the given message forever in the given interval., Creates a new StandAlone object. Args: message: Message to log in the given… (+32 more)

### Community 47 - "IDataSequence"
Cohesion: 0.29
Nodes (6): IDataSequence, Any, SECONDS, The module can grab a counted sequence of data (images, spectra, ...)., Start a sequence of `count` grabs. Returns immediately; progress is available…, Stop the sequence after the current grab. The grab currently in progress, if…

### Community 48 - "PyobsError"
Cohesion: 0.08
Nodes (20): Declare that the given PyobsError types (and their subclasses) fire often…, AbortedError, AcquisitionError, DeviceBusyError, GeneralError, InvalidArgumentError, ModuleError, ModuleStartingError (+12 more)

### Community 49 - "test_stellarexptime.py"
Cohesion: 0.09
Nodes (37): ExposureTimeProvider, Determine and return the exposure time in seconds. Returns: Exposure time in…, Abstract base class for providers that determine camera exposure time., ndarray, Find the brightest star near the image centre by fitting a 2D Gaussian. Args:…, Determines exposure time by finding a star near the image centre and adjusting…, Determine the optimal exposure time. Returns: Optimal exposure time in seconds., StellarExposureTimeProvider (+29 more)

### Community 50 - "SkyFlatsBasePointing"
Cohesion: 0.14
Nodes (13): IPointingAltAz, PolymorphicBaseModel, Move telescope. Args: telescope: Telescope to use., Base class for flat pointings., SkyFlatsBasePointing, IPointingAltAz, Static flat pointing., Move telescope. Args: telescope: Telescope to use. (+5 more)

### Community 51 - "test_dynamictarget.py"
Cohesion: 0.15
Nodes (27): Constraint, fixture, _clear_vfs_buffer(), MemoryFile's buffer is a process-wide class dict; every Mastermind instance in…, data(), make_task(), mock_vfs(), observer() (+19 more)

### Community 52 - "WindowCapabilities"
Cohesion: 0.08
Nodes (40): ModuleCapabilities, WindowCapabilities, make_module(), Minimal module stub satisfying what XmppComm needs on connect. IModule must be…, Integration test for DummyCamera state publishing via XEP-0060., DummyCamera.open() must publish IWindow.Capabilities with the SimCamera full…, DummyCamera.open() must publish IModule.Capabilities with version and label., get_capabilities() must return None for an interface DummyCamera doesn't… (+32 more)

### Community 53 - "test_shellcommand.py"
Cohesion: 0.10
Nodes (29): ParserState, Any, Enum, ShellCommand, ShellCommandResponse, asyncio, test_command_number_increments(), test_execute_invalid_param() (+21 more)

### Community 54 - "Calibration"
Cohesion: 0.10
Nodes (18): Calibration, Calibrate an image. Args: image: Image to calibrate. Returns: Calibrated image., Calibrate an image using master bias, dark, and flat frames fetched from an…, Find master calibration frame for given parameters using a cache. Args:…, _CCDDataCalibrator, CCDData, ConcreteArchive, mock_image() (+10 more)

### Community 55 - "ImagingScript"
Cohesion: 0.14
Nodes (12): Future, ImagingScript, Any, FitsHeaderEntry, Target, Time, Default script for imaging configs., Whether this config can currently run. Returns: True, if the script can run now (+4 more)

### Community 56 - "Publisher"
Cohesion: 0.07
Nodes (25): Any, Creates a new seeing estimator. Args: sources: List of sources (e.g. cameras)…, Any, Initializes a new ApplyAltAzOffsets. Args: min_offset: Min offset in arcsec to…, Any, Any, Initializes a new ApplyRaDecOffsets. Args: min_offset: Min offset in arcsec to…, CsvPublisher (+17 more)

### Community 57 - "PortalObservationArchive"
Cohesion: 0.08
Nodes (22): PortalObservationArchive, Any, Observation, ObservationArchive, ObservationList, ObservationState, TaskArchive, Time (+14 more)

### Community 58 - "test_lcoscript.py"
Cohesion: 0.10
Nodes (26): LcoAutoFocusScript, Auto focus script for LCO configs., # TODO: unfortunately this never happens, since the LCO portal forces…, LcoDefaultScript, Default script for LCO configs., LcoScript, Script for LCO configs. Dispatches to one of the named scripts in ``scripts``,…, Estimate duration based on the duration calculated by the LCO portal. (+18 more)

### Community 59 - "applyoffsets.py"
Cohesion: 0.09
Nodes (21): IOffsetsRaDec, Any, DEGREES, RaDecOffsetState, The module supports RA/Dec offsets, usually combined with…, Move an RA/Dec offset. Args: dra: RA offset in degrees. ddec: Dec offset in…, DummyRaDecTelescope, Any (+13 more)

### Community 60 - "FilenameFormatter"
Cohesion: 0.07
Nodes (32): Format filename with given formatter., FilenameFormatter, fitssec(), format_filename(), parse_section_bounds(), Any, Header, NDArray (+24 more)

### Community 61 - "test_basevideo.py"
Cohesion: 0.12
Nodes (46): ImageRequest, NextImage, make_basevideo(), make_request(), asyncio, BaseVideo must forward fits_header_timeout to ImageFitsHeaderMixin, not swallow…, _route_paths(), test_activate_camera_from_inactive_calls_hook() (+38 more)

### Community 62 - "test_yaml_archives.py"
Cohesion: 0.11
Nodes (37): FileSystemTaskArchive, Any, Task archive based on files., Creates a new filesystem-based task archive. Args: extension: Extension of…, Returns time when last time any blocks changed., Returns list of projects. Returns: List of projects., Returns list of schedulable tasks. Returns: List of schedulable tasks, Returns the task with the given ID. Returns: Task with given ID. (+29 more)

### Community 63 - "Any"
Cohesion: 0.10
Nodes (16): ImageHDU, Any, floating, HDUList, Header, NDArray, setter, Table (+8 more)

### Community 64 - "FlatFielder"
Cohesion: 0.07
Nodes (28): Enum, ICamera, IFilters, ITelescope, Object, FlatFielder, Any, Calls next step in state machine. Args: telescope: Telescope to use. camera:… (+20 more)

### Community 65 - "IExposure"
Cohesion: 0.06
Nodes (34): Comm._get_client, ADR-0001: Check Interface.state by own declaration, not inheritance, Composite interfaces inheriting stateful bases (ICamera, IDome, ITelescope, ...), Interface.capabilities (ClassVar), Interface.has_own_state(), Interface.state (ClassVar), XmppComm disco#info feature registration, ADR-0006: Proxy.wait_for_state() returns None on timeout (+26 more)

### Community 66 - "Telegram"
Cohesion: 0.13
Nodes (19): CallbackContext, Any, Save storage file. Args: context: Telegram context., Is user authorized? Args: context: Telegram context. user_id: ID of user.…, Store new user in auth database. Args: context: Telegram context. user_id: ID…, Handle /start command. Args: update: Message to process. context: Telegram…, Handle /exec command. Args: update: Message to process. context: Telegram…, Handle click on buttons. Args: update: Message to process. context: Telegram… (+11 more)

### Community 67 - "Any"
Cohesion: 0.09
Nodes (15): Any, ProxyType, Returns object directly if it is of given type. Otherwise get proxy of client…, Backend hook, called when a proxy exists but doesn't implement obj_type.…, Calls proxy() in a safe way and returns None instead of raising an exception., Returns a context manager; use as `async with self.proxy(...) as x:`., Same as proxy(), but yields None inside the block instead of raising., True if a proxy of the given type can currently be resolved. Doesn't keep a… (+7 more)

### Community 68 - "Task"
Cohesion: 0.04
Nodes (108): AirmassConstraint, ndarray, SkyCoord, DataProvider, Data provider for Merit classes. The ``@cache``d methods below are only safe to…, ConstantMerit, Merit function that returns a constant value., Merit function that uses time windows. (+100 more)

### Community 69 - "Offsets"
Cohesion: 0.09
Nodes (16): CorrelationMaxCloseToBorderError, Exception, BrightestStarGuiding, Any, SkyCoord, Table, Initializes a new auto guiding system., Processes an image and sets x/y pixel offset to reference in offset attribute.… (+8 more)

### Community 70 - ".now"
Cohesion: 0.08
Nodes (29): Observer, ObservationArchiveEvolution, date, Observer, Populates the task cache and the one real night (anchored to `start`) up front.…, Freezes observation cache. After this: a task-id miss raises RuntimeError; a…, Returns list of observations for the given task. Args: date: Date of night to…, MockLcoObservationArchive (+21 more)

### Community 71 - "PyObsError"
Cohesion: 0.07
Nodes (31): ADR-0003: Restrict Proxy access to async with, has_proxy() / safe_proxy, Proxy, _ProxyContext.__await__ (removed), specs/design/pyobs_2_0_wire_protocol.md, acl: config block (allow/deny), ADR-0004: Enforce access control on the callee, not the caller, Module.execute() (+23 more)

### Community 72 - "test_proxy.py"
Cohesion: 0.12
Nodes (33): _cooling_state(), make_proxy(), asyncio, Methods from both interfaces are callable., A CoolingState timestamped `age_seconds` in the past., Callers that don't pass max_age see no behavior change, however old the cached…, A future interface whose State dataclass has no `time` field fails loudly at…, Create a Proxy with a mock comm. (+25 more)

### Community 73 - "XEP_0009"
Cohesion: 0.12
Nodes (7): Expose method to public., Expose method to public., Expose method to public., Small fix for the original XEP_0009 plugin., Route RPC-level errors (e.g. forbidden, item-not-found) through the same…, XEP_0009, XEP_0009_original

### Community 74 - "test_schedulereader.py"
Cohesion: 0.15
Nodes (21): LcoScheduleReader, Update list of requests. Args: force: Force update., Fetch schedule from portal. Returns: Dictionary with tasks. Raises: Timeout: If…, Fetch schedule from portal. Args: start_before: Task must start before this…, Returns the active scheduled task at the given time. Args: time: Time to return…, Scheduler for using the LCO portal, make_observation(), make_reader() (+13 more)

### Community 75 - "PyobsDaemon"
Cohesion: 0.06
Nodes (28): CLI, Initializes a new instance of the CLI class., Overwrite this to set CLI parameters with argparse., Overwrite this to actually run the CLI., Load config from config file, Load config from environment variables., main(), Any (+20 more)

### Community 76 - "IPointingAltAz.py"
Cohesion: 0.07
Nodes (39): AltAzState, IPointingAltAz, Any, DEGREES, The module can move to Alt/Az coordinates, usually combined with…, Moves to given coordinates. Args: alt: Alt in deg to move to. az: Az in deg to…, IPointingRaDec, Any (+31 more)

### Community 77 - "test_config.py"
Cohesion: 0.07
Nodes (43): include_parts(), pre_process_yaml(), Any, Replaces blocks of the form {include <source.yaml> <key>} in the loaded config…, Finds anchors ('&') in the included file. Args: filename: name of the file with…, Replaces aliases ('<<: *...') in the main file by the anchor in the included…, Include nested contents from another YAML file. Args: include: dictionary based…, Finds keys that hold an anchor ('&') at the top level (no leading whitespace)… (+35 more)

### Community 78 - "test_control.py"
Cohesion: 0.13
Nodes (45): ConditionalRunner, Script for running an if condition., ParallelRunner, Script for running other scripts in parallel., Script for running a sequence of other scripts., SequentialRunner, AlwaysRunScript, NeverRunScript (+37 more)

### Community 79 - "xmppcomm.py"
Cohesion: 0.08
Nodes (20): Any, Disconnect only, instead of slixmpp's default reconnect-in-place. xep_0199's…, Called when the server sends a <stream:error/>, e.g. when this connection gets…, Whether this client was (or is being) kicked because another session connected…, Human-readable reason text sent alongside the conflict stream error, if any., Wait for client to connect. Returns: Success or not., XMPP client for pyobs., Session start event. Args: event: The event sent at session start. (+12 more)

### Community 80 - "Weather"
Cohesion: 0.11
Nodes (27): Any, Builds the current per-sensor readings from the last raw status, for state…, Returns FITS header for the current status of this module. Args: namespaces: If…, Connection to pyobs-weather., Initialize a new pyobs-weather connector. Args: url: URL to weather station…, Weather, asyncio, test_active_flag_defaults_true_and_tracks_stop() (+19 more)

### Community 81 - "Portal"
Cohesion: 0.06
Nodes (38): InstrumentLocation, ConfigDB, Portal, Any, Do a GET request on the portal. Args: url: URL to request. Returns: Response…, Clear schedule after given start time. Args: start: Start time to clear…, Submit observations. Args: observations: List of observations to submit., Send report to LCO portal Args: status_id: id of config status status: Status… (+30 more)

### Community 82 - "test_autoguiding.py"
Cohesion: 0.20
Nodes (32): make_guiding(), make_image(), asyncio, _state_for(), test_auto_guiding_sleeps_when_disabled(), test_auto_guiding_takes_and_processes_image_when_enabled(), test_get_fits_header_after_includes_statistics(), test_get_fits_header_before_reports_closed_loop() (+24 more)

### Community 83 - "test_acquisition.py"
Cohesion: 0.28
Nodes (29): OffsetResult, make_acquisition(), make_camera(), make_image(), make_telescope(), asyncio, offsets_frame: 'radec', 'altaz', or None (telescope supports neither offsets…, _state_for() (+21 more)

### Community 84 - "PipelineMixin"
Cohesion: 0.05
Nodes (45): Handle an ImageError raised by this step, when on_error == "error". Override…, PipelineMixin, Any, Mixin for a module that needs to implement an image pipeline., Initializes the mixin. Args: steps: Pipeline steps to run on images. archive:…, Whether the given class declares an `archive` parameter anywhere in its…, Resets all previous state of the involved image processors., PipelineCamera (+37 more)

### Community 85 - "Ring"
Cohesion: 0.14
Nodes (9): integer, Any, floating, NDArray, Estimate pixel guiding offsets from asymmetry of spilled light around a fiber…, Init an image processor that adds the calculated offset. Args: fibers:…, Processes an image and sets x/y pixel offset to reference in offset attribute.…, Ring (+1 more)

### Community 86 - "loaded_pyobs_packages"
Cohesion: 0.40
Nodes (9): loaded_pyobs_packages(), Return the version of every loaded ``pyobs``-prefixed distribution. Builds the…, _fake_modules(), test_defaults_to_sys_modules(), test_excludes_non_pyobs_distributions(), test_excludes_not_loaded_top_level_names(), test_returns_loaded_pyobs_distributions(), test_skips_package_not_found() (+1 more)

### Community 87 - "DataCache"
Cohesion: 0.10
Nodes (15): Any, Initializes file cache. Args: port: Port for HTTP server. cache_size: Size of…, DataCache, DataCacheEntry, Any, A single entry in the data cache., Delete entry in cache. Args: name: Name of entry to delete., Create a new entry for the data cache Args: name: Name of item data: Data for… (+7 more)

### Community 88 - "test_exception_logging.py"
Cohesion: 0.27
Nodes (20): Callback for flat-field class to call with statistics., FocusError, _AbortableModule, asyncio, Minimal test module whose abort() raises whatever exception it's given. Starts…, test_call_id_is_attached_to_the_exception_and_included_in_the_log_line(), test_call_id_omitted_from_log_line_when_not_given(), test_disable_exception_logging_covers_subclasses() (+12 more)

### Community 89 - "test_config_schema.py"
Cohesion: 0.20
Nodes (22): ConfigFieldSchema, ConfigSchema, dataclass_to_schema(), _field_schema(), Any, _pydantic_field_schema(), pydantic_to_schema(), Recursively derive a ConfigSchema from a dataclass type. Handles: plain scalars… (+14 more)

### Community 90 - "Application"
Cohesion: 0.06
Nodes (45): Module, Application, _disable_iers_auto_download(), GuiApplication, InfluxLogConfig, Any, Initializes a pyobs application. Exactly one of `config`/`module_factory` must…, React to signals and quit the module. (+37 more)

### Community 91 - "DummyComm"
Cohesion: 0.13
Nodes (16): DummyComm, A dummy implementation of the Comm interface., Always return zero clients., No interfaces implemented., Interfaces are never supported., Send an event to other clients. Args: event (Event): Event to send, comm(), asyncio (+8 more)

### Community 92 - "CallModuleScript"
Cohesion: 0.11
Nodes (24): model_validator, Any, get_class_from_string(), Get class from a given string. Args: class_name: Name of class as string.…, _build_params_model(), CallModuleScript, _get_valid_param_names(), Script for calling a method on a module. (+16 more)

### Community 93 - "ProjectedOffsets"
Cohesion: 0.14
Nodes (20): ProjectedOffsets, Any, floating, NDArray, Processes an image and sets x/y pixel offset to reference in offset attribute.…, Project image along x and y axes and return results. Args: image: Image to…, Compute pixel offsets for guiding by correlating 1D projections of the current…, Initializes a new auto guiding system. (+12 more)

### Community 94 - "LocalArchive"
Cohesion: 0.06
Nodes (71): DataFrame, FrameInfo, Any, ImageType, Time, Base class for frame infos., LocalArchive, Any (+63 more)

### Community 95 - "HttpFile"
Cohesion: 0.10
Nodes (18): ArchiveFile, Wraps a file in an archive. To be used in combination with pyobs-archive., Creates a new archive file. Args: name: Name of file. mode: Open mode (r/w).…, If in write mode, actually send the file to the archive., HttpFile, Any, Read number of bytes from stream. Args: n: Number of bytes to read. Read until…, Write data into the stream. Args: s: Bytes of data to write. (+10 more)

### Community 96 - "test_transit_mastermind.py"
Cohesion: 0.17
Nodes (22): Configuration, InstrumentConfig, make_transit_merit(), make_transit_observation(), make_transit_task(), asyncio, integration, Mastermind picks up a transit observation and runs it to completion. (+14 more)

### Community 97 - "InfluxHandler"
Cohesion: 0.24
Nodes (4): InfluxHandler, Any, LogRecord, WriteOptions

### Community 98 - "FocusSeries"
Cohesion: 0.05
Nodes (40): AutoFocusPoint, fit_hyperbola(), Fit a hyperbola Args: x_arr: X data y_arr: Y data y_err: Y errors Returns:…, FocusSeries, Analyse given image. Args: image: Image to analyse focus_value: Value to fit…, Returns a list of data points., Fit focus from analysed images Returns: Tuple of new focus and its error, Base class for focus series helper classes. (+32 more)

### Community 99 - "RemoveBackground"
Cohesion: 0.21
Nodes (9): Any, Estimate and subtract the background from an image using a DAOPhot-style…, Init an image processor that removes background from image. Args: sigma: Sigma…, Remove background from image. Args: image: Image to remove background from.…, RemoveBackground, asyncio, test_call_const_background(), test_init() (+1 more)

### Community 100 - "make_proxy_cm"
Cohesion: 0.21
Nodes (27): make_proxy_cm(), Wrap value in a MagicMock standing in for the async context manager returned by…, make_flatfield(), asyncio, Find the state object set_state() was called with for the given interface., _ready_telescope(), _state_for(), test_abort_sets_event() (+19 more)

### Community 101 - "PortalTaskArchive"
Cohesion: 0.08
Nodes (19): PortalTaskArchive, Any, ClientSession, TaskArchive, Time, Fetches last schedule update time., Fetch projects from portal., Fetch tasks from portal. (+11 more)

### Community 102 - "test_background_task.py"
Cohesion: 0.07
Nodes (33): ObjectClass, PydanticModel, BackgroundTask, Any, get_safe_object(), Any, ProxyType, Calls get_object in a safe way and returns None, if an exceptions thrown. Args:… (+25 more)

### Community 103 - "_DaoBackgroundRemover"
Cohesion: 0.07
Nodes (31): Source Detection processors doc, DaophotSourceDetection (detection processor), SepSourceDetection (detection processor), _DaoBackgroundRemover, Any, floating, NDArray, DaophotSourceDetection (+23 more)

### Community 104 - "test_coordinates.py"
Cohesion: 0.15
Nodes (25): offset_altaz_to_radec(), offset_radec_to_altaz(), EarthLocation, SkyCoord, make_altaz(), make_radec(), SkyCoord, Zero offset returns (0, 0). (+17 more)

### Community 105 - "get_registered_interface"
Cohesion: 0.12
Nodes (22): get_registered_interface(), Look up a registered interface class by name, or None if unknown., All currently-registered interface classes, keyed by name., registered_interfaces(), Tests for the import-time interface registry in pyobs/interfaces/interface.py.…, Re-importing the same interface module twice resolves to the same class object…, Two genuinely different classes claiming the same name must raise TypeError…, Mutating the returned dict must not affect the live registry. (+14 more)

### Community 106 - "test_xmpp_rpc.py"
Cohesion: 0.19
Nodes (14): Integration tests for the pyobs 2.0 RPC payload encoding (urn:pyobs:rpc:1).…, set_binning(int, int) -> None: multiple int params, void return., Calling a method that raises on the remote side propagates the exception., set_cooling(bool, float) then verify via state: full encode/decode cycle., set_cooling(bool, float) -> None: void return with bool + float params., set_gain(float) -> None and verify via IGain state: float param, state readback., set_gain(float) then verify via IGain state: float param round-trip., test_rpc_bool_float_roundtrip() (+6 more)

### Community 107 - "PixelOffsets"
Cohesion: 0.11
Nodes (14): PixelOffsets, AstrometryOffsets, Any, SkyCoord, Compute pixel offsets from WCS by comparing image reference coordinates to…, Initializes new astrometry offsets. MUST run after an astrometry processor., Processes an image and sets x/y pixel offset to reference in offset attribute.…, DummyOffsets (+6 more)

### Community 108 - "Plan: Systematic ejabberd throughput/latency benchmarking"
Cohesion: 0.07
Nodes (28): Blockers found while getting the environment working (2026-07-27), Conclusion on the O(N²) finding: real bug, not a pyobs design problem, Deeper dig: isolating the real mechanism (2026-07-27, same day), Environment, Fifth investigation session (2026-07-28, same day) — found the specific mechanism: an un-re-armed passive socket, First real results (2026-07-27), Fourth live run (2026-07-28, same day) — found the actual mechanism: stuck per-connection Recv-Q on ejabberd's side, Full incident timeline and what's been ruled out (2026-07-27) (+20 more)

### Community 109 - "_SepAperturePhotometry"
Cohesion: 0.15
Nodes (11): Any, floating, NDArray, Table, since SEP sums up whole pixels, we need to do the same on an image of ones for…, _SepAperturePhotometry, asyncio, fixture (+3 more)

### Community 110 - "Mixins (pyobs.mixins) API doc"
Cohesion: 0.09
Nodes (25): Images (pyobs.images) API doc, ImageProcessor base class, Object base class, Pipeline module (pyobs.modules.image.Pipeline), API index (toctree), ICamera, IStartStop, CameraSettingsMixin (+17 more)

### Community 111 - "Script base class"
Cohesion: 0.09
Nodes (25): IMode, TaskData, AutoFocusScript, CallModuleScript, CasesRunner, ConditionalRunner, ConstSkyflatPriorities, DarkBiasScript (+17 more)

### Community 112 - "ImageWatcher"
Cohesion: 0.18
Nodes (7): CurrentFile, ImageWatcher, Add a file to the file queue. Args: filename (str): Local filename of new file., Can be overwritten by derived classes to do extra processing on files. All…, Can be overwritten by derived classes to do clean up after successful copying.…, Watch for new files and write them to all given destinations. Watches a path…, test_constructor_raises_without_destinations()

### Community 113 - "Comm"
Cohesion: 0.06
Nodes (18): Comm responsibility: Discovery (clients_with_interface), Comm responsibility: Events (broadcast typed events), Comm, Base class for all Comm modules in pyobs., Returns list of currently connected clients. Returns: (list) list of currently…, Returns list of currently connected clients that implement the given interface.…, Checks, whether the given client supports the given interface. Args: client:…, Background thread for handling the logging. (+10 more)

### Community 114 - "LogEvent"
Cohesion: 0.08
Nodes (26): Send an event to all connected modules. Args: event: Event to send.…, CommLoggingHandler, Any, A logging handler that sends all messages through a Comm module., Create a new logging handler. Args: comm: Comm module to use., Send a new log entry to the comm module. Args: rec: Log record to send., LogEvent, Event for log entries. (+18 more)

### Community 115 - "test_dummyradectelescope.py"
Cohesion: 0.24
Nodes (21): TrackingRateCapabilities, make_dummyradectelescope(), asyncio, test_move_altaz_clears_tracked_body(), test_move_altaz_resets_tracking_mode_to_off(), test_move_radec_clears_tracked_body(), test_move_radec_resets_tracking_mode_to_sidereal(), test_move_task_applies_tracking_rate_to_position() (+13 more)

### Community 116 - "dummycamera.py"
Cohesion: 0.06
Nodes (38): Binning, BinningCapabilities, BinningState, IBinning, Any, The camera supports binning, to be used together with…, Set the camera binning. Args: x: X binning. y: Y binning. Raises: ValueError:…, IFlatField (+30 more)

### Community 117 - "test_xmpp_acl.py"
Cohesion: 0.22
Nodes (12): Integration tests for Phase 8 Access Control (ACLs) over real XMPP. Verifies…, A caller granted "*" access under "allow" can still call normally., A caller not present in the "allow" map is denied by default., A caller on the "deny" list gets exc.RemoteError with a forbidden message, not…, Naming an interface under "allow" permits all of its methods, but nothing…, A module not on the "deny" list is unaffected., test_acl_allow_denies_unlisted_caller(), test_acl_allow_interface_name_sugar() (+4 more)

### Community 118 - "MemoryFile"
Cohesion: 0.14
Nodes (9): MemoryFile, Any, A file stored in memory., Open/create a file in memory. Args: name: Name of file. mode: Open mode., Read number of bytes from stream. Args: n: Number of bytes to read, -1 reads…, Write data into the stream. Args: buf: Bytes of data to write., Whether stream is closed., asyncio (+1 more)

### Community 119 - "VFSFile"
Cohesion: 0.08
Nodes (16): Any, Returns content of given path. Args: path: Path to list. kwargs: Parameters for…, Find files by pattern matching. Args: path: Path to search in. pattern: Pattern…, Remove file at given path. Args: path: Path of file to delete. Returns: Success…, Base class for all VFS file classes., Checks, whether a given path or file exists. Args: path: Path to check.…, VFSFile, __getattr__() (+8 more)

### Community 120 - "LocalFile"
Cohesion: 0.13
Nodes (15): LocalFile, Any, Find files by pattern matching. Args: path: Path to search in. pattern: Pattern…, Wraps a local file with the virtual file system., Remove file at given path. Args: path: Path of file to delete. Returns: Success…, Checks, whether a given path or file exists. Args: path: Path to check. root:…, Open a local file. Args: name: Name of file. mode: Open mode. root: Root to…, Returns local path of given path. Args: path: Path to list. kwargs: Parameters… (+7 more)

### Community 121 - "test_version_mismatch.py"
Cohesion: 0.13
Nodes (24): FakeInterface, make_xmpp_comm(), asyncio, LogCaptureFixture, Tests for the mixed-version-fleet diagnostic on interface resolution. Covers…, The raw feature list is cached even for names that get filtered out --…, Base Comm._diagnose_missing_interface returns None -- e.g. LocalComm, which…, Sanity check that ICooling/IModule (used above as real interfaces) still have… (+16 more)

### Community 122 - "CLAUDE.md (repo guide)"
Cohesion: 0.10
Nodes (23): check_coverage.md (coverage gap survey), Coverage Category A: needs live external service/credentials, Coverage Category B: GUI widgets needing a display, Coverage Category C: CLI/app bootstrap, Coverage Category D: dev/test-support tooling, Coverage Category E: real gaps, no external-service/GUI excuse, Cross-repo docs convention (Repos: line + specs/README.md pointer), graphify usage rules for this repo (+15 more)

### Community 123 - "SoftBin"
Cohesion: 0.16
Nodes (11): Any, floating, NDArray, Bin a 2D image by averaging non-overlapping blocks, updating relevant FITS…, Init a new software binning pipeline step. Args: binning: Binning to apply to…, Bin an image. Args: image: Image to bin. Returns: Binned image., SoftBin, asyncio (+3 more)

### Community 124 - "FocusModel"
Cohesion: 0.07
Nodes (40): IFilters, Any, The module can change filters in a device., Set the current filter. Args: filter_name: Name of filter to set. Raises:…, OptimalFocusState, Any, Initializes the mixin. Args: filters: Filter wheel module. filter: Filter to…, FocusModel (+32 more)

### Community 125 - "SFTPFile"
Cohesion: 0.22
Nodes (5): Any, VFS wrapper for a file that can be accessed over a SFTP connection., Open/create a file over a SSH connection. Args: name: Name of file. mode: Open…, Returns content of given path. Args: path: Path to list. kwargs: Parameters for…, SFTPFile

### Community 126 - "ImageSourceFilter"
Cohesion: 0.12
Nodes (17): ImageSourceFilter, Any, floating, NDArray, Table, Filters the source table after pysep detection has run Args:…, Filter a source catalog by border distance, quality metrics, and brightness,…, Convert from FITS to numpy conventions for pixel coordinates. (+9 more)

### Community 127 - "test_darkbias.py"
Cohesion: 0.19
Nodes (21): DarkBiasScript, Time, Script for running darks or biases., Whether this config can currently run. Returns: True if script can run now., Run script. Raises: InterruptedError: If interrupted, Estimate duration of the dark/bias series., make_camera(), make_script() (+13 more)

### Community 128 - ".__init__"
Cohesion: 0.10
Nodes (13): Args: label: Label for module. If None, name is used. own_comm: If True, module…, Returns name of module., List interfaces and methods of this module., Returns a dictionary with config caps., Check for getter and setter Params: name: Name of variable. Returns: Tuple of…, Returns dict of all config capabilities. First value is whether it has a…, Args: modules: Dictionary with modules. shared: Shared objects between modules., Any (+5 more)

### Community 129 - "OffsetsAltAzEvent"
Cohesion: 0.11
Nodes (14): DataTypeAltAz, DataTypeRaDec, OffsetsAltAzEvent, OffsetsEvent, OffsetsRaDecEvent, Any, TypedDict, Event to be sent when an RA/Dec offset is to be moved. (+6 more)

### Community 130 - "Plan: pyobs-pipeline"
Cohesion: 0.08
Nodes (24): Celery task, Consequences, Django models, Implementation checklist, Log viewing, Open questions, Pages, Pipeline builder (+16 more)

### Community 131 - "Test Localcomm (local)"
Cohesion: 0.18
Nodes (22): make_comm(), asyncio, fixture, Sender also receives its own events., Reset LocalNetwork singleton between tests., #677: a late-joining module must announce itself via ModuleOpenedEvent once…, get_interfaces returns [] when the remote client has no module., reset_network() (+14 more)

### Community 132 - "integration/conftest.py"
Cohesion: 0.23
Nodes (13): connect(), make_camera_comm(), make_unopened_comm(), make_xmpp_comm(), fixture, Fixtures shared across all integration tests., Factory fixture: ``await make_xmpp_comm(user)`` returns an open XmppComm for…, Connect a module to LocalComm and return the comm. (+5 more)

### Community 133 - ".__init__"
Cohesion: 0.06
Nodes (20): Any, JSON representation of event., String representation of event., Generic from_dict method for derived classes that don't need their own., Any, Any, Any, Initializes a new good weather event. Args: eta: Predicted ETA for when the… (+12 more)

### Community 134 - "module.py"
Cohesion: 0.07
Nodes (14): ConfigCapabilities, A module in *pyobs* is the smalles executable unit. The base class for all…, MultiModule, Wait until all sub-module tasks have finished., Cancel sub-module tasks and close shared objects., Quit all sub-modules., Returns pyobs version of module., React to other modules connecting. (+6 more)

### Community 135 - "test_dummymode.py"
Cohesion: 0.32
Nodes (13): _event_of_type(), make_dummymode(), asyncio, Find the most recent state object set_state() was called with for the given…, Find the send_event() call with an event of the given type., _state_for(), test_init_default_modes(), test_init_park_stop_motion_are_noops() (+5 more)

### Community 136 - "MockWeather"
Cohesion: 0.13
Nodes (23): pyobs.modules.weather (doc), MockWeather, Weather (module), MockWeather, Any, Returns FITS header for the current status of this module. Args: namespaces: If…, A mock weather station for testing and simulations., Creates a new mock weather station. Args: good: Initial weather-good state.… (+15 more)

### Community 137 - "SchedulerItem"
Cohesion: 0.13
Nodes (9): Iterate over scheduler items, Return schedule item., Find a possible slot for a given filter/binning in the given schedule Args:…, A single item in the flat scheduler, Checks, whether a new scheduler item would overlap an existing item Args:…, Initializes a new scheduler item Args: start: Start time in seconds end: End…, Nice string representation for item, Calculate schedule starting at given time Args: time: Time to start schedule at (+1 more)

### Community 138 - "Grid"
Cohesion: 0.09
Nodes (21): AvoidMoon, GridFilter, Any, RandomizeGrid, Initialize the conversion filter. Args: grid: Upstream grid or filter that…, Abstract base class for grid filters that wrap another GridNode. A GridFilter…, Initialize the frame conversion filter. Args: grid: Upstream grid or filter…, Randomize iteration order by rotating the underlying sequence. For each… (+13 more)

### Community 139 - "test_kiosk.py"
Cohesion: 0.24
Nodes (21): _cancel_after(), _make_image(), make_kiosk(), asyncio, Side effect that raises CancelledError starting from the n-th call., test_camera_thread_captures_and_adjusts_exposure_time(), test_camera_thread_clips_exposure_time_to_minimum(), test_camera_thread_continues_on_file_not_found() (+13 more)

### Community 140 - "Plan: pyobs-iag50 pyobs-core 2.x migration"
Cohesion: 0.17
Nodes (12): 1. `pyobs_iag50/aligntest.py`, 2. `pyobs_iag50/pointing.py`, 3. `config/iag50srv/pointing.yaml`, Consequences, Design decisions, Implementation, Open questions — need your input before finishing §3, Plan: pyobs-iag50 pyobs-core 2.x migration (+4 more)

### Community 141 - "Robotic recipe (doc)"
Cohesion: 0.17
Nodes (21): pyobs.modules.robotic (doc), Mastermind (module), PointingSeries, Scheduler (module), ScriptRunner, Robotic recipe (doc), AirmassConstraint, BackendObservationArchive (+13 more)

### Community 142 - "._move_radec"
Cohesion: 0.11
Nodes (15): AltitudeLimitError, _format_dec(), _format_ra(), MissingObserverError, Actually starts tracking on given coordinates. Must be implemented by derived…, Starts tracking on given coordinates. Args: ra: RA in deg to track. dec: Dec in…, Format an RA in degrees as sexagesimal HH:MM:SS.sss. Deliberately avoids…, Actually moves to given coordinates. Must be implemented by derived classes.… (+7 more)

### Community 143 - "SiderealTarget"
Cohesion: 0.04
Nodes (49): HeliocentricPolarTarget, SkyCoord, Target, HelioprojectiveTarget, SkyCoord, Target, CsvPicker, Target (+41 more)

### Community 144 - "RollingTimeAverage"
Cohesion: 0.10
Nodes (24): Any, Runs an async callable to completion on a dedicated worker thread, off the…, run_cpu_bound(), RollingTimeAverage, _T, asyncio, test_run_cpu_bound_propagates_exception(), test_run_cpu_bound_returns_value() (+16 more)

### Community 145 - "._create_image"
Cohesion: 0.11
Nodes (13): NamedTuple, NDArray, ExposureInfo, Info about a running exposure., LastImage, Build the JSON meta header and raw bytes for one frame. Args: data: Numpy array…, Convert a FITS header value to a JSON-serializable Python scalar., Create a JPEG ge from a numpy array and return as bytes. Args: data: Numpy… (+5 more)

### Community 146 - "WeatherApi"
Cohesion: 0.19
Nodes (10): Any, ClientSession, WeatherApi, MockResponse, Any, asyncio, test_get_current_status(), test_get_sensor_value() (+2 more)

### Community 148 - "utils/exceptions.py"
Cohesion: 0.14
Nodes (10): IAutonomous, The module does some autonomous actions, mainly used for warnings to users., IStartStop, Any, The module can be started and stopped., InitError, MotionError, MoveError (+2 more)

### Community 149 - "OnSkyDistance"
Cohesion: 0.14
Nodes (7): AltAzOffsets, OnSkyDistance, Angle, RaDecOffsets, test_alt_az_offsets(), test_onskydistance(), test_radecoffsets()

### Community 151 - "`OBSNUM`: per-night observation counter in FITS headers"
Cohesion: 0.06
Nodes (28): 1. Event-driven frame delivery, not polling, 2. Backpressure: latest-frame-wins, not a queue, 3. Wire format (new — nothing in pyobs streams raw binary today), 4. Capability advertisement: `mjpeg`/`raw`, both `str | None`, on by default, 5. Activate/deactivate wiring, Alternatives considered, `BaseVideo`: raw-frame streaming endpoint, alongside the existing MJPEG live view, Constraint: one module, one job (+20 more)

### Community 152 - "3rd party packages (doc)"
Cohesion: 0.11
Nodes (20): 3rd party packages (doc), Astroplan, Astropy, Astroquery, Cython, LMFIT, matplotlib, NumPy (+12 more)

### Community 153 - "CatalogCircularMask"
Cohesion: 0.18
Nodes (9): CatalogCircularMask, Any, NDArray, Table, Init an image processor that masks out everything except for a central circle.…, Remove everything outside the given radius from the image. Args: image: Image…, Filter a source catalog by keeping only entries inside a central circle (or…, asyncio (+1 more)

### Community 154 - "SSHFile"
Cohesion: 0.12
Nodes (12): Any, VFS wrapper for a file that can be accessed over a SFTP connection., Write data into the stream. Args: b: Bytes of data to write., If in write mode, actually send the file to the SSH server., Returns content of given path. Args: path: Path to list. kwargs: Parameters for…, Open/create a file over a SSH connection. Args: name: Name of file. mode: Open…, For read access, download the file into a local buffer. Raises:…, Read number of bytes from stream. Args: n: Number of bytes to read. Read until… (+4 more)

### Community 155 - "create_rst.py"
Cohesion: 0.33
Nodes (18): create_image_processors_rst(), create_modules_rst(), create_rst_overview(), create_utils_rst(), find_classes_in_modules(), find_python_modules(), find_submodules(), Any (+10 more)

### Community 156 - "_PhotUtilAperturePhotometry"
Cohesion: 0.17
Nodes (10): _PhotUtilAperturePhotometry, Table, PhotUtilsPhotometry, Any, Perform photometry using PhotUtils., test_init(), asyncio, test_call_const() (+2 more)

### Community 157 - "XEP_0009_timeout"
Cohesion: 0.17
Nodes (6): BasePlugin, A plugin for SleekXMPP, adding a timeout to RPC calls., XEP_0009_timeout, SleekXMPP: The Sleek XMPP Library Copyright (C) 2011 Nathanael C. Fritz, Dann…, MethodTimeout, ElementBase

### Community 158 - "AddMask"
Cohesion: 0.21
Nodes (13): AddMask, Any, floating, NDArray, Add mask to image. Args: image: Image to add mask to. Returns: Image with mask, Attach a precomputed mask to an image based on instrument and binning. This…, Init an image processor that adds a mask to an image. Args: masks: Dictionary…, asyncio (+5 more)

### Community 159 - "Any"
Cohesion: 0.13
Nodes (7): Any, Store capabilities locally., Return this client's own published capabilities., Fetch capabilities from a remote module., Execute a given method on a remote client., Publish state locally and dispatch to subscribers., Subscribe to state updates from a remote module.

### Community 160 - "SkyCoord"
Cohesion: 0.13
Nodes (9): SkyCoord, Return the next point that satisfies all constraints. Iterates underlying…, Convert the next tuple to a SkyCoord. Expects a tuple (x_deg, y_deg) from the…, Transform the next SkyCoord to the target frame. Returns: A SkyCoord…, Yield a point after rotating the underlying grid a random number of times.…, Yield a point after rotating the underlying grid a random number of times.…, Yield the point from the CSV closest to the next grid point. Returns: A point…, Fetch the next point from the underlying grid. Returns: The next point from the… (+1 more)

### Community 161 - ".retrieve_class_on_deserialization"
Cohesion: 0.24
Nodes (7): model_serializer, Any, model_validator, Self, Get the correct class for this model and run model_validate on that class with…, ValidationInfo, ValidatorFunctionWrapHandler

### Community 162 - ".get_object"
Cohesion: 0.04
Nodes (45): GuidingState, IAutoGuiding, The module can perform auto-guiding., ExposureTimeState, IExposureTime, Any, SECONDS, The camera supports exposure times, to be used together with… (+37 more)

### Community 163 - "_SourceCatalog"
Cohesion: 0.09
Nodes (16): Any, floating, NDArray, PySepStatsCalculator, Any, DataFrame, floating, NDArray (+8 more)

### Community 164 - "Design"
Cohesion: 0.15
Nodes (12): `comm.py` changes, Design, Node naming, Plan: Explicit pubsub subscriptions for event delivery, Post-merge fixes (review, 2026-08-16), Problem, Publishing (`send_event`, `xmppcomm.py:763`), Removed / unchanged (+4 more)

### Community 165 - "ExpTimeEval"
Cohesion: 0.11
Nodes (15): ExpTimeEval, Any, Observer, Return list of binnings., Return list of filters., Estimate exposure time for given filter Args: solalt: Solar altitude. binning:…, Initialize object with the given time. Args: time: Start time for all further…, Estimates exposure time for a given filter and binning at a given time offset… (+7 more)

### Community 166 - "Plan: Stop ImageWatcher per-file processing from blocking the event loop"
Cohesion: 0.13
Nodes (14): 1. Offload the FITS parse — `pyobs/modules/image/imagewatcher.py`, 2. Make `LocalFile` I/O non-blocking — `pyobs/vfs/localfile.py`, 3. Stop `LocalFile.__init__` opening the file synchronously — `pyobs/vfs/localfile.py`, 4. (step 0, diagnostic) Confirm the culprit and measure before/after, Consequences, Considered options, Decision, Existing coverage (regression net, must keep passing) (+6 more)

### Community 167 - "BrightestStarOffsets"
Cohesion: 0.18
Nodes (13): BrightestStarOffsets, Angle, Any, Table, Processes an image and sets x/y pixel offset to reference in offset attribute.…, Compute pixel offsets from the image center to the brightest star and store…, Initializes a new auto guiding system., asyncio (+5 more)

### Community 168 - "._set_optimal_focus"
Cohesion: 0.20
Nodes (5): Sets optimal focus. Args: filter_name: Name of filter to use. Raises:…, Sets optimal focus. Raises: WeatherDataError: If the weather station returned…, Receive FilterChangedEvent and set focus. Args: event: The event itself sender:…, Initialize telescope., Creates a new dummy telescope. Args: position: Initial RA/Dec position in…

### Community 169 - "test_xmpp_state.py"
Cohesion: 0.17
Nodes (15): Integration tests for the XEP-0060 state pub/sub path. Requires a live ejabberd…, proxy.get_state(ICooling) must return the latest value without an RPC round-…, When the remote module disconnects, _client_disconnected must call…, After disconnect and reconnect, the next proxy() call must produce a fresh…, Poll *condition* until truthy or *timeout* seconds elapse., Wait until *comm* sees *peer* in its client list (presence + disco#info done)., A subscriber that connects after the first publish must receive the current…, After subscribing, subsequent set_state calls must arrive at the subscriber. (+7 more)

### Community 170 - "HttpFileCache"
Cohesion: 0.15
Nodes (20): HttpFileCache, Response, Handles OPTIONS access to /{filename} for CORS preflight requests. Args:…, Handles GET access to /{filename} and returns image. Args: request: Request to…, Handles PUSH access to /, stores image and returns filename. Args: request:…, A file cache based on a HTTP server., Whether the server is started., Raises HTTPUnauthorized if a token is configured and the request doesn't carry… (+12 more)

### Community 171 - "._get_client"
Cohesion: 0.11
Nodes (10): PresenceCallback, Get a proxy to the given client. Args: client: Name of client. Returns: Proxy…, Fetch capabilities for a single interface and push them into the given proxy…, Called when a client disconnects. Args: event: Disconnect event. sender: Name…, Returns list of interfaces for given client. Args: client: Name of client.…, Subscribe to state updates for a given module and interface. Delivers the…, Unsubscribe from state updates. Args: module: Name of remote module. interface:…, Subscribe to presence updates for a given module. Delivers the current value… (+2 more)

### Community 172 - "test_grab_sequence.py"
Cohesion: 0.29
Nodes (16): make_camera(), asyncio, Tests for BaseCamera.grab_sequence()/abort_sequence(), the IDataSequence…, grab_sequence() must not block for the whole sequence -- see design doc: a…, test_abort_clears_running_sequence(), test_abort_cuts_delay_short(), test_abort_sequence_cuts_delay_short(), test_abort_sequence_lets_current_grab_finish_but_stops_the_rest() (+8 more)

### Community 173 - "binding.py"
Cohesion: 0.23
Nodes (8): fault2xml(), py2xml(), Any, Element, rpcbase64, rpctime, xml2fault(), xml2py()

### Community 174 - "WeatherAwareMixin"
Cohesion: 0.09
Nodes (13): Event, IWeather, Any, Thread for continuously checking for good weather, Mixin for IMotion devices that should park(), when weather gets bad., Abort exposure if a bad weather event occurs. Args: event: The bad weather…, Change status of weather. Args: event: The good weather event. sender: Who sent…, WeatherAwareMixin (+5 more)

### Community 175 - "SepSourceDetection"
Cohesion: 0.16
Nodes (17): Background, Any, floating, NDArray, Initializes a wrapper for SEP. See its documentation for details. Highly…, Find stars in given image and append catalog. Args: image: Image to find stars…, Remove background from image in data. Args: data: Data to remove background…, Detect astronomical sources using SEP (Source Extractor for Python). This… (+9 more)

### Community 176 - "test_xmppcomm_event_payload.py"
Cohesion: 0.16
Nodes (22): _log_task_exception(), Retrieve and log a background task's exception, if it failed. Results of…, _event_msg(), _EventMsg, _log_event_json(), _make_comm(), asyncio, XmppComm._handle_event must tolerate pubsub notifications without a payload.… (+14 more)

### Community 177 - "_CalibrationCache"
Cohesion: 0.18
Nodes (9): _CalibrationCache, Any, Init a new image calibration pipeline step. Args: archive: Archive to fetch…, mock_image(), fixture, test_add_to_cache(), test_add_to_cache_size(), test_find_cache_entry_emtpy() (+1 more)

### Community 178 - "test_dummyvideo.py"
Cohesion: 0.15
Nodes (16): Creates a new BaseWebcam. On the receiving end, a VFS root with a HTTPFile must…, DummyVideo, Any, A dummy video module for testing — streams simulated noise frames., Creates a new dummy video module. Args: fps: Frames per second to simulate.…, Set the exposure time (frame interval). Args: exposure_time: Exposure time in…, Background task that generates simulated frames., make_dummyvideo() (+8 more)

### Community 179 - "test_aperture_photometry.py"
Cohesion: 0.26
Nodes (9): MockPhotometryCalculator, asyncio, QTable, AperturePhotometry.__init__ is abstract -- concrete calculators…, test_call_invalid_catalog(), test_call_invalid_data(), test_call_invalid_pixelscale(), test_call_valid() (+1 more)

### Community 180 - "Steering: astropy IERS auto-download blocks event loop"
Cohesion: 0.32
Nodes (8): BaseTelescope._celestial / _update_celestial_headers, Steering: astropy IERS auto-download blocks event loop, iers_offline config flag (stopgap fix), Steering: Blocking vendor SDK calls must never run directly on the event loop, _run_blocking() pattern (pyobs_aravis.araviscamera.AravisCamera), _wait_for_frame() tight-poll wrapper pattern, Steering: OnDemandScheduler.evolve() uncached sunset lookup stalls event loop, ObservationArchiveEvolution.evolve() Time.night_obs() bug (fixed via memoization)

### Community 181 - "filters.py"
Cohesion: 0.15
Nodes (20): ConvertGridFrame, ConvertGridToSkyCoord, FromList, GridFilterValue, Convert (x, y) degree tuples to SkyCoord objects. Wraps a tuple-producing grid…, Transform SkyCoord points to a different frame., Select closest point from a list. Only select points if they are closer than a…, Filter points by numeric constraints on x and y. Accepts points as: - (x, y)… (+12 more)

### Community 182 - "FitsHeaderOffsets"
Cohesion: 0.19
Nodes (10): GenericOffset, FitsHeaderOffsets, Any, Compute a 2D offset from FITS header coordinates and store it in image…, Initializes new fits header offsets., Processes an image and sets x/y pixel offset to reference in offset attribute.…, asyncio, test_attribute_validation() (+2 more)

### Community 183 - "._run_configurations"
Cohesion: 0.50
Nodes (3): Any, Target, Loop instrument configurations until the transit window ends.

### Community 184 - "Merit"
Cohesion: 0.15
Nodes (15): AfterTimeMerit, BeforeTimeMerit, ConstantMerit, DataProvider, FollowMerit, IntervalMerit, ObservationArchiveEvolution wraps ObservationArchive with per-run caching (avoid repeated HTTP requests) and lookahead simulation (evolve() records tentative future assignments so IntervalMerit/PerNightMerit see them and avoid double-scheduling within one run), Merit (+7 more)

### Community 185 - "ejabberd shaper throttling bug (xmpp_socket.erl re-arm) & fix"
Cohesion: 0.21
Nodes (12): XMPP/ejabberd diagnostics recipe (doc), benchmark_state_throughput.py, check_ejabberd_notify.py, delete_pubsub_nodes.py, list_pubsub_nodes.py, Comparing shaper configs (rationale), show_module_info.py, scripts/xmpp/install-ejabberd.sh (+4 more)

### Community 186 - "_ResponseImageWriter"
Cohesion: 0.22
Nodes (4): Any, WCS, astrometry.net gives a CD matrix, so we have to delete the PC matrix and the…, _ResponseImageWriter

### Community 187 - "Plan: Make the pydantic config layer reject unknown keys (`extra="forbid"`)"
Cohesion: 0.18
Nodes (10): Decision, Gap: the imaging config models are not covered by this change, Implementation checklist, Latent bug this surfaced (separate from the above), Merged, Plan: Make the pydantic config layer reject unknown keys (`extra="forbid"`), PR review follow-up (github.com/pyobs/pyobs-core/pull/762, thusser), Problem (+2 more)

### Community 188 - "Work Plan"
Cohesion: 0.12
Nodes (16): Dropped items, Phase 0 — Foundations, Phase 1.5 — RPC payload encoding 2.0, Phase 1 — Walking skeleton: prove State end-to-end on one interface, Phase 2.5 — Discovery and Presence, Phase 2 — Audit and design pass (no implementation yet), Phase 3 — Bulk rollout, Phase 4 — Other backends and Presence (+8 more)

### Community 189 - "Plan: `pyobs-gui` TelescopeWidget layout — width floor investigation & design notes"
Cohesion: 0.12
Nodes (16): 1. Make the stacked widget size to the current page, not the widest one, 2. Adopt a width convention for future coordinate-type pages, 3. `QFormLayout::setRowWrapPolicy()` on the individual form pages, 4. Resize-driven reparenting for the four-groupbox row, Capability-driven visibility is handled by toggling pre-built sections on/off, Coordinate-type selection is already a combobox, not tabs, Each coordinate-type page has a fixed, hand-built field set, Filter, Focus, and the offsets rows are structurally duplicated (+8 more)

### Community 190 - "MoveAltAzEvent"
Cohesion: 0.11
Nodes (14): DataTypeAltAz, DataTypeRaDec, MoveAltAzEvent, MoveEvent, MoveRaDecEvent, Any, TypedDict, Event to be sent when moving to RA/Dec. (+6 more)

### Community 191 - "GridNode"
Cohesion: 0.09
Nodes (15): GridNode, Log the last yielded point, if any. Implementations typically delegate to…, Abstract base class for grid nodes. A GridNode implements the Python iterator…, Return iterator self. Returns: The GridNode itself as an iterator., Return the number of points remaining. Returns: Number of points remaining to…, Append the last yielded point back to the underlying sequence. This can be used…, GridPipeline, Any (+7 more)

### Community 192 - "Plan: Make mixin `__init__` composition cooperative, then enforce unrecognized kwargs at `Object.__init__`"
Cohesion: 0.11
Nodes (18): Approach, Critical finding (2026-08-18): PR #776's blast radius isn't scoped by rollout order, Decision, Implementation checklist, Non-goals, Plan: Make mixin `__init__` composition cooperative, then enforce unrecognized kwargs at `Object.__init__`, Problem, Rollout order (proposed, safest first — confirm before starting, not confirmed operational (+10 more)

### Community 193 - "Plan: `pyobs-gui` IAutoGuiding widget"
Cohesion: 0.25
Nodes (7): Known bug in the shipped widget (to fix alongside this change), Plan: `pyobs-gui` IAutoGuiding widget, Problem: pixel offsets aren't physical, and the per-image correction is discarded, Proposed pyobs-core change, Resolved from the original open questions, Shipped (pyobs-core, `develop`), Widget design (pyobs-gui)

### Community 194 - "What's New in pyobs 2.0 (doc)"
Cohesion: 0.15
Nodes (14): What's New in pyobs 2.0 (doc), ACL feature (2.0), Capabilities and versioned discovery, Exception handling redesign, External-package interfaces, ICamera/ISpectrograph no longer imply IExposure, IDataSequence, InvocationError / SevereError retired (+6 more)

### Community 195 - "NewImageEvent"
Cohesion: 0.07
Nodes (29): NewImageEvent, Any, Event to be sent on a new image., Initializes new NewImageEvent. Args: filename: Name of new image file.…, ImageWriter, Any, Writes new images to disk., Creates a new image writer. Args: filename: Pattern for filename to store… (+21 more)

### Community 196 - "test_istructuredconfig.py"
Cohesion: 0.13
Nodes (18): ConfigAppliedState, IStructuredConfig, Any, ConfigValue, The module accepts a whole structured (possibly nested) config object in one…, Apply a full structured config to this module. Args: config: Nested dict…, DummyConfig, DummyStructuredConfigModule (+10 more)

### Community 197 - "test_imagewatcher.py"
Cohesion: 0.33
Nodes (15): make_fits_bytes(), make_read_write_ctx(), make_watcher(), asyncio, On write failure the file is re-queued and remove is NOT called., test_add_file_queues_filename(), test_add_file_respects_pattern(), test_add_file_skips_non_matching_pattern() (+7 more)

### Community 198 - "TaskStartedEvent"
Cohesion: 0.16
Nodes (9): Any, Event to be sent when a task has started., Initializes a new task started event. Args: name: Name of task that just…, TaskStartedEvent, test_task_started_invalid_name(), test_task_started_missing_id(), test_task_started_no_eta(), test_task_started_properties() (+1 more)

### Community 199 - "comm/test_events.py"
Cohesion: 0.18
Nodes (15): asyncio, Tests for Comm.register_event / unregister_event. Covers…, Two independent subscribers for the same event: one tearing down must not un-…, A module that both sends an event (handler-less register_event()) and…, unregister must mirror the exact same derived-events expansion register_event…, Two independent subscribers (e.g. two widget instances for the same event type)…, Once the last handler for an event is unregistered, the event must no longer be…, test_unregister_event_drops_subscribed_role_when_last_handler_removed() (+7 more)

### Community 201 - "test_basecamera.py"
Cohesion: 0.16
Nodes (17): asyncio, parametrize, DummyCamera's _expose() must raise AbortedError, not some guessed builtin, when…, BaseCamera must forward fits_header_timeout to ImageFitsHeaderMixin, not…, Test basic open/close of BaseCamera., #547: BaseCamera must abort on BadWeatherEvent., #547: a BadWeatherEvent must actually trigger abort() -- exposure + any running…, #672: a BadWeatherEvent must not interrupt a dark/bias sequence -- the shutter… (+9 more)

### Community 202 - "show_module_info.py"
Cohesion: 0.25
Nodes (13): h1(), h2(), inspect_module(), _interface_from_feature(), kv(), main(), _module_state_from_show(), ok() (+5 more)

### Community 203 - ".__call__"
Cohesion: 0.38
Nodes (5): ApertureMask, CircularAperture, Any, floating, NDArray

### Community 204 - "SkyflatPriorities"
Cohesion: 0.17
Nodes (8): ArchiveSkyflatPriorities, SkyflatPriorities, Calculate flat priorities from an archive., PolymorphicBaseModel, Base class for sky flat priorities., SkyflatPriorities, Observer, Initializes a new scheduler for taking flat fields Args: functions: Flat field…

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

### Community 210 - "AstrometryDotNet"
Cohesion: 0.05
Nodes (36): Astrometry, Finds astrometric solution to a given image. Args: image: Image to analyse.…, Base class for astrometry processors, AstrometryDotNet, Any, Init new astronomy.net processor. Args: url: URL to service. source_count:…, Deprecated, use on_error instead., Find astrometric solution on given image. Writes WCSERR=1 into FITS header on… (+28 more)

### Community 211 - "._get_method"
Cohesion: 0.14
Nodes (6): Returns a local filename, but only, if path leads to a LocalFile. Args: path:…, Find a file in the given path. Args: path: Path to search in. pattern: Pattern…, Find a file in the given path. Args: path: Path to search in. pattern: Pattern…, Checks, whether a given path or file exists. Args: path: Path to check.…, Removes file with given path. Args: path: Path to delete. Returns: Success of…, Splits the root from the rest of the path. Args: path (str): Path to split.…

### Community 212 - "Plan: Widget plugin mechanism + `pyside6-deploy` packaging for `pyobs-gui`"
Cohesion: 0.14
Nodes (14): Consequences, Considered options, Considered options, Deciding which widget to use, without user-side config, Decision, Decision outcome, Implementation checklist, Non-goals (+6 more)

### Community 213 - "Plan: Split archive prefetch from CPU-bound merit evaluation, to unblock a `ProcessPoolExecutor`"
Cohesion: 0.12
Nodes (16): 1. `ObservationArchiveEvolution` — add prefetch + freeze (`observationarchiveevolution.py`), 2. Call prefetch + freeze — `ondemandscheduler.py`, `schedule()`, 3. Confirm zero cache misses before touching the executor, 4. Only after step 3 is clean: swap the executor (`_executor.py`), Consequences, Considered options, Decision, Existing coverage (+8 more)

### Community 214 - "BaseVideo"
Cohesion: 0.09
Nodes (18): IVideo, BaseVideo, Whether the server is started., Handles access to / and returns HTML page. Args: request: Request to respond…, Handles GET access to /ping for testing connectivity. Args: request: Request to…, Handles access to /video.mjpg and returns the video. Args: request: Request to…, Handles access to /video.raw and returns raw frames. Args: request: Request to…, Handles access to /* and returns a specified image. Args: request: Request to… (+10 more)

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
Cohesion: 0.13
Nodes (11): IRunnable, IStartStop, Any, ObservationArchive, ObservationList, TaskArchive, Compares two lists of tasks and returns two lists, containing those that are…, Trigger a re-schedule. (+3 more)

### Community 220 - "test_autofocus.py"
Cohesion: 0.27
Nodes (18): isinstance_class(), Shared test-double helpers used across multiple test modules., Build a fresh class purely for isinstance() checks against a MagicMock.…, make_autofocus(), make_script(), make_task(), make_telescope(), asyncio (+10 more)

### Community 221 - "time.py"
Cohesion: 0.05
Nodes (50): ProgressEvent, IImageType, ImageTypeState, Any, The module supports different image types (e.g. object, bias, dark, etc),…, Set the image type. Args: image_type: New image type., # TODO: find a better way to convert to uint8, # TODO: add abort (see old robotic/scheduler.py) (+42 more)

### Community 222 - "DummyAltAzTelescope"
Cohesion: 0.22
Nodes (9): DummyAltAzTelescope, Any, A dummy alt/az-offset telescope for testing, offering Alt/Az offsets., Creates a new dummy Alt/Az telescope. Args: offsets: Initial Alt/Az offsets in…, Move an Alt/Az offset., make_dummyaltaztelescope(), asyncio, test_open_registers_offsets_altaz_event_and_publishes_initial_state() (+1 more)

### Community 223 - "Mastermind"
Cohesion: 0.11
Nodes (13): FitsHeaderEntry, IAutonomous, IFitsHeaderBefore, ObservationArchive, Mastermind, Any, TaskRunner, Returns FITS header for the current status of this module. Args: namespaces: If… (+5 more)

### Community 224 - "Kiosk"
Cohesion: 0.07
Nodes (23): ICamera, The module controls a camera., IData, Any, Grabs an image and returns reference. Args: broadcast: Broadcast existence of…, The module can grab and return an image from whatever device., ISpectrograph, The module controls a camera. (+15 more)

### Community 225 - "is_valid_jid"
Cohesion: 0.14
Nodes (9): is_valid_jid(), Whether jid is a valid user@domain or user@domain/resource JID -- exactly what…, asyncio, JID parsing/validation in XmppComm.__init__ and the reusable is_valid_jid()…, The actual production bug this was found from: a JID ending in "/" with nothing…, re.match alone doesn't anchor the end -- confirms the pattern is anchored so…, async def, not plain def -- XmppComm.__init__ calls asyncio.get_event_loop(),…, TestIsValidJid (+1 more)

### Community 226 - ".move_heliographic_stonyhurst"
Cohesion: 0.50
Nodes (3): Any, DEGREES, Moves on given coordinates. Args: lon: Longitude in deg to track. lat: Latitude…

### Community 227 - "FileList"
Cohesion: 0.27
Nodes (5): FileList, Base class for file lists., Any, File list for testing., TestingFileList

### Community 228 - ".move_helioprojective"
Cohesion: 0.50
Nodes (3): Any, DEGREES, Moves on given coordinates. Args: theta_x: The theta_x coordinate. theta_y: The…

### Community 229 - "test_transitimaging.py"
Cohesion: 0.08
Nodes (34): EarthLocation, model_validator, Self, SkyCoord, Merit function for observing transits., Returns the time of the next mid-transit., Returns the time until which observations should run: mid-transit + duration/2…, TransitMerit (+26 more)

### Community 230 - "pyobs 2.0 Wire Protocol, State, and Access Control design doc"
Cohesion: 0.09
Nodes (22): pyobs/utils/config_schema.py: dataclass_to_schema, ICooling interface (reference pattern), slixmpp O(N^2) IQ handler dispatch bug (cross-referenced), IStructuredConfig design doc, IStructuredConfig interface, Rationale: IStructuredConfig coexists with IConfig (per-field vs bulk dataclass config), pyobs 2.0 Wire Protocol, State, and Access Control design doc, Access Control (ACLs): allow/deny, mode: enforce|log (+14 more)

### Community 231 - "Plan: Log the loaded pyobs-* package versions at module startup"
Cohesion: 0.20
Nodes (9): Decision, Design, Helper, Implementation checklist, Log point, Open questions, Out of scope (follow-ups), Plan: Log the loaded pyobs-* package versions at module startup (+1 more)

### Community 232 - "Findings: driver/gui correctness review, all 8 repos (reviewed 2026-08-11)"
Cohesion: 0.13
Nodes (14): Context, Findings: driver/gui correctness review, all 8 repos (reviewed 2026-08-11), Plan: Driver/GUI split for all camera modules + qhyccd correctness review, pyobs-aravis, pyobs-asi, pyobs-fli (driver split only — gui.py built 2026-08-18 via PR #85), pyobs-flipro, pyobs-qhyccd (+6 more)

### Community 233 - "test_baseroof.py"
Cohesion: 0.30
Nodes (8): MockBaseRoof, Any, asyncio, test_get_fits_header_before_closed(), test_get_fits_header_before_open(), test_not_ready(), test_open(), test_ready()

### Community 234 - "CHANGELOG.rst"
Cohesion: 0.22
Nodes (9): ejabberd shaper/xmpp_socket.erl reactivation bug (iag50srv capability-fetch timeouts), XmppComm disco#info role attribute (send/subscribe split), OnDemandScheduler CPU-bound work offloaded to ThreadPoolExecutor, Vfs.write_image()/write_fits() moved to asyncio.to_thread(), run_cpu_bound (scheduler/_executor.py), Vfs.write_fits (pyobs/vfs/vfs.py), Vfs.write_image (pyobs/vfs/vfs.py), specs/plans/event-role-advertising.md (+1 more)

### Community 235 - "Use a self-hosted Keycloak alongside odin, as two parallel auth backends"
Cohesion: 0.10
Nodes (17): Consequences, Considered Options, Context and Problem Statement, Decision Outcome, Use a self-hosted Keycloak alongside odin, as two parallel auth backends, Consequences, Considered Options, Context and Problem Statement (+9 more)

### Community 236 - "Image class"
Cohesion: 0.20
Nodes (10): meta.AltAzOffsets, meta.ExpTime, Image class, Image.meta dict; rationale: keyed by class to avoid collisions between pipeline stages, kept out of FITS since it's runtime-only data, meta.OnSkyDistance, meta.PixelOffsets, meta.RaDecOffsets, meta.SkyOffsets (+2 more)

### Community 237 - "Scheduler"
Cohesion: 0.19
Nodes (8): ConstSkyflatPriorities, SkyflatPriorities, Constant flat priorities., Iterator for scheduler items, Scheduler for taking flat fields, Scheduler, asyncio, test_scheduler()

### Community 238 - "Implementation"
Cohesion: 0.14
Nodes (13): 1. Frame.PROJECT — `pyobs_archive/api/models.py`, 2. Backend connection (project/user knowledge), 3. Access layer — `pyobs_archive/api/permissions.py`, 4. Endpoint filtering — `pyobs_archive/api/views.py`, 5. Frontend — `pyobs_archive/frontend`, 6. Backend dependency — tracked in pyobs/pyobs-robotic-backend#79, Consequences, Implementation (+5 more)

### Community 239 - ".abort"
Cohesion: 0.40
Nodes (3): Any, Abort current actions., Sets the currently active fiber. Must be in fiber_names capability. Args:…

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

### Community 245 - "AperturePhotometry"
Cohesion: 0.12
Nodes (11): AperturePhotometry, Any, Base class for aperture photometry processors -- not meant to be used directly,…, Do aperture photometry on given image. Args: image: Image to do aperture…, Photometry, Do aperture photometry on given image. Args: image: Image to do aperture…, Base class for photometry processors., Any (+3 more)

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

### Community 250 - "WeatherSensors"
Cohesion: 0.16
Nodes (13): IWeather, Any, The module acts as a weather station., Return value for given sensor. Args: station: Name of weather station to get…, WeatherSensorReading, Weather modules. TODO: write doc, Return value for given sensor. Args: station: Name of weather station to get…, Set a simulated sensor's value, for use in tests and simulations. Args: sensor:… (+5 more)

### Community 251 - "Two-phase Object lifecycle; rationale: __init__ must not touch hardware/external services (only store params, create children, register background tasks); open() is where side effects happen, so objects can be constructed cheaply/safely before being started"
Cohesion: 0.22
Nodes (8): Object.add_child_object(), create_object(), get_object(), Two-phase Object lifecycle; rationale: __init__ must not touch hardware/external services (only store params, create children, register background tasks); open() is where side effects happen, so objects can be constructed cheaply/safely before being started, class: key YAML instantiation; rationale: strips class key, passes remaining keys as kwargs, recursing into nested blocks, so any pyobs object graph is fully describable in YAML, Configuration utilities (pyobs.utils.config) API doc, pre_process_yaml(), Coordinate utilities (pyobs.utils.coordinates) API doc

### Community 252 - "Simulation recipe (doc)"
Cohesion: 0.42
Nodes (9): pyobs.modules.telescope (doc), BaseTelescope, DummyAltAzTelescope, DummyRaDecTelescope, DummySolarTelescope, Simulation recipe (doc), DummyCamera, pyobs_gui.GUI (+1 more)

### Community 253 - "ResolvableErrorLogger"
Cohesion: 0.23
Nodes (7): Any, Logger, Logging for resolvable errors. Args: logger: Logger to use. error_level: Log…, Log an error message., ResolvableErrorLogger, create_logger(), test_logger()

### Community 254 - "MockBaseDome"
Cohesion: 0.21
Nodes (8): pyobs.modules.roof (doc), BaseDome, BaseRoof, DummyRoof, MockBaseDome, Any, asyncio, test_get_fits_header_before()

### Community 255 - "Save"
Cohesion: 0.25
Nodes (8): Save an image to the virtual file system and optionally broadcast a…, Initialize processor., Broadcast image. Args: image: Image to broadcast. Returns: Original image., Save, asyncio, test_call(), test_init(), test_open()

### Community 256 - "Decision"
Cohesion: 0.17
Nodes (11): 1. `ImageProcessor` — new methods and kwarg, 2. `PipelineMixin.run_pipeline()` — wrap each step, 3. `AstrometryDotNet` — migrate to handle_error, 4. Deprecation notes, 5. Tests, Consequences, Considered options, Decision (+3 more)

### Community 257 - "CasesRunner"
Cohesion: 0.25
Nodes (6): CasesRunner, FitsHeaderEntry, Time, Script for distinguishing cases., Returns FITS header for the current status of this module. Args: namespaces: If…, Estimate duration of the script for the current case.

### Community 258 - "RuntimeError"
Cohesion: 0.08
Nodes (26): Exposure Time estimators doc, ExpTimeEstimator (exptime processor base), StarExpTimeEstimator (exptime processor), ExpTimeEstimator, Any, Estimate exposure time., Init new exposure time estimator., Any (+18 more)

### Community 259 - "flatfield/test_scheduler.py"
Cohesion: 0.47
Nodes (9): FlatFieldScheduler, Run the flat-field scheduler., make_scheduler_module(), asyncio, setup_flatfield_proxy(), test_abort_sets_event(), test_run_aborts_current_flat_field_when_requested(), test_run_raises_when_already_running() (+1 more)

### Community 260 - "RunningState"
Cohesion: 0.04
Nodes (69): F, ExpTime, IAbortable, Any, Abort current actions., The module has an abortable action., AcquisitionAttempt, AcquisitionResult (+61 more)

### Community 261 - "robotic"
Cohesion: 0.43
Nodes (8): acquisition, fibercamera, fts, guiding, robotic, solar telescope, suncamera, weather

### Community 262 - "Archive (image archive base)"
Cohesion: 0.32
Nodes (8): Archive (image archive base), LocalArchive, PyobsArchive, ArchiveSkyflatPriorities, Archive, Image archives (pyobs.robotic.utils.archive) API doc, LocalArchive, PyobsArchive

### Community 263 - "RemoteError"
Cohesion: 0.20
Nodes (7): ForbiddenError, The call itself didn't reach/return -- a transport failure, not a domain…, Raised when a caller is not permitted to invoke a method under the target…, RemoteError, RemoteTimeoutError, test_forbidden_error(), test_log_only_logs_once()

### Community 264 - "test_dummysolartelescope.py"
Cohesion: 0.49
Nodes (9): make_dummysolartelescope(), asyncio, test_does_not_implement_body_or_orbital_element_tracking(), test_move_heliocentric_polar_slews_tracks_solar_and_publishes_state(), test_move_heliographic_stonyhurst_slews_tracks_solar_and_publishes_state(), test_move_helioprojective_slews_tracks_solar_and_publishes_state(), test_plain_move_altaz_clears_solar_target(), test_plain_move_radec_clears_solar_target_and_resets_to_sidereal() (+1 more)

### Community 265 - "TaskFinishedEvent"
Cohesion: 0.25
Nodes (6): Any, Event to be sent when a task has finished., Initializes a new task finished event. Args: name: Name of task that just…, TaskFinishedEvent, test_task_finished_properties(), test_task_finished_roundtrip()

### Community 266 - "Plan: Rename pyobs-robotic-backend → pyobs-portal"
Cohesion: 0.18
Nodes (10): Open questions — resolved 2026-08-25, Ordering constraint, Plan: Rename pyobs-robotic-backend → pyobs-portal, Step 1 — `pyobs-robotic-backend` repo/package rename, Step 2 — `pyobs-core` storage rename (this repo), Step 3 — `pyobs-auth`, Step 4 — `pyobs-archive`, Step 5 — Deployment YAML (fleet) (+2 more)

### Community 267 - "test_camerasettings.py"
Cohesion: 0.36
Nodes (9): make_camera_proxy(), make_module(), asyncio, Minimal concrete module for exercising CameraSettingsMixin in isolation., Capabilities for a Proxy are fetched in the background (see…, SettingsModule, test_raises_when_capabilities_never_arrive(), test_sets_binning_before_window() (+1 more)

### Community 268 - "Image processors index (docs)"
Cohesion: 0.22
Nodes (8): ImageProcessor on_error kwarg / per-step error handling, Additional Modules index (docs), Image processors index (docs), Astrometry processors doc, AstrometryDotNet (astrometry processor), Calibration processors doc, Run the pipeline on the given image. Each step is run, and an ImageError it…, specs/plans/pipeline-step-error-control.md

### Community 269 - "Discussion: LogEvent double-delivery fix — should we drop add_interest()?"
Cohesion: 0.20
Nodes (9): Can roster and pubsub delivery be split?, Consequence: are all events sent to all clients?, Did we ever need add_interest()?, Discussion: LogEvent double-delivery fix — should we drop add_interest()?, How could real interest-based filtering be achieved?, Monitoring / rollback plan, Proposed fix (from the investigation, point 15), Was shared roster a bad idea? (+1 more)

### Community 270 - "Plan: `pyobs-gui` navbar keyboard shortcuts"
Cohesion: 0.18
Nodes (10): Binding is by page name, not by widget or list-item instance, File changes, Key scheme, Motivation, Plan: `pyobs-gui` navbar keyboard shortcuts, Shortcut wiring, State, Verification (once implemented) (+2 more)

### Community 272 - "._combine_calib_images_async"
Cohesion: 0.20
Nodes (5): Any, Create master bias frame. Args: images: List of raw bias frames. Returns:…, Create master dark frame. Args: images: List of raw dark frames. bias: Bias…, Create master flat frame. Args: images: List of raw flat frames. bias: Bias…, Pipeline for science images. Args: steps: List of pipeline steps to perform.…

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
Nodes (9): Consequences, Design, Out of scope (pyobs-portal), Plan: Stop gating backend-archive refreshes on the `last_*_update` marker, `PortalObservationArchive`, `PortalTaskArchive`, Problem, Rollout (+1 more)

### Community 278 - ".__get_script"
Cohesion: 0.22
Nodes (4): FitsHeaderEntry, Time, Returns FITS header for the current status of this module. Args: namespaces: If…, Estimate duration of the branch that would be run for the current condition.

### Community 279 - "FitsHeaderEntry"
Cohesion: 0.07
Nodes (24): datetime, IN, OUT, Any, Returns FITS header for the current status of this module. Args: namespaces: If…, FitsHeaderEntry, Any, Returns FITS header for the current status of this module. Args: namespaces: If… (+16 more)

### Community 280 - "DummyMode"
Cohesion: 0.17
Nodes (11): IMode, ModeCapabilities, ModeState, Any, The module can change modes in a device., Set the current mode. Args: mode: Name of mode to set. group: Name of the group…, DummyMode, Any (+3 more)

### Community 281 - "ObservationList"
Cohesion: 0.06
Nodes (62): ObservationList, Time, date, Add the list of scheduled tasks to the schedule. Args: tasks: Scheduled tasks., Returns a list of observations for the given task. Args: date: Date of night to…, Fetch schedule from the portal. Returns: Dictionary with tasks. Raises:…, Add observations to the archive. Args: observations: Observations to add., Remove all PENDING observations that end after start_time. Args: start_time:… (+54 more)

### Community 282 - ".move_heliocentric_polar"
Cohesion: 0.50
Nodes (3): Any, DEGREES, Moves on given coordinates. Args: mu: Cosine of the angular distance from Sun…

### Community 283 - "WeatherStatus"
Cohesion: 0.27
Nodes (6): Any, setter, WeatherStatus, test_status_set(), test_status_set_non_good(), test_status_set_none_good()

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

### Community 290 - "_event_role"
Cohesion: 0.17
Nodes (14): _event_schema_to_xml(), _interface_schema_to_xml(), Map a Python type hint to a (wire_type_string, unit_string|None) pair., Build the <{ns}interface> disco#info schema element for one Interface subclass., Build the <{ns}event> disco#info schema element for one Event subclass., _wire_type(), _event_role(), Custom disco#info handler that adds <capability> elements for static module… (+6 more)

### Community 292 - "_PhotometryCalculator"
Cohesion: 0.29
Nodes (3): _PhotometryCalculator, Table, Abstract class for photometry calculators.

### Community 293 - "DummyCamera"
Cohesion: 0.12
Nodes (9): DummyCamera, Any, Header, NDArray, Table, Update cached telescope position from IPointingRaDec state., Returns current solar altitude in degrees, or -18 if no observer., A dummy camera for testing. (+1 more)

### Community 294 - "pyobs/modules/utils/__init__.py"
Cohesion: 0.15
Nodes (7): FluentLogger, Log to fluentd server., Process a new log entry. Args: event: The log event. sender: Name of sender., Utilities TODO: write doc, Matrix, Drain the message queue and send messages one at a time. Sending sequentially…, Process a new log entry. Args: entry: The log event. sender: Name of sender.

### Community 295 - "Investigation: pyobs-gui receives every LogEvent twice (SAAO/monet production)"
Cohesion: 0.25
Nodes (7): Access used, Artifacts from this session, Investigation: pyobs-gui receives every LogEvent twice (SAAO/monet production), Next steps, Problem, What's confirmed, What's ruled out

### Community 296 - "Overview (doc)"
Cohesion: 0.18
Nodes (17): Overview (doc), Access control (ACL), Comm, Events, Interface, Module (base class), Object (base class), Location / astroplan.Observer (+9 more)

### Community 297 - "Plan: Module observer-location capabilities (reconstructed)"
Cohesion: 0.33
Nodes (5): Architecture, File Map, Goal, Plan: Module observer-location capabilities (reconstructed), Tasks

### Community 298 - ".set_gain"
Cohesion: 0.40
Nodes (3): Any, Set the camera gain. Args: gain: New camera gain. Raises: ValueError: If gain…, Set the camera offset. Args: offset: New camera offset. Raises: ValueError: If…

### Community 299 - "Plan: One-click IdP login via `kc_idp_hint` (dual login buttons)"
Cohesion: 0.22
Nodes (8): 1. pyobs-auth — `IDP_HINT` support (new release), 2. Consuming services — dual buttons on the login page, 3. Docs (pyobs-core), 4. Verification, 5. Not in this plan, Mechanism, Plan: One-click IdP login via `kc_idp_hint` (dual login buttons), Problem

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

### Community 308 - "plans/index.md"
Cohesion: 0.06
Nodes (27): Architecture, File Map, Goal, Plan: Decouple `ICamera`/`IExposure` (reconstructed), Tasks, Architecture, File Map, Goal (+19 more)

### Community 309 - "Script"
Cohesion: 0.08
Nodes (24): calc_run_timeout(), Any, Calculates timeout for run()., Module for running a script., Initialize a new script runner. Args: script: Config for script to run., Run script. Raises: ScriptError: If the script failed (e.g. a proxy/network…, Abort current actions., ScriptRunner (+16 more)

### Community 310 - "SMBFile"
Cohesion: 0.22
Nodes (5): Any, Returns content of given path. Args: path: Path to list. kwargs: Parameters for…, VFS wrapper for a file that can be accessed over a SMB connection. Requires…, Open/create a file over a SSH connection. Args: name: Name of file. mode: Open…, SMBFile

### Community 312 - ".set_tracking_rate"
Cohesion: 0.50
Nodes (3): ARCSEC_PER_SEC, Any, Sets an absolute tracking rate on the sky, in arcsec/sec. Args: ra_rate: Rate…

### Community 313 - "Open plans"
Cohesion: 0.33
Nodes (6): Design docs still *proposed*, Fleet open items: open issues and plans across the pyobs fleet, Open issues (4, checked 2026-08-25), Open plans, pyobs-core `specs/plans/`, Sibling repos

### Community 316 - "ModuleLocation dataclass (nested in ModuleCapabilities)"
Cohesion: 0.50
Nodes (4): Location-mismatch warning via _on_module_opened, Rationale: location as one-shot capability, not pubsub state, ModuleLocation dataclass (nested in ModuleCapabilities), Module observer-location capabilities design doc

### Community 317 - "check_pyobs_releases.sh"
Cohesion: 0.70
Nodes (4): check_repo(), main(), print_header(), check_pyobs_releases.sh script

### Community 318 - "check_ejabberd_notify.py"
Cohesion: 0.60
Nodes (4): connect(), main(), make_client(), Minimal ejabberd notification test — no pyobs code involved.

### Community 320 - "Plan: Bound the FITS-header fetch so a dead peer can't stall the frame"
Cohesion: 0.29
Nodes (6): Design, Plan: Bound the FITS-header fetch so a dead peer can't stall the frame, Post-merge fixes (review, 2026-08-16), Problem, Rollout, Testing

### Community 321 - ".__init__"
Cohesion: 0.29
Nodes (4): Creates a comm module., Any, Creates a new dummy comm. Args: name: Name to report for this comm. Defaults to…, Execute a given method on a remote client. Args: client (str): ID of client.…

### Community 322 - "Photometry (pyobs.images.processors.photometry) API doc"
Cohesion: 0.83
Nodes (4): Photometry (pyobs.images.processors.photometry) API doc, Photometry, PhotUtilsPhotometry, SepPhotometry

### Community 323 - "Plan: `pyobs-gui` IAutoFocus widget"
Cohesion: 0.29
Nodes (6): Current state (pyobs-core, `develop`), Gap, Open questions, Plan: `pyobs-gui` IAutoFocus widget, Proposed pyobs-core change, Widget design (pyobs-gui)

### Community 324 - ".set_focus"
Cohesion: 0.40
Nodes (4): Any, MM, Sets new focus. Args: focus: New focus value in mm. Raises:…, Sets focus offset. Args: offset: New focus offset in mm. Raises: ValueError: If…

### Community 325 - "Target"
Cohesion: 0.29
Nodes (4): Target, Set the resolved target if not already set, e.g. when restoring from an…, The resolved target, or the static target if not dynamic., Target for this specific run: the observation's own record if known, otherwise…

### Community 326 - "Any"
Cohesion: 0.25
Nodes (4): Any, Return the last received state for the given interface, or None., Return the capabilities for the given interface, or None., Return state immediately if available, otherwise wait for the first update.

### Community 327 - "._get_next"
Cohesion: 0.33
Nodes (4): SkyCoord, Log a point if logging is enabled. For SkyCoord instances, logs RA/Dec in…, Return the next point in the sequence. Implementors must return either a (x, y)…, Return the next point, storing it as the last yielded value. Returns: A point…

### Community 328 - ".get_config_value"
Cohesion: 0.40
Nodes (4): Any, ConfigValue, Returns current value of config item with given name. Args: name: Name of…, Sets value of config item with given name. Args: name: Name of config item.…

### Community 329 - "FitsNamespaceMixin"
Cohesion: 0.31
Nodes (5): FitsNamespaceMixin, Any, Mixin for IFitsHeaderProvider modules that filters FITS headers by namespace., Filter FITS header keywords by given namespaces. If no namespaces are given,…, Add FITS header keywords from namespace to list of valid keywords Args: name:…

### Community 330 - "Plan: `IDataSequence` — server-side counted data sequences (reconstructed)"
Cohesion: 0.33
Nodes (5): Architecture, File Map, Goal, Plan: `IDataSequence` — server-side counted data sequences (reconstructed), Tasks

### Community 331 - "Plan: Exception handling across the RPC boundary (reconstructed)"
Cohesion: 0.33
Nodes (5): Architecture, File Map (representative, not exhaustive — see commit diffs for the full ~74-file list), Goal, Plan: Exception handling across the RPC boundary (reconstructed), Tasks

### Community 332 - "._create_script"
Cohesion: 0.25
Nodes (4): Build the script selected via the configuration's extra_params["script_name"].…, Whether this config can currently run. Returns: True, if the script can run now, Run script. Raises: InterruptedError: If interrupted, Returns FITS header for the current status of this module. Args: namespaces: If…

### Community 333 - "FlatFieldPointing"
Cohesion: 0.14
Nodes (11): IRunnable, Any, Perform module task Raises: DeviceBusyError: If this task is already running.…, The module has some action that can be started remotely., Modules for performing flatfields. TODO: write doc, FlatFieldPointing, Any, Module for pointing a telescope. (+3 more)

### Community 334 - "http_request_with_retries"
Cohesion: 0.32
Nodes (6): http_request_with_retries(), InvalidResponseError, Any, ClientSession, Raised when the server returns an unexpected HTTP status. Carries the status…, retry

### Community 335 - ".__init__"
Cohesion: 0.33
Nodes (4): Any, Abort current actions., Initialize a new flat field scheduler. Args: flatfield: Flat field module to…, Perform flat-fielding Raises: DeviceBusyError: If a flat-fielding run is…

### Community 337 - "_ProxyContext"
Cohesion: 0.40
Nodes (3): _ProxyContext, ProxyType, Returned by Comm.proxy() / Object.proxy() / Comm.safe_proxy(). Must be used as:…

### Community 338 - "test_module_state_publishing.py"
Cohesion: 0.33
Nodes (6): _discover_concrete_modules(), asyncio, parametrize, Parametrized check: every concrete Module publishes state for each stateful…, All concrete (non-abstract, non-internal) pyobs.modules.Module subclasses.…, test_module_publishes_all_stateful_interfaces()

### Community 339 - "IModule"
Cohesion: 0.33
Nodes (5): IModule, Any, The module is actually a module. Implemented by all modules., Reset error of module, if any., Returns names of all methods the calling module is allowed to invoke on this…

### Community 340 - ".set_offsets_altaz"
Cohesion: 0.50
Nodes (3): Any, DEGREES, Move an Alt/Az offset. Args: dalt: Altitude offset in degrees. daz: Azimuth…

### Community 341 - "._expose"
Cohesion: 0.40
Nodes (4): HDUList, Store spectrum at given destination. Can be overwritten by derived classes to…, Actually do the exposure, should be implemented by derived classes. Args:…, Wrapper for a single exposure. Args: broadcast: Whether or not the new image…

### Community 342 - ".__call__"
Cohesion: 0.33
Nodes (4): EarthLocation, SkyCoord, Take the pixel offsets stored in the meta data of the image and apply them to…, Return RA/Dec of central pixel and of central pixel plus offsets. Args: image:…

### Community 343 - "Plan: raw-frame streaming endpoint in `BaseVideo`"
Cohesion: 0.29
Nodes (6): Context, Explicitly out of scope for this plan, Plan: raw-frame streaming endpoint in `BaseVideo`, Post-merge fixes (review, 2026-08-16), Testing, Todo

### Community 344 - "test_localcomm_state.py"
Cohesion: 0.09
Nodes (28): asyncio, fixture, Tests for LocalComm state, capabilities, and presence., set_presence stores and get_client_state retrieves., Default presence is READY with no error string., subscribe_presence fires callback immediately with the current presence state., subscribe_presence callback is called whenever presence changes., Reset LocalNetwork singleton before each test. (+20 more)

### Community 349 - "ModuleNameFilter"
Cohesion: 0.40
Nodes (3): ModuleNameFilter, LogRecord, Logging filter that stamps the current module name onto every LogRecord.…

### Community 350 - "GuidingStatisticsPixelOffset"
Cohesion: 0.25
Nodes (7): GuidingStatisticsPixelOffset, Calculates RMS of data. Args: data: Data to calculate RMS for. Returns: Tuple…, mock_meta_image(), fixture, test_build_header_to_few_values(), test_end_to_end(), test_get_session_data()

### Community 351 - "README.md"
Cohesion: 0.50
Nodes (3): pyobs CLI (foreground module runner), pyobsd CLI (background daemon manager), pyobsw CLI (Windows equivalent of pyobs)

### Community 352 - "Install-ejabberd (xmpp)"
Cohesion: 0.83
Nodes (3): restore_perms(), install-ejabberd.sh script, yq_is_correct_variant()

### Community 353 - "XmppComm._disconnected"
Cohesion: 0.50
Nodes (3): ADR-0002: XMPP stream-error conflict quits instead of reconnecting, XMPP stream-error condition 'conflict' (RFC 6120 §4.9.3), XmppComm._disconnected()

### Community 355 - "test_comm_interface_resolution.py"
Cohesion: 0.29
Nodes (8): Converts a list of interface names to interface classes. Args: interfaces: list…, LogCaptureFixture, Tests for Comm._interface_names_to_classes -- the base-Comm chokepoint that…, An interface defined entirely outside pyobs.interfaces resolves the same way…, test_resolves_external_interface(), test_resolves_known_and_skips_unknown_in_same_list(), test_resolves_known_core_interfaces(), test_skips_unknown_name()

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

### Community 373 - ".set_cooling"
Cohesion: 0.50
Nodes (3): CELSIUS, Any, Enables/disables cooling and sets setpoint. Args: enabled: Enable or disable…

### Community 462 - "Plan: Advertise event send/subscribe role in disco#info"
Cohesion: 0.33
Nodes (5): Architecture, File Map, Plan: Advertise event send/subscribe role in disco#info, Problem, Tasks

### Community 464 - "DummySkyOffsets"
Cohesion: 0.29
Nodes (6): DummySkyOffsets, Any, SkyCoord, Attach a precomputed sky-coordinate offset to image metadata for testing or…, asyncio, test_call()

### Community 469 - "ModuleGui"
Cohesion: 0.33
Nodes (3): ModuleGui, Any, LogRecord

### Community 470 - "Future"
Cohesion: 0.17
Nodes (9): Run script. Raises: InterruptedError: If interrupted, Future, Any, Sets a new timeout for the method call. Cancels any existing timeout handle and…, Returns async timeout., wait_all awaits all futures and returns their results., wait_all skips None entries., test_wait_all_resolves_all() (+1 more)

## Ambiguous Edges - Review These
- `Configuration utilities (pyobs.utils.config) API doc` → `Coordinate utilities (pyobs.utils.coordinates) API doc`  [AMBIGUOUS]
  docs/source/api/utils/coordinates.rst · relation: conceptually_related_to
- `PyObsError` → `ScriptRunner.run()`  [AMBIGUOUS]
  specs/design/exception_handling.md · relation: conceptually_related_to
- `FocusError` → `FocusModel.set_optimal_focus`  [AMBIGUOUS]
  specs/design/exception_handling.md · relation: conceptually_related_to

## Knowledge Gaps
- **691 isolated node(s):** `pyobs-core`, `Open issues (4, checked 2026-08-25)`, `pyobs-core `specs/plans/``, `Design docs still *proposed*`, `Sibling repos` (+686 more)
  These have ≤1 connection - possible missing edges or undocumented components.
- **95 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **What is the exact relationship between `Configuration utilities (pyobs.utils.config) API doc` and `Coordinate utilities (pyobs.utils.coordinates) API doc`?**
  _Edge tagged AMBIGUOUS (relation: conceptually_related_to) - confidence is low._
- **What is the exact relationship between `PyObsError` and `ScriptRunner.run()`?**
  _Edge tagged AMBIGUOUS (relation: conceptually_related_to) - confidence is low._
- **What is the exact relationship between `FocusError` and `FocusModel.set_optimal_focus`?**
  _Edge tagged AMBIGUOUS (relation: conceptually_related_to) - confidence is low._
- **Why does `Time` connect `Time` to `ExposureStatus`, `flatfield/test_scheduler.py`, `RunningState`, `.__init__`, `Observation`, `SchedulerItem`, `Grid`, `Interface`, `SiderealTarget`, `mixins/test_fitsheader.py`, `Event`, `MotionStatus`, `_DummyTelescopeBase`, `test_flatfielder.py`, `DummyMode`, `tests/test_events.py`, `ObservationList`, `Object`, `test_basetelescope.py`, `test_lco_http.py`, `DummySolarTelescope`, `.get_object`, `test_astroplanscheduler.py`, `DummyCamera`, `pyobs/modules/utils/__init__.py`, `ExpTimeEval`, `Proxy`, `.__init__`, `test_dynamictarget.py`, `filters.py`, `Calibration`, `test_lcoscript.py`, `applyoffsets.py`, `FilenameFormatter`, `test_yaml_archives.py`, `.__call__`, `NewImageEvent`, `Task`, `Offsets`, `TaskStartedEvent`, `.now`, `test_proxy.py`, `test_schedulereader.py`, `IPointingAltAz.py`, `Weather`, `_ProxyContext`, `Portal`, `test_acquisition.py`, `Application`, `Scheduler`, `time.py`, `LocalArchive`, `InfluxHandler`, `test_transitimaging.py`, `test_coordinates.py`, `Scheduler`, `LogEvent`, `dummycamera.py`, `WeatherSensors`, `FocusModel`?**
  _High betweenness centrality (0.190) - this node is a cross-community bridge._
- **Why does `Image` connect `Image` to `RuntimeError`, `ImageProcessor`, `Image processors index (docs)`, `.open_file`, `._combine_calib_images_async`, `mixins/test_fitsheader.py`, `utils/exceptions.py`, `MotionStatus`, `FitsHeaderEntry`, `test_flatfielder.py`, `CatalogCircularMask`, `_PhotUtilAperturePhotometry`, `AddMask`, `.get_object`, `_SourceCatalog`, `_PhotometryCalculator`, `DummyCamera`, `BrightestStarOffsets`, `SkyOffsets`, `.__init__`, `SepSourceDetection`, `_CalibrationCache`, `test_aperture_photometry.py`, `Calibration`, `FitsHeaderOffsets`, `_ResponseImageWriter`, `applyoffsets.py`, `FilenameFormatter`, `test_basevideo.py`, `.__call__`, `Any`, `FlatFielder`, `Offsets`, `.__call__`, `DummySkyOffsets`, `AstrometryDotNet`, `test_acquisition.py`, `PipelineMixin`, `Ring`, `.__call__`, `test_autoguiding.py`, `Smooth`, `time.py`, `ProjectedOffsets`, `GuidingStatisticsPixelOffset`, `LocalArchive`, `FocusSeries`, `RemoveBackground`, `_DaoBackgroundRemover`, `PixelOffsets`, `_SepAperturePhotometry`, `CreateFilename`, `dummycamera.py`, `AperturePhotometry`, `VFSFile`, `SoftBin`, `ImageSourceFilter`, `Save`?**
  _High betweenness centrality (0.117) - this node is a cross-community bridge._
- **Why does `Module` connect `Module` to `ExposureStatus`, `.__init__`, `flatfield/test_scheduler.py`, `RunningState`, `module.py`, `test_dummymode.py`, `MockWeather`, `XmppComm`, `Interface`, `xmpp/rpc.py`, `test_camerasettings.py`, `test_kiosk.py`, `mixins/test_fitsheader.py`, `utils/exceptions.py`, `MotionStatus`, `DummyMode`, `Object`, `.get_object`, `_AbortableModule`, `pyobs/modules/utils/__init__.py`, `PointingSeries`, `test_presence.py`, `HttpFileCache`, `._get_client`, `StandAlone`, `PyobsError`, `WindowCapabilities`, `Script`, `test_basevideo.py`, `GridNode`, `Telegram`, `NewImageEvent`, `IPointingAltAz.py`, `FlatFieldPointing`, `xmppcomm.py`, `Weather`, `Stellarium`, `test_autoguiding.py`, `IModule`, `PipelineMixin`, `test_acquisition.py`, `test_module_state_publishing.py`, `DataCache`, `test_exception_logging.py`, `time.py`, `Kiosk`, `make_proxy_cm`, `LogEvent`, `dummycamera.py`, `WeatherSensors`, `FocusModel`?**
  _High betweenness centrality (0.070) - this node is a cross-community bridge._
- **Are the 122 inferred relationships involving `Time` (e.g. with `PyobsCLI` and `Proxy`) actually correct?**
  _`Time` has 122 INFERRED edges - model-reasoned connections that need verification._