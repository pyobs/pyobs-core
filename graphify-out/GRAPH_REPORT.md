# Graph Report - pyobs-core  (2026-08-11)

## Corpus Check
- 762 files · ~389,071 words
- Verdict: corpus is large enough that graph structure adds value.

## Summary
- 8558 nodes · 20715 edges · 409 communities (369 shown, 40 thin omitted)
- Extraction: 93% EXTRACTED · 7% INFERRED · 0% AMBIGUOUS · INFERRED: 1398 edges (avg confidence: 0.55)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `19d3be73`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- time.py
- enums.py
- Time
- RunningState
- MotionStatus
- Module
- Image
- DynamicTarget
- utils/exceptions.py
- ImageProcessor
- ObservationList
- test_dummyradectelescope.py
- test_presence.py
- XmppComm
- AstrometryDotNet
- FilenameFormatter
- test_scheduler_mastermind.py
- _SepAperturePhotometry
- DummyRoof
- mixins/test_fitsheader.py
- Event
- PipelineMixin
- test_astroplanscheduler.py
- test_flatfielder.py
- LocalComm
- tests/test_events.py
- _SourceCatalog
- Object
- .__init__
- WindowingWidget
- Interfaces (pyobs.interfaces) API doc
- test_control.py
- _DaoBackgroundRemover
- LogScript
- test_lco_http.py
- BaseTelescope
- Future
- VirtualFileSystem
- xmppcomm.py
- test_follow.py
- test_yaml_archives.py
- test_lcoscript.py
- BaseVideo
- Comm
- test_transit_mastermind.py
- robotic/test_scheduler.py
- StandAlone
- PyobsError
- CLI
- test_stellarexptime.py
- StarExpTimeEstimator
- RPC
- WindowCapabilities
- test_shellcommand.py
- Calibration
- .get_object
- Publisher
- http_request_with_retries
- test_units.py
- Proxy
- IOffsetsAltAz.py
- test_basevideo.py
- IPointingAltAz
- AirmassConstraint
- FlatFielder
- IExposure
- Telegram
- benchmark_state_throughput.py
- scripts/autofocus.py
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
- test_acquisition.py
- Weather
- SolarElevationConstraint
- SkyOffsets
- test_backend_archives.py
- Portal
- Ring
- DummySolarTelescope
- XmppClient
- _AbortableModule
- DummyCamera
- Application
- DummyComm
- CallModuleScript
- ProjectedOffsets
- test_pyobs_archive.py
- HttpFile
- Constraint
- application.py
- FocusSeries
- SepSourceDetection
- make_proxy_cm
- _DotNetRequest
- ScriptRunner
- ResolvableErrorLogger
- test_coordinates.py
- get_registered_interface
- OnSkyDistance
- LocalArchive
- _AbortableModule
- _PhotUtilAperturePhotometry
- Mixins (pyobs.mixins) API doc
- Script base class
- test_background_task.py
- Test Commlogging (comm)
- .__init__
- .__init__
- ImagingScript
- BackendTaskArchive
- BufferedFile
- VFSFile
- LocalFile
- test_version_mismatch.py
- CLAUDE.md (repo guide)
- SFTPFile
- WeatherSensors
- TaskFinishedEvent
- ImageSourceFilter
- test_darkbias.py
- test_config_schema.py
- GridNode
- MoveAltAzEvent
- Test Localcomm (local)
- GoodWeatherEvent
- test_pyobsd.py
- test_dummymode.py
- ProjectionFocusSeries
- OffsetsAltAzEvent
- test_autofocus.py
- Grid
- test_kiosk.py
- pyobs.py
- Robotic recipe (doc)
- is_valid_jid
- _CalibrationCache
- test_dummyvideo.py
- fit_hyperbola
- Scheduler
- RollingTimeAverage
- test_localcomm_state.py
- CsvPublisher
- Plan: pyobs 2.0 rollout (work plan)
- `OBSNUM`: per-night observation counter in FITS headers
- 3rd party packages (doc)
- Any
- SSHFile
- create_rst.py
- GuidingStatistics
- SoftBin
- AddMask
- Archive
- RandomizeGrid
- comm/test_events.py
- _event_role
- pyobs/modules/utils/__init__.py
- NewImageEvent
- ExpTimeEval
- Stellarium
- Overview (doc)
- test_schedulewriter.py
- MultiModule
- FileSystemTaskArchive
- Kiosk
- test_grab_sequence.py
- binding.py
- NewSpectrumEvent
- gui/camera/__init__.py
- .set_config
- HttpFileCache
- FitsHeaderOffsets
- Scheduler
- Plan: Split archive prefetch from CPU-bound merit evaluation
- Test Basecamera (camera)
- Test Imagewatcher (image)
- ._do_camera_settings
- Merit
- ejabberd shaper throttling bug (xmpp_socket.erl re-arm) & fix
- BrightestStarGuiding
- .__init__
- pyobs/interfaces/__init__.py
- .__init__
- PointingSeries
- GridPipeline
- wait_for
- Plan: Widget plugin mechanism + pyside6-deploy packaging for pyobs-gui
- What's New in pyobs 2.0 (doc)
- TaskStartedEvent
- pyobs/images/meta/__init__.py
- CatalogCircularMask
- .__call__
- ImageWatcher
- .__init__
- test_filters.py
- show_module_info.py
- integration/conftest.py
- .set_cooling
- robotic
- Scheduler module
- BaseModel (pyobs.utils.serialization)
- configdb.py
- Smooth
- SkyflatPriorities
- DataCache
- wait_for
- wait_for
- test_httpfilecache.py
- Image (pyobs.images.processors.image) API doc
- Offsets (pyobs.images.processors.offsets) API doc
- Constraint
- .set_offsets_altaz
- .add_fits_headers
- FlatField
- flatfield/test_scheduler.py
- AstrometryOffsets
- NextImage
- ExposeWidget
- XEP_0009_timeout
- DataDisplayWidget
- FileList
- ModuleState
- TempFile
- pyobs 2.0 Wire Protocol, State, and Access Control design doc
- test_xmpp_acl.py
- IAcquisition interface / AcquisitionState / AcquisitionResult
- iag50 reconnect-storm / late-joiner capability-fetch incident
- CHANGELOG.rst
- .set_binning
- Image class
- MotionStatusChangedEvent
- Access Control (ACLs): allow/deny, mode: enforce|log
- .retrieve_class_on_deserialization
- Module.startup() lifecycle helper
- test_comm_interface_resolution.py
- .__init__
- .__init__
- .__call__
- SMBFile
- pyobs-gui as a standalone binary (umbrella design)
- Plan: pyobs-pipeline (Django web project)
- LogEvent
- test_safe_send.py
- get_class_from_string
- Two-phase Object lifecycle; rationale: __init__ must not touch hardware/external services (only store params, create children, register background tasks); open() is where side effects happen, so objects can be constructed cheaply/safely before being started
- Simulation recipe (doc)
- RemoteError
- Seeing
- RegularSphericalGrid
- ConfigDB
- GuidingStatisticsSkyOffset
- IMultiFiber
- test_module_state_publishing.py
- IStructuredConfig interface
- robotic
- Archive (image archive base)
- .get_meta
- ._client_disconnected
- solarhelioprojective.py
- IGain
- IModule
- ._get_next
- ExposureTimeWidget
- ._subscribe_presence
- .calibrate
- FlatFieldScheduler
- Image.trim
- conftest.py
- Misc (pyobs.images.processors.misc) API doc
- PolymorphicBaseModel
- .add_pointing_measurement
- .run_script
- Any
- ._expose
- Observation
- .calculate_derived
- Target
- ImageType
- .__init__
- reset_network
- pyobs.modules.utils (doc)
- IConfig
- IDataSequence
- .set_focus
- IWindow
- ADR-0008: _safe_send keeps bounded retry unlike capability/subscribe fetches
- Module._watch_event_loop_lag
- ICamera(IData, IExposure) -> ICamera(IData); IExposure moved to BaseCamera
- pyobs.modules.image (doc)
- check_pyobs_releases.sh
- check_ejabberd_notify.py
- _DummyTelescopeBase
- Photometry (pyobs.images.processors.photometry) API doc
- Event <event role="send|subscribe|send subscribe"> attribute
- HttpFileCache token param + Bearer auth check + CORS headers
- Plan: pyobs-gui TelescopeWidget layout width-floor investigation
- self._slot_bindings, Ctrl+N recall / Ctrl+Alt+N bind scheme
- Image.trim() (data/mask/uncertainty alignment, CRPIX shift, catalog guard)
- .__init__
- .add_image
- IOffsetsRaDec
- .move_radec
- .night_obs
- README.md
- Install-ejabberd (xmpp)
- XmppComm._disconnected
- Autocompletion ()
- AutoFocusWidget (pyobs-gui)
- pyobs.modules.pointing (doc)
- check_changelog.sh
- delete_pubsub_nodes.py
- ejabberd 10x Shaper Benchmark Config
- list_pubsub_nodes.py
- ADR-0005: IConfig stays a stringly-keyed fallback
- Exception handling across the RPC boundary (design doc)
- ModuleLocation dataclass (nested in ModuleCapabilities)
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

## Communities (409 total, 40 thin omitted)

### Community 0 - "time.py"
Cohesion: 0.02
Nodes (80): datetime, Modules for robotic mode. TODO: write doc, Initialize a new auto focus system. Args: schedule: Object that can return…, # TODO: add abort (see old robotic/scheduler.py), Initialize a new scheduler. Args: scheduler: Scheduler to use. tasks: Task…, ObservationState, StrEnum, Abstract base class for tasks scheduler. (+72 more)

### Community 1 - "enums.py"
Cohesion: 0.04
Nodes (52): IFitsHeaderAfter, GuidingState, IAutoGuiding, IExposureTime, IStartStop, The module can perform auto-guiding., ExposureTimeState, IExposureTime (+44 more)

### Community 2 - "Time"
Cohesion: 0.03
Nodes (116): DataProvider, date, SkyCoord, Data provider for Merit classes. The ``@cache``d methods below are only safe to…, Returns the time of the last sunset., Returns the time of the last sunrise., Returns the time of the last sunset., Returns the Sun's coordinates at the given time. (+108 more)

### Community 3 - "RunningState"
Cohesion: 0.03
Nodes (76): IAbortable, Any, Interface, Abort current actions., The module has an abortable action., AcquisitionAttempt, AcquisitionResult, AcquisitionState (+68 more)

### Community 4 - "MotionStatus"
Cohesion: 0.03
Nodes (68): IDome, IReady, IDome, IPointingAltAz, IRoof, The module controls a dome, i.e. a :class:`~pyobs.interfaces.IRoof` with a…, FilterState, IFocuser (+60 more)

### Community 5 - "Module"
Cohesion: 0.05
Nodes (37): AbstractEventLoop, IConfig, IModule, setter, The module that this Comm object is attached to., The module that this Comm object is attached to., Module, Any (+29 more)

### Community 6 - "Image"
Cohesion: 0.03
Nodes (86): ImageHDU, Image, Any, CCDData, floating, HDUList, Header, NDArray (+78 more)

### Community 7 - "DynamicTarget"
Cohesion: 0.07
Nodes (37): DynamicTarget, SkyCoord, Target, Pick the best available target given current conditions. For static targets…, HeliocentricPolarTarget, SkyCoord, Target, HelioprojectiveTarget (+29 more)

### Community 8 - "utils/exceptions.py"
Cohesion: 0.02
Nodes (95): F, ISpectrograph, ICamera, IData, The module controls a camera., IData, Any, Interface (+87 more)

### Community 9 - "ImageProcessor"
Cohesion: 0.03
Nodes (58): Annotation processors doc, Some info about :class:`pyobs.images.Image`., ImageProcessor, The error handling mode for this step., Processes an image. Args: image: Image to process. Returns: Processed image., Resets state of image processor, Circle, Draw a circle on an image, optionally interpreting the center in WCS… (+50 more)

### Community 10 - "ObservationList"
Cohesion: 0.04
Nodes (72): ObservationList, Any, Add the list of scheduled tasks to the schedule. Args: tasks: Scheduled tasks., FileSystemObservationArchive, Any, date, Clear schedule after given start time. Args: start_time: Start time to clear…, Fetch schedule from portal. Returns: Dictionary with tasks. Raises: Timeout: If… (+64 more)

### Community 11 - "test_dummyradectelescope.py"
Cohesion: 0.06
Nodes (60): IOffsetsRaDec, OrbitalElements, Any, Starts tracking a body defined by orbital elements. Args: elements: Orbital…, TrackingRateCapabilities, InvalidOrbitalElementsError, _orbital_plane_to_ecliptic_cartesian(), _perifocal_to_radec() (+52 more)

### Community 12 - "test_presence.py"
Cohesion: 0.05
Nodes (51): ModuleOpenedEvent, Event to be sent when a module has opened., ModuleLocation, _FakeProxyContext, make_xmpp_comm(), asyncio, Tests for Phase 2.5 Presence and Capabilities implementation., Module.open() passes empty string for label when _label is None. (+43 more)

### Community 13 - "XmppComm"
Cohesion: 0.05
Nodes (37): Any, Interface, Store published capabilities for inclusion in disco#info responses., Return this client's own published capabilities., Fetch and deserialize capabilities for a remote module's interface. Retries…, Send XMPP presence stanza reflecting the module lifecycle state. ModuleState…, See Comm.mark_ready(). Remembers readiness on self (survives client recreation…, Subscribe to a pubsub node, retrying until the node exists. Runs as a… (+29 more)

### Community 14 - "AstrometryDotNet"
Cohesion: 0.04
Nodes (41): ImageProcessor on_error kwarg / per-step error handling, Astrometry processors doc, AstrometryDotNet (astrometry processor), Astrometry, Finds astrometric solution to a given image. Args: image: Image to analyse.…, Base class for astrometry processors, AstrometryDotNet, Any (+33 more)

### Community 15 - "FilenameFormatter"
Cohesion: 0.05
Nodes (50): Format filename with given formatter., Any, Save an image to the virtual file system and optionally broadcast a…, Init an image processor that broadcasts an image Args: filename: Filename to…, Initialize processor., Save, CreateFilename, Any (+42 more)

### Community 16 - "test_scheduler_mastermind.py"
Cohesion: 0.06
Nodes (55): Mastermind, Any, IAutonomous, IFitsHeaderBefore, Returns FITS header for the current status of this module. Args: namespaces: If…, Mastermind for a full robotic mode., MemoryObservationArchive, Returns filtered observations. Args: task: If given, only return observations… (+47 more)

### Community 17 - "_SepAperturePhotometry"
Cohesion: 0.05
Nodes (34): AperturePhotometry, Any, Base class for aperture photometry processors -- not meant to be used directly,…, Do aperture photometry on given image. Args: image: Image to do aperture…, _PhotometryCalculator, Table, Abstract class for photometry calculators., PhotUtilsPhotometry (+26 more)

### Community 18 - "DummyRoof"
Cohesion: 0.05
Nodes (45): pyobs.modules.roof (doc), BaseDome, BaseRoof, DummyRoof, DummyRoof, Any, IRoof, Get the percentage the roof is open. (+37 more)

### Community 19 - "mixins/test_fitsheader.py"
Cohesion: 0.08
Nodes (57): Any, Initialise the mixin. Args: fits_namespaces: List of namespaces for FITS…, Initialise the mixin. Args: fits_namespaces: List of namespaces for FITS…, Request FITS headers from other modules. Returns: Futures from all modules., Add requested FITS headers to header of given image. Args: image: Image with…, Any, Creates a new pipeline cammera., Grabs an image and returns reference. Args: broadcast: Broadcast existence of… (+49 more)

### Community 20 - "Event"
Cohesion: 0.06
Nodes (38): Event, Base class for all events., DataType, TypedDict, DataType, TypedDict, DataType, TypedDict (+30 more)

### Community 21 - "PipelineMixin"
Cohesion: 0.05
Nodes (43): Handle an ImageError raised by this step, when on_error == "error". Override…, PipelineMixin, Any, Mixin for a module that needs to implement an image pipeline., Initializes the mixin. Args: steps: Pipeline steps to run on images. archive:…, Resets all previous state of the involved image processors., Modules for image operations. TODO: write doc, Pipeline (+35 more)

### Community 22 - "test_astroplanscheduler.py"
Cohesion: 0.07
Nodes (44): AstroplanScheduler, Any, ObservingBlock, Actually do the scheduling, usually run in a separate process., Scheduler based on astroplan., Initialize a new scheduler. Args: twilight: astronomical or nautical, CsvPicker, Target (+36 more)

### Community 23 - "test_flatfielder.py"
Cohesion: 0.08
Nodes (60): make_flatfielder(), make_observer(), make_twilight_observer(), asyncio, parametrize, Regression test for #481: median == bias_level used to raise ZeroDivisionError., Observer stub returning a constant solar altitude for every sun_altaz() call., Observer stub distinguishing the first (now) vs second (+10min) sun_altaz()… (+52 more)

### Community 24 - "LocalComm"
Cohesion: 0.10
Nodes (23): LocalComm, Announce this module to already-connected peers, mirroring XmppComm's presence-…, Returns list of currently connected clients., Send an event to other clients., LocalNetwork, ConfigAppliedState, DummyConfig, DummyStructuredConfigModule (+15 more)

### Community 25 - "tests/test_events.py"
Cohesion: 0.08
Nodes (42): BadWeatherEvent, Event to be sent on bad weather., Create Event from a dictionary. Args: obj_dict: JSON string for event. Returns:…, FilterChangedEvent, Event to be sent when a filter has been changed., FocusFoundEvent, Event to be sent when a new best focus has been found, e.g. after a focus…, TestEvent (+34 more)

### Community 26 - "_SourceCatalog"
Cohesion: 0.09
Nodes (16): Any, floating, NDArray, PySepStatsCalculator, Any, DataFrame, floating, NDArray (+8 more)

### Community 27 - "Object"
Cohesion: 0.04
Nodes (69): PydanticBaseModel, Object, :class:`~pyobs.object.Object` is the base for almost all classes in *pyobs*. It…, Base class for all objects in *pyobs*., Whether object has been opened., Can be overloaded to quit program., Any, ConfigurationStatus (+61 more)

### Community 28 - ".__init__"
Cohesion: 0.04
Nodes (33): Any, Init new image processor. Args: on_error: How the pipeline should handle an…, Any, Init a new circle processor. Args: x: Center x coordinate. y: Center y…, Any, Init a new crosshair processor. Args: x: Center x coordinate. y: Center y…, Any, Init a new grayscale processor. Args: x: Center x coordinate. y: Center y… (+25 more)

### Community 29 - "WindowingWidget"
Cohesion: 0.17
Nodes (3): setter, Slot, WindowingWidget

### Community 30 - "Interfaces (pyobs.interfaces) API doc"
Cohesion: 0.04
Nodes (53): Interfaces (pyobs.interfaces) API doc, IAbortable, IAcquisition, IAutoFocus, IAutoGuiding, IAutonomous, IBinning, ICalibrate (+45 more)

### Community 31 - "test_control.py"
Cohesion: 0.08
Nodes (53): CasesRunner, Script for distinguishing cases., Returns FITS header for the current status of this module. Args: namespaces: If…, ConditionalRunner, Script for running an if condition., Returns FITS header for the current status of this module. Args: namespaces: If…, ParallelRunner, Script for running other scripts in parallel. (+45 more)

### Community 32 - "_DaoBackgroundRemover"
Cohesion: 0.07
Nodes (31): Source Detection processors doc, DaophotSourceDetection (detection processor), SepSourceDetection (detection processor), _DaoBackgroundRemover, Any, floating, NDArray, DaophotSourceDetection (+23 more)

### Community 33 - "LogScript"
Cohesion: 0.20
Nodes (12): DebugTriggerScript, Script for a debug trigger., LogScript, Script for logging something., asyncio, Expression has access to 'now' as a datetime., test_debug_trigger_can_run(), test_debug_trigger_sets_triggered() (+4 more)

### Community 34 - "test_lco_http.py"
Cohesion: 0.13
Nodes (30): make_observation_archive(), make_task_archive(), Create LcoTaskArchive without background tasks or Object.__init__., Create LcoObservationArchive without background tasks or Object.__init__., make_lco_task(), asyncio, get_task returns task when found in cache., get_task returns None when task not in cache. (+22 more)

### Community 35 - "BaseTelescope"
Cohesion: 0.06
Nodes (28): Any, Initializes the mixin. Args: interfaces: List of interfaces to handle or None, Any, IWeather, BaseTelescope, Any, IFitsHeaderBefore, ITelescope (+20 more)

### Community 36 - "Future"
Cohesion: 0.08
Nodes (36): Wait until all devices are in one of the given motion states. Args: abort:…, Run script. Raises: InterruptedError: If interrupted, acquire_lock(), event_wait(), Future, Any, Lock, Sets a new timeout for the method call. Cancels any existing timeout handle and… (+28 more)

### Community 37 - "VirtualFileSystem"
Cohesion: 0.08
Nodes (24): Any, DataFrame, HDUList, Convenience function for writing an Image to a FITS file. Args: filename: Name…, Convenience function that wraps around open_file() to read an Image. Args:…, Convenience function for writing an Image to a FITS file. Args: filename: Name…, Convenience function for writing bytes to a file. Args: filename: Name of file…, Convenience function for reading a CSV file into a DataFrame. Args: filename:… (+16 more)

### Community 38 - "xmppcomm.py"
Cohesion: 0.10
Nodes (29): _dataclass_to_xml(), _event_schema_to_xml(), _interface_schema_to_xml(), _parse_scalar(), Any, Element, Shared XML serializer for pyobs 2.0 (urn:pyobs:rpc:1). Both the state pub/sub…, Deserialize an XML element (produced by ``value_to_xml``) to a Python value.… (+21 more)

### Community 39 - "test_follow.py"
Cohesion: 0.08
Nodes (30): build_skycoord(), FollowMixin, get_coords(), Any, IPointingAltAz, IPointingRaDec, SkyCoord, Returns True, if we're following another device. (+22 more)

### Community 40 - "test_yaml_archives.py"
Cohesion: 0.24
Nodes (28): make_obs(), make_obs_archive(), make_task(), make_task_archive(), asyncio, Verify observations are actually written to disk in valid YAML., test_add_and_load_observations(), test_add_empty_list_is_noop() (+20 more)

### Community 41 - "test_lcoscript.py"
Cohesion: 0.11
Nodes (24): LcoScript, Script for LCO configs. Dispatches to one of the named scripts in ``scripts``,…, Build the script selected via the configuration's extra_params["script_name"].…, Whether this config can currently run. Returns: True, if the script can run now, Run script. Raises: InterruptedError: If interrupted, Returns FITS header for the current status of this module. Args: namespaces: If…, FakeScript, make_lco_script() (+16 more)

### Community 42 - "BaseVideo"
Cohesion: 0.07
Nodes (19): IVideo, BaseVideo, IImageType, Response, Whether the server is started., Handles access to / and returns HTML page. Args: request: Request to respond…, Handles GET access to /ping for testing connectivity. Args: request: Request to…, Handles access to /video.mjpg and returns the video. Args: request: Request to… (+11 more)

### Community 43 - "Comm"
Cohesion: 0.04
Nodes (41): Comm responsibility: Discovery (clients_with_interface), Comm responsibility: Events (broadcast typed events), Comm, Any, Interface, ProxyType, Get a proxy to the given client. Args: client: Name of client. Returns: Proxy…, Fetch capabilities for a single interface and push them into the given proxy… (+33 more)

### Community 44 - "test_transit_mastermind.py"
Cohesion: 0.06
Nodes (52): EarthLocation, SkyCoord, Merit function for observing transits., Returns the time of the next mid-transit., Returns the time until which observations should run: mid-transit + duration/2…, TransitMerit, Configuration, InstrumentConfig (+44 more)

### Community 45 - "robotic/test_scheduler.py"
Cohesion: 0.13
Nodes (39): Scheduler, DummyTask, make_async_gen(), make_obs(), make_scheduler(), asyncio, Regression test: _on_task_finished is registered for both TaskFinishedEvent and…, _state_for() (+31 more)

### Community 46 - "StandAlone"
Cohesion: 0.09
Nodes (40): pyobs.modules.test (doc), StandAlone, Quickstart (doc), pyobs-core (pip package), Test modules. TODO: write doc, Any, Example module that only logs the given message forever in the given interval., Creates a new StandAlone object. Args: message: Message to log in the given… (+32 more)

### Community 47 - "PyobsError"
Cohesion: 0.06
Nodes (29): Exception, Declare that the given PyobsError types (and their subclasses) fire often…, Watch for repeated occurrences of exc_type -- optionally scoped to a specific…, Records exception for severity tracking (see _register_exception) and fires any…, Whether exception should count as an instance of exc_type for severity-handler…, Checks all handlers against all recorded exceptions and returns those whose…, Execute a local method safely with type conversion All incoming variables in…, AbortedError (+21 more)

### Community 48 - "CLI"
Cohesion: 0.16
Nodes (9): CLI, Initializes a new instance of the CLI class., Overwrite this to set CLI parameters with argparse., Overwrite this to actually run the CLI., Load config from config file, Load config from environment variables., main(), PyobsDaemonCLI (+1 more)

### Community 49 - "test_stellarexptime.py"
Cohesion: 0.09
Nodes (37): ExposureTimeProvider, Determine and return the exposure time in seconds. Returns: Exposure time in…, Abstract base class for providers that determine camera exposure time., ndarray, Find the brightest star near the image centre by fitting a 2D Gaussian. Args:…, Determines exposure time by finding a star near the image centre and adjusting…, Determine the optimal exposure time. Returns: Optimal exposure time in seconds., StellarExposureTimeProvider (+29 more)

### Community 50 - "StarExpTimeEstimator"
Cohesion: 0.07
Nodes (27): Exposure Time estimators doc, ExpTimeEstimator (exptime processor base), StarExpTimeEstimator (exptime processor), ExpTime, ExpTimeEstimator, Any, Estimate exposure time., Init new exposure time estimator. (+19 more)

### Community 51 - "RPC"
Cohesion: 0.08
Nodes (23): fault_to_xml(), params_to_xml(), Any, ClientXMPP, Element, Exception, Parse <fault> and return (exception_qualified_name, message)., RPC wrapper around XEP-0009 using pyobs 2.0 payload encoding (urn:pyobs:rpc:1). (+15 more)

### Community 52 - "WindowCapabilities"
Cohesion: 0.14
Nodes (27): ModuleCapabilities, WindowCapabilities, make_module(), Minimal module stub satisfying what XmppComm needs on connect. IModule must be…, get_capabilities_from_disco(), Integration tests for Phase 2.5 Presence and Discovery. Requires a live…, LOCAL state must arrive as away presence., Module.set_state() must automatically push presence — no explicit call. (+19 more)

### Community 53 - "test_shellcommand.py"
Cohesion: 0.10
Nodes (29): ParserState, Any, Enum, ShellCommand, ShellCommandResponse, asyncio, test_command_number_increments(), test_execute_invalid_param() (+21 more)

### Community 54 - "Calibration"
Cohesion: 0.09
Nodes (21): Additional Modules index (docs), Image processors index (docs), Calibration processors doc, Calibration, Calibrate an image. Args: image: Image to calibrate. Returns: Calibrated image., Calibrate an image using master bias, dark, and flat frames fetched from an…, Find master calibration frame for given parameters using a cache. Args:…, _CCDDataCalibrator (+13 more)

### Community 55 - ".get_object"
Cohesion: 0.10
Nodes (19): ObjectClass, create_object(), get_object(), get_safe_object(), Any, ProxyType, Calls get_object in a safe way and returns None, if an exceptions thrown. Args:…, Create object from dict config. Args: config: Config to create object from… (+11 more)

### Community 56 - "Publisher"
Cohesion: 0.29
Nodes (7): LogPublisher, MultiPublisher, Any, Forwards a message to multiple publishers., Initialize new multi publisher. Args: publishers: Publishers to forward…, Publish the given results. Args: **kwargs: Results to publish., Publisher

### Community 57 - "http_request_with_retries"
Cohesion: 0.18
Nodes (26): http_request_paginated(), http_request_with_retries(), Any, ClientSession, Fetches all pages of a DRF-style paginated list endpoint and returns the…, retry, make_response(), make_session() (+18 more)

### Community 58 - "test_units.py"
Cohesion: 0.10
Nodes (25): _extract_unit(), _interface_unit_hints(), Any, Return Unit annotations from the abstract interface declaration for method_name., Convert annotated float parameters to astropy Quantities before the method…, with_units(), Focuser, IFocus (+17 more)

### Community 59 - "Proxy"
Cohesion: 0.06
Nodes (34): Comm responsibility: Method calls (via Proxy), The Comm object is responsible for all communication between modules (see…, Proxy, _ProxyContext, Any, Interface, ProxyType, Signature (+26 more)

### Community 60 - "IOffsetsAltAz.py"
Cohesion: 0.11
Nodes (20): IOffsetsAltAz, AltAzOffsetState, IOffsetsAltAz, Interface, The module supports Alt/Az offsets, usually combined with…, IPointingBody, Any, Interface (+12 more)

### Community 61 - "test_basevideo.py"
Cohesion: 0.16
Nodes (34): ImageRequest, make_basevideo(), make_request(), asyncio, test_activate_camera_from_inactive_calls_hook(), test_activate_camera_when_already_active_skips_hook(), test_active_update_deactivates_after_sleep_timeout(), test_active_update_skips_deactivate_when_recently_active() (+26 more)

### Community 62 - "IPointingAltAz"
Cohesion: 0.06
Nodes (29): IPointingAltAz, Any, DEGREES, Interface, The module can move to Alt/Az coordinates, usually combined with…, Moves to given coordinates. Args: alt: Alt in deg to move to. az: Az in deg to…, Modules for performing flatfields. TODO: write doc, FlatFieldPointing (+21 more)

### Community 63 - "AirmassConstraint"
Cohesion: 0.12
Nodes (33): AirmassConstraint, ndarray, SkyCoord, make_dynamic_task(), make_vfs(), asyncio, integration, Path (+25 more)

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
Cohesion: 0.12
Nodes (34): Open the connection to the XMPP server. Returns: Whether opening was successful., attach_module(), env_config(), main(), make_comm(), maybe_register(), open_publisher(), Any (+26 more)

### Community 68 - "scripts/autofocus.py"
Cohesion: 0.17
Nodes (8): LcoAutoFocusScript, Auto focus script for LCO configs., Whether this config can currently run. Returns: True, if the script can run now, Run script. Raises: InterruptedError: If interrupted, # TODO: unfortunately this never happens, since the LCO portal forces…, DuplicateFilter, Any, Logging filter that removes duplicate entries. Should be used with new logger,…

### Community 69 - "Offsets"
Cohesion: 0.11
Nodes (15): PixelOffsets, CorrelationMaxCloseToBorderError, Exception, DummyOffsets, Attach a dummy offset metadata entry using a class resolved from its name, for…, Offsets, Base class for determining offsets., Processes an image and sets x/y pixel offset to reference in meta data. Args:… (+7 more)

### Community 70 - ".now"
Cohesion: 0.10
Nodes (27): Observer, ObservationArchiveEvolution, date, Observer, Populates the task cache and the one real night (anchored to `start`) up front.…, Freezes observation cache. After this: a task-id miss raises RuntimeError; a…, Returns list of observations for the given task. Args: date: Date of night to…, Any (+19 more)

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
Cohesion: 0.05
Nodes (45): MoonSeparationConstraint, ndarray, SkyCoord, Moon separation constraint., model_validator, Self, SkyCoord, Target (+37 more)

### Community 75 - "PyobsDaemon"
Cohesion: 0.14
Nodes (10): Any, PyobsDaemon, Return the bare module name from a config or PID file path., Strip a leading underscore, which marks a module as disabled. PID and log files…, Return sorted module names from *.yaml files, excluding *.shared.yaml., Read and return the PID from the module's PID file, or None., Return the live PID for a module, or None. Cleans up stale PID files., Return uptime (seconds) and rss_mb for a running PID. No CPU -- that needs a… (+2 more)

### Community 76 - "MockWeather"
Cohesion: 0.11
Nodes (26): pyobs.modules.weather (doc), MockWeather, Weather (module), MockWeather, Any, IFitsHeaderBefore, IWeather, Returns FITS header for the current status of this module. Args: namespaces: If… (+18 more)

### Community 77 - "test_config.py"
Cohesion: 0.10
Nodes (31): include_parts(), pre_process_yaml(), Any, Replaces blocks of the form {include <source.yaml> <key>} in the loaded config…, Include nested contents from another YAML file. Args: include: dictionary based…, Finds anchors ('&') in the included file. Args: filename: name of the file with…, Replaces aliases ('<<: *...') in the main file by the anchor in the included…, reload_anchors() (+23 more)

### Community 78 - "Pipeline"
Cohesion: 0.13
Nodes (18): Pipeline, Any, Create master bias frame. Args: images: List of raw bias frames. Returns:…, Create master dark frame. Args: images: List of raw dark frames. bias: Bias…, Create master flat frame. Args: images: List of raw flat frames. bias: Bias…, Calibrate a single science frame. Args: image: Image to calibrate. Returns:…, Pipeline based on the astropy package ccdproc., Pipeline for science images. Args: steps: List of pipeline steps to perform.… (+10 more)

### Community 79 - "test_acquisition.py"
Cohesion: 0.06
Nodes (84): ApplyAltAzOffsets, Any, EarthLocation, ITelescope, Apply offsets from a given image to a given telescope., Initializes a new ApplyAltAzOffsets. Args: min_offset: Min offset in arcsec to…, Take the pixel offsets stored in the meta data of the image and apply them to…, ApplyOffsets (+76 more)

### Community 80 - "Weather"
Cohesion: 0.06
Nodes (45): Any, ClientSession, WeatherApi, Any, IFitsHeaderBefore, IWeather, Builds the current per-sensor readings from the last raw status, for state…, Returns FITS header for the current status of this module. Args: namespaces: If… (+37 more)

### Community 81 - "SolarElevationConstraint"
Cohesion: 0.17
Nodes (27): AtNightConstraint, Solar elevation constraint., SolarElevationConstraint, constraint(), data(), observer(), asyncio, fixture (+19 more)

### Community 82 - "SkyOffsets"
Cohesion: 0.10
Nodes (22): BaseCoordinateFrame, Angle, SkyCoord, Returns separatation between both coordinates, either in their own or a given…, Calculates spherical offset from first coordinate to second. Args: frame:…, Args: frame: Coordinate frame to use, or None to use coordinates' own frames.…, SkyOffsets, DummySkyOffsets (+14 more)

### Community 83 - "test_backend_archives.py"
Cohesion: 0.21
Nodes (30): make_obs(), make_obs_archive(), make_task(), make_task_archive(), asyncio, time parameter is unused — backend returns cached observations., Backend uses strictly exclusive boundaries (start < time < end)., fetch_task is called with task_archive when provided. (+22 more)

### Community 84 - "Portal"
Cohesion: 0.13
Nodes (11): Portal, Any, Do a GET request on the portal. Args: url: URL to request. Returns: Response…, Clear schedule after given start time. Args: start: Start time to clear…, Submit observations. Args: observations: List of observations to submit., Send report to LCO portal Args: status_id: id of config status status: Status…, Delay re-attempt to send report to LCO portal Args: status_id: id of config…, Fetch schedule from portal. Args: start_before: Task must start before this… (+3 more)

### Community 85 - "Ring"
Cohesion: 0.14
Nodes (9): integer, Any, floating, NDArray, Estimate pixel guiding offsets from asymmetry of spilled light around a fiber…, Init an image processor that adds the calculated offset. Args: fibers:…, Processes an image and sets x/y pixel offset to reference in offset attribute.…, Ring (+1 more)

### Community 86 - "DummySolarTelescope"
Cohesion: 0.06
Nodes (44): IPointingHelioprojective, HeliocentricPolarState, IPointingHeliocentricPolar, Any, DEGREES, Interface, The module can move to Heliocentric Polar (Mu/Psi) coordinates, usually…, Moves on given coordinates. Args: mu: Cosine of the angular distance from Sun… (+36 more)

### Community 87 - "XmppClient"
Cohesion: 0.08
Nodes (19): Any, Disconnect only, instead of slixmpp's default reconnect-in-place. xep_0199's…, Called when the server sends a <stream:error/>, e.g. when this connection gets…, Whether this client was (or is being) kicked because another session connected…, Human-readable reason text sent alongside the conflict stream error, if any., Wait for client to connect. Returns: Success or not., XMPP client for pyobs., Session start event. Args: event: The event sent at session start. (+11 more)

### Community 88 - "_AbortableModule"
Cohesion: 0.20
Nodes (23): Callback for flat-field class to call with statistics., FocusError, _AbortableModule, Any, asyncio, Exception, IAbortable, Minimal test module whose abort() raises whatever exception it's given. Starts… (+15 more)

### Community 89 - "DummyCamera"
Cohesion: 0.10
Nodes (13): ICooling, IGain, IImageFormat, DummyCamera, Any, Header, IBinning, IWindow (+5 more)

### Community 90 - "Application"
Cohesion: 0.11
Nodes (26): Application, React to signals and quit the module., Actually run the application., Force astropy's IERS-A table and leap-second table to be loaded/downloaded now,…, Class for initializing and shutting down a pyobs process., _warm_iers_cache(), make_bare_application(), Any (+18 more)

### Community 91 - "DummyComm"
Cohesion: 0.10
Nodes (20): DummyComm, Any, Interface, A dummy implementation of the Comm interface., Creates a new dummy comm. Args: name: Name to report for this comm. Defaults to…, Always return zero clients., No interfaces implemented., Interfaces are never supported. (+12 more)

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
Cohesion: 0.11
Nodes (18): ArchiveFile, Wraps a file in an archive. To be used in combination with pyobs-archive., Creates a new archive file. Args: name: Name of file. mode: Open mode (r/w).…, If in write mode, actually send the file to the archive., HttpFile, Any, Read number of bytes from stream. Args: n: Number of bytes to read. Read until…, Write data into the stream. Args: s: Bytes of data to write. (+10 more)

### Community 96 - "Constraint"
Cohesion: 0.13
Nodes (10): Constraint, Any, ndarray, SkyCoord, Returns a boolean mask of candidates passing this constraint. Default…, MoonIlluminationConstraint, Moon illumination constraint., TimeConstraint (+2 more)

### Community 97 - "application.py"
Cohesion: 0.09
Nodes (18): _disable_iers_auto_download(), GuiApplication, InfluxLogConfig, Any, TypedDict, Derived Application class that uses a Qt GUI. Allows for graceful shutdown in…, Create a new GUI application., Initializes a pyobs application. Exactly one of `config`/`module_factory` must… (+10 more)

### Community 98 - "FocusSeries"
Cohesion: 0.13
Nodes (10): FocusSeries, Analyse given image. Args: image: Image to analyse focus_value: Value to fit…, Returns a list of data points., Fit focus from analysed images Returns: Tuple of new focus and its error, Base class for focus series helper classes., PhotometryFocusSeries, Focus series based on source detection., Analyse given image. Args: image: Image to analyse focus_value: Value to fit… (+2 more)

### Community 99 - "SepSourceDetection"
Cohesion: 0.16
Nodes (17): Background, Any, floating, NDArray, Initializes a wrapper for SEP. See its documentation for details. Highly…, Find stars in given image and append catalog. Args: image: Image to find stars…, Remove background from image in data. Args: data: Data to remove background…, Detect astronomical sources using SEP (Source Extractor for Python). This… (+9 more)

### Community 100 - "make_proxy_cm"
Cohesion: 0.21
Nodes (27): make_proxy_cm(), Wrap value in a MagicMock standing in for the async context manager returned by…, make_flatfield(), asyncio, Find the state object set_state() was called with for the given interface., _ready_telescope(), _state_for(), test_abort_sets_event() (+19 more)

### Community 101 - "_DotNetRequest"
Cohesion: 0.22
Nodes (4): _DotNetRequest, Any, asyncio, test_generate_request_error_msg()

### Community 102 - "ScriptRunner"
Cohesion: 0.13
Nodes (16): calc_run_timeout(), Any, IRunnable, Calculates timeout for run()., Module for running a script., Initialize a new script runner. Args: script: Config for script to run., Run script. Raises: ScriptError: If the script failed (e.g. a proxy/network…, Abort current actions. (+8 more)

### Community 103 - "ResolvableErrorLogger"
Cohesion: 0.17
Nodes (9): Any, Creates a new LCO scheduler. Args: url: URL to portal site: Site filter for…, Any, Logger, Logging for resolvable errors. Args: logger: Logger to use. error_level: Log…, Log an error message., ResolvableErrorLogger, create_logger() (+1 more)

### Community 104 - "test_coordinates.py"
Cohesion: 0.15
Nodes (25): offset_altaz_to_radec(), offset_radec_to_altaz(), EarthLocation, SkyCoord, make_altaz(), make_radec(), SkyCoord, Zero offset returns (0, 0). (+17 more)

### Community 105 - "get_registered_interface"
Cohesion: 0.12
Nodes (22): get_registered_interface(), Look up a registered interface class by name, or None if unknown., All currently-registered interface classes, keyed by name., registered_interfaces(), Tests for the import-time interface registry in pyobs/interfaces/interface.py.…, Re-importing the same interface module twice resolves to the same class object…, Two genuinely different classes claiming the same name must raise TypeError…, Mutating the returned dict must not affect the live registry. (+14 more)

### Community 106 - "OnSkyDistance"
Cohesion: 0.13
Nodes (16): OnSkyDistance, Angle, BrightestStarOffsets, Angle, Any, Table, Processes an image and sets x/y pixel offset to reference in offset attribute.…, Compute pixel offsets from the image center to the brightest star and store… (+8 more)

### Community 107 - "LocalArchive"
Cohesion: 0.33
Nodes (25): LocalArchive, Connector class to a local image archive., make_frame_headers(), asyncio, Path, test_download_frames_loads_real_files(), test_download_frames_skips_frames_without_filename(), test_download_headers_returns_header_dicts() (+17 more)

### Community 108 - "_AbortableModule"
Cohesion: 0.10
Nodes (21): _AbortableModule, Any, asyncio, IAbortable, IStartStop, parametrize, Minimal test module with one guarded (non-whitelisted) RPC method., Module implementing IStartStop, whose abstract `start(**kwargs)` RPC method has… (+13 more)

### Community 109 - "_PhotUtilAperturePhotometry"
Cohesion: 0.17
Nodes (12): ApertureMask, CircularAperture, _PhotUtilAperturePhotometry, Any, floating, NDArray, Table, Any (+4 more)

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
Cohesion: 0.09
Nodes (12): Any, JSON representation of event., String representation of event., Generic from_dict method for derived classes that don't need their own., Any, Any, Any, ModeChangedEvent (+4 more)

### Community 115 - ".__init__"
Cohesion: 0.10
Nodes (13): Args: label: Label for module. If None, name is used. own_comm: If True, module…, Returns name of module., List interfaces and methods of this module., Returns a dictionary with config caps., Check for getter and setter Params: name: Name of variable. Returns: Tuple of…, Returns dict of all config capabilities. First value is whether it has a…, Args: modules: Dictionary with modules. shared: Shared objects between modules., Any (+5 more)

### Community 116 - "ImagingScript"
Cohesion: 0.17
Nodes (8): ImagingScript, Any, Target, Run script. Raises: InterruptedError: If interrupted, Returns FITS header for the current status of this module. Args: namespaces: If…, Return the exposure time, computing it dynamically if needed., Default script for imaging configs., Whether this config can currently run. Returns: True, if the script can run now

### Community 117 - "BackendTaskArchive"
Cohesion: 0.11
Nodes (12): BackendTaskArchive, ClientSession, Task archive based on pyobs-robotic-backend., Opens the backend task archive., Closes the backend observation archive., Update tasks in background., Fetches last schedule update time., Fetch projects from backend. (+4 more)

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
Cohesion: 0.24
Nodes (5): Any, VFS wrapper for a file that can be accessed over a SFTP connection., Open/create a file over a SSH connection. Args: name: Name of file. mode: Open…, Returns content of given path. Args: path: Path to list. kwargs: Parameters for…, SFTPFile

### Community 124 - "WeatherSensors"
Cohesion: 0.04
Nodes (64): IFocusModel, IAutonomous, IStartStop, The module does some autonomous actions, mainly used for warnings to users., IFilters, Any, IMotion, The module can change filters in a device. (+56 more)

### Community 125 - "TaskFinishedEvent"
Cohesion: 0.13
Nodes (10): Any, Event to be sent when a task has failed., Initializes a new task failed event. Args: name: Name of task that just…, TaskFailedEvent, Any, Event to be sent when a task has finished., Initializes a new task finished event. Args: name: Name of task that just…, TaskFinishedEvent (+2 more)

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

### Community 130 - "MoveAltAzEvent"
Cohesion: 0.13
Nodes (12): DataTypeAltAz, DataTypeRaDec, MoveAltAzEvent, MoveEvent, MoveRaDecEvent, Any, TypedDict, Event to be sent when moving to RA/Dec. (+4 more)

### Community 131 - "Test Localcomm (local)"
Cohesion: 0.18
Nodes (22): make_comm(), asyncio, fixture, Sender also receives its own events., Reset LocalNetwork singleton between tests., #677: a late-joining module must announce itself via ModuleOpenedEvent once…, get_interfaces returns [] when the remote client has no module., reset_network() (+14 more)

### Community 132 - "GoodWeatherEvent"
Cohesion: 0.11
Nodes (14): Comm API doc (pyobs.comm), Events API doc (pyobs.events), ExposureStatusChangedEvent, Any, Event to be sent, when the exposure status of a device changes., GoodWeatherEvent, Any, Event to be sent on good weather. (+6 more)

### Community 133 - "test_pyobsd.py"
Cohesion: 0.29
Nodes (9): make_daemon(), Any, parametrize, Tests for PyobsDaemon._start_service()'s command construction -- in particular,…, file_log defaults to False -- --log-file is opt-in, not unconditional., test_start_service_creates_log_path_only_when_file_log_enabled(), test_start_service_creates_log_path_when_file_log_enabled(), test_start_service_default_is_no_file_log() (+1 more)

### Community 134 - "test_dummymode.py"
Cohesion: 0.10
Nodes (27): IMode, IMode, ModeCapabilities, ModeState, Any, Interface, The module can change modes in a device., Set the current mode. Args: mode: Name of mode to set. group: Name of the group… (+19 more)

### Community 135 - "ProjectionFocusSeries"
Cohesion: 0.16
Nodes (11): ProjectionFocusSeries, Any, floating, NDArray, Returns a list of data points., Fit focus from analysed images Returns: Tuple of new focus and its error, Creates a sine window function of the same size as some 1-D array "arr".…, Removes global slopes and fills up bad rows (ybad) or columns (xbad). (+3 more)

### Community 136 - "OffsetsAltAzEvent"
Cohesion: 0.13
Nodes (12): DataTypeAltAz, DataTypeRaDec, OffsetsAltAzEvent, OffsetsEvent, OffsetsRaDecEvent, Any, TypedDict, Event to be sent when an RA/Dec offset is to be moved. (+4 more)

### Community 137 - "test_autofocus.py"
Cohesion: 0.27
Nodes (18): isinstance_class(), Shared test-double helpers used across multiple test modules., Build a fresh class purely for isinstance() checks against a MagicMock.…, make_autofocus(), make_script(), make_task(), make_telescope(), asyncio (+10 more)

### Community 138 - "Grid"
Cohesion: 0.09
Nodes (19): AvoidMoon, GridFilter, Any, Initialize the conversion filter. Args: grid: Upstream grid or filter that…, Abstract base class for grid filters that wrap another GridNode. A GridFilter…, Initialize the frame conversion filter. Args: grid: Upstream grid or filter…, Initialize the randomizer. Args: grid: Upstream grid or filter. iterations:…, Initialize a filter with an underlying grid. Args: grid: The upstream GridNode… (+11 more)

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
Cohesion: 0.14
Nodes (9): is_valid_jid(), Whether jid is a valid user@domain or user@domain/resource JID -- exactly what…, asyncio, JID parsing/validation in XmppComm.__init__ and the reusable is_valid_jid()…, The actual production bug this was found from: a JID ending in "/" with nothing…, re.match alone doesn't anchor the end -- confirms the pattern is anchored so…, async def, not plain def -- XmppComm.__init__ calls asyncio.get_event_loop(),…, TestIsValidJid (+1 more)

### Community 143 - "_CalibrationCache"
Cohesion: 0.17
Nodes (9): _CalibrationCache, Any, Init a new image calibration pipeline step. Args: archive: Archive to fetch…, mock_image(), fixture, test_add_to_cache(), test_add_to_cache_size(), test_find_cache_entry_emtpy() (+1 more)

### Community 144 - "test_dummyvideo.py"
Cohesion: 0.14
Nodes (17): Creates a new BaseWebcam. On the receiving end, a VFS root with a HTTPFile must…, DummyVideo, Any, IExposureTime, A dummy video module for testing — streams simulated noise frames., Creates a new dummy video module. Args: fps: Frames per second to simulate.…, Set the exposure time (frame interval). Args: exposure_time: Exposure time in…, Background task that generates simulated frames. (+9 more)

### Community 145 - "fit_hyperbola"
Cohesion: 0.18
Nodes (16): fit_hyperbola(), Fit a hyperbola Args: x_arr: X data y_arr: Y data y_err: Y errors Returns:…, Fit focus from analysed images Returns: Tuple of new focus and its error, make_hyperbola(), ndarray, Generate clean hyperbola data: b * sqrt((x-c)^2/a^2 + 1)., fit_hyperbola recovers the minimum position of a clean hyperbola., fit_hyperbola returns (minimum, variance). (+8 more)

### Community 146 - "Scheduler"
Cohesion: 0.13
Nodes (9): Any, IRunnable, IStartStop, Compares two lists of tasks and returns two lists, containing those that are…, Trigger a re-schedule., Re-schedule when task has started and we can predict its end. Args: event: The…, Reset current task, when it has finished or failed. Args: event: The task…, Re-schedule on incoming good weather event. Args: event: The good weather… (+1 more)

### Community 147 - "RollingTimeAverage"
Cohesion: 0.10
Nodes (24): Any, Runs an async callable to completion on a dedicated worker thread, off the…, run_cpu_bound(), RollingTimeAverage, _T, asyncio, test_run_cpu_bound_propagates_exception(), test_run_cpu_bound_returns_value() (+16 more)

### Community 148 - "test_localcomm_state.py"
Cohesion: 0.09
Nodes (28): asyncio, fixture, Tests for LocalComm state, capabilities, and presence., set_presence stores and get_client_state retrieves., Default presence is READY with no error string., subscribe_presence fires callback immediately with the current presence state., subscribe_presence callback is called whenever presence changes., Reset LocalNetwork singleton before each test. (+20 more)

### Community 149 - "CsvPublisher"
Cohesion: 0.31
Nodes (6): CsvPublisher, Any, DataFrame, Initialize new CSV publisher. Args: filename: Name of file to log in., Publish the given results. Args: **kwargs: Results to publish., Return data that has so far been published.

### Community 150 - "Plan: pyobs 2.0 rollout (work plan)"
Cohesion: 0.10
Nodes (21): XmppComm._register_events add_interest (XEP-0163), LogEvent Double-Delivery Investigation (SAAO/monet), Root cause: dual PEP delivery paths (implicit roster + explicit interest), XmppComm._safe_send retry-on-timeout (ruled out), AstrometryDotNet migrated to handle_error, Plan: Per-step error control in image processing pipelines, ExceptionHandler nested wrapper (#328, rejected), on_error kwarg + handle_error() override point (+13 more)

### Community 151 - "`OBSNUM`: per-night observation counter in FITS headers"
Cohesion: 0.22
Nodes (8): Migration, `OBSNUM`: per-night observation counter in FITS headers, Problem, Proposed design, Still open (not resolved by this doc), When is `obsnum` assigned: scheduled, or observed?, Where the pieces actually are, Why this determines the design, not just where to put a function

### Community 152 - "3rd party packages (doc)"
Cohesion: 0.11
Nodes (20): 3rd party packages (doc), Astroplan, Astropy, Astroquery, Cython, LMFIT, matplotlib, NumPy (+12 more)

### Community 153 - "Any"
Cohesion: 0.13
Nodes (10): Any, Interface, Store capabilities locally., Return this client's own published capabilities., Fetch capabilities from a remote module., Returns list of interfaces for given client., Checks whether the given client supports the given interface., Execute a given method on a remote client. (+2 more)

### Community 154 - "SSHFile"
Cohesion: 0.12
Nodes (12): Any, VFS wrapper for a file that can be accessed over a SFTP connection., Write data into the stream. Args: b: Bytes of data to write., If in write mode, actually send the file to the SSH server., Returns content of given path. Args: path: Path to list. kwargs: Parameters for…, Open/create a file over a SSH connection. Args: name: Name of file. mode: Open…, For read access, download the file into a local buffer. Raises:…, Read number of bytes from stream. Args: n: Number of bytes to read. Read until… (+4 more)

### Community 155 - "create_rst.py"
Cohesion: 0.33
Nodes (18): create_image_processors_rst(), create_modules_rst(), create_rst_overview(), create_utils_rst(), find_classes_in_modules(), find_python_modules(), find_submodules(), Any (+10 more)

### Community 156 - "GuidingStatistics"
Cohesion: 0.08
Nodes (19): IN, OUT, Initializes a new science frame auto guiding system. Args: max_exposure_time:…, GuidingStatistics, Any, Calculates statistics for guiding., Inits a stat measurement session for a client. Args: client: name/id of the…, Add statistics to given header. Args: client: id/name of the client header:… (+11 more)

### Community 157 - "SoftBin"
Cohesion: 0.16
Nodes (11): Any, floating, NDArray, Bin a 2D image by averaging non-overlapping blocks, updating relevant FITS…, Init a new software binning pipeline step. Args: binning: Binning to apply to…, Bin an image. Args: image: Image to bin. Returns: Binned image., SoftBin, asyncio (+3 more)

### Community 158 - "AddMask"
Cohesion: 0.21
Nodes (13): AddMask, Any, floating, NDArray, Add mask to image. Args: image: Image to add mask to. Returns: Image with mask, Attach a precomputed mask to an image based on instrument and binning. This…, Init an image processor that adds a mask to an image. Args: masks: Dictionary…, asyncio (+5 more)

### Community 159 - "Archive"
Cohesion: 0.12
Nodes (13): Archive, FrameInfo, Base class for frame infos., Base class for image archives., Any, TypedDict, PyobsArchive, PyobsArchiveFrameInfoDict (+5 more)

### Community 160 - "RandomizeGrid"
Cohesion: 0.12
Nodes (11): SkyCoord, RandomizeGrid, Return the next point that satisfies all constraints. Iterates underlying…, Convert the next tuple to a SkyCoord. Expects a tuple (x_deg, y_deg) from the…, Transform the next SkyCoord to the target frame. Returns: A SkyCoord…, Randomize iteration order by rotating the underlying sequence. For each…, Yield a point after rotating the underlying grid a random number of times.…, Yield a point after rotating the underlying grid a random number of times.… (+3 more)

### Community 161 - "comm/test_events.py"
Cohesion: 0.18
Nodes (15): asyncio, Tests for Comm.register_event / unregister_event. Covers…, Two independent subscribers for the same event: one tearing down must not un-…, A module that both sends an event (handler-less register_event()) and…, unregister must mirror the exact same derived-events expansion register_event…, Two independent subscribers (e.g. two widget instances for the same event type)…, Once the last handler for an event is unregistered, the event must no longer be…, test_unregister_event_drops_subscribed_role_when_last_handler_removed() (+7 more)

### Community 162 - "_event_role"
Cohesion: 0.39
Nodes (7): _event_role(), Space-separated role(s) ("send", "subscribe", or both) for an event class, for…, Tests for XmppComm's disco#info event role tagging. See specs/plans/event-role-…, test_event_role_ignores_unrelated_events(), test_event_role_send_and_subscribe(), test_event_role_send_only(), test_event_role_subscribe_only()

### Community 163 - "pyobs/modules/utils/__init__.py"
Cohesion: 0.09
Nodes (13): FluentLogger, Log to fluentd server., Process a new log entry. Args: event: The log event. sender: Name of sender., Utilities TODO: write doc, Matrix, Drain the message queue and send messages one at a time. Sending sequentially…, Process a new log entry. Args: entry: The log event. sender: Name of sender., Any (+5 more)

### Community 164 - "NewImageEvent"
Cohesion: 0.10
Nodes (24): NewImageEvent, Any, Event to be sent on a new image., Initializes new NewImageEvent. Args: filename: Name of new image file.…, ImageWriter, Any, Writes new images to disk., Creates a new image writer. Args: filename: Pattern for filename to store… (+16 more)

### Community 165 - "ExpTimeEval"
Cohesion: 0.11
Nodes (15): ExpTimeEval, Any, Observer, Return list of binnings., Return list of filters., Estimate exposure time for given filter Args: solalt: Solar altitude. binning:…, Initialize object with the given time. Args: time: Start time for all further…, Estimates exposure time for a given filter and binning at a given time offset… (+7 more)

### Community 166 - "Stellarium"
Cohesion: 0.16
Nodes (6): BaseTransport, Exception, Send coordinates to clients., A stellarium telescope., Stellarium, StellariumProtocol

### Community 167 - "Overview (doc)"
Cohesion: 0.18
Nodes (17): Overview (doc), Access control (ACL), Comm, Events, Interface, Module (base class), Object (base class), Location / astroplan.Observer (+9 more)

### Community 168 - "test_schedulewriter.py"
Cohesion: 0.25
Nodes (16): make_portal(), Shared helpers for LCO tests., Create Portal bypassing Object.__init__ and aiohttp session., make_configdb(), make_lco_observation(), make_writer(), asyncio, test_add_schedule_calls_portal() (+8 more)

### Community 169 - "MultiModule"
Cohesion: 0.14
Nodes (9): MultiModule, Wait until all sub-module tasks have finished., Cancel sub-module tasks and close shared objects., Quit all sub-modules., Wrapper for running multiple modules in a single process., Checks, whether this multi-module contains a module of given name., Returns module of given name., Open MultiModule. Shared/non-module child objects are opened normally. Each… (+1 more)

### Community 170 - "FileSystemTaskArchive"
Cohesion: 0.15
Nodes (9): FileSystemTaskArchive, Any, Task archive based on files., Creates a new filesystem-based task archive. Args: extension: Extension of…, Returns time when last time any blocks changed., Returns list of projects. Returns: List of projects., Returns list of schedulable tasks. Returns: List of schedulable tasks, Returns the task with the given ID. Returns: Task with given ID. (+1 more)

### Community 171 - "Kiosk"
Cohesion: 0.09
Nodes (10): Kiosk, Any, ICamera, IStartStop, Response, Thread for taking images., A kiosk mode for a pyobs camera that takes images and published them via HTTP., Initializes file cache. Args: camera: Camera to use for kiosk mode. port: Port… (+2 more)

### Community 172 - "test_grab_sequence.py"
Cohesion: 0.29
Nodes (16): make_camera(), asyncio, Tests for BaseCamera.grab_sequence()/abort_sequence(), the IDataSequence…, grab_sequence() must not block for the whole sequence -- see design doc: a…, test_abort_clears_running_sequence(), test_abort_cuts_delay_short(), test_abort_sequence_cuts_delay_short(), test_abort_sequence_lets_current_grab_finish_but_stops_the_rest() (+8 more)

### Community 173 - "binding.py"
Cohesion: 0.23
Nodes (8): fault2xml(), py2xml(), Any, Element, rpcbase64, rpctime, xml2fault(), xml2py()

### Community 174 - "NewSpectrumEvent"
Cohesion: 0.15
Nodes (10): NewSpectrumEvent, Any, Event to be sent on a new image., Initializes new NewSpectrumEvent. Args: filename: Name of new image file., HDUList, Store spectrum at given destination. Can be overwritten by derived classes to…, Actually do the exposure, should be implemented by derived classes. Args:…, Wrapper for a single exposure. Args: broadcast: Whether or not the new image… (+2 more)

### Community 175 - "gui/camera/__init__.py"
Cohesion: 0.15
Nodes (4): BinningWidget, ImageFormatWidget, ListPickerDialog, QComboBox

### Community 176 - ".set_config"
Cohesion: 0.50
Nodes (3): Any, ConfigValue, Apply a full structured config to this module. Args: config: Nested dict…

### Community 177 - "HttpFileCache"
Cohesion: 0.13
Nodes (11): HttpFileCache, Any, Response, Handles OPTIONS access to /{filename} for CORS preflight requests. Args:…, Handles GET access to /{filename} and returns image. Args: request: Request to…, Handles PUSH access to /, stores image and returns filename. Args: request:…, A file cache based on a HTTP server., Initializes file cache. Args: port: Port for HTTP server. cache_size: Size of… (+3 more)

### Community 178 - "FitsHeaderOffsets"
Cohesion: 0.19
Nodes (10): GenericOffset, FitsHeaderOffsets, Any, Compute a 2D offset from FITS header coordinates and store it in image…, Initializes new fits header offsets., Processes an image and sets x/y pixel offset to reference in offset attribute.…, asyncio, test_attribute_validation() (+2 more)

### Community 179 - "Scheduler"
Cohesion: 0.15
Nodes (8): Iterator for scheduler items, Iterate over scheduler items, Return schedule item., Find a possible slot for a given filter/binning in the given schedule Args:…, Checks, whether a new scheduler item would overlap an existing item Args:…, Scheduler for taking flat fields, Calculate schedule starting at given time Args: time: Time to start schedule at, Scheduler

### Community 180 - "Plan: Split archive prefetch from CPU-bound merit evaluation"
Cohesion: 0.17
Nodes (16): Plan: Split archive prefetch from CPU-bound merit evaluation, FrozenObservations picklable snapshot dataclass, ObservationArchiveEvolution.prefetch()/freeze(), Plan on hold: motivating incident had different cause; premise unconfirmed, AstroplanScheduler (subprocess-isolated precedent), DataProvider @cache sun/moon/sun_altaz/moon_illumination, Plan: Stop scheduler constraint/merit evaluation from blocking the event loop, run_cpu_bound() dedicated ThreadPoolExecutor helper (+8 more)

### Community 181 - "Test Basecamera (camera)"
Cohesion: 0.18
Nodes (15): asyncio, parametrize, DummyCamera's _expose() must raise AbortedError, not some guessed builtin, when…, Test basic open/close of BaseCamera., #547: BaseCamera must abort on BadWeatherEvent., #547: a BadWeatherEvent must actually trigger abort() -- exposure + any running…, #672: a BadWeatherEvent must not interrupt a dark/bias sequence -- the shutter…, Test the methods for remaining exposure time and progress. (+7 more)

### Community 182 - "Test Imagewatcher (image)"
Cohesion: 0.33
Nodes (15): make_fits_bytes(), make_read_write_ctx(), make_watcher(), asyncio, On write failure the file is re-queued and remove is NOT called., test_add_file_queues_filename(), test_add_file_respects_pattern(), test_add_file_skips_non_matching_pattern() (+7 more)

### Community 183 - "._do_camera_settings"
Cohesion: 0.33
Nodes (5): IBinning, IData, IFilters, IWindow, Do camera settings for given camera.

### Community 184 - "Merit"
Cohesion: 0.15
Nodes (15): AfterTimeMerit, BeforeTimeMerit, ConstantMerit, DataProvider, FollowMerit, IntervalMerit, ObservationArchiveEvolution wraps ObservationArchive with per-run caching (avoid repeated HTTP requests) and lookahead simulation (evolve() records tentative future assignments so IntervalMerit/PerNightMerit see them and avoid double-scheduling within one run), Merit (+7 more)

### Community 185 - "ejabberd shaper throttling bug (xmpp_socket.erl re-arm) & fix"
Cohesion: 0.21
Nodes (12): XMPP/ejabberd diagnostics recipe (doc), benchmark_state_throughput.py, check_ejabberd_notify.py, delete_pubsub_nodes.py, list_pubsub_nodes.py, Comparing shaper configs (rationale), show_module_info.py, scripts/xmpp/install-ejabberd.sh (+4 more)

### Community 186 - "BrightestStarGuiding"
Cohesion: 0.19
Nodes (7): BrightestStarGuiding, Any, SkyCoord, Table, Initializes a new auto guiding system., Processes an image and sets x/y pixel offset to reference in offset attribute.…, Compute guiding offsets by tracking the brightest star relative to an initial…

### Community 187 - ".__init__"
Cohesion: 0.40
Nodes (4): ICamera, IFilters, ITelescope, Initialize a new flat fielder. Args: telescope: Name of ITelescope. camera:…

### Community 188 - "pyobs/interfaces/__init__.py"
Cohesion: 0.03
Nodes (108): Binning, BinningCapabilities, BinningState, IBinning, Interface, The camera supports binning, to be used together with…, ICalibrate, Interface (+100 more)

### Community 189 - ".__init__"
Cohesion: 0.12
Nodes (10): Any, Initializes the mixin. Args: filters: Filter wheel module. filter: Filter to…, IData, IFilters, IFocuser, Initialize a new auto focus system. Args: focuser: Name of IFocuser. camera:…, Any, Abort current actions. (+2 more)

### Community 190 - "PointingSeries"
Cohesion: 0.18
Nodes (7): PointingSeries, Any, IAutonomous, SkyCoord, Module for running pointing series., Initialize a new pointing series. Args: grid: Grid to use for pointing series.…, Run a pointing series.

### Community 191 - "GridPipeline"
Cohesion: 0.14
Nodes (9): GridPipeline, Any, Build a GridPipeline from a list of steps. Args: steps: A non-empty list where…, Return the next point from the pipeline. Returns: The next point produced by…, Return the number of points remaining in the pipeline. Returns: The length…, Append the last yielded point back to the pipeline's final stage., Log the last yielded point via the pipeline's final stage., A pipeline that composes a grid and a sequence of filters. The pipeline expects… (+1 more)

### Community 192 - "wait_for"
Cohesion: 0.15
Nodes (13): set_binning(int, int) -> None: multiple int params, void return., Calling a method that raises on the remote side propagates the exception., set_cooling(bool, float) then verify via state: full encode/decode cycle., set_cooling(bool, float) -> None: void return with bool + float params., set_gain(float) -> None and verify via IGain state: float param, state readback., set_gain(float) then verify via IGain state: float param round-trip., test_rpc_bool_float_roundtrip(), test_rpc_exception_fault() (+5 more)

### Community 193 - "Plan: Widget plugin mechanism + pyside6-deploy packaging for pyobs-gui"
Cohesion: 0.18
Nodes (14): Application(module_factory=..., loop_module_class=...), astropy.units PLY/Nuitka frame-walking incompatibility (upstream bug, patched), Rationale: module construction must happen inside the running event loop for async login dialog, keyring-based per-account password storage, keyed by stable id, LoginWindow widget (list-left/detail-right), plugin_paths: external sys.path plugin directory mechanism (Nuitka-compatible), pyobs_iagvt.widgets custom widget package (grounding real-world case), pyobs-polaris LoginWindow.qml (UX model reused) (+6 more)

### Community 194 - "What's New in pyobs 2.0 (doc)"
Cohesion: 0.15
Nodes (14): What's New in pyobs 2.0 (doc), ACL feature (2.0), Capabilities and versioned discovery, Exception handling redesign, External-package interfaces, ICamera/ISpectrograph no longer imply IExposure, IDataSequence, InvocationError / SevereError retired (+6 more)

### Community 195 - "TaskStartedEvent"
Cohesion: 0.18
Nodes (8): Any, Event to be sent when a task has started., Initializes a new task started event. Args: name: Name of task that just…, TaskStartedEvent, test_task_started_invalid_name(), test_task_started_missing_id(), test_task_started_no_eta(), test_task_started_properties()

### Community 196 - "pyobs/images/meta/__init__.py"
Cohesion: 0.21
Nodes (4): AltAzOffsets, RaDecOffsets, test_alt_az_offsets(), test_radecoffsets()

### Community 197 - "CatalogCircularMask"
Cohesion: 0.18
Nodes (9): CatalogCircularMask, Any, NDArray, Table, Init an image processor that masks out everything except for a central circle.…, Remove everything outside the given radius from the image. Args: image: Image…, Filter a source catalog by keeping only entries inside a central circle (or…, asyncio (+1 more)

### Community 198 - ".__call__"
Cohesion: 0.40
Nodes (3): Any, Initialize new log publisher. Args: level: Level to log on., Publish the given results. Args: **kwargs: Results to publish.

### Community 199 - "ImageWatcher"
Cohesion: 0.15
Nodes (9): CurrentFile, ImageWatcher, Any, Add a file to the file queue. Args: filename (str): Local filename of new file., Can be overwritten by derived classes to do extra processing on files. All…, Can be overwritten by derived classes to do clean up after successful copying.…, Watch for new files and write them to all given destinations. Watches a path…, Create a new image watcher. Args: watchpath: Path to watch. destinations:… (+1 more)

### Community 200 - ".__init__"
Cohesion: 0.14
Nodes (8): Any, Returns the task with the given ID. Returns: Task with given ID., Creates a new task archive. Args: url: URL of pyobs-robotic-backend. token:…, Any, Creates a new LCO scheduler. Args: url: URL to portal token: Authorization…, Returns the task with the given ID., Any, Returns the task with the given ID. Returns: Task with given ID.

### Community 201 - "test_filters.py"
Cohesion: 0.27
Nodes (9): ConvertGridFrame, FromList, GridFilterValue, Transform SkyCoord points to a different frame., Select closest point from a list. Only select points if they are closer than a…, Filter points by numeric constraints on x and y. Accepts points as: - (x, y)…, Any, test_fromlistfilter() (+1 more)

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

### Community 208 - "configdb.py"
Cohesion: 0.21
Nodes (13): Camera, CameraType, ConfigurationType, Enclosure, Instrument, InstrumentType, Mode, ModeType (+5 more)

### Community 209 - "Smooth"
Cohesion: 0.22
Nodes (10): Any, Init a new smoothing pipeline step. Args: sigma: Standard deviation for…, Smooth an image. Args: image: Image to smooth. Returns: Smoothed image., Gaussian smoothing of image data using SciPy’s ndimage.gaussian_filter. This…, Smooth, asyncio, test_call(), test_call_no_image_data() (+2 more)

### Community 210 - "SkyflatPriorities"
Cohesion: 0.30
Nodes (6): ArchiveSkyflatPriorities, Calculate flat priorities from an archive., Base class for sky flat priorities., SkyflatPriorities, ConstSkyflatPriorities, Constant flat priorities.

### Community 211 - "DataCache"
Cohesion: 0.11
Nodes (13): DataCache, DataCacheEntry, Any, A single entry in the data cache., Delete entry in cache. Args: name: Name of entry to delete., Create a new entry for the data cache Args: name: Name of item data: Data for…, Update time for this item., Update usage time and return data for entry. (+5 more)

### Community 212 - "wait_for"
Cohesion: 0.14
Nodes (14): proxy.get_state(ICooling) must return the latest value without an RPC round-…, When the remote module disconnects, _client_disconnected must call…, After disconnect and reconnect, the next proxy() call must produce a fresh…, Poll *condition* until truthy or *timeout* seconds elapse., Wait until *comm* sees *peer* in its client list (presence + disco#info done)., A subscriber that connects after the first publish must receive the current…, After subscribing, subsequent set_state calls must arrive at the subscriber., test_disconnect_cleans_up_subscriptions() (+6 more)

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

### Community 218 - ".set_offsets_altaz"
Cohesion: 0.50
Nodes (3): Any, DEGREES, Move an Alt/Az offset. Args: dalt: Altitude offset in degrees. daz: Azimuth…

### Community 219 - ".add_fits_headers"
Cohesion: 0.24
Nodes (6): PrimaryHDU, Add requested FITS headers to header of given image. Args: image: Image with…, Add FITS header keywords to the given FITS header. Args: image: Image with…, Add FRAMENUM keyword to header Args: image: Image with header to add to., Format filename according to given pattern and store in header of image. Args:…, Add FITS header keywords to the given FITS header. Args: image: Image with…

### Community 220 - "FlatField"
Cohesion: 0.14
Nodes (12): FlatField, Any, IBinning, IFlatField, List available binnings. Returns: List of available binnings as (x, y) tuples., Set the camera binning. Args: x: X binning. y: Y binning. Raises: ValueError:…, List available filters. Returns: List of available filters., Set the current filter. Args: filter_name: Name of filter to set. (+4 more)

### Community 221 - "flatfield/test_scheduler.py"
Cohesion: 0.27
Nodes (11): A single item in the flat scheduler, Initializes a new scheduler item Args: start: Start time in seconds end: End…, Nice string representation for item, SchedulerItem, make_scheduler_module(), asyncio, setup_flatfield_proxy(), test_abort_sets_event() (+3 more)

### Community 222 - "AstrometryOffsets"
Cohesion: 0.20
Nodes (8): AstrometryOffsets, Any, SkyCoord, Compute pixel offsets from WCS by comparing image reference coordinates to…, Initializes new astrometry offsets. MUST run after an astrometry processor., Processes an image and sets x/y pixel offset to reference in offset attribute.…, asyncio, test_call()

### Community 223 - "NextImage"
Cohesion: 0.17
Nodes (13): calc_expose_timeout(), LastImage, NextImage, Any, IExposureTime, NamedTuple, NDArray, Create a JPEG ge from a numpy array and return as bytes. Args: data: Numpy… (+5 more)

### Community 225 - "XEP_0009_timeout"
Cohesion: 0.17
Nodes (6): BasePlugin, A plugin for SleekXMPP, adding a timeout to RPC calls., XEP_0009_timeout, SleekXMPP: The Sleek XMPP Library Copyright (C) 2011 Nathanael C. Fritz, Dann…, MethodTimeout, ElementBase

### Community 226 - "DataDisplayWidget"
Cohesion: 0.24
Nodes (4): DataDisplayWidget, PrimaryHDU, Slot, Select path for auto-saving.

### Community 227 - "FileList"
Cohesion: 0.27
Nodes (5): FileList, Base class for file lists., Any, File list for testing., TestingFileList

### Community 228 - "ModuleState"
Cohesion: 0.22
Nodes (5): Store presence state and dispatch to all subscribers., Return presence state of a connected module., Return cached presence state for a connected module., ModuleState, Enumerator for module states. Attributes: CLOSED: Module is closed. STARTING:…

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

### Community 236 - "Image class"
Cohesion: 0.20
Nodes (10): meta.AltAzOffsets, meta.ExpTime, Image class, Image.meta dict; rationale: keyed by class to avoid collisions between pipeline stages, kept out of FITS since it's runtime-only data, meta.OnSkyDistance, meta.PixelOffsets, meta.RaDecOffsets, meta.SkyOffsets (+2 more)

### Community 237 - "MotionStatusChangedEvent"
Cohesion: 0.22
Nodes (6): MotionStatusChangedEvent, Any, Event to be sent when the motion status of a device has changed., test_motion_status_invalid_status(), test_motion_status_no_interfaces(), test_motion_status_properties()

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

### Community 242 - ".__init__"
Cohesion: 0.13
Nodes (10): PydanticModel, PrivateAttrMixin, EarthLocation, Observer, Location of the observer, derived from :attr:`observer` (there is no separately…, Validate a pydantic model with additional fields., .. note:: Objects must always be opened and closed using…, Any (+2 more)

### Community 243 - ".__init__"
Cohesion: 0.18
Nodes (8): Any, SkyCoord, Create an approximately equidistributed spherical grid. Args: n: Target number…, Initialize a Grid with a list of points. Args: points: Initial list of points…, Return the next point and remove it from the internal list. Returns: The next…, Create a regular lon/lat grid. Args: n_lon: Number of longitudinal divisions.…, Any, Initialize a GridNode. Args: log: If True, enable informational logging for…

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
Cohesion: 0.20
Nodes (5): LogEvent, Event for log entries., Enum, TelegramUserState, test_log_event_properties()

### Community 249 - "test_safe_send.py"
Cohesion: 0.38
Nodes (9): make_xmpp_comm(), asyncio, Tests for XmppComm._safe_send's retry/timeout handling. Covers…, Create a minimal XmppComm instance for testing, without a live connection., A method that never returns (e.g. slixmpp's own IQ timeout not firing) must…, test_safe_send_enforces_own_timeout_when_method_hangs(), test_safe_send_retries_and_raises_on_iq_timeout(), test_safe_send_returns_result_on_success() (+1 more)

### Community 250 - "get_class_from_string"
Cohesion: 0.20
Nodes (6): Any, get_class_from_string(), Get class from a given string. Args: class_name: Name of class as string.…, _build_params_model(), _get_valid_param_names(), model_validator

### Community 251 - "Two-phase Object lifecycle; rationale: __init__ must not touch hardware/external services (only store params, create children, register background tasks); open() is where side effects happen, so objects can be constructed cheaply/safely before being started"
Cohesion: 0.22
Nodes (8): Object.add_child_object(), create_object(), get_object(), Two-phase Object lifecycle; rationale: __init__ must not touch hardware/external services (only store params, create children, register background tasks); open() is where side effects happen, so objects can be constructed cheaply/safely before being started, class: key YAML instantiation; rationale: strips class key, passes remaining keys as kwargs, recursing into nested blocks, so any pyobs object graph is fully describable in YAML, Configuration utilities (pyobs.utils.config) API doc, pre_process_yaml(), Coordinate utilities (pyobs.utils.coordinates) API doc

### Community 252 - "Simulation recipe (doc)"
Cohesion: 0.42
Nodes (9): pyobs.modules.telescope (doc), BaseTelescope, DummyAltAzTelescope, DummyRaDecTelescope, DummySolarTelescope, Simulation recipe (doc), DummyCamera, pyobs_gui.GUI (+1 more)

### Community 253 - "RemoteError"
Cohesion: 0.20
Nodes (7): ForbiddenError, The call itself didn't reach/return -- a transport failure, not a domain…, Raised when a caller is not permitted to invoke a method under the target…, RemoteError, RemoteTimeoutError, test_forbidden_error(), test_log_only_logs_once()

### Community 254 - "Seeing"
Cohesion: 0.22
Nodes (5): Any, Measures seeing on reduced images with a catalog., Creates a new seeing estimator. Args: sources: List of sources (e.g. cameras)…, Puts a new images in the DB with the given ID. Args: event: New image event…, Seeing

### Community 255 - "RegularSphericalGrid"
Cohesion: 0.31
Nodes (8): GraticuleSphericalGrid, Grid over a sphere using regular longitude/latitude sampling. Produces points…, Grid with approximately equidistributed points on a sphere. Uses a graticule-…, RegularSphericalGrid, Reinsert one point back into the grid., test_graticulesphericalgrid(), test_regularsphericalgrid(), test_regularsphericalgrid_append_last()

### Community 256 - "ConfigDB"
Cohesion: 0.29
Nodes (4): InstrumentLocation, ConfigDB, Any, Creates a new LCO scheduler. Args: portal: Portal to use. configdb: ConfigDB to…

### Community 257 - "GuidingStatisticsSkyOffset"
Cohesion: 0.25
Nodes (7): GuidingStatisticsSkyOffset, Calculates RMS of data. Args: data: Data to calculate RMS for. Returns: Tuple…, mock_meta_image(), fixture, test_build_header_to_few_values(), test_end_to_end(), test_get_session_data()

### Community 258 - "IMultiFiber"
Cohesion: 0.29
Nodes (6): IMultiFiber, Any, Interface, An interface for multi-fiber setups that helps to set/get a fiber and retrieve…, Abort current actions., Sets the currently active fiber. Must be in fiber_names capability. Args:…

### Community 259 - "test_module_state_publishing.py"
Cohesion: 0.33
Nodes (6): _discover_concrete_modules(), asyncio, parametrize, Parametrized check: every concrete Module publishes state for each stateful…, All concrete (non-abstract, non-internal) pyobs.modules.Module subclasses.…, test_module_publishes_all_stateful_interfaces()

### Community 260 - "IStructuredConfig interface"
Cohesion: 0.25
Nodes (8): pyobs/utils/config_schema.py: dataclass_to_schema, ICooling interface (reference pattern), IStructuredConfig design doc, IStructuredConfig interface, Rationale: IStructuredConfig coexists with IConfig (per-field vs bulk dataclass config), Interface.version / Event.version, Rationale: state and capabilities stay two independent ClassVars, not merged, Rationale: version lives on Interface only, not on State dataclass

### Community 261 - "robotic"
Cohesion: 0.43
Nodes (8): acquisition, fibercamera, fts, guiding, robotic, solar telescope, suncamera, weather

### Community 262 - "Archive (image archive base)"
Cohesion: 0.32
Nodes (8): Archive (image archive base), LocalArchive, PyobsArchive, ArchiveSkyflatPriorities, Archive, Image archives (pyobs.robotic.utils.archive) API doc, LocalArchive, PyobsArchive

### Community 263 - ".get_meta"
Cohesion: 0.40
Nodes (3): MetaClass, Returns meta information, assuming that it is stored under the class of the…, Calls get_meta in a safe way and returns default value in case of an exception.

### Community 264 - "._client_disconnected"
Cohesion: 0.29
Nodes (4): PresenceCallback, Called when a client disconnects. Args: event: Disconnect event. sender: Name…, Subscribe to presence updates for a given module. Delivers the current value…, Unsubscribe from presence updates. Args: module: Name of remote module.…

### Community 265 - "solarhelioprojective.py"
Cohesion: 0.40
Nodes (3): Add WCS. Args: image: Image to use. Returns: Image with new WCS., Add a time-aware solar helioprojective WCS to the image header based on disk…, SolarHelioprojective

### Community 266 - "IGain"
Cohesion: 0.29
Nodes (6): IGain, Any, Interface, The camera supports setting of gain, to be used together with…, Set the camera gain. Args: gain: New camera gain. Raises: ValueError: If gain…, Set the camera offset. Args: offset: New camera offset. Raises: ValueError: If…

### Community 267 - "IModule"
Cohesion: 0.29
Nodes (6): IModule, Any, Interface, The module is actually a module. Implemented by all modules., Reset error of module, if any., Returns names of all methods the calling module is allowed to invoke on this…

### Community 268 - "._get_next"
Cohesion: 0.33
Nodes (4): SkyCoord, Log a point if logging is enabled. For SkyCoord instances, logs RA/Dec in…, Return the next point in the sequence. Implementors must return either a (x, y)…, Return the next point, storing it as the last yielded value. Returns: A point…

### Community 272 - "FlatFieldScheduler"
Cohesion: 0.24
Nodes (8): FlatFieldScheduler, Any, IFlatField, IRunnable, Abort current actions., Run the flat-field scheduler., Initialize a new flat field scheduler. Args: flatfield: Flat field module to…, Perform flat-fielding Raises: DeviceBusyError: If a flat-fielding run is…

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

### Community 281 - "Observation"
Cohesion: 0.03
Nodes (56): Observation, Any, Fetch a task from the task archive., Updates observation. Args: observation: Observation to update., AcquisitionConfig, Configuration, GuidingConfig, InstrumentConfig (+48 more)

### Community 283 - "Target"
Cohesion: 0.29
Nodes (4): Target, Set the resolved target if not already set, e.g. when restoring from an…, The resolved target, or the static target if not dynamic., Target for this specific run: the observation's own record if known, otherwise…

### Community 284 - "ImageType"
Cohesion: 0.07
Nodes (16): Broadcast image. Args: image: Image to broadcast. Returns: Original image., Any, Set the image type. Args: image_type: New image type., LcoDefaultScript, Returns FITS header for the current status of this module. Args: namespaces: If…, Default script for LCO configs., Whether this config can currently run. Returns: True, if the script can run now, Any (+8 more)

### Community 286 - "reset_network"
Cohesion: 0.67
Nodes (3): fixture, Reset LocalNetwork singleton before each test., reset_network()

### Community 287 - "pyobs.modules.utils (doc)"
Cohesion: 0.33
Nodes (6): pyobs.modules.utils (doc), FluentLogger, Kiosk, Matrix, Telegram, Trigger

### Community 292 - "IConfig"
Cohesion: 0.28
Nodes (7): IConfig, Any, ConfigValue, Interface, The module allows access to some of its configuration options., Returns current value of config item with given name. Args: name: Name of…, Sets value of config item with given name. Args: name: Name of config item.…

### Community 293 - "IDataSequence"
Cohesion: 0.25
Nodes (7): IDataSequence, Any, IAbortable, SECONDS, The module can grab a counted sequence of data (images, spectra, ...)., Start a sequence of `count` grabs. Returns immediately; progress is available…, Stop the sequence after the current grab. The grab currently in progress, if…

### Community 294 - ".set_focus"
Cohesion: 0.40
Nodes (4): Any, MM, Sets new focus. Args: focus: New focus value in mm. Raises:…, Sets focus offset. Args: offset: New focus offset in mm. Raises: ValueError: If…

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

### Community 317 - "check_pyobs_releases.sh"
Cohesion: 0.70
Nodes (4): check_repo(), main(), print_header(), check_pyobs_releases.sh script

### Community 318 - "check_ejabberd_notify.py"
Cohesion: 0.60
Nodes (4): connect(), main(), make_client(), Minimal ejabberd notification test — no pyobs code involved.

### Community 320 - "_DummyTelescopeBase"
Cohesion: 0.05
Nodes (34): ARCSEC_PER_SEC, ITrackingMode, Any, Interface, The module supports switching between discrete, hardware-native tracking rates., Switches to the given tracking mode. Args: mode: Tracking mode to switch to.…, ITrackingRate, Any (+26 more)

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

### Community 339 - ".add_image"
Cohesion: 0.29
Nodes (4): Any, Initializes a new science frame auto guiding system., Set the exposure time for the auto-guider. Args: exposure_time: Exposure time…, Processes an image asynchronously, returns immediately. Args: event: Event for…

### Community 342 - "IOffsetsRaDec"
Cohesion: 0.29
Nodes (6): IOffsetsRaDec, Any, DEGREES, Interface, The module supports RA/Dec offsets, usually combined with…, Move an RA/Dec offset. Args: dra: RA offset in degrees. ddec: Dec offset in…

### Community 346 - ".move_radec"
Cohesion: 0.50
Nodes (3): Any, DEGREES, Starts tracking on given coordinates. Args: ra: RA in deg to track. dec: Dec in…

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
- **304 isolated node(s):** `pyobs-core`, `Problem`, `Where the pieces actually are`, `Why this determines the design, not just where to put a function`, `Proposed design` (+299 more)
  These have ≤1 connection - possible missing edges or undocumented components.
- **40 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

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
- **Why does `Time` connect `Time` to `time.py`, `enums.py`, `RunningState`, `MotionStatus`, `DynamicTarget`, `utils/exceptions.py`, `ObservationList`, `test_dummyradectelescope.py`, `FilenameFormatter`, `test_scheduler_mastermind.py`, `Event`, `test_astroplanscheduler.py`, `test_flatfielder.py`, `tests/test_events.py`, `Object`, `test_control.py`, `test_lco_http.py`, `BaseTelescope`, `xmppcomm.py`, `test_yaml_archives.py`, `test_lcoscript.py`, `test_transit_mastermind.py`, `robotic/test_scheduler.py`, `Calibration`, `Proxy`, `IOffsetsAltAz.py`, `IPointingAltAz`, `AirmassConstraint`, `FlatFielder`, `Offsets`, `.now`, `test_proxy.py`, `SiderealTarget`, `Pipeline`, `test_acquisition.py`, `Weather`, `SolarElevationConstraint`, `test_backend_archives.py`, `Portal`, `DummySolarTelescope`, `DummyCamera`, `test_pyobs_archive.py`, `Constraint`, `application.py`, `test_coordinates.py`, `LocalArchive`, `Test Commlogging (comm)`, `ImagingScript`, `BackendTaskArchive`, `WeatherSensors`, `test_darkbias.py`, `GridNode`, `GoodWeatherEvent`, `test_dummymode.py`, `Grid`, `pyobs.py`, `Scheduler`, `Archive`, `RandomizeGrid`, `pyobs/modules/utils/__init__.py`, `ExpTimeEval`, `test_schedulewriter.py`, `FileSystemTaskArchive`, `Scheduler`, `BrightestStarGuiding`, `pyobs/interfaces/__init__.py`, `TaskStartedEvent`, `test_filters.py`, `SkyflatPriorities`, `.add_fits_headers`, `flatfield/test_scheduler.py`, `Seeing`, `solarhelioprojective.py`, `FlatFieldScheduler`, `Observation`, `ImageType`, `_DummyTelescopeBase`, `.night_obs`?**
  _High betweenness centrality (0.282) - this node is a cross-community bridge._
- **Why does `Image` connect `Image` to `enums.py`, `GuidingStatisticsSkyOffset`, `.get_meta`, `utils/exceptions.py`, `ImageProcessor`, `solarhelioprojective.py`, `ProjectionFocusSeries`, `AstrometryDotNet`, `FilenameFormatter`, `_CalibrationCache`, `_SepAperturePhotometry`, `mixins/test_fitsheader.py`, `PipelineMixin`, `test_flatfielder.py`, `_SourceCatalog`, `.__init__`, `ImageType`, `SoftBin`, `AddMask`, `_DaoBackgroundRemover`, `GuidingStatistics`, `Archive`, `VirtualFileSystem`, `BaseVideo`, `StarExpTimeEstimator`, `FitsHeaderOffsets`, `Calibration`, `BrightestStarGuiding`, `pyobs/interfaces/__init__.py`, `test_basevideo.py`, `CatalogCircularMask`, `Offsets`, `Pipeline`, `test_acquisition.py`, `Smooth`, `SkyOffsets`, `Ring`, `DummyCamera`, `.add_fits_headers`, `ProjectedOffsets`, `AstrometryOffsets`, `NextImage`, `test_pyobs_archive.py`, `FocusSeries`, `SepSourceDetection`, `_DotNetRequest`, `OnSkyDistance`, `LocalArchive`, `_PhotUtilAperturePhotometry`, `VFSFile`, `ImageSourceFilter`?**
  _High betweenness centrality (0.119) - this node is a cross-community bridge._