## Changelog

### v0.16.0 ()
* Added new exceptions.
* Use those new exceptions to keep track of errors over time and raise SevereErrors.
* Add new state to module, so that a severe error can put a module into an error state.

### v0.15.0 (2021-12-29)
* Added Comm implementation for SliXMPP (which should now be default) and moved old comm.xmpp to comm.sleekcmpp.
* Using asyncio throughout the project, all method and event handlers are async now, as well as open/close methods.
* Got rid of multi-threading as best as possible.
* VFS now also uses asyncio.

### v0.14.2
* Fixed a bug with Poetry

### v0.14.1
* Added possibility to use class hierarchy for events, i.e. subscribe to a class and receive all derived events.
* Change to Poetry as build system

### v0.14 (2021-11-03)
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


### v0.13 (2021-04-30)
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


### v0.12 (2021-01-01)

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


### v0.11 (2020-10-18)

* Major changes to robotic system based on LCO portal.
* Setting filter/window/binning in acquisition.
* Added WaitForMotion and Follow mixins.
* Added support for flats that don't directly scale with binning.
* New module for acoustic warning when autonomous modules are running.
* Improved SepPhotometry by calculating columns used also by LCO.
* New interface for Lat/Lon telescopes, e.g. solar telescopes.


### v0.10 (2020-05-05)

* Re-factored acquisition modules and added one based on astrometry.
* Added combine_binnings parameter to FlatFielder, which triggers, whether to use one function for all binnings or not
* Added get_current_weather() to IWeather
* New FlatFieldPointing module that can move telescope to a flatfield pointing
* Changed requirements in setup.py and put packages that are only required by a server module into [full]
* Removed HTTP proxy classes
* Some new mixins


### v0.9 (2020-03-06)

* working on robotic system based on LCO portal


### v0.8 (2019-11-17)

* Added module for bright star acquisition.
* Added and changed some FITS header keywords.
* Added module for flat-fielding.
* Changed some interfaces.
* Added basic pipeline.
* Started with code that will be used for a full robotic mode.
* Re-organized auto-guiding modules.
* and many more...