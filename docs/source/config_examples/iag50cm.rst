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

robotic
"""""""

scheduler
"""""""""

sfag
""""

startup
"""""""

telegram
""""""""

telescope
"""""""""

weather
"""""""


iag50cam
^^^^^^^^

sbig6303e
"""""""""
