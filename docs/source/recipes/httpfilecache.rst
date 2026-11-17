.. _httpfilecache-recipe:

Distributing large images with HttpFileCache
============================================

Modern CMOS cameras produce large images. A 6248x4176 sensor with 16 bit pixels gives a FITS file of
about 52 MB. The usual way to hand such images from a camera module to other modules (GUI, pipeline,
archive) is a :class:`~pyobs.modules.utils.HttpFileCache` together with the
:class:`~pyobs.vfs.HttpFile` VFS class. This recipe shows how to set this up and what transfer times
to expect.


Setup
-----

The cache is a module of its own. Run it on the server, i.e. the machine where most of the image
consumers run, not on the camera PC:

.. code-block:: YAML

  class: pyobs.modules.utils.HttpFileCache
  port: 37075
  cache_size: 25
  max_file_size: 100

``max_file_size`` is in MB and must be larger than the largest file you upload. Note that an image
that was converted to float32 (e.g. by a calibration step) is twice the size of the raw 16 bit image.

The camera module only needs to upload, so its VFS root only gets an ``upload`` URL:

.. code-block:: YAML

  vfs:
    class: pyobs.vfs.VirtualFileSystem
    roots:
      cache:
        class: pyobs.vfs.HttpFile
        upload: http://server:37075/

Modules that read the images only get a ``download`` URL. On the server itself, use ``localhost``:

.. code-block:: YAML

  vfs:
    class: pyobs.vfs.VirtualFileSystem
    roots:
      cache:
        class: pyobs.vfs.HttpFile
        download: http://localhost:37075/

If the cache is reachable from outside your network, set a ``token`` on the cache and the same
``token`` on all ``HttpFile`` roots. ``HttpFile`` has a ``timeout`` (default 30 s) for each
upload/download, which you may need to increase for slow links.


Expected transfer times
-----------------------

We measured a synthetic 52.2 MB frame (6248x4176, uint16) between a small industrial camera PC
(Intel Atom E3950, 4 cores) and a server (Intel Xeon E3-1240 v6), connected via Gigabit Ethernet.
A plain TCP transfer between the two reached 117 MB/s. Medians of 5 runs:

=============================  ========  ==========  ===============  ===============
Client -> cache                Upload    Download    ``write_image``  ``read_image``
=============================  ========  ==========  ===============  ===============
camera PC -> server            461 ms    497 ms      585 ms           679 ms
server -> camera PC            469 ms    465 ms      541 ms           556 ms
camera PC -> camera PC         311 ms    169 ms      437 ms           354 ms
server -> server               60 ms     45 ms       98 ms            124 ms
=============================  ========  ==========  ===============  ===============

``write_image`` includes converting the image to FITS, ``read_image`` includes parsing it. On the
camera PC, converting takes about 130 ms and parsing about 185 ms, on the server both take less than
50 ms.

What this means:

- Over Gigabit Ethernet, both upload and download run at about line speed. The overhead of HTTP and
  Python is small, the network is the limit. A 52 MB image needs about 0.5 s per network hop.
- With the cache on the server, the camera needs about 0.6 s to get an image off the camera PC.
  Consumers on the server then get it in about 0.1 s.
- With the cache on the camera PC, every consumer has to pull the image over the network from the
  slowest machine in the system. Don't do that.
- Compressing images on a small camera PC costs more CPU time than it saves in transfer time at
  Gigabit speeds. If you need compression for remote clients on slow links, do it on the server.
- If transfers are still too slow, send fewer bytes (binning, sub-frames, previews for the GUI) or
  use a faster network.


Measuring your own setup
------------------------

The script :file:`scripts/vfs/bench_httpfilecache.py` runs the same test. Start a cache on one
machine:

.. code-block:: bash

  python bench_httpfilecache.py serve 37099

and run the client on another one:

.. code-block:: bash

  python bench_httpfilecache.py client http://server:37099/ 5

Use a port that is not used by your production cache. To get a reference for the raw network
speed, you can use ``iperf3`` or a simple ``nc`` transfer.
