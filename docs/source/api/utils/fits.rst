FITS utilities (pyobs.utils.fits)
---------------------------------

.. automodule:: pyobs.utils.fits

This module provides two utilities for working with FITS files: a function for extracting image sections
defined by standard FITS keywords, and a flexible filename formatter that builds filenames from FITS
header values.


Image sections: ``fitssec``
^^^^^^^^^^^^^^^^^^^^^^^^^^^^

CCD images often carry ``TRIMSEC`` and ``BIASSEC`` header keywords that define the science region and
the overscan region, respectively. :func:`~pyobs.utils.fits.fitssec` reads such a keyword and slices
the image array accordingly::

    from pyobs.utils.fits import fitssec

    science_data = fitssec(hdu, "TRIMSEC")   # trim to science region
    bias_data    = fitssec(hdu, "BIASSEC")   # extract overscan strip

If the keyword is absent, the full image array is returned unchanged.


Filename formatting: ``FilenameFormatter``
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

:class:`~pyobs.utils.fits.FilenameFormatter` builds output filenames from FITS header values using a
template string. Placeholders are wrapped in curly braces and reference FITS header keywords::

    from pyobs.utils.fits import FilenameFormatter

    fmt = FilenameFormatter("{DATE-OBS|date}-{OBJECT|lower}-{EXPTIME|string:05.1f}s.fits")
    filename = fmt(hdu.header)
    # → "2024-06-01-m51-030.0s.fits"

Placeholders support an optional pipe-separated modifier:

.. list-table::
   :header-rows: 1
   :widths: 20 80

   * - Modifier
     - Effect
   * - ``{KEY}``
     - Raw value of header keyword ``KEY``
   * - ``{KEY|lower}``
     - String value converted to lowercase
   * - ``{KEY|date}``
     - Parses value as a time and formats as ``YYYY-MM-DD``
   * - ``{KEY|date:-}``
     - Date with a custom delimiter (e.g. ``YYYY.MM.DD``)
   * - ``{KEY|time}``
     - Parses value as a time and formats as ``HH-MM-SS``
   * - ``{KEY|string:fmt}``
     - Formats numeric value with a Python ``%``-style format (e.g. ``05d``, ``4.1f``)
   * - ``{KEY|filter}``
     - Includes the filter name (prefixed with ``-``) only for light/flat frames; empty otherwise
   * - ``{KEY|type}``
     - Maps ``IMAGETYP`` to a single letter: ``b`` (bias), ``d`` (dark), ``f`` (flat), ``e`` (object)

A list of format strings can be passed instead of a single string — the first one that resolves
without a ``KeyError`` is used, which is convenient for handling images from different instruments
with different header conventions::

    fmt = FilenameFormatter([
        "{DATE-OBS|date}-{OBJECT|lower}-{FILTER|lower}.fits",
        "{DATE-OBS|date}-{OBJECT|lower}.fits",   # fallback if no FILTER key
    ])

The convenience function :func:`~pyobs.utils.fits.format_filename` wraps the class for one-off use::

    from pyobs.utils.fits import format_filename

    filename = format_filename(hdu.header, "{DATE-OBS|date}-{OBJECT|lower}.fits")


API reference
^^^^^^^^^^^^^

.. autofunction:: pyobs.utils.fits.fitssec

.. autofunction:: pyobs.utils.fits.format_filename

.. autoclass:: pyobs.utils.fits.FilenameFormatter
   :members: