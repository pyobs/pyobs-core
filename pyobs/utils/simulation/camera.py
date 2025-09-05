from __future__ import annotations

import glob
import numpy as np
import astropy.units as u
from astropy.table import Table
from astropy.time import Time
from typing import Tuple, TYPE_CHECKING, Optional, Any, cast
from astropy.wcs import WCS
from astropy.io import fits
from numpy.typing import NDArray

from photutils.datasets import make_model_image, make_noise_image
from astropy.modeling import models
import logging

from pyobs.object import Object
from pyobs.utils.enums import ImageFormat
from pyobs.images import Image

if TYPE_CHECKING:
    from pyobs.utils.simulation import SimWorld


log = logging.getLogger(__name__)


class SimCamera(Object):
    """A simulated camera."""

    __module__ = "pyobs.utils.simulation"

    def __init__(
        self,
        world: "SimWorld",
        image_size: Optional[Tuple[int, int]] = None,
        pixel_size: float = 0.015,
        images: Optional[str] = None,
        max_mag: float = 20.0,
        seeing: float = 3.0,
        **kwargs: Any,
    ):
        """Inits a new camera.

        Args:
            world: World to use.
            image_size: Size of image.
            pixel_size: Square pixel size in mm.
            images: Filename pattern (e.g. /path/to/*.fits) for files to return instead of simulated images.
            max_mag: Maximum magnitude for sim.
            seeing: Seeing in arcsec.
        """
        Object.__init__(self, **kwargs)

        # store
        self.world = world
        self.telescope = world.telescope
        self.full_frame: Tuple[int, int, int, int] = (
            (0, 0, image_size[0], image_size[1]) if image_size is not None else (0, 0, 512, 512)
        )
        self.window = self.full_frame
        self.binning = (1, 1)
        self.pixel_size = pixel_size
        self.image_format = ImageFormat.INT16
        self.images = (
            [] if images is None else sorted(glob.glob(images)) if "*" in images or "?" in images else [images]
        )
        self._max_mag = max_mag
        self._seeing = seeing

        # private stuff
        self._catalog = None
        self._catalog_coords = None

    def get_image(self, exp_time: float, open_shutter: bool) -> Image:
        """Simulate an image.

        Args:
            exp_time: Exposure time in seconds.
            open_shutter: Whether the shutter is opened.

        Returns:
            numpy array with image.
        """

        # get now
        now = Time.now()

        # simulate or what?
        if self.images:
            # take image from list
            filename = self.images.pop(0)
            data = fits.getdata(filename)
            self.images.append(filename)

        else:
            # simulate
            data = self._simulate_image(exp_time, open_shutter)

        # create header
        hdr = self._create_header(exp_time, open_shutter, now, data)

        # return it
        return Image(data, header=hdr)

    def _simulate_image(self, exp_time: float, open_shutter: bool) -> NDArray[Any]:
        """Simulate an image.

        Args:
            exp_time: Exposure time in seconds.
            open_shutter: Whether the shutter is opened.

        Returns:
            numpy array with image.
        """

        # get shape for image
        shape = (int(self.window[3]), int(self.window[2]))

        # create image with Gaussian noise for BIAS
        data = make_noise_image(shape, distribution="gaussian", mean=10, stddev=1.0)

        # non-zero exposure time?
        if exp_time > 0:
            # add DARK
            data += make_noise_image(shape, distribution="gaussian", mean=exp_time / 1e4, stddev=exp_time / 1e5)

            # add stars and stuff
            if open_shutter:
                # get solar altitude
                sun_alt = self.world.sun_alt

                # get mean flatfield counts
                flat_counts = 30000 / np.exp(-1.28 * (4.209 + sun_alt)) * exp_time

                # create flat
                data += make_noise_image(shape, distribution="gaussian", mean=flat_counts, stddev=flat_counts / 10.0)

                # get catalog with sources
                sources = self._get_sources_table(exp_time)

                # filter out all sources outside FoV
                sources = sources[
                    (sources["x_mean"] > 0)
                    & (sources["x_mean"] < shape[1])
                    & (sources["y_mean"] > 0)
                    & (sources["y_mean"] < shape[0])
                ]

                # create image
                model = models.Moffat2D()
                model_shape = (15, 15)
                data += make_model_image(shape, model, sources, model_shape=model_shape)

        # saturate
        data[data > 65535] = 65535

        # finished
        return cast(NDArray[Any], data).astype(np.uint16)

    def _create_header(self, exp_time: float, open_shutter: float, time: Time, data: NDArray[Any]) -> fits.Header:
        # create header
        hdr = fits.Header()
        hdr["NAXIS1"] = data.shape[1]
        hdr["NAXIS2"] = data.shape[0]

        # set values
        hdr["DATE-OBS"] = (time.isot, "Date and time of start of exposure")
        hdr["EXPTIME"] = (exp_time, "Exposure time [s]")

        # binning
        hdr["XBINNING"] = hdr["DET-BIN1"] = (int(self.binning[0]), "Binning factor used on X axis")
        hdr["YBINNING"] = hdr["DET-BIN2"] = (int(self.binning[1]), "Binning factor used on Y axis")

        # window
        hdr["XORGSUBF"] = (int(self.window[0]), "Subframe origin on X axis")
        hdr["YORGSUBF"] = (int(self.window[1]), "Subframe origin on Y axis")

        # statistics
        hdr["DATAMIN"] = (float(np.min(data)), "Minimum data value")
        hdr["DATAMAX"] = (float(np.max(data)), "Maximum data value")
        hdr["DATAMEAN"] = (float(np.mean(data)), "Mean data value")

        # hardware
        hdr["TEL-FOCL"] = (self.telescope.focal_length, "Focal length [mm]")
        hdr["DET-PIXL"] = (self.pixel_size, "Size of detector pixels (square) [mm]")

        # finished
        return hdr

    def _get_catalog(self, fov: float) -> Table:
        """Returns GAIA catalog for current telescope coordinates."""
        # get catalog
        if self._catalog_coords is None or self._catalog_coords.separation(self.telescope.real_pos) > 10.0 * u.arcmin:
            from astroquery.utils.tap import TapPlus

            # get coordinates
            coords = self.telescope.real_pos

            # query TAP
            tap = TapPlus(url="https://gea.esac.esa.int/tap-server/tap")
            query = self._get_gaia_query(coords.ra.degree, coords.dec.degree, fov * 1.5)
            job = tap.launch_job(query)

            # get result table
            self._catalog = job.get_results()

        return self._catalog

    def _get_gaia_query(self, ra: float, dec: float, radius: float) -> str:
        # define query
        return f"""
                SELECT
                  TOP 1000
                  DISTANCE(
                    POINT('ICRS', ra, dec),
                    POINT('ICRS', {ra}, {dec})
                  ) as dist,
                  ra, dec, phot_g_mean_flux, phot_g_mean_mag
                FROM
                  gaiadr2.gaia_source
                WHERE
                  1 = CONTAINS(
                    POINT('ICRS', ra, dec),
                    CIRCLE('ICRS', {ra}, {dec}, {radius})
                  )
                  AND phot_g_mean_mag < {self._max_mag}
                ORDER BY
                  phot_g_mean_mag ASC
                """

    def _get_sources_table(self, exp_time: float) -> Table:
        """Create sources table."""

        # calculate cdelt1/2
        tmp = 360.0 / (2.0 * np.pi) * self.pixel_size / self.telescope.focal_length
        cdelt1, cdelt2 = tmp * self.binning[0], tmp * self.binning[1]
        log.info(
            "Plate scale is %.2f\"/px, image size is %.2f'x%.2f'.",
            cdelt1 * 3600,
            cdelt1 * 60 * self.window[2],
            cdelt2 * 60 * self.window[3],
        )

        # FoV
        fov = np.max(cdelt2 * np.array(self.full_frame[2:]))

        # get catalog
        cat = self._get_catalog(fov)

        # create WCS
        w = WCS(naxis=2)
        w.wcs.crpix = [self.window[3] / 2.0, self.window[2] / 2.0]
        w.wcs.cdelt = np.array([-cdelt1, cdelt2])
        w.wcs.crval = [self.telescope.real_pos.ra.degree, self.telescope.real_pos.dec.degree]
        w.wcs.ctype = ["RA---TAN", "DEC--TAN"]

        # set sigma to given seeing (in FWHM) in pixels
        fwhm = self._seeing / 3600.0 / cdelt1 / 2.3548

        # convert world to pixel coordinates
        cat["x"], cat["y"] = w.wcs_world2pix(cat["ra"], cat["dec"], 0)

        # get columns
        sources = cat["x", "y", "phot_g_mean_flux", "phot_g_mean_mag"]
        sources.rename_columns(["x", "y", "phot_g_mean_flux"], ["x_mean", "y_mean", "flux"])
        sources.add_column([fwhm] * len(sources), name="x_stddev")
        sources.add_column([fwhm] * len(sources), name="y_stddev")
        sources["flux"] *= exp_time

        """
        table['amplitude'] = [50, 70, 150, 210]
        table['x_mean'] = [160, 25, 150, 90]
        table['y_mean'] = [70, 40, 25, 60]
        table['x_stddev'] = [15.2, 5.1, 3., 8.1]
        table['y_stddev'] = [2.6, 2.5, 3., 4.7]
        table['theta'] = np.radians(np.array([145., 20., 0., 60.]))
        """

        # finished
        return sources


__all__ = ["SimCamera"]
