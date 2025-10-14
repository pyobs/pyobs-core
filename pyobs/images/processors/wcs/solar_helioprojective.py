import logging
from typing import Any

from astropy.time import Time

from pyobs.images.processor import ImageProcessor
from pyobs.images import Image


log = logging.getLogger(__name__)


class SolarHelioprojective(ImageProcessor):
    """
    Add a time-aware solar helioprojective WCS to the image header based on disk center, radius, and DATE-OBS.

    This processor writes a helioprojective Cartesian WCS (HPLN/HPLT,
    tangent projection) to the image’s FITS header. It reads the solar disk center
    pixel coordinates and disk radius (in pixels) from header keywords and computes
    the angular pixel scale at the observation time using the Sun’s apparent angular
    radius. The observation time is taken from ``DATE-OBS`` and interpreted as UTC.

    The WCS fields set are:

        - CRPIX1/CRPIX2: the disk center pixel coordinates (x, y).
        - CRVAL1/CRVAL2: 0.0, i.e., the helioprojective longitude/latitude at the center.
        - CTYPE1/CTYPE2: "HPLN-TAN" and "HPLT-TAN".
        - CDELT1/CDELT2: angular pixel scale in degrees per pixel, computed as
          ``sunpy.coordinates.sun.angular_radius(obs_time).degree / disk_radius_pixels``,
          where ``obs_time = astropy.time.Time(DATE-OBS, scale="utc")``.

    :param str keyword_x: FITS header keyword holding the x coordinate of the solar
                          disk center in pixels. Default: "DISKPOS1".
    :param str keyword_y: FITS header keyword holding the y coordinate of the solar
                          disk center in pixels. Default: "DISKPOS2".
    :param str keyword_radius: FITS header keyword holding the solar disk radius in
                               pixels. Default: "DISKRAD".
    :param kwargs: Additional keyword arguments forwarded to
                   :class:`pyobs.images.processor.ImageProcessor`.

    Behavior
    --------
    - Parses the observation time from ``DATE-OBS`` with
      ``obs_time = Time(image.header["DATE-OBS"], scale="utc")``.
    - Computes the angular pixel scale (CDELT) as the Sun’s apparent angular radius
      at ``obs_time`` (in degrees) divided by the disk radius in pixels.
    - Writes CRPIX1/CRPIX2 from the specified center keywords and sets CRVAL1/CRVAL2
      to 0.0 with helioprojective tangent CTYPEs.
    - Returns a copy of the input image with the updated header; pixel data are unchanged.

    Input/Output
    ------------
    - Input: :class:`pyobs.images.Image` whose header contains:

      - the disk center and radius keywords specified by ``keyword_x``, ``keyword_y``,
        and ``keyword_radius``, and
      - ``DATE-OBS`` parsable by ``astropy.time.Time`` (UTC assumed here).

    - Output: :class:`pyobs.images.Image` (copied) with a helioprojective WCS written
      into the FITS header.

    Configuration (YAML)
    --------------------
    Use disk center/radius estimated upstream (e.g., via SimpleDisk):

    .. code-block:: yaml

       class: pyobs.images.processors.wcs.SolarHelioprojective
       keyword_x: "DISKPOS1"
       keyword_y: "DISKPOS2"
       keyword_radius: "DISKRAD"

    Notes
    -----
    - Coordinate convention: CRPIX values in FITS/WCS are defined in 1-based pixel
      coordinates. Ensure the disk center stored under ``keyword_x``/``keyword_y`` is
      in FITS convention; if zero-based values were written previously, add 1 before
      using them as CRPIX.
    - Units: This implementation sets CDELT in degrees per pixel and does not add
      CUNIT keywords. If arcseconds are preferred, convert CDELT to arcseconds and
      set ``CUNIT1 = CUNIT2 = "arcsec"``.
    - Time dependence: The angular pixel scale is computed at the observation time
      from ``DATE-OBS`` (UTC). If ``DATE-OBS`` is missing or not parseable, the step
      cannot proceed.
    - Disk radius must be positive and non-zero; otherwise the scale is undefined.
    """

    __module__ = "pyobs.images.processors.wcs"

    def __init__(
        self,
        keyword_x: str = "DISKPOS1",
        keyword_y: str = "DISKPOS2",
        keyword_radius: str = "DISKRAD",
        **kwargs: Any,
    ):
        """Init a new helioprojective wcs processor.

        Args:
            keyword_x: X coordinate of sun in image.
            keyword_y: Y coordinate of sun in image.
            keyword_radius: Radius of sun in image.
        """
        ImageProcessor.__init__(self, **kwargs)

        # store
        self._keyword_x = keyword_x
        self._keyword_y = keyword_y
        self._keyword_radius = keyword_radius

    async def __call__(self, image: Image) -> Image:
        """Add WCS.

        Args:
            image: Image to use.

        Returns:
            Image with new WCS.
        """
        import sunpy.coordinates  # type: ignore

        obs_time = Time(image.header["DATE-OBS"], scale="utc")
        cdelt = sunpy.coordinates.sun.angular_radius(obs_time).degree / image.header[self._keyword_radius]

        out = image.copy()
        out.header["CRPIX1"] = image.header[self._keyword_x]
        out.header["CRPIX2"] = image.header[self._keyword_y]
        out.header["CRVAL1"] = 0.0
        out.header["CRVAL2"] = 0.0
        out.header["CTYPE1"] = "HPLN-TAN"
        out.header["CTYPE2"] = "HPLT-TAN"
        out.header["CDELT1"] = cdelt
        out.header["CDELT2"] = cdelt
        return out


__all__ = ["SolarHelioprojective"]
