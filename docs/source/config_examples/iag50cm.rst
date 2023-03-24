Configuration of the IAG 50cm
-----------------------------

This is the configuration for the 50cm telescope at the Institute for Astrophysics and Geophysics in Göttingen. See
`here <https://www.uni-goettingen.de/en/217812.html>`_ for more details.

The modules are distributed over two different computers, ``iag50srv`` and ``iag50cam``. Autoslew is used as the
telescope software and is running on a third computer, together with an
`ASCOM Alpaca Remote server <https://www.ascom-standards.org/Developer/Alpaca.htm>`_ for remote access.

All the configs are shown here without the ``comm`` part and the environment details.

.. image:: ../_static/structure_iag50cm.svg


iag50srv
^^^^^^^^

acquisition
"""""""""""
Module for performing a fine-acquisition on target

.. code-block:: YAML
  :linenos:

  class: pyobs.modules.pointing.Acquisition

  # modules
  telescope: telescope
  camera: sbig6303e
  filters: sbig6303e

  # image settings
  filter_name: Clear
  binning: 2
  exposure_time: 2

  # log file
  log_file: /pyobs/acquisition.csv

  # tolerances
  max_offset: 7200
  tolerance: 10

  pipeline:
    - class: pyobs.images.processors.detection.SepSourceDetection
    - class: pyobs.images.processors.astrometry.AstrometryDotNet
      url: ...
      radius: 5
    - class: pyobs.images.processors.offsets.AstrometryOffsets

  apply:
    class: pyobs.utils.offsets.ApplyRaDecOffsets
    max_offset: 7200

  vfs:
    class: pyobs.vfs.VirtualFileSystem
    roots:
      cache:
        class: pyobs.vfs.HttpFile
        download: http://localhost:37075/

* The :class:`~pyobs.modules.pointing.Acquisition` class is used for the acquisition module (line 1).
* It requires the name of the other modules to use, which are :ref:`telescope` for the telescope, :ref:`sbig6303e`
  for the camera and the same for module for the filter wheel, since it is integrated into the camera (lines 4-6).
* The camera settings for the acquisition images (lines 9-11).
* A log file where all the offsets from the acquisitions are stored, can be useful for checking the pointing model
  (line 14).
* Tolerances for the acquisiton: it succeeds if the telescope is closer than 10" to the target and fails if the offsets
  get larger than 7200".
* The pipeline defines steps performed on the images in order to get the offsets for the next step (lines 20-25):

  #. :class:`~pyobs.images.processors.detection.SepSourceDetection` detects sources in the image.
  #. :class:`~pyobs.images.processors.astrometry.AstrometryDotNet` performs the astrometric calibration using a local
     astrometry.net server.
  #. :class:`~pyobs.images.processors.offsets.AstrometryOffsets` uses the astronomy to calculate offsets for the next
     telescope move.

* The offsets are applied via :class:`~pyobs.utils.offsets.ApplyRaDecOffsets`. It fails if the total offset gets larger
  than 7200" (lines 27-29).
* Finally, a VFS is defined with a root ``cache`` that points to the :ref:`filecache` HTTP cache server (lines 31-36)
  and is used for downloading the images from the camera.


autofocus
"""""""""
Module for performing an auto-focus series to determine the best focus

.. code-block:: YAML
  :linenos:

  class: pyobs.modules.focus.AutoFocusSeries

  # modules
  camera: sbig6303e
  focuser: focuser
  filters: sbig6303e

  # use absolute focus values instead of offsets
  offset: False

  # camera settings
  filter_name: Clear
  binning: 2

  # use projected stars
  series:
    class: pyobs.utils.focusseries.ProjectionFocusSeries

  vfs:
    class: pyobs.vfs.VirtualFileSystem
    roots:
      cache:
        class: pyobs.vfs.HttpFile
        download: http://localhost:37075/

* The :class:`~pyobs.modules.focus.AutoFocusSeries` class is used for the auto focus module (line 1).
* It requires the name of the other modules to use, which are :ref:`focuser` for the focus unit, :ref:`sbig6303e`
  for the camera and the same for module for the filter wheel, since it is integrated into the camera (lines 4-6).
* The ``offset`` parameter defines, whether absolute focus values are used or offsets from a fixed value (line 9).
* Image settings (lines 12-13).
* The actual focus series is done using the helper class :class:`~pyobs.utils.focusseries.ProjectionFocusSeries`
  (lines 16-17).
* Finally, a VFS is defined with a root ``cache`` that points to the :ref:`filecache` HTTP cache server (lines 31-36)
  and is used for downloading the images from the camera.


dome
""""
Module operating the dome

.. code-block:: YAML
  :linenos:

  class: pyobs_alpaca.AlpacaDome

  # Alpaca server
  server: xxx.xxx.xxx.xxx
  port: 11111

  # ASCOM device definition
  device_type: dome
  device: 0

  # Follow telescope on sky
  follow: telescope

  # Do not open on bad weather
  weather: weather

* The :class:`~pyobs_alpaca.AlpacaDome` class is used for the dome module (line 1).
* IP and port for the connection are set (lines 4-5).
* The ASCOM device type and number are given (lines 8-9).
* :class:`~pyobs_alpaca.AlpacaDome` inherits from :class:`~pyobs.mixins.follow.FollowMixin`, so it can automatically
  follow other devices, in this case the :ref:`telescope`.


filecache
"""""""""
Module used for distributing images among the other modules

.. code-block:: YAML
  :linenos:

  class: pyobs.modules.utils.HttpFileCache

  port: 37075
  max_file_size: 200

* :class:`~pyobs.modules.utils.HttpFileCache` provides a HTTP server that can be used for distributing files (line 1).
* It needs a port to run on (line 3).
* The maximum file size is set to 200MB (line 4).

flatfield
"""""""""
Modules used for automatic flat-fielding

.. code-block:: YAML
  :linenos:

  class: pyobs.modules.flatfield.FlatField

  # modules
  telescope: telescope
  camera: sbig6303e
  filters: sbig6303e

  # log file
  log_file: /pyobs/flatfield.csv

  # definition of the flat fielder
  flat_fielder:
    class: pyobs.utils.skyflats.FlatFielder
    pointing:
      class: pyobs.utils.skyflats.pointing.SkyFlatsStaticPointing
    combine_binnings: False
    functions:
      1x1:
        Clear: exp(-1.22421*(h+4.06676))
        Red: exp(-1.13196*(h+2.88736))
        Green: exp(-1.07774*(h+2.58413))
        Blue: exp(-1.02646*(h+2.60224))
      2x2:
        Clear: exp(-0.99118*(h+4.66784))
        Red: exp(-1.44869*(h+3.63067))
        Green: exp(-1.23137*(h+3.37692))
        Blue: exp(-1.13074*(h+3.47531))

  vfs:
    class: pyobs.vfs.VirtualFileSystem
    roots:
      cache:
        class: pyobs.vfs.HttpFile
        download: http://localhost:37075/
        upload: http://localhost:37075/
      pyobs:
        class: pyobs.vfs.LocalFile
        root: /opt/pyobs/storage

* The :class:`~pyobs.modules.flatfield.FlatField` class is used for the flat-field module (line 1).
* It requires the name of the other modules to use, which are :ref:`telescope` for the telescope, :ref:`sbig6303e`
  for the camera and the same for module for the filter wheel, since it is integrated into the camera (lines 4-6).
* A log file is created containing the exposure times, which can help refine the functions for the exposure times
  (line 9).
* The flat-fielding itself is done using the :class:`~pyobs.utils.skyflats.FlatFielder` class (lines 12-13).
* The ``pointing`` keyword defines where to point in the sky, for which
  :class:`~pyobs.utils.skyflats.pointing.SkyFlatsStaticPointing` is used (lines 14-15).
* The ``combine_binning`` flag is set to ``False``, so that the ``functions`` (see below) need to include binnings
  (line 16).
* The functions for calculating the exposure time as a function of ``h`` (solar elevation in degrees) are defined,
  depending on the given filter and binning (lines 17-27).
* Finally, a VFS is defined with a root ``cache`` that points to the :ref:`filecache` HTTP cache server (lines 31-36).


focuser
"""""""
Module operating the focus unit to focus the telescope

.. code-block:: YAML
  :linenos:

  class: pyobs_alpaca.AlpacaFocuser

  # Alpaca server
  server: xxx.xxx.xxx.xxx
  port: 11111

  # ASCOM device definition
  device_type: focuser
  device: 0

* The :class:`~pyobs_alpaca.AlpacaFocuser` class is used for the focuser module (line 1).
* IP and port for the connection are set (lines 4-5).
* The ASCOM device type and number are given (lines 8-9).


imagewatcher
""""""""""""
Module for copying new images into the archive

.. code-block:: YAML
  :linenos:

  class: pyobs.modules.image.ImageWatcher

  # path to watch
  watchpath: /temp/

  # paths to copy to
  destinations:
    - /archive/{FNAME}

  vfs:
    class: pyobs.vfs.VirtualFileSystem
    roots:
      temp:
        class: pyobs.vfs.LocalFile
        root: /path/to/new/data
      archive:
        class: pyobs.vfs.ArchiveFile
        url: ...
        token: ...

* The :class:`~pyobs.modules.image.ImageWatcher` class is used for uploading images to the archive (line 1).
* The module actively watches a path in the VFS, in which :ref:`imagewriter` writes new images` (line 4).
* Destination paths in the VFS are provided. Files are only deleted from the watchpath, if they have successfully
  been copied to all ``destinations`` (lines 7-8).
* The VFS defines the paths for the watchpath and all destinations (lines 10-19).


imagewriter
"""""""""""
Module that watches for :class:`~pyobs.events.newimage.NewImageEvent` and writes images to disk

.. code-block:: YAML
  :linenos:

  class: pyobs.modules.image.ImageWriter
  sources: [sbig6303e]

  vfs:
    class: pyobs.vfs.VirtualFileSystem
    roots:
      archive:
        class: pyobs.vfs.LocalFile
        root: /path/to/new/data
      cache:
        class: pyobs.vfs.HttpFile
        download: http://localhost:37075/

* The :class:`~pyobs.modules.image.ImageWriter` class is used for writing images to disk (line 1).
* Only images from the given sources are handled (line 2).
* The VFS defines a path for ``/cache/``, which are the images coming from the camera, and ``/archive/``, to which
  it stores the images.


pointing
""""""""
Module that takes images on various position on the sky for creating a pointing model

.. code-block:: YAML
  :linenos:

  class: pyobs_iag50.Pointing

  # module to use
  acquisition: acquisition

  # log file
  log_file: /pyobs/pointing.poi

  # grid config
  alt_range: [20., 85.]
  az_range: [5., 355.]
  dec_range: [-85., 85.]

  vfs:
    class: pyobs.vfs.VirtualFileSystem
    roots:
      pyobs:
        class: pyobs.vfs.LocalFile
        root: /opt/pyobs/storage

* The custom class ``pyobs_iag50.Pointing`` (inherits from :class:`~pyobs.modules.robotic.pointing.PointingSeries`) is
  used for the pointing module (line 1).
* It requires the name of an acquisition module (line 4).
* A log file is written, which can directly be used by Autoslew to create a new pointing model (line 7).
* The grid is defined in ranges, default values are used for the number of points to create, see
  :class:`~pyobs.modules.robotic.pointing.PointingSeries` for details (lines 10-12).
* A VFS is used to store the log file (lines 14-19).


robotic
"""""""
Module for full robotic mode

.. code-block:: YAML
  :linenos:

  class: pyobs.modules.robotic.Mastermind

  schedule:
    class: pyobs.robotic.lco.LcoTaskSchedule
    url: ...
    token: ...
    site: ...

  runner:
    class: pyobs.robotic.TaskRunner
    scripts:
      BIAS:
        class: pyobs.robotic.lco.scripts.LcoDefaultScript
        camera: sbig6303e
      DARK:
        class: pyobs.robotic.lco.scripts.LcoDefaultScript
        camera: sbig6303e
      EXPOSE:
        class: pyobs.robotic.lco.scripts.LcoDefaultScript
        telescope: telescope
        filters: sbig6303e
        camera: sbig6303e
        roof: dome
        acquisition: acquisition
        autoguider: autoguider
      REPEAT_EXPOSE:
        class: pyobs.robotic.lco.scripts.LcoDefaultScript
        telescope: telescope
        filters: sbig6303e
        camera: sbig6303e
        roof: dome
        acquisition: acquisition
        autoguider: autoguider
      AUTO_FOCUS:
        class: pyobs.robotic.lco.scripts.LcoAutoFocusScript
        telescope: telescope
        filters: sbig6303e
        camera: sbig6303e
        roof: dome
        autofocus: autofocus
      SCRIPT:
        class: pyobs.robotic.lco.scripts.LcoScript
        scripts:
          skyflats:
            class: pyobs.robotic.scripts.SkyFlats
            roof: dome
            telescope: telescope
            flatfield: flatfield
            combine_binnings: False
            readout:
              1x1: 19.6918
              2x2: 8.4241
              3x3: 5.4810
            functions:
              1x1:
                Clear: exp(-1.22421*(h+4.06676))
                Red: exp(-1.13196*(h+2.88736))
                Green: exp(-1.07774*(h+2.58413))
                Blue: exp(-1.02646*(h+2.60224))
              2x2:
                Clear: exp(-0.99118*(h+4.66784))
                Red: exp(-1.44869*(h+3.63067))
                Green: exp(-1.23137*(h+3.37692))
                Blue: exp(-1.13074*(h+3.47531))
            priorities:
              class: pyobs.utils.skyflats.priorities.ArchiveSkyflatPriorities
              archive:
                class: pyobs.utils.archive.PyobsArchive
                url: ...
                token: ...
              site: ...
              instrument: kb03
              filter_names: [ 'Clear', 'Red', 'Green', 'Blue' ]
              binnings: [ 1, 2 ]

* The class :class:`~pyobs.modules.robotic.Mastermind` provides the functionality for the full robotic mode (line 1).
* It requires a schedule to fetch its tasks from. Since we use the LCO observation portal, an object of type
  :class:`~pyobs.robotic.lco.LcoTaskSchedule` is used for this. The parameters given are for the connection to
  the portal (lines 3-7).
* The actual task runner is :class:`~pyobs.robotic.TaskRunner`, which is based on scripts that handle different kinds
  of request. For every type a class is given to handle it (mostly :class:`~pyobs.robotic.lco.scripts.LcoDefaultScript`)
  together with all the modules that this class needs to do its job (lines 9-74).


scheduler
"""""""""
Module for calculating the schedule

.. code-block:: YAML
  :linenos:

  class: pyobs.modules.robotic.Scheduler

  # which twilight to use
  twilight: nautical

  # estimated time of scheduler run
  safety_time: 600

  tasks:
    class: pyobs.robotic.lco.LcoTaskArchive
    url: ...
    token: ...
    instrument_type: ...

  schedule:
    class: pyobs.robotic.lco.LcoTaskSchedule
    url: ...
    token: ...
    site: ...
    enclosure: ...
    telescope: ...
    instrument: ...
    instrument_type: ...

* The class :class:`~pyobs.modules.robotic.Scheduler` calculates the schedule to be used by the :ref:`robotic`
  module (line 1).
* The used definition of twilight is used to determine, in which time frame to actually schedule tasks, can be
  ``nautical`` with sun elevation of -12 degrees or ``astronomical`` at -18 degrees (line 4).
* The ``safety_time`` is the estimated maximum number of seconds that the scheduler will run. That means that the
  scheduler will always only schedule tasks starting at ``now+safety_time`` (line 7).
* A task archive is needed to fetch schedulable tasks from, in this case handled by
  :class:`~pyobs.robotic.lco.LcoTaskArchive` (lines 9-13).
* Finally, the scheduler needs to write the calculated schedule somewhere, which in this case is an object of type
  :class:`~pyobs.robotic.lco.LcoTaskSchedule` (lines 15-23).


sfag
""""
Module that provides the science frame auto-guiding (sfag)

.. code-block:: YAML
  :linenos:

  class: pyobs.modules.pointing.ScienceFrameAutoGuiding

  # modules
  telescope: telescope
  camera: sbig6303e

  # config
  max_exposure_time: 180
  min_interval: 20
  max_interval: 200
  max_offset: 600

  # log file
  log_file: /pyobs/autoguiding.csv

  pipeline:
    - class: pyobs.images.processors.offsets.ProjectedOffsets

  apply:
    class: pyobs.utils.offsets.ApplyRaDecOffsets
    min_offset: 1

  vfs:
    class: pyobs.vfs.VirtualFileSystem
    roots:
      cache:
        class: pyobs.vfs.HttpFile
        download: http://localhost:37075/
      pyobs:
        class: pyobs.vfs.LocalFile
        root: /opt/pyobs/storage

* The class :class:`~pyobs.modules.pointing.ScienceFrameAutoGuiding` performs auto-guiding on images of the science
  camera (line 1).
* It requires the names of the telescope (:ref:`telescope`) and the camera (:ref:`sbig6303e`) modules (lines 4-5).
* The maximum exposure time of images to use for auto-guiding is defined as well as a min/max interval in seconds
  between offsets and a maximum offset to go (lines 8-11).
* A log file is written with all auto-guiding offsets (line 14).
* The pipeline is defined to calculate offsets, in this case based on
  :class:`~pyobs.images.processors.offsets.ProjectedOffsets` (lines 16-17).
* The determined offsets are applied using :class:`~pyobs.utils.offsets.ApplyRaDecOffsets`, with a minimum offset
  defined (lines 19-21).
* A VFS is used to catch the images from the camera and for storing the log (lines 23-31).


startup
"""""""
Module that opens dome and initializes telescope on good weather

.. code-block:: YAML
  :linenos:

  class: pyobs.modules.utils.Trigger

  triggers:
    - event: pyobs.events.GoodWeatherEvent
      module: dome
      method: init
    - event: pyobs.events.RoofOpenedEvent
      module: telescope
      method: init

* The class :class:`~pyobs.modules.utils.Trigger` provides a simple trigger on events (line 1).
* Two triggers are defined:

  * On a :class:`~pyobs.events.GoodWeatherEvent`, the dome is opened via the :ref:`dome` module (lines 4-6).
  * On a :class:`~pyobs.events.RoofOpenedEvent`, the telescope is initialized via the :ref:`telescope` module
    (lines 7-9).

telegram
""""""""
A module for communicating with pyobs via the Telegram app

.. code-block:: YAML
  :linenos:

  class: pyobs.modules.utils.Telegram
  token: ...
  password: ...

* The :class:`~pyobs.modules.utils.Telegram` class is used for the Telegram connection and requires a token and a
  password (lines 1-3).

telescope
"""""""""
Module operating the telescope

.. code-block:: YAML
  :linenos:

  class: pyobs_alpaca.AlpacaTelescope

  # Alpaca server
  server: xxx.xxx.xxx.xxx
  port: 11111

  # ASCOM device definition
  device_type: telescope
  device: 0

  # other modules
  wait_for_dome: dome
  weather: weather

  # additional FITS headers
  fits_headers:
    'TEL-FOCL': [3369.0, 'Focal length of telescope [mm]']
    'OBSERVAT': ['Goettingen', 'Location of telescope']
    'ORIGIN': ['IAG', 'Organization responsible for the data']
    'TEL-AEFF': [502.0, 'Telescope effective aperture [mm]']
    'TEL-APER': [514.8, 'Telescope circular aperture [mm]']
    'TELESCOP': ['IAG50', 'Name of telescope']

  # namespace for fits
  fits_namespaces:
    sbig6303e:
    asi071mc: ['OBSERVAT', 'ORIGIN', 'SITEID', 'TEL-ALT', 'TEL-AZ', 'TEL-RA', 'TEL-DEC', 'RA', 'DEC', 'ALTOFF',
               'AZOFF', 'CRVAL1', 'CRVAL2', 'AIRMASS', 'TEL-ZD', 'MOONDIST', 'MOONALT', 'MOONFRAC', 'SUNDIST', 'SUNALT']


* The :class:`~pyobs_alpaca.AlpacaTelescope` class is used for the telescope module (line 1).
* IP and port for the connection are set (lines 4-5).
* The ASCOM device type and number are given (lines 8-9).
* The module waits for the :ref:`dome` module after movements and consults the :ref:`weather` module about the current
  weather (lines 12-13).
* Additional static FITS headers are provided (lines 16-22).
* FITS namespaces for other modules providing FITS headers are given:

  * The :ref:`sbig6303e` module gets all FITS headers (line 26).
  * The :ref:`asi071mc` module only gets the listed FITS headers (lines 27-28).


weather
"""""""
Module that provides current weather information

.. code-block:: YAML
  :linenos:

  class: pyobs.modules.weather.Weather
  url: ...

* In this case, the :class:`~pyobs.modules.weather.Weather` class is used, which connects to a running instance of
  `pyobs-weather <https://docs.pyobs.org/projects/pyobs-weather/en/latest/>`_ (lines 1-2).

iag50cam
^^^^^^^^

sbig6303e
"""""""""
Module for operating a SBIG6303e camera

.. code-block:: YAML
  :linenos:

  class: pyobs_sbig.Sbig6303eCamera

  # temperature setpoint
  setpoint: -10

  # file naming
  filenames: /cache/iag50cm-kb03-{DAY-OBS|date:}-{FRAMENUM|string:04d}-{IMAGETYP|type}00.fits

  # additional fits headers
  fits_headers:
    INSTRUME: ['kb03', 'Name of instrument']
    'DET-PIXL': [0.009, 'Size of detector pixels (square) [mm]']
    'DET-NAME': ['KAF-6303E', 'Name of detector']
    'DET-RON': [13.5, 'Detector readout noise [e-]']
    'DET-SATU': [100000, 'Detector saturation limit [e-]']
    'DET-DARK': [0.3, 'Detector dark current [e-/s]']
    'TELID': ['0m5', 'ID for telescope']
    'SITEID': ['iag50cm', 'ID of site.']

  # opto-mechanical centre
  centre: [1536.0, 1024.0]

  # rotation (east of north)
  rotation: -1.76
  flip: True

  # filter wheel
  filter_wheel: AUTO
  filter_names: [Red, Green, Blue, Clear, Halpha]

  vfs:
    class: pyobs.vfs.VirtualFileSystem
    roots:
      cache:
        class: pyobs.vfs.HttpFile
        upload: http://iag50srv:37075/

* The :class:`~pyobs_sbig.Sbig6303eCamera` class is used for connecting to the camera (line 1).
* The temperature is set to -10 degrees C (line 4).
* The filenames for the images are create from a template that is filled from the FITS header (line 7).
* Additional static FITS headers are provided (lines 10-18).
* The opti-mechanic centre of the camera is provided (line 21).
* The rotation is given and whether the image must be flipped (lines 24-25).
* The names of the filters in the filter wheel are defined (lines 28-29).
* A VFS is used to store the images.

asi071mc
""""""""
Module for operating a ZWO ASI071MC Pro camera

.. code-block:: YAML
  :linenos:

  class: pyobs_asi.AsiCoolCamera
  camera: ZWO ASI071MC Pro

  # file naming
  filenames: /cache/iag50cm-sz01-{DAY-OBS|date:}-{FRAMENUM|string:04d}-{IMAGETYP|type}00.fits

  # additional fits headers
  fits_headers:
    INSTRUME: ['sz01', 'Name of instrument']
    'DET-PIXL': [0.00478, 'Size of detector pixels (square) [mm]']
    'DET-NAME': ['SONY IMX071', 'Name of detector']
    'DET-RON': [2.3, 'Detector readout noise [e-]']
    'DET-SATU': [46000, 'Detector saturation limit [e-]']
    'TELID': ['0m1', 'ID for telescope']
    'SITEID': ['goe', 'ID of site.']
    'TEL-FOCL': [770.0, 'Focal length of telescope [mm]']
    'OBSERVAT': ['Goettingen', 'Location of telescope']
    'ORIGIN': ['IAG', 'Organization responsible for the data']
    'TEL-AEFF': [110.0, 'Telescope effective aperture [mm]']
    'TEL-APER': [110.8, 'Telescope circular aperture [mm]']
    'TELESCOP': ['IAG50GUIDER', 'Name of telescope']

  # opto-mechanical centre
  centre: [2472.0, 1642.0]

  # rotation (east of north)
  rotation: 3.06
  flip: True

  vfs:
    class: pyobs.vfs.VirtualFileSystem
    roots:
      cache:
        class: pyobs.vfs.HttpFile
        upload: http://iag50srv:37075/

* Basically the same as the :ref:`sbig6303e` module, but using the :class:`~pyobs_asi.AsiCoolCamera` class for ZWO
  ASI cameras.
