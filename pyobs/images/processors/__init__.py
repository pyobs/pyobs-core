"""
Overview
========

An image processor is a modular, usually asynchronous component that accepts a
``pyobs.images.Image`` as input and returns an ``Image`` as output. Each processor
encapsulates a single, well-defined operation—such as calibration, source detection,
astrometric solving, geometric masking, filename creation, or offset computation—
so processors can be composed into configurable pipelines. Some processors modify
pixel data; many operate on FITS headers, attached source catalogs, or structured
metadata without touching pixels. The design emphasizes composability, clear
contracts, and explicit assumptions.

Core Interface
==============

All processors derive from a common base, ``ImageProcessor``, or from a specialized
base that adds a domain-specific contract (for example, ``Offsets`` for steps that
produce offsets, ``Astrometry`` for solvers, or ``ExpTimeEstimator`` for exposure
recommendations).

The Image Model
===============

The ``Image`` object bundles everything a processor acts on:

- Pixel data: ``image.data`` is typically a 2D NumPy array. Some processors support
  color layouts by selecting a plane if ``image.is_color`` is true.
- FITS header: ``image.header`` is a dict-like mapping carrying instrument metadata,
  WCS solutions, site/time information, and processing breadcrumbs.
- Source catalog: ``image.catalog`` is an ``astropy.table.Table`` with per-source
  measurements (positions, fluxes, sizes, shapes, flags). ``image.safe_catalog``
  yields ``None`` when no catalog is present.
- Mask: ``image.mask`` stores a pixel mask; ``image.safe_mask`` indicates presence.

Asynchrony and Execution
========================

Processors are asynchronous to integrate I/O and computation transparently with
the controller’s event loop.

- Network-bound steps (e.g., calling remote services or module proxies) are awaited.
- CPU-bound calls to third-party libraries (e.g., photutils, SEP) are commonly
  offloaded via ``run_in_executor`` to avoid blocking.
- Repeat lookups or expensive objects can be cached to reduce latency.

Configuration and Instantiation
===============================

Processors are typically configured in YAML:

.. code-block:: yaml

  class: pyobs.images.processors.detection.SepSourceDetection
  threshold: 1.8
  minarea: 9

- Nested object configurations can be resolved into concrete instances via
  ``get_object`` (for example, creating an ``Archive`` or a ``SkyCoord`` from a dict).
- Some processors acquire other modules through asynchronous proxies (e.g.,
  an ``IFitsHeaderBefore`` provider for headers, or an ``IMultiFiber`` module).

Conventions and Best Practices
==============================

Coordinate Conventions
----------------------

NumPy arrays use 0-based indices, while many catalogs and FITS headers follow
FITS-like 1-based pixel coordinates. A processor that mixes catalog positions with
array indices should either convert between systems or document its expectations
explicitly to avoid off-by-one errors.

WCS Assumptions
---------------

When required, ensure a valid WCS is present in the header and that frames and
units match expectations (commonly ICRS degrees). Processors that rely on WCS
should validate presence and fail clearly if it is missing or inconsistent.

Header Keys as Contracts
------------------------

Header keys carry the implicit contract between processors: instrument and binning
(e.g., ``INSTRUME``, ``XBINNING``/``YBINNING`` or ``DET-BIN1``), site location
(``LATITUDE``, ``LONGITUD``, ``HEIGHT``), observation time (``DATE-OBS``),
detector characteristics (``DET-GAIN``, ``DET-SATU``), and provenance
(e.g., filenames, reduction level). Pipelines should ensure upstream steps populate
what downstream steps expect.

Performance
===========

- Use ``safe_*`` accessors to short-circuit gracefully (e.g., no data or catalog).
- Offload CPU-heavy operations to executors to keep the loop responsive.
- Avoid unnecessary conversions and copies if an operation turns out to be a no-op.
- Cache external resources (e.g., calibration masters) to minimize I/O.

Writing Your Own Processor
==========================

1. Subclass ``ImageProcessor`` (or a specialized base like ``Offsets``).
2. Define a clear ``__init__`` signature; forward ``**kwargs`` to the base.
3. Implement ``async __call__(image: Image) -> Image``:
   - Validate prerequisites early (headers, catalog, WCS).
   - Decide on copy vs. in-place mutation and document it.
   - Prefer nonblocking patterns for heavy or remote work.
   - Log key steps and failure reasons; raise exceptions when appropriate.
4. Be explicit about units, coordinate conventions, and which parts of the
   ``Image`` you modify (data, header, catalog, metadata).

Example Pipelines
=================

Calibration → Astrometry → Detection → Filtering → Offsets
----------------------------------------------------------

.. code-block:: yaml

  - class: pyobs.images.processors.calibration.Calibration
    archive: { class: your.archive.Class, ... }
    max_days_bias: 7
    max_days_dark: 7
    max_days_flat: 7
  - class: pyobs.images.processors.astrometry.AstrometryDotNet
    url: "http://localhost:8080/api"
    source_count: 80
    timeout: 30
    exceptions: true
  - class: pyobs.images.processors.detection.SepSourceDetection
    threshold: 1.8
    minarea: 9
  - class: pyobs.images.processors.misc.ImageSourceFilter
    min_dist_to_border: 25
    num_stars: 20
    min_pixels: 10
  - class: pyobs.images.processors.offsets.BrightestStarOffsets

Drawing and Filename Formatting
-------------------------------

.. code-block:: yaml

  - class: pyobs.images.processors.misc.Circle
    x: 100
    y: 150
    radius: 50
    outline: [255, 0, 0]
    width: 3
  - class: pyobs.images.processors.misc.CreateFilename
    pattern: "{SITEID}-{DAY-OBS|date:%Y%m%d}-{FRAMENUM|string:05d}.fits"

FAQs
====

Why are processors asynchronous?
  Many processors interact with remote modules or services and perform heavy
  computations; the async interface integrates these operations without blocking
  the controller’s event loop.

Do processors always modify pixel data?
  No. Many operate on headers, catalogs, or metadata only. Always consult the
  processor’s documentation to understand which parts of the ``Image`` are affected.

How do processors signal failures?
  Some raise exceptions (optionally configurable), while others mark sentinel
  headers (e.g., ``WCSERR``) and log warnings. Pipelines should choose behavior
  appropriate to the use case.

What about units and coordinate systems?
  Be explicit. Use ICRS degrees for WCS when applicable, clarify whether pixel
  positions use FITS 1-based or NumPy 0-based conventions, and state units for
  thresholds and offsets (ADU, electrons, arcseconds, pixels).
"""
