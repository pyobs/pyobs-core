# Graph Report - pyobs-core  (2026-08-15)

## Corpus Check
- 783 files · ~411,766 words
- Verdict: corpus is large enough that graph structure adds value.

## Summary
- 8699 nodes · 20983 edges · 446 communities (397 shown, 49 thin omitted)
- Extraction: 93% EXTRACTED · 7% INFERRED · 0% AMBIGUOUS · INFERRED: 1370 edges (avg confidence: 0.55)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `ce0bc9d1`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- ._create_script
- BaseGuiding
- Time
- RunningState
- Interface
- Module
- Image
- DynamicTarget
- utils/exceptions.py
- ImageProcessor
- Script
- VirtualFileSystem
- Any
- XmppComm
- AstrometryDotNet
- FilenameFormatter
- TimeDelta
- AperturePhotometry
- DummyRoof
- mixins/test_fitsheader.py
- Event
- PipelineMixin
- http_request_with_retries
- test_flatfielder.py
- LocalComm
- tests/test_events.py
- AirmassConstraint
- Object
- ObservationState
- WindowingWidget
- Interfaces (pyobs.interfaces) API doc
- test_control.py
- test_presence.py
- LogScript
- test_lco_http.py
- FitsHeaderEntry
- Future
- test_backend_archives.py
- CoolingState
- IPointingAltAz.py
- test_astroplanscheduler.py
- IBinning
- Any
- Comm
- test_transitimaging.py
- robotic/test_scheduler.py
- StandAlone
- test_acquisition.py
- transitimaging.py
- test_stellarexptime.py
- StarExpTimeEstimator
- xmpp/rpc.py
- WindowCapabilities
- make_proxy_cm
- Calibration
- object.py
- Publisher
- PillowHelper
- Unit
- Proxy
- FitsHeaderOffsets
- test_basevideo.py
- SkyFlatsBasePointing
- test_yaml_archives.py
- FlatFielder
- IExposure
- Telegram
- benchmark_state_throughput.py
- ITelescope
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
- enums.py
- dummycamera.py
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
- test_flatfield.py
- WeatherApi
- ScriptRunner
- _schedulereader.py
- test_coordinates.py
- get_registered_interface
- DataProvider
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
- Any
- Events API doc (pyobs.events)
- Plan: pyobs-pipeline
- Test Localcomm (local)
- _SepAperturePhotometry
- Portal
- Kiosk
- test_dummymode.py
- _ResponseImageWriter
- test_autofocus.py
- Grid
- test_kiosk.py
- pyobs.py
- Robotic recipe (doc)
- is_valid_jid
- test_lcoscript.py
- test_config_schema.py
- DummyRaDecTelescope
- Scheduler
- RollingTimeAverage
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
- SkyCoord
- comm/test_events.py
- WeatherState
- LogEvent
- test_transit_mastermind.py
- ExpTimeEval
- Stellarium
- Overview (doc)
- test_xmpp_state.py
- GuidingStatisticsPixelOffset
- FlatFieldPointing
- .__init__
- test_grab_sequence.py
- binding.py
- NewSpectrumEvent
- .get_config_value
- CLI
- CoolingStatus
- SkyflatPriorities
- fits.py
- Steering: astropy IERS auto-download blocks event loop
- test_schedulereader.py
- test_istructuredconfig.py
- TransitMerit
- Merit
- ejabberd shaper throttling bug (xmpp_socket.erl re-arm) & fix
- WeatherStatus
- Save
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
- .set_exposure_time
- ImageWatcher
- robotic/task.py
- test_xmpp_acl.py
- show_module_info.py
- integration/conftest.py
- ICooling
- robotic
- Scheduler module
- BaseModel (pyobs.utils.serialization)
- Decision
- Smooth
- Scheduler
- HttpFileCache
- Plan: Widget plugin mechanism + `pyside6-deploy` packaging for `pyobs-gui`
- Plan: Split archive prefetch from CPU-bound merit evaluation, to unblock a `ProcessPoolExecutor`
- test_httpfilecache.py
- Image (pyobs.images.processors.image) API doc
- Offsets (pyobs.images.processors.offsets) API doc
- Constraint
- .set_offsets_radec
- .add_fits_headers
- test_aperture_photometry.py
- flatfield/test_scheduler.py
- ImageWriter
- CreateFilename
- .move_heliocentric_polar
- .__call__
- .move_heliographic_stonyhurst
- FileList
- .move_helioprojective
- TempFile
- pyobs 2.0 Wire Protocol, State, and Access Control design doc
- .move_radec
- Findings: driver/gui correctness review, all 8 repos (reviewed 2026-08-11)
- ImageFormat
- CHANGELOG.rst
- Use a self-hosted Keycloak alongside odin, as two parallel auth backends
- Image class
- PyobsArchive
- ._expose
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
- test_imagewriter.py
- test_dummyvideo.py
- test_baseroof.py
- Decision
- MotionStatusChangedEvent
- datetime
- BufferedFile
- TaskData
- robotic
- Archive (image archive base)
- ExposureStatusChangedEvent
- ._get_client
- GuidingStatisticsSkyOffset
- BaseVideo
- CasesRunner
- ._get_next
- Shared authentication across pyobs web projects via Keycloak
- Plan: `pyobs-gui` navbar keyboard shortcuts
- filters.py
- ._set_optimal_focus
- Image.trim
- conftest.py
- Misc (pyobs.images.processors.misc) API doc
- PolymorphicBaseModel
- test_camerasettings.py
- PolymorphicBaseModel
- test_comm_interface_resolution.py
- OffsetsAltAzEvent
- ObservationList
- IFilters
- Target
- GoodWeatherEvent
- Implementation
- Plan: Interactive login/settings dialog for `pyobs-gui`, deferring `Application`'s module construction
- pyobs.modules.utils (doc)
- Plan: Add baseline tests to core-tier repos, then enable grouped Dependabot auto-merge
- Plan: CORS + token auth for `HttpFileCache`
- TaskFailedEvent
- TaskFinishedEvent
- Plan: `pyobs-gui` IAutoGuiding widget
- _event_role
- _DummyTelescopeBase
- Investigation: pyobs-gui receives every LogEvent twice (SAAO/monet production)
- format_filename
- version
- Plan: `pyobs-gui` IAutoFocus widget
- _PhotometryCalculator
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
- IGain
- ConditionalRunner
- Implemented
- Plan: `pyobs-gui` IAcquisition widget
- ModuleLocation dataclass (nested in ModuleCapabilities)
- check_pyobs_releases.sh
- check_ejabberd_notify.py
- comm.py
- MockBaseDome
- IModule
- Photometry (pyobs.images.processors.photometry) API doc
- IWindow
- ._register_exception
- test_module_state_publishing.py
- WeatherSensors
- ._expose
- HelioprojectiveTarget
- .abort
- DataFrame
- floating
- NDArray
- .__init__
- .get_interfaces
- ._get_image_median
- ._subscribe_presence
- .calibrate
- Pipeline
- .grab_data
- .set_optimal_focus
- .track_body
- .add_pointing_measurement
- .run_script
- .sync_target
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
2. `Image` - 441 edges
3. `Task` - 227 edges
4. `Interface` - 186 edges
5. `Module` - 178 edges
6. `ObservationList` - 168 edges
7. `DataProvider` - 168 edges
8. `Event` - 149 edges
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

## Communities (446 total, 49 thin omitted)

### Community 0 - "._create_script"
Cohesion: 0.25
Nodes (4): Build the script selected via the configuration's extra_params["script_name"].…, Whether this config can currently run. Returns: True, if the script can run now, Run script. Raises: InterruptedError: If interrupted, Returns FITS header for the current status of this module. Args: namespaces: If…

### Community 1 - "BaseGuiding"
Cohesion: 0.05
Nodes (33): GuidingState, ExposureTimeState, # TODO: find a better way to convert to uint8, AutoGuiding, Any, An auto-guiding system., Initializes a new auto guiding system. Args: exposure_time: Initial exposure…, Set the exposure time in seconds. Args: exposure_time: Exposure time in… (+25 more)

### Community 2 - "Time"
Cohesion: 0.04
Nodes (58): Constraint, MoonIlluminationConstraint, Moon illumination constraint., MoonSeparationConstraint, Moon separation constraint., TimeConstraint, AfterTimeMerit, Merit function that gives 1 after a given time. (+50 more)

### Community 3 - "RunningState"
Cohesion: 0.03
Nodes (83): F, IAbortable, Any, Abort current actions., The module has an abortable action., AcquisitionAttempt, AcquisitionResult, AcquisitionState (+75 more)

### Community 4 - "Interface"
Cohesion: 0.04
Nodes (76): ABC, IAutoGuiding, The module can perform auto-guiding., ICalibrate, The module can calibrate a device., IConfig, The module allows access to some of its configuration options., IData (+68 more)

### Community 5 - "Module"
Cohesion: 0.04
Nodes (49): AbstractEventLoop, setter, The module that this Comm object is attached to., The module that this Comm object is attached to., ConfigCapabilities, A module in *pyobs* is the smalles executable unit. The base class for all…, Module, MultiModule (+41 more)

### Community 6 - "Image"
Cohesion: 0.04
Nodes (74): MetaClass, Image, CCDData, Create Image from a bytes array containing a FITS file. Args: data: Bytes array…, Create image from FITS file. Args: filename: Name of file to load image from.…, Create image from astropy.CCDData. Args: data: CCDData to create image from.…, Load Image from HDU list. Args: data: HDU list. Returns: Image., A container class for astronomical image data and associated metadata. This… (+66 more)

### Community 7 - "DynamicTarget"
Cohesion: 0.06
Nodes (46): DynamicTarget, SkyCoord, Target, Pick the best available target given current conditions. For static targets…, CsvPicker, Target, A helper class for picking a target from a list., Load CSV and build coordinate array. Returns False if loading failed. (+38 more)

### Community 8 - "utils/exceptions.py"
Cohesion: 0.04
Nodes (60): DataSequenceState, ExposureState, IExposure, The module controls a camera., IFitsHeaderAfter, Any, The module provides some additional header entries for FITS headers after some…, Returns FITS header for the current status of this module. Args: namespaces: If… (+52 more)

### Community 9 - "ImageProcessor"
Cohesion: 0.03
Nodes (64): Some info about :class:`pyobs.images.Image`., ImageProcessor, Any, Init new image processor. Args: on_error: How the pipeline should handle an…, The error handling mode for this step., Processes an image. Args: image: Image to process. Returns: Processed image., Resets state of image processor, AddFitsHeaders (+56 more)

### Community 10 - "Script"
Cohesion: 0.10
Nodes (12): Script for running Mode Selection., Whether this config can currently run. Returns: True if script can run now., Run script. Raises: InterruptedError: If interrupted, Estimate duration of the mode change., # TODO: get a better estimate for mode-change durations, SelectorScript, Checks whether this script could run now. Returns: True, if the script can run…, Returns reason why script cannot run, or None if it can. (+4 more)

### Community 11 - "VirtualFileSystem"
Cohesion: 0.08
Nodes (23): Any, DataFrame, HDUList, Convenience function for writing an Image to a FITS file. Args: filename: Name…, Convenience function for writing an Image to a FITS file. Args: filename: Name…, Convenience function for writing bytes to a file. Args: filename: Name of file…, Convenience function for reading a CSV file into a DataFrame. Args: filename:…, Convenience function for writing a CSV file from a DataFrame. Args: filename:… (+15 more)

### Community 12 - "Any"
Cohesion: 0.11
Nodes (13): ImageHDU, Any, floating, HDUList, Header, NDArray, setter, Table (+5 more)

### Community 13 - "XmppComm"
Cohesion: 0.04
Nodes (39): Any, Store published capabilities for inclusion in disco#info responses., Return this client's own published capabilities., Fetch and deserialize capabilities for a remote module's interface. Retries…, Send XMPP presence stanza reflecting the module lifecycle state. ModuleState…, See Comm.mark_ready(). Remembers readiness on self (survives client recreation…, Subscribe to a pubsub node, retrying until the node exists. Runs as a…, Create a new XMPP Comm module. Either a fill JID needs to be provided, or a set… (+31 more)

### Community 14 - "AstrometryDotNet"
Cohesion: 0.04
Nodes (41): ImageProcessor on_error kwarg / per-step error handling, Astrometry processors doc, AstrometryDotNet (astrometry processor), Astrometry, Finds astrometric solution to a given image. Args: image: Image to analyse.…, Base class for astrometry processors, AstrometryDotNet, Any (+33 more)

### Community 15 - "FilenameFormatter"
Cohesion: 0.14
Nodes (13): Format filename with given formatter., FilenameFormatter, Header, Returns value for given key. Args: hdr: fits.Header to take value from. key:…, Formats a filename given a format template and a FITS header. Args: hdr: FITS…, Format a given placeholder. Args: placeholder: Placeholder to format. hdr: FITS…, Sets a given string to lowercase. Args: hdr: FITS header to take values from.…, Formats time using the given delimiter. Args: hdr: FITS header to take values… (+5 more)

### Community 16 - "TimeDelta"
Cohesion: 0.07
Nodes (55): ConstantMerit, Merit function that returns a constant value., model_validator, Self, Merit function that uses time windows., TimeWindow, TimeWindowMerit, OnDemandScheduler (+47 more)

### Community 17 - "AperturePhotometry"
Cohesion: 0.12
Nodes (11): AperturePhotometry, Any, Base class for aperture photometry processors -- not meant to be used directly,…, Do aperture photometry on given image. Args: image: Image to do aperture…, Photometry, Do aperture photometry on given image. Args: image: Image to do aperture…, Base class for photometry processors., Any (+3 more)

### Community 18 - "DummyRoof"
Cohesion: 0.14
Nodes (17): DummyRoof, Any, Get the percentage the roof is open., Stop the motion. Args: device: Name of device to stop, or None for all. Raises:…, A dummy camera for testing., Creates a new dummy root., Open the roof. Raises: InitError: If the roof could not be initialized (e.g.…, Close the roof. Raises: ParkError: If the roof could not be parked (e.g.… (+9 more)

### Community 19 - "mixins/test_fitsheader.py"
Cohesion: 0.08
Nodes (56): Any, Initialise the mixin. Args: fits_namespaces: List of namespaces for FITS…, Initialise the mixin. Args: fits_namespaces: List of namespaces for FITS…, Request FITS headers from other modules. Returns: Futures from all modules., Any, Creates a new pipeline cammera., Grabs an image and returns reference. Args: broadcast: Broadcast existence of…, FitsModule (+48 more)

### Community 20 - "Event"
Cohesion: 0.05
Nodes (44): Event, Base class for all events., DataType, TypedDict, DataType, TypedDict, DataType, TypedDict (+36 more)

### Community 21 - "PipelineMixin"
Cohesion: 0.06
Nodes (38): Handle an ImageError raised by this step, when on_error == "error". Override…, PipelineMixin, Any, Mixin for a module that needs to implement an image pipeline., Initializes the mixin. Args: steps: Pipeline steps to run on images. archive:…, Resets all previous state of the involved image processors., Pipeline, Any (+30 more)

### Community 22 - "http_request_with_retries"
Cohesion: 0.16
Nodes (27): Clear schedule after given start time. Args: start_time: Start time to clear…, http_request_paginated(), http_request_with_retries(), Any, ClientSession, Fetches all pages of a DRF-style paginated list endpoint and returns the…, retry, make_response() (+19 more)

### Community 23 - "test_flatfielder.py"
Cohesion: 0.08
Nodes (60): make_flatfielder(), make_observer(), make_twilight_observer(), asyncio, parametrize, Regression test for #481: median == bias_level used to raise ZeroDivisionError., Observer stub returning a constant solar altitude for every sun_altaz() call., Observer stub distinguishing the first (now) vs second (+10min) sun_altaz()… (+52 more)

### Community 24 - "LocalComm"
Cohesion: 0.07
Nodes (22): LocalComm, Any, Store capabilities locally., Return this client's own published capabilities., Fetch capabilities from a remote module., Store presence state and dispatch to all subscribers., Return presence state of a connected module., Announce this module to already-connected peers, mirroring XmppComm's presence-… (+14 more)

### Community 25 - "tests/test_events.py"
Cohesion: 0.06
Nodes (41): BadWeatherEvent, Event to be sent on bad weather., Create Event from a dictionary. Args: obj_dict: JSON string for event. Returns:…, FilterChangedEvent, Event to be sent when a filter has been changed., FocusFoundEvent, Event to be sent when a new best focus has been found, e.g. after a focus…, ModeChangedEvent (+33 more)

### Community 26 - "AirmassConstraint"
Cohesion: 0.12
Nodes (33): AirmassConstraint, ndarray, SkyCoord, make_dynamic_task(), make_vfs(), asyncio, integration, Path (+25 more)

### Community 27 - "Object"
Cohesion: 0.03
Nodes (86): PydanticBaseModel, Object, Base class for all objects in *pyobs*., Whether object has been opened., Can be overloaded to quit program., Any, AcquisitionConfig, GuidingConfig (+78 more)

### Community 28 - "ObservationState"
Cohesion: 0.06
Nodes (67): Modules for robotic mode. TODO: write doc, Mastermind, Any, Returns FITS header for the current status of this module. Args: namespaces: If…, Mastermind for a full robotic mode., ObservationState, StrEnum, MemoryObservationArchive (+59 more)

### Community 29 - "WindowingWidget"
Cohesion: 0.05
Nodes (14): BinningWidget, DataDisplayWidget, PrimaryHDU, Slot, Select path for auto-saving., ExposeWidget, Slot, ExposureTimeWidget (+6 more)

### Community 30 - "Interfaces (pyobs.interfaces) API doc"
Cohesion: 0.04
Nodes (53): Interfaces (pyobs.interfaces) API doc, IAbortable, IAcquisition, IAutoFocus, IAutoGuiding, IAutonomous, IBinning, ICalibrate (+45 more)

### Community 31 - "test_control.py"
Cohesion: 0.13
Nodes (42): ParallelRunner, Script for running other scripts in parallel., Script for running a sequence of other scripts., SequentialRunner, AlwaysRunScript, NeverRunScript, Any, asyncio (+34 more)

### Community 32 - "test_presence.py"
Cohesion: 0.05
Nodes (51): ModuleOpenedEvent, Event to be sent when a module has opened., ModuleLocation, _FakeProxyContext, make_xmpp_comm(), asyncio, Tests for Phase 2.5 Presence and Capabilities implementation., Module.open() passes empty string for label when _label is None. (+43 more)

### Community 33 - "LogScript"
Cohesion: 0.18
Nodes (12): DebugTriggerScript, Script for a debug trigger., LogScript, Script for logging something., asyncio, Expression has access to 'now' as a datetime., test_debug_trigger_can_run(), test_debug_trigger_sets_triggered() (+4 more)

### Community 34 - "test_lco_http.py"
Cohesion: 0.09
Nodes (44): Camera, CameraType, ConfigurationType, Enclosure, Instrument, InstrumentType, Mode, ModeType (+36 more)

### Community 35 - "FitsHeaderEntry"
Cohesion: 0.03
Nodes (85): FitsHeaderEntry, IFitsHeaderBefore, Any, The module provides some additional header entries for FITS headers before some…, Returns FITS header for the current status of this module. Args: namespaces: If…, OrbitalElements, Any, Starts tracking a body defined by orbital elements. Args: elements: Orbital… (+77 more)

### Community 36 - "Future"
Cohesion: 0.08
Nodes (36): Wait until all devices are in one of the given motion states. Args: abort:…, Run script. Raises: InterruptedError: If interrupted, acquire_lock(), event_wait(), Future, Any, Lock, Sets a new timeout for the method call. Cancels any existing timeout handle and… (+28 more)

### Community 37 - "test_backend_archives.py"
Cohesion: 0.07
Nodes (47): BackendTaskArchive, Any, ClientSession, Returns the task with the given ID. Returns: Task with given ID., Task archive based on pyobs-robotic-backend., Creates a new task archive. Args: url: URL of pyobs-robotic-backend. token:…, Opens the backend task archive., Closes the backend observation archive. (+39 more)

### Community 38 - "CoolingState"
Cohesion: 0.10
Nodes (29): _dataclass_to_xml(), _event_schema_to_xml(), _interface_schema_to_xml(), _parse_scalar(), Any, Element, Shared XML serializer for pyobs 2.0 (urn:pyobs:rpc:1). Both the state pub/sub…, Deserialize an XML element (produced by ``value_to_xml``) to a Python value.… (+21 more)

### Community 39 - "IPointingAltAz.py"
Cohesion: 0.08
Nodes (34): AltAzState, IPointingAltAz, Any, DEGREES, The module can move to Alt/Az coordinates, usually combined with…, Moves to given coordinates. Args: alt: Alt in deg to move to. az: Az in deg to…, RaDecState, build_skycoord() (+26 more)

### Community 40 - "test_astroplanscheduler.py"
Cohesion: 0.08
Nodes (38): AstroplanScheduler, Any, ObservingBlock, Actually do the scheduling, usually run in a separate process., Scheduler based on astroplan., Initialize a new scheduler. Args: twilight: astronomical or nautical, Abstract base class for tasks scheduler., TaskScheduler (+30 more)

### Community 41 - "IBinning"
Cohesion: 0.11
Nodes (19): BinningState, IBinning, Any, The camera supports binning, to be used together with…, Set the camera binning. Args: x: X binning. y: Y binning. Raises: ValueError:…, FlatField, Any, Enum (+11 more)

### Community 42 - "Any"
Cohesion: 0.11
Nodes (18): Any, DataFrame, floating, IExposureTime, Image, ImageType, NDArray, calc_expose_timeout() (+10 more)

### Community 43 - "Comm"
Cohesion: 0.06
Nodes (18): Comm responsibility: Discovery (clients_with_interface), Comm responsibility: Events (broadcast typed events), Comm, Base class for all Comm modules in pyobs., Returns list of currently connected clients. Returns: (list) list of currently…, Returns list of currently connected clients that implement the given interface.…, Checks, whether the given client supports the given interface. Args: client:…, Background thread for handling the logging. (+10 more)

### Community 44 - "test_transitimaging.py"
Cohesion: 0.19
Nodes (20): make_script(), make_task_data(), make_transit_merit(), asyncio, _run_configurations does not run at all if end_time is already past., repeat index wraps around configuration.repeats., estimate_duration(data=None, time=None) returns ingress+duration+ingress., estimate_duration(time=t) must never return 0 just because the nearest transit… (+12 more)

### Community 45 - "robotic/test_scheduler.py"
Cohesion: 0.13
Nodes (39): Scheduler, DummyTask, make_async_gen(), make_obs(), make_scheduler(), asyncio, Regression test: _on_task_finished is registered for both TaskFinishedEvent and…, _state_for() (+31 more)

### Community 46 - "StandAlone"
Cohesion: 0.09
Nodes (40): pyobs.modules.test (doc), StandAlone, Quickstart (doc), pyobs-core (pip package), Test modules. TODO: write doc, Any, Example module that only logs the given message forever in the given interval., Creates a new StandAlone object. Args: message: Message to log in the given… (+32 more)

### Community 47 - "test_acquisition.py"
Cohesion: 0.06
Nodes (58): Exception, Declare that the given PyobsError types (and their subclasses) fire often…, Records exception for severity tracking (see _register_exception) and fires any…, Whether exception should count as an instance of exc_type for severity-handler…, AbortedError, AcquisitionError, DeviceBusyError, ForbiddenError (+50 more)

### Community 48 - "transitimaging.py"
Cohesion: 0.15
Nodes (9): Any, Target, Imaging script that runs until the end of a transit window. Requires a…, Whether this script can currently run. In addition to ImagingScript checks,…, Returns the TransitMerit from the task, or None., Loop instrument configurations until the transit window ends., Run script. Raises: InterruptedError: If interrupted. ValueError: If no…, Estimate duration of the transit observation. Args: data: Task data containing… (+1 more)

### Community 49 - "test_stellarexptime.py"
Cohesion: 0.11
Nodes (34): ndarray, Find the brightest star near the image centre by fitting a 2D Gaussian. Args:…, Determines exposure time by finding a star near the image centre and adjusting…, Determine the optimal exposure time. Returns: Optimal exposure time in seconds., StellarExposureTimeProvider, attach_proxies(), make_camera_mocks(), make_image() (+26 more)

### Community 50 - "StarExpTimeEstimator"
Cohesion: 0.07
Nodes (27): Exposure Time estimators doc, ExpTimeEstimator (exptime processor base), StarExpTimeEstimator (exptime processor), ExpTime, ExpTimeEstimator, Any, Estimate exposure time., Init new exposure time estimator. (+19 more)

### Community 51 - "xmpp/rpc.py"
Cohesion: 0.10
Nodes (20): fault_to_xml(), params_to_xml(), Any, Element, Exception, Parse <fault> and return (exception_qualified_name, message)., Serialize a parameter list to…, Deserialize <params> to a list of Python values. (+12 more)

### Community 52 - "WindowCapabilities"
Cohesion: 0.14
Nodes (27): ModuleCapabilities, WindowCapabilities, make_module(), Minimal module stub satisfying what XmppComm needs on connect. IModule must be…, get_capabilities_from_disco(), Integration tests for Phase 2.5 Presence and Discovery. Requires a live…, LOCAL state must arrive as away presence., Module.set_state() must automatically push presence — no explicit call. (+19 more)

### Community 53 - "make_proxy_cm"
Cohesion: 0.10
Nodes (31): ParserState, Any, Enum, ShellCommand, ShellCommandResponse, make_proxy_cm(), Wrap value in a MagicMock standing in for the async context manager returned by…, asyncio (+23 more)

### Community 54 - "Calibration"
Cohesion: 0.07
Nodes (28): Calibration processors doc, _CalibrationCache, Calibration, Any, Init a new image calibration pipeline step. Args: archive: Archive to fetch…, Calibrate an image. Args: image: Image to calibrate. Returns: Calibrated image., Calibrate an image using master bias, dark, and flat frames fetched from an…, Find master calibration frame for given parameters using a cache. Args:… (+20 more)

### Community 55 - "object.py"
Cohesion: 0.11
Nodes (18): ObjectClass, create_object(), get_object(), get_safe_object(), Any, ProxyType, :class:`~pyobs.object.Object` is the base for almost all classes in *pyobs*. It…, Calls get_object in a safe way and returns None, if an exceptions thrown. Args:… (+10 more)

### Community 56 - "Publisher"
Cohesion: 0.06
Nodes (28): Any, Measures seeing on reduced images with a catalog., Creates a new seeing estimator. Args: sources: List of sources (e.g. cameras)…, Puts a new images in the DB with the given ID. Args: event: New image event…, Seeing, Any, Initializes a new ApplyAltAzOffsets. Args: min_offset: Min offset in arcsec to…, Any (+20 more)

### Community 57 - "PillowHelper"
Cohesion: 0.10
Nodes (19): Additional Modules index (docs), Image processors index (docs), Annotation processors doc, Circle, Any, Init a new circle processor. Args: x: Center x coordinate. y: Center y…, Draw a circle on an image, optionally interpreting the center in WCS…, Draws a circle on the image. Args: image: Image to draw on. Returns: Output… (+11 more)

### Community 58 - "Unit"
Cohesion: 0.08
Nodes (38): OffsetFrame, StrEnum, Enumerator for canonical physical units used on the wire. Attributes: DEGREES:…, The equivalent astropy.units unit, for code that needs to build a Quantity., Coordinate frame an offset is expressed in, whichever the mount supports.…, Unit, ApplyAltAzOffsets, Apply offsets from a given image to a given telescope. (+30 more)

### Community 59 - "Proxy"
Cohesion: 0.08
Nodes (21): Comm API doc (pyobs.comm), Comm responsibility: Method calls (via Proxy), Proxy, Any, Signature, Execute a method on the remote client. Args: method: Name of method to call.…, Create local methods for the remote client., Function wrapper for remote calls. Args: method: Name of method to wrap.… (+13 more)

### Community 60 - "FitsHeaderOffsets"
Cohesion: 0.19
Nodes (10): GenericOffset, FitsHeaderOffsets, Any, Compute a 2D offset from FITS header coordinates and store it in image…, Initializes new fits header offsets., Processes an image and sets x/y pixel offset to reference in offset attribute.…, asyncio, test_attribute_validation() (+2 more)

### Community 61 - "test_basevideo.py"
Cohesion: 0.14
Nodes (37): NamedTuple, ImageRequest, LastImage, NextImage, make_basevideo(), make_request(), asyncio, test_activate_camera_from_inactive_calls_hook() (+29 more)

### Community 62 - "SkyFlatsBasePointing"
Cohesion: 0.17
Nodes (8): Move telescope. Args: telescope: Telescope to use., Base class for flat pointings., SkyFlatsBasePointing, model_validator, Self, Static flat pointing., Move telescope. Args: telescope: Telescope to use., SkyFlatsStaticPointing

### Community 63 - "test_yaml_archives.py"
Cohesion: 0.11
Nodes (38): YamlObservationArchive, FileSystemTaskArchive, Any, Task archive based on files., Creates a new filesystem-based task archive. Args: extension: Extension of…, Returns time when last time any blocks changed., Returns list of projects. Returns: List of projects., Returns list of schedulable tasks. Returns: List of schedulable tasks (+30 more)

### Community 64 - "FlatFielder"
Cohesion: 0.09
Nodes (20): ICamera, The module controls a camera., FlatFielder, Enum, Calls next step in state machine. Args: telescope: Telescope to use. camera:…, Returns True, if functions are based on filters., Do a quick initial check. Returns: False, if flat-field time for this filter is…, Initialize whole system. (+12 more)

### Community 65 - "IExposure"
Cohesion: 0.06
Nodes (34): Comm._get_client, ADR-0001: Check Interface.state by own declaration, not inheritance, Composite interfaces inheriting stateful bases (ICamera, IDome, ITelescope, ...), Interface.capabilities (ClassVar), Interface.has_own_state(), Interface.state (ClassVar), XmppComm disco#info feature registration, ADR-0006: Proxy.wait_for_state() returns None on timeout (+26 more)

### Community 66 - "Telegram"
Cohesion: 0.13
Nodes (19): CallbackContext, Any, Save storage file. Args: context: Telegram context., Is user authorized? Args: context: Telegram context. user_id: ID of user.…, Store new user in auth database. Args: context: Telegram context. user_id: ID…, Handle /start command. Args: update: Message to process. context: Telegram…, Handle /exec command. Args: update: Message to process. context: Telegram…, Handle click on buttons. Args: update: Message to process. context: Telegram… (+11 more)

### Community 67 - "benchmark_state_throughput.py"
Cohesion: 0.14
Nodes (31): attach_module(), env_config(), main(), make_comm(), maybe_register(), open_publisher(), Any, Benchmark pyobs's XMPP state-push (XEP-0060) and RPC (XEP-0009)… (+23 more)

### Community 68 - "ITelescope"
Cohesion: 0.12
Nodes (11): ITelescope, The module controls a telescope., EarthLocation, Take the pixel offsets stored in the meta data of the image and apply them to…, EarthLocation, SkyCoord, Take the pixel offsets stored in the meta data of the image and apply them to…, Return RA/Dec of central pixel and of central pixel plus offsets. Args: image:… (+3 more)

### Community 69 - "Offsets"
Cohesion: 0.03
Nodes (56): AltAzOffsets, OnSkyDistance, Angle, PixelOffsets, RaDecOffsets, AstrometryOffsets, CorrelationMaxCloseToBorderError, Any (+48 more)

### Community 70 - ".now"
Cohesion: 0.06
Nodes (34): Compute and persist the next per-night observation number. Returns: Compound…, Observer, TaskSuccess, PerNightMerit, Merit functions for defining a max number of observations per night., ObservationArchiveEvolution, date, Populates the task cache and the one real night (anchored to `start`) up front.… (+26 more)

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
Cohesion: 0.12
Nodes (21): model_validator, Self, SkyCoord, Target, SiderealTarget, make_merit(), asyncio, transit_time should be jd0 + n*period for integer n closest to now. (+13 more)

### Community 75 - "PyobsDaemon"
Cohesion: 0.14
Nodes (10): Any, PyobsDaemon, Return the bare module name from a config or PID file path., Strip a leading underscore, which marks a module as disabled. PID and log files…, Return sorted module names from *.yaml files, excluding *.shared.yaml., Read and return the PID from the module's PID file, or None., Return the live PID for a module, or None. Cleans up stale PID files., Return uptime (seconds) and rss_mb for a running PID. No CPU -- that needs a… (+2 more)

### Community 76 - "MockWeather"
Cohesion: 0.13
Nodes (23): pyobs.modules.weather (doc), MockWeather, Weather (module), MockWeather, Any, Returns FITS header for the current status of this module. Args: namespaces: If…, A mock weather station for testing and simulations., Creates a new mock weather station. Args: good: Initial weather-good state.… (+15 more)

### Community 77 - "test_config.py"
Cohesion: 0.10
Nodes (31): include_parts(), pre_process_yaml(), Any, Replaces blocks of the form {include <source.yaml> <key>} in the loaded config…, Include nested contents from another YAML file. Args: include: dictionary based…, Finds anchors ('&') in the included file. Args: filename: name of the file with…, Replaces aliases ('<<: *...') in the main file by the anchor in the included…, reload_anchors() (+23 more)

### Community 78 - "ImageType"
Cohesion: 0.14
Nodes (14): ProgressEvent, Any, Set the image type. Args: image_type: New image type., ImageType, Enumerator specifying the image type. Attributes: BIAS: Bias/zero exposure.…, Find and download master calibration frame. Args: archive: Image archive.…, MasterCalibCreated, A master calibration frame (BIAS/DARK/SKYFLAT) was created and stored/uploaded. (+6 more)

### Community 79 - "test_autoguiding.py"
Cohesion: 0.21
Nodes (31): make_guiding(), make_image(), asyncio, _state_for(), test_auto_guiding_sleeps_when_disabled(), test_auto_guiding_takes_and_processes_image_when_enabled(), test_get_fits_header_after_includes_statistics(), test_get_fits_header_before_reports_closed_loop() (+23 more)

### Community 80 - "Weather"
Cohesion: 0.15
Nodes (24): Builds the current per-sensor readings from the last raw status, for state…, Connection to pyobs-weather., Weather, asyncio, test_active_flag_defaults_true_and_tracks_stop(), test_calc_system_init_eta(), test_get_fits_header_before(), test_get_fits_header_before_invalid() (+16 more)

### Community 81 - "FileSystemObservationArchive"
Cohesion: 0.09
Nodes (15): Any, FileSystemObservationArchive, Any, date, Clear schedule after given start time. Args: start_time: Start time to clear…, Fetch schedule from portal. Returns: Dictionary with tasks. Raises: Timeout: If…, Returns the active scheduled task at the given time. Args: time: Time to return…, Returns the currently running observation. Args: task_archive: Task archive to… (+7 more)

### Community 82 - "SkyOffsets"
Cohesion: 0.13
Nodes (18): BaseCoordinateFrame, Angle, SkyCoord, Returns separatation between both coordinates, either in their own or a given…, Calculates spherical offset from first coordinate to second. Args: frame:…, Args: frame: Coordinate frame to use, or None to use coordinates' own frames.…, SkyOffsets, Any (+10 more)

### Community 83 - "enums.py"
Cohesion: 0.04
Nodes (63): IDome, The module controls a dome, i.e. a :class:`~pyobs.interfaces.IRoof` with a…, FiltersCapabilities, FilterState, FocuserState, IMode, ModeCapabilities, ModeState (+55 more)

### Community 84 - "dummycamera.py"
Cohesion: 0.09
Nodes (27): Integration test for DummyCamera state publishing via XEP-0060., DummyCamera.open() must publish IWindow.Capabilities with the SimCamera full…, DummyCamera.open() must publish IModule.Capabilities with version and label., get_capabilities() must return None for an interface DummyCamera doesn't…, Poll *condition* until truthy or *timeout* seconds elapse., DummyCamera's _cooling_thread publishes CoolingState every second. An observer…, After calling set_cooling via RPC, the published CoolingState must reflect the…, test_dummy_camera_cooling_state_reflects_set_cooling() (+19 more)

### Community 85 - "Ring"
Cohesion: 0.14
Nodes (9): integer, Any, floating, NDArray, Estimate pixel guiding offsets from asymmetry of spilled light around a fiber…, Init an image processor that adds the calculated offset. Args: fibers:…, Processes an image and sets x/y pixel offset to reference in offset attribute.…, Ring (+1 more)

### Community 86 - "DummySolarTelescope"
Cohesion: 0.12
Nodes (22): HeliocentricPolarState, HeliographicStonyhurstState, HelioprojectiveState, DummySolarTelescope, Any, Moves to and continuously tracks a Heliocentric Polar (mu, psi) coordinate., Moves to and continuously tracks a Heliographic Stonyhurst (lon, lat)…, Moves to and continuously tracks a Helioprojective (theta_x, theta_y)… (+14 more)

### Community 87 - "xmppcomm.py"
Cohesion: 0.07
Nodes (23): ClientXMPP, RPC wrapper around XEP-0009 using pyobs 2.0 payload encoding (urn:pyobs:rpc:1)., RPC, Any, Disconnect only, instead of slixmpp's default reconnect-in-place. xep_0199's…, Called when the server sends a <stream:error/>, e.g. when this connection gets…, Whether this client was (or is being) kicked because another session connected…, Human-readable reason text sent alongside the conflict stream error, if any. (+15 more)

### Community 88 - "test_exception_logging.py"
Cohesion: 0.21
Nodes (22): Callback for flat-field class to call with statistics., FocusError, _AbortableModule, Any, asyncio, Exception, Minimal test module whose abort() raises whatever exception it's given. Starts…, test_call_id_is_attached_to_the_exception_and_included_in_the_log_line() (+14 more)

### Community 89 - "DummyCamera"
Cohesion: 0.10
Nodes (22): DummyCamera, Header, NDArray, Table, Update cached telescope position from IPointingRaDec state., Returns current solar altitude in degrees, or -18 if no observer., A dummy camera for testing., asyncio (+14 more)

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
Cohesion: 0.10
Nodes (18): ArchiveFile, Wraps a file in an archive. To be used in combination with pyobs-archive., Creates a new archive file. Args: name: Name of file. mode: Open mode (r/w).…, If in write mode, actually send the file to the archive., HttpFile, Any, Read number of bytes from stream. Args: n: Number of bytes to read. Read until…, Write data into the stream. Args: s: Bytes of data to write. (+10 more)

### Community 96 - ".__init__"
Cohesion: 0.40
Nodes (3): Any, Any, Initialize a new scheduler. Args: twilight: astronomical or nautical

### Community 97 - "application.py"
Cohesion: 0.09
Nodes (18): _disable_iers_auto_download(), GuiApplication, InfluxLogConfig, Any, TypedDict, Derived Application class that uses a Qt GUI. Allows for graceful shutdown in…, Create a new GUI application., Initializes a pyobs application. Exactly one of `config`/`module_factory` must… (+10 more)

### Community 98 - "FocusSeries"
Cohesion: 0.05
Nodes (40): AutoFocusPoint, fit_hyperbola(), Fit a hyperbola Args: x_arr: X data y_arr: Y data y_err: Y errors Returns:…, FocusSeries, Analyse given image. Args: image: Image to analyse focus_value: Value to fit…, Returns a list of data points., Fit focus from analysed images Returns: Tuple of new focus and its error, Base class for focus series helper classes. (+32 more)

### Community 99 - "_SourceCatalog"
Cohesion: 0.06
Nodes (33): Background, Any, floating, NDArray, Initializes a wrapper for SEP. See its documentation for details. Highly…, Find stars in given image and append catalog. Args: image: Image to find stars…, Remove background from image in data. Args: data: Data to remove background…, Detect astronomical sources using SEP (Source Extractor for Python). This… (+25 more)

### Community 100 - "test_flatfield.py"
Cohesion: 0.21
Nodes (25): make_flatfield(), asyncio, Find the state object set_state() was called with for the given interface., _ready_telescope(), _state_for(), test_abort_sets_event(), test_abort_weather_calls_abort(), test_callback_noop_without_publisher() (+17 more)

### Community 101 - "WeatherApi"
Cohesion: 0.19
Nodes (10): Any, ClientSession, WeatherApi, MockResponse, Any, asyncio, test_get_current_status(), test_get_sensor_value() (+2 more)

### Community 102 - "ScriptRunner"
Cohesion: 0.14
Nodes (15): calc_run_timeout(), Any, Calculates timeout for run()., Module for running a script., Initialize a new script runner. Args: script: Config for script to run., Run script. Raises: ScriptError: If the script failed (e.g. a proxy/network…, Abort current actions., ScriptRunner (+7 more)

### Community 103 - "_schedulereader.py"
Cohesion: 0.08
Nodes (20): Any, Creates a new LCO scheduler. Args: url: URL to portal site: Site filter for…, LcoAutoFocusScript, Auto focus script for LCO configs., # TODO: unfortunately this never happens, since the LCO portal forces…, LcoDefaultScript, Returns FITS header for the current status of this module. Args: namespaces: If…, Default script for LCO configs. (+12 more)

### Community 104 - "test_coordinates.py"
Cohesion: 0.15
Nodes (25): offset_altaz_to_radec(), offset_radec_to_altaz(), EarthLocation, SkyCoord, make_altaz(), make_radec(), SkyCoord, Zero offset returns (0, 0). (+17 more)

### Community 105 - "get_registered_interface"
Cohesion: 0.07
Nodes (28): BasePlugin, A plugin for SleekXMPP, adding a timeout to RPC calls., XEP_0009_timeout, SleekXMPP: The Sleek XMPP Library Copyright (C) 2011 Nathanael C. Fritz, Dann…, MethodTimeout, ElementBase, get_registered_interface(), Look up a registered interface class by name, or None if unknown. (+20 more)

### Community 106 - "DataProvider"
Cohesion: 0.05
Nodes (57): AtNightConstraint, ndarray, SkyCoord, Returns a boolean mask of candidates passing this constraint. Default…, ndarray, SkyCoord, Solar elevation constraint., SolarElevationConstraint (+49 more)

### Community 107 - "LocalArchive"
Cohesion: 0.33
Nodes (25): LocalArchive, Connector class to a local image archive., make_frame_headers(), asyncio, Path, test_download_frames_loads_real_files(), test_download_frames_skips_frames_without_filename(), test_download_headers_returns_header_dicts() (+17 more)

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

### Community 112 - "test_background_task.py"
Cohesion: 0.17
Nodes (19): BackgroundTask, Any, make_task(), asyncio, Too many fast failures calls parent.quit() when restart=True., Too many fast failures with restart=False just stops without calling quit., Failures spread over time don't trigger the rapid-failure quit., test_cancelled_error_exits_cleanly() (+11 more)

### Community 113 - "Test Commlogging (comm)"
Cohesion: 0.12
Nodes (20): Send an event to all connected modules. Args: event: Event to send.…, CommLoggingHandler, Any, A logging handler that sends all messages through a Comm module., Create a new logging handler. Args: comm: Comm module to use., Send a new log entry to the comm module. Args: rec: Log record to send., comm(), handler() (+12 more)

### Community 114 - ".__init__"
Cohesion: 0.11
Nodes (10): Any, JSON representation of event., String representation of event., Generic from_dict method for derived classes that don't need their own., Any, Any, Any, Any (+2 more)

### Community 115 - "test_dummyradectelescope.py"
Cohesion: 0.24
Nodes (21): TrackingRateCapabilities, make_dummyradectelescope(), asyncio, test_move_altaz_clears_tracked_body(), test_move_altaz_resets_tracking_mode_to_off(), test_move_radec_clears_tracked_body(), test_move_radec_resets_tracking_mode_to_sidereal(), test_move_task_applies_tracking_rate_to_position() (+13 more)

### Community 116 - "ImagingScript"
Cohesion: 0.15
Nodes (10): ImagingScript, InstrumentConfig, Any, Target, Run script. Raises: InterruptedError: If interrupted, Returns FITS header for the current status of this module. Args: namespaces: If…, Estimate the duration of this script in seconds., Return the exposure time, computing it dynamically if needed. (+2 more)

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
Cohesion: 0.24
Nodes (20): DarkBiasScript, Script for running darks or biases., isinstance_class(), Shared test-double helpers used across multiple test modules., Build a fresh class purely for isinstance() checks against a MagicMock.…, make_camera(), make_script(), asyncio (+12 more)

### Community 128 - "Any"
Cohesion: 0.09
Nodes (15): Any, ProxyType, Returns object directly if it is of given type. Otherwise get proxy of client…, Backend hook, called when a proxy exists but doesn't implement obj_type.…, Calls proxy() in a safe way and returns None instead of raising an exception., Returns a context manager; use as `async with self.proxy(...) as x:`., Same as proxy(), but yields None inside the block instead of raising., True if a proxy of the given type can currently be resolved. Doesn't keep a… (+7 more)

### Community 129 - "Events API doc (pyobs.events)"
Cohesion: 0.11
Nodes (17): Events API doc (pyobs.events), DataTypeAltAz, DataTypeRaDec, MoveAltAzEvent, MoveEvent, MoveRaDecEvent, Any, TypedDict (+9 more)

### Community 130 - "Plan: pyobs-pipeline"
Cohesion: 0.08
Nodes (24): Celery task, Consequences, Django models, Implementation checklist, Log viewing, Open questions, Pages, Pipeline builder (+16 more)

### Community 131 - "Test Localcomm (local)"
Cohesion: 0.18
Nodes (22): make_comm(), asyncio, fixture, Sender also receives its own events., Reset LocalNetwork singleton between tests., #677: a late-joining module must announce itself via ModuleOpenedEvent once…, get_interfaces returns [] when the remote client has no module., reset_network() (+14 more)

### Community 132 - "_SepAperturePhotometry"
Cohesion: 0.15
Nodes (11): Any, floating, NDArray, Table, since SEP sums up whole pixels, we need to do the same on an image of ones for…, _SepAperturePhotometry, asyncio, fixture (+3 more)

### Community 133 - "Portal"
Cohesion: 0.07
Nodes (32): InstrumentLocation, ConfigDB, Portal, Any, Do a GET request on the portal. Args: url: URL to request. Returns: Response…, Clear schedule after given start time. Args: start: Start time to clear…, Submit observations. Args: observations: List of observations to submit., Send report to LCO portal Args: status_id: id of config status status: Status… (+24 more)

### Community 134 - "Kiosk"
Cohesion: 0.07
Nodes (14): Utilities TODO: write doc, Kiosk, Any, Response, Thread for taking images., A kiosk mode for a pyobs camera that takes images and published them via HTTP., Initializes file cache. Args: camera: Camera to use for kiosk mode. port: Port…, Handles access to /* and returns a specified image. Args: request: Request to… (+6 more)

### Community 135 - "test_dummymode.py"
Cohesion: 0.32
Nodes (13): _event_of_type(), make_dummymode(), asyncio, Find the most recent state object set_state() was called with for the given…, Find the send_event() call with an event of the given type., _state_for(), test_init_default_modes(), test_init_park_stop_motion_are_noops() (+5 more)

### Community 136 - "_ResponseImageWriter"
Cohesion: 0.24
Nodes (4): Any, WCS, astrometry.net gives a CD matrix, so we have to delete the PC matrix and the…, _ResponseImageWriter

### Community 137 - "test_autofocus.py"
Cohesion: 0.31
Nodes (17): AutoFocusScript, Script for running autofocus series., make_autofocus(), make_script(), make_task(), make_telescope(), asyncio, Telescope is stopped even if auto_focus raises. (+9 more)

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
Cohesion: 0.14
Nodes (9): is_valid_jid(), Whether jid is a valid user@domain or user@domain/resource JID -- exactly what…, asyncio, JID parsing/validation in XmppComm.__init__ and the reusable is_valid_jid()…, The actual production bug this was found from: a JID ending in "/" with nothing…, re.match alone doesn't anchor the end -- confirms the pattern is anchored so…, async def, not plain def -- XmppComm.__init__ calls asyncio.get_event_loop(),…, TestIsValidJid (+1 more)

### Community 143 - "test_lcoscript.py"
Cohesion: 0.17
Nodes (18): FakeScript, make_lco_script(), make_request(), Any, asyncio, Minimal script used to verify LcoScript's dispatch., can_run() resolves and delegates to the script named in…, run() delegates to the named script and copies its exptime_done back. (+10 more)

### Community 144 - "test_config_schema.py"
Cohesion: 0.20
Nodes (22): ConfigFieldSchema, ConfigSchema, dataclass_to_schema(), _field_schema(), Any, _pydantic_field_schema(), pydantic_to_schema(), Recursively derive a ConfigSchema from a dataclass type. Handles: plain scalars… (+14 more)

### Community 145 - "DummyRaDecTelescope"
Cohesion: 0.08
Nodes (24): AltAzOffsetState, IOffsetsAltAz, Any, DEGREES, The module supports Alt/Az offsets, usually combined with…, Move an Alt/Az offset. Args: dalt: Altitude offset in degrees. daz: Azimuth…, DummyAltAzTelescope, Any (+16 more)

### Community 146 - "Scheduler"
Cohesion: 0.15
Nodes (7): Any, Compares two lists of tasks and returns two lists, containing those that are…, Trigger a re-schedule., Re-schedule when task has started and we can predict its end. Args: event: The…, Reset current task, when it has finished or failed. Args: event: The task…, Re-schedule on incoming good weather event. Args: event: The good weather…, Scheduler

### Community 147 - "RollingTimeAverage"
Cohesion: 0.10
Nodes (24): Any, Runs an async callable to completion on a dedicated worker thread, off the…, run_cpu_bound(), RollingTimeAverage, _T, asyncio, test_run_cpu_bound_propagates_exception(), test_run_cpu_bound_returns_value() (+16 more)

### Community 148 - ".__init__"
Cohesion: 0.13
Nodes (10): PydanticModel, PrivateAttrMixin, EarthLocation, Observer, Location of the observer, derived from :attr:`observer` (there is no separately…, Validate a pydantic model with additional fields., .. note:: Objects must always be opened and closed using…, Any (+2 more)

### Community 149 - "Observation"
Cohesion: 0.05
Nodes (31): Response, Observation, Any, Fetch a task from the task archive., Updates observation. Args: observation: Observation to update., AcquisitionConfig, Configuration, GuidingConfig (+23 more)

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
Cohesion: 0.16
Nodes (8): IN, OUT, GuidingStatistics, Any, Calculates statistics for guiding., Inits a stat measurement session for a client. Args: client: name/id of the…, Add statistics to given header. Args: client: id/name of the client header:…, Adds data to all client measurement sessions. Args: input_data: Image witch…

### Community 157 - "SoftBin"
Cohesion: 0.15
Nodes (11): Any, floating, NDArray, Bin a 2D image by averaging non-overlapping blocks, updating relevant FITS…, Init a new software binning pipeline step. Args: binning: Binning to apply to…, Bin an image. Args: image: Image to bin. Returns: Binned image., SoftBin, asyncio (+3 more)

### Community 158 - "AddMask"
Cohesion: 0.21
Nodes (13): AddMask, Any, floating, NDArray, Add mask to image. Args: image: Image to add mask to. Returns: Image with mask, Attach a precomputed mask to an image based on instrument and binning. This…, Init an image processor that adds a mask to an image. Args: masks: Dictionary…, asyncio (+5 more)

### Community 159 - "Archive"
Cohesion: 0.15
Nodes (10): Archive, FrameInfo, Any, Base class for frame infos., Base class for image archives., TypedDict, PyobsArchiveFrameInfoDict, _FlakyCalibArchive (+2 more)

### Community 160 - "SkyCoord"
Cohesion: 0.13
Nodes (9): SkyCoord, Return the next point that satisfies all constraints. Iterates underlying…, Convert the next tuple to a SkyCoord. Expects a tuple (x_deg, y_deg) from the…, Transform the next SkyCoord to the target frame. Returns: A SkyCoord…, Yield a point after rotating the underlying grid a random number of times.…, Yield a point after rotating the underlying grid a random number of times.…, Yield the point from the CSV closest to the next grid point. Returns: A point…, Fetch the next point from the underlying grid. Returns: The next point from the… (+1 more)

### Community 161 - "comm/test_events.py"
Cohesion: 0.18
Nodes (15): asyncio, Tests for Comm.register_event / unregister_event. Covers…, Two independent subscribers for the same event: one tearing down must not un-…, A module that both sends an event (handler-less register_event()) and…, unregister must mirror the exact same derived-events expansion register_event…, Two independent subscribers (e.g. two widget instances for the same event type)…, Once the last handler for an event is unregistered, the event must no longer be…, test_unregister_event_drops_subscribed_role_when_last_handler_removed() (+7 more)

### Community 162 - "WeatherState"
Cohesion: 0.17
Nodes (16): pyobs.modules.roof (doc), BaseDome, BaseRoof, DummyRoof, WeatherState, _FakeProxyContext, asyncio, Tests for WeatherAwareMixin's use of Proxy.wait_for_state's max_age -- see… (+8 more)

### Community 163 - "LogEvent"
Cohesion: 0.18
Nodes (5): LogEvent, Any, Event for log entries., test_log_event_properties(), test_log_event_roundtrip()

### Community 164 - "test_transit_mastermind.py"
Cohesion: 0.22
Nodes (19): Configuration, make_transit_merit(), make_transit_observation(), make_transit_task(), asyncio, integration, Mastermind picks up a transit observation and runs it to completion., Mastermind marks transit observation FAILED when runner raises. (+11 more)

### Community 165 - "ExpTimeEval"
Cohesion: 0.12
Nodes (14): ExpTimeEval, Any, Observer, Return list of binnings., Estimate exposure time for given filter Args: solalt: Solar altitude. binning:…, Initialize object with the given time. Args: time: Start time for all further…, Estimates exposure time for a given filter and binning at a given time offset…, Exposure time evaluator for skyflats. (+6 more)

### Community 166 - "Stellarium"
Cohesion: 0.16
Nodes (6): BaseTransport, Exception, Send coordinates to clients., A stellarium telescope., Stellarium, StellariumProtocol

### Community 167 - "Overview (doc)"
Cohesion: 0.18
Nodes (17): Overview (doc), Access control (ACL), Comm, Events, Interface, Module (base class), Object (base class), Location / astroplan.Observer (+9 more)

### Community 168 - "test_xmpp_state.py"
Cohesion: 0.17
Nodes (15): Integration tests for the XEP-0060 state pub/sub path. Requires a live ejabberd…, proxy.get_state(ICooling) must return the latest value without an RPC round-…, When the remote module disconnects, _client_disconnected must call…, After disconnect and reconnect, the next proxy() call must produce a fresh…, Poll *condition* until truthy or *timeout* seconds elapse., Wait until *comm* sees *peer* in its client list (presence + disco#info done)., A subscriber that connects after the first publish must receive the current…, After subscribing, subsequent set_state calls must arrive at the subscriber. (+7 more)

### Community 169 - "GuidingStatisticsPixelOffset"
Cohesion: 0.33
Nodes (5): GuidingStatisticsPixelOffset, Calculates RMS of data. Args: data: Data to calculate RMS for. Returns: Tuple…, test_build_header_to_few_values(), test_end_to_end(), test_get_session_data()

### Community 170 - "FlatFieldPointing"
Cohesion: 0.21
Nodes (10): FlatFieldPointing, Any, Module for pointing a telescope., Initialize a new flat field pointing. Args: telescope: Telescope to point…, Move telescope to pointing., Abort current actions., make_pointing_module(), asyncio (+2 more)

### Community 171 - ".__init__"
Cohesion: 0.09
Nodes (13): Args: label: Label for module. If None, name is used. own_comm: If True, module…, Parse the optional "acl" config block into _acl_allow/_acl_deny/_acl_mode.…, Expand any interface names (e.g. "ICamera") in an "allow" entry list into that…, List interfaces and methods of this module., FluentLogger, Any, Log to fluentd server., Initialize a new logger. Args: hostname: Hostname of server. port: Port of… (+5 more)

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

### Community 177 - "CoolingStatus"
Cohesion: 0.14
Nodes (9): Binning, BinningCapabilities, GainState, WindowState, Creates a new BaseCamera. Args: fits_headers: Additional FITS headers. centre:…, CoolingStatus, Any, NamedTuple (+1 more)

### Community 178 - "SkyflatPriorities"
Cohesion: 0.27
Nodes (6): ArchiveSkyflatPriorities, Calculate flat priorities from an archive., Base class for sky flat priorities., SkyflatPriorities, ConstSkyflatPriorities, Constant flat priorities.

### Community 179 - "fits.py"
Cohesion: 0.22
Nodes (12): fitssec(), parse_section_bounds(), Any, NDArray, Parse a FITS section keyword (e.g. TRIMSEC) into 0-based, half-open slice…, Trim an image to TRIMSEC or BIASSEC. Args: hdu: HDU to take data from. keyword:…, DummyHdu, test_fitssec_no_keyword() (+4 more)

### Community 180 - "Steering: astropy IERS auto-download blocks event loop"
Cohesion: 0.32
Nodes (8): BaseTelescope._celestial / _update_celestial_headers, Steering: astropy IERS auto-download blocks event loop, iers_offline config flag (stopgap fix), Steering: Blocking vendor SDK calls must never run directly on the event loop, _run_blocking() pattern (pyobs_aravis.araviscamera.AravisCamera), _wait_for_frame() tight-poll wrapper pattern, Steering: OnDemandScheduler.evolve() uncached sunset lookup stalls event loop, ObservationArchiveEvolution.evolve() Time.night_obs() bug (fixed via memoization)

### Community 181 - "test_schedulereader.py"
Cohesion: 0.15
Nodes (21): LcoScheduleReader, Update list of requests. Args: force: Force update., Fetch schedule from portal. Returns: Dictionary with tasks. Raises: Timeout: If…, Fetch schedule from portal. Args: start_before: Task must start before this…, Returns the active scheduled task at the given time. Args: time: Time to return…, Scheduler for using the LCO portal, make_observation(), make_reader() (+13 more)

### Community 182 - "test_istructuredconfig.py"
Cohesion: 0.18
Nodes (13): ConfigAppliedState, DummyConfig, DummyStructuredConfigModule, Any, asyncio, fixture, Tests for IStructuredConfig capabilities/state round-tripping through LocalComm., Reset LocalNetwork singleton before each test. (+5 more)

### Community 183 - "TransitMerit"
Cohesion: 0.19
Nodes (8): EarthLocation, model_validator, Self, SkyCoord, Merit function for observing transits., Returns the time of the next mid-transit., Returns the time until which observations should run: mid-transit + duration/2…, TransitMerit

### Community 184 - "Merit"
Cohesion: 0.15
Nodes (15): AfterTimeMerit, BeforeTimeMerit, ConstantMerit, DataProvider, FollowMerit, IntervalMerit, ObservationArchiveEvolution wraps ObservationArchive with per-run caching (avoid repeated HTTP requests) and lookahead simulation (evolve() records tentative future assignments so IntervalMerit/PerNightMerit see them and avoid double-scheduling within one run), Merit (+7 more)

### Community 185 - "ejabberd shaper throttling bug (xmpp_socket.erl re-arm) & fix"
Cohesion: 0.21
Nodes (12): XMPP/ejabberd diagnostics recipe (doc), benchmark_state_throughput.py, check_ejabberd_notify.py, delete_pubsub_nodes.py, list_pubsub_nodes.py, Comparing shaper configs (rationale), show_module_info.py, scripts/xmpp/install-ejabberd.sh (+4 more)

### Community 186 - "WeatherStatus"
Cohesion: 0.14
Nodes (9): Any, Returns FITS header for the current status of this module. Args: namespaces: If…, Initialize a new pyobs-weather connector. Args: url: URL to weather station…, Any, setter, WeatherStatus, test_status_set(), test_status_set_non_good() (+1 more)

### Community 187 - "Save"
Cohesion: 0.19
Nodes (10): Any, Save an image to the virtual file system and optionally broadcast a…, Init an image processor that broadcasts an image Args: filename: Filename to…, Initialize processor., Broadcast image. Args: image: Image to broadcast. Returns: Original image., Save, asyncio, test_call() (+2 more)

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

### Community 198 - ".set_exposure_time"
Cohesion: 0.50
Nodes (3): Any, SECONDS, Set the exposure time in seconds. Args: exposure_time: Exposure time in…

### Community 199 - "ImageWatcher"
Cohesion: 0.15
Nodes (9): CurrentFile, ImageWatcher, Any, Add a file to the file queue. Args: filename (str): Local filename of new file., Can be overwritten by derived classes to do extra processing on files. All…, Can be overwritten by derived classes to do clean up after successful copying.…, Watch for new files and write them to all given destinations. Watches a path…, Create a new image watcher. Args: watchpath: Path to watch. destinations:… (+1 more)

### Community 200 - "robotic/task.py"
Cohesion: 0.06
Nodes (28): Initialize a new auto focus system. Args: schedule: Object that can return…, # TODO: add abort (see old robotic/scheduler.py), Initialize a new scheduler. Args: scheduler: Scheduler to use. tasks: Task…, Observer, BackendObservationArchive, ClientSession, Add the list of scheduled tasks to the schedule. Args: tasks: Scheduled tasks., Fetch schedule from portal. Returns: Dictionary with tasks. Raises: Timeout: If… (+20 more)

### Community 201 - "test_xmpp_acl.py"
Cohesion: 0.22
Nodes (12): Integration tests for Phase 8 Access Control (ACLs) over real XMPP. Verifies…, A caller granted "*" access under "allow" can still call normally., A caller not present in the "allow" map is denied by default., A caller on the "deny" list gets exc.RemoteError with a forbidden message, not…, Naming an interface under "allow" permits all of its methods, but nothing…, A module not on the "deny" list is unaffected., test_acl_allow_denies_unlisted_caller(), test_acl_allow_interface_name_sugar() (+4 more)

### Community 202 - "show_module_info.py"
Cohesion: 0.25
Nodes (13): h1(), h2(), inspect_module(), _interface_from_feature(), kv(), main(), _module_state_from_show(), ok() (+5 more)

### Community 203 - "integration/conftest.py"
Cohesion: 0.23
Nodes (13): connect(), make_camera_comm(), make_unopened_comm(), make_xmpp_comm(), fixture, Fixtures shared across all integration tests., Factory fixture: ``await make_xmpp_comm(user)`` returns an open XmppComm for…, Connect a module to LocalComm and return the comm. (+5 more)

### Community 204 - "ICooling"
Cohesion: 0.33
Nodes (5): CELSIUS, ICooling, Any, The module can control the cooling of a device., Enables/disables cooling and sets setpoint. Args: enabled: Enable or disable…

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
Cohesion: 0.20
Nodes (10): Any, Init a new smoothing pipeline step. Args: sigma: Standard deviation for…, Smooth an image. Args: image: Image to smooth. Returns: Smoothed image., Gaussian smoothing of image data using SciPy’s ndimage.gaussian_filter. This…, Smooth, asyncio, test_call(), test_call_no_image_data() (+2 more)

### Community 210 - "Scheduler"
Cohesion: 0.12
Nodes (10): Observer, Iterator for scheduler items, Iterate over scheduler items, Return schedule item., Find a possible slot for a given filter/binning in the given schedule Args:…, Checks, whether a new scheduler item would overlap an existing item Args:…, Scheduler for taking flat fields, Initializes a new scheduler for taking flat fields Args: functions: Flat field… (+2 more)

### Community 211 - "HttpFileCache"
Cohesion: 0.06
Nodes (24): HttpFileCache, Any, Response, Handles OPTIONS access to /{filename} for CORS preflight requests. Args:…, Handles GET access to /{filename} and returns image. Args: request: Request to…, Handles PUSH access to /, stores image and returns filename. Args: request:…, A file cache based on a HTTP server., Initializes file cache. Args: port: Port for HTTP server. cache_size: Size of… (+16 more)

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
Cohesion: 0.19
Nodes (7): PrimaryHDU, Add requested FITS headers to header of given image. Args: image: Image with…, Add FITS header keywords to the given FITS header. Args: image: Image with…, Add FRAMENUM keyword to header Args: image: Image with header to add to., Format filename according to given pattern and store in header of image. Args:…, Add FITS header keywords to the given FITS header. Args: image: Image with…, Add requested FITS headers to header of given image. Args: image: Image with…

### Community 220 - "test_aperture_photometry.py"
Cohesion: 0.26
Nodes (9): MockPhotometryCalculator, asyncio, QTable, AperturePhotometry.__init__ is abstract -- concrete calculators…, test_call_invalid_catalog(), test_call_invalid_data(), test_call_invalid_pixelscale(), test_call_valid() (+1 more)

### Community 221 - "flatfield/test_scheduler.py"
Cohesion: 0.15
Nodes (17): FlatFieldScheduler, Any, Abort current actions., Run the flat-field scheduler., Initialize a new flat field scheduler. Args: flatfield: Flat field module to…, Perform flat-fielding Raises: DeviceBusyError: If a flat-fielding run is…, A single item in the flat scheduler, Initializes a new scheduler item Args: start: Start time in seconds end: End… (+9 more)

### Community 222 - "ImageWriter"
Cohesion: 0.18
Nodes (6): ImageWriter, Any, Writes new images to disk., Creates a new image writer. Args: filename: Pattern for filename to store…, Puts a new images in the DB with the given ID. Args: event: New image event…, Modules for image operations. TODO: write doc

### Community 223 - "CreateFilename"
Cohesion: 0.21
Nodes (9): CreateFilename, Any, Add filename to image. Args: image: Image to add filename to. Returns: Image…, Format and set a filename for the image using a pattern, storing it in the…, Init an image processor that adds a filename to an image. Args: pattern:…, asyncio, test_call(), test_init_default() (+1 more)

### Community 224 - ".move_heliocentric_polar"
Cohesion: 0.50
Nodes (3): Any, DEGREES, Moves on given coordinates. Args: mu: Cosine of the angular distance from Sun…

### Community 225 - ".__call__"
Cohesion: 0.38
Nodes (5): ApertureMask, CircularAperture, Any, floating, NDArray

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

### Community 233 - "ImageFormat"
Cohesion: 0.23
Nodes (6): ImageFormatState, Any, Set the camera image format. Args: fmt: New image format. Raises: ValueError:…, ImageFormat, Enumerator for image formats. Attributes: INT8: 8 bit integer (i.e. byte).…, ImageFormatWidget

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

### Community 238 - "._expose"
Cohesion: 0.17
Nodes (8): ExposureInfo, NamedTuple, Actually do the exposure, should be implemented by derived classes. Args:…, Method that is always called at the very beginning of __expose and can be used…, Wrapper for a single exposure. Args: exposure_time: The requested exposure time…, Add FITS headers in derived classes. Args: image: Image to write FITS headers…, Info about a running exposure., If the telescope has a meridian flip (MERIDIAN keyword in header), flip the…

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

### Community 253 - "test_imagewriter.py"
Cohesion: 0.47
Nodes (11): make_image_event(), make_writer(), asyncio, test_process_event_accepts_all_when_no_filter(), test_process_event_accepts_listed_source(), test_process_event_filters_by_source(), test_process_event_queues_filename(), test_process_event_rejects_wrong_type() (+3 more)

### Community 254 - "test_dummyvideo.py"
Cohesion: 0.15
Nodes (16): Creates a new BaseWebcam. On the receiving end, a VFS root with a HTTPFile must…, DummyVideo, Any, A dummy video module for testing — streams simulated noise frames., Creates a new dummy video module. Args: fps: Frames per second to simulate.…, Set the exposure time (frame interval). Args: exposure_time: Exposure time in…, Background task that generates simulated frames., make_dummyvideo() (+8 more)

### Community 255 - "test_baseroof.py"
Cohesion: 0.30
Nodes (8): MockBaseRoof, Any, asyncio, test_get_fits_header_before_closed(), test_get_fits_header_before_open(), test_not_ready(), test_open(), test_ready()

### Community 256 - "Decision"
Cohesion: 0.17
Nodes (11): 1. `ImageProcessor` — new methods and kwarg, 2. `PipelineMixin.run_pipeline()` — wrap each step, 3. `AstrometryDotNet` — migrate to handle_error, 4. Deprecation notes, 5. Tests, Consequences, Considered options, Decision (+3 more)

### Community 257 - "MotionStatusChangedEvent"
Cohesion: 0.20
Nodes (7): MotionStatusChangedEvent, Any, Event to be sent when the motion status of a device has changed., test_motion_status_invalid_status(), test_motion_status_no_interfaces(), test_motion_status_properties(), test_motion_status_roundtrip()

### Community 258 - "datetime"
Cohesion: 0.36
Nodes (5): datetime, GuidingStatisticsUptime, test_init_with_custom_guiding_statistic(), test_calc_uptime_percentage(), test_end_to_end()

### Community 260 - "TaskData"
Cohesion: 0.05
Nodes (23): Whether this config can currently run. Returns: True if script can run now., Run script. Raises: InterruptedError: If interrupted, Estimate duration of the dark/bias series., PointingScript, Script for pointing the telescope for flats., Whether this config can currently run. Returns: True if script can run now., Run script. Raises: InterruptedError: If interrupted, Estimate duration of slewing to the flat-field pointing. (+15 more)

### Community 261 - "robotic"
Cohesion: 0.43
Nodes (8): acquisition, fibercamera, fts, guiding, robotic, solar telescope, suncamera, weather

### Community 262 - "Archive (image archive base)"
Cohesion: 0.32
Nodes (8): Archive (image archive base), LocalArchive, PyobsArchive, ArchiveSkyflatPriorities, Archive, Image archives (pyobs.robotic.utils.archive) API doc, LocalArchive, PyobsArchive

### Community 263 - "ExposureStatusChangedEvent"
Cohesion: 0.20
Nodes (7): ExposureStatusChangedEvent, Any, Event to be sent, when the exposure status of a device changes., test_exposure_status_changed_no_last(), test_exposure_status_changed_properties(), test_exposure_status_changed_roundtrip(), test_exposure_status_invalid_current()

### Community 264 - "._get_client"
Cohesion: 0.11
Nodes (10): PresenceCallback, Get a proxy to the given client. Args: client: Name of client. Returns: Proxy…, Fetch capabilities for a single interface and push them into the given proxy…, Called when a client disconnects. Args: event: Disconnect event. sender: Name…, Returns list of interfaces for given client. Args: client: Name of client.…, Subscribe to state updates for a given module and interface. Delivers the…, Unsubscribe from state updates. Args: module: Name of remote module. interface:…, Subscribe to presence updates for a given module. Delivers the current value… (+2 more)

### Community 265 - "GuidingStatisticsSkyOffset"
Cohesion: 0.25
Nodes (7): GuidingStatisticsSkyOffset, Calculates RMS of data. Args: data: Data to calculate RMS for. Returns: Tuple…, mock_meta_image(), fixture, test_build_header_to_few_values(), test_end_to_end(), test_get_session_data()

### Community 266 - "BaseVideo"
Cohesion: 0.08
Nodes (19): IImageType, ImageFitsHeaderMixin, IVideo, Module, BaseVideo, Whether the server is started., Handles access to / and returns HTML page. Args: request: Request to respond…, Handles GET access to /ping for testing connectivity. Args: request: Request to… (+11 more)

### Community 267 - "CasesRunner"
Cohesion: 0.29
Nodes (5): CasesRunner, Script for distinguishing cases., Returns FITS header for the current status of this module. Args: namespaces: If…, Estimate duration of the script for the current case., test_cases_get_fits_headers()

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

### Community 272 - "._set_optimal_focus"
Cohesion: 0.22
Nodes (6): Event, Grabs an image ans returns reference. Args: broadcast: Broadcast existence of…, Sets optimal focus. Args: filter_name: Name of filter to use. Raises:…, Sets optimal focus. Raises: WeatherDataError: If the weather station returned…, Receive FilterChangedEvent and set focus. Args: event: The event itself sender:…, timeout

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

### Community 277 - "test_camerasettings.py"
Cohesion: 0.42
Nodes (9): make_camera_proxy(), make_module(), asyncio, Minimal concrete module for exercising CameraSettingsMixin in isolation., Capabilities for a Proxy are fetched in the background (see…, SettingsModule, test_raises_when_capabilities_never_arrive(), test_sets_binning_before_window() (+1 more)

### Community 278 - "PolymorphicBaseModel"
Cohesion: 0.14
Nodes (12): model_serializer, ExposureTimeProvider, Determine and return the exposure time in seconds. Returns: Exposure time in…, Abstract base class for providers that determine camera exposure time., PolymorphicBaseModel, Any, model_validator, Self (+4 more)

### Community 279 - "test_comm_interface_resolution.py"
Cohesion: 0.29
Nodes (8): Converts a list of interface names to interface classes. Args: interfaces: list…, LogCaptureFixture, Tests for Comm._interface_names_to_classes -- the base-Comm chokepoint that…, An interface defined entirely outside pyobs.interfaces resolves the same way…, test_resolves_external_interface(), test_resolves_known_and_skips_unknown_in_same_list(), test_resolves_known_core_interfaces(), test_skips_unknown_name()

### Community 280 - "OffsetsAltAzEvent"
Cohesion: 0.22
Nodes (5): OffsetsAltAzEvent, Any, Event to be sent when an RA/Dec offset is to be moved., test_offsets_altaz_properties(), test_offsets_altaz_roundtrip()

### Community 281 - "ObservationList"
Cohesion: 0.09
Nodes (52): ObservationList, Add observations to the archive. Args: observations: Observations to add., MemoryTaskArchive, Any, In-memory task archive for testing and simple deployments., Returns time when tasks last changed., Returns list of all tasks., Returns task with given ID, or None if not found. (+44 more)

### Community 282 - "IFilters"
Cohesion: 0.22
Nodes (6): IFilters, Any, The module can change filters in a device., Set the current filter. Args: filter_name: Name of filter to set. Raises:…, Initialize a new flat fielder. Args: telescope: Name of ITelescope. camera:…, Return list of filters.

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

### Community 290 - "TaskFailedEvent"
Cohesion: 0.25
Nodes (6): Any, Event to be sent when a task has failed., Initializes a new task failed event. Args: name: Name of task that just…, TaskFailedEvent, test_task_failed_properties(), test_task_failed_roundtrip()

### Community 291 - "TaskFinishedEvent"
Cohesion: 0.25
Nodes (6): Any, Event to be sent when a task has finished., Initializes a new task finished event. Args: name: Name of task that just…, TaskFinishedEvent, test_task_finished_properties(), test_task_finished_roundtrip()

### Community 292 - "Plan: `pyobs-gui` IAutoGuiding widget"
Cohesion: 0.25
Nodes (7): Known bug in the shipped widget (to fix alongside this change), Plan: `pyobs-gui` IAutoGuiding widget, Problem: pixel offsets aren't physical, and the per-image correction is discarded, Proposed pyobs-core change, Resolved from the original open questions, Shipped (pyobs-core, `develop`), Widget design (pyobs-gui)

### Community 293 - "_event_role"
Cohesion: 0.39
Nodes (7): _event_role(), Space-separated role(s) ("send", "subscribe", or both) for an event class, for…, Tests for XmppComm's disco#info event role tagging. See specs/plans/event-role-…, test_event_role_ignores_unrelated_events(), test_event_role_send_and_subscribe(), test_event_role_send_only(), test_event_role_subscribe_only()

### Community 294 - "_DummyTelescopeBase"
Cohesion: 0.07
Nodes (20): IFocuser, Any, MM, The module is a focusing device., Sets new focus. Args: focus: New focus value in mm. Raises:…, Sets focus offset. Args: offset: New focus offset in mm. Raises: ValueError: If…, _DummyTelescopeBase, Any (+12 more)

### Community 295 - "Investigation: pyobs-gui receives every LogEvent twice (SAAO/monet production)"
Cohesion: 0.25
Nodes (7): Access used, Artifacts from this session, Investigation: pyobs-gui receives every LogEvent twice (SAAO/monet production), Next steps, Problem, What's confirmed, What's ruled out

### Community 296 - "format_filename"
Cohesion: 0.43
Nodes (7): format_filename(), Formats a filename given a format template and a FITS header. Args: hdr: FITS…, test_date_obs(), test_default(), test_filter(), test_list(), test_string()

### Community 298 - "Plan: `pyobs-gui` IAutoFocus widget"
Cohesion: 0.29
Nodes (6): Current state (pyobs-core, `develop`), Gap, Open questions, Plan: `pyobs-gui` IAutoFocus widget, Proposed pyobs-core change, Widget design (pyobs-gui)

### Community 299 - "_PhotometryCalculator"
Cohesion: 0.29
Nodes (3): _PhotometryCalculator, Table, Abstract class for photometry calculators.

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

### Community 312 - "IGain"
Cohesion: 0.33
Nodes (5): IGain, Any, The camera supports setting of gain, to be used together with…, Set the camera gain. Args: gain: New camera gain. Raises: ValueError: If gain…, Set the camera offset. Args: offset: New camera offset. Raises: ValueError: If…

### Community 313 - "ConditionalRunner"
Cohesion: 0.33
Nodes (4): ConditionalRunner, Script for running an if condition., Returns FITS header for the current status of this module. Args: namespaces: If…, Estimate duration of the branch that would be run for the current condition.

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

### Community 319 - "comm.py"
Cohesion: 0.27
Nodes (4): The Comm object is responsible for all communication between modules (see…, _ProxyContext, ProxyType, Returned by Comm.proxy() / Object.proxy() / Comm.safe_proxy(). Must be used as:…

### Community 321 - "IModule"
Cohesion: 0.33
Nodes (5): IModule, Any, The module is actually a module. Implemented by all modules., Reset error of module, if any., Returns names of all methods the calling module is allowed to invoke on this…

### Community 322 - "Photometry (pyobs.images.processors.photometry) API doc"
Cohesion: 0.83
Nodes (4): Photometry (pyobs.images.processors.photometry) API doc, Photometry, PhotUtilsPhotometry, SepPhotometry

### Community 323 - "IWindow"
Cohesion: 0.29
Nodes (5): IWindow, Any, The camera supports windows, to be used together with…, Set the camera window. Args: left: X offset of window. top: Y offset of window.…, Do camera settings for given camera.

### Community 324 - "._register_exception"
Cohesion: 0.29
Nodes (5): Watch for repeated occurrences of exc_type -- optionally scoped to a specific…, Checks all handlers against all recorded exceptions and returns those whose…, ExceptionHandler, LoggedException, NamedTuple

### Community 325 - "test_module_state_publishing.py"
Cohesion: 0.33
Nodes (6): _discover_concrete_modules(), asyncio, parametrize, Parametrized check: every concrete Module publishes state for each stateful…, All concrete (non-abstract, non-internal) pyobs.modules.Module subclasses.…, test_module_publishes_all_stateful_interfaces()

### Community 326 - "WeatherSensors"
Cohesion: 0.12
Nodes (18): IAutonomous, The module does some autonomous actions, mainly used for warnings to users., IStartStop, Any, The module can be started and stopped., IWeather, Any, The module acts as a weather station. (+10 more)

### Community 328 - "HelioprojectiveTarget"
Cohesion: 0.47
Nodes (3): HelioprojectiveTarget, SkyCoord, Target

### Community 329 - ".abort"
Cohesion: 0.40
Nodes (3): Any, Abort current actions., Sets the currently active fiber. Must be in fiber_names capability. Args:…

### Community 333 - ".__init__"
Cohesion: 0.40
Nodes (4): Any, Pipeline, ProgressCallback, Args: archive: Archive to fetch raw and calibration frames from. pipeline:…

### Community 335 - "._get_image_median"
Cohesion: 0.50
Nodes (3): Returns median of image after trimming it to TRIMSEC and to given frame. Args:…, test_get_image_median_full_frame_without_trimsec(), test_get_image_median_restricts_to_frame()

### Community 338 - "Pipeline"
Cohesion: 0.12
Nodes (25): Pipeline, Any, Create master bias frame. Args: images: List of raw bias frames. Returns:…, Create master dark frame. Args: images: List of raw dark frames. bias: Bias…, Create master flat frame. Args: images: List of raw flat frames. bias: Bias…, Calibrate a single science frame. Args: image: Image to calibrate. Returns:…, Pipeline based on the astropy package ccdproc., Pipeline for science images. Args: steps: List of pipeline steps to perform.… (+17 more)

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
- **548 isolated node(s):** `pyobs-core`, `Goal`, `Architecture`, `File Map (representative, not exhaustive — see commit diffs for the full ~74-file list)`, `Tasks` (+543 more)
  These have ≤1 connection - possible missing edges or undocumented components.
- **49 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **What is the exact relationship between `Configuration utilities (pyobs.utils.config) API doc` and `Coordinate utilities (pyobs.utils.coordinates) API doc`?**
  _Edge tagged AMBIGUOUS (relation: conceptually_related_to) - confidence is low._
- **What is the exact relationship between `PyObsError` and `ScriptRunner.run()`?**
  _Edge tagged AMBIGUOUS (relation: conceptually_related_to) - confidence is low._
- **What is the exact relationship between `FocusError` and `FocusModel.set_optimal_focus`?**
  _Edge tagged AMBIGUOUS (relation: conceptually_related_to) - confidence is low._
- **Why does `Time` connect `Time` to `BaseGuiding`, `RunningState`, `Interface`, `DynamicTarget`, `utils/exceptions.py`, `ImageProcessor`, `Script`, `FilenameFormatter`, `TimeDelta`, `Event`, `http_request_with_retries`, `test_flatfielder.py`, `tests/test_events.py`, `AirmassConstraint`, `Object`, `ObservationState`, `test_control.py`, `test_lco_http.py`, `FitsHeaderEntry`, `test_backend_archives.py`, `CoolingState`, `IPointingAltAz.py`, `test_astroplanscheduler.py`, `test_transitimaging.py`, `robotic/test_scheduler.py`, `transitimaging.py`, `Calibration`, `Publisher`, `Unit`, `Proxy`, `SkyFlatsBasePointing`, `test_yaml_archives.py`, `FlatFielder`, `ITelescope`, `Offsets`, `.now`, `test_proxy.py`, `SiderealTarget`, `ImageType`, `Weather`, `FileSystemObservationArchive`, `enums.py`, `dummycamera.py`, `DummySolarTelescope`, `DummyCamera`, `test_pyobs_archive.py`, `application.py`, `_schedulereader.py`, `test_coordinates.py`, `DataProvider`, `LocalArchive`, `Test Commlogging (comm)`, `ImagingScript`, `test_darkbias.py`, `Portal`, `test_autofocus.py`, `Grid`, `pyobs.py`, `DummyRaDecTelescope`, `Scheduler`, `Observation`, `Archive`, `test_transit_mastermind.py`, `ExpTimeEval`, `.__init__`, `CoolingStatus`, `SkyflatPriorities`, `fits.py`, `test_schedulereader.py`, `TransitMerit`, `TaskStartedEvent`, `robotic/task.py`, `Scheduler`, `.add_fits_headers`, `flatfield/test_scheduler.py`, `PyobsArchive`, `.night_obs`, `._filter_data`, `TaskData`, `CasesRunner`, `filters.py`, `PolymorphicBaseModel`, `ObservationList`, `GoodWeatherEvent`, `_DummyTelescopeBase`, `ConditionalRunner`, `comm.py`, `WeatherSensors`, `HelioprojectiveTarget`, `Pipeline`?**
  _High betweenness centrality (0.280) - this node is a cross-community bridge._
- **Why does `Image` connect `Image` to `BaseGuiding`, `_SepAperturePhotometry`, `Interface`, `_ResponseImageWriter`, `ImageProcessor`, `utils/exceptions.py`, `GuidingStatisticsSkyOffset`, `Any`, `VirtualFileSystem`, `AstrometryDotNet`, `FilenameFormatter`, `AperturePhotometry`, `mixins/test_fitsheader.py`, `Event`, `PipelineMixin`, `test_flatfielder.py`, `_DaoBackgroundRemover`, `GuidingStatistics`, `SoftBin`, `AddMask`, `Archive`, `GuidingStatisticsPixelOffset`, `_PhotometryCalculator`, `test_acquisition.py`, `StarExpTimeEstimator`, `fits.py`, `Calibration`, `PillowHelper`, `Unit`, `Save`, `FitsHeaderOffsets`, `test_basevideo.py`, `ITelescope`, `CatalogCircularMask`, `Offsets`, `ImageType`, `._get_image_median`, `test_autoguiding.py`, `Smooth`, `Pipeline`, `dummycamera.py`, `Ring`, `DummyCamera`, `.add_fits_headers`, `test_aperture_photometry.py`, `ProjectedOffsets`, `test_pyobs_archive.py`, `CreateFilename`, `FocusSeries`, `_SourceCatalog`, `LocalArchive`, `_PhotUtilAperturePhotometry`, `._expose`, `PyobsArchive`, `._filter_data`, `VFSFile`, `ImageSourceFilter`?**
  _High betweenness centrality (0.163) - this node is a cross-community bridge._
- **Why does `Module` connect `Module` to `BaseGuiding`, `Time`, `RunningState`, `Interface`, `Kiosk`, `test_dummymode.py`, `._get_client`, `utils/exceptions.py`, `test_kiosk.py`, `XmppComm`, `Scheduler`, `mixins/test_fitsheader.py`, `PipelineMixin`, `test_camerasettings.py`, `Object`, `ObservationState`, `test_presence.py`, `FitsHeaderEntry`, `Stellarium`, `IPointingAltAz.py`, `IBinning`, `FlatFieldPointing`, `.__init__`, `version`, `robotic/test_scheduler.py`, `StandAlone`, `test_acquisition.py`, `xmpp/rpc.py`, `WindowCapabilities`, `Publisher`, `test_basevideo.py`, `PointingSeries`, `comm.py`, `GridNode`, `IModule`, `Telegram`, `IWindow`, `._register_exception`, `test_module_state_publishing.py`, `WeatherSensors`, `ImageWatcher`, `robotic/task.py`, `MockWeather`, `test_autoguiding.py`, `Weather`, `enums.py`, `HttpFileCache`, `xmppcomm.py`, `test_exception_logging.py`, `Application`, `flatfield/test_scheduler.py`, `ImageWriter`, `application.py`, `test_flatfield.py`, `ScriptRunner`, `FocusModel`, `_AbortableModule`?**
  _High betweenness centrality (0.081) - this node is a cross-community bridge._
- **Are the 163 inferred relationships involving `Time` (e.g. with `PyobsCLI` and `Proxy`) actually correct?**
  _`Time` has 163 INFERRED edges - model-reasoned connections that need verification._