Images (pyobs.images)
---------------------

.. automodule:: pyobs.images

The :class:`~pyobs.images.Image` class is the fundamental data structure passed through the entire
*pyobs* imaging pipeline. Every camera module produces an ``Image``, every
:class:`~pyobs.images.ImageProcessor` consumes and returns one, and the VFS convenience methods
(:meth:`~pyobs.vfs.VirtualFileSystem.read_image`, :meth:`~pyobs.vfs.VirtualFileSystem.write_image`)
serialise and deserialise them transparently.


The Image class
^^^^^^^^^^^^^^^

An ``Image`` holds up to five arrays alongside a FITS header:

.. list-table::
   :header-rows: 1
   :widths: 20 80

   * - Attribute
     - Contents
   * - ``data``
     - 2D float array of pixel values (or 3×H×W for colour images)
   * - ``mask``
     - Boolean/integer mask — non-zero pixels are excluded from processing
   * - ``uncertainty``
     - Per-pixel standard deviation array
   * - ``catalog``
     - :class:`astropy.table.Table` of detected sources, populated by source detection processors
   * - ``raw``
     - Copy of the pixel data before calibration

Every property has a ``safe_`` variant (e.g. ``safe_data``) that returns ``None`` instead of raising
an exception when the attribute is absent, which is useful in pipeline steps that handle both
calibrated and uncalibrated images.


Creating images
^^^^^^^^^^^^^^^

::

    from pyobs.images import Image

    # from a FITS file on disk
    image = Image.from_file("science_frame.fits")

    # from raw bytes (e.g. received over the network)
    image = Image.from_bytes(data)

    # from an astropy CCDData object
    image = Image.from_ccddata(ccd)

    # from scratch
    import numpy as np
    image = Image(data=np.zeros((1024, 1024), dtype=np.float32))


Serialisation
^^^^^^^^^^^^^

``Image`` serialises to a multi-extension FITS file. The primary HDU holds the science data;
mask, uncertainty, source catalog, and raw data are stored in additional extensions named
``MASK``, ``UNCERT``, ``CAT``, and ``RAW`` respectively. Round-tripping is lossless::

    image.writeto("output.fits")
    image2 = Image.from_file("output.fits")

    # or to/from bytes in memory
    raw_bytes = image.to_bytes()
    image3 = Image.from_bytes(raw_bytes)


Meta information
^^^^^^^^^^^^^^^^

The ``meta`` dict carries runtime data that is intentionally **not** written to FITS. It is keyed
by class, which prevents accidental collisions between different pipeline stages::

    from pyobs.images.meta import PixelOffsets, RaDecOffsets

    # store
    image.set_meta(PixelOffsets(dx=3.2, dy=-1.7))

    # retrieve (raises ValueError if absent)
    offsets = image.get_meta(PixelOffsets)

    # retrieve safely
    offsets = image.get_meta_safe(PixelOffsets)  # returns None if absent

The available meta classes are:

- :class:`~pyobs.images.meta.PixelOffsets` — pixel-space offset ``(dx, dy)``
- :class:`~pyobs.images.meta.RaDecOffsets` — equatorial offset ``(dra, ddec)`` in degrees
- :class:`~pyobs.images.meta.AltAzOffsets` — horizontal offset ``(dalt, daz)`` in degrees
- :class:`~pyobs.images.meta.SkyOffsets` — two :class:`~astropy.coordinates.SkyCoord` objects
- :class:`~pyobs.images.meta.OnSkyDistance` — on-sky separation in arcseconds
- :class:`~pyobs.images.meta.ExpTime` — recommended next exposure time


Image processors
^^^^^^^^^^^^^^^^

:class:`~pyobs.images.ImageProcessor` is the base class for all pipeline steps. A processor
is an :class:`~pyobs.object.Object` subclass that is callable — it receives an ``Image`` and
returns a (possibly modified) ``Image``::

    from pyobs.images import Image
    from pyobs.images.processor import ImageProcessor

    class MyProcessor(ImageProcessor):
        async def __call__(self, image: Image) -> Image:
            image.data = image.data - image.data.mean()
            return image

Processors are composable — the :class:`~pyobs.modules.image.Pipeline` module chains them in
sequence, passing each output as the next processor's input. See
:doc:`image_processors/index` for the full list of built-in processors.


API reference
^^^^^^^^^^^^^

.. autoclass:: pyobs.images.Image
   :members:
   :show-inheritance:

.. autoclass:: pyobs.images.processor.ImageProcessor
   :members:
   :show-inheritance:

Meta classes
""""""""""""

.. autoclass:: pyobs.images.meta.PixelOffsets
   :members:

.. autoclass:: pyobs.images.meta.RaDecOffsets
   :members:

.. autoclass:: pyobs.images.meta.AltAzOffsets
   :members:

.. autoclass:: pyobs.images.meta.SkyOffsets
   :members:

.. autoclass:: pyobs.images.meta.OnSkyDistance
   :members:

.. autoclass:: pyobs.images.meta.ExpTime
   :members: