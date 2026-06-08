v1.47.0 (2025-06-07)
*********************
* Set minimum Python version to 3.11.
* Replaced old-style type hints (``Optional``, ``Union``, ``List``, etc.) with modern Python 3.11+ syntax throughout.
* Replaced deprecated ``asyncio.ensure_future`` with ``asyncio.create_task``.
* Replaced deprecated ``asyncio.get_event_loop`` with ``asyncio.get_running_loop``.
* Replaced ``str, Enum`` with ``StrEnum`` throughout.
* Replaced ``asyncio.gather`` with ``asyncio.TaskGroup`` where applicable.
* Added ruff linting to CI and pre-commit.

v1.46.0 (2025-05-27)
*********************
* Added ``DynamicTarget`` class for runtime target selection via a pluggable ``Picker`` interface.
* Added ``CsvPicker`` for selecting targets from a CSV catalogue, with constraint-aware filtering.
* ``OnDemandScheduler`` now resolves dynamic targets before evaluating constraints and merits.
* Added ``direction`` parameter to ``SolarElevationConstraint`` for filtering on rising or setting sun.
* Resolved target is now stored on ``Observation`` and restored by the mastermind via ``fetch_task``.
* Target resolution result is cached per scheduling run.
* Added ``set_resolved_target`` and ``estimate_duration`` to ``Task``.
* ``LcoTaskRunner`` now correctly injects script before ``run_task``.
* Added missing abstract method implementations to ``LcoTaskArchive`` and ``LcoObservationArchive``.
* Fixed inverted ``PENDING`` filter in ``LcoTaskArchive.get_schedulable_tasks``.
* Fixed ``LcoConfiguration.state`` default to ``"PENDING"``.
* Portal now creates aiohttp session in ``open()`` instead of ``__init__()``.
* Portal now managed via ``add_child_object`` for correct lifecycle.
* Fixed ``SolarElevationConstraint`` direction logic using ``observer.midnight``.
* Added ``AstroplanScheduler`` tests; fixed empty block list causing subprocess hang.
* Fixed ``LcoRequest.location`` field name conflict with ``BaseModel.location``.
* Added ``ImagingScript`` for standard science exposures with acquisition and guiding support.
* Comprehensive test suite additions for LCO classes, scheduler, and scripts.

v1.45.0 (2025-05-14)
*********************
* Added unified ``get_observations`` interface to ``ObservationArchive`` with state and time filters.
* ``IntervalMerit`` and ``PerNightMerit`` now push filters directly to ``get_observations``.
* Added ``ObservationArchiveEvolution.get_observations`` method.
* Added ``min_safety_time`` parameter to ``Mastermind``.
* Added ``active`` field to ``Task``.
* Fixed telescope not stopping after auto focus.

v1.44.0 (2025-04-24)
*********************
* Renamed ``SubClassBaseModel`` to ``PolymorphicBaseModel``.
* Renamed ``MeritScheduler`` to ``OnDemandScheduler``.
* Moved ``utils.archive`` and ``utils.skyflats`` into ``robotic.utils`` as pydantic models.
* Moved ``serialization.py`` from ``robotic.utils`` to ``utils``.
* Converted ``SkyFlatsBasePointing``, ``SkyflatPriorities``, ``Archive``, and ``PyobsArchive`` to ``PolymorphicBaseModel``.
* Removed ``Object`` from ``Script`` base classes.
* Context injection now propagates to all child pydantic models.
* HTTP requests now use pagination; all list responses wrapped in ``{"results": [...]}`` format.
* Added ``create_script`` method to ``Task``.
* Added ``http_request_with_retries`` with tenacity-based retry logic.
* ``BaseModel`` no longer inherits from ``Object``.
* Added ``trigger_on_every_update`` parameter to ``Scheduler`` module.
* Added Observation priority field.
* Major documentation overhaul for the robotic subsystem.

v1.43.0 (2025-04-20)
*********************
* Added ``http_request_with_retries`` utility.
* Backend archives now use ``http_request_with_retries`` instead of direct HTTP calls.
* Added ``ignore_cert_errors`` parameter to backend archives.
* Added filesystem-based backend for robotic scheduling (``YamlTaskArchive``, ``YamlObservationArchive``).
* Fixed ``inject_class_on_serialization`` for pydantic models.

v1.42.0 (2025-03-08)
*********************
* Backend archives migrated from ``requests`` to ``aiohttp``.
* Observation fetching moved to a background task.
* Task changes now driven by ``on_tasks_changed`` callback.
* Refactored robotic subsystem to support pluggable backends.

v1.41.0 (2025-02-20)
*********************
* Added optional Qt widget dependencies for GUI support.
* Added general-purpose Qt widgets.

v1.40.0 (2025-02-10)
*********************
* XMPP communication now connects with TLS using slixmpp 1.4.1.
* Fixed PyPy compatibility issues.
* Added ``AvoidMoon`` constraint.
* Added ``FromList`` grid filter.
* ``PerNightMerit`` now uses last sunrise for night boundary.
* Auto focus now uses actual measured focus position.

v1.39.0 (2024-12-10)
*********************
* Major scheduler refactoring: introduced pluggable scheduler architecture.
* Added ``OnDemandScheduler`` (merit-based greedy scheduler) with ``DataProvider`` context.
* Added ``ABORTED``, ``IN_PROGRESS``, and ``FAILED`` observation states.
* Added ``ConfigurationSummary`` to LCO integration.

v1.38.0 (2024-11-05)
*********************
* Added config file support via ``--config`` flag.
* Added InfluxDB logging handler.
* Added ``CommLoggingHandler`` guard against duplicate logger registration.
* Added ``--verbose`` CLI switch.

v1.37.0 (2024-10-20)
*********************
* Added InfluxDB logging handler (``InfluxLoggingHandler``).

v1.36.0 (2024-10-05)
*********************
* Improved exception handling in background tasks; ``BackgroundTask`` now receives parent reference.
* Unknown remote exceptions now wrapped in ``RemoteError``.
* Added SSL check option for XMPP.
* Fixed: don't reconnect after intentional XMPP disconnect.
* Added example systemd service file.

v1.35.0 (2024-09-01)
*********************
* Added ``--verbose`` switch to CLI.
* Added ``CALIBRATING`` motion status.
* Refactored shell command handling into dedicated classes.

v1.34.0 (2024-08-20)
*********************
* Refactored shell command and response into dedicated ``ShellCommand`` classes.

v1.33.0 (2024-08-05)
*********************
* Added new grid creation for pointing series.
* Configurable wait times in pointing module.

v1.32.0 (2024-07-20)
*********************
* Moved exceptions to a dedicated module.
* Added ``AcquisitionError`` for failed acquisitions.
* Changed ``GeneralError`` to ``FocusError`` for focus-related errors.
* Added 60s timeout to autoguider stop method.
* LCO integration: use ConfigDB to fetch instrument; support multiple configurations.

v1.31.0 (2024-05-25)
*********************
* Added documentation for image processors.
* Registered ``pyobs`` exceptions now logged as ``INFO`` without stack trace.
* Added ``overwrite`` parameter to image writing.
* Added Matrix chat client module.

v1.30.0 (2024-05-01)
*********************
* Added Matrix chat client module.
* Fixed context propagation for non-dict objects.
* Added reset method to ``BrightestStarGuiding``.
* Added ``oneshot`` parameter to ``ScriptRunner``.
* Added logging when a script cannot run.

v1.29.0 (2024-03-15)
*********************
* Added ``PipelineCamera`` for running image pipeline on camera images.
* Added ``Flip`` image processor.
* Added TypeScript interface export.
* Added ``HttpServer`` to serve images via HTTP.
* Added ``SolarHelioprojective`` image processor.
* Added ``Pipeline`` module.

v1.28.0 (2024-02-20)
*********************
* Added offset parameter to ``IGain``.
* Reduced httpx logging verbosity.

v1.27.0 (2024-02-01)
*********************
* ``FilenameFormatter`` now supports formatting with FITS headers via ``GetFitsHeaders``.

v1.26.0 (2024-01-15)
*********************
* Added comprehensive typing throughout using ``TypedDict`` and ``npt.NDArray``.
* Improved ``get_object`` overloads.

v1.25.0 (2024-01-01)
*********************
* Migrated build system to ``uv``.
* Pointing module updated to use new grid classes.

v1.24.0 (2023-12-30)
*********************
* Added new spherical grid classes (``RegularSphericalGrid``, filters, pipeline) with tests.

v1.23.0 (2023-12-29)
*********************
* Improved spilled light guiding sigmoid function for more accurate relative offset calculation.
* Added weather station workaround.

v1.22.0 (2023-12-29)
*********************
* Added ``auto_focus`` integration to relevant modules.

v1.21.0 (2023-12-28)
*********************
* Added ``init_offset_to_zero`` functionality.
* Spilled light guiding: added binning correction, image trimming, and improved calculations.

v1.20.0 (2023-12-28)
*********************
* VFS not created if none is configured.
* Added pixel offset image processor for simplified acquisition workflow.
* ``get_object`` no longer overwrites existing parameters.

v1.19.0 (2023-12-28)
*********************
* Added spilled light guiding processor.
* Added ``IMultiFiber`` interface.

v1.18.0 (2023-12-28)
*********************
* ``ITelescope`` no longer directly implements ``IPointingRaDec``/``IPointingAltAz``; ``BaseTelescope`` handles dispatch.
* Added bright star guiding.
* Restore initial focus if focus series fails.

v1.17.0 (2023-12-28)
*********************
* Added ``DummyMode`` module and ``ModeChangedEvent``.
* Added ``ResolvableErrorLogger`` utility.
* Reactivated publisher module.
* Added XMPP auto-reconnect on connection loss.

v1.16.0 (2023-12-28)
*********************
* New ``pyobsd`` daemon with improved module management and config testing.
* Added several default scripts.
* Added group support for module configuration.

v1.15.0 (2023-12-28)
*********************
* Added group support for module configuration.

v1.14.0 (2023-12-28)
*********************
* Stop telescope after autofocus completes.
* Updated to Python 3.12; replaced deprecated ``datetime.utcnow()``.
* Warn when no RA/Dec given for pointing.

v1.13.0 (2023-12-28)
*********************
* Added acquisition support for bright central star.
* Added derotator offset handling.
* Added ``BackgroundTask`` class to simplify background task management in ``Object``.
* Added unit tests for ``BackgroundTask`` and ``Object``.

v1.12.0 (2023-12-28)
*******************
* Added `list` command for `pyobsd`, which outputs all configurations.
* Added bash auto-complete script `pyobsd`.
* Added timeouts (to be defined in the config) for `ScriptRunner` modules.


v1.11.0 (2023-12-25)
*******************
* Acquisition and AutoFocus both got a `broadcast` option to disable broadcast of images.
* AutoFocus got a `final_image` parameter to take a final image at optimal focus.


v1.10.0 (2023-12-24)
*******************
* Added CallModule script.
* Changed ScriptRunner module so that it can run a script multiple times.

v1.9.0 (2023-12-23)
*******************
* Added getters and safe getters for Image class.

v1.3.0 (2023-02-04)
*******************
* Adopted LCO default task to new LCO portal.

v1.2.0 (2022-10-06)
*******************
* Added AltAzOffsets and RaDecOffsets and (partly) implemented them in the ApplyOffsets classes.

v1.1.0 (2022-09-20)
*******************
* Changed signature of `pyobs.robotic.TaskSchedule.get_schedule` to have no parameters.

v1.0.0 (2022-09-13)
*******************

v0.22.0 (2022-08-25)
********************
* Removed comm.sleexxmpp implementation.
* Renamed comm.slixmpp to comm.xmpp.

v0.21.0 (2022-08-25)
********************
* Some pipeline stuff.
* Added DbusComm for communicating via Dbus.
* Cleaned up parameter casting for communication.

v0.20.0 (2022-06-22)
********************
* Some fixes with asyncio and the GUI.
* Handle JID conflicts in XMPP.

v0.19.0 (2022-05-17)
********************
* Getter/setter methods in Module must be async.
* get_task() in TaskScheduler is now async.
* Lots of bug fixes.

v0.18.0 (2022-03-13)
********************
* New IGain interface.

v0.17.0 (2022-02-14)
********************
* Restructuring robotic system.

v0.16.0 (2022-01-14)
********************
* Added new exceptions.
* Use those new exceptions to keep track of errors over time and raise SevereErrors.
* Add new state to module, so that a severe error can put a module into an error state.
* Added get_state() and get_error_string() methods to modules.

v0.15.0 (2021-12-29)
********************
* Added Comm implementation for SliXMPP (which should now be default) and moved old comm.xmpp to comm.sleekcmpp.
* Using asyncio throughout the project, all method and event handlers are async now, as well as open/close methods.
* Got rid of multi-threading as best as possible.
* VFS now also uses asyncio.

v0.14.2
*******
* Fixed a bug with Poetry

v0.14.1
*******
* Added possibility to use class hierarchy for events, i.e. subscribe to a class and receive all derived events.
* Change to Poetry as build system

v0.14 (2021-11-03)
******************
* Guiding modules accept a pipeline now, so more image processors than just Offsets can run.
* Renamed ICameraBinning, ICameraExposureTime and ICameraWindow and removed the "Camera" part.
* Added meta attribute (temporary storage, not I/O persistent) to Image.
* Extracted IImageGrabber from ICamera and renamed expose() to grab_image().
* Added new IVideo interface and a corresponding BaseVideo module.
* Raising exception, if XmppComm cannot connect to server, allowing for graceful exit.
* On shutdown, wait for hanging threads, and kill them after 30 seconds.
* Multi-processing for the pipeline, using ccdproc now.
* New interface IPointingSeries, giving access to methods at the telescope that support pointing series.
* Send logs in thread.
* Added concept of image processors that take an Image as parameter and return it after some processing.
* Added new NStarOffsets image processor (T. Masur).
* Improved scheduler.
* Added pipelines that take a list of image processors (see Pipeline mixin).
* Re-organized all get_object methods.
* Improved type hints throughout the code.
* Renamed all coordinated interfaces (IRaDec, etc) to IPointing*, i.e. IPointingRaDec.
* Renamed all offset interfaces to IOffsets*, i.e. IOffsetsRaDec.
* Renamed IFitsHeaderProvider to IFitsHeaderBefore and also renamed its only method.
* Added IFitsHeaderAfter to fetch FITS headers after an exposure as well.
* Moved functionality from Module to Object.
* New meta data system for images.
* Renamed IStoppable to IStartStop.
* Added new proxy interfaces in interfaces.proxies. All proxies now derive from these interfaces instead of the 
  original ones.
* And a lot more cleanup and re-organization.


v0.13 (2021-04-30)
******************
* Added a Telegram bot module.
* Added a module for a Kiosk mode, in which pictures are published on a webpage.
* Added new IImageFormats interface for cameras that support multiple ones (e.g. grayscale and color).
* Moved more enums into utils.enums, like WeatherSensors and MotionStatus.
* Added list_binnings() to IBinning interface and (temporary) default implementation in BaseCamera.
* Restructured image processors into pyobs.image.processors.
* Split photometry into separate SourceDetection and Photometry interfaces, added DaophotSourceDetection, and 
  PhotUtilsPhotometry.
* Sending events non-blocking, which might solve some problems with disappeared XMPP clients.
* Added lots of documentation, which included setting `__module__` for many classes.


v0.12 (2021-01-01)
******************
* Changed PyObsModule to Module.
* Removed possibility for network configs.
* Added MultiModule, which allows for multiple modules in one process.
* Flat scheduler: add options for readout times.
* New OnlineReduction module for reduction during the night.
* Fixed bug that sometimes appears in the interface caching for Comm.
* LcoTaskArchive: added MoonSeparationConstraint, fixed AirmassConstraint.
* Optimized Scheduler by only scheduling blocks that actually have a window in the given range.
* Added module Seeing that extracts FWHMs from the catalogs in reduced images and calculated a median seeing.
* Introduced concept of Publishers, which can be used to publish data to log, CSV, and hopefully later, database, 
  web, etc.
* Created new Object class that handles most of what Module did before so that Module only adds module specific stuff.
* Added some convenience methods for reading/writing files to VFS.
* Added new IConfig interface which is implemented in every module and allows remote access to config parameters 
  (if getter/setters are implemented).
* Removed count parameter from ICamera.expose().
* Removed exposure_time parameter from ICamera.expose() and introduced IExposureTime interface.
* Removed image_type parameter from ICamera.expose() and introduced IImageType.
* Moved ImageType enumerator from ICamera to utils.enums.


v0.11 (2020-10-18)
******************
* Major changes to robotic system based on LCO portal.
* Setting filter/window/binning in acquisition.
* Added WaitForMotion and Follow mixins.
* Added support for flats that don't directly scale with binning.
* New module for acoustic warning when autonomous modules are running.
* Improved SepPhotometry by calculating columns used also by LCO.
* New interface for Lat/Lon telescopes, e.g. solar telescopes.


v0.10 (2020-05-05)
******************
* Re-factored acquisition modules and added one based on astrometry.
* Added combine_binnings parameter to FlatFielder, which triggers, whether to use one function for all binnings or not
* Added get_current_weather() to IWeather
* New FlatFieldPointing module that can move telescope to a flatfield pointing
* Changed requirements in setup.py and put packages that are only required by a server module into [full]
* Removed HTTP proxy classes
* Some new mixins


v0.9 (2020-03-06)
*****************
* working on robotic system based on LCO portal


v0.8 (2019-11-17)
*****************
* Added module for bright star acquisition.
* Added and changed some FITS header keywords.
* Added module for flat-fielding.
* Changed some interfaces.
* Added basic pipeline.
* Started with code that will be used for a full robotic mode.
* Re-organized auto-guiding modules.
* and many more...