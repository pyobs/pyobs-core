# Graph Report - pyobs-core  (2026-08-10)

## Corpus Check
- 761 files · ~384,686 words
- Verdict: corpus is large enough that graph structure adds value.

## Summary
- 8550 nodes · 20708 edges · 418 communities (384 shown, 34 thin omitted)
- Extraction: 93% EXTRACTED · 7% INFERRED · 0% AMBIGUOUS · INFERRED: 1398 edges (avg confidence: 0.55)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `c1c59747`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- Observation
- time.py
- Time
- IAbortable
- MotionStatus
- Module
- Image
- DynamicTarget
- BaseCamera
- ImageProcessor
- ObservationList
- basetelescope.py
- TimeDelta
- XmppComm
- AstrometryDotNet
- FilenameFormatter
- test_astroplanscheduler.py
- AperturePhotometry
- DummyRoof
- mixins/test_fitsheader.py
- Event
- PipelineMixin
- test_acquisition.py
- test_flatfielder.py
- LocalComm
- tests/test_events.py
- _SourceCatalog
- Object
- FitsHeaderEntry
- WindowingWidget
- Interfaces (pyobs.interfaces) API doc
- test_control.py
- _DaoBackgroundRemover
- test_presence.py
- test_lco_http.py
- BaseRoof
- Future
- RemoveBackground
- CoolingState
- test_follow.py
- test_yaml_archives.py
- IRunnable
- BaseVideo
- Comm
- TaskData
- robotic/test_scheduler.py
- StandAlone
- utils/exceptions.py
- VirtualFileSystem
- test_stellarexptime.py
- StarExpTimeEstimator
- xmpp/rpc.py
- WindowCapabilities
- test_shellcommand.py
- Calibration
- object.py
- Publisher
- http_request_with_retries
- Unit
- Proxy
- DummyAltAzTelescope
- test_basevideo.py
- SkyFlatsBasePointing
- test_csvpicker_scheduler.py
- FlatFielder
- IExposure
- Telegram
- benchmark_state_throughput.py
- LcoScript
- Offsets
- .now
- PyObsError
- test_proxy.py
- XEP_0009
- SiderealTarget
- PyobsDaemon
- MockWeather
- test_config.py
- Pipeline
- test_autoguiding.py
- Weather
- SolarElevationConstraint
- SkyOffsets
- Image (images)
- test_schedulewriter.py
- Ring
- DummySolarTelescope
- xmppcomm.py
- test_backend_archives.py
- DummyCamera
- Application
- DummyComm
- CallModuleScript
- ProjectedOffsets
- test_pyobs_archive.py
- HttpFile
- PillowHelper
- application.py
- FocusSeries
- BaseGuiding
- make_proxy_cm
- _AbortableModule
- ScriptRunner
- LcoScheduleReader
- test_coordinates.py
- get_registered_interface
- Portal
- LocalArchive
- _AbortableModule
- _PhotUtilAperturePhotometry
- Mixins (pyobs.mixins) API doc
- Script base class
- test_background_task.py
- Test Commlogging (comm)
- MotionStatusChangedEvent
- WeatherApi
- ImagingScript
- LcoTaskArchive
- MemoryFile
- VFSFile
- LocalFile
- test_version_mismatch.py
- CLAUDE.md (repo guide)
- comm.py
- FocusModel
- TaskFinishedEvent
- ImageSourceFilter
- test_darkbias.py
- test_config_schema.py
- GridNode
- lco/taskrunner.py
- Test Localcomm (local)
- GoodWeatherEvent
- module.py
- test_dummymode.py
- test_dummyradectelescope.py
- IRunning.py
- test_autofocus.py
- Grid
- test_kiosk.py
- pyobs.py
- Robotic recipe (doc)
- is_valid_jid
- OffsetResult
- test_dummyvideo.py
- .__init__
- Scheduler
- RollingTimeAverage
- test_localcomm_state.py
- RegularSphericalGrid
- Plan: pyobs 2.0 rollout (work plan)
- test_lcoscript.py
- 3rd party packages (doc)
- Any
- BufferedFile
- create_rst.py
- GuidingStatistics
- SoftBin
- AddMask
- Archive
- RandomizeGrid
- comm/test_events.py
- BrightestStarOffsets
- pyobs/modules/utils/__init__.py
- test_imagewriter.py
- ExpTimeEval
- Stellarium
- Overview (doc)
- SepSourceDetection
- .__init__
- _CalibrationCache
- RunningState
- test_grab_sequence.py
- binding.py
- NewSpectrumEvent
- OptimalFocusState
- test_istructuredconfig.py
- HttpFileCache
- _SepAperturePhotometry
- Scheduler
- Plan: Split archive prefetch from CPU-bound merit evaluation
- Test Basecamera (camera)
- Test Imagewatcher (image)
- test_schedulereader.py
- Merit
- ejabberd shaper throttling bug (xmpp_socket.erl re-arm) & fix
- NewImageEvent
- FitsHeaderOffsets
- Interface
- CameraSettingsMixin
- PointingSeries
- GridPipeline
- test_xmpp_rpc.py
- Plan: Widget plugin mechanism + pyside6-deploy packaging for pyobs-gui
- What's New in pyobs 2.0 (doc)
- TaskStartedEvent
- ExpTime
- CatalogCircularMask
- BrightestStarGuiding
- ImageWatcher
- .__init__
- test_filters.py
- show_module_info.py
- integration/conftest.py
- MoveAltAzEvent
- robotic
- Scheduler module
- BaseModel (pyobs.utils.serialization)
- _ResponseImageWriter
- Smooth
- SkyflatPriorities
- DataCache
- PyobsArchive
- wait_for
- test_httpfilecache.py
- Image (pyobs.images.processors.image) API doc
- Offsets (pyobs.images.processors.offsets) API doc
- Constraint
- FileSystemTaskArchive
- .add_fits_headers
- FlatField
- flatfield/test_scheduler.py
- Pixeloffset (guidingstatistics)
- NextImage
- Weather State (weather)
- XEP_0009_timeout
- ConfigStatus
- FileList
- MockBaseDome
- TempFile
- pyobs 2.0 Wire Protocol, State, and Access Control design doc
- test_xmpp_acl.py
- IAcquisition interface / AcquisitionState / AcquisitionResult
- iag50 reconnect-storm / late-joiner capability-fetch incident
- CHANGELOG.rst
- test_aperture_photometry.py
- Image class
- .__call__
- Access Control (ACLs): allow/deny, mode: enforce|log
- .retrieve_class_on_deserialization
- Module.startup() lifecycle helper
- test_comm_interface_resolution.py
- ProjectionFocusSeries
- .__init__
- InfluxHandler
- SMBFile
- pyobs-gui as a standalone binary (umbrella design)
- Plan: pyobs-pipeline (Django web project)
- LogEvent
- test_safe_send.py
- test_camerasettings.py
- Two-phase Object lifecycle; rationale: __init__ must not touch hardware/external services (only store params, create children, register background tasks); open() is where side effects happen, so objects can be constructed cheaply/safely before being started
- Simulation recipe (doc)
- test_baseroof.py
- get_class_from_string
- .__init__
- TaskRunner
- GuidingStatisticsSkyOffset
- IAutoFocus
- format_filename
- IStructuredConfig interface
- robotic
- Archive (image archive base)
- .__init__
- ._client_disconnected
- _PhotometryCalculator
- IGain
- IModule
- ._get_next
- ._main
- WeatherSensors
- ._set_presence
- .__init__
- Image.trim
- conftest.py
- Misc (pyobs.images.processors.misc) API doc
- PolymorphicBaseModel
- .move_altaz
- .__init__
- Any
- LcoObservationArchive
- Target
- ._filter_data
- test_exceptions.py
- pyobs.modules.utils (doc)
- ICalibrate
- IConfig
- IDataSequence
- IFocuser
- IPointingSeries
- IScriptRunner
- ISyncTarget
- IWindow
- ADR-0008: _safe_send keeps bounded retry unlike capability/subscribe fetches
- Module._watch_event_loop_lag
- ICamera(IData, IExposure) -> ICamera(IData); IExposure moved to BaseCamera
- pyobs.modules.image (doc)
- .__init__
- check_pyobs_releases.sh
- check_ejabberd_notify.py
- ITrackingRate
- Photometry (pyobs.images.processors.photometry) API doc
- Event <event role="send|subscribe|send subscribe"> attribute
- HttpFileCache token param + Bearer auth check + CORS headers
- Plan: pyobs-gui TelescopeWidget layout width-floor investigation
- self._slot_bindings, Ctrl+N recall / Ctrl+Alt+N bind scheme
- Image.trim() (data/mask/uncertainty alignment, CRPIX shift, catalog guard)
- .__init__
- DummyAutoGuiding
- IFlatField
- IOffsetsRaDec
- IPointingHelioprojective
- IPointingRaDec
- IStructuredConfig
- .night_obs
- README.md
- Install-ejabberd (xmpp)
- XmppComm._disconnected
- Autocompletion ()
- AutoFocusWidget (pyobs-gui)
- pyobs.modules.pointing (doc)
- pyobs.modules.weather (doc)
- ._subscribe_presence
- .grab_data
- ._expose
- check_changelog.sh
- delete_pubsub_nodes.py
- ejabberd 10x Shaper Benchmark Config
- list_pubsub_nodes.py
- ADR-0005: IConfig stays a stringly-keyed fallback
- Exception handling across the RPC boundary (design doc)
- ModuleLocation dataclass (nested in ModuleCapabilities)
- Steering: pyobs project fleet tiers (core/connected/internal)
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
2. `Image` - 443 edges
3. `Task` - 227 edges
4. `Module` - 183 edges
5. `DataProvider` - 168 edges
6. `ObservationList` - 164 edges
7. `Event` - 152 edges
8. `Interface` - 137 edges
9. `Comm` - 113 edges
10. `ImageType` - 112 edges

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
- **State-driven pyobs-gui widgets for run-based interfaces (IAcquisition/IAutoFocus/IAutoGuiding)** — specs_plans_gui_iacquisition_widget_doc, specs_plans_gui_iautofocus_widget_doc, specs_plans_gui_iautoguiding_widget_doc [INFERRED 0.85]
- **pyobs-gui standalone-binary initiative (login flow, login window, widget packaging)** — specs_plans_gui_interactive_login_doc, specs_plans_gui_login_window_doc, specs_plans_gui_widget_plugins_and_packaging_doc [EXTRACTED 1.00]
- **Event-loop-blocking diagnosis family (astropy IERS, vendor SDK calls, scheduler CPU-bound)** — specs_steering_astropy_iers_event_loop_stalls_doc, specs_steering_blocking_sdk_calls_must_not_run_on_the_event_loop_doc, specs_steering_scheduler_cpu_bound_merit_evaluation_stalls_event_loop_doc [INFERRED 0.85]
- **OnDemandScheduler stall investigation/fix chain** — specs_plans_scheduler_event_loop_blocking_doc, specs_plans_scheduler_archive_prefetch_for_process_isolation_doc, specs_steering_scheduler_cpu_bound_merit_evaluation_stalls_event_loop_doc [EXTRACTED 1.00]
- **pyobs-pipeline project cluster (web app + Reduction/Night hardening + kwarg validation)** — specs_plans_pyobs_pipeline_doc, specs_plans_night_archive_io_hardening_doc, specs_plans_object_kwarg_validation_doc [EXTRACTED 1.00]

## Communities (418 total, 34 thin omitted)

### Community 0 - "Observation"
Cohesion: 0.03
Nodes (69): datetime, Modules for robotic mode. TODO: write doc, Initialize a new auto focus system. Args: schedule: Object that can return…, # TODO: add abort (see old robotic/scheduler.py), Initialize a new scheduler. Args: scheduler: Scheduler to use. tasks: Task…, Observation, ObservationState, StrEnum (+61 more)

### Community 1 - "time.py"
Cohesion: 0.05
Nodes (49): IAutonomous, IStartStop, The module does some autonomous actions, mainly used for warnings to users., ICamera, IData, The module controls a camera., IData, Interface (+41 more)

### Community 2 - "Time"
Cohesion: 0.03
Nodes (93): AirmassConstraint, ndarray, SkyCoord, Constraint, ndarray, SkyCoord, Returns a boolean mask of candidates passing this constraint. Default…, MoonIlluminationConstraint (+85 more)

### Community 3 - "IAbortable"
Cohesion: 0.09
Nodes (30): IAbortable, Any, Interface, Abort current actions., The module has an abortable action., AcquisitionAttempt, AcquisitionResult, AcquisitionState (+22 more)

### Community 4 - "MotionStatus"
Cohesion: 0.04
Nodes (57): IReady, FiltersCapabilities, FilterState, FocuserState, DeviceMotionStatus, IMotion, MotionState, Any (+49 more)

### Community 5 - "Module"
Cohesion: 0.04
Nodes (48): AbstractEventLoop, IConfig, IModule, setter, The module that this Comm object is attached to., The module that this Comm object is attached to., Module, Any (+40 more)

### Community 6 - "Image"
Cohesion: 0.03
Nodes (76): MetaClass, Image, CCDData, Create Image from a bytes array containing a FITS file. Args: data: Bytes array…, Create image from FITS file. Args: filename: Name of file to load image from.…, Create image from astropy.CCDData. Args: data: CCDData to create image from.…, Load Image from HDU list. Args: data: HDU list. Returns: Image., A container class for astronomical image data and associated metadata. This… (+68 more)

### Community 7 - "DynamicTarget"
Cohesion: 0.06
Nodes (42): DynamicTarget, SkyCoord, Target, Pick the best available target given current conditions. For static targets…, HeliocentricPolarTarget, Target, HelioprojectiveTarget, SkyCoord (+34 more)

### Community 8 - "BaseCamera"
Cohesion: 0.04
Nodes (56): ISpectrograph, ExposureState, IExposure, Interface, The module controls a camera., BaseCamera, calc_expose_timeout(), ExposureInfo (+48 more)

### Community 9 - "ImageProcessor"
Cohesion: 0.03
Nodes (68): Some info about :class:`pyobs.images.Image`., ImageProcessor, Any, Init new image processor. Args: on_error: How the pipeline should handle an…, The error handling mode for this step., Processes an image. Args: image: Image to process. Returns: Processed image., Resets state of image processor, Circle (+60 more)

### Community 10 - "ObservationList"
Cohesion: 0.06
Nodes (60): ObservationList, Any, Add the list of scheduled tasks to the schedule. Args: tasks: Scheduled tasks., Fetch schedule from the portal. Returns: Dictionary with tasks. Raises:…, Add observations to the archive. Args: observations: Observations to add., Remove all PENDING observations that end after start_time. Args: start_time:…, Return all observations. Args: time: Unused — in-memory archive holds all…, MemoryTaskArchive (+52 more)

### Community 11 - "basetelescope.py"
Cohesion: 0.03
Nodes (87): IOffsetsRaDec, IFitsHeaderBefore, Interface, The module provides some additional header entries for FITS headers before some…, RaDecOffsetState, IPointingBody, Any, Interface (+79 more)

### Community 12 - "TimeDelta"
Cohesion: 0.07
Nodes (58): ConstantMerit, Merit function that returns a constant value., model_validator, Self, Merit function that uses time windows., TimeWindow, TimeWindowMerit, OnDemandScheduler (+50 more)

### Community 13 - "XmppComm"
Cohesion: 0.05
Nodes (35): Any, Interface, Store published capabilities for inclusion in disco#info responses., Return this client's own published capabilities., Fetch and deserialize capabilities for a remote module's interface. Retries…, Subscribe to a pubsub node, retrying until the node exists. Runs as a…, Create a new XMPP Comm module. Either a fill JID needs to be provided, or a set…, Called, when the module connected to this Comm changes. Args: module: The… (+27 more)

### Community 14 - "AstrometryDotNet"
Cohesion: 0.04
Nodes (41): ImageProcessor on_error kwarg / per-step error handling, Astrometry processors doc, AstrometryDotNet (astrometry processor), Astrometry, Finds astrometric solution to a given image. Args: image: Image to analyse.…, Base class for astrometry processors, AstrometryDotNet, Any (+33 more)

### Community 15 - "FilenameFormatter"
Cohesion: 0.05
Nodes (44): Format filename with given formatter., Any, Save an image to the virtual file system and optionally broadcast a…, Init an image processor that broadcasts an image Args: filename: Filename to…, Initialize processor., Broadcast image. Args: image: Image to broadcast. Returns: Original image., Save, CreateFilename (+36 more)

### Community 16 - "test_astroplanscheduler.py"
Cohesion: 0.05
Nodes (83): Mastermind, IAutonomous, IFitsHeaderBefore, Mastermind for a full robotic mode., AstroplanScheduler, Any, ObservingBlock, Actually do the scheduling, usually run in a separate process. (+75 more)

### Community 17 - "AperturePhotometry"
Cohesion: 0.12
Nodes (11): AperturePhotometry, Any, Base class for aperture photometry processors -- not meant to be used directly,…, Do aperture photometry on given image. Args: image: Image to do aperture…, Photometry, Do aperture photometry on given image. Args: image: Image to do aperture…, Base class for photometry processors., Any (+3 more)

### Community 18 - "DummyRoof"
Cohesion: 0.09
Nodes (30): WeatherState, DummyRoof, Any, IRoof, Get the percentage the roof is open., Stop the motion. Args: device: Name of device to stop, or None for all. Raises:…, A dummy camera for testing., Creates a new dummy root. (+22 more)

### Community 19 - "mixins/test_fitsheader.py"
Cohesion: 0.11
Nodes (49): FitsModule, make_image(), make_module(), make_observer(), asyncio, date, EarthLocation, Minimal concrete module for exercising ImageFitsHeaderMixin in isolation. (+41 more)

### Community 20 - "Event"
Cohesion: 0.06
Nodes (42): Event, Base class for all events., DataType, TypedDict, DataType, TypedDict, DataType, TypedDict (+34 more)

### Community 21 - "PipelineMixin"
Cohesion: 0.06
Nodes (39): Handle an ImageError raised by this step, when on_error == "error". Override…, PipelineMixin, Any, Mixin for a module that needs to implement an image pipeline., Initializes the mixin. Args: steps: Pipeline steps to run on images. archive:…, Resets all previous state of the involved image processors., Modules for image operations. TODO: write doc, Pipeline (+31 more)

### Community 22 - "test_acquisition.py"
Cohesion: 0.28
Nodes (28): make_acquisition(), make_camera(), make_image(), make_telescope(), asyncio, offsets_frame: 'radec', 'altaz', or None (telescope supports neither offsets…, _state_for(), test_abort_sets_event() (+20 more)

### Community 23 - "test_flatfielder.py"
Cohesion: 0.08
Nodes (60): make_flatfielder(), make_observer(), make_twilight_observer(), asyncio, parametrize, Regression test for #481: median == bias_level used to raise ZeroDivisionError., Observer stub returning a constant solar altitude for every sun_altaz() call., Observer stub distinguishing the first (now) vs second (+10min) sun_altaz()… (+52 more)

### Community 24 - "LocalComm"
Cohesion: 0.11
Nodes (15): LocalComm, Store presence state and dispatch to all subscribers., Return presence state of a connected module., Announce this module to already-connected peers, mirroring XmppComm's presence-…, Returns list of currently connected clients., Send an event to other clients., LocalNetwork, fixture (+7 more)

### Community 25 - "tests/test_events.py"
Cohesion: 0.06
Nodes (42): BadWeatherEvent, Event to be sent on bad weather., Create Event from a dictionary. Args: obj_dict: JSON string for event. Returns:…, FilterChangedEvent, Event to be sent when a filter has been changed., FocusFoundEvent, Event to be sent when a new best focus has been found, e.g. after a focus…, ModeChangedEvent (+34 more)

### Community 26 - "_SourceCatalog"
Cohesion: 0.09
Nodes (16): Any, floating, NDArray, PySepStatsCalculator, Any, DataFrame, floating, NDArray (+8 more)

### Community 27 - "Object"
Cohesion: 0.06
Nodes (53): PydanticBaseModel, Object, Base class for all objects in *pyobs*., Whether object has been opened., Can be overloaded to quit program., Any, ConfigurationStatus, ConfigurationSummary (+45 more)

### Community 28 - "FitsHeaderEntry"
Cohesion: 0.05
Nodes (35): IFitsHeaderAfter, Any, Interface, The module provides some additional header entries for FITS headers after some…, Returns FITS header for the current status of this module. Args: namespaces: If…, FitsHeaderEntry, Any, Returns FITS header for the current status of this module. Args: namespaces: If… (+27 more)

### Community 29 - "WindowingWidget"
Cohesion: 0.05
Nodes (14): BinningWidget, DataDisplayWidget, PrimaryHDU, Slot, Select path for auto-saving., ExposeWidget, Slot, ExposureTimeWidget (+6 more)

### Community 30 - "Interfaces (pyobs.interfaces) API doc"
Cohesion: 0.04
Nodes (53): Interfaces (pyobs.interfaces) API doc, IAbortable, IAcquisition, IAutoFocus, IAutoGuiding, IAutonomous, IBinning, ICalibrate (+45 more)

### Community 31 - "test_control.py"
Cohesion: 0.07
Nodes (55): CasesRunner, Script for distinguishing cases., Returns FITS header for the current status of this module. Args: namespaces: If…, Estimate duration of the script for the current case., ConditionalRunner, Script for running an if condition., Returns FITS header for the current status of this module. Args: namespaces: If…, Estimate duration of the branch that would be run for the current condition. (+47 more)

### Community 32 - "_DaoBackgroundRemover"
Cohesion: 0.07
Nodes (31): Source Detection processors doc, DaophotSourceDetection (detection processor), SepSourceDetection (detection processor), _DaoBackgroundRemover, Any, floating, NDArray, DaophotSourceDetection (+23 more)

### Community 33 - "test_presence.py"
Cohesion: 0.05
Nodes (51): ModuleOpenedEvent, Event to be sent when a module has opened., ModuleLocation, _FakeProxyContext, make_xmpp_comm(), asyncio, Tests for Phase 2.5 Presence and Capabilities implementation., Module.open() passes empty string for label when _label is None. (+43 more)

### Community 34 - "test_lco_http.py"
Cohesion: 0.09
Nodes (44): Camera, CameraType, ConfigurationType, Enclosure, Instrument, InstrumentType, Mode, ModeType (+36 more)

### Community 35 - "BaseRoof"
Cohesion: 0.06
Nodes (29): IDome, IDome, IPointingAltAz, IRoof, The module controls a dome, i.e. a :class:`~pyobs.interfaces.IRoof` with a…, IRoof, IMotion, The module controls a roof. (+21 more)

### Community 36 - "Future"
Cohesion: 0.08
Nodes (36): Wait until all devices are in one of the given motion states. Args: abort:…, Run script. Raises: InterruptedError: If interrupted, acquire_lock(), event_wait(), Future, Any, Lock, Sets a new timeout for the method call. Cancels any existing timeout handle and… (+28 more)

### Community 37 - "RemoveBackground"
Cohesion: 0.21
Nodes (9): Any, Estimate and subtract the background from an image using a DAOPhot-style…, Init an image processor that removes background from image. Args: sigma: Sigma…, Remove background from image. Args: image: Image to remove background from.…, RemoveBackground, asyncio, test_call_const_background(), test_init() (+1 more)

### Community 38 - "CoolingState"
Cohesion: 0.10
Nodes (29): _dataclass_to_xml(), _event_schema_to_xml(), _interface_schema_to_xml(), _parse_scalar(), Any, Element, Shared XML serializer for pyobs 2.0 (urn:pyobs:rpc:1). Both the state pub/sub…, Deserialize an XML element (produced by ``value_to_xml``) to a Python value.… (+21 more)

### Community 39 - "test_follow.py"
Cohesion: 0.08
Nodes (34): AltAzState, IPointingAltAz, Interface, The module can move to Alt/Az coordinates, usually combined with…, build_skycoord(), FollowMixin, get_coords(), Any (+26 more)

### Community 40 - "test_yaml_archives.py"
Cohesion: 0.24
Nodes (28): make_obs(), make_obs_archive(), make_task(), make_task_archive(), asyncio, Verify observations are actually written to disk in valid YAML., test_add_and_load_observations(), test_add_empty_list_is_noop() (+20 more)

### Community 41 - "IRunnable"
Cohesion: 0.33
Nodes (5): IRunnable, Any, IAbortable, Perform module task Raises: DeviceBusyError: If this task is already running.…, The module has some action that can be started remotely.

### Community 42 - "BaseVideo"
Cohesion: 0.10
Nodes (14): IVideo, BaseVideo, IImageType, Whether the server is started., Handles access to /video.mjpg and returns the video. Args: request: Request to…, Whether camera is currently active., Can be overridden by derived class to implement inactivity sleep, Can be overridden by derived class to implement inactivity sleep (+6 more)

### Community 43 - "Comm"
Cohesion: 0.04
Nodes (40): Comm responsibility: Discovery (clients_with_interface), Comm responsibility: Events (broadcast typed events), Comm, Any, Interface, ProxyType, Get a proxy to the given client. Args: client: Name of client. Returns: Proxy…, Fetch capabilities for a single interface and push them into the given proxy… (+32 more)

### Community 44 - "TaskData"
Cohesion: 0.03
Nodes (95): EarthLocation, model_validator, Self, SkyCoord, Merit function for observing transits., Returns the time of the next mid-transit., Returns the time until which observations should run: mid-transit + duration/2…, TransitMerit (+87 more)

### Community 45 - "robotic/test_scheduler.py"
Cohesion: 0.13
Nodes (39): Scheduler, DummyTask, make_async_gen(), make_obs(), make_scheduler(), asyncio, Regression test: _on_task_finished is registered for both TaskFinishedEvent and…, _state_for() (+31 more)

### Community 46 - "StandAlone"
Cohesion: 0.09
Nodes (40): pyobs.modules.test (doc), StandAlone, Quickstart (doc), pyobs-core (pip package), Test modules. TODO: write doc, Any, Example module that only logs the given message forever in the given interval., Creates a new StandAlone object. Args: message: Message to log in the given… (+32 more)

### Community 47 - "utils/exceptions.py"
Cohesion: 0.08
Nodes (31): Declare that the given PyobsError types (and their subclasses) fire often…, AbortedError, AcquisitionError, DeviceBusyError, ExceptionHandler, GeneralError, GrabImageError, InitError (+23 more)

### Community 48 - "VirtualFileSystem"
Cohesion: 0.07
Nodes (24): Any, DataFrame, HDUList, Convenience function for writing an Image to a FITS file. Args: filename: Name…, Convenience function that wraps around open_file() to read an Image. Args:…, Convenience function for writing an Image to a FITS file. Args: filename: Name…, Convenience function for writing bytes to a file. Args: filename: Name of file…, Convenience function for reading a CSV file into a DataFrame. Args: filename:… (+16 more)

### Community 49 - "test_stellarexptime.py"
Cohesion: 0.09
Nodes (37): ExposureTimeProvider, Determine and return the exposure time in seconds. Returns: Exposure time in…, Abstract base class for providers that determine camera exposure time., ndarray, Find the brightest star near the image centre by fitting a 2D Gaussian. Args:…, Determines exposure time by finding a star near the image centre and adjusting…, Determine the optimal exposure time. Returns: Optimal exposure time in seconds., StellarExposureTimeProvider (+29 more)

### Community 50 - "StarExpTimeEstimator"
Cohesion: 0.07
Nodes (25): Exposure Time estimators doc, ExpTimeEstimator (exptime processor base), StarExpTimeEstimator (exptime processor), ExpTimeEstimator, Any, Estimate exposure time., Init new exposure time estimator., Any (+17 more)

### Community 51 - "xmpp/rpc.py"
Cohesion: 0.09
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

### Community 55 - "object.py"
Cohesion: 0.08
Nodes (25): ObjectClass, PydanticModel, create_object(), get_object(), get_safe_object(), PrivateAttrMixin, Any, EarthLocation (+17 more)

### Community 56 - "Publisher"
Cohesion: 0.08
Nodes (23): Any, Measures seeing on reduced images with a catalog., Creates a new seeing estimator. Args: sources: List of sources (e.g. cameras)…, Puts a new images in the DB with the given ID. Args: event: New image event…, Seeing, CsvPublisher, Any, DataFrame (+15 more)

### Community 57 - "http_request_with_retries"
Cohesion: 0.12
Nodes (31): Update tasks in background., Fetches last schedule update time., Fetch projects from backend., Fetch tasks from backend., Returns list of projects. Returns: List of projects., http_request_paginated(), http_request_with_retries(), Any (+23 more)

### Community 58 - "Unit"
Cohesion: 0.10
Nodes (29): Enumerator for canonical physical units used on the wire. Attributes: DEGREES:…, The equivalent astropy.units unit, for code that needs to build a Quantity., Unit, _extract_unit(), _interface_unit_hints(), Any, Return Unit annotations from the abstract interface declaration for method_name., Convert annotated float parameters to astropy Quantities before the method… (+21 more)

### Community 59 - "Proxy"
Cohesion: 0.09
Nodes (21): Comm responsibility: Method calls (via Proxy), Proxy, Any, Interface, Signature, Execute a method on the remote client. Args: method: Name of method to call.…, Create local methods for the remote client., Function wrapper for remote calls. Args: method: Name of method to wrap.… (+13 more)

### Community 60 - "DummyAltAzTelescope"
Cohesion: 0.12
Nodes (17): IOffsetsAltAz, AltAzOffsetState, IOffsetsAltAz, Any, DEGREES, Interface, The module supports Alt/Az offsets, usually combined with…, Move an Alt/Az offset. Args: dalt: Altitude offset in degrees. daz: Azimuth… (+9 more)

### Community 61 - "test_basevideo.py"
Cohesion: 0.16
Nodes (34): ImageRequest, make_basevideo(), make_request(), asyncio, test_activate_camera_from_inactive_calls_hook(), test_activate_camera_when_already_active_skips_hook(), test_active_update_deactivates_after_sleep_timeout(), test_active_update_skips_deactivate_when_recently_active() (+26 more)

### Community 62 - "SkyFlatsBasePointing"
Cohesion: 0.08
Nodes (23): Modules for performing flatfields. TODO: write doc, FlatFieldPointing, Any, IPointingAltAz, IRunnable, Module for pointing a telescope., Initialize a new flat field pointing. Args: telescope: Telescope to point…, Move telescope to pointing. (+15 more)

### Community 63 - "test_csvpicker_scheduler.py"
Cohesion: 0.25
Nodes (20): make_dynamic_task(), make_vfs(), asyncio, integration, Path, CsvPicker filters out targets that fail the airmass constraint., OnDemandScheduler resolves DynamicTarget via CsvPicker to a SiderealTarget., Scheduler produces no observations when all CSV targets are invisible. (+12 more)

### Community 64 - "FlatFielder"
Cohesion: 0.09
Nodes (21): FlatFielder, Enum, ICamera, IFilters, ITelescope, Calls next step in state machine. Args: telescope: Telescope to use. camera:…, Returns True, if functions are based on filters., Do a quick initial check. Returns: False, if flat-field time for this filter is… (+13 more)

### Community 65 - "IExposure"
Cohesion: 0.06
Nodes (34): Comm._get_client, ADR-0001: Check Interface.state by own declaration, not inheritance, Composite interfaces inheriting stateful bases (ICamera, IDome, ITelescope, ...), Interface.capabilities (ClassVar), Interface.has_own_state(), Interface.state (ClassVar), XmppComm disco#info feature registration, ADR-0006: Proxy.wait_for_state() returns None on timeout (+26 more)

### Community 66 - "Telegram"
Cohesion: 0.13
Nodes (19): CallbackContext, Any, Save storage file. Args: context: Telegram context., Is user authorized? Args: context: Telegram context. user_id: ID of user.…, Store new user in auth database. Args: context: Telegram context. user_id: ID…, Handle /start command. Args: update: Message to process. context: Telegram…, Handle /exec command. Args: update: Message to process. context: Telegram…, Handle click on buttons. Args: update: Message to process. context: Telegram… (+11 more)

### Community 67 - "benchmark_state_throughput.py"
Cohesion: 0.10
Nodes (37): Open the connection to the XMPP server. Returns: Whether opening was successful., Return cached presence state for a connected module., ModuleState, Enumerator for module states. Attributes: CLOSED: Module is closed. STARTING:…, attach_module(), env_config(), main(), make_comm() (+29 more)

### Community 68 - "LcoScript"
Cohesion: 0.10
Nodes (15): LcoAutoFocusScript, Auto focus script for LCO configs., Whether this config can currently run. Returns: True, if the script can run now, Run script. Raises: InterruptedError: If interrupted, # TODO: unfortunately this never happens, since the LCO portal forces…, LcoDefaultScript, Returns FITS header for the current status of this module. Args: namespaces: If…, Default script for LCO configs. (+7 more)

### Community 69 - "Offsets"
Cohesion: 0.08
Nodes (24): OnSkyDistance, Angle, PixelOffsets, AstrometryOffsets, CorrelationMaxCloseToBorderError, Exception, SkyCoord, Compute pixel offsets from WCS by comparing image reference coordinates to… (+16 more)

### Community 70 - ".now"
Cohesion: 0.10
Nodes (29): Observer, TaskSuccess, ObservationArchiveEvolution, date, Observer, Populates the task cache and the one real night (anchored to `start`) up front.…, Freezes observation cache. After this: a task-id miss raises RuntimeError; a…, Returns list of observations for the given task. Args: date: Date of night to… (+21 more)

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
Nodes (30): model_validator, Self, SkyCoord, Target, SiderealTarget, make_merit(), asyncio, transit_time should be jd0 + n*period for integer n closest to now. (+22 more)

### Community 75 - "PyobsDaemon"
Cohesion: 0.06
Nodes (28): CLI, Initializes a new instance of the CLI class., Overwrite this to set CLI parameters with argparse., Overwrite this to actually run the CLI., Load config from config file, Load config from environment variables., main(), Any (+20 more)

### Community 76 - "MockWeather"
Cohesion: 0.14
Nodes (22): MockWeather, Any, IFitsHeaderBefore, IWeather, Returns FITS header for the current status of this module. Args: namespaces: If…, A mock weather station for testing and simulations., Creates a new mock weather station. Args: good: Initial weather-good state.…, Set the simulated weather-good state, for use in tests and simulations. Fires a… (+14 more)

### Community 77 - "test_config.py"
Cohesion: 0.10
Nodes (31): include_parts(), pre_process_yaml(), Any, Replaces blocks of the form {include <source.yaml> <key>} in the loaded config…, Include nested contents from another YAML file. Args: include: dictionary based…, Finds anchors ('&') in the included file. Args: filename: name of the file with…, Replaces aliases ('<<: *...') in the main file by the anchor in the included…, reload_anchors() (+23 more)

### Community 78 - "Pipeline"
Cohesion: 0.12
Nodes (19): Pipeline, Any, Create master bias frame. Args: images: List of raw bias frames. Returns:…, Create master dark frame. Args: images: List of raw dark frames. bias: Bias…, Create master flat frame. Args: images: List of raw flat frames. bias: Bias…, Calibrate a single science frame. Args: image: Image to calibrate. Returns:…, Pipeline based on the astropy package ccdproc., Pipeline for science images. Args: steps: List of pipeline steps to perform.… (+11 more)

### Community 79 - "test_autoguiding.py"
Cohesion: 0.20
Nodes (32): make_guiding(), make_image(), asyncio, _state_for(), test_auto_guiding_sleeps_when_disabled(), test_auto_guiding_takes_and_processes_image_when_enabled(), test_get_fits_header_after_includes_statistics(), test_get_fits_header_before_reports_closed_loop() (+24 more)

### Community 80 - "Weather"
Cohesion: 0.10
Nodes (29): Any, IFitsHeaderBefore, IWeather, Builds the current per-sensor readings from the last raw status, for state…, Returns FITS header for the current status of this module. Args: namespaces: If…, Connection to pyobs-weather., Initialize a new pyobs-weather connector. Args: url: URL to weather station…, Weather (+21 more)

### Community 81 - "SolarElevationConstraint"
Cohesion: 0.17
Nodes (27): AtNightConstraint, Solar elevation constraint., SolarElevationConstraint, constraint(), data(), observer(), asyncio, fixture (+19 more)

### Community 82 - "SkyOffsets"
Cohesion: 0.10
Nodes (22): BaseCoordinateFrame, Angle, SkyCoord, Returns separatation between both coordinates, either in their own or a given…, Calculates spherical offset from first coordinate to second. Args: frame:…, Args: frame: Coordinate frame to use, or None to use coordinates' own frames.…, SkyOffsets, DummySkyOffsets (+14 more)

### Community 83 - "Image (images)"
Cohesion: 0.11
Nodes (13): ImageHDU, Any, floating, HDUList, Header, NDArray, setter, Table (+5 more)

### Community 84 - "test_schedulewriter.py"
Cohesion: 0.12
Nodes (24): InstrumentLocation, ConfigDB, LcoScheduleWriter, Any, Scheduler for using the LCO portal, Creates a new LCO scheduler. Args: portal: Portal to use. configdb: ConfigDB to…, Add the list of scheduled tasks to the schedule. Args: tasks: Scheduled tasks., Clear schedule after given start time. Args: start_time: Start time to clear… (+16 more)

### Community 85 - "Ring"
Cohesion: 0.14
Nodes (9): integer, Any, floating, NDArray, Estimate pixel guiding offsets from asymmetry of spilled light around a fiber…, Init an image processor that adds the calculated offset. Args: fibers:…, Processes an image and sets x/y pixel offset to reference in offset attribute.…, Ring (+1 more)

### Community 86 - "DummySolarTelescope"
Cohesion: 0.07
Nodes (35): IPointingHelioprojective, HeliocentricPolarState, IPointingHeliocentricPolar, Any, DEGREES, Interface, The module can move to Heliocentric Polar (Mu/Psi) coordinates, usually…, Moves on given coordinates. Args: mu: Cosine of the angular distance from Sun… (+27 more)

### Community 87 - "xmppcomm.py"
Cohesion: 0.07
Nodes (26): Any, Disconnect only, instead of slixmpp's default reconnect-in-place. xep_0199's…, Called when the server sends a <stream:error/>, e.g. when this connection gets…, Whether this client was (or is being) kicked because another session connected…, Human-readable reason text sent alongside the conflict stream error, if any., Wait for client to connect. Returns: Success or not., XMPP client for pyobs., Session start event. Args: event: The event sent at session start. (+18 more)

### Community 88 - "test_backend_archives.py"
Cohesion: 0.21
Nodes (30): make_obs(), make_obs_archive(), make_task(), make_task_archive(), asyncio, time parameter is unused — backend returns cached observations., Backend uses strictly exclusive boundaries (start < time < end)., fetch_task is called with task_archive when provided. (+22 more)

### Community 89 - "DummyCamera"
Cohesion: 0.10
Nodes (13): ICooling, IGain, IImageFormat, DummyCamera, Any, Header, IBinning, IWindow (+5 more)

### Community 90 - "Application"
Cohesion: 0.15
Nodes (23): Application, React to signals and quit the module., Class for initializing and shutting down a pyobs process., make_bare_application(), Any, asyncio, Tests for Application's module_factory path (see specs/plans/gui-interactive-…, Config path: _module is already set in __init__, so _main() must not touch the… (+15 more)

### Community 91 - "DummyComm"
Cohesion: 0.09
Nodes (21): Creates a comm module., DummyComm, Any, Interface, A dummy implementation of the Comm interface., Creates a new dummy comm. Args: name: Name to report for this comm. Defaults to…, Always return zero clients., No interfaces implemented. (+13 more)

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

### Community 96 - "PillowHelper"
Cohesion: 0.11
Nodes (16): Additional Modules index (docs), Image processors index (docs), Annotation processors doc, Calibration processors doc, Draws a circle on the image. Args: image: Image to draw on. Returns: Output…, Crosshair, Any, Drawn a crosshair on the image. Args: image: Image to draw on. Returns: Output… (+8 more)

### Community 97 - "application.py"
Cohesion: 0.13
Nodes (14): _disable_iers_auto_download(), GuiApplication, InfluxLogConfig, Any, TypedDict, Derived Application class that uses a Qt GUI. Allows for graceful shutdown in…, Create a new GUI application., Initializes a pyobs application. Exactly one of `config`/`module_factory` must… (+6 more)

### Community 98 - "FocusSeries"
Cohesion: 0.08
Nodes (28): AutoFocusPoint, fit_hyperbola(), Fit a hyperbola Args: x_arr: X data y_arr: Y data y_err: Y errors Returns:…, FocusSeries, Analyse given image. Args: image: Image to analyse focus_value: Value to fit…, Returns a list of data points., Fit focus from analysed images Returns: Tuple of new focus and its error, Base class for focus series helper classes. (+20 more)

### Community 99 - "BaseGuiding"
Cohesion: 0.09
Nodes (18): IFitsHeaderAfter, AutoGuiding, Any, An auto-guiding system., Initializes a new auto guiding system. Args: exposure_time: Initial exposure…, Set the exposure time in seconds. Args: exposure_time: Exposure time in…, Starts/resets auto-guiding., BaseGuiding (+10 more)

### Community 100 - "make_proxy_cm"
Cohesion: 0.21
Nodes (27): make_proxy_cm(), Wrap value in a MagicMock standing in for the async context manager returned by…, make_flatfield(), asyncio, Find the state object set_state() was called with for the given interface., _ready_telescope(), _state_for(), test_abort_sets_event() (+19 more)

### Community 101 - "_AbortableModule"
Cohesion: 0.25
Nodes (21): Callback for flat-field class to call with statistics., FocusError, _AbortableModule, asyncio, IAbortable, Minimal test module whose abort() raises whatever exception it's given. Starts…, test_call_id_is_attached_to_the_exception_and_included_in_the_log_line(), test_call_id_omitted_from_log_line_when_not_given() (+13 more)

### Community 102 - "ScriptRunner"
Cohesion: 0.13
Nodes (16): calc_run_timeout(), Any, IRunnable, Calculates timeout for run()., Module for running a script., Initialize a new script runner. Args: script: Config for script to run., Run script. Raises: ScriptError: If the script failed (e.g. a proxy/network…, Abort current actions. (+8 more)

### Community 103 - "LcoScheduleReader"
Cohesion: 0.09
Nodes (18): LcoScheduleReader, Any, Update list of requests. Args: force: Force update., Fetch schedule from portal. Returns: Dictionary with tasks. Raises: Timeout: If…, Fetch schedule from portal. Args: start_before: Task must start before this…, Returns the active scheduled task at the given time. Args: time: Time to return…, Scheduler for using the LCO portal, Creates a new LCO scheduler. Args: url: URL to portal site: Site filter for… (+10 more)

### Community 104 - "test_coordinates.py"
Cohesion: 0.15
Nodes (25): offset_altaz_to_radec(), offset_radec_to_altaz(), EarthLocation, SkyCoord, make_altaz(), make_radec(), SkyCoord, Zero offset returns (0, 0). (+17 more)

### Community 105 - "get_registered_interface"
Cohesion: 0.12
Nodes (22): get_registered_interface(), Look up a registered interface class by name, or None if unknown., All currently-registered interface classes, keyed by name., registered_interfaces(), Tests for the import-time interface registry in pyobs/interfaces/interface.py.…, Re-importing the same interface module twice resolves to the same class object…, Two genuinely different classes claiming the same name must raise TypeError…, Mutating the returned dict must not affect the live registry. (+14 more)

### Community 106 - "Portal"
Cohesion: 0.11
Nodes (11): Portal, Any, Do a GET request on the portal. Args: url: URL to request. Returns: Response…, Clear schedule after given start time. Args: start: Start time to clear…, Submit observations. Args: observations: List of observations to submit., Send report to LCO portal Args: status_id: id of config status status: Status…, Delay re-attempt to send report to LCO portal Args: status_id: id of config…, Fetch schedule from portal. Args: start_before: Task must start before this… (+3 more)

### Community 107 - "LocalArchive"
Cohesion: 0.33
Nodes (25): LocalArchive, Connector class to a local image archive., make_frame_headers(), asyncio, Path, test_download_frames_loads_real_files(), test_download_frames_skips_frames_without_filename(), test_download_headers_returns_header_dicts() (+17 more)

### Community 108 - "_AbortableModule"
Cohesion: 0.10
Nodes (21): _AbortableModule, Any, asyncio, IAbortable, IStartStop, parametrize, Minimal test module with one guarded (non-whitelisted) RPC method., Module implementing IStartStop, whose abstract `start(**kwargs)` RPC method has… (+13 more)

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
Cohesion: 0.15
Nodes (20): BackgroundTask, Any, Add a new function that should be run in the background. MUST be called in…, make_task(), asyncio, Too many fast failures calls parent.quit() when restart=True., Too many fast failures with restart=False just stops without calling quit., Failures spread over time don't trigger the rapid-failure quit. (+12 more)

### Community 113 - "Test Commlogging (comm)"
Cohesion: 0.12
Nodes (20): Send an event to all connected modules. Args: event: Event to send.…, CommLoggingHandler, Any, A logging handler that sends all messages through a Comm module., Create a new logging handler. Args: comm: Comm module to use., Send a new log entry to the comm module. Args: rec: Log record to send., comm(), handler() (+12 more)

### Community 114 - "MotionStatusChangedEvent"
Cohesion: 0.07
Nodes (16): Any, JSON representation of event., String representation of event., Generic from_dict method for derived classes that don't need their own., Any, Any, Any, Any (+8 more)

### Community 115 - "WeatherApi"
Cohesion: 0.19
Nodes (10): Any, ClientSession, WeatherApi, MockResponse, Any, asyncio, test_get_current_status(), test_get_sensor_value() (+2 more)

### Community 116 - "ImagingScript"
Cohesion: 0.17
Nodes (8): ImagingScript, Any, Target, Run script. Raises: InterruptedError: If interrupted, Returns FITS header for the current status of this module. Args: namespaces: If…, Return the exposure time, computing it dynamically if needed., Default script for imaging configs., Whether this config can currently run. Returns: True, if the script can run now

### Community 117 - "LcoTaskArchive"
Cohesion: 0.15
Nodes (9): LcoTaskArchive, Any, Returns a list of schedulable tasks and projects Returns: List of schedulable…, Scheduler for using the LCO portal, Creates a new LCO scheduler. Args: url: URL to portal token: Authorization…, Returns time when last time any tasks changed., Returns list of projects from the LCO portal., Returns list of schedulable tasks. Returns: List of schedulable tasks (+1 more)

### Community 118 - "MemoryFile"
Cohesion: 0.14
Nodes (9): MemoryFile, Any, A file stored in memory., Open/create a file in memory. Args: name: Name of file. mode: Open mode., Read number of bytes from stream. Args: n: Number of bytes to read, -1 reads…, Write data into the stream. Args: buf: Bytes of data to write., Whether stream is closed., asyncio (+1 more)

### Community 119 - "VFSFile"
Cohesion: 0.08
Nodes (15): Any, Returns content of given path. Args: path: Path to list. kwargs: Parameters for…, Find files by pattern matching. Args: path: Path to search in. pattern: Pattern…, Remove file at given path. Args: path: Path of file to delete. Returns: Success…, Base class for all VFS file classes., Checks, whether a given path or file exists. Args: path: Path to check.…, VFSFile, __getattr__() (+7 more)

### Community 120 - "LocalFile"
Cohesion: 0.13
Nodes (15): LocalFile, Any, Find files by pattern matching. Args: path: Path to search in. pattern: Pattern…, Wraps a local file with the virtual file system., Remove file at given path. Args: path: Path of file to delete. Returns: Success…, Checks, whether a given path or file exists. Args: path: Path to check. root:…, Open a local file. Args: name: Name of file. mode: Open mode. root: Root to…, Returns local path of given path. Args: path: Path to list. kwargs: Parameters… (+7 more)

### Community 121 - "test_version_mismatch.py"
Cohesion: 0.13
Nodes (24): FakeInterface, make_xmpp_comm(), asyncio, LogCaptureFixture, Tests for the mixed-version-fleet diagnostic on interface resolution. Covers…, Base Comm._diagnose_missing_interface returns None -- e.g. LocalComm, which…, Sanity check that ICooling/IModule (used above as real interfaces) still have…, Stand-in for a pyobs Interface class -- only __name__ and .version matter here. (+16 more)

### Community 122 - "CLAUDE.md (repo guide)"
Cohesion: 0.10
Nodes (23): check_coverage.md (coverage gap survey), Coverage Category A: needs live external service/credentials, Coverage Category B: GUI widgets needing a display, Coverage Category C: CLI/app bootstrap, Coverage Category D: dev/test-support tooling, Coverage Category E: real gaps, no external-service/GUI excuse, Cross-repo docs convention (Repos: line + specs/README.md pointer), graphify usage rules for this repo (+15 more)

### Community 123 - "comm.py"
Cohesion: 0.27
Nodes (4): The Comm object is responsible for all communication between modules (see…, _ProxyContext, ProxyType, Returned by Comm.proxy() / Object.proxy() / Comm.safe_proxy(). Must be used as:…

### Community 124 - "FocusModel"
Cohesion: 0.08
Nodes (30): IFocusModel, FocusModel, Any, DataFrame, floating, NDArray, Initialize a focus model. Args: focuser: Name of focuser. weather: Name of…, Returns the optimal focus. Args: filter_name: If given, use this filter name… (+22 more)

### Community 125 - "TaskFinishedEvent"
Cohesion: 0.10
Nodes (13): Any, Event to be sent when a task has failed., Initializes a new task failed event. Args: name: Name of task that just…, TaskFailedEvent, Any, Event to be sent when a task has finished., Initializes a new task finished event. Args: name: Name of task that just…, TaskFinishedEvent (+5 more)

### Community 126 - "ImageSourceFilter"
Cohesion: 0.12
Nodes (17): ImageSourceFilter, Any, floating, NDArray, Table, Filters the source table after pysep detection has run Args:…, Filter a source catalog by border distance, quality metrics, and brightness,…, Convert from FITS to numpy conventions for pixel coordinates. (+9 more)

### Community 127 - "test_darkbias.py"
Cohesion: 0.23
Nodes (19): DarkBiasScript, Script for running darks or biases., Whether this config can currently run. Returns: True if script can run now., Run script. Raises: InterruptedError: If interrupted, make_camera(), make_script(), asyncio, Create a mock camera supporting all or some interfaces. (+11 more)

### Community 128 - "test_config_schema.py"
Cohesion: 0.20
Nodes (22): ConfigFieldSchema, ConfigSchema, dataclass_to_schema(), _field_schema(), Any, _pydantic_field_schema(), pydantic_to_schema(), Recursively derive a ConfigSchema from a dataclass type. Handles: plain scalars… (+14 more)

### Community 129 - "GridNode"
Cohesion: 0.17
Nodes (9): ConvertGridToSkyCoord, Convert (x, y) degree tuples to SkyCoord objects. Wraps a tuple-producing grid…, GridNode, Log the last yielded point, if any. Implementations typically delegate to…, Abstract base class for grid nodes. A GridNode implements the Python iterator…, Return iterator self. Returns: The GridNode itself as an iterator., Return the number of points remaining. Returns: Number of points remaining to…, Append the last yielded point back to the underlying sequence. This can be used… (+1 more)

### Community 130 - "lco/taskrunner.py"
Cohesion: 0.22
Nodes (7): LcoTaskRunner, Any, Target, Creates a new LCO task runner. Args: scripts: External scripts, Run a task. Args: task: Task to run target: Resolved target for this specific…, Checks whether this task could run now. Args: task: Task to run target:…, Get config script for given configuration. Args: request: LCO request. Returns:…

### Community 131 - "Test Localcomm (local)"
Cohesion: 0.18
Nodes (22): make_comm(), asyncio, fixture, Sender also receives its own events., Reset LocalNetwork singleton between tests., #677: a late-joining module must announce itself via ModuleOpenedEvent once…, get_interfaces returns [] when the remote client has no module., reset_network() (+14 more)

### Community 132 - "GoodWeatherEvent"
Cohesion: 0.11
Nodes (15): Comm API doc (pyobs.comm), Events API doc (pyobs.events), ExposureStatusChangedEvent, Any, Event to be sent, when the exposure status of a device changes., GoodWeatherEvent, Any, Event to be sent on good weather. (+7 more)

### Community 133 - "module.py"
Cohesion: 0.08
Nodes (14): ConfigCapabilities, A module in *pyobs* is the smalles executable unit. The base class for all…, MultiModule, Wait until all sub-module tasks have finished., Cancel sub-module tasks and close shared objects., Quit all sub-modules., Returns pyobs version of module., React to other modules connecting. (+6 more)

### Community 134 - "test_dummymode.py"
Cohesion: 0.10
Nodes (27): IMode, IMode, ModeCapabilities, ModeState, Any, Interface, The module can change modes in a device., Set the current mode. Args: mode: Name of mode to set. group: Name of the group… (+19 more)

### Community 135 - "test_dummyradectelescope.py"
Cohesion: 0.24
Nodes (21): TrackingRateCapabilities, make_dummyradectelescope(), asyncio, test_move_altaz_clears_tracked_body(), test_move_altaz_resets_tracking_mode_to_off(), test_move_radec_clears_tracked_body(), test_move_radec_resets_tracking_mode_to_sidereal(), test_move_task_applies_tracking_rate_to_position() (+13 more)

### Community 136 - "IRunning.py"
Cohesion: 0.10
Nodes (24): F, AutoFocusResult, AutoFocusState, DummyAutoFocus, Any, IAutoFocus, Abort current actions., Dummy class for auto-focusing a telescope. (+16 more)

### Community 137 - "test_autofocus.py"
Cohesion: 0.20
Nodes (21): AutoFocusScript, Script for running autofocus series., Whether this config can currently run. Returns: True if script can run now., isinstance_class(), Shared test-double helpers used across multiple test modules., Build a fresh class purely for isinstance() checks against a MagicMock.…, make_autofocus(), make_script() (+13 more)

### Community 138 - "Grid"
Cohesion: 0.09
Nodes (19): AvoidMoon, GridFilter, Any, Initialize the conversion filter. Args: grid: Upstream grid or filter that…, Abstract base class for grid filters that wrap another GridNode. A GridFilter…, Initialize the frame conversion filter. Args: grid: Upstream grid or filter…, Initialize the randomizer. Args: grid: Upstream grid or filter. iterations:…, Initialize a filter with an underlying grid. Args: grid: The upstream GridNode… (+11 more)

### Community 139 - "test_kiosk.py"
Cohesion: 0.24
Nodes (21): _cancel_after(), _make_image(), make_kiosk(), asyncio, Side effect that raises CancelledError starting from the n-th call., test_camera_thread_captures_and_adjusts_exposure_time(), test_camera_thread_clips_exposure_time_to_minimum(), test_camera_thread_continues_on_file_not_found() (+13 more)

### Community 140 - "pyobs.py"
Cohesion: 0.21
Nodes (9): main(), Any, PyobsCLI, Start process as a daemon. Args: pid_file: Name of PID file., Class for initializing and running pyobs CLI., main(), Any, PyobsWinCLI (+1 more)

### Community 141 - "Robotic recipe (doc)"
Cohesion: 0.17
Nodes (21): pyobs.modules.robotic (doc), Mastermind (module), PointingSeries, Scheduler (module), ScriptRunner, Robotic recipe (doc), AirmassConstraint, BackendObservationArchive (+13 more)

### Community 142 - "is_valid_jid"
Cohesion: 0.14
Nodes (9): is_valid_jid(), Whether jid is a valid user@domain or user@domain/resource JID -- exactly what…, asyncio, JID parsing/validation in XmppComm.__init__ and the reusable is_valid_jid()…, The actual production bug this was found from: a JID ending in "/" with nothing…, re.match alone doesn't anchor the end -- confirms the pattern is anchored so…, async def, not plain def -- XmppComm.__init__ calls asyncio.get_event_loop(),…, TestIsValidJid (+1 more)

### Community 143 - "OffsetResult"
Cohesion: 0.12
Nodes (21): OffsetFrame, Coordinate frame an offset is expressed in, whichever the mount supports.…, ApplyAltAzOffsets, EarthLocation, ITelescope, Apply offsets from a given image to a given telescope., Take the pixel offsets stored in the meta data of the image and apply them to…, ApplyOffsets (+13 more)

### Community 144 - "test_dummyvideo.py"
Cohesion: 0.16
Nodes (16): DummyVideo, Any, IExposureTime, A dummy video module for testing — streams simulated noise frames., Creates a new dummy video module. Args: fps: Frames per second to simulate.…, Set the exposure time (frame interval). Args: exposure_time: Exposure time in…, Background task that generates simulated frames., make_dummyvideo() (+8 more)

### Community 145 - ".__init__"
Cohesion: 0.20
Nodes (7): Any, Abort current actions., Create a new acquisition. Args: exposure_time: Default exposure time.…, Any, ICamera, ITelescope, Initializes a new base pointing. Args: telescope: Telescope to use. pipeline:…

### Community 146 - "Scheduler"
Cohesion: 0.13
Nodes (9): Any, IRunnable, IStartStop, Compares two lists of tasks and returns two lists, containing those that are…, Trigger a re-schedule., Re-schedule when task has started and we can predict its end. Args: event: The…, Reset current task, when it has finished or failed. Args: event: The task…, Re-schedule on incoming good weather event. Args: event: The good weather… (+1 more)

### Community 147 - "RollingTimeAverage"
Cohesion: 0.10
Nodes (24): Any, Runs an async callable to completion on a dedicated worker thread, off the…, run_cpu_bound(), RollingTimeAverage, _T, asyncio, test_run_cpu_bound_propagates_exception(), test_run_cpu_bound_returns_value() (+16 more)

### Community 148 - "test_localcomm_state.py"
Cohesion: 0.09
Nodes (28): asyncio, fixture, Tests for LocalComm state, capabilities, and presence., set_presence stores and get_client_state retrieves., Default presence is READY with no error string., subscribe_presence fires callback immediately with the current presence state., subscribe_presence callback is called whenever presence changes., Reset LocalNetwork singleton before each test. (+20 more)

### Community 149 - "RegularSphericalGrid"
Cohesion: 0.31
Nodes (8): GraticuleSphericalGrid, Grid over a sphere using regular longitude/latitude sampling. Produces points…, Grid with approximately equidistributed points on a sphere. Uses a graticule-…, RegularSphericalGrid, Reinsert one point back into the grid., test_graticulesphericalgrid(), test_regularsphericalgrid(), test_regularsphericalgrid_append_last()

### Community 150 - "Plan: pyobs 2.0 rollout (work plan)"
Cohesion: 0.10
Nodes (21): XmppComm._register_events add_interest (XEP-0163), LogEvent Double-Delivery Investigation (SAAO/monet), Root cause: dual PEP delivery paths (implicit roster + explicit interest), XmppComm._safe_send retry-on-timeout (ruled out), AstrometryDotNet migrated to handle_error, Plan: Per-step error control in image processing pipelines, ExceptionHandler nested wrapper (#328, rejected), on_error kwarg + handle_error() override point (+13 more)

### Community 151 - "test_lcoscript.py"
Cohesion: 0.17
Nodes (18): FakeScript, make_lco_script(), make_request(), Any, asyncio, Minimal script used to verify LcoScript's dispatch., can_run() resolves and delegates to the script named in…, run() delegates to the named script and copies its exptime_done back. (+10 more)

### Community 152 - "3rd party packages (doc)"
Cohesion: 0.11
Nodes (20): 3rd party packages (doc), Astroplan, Astropy, Astroquery, Cython, LMFIT, matplotlib, NumPy (+12 more)

### Community 153 - "Any"
Cohesion: 0.13
Nodes (10): Any, Interface, Store capabilities locally., Return this client's own published capabilities., Fetch capabilities from a remote module., Returns list of interfaces for given client., Checks whether the given client supports the given interface., Execute a given method on a remote client. (+2 more)

### Community 154 - "BufferedFile"
Cohesion: 0.09
Nodes (14): BufferedFile, Base class for all byffered VFS file classes., Any, VFS wrapper for a file that can be accessed over a SFTP connection., Write data into the stream. Args: b: Bytes of data to write., If in write mode, actually send the file to the SSH server., Returns content of given path. Args: path: Path to list. kwargs: Parameters for…, Open/create a file over a SSH connection. Args: name: Name of file. mode: Open… (+6 more)

### Community 155 - "create_rst.py"
Cohesion: 0.33
Nodes (18): create_image_processors_rst(), create_modules_rst(), create_rst_overview(), create_utils_rst(), find_classes_in_modules(), find_python_modules(), find_submodules(), Any (+10 more)

### Community 156 - "GuidingStatistics"
Cohesion: 0.12
Nodes (11): IN, OUT, GuidingStatistics, Any, Calculates statistics for guiding., Inits a stat measurement session for a client. Args: client: name/id of the…, Add statistics to given header. Args: client: id/name of the client header:…, Adds data to all client measurement sessions. Args: input_data: Image witch… (+3 more)

### Community 157 - "SoftBin"
Cohesion: 0.16
Nodes (11): Any, floating, NDArray, Bin a 2D image by averaging non-overlapping blocks, updating relevant FITS…, Init a new software binning pipeline step. Args: binning: Binning to apply to…, Bin an image. Args: image: Image to bin. Returns: Binned image., SoftBin, asyncio (+3 more)

### Community 158 - "AddMask"
Cohesion: 0.21
Nodes (13): AddMask, Any, floating, NDArray, Add mask to image. Args: image: Image to add mask to. Returns: Image with mask, Attach a precomputed mask to an image based on instrument and binning. This…, Init an image processor that adds a mask to an image. Args: masks: Dictionary…, asyncio (+5 more)

### Community 159 - "Archive"
Cohesion: 0.13
Nodes (11): Archive, FrameInfo, Any, Base class for frame infos., Base class for image archives., TypedDict, PyobsArchiveFrameInfoDict, Find and download master calibration frame. Args: archive: Image archive.… (+3 more)

### Community 160 - "RandomizeGrid"
Cohesion: 0.12
Nodes (11): SkyCoord, RandomizeGrid, Return the next point that satisfies all constraints. Iterates underlying…, Convert the next tuple to a SkyCoord. Expects a tuple (x_deg, y_deg) from the…, Transform the next SkyCoord to the target frame. Returns: A SkyCoord…, Randomize iteration order by rotating the underlying sequence. For each…, Yield a point after rotating the underlying grid a random number of times.…, Yield a point after rotating the underlying grid a random number of times.… (+3 more)

### Community 161 - "comm/test_events.py"
Cohesion: 0.18
Nodes (15): asyncio, Tests for Comm.register_event / unregister_event. Covers…, Two independent subscribers for the same event: one tearing down must not un-…, A module that both sends an event (handler-less register_event()) and…, unregister must mirror the exact same derived-events expansion register_event…, Two independent subscribers (e.g. two widget instances for the same event type)…, Once the last handler for an event is unregistered, the event must no longer be…, test_unregister_event_drops_subscribed_role_when_last_handler_removed() (+7 more)

### Community 162 - "BrightestStarOffsets"
Cohesion: 0.18
Nodes (13): BrightestStarOffsets, Angle, Any, Table, Processes an image and sets x/y pixel offset to reference in offset attribute.…, Compute pixel offsets from the image center to the brightest star and store…, Initializes a new auto guiding system., asyncio (+5 more)

### Community 163 - "pyobs/modules/utils/__init__.py"
Cohesion: 0.10
Nodes (7): FluentLogger, Log to fluentd server., Process a new log entry. Args: event: The log event. sender: Name of sender., Utilities TODO: write doc, Matrix, Drain the message queue and send messages one at a time. Sending sequentially…, Process a new log entry. Args: entry: The log event. sender: Name of sender.

### Community 164 - "test_imagewriter.py"
Cohesion: 0.19
Nodes (16): ImageWriter, Any, Writes new images to disk., Creates a new image writer. Args: filename: Pattern for filename to store…, Puts a new images in the DB with the given ID. Args: event: New image event…, make_image_event(), make_writer(), asyncio (+8 more)

### Community 165 - "ExpTimeEval"
Cohesion: 0.10
Nodes (17): ExpTimeEval, Any, Observer, Return list of binnings., Return list of filters., Estimate exposure time for given filter Args: solalt: Solar altitude. binning:…, Initialize object with the given time. Args: time: Start time for all further…, Estimates exposure time for a given filter and binning at a given time offset… (+9 more)

### Community 166 - "Stellarium"
Cohesion: 0.18
Nodes (6): BaseTransport, Exception, Send coordinates to clients., A stellarium telescope., Stellarium, StellariumProtocol

### Community 167 - "Overview (doc)"
Cohesion: 0.18
Nodes (17): Overview (doc), Access control (ACL), Comm, Events, Interface, Module (base class), Object (base class), Location / astroplan.Observer (+9 more)

### Community 168 - "SepSourceDetection"
Cohesion: 0.16
Nodes (17): Background, Any, floating, NDArray, Initializes a wrapper for SEP. See its documentation for details. Highly…, Find stars in given image and append catalog. Args: image: Image to find stars…, Remove background from image in data. Args: data: Data to remove background…, Detect astronomical sources using SEP (Source Extractor for Python). This… (+9 more)

### Community 170 - "_CalibrationCache"
Cohesion: 0.18
Nodes (9): _CalibrationCache, Any, Init a new image calibration pipeline step. Args: archive: Archive to fetch…, mock_image(), fixture, test_add_to_cache(), test_add_to_cache_size(), test_find_cache_entry_emtpy() (+1 more)

### Community 171 - "RunningState"
Cohesion: 0.08
Nodes (19): RunningState, Any, Returns FITS header for the current status of this module. Args: namespaces: If…, Kiosk, Any, ICamera, IStartStop, Response (+11 more)

### Community 172 - "test_grab_sequence.py"
Cohesion: 0.29
Nodes (16): make_camera(), asyncio, Tests for BaseCamera.grab_sequence()/abort_sequence(), the IDataSequence…, grab_sequence() must not block for the whole sequence -- see design doc: a…, test_abort_clears_running_sequence(), test_abort_cuts_delay_short(), test_abort_sequence_cuts_delay_short(), test_abort_sequence_lets_current_grab_finish_but_stops_the_rest() (+8 more)

### Community 173 - "binding.py"
Cohesion: 0.23
Nodes (8): fault2xml(), py2xml(), Any, Element, rpcbase64, rpctime, xml2fault(), xml2py()

### Community 174 - "NewSpectrumEvent"
Cohesion: 0.14
Nodes (11): NewSpectrumEvent, Any, Event to be sent on a new image., Initializes new NewSpectrumEvent. Args: filename: Name of new image file., HDUList, Store spectrum at given destination. Can be overwritten by derived classes to…, Actually do the exposure, should be implemented by derived classes. Args:…, Wrapper for a single exposure. Args: broadcast: Whether or not the new image… (+3 more)

### Community 175 - "OptimalFocusState"
Cohesion: 0.11
Nodes (18): IFilters, Any, IMotion, The module can change filters in a device., Set the current filter. Args: filter_name: Name of filter to set. Raises:…, IFocusModel, OptimalFocusState, Any (+10 more)

### Community 176 - "test_istructuredconfig.py"
Cohesion: 0.18
Nodes (13): ConfigAppliedState, DummyConfig, DummyStructuredConfigModule, Any, asyncio, fixture, Tests for IStructuredConfig capabilities/state round-tripping through LocalComm., Reset LocalNetwork singleton before each test. (+5 more)

### Community 177 - "HttpFileCache"
Cohesion: 0.15
Nodes (9): HttpFileCache, Response, Handles OPTIONS access to /{filename} for CORS preflight requests. Args:…, Handles GET access to /{filename} and returns image. Args: request: Request to…, Handles PUSH access to /, stores image and returns filename. Args: request:…, A file cache based on a HTTP server., Whether the server is started., Raises HTTPUnauthorized if a token is configured and the request doesn't carry… (+1 more)

### Community 178 - "_SepAperturePhotometry"
Cohesion: 0.15
Nodes (11): Any, floating, NDArray, Table, since SEP sums up whole pixels, we need to do the same on an image of ones for…, _SepAperturePhotometry, asyncio, fixture (+3 more)

### Community 179 - "Scheduler"
Cohesion: 0.12
Nodes (12): Observer, Iterator for scheduler items, Iterate over scheduler items, Return schedule item., Find a possible slot for a given filter/binning in the given schedule Args:…, Checks, whether a new scheduler item would overlap an existing item Args:…, Scheduler for taking flat fields, Initializes a new scheduler for taking flat fields Args: functions: Flat field… (+4 more)

### Community 180 - "Plan: Split archive prefetch from CPU-bound merit evaluation"
Cohesion: 0.17
Nodes (16): Plan: Split archive prefetch from CPU-bound merit evaluation, FrozenObservations picklable snapshot dataclass, ObservationArchiveEvolution.prefetch()/freeze(), Plan on hold: motivating incident had different cause; premise unconfirmed, AstroplanScheduler (subprocess-isolated precedent), DataProvider @cache sun/moon/sun_altaz/moon_illumination, Plan: Stop scheduler constraint/merit evaluation from blocking the event loop, run_cpu_bound() dedicated ThreadPoolExecutor helper (+8 more)

### Community 181 - "Test Basecamera (camera)"
Cohesion: 0.18
Nodes (15): asyncio, parametrize, DummyCamera's _expose() must raise AbortedError, not some guessed builtin, when…, Test basic open/close of BaseCamera., #547: BaseCamera must abort on BadWeatherEvent., #547: a BadWeatherEvent must actually trigger abort() -- exposure + any running…, #672: a BadWeatherEvent must not interrupt a dark/bias sequence -- the shutter…, Test the methods for remaining exposure time and progress. (+7 more)

### Community 182 - "Test Imagewatcher (image)"
Cohesion: 0.33
Nodes (15): make_fits_bytes(), make_read_write_ctx(), make_watcher(), asyncio, On write failure the file is re-queued and remove is NOT called., test_add_file_queues_filename(), test_add_file_respects_pattern(), test_add_file_skips_non_matching_pattern() (+7 more)

### Community 183 - "test_schedulereader.py"
Cohesion: 0.31
Nodes (15): make_observation(), make_reader(), asyncio, Does not update if lock cannot be acquired within timeout., test_download_schedule_empty_portal_response(), test_download_schedule_returns_observations(), test_get_schedule_returns_cached_tasks(), test_get_schedule_returns_empty_initially() (+7 more)

### Community 184 - "Merit"
Cohesion: 0.15
Nodes (15): AfterTimeMerit, BeforeTimeMerit, ConstantMerit, DataProvider, FollowMerit, IntervalMerit, ObservationArchiveEvolution wraps ObservationArchive with per-run caching (avoid repeated HTTP requests) and lookahead simulation (evolve() records tentative future assignments so IntervalMerit/PerNightMerit see them and avoid double-scheduling within one run), Merit (+7 more)

### Community 185 - "ejabberd shaper throttling bug (xmpp_socket.erl re-arm) & fix"
Cohesion: 0.21
Nodes (12): XMPP/ejabberd diagnostics recipe (doc), benchmark_state_throughput.py, check_ejabberd_notify.py, delete_pubsub_nodes.py, list_pubsub_nodes.py, Comparing shaper configs (rationale), show_module_info.py, scripts/xmpp/install-ejabberd.sh (+4 more)

### Community 186 - "NewImageEvent"
Cohesion: 0.14
Nodes (9): NewImageEvent, Any, Event to be sent on a new image., Initializes new NewImageEvent. Args: filename: Name of new image file.…, test_new_image_invalid_filename(), test_new_image_no_image_type(), test_new_image_not_reduced(), test_new_image_properties() (+1 more)

### Community 187 - "FitsHeaderOffsets"
Cohesion: 0.19
Nodes (10): GenericOffset, FitsHeaderOffsets, Any, Compute a 2D offset from FITS header coordinates and store it in image…, Initializes new fits header offsets., Processes an image and sets x/y pixel offset to reference in offset attribute.…, asyncio, test_attribute_validation() (+2 more)

### Community 188 - "Interface"
Cohesion: 0.04
Nodes (64): CELSIUS, Binning, BinningCapabilities, BinningState, IBinning, Any, Interface, The camera supports binning, to be used together with… (+56 more)

### Community 189 - "CameraSettingsMixin"
Cohesion: 0.11
Nodes (15): CameraSettingsMixin, Any, IBinning, IData, IFilters, IWindow, Mixin for a device that should be able to set camera settings., Initializes the mixin. Args: filters: Filter wheel module. filter: Filter to… (+7 more)

### Community 190 - "PointingSeries"
Cohesion: 0.18
Nodes (7): PointingSeries, Any, IAutonomous, SkyCoord, Module for running pointing series., Initialize a new pointing series. Args: grid: Grid to use for pointing series.…, Run a pointing series.

### Community 191 - "GridPipeline"
Cohesion: 0.14
Nodes (9): GridPipeline, Any, Build a GridPipeline from a list of steps. Args: steps: A non-empty list where…, Return the next point from the pipeline. Returns: The next point produced by…, Return the number of points remaining in the pipeline. Returns: The length…, Append the last yielded point back to the pipeline's final stage., Log the last yielded point via the pipeline's final stage., A pipeline that composes a grid and a sequence of filters. The pipeline expects… (+1 more)

### Community 192 - "test_xmpp_rpc.py"
Cohesion: 0.19
Nodes (14): Integration tests for the pyobs 2.0 RPC payload encoding (urn:pyobs:rpc:1).…, set_binning(int, int) -> None: multiple int params, void return., Calling a method that raises on the remote side propagates the exception., set_cooling(bool, float) then verify via state: full encode/decode cycle., set_cooling(bool, float) -> None: void return with bool + float params., set_gain(float) -> None and verify via IGain state: float param, state readback., set_gain(float) then verify via IGain state: float param round-trip., test_rpc_bool_float_roundtrip() (+6 more)

### Community 193 - "Plan: Widget plugin mechanism + pyside6-deploy packaging for pyobs-gui"
Cohesion: 0.18
Nodes (14): Application(module_factory=..., loop_module_class=...), astropy.units PLY/Nuitka frame-walking incompatibility (upstream bug, patched), Rationale: module construction must happen inside the running event loop for async login dialog, keyring-based per-account password storage, keyed by stable id, LoginWindow widget (list-left/detail-right), plugin_paths: external sys.path plugin directory mechanism (Nuitka-compatible), pyobs_iagvt.widgets custom widget package (grounding real-world case), pyobs-polaris LoginWindow.qml (UX model reused) (+6 more)

### Community 194 - "What's New in pyobs 2.0 (doc)"
Cohesion: 0.15
Nodes (14): What's New in pyobs 2.0 (doc), ACL feature (2.0), Capabilities and versioned discovery, Exception handling redesign, External-package interfaces, ICamera/ISpectrograph no longer imply IExposure, IDataSequence, InvocationError / SevereError retired (+6 more)

### Community 195 - "TaskStartedEvent"
Cohesion: 0.16
Nodes (9): Any, Event to be sent when a task has started., Initializes a new task started event. Args: name: Name of task that just…, TaskStartedEvent, test_task_started_invalid_name(), test_task_started_missing_id(), test_task_started_no_eta(), test_task_started_properties() (+1 more)

### Community 196 - "ExpTime"
Cohesion: 0.15
Nodes (6): AltAzOffsets, ExpTime, RaDecOffsets, test_alt_az_offsets(), test_exp_time(), test_radecoffsets()

### Community 197 - "CatalogCircularMask"
Cohesion: 0.18
Nodes (9): CatalogCircularMask, Any, NDArray, Table, Init an image processor that masks out everything except for a central circle.…, Remove everything outside the given radius from the image. Args: image: Image…, Filter a source catalog by keeping only entries inside a central circle (or…, asyncio (+1 more)

### Community 198 - "BrightestStarGuiding"
Cohesion: 0.19
Nodes (7): BrightestStarGuiding, Any, SkyCoord, Table, Initializes a new auto guiding system., Processes an image and sets x/y pixel offset to reference in offset attribute.…, Compute guiding offsets by tracking the brightest star relative to an initial…

### Community 199 - "ImageWatcher"
Cohesion: 0.15
Nodes (9): CurrentFile, ImageWatcher, Any, Add a file to the file queue. Args: filename (str): Local filename of new file., Can be overwritten by derived classes to do extra processing on files. All…, Can be overwritten by derived classes to do clean up after successful copying.…, Watch for new files and write them to all given destinations. Watches a path…, Create a new image watcher. Args: watchpath: Path to watch. destinations:… (+1 more)

### Community 200 - ".__init__"
Cohesion: 0.10
Nodes (13): Args: label: Label for module. If None, name is used. own_comm: If True, module…, Returns name of module., List interfaces and methods of this module., Returns a dictionary with config caps., Check for getter and setter Params: name: Name of variable. Returns: Tuple of…, Returns dict of all config capabilities. First value is whether it has a…, Args: modules: Dictionary with modules. shared: Shared objects between modules., Any (+5 more)

### Community 201 - "test_filters.py"
Cohesion: 0.27
Nodes (9): ConvertGridFrame, FromList, GridFilterValue, Transform SkyCoord points to a different frame., Select closest point from a list. Only select points if they are closer than a…, Filter points by numeric constraints on x and y. Accepts points as: - (x, y)…, Any, test_fromlistfilter() (+1 more)

### Community 202 - "show_module_info.py"
Cohesion: 0.25
Nodes (13): h1(), h2(), inspect_module(), _interface_from_feature(), kv(), main(), _module_state_from_show(), ok() (+5 more)

### Community 203 - "integration/conftest.py"
Cohesion: 0.23
Nodes (13): connect(), make_camera_comm(), make_unopened_comm(), make_xmpp_comm(), fixture, Fixtures shared across all integration tests., Factory fixture: ``await make_xmpp_comm(user)`` returns an open XmppComm for…, Connect a module to LocalComm and return the comm. (+5 more)

### Community 204 - "MoveAltAzEvent"
Cohesion: 0.11
Nodes (14): DataTypeAltAz, DataTypeRaDec, MoveAltAzEvent, MoveEvent, MoveRaDecEvent, Any, TypedDict, Event to be sent when moving to RA/Dec. (+6 more)

### Community 205 - "robotic"
Cohesion: 0.32
Nodes (13): acquisition, autofocus, dome, flatfield, focuser, imagewriter, robotic, sbig6303e (+5 more)

### Community 206 - "Scheduler module"
Cohesion: 0.17
Nodes (13): Constraint (binary gate), Mastermind module, Merit (continuous ranking), Module layer (pyobs.modules.robotic: Scheduler, Mastermind — full Module subclasses with comm/background tasks) vs robotic layer (pyobs.robotic: Task, Script, Constraint, Merit, archives — Object subclasses or pydantic models, nested config, not modules); rationale: separates long-running orchestration processes from pure data/logic objects, Observation (scheduled task instance), ObservationArchive, Scheduler module, Script (observing logic) (+5 more)

### Community 207 - "BaseModel (pyobs.utils.serialization)"
Cohesion: 0.15
Nodes (13): Task (unit of work), TaskArchive, BackendTaskArchive, LcoTaskArchive, Observation, ObservationState, Task (pydantic model), TaskArchive (+5 more)

### Community 208 - "_ResponseImageWriter"
Cohesion: 0.24
Nodes (4): Any, WCS, astrometry.net gives a CD matrix, so we have to delete the PC matrix and the…, _ResponseImageWriter

### Community 209 - "Smooth"
Cohesion: 0.22
Nodes (10): Any, Init a new smoothing pipeline step. Args: sigma: Standard deviation for…, Smooth an image. Args: image: Image to smooth. Returns: Smoothed image., Gaussian smoothing of image data using SciPy’s ndimage.gaussian_filter. This…, Smooth, asyncio, test_call(), test_call_no_image_data() (+2 more)

### Community 210 - "SkyflatPriorities"
Cohesion: 0.27
Nodes (6): ArchiveSkyflatPriorities, Calculate flat priorities from an archive., Base class for sky flat priorities., SkyflatPriorities, ConstSkyflatPriorities, Constant flat priorities.

### Community 211 - "DataCache"
Cohesion: 0.10
Nodes (15): Any, Initializes file cache. Args: port: Port for HTTP server. cache_size: Size of…, DataCache, DataCacheEntry, Any, A single entry in the data cache., Delete entry in cache. Args: name: Name of entry to delete., Create a new entry for the data cache Args: name: Name of item data: Data for… (+7 more)

### Community 212 - "PyobsArchive"
Cohesion: 0.27
Nodes (5): Any, PyobsArchive, Connector class to running pyobs-archive instance., test_build_query_empty_when_nothing_given(), test_build_query_includes_all_given_params()

### Community 213 - "wait_for"
Cohesion: 0.17
Nodes (12): DummyCamera.open() must publish IWindow.Capabilities with the SimCamera full…, DummyCamera.open() must publish IModule.Capabilities with version and label., get_capabilities() must return None for an interface DummyCamera doesn't…, Poll *condition* until truthy or *timeout* seconds elapse., DummyCamera's _cooling_thread publishes CoolingState every second. An observer…, After calling set_cooling via RPC, the published CoolingState must reflect the…, test_dummy_camera_cooling_state_reflects_set_cooling(), test_dummy_camera_no_capabilities_for_unconfigured_interface() (+4 more)

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

### Community 218 - "FileSystemTaskArchive"
Cohesion: 0.15
Nodes (9): FileSystemTaskArchive, Any, Task archive based on files., Creates a new filesystem-based task archive. Args: extension: Extension of…, Returns time when last time any blocks changed., Returns list of projects. Returns: List of projects., Returns list of schedulable tasks. Returns: List of schedulable tasks, Returns the task with the given ID. Returns: Task with given ID. (+1 more)

### Community 219 - ".add_fits_headers"
Cohesion: 0.24
Nodes (6): PrimaryHDU, Add requested FITS headers to header of given image. Args: image: Image with…, Add FITS header keywords to the given FITS header. Args: image: Image with…, Add FRAMENUM keyword to header Args: image: Image with header to add to., Format filename according to given pattern and store in header of image. Args:…, Add FITS header keywords to the given FITS header. Args: image: Image with…

### Community 220 - "FlatField"
Cohesion: 0.11
Nodes (16): FlatField, Any, IBinning, ICamera, IFilters, IFlatField, ITelescope, List available binnings. Returns: List of available binnings as (x, y) tuples. (+8 more)

### Community 221 - "flatfield/test_scheduler.py"
Cohesion: 0.22
Nodes (14): FlatFieldScheduler, IRunnable, Run the flat-field scheduler., A single item in the flat scheduler, Initializes a new scheduler item Args: start: Start time in seconds end: End…, Nice string representation for item, SchedulerItem, make_scheduler_module() (+6 more)

### Community 222 - "Pixeloffset (guidingstatistics)"
Cohesion: 0.25
Nodes (7): GuidingStatisticsPixelOffset, Calculates RMS of data. Args: data: Data to calculate RMS for. Returns: Tuple…, mock_meta_image(), fixture, test_build_header_to_few_values(), test_end_to_end(), test_get_session_data()

### Community 223 - "NextImage"
Cohesion: 0.17
Nodes (13): calc_expose_timeout(), LastImage, NextImage, Any, IExposureTime, NamedTuple, NDArray, Create a JPEG ge from a numpy array and return as bytes. Args: data: Numpy… (+5 more)

### Community 224 - "Weather State (weather)"
Cohesion: 0.27
Nodes (6): Any, setter, WeatherStatus, test_status_set(), test_status_set_non_good(), test_status_set_none_good()

### Community 225 - "XEP_0009_timeout"
Cohesion: 0.17
Nodes (6): BasePlugin, A plugin for SleekXMPP, adding a timeout to RPC calls., XEP_0009_timeout, SleekXMPP: The Sleek XMPP Library Copyright (C) 2011 Nathanael C. Fritz, Dann…, MethodTimeout, ElementBase

### Community 226 - "ConfigStatus"
Cohesion: 0.25
Nodes (6): ConfigStatus, Run a config Args: script: Script to run Returns: Configuration status to send…, Status of a single configuration., Initializes a new Status with an ATTEMPTED., Finish this status with the given values and the current time. Args: state:…, Convert status to JSON for sending to portal.

### Community 227 - "FileList"
Cohesion: 0.27
Nodes (5): FileList, Base class for file lists., Any, File list for testing., TestingFileList

### Community 228 - "MockBaseDome"
Cohesion: 0.21
Nodes (8): pyobs.modules.roof (doc), BaseDome, BaseRoof, DummyRoof, MockBaseDome, Any, asyncio, test_get_fits_header_before()

### Community 229 - "TempFile"
Cohesion: 0.24
Nodes (6): Any, Open/create a temp file. Args: name: Name of file. mode: Open mode. prefix:…, TempFile, asyncio, test_name(), test_write_file()

### Community 230 - "pyobs 2.0 Wire Protocol, State, and Access Control design doc"
Cohesion: 0.20
Nodes (11): slixmpp O(N^2) IQ handler dispatch bug (root cause, filed upstream), slixmpp O(N^2) IQ handler dispatch bug (cross-referenced), pyobs 2.0 Wire Protocol, State, and Access Control design doc, Decision: async with is the only way to obtain a Proxy, Extended disco#info: command/state/capability/types schema, Proxy: get_state/get_capabilities/wait_for_state design, RPC Payload Encoding 2.0 (urn:pyobs:rpc:1), State: fourth wire concept (capabilities/commands/state/events) (+3 more)

### Community 231 - "test_xmpp_acl.py"
Cohesion: 0.22
Nodes (12): Integration tests for Phase 8 Access Control (ACLs) over real XMPP. Verifies…, A caller granted "*" access under "allow" can still call normally., A caller not present in the "allow" map is denied by default., A caller on the "deny" list gets exc.RemoteError with a forbidden message, not…, Naming an interface under "allow" permits all of its methods, but nothing…, A module not on the "deny" list is unaffected., test_acl_allow_denies_unlisted_caller(), test_acl_allow_interface_name_sugar() (+4 more)

### Community 232 - "IAcquisition interface / AcquisitionState / AcquisitionResult"
Cohesion: 0.22
Nodes (10): Rationale: AcquisitionResult reports cumulative offset (vs GuidingState's per-correction), Rationale: guiding reports per-image correction in arcsec, not cumulative or pixel offset, IAcquisition interface / AcquisitionState / AcquisitionResult, IAutoGuiding interface / GuidingState, OffsetFrame enum (pyobs/utils/enums.py), ApplyOffsets.__call__ -> OffsetResult, Plan: pyobs-gui IAcquisition widget, Plan: pyobs-gui IAutoGuiding widget (+2 more)

### Community 233 - "iag50 reconnect-storm / late-joiner capability-fetch incident"
Cohesion: 0.27
Nodes (10): BrotRaDecTelescope (pyobs-brot) missing ITemperatures publish bug, Comm._published_state / missing_published_state(), iag50 reconnect-storm / late-joiner capability-fetch incident, Shaper hypothesis refuted for concurrent-push latency, Root mechanism found: un-re-armed passive socket, stuck Recv-Q in ejabberd c2s, mod_client_state (CSI) hypothesis: correlated but ruled out as cause, Plan: Systematic ejabberd throughput/latency benchmarking, Plan: Enforce state publishing for stateful interfaces (+2 more)

### Community 234 - "CHANGELOG.rst"
Cohesion: 0.22
Nodes (9): ejabberd shaper/xmpp_socket.erl reactivation bug (iag50srv capability-fetch timeouts), XmppComm disco#info role attribute (send/subscribe split), OnDemandScheduler CPU-bound work offloaded to ThreadPoolExecutor, Vfs.write_image()/write_fits() moved to asyncio.to_thread(), run_cpu_bound (scheduler/_executor.py), Vfs.write_fits (pyobs/vfs/vfs.py), Vfs.write_image (pyobs/vfs/vfs.py), specs/plans/event-role-advertising.md (+1 more)

### Community 235 - "test_aperture_photometry.py"
Cohesion: 0.26
Nodes (9): MockPhotometryCalculator, asyncio, QTable, AperturePhotometry.__init__ is abstract -- concrete calculators…, test_call_invalid_catalog(), test_call_invalid_data(), test_call_invalid_pixelscale(), test_call_valid() (+1 more)

### Community 236 - "Image class"
Cohesion: 0.20
Nodes (10): meta.AltAzOffsets, meta.ExpTime, Image class, Image.meta dict; rationale: keyed by class to avoid collisions between pipeline stages, kept out of FITS since it's runtime-only data, meta.OnSkyDistance, meta.PixelOffsets, meta.RaDecOffsets, meta.SkyOffsets (+2 more)

### Community 237 - ".__call__"
Cohesion: 0.38
Nodes (5): ApertureMask, CircularAperture, Any, floating, NDArray

### Community 238 - "Access Control (ACLs): allow/deny, mode: enforce|log"
Cohesion: 0.24
Nodes (10): Rationale: grey out individual actions, hide only fully-blocked modules, BaseWidget._fetch_permitted_methods() / permitted(), InvocationError retired, real exception types reconstructed instead, Module.execute() as single catch/log/classify chokepoint, PyobsError registry (__init_subclass__), Plan: Exception handling across the RPC boundary, Plan: pyobs-gui ACL-aware widget gating, Access Control (ACLs): allow/deny, mode: enforce|log (+2 more)

### Community 239 - ".retrieve_class_on_deserialization"
Cohesion: 0.24
Nodes (7): model_serializer, Any, model_validator, Self, Get the correct class for this model and run model_validate on that class with…, ValidationInfo, ValidatorFunctionWrapHandler

### Community 240 - "Module.startup() lifecycle helper"
Cohesion: 0.22
Nodes (9): Location-mismatch warning via _on_module_opened, Rationale: location as one-shot capability, not pubsub state, Module._on_module_opened (N-fold capability-fetch burst trigger), Module.startup() lifecycle helper, ModuleLocation dataclass (nested in ModuleCapabilities), ModuleState.STARTING, Rationale: delay send_presence() until READY to avoid capability-publish race, Module observer-location capabilities design doc (+1 more)

### Community 241 - "test_comm_interface_resolution.py"
Cohesion: 0.29
Nodes (8): Converts a list of interface names to interface classes. Args: interfaces: list…, LogCaptureFixture, Tests for Comm._interface_names_to_classes -- the base-Comm chokepoint that…, An interface defined entirely outside pyobs.interfaces resolves the same way…, test_resolves_external_interface(), test_resolves_known_and_skips_unknown_in_same_list(), test_resolves_known_core_interfaces(), test_skips_unknown_name()

### Community 242 - "ProjectionFocusSeries"
Cohesion: 0.16
Nodes (11): ProjectionFocusSeries, Any, floating, NDArray, Returns a list of data points., Fit focus from analysed images Returns: Tuple of new focus and its error, Creates a sine window function of the same size as some 1-D array "arr".…, Removes global slopes and fills up bad rows (ybad) or columns (xbad). (+3 more)

### Community 243 - ".__init__"
Cohesion: 0.18
Nodes (8): Any, SkyCoord, Create an approximately equidistributed spherical grid. Args: n: Target number…, Initialize a Grid with a list of points. Args: points: Initial list of points…, Return the next point and remove it from the internal list. Returns: The next…, Create a regular lon/lat grid. Args: n_lon: Number of longitudinal divisions.…, Any, Initialize a GridNode. Args: log: If True, enable informational logging for…

### Community 244 - "InfluxHandler"
Cohesion: 0.24
Nodes (4): InfluxHandler, Any, LogRecord, WriteOptions

### Community 245 - "SMBFile"
Cohesion: 0.22
Nodes (5): Any, Returns content of given path. Args: path: Path to list. kwargs: Parameters for…, VFS wrapper for a file that can be accessed over a SMB connection. Requires…, Open/create a file over a SSH connection. Args: name: Name of file. mode: Open…, SMBFile

### Community 246 - "pyobs-gui as a standalone binary (umbrella design)"
Cohesion: 0.27
Nodes (10): ADR-0010: pyobs-gui stays on QtWidgets, not QML, gui-telescopewidget-layout.md, pyobs-gui (PySide6/QtWidgets app), pyobs-web-client (Vue 3 + TypeScript), QML (declarative UI framework), pyobs.application.Application, pyobs-gui as a standalone binary (umbrella design), specs/plans/gui-interactive-login.md (+2 more)

### Community 247 - "Plan: pyobs-pipeline (Django web project)"
Cohesion: 0.24
Nodes (10): Plan: Harden and rename Night -> Reduction; complete LocalArchive I/O, LocalArchive.upload_frames (silent no-op bug, fixed to real write), Rename rationale: 'Night' doesn't fit solar telescopes, Reduction class (renamed from Night), Plan: Surface unrecognized kwargs in Object.__init__, Object.__init__ silent **kwargs sink, reduce_period Celery task, DbScheduler (Celery Beat, dynamic per-site schedule) (+2 more)

### Community 248 - "LogEvent"
Cohesion: 0.18
Nodes (6): LogEvent, Event for log entries., Enum, TelegramUserState, test_log_event_properties(), test_log_event_roundtrip()

### Community 249 - "test_safe_send.py"
Cohesion: 0.38
Nodes (9): make_xmpp_comm(), asyncio, Tests for XmppComm._safe_send's retry/timeout handling. Covers…, Create a minimal XmppComm instance for testing, without a live connection., A method that never returns (e.g. slixmpp's own IQ timeout not firing) must…, test_safe_send_enforces_own_timeout_when_method_hangs(), test_safe_send_retries_and_raises_on_iq_timeout(), test_safe_send_returns_result_on_success() (+1 more)

### Community 250 - "test_camerasettings.py"
Cohesion: 0.42
Nodes (9): make_camera_proxy(), make_module(), asyncio, Minimal concrete module for exercising CameraSettingsMixin in isolation., Capabilities for a Proxy are fetched in the background (see…, SettingsModule, test_raises_when_capabilities_never_arrive(), test_sets_binning_before_window() (+1 more)

### Community 251 - "Two-phase Object lifecycle; rationale: __init__ must not touch hardware/external services (only store params, create children, register background tasks); open() is where side effects happen, so objects can be constructed cheaply/safely before being started"
Cohesion: 0.22
Nodes (8): Object.add_child_object(), create_object(), get_object(), Two-phase Object lifecycle; rationale: __init__ must not touch hardware/external services (only store params, create children, register background tasks); open() is where side effects happen, so objects can be constructed cheaply/safely before being started, class: key YAML instantiation; rationale: strips class key, passes remaining keys as kwargs, recursing into nested blocks, so any pyobs object graph is fully describable in YAML, Configuration utilities (pyobs.utils.config) API doc, pre_process_yaml(), Coordinate utilities (pyobs.utils.coordinates) API doc

### Community 252 - "Simulation recipe (doc)"
Cohesion: 0.42
Nodes (9): pyobs.modules.telescope (doc), BaseTelescope, DummyAltAzTelescope, DummyRaDecTelescope, DummySolarTelescope, Simulation recipe (doc), DummyCamera, pyobs_gui.GUI (+1 more)

### Community 253 - "test_baseroof.py"
Cohesion: 0.30
Nodes (8): MockBaseRoof, Any, asyncio, test_get_fits_header_before_closed(), test_get_fits_header_before_open(), test_not_ready(), test_open(), test_ready()

### Community 254 - "get_class_from_string"
Cohesion: 0.20
Nodes (6): Any, get_class_from_string(), Get class from a given string. Args: class_name: Name of class as string.…, _build_params_model(), _get_valid_param_names(), model_validator

### Community 255 - ".__init__"
Cohesion: 0.20
Nodes (5): Any, Returns the task with the given ID. Returns: Task with given ID., Creates a new task archive. Args: url: URL of pyobs-robotic-backend. token:…, Any, Returns the task with the given ID. Returns: Task with given ID.

### Community 256 - "TaskRunner"
Cohesion: 0.33
Nodes (5): Target, Checks, whether this task could run now. Args: task: Task to run target:…, Returns reason why task cannot run, or None if it can., Run a task. Args: task: Task to run target: Resolved target for this specific…, TaskRunner

### Community 257 - "GuidingStatisticsSkyOffset"
Cohesion: 0.25
Nodes (7): GuidingStatisticsSkyOffset, Calculates RMS of data. Args: data: Data to calculate RMS for. Returns: Tuple…, mock_meta_image(), fixture, test_build_header_to_few_values(), test_end_to_end(), test_get_session_data()

### Community 258 - "IAutoFocus"
Cohesion: 0.25
Nodes (7): IAutoFocus, Any, IAbortable, IRunning, SECONDS, The module can perform an autofocus., Perform an autofocus series. This method performs an autofocus series with…

### Community 259 - "format_filename"
Cohesion: 0.43
Nodes (7): format_filename(), Formats a filename given a format template and a FITS header. Args: hdr: FITS…, test_date_obs(), test_default(), test_filter(), test_list(), test_string()

### Community 260 - "IStructuredConfig interface"
Cohesion: 0.25
Nodes (8): pyobs/utils/config_schema.py: dataclass_to_schema, ICooling interface (reference pattern), IStructuredConfig design doc, IStructuredConfig interface, Rationale: IStructuredConfig coexists with IConfig (per-field vs bulk dataclass config), Interface.version / Event.version, Rationale: state and capabilities stay two independent ClassVars, not merged, Rationale: version lives on Interface only, not on State dataclass

### Community 261 - "robotic"
Cohesion: 0.43
Nodes (8): acquisition, fibercamera, fts, guiding, robotic, solar telescope, suncamera, weather

### Community 262 - "Archive (image archive base)"
Cohesion: 0.32
Nodes (8): Archive (image archive base), LocalArchive, PyobsArchive, ArchiveSkyflatPriorities, Archive, Image archives (pyobs.robotic.utils.archive) API doc, LocalArchive, PyobsArchive

### Community 263 - ".__init__"
Cohesion: 0.25
Nodes (5): Any, Initializes a new ApplyAltAzOffsets. Args: min_offset: Min offset in arcsec to…, Any, Any, Initializes a new ApplyRaDecOffsets. Args: min_offset: Min offset in arcsec to…

### Community 264 - "._client_disconnected"
Cohesion: 0.29
Nodes (4): PresenceCallback, Called when a client disconnects. Args: event: Disconnect event. sender: Name…, Subscribe to presence updates for a given module. Delivers the current value…, Unsubscribe from presence updates. Args: module: Name of remote module.…

### Community 265 - "_PhotometryCalculator"
Cohesion: 0.29
Nodes (3): _PhotometryCalculator, Table, Abstract class for photometry calculators.

### Community 266 - "IGain"
Cohesion: 0.29
Nodes (6): IGain, Any, Interface, The camera supports setting of gain, to be used together with…, Set the camera gain. Args: gain: New camera gain. Raises: ValueError: If gain…, Set the camera offset. Args: offset: New camera offset. Raises: ValueError: If…

### Community 267 - "IModule"
Cohesion: 0.29
Nodes (6): IModule, Any, Interface, The module is actually a module. Implemented by all modules., Reset error of module, if any., Returns names of all methods the calling module is allowed to invoke on this…

### Community 268 - "._get_next"
Cohesion: 0.33
Nodes (4): SkyCoord, Log a point if logging is enabled. For SkyCoord instances, logs RA/Dec in…, Return the next point in the sequence. Implementors must return either a (x, y)…, Return the next point, storing it as the last yielded value. Returns: A point…

### Community 269 - "._main"
Cohesion: 0.40
Nodes (3): Actually run the application., Force astropy's IERS-A table and leap-second table to be loaded/downloaded now,…, _warm_iers_cache()

### Community 270 - "WeatherSensors"
Cohesion: 0.14
Nodes (14): IWeather, Any, IStartStop, The module acts as a weather station., Return value for given sensor. Args: station: Name of weather station to get…, WeatherSensorReading, Weather modules. TODO: write doc, Return value for given sensor. Args: station: Name of weather station to get… (+6 more)

### Community 272 - ".__init__"
Cohesion: 0.29
Nodes (5): Any, IFlatField, Abort current actions., Initialize a new flat field scheduler. Args: flatfield: Flat field module to…, Perform flat-fielding Raises: DeviceBusyError: If a flat-fielding run is…

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

### Community 277 - ".move_altaz"
Cohesion: 0.50
Nodes (3): Any, DEGREES, Moves to given coordinates. Args: alt: Alt in deg to move to. az: Az in deg to…

### Community 281 - "LcoObservationArchive"
Cohesion: 0.06
Nodes (28): Response, Response, Handles access to / and returns HTML page. Args: request: Request to respond…, Handles GET access to /ping for testing connectivity. Args: request: Request to…, Handles access to /* and returns a specified image. Args: request: Request to…, AcquisitionConfig, Configuration, GuidingConfig (+20 more)

### Community 283 - "Target"
Cohesion: 0.29
Nodes (4): Target, Set the resolved target if not already set, e.g. when restoring from an…, The resolved target, or the static target if not dynamic., Target for this specific run: the observation's own record if known, otherwise…

### Community 284 - "._filter_data"
Cohesion: 0.24
Nodes (3): Any, DataFrame, Update files in root directory.

### Community 285 - "test_exceptions.py"
Cohesion: 0.29
Nodes (4): ForbiddenError, Raised when a caller is not permitted to invoke a method under the target…, test_forbidden_error(), test_log_only_logs_once()

### Community 287 - "pyobs.modules.utils (doc)"
Cohesion: 0.33
Nodes (6): pyobs.modules.utils (doc), FluentLogger, Kiosk, Matrix, Telegram, Trigger

### Community 291 - "ICalibrate"
Cohesion: 0.33
Nodes (5): ICalibrate, Any, Interface, Calibrate the device. Raises: GeneralError: If calibration failed., The module can calibrate a device.

### Community 292 - "IConfig"
Cohesion: 0.28
Nodes (7): IConfig, Any, ConfigValue, Interface, The module allows access to some of its configuration options., Returns current value of config item with given name. Args: name: Name of…, Sets value of config item with given name. Args: name: Name of config item.…

### Community 293 - "IDataSequence"
Cohesion: 0.25
Nodes (7): IDataSequence, Any, IAbortable, SECONDS, The module can grab a counted sequence of data (images, spectra, ...)., Start a sequence of `count` grabs. Returns immediately; progress is available…, Stop the sequence after the current grab. The grab currently in progress, if…

### Community 294 - "IFocuser"
Cohesion: 0.28
Nodes (7): IFocuser, Any, IMotion, MM, The module is a focusing device., Sets new focus. Args: focus: New focus value in mm. Raises:…, Sets focus offset. Args: offset: New focus offset in mm. Raises: ValueError: If…

### Community 296 - "IPointingSeries"
Cohesion: 0.33
Nodes (5): IPointingSeries, Any, Interface, Add a new measurement to the pointing series. Raises: GeneralError: If the…, The module provides the interface for a device that initializes and finalizes a…

### Community 297 - "IScriptRunner"
Cohesion: 0.33
Nodes (5): IScriptRunner, Any, Interface, Run the given script. Args: script: Script to run. Raises: ScriptError: If the…, The module can execute a script.

### Community 298 - "ISyncTarget"
Cohesion: 0.33
Nodes (5): ISyncTarget, Any, Interface, Synchronize device on current target. Raises: GeneralError: If synchronization…, The module can synchronize a target, e.g. via a telescope control software…

### Community 299 - "IWindow"
Cohesion: 0.33
Nodes (5): IWindow, Any, Interface, The camera supports windows, to be used together with…, Set the camera window. Args: left: X offset of window. top: Y offset of window.…

### Community 300 - "ADR-0008: _safe_send keeps bounded retry unlike capability/subscribe fetches"
Cohesion: 0.40
Nodes (5): ADR-0008: _safe_send keeps bounded retry unlike capability/subscribe fetches, #664/#666 slow-shaper hang incident, XmppComm._get_capabilities(), XmppComm._retry_delay() (jittered capped backoff), XmppComm._safe_send()

### Community 301 - "Module._watch_event_loop_lag"
Cohesion: 0.33
Nodes (5): BrotDome._update_status, ADR-0009: Event-loop lag watchdog lives on Module, FocusModel._update, pyobs-iag50 capability-fetch timeout incident, Module._watch_event_loop_lag

### Community 302 - "ICamera(IData, IExposure) -> ICamera(IData); IExposure moved to BaseCamera"
Cohesion: 0.33
Nodes (6): ICamera(IData, IExposure) -> ICamera(IData); IExposure moved to BaseCamera, Plan: Decouple ICamera/IExposure, Rationale: PipelineCamera was publishing fabricated ExposureState just to satisfy inherited contract, Plan: IDataSequence server-side counted data sequences, IDataSequence(IAbortable): grab_sequence()/abort_sequence()/DataSequenceState, Rationale: grab_sequence() non-blocking background task, server-side sequence concept

### Community 303 - "pyobs.modules.image (doc)"
Cohesion: 0.40
Nodes (5): pyobs.modules.image (doc), ImageWatcher, ImageWriter, Pipeline (image module), Seeing

### Community 316 - ".__init__"
Cohesion: 0.40
Nodes (3): Any, Any, Initialize a new scheduler. Args: twilight: astronomical or nautical

### Community 317 - "check_pyobs_releases.sh"
Cohesion: 0.70
Nodes (4): check_repo(), main(), print_header(), check_pyobs_releases.sh script

### Community 318 - "check_ejabberd_notify.py"
Cohesion: 0.60
Nodes (4): connect(), main(), make_client(), Minimal ejabberd notification test — no pyobs code involved.

### Community 320 - "ITrackingRate"
Cohesion: 0.29
Nodes (6): ARCSEC_PER_SEC, ITrackingRate, Any, Interface, The module accepts an arbitrary non-sidereal tracking rate as an absolute…, Sets an absolute tracking rate on the sky, in arcsec/sec. Args: ra_rate: Rate…

### Community 322 - "Photometry (pyobs.images.processors.photometry) API doc"
Cohesion: 0.83
Nodes (4): Photometry (pyobs.images.processors.photometry) API doc, Photometry, PhotUtilsPhotometry, SepPhotometry

### Community 323 - "Event <event role="send|subscribe|send subscribe"> attribute"
Cohesion: 0.67
Nodes (4): Rationale: undifferentiated event set caused send/subscribe ambiguity in pyobs-web-client, Event <event role="send|subscribe|send subscribe"> attribute, Comm._events_sent / _events_subscribed, Plan: Advertise event send/subscribe role in disco#info

### Community 334 - "HttpFileCache token param + Bearer auth check + CORS headers"
Cohesion: 0.50
Nodes (4): HttpFile client: token param, Authorization: Bearer, Rationale: Access-Control-Allow-Origin: * is safe since Authorization is explicit, not ambient, HttpFileCache token param + Bearer auth check + CORS headers, Plan: CORS + token auth for HttpFileCache

### Community 335 - "Plan: pyobs-gui TelescopeWidget layout width-floor investigation"
Cohesion: 0.50
Nodes (4): MoveStack: size to current widget, not widest page, Plan: pyobs-gui TelescopeWidget layout width-floor investigation, Root cause: QStackedWidget sizes to widest page, not current page, TemperaturesWidget dynamic-row generation precedent

### Community 336 - "self._slot_bindings, Ctrl+N recall / Ctrl+Alt+N bind scheme"
Cohesion: 0.67
Nodes (4): Rationale: always require Ctrl, avoid per-widget-type empirical verification, self._slot_bindings, Ctrl+N recall / Ctrl+Alt+N bind scheme, NavPageItemDelegate (badge paint overlay), Plan: pyobs-gui navbar keyboard shortcuts

### Community 338 - ".__init__"
Cohesion: 0.50
Nodes (3): Pipeline, Any, Creates a Reduction object for reducing a given observation period. Args:…

### Community 339 - "DummyAutoGuiding"
Cohesion: 0.07
Nodes (24): GuidingState, IAutoGuiding, IExposureTime, IStartStop, The module can perform auto-guiding., IExposureTime, Any, Interface (+16 more)

### Community 340 - "IFlatField"
Cohesion: 0.29
Nodes (6): IFlatField, Any, IAbortable, SECONDS, The module performs flat-fielding., Do a series of flat fields. Args: count: Number of images to take Returns:…

### Community 342 - "IOffsetsRaDec"
Cohesion: 0.29
Nodes (6): IOffsetsRaDec, Any, DEGREES, Interface, The module supports RA/Dec offsets, usually combined with…, Move an RA/Dec offset. Args: dra: RA offset in degrees. ddec: Dec offset in…

### Community 345 - "IPointingHelioprojective"
Cohesion: 0.29
Nodes (6): IPointingHelioprojective, Any, DEGREES, Interface, The module can move to Mu/Psi coordinates, usually combined with…, Moves on given coordinates. Args: theta_x: The theta_x coordinate. theta_y: The…

### Community 346 - "IPointingRaDec"
Cohesion: 0.29
Nodes (6): IPointingRaDec, Any, DEGREES, Interface, The module can move to RA/Dec coordinates, usually combined with…, Starts tracking on given coordinates. Args: ra: RA in deg to track. dec: Dec in…

### Community 348 - "IStructuredConfig"
Cohesion: 0.29
Nodes (6): IStructuredConfig, Any, ConfigValue, Interface, The module accepts a whole structured (possibly nested) config object in one…, Apply a full structured config to this module. Args: config: Nested dict…

### Community 350 - ".night_obs"
Cohesion: 0.50
Nodes (3): date, Observer, Returns the night for this time, i.e. the date of the start of the current…

### Community 351 - "README.md"
Cohesion: 0.50
Nodes (3): pyobs CLI (foreground module runner), pyobsd CLI (background daemon manager), pyobsw CLI (Windows equivalent of pyobs)

### Community 352 - "Install-ejabberd (xmpp)"
Cohesion: 0.83
Nodes (3): restore_perms(), install-ejabberd.sh script, yq_is_correct_variant()

### Community 353 - "XmppComm._disconnected"
Cohesion: 0.50
Nodes (3): ADR-0002: XMPP stream-error conflict quits instead of reconnecting, XMPP stream-error condition 'conflict' (RFC 6120 §4.9.3), XmppComm._disconnected()

### Community 355 - "AutoFocusWidget (pyobs-gui)"
Cohesion: 1.00
Nodes (3): AutoFocusWidget (pyobs-gui), IAutoFocus gains IRunning base, AutoFocusSeries publishes RunningState, Plan: pyobs-gui IAutoFocus widget

### Community 356 - "pyobs.modules.pointing (doc)"
Cohesion: 1.00
Nodes (3): pyobs.modules.pointing (doc), Acquisition (pointing module), BaseGuiding

### Community 357 - "pyobs.modules.weather (doc)"
Cohesion: 1.00
Nodes (3): pyobs.modules.weather (doc), MockWeather, Weather (module)

### Community 369 - "ejabberd 10x Shaper Benchmark Config"
Cohesion: 0.67
Nodes (3): ejabberd 10x Shaper Benchmark Config, ejabberd.yml (production default shaper), Throughput benchmark: shaper comparison

### Community 371 - "ADR-0005: IConfig stays a stringly-keyed fallback"
Cohesion: 0.67
Nodes (3): ADR-0005: IConfig stays a stringly-keyed fallback, IConfig, specs/design/istructuredconfig.md

### Community 372 - "Exception handling across the RPC boundary (design doc)"
Cohesion: 0.67
Nodes (3): Exception handling across the RPC boundary (design doc), Issue #446 (redundant local exception logging), PyObsError exception hierarchy

### Community 373 - "ModuleLocation dataclass (nested in ModuleCapabilities)"
Cohesion: 0.67
Nodes (3): Plan: Module observer-location capabilities, ModuleLocation dataclass (nested in ModuleCapabilities), Use capabilities (one-shot) not state (pub-sub) for location

### Community 374 - "Steering: pyobs project fleet tiers (core/connected/internal)"
Cohesion: 0.67
Nodes (3): Steering: Connected projects track pyobs-core major version, Steering: Fleet tooling consistency baseline, Steering: pyobs project fleet tiers (core/connected/internal)

## Ambiguous Edges - Review These
- `Configuration utilities (pyobs.utils.config) API doc` → `Coordinate utilities (pyobs.utils.coordinates) API doc`  [AMBIGUOUS]
  docs/source/api/utils/coordinates.rst · relation: conceptually_related_to
- `PyObsError` → `ScriptRunner.run()`  [AMBIGUOUS]
  specs/design/exception_handling.md · relation: conceptually_related_to
- `FocusError` → `FocusModel.set_optimal_focus`  [AMBIGUOUS]
  specs/design/exception_handling.md · relation: conceptually_related_to
- `XmppComm._safe_send retry-on-timeout (ruled out)` → `Root cause: dual PEP delivery paths (implicit roster + explicit interest)`  [AMBIGUOUS]
  specs/plans/logevent-double-delivery-investigation.md · relation: conceptually_related_to
- `ExceptionHandler nested wrapper (#328, rejected)` → `max_age: float | None parameter (opt-in staleness check)`  [AMBIGUOUS]
  specs/plans/pipeline-step-error-control.md · relation: semantically_similar_to

## Knowledge Gaps
- **297 isolated node(s):** `pyobs-core`, `autocompletion.bash script`, `OpticalElement`, `OpticalElementGroup`, `Mode` (+292 more)
  These have ≤1 connection - possible missing edges or undocumented components.
- **34 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **What is the exact relationship between `Configuration utilities (pyobs.utils.config) API doc` and `Coordinate utilities (pyobs.utils.coordinates) API doc`?**
  _Edge tagged AMBIGUOUS (relation: conceptually_related_to) - confidence is low._
- **What is the exact relationship between `PyObsError` and `ScriptRunner.run()`?**
  _Edge tagged AMBIGUOUS (relation: conceptually_related_to) - confidence is low._
- **What is the exact relationship between `FocusError` and `FocusModel.set_optimal_focus`?**
  _Edge tagged AMBIGUOUS (relation: conceptually_related_to) - confidence is low._
- **What is the exact relationship between `XmppComm._safe_send retry-on-timeout (ruled out)` and `Root cause: dual PEP delivery paths (implicit roster + explicit interest)`?**
  _Edge tagged AMBIGUOUS (relation: conceptually_related_to) - confidence is low._
- **What is the exact relationship between `ExceptionHandler nested wrapper (#328, rejected)` and `max_age: float | None parameter (opt-in staleness check)`?**
  _Edge tagged AMBIGUOUS (relation: semantically_similar_to) - confidence is low._
- **Why does `Time` connect `Time` to `Observation`, `time.py`, `IAbortable`, `MotionStatus`, `DynamicTarget`, `BaseCamera`, `ImageProcessor`, `ObservationList`, `basetelescope.py`, `TimeDelta`, `FilenameFormatter`, `test_astroplanscheduler.py`, `Event`, `test_flatfielder.py`, `tests/test_events.py`, `Object`, `FitsHeaderEntry`, `test_control.py`, `test_lco_http.py`, `CoolingState`, `test_yaml_archives.py`, `TaskData`, `robotic/test_scheduler.py`, `Calibration`, `Publisher`, `http_request_with_retries`, `Proxy`, `SkyFlatsBasePointing`, `FlatFielder`, `LcoScript`, `Offsets`, `.now`, `test_proxy.py`, `SiderealTarget`, `Pipeline`, `Weather`, `SolarElevationConstraint`, `test_schedulewriter.py`, `DummySolarTelescope`, `test_backend_archives.py`, `DummyCamera`, `test_pyobs_archive.py`, `BaseGuiding`, `LcoScheduleReader`, `test_coordinates.py`, `Portal`, `LocalArchive`, `Test Commlogging (comm)`, `ImagingScript`, `LcoTaskArchive`, `comm.py`, `FocusModel`, `test_darkbias.py`, `GridNode`, `GoodWeatherEvent`, `test_dummymode.py`, `IRunning.py`, `test_autofocus.py`, `Grid`, `pyobs.py`, `OffsetResult`, `Scheduler`, `Archive`, `RandomizeGrid`, `pyobs/modules/utils/__init__.py`, `ExpTimeEval`, `OptimalFocusState`, `Scheduler`, `test_schedulereader.py`, `Interface`, `TaskStartedEvent`, `BrightestStarGuiding`, `test_filters.py`, `SkyflatPriorities`, `PyobsArchive`, `FileSystemTaskArchive`, `.add_fits_headers`, `flatfield/test_scheduler.py`, `ConfigStatus`, `InfluxHandler`, `WeatherSensors`, `LcoObservationArchive`, `._filter_data`, `.night_obs`?**
  _High betweenness centrality (0.275) - this node is a cross-community bridge._
- **Why does `Image` connect `Image` to `time.py`, `GuidingStatisticsSkyOffset`, `BaseCamera`, `ImageProcessor`, `_PhotometryCalculator`, `AstrometryDotNet`, `FilenameFormatter`, `OffsetResult`, `AperturePhotometry`, `mixins/test_fitsheader.py`, `PipelineMixin`, `test_acquisition.py`, `test_flatfielder.py`, `_SourceCatalog`, `FitsHeaderEntry`, `SoftBin`, `AddMask`, `GuidingStatistics`, `_DaoBackgroundRemover`, `Archive`, `BrightestStarOffsets`, `._filter_data`, `RemoveBackground`, `SepSourceDetection`, `_CalibrationCache`, `BaseVideo`, `VirtualFileSystem`, `StarExpTimeEstimator`, `_SepAperturePhotometry`, `Calibration`, `FitsHeaderOffsets`, `Interface`, `test_basevideo.py`, `CatalogCircularMask`, `Offsets`, `BrightestStarGuiding`, `Pipeline`, `test_autoguiding.py`, `_ResponseImageWriter`, `Smooth`, `SkyOffsets`, `Image (images)`, `PyobsArchive`, `Ring`, `DummyCamera`, `.add_fits_headers`, `ProjectedOffsets`, `Pixeloffset (guidingstatistics)`, `NextImage`, `PillowHelper`, `test_pyobs_archive.py`, `FocusSeries`, `BaseGuiding`, `test_aperture_photometry.py`, `LocalArchive`, `_PhotUtilAperturePhotometry`, `ProjectionFocusSeries`, `VFSFile`, `ImageSourceFilter`?**
  _High betweenness centrality (0.161) - this node is a cross-community bridge._